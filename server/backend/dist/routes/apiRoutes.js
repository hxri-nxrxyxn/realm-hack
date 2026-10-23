"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.apiRouter = void 0;
const express_1 = require("express");
const telemetryController_js_1 = require("../controllers/telemetryController.js");
exports.apiRouter = (0, express_1.Router)();
exports.apiRouter.get("/health", (_req, res) => {
    res.json({
        status: "ok",
        service: "Rakshak Sensors Telemetry Backend",
        timestamp: Date.now(),
        uptime: process.uptime()
    });
});
exports.apiRouter.post("/telemetry", telemetryController_js_1.handlePostTelemetry);
exports.apiRouter.get("/telemetry/latest", telemetryController_js_1.handleGetLatest);
exports.apiRouter.get("/telemetry/history", telemetryController_js_1.handleGetHistory);
exports.apiRouter.get("/telemetry/alerts", telemetryController_js_1.handleGetAlerts);
exports.apiRouter.get("/devices", telemetryController_js_1.handleGetDevices);
exports.apiRouter.get("/stats", telemetryController_js_1.handleGetStats);
