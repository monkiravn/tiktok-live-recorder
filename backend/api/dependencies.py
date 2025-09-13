from fastapi import Depends, Header, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.core.config import get_settings


def api_key_auth(x_api_key: str | None = Header(default=None)):
    settings = get_settings()
    if not x_api_key or x_api_key not in settings.api_keys():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key",
        )
    return x_api_key


def get_correlation_id(x_correlation_id: str | None = Header(default=None)) -> str:
    # Best-effort pass-through; the app will generate one if missing
    return x_correlation_id or ""


def ratelimit_key(request):
    return request.headers.get("X-API-Key") or get_remote_address(request)


def get_limiter():
    settings = get_settings()
    return Limiter(
        key_func=ratelimit_key, default_limits=[f"{settings.RATE_LIMIT_PER_MIN}/minute"]
    )
