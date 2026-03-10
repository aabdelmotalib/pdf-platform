"""
Redis-based session timer service for hourly plan subscribers.

This is separate from the auth Session model (which stores JWT tokens).
This service manages countdown timers and file usage counters in Redis.

Keys:
    session_timer:{user_id}  — presence key with TTL = remaining seconds
    session_files:{user_id}  — integer counter of files used in this session
"""

import os
import redis

# Module-level singleton Redis client
_redis_client: redis.Redis = redis.Redis.from_url(
    os.getenv("REDIS_URL", "redis://redis:6379/0"),
    decode_responses=True,
)


def start_session_timer(user_id: str, duration_seconds: int = 3600) -> None:
    """
    Start (or restart) an hourly session timer for a user.

    Sets two Redis keys with the same TTL so they expire together:
    - session_timer:{user_id}  = "1"
    - session_files:{user_id}  = "0"
    """
    timer_key = f"session_timer:{user_id}"
    files_key = f"session_files:{user_id}"

    _redis_client.set(timer_key, "1", ex=duration_seconds)
    _redis_client.set(files_key, "0", ex=duration_seconds)


def get_session_remaining(user_id: str) -> int:
    """
    Return the number of seconds remaining on the session timer.

    Returns:
        Positive int  — seconds remaining
        -2            — key does not exist (session expired or never started)
        -1            — key exists but has no TTL (should not happen)
    """
    return _redis_client.ttl(f"session_timer:{user_id}")


def increment_session_files(user_id: str) -> int:
    """
    Increment the session file counter and return the new count.

    Returns:
        Positive int — new file count after increment
        -1           — key does not exist (session expired)
    """
    files_key = f"session_files:{user_id}"

    if not _redis_client.exists(files_key):
        return -1

    return _redis_client.incr(files_key)


def get_session_files_used(user_id: str) -> int:
    """
    Return the number of files used in the current session.

    Returns:
        int — file count (0 if key doesn't exist)
    """
    val = _redis_client.get(f"session_files:{user_id}")
    return int(val) if val is not None else 0


def clear_session_timer(user_id: str) -> None:
    """Delete both session keys (timer + file counter)."""
    _redis_client.delete(
        f"session_timer:{user_id}",
        f"session_files:{user_id}",
    )
