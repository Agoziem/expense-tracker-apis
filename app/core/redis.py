import redis.asyncio as aioredis
from typing import Any, Optional
import json

from .config import settings

DEFAULT_EXPIRY = 3600  # 

# Shared Redis instance
redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

# --- Token Blocklist (JWT JTI Blacklisting) ---
JTI_EXPIRY = 3600  # 1 hour

async def add_jti_to_blocklist(jti: str) -> None:
    await redis_client.set(name=jti, value="", ex=JTI_EXPIRY)


async def token_in_blocklist(jti: str) -> bool:
    jti = await redis_client.get(jti)

    return jti is not None


async def add_oauth_code_to_blocklist(code: str, user_id: str) -> None:
    await redis_client.set(name=code, value=user_id, ex=JTI_EXPIRY)


async def oauth_code_in_blocklist(code: str) -> Optional[str]:
    user_id = await redis_client.get(code)
    if user_id:
        await redis_client.delete(code)
        return user_id
    return None



# --- General Cache Utilities ---

async def set_cache(key: str, value: Any, expiry: int = DEFAULT_EXPIRY) -> None:
    # Convert complex data to JSON string
    serialized = json.dumps(value)
    await redis_client.set(name=key, value=serialized, ex=expiry)

async def get_cache(key: str) -> Optional[Any]:
    value = await redis_client.get(key)
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value

async def invalidate_cache(key: str) -> None:
    await redis_client.delete(key)
