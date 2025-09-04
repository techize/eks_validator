#!/usr/bin/env python3
"""
Pre-commit hook to validate that no sensitive AWS infrastructure data
is being committed.

This script checks for:
- Real AWS resource IDs (vpc-, subnet-, sg-, arn:aws:)
- Real cluster names (customizable patterns)
- Other sensitive infrastructure patterns

CUSTOMIZATION:
To add your organization's specific cluster naming patterns, modify the
`custom_cluster_patterns` list below or set the CUSTOM_PATTERNS environment variable.

Examples:
- export CUSTOM_PATTERNS="myco-eks-.*,my-cluster-.*"
- Or modify custom_cluster_patterns list directly

Usage: python3 scripts/validate_sensitive_data.py
"""

import os
import re
import sys
from pathlib import Path


class SensitiveDataValidator:
    """Validator for sensitive AWS infrastructure data."""

    def __init__(self):
        # Custom cluster patterns - MODIFY THIS for your organization
        self.custom_cluster_patterns = [
            # Add your organization's specific cluster naming patterns here
            # Examples:
            # r'\bsp-eks-(test|uat|prd|prod|dev|staging)-\d*\b',
            # r'\bmy-company-eks-[a-z0-9-]+\b',
        ]

        # Load custom patterns from environment variable if set
        env_patterns = os.getenv("CUSTOM_PATTERNS")
        if env_patterns:
            self.custom_cluster_patterns.extend(env_patterns.split(","))

        # Standard patterns that indicate sensitive data
        self.sensitive_patterns = [
            # AWS Resource IDs
            r"\bvpc-[0-9a-f]{8,17}\b",  # VPC IDs
            r"\bsubnet-[0-9a-f]{8,17}\b",  # Subnet IDs
            r"\bsg-[0-9a-f]{8,17}\b",  # Security Group IDs
            r"\bi-[0-9a-f]{8,17}\b",  # EC2 Instance IDs
            # Custom cluster patterns (loaded from environment or defaults)
            *self.custom_cluster_patterns,  # Include custom patterns
            # Generic cluster name patterns (customize for your organization)
            # Add your specific cluster naming patterns here
            # Examples:
            # r'\bsp-eks-(test|uat|prd|prod|dev|staging)-\d*\b',
            #     # Organization-specific
            # r'\beks-[a-z0-9-]+-\d{2}\b',  # Generic EKS pattern
            r"\bvol-[0-9a-f]{8,17}\b",  # EBS Volume IDs
            r"\bsnap-[0-9a-f]{8,17}\b",  # EBS Snapshot IDs
            r'\barn:aws:[^"]+',  # AWS ARNs
            r"\b\d{12}\b",  # AWS Account IDs (12 digits)
            # Generic cluster name patterns (customize for your organization)
            # Add your specific cluster naming patterns here
            # Examples:
            # r'\bsp-eks-(test|uat|prd|prod|dev|staging)-\d*\b',
            #     # Organization-specific
            # r'\beks-[a-z0-9-]+-\d{2}\b',  # Generic EKS pattern
            r"\beks-[a-z0-9-]+-\d{2}\b",  # Generic EKS cluster pattern
            # Database and storage
            r"\brds-[a-z0-9-]+\b",  # RDS instance identifiers
            r"\bdb-[a-z0-9-]+\b",  # Database identifiers
            r"\bs3://[a-z0-9][a-z0-9-]*[a-z0-9]\b",  # S3 bucket URLs
            # IP addresses (internal ranges that might be sensitive)
            r"\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",  # Private IP ranges
            r"\b172\.(1[6-9]|2[0-9]|3[0-1])\.\d{1,3}\.\d{1,3}\b",  # Private IP ranges
            r"\b192\.168\.\d{1,3}\.\d{1,3}\b",  # Private IP ranges
        ]

        # Files to exclude from validation
        self.exclude_files = {
            ".gitignore",
            "config.example.yaml",
            "reports/example_validation_report.md",
            "README.md",  # Contains placeholder examples
            "scripts/validate_sensitive_data.py",  # Exclude this validation script
        }

        # Directories to exclude from validation
        self.exclude_dirs = {
            "tests/",  # Test files contain placeholder data
            "examples/",  # Example files contain placeholder data
            "__pycache__/",
            ".git/",
            ".pytest_cache/",
            "node_modules/",
        }

        # File extensions to check
        self.check_extensions = {".yaml", ".yml", ".md", ".py", ".json", ".txt"}

    def should_check_file(self, file_path: Path) -> bool:
        """Determine if a file should be checked for sensitive data."""
        # Skip excluded files (check both filename and full path)
        if file_path.name in self.exclude_files or str(file_path) in self.exclude_files:
            return False

        # Skip files in excluded directories
        if any(
            str(file_path).startswith(excluded_dir)
            or excluded_dir.rstrip("/") in file_path.parts
            for excluded_dir in self.exclude_dirs
        ):
            return False

        # Only check specific file extensions
        return file_path.suffix in self.check_extensions

    def check_file_for_sensitive_data(self, file_path: Path) -> list:
        """Check a single file for sensitive data patterns."""
        violations = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            for pattern in self.sensitive_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    for match in matches:
                        violations.append(
                            {
                                "file": str(file_path),
                                "pattern": pattern,
                                "match": match,
                                "line": self._find_line_number(content, match),
                            }
                        )

        except (IOError, OSError) as e:
            print(f"Warning: Could not read file {file_path}: {e}", file=sys.stderr)

        return violations

    def _find_line_number(self, content: str, match) -> int:
        """Find the line number where a match occurs."""
        # Handle both string and tuple matches (from regex capture groups)
        if isinstance(match, tuple):
            match_str = "".join(str(m) for m in match if m is not None)
        else:
            match_str = str(match)

        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            if match_str in line:
                return i
        return 0

    def validate_staged_files(self) -> list:
        """Validate all staged files for sensitive data."""
        violations = []

        # Get list of staged files
        try:
            import subprocess

            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                cwd=Path.cwd(),
            )

            if result.returncode != 0:
                print(f"Error getting staged files: {result.stderr}", file=sys.stderr)
                return violations

            staged_files = result.stdout.strip().split("\n")
            staged_files = [f for f in staged_files if f]  # Remove empty strings

        except Exception as e:
            print(f"Error running git command: {e}", file=sys.stderr)
            return violations

        # Check each staged file
        for file_path_str in staged_files:
            file_path = Path(file_path_str)

            if self.should_check_file(file_path):
                file_violations = self.check_file_for_sensitive_data(file_path)
                violations.extend(file_violations)

        return violations

    def print_violations(self, violations: list):
        """Print violations in a readable format."""
        if not violations:
            return

        print("\n🚨 SENSITIVE DATA DETECTED IN STAGED FILES 🚨\n")
        print("The following files contain sensitive infrastructure data:")
        print("=" * 60)

        for violation in violations:
            print(f"File: {violation['file']}")
            print(f"Pattern: {violation['pattern']}")
            print(f"Match: {violation['match']}")
            if violation["line"] > 0:
                print(f"Line: {violation['line']}")
            print("-" * 40)

        print("\n❌ COMMIT BLOCKED: Sensitive data detected!")
        print("\nTo resolve this:")
        print("1. Remove sensitive data from the files above")
        print("2. Use placeholder values (e.g., vpc-xxxxxxxxxxxxxxxxx)")
        print("3. Ensure sensitive files are in .gitignore")
        print("4. Try committing again\n")


def main():
    """Main entry point for the pre-commit hook."""
    validator = SensitiveDataValidator()
    violations = validator.validate_staged_files()

    if violations:
        validator.print_violations(violations)
        sys.exit(1)  # Block the commit
    else:
        print("✅ No sensitive data detected in staged files.")
        sys.exit(0)  # Allow the commit


if __name__ == "__main__":
    main()
