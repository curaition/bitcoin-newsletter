# Crypto Newsletter CLI Usage Guide

The Crypto Newsletter CLI provides comprehensive command-line tools for managing the Bitcoin newsletter application. This guide covers all available commands and their usage.

## Installation & Setup

The CLI is automatically available after installing the project:

```bash
# Install the project
uv pip install -e .

# Use the CLI
crypto-newsletter --help
# OR
python -m crypto_newsletter.cli.main --help
```

## Quick Start

```bash
# Show all available commands
crypto-newsletter commands

# Check system health
crypto-newsletter health

# View database status
crypto-newsletter db-status

# Show article statistics
crypto-newsletter stats

# Start development server
crypto-newsletter serve --dev
```

## Command Categories

### 🔍 Health & Monitoring

#### `health`
Check the health of all pipeline components including database, API, and Celery connections.

```bash
crypto-newsletter health
```

#### `test`
Run a quick pipeline test with minimal data to verify everything is working.

```bash
crypto-newsletter test
```

#### `monitor`
Start a real-time monitoring dashboard that refreshes every 5 seconds.

```bash
crypto-newsletter monitor
```

#### `logs`
Show application logs (placeholder for log integration).

```bash
crypto-newsletter logs --service web --lines 50 --follow
```

### 📊 Data Management

#### `ingest`
Manually run article ingestion from the CoinDesk API.

```bash
# Basic ingestion
crypto-newsletter ingest

# Custom parameters
crypto-newsletter ingest --limit 20 --hours 12 --categories BTC,ETH --verbose
```

#### `schedule-ingest`
Schedule an immediate article ingestion task via Celery.

```bash
crypto-newsletter schedule-ingest --limit 10 --hours 4
```

#### `stats`
Show comprehensive article statistics and recent data.

```bash
crypto-newsletter stats
```

#### `db-status`
Check database connection and display basic statistics with a rich table format.

```bash
crypto-newsletter db-status
```

#### `db-cleanup`
Clean up old articles from the database.

```bash
# Dry run (default)
crypto-newsletter db-cleanup --days 30 --dry-run

# Actually delete
crypto-newsletter db-cleanup --days 30 --no-dry-run
```

### ⚙️ Task Management

#### `tasks-active`
Show currently active Celery tasks in a formatted table.

```bash
crypto-newsletter tasks-active
```

#### `task-status`
Get the status of a specific Celery task.

```bash
crypto-newsletter task-status <task-id>
```

#### `task-cancel`
Cancel a specific Celery task.

```bash
crypto-newsletter task-cancel <task-id>
```

### 🔧 Services

#### `serve`
Start the FastAPI web service.

```bash
# Development mode
crypto-newsletter serve --dev --port 8000

# Production mode
crypto-newsletter serve --production --workers 4 --port 8000
```

#### `worker`
Start Celery worker for background task processing.

```bash
crypto-newsletter worker --loglevel INFO --concurrency 2
```

#### `beat`
Start Celery beat scheduler for periodic tasks.

```bash
crypto-newsletter beat
```

#### `flower`
Start Flower monitoring interface for Celery.

```bash
crypto-newsletter flower --port 5555
```

### ⚙️ Configuration

#### `config-show`
Display current configuration settings in a formatted table.

```bash
crypto-newsletter config-show
```

#### `config-test`
Test configuration and external connections (database, Redis, CoinDesk API).

```bash
crypto-newsletter config-test
```

### 🛠️ Development

#### `dev-setup`
Set up and verify the development environment.

```bash
crypto-newsletter dev-setup
```

#### `dev-reset`
Reset development environment by clearing caches and temporary files.

```bash
crypto-newsletter dev-reset
```

#### `shell`
Start an interactive Python shell with application context loaded.

```bash
crypto-newsletter shell
```

### 📤 Utilities

#### `export-data`
Export article data to JSON or CSV format.

```bash
# Export to JSON
crypto-newsletter export-data --output articles.json --days 7

# Export to CSV
crypto-newsletter export-data --output articles.csv --format csv --days 30
```

#### `version`
Show version information.

```bash
crypto-newsletter version
```

#### `commands`
Show all available commands with descriptions organized by category.

```bash
crypto-newsletter commands
```

## Common Workflows

### Development Workflow

```bash
# 1. Set up development environment
crypto-newsletter dev-setup

# 2. Check configuration
crypto-newsletter config-show
crypto-newsletter config-test

# 3. Start services (in separate terminals)
crypto-newsletter worker
crypto-newsletter beat
crypto-newsletter serve --dev

# 4. Test the pipeline
crypto-newsletter health
crypto-newsletter test
crypto-newsletter ingest --limit 5
```

### Production Monitoring

```bash
# Check system status
crypto-newsletter health
crypto-newsletter db-status
crypto-newsletter tasks-active

# Monitor in real-time
crypto-newsletter monitor

# Export data for analysis
crypto-newsletter export-data --days 30 --format csv
```

### Troubleshooting

```bash
# Check configuration
crypto-newsletter config-test

# View system health
crypto-newsletter health

# Check database
crypto-newsletter db-status

# View active tasks
crypto-newsletter tasks-active

# Cancel problematic tasks
crypto-newsletter task-cancel <task-id>

# Reset development environment
crypto-newsletter dev-reset
```

## Rich Output Features

The CLI uses Rich library for enhanced output:

- **Colored text** and **styled formatting**
- **Tables** for structured data display
- **Progress bars** for long-running operations
- **Panels** for important information
- **Syntax highlighting** for code and data

## Error Handling

The CLI provides comprehensive error handling:

- **Graceful exits** with appropriate exit codes
- **Detailed error messages** with context
- **Keyboard interrupt handling** (Ctrl+C)
- **Import error detection** for missing dependencies

## Environment Variables

The CLI respects all application environment variables:

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `COINDESK_API_KEY` - CoinDesk API authentication
- `RAILWAY_ENVIRONMENT` - Environment mode
- `DEBUG` - Debug mode toggle
- `ENABLE_CELERY` - Celery functionality toggle

## Tips & Best Practices

1. **Use `--help`** with any command for detailed options
2. **Start with `health`** to verify system status
3. **Use `config-test`** before running operations
4. **Monitor with `tasks-active`** during heavy processing
5. **Export data regularly** for backup and analysis
6. **Use `dev-reset`** when encountering cache issues
7. **Check `db-status`** for database health monitoring

For more detailed information about specific commands, use:
```bash
crypto-newsletter <command> --help
```
