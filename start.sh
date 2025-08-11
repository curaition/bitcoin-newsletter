#!/bin/bash
set -e

echo "Starting Crypto Newsletter application..."
echo "Working directory: $(pwd)"
echo "Python executable: $(which python)"
echo "UV executable: $(which uv)"

# Ensure UV environment is properly activated
echo "Activating UV environment..."
export UV_SYSTEM_PYTHON=1
export PYTHONPATH="/app/src"

# Start the process manager using UV
echo "Starting process manager with UV..."
exec uv run --frozen python start_processes.py
