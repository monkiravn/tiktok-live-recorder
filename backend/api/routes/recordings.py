from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter

from backend.api.dependencies import api_key_auth, get_limiter
from backend.core.config import get_settings
from backend.core.security import sanitize_recording_request
from backend.core.celery_app import celery
from backend.models.requests import CreateRecordingRequest
from backend.models.responses import JobRef


router = APIRouter()
limiter = get_limiter()


@router.post("/recordings", response_model=JobRef)
@limiter.limit(f"{get_settings().RATE_LIMIT_PER_MIN}/minute")
def create_recording(
    request: Request,
    req: CreateRecordingRequest,
    api_key: str = Depends(api_key_auth),
):

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

    settings = get_settings()
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
