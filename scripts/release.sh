#!/bin/bash
# EKS Cluster Validator Release Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_NAME="eks-cluster-validator"
DOCKER_IMAGE="techize/eks-cluster-validator"
PYPI_PACKAGE="eks-cluster-validator"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
check_directory() {
    if [[ ! -f "setup.py" ]] || [[ ! -f "pyproject.toml" ]]; then
        log_error "Not in the project root directory. Please run from the eks-cluster-validator root."
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check Python
    if ! command -v python &> /dev/null; then
        log_error "Python is not installed or not in PATH"
        exit 1
    fi

    # Check pip
    if ! command -v pip &> /dev/null; then
        log_error "pip is not installed or not in PATH"
        exit 1
    fi

    # Check Docker (optional for local builds)
    if ! command -v docker &> /dev/null; then
        log_warning "Docker is not installed. Docker builds will be skipped."
        SKIP_DOCKER=true
    fi

    # Check git
    if ! command -v git &> /dev/null; then
        log_error "git is not installed or not in PATH"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Clean build artifacts
clean_build() {
    log_info "Cleaning build artifacts..."
    rm -rf build/ dist/ *.egg-info/ __pycache__/ .pytest_cache/ .mypy_cache/
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    log_success "Build artifacts cleaned"
}

# Install build dependencies
install_build_deps() {
    log_info "Installing build dependencies..."
    pip install --upgrade pip build twine
    if [[ "$SKIP_DOCKER" != "true" ]]; then
        # Check if Docker is running
        if docker info &> /dev/null; then
            log_info "Docker is available"
        else
            log_warning "Docker is not running. Docker builds will be skipped."
            SKIP_DOCKER=true
        fi
    fi
    log_success "Build dependencies installed"
}

# Run linting and formatting
run_quality_checks() {
    log_info "Running code quality checks..."

    # Install dev dependencies if requirements-dev.txt exists
    if [[ -f "requirements-dev.txt" ]]; then
        pip install -r requirements-dev.txt
    fi

    # Run black formatting check
    if command -v black &> /dev/null; then
        log_info "Running black formatting check..."
        black --check --diff eks_validator/ main.py test_*.py || {
            log_warning "Code formatting issues found. Run 'make format' to fix."
        }
    fi

    # Run flake8 linting
    if command -v flake8 &> /dev/null; then
        log_info "Running flake8 linting..."
        flake8 eks_validator/ main.py test_*.py || {
            log_warning "Linting issues found. Please fix them before release."
        }
    fi

    # Run mypy type checking
    if command -v mypy &> /dev/null; then
        log_info "Running mypy type checking..."
        mypy eks_validator/ main.py --ignore-missing-imports || {
            log_warning "Type checking issues found."
        }
    fi

    log_success "Code quality checks completed"
}

# Run tests
run_tests() {
    log_info "Running tests..."

    # Run basic tests
    if [[ -f "test_basic.py" ]]; then
        log_info "Running basic tests..."
        python test_basic.py || {
            log_error "Basic tests failed"
            exit 1
        }
    fi

    # Run config tests
    if [[ -f "test_config.py" ]]; then
        log_info "Running configuration tests..."
        python test_config.py || {
            log_warning "Configuration tests failed - check environment setup"
        }
    fi

    log_success "Tests completed"
}

# Build Python package
build_package() {
    log_info "Building Python package..."
    python -m build
    log_success "Python package built"

    # Check the package
    log_info "Checking package..."
    twine check dist/*
    log_success "Package check passed"
}

# Build Docker image
build_docker() {
    if [[ "$SKIP_DOCKER" == "true" ]]; then
        log_warning "Skipping Docker build (Docker not available)"
        return
    fi

    log_info "Building Docker image..."
    docker build -t $DOCKER_IMAGE:latest .
    log_success "Docker image built"

    # Tag with version if available
    if [[ -n "$VERSION" ]]; then
        docker tag $DOCKER_IMAGE:latest $DOCKER_IMAGE:$VERSION
        log_success "Docker image tagged as $DOCKER_IMAGE:$VERSION"
    fi
}

# Show release summary
show_release_summary() {
    log_info "Release Summary:"
    echo "  📦 Python Package: $PYPI_PACKAGE"
    echo "  🐳 Docker Image: $DOCKER_IMAGE"
    echo "  📁 Build Artifacts:"
    ls -la dist/ 2>/dev/null || echo "    No dist directory found"

    if [[ "$SKIP_DOCKER" != "true" ]]; then
        echo "  🐳 Docker Images:"
        docker images $DOCKER_IMAGE 2>/dev/null || echo "    No Docker images found"
    fi

    log_success "Release preparation complete!"
    echo ""
    log_info "Next steps:"
    echo "  1. Test the package: pip install dist/*.whl"
    echo "  2. Test Docker: docker run --rm $DOCKER_IMAGE:latest --help"
    echo "  3. For PyPI upload: twine upload dist/*"
    echo "  4. For Docker push: docker push $DOCKER_IMAGE:latest"
}

# Main release process
main() {
    echo "🚀 EKS Cluster Validator Release Script"
    echo "======================================"

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --version)
                VERSION="$2"
                shift 2
                ;;
            --skip-docker)
                SKIP_DOCKER=true
                shift
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo ""
                echo "Options:"
                echo "  --version VERSION    Set version for tagging"
                echo "  --skip-docker        Skip Docker build"
                echo "  --help              Show this help"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    check_directory
    check_prerequisites
    clean_build
    install_build_deps
    run_quality_checks
    run_tests
    build_package
    build_docker
    show_release_summary
}

# Run main function
main "$@"
