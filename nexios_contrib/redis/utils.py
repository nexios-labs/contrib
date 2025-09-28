"""
Utility functions for Redis operations in Nexios.

This module provides convenient functions for common Redis operations
that can be used directly in Nexios route handlers.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Union

from nexios_contrib.redis import get_redis_client


async def redis_get(key: str) -> Optional[str]:
    """
    Get a value from Redis by key.

    Args:
        key: Redis key

    Returns:
        Value as string or None if key doesn't exist

    Example:
        ```python
        from nexios_contrib.redis import redis_get

        value = await redis_get("user:123")
        if value:
            print(f"User data: {value}")
        ```
    """
    redis =  get_redis_client()
    return await redis.get(key)


async def redis_set(
    key: str,
    value: Union[str, int, float],
    ex: Optional[int] = None,
    px: Optional[int] = None,
    nx: bool = False,
    xx: bool = False,
) -> bool:
    """
    Set a value in Redis with optional expiration.

    Args:
        key: Redis key
        value: Value to set
        ex: Expire time in seconds
        px: Expire time in milliseconds
        nx: Only set if key does not exist
        xx: Only set if key exists

    Returns:
        True if successful

    Example:
        ```python
        from nexios_contrib.redis import redis_set

        # Set with expiration
        await redis_set("session:abc123", "user_data", ex=3600)  # 1 hour

        # Set only if doesn't exist
        await redis_set("counter", 1, nx=True)
        ```
    """
    redis = get_redis_client()
    return await redis.set(key, value, ex=ex, px=px, nx=nx, xx=xx)


async def redis_delete(*keys: str) -> int:
    """
    Delete one or more keys from Redis.

    Args:
        *keys: Keys to delete

    Returns:
        Number of keys deleted

    Example:
        ```python
        from nexios_contrib.redis import redis_delete

        deleted = await redis_delete("user:123", "session:abc123")
        print(f"Deleted {deleted} keys")
        ```
    """
    redis = get_redis_client()
    return await redis.delete(*keys)


async def redis_exists(*keys: str) -> int:
    """
    Check how many of the specified keys exist.

    Args:
        *keys: Keys to check

    Returns:
        Number of existing keys

    Example:
        ```python
        from nexios_contrib.redis import redis_exists

        exists = await redis_exists("user:123", "user:456")
        print(f"{exists} keys exist")
        ```
    """
    redis = get_redis_client()
    return await redis.exists(*keys)


async def redis_expire(
    key: str,
    seconds: int,
    nx: bool = False,
    xx: bool = False,
    gt: bool = False,
    lt: bool = False,
) -> bool:
    """
    Set expiration on a key.

    Args:
        key: Redis key
        seconds: Expiration time in seconds
        nx: Only set if key has no expiration
        xx: Only set if key has expiration
        gt: Only set if new expiration is greater than current
        lt: Only set if new expiration is less than current

    Returns:
        True if expiration was set

    Example:
        ```python
        from nexios_contrib.redis import redis_expire

        await redis_expire("temp_data", 300)  # 5 minutes
        ```
    """
    redis = get_redis_client()
    return await redis.expire(key, seconds, nx=nx, xx=xx, gt=gt, lt=lt)


async def redis_ttl(key: str) -> int:
    """
    Get the remaining time to live of a key.

    Args:
        key: Redis key

    Returns:
        TTL in seconds (-1 if no expiration, -2 if key doesn't exist)

    Example:
        ```python
        from nexios_contrib.redis import redis_ttl

        ttl = await redis_ttl("temp_data")
        if ttl > 0:
            print(f"Key expires in {ttl} seconds")
        ```
    """
    redis = get_redis_client()
    return await redis.ttl(key)


async def redis_incr(key: str, amount: int = 1) -> int:
    """
    Increment the number stored at key by the specified amount.

    Args:
        key: Redis key
        amount: Amount to increment by (default: 1)

    Returns:
        New value after increment

    Example:
        ```python
        from nexios_contrib.redis import redis_incr

        new_value = await redis_incr("counter", 5)
        print(f"Counter is now {new_value}")
        ```
    """
    redis = get_redis_client()
    return await redis.incr(key, amount)


async def redis_decr(key: str, amount: int = 1) -> int:
    """
    Decrement the number stored at key by the specified amount.

    Args:
        key: Redis key
        amount: Amount to decrement by (default: 1)

    Returns:
        New value after decrement

    Example:
        ```python
        from nexios_contrib.redis import redis_decr

        new_value = await redis_decr("counter", 2)
        print(f"Counter is now {new_value}")
        ```
    """
    redis = get_redis_client()
    return await redis.decr(key, amount)


async def redis_json_get(key: str, path: str = ".") -> Any:
    """
    Get JSON data from Redis.

    Args:
        key: Redis key
        path: JSON path to extract (default: root)

    Returns:
        JSON data or None if key doesn't exist

    Example:
        ```python
        from nexios_contrib.redis import redis_json_get

        user = await redis_json_get("user:123")
        if user:
            print(f"User: {user['name']}")
        ```
    """
    redis = get_redis_client()
    return await redis.json_get(key, path)


async def redis_json_set(
    key: str,
    path: str,
    value: Any,
    nx: bool = False,
    xx: bool = False,
) -> bool:
    """
    Set JSON data in Redis.

    Args:
        key: Redis key
        path: JSON path to set
        value: Value to set
        nx: Only set if key does not exist
        xx: Only set if key exists

    Returns:
        True if successful

    Example:
        ```python
        from nexios_contrib.redis import redis_json_set

        user_data = {"name": "John", "age": 30}
        await redis_json_set("user:123", ".", user_data)
        ```
    """
    redis = get_redis_client()
    return await redis.json_set(key, path, value, nx=nx, xx=xx)


async def redis_hget(key: str, field: str) -> Optional[str]:
    """
    Get the value of a hash field.

    Args:
        key: Redis key
        field: Hash field name

    Returns:
        Field value or None if field doesn't exist

    Example:
        ```python
        from nexios_contrib.redis import redis_hget

        email = await redis_hget("user:123", "email")
        if email:
            print(f"User email: {email}")
        ```
    """
    redis = get_redis_client()
    return await redis.hget(key, field)


async def redis_hset(key: str, field: str, value: Union[str, int, float]) -> int:
    """
    Set the value of a hash field.

    Args:
        key: Redis key
        field: Hash field name
        value: Field value

    Returns:
        Number of fields that were added

    Example:
        ```python
        from nexios_contrib.redis import redis_hset

        await redis_hset("user:123", "name", "John Doe")
        await redis_hset("user:123", "age", 30)
        ```
    """
    redis = get_redis_client()
    return await redis.hset(key, field, value)


async def redis_hgetall(key: str) -> Dict[str, str]:
    """
    Get all fields and values in a hash.

    Args:
        key: Redis key

    Returns:
        Dictionary of all hash fields and values

    Example:
        ```python
        from nexios_contrib.redis import redis_hgetall

        user = await redis_hgetall("user:123")
        print(f"User: {user}")
        ```
    """
    redis = get_redis_client()
    return await redis.hgetall(key)


async def redis_lpush(key: str, *values: Union[str, int, float]) -> int:
    """
    Push one or more values to the front of a list.

    Args:
        key: Redis key
        *values: Values to push

    Returns:
        New length of the list

    Example:
        ```python
        from nexios_contrib.redis import redis_lpush

        length = await redis_lpush("messages", "msg1", "msg2")
        print(f"List now has {length} items")
        ```
    """
    redis = get_redis_client()
    return await redis.lpush(key, *values)


async def redis_rpush(key: str, *values: Union[str, int, float]) -> int:
    """
    Push one or more values to the end of a list.

    Args:
        key: Redis key
        *values: Values to push

    Returns:
        New length of the list

    Example:
        ```python
        from nexios_contrib.redis import redis_rpush

        length = await redis_rpush("messages", "msg1", "msg2")
        print(f"List now has {length} items")
        ```
    """
    redis = get_redis_client()
    return await redis.rpush(key, *values)


async def redis_lpop(key: str, count: Optional[int] = None) -> Union[Optional[str], List[str]]:
    """
    Remove and return the first element(s) of a list.

    Args:
        key: Redis key
        count: Number of elements to pop (default: 1)

    Returns:
        First element(s) or None/empty list

    Example:
        ```python
        from nexios_contrib.redis import redis_lpop

        message = await redis_lpop("messages")
        if message:
            print(f"Popped: {message}")
        ```
    """
    redis = get_redis_client()
    return await redis.lpop(key, count)


async def redis_rpop(key: str, count: Optional[int] = None) -> Union[Optional[str], List[str]]:
    """
    Remove and return the last element(s) of a list.

    Args:
        key: Redis key
        count: Number of elements to pop (default: 1)

    Returns:
        Last element(s) or None/empty list

    Example:
        ```python
        from nexios_contrib.redis import redis_rpop

        message = await redis_rpop("messages")
        if message:
            print(f"Popped: {message}")
        ```
    """
    redis = get_redis_client()
    return await redis.rpop(key, count)


async def redis_llen(key: str) -> int:
    """
    Get the length of a list.

    Args:
        key: Redis key

    Returns:
        Length of the list

    Example:
        ```python
        from nexios_contrib.redis import redis_llen

        length = await redis_llen("messages")
        print(f"List has {length} items")
        ```
    """
    redis = get_redis_client()
    return await redis.llen(key)


async def redis_sadd(key: str, *members: Union[str, int, float]) -> int:
    """
    Add one or more members to a set.

    Args:
        key: Redis key
        *members: Members to add

    Returns:
        Number of new members added

    Example:
        ```python
        from nexios_contrib.redis import redis_sadd

        added = await redis_sadd("tags", "python", "redis", "cache")
        print(f"Added {added} new tags")
        ```
    """
    redis = get_redis_client()
    return await redis.sadd(key, *members)


async def redis_smembers(key: str) -> List[str]:
    """
    Get all members of a set.

    Args:
        key: Redis key

    Returns:
        List of all set members

    Example:
        ```python
        from nexios_contrib.redis import redis_smembers

        tags = await redis_smembers("article:123:tags")
        print(f"Tags: {tags}")
        ```
    """
    redis = get_redis_client()
    return await redis.smembers(key)


async def redis_srem(key: str, *members: Union[str, int, float]) -> int:
    """
    Remove one or more members from a set.

    Args:
        key: Redis key
        *members: Members to remove

    Returns:
        Number of members removed

    Example:
        ```python
        from nexios_contrib.redis import redis_srem

        removed = await redis_srem("tags", "old_tag")
        print(f"Removed {removed} tags")
        ```
    """
    redis = get_redis_client()
    return await redis.srem(key, *members)


async def redis_scard(key: str) -> int:
    """
    Get the number of members in a set.

    Args:
        key: Redis key

    Returns:
        Number of members in the set

    Example:
        ```python
        from nexios_contrib.redis import redis_scard

        count = await redis_scard("tags")
        print(f"Set has {count} members")
        ```
    """
    redis = get_redis_client()
    return await redis.scard(key)


async def redis_keys(pattern: str = "*") -> List[str]:
    """
    Get all keys matching a pattern.

    Args:
        pattern: Key pattern (default: "*")

    Returns:
        List of matching keys

    Example:
        ```python
        from nexios_contrib.redis import redis_keys

        user_keys = await redis_keys("user:*")
        print(f"Found {len(user_keys)} user keys")
        ```
    """
    redis = get_redis_client()
    return await redis.keys(pattern)


async def redis_flushdb(asynchronous: bool = False) -> bool:
    """
    Delete all keys in the current database.

    Args:
        asynchronous: Whether to perform asynchronously

    Returns:
        True if successful

    Example:
        ```python
        from nexios_contrib.redis import redis_flushdb

        await redis_flushdb()
        print("All keys deleted")
        ```
    """
    redis = get_redis_client()
    return await redis.flushdb(asynchronous)


async def redis_execute(*args: Any) -> Any:
    """
    Execute a raw Redis command.

    Args:
        *args: Redis command and arguments

    Returns:
        Command result

    Example:
        ```python
        from nexios_contrib.redis import redis_execute

        # Get Redis info
        info = await redis_execute("INFO", "memory")
        print(f"Memory info: {info}")
        ```
    """
    redis = get_redis_client()
    return await redis.execute(*args)
