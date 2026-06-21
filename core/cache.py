import hashlib
from cachetools import TTLCache
from core.config import settings

result_cache: TTLCache = TTLCache(maxsize=settings.CACHE_MAX_SIZE, ttl=settings.CACHE_TTL)

def make_cache_key(text: str) -> str:
    return hashlib.sha256(text.lower().strip().encode()).hexdigest()