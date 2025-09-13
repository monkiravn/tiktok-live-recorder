from __future__ import annotations

import time
import signal
from typing import Any, Dict, Optional

from backend.core.celery_app import celery
from backend.core.config import get_settings
from backend.utils.helpers import (
    load_cookies_from_path,
    run_recording,
    ensure_tlr_on_path,
)
from backend.utils.logging import set_task_context, get_logger
from backend.services.process_manager import register_process, cleanup_task_processes


log = get_logger(__name__)


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
