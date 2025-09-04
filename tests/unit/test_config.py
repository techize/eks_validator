"""
Unit tests for configuration management.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch

from eks_validator.config.settings import (
    AWSConfig,
    KubernetesConfig,
    ValidationConfig,
    ReportConfig,
    Settings,
    load_config_from_file,
    load_config_from_env,
)


class TestAWSConfig:
    """Test AWS configuration."""

    def test_default_values(self):
        """Test default AWS configuration values."""
        config = AWSConfig()
        assert config.region == "us-east-1"
        assert config.profile is None
        assert config.role_arn is None
        assert config.external_id is None

    def test_custom_values(self):
        """Test custom AWS configuration values."""
        config = AWSConfig(
            region="eu-west-1",
            profile="test-profile",
            role_arn="arn:aws:iam::123456789012:role/test-role",
            external_id="test-external-id",
        )
        assert config.region == "eu-west-1"
        assert config.profile == "test-profile"
        assert config.role_arn == "arn:aws:iam::123456789012:role/test-role"
        assert config.external_id == "test-external-id"

    def test_from_env(self):
        """Test loading AWS config from environment variables."""
        env_vars = {
            "AWS_REGION": "us-west-2",
            "AWS_PROFILE": "env-profile",
            "AWS_ROLE_ARN": "arn:aws:iam::123456789012:role/env-role",
            "AWS_EXTERNAL_ID": "env-external-id",
        }

        with patch.dict(os.environ, env_vars):
            config = AWSConfig.from_env()
            assert config.region == "us-west-2"
            assert config.profile == "env-profile"
            assert config.role_arn == "arn:aws:iam::123456789012:role/env-role"
            assert config.external_id == "env-external-id"


class TestKubernetesConfig:
    """Test Kubernetes configuration."""

    def test_default_values(self):
        """Test default Kubernetes configuration values."""
        config = KubernetesConfig()
        assert config.config_file == "~/.kube/config"
        assert config.context is None
        assert config.namespace == "default"

    def test_custom_values(self):
        """Test custom Kubernetes configuration values."""
        config = KubernetesConfig(
            config_file="/path/to/kubeconfig",
            context="test-context",
            namespace="test-namespace",
        )
        assert config.config_file == "/path/to/kubeconfig"
        assert config.context == "test-context"
        assert config.namespace == "test-namespace"

    def test_from_env(self):
        """Test loading Kubernetes config from environment variables."""
        env_vars = {
            "KUBECONFIG": "/env/kubeconfig",
            "KUBERNETES_CONTEXT": "env-context",
            "KUBERNETES_NAMESPACE": "env-namespace",
        }

        with patch.dict(os.environ, env_vars):
            config = KubernetesConfig.from_env()
            assert config.config_file == "/env/kubeconfig"
            assert config.context == "env-context"
            assert config.namespace == "env-namespace"


class TestValidationConfig:
    """Test validation configuration."""

    def test_default_values(self):
        """Test default validation configuration values."""
        config = ValidationConfig()
        assert config.checks == ["cluster-health", "node-status", "pod-status"]
        assert config.severity_threshold == "warning"
        assert config.timeout == 300
        assert config.retries == 3

    def test_custom_values(self):
        """Test custom validation configuration values."""
        config = ValidationConfig(
            checks=["custom-check"], severity_threshold="error", timeout=600, retries=5
        )
        assert config.checks == ["custom-check"]
        assert config.severity_threshold == "error"
        assert config.timeout == 600
        assert config.retries == 5

    def test_from_env(self):
        """Test loading validation config from environment variables."""
        env_vars = {
            "VALIDATION_CHECKS": "check1,check2,check3",
            "VALIDATION_SEVERITY_THRESHOLD": "error",
            "VALIDATION_TIMEOUT": "600",
            "VALIDATION_RETRIES": "5",
        }

        with patch.dict(os.environ, env_vars):
            config = ValidationConfig.from_env()
            assert config.checks == ["check1", "check2", "check3"]
            assert config.severity_threshold == "error"
            assert config.timeout == 600
            assert config.retries == 5


class TestReportConfig:
    """Test report configuration."""

    def test_default_values(self):
        """Test default report configuration values."""
        config = ReportConfig()
        assert config.format == "console"
        assert config.output_file is None
        assert config.include_details is True
        assert config.color_output is True

    def test_custom_values(self):
        """Test custom report configuration values."""
        config = ReportConfig(
            format="json",
            output_file="/path/to/report.json",
            include_details=False,
            color_output=False,
        )
        assert config.format == "json"
        assert config.output_file == "/path/to/report.json"
        assert config.include_details is False
        assert config.color_output is False

    def test_from_env(self):
        """Test loading report config from environment variables."""
        env_vars = {
            "REPORT_FORMAT": "json",
            "REPORT_OUTPUT_FILE": "/env/report.json",
            "REPORT_INCLUDE_DETAILS": "false",
            "REPORT_COLOR_OUTPUT": "false",
        }

        with patch.dict(os.environ, env_vars):
            config = ReportConfig.from_env()
            assert config.format == "json"
            assert config.output_file == "/env/report.json"
            assert config.include_details is False
            assert config.color_output is False


class TestSettings:
    """Test main settings configuration."""

    def test_default_values(self):
        """Test default settings values."""
        settings = Settings()
        assert isinstance(settings.aws, AWSConfig)
        assert isinstance(settings.kubernetes, KubernetesConfig)
        assert isinstance(settings.validation, ValidationConfig)
        assert isinstance(settings.report, ReportConfig)

    def test_custom_values(self):
        """Test custom settings values."""
        aws_config = AWSConfig(region="eu-west-1")
        k8s_config = KubernetesConfig(namespace="test")
        validation_config = ValidationConfig(severity_threshold="error")
        report_config = ReportConfig(format="json")

        settings = Settings(
            aws=aws_config,
            kubernetes=k8s_config,
            validation=validation_config,
            report=report_config,
        )

        assert settings.aws.region == "eu-west-1"
        assert settings.kubernetes.namespace == "test"
        assert settings.validation.severity_threshold == "error"
        assert settings.report.format == "json"

    def test_from_env(self):
        """Test loading settings from environment variables."""
        env_vars = {
            "AWS_REGION": "us-west-2",
            "KUBERNETES_NAMESPACE": "env-namespace",
            "VALIDATION_SEVERITY_THRESHOLD": "error",
            "REPORT_FORMAT": "json",
        }

        with patch.dict(os.environ, env_vars):
            settings = Settings.from_env()
            assert settings.aws.region == "us-west-2"
            assert settings.kubernetes.namespace == "env-namespace"
            assert settings.validation.severity_threshold == "error"
            assert settings.report.format == "json"


class TestConfigLoading:
    """Test configuration file loading."""

    def test_load_config_from_file(self, sample_config_yaml):
        """Test loading configuration from YAML file."""
        settings = load_config_from_file(sample_config_yaml)

        assert settings.aws.region == "us-east-1"
        assert settings.aws.profile == "default"
        assert settings.kubernetes.config_file == "~/.kube/config"
        assert settings.kubernetes.context == "test-cluster"
        assert settings.validation.checks == ["cluster-health", "node-status"]
        assert settings.validation.severity_threshold == "warning"
        assert settings.report.format == "console"
        assert settings.report.output_file == "test-report.txt"

    def test_load_config_from_file_not_found(self):
        """Test loading configuration from non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_config_from_file(Path("/nonexistent/config.yaml"))

    def test_load_config_from_env(self):
        """Test loading configuration from environment variables."""
        env_vars = {
            "AWS_REGION": "us-west-2",
            "AWS_PROFILE": "env-profile",
            "KUBECONFIG": "/env/kubeconfig",
            "KUBERNETES_CONTEXT": "env-context",
            "KUBERNETES_NAMESPACE": "env-namespace",
            "VALIDATION_CHECKS": "env-check1,env-check2",
            "VALIDATION_SEVERITY_THRESHOLD": "error",
            "VALIDATION_TIMEOUT": "600",
            "VALIDATION_RETRIES": "5",
            "REPORT_FORMAT": "json",
            "REPORT_OUTPUT_FILE": "/env/report.json",
            "REPORT_INCLUDE_DETAILS": "false",
            "REPORT_COLOR_OUTPUT": "false",
        }

        with patch.dict(os.environ, env_vars):
            settings = load_config_from_env()

            assert settings.aws.region == "us-west-2"
            assert settings.aws.profile == "env-profile"
            assert settings.kubernetes.config_file == "/env/kubeconfig"
            assert settings.kubernetes.context == "env-context"
            assert settings.kubernetes.namespace == "env-namespace"
            assert settings.validation.checks == ["env-check1", "env-check2"]
            assert settings.validation.severity_threshold == "error"
            assert settings.validation.timeout == 600
            assert settings.validation.retries == 5
            assert settings.report.format == "json"
            assert settings.report.output_file == "/env/report.json"
            assert settings.report.include_details is False
            assert settings.report.color_output is False

    def test_load_config_from_env_empty(self):
        """Test loading configuration from empty environment."""
        # Clear all relevant environment variables
        env_vars_to_clear = [
            "AWS_REGION",
            "AWS_PROFILE",
            "AWS_ROLE_ARN",
            "AWS_EXTERNAL_ID",
            "KUBECONFIG",
            "KUBERNETES_CONTEXT",
            "KUBERNETES_NAMESPACE",
            "VALIDATION_CHECKS",
            "VALIDATION_SEVERITY_THRESHOLD",
            "VALIDATION_TIMEOUT",
            "VALIDATION_RETRIES",
            "REPORT_FORMAT",
            "REPORT_OUTPUT_FILE",
            "REPORT_INCLUDE_DETAILS",
            "REPORT_COLOR_OUTPUT",
        ]

        with patch.dict(os.environ, {k: "" for k in env_vars_to_clear}, clear=True):
            settings = load_config_from_env()

            # Should use default values
            assert settings.aws.region == "us-east-1"
            assert settings.aws.profile is None
            assert settings.kubernetes.config_file == "~/.kube/config"
            assert settings.kubernetes.context is None
            assert settings.kubernetes.namespace == "default"
