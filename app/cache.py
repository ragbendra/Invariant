import logging

import redis

from app.config import REDIS_URL


logger = logging.getLogger(__name__)
redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=0.2,
    socket_timeout=0.2,
)


def _post_key(slug: str) -> str:
    return f"post:{slug}:html"


def get_cached_post(slug: str) -> str | None:
    try:
        cached = redis_client.get(_post_key(slug))
    except redis.RedisError:
        logger.warning("Redis cache read failed for post %s", slug, exc_info=True)
        return None

    if cached is not None:
        logger.info("Redis cache hit for post %s", slug)
    else:
        logger.info("Redis cache miss for post %s", slug)
    return cached


def set_cached_post(slug: str, html: str, ttl: int | None = None) -> None:
    try:
        if ttl is None:
            redis_client.set(_post_key(slug), html)
        else:
            redis_client.setex(_post_key(slug), ttl, html)
    except redis.RedisError:
        logger.warning("Redis cache write failed for post %s", slug, exc_info=True)


def invalidate_post(slug: str) -> None:
    try:
        redis_client.delete(_post_key(slug))
    except redis.RedisError:
        logger.warning("Redis cache invalidation failed for post %s", slug, exc_info=True)
