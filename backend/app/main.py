import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.schemas import CompressRequest, CompressResponse
from app.services.assembler import process_compression
from app.services.stats_logger import stats_tracker

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_PER_MINUTE])

app = FastAPI(
    title="TokenFlow AI API",
    description="Production-grade Prompt Memory Optimizer Middleware API",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "TokenFlow AI"}


@app.post("/api/v1/compress", response_model=CompressResponse)
@limiter.limit(settings.RATE_LIMIT_PER_MINUTE)
def compress_prompt(request: Request, body: CompressRequest):
    """
    Compresses conversation history and user query into an optimized, high-retention prompt.
    Processes request strictly in-memory without persisting any user data.
    """
    try:
        if not body.current_message or not body.current_message.strip():
            raise HTTPException(status_code=400, detail="current_message parameter cannot be empty.")
        
        return process_compression(body)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing prompt compression pipeline: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred while compressing the prompt."
        )


@app.get("/api/v1/stats")
def get_session_stats():
    """
    Returns cumulative session analytics and request history breakdown.
    """
    return stats_tracker.get_stats()


@app.post("/api/v1/stats/reset")
def reset_session_stats():
    """
    Resets all in-memory session statistics and history logs.
    """
    stats_tracker.reset_stats()
    return {"status": "success", "message": "Session statistics reset successfully."}


# Mount Static Files for Production Container SPA Deployment
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
