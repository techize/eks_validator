# EKS Cluster Validator

[![PyPI version](https://badge.fury.io/py/eks-cluster-validator.svg)](https://pypi.org/project/eks-cluster-validator/)
[![Docker Image](https://img.shields.io/docker/pulls/techize/eks-validator)](https://hub.docker.com/r/techize/eks-validator)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A comprehensive validation tool for AWS EKS clusters that ensures your Kubernetes infrastructure meets security, performance, and compliance standards.

## Features

- 🔍 **Comprehensive Validation**: Validates cluster configuration, security settings, and best practices
- 📊 **Detailed Reporting**: Generates detailed reports with actionable recommendations
- 🐳 **Container Ready**: Available as a Docker container for easy deployment
- ⚙️ **Flexible Configuration**: Environment-based configuration with sensible defaults
- 🔧 **Extensible**: Plugin architecture for custom validation rules
- 📈 **CI/CD Integration**: Perfect for automated validation in deployment pipelines

## Quick Start

### Using Docker (Recommended)

```bash
docker run --rm \
  -e AWS_PROFILE=your-profile \
  -e AWS_REGION=us-east-1 \
  -v ~/.aws:/root/.aws:ro \
  techize/eks-validator:latest \
  --cluster-name my-cluster \
  --validate-all
```

### Using pip

```bash
pip install eks-cluster-validator
eks-validator --cluster-name my-cluster --validate-all
```

## Installation

See [Installation Guide](getting-started/installation.md) for detailed instructions.

## Documentation

- [Getting Started](getting-started/)
- [User Guide](user-guide/)
- [API Reference](api/)
- [Contributing](development/contributing.md)

## License

This project is licensed under the MIT License - see the [LICENSE](about/license.md) file for details.

## Support

- 📖 [Documentation](https://techize.github.io/eks_validator/)
- 🐛 [Issue Tracker](https://github.com/techize/eks_validator/issues)
- 💬 [Discussions](https://github.com/techize/eks_validator/discussions)
