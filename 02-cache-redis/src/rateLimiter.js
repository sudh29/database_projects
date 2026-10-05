/**
 * Redis Sliding-Window Rate Limiter
 * Implements token/request throttling using Redis Sorted Sets (ZSET).
 */

function createRateLimiter(redisClient, options = {}) {
    const windowMs = options.windowMs || 60000; // 1 minute window
    const maxRequests = options.maxRequests || 20; // 20 requests per window

    return async function rateLimiterMiddleware(req, res, next) {
        if (!redisClient || !redisClient.isOpen) {
            // Graceful degradation: allow request if Redis is down
            return next();
        }

        const ip = req.headers["x-forwarded-for"] || req.socket.remoteAddress || "127.0.0.1";
        const key = `ratelimit:${ip}`;
        const now = Date.now();
        const clearBefore = now - windowMs;

        try {
            // Multi-command atomic pipeline
            const multi = redisClient.multi();
            multi.zRemRangeByScore(key, 0, clearBefore);
            multi.zCard(key);
            multi.zAdd(key, { score: now, value: `${now}:${Math.random()}` });
            multi.expire(key, Math.ceil(windowMs / 1000));

            const results = await multi.exec();
            const currentCount = results[1]; // Result of zCard

            res.setHeader("X-RateLimit-Limit", maxRequests);
            res.setHeader("X-RateLimit-Remaining", Math.max(0, maxRequests - (currentCount + 1)));

            if (currentCount >= maxRequests) {
                res.setHeader("Retry-After", Math.ceil(windowMs / 1000));
                return res.status(429).json({
                    error: "Too Many Requests",
                    message: `Rate limit of ${maxRequests} requests per ${windowMs / 1000}s exceeded.`,
                    retryAfterSeconds: Math.ceil(windowMs / 1000),
                });
            }

            next();
        } catch (err) {
            console.warn("[RateLimiter] Error evaluating rate limit, permitting request:", err.message);
            next();
        }
    };
}

module.exports = { createRateLimiter };
