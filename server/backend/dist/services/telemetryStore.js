"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.telemetryStore = exports.TelemetryStore = void 0;
const alertEngine_js_1 = require("./alertEngine.js");
class TelemetryStore {
    buffer = [];
    maxBufferSize = 500;
    activeDevices = new Map();
    allAlerts = [];
    maxAlertsSize = 100;
    totalPacketsCount = 0;
    ingest(packet) {
        const now = Date.now();
        const packetWithMeta = {
            ...packet,
            id: `pkt_${now}_${Math.random().toString(36).slice(2, 7)}`,
            receivedAt: now
        };
        // Evaluate alerts
        const alerts = alertEngine_js_1.alertEngine.evaluate(packetWithMeta);
        packetWithMeta.alerts = alerts;
        if (alerts.length > 0) {
            this.allAlerts.unshift(...alerts);
            if (this.allAlerts.length > this.maxAlertsSize) {
                this.allAlerts.length = this.maxAlertsSize;
            }
        }
        // Add to ring buffer
        this.buffer.unshift(packetWithMeta);
        if (this.buffer.length > this.maxBufferSize) {
            this.buffer.length = this.maxBufferSize;
        }
        // Update active devices
        this.activeDevices.set(packet.deviceId, {
            lastSeen: now,
            platform: packet.platform,
            latestPacket: packetWithMeta
        });
        this.totalPacketsCount++;
        return { packet: packetWithMeta, newAlerts: alerts };
    }
    getLatest(deviceId) {
        if (deviceId) {
            const dev = this.activeDevices.get(deviceId);
            return dev ? dev.latestPacket : null;
        }
        return this.buffer[0] || null;
    }
    getHistory(limit = 50, deviceId) {
        const list = deviceId
            ? this.buffer.filter((p) => p.deviceId === deviceId)
            : this.buffer;
        return list.slice(0, Math.min(limit, 200));
    }
    getAlerts(limit = 20) {
        return this.allAlerts.slice(0, limit);
    }
    getDevices() {
        const list = [];
        const now = Date.now();
        for (const [id, info] of this.activeDevices.entries()) {
            list.push({
                deviceId: id,
                platform: info.platform,
                lastSeen: info.lastSeen,
                online: now - info.lastSeen < 10000 // online if seen in last 10 seconds
            });
        }
        return list;
    }
    getStats() {
        return {
            totalPacketsIngested: this.totalPacketsCount,
            activeDevicesCount: this.activeDevices.size,
            totalAlertsGenerated: this.allAlerts.length,
            bufferUtilization: `${this.buffer.length}/${this.maxBufferSize}`
        };
    }
}
exports.TelemetryStore = TelemetryStore;
exports.telemetryStore = new TelemetryStore();
