import logging

import redis

from app.cache import redis_client


logger = logging.getLogger(__name__)


def allow_comment(ip_address: str, limit: int = 5, window: int = 60) -> bool:
    key = f"comment_rl:{ip_address}"
    try:
        count = redis_client.incr(key)
        if count == 1:
            redis_client.expire(key, window)
        return count <= limit
    except redis.RedisError:
        logger.warning("Comment rate-limit check failed for %s", ip_address, exc_info=True)
        return True
