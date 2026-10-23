#!/usr/bin/env python3
"""
RakshaNet Bluetooth Call WebSocket Server
=========================================
Monitors Bluetooth handsfree phone calls in PipeWire/Helvum.
When an active call is detected, extracts the phone number and
broadcasts it over WebSockets to the connected Capacitor mobile app
to trigger automatic SMS sending.
"""

import argparse
import asyncio
import json
import os
import socket
import sys
import threading
from datetime import datetime
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
import websockets

def get_local_ip():
    """Detect the local LAN / Wi-Fi IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't connect externally, used by OS kernel to resolve local interface route
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def format_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class CallServer:
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.local_ip = get_local_ip()
        self.connected_clients = set()
        self.loop = None
        self.service_name = "org.pipewire.Telephony"
        self.last_detected_number = None

    async def broadcast(self, payload):
        """Send JSON message to all connected phone clients."""
        if not self.connected_clients:
            print(f"[{format_timestamp()}] ⚠️ Call event occurred, but no phone app is connected yet to receive it.")
            return

        message_str = json.dumps(payload)
        print(f"[{format_timestamp()}] 📡 Broadcasting to {len(self.connected_clients)} client(s): {message_str}")
        
        dead_clients = set()
        for client in self.connected_clients:
            try:
                await client.send(message_str)
            except Exception as e:
                print(f"[{format_timestamp()}] Error sending to client: {e}")
                dead_clients.add(client)
        
        self.connected_clients -= dead_clients

    def on_call_detected(self, number, name="", state="active", raw_path=""):
        """Called from D-Bus thread when a call is extracted."""
        clean_num = str(number).strip()
        if not clean_num or clean_num == "Unknown":
            clean_num = "9995283835"

        self.last_detected_number = clean_num
        print("\n" + "=" * 60)
        print(f"[{format_timestamp()}] 📞 NEW CALL EXTRACTED FROM BLUETOOTH HANDSFREE")
        print("=" * 60)
        print(f"  📱 Phone Number : \033[1;32m{clean_num}\033[0m")
        if name:
            print(f"  👤 Contact Name : {name}")
        print(f"  ⚡ Call State   : {state}")
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
        """Handle incoming WebSocket connection from phone app."""
        client_addr = websocket.remote_address
        print(f"[{format_timestamp()}] 📱 Phone app connected from: {client_addr}")
        self.connected_clients.add(websocket)

        # Send greeting with server status and any recent number
        welcome_payload = {
            "type": "SERVER_READY",
            "server": "RakshaNet Call Server",
            "ip": self.local_ip,
            "port": self.port,
            "last_number": self.last_detected_number or "9995283835",
            "timestamp": format_timestamp()
        }
        await websocket.send(json.dumps(welcome_payload))

        try:
            async for raw_message in websocket:
                try:
                    data = json.loads(raw_message)
                    msg_type = data.get("type", "")
                    
                    if msg_type == "SMS_SENT":
                        num = data.get("number", "Unknown")
                        print(f"[{format_timestamp()}] ✅ Phone confirmed: Auto-sent SMS to \033[1;32m{num}\033[0m")
                    elif msg_type == "PING":
                        await websocket.send(json.dumps({"type": "PONG", "timestamp": format_timestamp()}))
                    else:
                        print(f"[{format_timestamp()}] 📩 Received from phone: {data}")
                except json.JSONDecodeError:
                    print(f"[{format_timestamp()}] 📩 Raw text from phone: {raw_message}")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.connected_clients.remove(websocket)
            print(f"[{format_timestamp()}] 🔌 Phone app disconnected: {client_addr}")

    def run_dbus_listener(self):
        """Runs PipeWire D-Bus listener inside a daemon thread."""
        DBusGMainLoop(set_as_default=True)
        try:
            bus = dbus.SessionBus()
        except Exception as e:
            print(f"[{format_timestamp()}] D-Bus init error: {e}")
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
            telephony = bus.get_object(self.service_name, "/org/pipewire/Telephony/ag1")
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
            bus_name=self.service_name
        )

        bus.add_signal_receiver(
            on_interfaces_added,
            signal_name="InterfacesAdded",
            dbus_interface="org.freedesktop.DBus.ObjectManager",
            bus_name=self.service_name
        )

        glib_loop = GLib.MainLoop()
        glib_loop.run()

    async def console_trigger_loop(self):
        """Allows testing by pressing Enter or typing a number in terminal."""
        loop = asyncio.get_event_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        while True:
            line = await reader.readline()
            if not line:
                break
            text = line.decode().strip()
            test_number = text if text else "9995283835"
            print(f"[{format_timestamp()}] 🧪 Manual trigger test with number: {test_number}")
            self.on_call_detected(test_number, name="Test Caller", state="active")

    async def start(self):
        self.loop = asyncio.get_running_loop()

        # Start D-Bus listener in background thread
        dbus_thread = threading.Thread(target=self.run_dbus_listener, daemon=True)
        dbus_thread.start()

        print("\n" + "=" * 65)
        print(" 🚀 RakshaNet Telephony WebSocket Server")
        print("=" * 65)
        print(f"  🌐 Local Wi-Fi IP  : \033[1;36m{self.local_ip}\033[0m")
        print(f"  🔌 Port            : \033[1;36m{self.port}\033[0m")
        print(f"  🔗 WebSocket URL   : \033[1;32mws://{self.local_ip}:{self.port}\033[0m")
        print("=" * 65)
        print(f"  📱 Connect your mobile app to: ws://{self.local_ip}:{self.port}")
        print("  💡 Tip: Press [Enter] anytime in this terminal to simulate a call test.")
        print("=" * 65 + "\n", flush=True)

        async with websockets.serve(self.handle_client, self.host, self.port):
            asyncio.create_task(self.console_trigger_loop())
            await asyncio.Future()  # run forever

def main():
    parser = argparse.ArgumentParser(description="RakshaNet Bluetooth Call WebSocket Server")
    parser.add_argument("--port", "-p", type=int, default=8765, help="Port to listen on (default: 8765)")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface (default: 0.0.0.0)")
    args = parser.parse_args()

    server = CallServer(host=args.host, port=args.port)
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    main()
