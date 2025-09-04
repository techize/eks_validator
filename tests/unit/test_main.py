"""
Unit tests for main CLI functionality.
"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from pathlib import Path

from main import cli, validate_cluster


class TestCLI:
    """Test CLI commands."""

    @pytest.fixture
    def runner(self):
        """CLI test runner."""
        return CliRunner()

    def test_cli_help(self, runner):
        """Test CLI help command."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "EKS Cluster Validator" in result.output
        assert "--config" in result.output
        assert "--env-only" in result.output
        assert "--verbose" in result.output

    def test_cli_version(self, runner):
        """Test CLI version command."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output.lower()

    @patch("main.load_config_from_file")
    @patch("main.load_config_from_env")
    @patch("main.validate_cluster")
    def test_cli_with_config_file(
        self, runner, mock_validate, mock_env_config, mock_file_config
    ):
        """Test CLI with configuration file."""
        mock_file_config.return_value = MagicMock()
        mock_validate.return_value = True

        with runner.isolated_filesystem():
            config_file = Path("test-config.yaml")
            config_file.write_text("aws:\n  region: us-east-1\n")

            result = runner.invoke(cli, ["--config", str(config_file)])

            assert result.exit_code == 0
            mock_file_config.assert_called_once_with(config_file)
            mock_validate.assert_called_once()

    @patch("main.load_config_from_env")
    @patch("main.validate_cluster")
    def test_cli_with_env_only(self, runner, mock_validate, mock_env_config):
        """Test CLI with environment-only configuration."""
        mock_env_config.return_value = MagicMock()
        mock_validate.return_value = True

        result = runner.invoke(cli, ["--env-only"])

        assert result.exit_code == 0
        mock_env_config.assert_called_once()
        mock_validate.assert_called_once()

    @patch("main.load_config_from_file")
    @patch("main.load_config_from_env")
    @patch("main.validate_cluster")
    def test_cli_with_both_config_and_env(
        self, runner, mock_validate, mock_env_config, mock_file_config
    ):
        """Test CLI with both config file and environment variables."""
        mock_file_config.return_value = MagicMock()
        mock_env_config.return_value = MagicMock()
        mock_validate.return_value = True

        with runner.isolated_filesystem():
            config_file = Path("test-config.yaml")
            config_file.write_text("aws:\n  region: us-east-1\n")

            result = runner.invoke(cli, ["--config", str(config_file)])

            assert result.exit_code == 0
            mock_file_config.assert_called_once_with(config_file)
            mock_env_config.assert_not_called()  # File config takes precedence
            mock_validate.assert_called_once()

    @patch("main.load_config_from_env")
    @patch("main.validate_cluster")
    def test_cli_validation_failure(self, runner, mock_validate, mock_env_config):
        """Test CLI when validation fails."""
        mock_env_config.return_value = MagicMock()
        mock_validate.return_value = False

        result = runner.invoke(cli, ["--env-only"])

        assert result.exit_code == 1  # Should exit with error code
        mock_validate.assert_called_once()

    def test_cli_missing_config(self, runner):
        """Test CLI when no configuration is provided."""
        result = runner.invoke(cli, [])

        # Should fail because no config file exists and no --env-only flag
        assert result.exit_code == 1
        assert "Error" in result.output or "config" in result.output.lower()

    @patch("main.load_config_from_file")
    def test_cli_invalid_config_file(self, runner, mock_file_config):
        """Test CLI with invalid configuration file."""
        mock_file_config.side_effect = FileNotFoundError("Config file not found")

        result = runner.invoke(cli, ["--config", "nonexistent.yaml"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    @patch("main.load_config_from_env")
    @patch("main.validate_cluster")
    def test_cli_verbose_output(self, runner, mock_validate, mock_env_config):
        """Test CLI with verbose output."""
        mock_env_config.return_value = MagicMock()
        mock_validate.return_value = True

        result = runner.invoke(cli, ["--env-only", "--verbose"])

        assert result.exit_code == 0
        # Verbose output should contain more detailed information
        assert len(result.output) > 0


class TestValidationFunction:
    """Test the main validation function."""

    @patch("main.AWSConfig")
    @patch("main.KubernetesConfig")
    @patch("main.ValidationConfig")
    @patch("main.ReportConfig")
    @patch("main.ClusterValidator")
    def test_validate_cluster_success(
        self,
        mock_validator_class,
        mock_report_config,
        mock_validation_config,
        mock_k8s_config,
        mock_aws_config,
    ):
        """Test successful cluster validation."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_validator_instance = MagicMock()
        mock_validator_instance.validate.return_value = True
        mock_validator_class.return_value = mock_validator_instance

        # Test
        result = validate_cluster(mock_settings)

        assert result is True
        mock_validator_class.assert_called_once_with(
            aws_config=mock_aws_config.return_value,
            k8s_config=mock_k8s_config.return_value,
            validation_config=mock_validation_config.return_value,
            report_config=mock_report_config.return_value,
        )
        mock_validator_instance.validate.assert_called_once()

    @patch("main.ClusterValidator")
    def test_validate_cluster_failure(self, mock_validator_class):
        """Test failed cluster validation."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_validator_instance = MagicMock()
        mock_validator_instance.validate.return_value = False
        mock_validator_class.return_value = mock_validator_instance

        # Test
        result = validate_cluster(mock_settings)

        assert result is False
        mock_validator_instance.validate.assert_called_once()

    @patch("main.ClusterValidator")
    def test_validate_cluster_exception(self, mock_validator_class):
        """Test cluster validation with exception."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_validator_instance = MagicMock()
        mock_validator_instance.validate.side_effect = Exception("Validation error")
        mock_validator_class.return_value = mock_validator_instance

        # Test
        result = validate_cluster(mock_settings)

        assert result is False
        mock_validator_instance.validate.assert_called_once()


class TestCLIOptions:
    """Test various CLI options and edge cases."""

    @pytest.fixture
    def runner(self):
        """CLI test runner."""
        return CliRunner()

    @patch("main.load_config_from_env")
    @patch("main.validate_cluster")
    def test_cli_multiple_verbose_flags(self, runner, mock_validate, mock_env_config):
        """Test CLI with multiple verbose flags."""
        mock_env_config.return_value = MagicMock()
        mock_validate.return_value = True

        result = runner.invoke(cli, ["--env-only", "-v", "--verbose"])

        assert result.exit_code == 0
        # Should handle multiple verbose flags gracefully

    @patch("main.load_config_from_file")
    @patch("main.validate_cluster")
    def test_cli_config_file_with_spaces(self, runner, mock_validate, mock_file_config):
        """Test CLI with config file path containing spaces."""
        mock_file_config.return_value = MagicMock()
        mock_validate.return_value = True

        with runner.isolated_filesystem():
            config_file = Path("test config file.yaml")
            config_file.write_text("aws:\n  region: us-east-1\n")

            result = runner.invoke(cli, ["--config", str(config_file)])

            assert result.exit_code == 0
            mock_file_config.assert_called_once_with(config_file)

    def test_cli_invalid_option_combination(self, runner):
        """Test CLI with invalid option combinations."""
        result = runner.invoke(
            cli, ["--config", "file1.yaml", "--config", "file2.yaml"]
        )

        # Click should handle this gracefully or show appropriate error
        assert result.exit_code != 0 or "Usage" in result.output
