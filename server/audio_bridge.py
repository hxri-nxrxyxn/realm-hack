#!/usr/bin/env python3
"""
RakshaNet Real-Time Audio Conversation Bridge
=============================================
1. Records 10-second audio segments from Bluetooth phone audio / system mic.
2. Encodes to MP3 with ffmpeg.
3. Dispatches to n8n AI webhook:
   curl -X POST http://192.168.2.69:5678/webhook-test/passive -F "data=@record.mp3"
   (Falls back to /webhook/passive if test mode is inactive).
4. Handles response:
   - If MP3 binary: plays directly on laptop + Bluetooth phone audio.
   - If JSON text: synthesizes neural Malayalam speech with edge-tts and plays.
5. Plays back on laptop speakers and Bluetooth phone call output for two-way conversation.
"""

import os
import sys
import time
import json
import shutil
import threading
import subprocess
from datetime import datetime
import requests

PRIMARY_WEBHOOK_URL = "http://192.168.2.69:5678/webhook-test/passive"
FALLBACK_WEBHOOK_URL = "http://192.168.2.69:5678/webhook/passive"
TEMP_RECORD_PATH = "/tmp/record.mp3"
TEMP_REPLY_PATH = "/tmp/caller_reply.mp3"

def format_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
        self.thread = None
        self.chunk_count = 0
        self.last_status = "idle"
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
                    "last_reply": self.last_ai_reply,
                    "timestamp": format_timestamp()
                })
            except Exception:
                pass

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
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
                    # Test webhook not active, fallback to production
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
        self.log("🎙️ Real-time Audio Conversation loop started (10s segments)")
        while self.is_running:
            self.chunk_count += 1
            self.last_chunk_time = format_timestamp()
            self.log(f"\n--- [Audio Chunk #{self.chunk_count}] Recording 10 seconds ---")
            
            ok = self.record_chunk(duration=10)
            if not self.is_running:
                break
            if not ok:
                self.log("⚠️ Recording failed or audio empty. Retrying in 1s...")
                time.sleep(1)
                continue

            self.log("🚀 Dispatched 10s MP3 to AI Webhook (http://192.168.2.69:5678/webhook-test/passive)...")
            resp = self.send_to_webhook()
            if not self.is_running:
                break
            if resp:
                self.process_response(resp)
            else:
                self.log("⚠️ No response from n8n webhook.")

            # Tiny pause between cycles
            time.sleep(0.5)

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False
        self.last_status = "stopped"
        self.log("🛑 Audio conversation loop stopped.")

if __name__ == "__main__":
    bridge = AudioConversationBridge()
    print("=" * 65)
    print(" RakshaNet Real-Time Audio AI Conversation Bridge")
    print("=================================================================")
    print(" Target: http://192.168.2.69:5678/webhook-test/passive")
    print(" Chunks: 10 seconds -> ffmpeg mp3 -> curl POST -> laptop playback")
    print(" Press Ctrl+C to stop.")
    print("=" * 65)
    bridge.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        bridge.stop()
        print("\nExiting.")
