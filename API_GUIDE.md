# TikTok Live Recorder API - Setup & Development Guide

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- FFmpeg (for recording functionality)

### Running with Docker (Recommended)

1. **Clone and start services:**

```bash
git clone <repository-url>
cd tiktok-live-recorder
docker compose up --build
```

2. **Access services:**

- API: http://localhost:8000/docs
- Flower (Celery Monitor): http://localhost:5555
- Metrics: http://localhost:8000/metrics

### Local Development Setup

1. **Install dependencies:**

```bash
cd service
pip install -r requirements.txt
```

2. **Start Redis:**

```bash
docker run -p 6379:6379 redis:7-alpine
```

3. **Start services:**

```bash
# Terminal 1: API
uvicorn backend.app:app --reload --port 8000

# Terminal 2: Worker
celery -A backend.core.celery_app.celery worker -Q default,recording -l info --concurrency 1

# Terminal 3: Flower
celery -A backend.core.celery_app.celery flower --broker=redis://localhost:6379/0 --port=5555
```

## 🧪 Running Tests

```bash
# Install test dependencies
pip install -r backend/requirements.txt

# Run tests with coverage
./run_tests.sh

# Or manually:
python -m pytest tests/ -v --cov=service --cov-report=html
```

Coverage report will be available at `htmlcov/index.html`.

## 📖 API Usage Examples

### Authentication

All API requests (except health checks) require `X-API-Key` header:

```bash
export API_KEY="dev-key"  # Change in production
```

### 1. Create Recording (Manual)

```bash
curl -X POST http://localhost:8000/recordings \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "url": "https://www.tiktok.com/@username/live",
    "duration": 1800,
    "options": {
      "upload_s3": true,
      "proxy": "http://proxy:8080"
    }
  }'
```

### 2. Create Watcher (Auto-record when live)

```bash
curl -X POST http://localhost:8000/watchers \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "room_id": "123456789",
    "poll_interval": 60,
    "options": {
      "upload_s3": false
    }
  }'
```

### 3. Check Job Status

```bash
curl -H "X-API-Key: $API_KEY" \
  http://localhost:8000/jobs/your-task-id-here
```

### 4. List Recordings

```bash
curl -H "X-API-Key: $API_KEY" \
  "http://localhost:8000/files?page=1&page_size=10"
```

### 5. Delete Watcher

```bash
curl -X DELETE -H "X-API-Key: $API_KEY" \
  http://localhost:8000/watchers/123456789
```

## 🔧 Configuration

### Environment Variables

| Variable                | Default                    | Description                         |
| ----------------------- | -------------------------- | ----------------------------------- |
| `CELERY_BROKER_URL`     | `redis://localhost:6379/0` | Redis broker URL                    |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/1` | Redis result backend URL            |
| `RECORDINGS_DIR`        | `/recordings`              | Directory to store recordings       |
| `API_KEYS`              | `dev-key`                  | Comma-separated API keys            |
| `RATE_LIMIT_PER_MIN`    | `60`                       | Rate limit per API key per minute   |
| `CORS_ALLOW_ORIGINS`    | `""`                       | CORS allowed origins (empty = none) |
| `TLR_ROOT`              | `/app/src`                 | Path to TikTok Live Recorder CLI    |

### S3/MinIO Configuration (Optional)

| Variable                | Default     | Description             |
| ----------------------- | ----------- | ----------------------- |
| `S3_BUCKET`             | `""`        | S3 bucket name          |
| `S3_ENDPOINT_URL`       | `""`        | S3 endpoint (for MinIO) |
| `AWS_ACCESS_KEY_ID`     | `""`        | AWS access key          |
| `AWS_SECRET_ACCESS_KEY` | `""`        | AWS secret key          |
| `AWS_REGION`            | `us-east-1` | AWS region              |

## 📊 Monitoring & Observability

### Structured Logging

All logs are in JSON format with correlation IDs:

```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "INFO",
  "service": "tiktok-live-recorder-api",
  "correlation_id": "uuid-here",
  "task_id": "celery-task-id",
  "room_id": "123456789",
  "message": "Recording task started"
}
```

### Metrics (Prometheus)

Available at `/metrics` endpoint:

- `celery_tasks_total` - Total Celery tasks by status
- `recordings_total` - Total recordings by status
- `watchers_active` - Number of active watchers
- `disk_free_bytes` - Free disk space
- `recording_files_total` - Total recording files
- `s3_uploads_total` - S3 uploads by status
- `http_requests_total` - HTTP requests by endpoint

### Flower Dashboard

Monitor Celery workers and tasks at http://localhost:5555

## 🔒 Security Features

### Input Validation

- TikTok URL format validation
- Room ID numeric validation (max 20 digits)
- Proxy URL format validation
- File path sanitization (prevent path traversal)
- Duration limits (max 24 hours)

### Rate Limiting

- Per API key: 60 requests/minute (configurable)
- Per endpoint rate limiting
- Automatic backoff for failed requests

### Process Security

- Non-root user in Docker container
- Signal handling for graceful shutdown
- Process timeout management
- Subprocess cleanup to prevent zombies

## 🚨 Error Handling

### Error Codes

Standard error codes with correlation IDs:

- `RECORDER_EXIT_NONZERO` - Recording process failed
- `FFMPEG_MISSING` - FFmpeg not found
- `LIVE_OFFLINE` - Stream is offline
- `NETWORK_TIMEOUT` - Network timeout
- `INVALID_URL` - Invalid TikTok URL
- `INVALID_ROOM_ID` - Invalid room ID format
- `S3_UPLOAD_FAILED` - S3 upload failed

### Error Response Format

```json
{
  "error_code": "INVALID_URL",
  "message": "URL must be a valid TikTok domain",
  "details": { "url": "invalid-url" },
  "correlation_id": "uuid-here"
}
```

## 🔄 Development Workflow

### Code Quality

```bash
# Linting
python -m ruff check service/ --fix
python -m black service/

# Type checking
python -m mypy service/

# Security scan
bandit -r service/
```

### Testing Strategy

- **Unit Tests**: Models, utilities, validators
- **Integration Tests**: API endpoints, Celery tasks
- **Mocking**: External services (Redis, subprocess calls)
- **Coverage Target**: ≥70% for core modules

### CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
- Lint code (ruff, black, mypy)
- Run tests with coverage
- Build Docker image
- Security scan (Trivy)
- Deploy to staging
```

## 🐛 Troubleshooting

### Common Issues

**1. Redis Connection Failed**

```bash
# Check Redis is running
docker ps | grep redis
# Check Redis logs
docker logs <redis-container-id>
```

**2. Recording Fails with FFMPEG_MISSING**

```bash
# Install FFmpeg in container/system
apt-get update && apt-get install -y ffmpeg
```

**3. S3 Upload Fails**

```bash
# Check S3 configuration
curl http://localhost:8000/metrics | grep s3_uploads_total
# Check S3 credentials and bucket permissions
```

**4. High Memory Usage**

```bash
# Check worker concurrency
celery -A service.celery_app.celery inspect active
# Reduce concurrency or add more workers
```

### Debug Mode

Set log level to DEBUG:

```bash
export LOG_LEVEL=DEBUG
```

### Health Checks

```bash
# API health
curl http://localhost:8000/healthz

# Readiness (Redis connection)
curl http://localhost:8000/ready

# Worker status
celery -A service.celery_app.celery inspect ping
```

## 📚 Architecture Details

### Components

- **FastAPI**: REST API server with async support
- **Celery**: Distributed task queue for background jobs
- **Redis**: Message broker and result backend
- **Docker**: Containerization for easy deployment
- **Prometheus**: Metrics collection and monitoring

### Task Queues

- `default`: Lightweight tasks (watchers, API operations)
- `recording`: Heavy I/O tasks (actual recording processes)

### Process Flow

1. Client → FastAPI (validation, auth)
2. FastAPI → Celery (task creation)
3. Celery Worker → TikTok Live Recorder CLI
4. Results → Redis (task results)
5. Optional: Files → S3/MinIO (upload)

## 📄 License

MIT License - see LICENSE file for details.
