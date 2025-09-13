from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, Optional

from celery import current_task
from celery.utils.log import get_task_logger

from backend.core.celery_app import celery
from backend.core.config import get_settings
from backend.utils.helpers import load_cookies_from_path, run_recording
from backend.core.exceptions import (
    ErrorCode,
    map_returncode_to_error,
    RecordingException,
)
from backend.utils.logging import set_task_context, get_logger


log = get_logger(__name__)


def _result_payload(**kwargs) -> Dict[str, Any]:
    """Create standardized result payload with error mapping."""
    returncode = kwargs.get("returncode", 0)
    error_code = kwargs.get("error_code")

    # Map return code to error code if not provided
    if returncode != 0 and not error_code:
        error_code = map_returncode_to_error(returncode)

    out = {
        "returncode": returncode,
        "files": kwargs.get("files", []),
        "s3": kwargs.get("s3", []),
        "started_at": kwargs.get("started_at"),
        "ended_at": kwargs.get("ended_at"),
        "error_code": error_code.value if error_code else None,
        "error_message": kwargs.get("error_message"),
    }
    return out


@celery.task(bind=True, name="record_once", queue=get_settings().CELERY_RECORDING_QUEUE)
def record_once(
    self,
    *,
    room_id: Optional[str] = None,
    url: Optional[str] = None,
    duration: Optional[int] = None,
    output_template: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    settings = get_settings()
    task_id = self.request.id

    # Set logging context
    set_task_context(task_id, room_id, url)

    started_at = datetime.utcnow().isoformat()

    try:
        proxy = (options or {}).get("proxy")
        cookies_path = (options or {}).get("cookies")
        cookies = load_cookies_from_path(cookies_path) if cookies_path else None

        output_dir = settings.RECORDINGS_DIR
        os.makedirs(output_dir, exist_ok=True)

        log.info(
            "Recording task started",
            extra={
                "task_id": task_id,
                "room_id": room_id,
                "url": url,
                "duration": duration,
                "output_dir": output_dir,
            },
        )

        rc, created = run_recording(
            url=url,
            room_id=room_id,
            duration=duration,
            output_dir=output_dir,
            proxy=proxy,
            cookies=cookies,
        )

        ended_at = datetime.utcnow().isoformat()

        # Handle S3 upload if enabled
        s3_results = []
        if (options or {}).get("upload_s3", False) and created:
            try:
                from backend.services.s3_client import get_s3_uploader

                uploader = get_s3_uploader()
                if uploader.is_enabled():
                    s3_prefix = f"{room_id or 'unknown'}/{datetime.utcnow().strftime('%Y/%m/%d')}"
                    s3_results = uploader.upload_files(created, s3_prefix)
                    log.info(
                        "S3 upload completed",
                        extra={"task_id": task_id, "uploaded_files": len(s3_results)},
                    )
            except Exception as e:
                log.error(
                    "S3 upload failed", extra={"task_id": task_id, "error": str(e)}
                )
                # Don't fail the task if S3 upload fails

        if rc == 0:
            log.info(
                "Recording task completed successfully",
                extra={
                    "task_id": task_id,
                    "files_created": len(created),
                    "files": created,
                    "s3_uploads": len(s3_results),
                },
            )
        else:
            error_code = map_returncode_to_error(rc)
            log.error(
                "Recording task failed",
                extra={
                    "task_id": task_id,
                    "returncode": rc,
                    "error_code": error_code.value,
                },
            )

        return _result_payload(
            returncode=rc,
            files=created,
            s3=s3_results,
            started_at=started_at,
            ended_at=ended_at,
        )

    except Exception as e:
        ended_at = datetime.utcnow().isoformat()
        log.exception(
            "Recording task failed with exception",
            extra={
                "task_id": task_id,
            },
        )
        return _result_payload(
            returncode=1,
            files=[],
            started_at=started_at,
            ended_at=ended_at,
            error_code=ErrorCode.INTERNAL_ERROR,
            error_message=str(e),
        )
