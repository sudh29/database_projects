/**
 * Modern Redis-Cached Express Server
 * Demonstrates Cache-Aside, Rate Limiting, and Resilient Fallback.
 */

const express = require("express");
const axios = require("axios");
const cors = require("cors");
const Redis = require("redis");
const CacheManager = require("./cacheManager");
const { createRateLimiter } = require("./rateLimiter");

const app = express();
const PORT = process.env.PORT || 3001;
const REDIS_URL = process.env.REDIS_URL || "redis://localhost:6379";
const DEFAULT_EXP = parseInt(process.env.CACHE_TTL || "3600", 10);

// Initialize Redis v4 client
const redisClient = Redis.createClient({ url: REDIS_URL });

redisClient.on("error", (err) => {
    console.error("[Redis Client Error]:", err.message);
});

redisClient.on("reconnecting", () => {
    console.log("[Redis] Reconnecting to server...");
});

redisClient.on("connect", () => {
    console.log("[Redis] Connected to server successfully.");
});

const cacheManager = new CacheManager(redisClient, { defaultTTL: DEFAULT_EXP });

app.use(cors());
app.use(express.json());

// Apply sliding-window rate limiter
app.use(createRateLimiter(redisClient, { windowMs: 60000, maxRequests: 60 }));

// Health & Telemetry
app.get("/health", (req, res) => {
    res.json({
        status: "healthy",
        redisConnected: redisClient.isOpen,
        cacheMetrics: cacheManager.getMetrics(),
    });
});

app.get("/metrics", (req, res) => {
    res.json(cacheManager.getMetrics());
});

// Cache Invalidation Endpoint
app.delete("/cache", async (req, res) => {
    const { key } = req.query;
    if (!key) {
        return res.status(400).json({ error: "Missing required query parameter: key" });
    }
    const success = await cacheManager.del(key);
    res.json({ success, deletedKey: key });
});

// GET /photos (All or filtered by albumId)
app.get("/photos", async (req, res) => {
    try {
        const { albumId } = req.query;
        const cacheKey = albumId ? `photos?albumId=${albumId}` : "photos:all";

        const { data, source } = await cacheManager.getOrSet(cacheKey, async () => {
            const config = albumId ? { params: { albumId } } : {};
            const response = await axios.get("https://jsonplaceholder.typicode.com/photos", config);
            return response.data;
        });

        res.setHeader("X-Cache-Source", source);
        res.json(data);
    } catch (err) {
        console.error("Error in GET /photos:", err.message);
        res.status(err.response?.status || 500).json({ error: err.message });
    }
});

// GET /photos/:id (Individual photo)
app.get("/photos/:id", async (req, res) => {
    try {
        const { id } = req.params;
        const cacheKey = `photos:${id}`;

        const { data, source } = await cacheManager.getOrSet(cacheKey, async () => {
            const response = await axios.get(`https://jsonplaceholder.typicode.com/photos/${id}`);
            return response.data;
        });

        res.setHeader("X-Cache-Source", source);
        res.json(data);
    } catch (err) {
        console.error(`Error in GET /photos/${req.params.id}:`, err.message);
        res.status(err.response?.status || 500).json({ error: err.message });
    }
});

async function startServer() {
    try {
        await redisClient.connect();
        console.log(`[Redis] Client connected to ${REDIS_URL}`);
    } catch (err) {
        console.warn("[Redis] Warning: Initial connection failed. Operating in cache-bypass fallback mode.");
    }

    const server = app.listen(PORT, () => {
        console.log(`[Cached Server] Listening on http://localhost:${PORT}`);
    });

    const shutdown = async () => {
        console.log("\n[Server] Graceful shutdown initiated...");
        server.close(async () => {
            if (redisClient.isOpen) {
                await redisClient.quit();
                console.log("[Redis] Client disconnected.");
            }
            process.exit(0);
        });
    };

    process.on("SIGINT", shutdown);
    process.on("SIGTERM", shutdown);
}

if (require.main === module) {
    startServer();
}

module.exports = { app, redisClient, cacheManager };
