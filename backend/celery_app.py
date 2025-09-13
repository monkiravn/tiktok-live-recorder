from __future__ import annotations

import os
from celery import Celery
from kombu import Queue

from .config import get_settings


def _create_celery() -> Celery:
    settings = get_settings()

    # Make sure `src` (TLR_ROOT) is importable for worker processes
    if settings.TLR_ROOT not in os.sys.path:
        os.sys.path.insert(0, settings.TLR_ROOT)

    app = Celery(
        "tlr_service",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=["service.tasks"],
    )

    app.conf.task_queues = (
        Queue(settings.CELERY_DEFAULT_QUEUE),
        Queue(settings.CELERY_RECORDING_QUEUE),
    )
    app.conf.task_default_queue = settings.CELERY_DEFAULT_QUEUE
    app.conf.task_track_started = True
    app.conf.worker_send_task_events = True
    app.conf.task_send_sent_event = True
    app.conf.result_expires = 24 * 3600
    app.conf.broker_heartbeat = 10
    app.conf.worker_prefetch_multiplier = 1
    app.conf.task_time_limit = 60 * 60 * 8  # 8h hard limit

    return app


celery = _create_celery()

