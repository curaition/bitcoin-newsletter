#!/bin/bash
# Start all services for local development

set -e

echo "🚀 Starting Crypto Newsletter Development Environment"
echo "=================================================="

# Activate virtual environment
echo "📦 Activating virtual environment..."
source .venv/bin/activate

# Start Redis
echo "🔴 Starting Redis..."
./scripts/start-redis.sh

# Wait a moment for Redis to be ready
sleep 2

echo ""
echo "🎯 Available commands:"
echo "  1. Start Celery Worker:    python -m crypto_newsletter.cli.main worker"
echo "  2. Start Celery Beat:      python -m crypto_newsletter.cli.main beat"
echo "  3. Start Flower Monitor:   python -m crypto_newsletter.cli.main flower"
echo "  4. Manual Ingestion:       python -m crypto_newsletter.cli.main ingest --limit 5"
echo "  5. Schedule Ingestion:     python -m crypto_newsletter.cli.main schedule-ingest --limit 5"
echo "  6. Check Health:           python -m crypto_newsletter.cli.main health"
echo "  7. View Statistics:        python -m crypto_newsletter.cli.main stats"
echo ""
echo "🔧 Development workflow:"
echo "  1. Open 3 terminals"
echo "  2. Terminal 1: python -m crypto_newsletter.cli.main worker"
echo "  3. Terminal 2: python -m crypto_newsletter.cli.main beat"
echo "  4. Terminal 3: python -m crypto_newsletter.cli.main flower (optional monitoring)"
echo ""
echo "✅ Development environment ready!"
