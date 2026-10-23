"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const http_1 = __importDefault(require("http"));
const cors_1 = __importDefault(require("cors"));
const dotenv_1 = __importDefault(require("dotenv"));
const apiRoutes_js_1 = require("./routes/apiRoutes.js");
const sensorSocket_js_1 = require("./websocket/sensorSocket.js");
dotenv_1.default.config();
const app = (0, express_1.default)();
const port = process.env.PORT || 3001;
// Middlewares
app.use((0, cors_1.default)());
app.use(express_1.default.json({ limit: "5mb" }));
// Routes
app.use("/api", apiRoutes_js_1.apiRouter);
// Root route
app.get("/", (_req, res) => {
    res.json({
        name: "Rakshak Sensors Telemetry Backend",
        version: "1.0.0",
        endpoints: {
            health: "/api/health",
            ingestTelemetry: "POST /api/telemetry",
            latestTelemetry: "GET /api/telemetry/latest",
            telemetryHistory: "GET /api/telemetry/history",
            alerts: "GET /api/telemetry/alerts",
            devices: "GET /api/devices",
            stats: "GET /api/stats",
            webSocket: "/ws"
        }
    });
});
const server = http_1.default.createServer(app);
// Setup WebSocket server
(0, sensorSocket_js_1.setupWebSocketServer)(server);
server.listen(port, () => {
    console.log(`[Rakshak Sensors Backend] Server listening on port ${port}`);
    console.log(`[WebSocket] Live stream available at ws://localhost:${port}/ws`);
});
