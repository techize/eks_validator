# Testing Framework

This directory contains the comprehensive testing framework for the EKS Cluster Validator. The tests are organized into unit tests, integration tests, and performance tests to ensure code quality and reliability.

## Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_config.py      # Configuration management tests
│   ├── test_main.py        # CLI functionality tests
│   └── test_validator.py   # Core validation logic tests
├── integration/            # Integration tests for full workflows
│   └── test_workflow.py    # End-to-end workflow tests
├── conftest.py             # Pytest configuration and fixtures
└── README.md              # This file
```

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install -r requirements-test.txt
```

Or install all dependencies (including tests):
```bash
pip install -r requirements.txt
```

### Basic Test Execution

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=eks_validator --cov-report=html
```

Run specific test categories:
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Tests with specific markers
pytest -m "not slow"  # Skip slow tests
pytest -m "integration"  # Run only integration tests
```

### Advanced Options

Run tests in parallel:
```bash
pytest -n auto
```

Run with verbose output:
```bash
pytest -v
```

Run specific test file:
```bash
pytest tests/unit/test_config.py
```

Run specific test function:
```bash
pytest tests/unit/test_config.py::TestAWSConfig::test_default_values
```

## Test Categories

### Unit Tests (`tests/unit/`)

- **test_config.py**: Tests for configuration management
  - AWS configuration loading and validation
  - Kubernetes configuration handling
  - Validation and reporting configuration
  - Environment variable parsing
  - YAML file parsing

- **test_main.py**: Tests for CLI functionality
  - Command-line argument parsing
  - Configuration file loading
  - Environment variable precedence
  - Error handling and validation

- **test_validator.py**: Tests for core validation logic
  - Individual validation checks
  - AWS service interactions
  - Kubernetes API calls
  - Error handling and reporting

### Integration Tests (`tests/integration/`)

- **test_workflow.py**: End-to-end workflow tests
  - Complete validation workflows
  - Configuration loading from multiple sources
  - AWS and Kubernetes service integration
  - Error handling in complex scenarios

## Test Fixtures

The `conftest.py` file provides shared fixtures for all tests:

- `temp_dir`: Temporary directory for file operations
- `mock_aws_credentials`: Mocked AWS credentials
- `mock_kubernetes_config`: Mocked Kubernetes configuration
- `sample_config_yaml`: Sample configuration file
- `mock_boto3_client`: Mocked AWS boto3 client
- `mock_kubernetes_client`: Mocked Kubernetes client

## Test Markers

Tests can be marked with pytest markers for selective execution:

- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.slow`: Slow-running tests
- `@pytest.mark.aws`: Tests requiring AWS credentials

## Code Coverage

Generate coverage reports:
```bash
# HTML report
pytest --cov=eks_validator --cov-report=html
open htmlcov/index.html

# Terminal report
pytest --cov=eks_validator --cov-report=term-missing

# XML report for CI/CD
pytest --cov=eks_validator --cov-report=xml
```

## Mocking Strategy

The tests use comprehensive mocking to isolate components:

- **AWS Services**: Mocked using `moto` and `unittest.mock`
- **Kubernetes API**: Mocked using `unittest.mock`
- **File System**: Temporary directories and files
- **Environment Variables**: Patched using `unittest.mock`

## Continuous Integration

Tests are automatically run in CI/CD pipelines:

- **GitHub Actions**: `.github/workflows/ci-cd.yml`
- **Pre-commit hooks**: Run tests on code changes
- **Coverage reporting**: Integrated with CI dashboards

## Writing New Tests

### Unit Test Template

```python
import pytest
from unittest.mock import patch, MagicMock

from eks_validator.module import ClassToTest

class TestClassToTest:
    """Test cases for ClassToTest."""

    def test_method_success(self):
        """Test successful method execution."""
        # Arrange
        instance = ClassToTest()

        # Act
        result = instance.method()

        # Assert
        assert result is True

    def test_method_failure(self):
        """Test method failure handling."""
        # Arrange
        instance = ClassToTest()

        # Act & Assert
        with pytest.raises(ValueError):
            instance.method(invalid_param=True)
```

### Integration Test Template

```python
import pytest

@pytest.mark.integration
class TestWorkflow:
    """Integration tests for complete workflows."""

    def test_full_workflow(self, mock_boto3_client, mock_kubernetes_client):
        """Test complete validation workflow."""
        # Arrange
        settings = Settings()

        # Act
        result = validate_cluster(settings)

        # Assert
        assert result is True
```

## Test Data

Test data is generated using:

- **Faker**: For realistic test data generation
- **Factory patterns**: For consistent test object creation
- **YAML fixtures**: For configuration test files
- **Mock responses**: For API call simulation

## Performance Testing

Performance tests use `pytest-benchmark`:

```bash
pytest tests/ --benchmark-only
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Descriptive Names**: Test names should clearly describe what they test
3. **Arrange-Act-Assert**: Follow the AAA pattern
4. **Mock External Dependencies**: Don't rely on external services
5. **Test Edge Cases**: Include boundary conditions and error scenarios
6. **Keep Tests Fast**: Avoid slow operations in unit tests
7. **Use Fixtures**: Reuse common test setup code

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Mock Failures**: Check mock setup and patching
3. **Coverage Issues**: Verify source code paths
4. **CI Failures**: Check environment variables and credentials

### Debug Mode

Run tests with debugging:
```bash
pytest -v -s --pdb
```

## Contributing

When adding new features:

1. Add corresponding unit tests
2. Update integration tests if needed
3. Ensure all tests pass
4. Maintain or improve code coverage
5. Follow existing test patterns and naming conventions

## CI/CD Integration

Tests are integrated into the CI/CD pipeline:

- **Pull Requests**: Run full test suite
- **Code Quality**: Lint and type checking
- **Security**: Security scanning
- **Coverage**: Coverage reporting and thresholds
- **Release**: Additional validation for releases

## Running Tests

### All Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=eks_validator --cov-report=html

# Run with verbose output
pytest -v
```

### Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_config.py

# Specific test function
pytest tests/unit/test_config.py::test_load_yaml_config -v
```

### Test Configuration

```bash
# Run tests in parallel
pytest -n auto

# Run failed tests first
pytest --lf

# Run tests with different markers
pytest -m "slow"        # Run slow tests
pytest -m "not slow"    # Skip slow tests
pytest -m "integration" # Run integration tests
```

## Test Fixtures

### AWS Mocking

Tests use `moto` library to mock AWS services:

- EKS clusters
- EC2 instances
- IAM roles and policies
- CloudWatch metrics

### Kubernetes Mocking

Tests use mock responses for Kubernetes API calls:

- Cluster status
- Node information
- Pod status
- Resource quotas

## Test Data

### Sample Configurations

- `basic-config.yaml`: Minimal working configuration
- `full-config.yaml`: Complete configuration with all options
- `invalid-config.yaml`: Configuration with validation errors

### Mock AWS Resources

- Sample EKS cluster with nodes
- Mock EC2 instances
- Sample IAM roles and policies
- CloudWatch metrics data

## CI/CD Integration

Tests are automatically run in GitHub Actions on:

- Push to main/develop branches
- Pull requests
- Manual workflow dispatch

### Coverage Requirements

- Minimum coverage: 80%
- Coverage report uploaded to GitHub
- Coverage badge in README

## Writing New Tests

### Unit Test Template
```python
import pytest
from eks_validator.config import Settings

class TestConfiguration:
    """Test configuration loading and validation."""

    def test_load_valid_config(self):
        """Test loading a valid configuration file."""
        config = Settings.from_yaml("tests/fixtures/valid-config.yaml")
        assert config.aws.region == "us-east-1"
        assert config.validation.severity_threshold == "warning"

    def test_load_invalid_config(self):
        """Test loading an invalid configuration file."""
        with pytest.raises(ValueError):
            Settings.from_yaml("tests/fixtures/invalid-config.yaml")

    def test_environment_variable_override(self):
        """Test environment variable override of config values."""
        import os
        os.environ["AWS_REGION"] = "us-west-2"

        config = Settings.from_env()
        assert config.aws.region == "us-west-2"

        # Clean up
        del os.environ["AWS_REGION"]
```

### Integration Test Template
```python
import pytest
from eks_validator.main import main
from click.testing import CliRunner

class TestCLIIntegration:
    """Test CLI integration and end-to-end functionality."""

    @pytest.fixture
    def runner(self):
        """CLI runner fixture."""
        return CliRunner()

    def test_cli_help(self, runner):
        """Test CLI help command."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "EKS Cluster Validator" in result.output

    def test_validation_with_config_file(self, runner, tmp_path):
        """Test validation using a configuration file."""
        config_file = tmp_path / "test-config.yaml"
        config_file.write_text("""
        aws:
          region: us-east-1
        kubernetes:
          config_file: ~/.kube/config
        validation:
          checks:
            - cluster-health
        """)

        result = runner.invoke(main, ["validate", "--config", str(config_file)])
        # Assert based on expected behavior
        assert result.exit_code in [0, 1]  # Success or validation failure
```

## Test Markers

### Custom Markers
```python
# Mark slow tests
@pytest.mark.slow
def test_slow_operation():
    pass

# Mark integration tests
@pytest.mark.integration
def test_full_workflow():
    pass

# Mark tests requiring AWS credentials
@pytest.mark.aws
def test_aws_integration():
    pass
```

### Marker Configuration
Markers are defined in `pytest.ini`:
```ini
[tool:pytest.ini_options]
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    aws: marks tests requiring AWS credentials
```

## Mocking Strategy

### AWS Services
```python
import boto3
from moto import mock_eks, mock_ec2

@mock_eks
@mock_ec2
def test_eks_cluster_validation():
    """Test EKS cluster validation with mocked AWS services."""
    # Create mock EKS cluster
    eks_client = boto3.client("eks", region_name="us-east-1")
    eks_client.create_cluster(
        name="test-cluster",
        version="1.24",
        roleArn="arn:aws:iam::123456789012:role/eks-service-role",
        resourcesVpcConfig={
            "subnetIds": ["subnet-12345", "subnet-67890"]
        }
    )

    # Test validation logic
    validator = EKSValidator()
    result = validator.validate_cluster("test-cluster")
    assert result is True
```

### Kubernetes API
```python
from unittest.mock import patch, MagicMock

def test_kubernetes_api_calls():
    """Test Kubernetes API interactions with mocked responses."""
    mock_response = {
        "items": [
            {"metadata": {"name": "pod-1"}, "status": {"phase": "Running"}},
            {"metadata": {"name": "pod-2"}, "status": {"phase": "Pending"}}
        ]
    }

    with patch("kubernetes.client.CoreV1Api.list_namespaced_pod") as mock_list:
        mock_list.return_value = MagicMock(**mock_response)

        validator = KubernetesValidator()
        pods = validator.get_pod_status("default")
        assert len(pods) == 2
        assert pods[0]["status"] == "Running"
```

## Performance Testing

### Benchmark Tests
```python
import time
import pytest

def test_validation_performance(benchmark):
    """Test validation performance using pytest-benchmark."""
    def run_validation():
        validator = EKSValidator()
        return validator.validate_cluster("test-cluster")

    result = benchmark(run_validation)
    assert result is not None

    # Performance assertions
    assert benchmark.stats.mean < 30.0  # Should complete in under 30 seconds
```

## Test Data Management

### Fixtures Directory
```
tests/fixtures/
├── configs/
│   ├── valid-basic.yaml
│   ├── valid-advanced.yaml
│   ├── invalid-missing-region.yaml
│   └── invalid-bad-severity.yaml
├── aws_responses/
│   ├── eks_cluster_healthy.json
│   ├── eks_cluster_unhealthy.json
│   └── ec2_instances.json
└── k8s_responses/
    ├── pods_healthy.json
    ├── pods_unhealthy.json
    └── nodes.json
```

### Fixture Usage
```python
import pytest
import json

@pytest.fixture
def sample_eks_cluster():
    """Load sample EKS cluster data."""
    with open("tests/fixtures/aws_responses/eks_cluster_healthy.json") as f:
        return json.load(f)

@pytest.fixture
def sample_config():
    """Load sample configuration."""
    return Settings.from_yaml("tests/fixtures/configs/valid-basic.yaml")
```

## Continuous Integration

### GitHub Actions Configuration
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.8", "3.9", "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v4
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run tests
      run: |
        pytest --cov=eks_validator --cov-report=xml

    - name: Upload coverage
      uses: actions/upload-artifact@v3
      with:
        name: coverage-${{ matrix.python-version }}
        path: coverage.xml
```

## Test Reporting

### Coverage Reports
- HTML reports generated locally: `pytest --cov=eks_validator --cov-report=html`
- XML reports for CI: `pytest --cov=eks_validator --cov-report=xml`
- Coverage badge updated automatically

### Test Results
- JUnit XML output: `pytest --junitxml=test-results.xml`
- Uploaded to GitHub as artifacts
- Integrated with GitHub checks

## Best Practices

### Test Organization
1. **One test per behavior**: Each test should verify one specific behavior
2. **Descriptive test names**: Test names should clearly describe what they're testing
3. **Arrange-Act-Assert**: Structure tests with clear setup, execution, and verification phases
4. **Independent tests**: Tests should not depend on each other
5. **Fast tests**: Keep unit tests fast, mark slow tests appropriately

### Mocking Guidelines
1. **Mock external dependencies**: AWS, Kubernetes, file system operations
2. **Use realistic test data**: Mock responses should resemble real API responses
3. **Verify mock interactions**: Ensure mocks are called as expected
4. **Clean up after tests**: Reset mock state between tests

### CI/CD Integration
1. **Fail fast**: Stop pipeline on test failures
2. **Parallel execution**: Run tests in parallel when possible
3. **Artifact collection**: Save test results and coverage reports
4. **Notification**: Alert team on test failures
5. **Branch protection**: Require tests to pass before merge
