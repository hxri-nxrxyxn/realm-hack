#!/usr/bin/env python3
"""
Mermaid Diagram Generator for realm-hack Monorepo.
Generates structured sequence diagrams for interactions between:
- Client (App): Hardware Sensors, Incident Detection, Default SMS Role
- Gateway (App): Bluetooth Call Auto-Responder, Quick Dialer
- Server: Python Telephony WebSocket Server, Express Backend, Speech Microservices
"""

def generate_telephony_sequence() -> str:
    """Sequence diagram for Python D-Bus Telephony monitor & Gateway auto-reply."""
    return """```mermaid
sequenceDiagram
    autonumber
    actor Caller as 📞 External Caller
    participant PW as 🎧 Linux PipeWire (D-Bus)
    participant PyServer as 🐍 Python Telephony Server (server.py)
    participant Gateway as 📱 Gateway App (Phone B)
    actor Responders as 👥 Emergency Responders

    Caller->>PW: Incoming phone call (HFP / mSBC codec)
    PW->>PyServer: D-Bus signal: org.pipewire.Telephony.CallAdded
    Note over PyServer: extract_call_number() parses LineIdentification & caller name
    PyServer->>PyServer: Check debounce window (15s throttle)
    PyServer->>Gateway: WebSocket Broadcast (port 8765): CALL_DETECTED {number, name, state}
    Note over Gateway: Svelte 5 state catches event & triggers autoSend check
    Gateway->>Gateway: DirectSmsPlugin.sendSms(number, message)
    Gateway-->>Caller: Instant automated SMS dispatch via cellular network
    Gateway->>PyServer: WebSocket confirmation: SMS_SENT {number, timestamp}
    PyServer->>Responders: Telephony event logged & ready for n8n notification
```"""

def generate_emergency_sequence() -> str:
    """Sequence diagram for sensor fall detection and edge server synchronization."""
    return """```mermaid
sequenceDiagram
    autonumber
    actor User as 🏃 Person / Device Carrier
    participant Sensors as 🧭 Hardware Sensors (5-Axis)
    participant Client as 📱 Client App (Phone A)
    participant Server as 🖥️ Server (Backend & Microservices)
    participant Gateway as 📱 Gateway App (Phone B)

    User->>Sensors: Impact / Kinematic shock event (Fall anomaly)
    Sensors->>Client: High sampling rate streams (Accel >2.5G, Gyro tilt, Stillness)
    Note over Client: sensorManager.svelte.ts evaluates threshold anomaly
    
    par Multi-Channel Alert & Ingestion
        Client->>Server: HTTP POST /api/telemetry (Accel, Gyro, Mag, Lux, Pedometer)
        Server->>Server: alertEngine checks safety thresholds & caches readings
        Server->>Server: Synthesize Malayalam voice alert (Piper TTS /speech)
        Server->>Server: Trigger n8n webhook workflow for multi-platform dispatch
    and Direct Cellular Emergency SMS
        Client->>Client: DirectSmsPlugin.sendSms(authorizedTarget, telemetrySnapshot)
        Client-->>Gateway: Encoded Emergency SMS broadcast (9495364448)
    end

    Note over Gateway: Gateway / Phone B receives distress telemetry and logs incident
```"""

def generate_default_sms_sequence() -> str:
    """Sequence diagram for Android Default SMS App role and priority alarm activation."""
    return """```mermaid
sequenceDiagram
    autonumber
    participant Cellular as 📶 Cellular Network
    participant AndroidOS as 🤖 Android OS (Telephony Provider)
    participant SmsReceiver as ⚡ SmsReceiver (Java BroadcastReceiver)
    participant MainActivity as 📱 MainActivity (Full-Screen Activity)
    participant SvelteUI as 🎨 Svelte 5 UI (/receiver route)

    Cellular->>AndroidOS: Incoming SMS payload
    AndroidOS->>SmsReceiver: Broadcast intent: SMS_DELIVER (Priority 999)
    SmsReceiver->>AndroidOS: Save SMS to telephony provider inbox
    SmsReceiver->>SmsReceiver: Verify sender matches target suffix (9495364448)

    alt Sender is Authorized Emergency Contact
        SmsReceiver->>SmsReceiver: Acquire PowerManager Full WakeLock (10s)
        SmsReceiver->>SmsReceiver: Trigger high-intensity alarm vibration waveform
        SmsReceiver->>AndroidOS: Post heads-up notification with FullScreenIntent
        SmsReceiver->>MainActivity: launchMainActivity() with FLAG_ACTIVITY_REORDER_TO_FRONT
        MainActivity->>MainActivity: unlockAndTurnOnScreen() & hideStatusBar()
        MainActivity->>SvelteUI: DefaultSmsPlugin.handleIncomingSms(sender, message)
        Note over SvelteUI: Svelte 5 runes update triggerCount & display active alert card
    else Regular Contact
        SmsReceiver->>AndroidOS: Post standard messages notification (no screen wake)
    end
```"""

def build_readme_diagrams_section() -> str:
    return f"""## System Sequence Diagrams

The interactions between **Client (App)**, **Gateway (App)**, and **Server** are coordinated via cellular SMS, local WebSockets, D-Bus IPC, and HTTP REST APIs.

### 1. Hands-Free Telephony & Auto-Responder (`server.py` & Gateway)
When an incoming call is picked up via Bluetooth hands-free audio, the Python telephony server extracts caller metadata over Linux D-Bus and coordinates with the Gateway app over WebSockets for automatic SMS response.

{generate_telephony_sequence()}

---

### 2. Emergency Incident Detection & Server Telemetry Ingestion
When kinematics detect an emergency or fall anomaly, the Client app executes multi-channel alerting: syncing full 5-axis telemetry with the backend server while dispatching an emergency SMS payload to the Gateway.

{generate_emergency_sequence()}

---

### 3. Default SMS App Role & Emergency Alarm Wake Lock
When an incoming emergency trigger is received on an Android device running the Client app with the Default SMS role, it intercepts the message at highest priority, bypasses lockscreens, and sounds vibration alarms.

{generate_default_sms_sequence()}
"""

def update_readme(readme_path: str = "README.md") -> None:
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    section_header = "## System Sequence Diagrams"
    diagrams_markdown = build_readme_diagrams_section()

    if section_header in content:
        # Replace existing section
        parts = content.split(section_header)
        # Find next section or end
        after = parts[1]
        next_section_idx = after.find("\n## ")
        if next_section_idx != -1:
            rest = after[next_section_idx:]
            new_content = parts[0].rstrip() + "\n\n" + diagrams_markdown + "\n" + rest.lstrip()
        else:
            new_content = parts[0].rstrip() + "\n\n" + diagrams_markdown
    else:
        # Insert before Quick Start
        quick_start_marker = "## Quick Start"
        if quick_start_marker in content:
            parts = content.split(quick_start_marker)
            new_content = parts[0].rstrip() + "\n\n" + diagrams_markdown + "\n---\n\n" + quick_start_marker + parts[1]
        else:
            new_content = content.rstrip() + "\n\n" + diagrams_markdown

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Successfully updated {readme_path} with sequence diagrams.")

if __name__ == "__main__":
    update_readme()
