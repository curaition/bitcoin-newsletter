#!/bin/bash

# Bitcoin Newsletter - Railway Setup Validation Script
# This script validates the complete Railway development environment setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Validation functions
validate_railway_cli() {
    print_status "Validating Railway CLI..."
    if command -v railway &> /dev/null; then
        print_success "Railway CLI is installed"
        railway --version
    else
        print_error "Railway CLI is not installed"
        echo "Install with: curl -fsSL https://railway.com/install.sh | sh"
        return 1
    fi
}

validate_project_link() {
    print_status "Validating Railway project link..."
    if railway status &> /dev/null; then
        print_success "Project is linked to Railway"
        railway status
    else
        print_error "Project is not linked to Railway"
        echo "Link with: railway link -p 6115f406-107e-45c3-85d4-d720c3638053"
        return 1
    fi
}

validate_main_py() {
    print_status "Validating main.py Celery app..."
    if [ -f "main.py" ]; then
        print_success "main.py exists"
        python main.py | head -10
    else
        print_error "main.py not found"
        return 1
    fi
}

validate_scripts() {
    print_status "Validating development scripts..."
    
    if [ -f "scripts/dev-railway.sh" ] && [ -x "scripts/dev-railway.sh" ]; then
        print_success "dev-railway.sh exists and is executable"
    else
        print_error "dev-railway.sh missing or not executable"
        return 1
    fi
    
    if [ -f "scripts/test-railway-tasks.sh" ] && [ -x "scripts/test-railway-tasks.sh" ]; then
        print_success "test-railway-tasks.sh exists and is executable"
    else
        print_error "test-railway-tasks.sh missing or not executable"
        return 1
    fi
}

validate_environment_variables() {
    print_status "Validating Railway environment variables..."
    
    # Test if we can get environment variables from Railway
    if railway run printenv | grep -q "DATABASE_URL"; then
        print_success "DATABASE_URL is available via Railway"
    else
        print_warning "DATABASE_URL not found in Railway environment"
    fi
    
    if railway run printenv | grep -q "COINDESK_API_KEY"; then
        print_success "COINDESK_API_KEY is available via Railway"
    else
        print_warning "COINDESK_API_KEY not found in Railway environment"
    fi
    
    if railway run printenv | grep -q "REDIS_URL"; then
        print_success "REDIS_URL is available via Railway"
    else
        print_warning "REDIS_URL not found in Railway environment"
    fi
}

validate_celery_app() {
    print_status "Validating Celery app configuration..."
    
    railway run python -c "
from main import app
print(f'✅ Celery app loaded successfully')
print(f'📋 Tasks found: {len([t for t in app.tasks.keys() if not t.startswith(\"celery.\")])}')
print(f'⏰ Beat schedule configured: {bool(app.conf.beat_schedule)}')
" 2>/dev/null || {
        print_error "Failed to load Celery app via Railway"
        return 1
    }
}

validate_database_connection() {
    print_status "Validating database connection..."

    railway run python -c "
import sys
sys.path.insert(0, 'src')
import asyncio

from crypto_newsletter.shared.database.connection import get_db_session
from crypto_newsletter.shared.models import Article
from sqlalchemy import select

async def test_db():
    try:
        async with get_db_session() as session:
            result = await session.execute(select(Article))
            articles = result.scalars().all()
            print(f'✅ Database connection successful')
            print(f'📊 Articles in database: {len(articles)}')
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        exit(1)

asyncio.run(test_db())
" 2>/dev/null || {
        print_error "Database connection validation failed"
        return 1
    }
}

# Main validation
main() {
    echo ""
    print_status "🧪 Bitcoin Newsletter - Railway Setup Validation"
    echo ""
    
    # Track validation results
    VALIDATION_ERRORS=0
    
    # Run all validations
    validate_railway_cli || ((VALIDATION_ERRORS++))
    echo ""
    
    validate_project_link || ((VALIDATION_ERRORS++))
    echo ""
    
    validate_main_py || ((VALIDATION_ERRORS++))
    echo ""
    
    validate_scripts || ((VALIDATION_ERRORS++))
    echo ""
    
    validate_environment_variables || ((VALIDATION_ERRORS++))
    echo ""
    
    validate_celery_app || ((VALIDATION_ERRORS++))
    echo ""
    
    validate_database_connection || ((VALIDATION_ERRORS++))
    echo ""
    
    # Summary
    if [ $VALIDATION_ERRORS -eq 0 ]; then
        print_success "🎉 All validations passed! Railway development environment is ready."
        echo ""
        print_status "Next steps:"
        echo "  1. Start development: ./scripts/dev-railway.sh"
        echo "  2. Test tasks: ./scripts/test-railway-tasks.sh"
        echo "  3. Monitor: Check Railway dashboard for logs"
    else
        print_error "❌ $VALIDATION_ERRORS validation(s) failed. Please fix the issues above."
        exit 1
    fi
}

# Run main function
main "$@"
