# Release Process

This document outlines the complete release process for the EKS Cluster Validator.

## Prerequisites

Before releasing, ensure you have:

1. **Python Environment**: Python 3.8+ with pip
2. **Build Tools**: `pip install build twine`
3. **Docker** (optional): For container builds
4. **AWS Credentials**: For testing (optional)
5. **GitHub Token**: For repository access
6. **PyPI Account**: For package publishing

## Quick Release

### Automated Release (Recommended)

```bash
# Run the automated release script
./scripts/release.sh

# Or with specific version
./scripts/release.sh --version 1.1.0
```

### Manual Release

```bash
# Clean and setup
make clean
make install

# Quality checks
make format
make lint
make test

# Build packages
make pypi-build
make pypi-check

# Build Docker (optional)
make docker-build

# Deploy documentation (optional)
make docs-deploy
```

## GitHub Actions Release

The repository includes automated GitHub Actions workflows for releases:

### Triggering a Release

1. **Manual Release**:
   - Go to GitHub Actions → "Release Management"
   - Click "Run workflow"
   - Enter version (e.g., `1.1.0`) and type (`major`, `minor`, `patch`)

2. **Automatic Release**:
   - Push a git tag: `git tag v1.1.0 && git push origin v1.1.0`
   - Or create a GitHub release

### Release Workflow Steps

1. **Build & Test**: Runs quality checks and tests
2. **PyPI Publishing**: Uploads to PyPI (requires `PYPI_API_TOKEN` secret)
3. **Docker Publishing**: Builds and pushes Docker image (requires Docker Hub credentials)
4. **Documentation**: Updates GitHub Pages documentation
5. **Notifications**: Sends release notifications

## Required Secrets

Set these in your GitHub repository secrets:

### PyPI Publishing
- `PYPI_API_TOKEN`: Your PyPI API token

### Docker Publishing
- `DOCKER_USERNAME`: Docker Hub username
- `DOCKER_PASSWORD`: Docker Hub password/token

### GitHub Token
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions

## Version Management

### Version Format
Follow [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH` (e.g., `1.2.3`)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Updating Version

Update version in these files:
1. `setup.py`: `version="1.2.3"`
2. `pyproject.toml`: `version = "1.2.3"`
3. `eks_validator/__init__.py`: `__version__ = "1.2.3"`

## Release Checklist

### Pre-Release
- [ ] All tests pass (`make test`)
- [ ] Code formatted (`make format`)
- [ ] Linting passes (`make lint`)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version numbers updated
- [ ] Branch is `main` and up-to-date

### Release
- [ ] Create git tag: `git tag v1.2.3`
- [ ] Push tag: `git push origin v1.2.3`
- [ ] Monitor GitHub Actions workflow
- [ ] Verify PyPI package installation
- [ ] Verify Docker image availability
- [ ] Test documentation deployment

### Post-Release
- [ ] Create GitHub release with changelog
- [ ] Announce release in relevant channels
- [ ] Update any dependent documentation
- [ ] Monitor for issues

## Troubleshooting

### PyPI Upload Issues
```bash
# Check package before upload
twine check dist/*

# Upload to test PyPI first
twine upload --repository testpypi dist/*

# Check your API token
echo $TWINE_PASSWORD
```

### Docker Issues
```bash
# Check Docker is running
docker info

# Test build locally
docker build -t eks-cluster-validator:test .

# Test run
docker run --rm eks-cluster-validator:test --help
```

### GitHub Actions Issues
- Check repository secrets are set correctly
- Verify workflow permissions
- Check GitHub Actions logs for detailed error messages

## Release Channels

### PyPI (Python Package Index)
- **URL**: https://pypi.org/project/eks-cluster-validator/
- **Installation**: `pip install eks-cluster-validator`

### Docker Hub
- **URL**: https://hub.docker.com/r/techize/eks-cluster-validator
- **Pull**: `docker pull techize/eks-cluster-validator:latest`

### GitHub Releases
- **URL**: https://github.com/techize/eks-cluster-validator/releases
- **Assets**: Source code, changelog, documentation

## Support

For release-related issues:
1. Check this documentation
2. Review GitHub Actions logs
3. Check PyPI/Docker Hub status
4. Create an issue in the repository
