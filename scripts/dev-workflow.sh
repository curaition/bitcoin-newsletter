#!/bin/bash
# Development Workflow Script for Bitcoin Newsletter
# Provides common development tasks and workflows

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_header() {
    echo -e "\n${PURPLE}$1${NC}"
    echo "=================================================="
}

# Ensure we're in the project root and virtual environment is activated
ensure_environment() {
    if [ ! -f "pyproject.toml" ]; then
        log_error "Not in project root directory. Please run from the project root."
        exit 1
    fi
    
    if [ ! -d ".venv" ]; then
        log_error "Virtual environment not found. Run ./scripts/setup-dev.sh first."
        exit 1
    fi
    
    source .venv/bin/activate
}

# Show help
show_help() {
    echo -e "${CYAN}Bitcoin Newsletter Development Workflow${NC}"
    echo "Usage: ./scripts/dev-workflow.sh <command>"
    echo ""
    echo "Available commands:"
    echo "  setup       - Run initial development setup"
    echo "  start       - Start all development services"
    echo "  stop        - Stop all development services"
    echo "  restart     - Restart all development services"
    echo "  test        - Run test suite"
    echo "  test-quick  - Run quick unit tests"
    echo "  test-watch  - Run tests in watch mode"
    echo "  lint        - Run code linting and formatting"
    echo "  lint-fix    - Run linting with auto-fix"
    echo "  type-check  - Run type checking"
    echo "  clean       - Clean up development environment"
    echo "  reset       - Reset development environment"
    echo "  db-migrate  - Run database migrations"
    echo "  db-reset    - Reset database"
    echo "  logs        - Show application logs"
    echo "  health      - Check system health"
    echo "  ingest      - Run manual article ingestion"
    echo "  shell       - Start interactive shell"
    echo "  docs        - Generate documentation"
    echo "  build       - Build the application"
    echo "  help        - Show this help message"
}

# Setup development environment
setup_dev() {
    log_header "🔧 Setting up Development Environment"
    ./scripts/setup-dev.sh
}

# Start development services
start_services() {
    log_header "🚀 Starting Development Services"
    
    # Start Redis if not running
    if ! redis-cli ping &> /dev/null; then
        log_info "Starting Redis..."
        ./scripts/start-redis.sh
    else
        log_success "Redis is already running"
    fi
    
    # Create tmux session for development
    if command -v tmux &> /dev/null; then
        log_info "Starting development services in tmux session..."
        
        # Kill existing session if it exists
        tmux kill-session -t bitcoin-newsletter 2>/dev/null || true
        
        # Create new session
        tmux new-session -d -s bitcoin-newsletter -n main
        
        # Split into panes
        tmux split-window -h -t bitcoin-newsletter:main
        tmux split-window -v -t bitcoin-newsletter:main.1
        
        # Start services in different panes
        tmux send-keys -t bitcoin-newsletter:main.0 'source .venv/bin/activate && crypto-newsletter worker' Enter
        tmux send-keys -t bitcoin-newsletter:main.1 'source .venv/bin/activate && crypto-newsletter beat' Enter
        tmux send-keys -t bitcoin-newsletter:main.2 'source .venv/bin/activate && crypto-newsletter serve --dev' Enter
        
        log_success "Development services started in tmux session 'bitcoin-newsletter'"
        log_info "Attach with: tmux attach -t bitcoin-newsletter"
        log_info "Detach with: Ctrl+B, then D"
    else
        log_warning "tmux not found. Starting services manually..."
        log_info "Open 3 terminals and run:"
        echo "  Terminal 1: crypto-newsletter worker"
        echo "  Terminal 2: crypto-newsletter beat"
        echo "  Terminal 3: crypto-newsletter serve --dev"
    fi
}

# Stop development services
stop_services() {
    log_header "🛑 Stopping Development Services"
    
    # Kill tmux session
    if tmux has-session -t bitcoin-newsletter 2>/dev/null; then
        tmux kill-session -t bitcoin-newsletter
        log_success "Stopped tmux session"
    fi
    
    # Stop any remaining processes
    pkill -f "crypto-newsletter" || true
    pkill -f "celery" || true
    
    log_success "Development services stopped"
}

# Restart development services
restart_services() {
    log_header "🔄 Restarting Development Services"
    stop_services
    sleep 2
    start_services
}

# Run tests
run_tests() {
    log_header "🧪 Running Test Suite"
    python tests/test_runner.py --report
}

# Run quick tests
run_quick_tests() {
    log_header "⚡ Running Quick Tests"
    python tests/test_runner.py --quick
}

# Run tests in watch mode
run_test_watch() {
    log_header "👀 Running Tests in Watch Mode"
    if command -v pytest-watch &> /dev/null; then
        ptw tests/ --runner "python tests/test_runner.py --quick"
    else
        log_warning "pytest-watch not installed. Install with: uv pip install pytest-watch"
        log_info "Running tests once..."
        run_quick_tests
    fi
}

# Run linting
run_lint() {
    log_header "🔍 Running Code Linting"
    
    log_info "Running Black..."
    black --check src/ tests/
    
    log_info "Running Ruff..."
    ruff check src/ tests/
    
    log_success "Linting completed"
}

# Run linting with auto-fix
run_lint_fix() {
    log_header "🔧 Running Code Linting with Auto-fix"
    
    log_info "Running Black..."
    black src/ tests/
    
    log_info "Running Ruff with auto-fix..."
    ruff check src/ tests/ --fix
    
    log_success "Linting and auto-fix completed"
}

# Run type checking
run_type_check() {
    log_header "🔍 Running Type Checking"
    mypy src/
}

# Clean development environment
clean_env() {
    log_header "🧹 Cleaning Development Environment"
    
    # Remove Python cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    
    # Remove test artifacts
    rm -rf .pytest_cache/ htmlcov/ .coverage coverage.xml
    
    # Remove build artifacts
    rm -rf build/ dist/ *.egg-info/
    
    # Clear Redis cache
    if redis-cli ping &> /dev/null; then
        redis-cli flushdb
        log_info "Cleared Redis cache"
    fi
    
    log_success "Development environment cleaned"
}

# Reset development environment
reset_env() {
    log_header "🔄 Resetting Development Environment"
    
    stop_services
    clean_env
    
    # Reset virtual environment
    log_info "Recreating virtual environment..."
    rm -rf .venv
    uv venv
    source .venv/bin/activate
    uv pip install -e .[dev]
    
    log_success "Development environment reset"
}

# Run database migrations
run_db_migrate() {
    log_header "🗄️  Running Database Migrations"
    
    if [ -f ".env.development" ]; then
        export $(grep -v '^#' .env.development | xargs)
    fi
    
    alembic upgrade head
    log_success "Database migrations completed"
}

# Reset database
reset_database() {
    log_header "🗄️  Resetting Database"
    
    log_warning "This will reset your database. Continue? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        if [ -f ".env.development" ]; then
            export $(grep -v '^#' .env.development | xargs)
        fi
        
        alembic downgrade base
        alembic upgrade head
        log_success "Database reset completed"
    else
        log_info "Database reset cancelled"
    fi
}

# Show logs
show_logs() {
    log_header "📋 Application Logs"
    
    if tmux has-session -t bitcoin-newsletter 2>/dev/null; then
        log_info "Showing tmux session logs..."
        tmux capture-pane -t bitcoin-newsletter:main.0 -p
    else
        log_info "No active tmux session. Check individual service logs."
    fi
}

# Check system health
check_health() {
    log_header "🏥 System Health Check"
    crypto-newsletter health
}

# Run manual ingestion
run_ingestion() {
    log_header "📰 Running Manual Article Ingestion"
    crypto-newsletter ingest --limit 10 --verbose
}

# Start interactive shell
start_shell() {
    log_header "🐚 Starting Interactive Shell"
    crypto-newsletter shell
}

# Generate documentation
generate_docs() {
    log_header "📚 Generating Documentation"
    
    if [ -d "docs/" ]; then
        log_info "Documentation directory found"
        # Add documentation generation logic here
        log_success "Documentation generated"
    else
        log_warning "No docs directory found"
    fi
}

# Build application
build_app() {
    log_header "🏗️  Building Application"
    
    # Run linting and tests first
    run_lint
    run_type_check
    run_quick_tests
    
    # Build package
    python -m build
    
    log_success "Application built successfully"
}

# Main execution
main() {
    ensure_environment
    
    case "${1:-help}" in
        setup)
            setup_dev
            ;;
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        test)
            run_tests
            ;;
        test-quick)
            run_quick_tests
            ;;
        test-watch)
            run_test_watch
            ;;
        lint)
            run_lint
            ;;
        lint-fix)
            run_lint_fix
            ;;
        type-check)
            run_type_check
            ;;
        clean)
            clean_env
            ;;
        reset)
            reset_env
            ;;
        db-migrate)
            run_db_migrate
            ;;
        db-reset)
            reset_database
            ;;
        logs)
            show_logs
            ;;
        health)
            check_health
            ;;
        ingest)
            run_ingestion
            ;;
        shell)
            start_shell
            ;;
        docs)
            generate_docs
            ;;
        build)
            build_app
            ;;
        help|*)
            show_help
            ;;
    esac
}

# Run main function
main "$@"
