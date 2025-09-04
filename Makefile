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

# Docker build
docker-build:
	@echo "Building Docker image..."
	docker build -t eks-cluster-validator .

# Docker run (requires AWS credentials)
docker-run:
	@echo "Running Docker container..."
	docker run --rm \
		-e AWS_PROFILE=${AWS_PROFILE} \
		-e AWS_REGION=${AWS_REGION} \
		-v ~/.aws:/root/.aws:ro \
		eks-cluster-validator:latest \
		$(ARGS)

# Build for PyPI
pypi-build:
	@echo "Building for PyPI..."
	python -m build

# Check PyPI package
pypi-check:
	@echo "Checking PyPI package..."
	twine check dist/*

# Upload to PyPI (requires TWINE_USERNAME and TWINE_PASSWORD)
pypi-upload:
	@echo "Uploading to PyPI..."
	twine upload dist/*

# Upload to Test PyPI
pypi-upload-test:
	@echo "Uploading to Test PyPI..."
	twine upload --repository testpypi dist/*

# Generate documentation
docs:
	@echo "Generating documentation..."
	mkdocs build

# Serve documentation locally
docs-serve:
	@echo "Serving documentation locally..."
	mkdocs serve

# Deploy documentation
docs-deploy:
	@echo "Deploying documentation..."
	mkdocs gh-deploy

# Release workflow
release: clean format lint test pypi-build pypi-check
	@echo "Release build complete! Ready for publishing."

# Full CI/CD simulation
ci: clean install format lint test pypi-build docker-build
	@echo "CI/CD pipeline simulation complete!"
