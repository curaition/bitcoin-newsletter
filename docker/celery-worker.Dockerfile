# Celery Worker Dockerfile for Railway deployment
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-cache

# Copy application code
COPY src/ ./src/
COPY alembic.ini ./
COPY alembic/ ./alembic/

# Set Python path
ENV PYTHONPATH=/app/src

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash celery
USER celery

# Default command (can be overridden)
CMD ["uv", "run", "celery", "-A", "crypto_newsletter.shared.celery.app", "worker", "--loglevel=INFO", "--concurrency=2", "--queues=default,ingestion,monitoring,maintenance"]
