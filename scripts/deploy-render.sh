#!/bin/bash

# Bitcoin Newsletter - Render Deployment Script
# This script helps deploy the Bitcoin Newsletter to Render

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
GITHUB_REPO_URL="https://github.com/curaition/bitcoin-newsletter.git"
RENDER_DASHBOARD_URL="https://dashboard.render.com"

echo -e "${BLUE}🚀 Bitcoin Newsletter - Render Deployment${NC}"
echo "=================================================="

# Function to print colored output
print_step() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ] || [ ! -f "render.yaml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

print_step "Pre-deployment checks passed"

# Check if git repo is clean and up to date
if [ -n "$(git status --porcelain)" ]; then
    print_warning "You have uncommitted changes. Committing them now..."
    git add .
    git commit -m "Prepare for Render deployment - $(date)"
fi

print_step "Git repository is ready"

# Push to GitHub
print_info "Pushing latest changes to GitHub..."
git push origin main
print_step "Code pushed to GitHub"

# Display deployment instructions
echo ""
echo -e "${BLUE}📋 RENDER DEPLOYMENT INSTRUCTIONS${NC}"
echo "=================================="
echo ""
echo "1. Go to Render Dashboard: ${RENDER_DASHBOARD_URL}"
echo ""
echo "2. Click 'New +' and select 'Blueprint'"
echo ""
echo "3. Connect your GitHub repository:"
echo "   - Repository: ${GITHUB_REPO_URL}"
echo "   - Branch: main"
echo ""
echo "4. Render will automatically detect the render.yaml file"
echo ""
echo "5. Review the services that will be created:"
echo "   ✅ bitcoin-newsletter-api (Web Service)"
echo "   ✅ bitcoin-newsletter-worker (Worker Service)"
echo "   ✅ bitcoin-newsletter-beat (Scheduler Service)"
echo "   ✅ bitcoin-newsletter-db (PostgreSQL Database)"
echo "   ✅ bitcoin-newsletter-redis (Redis Cache)"
echo ""
echo "6. Click 'Apply' to start deployment"
echo ""

# Option to use existing Neon database
echo -e "${YELLOW}💡 OPTIONAL: Use Existing Neon Database${NC}"
echo "============================================"
echo ""
echo "If you want to use your existing Neon database instead of creating a new one:"
echo ""
echo "1. In the Render dashboard, go to Environment Variables"
echo "2. Update DATABASE_URL to your Neon connection string:"
echo "   DATABASE_URL=postgresql+asyncpg://neondb_owner:npg_prKBLEUJ1f8P@ep-purple-firefly-ab009z0a-pooler.eu-west-2.aws.neon.tech/neondb"
echo ""
echo "3. Remove the database section from render.yaml if you prefer"
echo ""

# Environment variables checklist
echo -e "${BLUE}🔧 ENVIRONMENT VARIABLES CHECKLIST${NC}"
echo "=================================="
echo ""
echo "Verify these environment variables are set correctly in Render:"
echo ""
echo "✅ DATABASE_URL (auto-generated or your Neon URL)"
echo "✅ REDIS_URL (auto-generated from Redis service)"
echo "✅ CELERY_BROKER_URL (auto-generated from Redis service)"
echo "✅ CELERY_RESULT_BACKEND (auto-generated from Redis service)"
echo "✅ COINDESK_API_KEY (already set in render.yaml)"
echo "✅ ENVIRONMENT=production"
echo "✅ LOG_LEVEL=INFO"
echo ""

# Post-deployment verification
echo -e "${GREEN}🔍 POST-DEPLOYMENT VERIFICATION${NC}"
echo "================================"
echo ""
echo "After deployment completes, verify these endpoints:"
echo ""
echo "1. Health Check: https://your-app.onrender.com/health"
echo "2. API Documentation: https://your-app.onrender.com/docs"
echo "3. Detailed Health: https://your-app.onrender.com/health/detailed"
echo "4. Metrics: https://your-app.onrender.com/health/metrics"
echo ""

# CLI commands for testing
echo -e "${BLUE}🧪 TESTING COMMANDS${NC}"
echo "=================="
echo ""
echo "Once deployed, you can test the deployment using these commands:"
echo ""
echo "# Test health endpoint"
echo "curl https://your-app.onrender.com/health"
echo ""
echo "# Test article ingestion (if you want to trigger manually)"
echo "# This will be automated by the beat scheduler"
echo "curl -X POST https://your-app.onrender.com/api/admin/ingest"
echo ""

# Monitoring and logs
echo -e "${YELLOW}📊 MONITORING & LOGS${NC}"
echo "==================="
echo ""
echo "Monitor your deployment:"
echo ""
echo "1. Render Dashboard: View logs and metrics for all services"
echo "2. Service Logs: Check individual service logs for issues"
echo "3. Health Endpoints: Monitor application health"
echo "4. Database Metrics: Monitor database performance"
echo ""

# Troubleshooting
echo -e "${RED}🔧 TROUBLESHOOTING${NC}"
echo "=================="
echo ""
echo "Common issues and solutions:"
echo ""
echo "1. Build Failures:"
echo "   - Check that UV is properly installed in build command"
echo "   - Verify pyproject.toml dependencies"
echo ""
echo "2. Database Connection Issues:"
echo "   - Verify DATABASE_URL format"
echo "   - Check database service is running"
echo ""
echo "3. Redis Connection Issues:"
echo "   - Verify REDIS_URL is correctly set"
echo "   - Check Redis service is running"
echo ""
echo "4. Worker/Beat Not Processing:"
echo "   - Check worker service logs"
echo "   - Verify Celery environment variables"
echo ""

echo ""
print_step "Deployment guide complete!"
print_info "Open ${RENDER_DASHBOARD_URL} to start your deployment"
echo ""
