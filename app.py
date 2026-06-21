import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from core.limiter import limiter
from routes.classify import router as classify_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from core.config import settings
    import httpx

    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY is not set — /classify will fail at runtime")
    
    async with httpx.AsyncClient(timeout=8.0) as client:
        app.state.http_client = client
        logger.info("classify-api started")
        yield
    logger.info("classify-api shutting down")


app = FastAPI(
    title="Text Classifier API",
    description="Classifies text into: question, complaint, feedback, request, spam, or other.",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

app.include_router(classify_router)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "status": "success",
        "message": "Welcome to the Text Classifier API",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {
        "status": "success",
        "message": "The service is running",
    }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error = exc.errors()[0]
    message = error["msg"].replace("Value error, ", "")

    return JSONResponse(
        status_code=422, content={"status": "error", "message": message}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code, content={"status": "error", "message": exc.detail}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "An unexpected error occurred. Please try again later.",
        },
    )
