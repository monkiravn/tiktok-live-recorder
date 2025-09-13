import os
import uuid
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse, PlainTextResponse, Response

from .auth import api_key_auth
from .config import get_settings
from .logging_config import setup_logging, get_logger
from .middleware import RequestContextMiddleware
from .models import (
    CreateRecordingRequest,
    CreateWatcherRequest,
    FileInfo,
    FilesQuery,
    FilesResponse,
    JobRef,
    JobResult,
    JobStatusResponse,
    OkResponse,
)
from .celery_app import celery
from .storage import RedisStorage
from .utils import list_recording_files, paginate, to_fileinfo
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    multiprocess,
    generate_latest,
)


# Setup logging first
setup_logging()
logger = get_logger(__name__)

settings = get_settings()
app = FastAPI(title="TikTok Live Recorder API", version="1.0.0")

# Add request context middleware
app.add_middleware(RequestContextMiddleware)


# Rate limit: use API key as key when available, fallback to client IP
def ratelimit_key(request):
    return request.headers.get("X-API-Key") or get_remote_address(request)


limiter = Limiter(key_func=ratelimit_key, default_limits=[f"{settings.RATE_LIMIT_PER_MIN}/minute"])  # type: ignore
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


if settings.CORS_ALLOW_ORIGINS:
    origins = [o.strip() for o in settings.CORS_ALLOW_ORIGINS.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/healthz")
def healthz():
    return PlainTextResponse("ok")


@app.get("/ready")
def ready():
    try:
        celery.control.ping(timeout=0.5)
        return PlainTextResponse("ready")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"not ready: {e}")


@app.get("/metrics")
def metrics():
    from .metrics import get_metrics
    from starlette.responses import Response

    content = get_metrics()
    return Response(content=content, media_type="text/plain")


@app.post("/recordings", response_model=JobRef)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MIN}/minute")
def create_recording(
    request: Request, req: CreateRecordingRequest, api_key: str = Depends(api_key_auth)
):
    from .security import sanitize_recording_request

    if not req.room_id and not req.url:
        raise HTTPException(status_code=400, detail="Provide at least room_id or url")

    # Sanitize inputs
    sanitized = sanitize_recording_request(
        room_id=req.room_id,
        url=req.url,
        duration=req.duration,
        proxy=req.options.proxy,
        cookies=req.options.cookies,
        output_template=req.output_template,
    )

    t = celery.send_task(
        "record_once",
        kwargs={
            "room_id": sanitized["room_id"],
            "url": sanitized["url"],
            "duration": sanitized["duration"],
            "output_template": sanitized["output_template"],
            "options": {
                "upload_s3": req.options.upload_s3,
                "proxy": sanitized["proxy"],
                "cookies": sanitized["cookies"],
            },
        },
        queue=settings.CELERY_RECORDING_QUEUE,
    )
    return JobRef(task_id=t.id, status=t.status or "PENDING")


@app.get("/jobs/{task_id}", response_model=JobStatusResponse)
def job_status(task_id: str, api_key: str = Depends(api_key_auth)):
    res = celery.AsyncResult(task_id)
    status = res.status
    payload = None
    if res.ready():
        r = res.result
        if isinstance(r, dict):
            payload = JobResult(**r)
    return JobStatusResponse(task_id=task_id, status=status, result=payload)


@app.post("/watchers", response_model=JobRef)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MIN}/minute")
def create_watcher(
    request: Request, req: CreateWatcherRequest, api_key: str = Depends(api_key_auth)
):
    from .security import sanitize_watcher_request

    if not req.room_id and not req.url:
        raise HTTPException(status_code=400, detail="Provide at least room_id or url")

    # Sanitize inputs
    sanitized = sanitize_watcher_request(
        room_id=req.room_id,
        url=req.url,
        poll_interval=req.poll_interval,
        proxy=req.options.proxy,
        cookies=req.options.cookies,
    )

    key = sanitized["room_id"] or sanitized["url"]
    store = RedisStorage()
    existing = store.get_watcher(key)
    if existing:
        raise HTTPException(status_code=409, detail="Watcher already exists")

    t = celery.send_task(
        "watch_and_record",
        kwargs={
            "key": key,
            "room_id": sanitized["room_id"],
            "url": sanitized["url"],
            "poll_interval": sanitized["poll_interval"],
            "options": {
                "upload_s3": req.options.upload_s3,
                "proxy": sanitized["proxy"],
                "cookies": sanitized["cookies"],
            },
        },
        queue=settings.CELERY_DEFAULT_QUEUE,
    )
    store.set_watcher(key, t.id)
    return JobRef(task_id=t.id, status=t.status or "PENDING")


@app.delete("/watchers/{key}", response_model=OkResponse)
def delete_watcher(key: str, api_key: str = Depends(api_key_auth)):
    store = RedisStorage()
    task_id = store.get_watcher(key)
    if not task_id:
        raise HTTPException(status_code=404, detail="Watcher not found")

    try:
        celery.control.revoke(task_id, terminate=True, signal="SIGTERM")
    except Exception:
        pass
    store.del_watcher(key)
    return OkResponse(ok=True)


@app.get("/files", response_model=FilesResponse)
def list_files(
    api_key: str = Depends(api_key_auth),
    room_id: Optional[str] = Query(default=None),
    url: Optional[str] = Query(default=None),
    from_ts: Optional[float] = Query(default=None, alias="from"),
    to_ts: Optional[float] = Query(default=None, alias="to"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    # Basic listing; filtering by room_id/url depends on naming templates.
    # For now, we filter by simple substring match if provided.
    all_files = list_recording_files(
        settings.RECORDINGS_DIR, ts_from=from_ts, ts_to=to_ts
    )
    if room_id:
        all_files = [p for p in all_files if room_id in os.path.basename(p)]
    if url:
        # We don't embed URL into filename; ignore or future-enhance with index.
        pass

    all_files.sort(key=lambda p: os.stat(p).st_mtime, reverse=True)
    total = len(all_files)
    page_items = paginate(all_files, page, page_size)
    items = [FileInfo(**to_fileinfo(p)) for p in page_items]
    return FilesResponse(page=page, page_size=page_size, total=total, items=items)
