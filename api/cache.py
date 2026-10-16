"""Redis cache client and hit/miss tracking.

Maintains cache hit and miss counters in Redis and provides caching decorators/helpers
for datasets.
"""

import json
from typing import Any

from redis import Redis

from api.config import settings

redis_client = Redis.from_url(settings.redis_url, decode_responses=True)

# Counter keys in Redis
HITS_KEY = "cache:hits"
MISSES_KEY = "cache:misses"


def get_cache_stats() -> dict[str, int]:
    """Return total cache hits and misses."""
    hits = int(redis_client.get(HITS_KEY) or 0)
    misses = int(redis_client.get(MISSES_KEY) or 0)
    return {"hits": hits, "misses": misses}


def incr_hit() -> None:
    redis_client.incr(HITS_KEY)


def incr_miss() -> None:
    redis_client.incr(MISSES_KEY)


def cache_get(key: str) -> Any | None:
    """Get JSON-decoded value from cache, tracking hit/miss."""
    val = redis_client.get(key)
    if val is not None:
        incr_hit()
        return json.loads(val)
    incr_miss()
    return None


def cache_set(key: str, value: Any, ttl: int = settings.cache_ttl_seconds) -> None:
    """Serialize and store value in cache with TTL."""
    redis_client.setex(key, ttl, json.dumps(value))


def invalidate_datasets_cache() -> None:
    """Clear all dataset list and detail cache keys on any write."""
    # Pattern matching keys starting with dataset:
    cursor = 0
    while True:
        cursor, keys = redis_client.scan(cursor, match="dataset:*", count=100)
        if keys:
            redis_client.delete(*keys)
        if cursor == 0:
            break
