"""
Core EKS Validator class that orchestrates all validation checks
"""

import boto3
import time
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor
from loguru import logger
from kubernetes import client, config

from eks_validator.config.settings import Settings
from eks_validator.checkers.infrastructure_checker import InfrastructureChecker
from eks_validator.checkers.networking_checker import NetworkingChecker
from eks_validator.checkers.storage_checker import StorageChecker
from eks_validator.checkers.addon_checker import AddonChecker
from eks_validator.checkers.monitoring_checker import MonitoringChecker
from eks_validator.checkers.application_checker import ApplicationChecker


class EKSValidator:
    """Main validator class that orchestrates all EKS cluster validation checks"""

    def __init__(self, settings: Settings, environment: str):
        self.settings = settings
        self.environment = environment
        self.env_config = settings.get_environment_config(environment)

        # Initialize AWS and Kubernetes clients
        self.aws_session = self._create_aws_session()
        self.eks_client = self.aws_session.client(
            "eks", region_name=self.env_config.region
        )
        self.ec2_client = self.aws_session.client(
            "ec2", region_name=self.env_config.region
        )
        self.elbv2_client = self.aws_session.client(
            "elbv2", region_name=self.env_config.region
        )
        self.rds_client = self.aws_session.client(
            "rds", region_name=self.env_config.region
        )

        # Initialize Kubernetes client
        self.k8s_client = self._create_kubernetes_client()

        # Initialize checkers
        self.infrastructure_checker = InfrastructureChecker(
            self.eks_client, self.ec2_client, self.env_config
        )
        self.networking_checker = NetworkingChecker(
            self.ec2_client, self.elbv2_client, self.env_config
        )
        self.storage_checker = StorageChecker(self.k8s_client, self.env_config)
        self.addon_checker = AddonChecker(self.eks_client, self.env_config)
        self.monitoring_checker = MonitoringChecker(
            self.eks_client,
            self.aws_session.client("cloudwatch", region_name=self.env_config.region),
            self.env_config,
            self.k8s_client,
        )
        self.application_checker = ApplicationChecker(
            self.k8s_client, self.rds_client, self.env_config
        )

        logger.info(f"Initialized EKS Validator for environment: {environment}")

    def _create_aws_session(self) -> boto3.Session:
        """Create AWS session with proper credentials and role assumption"""
        session_kwargs = {"region_name": self.env_config.region}

        # Use environment-specific profile if available, otherwise
        # fall back to global profile
        profile = self.env_config.aws_profile or self.settings.aws.profile
        if profile:
            session_kwargs["profile_name"] = profile

        session = boto3.Session(**session_kwargs)

        # Assume role if specified
        if self.settings.aws.assume_role_arn:
            sts_client = session.client("sts")
            assume_role_kwargs = {
                "RoleArn": self.settings.aws.assume_role_arn,
                "RoleSessionName": (
                    f"eks-validator-{self.environment}-{int(time.time())}"
                ),
                "DurationSeconds": self.settings.aws.session_duration,
            }

            if self.settings.aws.external_id:
                assume_role_kwargs["ExternalId"] = self.settings.aws.external_id

            response = sts_client.assume_role(**assume_role_kwargs)

            session = boto3.Session(
                aws_access_key_id=response["Credentials"]["AccessKeyId"],
                aws_secret_access_key=response["Credentials"]["SecretAccessKey"],
                aws_session_token=response["Credentials"]["SessionToken"],
                region_name=self.env_config.region,
            )

        return session

    def _create_kubernetes_client(self):
        """Create Kubernetes client for cluster access"""
        try:
            # Try to load kubeconfig
            if self.settings.kubernetes.kubeconfig_path:
                config.load_kube_config(
                    config_file=self.settings.kubernetes.kubeconfig_path,
                    context=self.settings.kubernetes.context_name,
                )
            else:
                config.load_kube_config(context=self.settings.kubernetes.context_name)

            return client.CoreV1Api()
        except Exception as e:
            logger.warning(f"Failed to create Kubernetes client: {e}")
            return None

    def quick_cluster_check(self) -> str:
        """Perform a quick cluster health check"""
        try:
            response = self.eks_client.describe_cluster(
                name=self.env_config.cluster_name
            )
            status = response["cluster"]["status"]
            return f"Cluster is {status}"
        except Exception as e:
            logger.error(f"Quick cluster check failed: {e}")
            return f"Failed to check cluster: {e}"

    def quick_node_check(self) -> str:
        """Perform a quick node health check"""
        try:
            if not self.k8s_client:
                return "Kubernetes client not available"

            response = self.k8s_client.list_node()
            total_nodes = len(response.items)
            ready_nodes = sum(
                1
                for node in response.items
                if all(
                    condition.status == "True"
                    for condition in node.status.conditions
                    if condition.type == "Ready"
                )
            )

            return f"{ready_nodes}/{total_nodes} nodes ready"
        except Exception as e:
            logger.error(f"Quick node check failed: {e}")
            return f"Failed to check nodes: {e}"

    def check_infrastructure(self) -> Dict[str, Any]:
        """Check EKS infrastructure components"""
        logger.info("Running infrastructure checks")
        return self.infrastructure_checker.check_all()

    def check_networking(self) -> Dict[str, Any]:
        """Check networking components"""
        logger.info("Running networking checks")
        return self.networking_checker.check_all()

    def check_storage(self) -> Dict[str, Any]:
        """Check storage components"""
        logger.info("Running storage checks")
        return self.storage_checker.check_all()

    def check_addons(self) -> Dict[str, Any]:
        """Check EKS addons"""
        logger.info("Running addon checks")
        return self.addon_checker.check_all()

    def check_monitoring(self) -> Dict[str, Any]:
        """Check monitoring components"""
        logger.info("Running monitoring checks")
        return self.monitoring_checker.check_all()

    def check_applications(self) -> Dict[str, Any]:
        """Check application components"""
        logger.info("Running application checks")
        return self.application_checker.check_all()

    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks"""
        logger.info("Starting comprehensive validation")

        results = {}

        if self.settings.validation.parallel_checks:
            # Run checks in parallel
            with ThreadPoolExecutor(
                max_workers=self.settings.validation.max_parallel_workers
            ) as executor:
                futures = {
                    "infrastructure": executor.submit(self.check_infrastructure),
                    "networking": executor.submit(self.check_networking),
                    "storage": executor.submit(self.check_storage),
                    "addons": executor.submit(self.check_addons),
                    "monitoring": executor.submit(self.check_monitoring),
                    "applications": executor.submit(self.check_applications),
                }

                for check_name, future in futures.items():
                    try:
                        results[check_name] = future.result(
                            timeout=self.settings.validation.timeout
                        )
                    except Exception as e:
                        logger.error(f"{check_name} check failed: {e}")
                        results[check_name] = {"error": str(e)}
        else:
            # Run checks sequentially
            try:
                results["infrastructure"] = self.check_infrastructure()
            except Exception as e:
                logger.error(f"Infrastructure check failed: {e}")
                results["infrastructure"] = {"error": str(e)}

            try:
                results["networking"] = self.check_networking()
            except Exception as e:
                logger.error(f"Networking check failed: {e}")
                results["networking"] = {"error": str(e)}

            try:
                results["storage"] = self.check_storage()
            except Exception as e:
                logger.error(f"Storage check failed: {e}")
                results["storage"] = {"error": str(e)}

            try:
                results["addons"] = self.check_addons()
            except Exception as e:
                logger.error(f"Addon check failed: {e}")
                results["addons"] = {"error": str(e)}

            try:
                results["monitoring"] = self.check_monitoring()
            except Exception as e:
                logger.error(f"Monitoring check failed: {e}")
                results["monitoring"] = {"error": str(e)}

            try:
                results["applications"] = self.check_applications()
            except Exception as e:
                logger.error(f"Application check failed: {e}")
                results["applications"] = {"error": str(e)}

        logger.info("Validation completed")
        return results

    def get_validation_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of validation results"""
        summary = {
            "total_checks": 0,
            "passed_checks": 0,
            "failed_checks": 0,
            "warning_checks": 0,
            "errors": [],
            "categories": {},
        }

        for category, category_results in results.items():
            if "error" in category_results:
                summary["errors"].append(f"{category}: {category_results['error']}")
                continue

            category_summary = {"total": 0, "passed": 0, "failed": 0, "warnings": 0}

            # Count checks in this category
            def count_checks(data):
                if isinstance(data, dict):
                    for key, value in data.items():
                        if key in ["status", "result"]:
                            category_summary["total"] += 1
                            if value == "PASS":
                                category_summary["passed"] += 1
                            elif value == "FAIL":
                                category_summary["failed"] += 1
                            elif value == "WARN":
                                category_summary["warnings"] += 1
                        else:
                            count_checks(value)
                elif isinstance(data, list):
                    for item in data:
                        count_checks(item)

            count_checks(category_results)
            summary["categories"][category] = category_summary

            # Update totals
            summary["total_checks"] += category_summary["total"]
            summary["passed_checks"] += category_summary["passed"]
            summary["failed_checks"] += category_summary["failed"]
            summary["warning_checks"] += category_summary["warnings"]

        return summary
