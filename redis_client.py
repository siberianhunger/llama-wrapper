import aioredis
import json
import os

from logger import logger


redis_pool = aioredis.from_url(
    f'redis://{os.environ.get("redis_host") or "localhost"}',
    password=os.environ.get("redis_password") or 'pepe123',
    port=6379,
    decode_responses=True
)


async def get_cached_messages(key: str) -> list[dict] | None:
    try:
        raw_data = await redis_pool.get(key)
        if raw_data:
            logger.info(f'get_cached_messages {raw_data}')
            return json.loads(raw_data)
    except Exception as exc:
        logger.info(f"Exception while trying to get cached msgs for key: {key} exc: {exc}")
        return


async def set_messages_in_cache(key: str, raw_data: list[dict]) -> None:
    try:
        data = json.dumps(raw_data)
        await redis_pool.set(key, data, ex=20 * 60)
    except Exception as exc:
        logger.info(f"Exception while trying to set cached msgs for key: {key} exc: {exc}")
