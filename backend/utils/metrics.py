"""
Enhanced Prometheus metrics for TikTok Live Recorder API.
"""

import os
import shutil
import time
from typing import Dict, Any
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Info,
    CollectorRegistry,
    generate_latest,
)

from backend.core.config import get_settings
from backend.services.storage import RedisStorage
from backend.utils.logging import get_logger


logger = get_logger(__name__)

# Create custom registry for multiprocess support
registry = CollectorRegistry()

# Task metrics
celery_tasks_total = Counter(
    "celery_tasks_total",
    "Total number of Celery tasks by status",
    ["task_name", "status"],
    registry=registry,
)

recordings_total = Counter(
    "recordings_total",
    "Total number of recordings by status",
    ["status"],
    registry=registry,
)

recordings_duration = Histogram(
    "recordings_duration_seconds",
    "Duration of recording tasks in seconds",
    registry=registry,
)

# Watcher metrics
watchers_active = Gauge(
    "watchers_active", "Number of active watchers", registry=registry
)

watchers_total = Counter(
    "watchers_total",
    "Total number of watchers created/deleted",
    ["action"],
    registry=registry,
)

# Storage metrics
disk_free_bytes = Gauge(
    "disk_free_bytes", "Free disk space in bytes", ["path"], registry=registry
)

disk_total_bytes = Gauge(
    "disk_total_bytes", "Total disk space in bytes", ["path"], registry=registry
)

# File metrics
recording_files_total = Gauge(
    "recording_files_total", "Total number of recording files", registry=registry
)

recording_files_size_bytes = Gauge(
    "recording_files_size_bytes",
    "Total size of recording files in bytes",
    registry=registry,
)

# S3 metrics
s3_uploads_total = Counter(
    "s3_uploads_total",
    "Total number of S3 uploads by status",
    ["status"],
    registry=registry,
)

s3_upload_duration = Histogram(
    "s3_upload_duration_seconds", "Duration of S3 uploads in seconds", registry=registry
)

# API metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests by endpoint and status",
    ["method", "endpoint", "status_code"],
    registry=registry,
)

http_request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    registry=registry,
)

# Service info
service_info = Info("service_info", "Service information", registry=registry)


class MetricsCollector:
    """Collects and updates metrics."""

    def __init__(self):
        self.settings = get_settings()
        self.storage = RedisStorage()

        # Set service info
        service_info.info(
            {
                "version": "1.0.0",
                "service": "tiktok-live-recorder-api",
                "recordings_dir": self.settings.RECORDINGS_DIR,
            }
        )

    def update_disk_metrics(self):
        """Update disk usage metrics."""
        try:
            path = self.settings.RECORDINGS_DIR
            if os.path.exists(path):
                stat = shutil.disk_usage(path)
                disk_total_bytes.labels(path=path).set(stat.total)
                disk_free_bytes.labels(path=path).set(stat.free)
        except Exception as e:
            logger.error("Failed to update disk metrics", extra={"error": str(e)})

    def update_watcher_metrics(self):
        """Update watcher metrics."""
        try:
            watchers = self.storage.list_watchers()
            watchers_active.set(len(watchers))
        except Exception as e:
            logger.error("Failed to update watcher metrics", extra={"error": str(e)})

    def update_file_metrics(self):
        """Update recording file metrics."""
        try:
            from backend.utils.helpers import list_recording_files

            files = list_recording_files(self.settings.RECORDINGS_DIR)
            recording_files_total.set(len(files))

            total_size = 0
            for file_path in files:
                try:
                    total_size += os.path.getsize(file_path)
                except (OSError, IOError):
                    continue

            recording_files_size_bytes.set(total_size)

        except Exception as e:
            logger.error("Failed to update file metrics", extra={"error": str(e)})

    def update_all_metrics(self):
        """Update all collectible metrics."""
        self.update_disk_metrics()
        self.update_watcher_metrics()
        self.update_file_metrics()


# Global collector instance
_collector = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector."""
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector


# Metric increment functions for use in other modules
def increment_task_counter(task_name: str, status: str):
    """Increment task counter metric."""
    celery_tasks_total.labels(task_name=task_name, status=status).inc()


def increment_recording_counter(status: str):
    """Increment recording counter metric."""
    recordings_total.labels(status=status).inc()


def observe_recording_duration(duration: float):
    """Observe recording duration metric."""
    recordings_duration.observe(duration)


def increment_watcher_counter(action: str):
    """Increment watcher counter metric."""
    watchers_total.labels(action=action).inc()


def increment_s3_upload_counter(status: str):
    """Increment S3 upload counter metric."""
    s3_uploads_total.labels(status=status).inc()


def observe_s3_upload_duration(duration: float):
    """Observe S3 upload duration metric."""
    s3_upload_duration.observe(duration)


def increment_http_request_counter(method: str, endpoint: str, status_code: int):
    """Increment HTTP request counter metric."""
    http_requests_total.labels(
        method=method, endpoint=endpoint, status_code=status_code
    ).inc()


def observe_http_request_duration(method: str, endpoint: str, duration: float):
    """Observe HTTP request duration metric."""
    http_request_duration.labels(method=method, endpoint=endpoint).observe(duration)


def get_metrics() -> str:
    """Get current metrics in Prometheus format."""
    # Update dynamic metrics
    collector = get_metrics_collector()
    collector.update_all_metrics()

    # Generate metrics
    return generate_latest(registry)
