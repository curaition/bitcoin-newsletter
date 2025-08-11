#!/bin/bash
# Development Environment Setup Script for Bitcoin Newsletter
# This script sets up a complete development environment from scratch

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
    echo -e "\n${BLUE}$1${NC}"
    echo "=================================================="
}

# Check if we're in the project root
check_project_root() {
    if [ ! -f "pyproject.toml" ]; then
        log_error "Not in project root directory. Please run from the project root."
        exit 1
    fi
}

# Check system requirements
check_system_requirements() {
    log_header "🔍 Checking System Requirements"
    
    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_info "Python version: $PYTHON_VERSION"
        
        # Check if Python 3.11+
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
            log_success "Python 3.11+ detected"
        else
            log_error "Python 3.11+ required. Current version: $PYTHON_VERSION"
            exit 1
        fi
    else
        log_error "Python 3 not found. Please install Python 3.11+"
        exit 1
    fi
    
    # Check Git
    if command -v git &> /dev/null; then
        log_success "Git is installed"
    else
        log_error "Git not found. Please install Git"
        exit 1
    fi
    
    # Check if UV is installed
    if command -v uv &> /dev/null; then
        UV_VERSION=$(uv --version | cut -d' ' -f2)
        log_success "UV is installed (version: $UV_VERSION)"
    else
        log_warning "UV not found. Installing UV..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
        
        if command -v uv &> /dev/null; then
            log_success "UV installed successfully"
        else
            log_error "Failed to install UV. Please install manually: https://docs.astral.sh/uv/"
            exit 1
        fi
    fi
}

# Setup Python environment
setup_python_environment() {
    log_header "🐍 Setting up Python Environment"
    
    # Create virtual environment
    if [ ! -d ".venv" ]; then
        log_info "Creating virtual environment..."
        uv venv
        log_success "Virtual environment created"
    else
        log_info "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    log_info "Activating virtual environment..."
    source .venv/bin/activate
    
    # Install dependencies
    log_info "Installing dependencies..."
    uv pip install -e .[dev]
    log_success "Dependencies installed"
}

# Setup pre-commit hooks
setup_pre_commit() {
    log_header "🪝 Setting up Pre-commit Hooks"
    
    if [ -f ".pre-commit-config.yaml" ]; then
        log_info "Installing pre-commit hooks..."
        source .venv/bin/activate
        pre-commit install
        log_success "Pre-commit hooks installed"
        
        # Run pre-commit on all files to ensure everything is set up correctly
        log_info "Running pre-commit on all files..."
        pre-commit run --all-files || log_warning "Some pre-commit checks failed (this is normal for first run)"
    else
        log_warning "No .pre-commit-config.yaml found, skipping pre-commit setup"
    fi
}

# Setup environment variables
setup_environment_variables() {
    log_header "🔧 Setting up Environment Variables"
    
    if [ ! -f ".env.development" ]; then
        if [ -f ".env.example" ]; then
            log_info "Creating .env.development from .env.example..."
            cp .env.example .env.development
            log_success ".env.development created"
            log_warning "Please edit .env.development with your configuration"
        else
            log_warning "No .env.example found, creating basic .env.development..."
            cat > .env.development << EOF
# Development Environment Configuration
RAILWAY_ENVIRONMENT=development
SERVICE_TYPE=web
DEBUG=true
TESTING=false

# Database (use your Neon database URL)
DATABASE_URL=postgresql://user:password@host/database

# Redis (local development)
REDIS_URL=redis://localhost:6379/0

# CoinDesk API
COINDESK_API_KEY=your-api-key-here
COINDESK_BASE_URL=https://data-api.coindesk.com

# Celery
ENABLE_CELERY=true

# Logging
LOG_LEVEL=DEBUG

# Server
PORT=8000
EOF
            log_success "Basic .env.development created"
            log_warning "Please edit .env.development with your actual configuration"
        fi
    else
        log_info ".env.development already exists"
    fi
}

# Check external dependencies
check_external_dependencies() {
    log_header "🔍 Checking External Dependencies"
    
    # Check Redis
    if command -v redis-server &> /dev/null; then
        log_success "Redis is installed"
        
        # Check if Redis is running
        if redis-cli ping &> /dev/null 2>&1; then
            log_success "Redis is running"
        else
            log_warning "Redis is not running. You can start it with: ./scripts/start-redis.sh"
        fi
    else
        log_warning "Redis not found. Install with:"
        log_info "  macOS: brew install redis"
        log_info "  Ubuntu: sudo apt-get install redis-server"
        log_info "  Docker: docker run -d -p 6379:6379 redis:alpine"
    fi
    
    # Check PostgreSQL client (for database operations)
    if command -v psql &> /dev/null; then
        log_success "PostgreSQL client is installed"
    else
        log_warning "PostgreSQL client not found. Install with:"
        log_info "  macOS: brew install postgresql"
        log_info "  Ubuntu: sudo apt-get install postgresql-client"
    fi
}

# Initialize database
initialize_database() {
    log_header "🗄️  Initializing Database"
    
    source .venv/bin/activate
    
    # Check if alembic is configured
    if [ -f "alembic.ini" ]; then
        log_info "Running database migrations..."
        
        # Check if DATABASE_URL is set
        if [ -f ".env.development" ]; then
            export $(grep -v '^#' .env.development | xargs)
        fi
        
        if [ -z "$DATABASE_URL" ]; then
            log_warning "DATABASE_URL not set. Please configure your database connection in .env.development"
        else
            # Try to run migrations
            if alembic upgrade head; then
                log_success "Database migrations completed"
            else
                log_warning "Database migrations failed. Please check your DATABASE_URL and database connectivity"
            fi
        fi
    else
        log_warning "No alembic.ini found, skipping database initialization"
    fi
}

# Run tests to verify setup
verify_setup() {
    log_header "🧪 Verifying Setup"
    
    source .venv/bin/activate
    
    log_info "Running quick tests..."
    if python tests/test_runner.py --quick; then
        log_success "Quick tests passed"
    else
        log_warning "Some tests failed. This might be due to missing configuration or external dependencies"
    fi
    
    log_info "Testing CLI..."
    if crypto-newsletter --help > /dev/null; then
        log_success "CLI is working"
    else
        log_warning "CLI test failed"
    fi
}

# Display next steps
show_next_steps() {
    log_header "🎉 Setup Complete!"
    
    echo ""
    log_info "Next steps:"
    echo "1. Edit .env.development with your configuration"
    echo "2. Start Redis: ./scripts/start-redis.sh"
    echo "3. Start development environment: ./scripts/dev-start.sh"
    echo ""
    log_info "Development commands:"
    echo "• Start web server: crypto-newsletter serve --dev"
    echo "• Run worker: crypto-newsletter worker"
    echo "• Run scheduler: crypto-newsletter beat"
    echo "• Run tests: python tests/test_runner.py"
    echo "• Check health: crypto-newsletter health"
    echo ""
    log_info "Useful aliases (add to your shell profile):"
    echo "alias cn='crypto-newsletter'"
    echo "alias cn-dev='source .venv/bin/activate && crypto-newsletter'"
    echo ""
    log_success "Development environment is ready! 🚀"
}

# Main execution
main() {
    log_header "🚀 Bitcoin Newsletter Development Setup"
    
    check_project_root
    check_system_requirements
    setup_python_environment
    setup_pre_commit
    setup_environment_variables
    check_external_dependencies
    initialize_database
    verify_setup
    show_next_steps
}

# Run main function
main "$@"
