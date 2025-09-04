# EKS Cluster Validator API Reference

This document provides a comprehensive API reference for the EKS Cluster Validator tool.

## Table of Contents

- [Core Classes](#core-classes)
- [Configuration Classes](#configuration-classes)
- [Checker Classes](#checker-classes)
- [Utility Classes](#utility-classes)
- [CLI Interface](#cli-interface)

## Core Classes

### EKSValidator

The main validation orchestrator class.

#### EKSValidator Constructor

```python
EKSValidator(settings: Settings)
```

**Parameters:**

- `settings` (Settings): Configuration object containing all validation settings

#### EKSValidator Methods

##### `validate_environment(environment: str) -> ValidationReport`

Validates a complete EKS environment.

**Parameters:**

- `environment` (str): Environment name ('test', 'uat', 'prod')

**Returns:**

- `ValidationReport`: Complete validation results

**Raises:**

- `ValidationError`: When validation fails critically
- `ConfigurationError`: When configuration is invalid

##### `validate_component(environment: str, component: str) -> ComponentReport`

Validates a specific component only.

**Parameters:**

- `environment` (str): Environment name
- `component` (str): Component name ('infra', 'network', 'storage', 'addons', 'monitoring', 'apps')

**Returns:**

- `ComponentReport`: Component-specific validation results

## Configuration Classes

### Settings

Main configuration container.

#### Settings Constructor

```python
Settings.from_yaml(config_path: Path) -> Settings
Settings.from_env() -> Settings
```

#### Settings Properties

- `aws` (AWSConfig): AWS-specific configuration
- `kubernetes` (KubernetesConfig): Kubernetes configuration
- `validation` (ValidationConfig): Validation settings
- `report` (ReportConfig): Report generation settings
- `logging` (LoggingConfig): Logging configuration
- `environments` (Dict[str, EnvironmentConfig]): Per-environment configs

### AWSConfig

AWS configuration settings.

#### AWSConfig Properties

- `profile` (Optional[str]): AWS profile name
- `region` (Optional[str]): Default AWS region
- `access_key_id` (Optional[str]): AWS access key
- `secret_access_key` (Optional[str]): AWS secret key
- `assume_role_arn` (Optional[str]): Role to assume
- `external_id` (Optional[str]): External ID for role assumption

### ValidationConfig

Validation behavior configuration.

#### ValidationConfig Properties

- `timeout` (int): Validation timeout in seconds (default: 300)
- `retry_attempts` (int): Number of retry attempts (default: 3)
- `parallel_checks` (bool): Enable parallel validation (default: True)
- `max_parallel_workers` (int): Maximum parallel workers (default: 5)
- `strict_security_mode` (bool): Enable strict security checks (default: True)

## Checker Classes

### InfrastructureChecker

Validates EKS infrastructure components.

#### InfrastructureChecker Methods

##### `check_cluster_status() -> CheckResult`

Validates EKS cluster status and version.

##### `check_node_groups() -> CheckResult`

Validates node group configurations.

##### `check_vpc_configuration() -> CheckResult`

Validates VPC and networking setup.

### NetworkingChecker

Validates networking components.

#### NetworkingChecker Methods

##### `check_load_balancers() -> CheckResult`

Validates load balancer configurations.

##### `check_security_groups() -> CheckResult`

Validates security group rules.

##### `check_route_tables() -> CheckResult`

Validates route table configurations.

### StorageChecker

Validates storage components.

#### StorageChecker Methods

##### `check_ebs_volumes() -> CheckResult`

Validates EBS volume configurations.

##### `check_efs_filesystems() -> CheckResult`

Validates EFS filesystem setup.

##### `check_storage_classes() -> CheckResult`

Validates Kubernetes storage classes.

### AddonChecker

Validates EKS addons.

#### AddonChecker Methods

##### `check_core_dns() -> CheckResult`

Validates CoreDNS addon.

##### `check_kube_proxy() -> CheckResult`

Validates kube-proxy addon.

##### `check_vpc_cni() -> CheckResult`

Validates VPC CNI addon.

### MonitoringChecker

Validates monitoring setup.

#### MonitoringChecker Methods

##### `check_cloudwatch_logs() -> CheckResult`

Validates CloudWatch logging.

##### `check_container_insights() -> CheckResult`

Validates Container Insights.

##### `check_prometheus() -> CheckResult`

Validates Prometheus monitoring.

### ApplicationChecker

Validates application deployments.

#### ApplicationChecker Methods

##### `check_deployments() -> CheckResult`

Validates Kubernetes deployments.

##### `check_services() -> CheckResult`

Validates Kubernetes services.

##### `check_ingresses() -> CheckResult`

Validates ingress configurations.

## Utility Classes

### ReportGenerator

Generates validation reports.

#### ReportGenerator Methods

##### `generate_markdown_report(results: ValidationResults) -> str`

Generates a markdown-formatted report.

##### `generate_json_report(results: ValidationResults) -> str`

Generates a JSON-formatted report.

##### `save_report(report: str, output_path: Path)`

Saves report to file.

### CheckResult

Standardized result format for all checks.

#### CheckResult Properties

- `status` (str): 'PASS', 'FAIL', 'WARNING', 'ERROR'
- `message` (str): Human-readable result message
- `details` (Dict): Additional result details
- `recommendations` (List[str]): Suggested fixes or improvements
- `metadata` (Dict): Additional metadata

## CLI Interface

### Command Line Usage

```bash
# Validate complete environment
eks-validator validate <environment>

# Validate specific component
eks-validator check-component <environment> --component <component>

# Use custom config file
eks-validator --config config.yaml validate test

# Load from environment variables only
eks-validator --env-only validate prod

# Enable verbose logging
eks-validator --verbose validate test
```

### CLI Options

- `--config, -c`: Path to configuration file
- `--env-only`: Load configuration from environment variables only
- `--verbose, -v`: Enable verbose logging
- `--output, -o`: Output file path for reports
- `--format, -f`: Report format ('markdown', 'json', 'html')

## Error Handling

### Custom Exceptions

#### `ValidationError`

Raised when validation encounters a critical error.

#### `ConfigurationError`

Raised when configuration is invalid or missing.

#### `AWSError`

Raised when AWS API calls fail.

#### `KubernetesError`

Raised when Kubernetes API calls fail.

### Error Response Format

```python
{
    "error": {
        "type": "ValidationError",
        "message": "Critical validation failure",
        "details": {...},
        "recommendations": [...]
    }
}
```

## Environment Variables

All configuration can be provided via environment variables:

### AWS Configuration

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_DEFAULT_REGION`
- `AWS_PROFILE`
- `AWS_ASSUME_ROLE_ARN`
- `AWS_EXTERNAL_ID`

### Application Configuration

- `LOG_LEVEL`
- `REPORT_DIR`
- `VALIDATION_TIMEOUT`
- `MAX_PARALLEL_WORKERS`
- `STRICT_SECURITY_MODE`
- `DEBUG`

### Kubernetes Configuration

- `KUBECONFIG`
- `KUBERNETES_CONTEXT`

## Examples

### Basic Validation

```python
from eks_validator.core.validator import EKSValidator
from eks_validator.config.settings import Settings

# Load configuration
settings = Settings.from_yaml(Path("config.yaml"))

# Create validator
validator = EKSValidator(settings)

# Validate environment
report = validator.validate_environment("test")
print(report.generate_markdown())
```

### Custom Check Implementation

```python
from eks_validator.checkers.base_checker import BaseChecker
from eks_validator.utils.check_result import CheckResult

class CustomChecker(BaseChecker):
    def check_custom_component(self) -> CheckResult:
        # Implement custom validation logic
        return CheckResult(
            status="PASS",
            message="Custom component validation successful",
            details={"component": "custom"}
        )
```

## Contributing

When adding new checkers or modifying the API:

1. Extend `BaseChecker` for new checkers
2. Return `CheckResult` objects for all checks
3. Add proper error handling and logging
4. Update this API documentation
5. Add unit tests for new functionality
