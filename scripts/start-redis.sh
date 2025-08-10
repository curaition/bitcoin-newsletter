#!/bin/bash
# Start Redis server for local development

echo "🔴 Starting Redis server for Celery..."

# Check if Redis is installed
if ! command -v redis-server &> /dev/null; then
    echo "❌ Redis not found. Please install Redis:"
    echo "   macOS: brew install redis"
    echo "   Ubuntu: sudo apt-get install redis-server"
    echo "   Docker: docker run -d -p 6379:6379 redis:alpine"
    exit 1
fi

# Check if Redis is already running
if redis-cli ping &> /dev/null; then
    echo "✅ Redis is already running"
    redis-cli info server | grep redis_version
else
    echo "🚀 Starting Redis server..."
    redis-server --daemonize yes --port 6379
    
    # Wait for Redis to start
    sleep 2
    
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis started successfully"
        redis-cli info server | grep redis_version
    else
        echo "❌ Failed to start Redis"
        exit 1
    fi
fi

echo "🔗 Redis connection: redis://localhost:6379/0"
echo "📊 Monitor with: redis-cli monitor"
