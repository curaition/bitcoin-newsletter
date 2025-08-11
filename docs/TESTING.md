# Testing Framework Documentation

This document describes the comprehensive testing framework for the Crypto Newsletter application.

## Overview

The testing framework provides:
- **Unit Tests**: Fast, isolated tests for individual components
- **Integration Tests**: Tests for component interactions and external dependencies
- **CLI Tests**: Tests for command-line interface functionality
- **Test Fixtures**: Reusable test data and mock objects
- **Test Runner**: Automated test execution with various options
- **CI/CD Integration**: GitHub Actions workflow for automated testing

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_runner.py           # Test execution script
├── unit/                    # Unit tests
│   ├── test_article_processor.py
│   ├── test_coindesk_client.py
│   ├── test_deduplication.py
│   ├── test_ingestion_pipeline.py
│   ├── test_repository.py
│   └── test_settings.py
├── integration/             # Integration tests
│   ├── test_article_pipeline.py
│   ├── test_cli.py
│   └── test_web_endpoints.py
└── fixtures/                # Test data files
    └── sample_articles.json
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
- Fast execution (< 1 second each)
- No external dependencies
- Mock all I/O operations
- Test individual functions and classes

### Integration Tests (`@pytest.mark.integration`)
- Test component interactions
- May use real databases (test instances)
- Test API endpoints
- Test CLI commands

### Slow Tests (`@pytest.mark.slow`)
- Performance tests
- Large dataset tests
- Long-running operations

## Running Tests

### Quick Test Run
```bash
# Run unit tests only (fast)
python tests/test_runner.py --quick

# Run specific test type
python tests/test_runner.py --type unit
python tests/test_runner.py --type integration
```

### Full Test Suite
```bash
# Run all tests with coverage
python tests/test_runner.py --report

# Run tests in parallel
python tests/test_runner.py --parallel

# Run specific test file
python tests/test_runner.py --test tests/unit/test_settings.py
```

### Using Pytest Directly
```bash
# Run unit tests
pytest tests/unit/ -m unit -v

# Run with coverage
pytest --cov=src/crypto_newsletter --cov-report=html

# Run specific markers
pytest -m "unit and not slow"
```

## Test Configuration

### Pytest Configuration (`pytest.ini`)
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests
    slow: Slow tests
    api: Tests requiring API access
    database: Tests requiring database
```

### Environment Variables for Testing
```bash
DATABASE_URL=sqlite:///test.db
REDIS_URL=redis://localhost:6379/1
COINDESK_API_KEY=test-api-key
TESTING=true
DEBUG=true
ENABLE_CELERY=false
```

## Test Fixtures

### Database Fixtures
```python
@pytest.fixture
async def test_db_session():
    """Provides isolated database session for testing."""
    
@pytest.fixture
async def test_db_engine():
    """In-memory SQLite database for testing."""
```

### Mock Fixtures
```python
@pytest.fixture
def mock_coindesk_client():
    """Mock CoinDesk API client."""
    
@pytest.fixture
def mock_redis():
    """Mock Redis client."""
```

### Data Fixtures
```python
@pytest.fixture
def sample_article_data():
    """Sample article data for testing."""
    
@pytest.fixture
def test_data_factory():
    """Factory for creating test data."""
```

## Writing Tests

### Unit Test Example
```python
@pytest.mark.unit
class TestArticleProcessor:
    @pytest.mark.asyncio
    async def test_process_article(self, processor, sample_article_data):
        """Test article processing."""
        result = await processor.process_article(sample_article_data)
        assert result is not None
```

### Integration Test Example
```python
@pytest.mark.integration
class TestArticlePipeline:
    @pytest.mark.asyncio
    async def test_full_pipeline(self, test_db_session):
        """Test complete article ingestion pipeline."""
        pipeline = ArticleIngestionPipeline()
        result = await pipeline.run_full_ingestion(limit=5)
        assert result["summary"]["articles_processed"] > 0
```

### CLI Test Example
```python
@pytest.mark.integration
def test_health_command(runner):
    """Test CLI health command."""
    result = runner.invoke(app, ["health"])
    assert result.exit_code == 0
    assert "healthy" in result.output
```

## Test Data Management

### Test Data Factory
```python
class TestDataFactory:
    @staticmethod
    def create_article_data(article_id=12345, **kwargs):
        """Create test article data."""
        return {
            "ID": article_id,
            "TITLE": "Test Article",
            "URL": f"https://test.com/{article_id}",
            **kwargs
        }
```

### Sample Data Files
- `tests/fixtures/sample_articles.json`: Sample article responses
- `tests/fixtures/sample_publishers.json`: Sample publisher data

## Mocking Guidelines

### External APIs
```python
@patch('crypto_newsletter.core.ingestion.coindesk_client.CoinDeskAPIClient')
def test_api_integration(mock_client):
    mock_client.return_value.fetch_articles.return_value = sample_data
```

### Database Operations
```python
@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    return session
```

### Async Operations
```python
@pytest.mark.asyncio
async def test_async_function():
    mock_func = AsyncMock(return_value="test_result")
    result = await mock_func()
    assert result == "test_result"
```

## Coverage Requirements

### Coverage Targets
- **Overall Coverage**: > 80%
- **Unit Tests**: > 90%
- **Critical Paths**: 100%

### Coverage Exclusions
```python
# pragma: no cover
def debug_function():
    pass

if __name__ == "__main__":  # pragma: no cover
    main()
```

### Coverage Reports
```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# View coverage in browser
open htmlcov/index.html
```

## Continuous Integration

### GitHub Actions Workflow
- **Lint Check**: Black, Ruff, MyPy
- **Unit Tests**: Fast test execution
- **Integration Tests**: With database and Redis
- **Security Scan**: Bandit and Safety
- **Coverage Upload**: Codecov integration

### Test Matrix
- Python 3.11
- Multiple test types (unit, integration)
- Different environments (development, production)

## Performance Testing

### Benchmark Tests
```python
@pytest.mark.slow
def test_deduplication_performance():
    """Test deduplication with large dataset."""
    articles = create_large_dataset(1000)
    start_time = time.time()
    result = deduplicate_articles(articles)
    duration = time.time() - start_time
    assert duration < 1.0  # Should complete in under 1 second
```

### Memory Usage Tests
```python
@pytest.mark.slow
def test_memory_usage():
    """Test memory usage during processing."""
    import psutil
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    # ... perform operations
    final_memory = process.memory_info().rss
    assert final_memory - initial_memory < 100 * 1024 * 1024  # < 100MB
```

## Debugging Tests

### Running Single Tests
```bash
# Run specific test with verbose output
pytest tests/unit/test_settings.py::TestSettings::test_initialization -v -s

# Run with debugger
pytest --pdb tests/unit/test_settings.py::TestSettings::test_initialization
```

### Test Debugging Tips
1. Use `pytest -s` to see print statements
2. Use `pytest --pdb` to drop into debugger on failure
3. Use `pytest -x` to stop on first failure
4. Use `pytest --lf` to run only last failed tests

## Test Maintenance

### Regular Tasks
1. **Update test data** when API responses change
2. **Review coverage reports** and add tests for uncovered code
3. **Update mocks** when external APIs change
4. **Refactor tests** when code structure changes

### Test Quality Checklist
- [ ] Tests are isolated and independent
- [ ] Tests have descriptive names
- [ ] Tests cover both success and failure cases
- [ ] Tests use appropriate fixtures
- [ ] Tests run quickly (unit tests < 1s)
- [ ] Tests are deterministic (no random failures)

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Ensure package is installed in development mode
uv pip install -e .
```

**Database Connection Issues**
```bash
# Check test database configuration
export DATABASE_URL=sqlite:///test.db
```

**Async Test Issues**
```python
# Use pytest-asyncio for async tests
@pytest.mark.asyncio
async def test_async_function():
    pass
```

**Mock Issues**
```python
# Patch at the right location
@patch('module.where.function.is.used')
def test_function(mock_func):
    pass
```

## Best Practices

1. **Write tests first** (TDD approach)
2. **Keep tests simple** and focused
3. **Use descriptive test names** that explain what is being tested
4. **Mock external dependencies** in unit tests
5. **Test edge cases** and error conditions
6. **Maintain test data** separate from test logic
7. **Use fixtures** for common setup
8. **Group related tests** in classes
9. **Document complex test scenarios**
10. **Review test coverage** regularly

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Factory Boy](https://factoryboy.readthedocs.io/)
