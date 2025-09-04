# EKS Cluster Validator - Configuration Examples

This directory contains example configuration files for different use cases of the EKS Cluster Validator.

## Basic Configuration

### `basic-config.yaml`

A minimal configuration for basic EKS cluster validation.

```yaml
# Basic EKS validation configuration
aws:
  region: us-east-1
  profile: default

kubernetes:
  config_file: ~/.kube/config
  context: my-eks-cluster

validation:
  checks:
    - cluster-health
    - node-status
    - pod-status
  severity_threshold: warning

reporting:
  format: console
  output_file: validation-report.txt
```

## Advanced Configuration

### `advanced-config.yaml`

A comprehensive configuration with all available options.

```yaml
# Advanced EKS validation configuration
aws:
  region: us-west-2
  profile: production
  role_arn: arn:aws:iam::123456789012:role/EKSValidatorRole
  session_duration: 3600

kubernetes:
  config_file: ~/.kube/config
  context: production-eks
  namespace: default

validation:
  checks:
    - cluster-health
    - node-status
    - pod-status
    - security-groups
    - iam-permissions
    - network-policies
    - resource-quotas
    - pod-security
  severity_threshold: info
  timeout: 300
  retry_count: 3
  retry_delay: 5

reporting:
  format: json
  output_file: /var/log/eks-validation-report.json
  include_timestamps: true
  include_metadata: true

logging:
  level: INFO
  file: /var/log/eks-validator.log
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
```

## Environment-Specific Configurations

### `development-config.yaml`

Configuration optimized for development environments.

```yaml
aws:
  region: us-east-1
  profile: dev

kubernetes:
  config_file: ~/.kube/config
  context: dev-eks

validation:
  checks:
    - cluster-health
    - node-status
    - pod-status
  severity_threshold: info
  timeout: 60

reporting:
  format: console
  include_timestamps: false

logging:
  level: DEBUG
```

### `production-config.yaml`

Configuration for production environments with enhanced security and monitoring.

```yaml
aws:
  region: us-west-2
  profile: production
  role_arn: arn:aws:iam::123456789012:role/EKSValidatorRole

kubernetes:
  config_file: /etc/kubernetes/config
  context: production-eks

validation:
  checks:
    - cluster-health
    - node-status
    - pod-status
    - security-groups
    - iam-permissions
    - network-policies
    - resource-quotas
    - pod-security
  severity_threshold: warning
  timeout: 600
  retry_count: 5

reporting:
  format: json
  output_file: /var/log/eks-validation/production-report.json
  include_timestamps: true
  include_metadata: true

logging:
  level: WARNING
  file: /var/log/eks-validator/production.log
```

## CI/CD Integration

### `ci-config.yaml`

Configuration for use in CI/CD pipelines.

```yaml
aws:
  region: ${{ AWS_REGION }}
  role_arn: ${{ AWS_ROLE_ARN }}

kubernetes:
  config_data: ${{ KUBE_CONFIG }}

validation:
  checks:
    - cluster-health
    - node-status
    - pod-status
  severity_threshold: error
  timeout: 120

reporting:
  format: json
  output_file: ci-validation-report.json

logging:
  level: INFO
```

## Usage Examples

### Command Line Usage

```bash
# Basic validation
eks-validator validate --config examples/basic-config.yaml

# With environment variables
export AWS_REGION=us-east-1
export KUBECONFIG=~/.kube/config
eks-validator validate --env-only

# CI/CD usage
eks-validator validate --config examples/ci-config.yaml --format json

# Custom output
eks-validator validate --config examples/advanced-config.yaml --output my-report.html
```

### Docker Usage

```bash
# Using Docker with config file
docker run --rm \
  -v $(pwd)/examples:/config \
  -v ~/.aws:/root/.aws \
  -v ~/.kube:/root/.kube \
  techize/eks-validator:latest \
  validate --config /config/production-config.yaml

# Using Docker with environment variables
docker run --rm \
  -e AWS_REGION=us-east-1 \
  -e AWS_PROFILE=production \
  -e KUBECONFIG=/kube/config \
  -v ~/.kube:/kube \
  techize/eks-validator:latest \
  validate --env-only
```

### Kubernetes Job

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: eks-validation-job
spec:
  template:
    spec:
      serviceAccountName: eks-validator-sa
      containers:
      - name: validator
        image: techize/eks-validator:latest
        command: ["eks-validator", "validate", "--env-only"]
        env:
        - name: AWS_REGION
          value: "us-east-1"
        - name: KUBECONFIG
          value: "/etc/kubernetes/config"
        volumeMounts:
        - name: kubeconfig
          mountPath: /etc/kubernetes
      volumes:
      - name: kubeconfig
        secret:
          secretName: kubeconfig-secret
      restartPolicy: Never
```

## Configuration Reference

### AWS Configuration

- `region`: AWS region where the EKS cluster is located
- `profile`: AWS CLI profile to use for authentication
- `role_arn`: IAM role ARN for cross-account access
- `session_duration`: Session duration in seconds (default: 3600)

### Kubernetes Configuration

- `config_file`: Path to kubeconfig file
- `config_data`: Base64 encoded kubeconfig data (for CI/CD)
- `context`: Kubernetes context to use
- `namespace`: Default namespace for validation

### Validation Configuration

- `checks`: List of validation checks to perform
- `severity_threshold`: Minimum severity level to report (info, warning, error)
- `timeout`: Validation timeout in seconds
- `retry_count`: Number of retries for failed checks
- `retry_delay`: Delay between retries in seconds

### Reporting Configuration

- `format`: Output format (console, json, yaml, html)
- `output_file`: Path to save validation report
- `include_timestamps`: Include timestamps in report
- `include_metadata`: Include metadata in report

### Logging Configuration

- `level`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `file`: Path to log file
- `format`: Log message format
