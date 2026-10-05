/**
 * Redis Core Data Structures Showcase
 * Demonstrates: Strings, Hashes, Lists, Sets, Sorted Sets, and Bitmaps.
 */

const Redis = require("redis");

async function runDataStructuresDemo() {
    const client = Redis.createClient({ url: process.env.REDIS_URL || "redis://localhost:6379" });
    client.on("error", (err) => console.error("Redis Error:", err.message));

    try {
        await client.connect();
        console.log("=== Connected to Redis for Data Structures Demo ===\n");

        // 1. Strings (Simple caching & atomic counters)
        console.log("--- 1. Strings & Atomic Counters ---");
        await client.set("system:status", "operational", { EX: 60 });
        await client.incr("page:views:home");
        await client.incrBy("page:views:home", 4);
        const views = await client.get("page:views:home");
        console.log(`Page views count (atomic INCR): ${views}\n`);

        // 2. Hashes (Object representation)
        console.log("--- 2. Hashes (Objects / Profiles) ---");
        await client.hSet("user:101", {
            username: "johndoe",
            email: "john@example.com",
            role: "admin",
            loginCount: "1",
        });
        await client.hIncrBy("user:101", "loginCount", 1);
        const userProfile = await client.hGetAll("user:101");
        console.log("Stored user hash:", userProfile);
        console.log();

        // 3. Lists (Queues & Feeds)
        console.log("--- 3. Lists (Queue / Recent Activity) ---");
        await client.del("feed:notifications");
        await client.lPush("feed:notifications", "Notification 1: New sign-up");
        await client.lPush("feed:notifications", "Notification 2: Payment received");
        await client.lPush("feed:notifications", "Notification 3: Password changed");
        const latestNotifications = await client.lRange("feed:notifications", 0, -1);
        console.log("Recent notifications (LIFO stack):", latestNotifications);
        console.log();

        // 4. Sets (Unique membership & Set intersections)
        console.log("--- 4. Sets (Tags & Intersections) ---");
        await client.sAdd("user:101:skills", ["postgresql", "redis", "docker"]);
        await client.sAdd("job:backend:skills", ["postgresql", "redis", "kubernetes", "golang"]);
        const matchingSkills = await client.sInter(["user:101:skills", "job:backend:skills"]);
        console.log("Matching skills between candidate and job (SINTER):", matchingSkills);
        console.log();

        // 5. Sorted Sets (ZSET - Leaderboards & Priority Queues)
        console.log("--- 5. Sorted Sets (Real-time Leaderboard) ---");
        await client.del("leaderboard:gaming");
        await client.zAdd("leaderboard:gaming", [
            { score: 1540, value: "PlayerAlice" },
            { score: 2890, value: "PlayerBob" },
            { score: 2100, value: "PlayerCharlie" },
            { score: 3200, value: "PlayerDavid" },
        ]);
        // Retrieve top 3 players with scores
        const topPlayers = await client.zRangeWithScores("leaderboard:gaming", 0, 2, { REV: true });
        console.log("Top 3 Players Leaderboard (ZREVRANGE):");
        topPlayers.forEach((p, idx) => console.log(`  #${idx + 1}: ${p.value} - ${p.score} pts`));
        console.log();

        // 6. Bitmaps (Hyper-efficient Daily Active Users / DAU)
        console.log("--- 6. Bitmaps (Daily Active Users tracking) ---");
        const today = "2026-10-05";
        await client.setBit(`dau:${today}`, 101, 1); // User 101 active
        await client.setBit(`dau:${today}`, 205, 1); // User 205 active
        await client.setBit(`dau:${today}`, 309, 1); // User 309 active
        const dauCount = await client.bitCount(`dau:${today}`);
        console.log(`Daily Active Users for ${today} (BITCOUNT): ${dauCount} active users\n`);

        console.log("=== Demo completed successfully. ===");
    } catch (err) {
        console.error("Demo failed:", err);
    } finally {
        if (client.isOpen) await client.quit();
    }
}

if (require.main === module) {
    runDataStructuresDemo();
}

module.exports = { runDataStructuresDemo };
