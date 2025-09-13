FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/backend

# Create non-root user for security
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        curl \
        procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements files first (for better layer caching)
COPY backend/requirements.txt /app/backend/requirements.txt
COPY src/requirements.txt /app/src/requirements.txt

# Install API deps first
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Install CLI deps
RUN pip install --no-cache-dir -r /app/src/requirements.txt

# Copy backend source
COPY backend/ /app/backend/

# Copy src directory
COPY src/ /app/src/

# Create recordings directory and set permissions
RUN mkdir -p /recordings && \
    chown -R appuser:appuser /app /recordings

# Switch to non-root user
USER appuser

ENV TLR_ROOT=/app/src \
    RECORDINGS_DIR=/recordings

VOLUME ["/recordings"]

EXPOSE 8000 5555

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]

