# EKS Cluster Validator

A comprehensive validation tool for AWS EKS clusters that performs systematic testing across infrastructure, networking, storage, addons, monitoring, and application components, generating detailed markdown reports.

## ⚠️ Security Notice

**IMPORTANT**: This repository contains sensitive AWS infrastructure information that should never be committed to public repositories. The tool is designed to validate your EKS clusters but generates reports containing real AWS resource IDs, cluster names, VPC configurations, and other sensitive data.

### Safe Usage Guidelines

1. **Never commit sensitive files**: The `.gitignore` file excludes `config.yaml` and `reports/` directory
2. **Use example files**: Copy `config.example.yaml` to `config.yaml` and customize with your values
3. **Local development only**: Keep sensitive configuration files local and never share them
4. **Clean before sharing**: Always run `git status` and ensure no sensitive files are staged

### Repository Structure
```
eks-cluster-validator/
├── config.example.yaml    # Template with placeholder values
├── config.yaml           # Your local config (gitignored)
├── reports/              # Generated reports (gitignored)
│   └── example_validation_report.md  # Example report structure
└── .gitignore           # Excludes sensitive files
```

## Features

- **Comprehensive Validation**: Tests all critical EKS cluster components
- **Multi-Environment Support**: Validate test, UAT, and production environments
- **Parallel Processing**: Run checks concurrently for faster validation
- **Detailed Reports**: Generate markdown reports with recommendations
- **Modular Architecture**: Easily extend with custom checkers
- **AWS Integration**: Full AWS SDK integration with role assumption support

## Prerequisites

Before installing and using the EKS Cluster Validator, ensure you have the following prerequisites:

### Required Tools

- **Python 3.8+**: The validator is written in Python
- **AWS CLI**: For AWS authentication and cluster access
- **kubectl**: For Kubernetes cluster interaction
- **markdownlint**: For documentation validation and formatting

### Installation Commands

```bash
# Install markdownlint (Node.js required)
npm install -g markdownlint-cli

# Or using Homebrew (macOS)
brew install markdownlint-cli

# Or using pip (Python package)
pip install markdownlint
```

## Installation

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd eks-cluster-validator
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure AWS credentials:**

   ```bash
   # Option 1: AWS CLI configuration
   aws configure

   # Option 2: Environment variables
   export AWS_ACCESS_KEY_ID=your-access-key
   export AWS_SECRET_ACCESS_KEY=your-secret-key
   export AWS_DEFAULT_REGION=us-east-1
   ```

4. **Configure the application:**

   ```bash
   # Copy the example configuration file
   cp config.example.yaml config.yaml

   # Edit config.yaml with your actual cluster details
   # NEVER commit config.yaml to version control
   ```

## Configuration

**Security Note**: Never commit your `config.yaml` file. Use the provided `config.example.yaml` as a template.

### Using Example Configuration

1. **Copy the example file:**
   ```bash
   cp config.example.yaml config.yaml
   ```

2. **Edit your configuration:**
   ```bash
   # Edit config.yaml with your actual values
   nano config.yaml  # or your preferred editor
   ```

3. **Example configuration structure:**
   ```yaml
   environments:
     test:
       cluster_name: "your-test-cluster-name"
       region: "us-east-1"
       environment: "test"
       # Add your VPC configuration here
       vpc:
         vpc_id: "vpc-xxxxxxxxxxxxxxxxx"
         subnet_ids:
           - "subnet-xxxxxxxxxxxxxxxxx"
         security_groups:
           - "sg-xxxxxxxxxxxxxxxxx"
   ```

### Configuration File Security

- `config.example.yaml`: Safe to commit (contains placeholder values)
- `config.yaml`: Your local configuration (automatically gitignored)
- `config.local.yaml`: Alternative local config file (also gitignored)

**Important**: The `.gitignore` file automatically excludes:
- `config.yaml`
- `config.local.yaml`
- `reports/` directory
- All `.report` files

## Development Setup

### Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) to maintain code quality and prevent common issues. Pre-commit hooks automatically run checks on your code before each commit.

#### Installing Pre-commit

```bash
# Install pre-commit (choose one method)

# Using pip (recommended)
pip install pre-commit

# Using Homebrew (macOS)
brew install pre-commit

# Using conda
conda install -c conda-forge pre-commit
```

#### Setting Up Pre-commit Hooks

After cloning the repository and installing dependencies:

```bash
# Install the pre-commit hooks
pre-commit install

# Optional: Install hooks for commit-msg checks
pre-commit install --hook-type commit-msg
```

#### Pre-commit Configuration

The project includes the following pre-commit hooks:

- **trailing-whitespace**: Removes trailing whitespace
- **end-of-file-fixer**: Ensures files end with a newline
- **check-yaml**: Validates YAML file syntax
- **check-added-large-files**: Prevents large files from being committed
- **check-merge-conflict**: Checks for merge conflict markers
- **debug-statements**: Prevents debug statements in production code
- **black**: Code formatting (88 character line length)
- **flake8**: Linting with custom rules (max line length 88, ignores E203, W503)
- **validate-no-sensitive-data**: Custom hook to prevent committing sensitive AWS data

#### Running Pre-commit Manually

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
pre-commit run flake8 --all-files

# Run hooks on staged files only
pre-commit run

# Run hooks on specific files
pre-commit run --files main.py eks_validator/config/settings.py
```

#### Advanced Pre-commit Configuration

For advanced users, you can customize the pre-commit behavior:

```bash
# Update all hooks to their latest versions
pre-commit autoupdate
```

```bash
# Run hooks on specific file types only
pre-commit run --files "*.py" --all-files
```

```bash
# Skip specific hooks for a commit
SKIP=black,flake8 git commit -m "Quick fix"
```

```bash
# Run hooks without fixing files (check-only mode)
pre-commit run --all-files --check-only
```

#### Pre-commit in Docker Development

When developing with Docker, you can run pre-commit checks:

```bash
# Run pre-commit in Docker container
docker run --rm -v $(pwd):/app -w /app python:3.11-slim
  bash -c "pip install pre-commit && pre-commit run --all-files"
```

```bash
# Or use the project's Dockerfile
docker build -t eks-validator .
docker run --rm -v $(pwd):/app eks-validator
  bash -c "cd /app && pre-commit run --all-files"
```

#### Pre-commit Troubleshooting

**Common Issues and Solutions:**

1. **"pre-commit not found"**:

   ```bash
   # Ensure pre-commit is installed
   pip install --upgrade pre-commit
   ```

2. **Hooks fail after dependency updates**:

   ```bash
   # Update hook versions
   pre-commit autoupdate
   ```

3. **Want to bypass hooks temporarily**:

   ```bash
   # Use --no-verify (not recommended for regular use)
   git commit --no-verify -m "Emergency fix"
   ```

4. **Pre-commit is slow**:

   ```bash
   # Run only on changed files
   pre-commit run
   # Or install faster alternatives for some hooks
   pip install black[isort]  # Faster sorting
   ```

#### Pre-commit Integration with IDEs

**VS Code Integration:**

- Install the "Pre-commit" extension
- Configure automatic pre-commit runs on save
- Set up pre-commit as the default formatter

**PyCharm/IntelliJ Integration:**

- Configure pre-commit as an external tool
- Set up pre-commit hooks to run before commit
- Enable automatic import sorting with black integration

#### Pre-commit in Docker Development

When developing with Docker, you can run pre-commit checks:

```bash
# Run pre-commit in Docker container
docker run --rm -v $(pwd):/app -w /app python:3.11-slim \
  bash -c "pip install pre-commit && pre-commit run --all-files"
```

```bash
# Or use the project's Dockerfile
docker build -t eks-validator .
docker run --rm -v $(pwd):/app eks-validator \
  bash -c "cd /app && pre-commit run --all-files"
```

#### Advanced Pre-commit Troubleshooting

**Common Issues and Solutions:**

1. **"pre-commit not found"**:

   ```bash
   # Ensure pre-commit is installed
   pip install --upgrade pre-commit
   ```

2. **Hooks fail after dependency updates**:

   ```bash
   # Update hook versions
   pre-commit autoupdate
   ```

3. **Want to bypass hooks temporarily**:

   ```bash
   # Use --no-verify (not recommended for regular use)
   git commit --no-verify -m "Emergency fix"
   ```

4. **Pre-commit is slow**:

   ```bash
   # Run only on changed files
   pre-commit run
   # Or install faster alternatives for some hooks
   pip install black[isort]  # Faster sorting
   ```

#### IDE Integration with Pre-commit

**VS Code Integration:**

- Install the "Pre-commit" extension
- Configure automatic pre-commit runs on save
- Set up pre-commit as the default formatter

**PyCharm/IntelliJ Integration:**

- Configure pre-commit as an external tool
- Set up pre-commit hooks to run before commit
- Enable automatic import sorting with black integration

### Environment Variables

The application supports configuration via environment variables for sensitive data and runtime configuration:

#### AWS Configuration

```bash
# AWS Credentials (alternative to AWS CLI)
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=us-east-1

# AWS Profile (if using named profiles)
export AWS_PROFILE=my-profile

# Role Assumption
export AWS_ASSUME_ROLE_ARN=arn:aws:iam::123456789012:role/EKSValidatorRole
export AWS_EXTERNAL_ID=your-external-id
```

#### Kubernetes Configuration

```bash
# Kubeconfig path
export KUBECONFIG=~/.kube/config

# Kubernetes context
export KUBERNETES_CONTEXT=my-cluster-context
```

#### Application Configuration

```bash
# Logging level
export LOG_LEVEL=DEBUG

# Report output directory
export REPORT_DIR=./reports

# Validation timeout
export VALIDATION_TIMEOUT=300

# Parallel processing
export MAX_PARALLEL_WORKERS=5
```

#### Environment File

Create a `.env` file in the project root for local development:

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your values
nano .env
```

**Security Note**: Never commit `.env` files containing real credentials. The `.gitignore` file automatically excludes `.env` files.

## Usage

### Basic Validation

```bash
# Validate test environment
python main.py validate test

# Validate with custom output file
python main.py validate prod --output reports/prod-validation.md

# Quick health check
python main.py quick-check test
```

### Component-Specific Checks

```bash
# Check only infrastructure
python main.py check-component test --component infra

# Check only networking
python main.py check-component prod --component network

# Available components: infra, network, storage, addons, monitoring, apps
```

### Advanced Options

```bash
# Verbose logging
python main.py --verbose validate test

# Custom configuration file
python main.py --config config.prod.yaml validate prod

# Generate JSON report
python main.py validate test --format json --output report.json
```

## Report Security

**Critical**: Validation reports contain sensitive infrastructure information including:

- Real AWS resource IDs (VPC, subnets, security groups)
- Cluster names and configurations
- Database instance details
- Network configurations
- IAM role ARNs

### Safe Report Handling

1. **Reports are automatically excluded** from git commits via `.gitignore`
2. **Example report available**: See `reports/example_validation_report.md` for structure
3. **Never share real reports** containing sensitive data
4. **Clean reports directory** before sharing the repository:

   ```bash
   rm -rf reports/*.md  # Remove all real reports
   ```

### Report Structure

The `example_validation_report.md` shows the complete report structure with:

- Infrastructure validation results
- Networking configuration details
- Storage and addon status
- Monitoring setup verification
- Application health checks
- Security recommendations

## Validation Components

### Infrastructure Validation

- EKS cluster status and version
- Node groups configuration
- VPC and subnet setup
- Security groups
- IAM roles and policies

### Networking Validation

- Load balancers (ALB/NLB)
- Security group rules
- Network ACLs
- Route tables
- Internet gateway and NAT gateways

### Storage Validation

- CSI drivers (EBS, EFS) - supports both EKS add-ons and self-managed installations
- Storage classes
- Persistent volumes
- Persistent volume claims

### Addon Validation

- EKS managed addons (CoreDNS, kube-proxy, VPC CNI)
- Addon versions and health
- Essential addon requirements

### Monitoring Validation

- CloudWatch logging configuration
- CloudWatch Container Insights
- CloudTrail setup
- Prometheus stack detection
- Fluent Bit configuration
- **Loki logging stack detection** (Grafana Loki with Promtail)
- **Multi-logging architecture support** - recognizes both CloudWatch AND Loki as valid logging solutions

### Application Validation

- Kubernetes deployments health
- Services configuration
- Ingress resources and TLS
- Database connectivity
- Application health checks

## Report Formats

### Markdown Reports

- Executive summary with status overview
- Detailed findings for each component
- Actionable recommendations
- Formatted for easy reading and sharing

### JSON Reports

- Structured data for integration
- Complete validation results
- Machine-readable format

### HTML Reports

- Web-viewable reports
- Enhanced formatting
- Downloadable artifacts

## AWS Permissions Required

The tool requires the following IAM permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "eks:DescribeCluster",
                "eks:ListClusters",
                "eks:ListNodegroups",
                "eks:DescribeNodegroup",
                "eks:ListAddons",
                "eks:DescribeAddon",
                "eks:DescribeAddonVersions",
                "ec2:DescribeVpcs",
                "ec2:DescribeSubnets",
                "ec2:DescribeSecurityGroups",
                "ec2:DescribeNetworkAcls",
                "ec2:DescribeRouteTables",
                "ec2:DescribeInternetGateways",
                "ec2:DescribeNatGateways",
                "ec2:DescribeInstances",
                "elasticloadbalancing:DescribeLoadBalancers",
                "elasticloadbalancing:DescribeTargetGroups",
                "rds:DescribeDBInstances",
                "cloudwatch:ListMetrics",
                "logs:DescribeLogGroups",
                "cloudtrail:ListTrails",
                "cloudtrail:GetTrailStatus",
                "iam:ListRoles",
                "iam:ListAttachedRolePolicies"
            ],
            "Resource": "*"
        }
    ]
}
```

## Kubernetes Access

For application and storage validation, the tool needs Kubernetes API access:

```bash
# Option 1: Use kubeconfig
export KUBECONFIG=/path/to/kubeconfig

# Option 2: Run in-cluster (when deployed as a pod)
# The tool will auto-detect in-cluster configuration
```

## Development

### Adding Custom Checkers

1. Create a new checker class in `eks_validator/checkers/`
2. Implement the `check_all()` method
3. Add the checker to the `EKSValidator` class
4. Update the CLI component choices

### Extending Reports

1. Modify templates in `eks_validator/templates/`
2. Update the `ReportGenerator` class
3. Add new export formats as needed

## Troubleshooting

### Common Issues

1. **AWS Credentials**: Ensure AWS credentials are properly configured
2. **Kubernetes Access**: Verify kubeconfig or in-cluster permissions
3. **Network Connectivity**: Check VPC and security group configurations
4. **SSL Certificate Issues**: If you see SSL certificate verification errors, the validator will gracefully handle them:
   - Storage and application checks may show warnings instead of failures
   - Loki logging detection will provide manual verification guidance
   - Use `export KUBERNETES_SKIP_TLS_VERIFY=true` to bypass SSL verification if needed
5. **Multi-Logging Architecture**: The validator now supports both CloudWatch AND Loki as valid logging solutions:
   - Production environments typically use CloudWatch
   - UAT/development may use Loki with Promtail
   - Either logging solution being properly configured will result in acceptable monitoring status
6. **Permissions**: Ensure IAM roles have required permissions

### Debug Mode

```bash
# Enable verbose logging
python main.py --verbose validate test

# Check specific component with detailed output
python main.py --verbose check-component test --component infra
```

## Preparing for Public Sharing

Before making this repository public, ensure security:

### Pre-Sharing Checklist

1. **Verify .gitignore exclusions:**

   ```bash
   git status
   # Ensure no sensitive files are staged
   ```

2. **Clean sensitive files:**

   ```bash
   # Remove any real reports (keep example)
   rm -f reports/*.md
   ls reports/  # Should only show example_validation_report.md
   ```

3. **Check for sensitive data:**

   ```bash
   # Search for potential AWS resource IDs
   grep -r "vpc-\|subnet-\|sg-\|arn:aws:" .
   # Should only find placeholder values in example files
   ```

4. **Validate configuration:**

   ```bash
   # Ensure only example config exists
   ls -la config*
   # Should show: config.example.yaml (tracked) and config.yaml (gitignored)
   ```

### What Gets Shared Publicly

✅ **Safe to share:**

- Source code and scripts
- `config.example.yaml` (placeholder values)
- `reports/example_validation_report.md` (placeholder data)
- Documentation and README
- Requirements and dependencies

❌ **Never share:**

- `config.yaml` (real cluster configuration)
- `reports/*.md` (real validation reports)
- Any files containing real AWS resource IDs
- Local configuration files

## Pre-commit Hooks Setup

This repository uses pre-commit hooks to ensure code quality and security. The hooks automatically validate that no sensitive AWS infrastructure data is committed.

### Installing Pre-commit Hooks

```bash
# Install pre-commit (if not already installed)
pip install pre-commit

# Install the hooks in this repository
pre-commit install

# (Optional) Run hooks on all files
pre-commit run --all-files
```

#### What the Hooks Do

- **Security Validation**: Blocks commits containing sensitive AWS data (resource IDs, cluster names, IP addresses)
- **Code Quality**: Runs Black (code formatting), Flake8 (linting), and other quality checks
- **File Validation**: Checks for trailing whitespace, merge conflicts, and large files

#### Customizing Validation Patterns

The sensitive data validation is designed to be generic but customizable for your organization's naming conventions. By default, it includes common AWS resource patterns and a generic EKS cluster pattern.

##### Environment Variable Configuration

The recommended way to customize validation patterns is through environment variables. This keeps your configuration separate from the code and allows for easy updates.

###### Creating Environment Configuration File

Create a dedicated environment file for your EKS validator settings:

```bash
# Create the environment file
touch ~/.eks_validator_env
```

Add your organization-specific patterns to the file:

```bash
# ~/.eks_validator_env
# Custom validation patterns for your organization
export CUSTOM_PATTERNS='\bsp-eks-(test|uat|prd|prod|dev|staging)-\d*\b,\bk8s-[a-z0-9-]+\b,\beks-[a-z0-9-]+-\d{2}\b'
```

###### Shell Integration

To automatically load your environment variables when opening a new terminal:

**For Zsh (macOS default):**

```bash
# Add to ~/.zshrc
if [ -f ~/.eks_validator_env ]; then
    source ~/.eks_validator_env
fi
```

**For Bash:**

```bash
# Add to ~/.bashrc or ~/.bash_profile
if [ -f ~/.eks_validator_env ]; then
    source ~/.eks_validator_env
fi
```

**For Fish:**

```bash
# Add to ~/.config/fish/config.fish
if test -f ~/.eks_validator_env
    source ~/.eks_validator_env
end
```

After updating your shell configuration, reload it:

```bash
# For Zsh
source ~/.zshrc

# For Bash
source ~/.bashrc

# For Fish
source ~/.config/fish/config.fish
```

###### Verifying Environment Setup

Test that your environment variables are loaded:

```bash
# Check if CUSTOM_PATTERNS is set
echo $CUSTOM_PATTERNS

# Test the validation script with your patterns
python scripts/validate_sensitive_data.py --test-patterns
```

#### Adding Organization-Specific Patterns

You can customize the validation patterns in two ways:

##### Option 1: Environment Variable (Recommended)

Set the `CUSTOM_PATTERNS` environment variable with comma-separated regex patterns:

```bash
# For macOS/Linux
export CUSTOM_PATTERNS='\bsp-eks-(test|uat|prd|prod|dev|staging)-\d*\b,\bmy-company-eks-[a-z0-9-]+\b'

# For Windows PowerShell
$env:CUSTOM_PATTERNS='\bsp-eks-(test|uat|prd|prod|dev|staging)-\d*\b,\bmy-company-eks-[a-z0-9-]+\b'
```

###### Option 2: Direct Script Modification

Edit `scripts/validate_sensitive_data.py` and add your patterns to the `custom_cluster_patterns` list:

```python
# In scripts/validate_sensitive_data.py, around line 35
self.custom_cluster_patterns = [
    r'\bsp-eks-(test|uat|prd|prod|dev|staging)-\d*\b',  # Your organization pattern
    r'\bmy-company-eks-[a-z0-9-]+\b',  # Another pattern
    r'\beks-[a-z0-9-]+-\d{2}\b',  # Generic EKS pattern (already included)
]
```

##### Pattern Examples

- `r'\bsp-eks-(test|uat|prd|prod|dev|staging)-\d*\b'` - Matches `sp-eks-test-01`, `sp-eks-prod-123`
- `r'\beks-[a-z0-9-]+-\d{2}\b'` - Matches `eks-my-cluster-01`, `eks-production-02`
- `r'\bmy-company-eks-[a-z0-9-]+\b'` - Matches `my-company-eks-dev`, `my-company-eks-staging`

#### Manual Testing

You can test the security validation manually:

```bash
# Test sensitive data validation
pre-commit run validate-no-sensitive-data --all-files

# Test all hooks
pre-commit run --all-files
```

#### Bypassing Hooks (Emergency Only)

In rare cases where you need to bypass the hooks:

```bash
git commit --no-verify -m "Your commit message"
```

⚠️ **Warning**: Only use `--no-verify` when absolutely necessary and ensure no sensitive data is being committed.
