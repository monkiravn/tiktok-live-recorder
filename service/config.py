import os
from functools import lru_cache
from typing import List, Optional


class Settings:
    """Runtime configuration loaded from environment.

    Defaults are reasonable for local development.
    """

    # Celery / Redis
    CELERY_BROKER_URL: str = os.environ.get(
        "CELERY_BROKER_URL", "redis://localhost:6379/0"
    )
    CELERY_RESULT_BACKEND: str = os.environ.get(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/1"
    )

    # Paths
    BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    TLR_ROOT: str = os.environ.get("TLR_ROOT", os.path.join(BASE_DIR, "src"))
    RECORDINGS_DIR: str = os.environ.get(
        "RECORDINGS_DIR", os.path.join(BASE_DIR, "recordings")
    )

    # API
    API_KEYS_RAW: str = os.environ.get("API_KEYS", "dev-key")
    RATE_LIMIT_PER_MIN: int = int(os.environ.get("RATE_LIMIT_PER_MIN", "60"))
    CORS_ALLOW_ORIGINS: str = os.environ.get("CORS_ALLOW_ORIGINS", "")

    # Optional S3
    S3_BUCKET: Optional[str] = os.environ.get("S3_BUCKET")
    S3_ENDPOINT_URL: Optional[str] = os.environ.get("S3_ENDPOINT_URL")
    AWS_ACCESS_KEY_ID: Optional[str] = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: Optional[str] = os.environ.get("AWS_REGION")

    # Observability
    PROMETHEUS_ENABLED: bool = (
        os.environ.get("PROMETHEUS_ENABLED", "true").lower() == "true"
    )

    # Queues
    CELERY_DEFAULT_QUEUE: str = "default"
    CELERY_RECORDING_QUEUE: str = "recording"

    def api_keys(self) -> List[str]:
        return [k.strip() for k in self.API_KEYS_RAW.split(",") if k.strip()]


@lru_cache()
def get_settings() -> Settings:
    s = Settings()
    # Ensure folders exist
    os.makedirs(s.RECORDINGS_DIR, exist_ok=True)
    return s
