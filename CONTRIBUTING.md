# Contributing to EKS Cluster Validator

Thank you for your interest in contributing to the EKS Cluster Validator! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

This project follows a code of conduct to ensure a welcoming environment for all contributors. By participating, you agree to:

- Be respectful and inclusive
- Focus on constructive feedback
- Accept responsibility for mistakes
- Show empathy towards other contributors
- Help create a positive community

## Getting Started

### Prerequisites

Before you begin, ensure you have:

- Python 3.8 or higher
- AWS CLI configured with appropriate permissions
- kubectl installed and configured
- Git

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

   ```bash
   git clone https://github.com/your-username/eks-cluster-validator.git
   cd eks-cluster-validator
   ```

3. Set up the upstream remote:

   ```bash
   git remote add upstream https://github.com/techize/eks-cluster-validator.git
   ```

## Development Setup

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### 2. Set Up Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install the hooks
pre-commit install

# Install commit-msg hooks
pre-commit install --hook-type commit-msg
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your development values
nano .env
```

### 4. Run Basic Tests

```bash
# Run the basic test suite
python test_basic.py

# Run with verbose output
python test_basic.py --verbose
```

## Development Workflow

### 1. Choose an Issue

- Check the [Issues](https://github.com/techize/eks-cluster-validator/issues) page
- Look for issues labeled `good first issue` or `help wanted`
- Comment on the issue to indicate you're working on it

### 2. Create a Feature Branch

```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 3. Make Changes

- Write clear, focused commits
- Test your changes thoroughly
- Ensure all pre-commit hooks pass
- Update documentation as needed

### 4. Test Your Changes

```bash
# Run pre-commit on all files
pre-commit run --all-files

# Run basic tests
python test_basic.py

# Test specific functionality
python main.py --help
```

### 5. Submit a Pull Request

- Push your branch to your fork
- Create a Pull Request against the main branch
- Fill out the PR template completely
- Link to any related issues

## Coding Standards

### Python Style

This project follows PEP 8 with some modifications:

- **Line Length**: 88 characters (Black default)
- **Imports**: Use absolute imports
- **Docstrings**: Use triple quotes with proper formatting
- **Naming**: Use descriptive names following PEP 8 conventions

### Code Formatting

We use [Black](https://black.readthedocs.io/) for code formatting:

```bash
# Format code
black eks_validator/ main.py test_basic.py

# Check formatting without changes
black --check eks_validator/ main.py test_basic.py
```

### Linting

We use [Flake8](https://flake8.pycqa.org/) for linting:

```bash
# Run linting
flake8 eks_validator/ main.py test_basic.py

# With specific rules
flake8 --max-line-length=88 --extend-ignore=E203,W503 eks_validator/
```

### Pre-commit Hooks

All code must pass pre-commit hooks before being merged:

- `trailing-whitespace`: Removes trailing whitespace
- `end-of-file-fixer`: Ensures files end with newline
- `check-yaml`: Validates YAML syntax
- `black`: Code formatting
- `flake8`: Linting
- `validate-no-sensitive-data`: Custom security validation

## Testing

### Running Tests

```bash
# Run basic functionality tests
python test_basic.py

# Run with coverage (if pytest is configured)
pytest --cov=eks_validator

# Run specific test categories
pytest tests/test_infrastructure.py
```

### Writing Tests

When adding new features, include appropriate tests:

1. **Unit Tests**: Test individual functions and methods
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Test complete workflows

### Test Coverage

Aim for high test coverage, especially for:

- Core validation logic
- Error handling
- Edge cases
- Security-sensitive code

## Submitting Changes

### Commit Messages

Follow conventional commit format:

```text
type(scope): description

[optional body]

[optional footer]
```

Types:

- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/modifications
- `chore`: Maintenance tasks

Examples:

```text
feat(infrastructure): add VPC validation checks
fix(networking): resolve load balancer detection issue
docs(readme): update installation instructions
```

### Pull Request Process

1. **Title**: Clear, descriptive title following commit conventions
2. **Description**: Detailed explanation of changes
3. **Testing**: Describe how changes were tested
4. **Breaking Changes**: Note any breaking changes
5. **Screenshots**: Include screenshots for UI changes
6. **Checklist**: Complete the PR template checklist

### Review Process

- At least one maintainer must approve
- All CI checks must pass
- Conflicts must be resolved
- Documentation must be updated

## Reporting Issues

### Bug Reports

When reporting bugs, include:

- **Description**: Clear description of the issue
- **Steps to Reproduce**: Step-by-step reproduction instructions
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: Python version, OS, AWS region, etc.
- **Logs**: Relevant log output (sanitize sensitive data)
- **Screenshots**: If applicable

### Feature Requests

When requesting features, include:

- **Description**: Clear description of the desired feature
- **Use Case**: Why this feature would be useful
- **Proposed Solution**: How you think it should work
- **Alternatives**: Other solutions you've considered

### Security Issues

For security-related issues:

- **DO NOT** create public issues
- Email [security@company.com](mailto:security@company.com) with details
- Include full details and reproduction steps
- Allow time for proper assessment and fix

## Additional Resources

- [Project Documentation](./docs/)
- [API Reference](./docs/api.md)
- [Architecture Overview](./docs/architecture.md)
- [Security Guidelines](./docs/security.md)

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/techize/eks-cluster-validator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/techize/eks-cluster-validator/discussions)
- **Documentation**: [Project Wiki](https://github.com/techize/eks-cluster-validator/wiki)

Thank you for contributing to the EKS Cluster Validator! 🎉
