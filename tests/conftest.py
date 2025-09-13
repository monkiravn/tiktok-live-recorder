import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import os
import sys

# Add src and service to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "service"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture
def client():
    """Test client for FastAPI app."""
    from service.app import app

    return TestClient(app)


@pytest.fixture
def mock_celery():
    """Mock celery for testing without Redis."""
    with patch("service.app.celery") as mock:
        mock.send_task.return_value = Mock(id="test-task-id", status="PENDING")
        mock.AsyncResult.return_value = Mock(
            status="SUCCESS",
            ready=Mock(return_value=True),
            result={"returncode": 0, "files": ["test.mp4"]},
        )
        mock.control.ping.return_value = True
        yield mock


@pytest.fixture
def mock_redis():
    """Mock Redis storage for testing."""
    with patch("service.storage.RedisStorage") as mock:
        instance = Mock()
        instance.get_watcher.return_value = None
        instance.set_watcher.return_value = None
        instance.del_watcher.return_value = 1
        mock.return_value = instance
        yield instance


@pytest.fixture
def api_headers():
    """Valid API headers for testing."""
    return {"X-API-Key": "dev-key"}
