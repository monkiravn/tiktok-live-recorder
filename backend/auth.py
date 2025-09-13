from fastapi import Depends, Header, HTTPException, status
from .config import get_settings


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

