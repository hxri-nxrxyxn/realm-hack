#!/usr/bin/env python3
"""
RakshaNet Bluetooth Call & Telemetry WebSocket + Dashboard Server
=================================================================
1. Monitors Bluetooth handsfree phone calls in PipeWire/Helvum.
   When an active call is detected, extracts the phone number and
   broadcasts it over WebSockets to trigger automatic SMS dispatch.
2. Monitors Bluetooth BLE / Message Access Profile (MAP) notifications
   from the connected gateway phone (08:1C:6E:5F:10:F7). When an incoming
   sensor telemetry SMS alert arrives from the client phone, extracts the
   payload and prints the live readings in the exact requested format.
3. Hosts a real-time web dashboard UI on HTTP (default port 8080) displaying
   live sensor cards, visual compass needle, telephony status, and alert logs.
4. Accepts direct WebSocket telemetry streams from connected client apps.
"""

import argparse
import asyncio
import http.server
import json
import os
import re
import socket
import socketserver
import sys
import tempfile
import threading
import time
from datetime import datetime
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
import websockets

def get_local_ip():
    """Detect the local LAN / Wi-Fi IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def format_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def extract_body_from_bmsg(raw_text: str) -> str:
    """Extract body text between BEGIN:MSG and END:MSG from bMessage format."""
    lines = raw_text.splitlines()
    in_msg = False
    body_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped == 'BEGIN:MSG':
            in_msg = True
            continue
        elif stripped == 'END:MSG':
            in_msg = False
            break
        elif in_msg:
            body_lines.append(line)
    if body_lines:
        return '\n'.join(body_lines).strip()
    return raw_text.strip()

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, server_instance=None, **kwargs):
        self.server_instance = server_instance
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        # Suppress routine HTTP request logging to keep console clean
        pass

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        if self.path in ["/", "/index.html"]:
            dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
            if not os.path.exists(dashboard_path):
                self.send_error(404, "dashboard.html not found")
                return
            try:
                with open(dashboard_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_error(500, f"Error loading dashboard: {e}")
        elif self.path == "/api/status":
            phone_clients = [str(c.remote_address[0]) for c in self.server_instance.connected_clients if str(c.remote_address[0]) != '127.0.0.1']
            status_data = {
                "server": "RakshaNet Telemetry Server",
                "local_ip": self.server_instance.local_ip,
                "ws_port": self.server_instance.port,
                "http_port": self.server_instance.http_port,
                "bt_mac": self.server_instance.bt_mac,
                "clients_count": len(self.server_instance.connected_clients),
                "gateway_online": len(phone_clients) > 0,
                "gateway_ips": phone_clients,
                "last_call_number": self.server_instance.last_detected_number or "9995283835",
                "telemetry_count": self.server_instance.telemetry_count,
                "timestamp": format_timestamp()
            }
            body = json.dumps(status_data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path == "/api/trigger-call":
            self.server_instance.on_call_detected("+918714711540", name="Simulated Caller", state="active")
            body = b'{"success":true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/trigger-telemetry":
            sample_alert = (
                "Rakshak Alert: Emergency assistance requested\n\n"
                "Live Sensors (5/5):\n"
                "• Pedometer: 0 steps (0.00 km)\n"
                "• Light: 53 lx\n"
                "• Accelerometer: 9.7 m/s²\n"
                "• Gyroscope: 0.2 rad/s\n"
                "• Magnetometer: 186° S"
            )
            self.server_instance.display_telemetry(sample_alert, sender="+919495364448", source="Simulated Test")
            body = b'{"success":true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404, "Not Found")

class TelemetryServer:
    def __init__(self, host="0.0.0.0", port=8765, http_port=8080, bt_mac="08:1C:6E:5F:10:F7"):
        self.host = host
        self.port = port
        self.http_port = http_port
        self.bt_mac = bt_mac
        self.local_ip = get_local_ip()
        self.connected_clients = set()
        self.loop = None
        self.telephony_service = "org.pipewire.Telephony"
        self.last_detected_number = None
        self.last_call_time = 0
        self.last_call_number = None
        self.latest_telemetry = None
        self.telemetry_count = 0
        self.processed_msg_ids = set()
        self.map_session_path = None
        self.pending_call_trigger = None

    def display_telemetry(self, raw_content: str, sender: str = "", source: str = "BLE / Bluetooth MAP"):
        """
        Displays live sensor readings in the exact requested visual format:
        
        Rakshak Alert: Emergency assistance requested

        Live Sensors (5/5):
        • Pedometer: <steps> steps (<dist> km)
        • Light: <lux> lx
        • Accelerometer: <accel> m/s²
        • Gyroscope: <gyro> rad/s
        • Magnetometer: <mag>° <cardinal>
        """
        clean_text = raw_content.strip()
        
        # If wrapped inside bMessage, extract it first
        if "BEGIN:MSG" in clean_text:
            clean_text = extract_body_from_bmsg(clean_text)

        # Standardize header if present with trailing punctuation
        clean_text = re.sub(
            r"Rakshak Alert:\s*Emergency assistance requested\.?",
            "Rakshak Alert: Emergency assistance requested",
            clean_text
        )

        self.telemetry_count += 1
        ts = format_timestamp()
        source_label = f"{sender} ({source})" if sender else source

        print("\n" + "=" * 65, flush=True)
        print(f"\033[1;31m[{ts}] 🚨 RAKSHAK SENSOR TELEMETRY RECEIVED (Update #{self.telemetry_count})\033[0m", flush=True)
        print(f"\033[1;36m  Channel Source  : \033[0m{source_label}", flush=True)
        print("=" * 65, flush=True)
        print(f"\033[1;32m{clean_text}\033[0m", flush=True)
        print("=" * 65 + "\n", flush=True)

        # Store latest telemetry in memory for newly connected clients
        self.latest_telemetry = {
            "content": clean_text,
            "sender": sender,
            "source": source,
            "timestamp": ts,
            "update_count": self.telemetry_count
        }

        # Broadcast to all connected WebSockets (phone apps + web dashboard)
        if self.loop and self.connected_clients:
            payload = {
                "type": "TELEMETRY_RECEIVED",
                "content": clean_text,
                "sender": sender,
                "source": source,
                "timestamp": ts,
                "update_count": self.telemetry_count
            }
            asyncio.run_coroutine_threadsafe(self.broadcast(payload), self.loop)

    async def broadcast(self, payload):
        """Send JSON message to all connected clients."""
        if not self.connected_clients:
            return

        message_str = json.dumps(payload)
        dead_clients = set()
        for client in self.connected_clients:
            try:
                await client.send(message_str)
            except Exception:
                dead_clients.add(client)
        self.connected_clients -= dead_clients

    def on_call_detected(self, number, name="", state="active", raw_path=""):
        """Called from D-Bus thread when a call is extracted."""
        clean_num = str(number).strip()
        if not clean_num or clean_num == "Unknown":
            clean_num = "9995283835"

        now = time.time()
        # Deduplicate triggers for the same number within 3 seconds
        if self.last_call_number == clean_num and (now - self.last_call_time) < 3:
            print(f"[{format_timestamp()}] ⏳ Debounced: Duplicate trigger for {clean_num} ignored (<3s)")
            return

        self.last_call_time = now
        self.last_call_number = clean_num
        self.last_detected_number = clean_num
        self.pending_call_trigger = {
            "number": clean_num,
            "name": str(name),
            "state": str(state),
            "timestamp": now
        }

        print("\n" + "=" * 60)
        print(f"[{format_timestamp()}] 📞 NEW CALL EXTRACTED FROM BLUETOOTH HANDSFREE")
        print("=" * 60)
        print(f"  📱 Phone Number : \033[1;32m{clean_num}\033[0m")
        if name:
            print(f"  👤 Contact Name : {name}")
        print(f"  ⚡ Call State   : {state}")

        phone_clients = [str(c.remote_address[0]) for c in self.connected_clients if str(c.remote_address[0]) != '127.0.0.1']
        if not phone_clients:
            print(f"  ⚠️ \033[1;31mWARNING: Phone A Gateway App is DISCONNECTED!\033[0m")
            print(f"     Phone A's screen is off or app is closed. Trigger queued for auto-send upon reconnect.")
        else:
            print(f"  📶 Gateway Link : \033[1;32mConnected ({', '.join(phone_clients)})\033[0m")
        print("=" * 60 + "\n", flush=True)

        payload = {
            "type": "CALL_DETECTED",
            "number": clean_num,
            "name": str(name),
            "state": str(state),
            "timestamp": format_timestamp()
        }

        if self.loop:
            asyncio.run_coroutine_threadsafe(self.broadcast(payload), self.loop)

    async def handle_client(self, websocket):
        """Handle incoming WebSocket connection from phone apps & browser dashboard."""
        client_addr = websocket.remote_address
        print(f"[{format_timestamp()}] 📱 Client connected from: {client_addr}")
        self.connected_clients.add(websocket)

        welcome_payload = {
            "type": "SERVER_READY",
            "server": "RakshaNet Call & Telemetry Server",
            "ip": self.local_ip,
            "port": self.port,
            "http_port": self.http_port,
            "last_number": self.last_detected_number or "9995283835",
            "telemetry_count": self.telemetry_count,
            "latest_telemetry": self.latest_telemetry,
            "timestamp": format_timestamp()
        }
        await websocket.send(json.dumps(welcome_payload))

        # Replay any recent pending call trigger (<45s old) to newly connected phone
        if self.pending_call_trigger and client_addr[0] != '127.0.0.1':
            age = time.time() - self.pending_call_trigger.get("timestamp", 0)
            if age < 45:
                print(f"[{format_timestamp()}] 🚀 Replaying queued call trigger for {self.pending_call_trigger['number']} to Gateway ({client_addr[0]})!")
                replay_payload = {
                    "type": "CALL_DETECTED",
                    "number": self.pending_call_trigger["number"],
                    "name": self.pending_call_trigger.get("name", ""),
                    "state": self.pending_call_trigger.get("state", "active"),
                    "timestamp": format_timestamp()
                }
                await websocket.send(json.dumps(replay_payload))

        try:
            async for raw_message in websocket:
                try:
                    data = json.loads(raw_message)
                    msg_type = data.get("type", "")

                    if msg_type == "CLIENT_TELEMETRY":
                        report = data.get("report") or data.get("message") or ""
                        sender = data.get("sender", "Client App")
                        self.display_telemetry(report, sender=sender, source="Direct App WebSocket")
                    elif msg_type == "SMS_SENT":
                        num = data.get("number", "Unknown")
                        self.pending_call_trigger = None
                        print(f"[{format_timestamp()}] ✅ Phone confirmed: Auto-sent SMS to \033[1;32m{num}\033[0m")
                    elif msg_type == "PING":
                        await websocket.send(json.dumps({"type": "PONG", "timestamp": format_timestamp()}))
                    elif "Live Sensors" in str(data):
                        self.display_telemetry(str(data), sender="Client App", source="Direct App WebSocket")
                    else:
                        print(f"[{format_timestamp()}] 📩 Received from client: {data}")
                except json.JSONDecodeError:
                    if "Live Sensors" in raw_message or "Rakshak Alert" in raw_message:
                        self.display_telemetry(raw_message, sender="Client App", source="Raw App WebSocket")
                    else:
                        print(f"[{format_timestamp()}] 📩 Raw text from client: {raw_message}")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.connected_clients.remove(websocket)
            print(f"[{format_timestamp()}] 🔌 Client disconnected: {client_addr}")

    def run_telephony_listener(self):
        """Monitors PipeWire / oFono handsfree calls."""
        DBusGMainLoop(set_as_default=True)
        try:
            bus = dbus.SessionBus()
        except Exception as e:
            print(f"[{format_timestamp()}] Telephony D-Bus init error: {e}")
            return

        def extract_props(props):
            num = str(props.get("LineIdentification", "")).strip()
            name = str(props.get("Name", "")).strip()
            state = str(props.get("State", "active")).strip()
            return num, name, state

        def on_call_added(path, properties):
            num, name, state = extract_props(properties)
            if num:
                self.on_call_detected(num, name, state, path)

        def on_interfaces_added(path, interfaces):
            if "org.pipewire.Telephony.Call1" in interfaces:
                props = interfaces["org.pipewire.Telephony.Call1"]
                num, name, state = extract_props(props)
                if num:
                    self.on_call_detected(num, name, state, path)

        # Check existing active call immediately on launch
        try:
            telephony = bus.get_object(self.telephony_service, "/org/pipewire/Telephony/ag1")
            vcm = dbus.Interface(telephony, "org.ofono.VoiceCallManager")
            for c_path, c_props in vcm.GetCalls().items():
                num, name, state = extract_props(c_props)
                if num:
                    self.on_call_detected(num, name, state, c_path)
        except Exception:
            pass

        bus.add_signal_receiver(
            on_call_added,
            signal_name="CallAdded",
            dbus_interface="org.ofono.VoiceCallManager",
            bus_name=self.telephony_service
        )

        glib_loop = GLib.MainLoop()
        glib_loop.run()

    def run_bluetooth_map_listener(self):
        """
        Monitors Bluetooth BLE / Message Access Profile (MAP) notifications.
        Connects to org.bluez.obex and captures incoming SMS telemetry from Phone A.
        """
        DBusGMainLoop(set_as_default=True)
        try:
            bus = dbus.SessionBus()
        except Exception as e:
            print(f"[{format_timestamp()}] Bluetooth MAP D-Bus init error: {e}")
            return

        mas_interface = None

        def init_session():
            nonlocal mas_interface
            try:
                obex_client = dbus.Interface(
                    bus.get_object('org.bluez.obex', '/org/bluez/obex'),
                    'org.bluez.obex.Client1'
                )
                session_path = obex_client.CreateSession(self.bt_mac, {'Target': 'map'})
                self.map_session_path = session_path
                mas_obj = bus.get_object('org.bluez.obex', session_path)
                mas_interface = dbus.Interface(mas_obj, 'org.bluez.obex.MessageAccess1')
                mas_interface.SetFolder('telecom')
                mas_interface.SetFolder('msg')
                print(f"[{format_timestamp()}] 📶 Bluetooth MAP notification listener active for {self.bt_mac}")
                return True
            except Exception:
                return False

        def fetch_full_message(msg_path):
            """Fetch full bMessage payload using Message1.Get()"""
            try:
                msg_obj = dbus.Interface(bus.get_object('org.bluez.obex', msg_path), 'org.bluez.obex.Message1')
                tmp_fd, tmp_file = tempfile.mkstemp(prefix="map_msg_")
                os.close(tmp_fd)
                transfer, _ = msg_obj.Get(tmp_file, False)
                for _ in range(10):
                    time.sleep(0.15)
                    if os.path.exists(tmp_file) and os.path.getsize(tmp_file) > 0:
                        break
                content = ""
                if os.path.exists(tmp_file):
                    with open(tmp_file, 'r', errors='ignore') as f:
                        content = f.read()
                    try:
                        os.remove(tmp_file)
                    except OSError:
                        pass
                return content
            except Exception:
                return ""

        def process_message_candidate(path, props):
            subj = str(props.get('Subject', ''))
            sender = str(props.get('SenderAddress', ''))
            
            # Check if this message is a Rakshak sensor reading
            if 'Rakshak' in subj or 'Sensors' in subj or 'Live Sensors' in subj or 'Pedometer' in subj:
                full_content = fetch_full_message(path)
                final_text = full_content if full_content else subj
                self.display_telemetry(final_text, sender=sender, source="Bluetooth BLE / MAP")
                return True
            return False

        def on_interfaces_added(path, interfaces):
            """Real-time event trigger from BlueZ OBEX MNS when an SMS notification arrives."""
            if 'org.bluez.obex.Message1' in interfaces:
                props = interfaces['org.bluez.obex.Message1']
                msg_id = str(path)
                if msg_id not in self.processed_msg_ids:
                    self.processed_msg_ids.add(msg_id)
                    process_message_candidate(path, props)

        bus.add_signal_receiver(
            on_interfaces_added,
            signal_name='InterfacesAdded',
            dbus_interface='org.freedesktop.DBus.ObjectManager',
            bus_name='org.bluez.obex'
        )

        def periodic_inbox_check():
            """Periodic fast scanner of top inbox messages to guarantee zero dropped alerts."""
            nonlocal mas_interface
            if not mas_interface:
                init_session()
                return True

            try:
                msgs = mas_interface.ListMessages('inbox', {'MaxListCount': dbus.UInt16(5)})
                for path, meta in msgs.items():
                    msg_id = str(path)
                    if msg_id not in self.processed_msg_ids:
                        self.processed_msg_ids.add(msg_id)
                        process_message_candidate(path, meta)
            except dbus.exceptions.DBusException:
                mas_interface = None
            except Exception:
                pass
            return True

        init_session()
        GLib.timeout_add_seconds(1, periodic_inbox_check)

        glib_loop = GLib.MainLoop()
        glib_loop.run()

    def run_http_server(self):
        """Runs the standalone Dashboard HTTP Server in a daemon thread."""
        server_inst = self
        class BoundHandler(DashboardHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, server_instance=server_inst, **kwargs)

        socketserver.ThreadingTCPServer.allow_reuse_address = True
        try:
            httpd = socketserver.ThreadingTCPServer((self.host, self.http_port), BoundHandler)
            print(f"[{format_timestamp()}] 🖥️ Web Dashboard UI active: \033[1;32mhttp://{self.local_ip}:{self.http_port}\033[0m")
            httpd.serve_forever()
        except Exception as e:
            print(f"[{format_timestamp()}] HTTP server error: {e}")

    async def console_trigger_loop(self):
        """Allows testing in terminal: press Enter to test call, or type 't' to test telemetry."""
        loop = asyncio.get_event_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        try:
            while True:
                line = await reader.readline()
                if not line:
                    await asyncio.sleep(1)
                    continue
                text = line.decode().strip()
                if text in ['t', 'telemetry', 'alert']:
                    print(f"[{format_timestamp()}] 🧪 Simulating sensor telemetry alert:")
                    sample_alert = (
                        "Rakshak Alert: Emergency assistance requested\n\n"
                        "Live Sensors (5/5):\n"
                        "• Pedometer: 0 steps (0.00 km)\n"
                        "• Light: 53 lx\n"
                        "• Accelerometer: 9.7 m/s²\n"
                        "• Gyroscope: 0.2 rad/s\n"
                        "• Magnetometer: 186° S"
                    )
                    self.display_telemetry(sample_alert, sender="+919495364448", source="Simulated Test")
                else:
                    test_number = text if text else "9995283835"
                    print(f"[{format_timestamp()}] 🧪 Manual call trigger test with number: {test_number}")
                    self.on_call_detected(test_number, name="Test Caller", state="active")
        except asyncio.CancelledError:
            pass

    async def start(self):
        self.loop = asyncio.get_running_loop()

        # Thread 1: PipeWire / oFono Telephony listener
        telephony_thread = threading.Thread(target=self.run_telephony_listener, daemon=True)
        telephony_thread.start()

        # Thread 2: Bluetooth BLE / Message Access Profile (MAP) notification listener
        map_thread = threading.Thread(target=self.run_bluetooth_map_listener, daemon=True)
        map_thread.start()

        # Thread 3: HTTP Web Dashboard UI server
        http_thread = threading.Thread(target=self.run_http_server, daemon=True)
        http_thread.start()

        print("\n" + "=" * 65)
        print(" 🚀 RakshaNet Telephony, BLE & Dashboard Server")
        print("=" * 65)
        print(f"  🌐 Local Wi-Fi IP  : \033[1;36m{self.local_ip}\033[0m")
        print(f"  🔌 WebSocket Port  : \033[1;36m{self.port}\033[0m  (\033[1;32mws://{self.local_ip}:{self.port}\033[0m)")
        print(f"  🖥️ Web Dashboard UI: \033[1;36m{self.http_port}\033[0m  (\033[1;32mhttp://{self.local_ip}:{self.http_port}\033[0m)")
        print(f"  📶 Gateway BLE MAC : \033[1;36m{self.bt_mac}\033[0m")
        print("=" * 65)
        print("  💡 Tip: Open the dashboard in browser to view live visual sensors.")
        print("  💡 Tip: Press [Enter] to simulate a call test.")
        print("  💡 Tip: Type 't' + [Enter] to simulate sensor telemetry display.")
        print("=" * 65 + "\n", flush=True)

        async with websockets.serve(self.handle_client, self.host, self.port):
            asyncio.create_task(self.console_trigger_loop())
            await asyncio.Future()  # run forever

def main():
    parser = argparse.ArgumentParser(description="RakshaNet Bluetooth Call & Telemetry Server")
    parser.add_argument("--port", "-p", type=int, default=8765, help="WebSocket port (default: 8765)")
    parser.add_argument("--http-port", type=int, default=8080, help="Web Dashboard HTTP port (default: 8080)")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface (default: 0.0.0.0)")
    parser.add_argument("--bt-mac", default="08:1C:6E:5F:10:F7", help="Gateway Bluetooth MAC address")
    args = parser.parse_args()

    server = TelemetryServer(host=args.host, port=args.port, http_port=args.http_port, bt_mac=args.bt_mac)
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    main()
