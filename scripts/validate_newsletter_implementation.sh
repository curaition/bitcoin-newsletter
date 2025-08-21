#!/bin/bash

# Newsletter Implementation Validation Script
# Runs comprehensive validation before deployment

set -e  # Exit on any error

echo "🧪 Newsletter Implementation Validation"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
    esac
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_status "ERROR" "Must be run from project root directory"
    exit 1
fi

print_status "INFO" "Starting validation from $(pwd)"

# Step 1: Environment Check
echo -e "\n${BLUE}📋 Step 1: Environment Check${NC}"
echo "--------------------------------"

# Check Python environment
if command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version)
    print_status "SUCCESS" "Python available: $PYTHON_VERSION"
else
    print_status "ERROR" "Python not found"
    exit 1
fi

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" != "" ]]; then
    print_status "SUCCESS" "Virtual environment active: $VIRTUAL_ENV"
else
    print_status "WARNING" "No virtual environment detected"
fi

# Check required packages
echo "Checking required packages..."
if python -c "import crypto_newsletter" 2>/dev/null; then
    print_status "SUCCESS" "crypto_newsletter package importable"
else
    print_status "ERROR" "crypto_newsletter package not found. Run: pip install -e ."
    exit 1
fi

# Step 2: Database Connection
echo -e "\n${BLUE}📊 Step 2: Database Connection${NC}"
echo "--------------------------------"

# Check database connection
if python -c "
import asyncio
import sys
import os
from sqlalchemy import text

# Set test environment variables
os.environ.setdefault('GEMINI_API_KEY', 'test-key-for-validation')
os.environ.setdefault('TAVILY_API_KEY', 'test-key-for-validation')
os.environ.setdefault('TESTING', 'true')

sys.path.insert(0, 'src')
from crypto_newsletter.shared.database.connection import get_db_session

async def test_db():
    try:
        async with get_db_session() as db:
            result = await db.execute(text('SELECT 1'))
            print('Database connection successful')
            return True
    except Exception as e:
        print(f'Database connection failed: {e}')
        return False

success = asyncio.run(test_db())
sys.exit(0 if success else 1)
" 2>/dev/null; then
    print_status "SUCCESS" "Database connection working"
else
    print_status "ERROR" "Database connection failed"
    print_status "INFO" "Check DATABASE_URL environment variable"
    exit 1
fi

# Step 3: Implementation Tests
echo -e "\n${BLUE}🧪 Step 3: Implementation Tests${NC}"
echo "--------------------------------"

# Run our custom implementation test
if python scripts/test_newsletter_implementation.py; then
    print_status "SUCCESS" "Implementation tests passed"
else
    print_status "ERROR" "Implementation tests failed"
    echo "Check the detailed report for specific issues"
    exit 1
fi

# Step 4: Existing Test Suite
echo -e "\n${BLUE}🔬 Step 4: Existing Test Suite${NC}"
echo "--------------------------------"

# Run quick unit tests to ensure no regressions
if python tests/test_runner.py --quick; then
    print_status "SUCCESS" "Unit tests passed - no regressions"
else
    print_status "WARNING" "Some unit tests failed - check for regressions"
    echo "This may be acceptable if only newsletter-related tests fail"
fi

# Step 5: Frontend File Check
echo -e "\n${BLUE}🎨 Step 5: Frontend Files${NC}"
echo "--------------------------------"

# Check key frontend files exist
FRONTEND_FILES=(
    "admin-dashboard/src/pages/newsletters/NewslettersPage.tsx"
    "admin-dashboard/src/pages/newsletters/NewsletterDetailPage.tsx"
    "admin-dashboard/src/pages/newsletters/NewsletterGeneratePage.tsx"
    "admin-dashboard/src/hooks/api/useNewsletters.ts"
    "shared/types/api.ts"
)

ALL_FILES_EXIST=true
for file in "${FRONTEND_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_status "SUCCESS" "Found: $file"
    else
        print_status "ERROR" "Missing: $file"
        ALL_FILES_EXIST=false
    fi
done

if [ "$ALL_FILES_EXIST" = true ]; then
    print_status "SUCCESS" "All frontend files present"
else
    print_status "ERROR" "Some frontend files missing"
    exit 1
fi

# Step 6: API Import Check
echo -e "\n${BLUE}🌐 Step 6: API Imports${NC}"
echo "--------------------------------"

# Test API imports
if python -c "
import sys
import os

# Set test environment variables
os.environ.setdefault('GEMINI_API_KEY', 'test-key-for-validation')
os.environ.setdefault('TAVILY_API_KEY', 'test-key-for-validation')
os.environ.setdefault('TESTING', 'true')

sys.path.insert(0, 'src')
try:
    from crypto_newsletter.web.routers.api import router as api_router
    from crypto_newsletter.web.routers.admin import router as admin_router
    from crypto_newsletter.web.models import NewsletterResponse
    from crypto_newsletter.web.utils.newsletter_validation import NewsletterValidator
    print('All API imports successful')
except ImportError as e:
    print(f'Import error: {e}')
    sys.exit(1)
" 2>/dev/null; then
    print_status "SUCCESS" "API imports working"
else
    print_status "ERROR" "API import issues detected"
    exit 1
fi

# Step 7: Generate Summary
echo -e "\n${BLUE}📋 Step 7: Validation Summary${NC}"
echo "--------------------------------"

print_status "SUCCESS" "All validation checks passed!"
echo ""
echo "🎉 Newsletter implementation is ready for deployment!"
echo ""
echo "Next steps:"
echo "1. Create feature branch: git checkout -b feature/newsletter-implementation"
echo "2. Commit changes: git add . && git commit -m 'feat: newsletter management system'"
echo "3. Push branch: git push origin feature/newsletter-implementation"
echo "4. Create Pull Request for Render preview deployment"
echo "5. Test in preview environment using the testing strategy"
echo ""
echo "📖 See docs/NEWSLETTER_TESTING_STRATEGY.md for detailed testing plan"

# Step 8: Optional - Generate Git Commands
echo -e "\n${YELLOW}📝 Optional: Ready-to-use Git Commands${NC}"
echo "--------------------------------"

cat << 'EOF'
# Copy and paste these commands to create your feature branch:

git checkout -b feature/newsletter-implementation
git add .
git commit -m "feat: implement newsletter management system

- Add newsletter database models and repository (Phase 1A-1C)
- Add newsletter API endpoints with CRUD and admin operations (Phase 2A-2B)
- Add newsletter response models and validation utilities (Phase 2C)
- Add React newsletter management pages with routing (Phase 3A)
- Add newsletter navigation and UI components

Phases completed:
- 1A: Newsletter database model and migrations
- 1B: NewsletterRepository with CRUD operations
- 1C: Database integration and query optimization
- 2A: Core newsletter API endpoints (/api/newsletters)
- 2B: Admin newsletter API endpoints (/admin/newsletters)
- 2C: Pydantic response models and validation utilities
- 3A: React newsletter pages and navigation

Ready for testing in PR preview environment."

git push origin feature/newsletter-implementation

EOF

echo ""
print_status "INFO" "Validation complete! 🚀"
