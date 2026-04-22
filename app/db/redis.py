import os
from redis.asyncio import Redis

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)

async def get_redis():
    redis = Redis(
        host=REDIS_HOST, 
        port=int(REDIS_PORT), 
        decode_responses=True
    )
    try:
        yield redis
    finally:
        await redis.close()