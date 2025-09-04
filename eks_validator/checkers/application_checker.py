"""
Application validation checker for EKS clusters
"""

import boto3
from typing import Dict, Any
from loguru import logger


class ApplicationChecker:
    """Checks application deployments and database connectivity"""

    def __init__(
        self,
        eks_client: boto3.client,
        rds_client: boto3.client,
        env_config,
        k8s_client=None,
    ):
        self.eks_client = eks_client
        self.rds_client = rds_client
        self.env_config = env_config
        self.k8s_client = k8s_client

        # Extract VPC configuration - support both new nested structure
        # and legacy fields
        self.vpc_config = env_config.vpc if env_config.vpc else {}
        self.vpc_id = self.vpc_config.get("vpc_id") or env_config.vpc_id

    def check_all(self) -> Dict[str, Any]:
        """Run all application checks"""
        return {
            "deployments": self.check_deployments(),
            "services": self.check_services(),
            "ingresses": self.check_ingresses(),
            "database_connectivity": self.check_database_connectivity(),
            "application_health": self.check_application_health(),
        }

    def check_deployments(self) -> Dict[str, Any]:
        """Check Kubernetes deployments status"""
        if not self.k8s_client:
            return {
                "check_status": "SKIP",
                "message": "Kubernetes client not available for deployment check",
            }

        try:
            # Get all deployments across namespaces
            deployments_response = self.k8s_client.list_deployment_for_all_namespaces()

            deployments = []
            healthy_count = 0
            unhealthy_count = 0

            for deployment in deployments_response.items:
                name = deployment.metadata.name
                namespace = deployment.metadata.namespace
                replicas = deployment.spec.replicas or 0
                ready_replicas = deployment.status.ready_replicas or 0
                available_replicas = deployment.status.available_replicas or 0

                deployment_info = {
                    "name": name,
                    "namespace": namespace,
                    "desired_replicas": replicas,
                    "ready_replicas": ready_replicas,
                    "available_replicas": available_replicas,
                    "conditions": [],
                }

                # Check deployment conditions
                if deployment.status.conditions:
                    for condition in deployment.status.conditions:
                        deployment_info["conditions"].append(
                            {
                                "type": condition.type,
                                "status": condition.status,
                                "reason": condition.reason,
                                "message": condition.message,
                            }
                        )

                # Determine health status
                if (
                    replicas > 0
                    and ready_replicas == replicas
                    and available_replicas == replicas
                ):
                    deployment_info["health_status"] = "HEALTHY"
                    healthy_count += 1
                elif ready_replicas < replicas or available_replicas < replicas:
                    deployment_info["health_status"] = "DEGRADED"
                    unhealthy_count += 1
                else:
                    deployment_info["health_status"] = "UNHEALTHY"
                    unhealthy_count += 1

                deployments.append(deployment_info)

            result = {
                "deployments": deployments,
                "total_deployments": len(deployments),
                "healthy_count": healthy_count,
                "unhealthy_count": unhealthy_count,
                "healthy_percentage": (
                    (healthy_count / len(deployments) * 100) if deployments else 0
                ),
            }

            if unhealthy_count == 0:
                result["check_status"] = "PASS"
                result["message"] = f"All {len(deployments)} deployments are healthy"
            elif unhealthy_count < len(deployments) * 0.5:
                result["check_status"] = "WARN"
                result["message"] = (
                    f"{unhealthy_count}/{len(deployments)} " "deployments are unhealthy"
                )
            else:
                result["check_status"] = "FAIL"
                result["message"] = (
                    f"Majority of deployments unhealthy: "
                    f"{unhealthy_count}/{len(deployments)}"
                )

            return result

        except Exception as e:
            logger.error(f"Failed to check deployments: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check deployments: {e}",
                "error": str(e),
            }

    def check_services(self) -> Dict[str, Any]:
        """Check Kubernetes services status"""
        if not self.k8s_client:
            return {
                "check_status": "SKIP",
                "message": "Kubernetes client not available for service check",
            }

        try:
            # Get all services across namespaces
            services_response = self.k8s_client.list_service_for_all_namespaces()

            services = []
            load_balancer_count = 0
            cluster_ip_count = 0
            node_port_count = 0

            for service in services_response.items:
                name = service.metadata.name
                namespace = service.metadata.namespace
                service_type = service.spec.type
                cluster_ip = service.spec.cluster_ip

                service_info = {
                    "name": name,
                    "namespace": namespace,
                    "type": service_type,
                    "cluster_ip": cluster_ip,
                    "ports": [],
                }

                # Check service ports
                if service.spec.ports:
                    for port in service.spec.ports:
                        service_info["ports"].append(
                            {
                                "name": port.name,
                                "port": port.port,
                                "target_port": port.target_port,
                                "protocol": port.protocol,
                            }
                        )

                # Count service types
                if service_type == "LoadBalancer":
                    load_balancer_count += 1
                elif service_type == "ClusterIP":
                    cluster_ip_count += 1
                elif service_type == "NodePort":
                    node_port_count += 1

                services.append(service_info)

            result = {
                "services": services,
                "total_services": len(services),
                "load_balancer_count": load_balancer_count,
                "cluster_ip_count": cluster_ip_count,
                "node_port_count": node_port_count,
            }

            if services:
                result["check_status"] = "PASS"
                result["message"] = (
                    f"Found {len(services)} services "
                    f"({load_balancer_count} LoadBalancer, "
                    f"{cluster_ip_count} ClusterIP, "
                    f"{node_port_count} NodePort)"
                )
            else:
                result["check_status"] = "INFO"
                result["message"] = "No services found in cluster"

            return result

        except Exception as e:
            logger.error(f"Failed to check services: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check services: {e}",
                "error": str(e),
            }

    def check_ingresses(self) -> Dict[str, Any]:
        """Check Kubernetes ingress resources"""
        if not self.k8s_client:
            return {
                "check_status": "SKIP",
                "message": "Kubernetes client not available for ingress check",
            }

        try:
            # Get all ingresses across namespaces
            ingresses_response = self.k8s_client.list_ingress_for_all_namespaces()

            ingresses = []
            tls_count = 0
            no_tls_count = 0

            for ingress in ingresses_response.items:
                name = ingress.metadata.name
                namespace = ingress.metadata.namespace
                ingress_class = ingress.spec.ingress_class_name

                ingress_info = {
                    "name": name,
                    "namespace": namespace,
                    "ingress_class": ingress_class,
                    "hosts": [],
                    "tls": [],
                }

                # Check hosts
                if ingress.spec.rules:
                    for rule in ingress.spec.rules:
                        if rule.host:
                            ingress_info["hosts"].append(rule.host)

                # Check TLS configuration
                if ingress.spec.tls:
                    tls_count += 1
                    for tls in ingress.spec.tls:
                        ingress_info["tls"].append(
                            {"secret_name": tls.secret_name, "hosts": tls.hosts}
                        )
                else:
                    no_tls_count += 1

                ingresses.append(ingress_info)

            result = {
                "ingresses": ingresses,
                "total_ingresses": len(ingresses),
                "tls_enabled_count": tls_count,
                "no_tls_count": no_tls_count,
                "tls_percentage": (
                    (tls_count / len(ingresses) * 100) if ingresses else 0
                ),
            }

            if ingresses:
                if tls_count == len(ingresses):
                    result["check_status"] = "PASS"
                    result["message"] = (
                        f"All {len(ingresses)} ingresses have TLS enabled"
                    )
                elif tls_count > 0:
                    result["check_status"] = "WARN"
                    result["message"] = (
                        f"{tls_count}/{len(ingresses)} ingresses have TLS enabled"
                    )
                else:
                    result["check_status"] = "FAIL"
                    result["message"] = "No ingresses have TLS enabled"
            else:
                result["check_status"] = "INFO"
                result["message"] = "No ingresses found in cluster"

            return result

        except Exception as e:
            logger.error(f"Failed to check ingresses: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check ingresses: {e}",
                "error": str(e),
            }

    def check_database_connectivity(self) -> Dict[str, Any]:
        """Check database connectivity and configuration"""
        try:
            # Get RDS instances in the region
            rds_response = self.rds_client.describe_db_instances()

            db_instances = []
            for db in rds_response.get("DBInstances", []):
                db_identifier = db["DBInstanceIdentifier"]
                db_status = db["DBInstanceStatus"]
                db_engine = db["Engine"]
                db_endpoint = db.get("Endpoint", {})

                db_info = {
                    "identifier": db_identifier,
                    "status": db_status,
                    "engine": db_engine,
                    "endpoint": db_endpoint.get("Address"),
                    "port": db_endpoint.get("Port"),
                    "vpc_security_groups": [
                        sg["VpcSecurityGroupId"]
                        for sg in db.get("VpcSecurityGroups", [])
                    ],
                }

                # Check if database is accessible from cluster VPC
                if self.vpc_id:
                    # This would need additional logic to check security group rules
                    db_info["cluster_vpc_access"] = "CHECK_NEEDED"
                else:
                    db_info["cluster_vpc_access"] = "UNKNOWN"

                db_instances.append(db_info)

            result = {
                "db_instances": db_instances,
                "total_instances": len(db_instances),
                "available_count": len(
                    [db for db in db_instances if db["status"] == "available"]
                ),
                "unavailable_count": len(
                    [db for db in db_instances if db["status"] != "available"]
                ),
            }

            if db_instances:
                available_count = result["available_count"]
                total_count = result["total_instances"]

                if available_count == total_count:
                    result["check_status"] = "PASS"
                    result["message"] = (
                        f"All {total_count} database instances " "are available"
                    )
                else:
                    result["check_status"] = "WARN"
                    result["message"] = (
                        f"{available_count}/{total_count} database "
                        "instances are available"
                    )
            else:
                result["check_status"] = "INFO"
                result["message"] = "No RDS instances found in region"

            return result

        except Exception as e:
            logger.error(f"Failed to check database connectivity: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check database connectivity: {e}",
                "error": str(e),
            }

    def check_application_health(self) -> Dict[str, Any]:
        """Check application health endpoints"""
        if not self.k8s_client:
            return {
                "check_status": "SKIP",
                "message": "Kubernetes client not available for health check",
            }

        try:
            # Get all services with health check annotations
            services_response = self.k8s_client.list_service_for_all_namespaces()

            health_checks = []
            services_with_health = 0
            services_without_health = 0

            for service in services_response.items:
                name = service.metadata.name
                namespace = service.metadata.namespace

                # Check for health check annotations
                annotations = service.metadata.annotations or {}
                health_check_path = annotations.get("health-check-path")
                health_check_port = annotations.get("health-check-port")

                service_info = {
                    "name": name,
                    "namespace": namespace,
                    "health_check_path": health_check_path,
                    "health_check_port": health_check_port,
                }

                if health_check_path and health_check_port:
                    services_with_health += 1
                    service_info["has_health_check"] = True
                    service_info["health_status"] = "CONFIGURED"
                else:
                    services_without_health += 1
                    service_info["has_health_check"] = False
                    service_info["health_status"] = "NOT_CONFIGURED"

                health_checks.append(service_info)

            result = {
                "health_checks": health_checks,
                "total_services": len(health_checks),
                "services_with_health": services_with_health,
                "services_without_health": services_without_health,
                "health_coverage_percentage": (
                    (services_with_health / len(health_checks) * 100)
                    if health_checks
                    else 0
                ),
            }

            if services_with_health > 0:
                coverage = result["health_coverage_percentage"]
                if coverage >= 80:
                    result["check_status"] = "PASS"
                    result["message"] = (
                        f"Good health check coverage: {coverage:.1f}% of services"
                    )
                elif coverage >= 50:
                    result["check_status"] = "WARN"
                    result["message"] = (
                        f"Moderate health check coverage: {coverage:.1f}% of services"
                    )
                else:
                    result["check_status"] = "FAIL"
                    result["message"] = (
                        f"Poor health check coverage: {coverage:.1f}% of services"
                    )
            else:
                result["check_status"] = "FAIL"
                result["message"] = "No services have health checks configured"

            return result

        except Exception as e:
            logger.error(f"Failed to check application health: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check application health: {e}",
                "error": str(e),
            }

    def get_application_recommendations(self) -> Dict[str, Any]:
        """Provide recommendations for application deployment"""
        try:
            recommendations = []

            # Check deployments health
            deployments_check = self.check_deployments()
            if deployments_check.get("check_status") in ["WARN", "FAIL"]:
                unhealthy_count = deployments_check.get("unhealthy_count", 0)
                recommendations.append(
                    {
                        "type": "deployment_health",
                        "message": f"Fix {unhealthy_count} unhealthy deployments",
                        "severity": "HIGH",
                    }
                )

            # Check ingress TLS
            ingresses_check = self.check_ingresses()
            if ingresses_check.get("check_status") == "FAIL":
                recommendations.append(
                    {
                        "type": "ingress_tls",
                        "message": "Enable TLS for all ingresses",
                        "severity": "HIGH",
                    }
                )

            # Check database connectivity
            db_check = self.check_database_connectivity()
            if db_check.get("check_status") == "WARN":
                unavailable_count = db_check.get("unavailable_count", 0)
                recommendations.append(
                    {
                        "type": "database_availability",
                        "message": (
                            f"Check {unavailable_count} unavailable "
                            "database instances"
                        ),
                        "severity": "HIGH",
                    }
                )

            # Check application health
            health_check = self.check_application_health()
            if health_check.get("check_status") == "FAIL":
                recommendations.append(
                    {
                        "type": "health_checks",
                        "message": "Configure health checks for all services",
                        "severity": "MEDIUM",
                    }
                )

            return {
                "recommendations": recommendations,
                "total_recommendations": len(recommendations),
                "check_status": "PASS" if not recommendations else "WARN",
                "message": f"Found {len(recommendations)} application recommendations",
            }

        except Exception as e:
            logger.error(f"Failed to generate application recommendations: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to generate application recommendations: {e}",
                "error": str(e),
            }
