/**
 * Resilient Cache-Aside Manager using Redis v4
 * Handles serialization, TTL, error fallback, and telemetry.
 */

class CacheManager {
    constructor(client, options = {}) {
        this.client = client;
        this.defaultTTL = options.defaultTTL || 3600; // 1 hour default
        this.stats = { hits: 0, misses: 0, errors: 0 };
    }

    get isReady() {
        return Boolean(this.client && this.client.isOpen);
    }

    async get(key) {
        if (!this.isReady) return null;
        try {
            const raw = await this.client.get(key);
            if (raw) {
                this.stats.hits++;
                return JSON.parse(raw);
            }
            this.stats.misses++;
            return null;
        } catch (err) {
            this.stats.errors++;
            console.warn(`[CacheManager] GET failed for key "${key}":`, err.message);
            return null;
        }
    }

    async set(key, value, ttl = this.defaultTTL) {
        if (!this.isReady || value === undefined) return false;
        try {
            await this.client.set(key, JSON.stringify(value), { EX: ttl });
            return true;
        } catch (err) {
            this.stats.errors++;
            console.warn(`[CacheManager] SET failed for key "${key}":`, err.message);
            return false;
        }
    }

    async del(key) {
        if (!this.isReady) return false;
        try {
            await this.client.del(key);
            return true;
        } catch (err) {
            console.warn(`[CacheManager] DEL failed for key "${key}":`, err.message);
            return false;
        }
    }

    /**
     * Cache-Aside Pattern:
     * 1. Query Redis for key.
     * 2. If present (Cache Hit), return immediately.
     * 3. If absent or Redis down (Cache Miss), invoke fallback fetcher().
     * 4. Save result in Redis with TTL and return to caller.
     */
    async getOrSet(key, fetcher, ttl = this.defaultTTL) {
        const cached = await this.get(key);
        if (cached !== null) {
            return { data: cached, source: "cache" };
        }

        const freshData = await fetcher();
        if (freshData !== null && freshData !== undefined) {
            await this.set(key, freshData, ttl);
        }

        return { data: freshData, source: "origin" };
    }

    getMetrics() {
        const total = this.stats.hits + this.stats.misses;
        const hitRate = total > 0 ? ((this.stats.hits / total) * 100).toFixed(2) + "%" : "0%";
        return { ...this.stats, totalRequests: total, hitRate };
    }
}

module.exports = CacheManager;
