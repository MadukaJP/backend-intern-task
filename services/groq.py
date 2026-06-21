import json
import logging

import httpx
from fastapi import HTTPException

from core.config import settings, VALID_LABELS, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


async def classify_text(text: str, client: httpx.AsyncClient = None) -> dict:
    if not settings.GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="Classifier backend not configured")

    payload = {
        "model": settings.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": text},
        ],
        "temperature": 0,
        "max_tokens": 60,
    }

    try:
        if client is not None:
            resp = await client.post(
                settings.GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type":  "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
        else:
            async with httpx.AsyncClient(timeout=8.0) as local_client:
                resp = await local_client.post(
                    settings.GROQ_API_URL,
                    headers={
                        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                        "Content-Type":  "application/json",
                    },
                    json=payload,
                )
                resp.raise_for_status()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Classifier timed out")
    except httpx.HTTPStatusError as e:
        logger.error("Groq API error: %s", e.response.text)
        raise HTTPException(status_code=502, detail="Classifier backend error")

    raw = resp.json()["choices"][0]["message"]["content"].strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("Non-JSON response from model: %r", raw)
        return {"type": "other", "confidence": 0.5}

    if result.get("type") not in VALID_LABELS:
        result["type"] = "other"

    raw_confidence = float(result.get("confidence", 0.5))
    clamped = max(0.0, min(1.0, raw_confidence))
    result["confidence"] = round(clamped, 4)

    return result