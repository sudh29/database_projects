/**
 * Cache Performance Benchmark
 * Compares latency between Direct Upstream API calls and Redis In-Memory Cache Hits.
 */

const axios = require("axios");

const BASE_URL = process.env.API_URL || "http://localhost:3001";
const SAMPLES = 10;

async function measureRequest(url) {
    const start = process.hrtime.bigint();
    const response = await axios.get(url);
    const end = process.hrtime.bigint();
    const durationMs = Number(end - start) / 1e6;
    const source = response.headers["x-cache-source"] || "upstream";
    return { durationMs, source };
}

async function runBenchmark() {
    console.log("=================================================");
    console.log(`Starting Redis Cache Benchmark against ${BASE_URL}`);
    console.log("=================================================\n");

    try {
        // Clear cache for clean benchmark run
        try {
            await axios.delete(`${BASE_URL}/cache?key=photos:1`);
        } catch (_) {}

        console.log(`Executing ${SAMPLES} sequential requests for /photos/1 ...\n`);

        const latencies = [];
        for (let i = 1; i <= SAMPLES; i++) {
            const { durationMs, source } = await measureRequest(`${BASE_URL}/photos/1`);
            latencies.push({ run: i, durationMs: durationMs.toFixed(2), source });
            console.log(`Run #${i}: ${durationMs.toFixed(2)} ms [Source: ${source}]`);
        }

        const miss = latencies.find((l) => l.source === "origin") || latencies[0];
        const hits = latencies.filter((l) => l.source === "cache");

        const avgHitMs = hits.length > 0 
            ? hits.reduce((acc, h) => acc + parseFloat(h.durationMs), 0) / hits.length 
            : 0;

        console.log("\n================ Summary ================");
        console.log(`Cache Miss (Origin Fetch):   ${miss.durationMs} ms`);
        console.log(`Average Cache Hit (Redis):  ${avgHitMs.toFixed(2)} ms`);
        if (avgHitMs > 0) {
            const speedup = (parseFloat(miss.durationMs) / avgHitMs).toFixed(1);
            console.log(`Performance Improvement:     ${speedup}x FASTER with Redis!`);
        }
        console.log("=========================================\n");
    } catch (err) {
        console.error("Benchmark failed. Ensure server_redis.js is running:", err.message);
    }
}

if (require.main === module) {
    runBenchmark();
}

module.exports = { runBenchmark };
