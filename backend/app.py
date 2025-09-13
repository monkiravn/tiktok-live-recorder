from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

from backend.core.config import get_settings
from backend.utils.logging import setup_logging, get_logger
from backend.utils.middleware import RequestContextMiddleware
from backend.api.dependencies import ratelimit_key
from backend.api.routes import health, recordings, watchers, jobs, files

# Setup logging first
setup_logging()
logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(title="TikTok Live Recorder API", version="1.0.0")

    # Add request context middleware
    app.add_middleware(RequestContextMiddleware)

    # Setup rate limiter
    limiter = Limiter(
        key_func=ratelimit_key, default_limits=[f"{settings.RATE_LIMIT_PER_MIN}/minute"]
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # Setup CORS if configured
    if settings.CORS_ALLOW_ORIGINS:
        origins = [
            o.strip() for o in settings.CORS_ALLOW_ORIGINS.split(",") if o.strip()
        ]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Include all route modules
    app.include_router(health.router, tags=["Health"])
    app.include_router(recordings.router, tags=["Recordings"])
    app.include_router(watchers.router, tags=["Watchers"])
    app.include_router(jobs.router, tags=["Jobs"])
    app.include_router(files.router, tags=["Files"])

    logger.info("FastAPI application created successfully")
    return app


# Create the app instance
app = create_app()
