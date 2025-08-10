# Bitcoin Newsletter

AI-powered cryptocurrency newsletter with signal detection and automated content generation.

## Overview

This project implements a comprehensive crypto newsletter system that:
- Ingests articles from CoinDesk API every 4 hours
- Processes and deduplicates content automatically
- Generates AI-powered newsletters with signal detection
- Deploys on Railway with Neon database backend

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

## Development Commands

```bash
# Development server
uv run crypto-newsletter serve --dev

# Manual article ingestion
uv run crypto-newsletter ingest-articles

# Run tests
uv run pytest

# Code formatting
uv run black src/ tests/
uv run ruff check src/ tests/ --fix

# Type checking
uv run mypy src/

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
