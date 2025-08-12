#!/bin/bash

# Bitcoin Newsletter - Railway Development Environment
# This script starts local development using Railway's cloud infrastructure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Railway CLI is installed
check_railway_cli() {
    if ! command -v railway &> /dev/null; then
        print_error "Railway CLI is not installed!"
        echo ""
        echo "Please install it using one of these methods:"
        echo "  curl -fsSL https://railway.com/install.sh | sh"
        echo "  npm i -g @railway/cli"
        echo ""
        exit 1
    fi
    print_success "Railway CLI is installed"
}

# Check if project is linked
check_project_link() {
    if ! railway status &> /dev/null; then
        print_error "Project is not linked to Railway!"
        echo ""
        echo "Please link to the project using:"
        echo "  railway link -p 6115f406-107e-45c3-85d4-d720c3638053"
        echo ""
        exit 1
    fi
    print_success "Project is linked to Railway"
}

# Display Railway project info
show_project_info() {
    print_status "Railway Project Information:"
    railway status
    echo ""
}

# Check if main.py exists
check_main_py() {
    if [ ! -f "main.py" ]; then
        print_error "main.py not found! This file is required for Railway compatibility."
        exit 1
    fi
    print_success "main.py found"
}

# Start the development server
start_dev_server() {
    print_status "Starting Bitcoin Newsletter development server..."
    print_status "Using Railway infrastructure for:"
    print_status "  - Redis (message broker)"
    print_status "  - Celery Worker (task processing)"
    print_status "  - Celery Beat (task scheduling)"
    print_status "  - Environment variables"
    echo ""
    print_status "Local web server will be available at: http://localhost:8000"
    print_warning "Press Ctrl+C to stop the server"
    echo ""
    
    # Use Railway to run the local development server with cloud environment
    railway run uvicorn crypto_newsletter.web.main:app --host 0.0.0.0 --port 8000 --reload
}

# Main execution
main() {
    echo ""
    print_status "🚀 Bitcoin Newsletter - Railway Development Environment"
    echo ""
    
    check_railway_cli
    check_project_link
    check_main_py
    show_project_info
    start_dev_server
}

# Run main function
main "$@"
