import pytest
from unittest.mock import Mock, patch
from service.models import CreateRecordingRequest, RecordingOptions


class TestModels:
    """Test Pydantic models validation and serialization."""

    def test_recording_options_defaults(self):
        """Test RecordingOptions default values."""
        options = RecordingOptions()
        assert options.upload_s3 is False
        assert options.proxy is None
        assert options.cookies is None

    def test_recording_options_with_values(self):
        """Test RecordingOptions with custom values."""
        options = RecordingOptions(
            upload_s3=True, proxy="http://proxy:8080", cookies="/path/to/cookies.json"
        )
        assert options.upload_s3 is True
        assert options.proxy == "http://proxy:8080"
        assert options.cookies == "/path/to/cookies.json"

    def test_create_recording_request_valid_room_id(self):
        """Test valid CreateRecordingRequest with room_id."""
        req = CreateRecordingRequest(room_id="123456789", duration=120)
        assert req.room_id == "123456789"
        assert req.url is None
        assert req.duration == 120

    def test_create_recording_request_valid_url(self):
        """Test valid CreateRecordingRequest with URL."""
        req = CreateRecordingRequest(url="https://www.tiktok.com/@user/live")
        assert req.url == "https://www.tiktok.com/@user/live"
        assert req.room_id is None

    def test_create_recording_request_url_strip(self):
        """Test URL stripping functionality."""
        req = CreateRecordingRequest(url="  https://www.tiktok.com/@user/live  ")
        assert req.url == "https://www.tiktok.com/@user/live"

    def test_create_recording_request_empty_url(self):
        """Test empty URL becomes None."""
        req = CreateRecordingRequest(url="   ")
        assert req.url is None

    def test_duration_validation_positive(self):
        """Test duration must be positive."""
        req = CreateRecordingRequest(room_id="123", duration=10)
        assert req.duration == 10

    def test_duration_validation_zero_fails(self):
        """Test duration cannot be zero."""
        with pytest.raises(ValueError):
            CreateRecordingRequest(room_id="123", duration=0)

    def test_duration_validation_negative_fails(self):
        """Test duration cannot be negative."""
        with pytest.raises(ValueError):
            CreateRecordingRequest(room_id="123", duration=-1)
