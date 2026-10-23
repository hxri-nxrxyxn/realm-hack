# realm-hack

Monorepo comprising three core components:

* **`client/`** — User-facing mobile app (Capacitor 7 + Svelte 5) tracking hardware sensors, sending emergency telemetry, and handling default SMS role alerts.
* **`gateway/`** — Gateway mobile app (Capacitor + SvelteKit) for automated phone call response and quick dialing.
* **`server/`** — Backend services including the telemetry ingestion server (`server/backend`), PipeWire Bluetooth telephony listeners (`server/server.py`), and Malayalam TTS microservice (`server/services/malayalam-tts`).

---

## Quick Start

### Client (App)
```bash
# Run web preview
npm run dev:client

# Build web assets
npm run build:client
```

### Gateway (App)
```bash
# Run web preview
npm run dev:gateway

# Build web assets
npm run build:gateway
```

### Server
```bash
# Run telemetry server
npm run dev:server

# Run Bluetooth telephony listener
python3 server/server.py
```
