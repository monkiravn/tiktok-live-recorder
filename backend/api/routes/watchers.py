from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter

from backend.api.dependencies import api_key_auth, get_limiter
from backend.core.config import get_settings
from backend.core.security import sanitize_watcher_request
from backend.core.celery_app import celery
from backend.models.requests import CreateWatcherRequest
from backend.models.responses import JobRef, OkResponse
from backend.services.storage import RedisStorage


router = APIRouter()
limiter = get_limiter()


@router.post("/watchers", response_model=JobRef)
@limiter.limit(f"{get_settings().RATE_LIMIT_PER_MIN}/minute")
def create_watcher(
    request: Request,
    req: CreateWatcherRequest,
    api_key: str = Depends(api_key_auth),
):

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

    settings = get_settings()
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


@router.delete("/watchers/{key}", response_model=OkResponse)
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
