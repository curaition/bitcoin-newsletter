# Local Testing Guide for Worker Connectivity Fix

## Prerequisites

Before testing the worker connectivity fix locally, ensure you have:

### 1. Redis Running Locally
```bash
# macOS (with Homebrew)
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis-server

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

### 2. Required Python Packages
```bash
# Install required packages
uv add celery[redis]
uv add celery-aio-pool

# Or with pip
pip install celery[redis] celery-aio-pool
```

### 3. Environment Setup
Create a `.env` file in the project root (if not exists):
```bash
cp .env.example .env
```

Edit `.env` to ensure these values:
```env
ENVIRONMENT=development
REDIS_URL=redis://localhost:6379/0
ENABLE_CELERY=true
LOG_LEVEL=INFO
DEBUG=true
```

## Running the Local Test

### Option 1: Automated Test Script
```bash
# Run the comprehensive test script
python scripts/local_worker_test.py
```

This script will:
1. ✅ Check prerequisites (Redis, packages)
2. 🔧 Set up test environment
3. 🏥 Test health detection (no workers)
4. 🚀 Start a test worker
5. 🔍 Test worker detection (with workers)
6. 🧹 Clean up test processes

### Option 2: Manual Step-by-Step Testing

#### Terminal 1: Start Worker
```bash
# Start a test worker
python -m crypto_newsletter.cli.main worker --loglevel INFO --concurrency 2
```

#### Terminal 2: Test Connectivity
```bash
# Run the connectivity test
python scripts/test_worker_connectivity.py
```

## Expected Results

### Before Fix (Broken State)
If you had the old configuration with `--without-heartbeat`:
```
❌ No workers found via direct inspection
❌ Worker health check failed: No workers available
```

### After Fix (Working State)
With the heartbeat fix applied:
```
✅ Found 1 workers via direct inspection
✅ Worker health check passed
✅ Queue health check passed
✅ Broker connection successful
```

## Troubleshooting

### Redis Connection Issues
```bash
# Check if Redis is running
redis-cli ping

# Check Redis logs
tail -f /usr/local/var/log/redis.log  # macOS
sudo journalctl -u redis-server -f   # Linux
```

### Worker Startup Issues
```bash
# Check worker logs for errors
python -m crypto_newsletter.cli.main worker --loglevel DEBUG

# Test Celery directly
celery -A crypto_newsletter.shared.celery.app worker --loglevel=INFO
```

### Import/Package Issues
```bash
# Verify packages are installed
python -c "import celery; print(celery.__version__)"
python -c "import celery_aio_pool; print('celery-aio-pool OK')"

# Check Python path
python -c "import sys; print(sys.path)"
```

## Test Validation Checklist

- [ ] Redis is running and accessible
- [ ] Required packages are installed
- [ ] Worker starts without errors
- [ ] Health check detects running workers
- [ ] Worker count > 0 in health response
- [ ] No errors in worker logs
- [ ] Clean shutdown works

## What This Test Validates

1. **Heartbeat Functionality**: Workers send heartbeat signals
2. **Health Detection**: Monitoring system detects active workers
3. **AsyncIO Pool**: Custom pool works with heartbeat
4. **Configuration**: All Celery settings are correct
5. **Local Environment**: Setup matches production expectations

## Next Steps After Successful Local Test

1. ✅ **Local test passes** → Safe to deploy to production
2. ❌ **Local test fails** → Debug and fix issues before deployment

The local test environment closely mirrors production, so success here indicates the fix will work in production.
