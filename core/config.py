from typing import Literal
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")

    ENV: Literal["development", "staging", "production"] = "development"

    GROQ_API_KEY: str
    GROQ_API_URL: str = "https://api.groq.com/openai/v1/chat/completions"
    GROQ_MODEL:   str = "llama-3.1-8b-instant"

    CACHE_MAX_SIZE: int = 1024
    CACHE_TTL:      int = 3600  # seconds

    # Rate limiting
    RATE_LIMIT: str = "120/minute"


settings = Settings()

VALID_LABELS = {"question", "complaint", "feedback", "request", "spam", "other"}

SYSTEM_PROMPT = """You are a precise text classifier. Given any user input, respond ONLY with a valid JSON object — no explanation, no markdown, no extra text.

Classify the input into exactly one of these labels:
- question   → the user is asking something / seeking information
- complaint  → the user is expressing dissatisfaction or reporting a problem
- feedback   → the user is giving an opinion, review, or suggestion
- request    → the user is asking for an action to be taken
- spam       → irrelevant, promotional, or nonsensical content
- other      → none of the above apply clearly

Respond ONLY with this exact format:
{"type": "<label>", "confidence": <float between 0.0 and 1.0>}

confidence reflects how certain you are of the classification."""