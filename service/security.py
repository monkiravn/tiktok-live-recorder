"""
Security validators and input sanitization for TikTok Live Recorder API.
"""

import re
import urllib.parse
from typing import Optional

from .exceptions import TLRAPIException, ErrorCode


# URL validation patterns
TIKTOK_URL_PATTERN = re.compile(
    r"^https?://(www\.)?(tiktok\.com|vm\.tiktok\.com|m\.tiktok\.com)/.+", re.IGNORECASE
)

ROOM_ID_PATTERN = re.compile(r"^\d{1,20}$")

# Proxy URL pattern (http/https/socks5)
PROXY_PATTERN = re.compile(
    r"^(https?|socks5)://[^\s@]+@?[^\s:]+:\d{1,5}$", re.IGNORECASE
)

# File path sanitization
SAFE_PATH_PATTERN = re.compile(r"^[a-zA-Z0-9._/-]+$")


class SecurityValidator:
    """Security validator for input sanitization."""

    @staticmethod
    def validate_room_id(room_id: Optional[str]) -> Optional[str]:
        """Validate and sanitize room_id."""
        if not room_id:
            return None

        room_id = room_id.strip()
        if not room_id:
            return None

        if not ROOM_ID_PATTERN.match(room_id):
            raise TLRAPIException(
                "Invalid room_id format. Must be numeric string up to 20 digits.",
                ErrorCode.INVALID_ROOM_ID,
                details={"room_id": room_id[:50]},  # Limit in error message
            )

        return room_id

    @staticmethod
    def validate_url(url: Optional[str]) -> Optional[str]:
        """Validate and sanitize TikTok URL."""
        if not url:
            return None

        url = url.strip()
        if not url:
            return None

        # Basic URL validation
        try:
            parsed = urllib.parse.urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL format")
        except Exception:
            raise TLRAPIException(
                "Invalid URL format", ErrorCode.INVALID_URL, details={"url": url[:100]}
            )

        # Check if it's a TikTok URL
        if not TIKTOK_URL_PATTERN.match(url):
            raise TLRAPIException(
                "URL must be a valid TikTok domain (tiktok.com, vm.tiktok.com, m.tiktok.com)",
                ErrorCode.INVALID_URL,
                details={"url": url[:100]},
            )

        # Additional security: limit URL length
        if len(url) > 500:
            raise TLRAPIException(
                "URL too long. Maximum 500 characters allowed.", ErrorCode.INVALID_URL
            )

        return url

    @staticmethod
    def validate_proxy(proxy: Optional[str]) -> Optional[str]:
        """Validate and sanitize proxy URL."""
        if not proxy:
            return None

        proxy = proxy.strip()
        if not proxy:
            return None

        if not PROXY_PATTERN.match(proxy):
            raise TLRAPIException(
                "Invalid proxy format. Must be http://host:port, https://host:port, or socks5://host:port",
                ErrorCode.PROXY_ERROR,
                details={"proxy": proxy[:50]},
            )

        # Limit proxy URL length
        if len(proxy) > 200:
            raise TLRAPIException(
                "Proxy URL too long. Maximum 200 characters allowed.",
                ErrorCode.PROXY_ERROR,
            )

        return proxy

    @staticmethod
    def validate_cookies_path(cookies_path: Optional[str]) -> Optional[str]:
        """Validate and sanitize cookies file path."""
        if not cookies_path:
            return None

        cookies_path = cookies_path.strip()
        if not cookies_path:
            return None

        # Check for path traversal attempts
        if ".." in cookies_path or cookies_path.startswith("/"):
            raise TLRAPIException(
                "Invalid cookies path. Relative paths with '..' or absolute paths not allowed.",
                ErrorCode.COOKIES_INVALID,
                details={"path": cookies_path[:100]},
            )

        # Must end with .json
        if not cookies_path.endswith(".json"):
            raise TLRAPIException(
                "Cookies file must have .json extension",
                ErrorCode.COOKIES_INVALID,
                details={"path": cookies_path[:100]},
            )

        # Check for safe characters only
        if not SAFE_PATH_PATTERN.match(cookies_path):
            raise TLRAPIException(
                "Cookies path contains invalid characters. Only alphanumeric, dots, hyphens, underscores and forward slashes allowed.",
                ErrorCode.COOKIES_INVALID,
                details={"path": cookies_path[:100]},
            )

        # Limit path length
        if len(cookies_path) > 200:
            raise TLRAPIException(
                "Cookies path too long. Maximum 200 characters allowed.",
                ErrorCode.COOKIES_INVALID,
            )

        return cookies_path

    @staticmethod
    def validate_duration(duration: Optional[int]) -> Optional[int]:
        """Validate recording duration."""
        if duration is None:
            return None

        # Must be positive
        if duration <= 0:
            raise TLRAPIException(
                "Duration must be positive",
                ErrorCode.VALIDATION_ERROR,
                details={"duration": duration},
            )

        # Reasonable upper limit (24 hours)
        if duration > 86400:
            raise TLRAPIException(
                "Duration too long. Maximum 86400 seconds (24 hours) allowed.",
                ErrorCode.VALIDATION_ERROR,
                details={"duration": duration},
            )

        return duration

    @staticmethod
    def validate_poll_interval(poll_interval: int) -> int:
        """Validate watcher poll interval."""
        if poll_interval < 10:
            raise TLRAPIException(
                "Poll interval too short. Minimum 10 seconds required.",
                ErrorCode.VALIDATION_ERROR,
                details={"poll_interval": poll_interval},
            )

        if poll_interval > 3600:
            raise TLRAPIException(
                "Poll interval too long. Maximum 3600 seconds (1 hour) allowed.",
                ErrorCode.VALIDATION_ERROR,
                details={"poll_interval": poll_interval},
            )

        return poll_interval

    @staticmethod
    def validate_output_template(template: Optional[str]) -> Optional[str]:
        """Validate output filename template."""
        if not template:
            return None

        template = template.strip()
        if not template:
            return None

        # Check for dangerous characters
        dangerous_chars = ["..", "/", "\\", "|", "&", ";", "`", "$", "(", ")", "<", ">"]
        for char in dangerous_chars:
            if char in template:
                raise TLRAPIException(
                    f"Output template contains dangerous character: {char}",
                    ErrorCode.VALIDATION_ERROR,
                    details={"template": template[:100]},
                )

        # Limit length
        if len(template) > 100:
            raise TLRAPIException(
                "Output template too long. Maximum 100 characters allowed.",
                ErrorCode.VALIDATION_ERROR,
            )

        return template


def sanitize_recording_request(
    room_id: Optional[str],
    url: Optional[str],
    duration: Optional[int],
    proxy: Optional[str],
    cookies: Optional[str],
    output_template: Optional[str],
) -> dict:
    """Sanitize and validate all recording request inputs."""
    validator = SecurityValidator()

    return {
        "room_id": validator.validate_room_id(room_id),
        "url": validator.validate_url(url),
        "duration": validator.validate_duration(duration),
        "proxy": validator.validate_proxy(proxy),
        "cookies": validator.validate_cookies_path(cookies),
        "output_template": validator.validate_output_template(output_template),
    }


def sanitize_watcher_request(
    room_id: Optional[str],
    url: Optional[str],
    poll_interval: int,
    proxy: Optional[str],
    cookies: Optional[str],
) -> dict:
    """Sanitize and validate all watcher request inputs."""
    validator = SecurityValidator()

    return {
        "room_id": validator.validate_room_id(room_id),
        "url": validator.validate_url(url),
        "poll_interval": validator.validate_poll_interval(poll_interval),
        "proxy": validator.validate_proxy(proxy),
        "cookies": validator.validate_cookies_path(cookies),
    }
