# EKS Cluster Validator Makefile

.PHONY: help install test clean lint format build package

# Default target
help:
	@echo "EKS Cluster Validator - Development Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  install     Install dependencies"
	@echo "  test        Run basic tests"
	@echo "  clean       Clean up build artifacts and cache files"
	@echo "  lint        Run linting checks"
	@echo "  format      Format code with black"
	@echo "  build       Build the package"
	@echo "  package     Create distribution packages"
	@echo "  help        Show this help message"

# Install dependencies
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt

# Run basic tests
test:
	@echo "Running basic tests..."
	python test_basic.py

# Clean up
clean:
	@echo "Cleaning up..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete

# Linting
lint:
	@echo "Running linting checks..."
	flake8 eks_validator/ main.py test_basic.py
	mypy eks_validator/ main.py --ignore-missing-imports

# Code formatting
format:
	@echo "Formatting code..."
	black eks_validator/ main.py test_basic.py
	isort eks_validator/ main.py test_basic.py

# Build package
build:
	@echo "Building package..."
	python setup.py build

# Create distribution packages
package:
	@echo "Creating distribution packages..."
	python setup.py sdist bdist_wheel

# Development setup
dev-setup: clean install
	@echo "Development environment setup complete!"

# Full test suite (requires additional test dependencies)
test-full: test
	@echo "Running full test suite..."
	pytest tests/ -v --cov=eks_validator --cov-report=html

# Docker build (if you add a Dockerfile later)
docker-build:
	@echo "Building Docker image..."
	docker build -t eks-cluster-validator .

# Quick validation test (requires AWS credentials)
quick-test:
	@echo "Running quick validation test..."
	python main.py quick-check test

# Generate documentation
docs:
	@echo "Generating documentation..."
	# Add documentation generation commands here

# Security scan
security:
	@echo "Running security scan..."
	bandit -r eks_validator/
	safety check

# All-in-one setup and test
all: dev-setup format lint test package
	@echo "All tasks completed successfully!"
