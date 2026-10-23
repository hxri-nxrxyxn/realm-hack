"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.setupWebSocketServer = setupWebSocketServer;
exports.broadcastTelemetry = broadcastTelemetry;
const ws_1 = require("ws");
const telemetryStore_js_1 = require("../services/telemetryStore.js");
let wss = null;
const clients = new Set();
function setupWebSocketServer(server) {
    wss = new ws_1.WebSocketServer({ server, path: "/ws" });
    wss.on("connection", (ws) => {
        clients.add(ws);
        // Send latest available packet immediately upon connection
        const latest = telemetryStore_js_1.telemetryStore.getLatest();
        if (latest) {
            ws.send(JSON.stringify({ type: "INITIAL_STATE", data: latest }));
        }
        ws.on("message", (message) => {
            try {
                const parsed = JSON.parse(message.toString());
                if (parsed.type === "TELEMETRY" && parsed.data) {
                    const { packet } = telemetryStore_js_1.telemetryStore.ingest(parsed.data);
                    broadcastTelemetry(packet);
                }
            }
            catch {
                // Ignore unparseable frames
            }
        });
        ws.on("close", () => {
            clients.delete(ws);
        });
        ws.on("error", () => {
            clients.delete(ws);
        });
    });
    return wss;
}
function broadcastTelemetry(packet) {
    if (!wss || clients.size === 0)
        return;
    const payload = JSON.stringify({
        type: "TELEMETRY_UPDATE",
        data: packet
    });
    for (const client of clients) {
        if (client.readyState === ws_1.WebSocket.OPEN) {
            client.send(payload);
        }
    }
}
