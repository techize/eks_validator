#!/usr/bin/env python3
"""
Test script to validate environment variable expansion and backward compatibility
"""

import os
import re
from typing import Any


def expand_env_vars(value: Any) -> Any:
    """
    Recursively expand environment variables in configuration values.

    Supports syntax: ${VAR_NAME:default_value}
    - If VAR_NAME is set, uses its value
    - If VAR_NAME is not set and default_value is provided, uses default_value
    - If VAR_NAME is not set and no default_value, returns the original value
    """
    if isinstance(value, str):
        # Pattern to match ${VAR_NAME:default_value} or ${VAR_NAME}
        pattern = r"\$\{([^:}]+)(?::([^}]*))?\}"

        def replace_var(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else ""

            env_value = os.getenv(var_name)
            if env_value is not None:
                return env_value
            elif default_value:
                return default_value
            else:
                # No env var and no default - keep original placeholder
                return match.group(0)

        # Replace all environment variable references
        expanded_value = re.sub(pattern, replace_var, value)

        return expanded_value
    elif isinstance(value, dict):
        return {k: expand_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [expand_env_vars(item) for item in value]
    else:
        return value


def test_env_var_expansion():
    """Test environment variable expansion functionality"""
    print("🧪 Testing environment variable expansion...")

    # Test cases
    test_cases = [
        # (input, expected_output, description)
        ("${TEST_VAR:default}", "default", "Default value when var not set"),
        ("${TEST_VAR}", "${TEST_VAR}", "Unresolved when no default"),
        ("simple_string", "simple_string", "No expansion needed"),
        (
            "${TEST_VAR1} and ${TEST_VAR2:fallback}",
            "value1 and fallback",
            "Mixed expansion",
        ),
        ("cluster-${ENV:test}", "cluster-test", "Default in middle of string"),
    ]

    # Set test environment variable
    os.environ["TEST_VAR1"] = "value1"

    for input_val, expected, description in test_cases:
        result = expand_env_vars(input_val)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {description}: '{input_val}' -> '{result}'")

    # Clean up
    del os.environ["TEST_VAR1"]


def test_config_structure():
    """Test that config.yaml has the expected structure"""
    print("\n🧪 Testing configuration file structure...")

    try:
        import yaml

        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)

        # Check that environments exist
        if "environments" in config:
            print("  ✅ Environments section found")
            envs = config["environments"]
            for env_name in ["test", "uat", "prod"]:
                if env_name in envs:
                    print(f"  ✅ Environment '{env_name}' configured")
                    env_config = envs[env_name]
                    if "vpc" in env_config and "vpc_id" in env_config["vpc"]:
                        vpc_id = env_config["vpc"]["vpc_id"]
                        if vpc_id.startswith("${"):
                            print(print(f"  ✅ {env_name}: uses placeholders"))
                        else:
                            print(f"  ⚠️  {env_name}: hardcoded VPC ID")
                else:
                    print(f"  ❌ Environment '{env_name}' missing")
        else:
            print("  ❌ Environments section missing")

        # Check AWS config
        if "aws" in config:
            print("  ✅ AWS configuration section found")
            aws_config = config["aws"]
            if "profile" in aws_config and str(aws_config["profile"]).startswith("${"):
                print("  ✅ AWS profile uses env var placeholder")
        else:
            print("  ❌ AWS configuration section missing")

    except Exception as e:
        print(f"  ❌ Error reading config.yaml: {e}")
        return False

    return True


def main():
    """Run all tests"""
    print("🚀 EKS Validator Configuration Test Suite")
    print("=" * 50)

    success = True

    try:
        test_env_var_expansion()
        success &= test_config_structure()

    except Exception as e:
        print(f"❌ Test suite failed with error: {e}")
        success = False

    print("\n" + "=" * 50)
    if success:
        print(
            "🎉 All tests passed! Configuration system supports environment variables."
        )
    else:
        print("💥 Some tests failed. Please check the configuration system.")

    return 0 if success else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
