from fastapi import HTTPException 
from app.core.redis import redis_client

async def check_rate_limit(user_id: str):
    key = f'rate-limit:{user_id}'

    current_count = await redis_client.incr(key)

    if current_count == 1:
        await redis_client.expire(key, 1)

    if current_count > 10:
        raise HTTPException(
            status_code=429,
            detail="Too many requests",
            )