from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, Optional

from celery import current_task
from celery.utils.log import get_task_logger

from .celery_app import celery
from .config import get_settings
from .utils import load_cookies_from_path, run_recording
from .exceptions import ErrorCode, map_returncode_to_error, RecordingException
from .logging_config import set_task_context, get_logger


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
                from .s3_client import get_s3_uploader

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


@celery.task(
    bind=True, name="watch_and_record", queue=get_settings().CELERY_DEFAULT_QUEUE
)
def watch_and_record(
    self,
    *,
    key: str,
    room_id: Optional[str] = None,
    url: Optional[str] = None,
    poll_interval: int = 60,
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Lightweight watcher: polls liveness and, if live, runs record_once inline.

    Enhanced with proper signal handling and cancellation checks.
    """
    import time
    import signal
    from .process_manager import register_process, cleanup_task_processes

    settings = get_settings()
    task_id = self.request.id
    proxy = (options or {}).get("proxy")
    cookies_path = (options or {}).get("cookies")
    cookies = load_cookies_from_path(cookies_path) if cookies_path else None

    # Set logging context
    set_task_context(task_id, room_id, url)

    # Setup signal handler for graceful shutdown
    def signal_handler(signum, frame):
        log.info(
            "Watcher received shutdown signal",
            extra={"task_id": task_id, "signal": signum},
        )
        cleanup_task_processes(task_id)
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Import here to avoid overhead for non-watcher tasks
    from .utils import ensure_tlr_on_path

    ensure_tlr_on_path()
    from core.tiktok_api import TikTokAPI

    api = TikTokAPI(proxy=proxy, cookies=cookies)

    log.info(
        "Watcher task started",
        extra={"task_id": task_id, "key": key, "poll_interval": poll_interval},
    )

    consecutive_errors = 0
    max_consecutive_errors = 5

    try:
        while True:
            # Check if task was revoked
            if self.is_aborted():
                log.info("Watcher task was aborted", extra={"task_id": task_id})
                break

            try:
                # resolve room_id
                rid = room_id
                if url and not rid:
                    _, rid = api.get_room_and_user_from_url(url)
                if not rid:
                    time.sleep(poll_interval)
                    continue

                if api.is_room_alive(rid):
                    log.info(
                        "Live stream detected, starting recording",
                        extra={"task_id": task_id, "room_id": rid},
                    )

                    # one-shot recording with default duration=None (until offline/stop)
                    rc, created = run_recording(
                        url=url,
                        room_id=rid,
                        duration=None,
                        output_dir=settings.RECORDINGS_DIR,
                        proxy=proxy,
                        cookies=cookies,
                    )

                    log.info(
                        "Watcher recording completed",
                        extra={"task_id": task_id, "files": created, "returncode": rc},
                    )

                # Reset error counter on success
                consecutive_errors = 0
                time.sleep(poll_interval)

            except Exception as e:
                consecutive_errors += 1
                backoff_time = min(300, poll_interval * (2**consecutive_errors))

                log.error(
                    "Watcher loop error",
                    extra={
                        "task_id": task_id,
                        "consecutive_errors": consecutive_errors,
                        "backoff_time": backoff_time,
                        "error": str(e),
                    },
                )

                # Exit if too many consecutive errors
                if consecutive_errors >= max_consecutive_errors:
                    log.error(
                        "Too many consecutive errors, terminating watcher",
                        extra={
                            "task_id": task_id,
                            "consecutive_errors": consecutive_errors,
                        },
                    )
                    return {"ok": False, "error": "Too many consecutive errors"}

                time.sleep(backoff_time)

    except (SystemExit, KeyboardInterrupt):
        log.info("Watcher task interrupted", extra={"task_id": task_id})
    except Exception as e:
        log.exception("Watcher fatal error", extra={"task_id": task_id})
        raise
    finally:
        cleanup_task_processes(task_id)

    return {"ok": True}
