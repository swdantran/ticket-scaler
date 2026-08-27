from fastapi import HTTPException

from app.core.redis import redis_client


MAX_ACTIVE_REQUESTS = 50
WINDOW_SECONDS = 2


async def check_admission():
    key = "admission:active"

    current_count = await redis_client.incr(key)

    if current_count == 1:
        await redis_client.expire(key, WINDOW_SECONDS)

    if current_count > MAX_ACTIVE_REQUESTS:
        raise HTTPException(
            status_code=503,
            detail="System is busy. Please retry shortly.",
        )