"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.handlePostTelemetry = handlePostTelemetry;
exports.handleGetLatest = handleGetLatest;
exports.handleGetHistory = handleGetHistory;
exports.handleGetAlerts = handleGetAlerts;
exports.handleGetDevices = handleGetDevices;
exports.handleGetStats = handleGetStats;
const telemetryStore_js_1 = require("../services/telemetryStore.js");
const sensorSocket_js_1 = require("../websocket/sensorSocket.js");
function handlePostTelemetry(req, res) {
    const data = req.body;
    if (!data || !data.deviceId || !data.sensors) {
        res.status(400).json({ error: "Invalid telemetry packet format. Must include deviceId and sensors." });
        return;
    }
    const { packet, newAlerts } = telemetryStore_js_1.telemetryStore.ingest(data);
    // Broadcast to all active WebSocket dashboard clients
    (0, sensorSocket_js_1.broadcastTelemetry)(packet);
    res.status(200).json({
        success: true,
        packetId: packet.id,
        alerts: newAlerts,
        receivedAt: packet.receivedAt
    });
}
function handleGetLatest(req, res) {
    const deviceId = req.query.deviceId;
    const latest = telemetryStore_js_1.telemetryStore.getLatest(deviceId);
    if (!latest) {
        res.status(404).json({ message: "No telemetry data recorded yet." });
        return;
    }
    res.status(200).json(latest);
}
function handleGetHistory(req, res) {
    const limit = parseInt(req.query.limit || "50", 10);
    const deviceId = req.query.deviceId;
    const history = telemetryStore_js_1.telemetryStore.getHistory(limit, deviceId);
    res.status(200).json({
        count: history.length,
        packets: history
    });
}
function handleGetAlerts(req, res) {
    const limit = parseInt(req.query.limit || "20", 10);
    const alerts = telemetryStore_js_1.telemetryStore.getAlerts(limit);
    res.status(200).json({ count: alerts.length, alerts });
}
function handleGetDevices(_req, res) {
    const devices = telemetryStore_js_1.telemetryStore.getDevices();
    res.status(200).json({ count: devices.length, devices });
}
function handleGetStats(_req, res) {
    const stats = telemetryStore_js_1.telemetryStore.getStats();
    res.status(200).json(stats);
}
