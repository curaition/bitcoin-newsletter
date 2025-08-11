#!/bin/bash
# Production Deployment Script for Bitcoin Newsletter
# Handles production deployment with safety checks and rollback capabilities

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

# Configuration
RAILWAY_PROJECT_ID="f672d6bf-ac6b-4d62-9a38-158919110629"
BACKUP_DIR="production-backups"
DEPLOYMENT_LOG="deployment.log"

# Ensure we're in the project root
ensure_project_root() {
    if [ ! -f "pyproject.toml" ]; then
        log_error "Not in project root directory. Please run from the project root."
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log_header "🔍 Checking Prerequisites"
    
    # Check Railway CLI
    if ! command -v railway &> /dev/null; then
        log_error "Railway CLI not found. Install with: npm install -g @railway/cli"
        exit 1
    fi
    
    # Check Git
    if ! command -v git &> /dev/null; then
        log_error "Git not found. Please install Git"
        exit 1
    fi
    
    # Check if we're logged into Railway
    if ! railway whoami &> /dev/null; then
        log_error "Not logged into Railway. Run: railway login"
        exit 1
    fi
    
    # Check if we have uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        log_warning "You have uncommitted changes. Please commit or stash them first."
        git status --porcelain
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Run pre-deployment tests
run_pre_deployment_tests() {
    log_header "🧪 Running Pre-deployment Tests"
    
    if [ ! -d ".venv" ]; then
        log_info "Creating virtual environment for testing..."
        uv venv
    fi
    
    source .venv/bin/activate
    
    # Install dependencies
    log_info "Installing dependencies..."
    uv pip install -e .[dev]
    
    # Run linting
    log_info "Running code linting..."
    black --check src/ tests/
    ruff check src/ tests/
    
    # Run type checking
    log_info "Running type checking..."
    mypy src/
    
    # Run tests
    log_info "Running test suite..."
    python tests/test_runner.py --type unit
    
    log_success "Pre-deployment tests passed"
}

# Create deployment backup
create_deployment_backup() {
    log_header "💾 Creating Deployment Backup"
    
    mkdir -p "$BACKUP_DIR"
    
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_NAME="backup_$TIMESTAMP"
    
    # Get current commit hash
    CURRENT_COMMIT=$(git rev-parse HEAD)
    
    # Create backup metadata
    cat > "$BACKUP_DIR/$BACKUP_NAME.json" << EOF
{
    "timestamp": "$TIMESTAMP",
    "commit_hash": "$CURRENT_COMMIT",
    "branch": "$(git branch --show-current)",
    "deployment_type": "production",
    "railway_project": "$RAILWAY_PROJECT_ID"
}
EOF
    
    log_success "Backup metadata created: $BACKUP_DIR/$BACKUP_NAME.json"
    
    # Export current Railway environment variables (for rollback)
    log_info "Backing up Railway environment variables..."
    railway variables --json > "$BACKUP_DIR/$BACKUP_NAME.env.json" || log_warning "Could not backup environment variables"
    
    echo "$BACKUP_NAME" > "$BACKUP_DIR/latest_backup.txt"
    log_success "Deployment backup created: $BACKUP_NAME"
}

# Deploy to Railway
deploy_to_railway() {
    log_header "🚀 Deploying to Railway"
    
    # Link to Railway project
    log_info "Linking to Railway project..."
    railway link "$RAILWAY_PROJECT_ID"
    
    # Push to GitHub (Railway deploys from GitHub)
    log_info "Pushing to GitHub..."
    git push origin main
    
    # Trigger Railway deployment
    log_info "Triggering Railway deployment..."
    railway up --detach
    
    log_success "Deployment triggered"
}

# Wait for deployment to complete
wait_for_deployment() {
    log_header "⏳ Waiting for Deployment"
    
    log_info "Waiting for services to deploy..."
    
    # Wait for deployment to complete (timeout after 10 minutes)
    TIMEOUT=600
    ELAPSED=0
    INTERVAL=10
    
    while [ $ELAPSED -lt $TIMEOUT ]; do
        # Check deployment status
        if railway status | grep -q "Deployed"; then
            log_success "Deployment completed"
            return 0
        fi
        
        log_info "Deployment in progress... (${ELAPSED}s elapsed)"
        sleep $INTERVAL
        ELAPSED=$((ELAPSED + INTERVAL))
    done
    
    log_error "Deployment timeout after ${TIMEOUT}s"
    return 1
}

# Run post-deployment health checks
run_health_checks() {
    log_header "🏥 Running Health Checks"
    
    # Get the deployed URL
    DEPLOYED_URL=$(railway domain | head -n 1 | awk '{print $2}' || echo "")
    
    if [ -z "$DEPLOYED_URL" ]; then
        log_warning "Could not determine deployed URL"
        return 1
    fi
    
    log_info "Testing deployed application: $DEPLOYED_URL"
    
    # Test health endpoint
    if curl -f -s "$DEPLOYED_URL/health" > /dev/null; then
        log_success "Health endpoint responding"
    else
        log_error "Health endpoint not responding"
        return 1
    fi
    
    # Test detailed health endpoint
    if curl -f -s "$DEPLOYED_URL/health/detailed" > /dev/null; then
        log_success "Detailed health endpoint responding"
    else
        log_warning "Detailed health endpoint not responding"
    fi
    
    # Test API endpoint
    if curl -f -s "$DEPLOYED_URL/api/articles" > /dev/null; then
        log_success "API endpoint responding"
    else
        log_warning "API endpoint not responding"
    fi
    
    log_success "Health checks completed"
    return 0
}

# Run database migrations in production
run_production_migrations() {
    log_header "🗄️  Running Production Migrations"
    
    log_warning "Running database migrations in production. Continue? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        # Run migrations via Railway
        railway run alembic upgrade head
        log_success "Production migrations completed"
    else
        log_info "Migrations skipped"
    fi
}

# Show deployment summary
show_deployment_summary() {
    log_header "📋 Deployment Summary"
    
    DEPLOYED_URL=$(railway domain | head -n 1 | awk '{print $2}' || echo "Unknown")
    CURRENT_COMMIT=$(git rev-parse HEAD)
    CURRENT_BRANCH=$(git branch --show-current)
    
    echo "🚀 Deployment completed successfully!"
    echo ""
    echo "📊 Deployment Details:"
    echo "  • Project: Bitcoin Newsletter"
    echo "  • Environment: Production"
    echo "  • URL: $DEPLOYED_URL"
    echo "  • Commit: $CURRENT_COMMIT"
    echo "  • Branch: $CURRENT_BRANCH"
    echo "  • Timestamp: $(date)"
    echo ""
    echo "🔗 Useful Links:"
    echo "  • Application: $DEPLOYED_URL"
    echo "  • Health Check: $DEPLOYED_URL/health"
    echo "  • API: $DEPLOYED_URL/api/articles"
    echo "  • Admin Status: $DEPLOYED_URL/admin/status"
    echo ""
    echo "📋 Next Steps:"
    echo "  • Monitor logs: railway logs"
    echo "  • Check metrics: railway metrics"
    echo "  • View services: railway status"
    echo ""
    log_success "Production deployment completed! 🎉"
}

# Rollback deployment
rollback_deployment() {
    log_header "⏪ Rolling Back Deployment"
    
    if [ ! -f "$BACKUP_DIR/latest_backup.txt" ]; then
        log_error "No backup found for rollback"
        exit 1
    fi
    
    BACKUP_NAME=$(cat "$BACKUP_DIR/latest_backup.txt")
    BACKUP_FILE="$BACKUP_DIR/$BACKUP_NAME.json"
    
    if [ ! -f "$BACKUP_FILE" ]; then
        log_error "Backup metadata not found: $BACKUP_FILE"
        exit 1
    fi
    
    # Read backup metadata
    BACKUP_COMMIT=$(jq -r '.commit_hash' "$BACKUP_FILE")
    BACKUP_BRANCH=$(jq -r '.branch' "$BACKUP_FILE")
    
    log_warning "This will rollback to commit $BACKUP_COMMIT on branch $BACKUP_BRANCH"
    log_warning "Continue with rollback? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        # Checkout previous commit
        git checkout "$BACKUP_COMMIT"
        
        # Push to trigger redeployment
        git push origin HEAD:main --force
        
        # Wait for rollback deployment
        wait_for_deployment
        
        # Run health checks
        if run_health_checks; then
            log_success "Rollback completed successfully"
        else
            log_error "Rollback completed but health checks failed"
        fi
    else
        log_info "Rollback cancelled"
    fi
}

# Show help
show_help() {
    echo -e "${PURPLE}Bitcoin Newsletter Production Deployment${NC}"
    echo "Usage: ./scripts/deploy-production.sh <command>"
    echo ""
    echo "Commands:"
    echo "  deploy      - Full production deployment"
    echo "  rollback    - Rollback to previous deployment"
    echo "  health      - Run health checks on production"
    echo "  status      - Show production status"
    echo "  logs        - Show production logs"
    echo "  migrate     - Run database migrations"
    echo "  help        - Show this help message"
}

# Show production status
show_status() {
    log_header "📊 Production Status"
    railway status
}

# Show production logs
show_logs() {
    log_header "📋 Production Logs"
    railway logs --tail 100
}

# Main deployment function
deploy_full() {
    log_header "🚀 Bitcoin Newsletter Production Deployment"
    
    # Log deployment start
    echo "$(date): Starting production deployment" >> "$DEPLOYMENT_LOG"
    
    check_prerequisites
    run_pre_deployment_tests
    create_deployment_backup
    deploy_to_railway
    
    if wait_for_deployment; then
        if run_health_checks; then
            show_deployment_summary
            echo "$(date): Production deployment successful" >> "$DEPLOYMENT_LOG"
        else
            log_error "Health checks failed after deployment"
            echo "$(date): Production deployment failed - health checks" >> "$DEPLOYMENT_LOG"
            exit 1
        fi
    else
        log_error "Deployment failed or timed out"
        echo "$(date): Production deployment failed - timeout" >> "$DEPLOYMENT_LOG"
        exit 1
    fi
}

# Main execution
main() {
    ensure_project_root
    
    case "${1:-help}" in
        deploy)
            deploy_full
            ;;
        rollback)
            rollback_deployment
            ;;
        health)
            run_health_checks
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        migrate)
            run_production_migrations
            ;;
        help|*)
            show_help
            ;;
    esac
}

# Run main function
main "$@"
