# realm-hack

Monorepo workspace organized into three core architecture components: **Client (App)**, **Gateway (App)**, and **Server**.

```
realm-hack/
├── client/                     # Client application (Phone A / user-facing)
│   ├── src/                    # Rakshak Sensors Svelte 5 & Capacitor app
│   ├── android/                # Native Android build for Rakshak Sensors
│   └── sample_app/             # SMS receiver & user-facing phone interface
├── gateway/                    # Gateway application (Phone B / RakshaNet)
│   ├── src/                    # Quick-dial & Bluetooth handsfree call responder
│   ├── android/                # Native Android build for RakshaNet
│   └── RakshaNet.apk           # Prebuilt APK
└── server/                     # Server backend, microservices, and listeners
    ├── backend/                # Node.js/TypeScript telemetry ingestion & WebSocket server
    ├── services/               # Microservices (e.g., Malayalam TTS via Piper)
    ├── server.py               # PipeWire Bluetooth call monitor & WebSocket broadcaster
    └── extract_call_number.py  # D-Bus telephony phone number extractor CLI
```

---

## Components

### 1. Client (`client/`)
Real-time hardware sensor detection and user-facing mobile client built with **Capacitor 7**, **Android Studio**, and **Svelte 5 (Runes mode)**.
- Tracks 5 hardware sensors (Pedometer, Gyroscope, Magnetometer/Compass, Accelerometer, Ambient Light).
- Sends emergency alerts and sensor telemetry via SMS.
- Houses [`client/sample_app/`](client/sample_app) for SMS reception and default SMS role handling.

```bash
# Run client app (web preview)
npm run dev:client

# Sync assets to Capacitor Android
npm run sync:android

# Open in Android Studio / Build APK
npm run open:android
npm run build:android
```

---

### 2. Gateway (`gateway/`)
Capacitor mobile application for quick-dialing and automated Bluetooth hands-free call responses.
- Listens to call detection events over WebSockets from the telephony server.
- Triggers automatic SMS dispatches to callers.

```bash
# Start development server
npm run dev:gateway

# Sync assets to Capacitor Android
npm run cap:sync

# Open in Android Studio
npm run cap:open
```

---

### 3. Server (`server/`)
Hosts telemetry processing, microservices, and Bluetooth telephony integrations:
- **`server/backend/`**: Node.js/TypeScript server with WebSocket streaming (`/ws`) and threshold alert engine.
- **`server/services/malayalam-tts/`**: Dockerized Malayalam Text-to-Speech service using Piper.
- **`server/server.py`**: Real-time Linux PipeWire / oFono D-Bus call monitor broadcasting detected caller IDs.
- **`server/extract_call_number.py`**: CLI utility for PipeWire telephony inspection.

```bash
# Run telemetry server backend
npm run dev:server

# Run Bluetooth call WebSocket monitor
python3 server/server.py
```
