"""
Pytest configuration and fixtures for EKS Cluster Validator tests.
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Test markers
pytestmark = [
    pytest.mark.filterwarnings("ignore::DeprecationWarning"),
    pytest.mark.filterwarnings("ignore::PendingDeprecationWarning"),
]


@pytest.fixture(scope="session")
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_aws_credentials():
    """Mock AWS credentials for tests."""
    with patch.dict(
        os.environ,
        {
            "AWS_ACCESS_KEY_ID": "testing",
            "AWS_SECRET_ACCESS_KEY": "testing",
            "AWS_SECURITY_TOKEN": "testing",
            "AWS_SESSION_TOKEN": "testing",
            "AWS_DEFAULT_REGION": "us-east-1",
        },
    ):
        yield


@pytest.fixture
def mock_kubernetes_config(temp_dir):
    """Create a mock Kubernetes config file."""
    kubeconfig_path = temp_dir / "kubeconfig"
    kubeconfig_content = """
apiVersion: v1
clusters:
- cluster:
    server: https://test-cluster.example.com
  name: test-cluster
contexts:
- context:
    cluster: test-cluster
    user: test-user
  name: test-context
current-context: test-context
kind: Config
preferences: {}
users:
- name: test-user
  user:
    token: test-token
"""
    kubeconfig_path.write_text(kubeconfig_content)
    with patch.dict(os.environ, {"KUBECONFIG": str(kubeconfig_path)}):
        yield kubeconfig_path


@pytest.fixture
def sample_config_yaml(temp_dir):
    """Create a sample configuration YAML file."""
    config_path = temp_dir / "config.yaml"
    config_content = """
aws:
  region: us-east-1
  profile: default

kubernetes:
  config_file: ~/.kube/config
  context: test-cluster

validation:
  checks:
    - cluster-health
    - node-status
  severity_threshold: warning

reporting:
  format: console
  output_file: test-report.txt
"""
    config_path.write_text(config_content)
    return config_path


@pytest.fixture
def mock_boto3_client():
    """Mock boto3 client for AWS services."""
    with patch("boto3.client") as mock_client:
        # Configure mock EKS client
        mock_eks = MagicMock()
        mock_eks.describe_cluster.return_value = {
            "cluster": {
                "name": "test-cluster",
                "status": "ACTIVE",
                "version": "1.24",
                "endpoint": "https://test-cluster.example.com",
                "roleArn": "arn:aws:iam::123456789012:role/eks-service-role",
            }
        }

        # Configure mock EC2 client
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-1234567890abcdef0",
                            "State": {"Name": "running"},
                            "InstanceType": "t3.medium",
                        }
                    ]
                }
            ]
        }

        # Return appropriate client based on service name
        def get_client(service_name, **kwargs):
            if service_name == "eks":
                return mock_eks
            elif service_name == "ec2":
                return mock_ec2
            else:
                return MagicMock()

        mock_client.side_effect = get_client
        yield mock_client


@pytest.fixture
def mock_kubernetes_client():
    """Mock Kubernetes client."""
    with patch("kubernetes.config.load_kube_config"), patch(
        "kubernetes.client.CoreV1Api"
    ) as mock_core_v1, patch("kubernetes.client.AppsV1Api") as mock_apps_v1:

        # Mock pod listing
        mock_pods = MagicMock()
        mock_pods.items = [
            MagicMock(status=MagicMock(phase="Running")),
            MagicMock(status=MagicMock(phase="Pending")),
        ]
        mock_core_v1.return_value.list_namespaced_pod.return_value = mock_pods

        # Mock node listing
        mock_nodes = MagicMock()
        mock_nodes.items = [
            MagicMock(
                status=MagicMock(conditions=[MagicMock(type="Ready", status="True")])
            )
        ]
        mock_core_v1.return_value.list_node.return_value = mock_nodes

        yield {
            "core_v1": mock_core_v1.return_value,
            "apps_v1": mock_apps_v1.return_value,
        }


# Test configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "aws: marks tests requiring AWS credentials")


# Test collection modifications
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Mark AWS-related tests
        if "aws" in item.nodeid or "boto3" in item.nodeid:
            item.add_marker(pytest.mark.aws)

        # Mark slow tests
        if "slow" in item.keywords or "performance" in item.keywords:
            item.add_marker(pytest.mark.slow)
