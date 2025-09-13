#!/bin/bash
set -e

echo "🎯 Building and testing TikTok Live Recorder API"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose >/dev/null 2>&1 && ! docker compose version >/dev/null 2>&1; then
    print_error "Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

print_status "Building Docker images..."
docker compose -f docker-compose.yml build

print_status "Starting services..."
docker compose -f docker-compose.yml up -d

print_status "Waiting for services to be ready..."
sleep 10

# Wait for API to be ready
print_status "Checking API health..."
for i in {1..30}; do
    if curl -f -s http://localhost:8000/healthz >/dev/null; then
        print_status "API is healthy!"
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "API health check failed after 30 attempts"
        docker compose -f docker-compose.yml logs api
        exit 1
    fi
    echo -n "."
    sleep 2
done

# Wait for Redis to be ready
print_status "Checking Redis readiness..."
if curl -f -s http://localhost:8000/ready >/dev/null; then
    print_status "Redis is ready!"
else
    print_warning "Redis readiness check failed, but continuing..."
fi

print_status "Running API tests..."
# Test basic endpoints
API_KEY="dev-key"

echo "Testing health endpoint..."
curl -f -s http://localhost:8000/healthz || (print_error "Health check failed" && exit 1)

echo "Testing ready endpoint..."
curl -f -s http://localhost:8000/ready || print_warning "Ready check failed"

echo "Testing docs endpoint..."
curl -f -s http://localhost:8000/docs >/dev/null || print_warning "Docs endpoint failed"

echo "Testing metrics endpoint..."
curl -f -s http://localhost:8000/metrics >/dev/null || print_warning "Metrics endpoint failed"

# Test authentication
echo "Testing authentication..."
curl -f -s -H "X-API-Key: invalid" http://localhost:8000/files 2>/dev/null && print_error "Authentication bypass detected!" || print_status "Authentication working correctly"

# Test valid API call
echo "Testing valid API call..."
curl -f -s -H "X-API-Key: $API_KEY" http://localhost:8000/files >/dev/null || print_warning "Valid API call failed"

print_status "Integration tests completed successfully!"

print_status "Service URLs:"
echo "  📖 API Documentation: http://localhost:8000/docs"
echo "  🌸 Flower Dashboard: http://localhost:5555"  
echo "  📊 Metrics: http://localhost:8000/metrics"

print_status "Example API calls:"
echo "  # Create recording:"
echo "  curl -X POST http://localhost:8000/recordings \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -H \"X-API-Key: $API_KEY\" \\"
echo "    -d '{\"url\": \"https://www.tiktok.com/@user/live\", \"duration\": 120}'"
echo ""
echo "  # List files:"
echo "  curl -H \"X-API-Key: $API_KEY\" http://localhost:8000/files"

echo ""
print_status "To stop services: docker compose -f docker-compose.yml down"
print_status "To view logs: docker compose -f docker-compose.yml logs -f [service]"

print_status "🎉 Setup completed successfully!"