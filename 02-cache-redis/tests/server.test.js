/**
 * Test Suite for Redis Caching Layer and Rate Limiter
 * Uses Node.js native assert module for zero-dependency execution.
 */

const assert = require("assert");
const CacheManager = require("../src/cacheManager");
const { createRateLimiter } = require("../src/rateLimiter");

async function testCacheManager() {
    console.log("Running CacheManager tests...");

    // Mock Redis Client in memory
    const store = new Map();
    const mockRedisClient = {
        isOpen: true,
        async get(k) {
            return store.get(k) || null;
        },
        async set(k, v) {
            store.set(k, v);
            return "OK";
        },
        async del(k) {
            return store.delete(k) ? 1 : 0;
        },
    };

    const cache = new CacheManager(mockRedisClient, { defaultTTL: 60 });

    // 1. Initial Miss
    let originFetchCount = 0;
    const fetcher = async () => {
        originFetchCount++;
        return { id: 1, title: "Test Photo" };
    };

    const res1 = await cache.getOrSet("photos:1", fetcher);
    assert.strictEqual(res1.source, "origin");
    assert.strictEqual(res1.data.id, 1);
    assert.strictEqual(originFetchCount, 1);

    // 2. Cache Hit on second call
    const res2 = await cache.getOrSet("photos:1", fetcher);
    assert.strictEqual(res2.source, "cache");
    assert.strictEqual(res2.data.id, 1);
    assert.strictEqual(originFetchCount, 1, "Fetcher should NOT have been called on cache hit");

    // 3. Verify Metrics
    const metrics = cache.getMetrics();
    assert.strictEqual(metrics.hits, 1);
    assert.strictEqual(metrics.misses, 1);
    assert.strictEqual(metrics.hitRate, "50.00%");

    // 4. Invalidation
    await cache.del("photos:1");
    const res3 = await cache.getOrSet("photos:1", fetcher);
    assert.strictEqual(res3.source, "origin");
    assert.strictEqual(originFetchCount, 2);

    // 5. Graceful Degradation (Client Offline)
    mockRedisClient.isOpen = false;
    const resOffline = await cache.getOrSet("photos:1", fetcher);
    assert.strictEqual(resOffline.source, "origin");
    assert.strictEqual(originFetchCount, 3, "Fetcher should execute directly when Redis is offline");

    console.log("✔ All CacheManager tests passed successfully!\n");
}

async function testRateLimiter() {
    console.log("Running RateLimiter tests...");

    function createMockRedis(isOpen = true) {
        let items = [];
        return {
            isOpen,
            multi() {
                let countBeforeAdd = 0;
                return {
                    zRemRangeByScore(key, min, max) {
                        items = items.filter(ts => ts > max);
                        return this;
                    },
                    zCard(key) {
                        countBeforeAdd = items.length;
                        return this;
                    },
                    zAdd(key, obj) {
                        items.push(obj.score);
                        return this;
                    },
                    expire(key, sec) {
                        return this;
                    },
                    async exec() {
                        return [1, countBeforeAdd, 1, 1];
                    }
                };
            }
        };
    }

    function createMockReqRes() {
        const headers = {};
        let statusCode = 200;
        let jsonBody = null;
        let nextCalled = false;

        const req = {
            headers: { "x-forwarded-for": "192.168.1.100" },
            socket: { remoteAddress: "192.168.1.100" }
        };

        const res = {
            setHeader(k, v) {
                headers[k] = v;
            },
            status(code) {
                statusCode = code;
                return this;
            },
            json(body) {
                jsonBody = body;
                return this;
            }
        };

        const next = () => {
            nextCalled = true;
        };

        return { req, res, headers, getStatus: () => statusCode, getBody: () => jsonBody, isNext: () => nextCalled, next };
    }

    const mockRedis = createMockRedis(true);
    const limiter = createRateLimiter(mockRedis, { windowMs: 60000, maxRequests: 2 });

    // Request 1: should pass
    const ctx1 = createMockReqRes();
    await limiter(ctx1.req, ctx1.res, ctx1.next);
    assert.strictEqual(ctx1.isNext(), true, "Request 1 should call next()");
    assert.strictEqual(ctx1.headers["X-RateLimit-Limit"], 2);
    assert.strictEqual(ctx1.headers["X-RateLimit-Remaining"], 1);

    // Request 2: should pass
    const ctx2 = createMockReqRes();
    await limiter(ctx2.req, ctx2.res, ctx2.next);
    assert.strictEqual(ctx2.isNext(), true, "Request 2 should call next()");
    assert.strictEqual(ctx2.headers["X-RateLimit-Remaining"], 0);

    // Request 3: should be rate-limited (429)
    const ctx3 = createMockReqRes();
    await limiter(ctx3.req, ctx3.res, ctx3.next);
    assert.strictEqual(ctx3.isNext(), false, "Request 3 should NOT call next() on 429");
    assert.strictEqual(ctx3.getStatus(), 429, "Status should be 429 Too Many Requests");
    assert.strictEqual(ctx3.headers["Retry-After"], 60);
    assert.strictEqual(ctx3.getBody().error, "Too Many Requests");

    // Graceful degradation when Redis is offline
    const offlineRedis = createMockRedis(false);
    const offlineLimiter = createRateLimiter(offlineRedis, { windowMs: 60000, maxRequests: 2 });
    const ctxOffline = createMockReqRes();
    await offlineLimiter(ctxOffline.req, ctxOffline.res, ctxOffline.next);
    assert.strictEqual(ctxOffline.isNext(), true, "Offline Redis should gracefully allow request via next()");

    console.log("✔ All RateLimiter tests passed successfully!\n");
}

async function run() {
    try {
        await testCacheManager();
        await testRateLimiter();
        console.log("=========================================");
        console.log("All Redis module tests completed with OK.");
        console.log("=========================================");
    } catch (err) {
        console.error("Test failure:", err);
        process.exit(1);
    }
}

run();
