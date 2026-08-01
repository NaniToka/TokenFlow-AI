import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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
    allow_origins=settings.cors_origins if settings.cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy", "service": "TokenFlow AI", "version": "1.0.0"}


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


# Single-Container SPA Static Asset Mounting
base_dir = os.path.dirname(os.path.abspath(__file__))
possible_static_dirs = [
    os.path.join(base_dir, "..", "static"),
    os.path.join(base_dir, "..", "..", "frontend", "dist"),
]

static_dir = None
for candidate in possible_static_dirs:
    if os.path.exists(candidate) and os.path.isdir(candidate):
        static_dir = os.path.abspath(candidate)
        break

if static_dir:
    assets_dir = os.path.join(static_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    index_file = os.path.join(static_dir, "index.html")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path == "health":
            raise HTTPException(status_code=404, detail="API route not found.")
        
        file_path = os.path.join(static_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        
        if os.path.exists(index_file):
            return FileResponse(index_file)
        
        raise HTTPException(status_code=404, detail="Frontend asset not found.")
