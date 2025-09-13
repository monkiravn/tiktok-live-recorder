import pytest
import httpx
from unittest.mock import Mock, patch


@pytest.mark.asyncio
class TestAPIEndpoints:
    """Integration tests for API endpoints."""

    def test_healthz_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.text == "ok"

    @patch("service.app.celery")
    def test_ready_endpoint_success(self, mock_celery, client):
        """Test readiness endpoint when Redis is available."""
        mock_celery.control.ping.return_value = True

        response = client.get("/ready")
        assert response.status_code == 200
        assert response.text == "ready"

    @patch("service.app.celery")
    def test_ready_endpoint_failure(self, mock_celery, client):
        """Test readiness endpoint when Redis is unavailable."""
        mock_celery.control.ping.side_effect = Exception("Redis unavailable")

        response = client.get("/ready")
        assert response.status_code == 503
        assert "not ready" in response.json()["detail"]

    def test_recordings_endpoint_no_auth(self, client):
        """Test recordings endpoint without authentication."""
        response = client.post("/recordings", json={"room_id": "123"})
        assert response.status_code == 401

    @patch("service.app.celery")
    def test_recordings_endpoint_success(self, mock_celery, client, api_headers):
        """Test successful recording creation."""
        mock_task = Mock(id="test-task-123", status="PENDING")
        mock_celery.send_task.return_value = mock_task

        response = client.post(
            "/recordings",
            json={"room_id": "123456789", "duration": 120},
            headers=api_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-123"
        assert data["status"] == "PENDING"

    def test_recordings_endpoint_missing_identifiers(self, client, api_headers):
        """Test recordings endpoint with missing room_id and url."""
        response = client.post(
            "/recordings", json={"duration": 120}, headers=api_headers
        )
        assert response.status_code == 400
        assert "Provide at least room_id or url" in response.json()["detail"]

    @patch("service.app.celery")
    def test_job_status_endpoint(self, mock_celery, client, api_headers):
        """Test job status endpoint."""
        mock_result = Mock()
        mock_result.status = "SUCCESS"
        mock_result.ready.return_value = True
        mock_result.result = {"returncode": 0, "files": ["test.mp4"]}
        mock_celery.AsyncResult.return_value = mock_result

        response = client.get("/jobs/test-task-123", headers=api_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-123"
        assert data["status"] == "SUCCESS"
        assert data["result"]["returncode"] == 0

    @patch("service.storage.RedisStorage")
    @patch("service.app.celery")
    def test_watchers_create_success(
        self, mock_celery, mock_storage_class, client, api_headers
    ):
        """Test successful watcher creation."""
        # Setup mocks
        mock_storage = Mock()
        mock_storage.get_watcher.return_value = None  # No existing watcher
        mock_storage_class.return_value = mock_storage

        mock_task = Mock(id="watcher-task-123", status="PENDING")
        mock_celery.send_task.return_value = mock_task

        response = client.post(
            "/watchers",
            json={"room_id": "123456789", "poll_interval": 60},
            headers=api_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "watcher-task-123"
        assert data["status"] == "PENDING"

        # Verify storage was called
        mock_storage.set_watcher.assert_called_once_with(
            "123456789", "watcher-task-123"
        )

    @patch("service.storage.RedisStorage")
    def test_watchers_create_conflict(self, mock_storage_class, client, api_headers):
        """Test watcher creation when one already exists."""
        mock_storage = Mock()
        mock_storage.get_watcher.return_value = "existing-task-id"
        mock_storage_class.return_value = mock_storage

        response = client.post(
            "/watchers",
            json={"room_id": "123456789", "poll_interval": 60},
            headers=api_headers,
        )

        assert response.status_code == 409
        assert "Watcher already exists" in response.json()["detail"]

    @patch("service.storage.RedisStorage")
    @patch("service.app.celery")
    def test_watchers_delete_success(
        self, mock_celery, mock_storage_class, client, api_headers
    ):
        """Test successful watcher deletion."""
        mock_storage = Mock()
        mock_storage.get_watcher.return_value = "task-to-delete"
        mock_storage_class.return_value = mock_storage

        response = client.delete("/watchers/123456789", headers=api_headers)

        assert response.status_code == 200
        assert response.json()["ok"] is True

        # Verify revoke was called
        mock_celery.control.revoke.assert_called_once_with(
            "task-to-delete", terminate=True, signal="SIGTERM"
        )
        mock_storage.del_watcher.assert_called_once_with("123456789")

    @patch("service.storage.RedisStorage")
    def test_watchers_delete_not_found(self, mock_storage_class, client, api_headers):
        """Test watcher deletion when watcher doesn't exist."""
        mock_storage = Mock()
        mock_storage.get_watcher.return_value = None
        mock_storage_class.return_value = mock_storage

        response = client.delete("/watchers/nonexistent", headers=api_headers)

        assert response.status_code == 404
        assert "Watcher not found" in response.json()["detail"]

    @patch("service.app.list_recording_files")
    @patch("service.app.to_fileinfo")
    def test_files_endpoint(
        self, mock_to_fileinfo, mock_list_files, client, api_headers
    ):
        """Test files listing endpoint."""
        mock_list_files.return_value = [
            "/recordings/test1.mp4",
            "/recordings/test2.mp4",
        ]
        mock_to_fileinfo.side_effect = [
            {
                "name": "test1.mp4",
                "size": 1024,
                "mtime": 1234567890.0,
                "path": "/recordings/test1.mp4",
            },
            {
                "name": "test2.mp4",
                "size": 2048,
                "mtime": 1234567891.0,
                "path": "/recordings/test2.mp4",
            },
        ]

        response = client.get("/files?page=1&page_size=10", headers=api_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["total"] == 2
        assert len(data["items"]) == 2
