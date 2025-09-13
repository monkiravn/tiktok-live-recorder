"""
S3/MinIO upload utilities with retry logic and error handling.
"""

import os
import threading
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config

from backend.core.config import get_settings
from backend.utils.logging import get_logger
from backend.core.exceptions import StorageException, ErrorCode


logger = get_logger(__name__)


class S3Uploader:
    """S3/MinIO uploader with retry logic and progress tracking."""

    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self.bucket = self.settings.S3_BUCKET
        self._init_client()

    def _init_client(self):
        """Initialize S3 client with configuration."""
        if not self.bucket:
            logger.info("S3 not configured, uploads disabled")
            return

        try:
            config = Config(
                retries={"max_attempts": 3, "mode": "adaptive"}, max_pool_connections=10
            )

            self.client = boto3.client(
                "s3",
                endpoint_url=self.settings.S3_ENDPOINT_URL,
                aws_access_key_id=self.settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=self.settings.AWS_SECRET_ACCESS_KEY,
                region_name=self.settings.AWS_REGION or "us-east-1",
                config=config,
            )

            # Test connection
            self.client.head_bucket(Bucket=self.bucket)
            logger.info(
                "S3 client initialized successfully",
                extra={
                    "bucket": self.bucket,
                    "endpoint": self.settings.S3_ENDPOINT_URL,
                },
            )

        except NoCredentialsError:
            logger.error("S3 credentials not provided")
            self.client = None
        except ClientError as e:
            logger.error(
                "S3 client initialization failed",
                extra={"bucket": self.bucket, "error": str(e)},
            )
            self.client = None
        except Exception as e:
            logger.exception(
                "Unexpected S3 initialization error", extra={"error": str(e)}
            )
            self.client = None

    def is_enabled(self) -> bool:
        """Check if S3 upload is enabled and configured."""
        return self.client is not None and self.bucket is not None

    def upload_file(
        self, file_path: str, s3_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a single file to S3 with retry logic.

        Args:
            file_path: Local file path
            s3_key: S3 object key (optional, will be generated if not provided)

        Returns:
            Dict with upload result information
        """
        if not self.is_enabled():
            raise StorageException(
                "S3 upload not configured or available", ErrorCode.STORAGE_ERROR
            )

        if not os.path.exists(file_path):
            raise StorageException(
                f"File not found: {file_path}", ErrorCode.FILE_NOT_FOUND
            )

        # Generate S3 key if not provided
        if not s3_key:
            s3_key = self._generate_s3_key(file_path)

        file_size = os.path.getsize(file_path)

        logger.info(
            "Starting S3 upload",
            extra={
                "file_path": file_path,
                "s3_key": s3_key,
                "file_size": file_size,
                "bucket": self.bucket,
            },
        )

        try:
            # Upload with progress callback
            extra_args = {
                "Metadata": {
                    "upload_timestamp": datetime.utcnow().isoformat(),
                    "original_path": os.path.basename(file_path),
                    "file_size": str(file_size),
                }
            }

            self.client.upload_file(
                file_path,
                self.bucket,
                s3_key,
                ExtraArgs=extra_args,
                Callback=self._upload_callback(file_path, file_size),
            )

            # Get object URL
            url = (
                f"{self.settings.S3_ENDPOINT_URL}/{self.bucket}/{s3_key}"
                if self.settings.S3_ENDPOINT_URL
                else f"https://{self.bucket}.s3.amazonaws.com/{s3_key}"
            )

            result = {
                "bucket": self.bucket,
                "key": s3_key,
                "url": url,
                "size": file_size,
                "uploaded_at": datetime.utcnow().isoformat(),
            }

            logger.info("S3 upload completed", extra=result)
            return result

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(
                "S3 upload failed",
                extra={
                    "file_path": file_path,
                    "s3_key": s3_key,
                    "error_code": error_code,
                    "error": str(e),
                },
            )
            raise StorageException(
                f"S3 upload failed: {error_code}",
                ErrorCode.S3_UPLOAD_FAILED,
                details={"s3_error": error_code, "file_path": file_path},
            )
        except Exception as e:
            logger.exception(
                "Unexpected S3 upload error",
                extra={"file_path": file_path, "s3_key": s3_key},
            )
            raise StorageException(
                f"S3 upload failed: {str(e)}",
                ErrorCode.S3_UPLOAD_FAILED,
                details={"file_path": file_path},
            )

    def upload_files(
        self, file_paths: List[str], s3_prefix: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Upload multiple files to S3.

        Args:
            file_paths: List of local file paths
            s3_prefix: Optional S3 key prefix

        Returns:
            List of upload results
        """
        results = []

        for file_path in file_paths:
            try:
                s3_key = None
                if s3_prefix:
                    filename = os.path.basename(file_path)
                    s3_key = f"{s3_prefix.rstrip('/')}/{filename}"

                result = self.upload_file(file_path, s3_key)
                results.append(result)

            except Exception as e:
                logger.error(
                    "Failed to upload file",
                    extra={"file_path": file_path, "error": str(e)},
                )
                # Continue with other files
                results.append(
                    {"file_path": file_path, "error": str(e), "uploaded": False}
                )

        return results

    def _generate_s3_key(self, file_path: str) -> str:
        """Generate S3 key from file path."""
        now = datetime.utcnow()
        filename = os.path.basename(file_path)

        # Extract potential room_id from path or filename
        path_parts = Path(file_path).parts
        room_id = "unknown"
        for part in reversed(path_parts):
            if part.isdigit():
                room_id = part
                break

        return (
            f"recordings/{room_id}/{now.year}/{now.month:02d}/{now.day:02d}/{filename}"
        )

    def _upload_callback(self, file_path: str, total_size: int):
        """Create upload progress callback."""
        uploaded = 0

        def callback(bytes_transferred):
            nonlocal uploaded
            uploaded += bytes_transferred
            percent = (uploaded / total_size) * 100 if total_size > 0 else 0

            if (
                uploaded % (1024 * 1024) == 0 or uploaded == total_size
            ):  # Log every MB or completion
                logger.debug(
                    "S3 upload progress",
                    extra={
                        "file_path": file_path,
                        "uploaded_bytes": uploaded,
                        "total_bytes": total_size,
                        "percent": round(percent, 1),
                    },
                )

        return callback

    def delete_file(self, s3_key: str) -> bool:
        """Delete file from S3."""
        if not self.is_enabled():
            return False

        try:
            self.client.delete_object(Bucket=self.bucket, Key=s3_key)
            logger.info("S3 file deleted", extra={"bucket": self.bucket, "key": s3_key})
            return True
        except Exception as e:
            logger.error(
                "Failed to delete S3 file",
                extra={"bucket": self.bucket, "key": s3_key, "error": str(e)},
            )
            return False


# Global uploader instance
_uploader = None


def get_s3_uploader() -> S3Uploader:
    """Get global S3 uploader instance."""
    global _uploader
    if _uploader is None:
        _uploader = S3Uploader()
    return _uploader


def upload_files_async(file_paths: List[str], s3_prefix: Optional[str] = None) -> None:
    """Upload files to S3 asynchronously in background thread."""
    uploader = get_s3_uploader()
    if not uploader.is_enabled():
        logger.info("S3 not enabled, skipping upload")
        return

    def upload_worker():
        try:
            results = uploader.upload_files(file_paths, s3_prefix)
            successful = [r for r in results if r.get("uploaded", True)]
            failed = [r for r in results if not r.get("uploaded", True)]

            logger.info(
                "Async S3 upload completed",
                extra={
                    "total_files": len(file_paths),
                    "successful": len(successful),
                    "failed": len(failed),
                },
            )
        except Exception as e:
            logger.exception(
                "Async S3 upload failed",
                extra={"file_paths": file_paths, "error": str(e)},
            )

    thread = threading.Thread(target=upload_worker, daemon=True)
    thread.start()
