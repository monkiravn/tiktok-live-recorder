import pytest
from unittest.mock import Mock, patch, MagicMock
from service.utils import (
    list_recording_files,
    paginate,
    to_fileinfo,
    load_cookies_from_path,
    run_recording,
)
import os
import tempfile
import json


class TestUtils:
    """Test utility functions."""

    def test_paginate_first_page(self):
        """Test pagination first page."""
        items = list(range(100))
        result = paginate(items, page=1, page_size=10)
        assert len(result) == 10
        assert result == list(range(10))

    def test_paginate_middle_page(self):
        """Test pagination middle page."""
        items = list(range(100))
        result = paginate(items, page=3, page_size=10)
        assert len(result) == 10
        assert result == list(range(20, 30))

    def test_paginate_last_page(self):
        """Test pagination last page."""
        items = list(range(25))
        result = paginate(items, page=3, page_size=10)
        assert len(result) == 5
        assert result == list(range(20, 25))

    def test_paginate_empty_result(self):
        """Test pagination beyond available items."""
        items = list(range(10))
        result = paginate(items, page=5, page_size=10)
        assert len(result) == 0
        assert result == []

    @patch("os.stat")
    def test_to_fileinfo(self, mock_stat):
        """Test file info extraction."""
        mock_stat.return_value = Mock(st_size=1024, st_mtime=1234567890.0)

        result = to_fileinfo("/path/to/file.mp4")

        assert result["name"] == "file.mp4"
        assert result["size"] == 1024
        assert result["mtime"] == 1234567890.0
        assert result["path"] == "/path/to/file.mp4"

    def test_load_cookies_from_path_none(self):
        """Test loading cookies with None path."""
        result = load_cookies_from_path(None)
        assert result is None

    def test_load_cookies_from_path_valid(self):
        """Test loading cookies from valid file."""
        test_cookies = {"session": "abc123", "csrf": "xyz789"}

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump(test_cookies, f)
            f.flush()

            result = load_cookies_from_path(f.name)
            assert result == test_cookies

            os.unlink(f.name)

    @patch("service.utils.list_recording_files")
    @patch("service.utils.ensure_tlr_on_path")
    @patch("core.tiktok_recorder.TikTokRecorder")
    def test_run_recording_success(
        self, mock_recorder_class, mock_ensure_path, mock_list_files
    ):
        """Test successful recording run."""
        # Setup mocks
        mock_list_files.side_effect = [
            [],  # before recording
            ["/recordings/test.mp4"],  # after recording
        ]

        mock_recorder = Mock()
        mock_recorder_class.return_value = mock_recorder

        # Run test
        rc, files = run_recording(
            url="https://test.com/live",
            room_id="123",
            duration=60,
            output_dir="/recordings",
            proxy=None,
            cookies=None,
        )

        # Assertions
        assert rc == 0
        assert files == ["/recordings/test.mp4"]
        mock_recorder.run.assert_called_once()
        mock_recorder_class.assert_called_once()

    @patch("service.utils.list_recording_files")
    @patch("service.utils.ensure_tlr_on_path")
    @patch("core.tiktok_recorder.TikTokRecorder")
    def test_run_recording_failure(
        self, mock_recorder_class, mock_ensure_path, mock_list_files
    ):
        """Test recording run with exception."""
        # Setup mocks
        mock_list_files.return_value = []

        mock_recorder = Mock()
        mock_recorder.run.side_effect = Exception("Recording failed")
        mock_recorder_class.return_value = mock_recorder

        # Run test
        rc, files = run_recording(
            url="https://test.com/live",
            room_id="123",
            duration=60,
            output_dir="/recordings",
            proxy=None,
            cookies=None,
        )

        # Assertions
        assert rc == 1
        assert files == []
