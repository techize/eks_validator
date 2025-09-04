"""
Configuration management for EKS Cluster Validator
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class EnvironmentConfig(BaseModel):
    """Configuration for a specific environment (test, uat, prod)"""

    name: str
    region: str
    cluster_name: str
    aws_profile: Optional[str] = None  # AWS profile specific to this environment
    environment: Optional[str] = None
    description: Optional[str] = None

    # VPC Configuration for enhanced networking checks
    vpc: Optional[Dict[str, Any]] = Field(default_factory=dict)

    # Legacy fields for backward compatibility
    vpc_id: Optional[str] = None
    subnet_ids: List[str] = Field(default_factory=list)
    security_groups: List[str] = Field(default_factory=list)
    node_groups: List[str] = Field(default_factory=list)
    load_balancers: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)
    monitoring_endpoints: List[str] = Field(default_factory=list)

    @validator("region")
    def validate_region(cls, v):
        """Validate AWS region format"""
        if not v.startswith(("us-", "eu-", "ap-", "ca-", "sa-")):
            raise ValueError(f"Invalid AWS region format: {v}")
        return v


class AWSConfig(BaseModel):
    """AWS-specific configuration"""

    profile: Optional[str] = None
    region: Optional[str] = None
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    assume_role_arn: Optional[str] = None
    session_duration: int = 3600
    external_id: Optional[str] = None


class KubernetesConfig(BaseModel):
    """Kubernetes-specific configuration"""

    kubeconfig_path: Optional[str] = None
    context_name: Optional[str] = None
    timeout: int = 30


class ValidationConfig(BaseModel):
    """Validation-specific configuration"""

    timeout: int = 300
    retry_attempts: int = 3
    retry_delay: int = 5
    parallel_checks: bool = True
    max_parallel_workers: int = 5
    strict_security_mode: bool = True
    debug: bool = False


class ReportConfig(BaseModel):
    """Report generation configuration"""

    output_dir: str = "reports"
    template_dir: str = "templates"
    include_timestamps: bool = True
    include_metadata: bool = True
    compress_reports: bool = False
    include_sensitive_data: bool = False
    format: str = "markdown"


class LoggingConfig(BaseModel):
    """Logging configuration"""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: str = "10 MB"
    retention: str = "7 days"


class Settings(BaseModel):
    """Main configuration settings"""

    aws: AWSConfig = Field(default_factory=AWSConfig)
    kubernetes: KubernetesConfig = Field(default_factory=KubernetesConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    report: ReportConfig = Field(default_factory=ReportConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    environments: Dict[str, EnvironmentConfig] = Field(default_factory=dict)

    @classmethod
    def from_yaml(cls, config_path: Path) -> "Settings":
        """Load settings from YAML configuration file"""
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)

        return cls(**config_data)

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables"""
        return cls(
            aws=AWSConfig(
                profile=os.getenv("AWS_PROFILE"),
                region=os.getenv("AWS_DEFAULT_REGION"),
                access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                assume_role_arn=os.getenv("AWS_ASSUME_ROLE_ARN"),
                external_id=os.getenv("AWS_EXTERNAL_ID"),
            ),
            kubernetes=KubernetesConfig(
                kubeconfig_path=os.getenv("KUBECONFIG"),
                context_name=os.getenv("KUBERNETES_CONTEXT"),
            ),
            validation=ValidationConfig(
                timeout=int(os.getenv("VALIDATION_TIMEOUT", "300")),
                max_parallel_workers=int(os.getenv("MAX_PARALLEL_WORKERS", "5")),
                strict_security_mode=os.getenv("STRICT_SECURITY_MODE", "true").lower()
                == "true",
                debug=os.getenv("DEBUG", "false").lower() == "true",
            ),
            report=ReportConfig(
                output_dir=os.getenv("REPORT_DIR", "reports"),
                include_sensitive_data=os.getenv(
                    "INCLUDE_SENSITIVE_DATA", "false"
                ).lower()
                == "true",
                format=os.getenv("REPORT_FORMAT", "markdown"),
            ),
            logging=LoggingConfig(
                level=os.getenv("LOG_LEVEL", "INFO"),
            ),
        )

    def get_environment_config(self, environment: str) -> EnvironmentConfig:
        """Get configuration for a specific environment"""
        if environment not in self.environments:
            raise ValueError(f"Environment '{environment}' not found in configuration")
        return self.environments[environment]

    def validate_configuration(self) -> List[str]:
        """Validate the complete configuration and return any issues"""
        issues = []

        # Check AWS configuration
        if not self.aws.profile and not os.getenv("AWS_ACCESS_KEY_ID"):
            issues.append(
                "AWS credentials not configured. Set AWS_PROFILE or "
                "AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY"
            )

        # Check environments
        if not self.environments:
            issues.append("No environments configured")

        for env_name, env_config in self.environments.items():
            if not env_config.cluster_name:
                issues.append(f"Environment '{env_name}': cluster_name is required")
            if not env_config.region:
                issues.append(f"Environment '{env_name}': region is required")

        return issues

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary"""
        return self.dict()

    def save_to_yaml(self, config_path: Path):
        """Save settings to YAML file"""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)
