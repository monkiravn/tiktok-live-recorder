"""
Error codes and exception classes for TikTok Live Recorder API.
"""

from enum import Enum
from typing import Optional


class ErrorCode(str, Enum):
    """Standard error codes for API responses."""

    # General errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Recorder specific errors
    RECORDER_EXIT_NONZERO = "RECORDER_EXIT_NONZERO"
    FFMPEG_MISSING = "FFMPEG_MISSING"
    LIVE_OFFLINE = "LIVE_OFFLINE"
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    INVALID_URL = "INVALID_URL"
    INVALID_ROOM_ID = "INVALID_ROOM_ID"
    COOKIES_INVALID = "COOKIES_INVALID"
    PROXY_ERROR = "PROXY_ERROR"
    STORAGE_ERROR = "STORAGE_ERROR"

    # Watcher errors
    WATCHER_ALREADY_EXISTS = "WATCHER_ALREADY_EXISTS"
    WATCHER_NOT_FOUND = "WATCHER_NOT_FOUND"
    WATCHER_STOP_FAILED = "WATCHER_STOP_FAILED"

    # File/Storage errors
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    DISK_FULL = "DISK_FULL"
    S3_UPLOAD_FAILED = "S3_UPLOAD_FAILED"


class TLRAPIException(Exception):
    """Base exception for TikTok Live Recorder API."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        correlation_id: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.correlation_id = correlation_id
        self.details = details or {}
        super().__init__(message)


class RecordingException(TLRAPIException):
    """Exception raised during recording operations."""

    pass


class WatcherException(TLRAPIException):
    """Exception raised during watcher operations."""

    pass


class StorageException(TLRAPIException):
    """Exception raised during storage operations."""

    pass


def map_returncode_to_error(returncode: int) -> ErrorCode:
    """Map subprocess return code to error code."""
    error_mapping = {
        1: ErrorCode.RECORDER_EXIT_NONZERO,
        2: ErrorCode.INVALID_URL,
        3: ErrorCode.INVALID_ROOM_ID,
        4: ErrorCode.NETWORK_TIMEOUT,
        5: ErrorCode.LIVE_OFFLINE,
        127: ErrorCode.FFMPEG_MISSING,
    }
    return error_mapping.get(returncode, ErrorCode.RECORDER_EXIT_NONZERO)
