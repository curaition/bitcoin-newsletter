# Development Environment Guide

This guide provides comprehensive instructions for setting up and working with the Bitcoin Newsletter development environment.

## Quick Start

### 1. Initial Setup
```bash
# Clone the repository
git clone https://github.com/curaition/bitcoin-newsletter.git
cd bitcoin-newsletter

# Run automated setup
./scripts/setup-dev.sh
```

### 2. Start Development Environment
```bash
# Start all services
./scripts/dev-workflow.sh start

# Or start services manually in separate terminals:
crypto-newsletter worker    # Terminal 1
crypto-newsletter beat      # Terminal 2  
crypto-newsletter serve --dev  # Terminal 3
```

### 3. Verify Setup
```bash
# Check system health
crypto-newsletter health

# Run quick tests
./scripts/dev-workflow.sh test-quick
```

## Development Scripts

### Setup and Environment Management

#### `./scripts/setup-dev.sh`
Complete development environment setup from scratch.

**Features:**
- System requirements validation
- UV and Python environment setup
- Dependency installation
- Pre-commit hooks configuration
- Environment variables setup
- Database initialization
- Setup verification

**Usage:**
```bash
./scripts/setup-dev.sh
```

#### `./scripts/dev-workflow.sh`
Comprehensive development workflow management.

**Available Commands:**
```bash
./scripts/dev-workflow.sh setup       # Initial setup
./scripts/dev-workflow.sh start       # Start all services
./scripts/dev-workflow.sh stop        # Stop all services
./scripts/dev-workflow.sh restart     # Restart services
./scripts/dev-workflow.sh test        # Run full test suite
./scripts/dev-workflow.sh test-quick  # Run unit tests only
./scripts/dev-workflow.sh lint        # Code linting
./scripts/dev-workflow.sh lint-fix    # Auto-fix linting issues
./scripts/dev-workflow.sh clean       # Clean environment
./scripts/dev-workflow.sh reset       # Reset environment
```

### Database Management

#### `./scripts/db-manager.sh`
Database operations and maintenance.

**Migration Commands:**
```bash
./scripts/db-manager.sh migrate       # Run migrations
./scripts/db-manager.sh rollback      # Rollback last migration
./scripts/db-manager.sh create "msg"  # Create new migration
./scripts/db-manager.sh history       # Show migration history
./scripts/db-manager.sh reset         # Reset database
```

**Data Commands:**
```bash
./scripts/db-manager.sh seed          # Seed with sample data
./scripts/db-manager.sh backup        # Create backup
./scripts/db-manager.sh export        # Export data
./scripts/db-manager.sh stats         # Show statistics
```

### Monitoring and Maintenance

#### `./scripts/monitor.sh`
System monitoring and health checks.

**Monitoring Commands:**
```bash
./scripts/monitor.sh status           # System status
./scripts/monitor.sh health           # Health check
./scripts/monitor.sh watch            # Real-time monitoring
./scripts/monitor.sh alerts           # Check alerts
./scripts/monitor.sh report           # Generate report
```

**Maintenance Commands:**
```bash
./scripts/monitor.sh cleanup          # Clean old data
./scripts/monitor.sh backup           # System backup
./scripts/monitor.sh optimize         # Performance optimization
```

### Production Deployment

#### `./scripts/deploy-production.sh`
Production deployment with safety checks.

**Commands:**
```bash
./scripts/deploy-production.sh deploy    # Full deployment
./scripts/deploy-production.sh rollback  # Rollback deployment
./scripts/deploy-production.sh health    # Production health check
./scripts/deploy-production.sh status    # Production status
```

## Development Workflow

### Daily Development

1. **Start Development Session:**
   ```bash
   ./scripts/dev-workflow.sh start
   ```

2. **Make Changes:**
   - Edit code in your preferred editor
   - Pre-commit hooks will run automatically on commit

3. **Test Changes:**
   ```bash
   ./scripts/dev-workflow.sh test-quick  # Fast feedback
   ./scripts/dev-workflow.sh test        # Full test suite
   ```

4. **Code Quality:**
   ```bash
   ./scripts/dev-workflow.sh lint-fix    # Auto-fix issues
   ./scripts/dev-workflow.sh type-check  # Type checking
   ```

### Working with Database

1. **Create Migration:**
   ```bash
   ./scripts/db-manager.sh create "Add new feature"
   ```

2. **Run Migration:**
   ```bash
   ./scripts/db-manager.sh migrate
   ```

3. **Seed Development Data:**
   ```bash
   ./scripts/db-manager.sh seed
   ```

### Testing Workflow

1. **Quick Tests (Unit):**
   ```bash
   ./scripts/dev-workflow.sh test-quick
   ```

2. **Full Test Suite:**
   ```bash
   ./scripts/dev-workflow.sh test
   ```

3. **Watch Mode (if available):**
   ```bash
   ./scripts/dev-workflow.sh test-watch
   ```

4. **Specific Test Categories:**
   ```bash
   python tests/test_runner.py --type unit
   python tests/test_runner.py --type integration
   ```

## Environment Configuration

### Environment Files

- `.env.development` - Development configuration
- `.env.production` - Production configuration (not in repo)
- `.env.example` - Template for environment variables

### Key Environment Variables

```bash
# Application
RAILWAY_ENVIRONMENT=development
SERVICE_TYPE=web
DEBUG=true

# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Redis
REDIS_URL=redis://localhost:6379/0

# API
COINDESK_API_KEY=your-api-key
COINDESK_BASE_URL=https://data-api.coindesk.com

# Celery
ENABLE_CELERY=true
```

## Service Architecture

### Local Development Services

1. **Web Service** (`crypto-newsletter serve --dev`)
   - FastAPI application
   - Port: 8000 (default)
   - Auto-reload enabled

2. **Worker Service** (`crypto-newsletter worker`)
   - Celery worker for background tasks
   - Processes article ingestion
   - Handles scheduled operations

3. **Beat Service** (`crypto-newsletter beat`)
   - Celery beat scheduler
   - Triggers 4-hour article ingestion
   - Manages periodic maintenance

4. **Redis Service** (external)
   - Message broker for Celery
   - Caching layer
   - Session storage

### Service Communication

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Web Service │    │   Worker    │    │    Beat     │
│   (FastAPI) │    │  (Celery)   │    │  (Celery)   │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                    ┌─────────────┐
                    │    Redis    │
                    │  (Message   │
                    │   Broker)   │
                    └─────────────┘
                           │
                    ┌─────────────┐
                    │ PostgreSQL  │
                    │ (Database)  │
                    └─────────────┘
```

## Debugging and Troubleshooting

### Common Issues

1. **Redis Connection Failed:**
   ```bash
   ./scripts/start-redis.sh
   ```

2. **Database Connection Issues:**
   ```bash
   ./scripts/db-manager.sh test-connection
   ```

3. **Import Errors:**
   ```bash
   source .venv/bin/activate
   uv pip install -e .[dev]
   ```

4. **Pre-commit Issues:**
   ```bash
   pre-commit install
   pre-commit run --all-files
   ```

### Debugging Tools

1. **Application Logs:**
   ```bash
   ./scripts/monitor.sh logs
   ```

2. **System Health:**
   ```bash
   ./scripts/monitor.sh health
   ```

3. **Interactive Shell:**
   ```bash
   crypto-newsletter shell
   ```

4. **Database Shell:**
   ```bash
   ./scripts/db-manager.sh shell
   ```

### Performance Monitoring

1. **Real-time Monitoring:**
   ```bash
   ./scripts/monitor.sh watch
   ```

2. **System Metrics:**
   ```bash
   ./scripts/monitor.sh metrics
   ```

3. **Generate Report:**
   ```bash
   ./scripts/monitor.sh report
   ```

## Code Quality Standards

### Pre-commit Hooks

Automatically run on every commit:
- **Black**: Code formatting
- **Ruff**: Linting and import sorting
- **MyPy**: Type checking
- **Trailing whitespace**: Cleanup
- **YAML validation**: Config file validation

### Manual Quality Checks

```bash
# Code formatting
./scripts/dev-workflow.sh lint-fix

# Type checking
./scripts/dev-workflow.sh type-check

# Security scanning
bandit -r src/

# Dependency vulnerabilities
safety check
```

## IDE Configuration

### VS Code Settings

Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"]
}
```

### PyCharm Settings

1. Set Python interpreter to `.venv/bin/python`
2. Enable Black formatter
3. Configure Ruff as external tool
4. Set pytest as test runner

## Useful Aliases

Add to your shell profile (`.bashrc`, `.zshrc`):

```bash
# Bitcoin Newsletter aliases
alias cn='crypto-newsletter'
alias cn-dev='source .venv/bin/activate && crypto-newsletter'
alias cn-test='./scripts/dev-workflow.sh test-quick'
alias cn-lint='./scripts/dev-workflow.sh lint-fix'
alias cn-health='crypto-newsletter health'
alias cn-start='./scripts/dev-workflow.sh start'
alias cn-stop='./scripts/dev-workflow.sh stop'
```

## Contributing Guidelines

1. **Branch Naming:**
   - `feature/description`
   - `bugfix/description`
   - `hotfix/description`

2. **Commit Messages:**
   - Use conventional commits format
   - Include scope when relevant
   - Example: `feat(api): add article filtering endpoint`

3. **Pull Request Process:**
   - Run full test suite
   - Update documentation
   - Request code review
   - Ensure CI passes

4. **Code Review Checklist:**
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] No security vulnerabilities
   - [ ] Performance considerations
   - [ ] Error handling implemented

## Resources

- [CLI Usage Guide](CLI_USAGE.md)
- [Testing Documentation](TESTING.md)
- [API Documentation](API.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Architecture Overview](ARCHITECTURE.md)
