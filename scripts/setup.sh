#!/bin/bash
# EKS Cluster Validator Setup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Setup Python virtual environment
setup_venv() {
    log_info "Setting up Python virtual environment..."

    if [[ ! -d "venv" ]]; then
        python3 -m venv venv
        log_success "Virtual environment created"
    else
        log_info "Virtual environment already exists"
    fi

    source venv/bin/activate
    log_success "Virtual environment activated"
}

# Install dependencies
install_deps() {
    log_info "Installing dependencies..."

    # Upgrade pip
    pip install --upgrade pip

    # Install main dependencies
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
        log_success "Main dependencies installed"
    fi

    # Install development dependencies
    if [[ -f "requirements-dev.txt" ]]; then
        pip install -r requirements-dev.txt
        log_success "Development dependencies installed"
    fi

    # Install build tools
    pip install build twine mkdocs mkdocs-material mike
    log_success "Build tools installed"
}

# Install Node.js dependencies (optional)
install_node_deps() {
    if command -v node &> /dev/null && command -v npm &> /dev/null; then
        log_info "Installing Node.js dependencies..."

        # Check if markdownlint is already available (e.g., installed via Homebrew)
        if command -v markdownlint &> /dev/null; then
            log_info "markdownlint already available (likely installed via Homebrew)"
            log_success "Node.js dependencies satisfied"
        else
            # Try to install markdownlint-cli globally
            if npm install -g markdownlint-cli; then
                log_success "Node.js dependencies installed"
            else
                log_warning "Failed to install markdownlint-cli via npm. Install manually or via package manager."
            fi
        fi
    else
        log_warning "Node.js/npm not found. Install Node.js for markdownlint-cli support."
    fi
}

# Setup pre-commit hooks
setup_precommit() {
    log_info "Setting up pre-commit hooks..."

    if [[ -f ".pre-commit-config.yaml" ]]; then
        pip install pre-commit
        pre-commit install
        log_success "Pre-commit hooks installed"
    else
        log_warning "No .pre-commit-config.yaml found, skipping pre-commit setup"
    fi
}

# Setup environment variables
setup_env() {
    log_info "Setting up environment configuration..."

    if [[ ! -f ".env" ]] && [[ -f ".env.example" ]]; then
        cp .env.example .env
        log_success "Environment file created from template"
        log_warning "Please edit .env file with your actual values"
    elif [[ -f ".env" ]]; then
        log_info "Environment file already exists"
    else
        log_warning "No .env.example found, skipping environment setup"
    fi
}

# Test basic functionality
test_setup() {
    log_info "Testing basic functionality..."

    # Test import
    python -c "import eks_validator; print('✅ Package import successful')" || {
        log_error "Package import failed"
        return 1
    }

    # Test basic command
    python main.py --help > /dev/null || {
        log_error "Basic command test failed"
        return 1
    }

    # Test config validation
    if [[ -f "test_config.py" ]]; then
        python test_config.py || {
            log_warning "Configuration test failed - check environment setup"
        }
    fi

    log_success "Basic functionality tests passed"
}

# Setup Docker (optional)
setup_docker() {
    if ! command -v docker &> /dev/null; then
        log_warning "Docker not found. Install Docker for container builds."
        return
    fi

    if [[ -f "Dockerfile" ]]; then
        log_info "Testing Docker setup..."
        docker build -t eks-cluster-validator:test . || {
            log_warning "Docker build failed - check Docker installation"
            return
        }
        log_success "Docker setup verified"
    fi
}

# Show setup summary
show_summary() {
    log_success "Setup completed successfully!"
    echo ""
    log_info "Next steps:"
    echo "  1. Configure your environment: edit .env file"
    echo "  2. Run tests: make test"
    echo "  3. Format code: make format"
    echo "  4. Build package: make pypi-build"
    echo "  5. For development: source venv/bin/activate"
    echo ""
    log_info "Available commands:"
    echo "  • make help          - Show all available commands"
    echo "  • make test          - Run tests"
    echo "  • make lint          - Run linting"
    echo "  • make format        - Format code"
    echo "  • make pypi-build    - Build for PyPI"
    echo "  • make docker-build  - Build Docker image"
    echo "  • ./scripts/release.sh - Run release process"
    echo ""
    log_info "Documentation:"
    echo "  • RELEASE.md         - Release process documentation"
    echo "  • ENVIRONMENT_SETUP.md - Environment configuration guide"
}

# Main setup process
main() {
    echo "🚀 EKS Cluster Validator Setup"
    echo "=============================="

    # Parse arguments
    SKIP_DOCKER=false
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-docker)
                SKIP_DOCKER=true
                shift
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo ""
                echo "Options:"
                echo "  --skip-docker    Skip Docker setup"
                echo "  --help          Show this help"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    check_directory
    setup_venv
    install_deps
    install_node_deps
    setup_precommit
    setup_env
    test_setup

    if [[ "$SKIP_DOCKER" != "true" ]]; then
        setup_docker
    fi

    show_summary
}

# Run main function
main "$@"
