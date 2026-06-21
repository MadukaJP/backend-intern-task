import logging
import time

from fastapi import APIRouter, HTTPException, Request
from starlette.responses import JSONResponse
from core.cache import make_cache_key, result_cache
from core.limiter import limiter
from core.config import settings
from schemas.classify_request import ClassifyRequest
from schemas.classify_response import ClassifyResponse
from services.groq import classify_text

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/classify", response_model=ClassifyResponse)
@limiter.limit(settings.RATE_LIMIT)
async def classify(request: Request, body: ClassifyRequest):
    if not body.text: 
        raise HTTPException(status_code=422, detail="text is required")

    cache_key = make_cache_key(body.text)

    if cache_key in result_cache:
        logger.info("cache hit for key=%s", cache_key[:8])
        return result_cache[cache_key]

    t0 = time.monotonic()
    client = getattr(request.app.state, "http_client", None)
    result = await classify_text(body.text, client=client)
    elapsed = round((time.monotonic() - t0) * 1000)

    logger.info(
        "classified | type=%s confidence=%.2f latency=%dms",
        result["type"], result["confidence"], elapsed,
    )

    result_cache[cache_key] = result
    return result