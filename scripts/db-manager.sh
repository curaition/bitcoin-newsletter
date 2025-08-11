#!/bin/bash
# Database Management Script for Bitcoin Newsletter
# Handles database operations, migrations, and maintenance

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

# Ensure we're in the project root and environment is set up
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
    
    # Load environment variables
    if [ -f ".env.development" ]; then
        export $(grep -v '^#' .env.development | xargs)
    elif [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
    fi
    
    if [ -z "$DATABASE_URL" ]; then
        log_error "DATABASE_URL not set. Please configure your database connection."
        exit 1
    fi
}

# Show help
show_help() {
    echo -e "${PURPLE}Bitcoin Newsletter Database Manager${NC}"
    echo "Usage: ./scripts/db-manager.sh <command>"
    echo ""
    echo "Migration Commands:"
    echo "  migrate         - Run pending migrations"
    echo "  rollback        - Rollback last migration"
    echo "  rollback-to     - Rollback to specific revision"
    echo "  create          - Create new migration"
    echo "  history         - Show migration history"
    echo "  current         - Show current migration"
    echo "  reset           - Reset database (WARNING: destructive)"
    echo ""
    echo "Data Commands:"
    echo "  seed            - Seed database with sample data"
    echo "  backup          - Create database backup"
    echo "  restore         - Restore database from backup"
    echo "  export          - Export data to files"
    echo "  import          - Import data from files"
    echo ""
    echo "Maintenance Commands:"
    echo "  status          - Show database status"
    echo "  stats           - Show database statistics"
    echo "  cleanup         - Clean up old data"
    echo "  vacuum          - Vacuum database (PostgreSQL)"
    echo "  analyze         - Analyze database performance"
    echo ""
    echo "Development Commands:"
    echo "  shell           - Open database shell"
    echo "  test-connection - Test database connection"
    echo "  help            - Show this help message"
}

# Run database migrations
run_migrations() {
    log_header "🗄️  Running Database Migrations"
    
    log_info "Checking current migration status..."
    alembic current
    
    log_info "Running pending migrations..."
    alembic upgrade head
    
    log_success "Migrations completed"
}

# Rollback last migration
rollback_migration() {
    log_header "⏪ Rolling Back Last Migration"
    
    log_warning "This will rollback the last migration. Continue? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        alembic downgrade -1
        log_success "Migration rolled back"
    else
        log_info "Rollback cancelled"
    fi
}

# Rollback to specific revision
rollback_to_revision() {
    log_header "⏪ Rolling Back to Specific Revision"
    
    if [ -z "$2" ]; then
        log_error "Please specify revision ID"
        log_info "Usage: ./scripts/db-manager.sh rollback-to <revision_id>"
        exit 1
    fi
    
    log_warning "This will rollback to revision $2. Continue? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        alembic downgrade "$2"
        log_success "Rolled back to revision $2"
    else
        log_info "Rollback cancelled"
    fi
}

# Create new migration
create_migration() {
    log_header "📝 Creating New Migration"
    
    if [ -z "$2" ]; then
        log_error "Please specify migration message"
        log_info "Usage: ./scripts/db-manager.sh create \"migration message\""
        exit 1
    fi
    
    log_info "Creating migration: $2"
    alembic revision --autogenerate -m "$2"
    
    log_success "Migration created"
    log_info "Review the generated migration file before running migrations"
}

# Show migration history
show_history() {
    log_header "📚 Migration History"
    alembic history --verbose
}

# Show current migration
show_current() {
    log_header "📍 Current Migration"
    alembic current --verbose
}

# Reset database
reset_database() {
    log_header "🔄 Resetting Database"
    
    log_error "WARNING: This will completely reset your database!"
    log_warning "All data will be lost. Continue? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        log_info "Dropping all tables..."
        alembic downgrade base
        
        log_info "Running all migrations..."
        alembic upgrade head
        
        log_success "Database reset completed"
    else
        log_info "Database reset cancelled"
    fi
}

# Seed database with sample data
seed_database() {
    log_header "🌱 Seeding Database"
    
    log_info "Running sample data ingestion..."
    crypto-newsletter ingest --limit 20 --verbose
    
    log_success "Database seeded with sample data"
}

# Create database backup
backup_database() {
    log_header "💾 Creating Database Backup"
    
    BACKUP_DIR="backups"
    mkdir -p "$BACKUP_DIR"
    
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql"
    
    log_info "Creating backup: $BACKUP_FILE"
    
    # Extract database info from URL
    DB_URL_REGEX="postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+)"
    if [[ $DATABASE_URL =~ $DB_URL_REGEX ]]; then
        DB_USER="${BASH_REMATCH[1]}"
        DB_PASS="${BASH_REMATCH[2]}"
        DB_HOST="${BASH_REMATCH[3]}"
        DB_PORT="${BASH_REMATCH[4]}"
        DB_NAME="${BASH_REMATCH[5]}"
        
        PGPASSWORD="$DB_PASS" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE"
        
        log_success "Backup created: $BACKUP_FILE"
    else
        log_error "Could not parse DATABASE_URL for backup"
        exit 1
    fi
}

# Restore database from backup
restore_database() {
    log_header "📥 Restoring Database"
    
    if [ -z "$2" ]; then
        log_error "Please specify backup file"
        log_info "Usage: ./scripts/db-manager.sh restore <backup_file>"
        exit 1
    fi
    
    if [ ! -f "$2" ]; then
        log_error "Backup file not found: $2"
        exit 1
    fi
    
    log_warning "This will restore database from $2. All current data will be lost. Continue? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        # Extract database info from URL
        DB_URL_REGEX="postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+)"
        if [[ $DATABASE_URL =~ $DB_URL_REGEX ]]; then
            DB_USER="${BASH_REMATCH[1]}"
            DB_PASS="${BASH_REMATCH[2]}"
            DB_HOST="${BASH_REMATCH[3]}"
            DB_PORT="${BASH_REMATCH[4]}"
            DB_NAME="${BASH_REMATCH[5]}"
            
            PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" < "$2"
            
            log_success "Database restored from $2"
        else
            log_error "Could not parse DATABASE_URL for restore"
            exit 1
        fi
    else
        log_info "Restore cancelled"
    fi
}

# Export data to files
export_data() {
    log_header "📤 Exporting Data"
    
    EXPORT_DIR="exports"
    mkdir -p "$EXPORT_DIR"
    
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    
    log_info "Exporting articles..."
    crypto-newsletter export-data --output "$EXPORT_DIR/articles_$TIMESTAMP.json" --days 30
    
    log_success "Data exported to $EXPORT_DIR/"
}

# Show database status
show_status() {
    log_header "📊 Database Status"
    
    log_info "Testing connection..."
    crypto-newsletter config-test
    
    log_info "Current migration:"
    alembic current
    
    log_info "Database statistics:"
    crypto-newsletter db-status
}

# Show database statistics
show_stats() {
    log_header "📈 Database Statistics"
    crypto-newsletter db-status
}

# Clean up old data
cleanup_data() {
    log_header "🧹 Cleaning Up Old Data"
    
    log_info "Cleaning up articles older than 30 days..."
    crypto-newsletter db-cleanup --days 30 --no-dry-run
    
    log_success "Data cleanup completed"
}

# Vacuum database (PostgreSQL)
vacuum_database() {
    log_header "🧹 Vacuuming Database"
    
    log_info "Running VACUUM ANALYZE..."
    
    # Extract database info from URL
    DB_URL_REGEX="postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+)"
    if [[ $DATABASE_URL =~ $DB_URL_REGEX ]]; then
        DB_USER="${BASH_REMATCH[1]}"
        DB_PASS="${BASH_REMATCH[2]}"
        DB_HOST="${BASH_REMATCH[3]}"
        DB_PORT="${BASH_REMATCH[4]}"
        DB_NAME="${BASH_REMATCH[5]}"
        
        PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "VACUUM ANALYZE;"
        
        log_success "Database vacuumed"
    else
        log_error "Could not parse DATABASE_URL for vacuum"
        exit 1
    fi
}

# Open database shell
open_shell() {
    log_header "🐚 Opening Database Shell"
    
    # Extract database info from URL
    DB_URL_REGEX="postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+)"
    if [[ $DATABASE_URL =~ $DB_URL_REGEX ]]; then
        DB_USER="${BASH_REMATCH[1]}"
        DB_PASS="${BASH_REMATCH[2]}"
        DB_HOST="${BASH_REMATCH[3]}"
        DB_PORT="${BASH_REMATCH[4]}"
        DB_NAME="${BASH_REMATCH[5]}"
        
        log_info "Connecting to database..."
        PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"
    else
        log_error "Could not parse DATABASE_URL for shell"
        exit 1
    fi
}

# Test database connection
test_connection() {
    log_header "🔌 Testing Database Connection"
    crypto-newsletter config-test
}

# Main execution
main() {
    ensure_environment
    
    case "${1:-help}" in
        migrate)
            run_migrations
            ;;
        rollback)
            rollback_migration
            ;;
        rollback-to)
            rollback_to_revision "$@"
            ;;
        create)
            create_migration "$@"
            ;;
        history)
            show_history
            ;;
        current)
            show_current
            ;;
        reset)
            reset_database
            ;;
        seed)
            seed_database
            ;;
        backup)
            backup_database
            ;;
        restore)
            restore_database "$@"
            ;;
        export)
            export_data
            ;;
        status)
            show_status
            ;;
        stats)
            show_stats
            ;;
        cleanup)
            cleanup_data
            ;;
        vacuum)
            vacuum_database
            ;;
        shell)
            open_shell
            ;;
        test-connection)
            test_connection
            ;;
        help|*)
            show_help
            ;;
    esac
}

# Run main function
main "$@"
