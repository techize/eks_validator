#!/usr/bin/env python3
"""
Basic test script to validate EKS Cluster Validator functionality
"""
# noqa: F401

import sys
import os
import tempfile
import yaml
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")

    try:
        from eks_validator.config.settings import Settings  # noqa: F401

        print("✓ Settings import successful")
    except ImportError as e:
        print(f"✗ Settings import failed: {e}")
        return False

    try:
        from eks_validator.core.validator import EKSValidator  # noqa: F401

        print("✓ EKSValidator import successful")
    except ImportError as e:
        print(f"✗ EKSValidator import failed: {e}")
        return False

    try:
        from eks_validator.checkers.infrastructure_checker import (  # noqa
            InfrastructureChecker,
        )

        print("✓ InfrastructureChecker import successful")
    except ImportError as e:
        print(f"✗ InfrastructureChecker import failed: {e}")
        return False

    try:
        from eks_validator.checkers.networking_checker import NetworkingChecker  # noqa

        print("✓ NetworkingChecker import successful")
    except ImportError as e:
        print(f"✗ NetworkingChecker import failed: {e}")
        return False

    try:
        from eks_validator.checkers.storage_checker import StorageChecker  # noqa: F401

        print("✓ StorageChecker import successful")
    except ImportError as e:
        print(f"✗ StorageChecker import failed: {e}")
        return False

    try:
        from eks_validator.checkers.addon_checker import AddonChecker  # noqa: F401

        print("✓ AddonChecker import successful")
    except ImportError as e:
        print(f"✗ AddonChecker import failed: {e}")
        return False

    try:
        from eks_validator.checkers.monitoring_checker import MonitoringChecker  # noqa

        print("✓ MonitoringChecker import successful")
    except ImportError as e:
        print(f"✗ MonitoringChecker import failed: {e}")
        return False

    try:
        from eks_validator.checkers.application_checker import (  # noqa
            ApplicationChecker,
        )

        print("✓ ApplicationChecker import successful")
    except ImportError as e:
        print(f"✗ ApplicationChecker import failed: {e}")
        return False

    try:
        from eks_validator.utils.report_generator import ReportGenerator  # noqa: F401

        print("✓ ReportGenerator import successful")
    except ImportError as e:
        print(f"✗ ReportGenerator import failed: {e}")
        return False

    return True


def test_configuration():
    """Test configuration loading"""
    print("\nTesting configuration...")

    # Create a temporary config file
    config_data = {
        "environments": {
            "test": {
                "cluster_name": "test-cluster",
                "region": "us-east-1",
                "environment": "test",
            }
        },
        "aws": {"profile": "default", "region": "us-east-1"},
        "kubernetes": {"kubeconfig": "~/.kube/config"},
        "validation": {"parallel_checks": True, "timeout_seconds": 300},
        "report": {"output_format": "markdown", "include_recommendations": True},
        "logging": {"level": "INFO", "file": "logs/validator.log"},
    }

    try:
        from eks_validator.config.settings import Settings

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name

        settings = Settings(config_file=config_file)  # noqa: F841
        print("✓ Configuration loading successful")

        # Clean up
        os.unlink(config_file)
        return True

    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        return False


def test_cli_help():
    """Test CLI help command"""
    print("\nTesting CLI...")

    try:
        import subprocess

        result = subprocess.run(
            [sys.executable, "main.py", "--help"],
            capture_output=True,
            text=True,
            cwd=project_root,
        )

        if result.returncode == 0 and "Usage:" in result.stdout:
            print("✓ CLI help command successful")
            return True
        else:
            print(f"✗ CLI help command failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"✗ CLI test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("EKS Cluster Validator - Basic Test Suite")
    print("=" * 50)

    tests = [test_imports, test_configuration, test_cli_help]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The application is ready for use.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Configure AWS credentials")
        print("3. Update config.yaml with your cluster details")
        print("4. Run: python main.py validate <environment>")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Make sure all dependencies are installed")
        print("2. Check Python version (requires 3.8+)")
        print("3. Verify file permissions")
        return 1


if __name__ == "__main__":
    sys.exit(main())
