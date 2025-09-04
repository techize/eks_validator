"""
Monitoring validation checker for EKS clusters
"""

import boto3
from typing import Dict, Any
from loguru import logger


class MonitoringChecker:
    """Checks monitoring stack and observability components"""

    def __init__(
        self,
        eks_client: boto3.client,
        cloudwatch_client: boto3.client,
        env_config,
        k8s_client=None,
    ):
        self.eks_client = eks_client
        self.cloudwatch_client = cloudwatch_client
        self.env_config = env_config
        self.k8s_client = k8s_client
        self.logger = logger

    def check_all(self) -> Dict[str, Any]:
        """Run all monitoring checks"""
        results = {
            "cloudwatch_logs": self.check_cloudwatch_logs(),
            "cloudwatch_metrics": self.check_cloudwatch_metrics(),
            "cloudtrail": self.check_cloudtrail(),
            "prometheus": self.check_prometheus_stack(),
            "fluent_bit": self.check_fluent_bit(),
            "container_insights": self.check_container_insights(),
            "loki": self.check_loki_logging(),
        }

        # Determine overall monitoring status
        # Accept either CloudWatch OR Loki as valid logging solutions
        cloudwatch_logs_result = results.get("cloudwatch_logs", {})
        loki_result = results.get("loki", {})

        cloudwatch_logs_status = (
            cloudwatch_logs_result.get("check_status", "UNKNOWN")
            if isinstance(cloudwatch_logs_result, dict)
            else "UNKNOWN"
        )
        loki_status = (
            loki_result.get("check_status", "UNKNOWN")
            if isinstance(loki_result, dict)
            else "UNKNOWN"
        )

        # Logging is acceptable if either CloudWatch OR Loki is working
        logging_acceptable = cloudwatch_logs_status == "PASS" or loki_status == "PASS"

        # Count other monitoring components
        other_components = [
            "cloudwatch_metrics",
            "cloudtrail",
            "prometheus",
            "fluent_bit",
            "container_insights",
        ]
        other_statuses = []
        for comp in other_components:
            comp_result = results.get(comp, {})
            if isinstance(comp_result, dict):
                status = comp_result.get("check_status", "UNKNOWN")
            else:
                status = "UNKNOWN"
            other_statuses.append(status)

        # Overall monitoring status logic:
        # - FAIL if logging is not acceptable (neither CloudWatch nor Loki working)
        # - FAIL if any other critical component fails
        # - WARN if some non-critical components have issues but logging is working
        # - PASS if logging is working and no critical failures

        critical_failures = sum(1 for status in other_statuses if status == "FAIL")
        warnings = sum(
            1
            for status in [cloudwatch_logs_status, loki_status] + other_statuses
            if status == "WARN"
        )

        if not logging_acceptable:
            overall_status = "FAIL"
            overall_message = (
                "No valid logging solution found (neither CloudWatch "
                "nor Loki is properly configured)"
            )
        elif critical_failures > 0:
            overall_status = "FAIL"
            overall_message = (
                f"Critical monitoring components failed ({critical_failures} failures)"
            )
        elif warnings > 0:
            overall_status = "WARN"
            overall_message = (
                f"Monitoring operational but with warnings ({warnings} issues)"
            )
        else:
            overall_status = "PASS"
            overall_message = "All monitoring components are properly configured"

        # Add overall status to results
        results["overall_status"] = overall_status
        results["overall_message"] = overall_message

        return results

    def check_loki_logging(self) -> Dict[str, Any]:
        """Check if Loki logging stack is properly deployed and running"""
        try:
            # First check if Kubernetes client is available
            if not self.k8s_client:
                self.logger.warning(
                    "Kubernetes client not available - cannot check "
                    "Loki components directly"
                )
                return {
                    "check_status": "WARN",
                    "message": (
                        "Cannot verify Loki logging due to SSL/"
                        "Kubernetes client issues. Manual verification "
                        "recommended."
                    ),
                    "error": "Kubernetes client unavailable",
                    "recommendation": (
                        "Check manually with: kubectl get deployments "
                        "-n logging | grep loki"
                    ),
                }

            # Check for Loki components in the logging namespace
            loki_components = {
                "loki-backend": {"found": False, "replicas": 0},
                "loki-gateway": {"found": False, "replicas": 0},
                "loki-read": {"found": False, "replicas": 0},
                "loki-write": {"found": False, "replicas": 0},
                "promtail": {"found": False, "replicas": 0},
            }

            # Check deployments in logging namespace
            deployment_check_failed = False
            try:
                from kubernetes.client import AppsV1Api

                apps_v1 = AppsV1Api()
                deployments = apps_v1.list_namespaced_deployment("logging")
                for deployment in deployments.items:
                    name = deployment.metadata.name
                    replicas = deployment.spec.replicas or 0

                    if "loki-backend" in name:
                        loki_components["loki-backend"]["found"] = True
                        loki_components["loki-backend"]["replicas"] = replicas
                    elif "loki-gateway" in name:
                        loki_components["loki-gateway"]["found"] = True
                        loki_components["loki-gateway"]["replicas"] = replicas
                    elif "loki-read" in name:
                        loki_components["loki-read"]["found"] = True
                        loki_components["loki-read"]["replicas"] = replicas
                    elif "loki-write" in name:
                        loki_components["loki-write"]["found"] = True
                        loki_components["loki-write"]["replicas"] = replicas
                    elif "promtail" in name:
                        loki_components["promtail"]["found"] = True
                        loki_components["promtail"]["replicas"] = replicas
            except Exception as e:
                self.logger.warning(
                    f"Could not check Loki deployments via Kubernetes API: {e}"
                )
                deployment_check_failed = True

            # Check services in logging namespace
            services_found = []
            service_check_failed = False
            try:
                services = self.k8s_client.list_namespaced_service("logging")
                for service in services.items:
                    name = service.metadata.name
                    if any(component in name for component in ["loki", "promtail"]):
                        services_found.append(name)
            except Exception as e:
                self.logger.warning(
                    f"Could not check Loki services via " f"Kubernetes API: {e}"
                )
                service_check_failed = True

            # If both checks failed, provide helpful guidance
            if deployment_check_failed and service_check_failed:
                return {
                    "check_status": "WARN",
                    "message": (
                        "Cannot verify Loki logging due to API "
                        "connectivity issues. Manual verification "
                        "recommended."
                    ),
                    "error": "Both deployment and service checks failed",
                    "recommendation": (
                        "Check manually with: kubectl get "
                        "deployments,services -n logging | grep -E "
                        '"(loki|promtail)"'
                    ),
                    "troubleshooting": (
                        "SSL certificate issues may be preventing "
                        "Kubernetes API access"
                    ),
                }

            # Determine overall status based on what we could check
            core_components_found = all(
                [
                    loki_components["loki-backend"]["found"],
                    loki_components["loki-gateway"]["found"],
                    loki_components["loki-read"]["found"],
                    loki_components["loki-write"]["found"],
                ]
            )

            promtail_found = loki_components["promtail"]["found"]
            services_present = len(services_found) > 0

            result = {
                "components": loki_components,
                "services": services_found,
                "core_components_found": core_components_found,
                "promtail_found": promtail_found,
                "services_present": services_present,
                "deployment_check_failed": deployment_check_failed,
                "service_check_failed": service_check_failed,
            }

            if core_components_found and promtail_found and services_present:
                result["check_status"] = "PASS"
                result["message"] = (
                    "Loki logging stack is properly deployed and running"
                )
            elif core_components_found and services_present:
                result["check_status"] = "WARN"
                result["message"] = (
                    "Loki core components found but Promtail collectors missing"
                )
            elif core_components_found:
                result["check_status"] = "WARN"
                result["message"] = (
                    "Loki core components found but services " "may be missing"
                )
            elif deployment_check_failed and service_check_failed:
                result["check_status"] = "WARN"
                result["message"] = (
                    "Cannot verify Loki logging due to connectivity issues"
                )
            else:
                result["check_status"] = "FAIL"
                result["message"] = "Loki logging stack not found or incomplete"

            return result

        except Exception as e:
            self.logger.error(f"Failed to check Loki logging: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check Loki logging: {e}",
                "error": str(e),
                "recommendation": (
                    "Check manually with kubectl commands in " "logging namespace"
                ),
            }

    def check_cloudwatch_logs(self) -> Dict[str, Any]:
        """Check CloudWatch Logs configuration"""
        try:
            # Check if CloudWatch logging is enabled for the cluster
            response = self.eks_client.describe_cluster(
                name=self.env_config.cluster_name
            )

            cluster = response["cluster"]
            logging_config = cluster.get("logging", {})

            if not logging_config:
                return {
                    "check_status": "FAIL",
                    "message": "CloudWatch logging not configured for cluster",
                    "enabled": False,
                }

            enabled_types = []
            disabled_types = []

            for log_config in logging_config.get("clusterLogging", []):
                log_type = log_config.get("types", [])
                enabled = log_config.get("enabled", False)

                if enabled:
                    enabled_types.extend(log_type)
                else:
                    disabled_types.extend(log_type)

            result = {
                "enabled": bool(enabled_types),
                "enabled_types": enabled_types,
                "disabled_types": disabled_types,
                "log_group_prefix": f"/aws/eks/{self.env_config.cluster_name}/cluster",
            }

            if enabled_types:
                result["check_status"] = "PASS"
                result["message"] = f"CloudWatch logging enabled for: {enabled_types}"
            else:
                result["check_status"] = "FAIL"
                result["message"] = "No CloudWatch logging types enabled"

            return result

        except Exception as e:
            logger.error(f"Failed to check CloudWatch logs: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check CloudWatch logs: {e}",
                "error": str(e),
            }

    def check_cloudwatch_metrics(self) -> Dict[str, Any]:
        """Check CloudWatch metrics for the cluster"""
        try:
            # Check for EKS-specific metrics
            metrics_to_check = [
                f"cluster/{self.env_config.cluster_name}/node_cpu_utilization",
                f"cluster/{self.env_config.cluster_name}/node_memory_utilization",
                f"cluster/{self.env_config.cluster_name}/pod_cpu_utilization",
                f"cluster/{self.env_config.cluster_name}/pod_memory_utilization",
            ]

            found_metrics = []
            missing_metrics = []

            for metric_name in metrics_to_check:
                try:
                    response = self.cloudwatch_client.list_metrics(
                        Namespace="AWS/EKS",
                        MetricName=metric_name.split("/")[-1],
                        Dimensions=[
                            {
                                "Name": "ClusterName",
                                "Value": self.env_config.cluster_name,
                            }
                        ],
                    )

                    if response.get("Metrics"):
                        found_metrics.append(metric_name)
                    else:
                        missing_metrics.append(metric_name)

                except Exception as e:
                    logger.warning(f"Failed to check metric {metric_name}: {e}")
                    missing_metrics.append(metric_name)

            result = {
                "found_metrics": found_metrics,
                "missing_metrics": missing_metrics,
                "total_metrics": len(metrics_to_check),
                "found_count": len(found_metrics),
                "missing_count": len(missing_metrics),
            }

            if found_metrics:
                result["check_status"] = "PASS"
                result["message"] = (
                    f"Found {len(found_metrics)}/"
                    f"{len(metrics_to_check)} CloudWatch metrics"
                )
            else:
                result["check_status"] = "WARN"
                result["message"] = "No CloudWatch metrics found for cluster"

            return result

        except Exception as e:
            logger.error(f"Failed to check CloudWatch metrics: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check CloudWatch metrics: {e}",
                "error": str(e),
            }

    def check_cloudtrail(self) -> Dict[str, Any]:
        """Check CloudTrail configuration for the cluster"""
        try:
            cloudtrail_client = boto3.client(
                "cloudtrail", region_name=self.env_config.region
            )

            # List trails
            trails_response = cloudtrail_client.list_trails()

            if not trails_response.get("Trails"):
                return {
                    "check_status": "FAIL",
                    "message": "No CloudTrail trails found",
                    "trails": [],
                }

            active_trails = []
            for trail in trails_response["Trails"]:
                trail_name = trail["TrailARN"].split("/")[-1]

                # Get trail status
                status_response = cloudtrail_client.get_trail_status(Name=trail_name)

                if status_response.get("IsLogging", False):
                    active_trails.append(
                        {
                            "name": trail_name,
                            "arn": trail["TrailARN"],
                            "is_logging": True,
                            "is_multi_region": trail.get("IsMultiRegionTrail", False),
                        }
                    )

            result = {
                "active_trails": active_trails,
                "total_trails": len(trails_response["Trails"]),
                "active_count": len(active_trails),
            }

            if active_trails:
                result["check_status"] = "PASS"
                result["message"] = (
                    f"Found {len(active_trails)} active CloudTrail trails"
                )
            else:
                result["check_status"] = "FAIL"
                result["message"] = "No active CloudTrail trails found"

            return result

        except Exception as e:
            logger.error(f"Failed to check CloudTrail: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check CloudTrail: {e}",
                "error": str(e),
            }

    def check_prometheus_stack(self) -> Dict[str, Any]:
        """Check if Prometheus monitoring stack is deployed"""
        if not self.k8s_client:
            return {
                "check_status": "SKIP",
                "message": "Kubernetes client not available for Prometheus check",
            }

        try:
            # Check for Prometheus deployment
            prometheus_deployments = [
                "prometheus-server",
                "prometheus-kube-state-metrics",
                "prometheus-node-exporter",
            ]

            found_components = []
            missing_components = []

            for deployment in prometheus_deployments:
                try:
                    from kubernetes.client import AppsV1Api

                    apps_v1 = AppsV1Api()
                    response = apps_v1.read_namespaced_deployment(
                        name=deployment, namespace="monitoring"
                    )

                    if response:
                        found_components.append(
                            {
                                "name": deployment,
                                "namespace": "monitoring",
                                "replicas": response.spec.replicas,
                                "ready_replicas": response.status.ready_replicas,
                            }
                        )

                except Exception:
                    # Try default namespace
                    try:
                        from kubernetes.client import AppsV1Api

                        apps_v1 = AppsV1Api()
                        response = apps_v1.read_namespaced_deployment(
                            name=deployment, namespace="default"
                        )

                        if response:
                            found_components.append(
                                {
                                    "name": deployment,
                                    "namespace": "default",
                                    "replicas": response.spec.replicas,
                                    "ready_replicas": response.status.ready_replicas,
                                }
                            )
                    except Exception as e:
                        if hasattr(e, "status") and e.status == 404:
                            self.logger.warning(
                                f"Deployment {deployment} not found in "
                                "default namespace"
                            )
                        else:
                            self.logger.error(
                                f"Error checking deployment {deployment} in "
                                f"default namespace: {e}"
                            )
                        missing_components.append(deployment)

            result = {
                "found_components": found_components,
                "missing_components": missing_components,
                "total_components": len(prometheus_deployments),
                "found_count": len(found_components),
                "missing_count": len(missing_components),
            }

            if found_components:
                result["check_status"] = "PASS"
                result["message"] = (
                    f"Found {len(found_components)}/"
                    f"{len(prometheus_deployments)} Prometheus components"
                )
            else:
                result["check_status"] = "INFO"
                result["message"] = (
                    "Prometheus stack not detected (may be using "
                    "CloudWatch Container Insights)"
                )

            return result

        except Exception as e:
            self.logger.error(f"Failed to check Prometheus stack: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check Prometheus stack: {e}",
                "error": str(e),
            }

    def check_fluent_bit(self) -> Dict[str, Any]:
        """Check if Fluent Bit is configured for log shipping"""
        if not self.k8s_client:
            return {
                "check_status": "SKIP",
                "message": "Kubernetes client not available for Fluent Bit check",
            }

        try:
            # Check for Fluent Bit daemonset
            try:
                from kubernetes.client import AppsV1Api

                apps_v1 = AppsV1Api()
                response = apps_v1.read_namespaced_daemon_set(
                    name="fluent-bit", namespace="amazon-cloudwatch"
                )

                if response:
                    return {
                        "check_status": "PASS",
                        "message": (
                            "Fluent Bit daemonset found in "
                            "amazon-cloudwatch namespace"
                        ),
                        "namespace": "amazon-cloudwatch",
                        "desired_number_scheduled": (
                            response.status.desired_number_scheduled
                        ),
                        "number_ready": response.status.number_ready,
                    }

            except Exception:
                pass

            # Check other common namespaces
            namespaces_to_check = ["kube-system", "logging", "monitoring"]

            for namespace in namespaces_to_check:
                try:
                    from kubernetes.client import AppsV1Api

                    apps_v1 = AppsV1Api()
                    response = apps_v1.read_namespaced_daemon_set(
                        name="fluent-bit", namespace=namespace
                    )

                    if response:
                        return {
                            "check_status": "PASS",
                            "message": (
                                f"Fluent Bit daemonset found in {namespace} "
                                "namespace"
                            ),
                            "namespace": namespace,
                            "desired_number_scheduled": (
                                response.status.desired_number_scheduled
                            ),
                            "number_ready": response.status.number_ready,
                        }

                except Exception:
                    continue

            return {
                "check_status": "INFO",
                "message": (
                    "Fluent Bit daemonset not found (may be using "
                    "different log shipping solution)"
                ),
            }

        except Exception as e:
            logger.error(f"Failed to check Fluent Bit: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check Fluent Bit: {e}",
                "error": str(e),
            }

    def check_container_insights(self) -> Dict[str, Any]:
        """Check if CloudWatch Container Insights is enabled"""
        try:
            # Check for Container Insights log groups
            log_groups_to_check = [
                f"/aws/containerinsights/{self.env_config.cluster_name}/application",
                f"/aws/containerinsights/{self.env_config.cluster_name}/dataplane",
                f"/aws/containerinsights/{self.env_config.cluster_name}/host",
                f"/aws/containerinsights/{self.env_config.cluster_name}/performance",
            ]

            found_log_groups = []
            missing_log_groups = []

            logs_client = boto3.client("logs", region_name=self.env_config.region)

            for log_group_name in log_groups_to_check:
                try:
                    response = logs_client.describe_log_groups(
                        logGroupNamePrefix=log_group_name
                    )

                    if response.get("logGroups"):
                        found_log_groups.append(log_group_name)
                    else:
                        missing_log_groups.append(log_group_name)

                except Exception as e:
                    logger.warning(f"Failed to check log group {log_group_name}: {e}")
                    missing_log_groups.append(log_group_name)

            result = {
                "found_log_groups": found_log_groups,
                "missing_log_groups": missing_log_groups,
                "total_log_groups": len(log_groups_to_check),
                "found_count": len(found_log_groups),
                "missing_count": len(missing_log_groups),
            }

            if found_log_groups:
                result["check_status"] = "PASS"
                result["message"] = (
                    f"Container Insights enabled "
                    f"({len(found_log_groups)}/"
                    f"{len(log_groups_to_check)} log groups found)"
                )
            else:
                result["check_status"] = "INFO"
                result["message"] = (
                    "Container Insights log groups not found (may not be enabled)"
                )

            return result

        except Exception as e:
            logger.error(f"Failed to check Container Insights: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check Container Insights: {e}",
                "error": str(e),
            }

    def get_monitoring_recommendations(self) -> Dict[str, Any]:
        """Provide recommendations for monitoring setup"""
        try:
            recommendations = []

            # Check CloudWatch logging
            logs_check = self.check_cloudwatch_logs()
            if logs_check.get("check_status") == "FAIL":
                recommendations.append(
                    {
                        "type": "cloudwatch_logging",
                        "message": "Enable CloudWatch logging for the EKS cluster",
                        "severity": "HIGH",
                    }
                )

            # Check Container Insights
            insights_check = self.check_container_insights()
            if insights_check.get("check_status") == "INFO":
                recommendations.append(
                    {
                        "type": "container_insights",
                        "message": (
                            "Consider enabling CloudWatch Container "
                            "Insights for enhanced monitoring"
                        ),
                        "severity": "MEDIUM",
                    }
                )

            # Check CloudTrail
            cloudtrail_check = self.check_cloudtrail()
            if cloudtrail_check.get("check_status") == "FAIL":
                recommendations.append(
                    {
                        "type": "cloudtrail",
                        "message": "Enable CloudTrail for audit logging",
                        "severity": "HIGH",
                    }
                )

            # Check Prometheus
            prometheus_check = self.check_prometheus_stack()
            if prometheus_check.get("check_status") == "INFO":
                recommendations.append(
                    {
                        "type": "prometheus",
                        "message": (
                            "Consider deploying Prometheus stack for "
                            "detailed metrics collection"
                        ),
                        "severity": "MEDIUM",
                    }
                )

            # Check Loki
            loki_check = self.check_loki_logging()
            if loki_check.get("check_status") == "FAIL":
                recommendations.append(
                    {
                        "type": "loki_logging",
                        "message": (
                            "Deploy Loki logging stack for log "
                            "aggregation and monitoring"
                        ),
                        "severity": "HIGH",
                    }
                )

            return {
                "recommendations": recommendations,
                "total_recommendations": len(recommendations),
                "check_status": "PASS" if not recommendations else "WARN",
                "message": f"Found {len(recommendations)} monitoring recommendations",
            }

        except Exception as e:
            logger.error(f"Failed to generate monitoring recommendations: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to generate monitoring recommendations: {e}",
                "error": str(e),
            }
