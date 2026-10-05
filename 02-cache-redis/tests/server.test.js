/**
 * Test Suite for Redis Caching Layer and Rate Limiter
 * Uses Node.js native assert module for zero-dependency execution.
 */

const assert = require("assert");
const CacheManager = require("../src/cacheManager");

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

async function run() {
    try {
        await testCacheManager();
        console.log("=========================================");
        console.log("All Redis module tests completed with OK.");
        console.log("=========================================");
    } catch (err) {
        console.error("Test failure:", err);
        process.exit(1);
    }
}

run();
