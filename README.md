# Rakshak Sensors

A real-time hardware sensor detection application and telemetry platform built with **Capacitor 7**, **Android Studio**, **Svelte 5 (Runes mode)**, and **shadcn-svelte**.

The app tracks and renders live telemetry for **5 physical hardware sensors**:
1. **Pedometer**: Step counter, step detector, estimated walking distance (km), and calories burned (kcal).
2. **Gyroscope**: 3-axis angular velocity ($\text{rad/s}$ and $\text{deg/s}$) across Pitch (X), Roll (Y), and Yaw (Z).
3. **Magnetometer**: Geomagnetic field strength ($\mu\text{T}$), microtesla flux along X, Y, Z, and dynamic 360° rotating digital compass with cardinal directions (N, NE, E, SE, S, SW, W, NW).
4. **Accelerometer**: 3-axis linear and gravity acceleration ($m/s^2$), total G-force magnitude, and dynamic force meters.
5. **Ambient Light Sensor**: Real-time illuminance in Lux ($\text{lx}$) with environment classification (Dark, Indoor, Office, Daylight, Direct Sunlight).

---

## Project Structure

```
rakshak-net/
├── frontend/                     # Svelte 5 + Capacitor Android App
│   ├── android/                  # Android Studio Project
│   │   ├── app/src/main/java/net/rakshak/sensors/
│   │   │   ├── MainActivity.java
│   │   │   └── RakshakSensorsPlugin.java   # Native Android Sensor Manager Bridge
│   │   └── app/src/main/AndroidManifest.xml
│   ├── src/
│   │   ├── lib/
│   │   │   ├── components/       # Sensor Cards & Sparkline charts
│   │   │   │   ├── PedometerCard.svelte
│   │   │   │   ├── AccelerometerCard.svelte
│   │   │   │   ├── GyroscopeCard.svelte
│   │   │   │   ├── MagnetometerCard.svelte
│   │   │   │   ├── AmbientLightCard.svelte
│   │   │   │   └── Sparkline.svelte
│   │   │   │   └── ui/           # shadcn-svelte components (Card, Badge, Button, Tabs, etc.)
│   │   │   ├── services/
│   │   │   │   └── sensorManager.svelte.ts # Svelte 5 reactive sensor state & bridge
│   │   │   └── types/
│   │   │       └── sensor.ts
│   │   └── routes/
│   │       ├── +page.svelte      # Main Live Detection Dashboard
│   │       ├── +layout.svelte
│   │       └── layout.css        # Tailwind CSS + shadcn theme
│   ├── capacitor.config.ts
│   └── package.json
│
├── backend/                      # Telemetry & WebSocket Ingestion Server
│   ├── src/
│   │   ├── controllers/
│   │   ├── services/
│   │   │   ├── alertEngine.ts    # Anomaly, impact, and threshold detection
│   │   │   └── telemetryStore.ts # In-memory telemetry buffer & metrics
│   │   ├── routes/
│   │   ├── websocket/
│   │   │   └── sensorSocket.ts   # Real-time WebSocket broadcasting (/ws)
│   │   ├── types/
│   │   └── server.ts
│   └── package.json
│
└── package.json                  # Root orchestration scripts
```

---

## Quick Start

### 1. Run the Frontend (Web Preview)
```bash
npm run dev:frontend
```
Open [http://localhost:5173](http://localhost:5173). In a browser, the app utilizes DeviceMotion / simulated telemetry so you can interact with all 5 sensors immediately.

### 2. Run the Backend Server
```bash
npm run dev:backend
```
The backend server runs on `http://localhost:3001` with:
- `GET /api/health` - Health check
- `POST /api/telemetry` - Ingest sensor telemetry packets
- `GET /api/telemetry/latest` - Latest readings
- `GET /api/telemetry/history` - Historical time series
- `GET /api/telemetry/alerts` - Anomaly alerts
- `ws://localhost:3001/ws` - Live WebSocket broadcast stream

---

## Android Studio & Capacitor

### Open in Android Studio
You can launch the Android project directly in Android Studio:
```bash
npm run open:android
```
Or open the `/home/athira/rakshak-net/frontend/android` folder directly in Android Studio.

### Build Android APK via CLI
```bash
npm run build:android
```
The compiled debug APK is located at:
`frontend/android/app/build/outputs/apk/debug/app-debug.apk`

---

## Native Android Sensor Bridge Architecture

The native bridge is implemented in `RakshakSensorsPlugin.java` using Android's native `SensorManager`:
- `Sensor.TYPE_ACCELEROMETER`
- `Sensor.TYPE_GYROSCOPE`
- `Sensor.TYPE_MAGNETIC_FIELD`
- `Sensor.TYPE_LIGHT`
- `Sensor.TYPE_STEP_COUNTER` & `Sensor.TYPE_STEP_DETECTOR` (with runtime `android.permission.ACTIVITY_RECOGNITION` permission handling)
- Automatic software step detection fallback for hardware lacking dedicated step detector chips.
