#!/bin/bash
# Monitoring and Maintenance Script for Bitcoin Newsletter
# Provides system monitoring, health checks, and maintenance tasks

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

# Configuration
MONITOR_LOG="monitor.log"
ALERT_THRESHOLD_CPU=80
ALERT_THRESHOLD_MEMORY=80
ALERT_THRESHOLD_DISK=90

# Ensure environment is set up
ensure_environment() {
    if [ ! -f "pyproject.toml" ]; then
        log_error "Not in project root directory. Please run from the project root."
        exit 1
    fi
    
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
}

# Show help
show_help() {
    echo -e "${CYAN}Bitcoin Newsletter Monitoring & Maintenance${NC}"
    echo "Usage: ./scripts/monitor.sh <command>"
    echo ""
    echo "Monitoring Commands:"
    echo "  status          - Show system status"
    echo "  health          - Run comprehensive health check"
    echo "  metrics         - Show system metrics"
    echo "  logs            - Show application logs"
    echo "  watch           - Real-time monitoring dashboard"
    echo "  alerts          - Check for system alerts"
    echo ""
    echo "Maintenance Commands:"
    echo "  cleanup         - Clean up old data and logs"
    echo "  backup          - Create system backup"
    echo "  optimize        - Optimize system performance"
    echo "  restart         - Restart services"
    echo "  update          - Update system dependencies"
    echo ""
    echo "Analysis Commands:"
    echo "  performance     - Analyze system performance"
    echo "  errors          - Show recent errors"
    echo "  usage           - Show resource usage"
    echo "  report          - Generate monitoring report"
    echo ""
    echo "Utility Commands:"
    echo "  test            - Test monitoring tools"
    echo "  help            - Show this help message"
}

# Show system status
show_status() {
    log_header "📊 System Status"
    
    # Application health
    log_info "Application Health:"
    if command -v crypto-newsletter &> /dev/null; then
        crypto-newsletter health || log_warning "Application health check failed"
    else
        log_warning "CLI not available"
    fi
    
    # Database status
    log_info "Database Status:"
    if command -v crypto-newsletter &> /dev/null; then
        crypto-newsletter db-status || log_warning "Database status check failed"
    fi
    
    # System resources
    log_info "System Resources:"
    if command -v free &> /dev/null; then
        echo "Memory Usage:"
        free -h
    fi
    
    if command -v df &> /dev/null; then
        echo "Disk Usage:"
        df -h
    fi
    
    # Process status
    log_info "Process Status:"
    if pgrep -f "crypto-newsletter" > /dev/null; then
        log_success "Application processes running"
        pgrep -f "crypto-newsletter" | wc -l | xargs echo "Active processes:"
    else
        log_warning "No application processes found"
    fi
    
    # Redis status
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &> /dev/null; then
            log_success "Redis is running"
        else
            log_warning "Redis is not responding"
        fi
    fi
}

# Run comprehensive health check
run_health_check() {
    log_header "🏥 Comprehensive Health Check"
    
    HEALTH_SCORE=0
    TOTAL_CHECKS=0
    
    # Application health
    log_info "Checking application health..."
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if crypto-newsletter health &> /dev/null; then
        log_success "Application health: OK"
        HEALTH_SCORE=$((HEALTH_SCORE + 1))
    else
        log_error "Application health: FAILED"
    fi
    
    # Database connectivity
    log_info "Checking database connectivity..."
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if crypto-newsletter config-test &> /dev/null; then
        log_success "Database connectivity: OK"
        HEALTH_SCORE=$((HEALTH_SCORE + 1))
    else
        log_error "Database connectivity: FAILED"
    fi
    
    # Redis connectivity
    log_info "Checking Redis connectivity..."
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if redis-cli ping &> /dev/null; then
        log_success "Redis connectivity: OK"
        HEALTH_SCORE=$((HEALTH_SCORE + 1))
    else
        log_error "Redis connectivity: FAILED"
    fi
    
    # Disk space
    log_info "Checking disk space..."
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -lt "$ALERT_THRESHOLD_DISK" ]; then
        log_success "Disk space: OK ($DISK_USAGE% used)"
        HEALTH_SCORE=$((HEALTH_SCORE + 1))
    else
        log_error "Disk space: CRITICAL ($DISK_USAGE% used)"
    fi
    
    # Memory usage
    log_info "Checking memory usage..."
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if command -v free &> /dev/null; then
        MEMORY_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
        if [ "$MEMORY_USAGE" -lt "$ALERT_THRESHOLD_MEMORY" ]; then
            log_success "Memory usage: OK ($MEMORY_USAGE% used)"
            HEALTH_SCORE=$((HEALTH_SCORE + 1))
        else
            log_warning "Memory usage: HIGH ($MEMORY_USAGE% used)"
        fi
    else
        log_warning "Memory check not available"
    fi
    
    # Calculate health percentage
    HEALTH_PERCENTAGE=$((HEALTH_SCORE * 100 / TOTAL_CHECKS))
    
    log_header "🎯 Health Summary"
    echo "Health Score: $HEALTH_SCORE/$TOTAL_CHECKS ($HEALTH_PERCENTAGE%)"
    
    if [ "$HEALTH_PERCENTAGE" -ge 80 ]; then
        log_success "System health: EXCELLENT"
    elif [ "$HEALTH_PERCENTAGE" -ge 60 ]; then
        log_warning "System health: GOOD"
    else
        log_error "System health: POOR - Immediate attention required"
    fi
}

# Show system metrics
show_metrics() {
    log_header "📈 System Metrics"
    
    # Application metrics
    log_info "Application Metrics:"
    crypto-newsletter stats || log_warning "Could not retrieve application stats"
    
    # System metrics
    log_info "System Metrics:"
    
    # CPU usage
    if command -v top &> /dev/null; then
        echo "CPU Usage (top 5 processes):"
        top -b -n1 | head -12 | tail -5
    fi
    
    # Memory details
    if command -v free &> /dev/null; then
        echo "Memory Details:"
        free -h
    fi
    
    # Disk I/O
    if command -v iostat &> /dev/null; then
        echo "Disk I/O:"
        iostat -x 1 1
    fi
    
    # Network connections
    if command -v netstat &> /dev/null; then
        echo "Network Connections:"
        netstat -tuln | grep -E ':(8000|6379|5432)'
    fi
}

# Show application logs
show_logs() {
    log_header "📋 Application Logs"
    
    # Show recent logs
    if [ -f "app.log" ]; then
        log_info "Recent application logs:"
        tail -50 app.log
    else
        log_warning "No application log file found"
    fi
    
    # Show system logs if available
    if command -v journalctl &> /dev/null; then
        log_info "Recent system logs:"
        journalctl -u crypto-newsletter --lines=20 --no-pager || log_info "No systemd service logs found"
    fi
}

# Real-time monitoring dashboard
watch_system() {
    log_header "👀 Real-time Monitoring Dashboard"
    
    log_info "Starting real-time monitoring (Press Ctrl+C to exit)..."
    
    while true; do
        clear
        echo -e "${CYAN}Bitcoin Newsletter - Live Monitor${NC}"
        echo "=================================================="
        echo "$(date)"
        echo ""
        
        # Quick health check
        if crypto-newsletter health &> /dev/null; then
            echo -e "${GREEN}✅ Application: HEALTHY${NC}"
        else
            echo -e "${RED}❌ Application: UNHEALTHY${NC}"
        fi
        
        # System resources
        if command -v free &> /dev/null; then
            MEMORY_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
            echo "💾 Memory: $MEMORY_USAGE%"
        fi
        
        DISK_USAGE=$(df / | awk 'NR==2 {print $5}')
        echo "💿 Disk: $DISK_USAGE"
        
        # Active processes
        PROCESS_COUNT=$(pgrep -f "crypto-newsletter" | wc -l)
        echo "⚙️  Processes: $PROCESS_COUNT"
        
        # Redis status
        if redis-cli ping &> /dev/null; then
            echo -e "${GREEN}🔴 Redis: RUNNING${NC}"
        else
            echo -e "${RED}🔴 Redis: DOWN${NC}"
        fi
        
        echo ""
        echo "Press Ctrl+C to exit..."
        
        sleep 5
    done
}

# Check for system alerts
check_alerts() {
    log_header "🚨 System Alerts"
    
    ALERTS=0
    
    # Check disk space
    DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -gt "$ALERT_THRESHOLD_DISK" ]; then
        log_error "ALERT: Disk usage is $DISK_USAGE% (threshold: $ALERT_THRESHOLD_DISK%)"
        ALERTS=$((ALERTS + 1))
    fi
    
    # Check memory usage
    if command -v free &> /dev/null; then
        MEMORY_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
        if [ "$MEMORY_USAGE" -gt "$ALERT_THRESHOLD_MEMORY" ]; then
            log_error "ALERT: Memory usage is $MEMORY_USAGE% (threshold: $ALERT_THRESHOLD_MEMORY%)"
            ALERTS=$((ALERTS + 1))
        fi
    fi
    
    # Check application health
    if ! crypto-newsletter health &> /dev/null; then
        log_error "ALERT: Application health check failed"
        ALERTS=$((ALERTS + 1))
    fi
    
    # Check Redis
    if ! redis-cli ping &> /dev/null; then
        log_error "ALERT: Redis is not responding"
        ALERTS=$((ALERTS + 1))
    fi
    
    if [ "$ALERTS" -eq 0 ]; then
        log_success "No alerts - system is healthy"
    else
        log_warning "Found $ALERTS alert(s) - review system status"
    fi
}

# Clean up old data and logs
cleanup_system() {
    log_header "🧹 System Cleanup"
    
    # Clean up old articles
    log_info "Cleaning up old articles..."
    crypto-newsletter db-cleanup --days 30 --no-dry-run || log_warning "Article cleanup failed"
    
    # Clean up log files
    log_info "Cleaning up old log files..."
    find . -name "*.log" -mtime +7 -delete 2>/dev/null || true
    
    # Clean up temporary files
    log_info "Cleaning up temporary files..."
    find /tmp -name "crypto-newsletter*" -mtime +1 -delete 2>/dev/null || true
    
    # Clean up Python cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    
    log_success "System cleanup completed"
}

# Create system backup
create_backup() {
    log_header "💾 Creating System Backup"
    
    BACKUP_DIR="system-backups"
    mkdir -p "$BACKUP_DIR"
    
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_NAME="system_backup_$TIMESTAMP"
    
    # Export data
    log_info "Exporting application data..."
    crypto-newsletter export-data --output "$BACKUP_DIR/$BACKUP_NAME.json" --days 30
    
    # Backup configuration
    log_info "Backing up configuration..."
    cp .env.* "$BACKUP_DIR/" 2>/dev/null || true
    
    log_success "System backup created: $BACKUP_DIR/$BACKUP_NAME"
}

# Generate monitoring report
generate_report() {
    log_header "📊 Generating Monitoring Report"
    
    REPORT_FILE="monitoring_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "Bitcoin Newsletter Monitoring Report"
        echo "Generated: $(date)"
        echo "========================================"
        echo ""
        
        echo "SYSTEM STATUS:"
        show_status
        echo ""
        
        echo "HEALTH CHECK:"
        run_health_check
        echo ""
        
        echo "RECENT ERRORS:"
        grep -i error app.log 2>/dev/null | tail -10 || echo "No recent errors found"
        echo ""
        
    } > "$REPORT_FILE"
    
    log_success "Monitoring report generated: $REPORT_FILE"
}

# Main execution
main() {
    ensure_environment
    
    case "${1:-help}" in
        status)
            show_status
            ;;
        health)
            run_health_check
            ;;
        metrics)
            show_metrics
            ;;
        logs)
            show_logs
            ;;
        watch)
            watch_system
            ;;
        alerts)
            check_alerts
            ;;
        cleanup)
            cleanup_system
            ;;
        backup)
            create_backup
            ;;
        report)
            generate_report
            ;;
        help|*)
            show_help
            ;;
    esac
}

# Run main function
main "$@"
