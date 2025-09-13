from fastapi import APIRouter
from starlette.responses import PlainTextResponse

from backend.core.celery_app import celery


router = APIRouter()


@router.get("/healthz")
def healthz():
    return PlainTextResponse("ok")


@router.get("/ready")
def ready():
    try:
        celery.control.ping(timeout=0.5)
        return PlainTextResponse("ready")
    except Exception as e:
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail=f"not ready: {e}")


@router.get("/metrics")
def metrics():
    from backend.utils.metrics import get_metrics
    from starlette.responses import Response

    content = get_metrics()
    return Response(content=content, media_type="text/plain")
