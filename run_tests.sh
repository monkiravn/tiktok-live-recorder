#!/bin/bash
set -e

echo "🧪 Running TikTok Live Recorder API Tests"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r service/requirements.txt

# Run linting
echo "🔍 Running code quality checks..."
python -m ruff check service/ --fix || true
python -m black service/ || true

# Run tests with coverage
echo "🚀 Running tests..."
python -m pytest tests/ -v --cov=service --cov-report=term-missing --cov-report=html

echo "✅ Tests completed! Check htmlcov/index.html for coverage report."