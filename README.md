# Bitcoin Newsletter

<!-- Phase 1 Preview Environment Test -->

AI-powered cryptocurrency newsletter with signal detection and automated content generation.

## Overview

This project implements a comprehensive crypto newsletter system that:
- Ingests articles from CoinDesk API every 4 hours
- Processes and deduplicates content automatically
- Generates AI-powered newsletters with signal detection
- Deploys on Railway with Neon database backend

## Features

### 🔍 Intelligent Signal Detection
- **Multi-Agent Analysis**: PydanticAI-powered system with specialized agents for content analysis and signal validation
- **Weak Signal Identification**: Detects early indicators of market shifts, regulatory changes, and technological developments
- **Pattern Anomaly Detection**: Identifies deviations from expected market patterns and behaviors
- **Adjacent Possibility Mapping**: Discovers connections between crypto developments and external domains
- **Quality Validation**: Comprehensive validation system ensuring signal accuracy and relevance

### 📰 Enhanced Newsletter Generation
- **Real-time Progress Tracking**: Step-by-step visualization of newsletter generation with live updates
- **Quality Validation Gates**: Automated quality checks at each generation step with configurable thresholds
- **Rich Citation System**: Proper article citations with URLs and signal confidence scores
- **Daily & Weekly Newsletters**: Automated generation based on analyzed articles and detected signals
- **Story Selection**: AI-powered selection of the most revealing and unique stories with transparency
- **Synthesis & Analysis**: Cross-story pattern identification and thematic analysis with preview
- **Editorial Quality**: Professional newsletter writing with enhanced prompts and validation
- **Manual Override**: Admin interface with progress monitoring and error recovery

### 📊 Advanced Monitoring & Alerting
- **Real-time Progress Visualization**: Live tracking of newsletter generation with step indicators
- **Quality Metrics Dashboard**: Comprehensive tracking of generation quality, citations, and success rates
- **Intelligent Alert System**: Automated alerts for quality degradation, failures, and stuck processes
- **Performance Analytics**: Detailed metrics for signal detection, generation times, and cost tracking
- **Health Monitoring**: System, database, and external API monitoring with proactive issue detection
- **Admin Dashboard**: Enhanced web interface with progress tracking and quality management

## Quick Start

### Prerequisites

- Python 3.11+
- UV package manager
- Git

### Setup

1. **Clone and setup environment:**
```bash
git clone <repository-url>
cd bitcoin_newsletter
```

2. **Install UV (if not already installed):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. **Create virtual environment and install dependencies:**
```bash
uv venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
uv pip install -e .[dev]
```

4. **Set up pre-commit hooks:**
```bash
pre-commit install
```

5. **Configure environment variables:**
```bash
cp .env.example .env.development
# Edit .env.development with your configuration
```

6. **Initialize database:**
```bash
alembic upgrade head
```

7. **Run tests:**
```bash
pytest
```

8. **Start development server:**
```bash
uv run crypto-newsletter serve --dev
```

## CLI Commands

The project includes a comprehensive CLI for managing all aspects of the application:

```bash
# Show all available commands
crypto-newsletter commands

# Health and monitoring
crypto-newsletter health              # Check system health
crypto-newsletter monitor             # Real-time monitoring dashboard
crypto-newsletter db-status           # Database status and statistics

# Data management
crypto-newsletter ingest              # Manual article ingestion
crypto-newsletter stats               # Show article statistics
crypto-newsletter export-data         # Export articles to JSON/CSV

# Services
crypto-newsletter serve --dev         # Start development server
crypto-newsletter worker              # Start Celery worker
crypto-newsletter beat                # Start Celery scheduler
crypto-newsletter flower              # Start monitoring interface

# Configuration
crypto-newsletter config-show         # Show current configuration
crypto-newsletter config-test         # Test all connections

# Development
crypto-newsletter dev-setup           # Setup development environment
crypto-newsletter shell               # Interactive Python shell
```

For detailed CLI documentation, see [CLI Usage Guide](docs/CLI_USAGE.md).

## Development Scripts

The project includes comprehensive development scripts for easy environment management:

### Quick Start
```bash
# Complete development setup
./scripts/setup-dev.sh

# Start development environment
./scripts/dev-workflow.sh start

# Run tests
./scripts/dev-workflow.sh test-quick
```

### Development Workflow
```bash
./scripts/dev-workflow.sh start       # Start all services
./scripts/dev-workflow.sh stop        # Stop all services
./scripts/dev-workflow.sh test        # Run full test suite
./scripts/dev-workflow.sh lint-fix    # Fix code formatting
./scripts/dev-workflow.sh clean       # Clean environment
```

### Database Management
```bash
./scripts/db-manager.sh migrate       # Run migrations
./scripts/db-manager.sh seed          # Add sample data
./scripts/db-manager.sh backup        # Create backup
./scripts/db-manager.sh stats         # Show statistics
```

### Monitoring & Maintenance
```bash
./scripts/monitor.sh status           # System status
./scripts/monitor.sh health           # Health check
./scripts/monitor.sh watch            # Real-time monitoring
./scripts/monitor.sh cleanup          # Clean old data
```

### Production Deployment
```bash
./scripts/deploy-production.sh deploy    # Deploy to production
./scripts/deploy-production.sh health    # Check production health
./scripts/deploy-production.sh rollback  # Rollback if needed
```

For detailed development documentation, see [Development Guide](docs/DEVELOPMENT.md).

## Manual Development Commands

```bash
# Code formatting
uv run black src/ tests/
uv run ruff check src/ tests/ --fix

# Type checking
uv run mypy src/

# Run tests
uv run pytest

# Database migrations
uv run alembic revision --autogenerate -m "Description"
uv run alembic upgrade head
```

## Architecture

- **FastAPI**: Web framework and API
- **Celery + Redis**: Task queue and scheduling
- **SQLAlchemy**: Database ORM with async support
- **Alembic**: Database migrations
- **UV**: Python package management
- **Railway**: Deployment platform
- **Neon**: PostgreSQL database

## Project Structure

```
src/crypto_newsletter/
├── core/               # Core Data Pipeline
│   ├── ingestion/      # CoinDesk API client
│   ├── storage/        # Database models
│   └── scheduling/     # Celery tasks
├── analysis/           # Signal Detection & Analysis
├── newsletter/         # Newsletter Generation
├── monitoring/         # Monitoring & Prompt Engineering
├── shared/             # Shared utilities
│   ├── database/       # DB connection
│   ├── config/         # Settings
│   └── utils/          # Common utilities
└── cli/                # Command-line interface
```

## Deployment

The project deploys to Railway with multiple services:
- **Web Service**: FastAPI application
- **Worker Service**: Celery workers
- **Beat Service**: Celery scheduler
- **Redis Service**: Task queue backend

External services:
- **Neon Database**: PostgreSQL database

## Contributing

1. Create a feature branch
2. Make changes with tests
3. Run pre-commit hooks
4. Submit pull request

## License

MIT License
