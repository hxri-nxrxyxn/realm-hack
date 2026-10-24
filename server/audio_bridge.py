#!/usr/bin/env python3
"""
RakshaNet Real-Time Audio Conversation Bridge
=============================================
Records and processes 10-second audio segments ONLY DURING AN ACTIVE CALL on Redmi Note 10.

Workflow:
1. Dormant / Idle when no call is active.
2. Triggers immediately when an incoming or connected call is detected on Redmi Note 10.
3. Records 10s audio chunk via ffmpeg from the Bluetooth call stream (or PulseAudio default).
4. Dispatches to n8n AI webhook:
   curl -X POST http://192.168.2.69:5678/webhook-test/passive -F "data=@record.mp3"
   (Falls back to /webhook/passive if test mode is inactive).
5. Receives AI reply:
   - If MP3 binary: plays directly.
   - If JSON text: synthesizes neural Malayalam speech (ml-IN-SobhanaNeural) and plays.
6. Plays audio back to BOTH laptop speakers and Bluetooth phone call output.
7. Stops recording immediately when the call ends.
"""

import os
import sys
import time
import json
import shutil
import threading
import subprocess
from datetime import datetime
import dbus
import requests

PRIMARY_WEBHOOK_URL = "http://192.168.2.69:5678/webhook-test/passive"
FALLBACK_WEBHOOK_URL = "http://192.168.2.69:5678/webhook/passive"
TEMP_RECORD_PATH = "/tmp/record.mp3"
TEMP_REPLY_PATH = "/tmp/caller_reply.mp3"

def format_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def is_call_active():
    """Checks if a call is actively connected on Redmi Note 10 (via D-Bus or Bluetooth audio stream)."""
    # Check 1: D-Bus oFono VoiceCallManager on PipeWire Telephony
    try:
        bus = dbus.SessionBus()
        telephony = bus.get_object("org.pipewire.Telephony", "/org/pipewire/Telephony/ag1")
        vcm = dbus.Interface(telephony, "org.ofono.VoiceCallManager")
        calls = vcm.GetCalls()
        if len(calls) > 0:
            return True
    except Exception:
        pass

    # Check 2: Active bluez audio input source in pactl
    try:
        res = subprocess.run(["pactl", "list", "sources", "short"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for line in res.stdout.strip().splitlines():
            parts = line.split()
            if len(parts) >= 2:
                name = parts[1]
                if "bluez" in name and "monitor" not in name:
                    return True
    except Exception:
        pass

    return False

def get_recording_source():
    """Finds active Bluetooth phone input source or falls back to default."""
    try:
        res = subprocess.run(["pactl", "list", "sources", "short"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for line in res.stdout.strip().splitlines():
            parts = line.split()
            if len(parts) >= 2:
                name = parts[1]
                if "bluez" in name and "monitor" not in name:
                    return name
    except Exception:
        pass
    return "default"

def get_playback_sinks():
    """Finds all sinks to play to (default laptop speakers + bluetooth phone sink)."""
    sinks = ["default"]
    try:
        res = subprocess.run(["pactl", "list", "sinks", "short"], stdout=subprocess.PIPE, text=True)
        for line in res.stdout.strip().splitlines():
            parts = line.split()
            if len(parts) >= 2:
                name = parts[1]
                if "bluez" in name and name not in sinks:
                    sinks.append(name)
    except Exception:
        pass
    return sinks

def play_audio(audio_path):
    """Plays audio through laptop speaker and Bluetooth phone call output."""
    if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 100:
        return

    sinks = get_playback_sinks()
    procs = []
    for sink in sinks:
        env = os.environ.copy()
        if sink != "default":
            env["PULSE_SINK"] = sink
        try:
            p = subprocess.Popen(
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "error", audio_path],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            procs.append(p)
        except Exception as e:
            print(f"[{format_timestamp()}] ⚠️ Audio playback error on {sink}: {e}")

    for p in procs:
        try:
            p.wait(timeout=20)
        except Exception:
            p.kill()

class AudioConversationBridge:
    def __init__(self, primary_url=PRIMARY_WEBHOOK_URL, fallback_url=FALLBACK_WEBHOOK_URL, on_event=None):
        self.primary_url = primary_url
        self.fallback_url = fallback_url
        self.on_event = on_event
        self.is_running = False
        self.call_in_progress = False
        self.thread = None
        self.record_proc = None
        self.chunk_count = 0
        self.last_status = "idle (waiting for call)"
        self.last_transcript = ""
        self.last_ai_reply = ""
        self.last_chunk_time = None

    def log(self, msg):
        print(f"[{format_timestamp()}] {msg}", flush=True)
        if self.on_event:
            try:
                self.on_event({
                    "type": "AUDIO_BRIDGE_LOG",
                    "status": self.last_status,
                    "chunk": self.chunk_count,
                    "call_active": self.call_in_progress,
                    "last_reply": self.last_ai_reply,
                    "timestamp": format_timestamp()
                })
            except Exception:
                pass

    def notify_call_started(self):
        """Called by server when a call on Redmi Note 10 starts."""
        self.call_in_progress = True
        self.log("📞 Call started on Redmi Note 10 -> Starting 10s audio AI recording loop.")
        self.start()

    def notify_call_ended(self):
        """Called by server when a call on Redmi Note 10 ends."""
        self.call_in_progress = False
        self.log("📴 Call ended on Redmi Note 10 -> Stopping audio recording.")
        self.stop()

    def record_chunk(self, duration=10, output_path=TEMP_RECORD_PATH):
        source = get_recording_source()
        cmd = [
            "ffmpeg", "-y",
            "-f", "pulse",
            "-i", source,
            "-t", str(duration),
            "-acodec", "libmp3lame",
            "-ab", "128k",
            "-ar", "44100",
            "-ac", "1",
            output_path
        ]
        self.last_status = f"recording ({duration}s from {source})"
        self.record_proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            self.record_proc.wait(timeout=duration + 3)
        except Exception:
            if self.record_proc:
                self.record_proc.kill()
        finally:
            self.record_proc = None

        return os.path.exists(output_path) and os.path.getsize(output_path) > 1000

    def send_to_webhook(self, mp3_path=TEMP_RECORD_PATH):
        """Sends MP3 to webhook-test/passive or fallback /webhook/passive."""
        for url in [self.primary_url, self.fallback_url]:
            try:
                self.last_status = f"sending to {url}"
                with open(mp3_path, "rb") as f:
                    files = {"data": ("record.mp3", f, "audio/mpeg")}
                    resp = requests.post(url, files=files, timeout=60)

                if resp.status_code == 200:
                    return resp
                elif resp.status_code == 404 and url == self.primary_url:
                    continue
                else:
                    self.log(f"⚠️ Webhook {url} returned HTTP {resp.status_code}")
            except Exception as e:
                self.log(f"⚠️ Webhook error on {url}: {e}")
        return None

    def process_response(self, response):
        """Extracts audio or synthesizes text reply, then plays back."""
        content_type = response.headers.get("Content-Type", "")
        raw_bytes = response.content

        # Check if response is raw binary audio
        is_audio = (
            "audio" in content_type or
            raw_bytes.startswith(b"ID3") or
            raw_bytes.startswith(b"\xff\xfb") or
            raw_bytes.startswith(b"RIFF")
        )

        if is_audio:
            with open(TEMP_REPLY_PATH, "wb") as f:
                f.write(raw_bytes)
            self.last_ai_reply = f"[Binary Audio: {len(raw_bytes)} bytes]"
            self.log(f"🔊 Received MP3 audio response ({len(raw_bytes)} bytes). Playing back to caller...")
            play_audio(TEMP_REPLY_PATH)
            return

        # Check if response is JSON
        try:
            data = response.json()
            # If JSON contains audio base64
            for audio_key in ["audio", "data", "mp3", "audio_base64"]:
                if audio_key in data and isinstance(data[audio_key], str) and len(data[audio_key]) > 500:
                    import base64
                    try:
                        audio_data = base64.b64decode(data[audio_key])
                        with open(TEMP_REPLY_PATH, "wb") as f:
                            f.write(audio_data)
                        self.last_ai_reply = f"[Decoded base64 audio: {len(audio_data)} bytes]"
                        self.log(f"🔊 Playing back base64 audio response...")
                        play_audio(TEMP_REPLY_PATH)
                        return
                    except Exception:
                        pass

            # If JSON contains text reply (e.g. {"content": "..."})
            text_reply = data.get("content") or data.get("text") or data.get("message") or data.get("output") or ""
            if text_reply:
                self.last_ai_reply = str(text_reply).strip()
                self.log(f"🤖 AI Response: \033[1;36m{self.last_ai_reply}\033[0m")
                # Synthesize neural Malayalam speech using edge-tts
                tts_cmd = [
                    "edge-tts",
                    "--voice", "ml-IN-SobhanaNeural",
                    "--text", self.last_ai_reply,
                    "--write-media", TEMP_REPLY_PATH
                ]
                res = subprocess.run(tts_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if res.returncode == 0 and os.path.exists(TEMP_REPLY_PATH):
                    self.log(f"🔊 Synthesized Neural Malayalam Voice. Playing back to caller...")
                    play_audio(TEMP_REPLY_PATH)
        except Exception as e:
            self.log(f"⚠️ Response parsing note: {e}")

    def loop(self):
        self.log("🎙️ Call audio monitor active: waiting for active call on Redmi Note 10...")
        while self.is_running:
            # Check if call is actually in progress
            if not self.call_in_progress and not is_call_active():
                self.last_status = "idle (waiting for call)"
                time.sleep(0.5)
                continue

            self.chunk_count += 1
            self.last_chunk_time = format_timestamp()
            self.log(f"\n📞 [Active Call on Redmi Note 10 - Chunk #{self.chunk_count}] Recording 10s audio...")
            
            ok = self.record_chunk(duration=10)
            if not self.is_running:
                break
            if not ok:
                time.sleep(0.5)
                continue

            self.log("🚀 Dispatched 10s MP3 to AI Webhook (http://192.168.2.69:5678/webhook-test/passive)...")
            resp = self.send_to_webhook()
            if not self.is_running:
                break
            if resp:
                self.process_response(resp)
            else:
                self.log("⚠️ No response from n8n webhook.")

            # Pause briefly between chunks, checking if call is still active
            if not is_call_active() and not self.call_in_progress:
                self.log("📴 Call ended on Redmi Note 10. Pausing recording.")
                self.last_status = "idle (call ended)"
                time.sleep(0.5)

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False
        self.last_status = "idle (waiting for call)"
        if self.record_proc:
            try:
                self.record_proc.kill()
            except Exception:
                pass
            self.record_proc = None
        self.log("🛑 Audio conversation loop stopped (standby).")

if __name__ == "__main__":
    bridge = AudioConversationBridge()
    print("=" * 65)
    print(" RakshaNet Call-Activated Audio AI Conversation Bridge")
    print("=================================================================")
    print(" Active: ONLY DURING PHONE CALLS on Redmi Note 10")
    print(" Target: http://192.168.2.69:5678/webhook-test/passive")
    print(" Press Ctrl+C to stop.")
    print("=" * 65)
    bridge.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        bridge.stop()
        print("\nExiting.")
