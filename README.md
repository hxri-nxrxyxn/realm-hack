# realm-hack

Monorepo / project workspace for the hackathon.

## Projects

### 1. Rakshak Sensors (`frontend/` & `backend/`)
A real-time hardware sensor detection application and telemetry platform built with **Capacitor 7**, **Android Studio**, **Svelte 5 (Runes mode)**, and **shadcn-svelte**.

The app tracks and renders live telemetry for **5 physical hardware sensors**:
1. **Pedometer**: Step counter, step detector, estimated walking distance (km), and calories burned (kcal).
2. **Gyroscope**: 3-axis angular velocity ($\text{rad/s}$ and $\text{deg/s}$) across Pitch (X), Roll (Y), and Yaw (Z).
3. **Magnetometer**: Geomagnetic field strength ($\mu\text{T}$), microtesla flux along X, Y, Z, and dynamic 360° rotating digital compass with cardinal directions (N, NE, E, SE, S, SW, W, NW).
4. **Accelerometer**: 3-axis linear and gravity acceleration ($m/s^2$), total G-force magnitude, and dynamic force meters.
5. **Ambient Light Sensor**: Real-time illuminance in Lux ($\text{lx}$) with environment classification (Dark, Indoor, Office, Daylight, Direct Sunlight).

#### Architecture
- **Front Page (`/`)**: Displays Compass, Pedometer, and Light Meter directly below the enlarged menu bar, plus an interactive 4×1 preview matrix linking to the full suite.
- **Full Suite Route (`/sensors`)**: Dedicated page with all 5 hardware sensors and hardware diagnostic details.
- **Backend Service (`backend/`)**: Real-time telemetry ingestion, WebSocket broadcast (`ws://localhost:3001/ws`), and threshold anomaly alert engine.
- **Single Master Control**: One high-visibility "Start Sensors" / "Stop Sensors" button at the end of each view.

```bash
# Run sensor frontend (web preview)
npm run dev:frontend

# Run telemetry backend
npm run dev:backend

# Open sensor Android project in Android Studio
npm run open:android

# Build sensor Android APK
npm run build:android
```

---

### 2. RakshaNet (`rakshanet/`)
Capacitor quick-dial mobile & web app featuring a custom phone dialer with placeholder `9995283835` and one-tap calling / Bluetooth handsfree integration.

```bash
# Start development server
npm run dev

# Sync assets to Capacitor Android
npm run cap:sync

# Open in Android Studio
npm run cap:open
```
