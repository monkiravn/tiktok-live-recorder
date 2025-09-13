"""
Custom middleware for request tracking and logging.
"""

import time
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .logging_config import (
    generate_correlation_id,
    set_correlation_id,
    get_correlation_id,
    clear_context,
    get_logger,
)
from .exceptions import TLRAPIException, ErrorCode


logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to track request context and add correlation IDs."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # Generate or extract correlation ID
        correlation_id = (
            request.headers.get("X-Correlation-ID") or generate_correlation_id()
        )
        set_correlation_id(correlation_id)

        # Start timing
        start_time = time.time()

        # Log request start
        logger.info(
            "Request started",
            extra={
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("User-Agent"),
            },
        )

        # Track metrics
        from .metrics import (
            increment_http_request_counter,
            observe_http_request_duration,
        )

        endpoint = request.url.path

        try:
            # Process request
            response = await call_next(request)

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            # Calculate duration
            duration = time.time() - start_time

            # Track metrics
            increment_http_request_counter(
                request.method, endpoint, response.status_code
            )
            observe_http_request_duration(request.method, endpoint, duration)

            # Log request completion
            logger.info(
                "Request completed",
                extra={
                    "method": request.method,
                    "url": str(request.url),
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                },
            )

            return response

        except TLRAPIException as e:
            # Handle known API exceptions
            duration = time.time() - start_time

            logger.error(
                "Request failed with API exception",
                extra={
                    "method": request.method,
                    "url": str(request.url),
                    "error_code": e.error_code,
                    "error_message": e.message,
                    "duration_ms": round(duration * 1000, 2),
                },
            )

            return JSONResponse(
                status_code=400,
                content={
                    "error_code": e.error_code,
                    "message": e.message,
                    "details": e.details,
                    "correlation_id": correlation_id,
                },
                headers={"X-Correlation-ID": correlation_id},
            )

        except Exception as e:
            # Handle unexpected exceptions
            duration = time.time() - start_time

            logger.exception(
                "Request failed with unexpected exception",
                extra={
                    "method": request.method,
                    "url": str(request.url),
                    "duration_ms": round(duration * 1000, 2),
                },
            )

            return JSONResponse(
                status_code=500,
                content={
                    "error_code": ErrorCode.INTERNAL_ERROR,
                    "message": "Internal server error",
                    "correlation_id": correlation_id,
                },
                headers={"X-Correlation-ID": correlation_id},
            )

        finally:
            # Clear context after request
            clear_context()
