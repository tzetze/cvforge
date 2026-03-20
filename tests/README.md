# CVForge Test Suite

Comprehensive unit tests for CVForge core modules.

## Test Structure

```
tests/
├── __init__.py
├── README.md                    # This file
├── fixtures/
│   └── sample_cv.yaml          # Sample CV data for testing
├── test_achievement_scorer.py  # Achievement scoring tests (17 tests)
├── test_data_manager.py        # Data loading/saving tests
├── test_job_parser.py          # Job description parsing tests
├── test_cv_selector.py         # CV content selection tests
├── test_llm_providers.py       # LLM provider tests (with mocking)
└── integration/                # Integration tests (future)
```

## Running Tests

### Quick Start

```bash
# Run all tests
./run_tests.sh

# Or manually with pytest
source venv/bin/activate
python3 -m pytest tests/ -v
```

### Run Specific Test Files

```bash
# Test data manager
python3 -m pytest tests/test_data_manager.py -v

# Test job parser
python3 -m pytest tests/test_job_parser.py -v

# Test CV selector
python3 -m pytest tests/test_cv_selector.py -v

# Test LLM providers
python3 -m pytest tests/test_llm_providers.py -v

# Test achievement scorer
python3 -m pytest tests/test_achievement_scorer.py -v
```

### Run Specific Test Classes or Methods

```bash
# Run specific test class
python3 -m pytest tests/test_data_manager.py::TestLoadCVData -v

# Run specific test method
python3 -m pytest tests/test_data_manager.py::TestLoadCVData::test_load_valid_cv_data -v
```

### Run with Coverage

```bash
# Install pytest-cov if not already installed
pip install pytest-cov

# Run tests with coverage report
python3 -m pytest tests/ --cov=core --cov-report=html --cov-report=term-missing

# View HTML coverage report
open htmlcov/index.html
```

## Test Coverage

### Current Test Modules

1. **test_achievement_scorer.py** (17 tests)
   - Keyword matching
   - Skill matching
   - Impact scoring
   - Recency scoring
   - Semantic similarity
   - Edge cases

2. **test_data_manager.py** (9 tests)
   - Loading CV data from YAML
   - Saving CV data to YAML
   - Error handling (missing files, invalid YAML, validation errors)
   - Round-trip data preservation

3. **test_job_parser.py** (13 tests)
   - Basic job data parsing
   - Keyword extraction
   - Required vs preferred skills
   - Missing fields handling
   - Special characters and HTML
   - Edge cases

4. **test_cv_selector.py** (10 tests)
   - Content selection based on job requirements
   - Relevance filtering
   - Max achievements per role
   - Threshold handling
   - Personal info preservation
   - Custom scorer integration

5. **test_llm_providers.py** (15 tests)
   - Base provider interface
   - Factory pattern
   - Claude provider (mocked)
   - Ollama provider (mocked)
   - Error handling
   - Integration tests

**Total: 64 unit tests**

## Test Fixtures

### sample_cv.yaml

Sample CV data with:
- Personal information
- 2 work experiences
- 5 achievements with metrics and skills
- Technical and soft skills
- Education

Used by multiple test modules to ensure consistent test data.

## Writing New Tests

### Test Structure

```python
"""
Unit tests for module_name
"""
import pytest
from core.module import ClassName

class TestClassName:
    """Tests for ClassName"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.instance = ClassName()
    
    def test_basic_functionality(self):
        """Test basic functionality"""
        result = self.instance.method()
        assert result is not None
    
    def test_error_handling(self):
        """Test error handling"""
        with pytest.raises(ExpectedException):
            self.instance.method_that_raises()
```

### Best Practices

1. **Use descriptive test names**: `test_load_valid_cv_data` not `test1`
2. **One assertion per test**: Focus on testing one thing
3. **Use fixtures**: Share common setup code
4. **Test edge cases**: Empty inputs, None values, invalid data
5. **Mock external dependencies**: Use `unittest.mock` for API calls
6. **Test error paths**: Ensure errors are handled correctly
7. **Keep tests independent**: Tests should not depend on each other

### Mocking External Services

```python
from unittest.mock import Mock, patch

@patch('anthropic.Anthropic')
def test_with_mocked_api(self, mock_anthropic):
    """Test with mocked external API"""
    mock_client = Mock()
    mock_client.method.return_value = "mocked response"
    mock_anthropic.return_value = mock_client
    
    # Your test code here
```

## Continuous Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest tests/ -v --cov=core
```

## Test Categories

### Unit Tests (Current)
- Test individual functions and classes in isolation
- Mock external dependencies
- Fast execution

### Integration Tests (Future)
- Test multiple components working together
- Test with real external services (optional)
- Slower execution

### End-to-End Tests (Future)
- Test complete workflows
- Test web UI functionality
- Test PDF generation pipeline

## Troubleshooting

### Import Errors

If you get import errors, ensure you're running from the project root:

```bash
cd /path/to/cvmaker
python3 -m pytest tests/
```

### Missing Dependencies

Install test dependencies:

```bash
pip install pytest pytest-cov pytest-mock
```

### Fixture Not Found

Ensure the fixture file exists:

```bash
ls tests/fixtures/sample_cv.yaml
```

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure all tests pass
3. Aim for >80% code coverage
4. Update this README if adding new test files

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)