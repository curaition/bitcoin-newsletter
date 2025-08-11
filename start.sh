#!/bin/bash
set -e

echo "=== SHELL SCRIPT STARTED ==="
echo "Starting Crypto Newsletter application..."
echo "Working directory: $(pwd)"
echo "Python executable: $(which python)"
echo "UV executable: $(which uv)"
echo "PATH: $PATH"
echo "PYTHONPATH: $PYTHONPATH"

# List files to verify we're in the right place
echo "Files in current directory:"
ls -la

# Check if UV is working
echo "Testing UV..."
uv --version

# Ensure UV environment is properly activated
echo "Activating UV environment..."
export UV_SYSTEM_PYTHON=1
export PYTHONPATH="/app/src"

# Test UV run
echo "Testing UV run with simple command..."
uv run python --version

# Start the process manager using UV
echo "Starting process manager with UV..."
exec uv run --frozen python start_processes.py
