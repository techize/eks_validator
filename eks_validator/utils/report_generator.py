"""
Report generator for EKS cluster validation results
"""

import os
from datetime import datetime
from typing import Dict, List, Any
from jinja2 import Environment, FileSystemLoader
from loguru import logger


class ReportGenerator:
    """Generates markdown reports from validation results"""

    def __init__(self, template_dir: str = None):
        self.template_dir = template_dir or os.path.join(
            os.path.dirname(__file__), "..", "templates"
        )
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate_report(
        self, validation_results: Dict[str, Any], env_config, output_file: str = None
    ) -> str:
        """Generate a comprehensive markdown report"""
        try:
            # Prepare report data
            report_data = self._prepare_report_data(validation_results, env_config)

            # Generate report using template
            template = self.jinja_env.get_template("validation_report.md.j2")
            report_content = template.render(**report_data)

            # Save report if output file specified
            if output_file:
                self._save_report(report_content, output_file)

            return report_content

        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return self._generate_fallback_report(validation_results, env_config)

    def _prepare_report_data(
        self, validation_results: Dict[str, Any], env_config
    ) -> Dict[str, Any]:
        """Prepare data for report template"""
        return {
            "cluster_name": env_config.cluster_name,
            "region": env_config.region,
            "environment": env_config.name,
            "timestamp": datetime.now().isoformat(),
            "validation_results": validation_results,
            "summary": self._generate_summary(validation_results),
            "recommendations": self._collect_recommendations(validation_results),
            "status_counts": self._count_statuses(validation_results),
            "critical_issues": self._get_critical_issues(validation_results),
            "warnings": self._get_warnings(validation_results),
            "passed_checks": self._get_passed_checks(validation_results),
            "skipped_checks": self._get_skipped_checks(validation_results),
            "detailed_results": self._organize_results_by_category(validation_results),
            "vpc_id": (
                getattr(env_config.vpc, "vpc_id", "N/A")
                if hasattr(env_config, "vpc")
                else "N/A"
            ),
        }

    def _generate_summary(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall summary of validation results"""
        summary = {
            "total_checks": 0,
            "passed_checks": 0,
            "warning_checks": 0,
            "failed_checks": 0,
            "skipped_checks": 0,
            "overall_status": "UNKNOWN",
        }

        def count_statuses(data):
            if isinstance(data, dict):
                if "check_status" in data:
                    status = data["check_status"]
                    summary["total_checks"] += 1

                    if status == "PASS":
                        summary["passed_checks"] += 1
                    elif status == "WARN":
                        summary["warning_checks"] += 1
                    elif status == "FAIL":
                        summary["failed_checks"] += 1
                    elif status == "SKIP":
                        summary["skipped_checks"] += 1

                for value in data.values():
                    count_statuses(value)
            elif isinstance(data, list):
                for item in data:
                    count_statuses(item)

        count_statuses(validation_results)

        # Determine overall status
        if summary["failed_checks"] > 0:
            summary["overall_status"] = "FAIL"
        elif summary["warning_checks"] > 0:
            summary["overall_status"] = "WARN"
        elif summary["passed_checks"] > 0:
            summary["overall_status"] = "PASS"
        else:
            summary["overall_status"] = "UNKNOWN"

        return summary

    def _collect_recommendations(
        self, validation_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Collect all recommendations from validation results"""
        recommendations = []

        def extract_recommendations(data, category=""):
            if isinstance(data, dict):
                if "recommendations" in data and isinstance(
                    data["recommendations"], list
                ):
                    for rec in data["recommendations"]:
                        rec_copy = rec.copy()
                        rec_copy["category"] = category
                        recommendations.append(rec_copy)

                for key, value in data.items():
                    if key != "recommendations":
                        extract_recommendations(
                            value, key if not category else f"{category}.{key}"
                        )
            elif isinstance(data, list):
                for item in data:
                    extract_recommendations(item, category)

        extract_recommendations(validation_results)

        # Sort by severity
        severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        recommendations.sort(
            key=lambda x: severity_order.get(x.get("severity", "LOW"), 3)
        )

        return recommendations

    def _count_statuses(self, validation_results: Dict[str, Any]) -> Dict[str, int]:
        """Count occurrences of each status type"""
        status_counts = {"PASS": 0, "WARN": 0, "FAIL": 0, "SKIP": 0, "INFO": 0}

        def count_status(data):
            if isinstance(data, dict):
                if "check_status" in data:
                    status = data["check_status"]
                    if status in status_counts:
                        status_counts[status] += 1

                for value in data.values():
                    count_status(value)
            elif isinstance(data, list):
                for item in data:
                    count_status(item)

        count_status(validation_results)
        return status_counts

    def _get_critical_issues(
        self, validation_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get all critical issues (FAIL status)"""
        critical_issues = []

        def extract_critical(data, category=""):
            if isinstance(data, dict):
                if "check_status" in data and data["check_status"] == "FAIL":
                    critical_issues.append({"category": category, "results": data})

                for key, value in data.items():
                    if key != "check_status":
                        extract_critical(
                            value, key if not category else f"{category}.{key}"
                        )
            elif isinstance(data, list):
                for item in data:
                    extract_critical(item, category)

        extract_critical(validation_results)
        return critical_issues

    def _get_warnings(self, validation_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get all warnings (WARN status)"""
        warnings = []

        def extract_warnings(data, category=""):
            if isinstance(data, dict):
                if "check_status" in data and data["check_status"] == "WARN":
                    warnings.append({"category": category, "results": data})

                for key, value in data.items():
                    if key != "check_status":
                        extract_warnings(
                            value, key if not category else f"{category}.{key}"
                        )
            elif isinstance(data, list):
                for item in data:
                    extract_warnings(item, category)

        extract_warnings(validation_results)
        return warnings

    def _get_passed_checks(
        self, validation_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get all passed checks"""
        passed_checks = []

        def extract_passed(data, category=""):
            if isinstance(data, dict):
                if "check_status" in data and data["check_status"] == "PASS":
                    passed_checks.append({"category": category, "results": data})

                for key, value in data.items():
                    if key != "check_status":
                        extract_passed(
                            value, key if not category else f"{category}.{key}"
                        )
            elif isinstance(data, list):
                for item in data:
                    extract_passed(item, category)

        extract_passed(validation_results)
        return passed_checks

    def _get_skipped_checks(
        self, validation_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get all skipped checks"""
        skipped_checks = []

        def extract_skipped(data, category=""):
            if isinstance(data, dict):
                if "check_status" in data and data["check_status"] == "SKIP":
                    skipped_checks.append({"category": category, "results": data})

                for key, value in data.items():
                    if key != "check_status":
                        extract_skipped(
                            value, key if not category else f"{category}.{key}"
                        )
            elif isinstance(data, list):
                for item in data:
                    extract_skipped(item, category)

        extract_skipped(validation_results)
        return skipped_checks

    def _organize_results_by_category(
        self, validation_results: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Organize validation results by category"""
        categories = {
            "infrastructure": [],
            "networking": [],
            "storage": [],
            "addons": [],
            "monitoring": [],
            "applications": [],
        }

        def categorize_results(data, current_path=""):
            if isinstance(data, dict):
                if "check_status" in data:
                    # Determine category based on path or content
                    category = "infrastructure"  # default

                    path_lower = current_path.lower()
                    if any(
                        keyword in path_lower
                        for keyword in ["network", "vpc", "subnet", "security", "load"]
                    ):
                        category = "networking"
                    elif any(
                        keyword in path_lower
                        for keyword in ["storage", "ebs", "efs", "volume"]
                    ):
                        category = "storage"
                    elif any(
                        keyword in path_lower for keyword in ["addon", "cni", "csi"]
                    ):
                        category = "addons"
                    elif any(
                        keyword in path_lower
                        for keyword in ["monitor", "log", "cloudwatch", "metric"]
                    ):
                        category = "monitoring"
                    elif any(
                        keyword in path_lower
                        for keyword in ["app", "deployment", "pod", "service"]
                    ):
                        category = "applications"

                    if category in categories:
                        categories[category].append(
                            {"path": current_path, "results": data}
                        )

                for key, value in data.items():
                    if key != "check_status":
                        new_path = f"{current_path}.{key}" if current_path else key
                        categorize_results(value, new_path)
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    new_path = f"{current_path}[{i}]" if current_path else f"[{i}]"
                    categorize_results(item, new_path)

        categorize_results(validation_results)
        return categories

    def _save_report(self, content: str, output_file: str):
        """Save report to file"""
        try:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Report saved to: {output_file}")

        except Exception as e:
            logger.error(f"Failed to save report to {output_file}: {e}")

    def _generate_fallback_report(
        self, validation_results: Dict[str, Any], env_config
    ) -> str:
        """Generate a basic fallback report if template fails"""
        timestamp = datetime.now().isoformat()

        report = f"""# EKS Cluster Validation Report

**Cluster:** {env_config.cluster_name}
**Region:** {env_config.region}
**Environment:** {env_config.name}
**Generated:** {timestamp}

## Summary

This is a fallback report generated due to template issues.

## Raw Results

```json
{validation_results}
```

## Recommendations

- Review the raw validation results above
- Check for any FAIL or WARN status items
- Address critical issues first

---
*Report generated by EKS Cluster Validator*
"""

        return report

    def generate_quick_report(
        self, validation_results: Dict[str, Any], env_config
    ) -> str:
        """Generate a quick summary report"""
        summary = self._generate_summary(validation_results)
        recommendations = self._collect_recommendations(validation_results)

        report = f"""# Quick EKS Validation Report

**Cluster:** {env_config.cluster_name} | **Status:** {summary['overall_status']}

## Summary
- Total Checks: {summary['total_checks']}
- ✅ Passed: {summary['passed_checks']}
- ⚠️  Warnings: {summary['warning_checks']}
- ❌ Failed: {summary['failed_checks']}
- ⏭️  Skipped: {summary['skipped_checks']}

## Top Recommendations
"""

        # Add top 5 recommendations
        for i, rec in enumerate(recommendations[:5]):
            severity_icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(
                rec.get("severity"), "⚪"
            )
            report += (
                str(i + 1)
                + ". "
                + severity_icon
                + " "
                + rec.get("message", "Unknown recommendation")
                + "\n"
            )

        if len(recommendations) > 5:
            report += f"\n... and {len(recommendations) - 5} more recommendations\n"

        report += f"\n---\n*Generated: {datetime.now().isoformat()}*"

        return report

    def generate_detailed_report(
        self, validation_results: Dict[str, Any], env_config, output_file: str = None
    ) -> str:
        """Generate a detailed report with all findings"""
        try:
            # Use the main template for detailed report
            return self.generate_report(validation_results, env_config, output_file)

        except Exception as e:
            logger.error(f"Failed to generate detailed report: {e}")
            return self._generate_fallback_report(validation_results, env_config)

    def export_json_report(
        self, validation_results: Dict[str, Any], env_config, output_file: str
    ):
        """Export validation results as JSON"""
        try:
            import json

            report_data = {
                "metadata": {
                    "cluster_name": env_config.cluster_name,
                    "region": env_config.region,
                    "environment": env_config.name,
                    "generated_at": datetime.now().isoformat(),
                    "tool_version": "1.0.0",
                },
                "validation_results": validation_results,
                "summary": self._generate_summary(validation_results),
                "recommendations": self._collect_recommendations(validation_results),
            }

            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, default=str)

            logger.info(f"JSON report exported to: {output_file}")

        except Exception as e:
            logger.error(f"Failed to export JSON report: {e}")

    def generate_html_report(
        self, validation_results: Dict[str, Any], env_config, output_file: str = None
    ) -> str:
        """Generate HTML report (placeholder for future implementation)"""
        # For now, return markdown wrapped in basic HTML
        markdown_content = self.generate_report(validation_results, env_config)

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>EKS Cluster Validation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ background: #e8f4f8; padding: 15px; margin: 20px 0; }}
        .recommendations {{ background: #fff3cd; padding: 15px; margin: 20px 0; }}
        pre {{ background: #f8f8f8; padding: 10px; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>EKS Cluster Validation Report</h1>
        <p><strong>Cluster:</strong> {env_config.cluster_name}</p>
        <p><strong>Region:</strong> {env_config.region}</p>
        <p><strong>Environment:</strong> {env_config.name}</p>
    </div>

    <div class="summary">
        <h2>Summary</h2>
        <pre>{self._generate_summary(validation_results)}</pre>
    </div>

    <div class="recommendations">
        <h2>Recommendations</h2>
        <pre>{self._collect_recommendations(validation_results)}</pre>
    </div>

    <h2>Detailed Results</h2>
    <pre>{markdown_content}</pre>
</body>
</html>"""

        if output_file:
            self._save_report(html_content, output_file)

        return html_content
