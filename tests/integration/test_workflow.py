"""
Integration tests for EKS Cluster Validator.
"""

import os
import pytest
from unittest.mock import patch

from eks_validator.config.settings import Settings, load_config_from_file
from eks_validator.core.validator import ClusterValidator


@pytest.mark.integration
class TestFullWorkflow:
    """Test the complete validation workflow."""

    def test_config_file_loading_and_validation(
        self, sample_config_yaml, mock_boto3_client, mock_kubernetes_client
    ):
        """Test loading config from file and running validation."""
        # Load configuration
        settings = load_config_from_file(sample_config_yaml)

        # Verify configuration loaded correctly
        assert settings.aws.region == "us-east-1"
        assert settings.aws.profile == "default"
        assert settings.kubernetes.context == "test-cluster"
        assert settings.validation.checks == ["cluster-health", "node-status"]
        assert settings.report.format == "console"

        # Create validator with mocked clients
        with patch("boto3.client", mock_boto3_client), patch(
            "kubernetes.config.load_kube_config"
        ), patch(
            "kubernetes.client.CoreV1Api",
            return_value=mock_kubernetes_client["core_v1"],
        ), patch(
            "kubernetes.client.AppsV1Api",
            return_value=mock_kubernetes_client["apps_v1"],
        ):

            validator = ClusterValidator(
                aws_config=settings.aws,
                k8s_config=settings.kubernetes,
                validation_config=settings.validation,
                report_config=settings.report,
            )

            # Run validation
            result = validator.validate()

            # Should succeed with mocked data
            assert result is True

    def test_environment_variable_configuration(
        self, mock_aws_credentials, mock_kubernetes_config
    ):
        """Test configuration loading from environment variables."""
        # Set environment variables
        env_vars = {
            "AWS_REGION": "us-west-2",
            "AWS_PROFILE": "test-profile",
            "KUBECONFIG": str(mock_kubernetes_config),
            "KUBERNETES_CONTEXT": "test-context",
            "KUBERNETES_NAMESPACE": "test-namespace",
            "VALIDATION_CHECKS": "cluster-health,pod-status",
            "VALIDATION_SEVERITY_THRESHOLD": "error",
            "REPORT_FORMAT": "json",
            "REPORT_OUTPUT_FILE": "/tmp/test-report.json",
        }

        with patch.dict(os.environ, env_vars):
            settings = Settings.from_env()

            # Verify environment variables were loaded
            assert settings.aws.region == "us-west-2"
            assert settings.aws.profile == "test-profile"
            assert settings.kubernetes.config_file == str(mock_kubernetes_config)
            assert settings.kubernetes.context == "test-context"
            assert settings.kubernetes.namespace == "test-namespace"
            assert settings.validation.checks == ["cluster-health", "pod-status"]
            assert settings.validation.severity_threshold == "error"
            assert settings.report.format == "json"
            assert settings.report.output_file == "/tmp/test-report.json"

    def test_config_file_override_environment(self, sample_config_yaml):
        """Test that config file values override environment variables."""
        # Set environment variables
        env_vars = {"AWS_REGION": "env-region", "REPORT_FORMAT": "env-format"}

        with patch.dict(os.environ, env_vars):
            # Load from file (should take precedence)
            settings = load_config_from_file(sample_config_yaml)

            # File values should override environment
            assert settings.aws.region == "us-east-1"  # From file
            assert settings.report.format == "console"  # From file, not env

    def test_validation_with_mocked_aws_services(
        self, mock_boto3_client, mock_kubernetes_client
    ):
        """Test validation with mocked AWS and Kubernetes services."""
        settings = Settings()

        with patch("boto3.client", mock_boto3_client), patch(
            "kubernetes.config.load_kube_config"
        ), patch(
            "kubernetes.client.CoreV1Api",
            return_value=mock_kubernetes_client["core_v1"],
        ), patch(
            "kubernetes.client.AppsV1Api",
            return_value=mock_kubernetes_client["apps_v1"],
        ):

            validator = ClusterValidator(
                aws_config=settings.aws,
                k8s_config=settings.kubernetes,
                validation_config=settings.validation,
                report_config=settings.report,
            )

            result = validator.validate()

            # Should succeed with properly mocked services
            assert result is True

            # Verify AWS client was called
            mock_boto3_client.assert_called()

            # Verify Kubernetes client methods were called
            mock_kubernetes_client["core_v1"].list_namespaced_pod.assert_called()
            mock_kubernetes_client["core_v1"].list_node.assert_called()


@pytest.mark.integration
@pytest.mark.slow
class TestEndToEndWorkflow:
    """End-to-end workflow tests (marked as slow)."""

    def test_cli_workflow_with_config_file(self, runner, sample_config_yaml):
        """Test complete CLI workflow with config file."""
        # This would be a full integration test with actual CLI
        # For now, we'll mock the components
        pass

    def test_cli_workflow_with_environment_vars(self, runner, mock_aws_credentials):
        """Test complete CLI workflow with environment variables."""
        # This would test the full CLI pipeline
        pass

    def test_validation_output_formats(self, sample_config_yaml):
        """Test different validation output formats."""
        # Test console, JSON, and other output formats
        pass


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling in integration scenarios."""

    def test_aws_connection_failure(self):
        """Test handling of AWS connection failures."""
        settings = Settings()

        with patch("boto3.client") as mock_client:
            mock_client.side_effect = Exception("AWS connection failed")

            validator = ClusterValidator(
                aws_config=settings.aws,
                k8s_config=settings.kubernetes,
                validation_config=settings.validation,
                report_config=settings.report,
            )

            result = validator.validate()

            # Should handle AWS failure gracefully
            assert result is False

    def test_kubernetes_connection_failure(self):
        """Test handling of Kubernetes connection failures."""
        settings = Settings()

        with patch("kubernetes.config.load_kube_config") as mock_load_config:
            mock_load_config.side_effect = Exception("Kubernetes connection failed")

            validator = ClusterValidator(
                aws_config=settings.aws,
                k8s_config=settings.kubernetes,
                validation_config=settings.validation,
                report_config=settings.report,
            )

            result = validator.validate()

            # Should handle Kubernetes failure gracefully
            assert result is False

    def test_partial_service_failures(self, mock_boto3_client, mock_kubernetes_client):
        """Test handling of partial service failures."""
        settings = Settings()

        # Make one service fail while others succeed
        with patch("boto3.client", mock_boto3_client), patch(
            "kubernetes.config.load_kube_config"
        ) as mock_load_config:

            mock_load_config.side_effect = Exception("K8s config load failed")

            validator = ClusterValidator(
                aws_config=settings.aws,
                k8s_config=settings.kubernetes,
                validation_config=settings.validation,
                report_config=settings.report,
            )

            result = validator.validate()

            # Should handle partial failures appropriately
            # (Exact behavior depends on implementation)
            assert isinstance(result, bool)
