# Use Python 3.11 image with build tools already included
FROM python:3.11

# Set working directory
WORKDIR /app

# Install UV directly
RUN pip install uv

# Copy dependency files first (for better caching)
COPY pyproject.toml ./
COPY uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PATH="/app/.venv/bin:$PATH"

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "start_processes.py"]
