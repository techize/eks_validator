"""
Addon validation checker for EKS clusters
"""

import boto3
from typing import Dict, Any
from loguru import logger


class AddonChecker:
    """Checks EKS addon installation and status"""

    def __init__(self, eks_client: boto3.client, env_config):
        self.eks_client = eks_client
        self.env_config = env_config

    def check_all(self) -> Dict[str, Any]:
        """Run all addon checks"""
        return {
            "eks_addons": self.check_eks_addons(),
            "coredns": self.check_coredns_addon(),
            "kube_proxy": self.check_kube_proxy_addon(),
            "vpc_cni": self.check_vpc_cni_addon(),
        }

    def check_eks_addons(self) -> Dict[str, Any]:
        """Check EKS managed addons"""
        try:
            response = self.eks_client.list_addons(
                clusterName=self.env_config.cluster_name
            )

            addon_names = response.get("addons", [])
            results = {}

            for addon_name in addon_names:
                addon_response = self.eks_client.describe_addon(
                    clusterName=self.env_config.cluster_name, addonName=addon_name
                )

                addon = addon_response["addon"]
                status = addon["status"]
                version = addon["addonVersion"]
                health_issues = addon.get("health", {}).get("issues", [])

                results[addon_name] = {
                    "status": status,
                    "version": version,
                    "health_issues": health_issues,
                    "service_account_role_arn": addon.get("serviceAccountRoleArn"),
                    "configuration_values": addon.get("configurationValues"),
                }

                # Determine check status
                if status == "ACTIVE":
                    if health_issues:
                        results[addon_name]["check_status"] = "WARN"
                        results[addon_name]["message"] = (
                            f"Addon {addon_name} is active but has "
                            f"{len(health_issues)} health issues"
                        )
                    else:
                        results[addon_name]["check_status"] = "PASS"
                        results[addon_name][
                            "message"
                        ] = f"Addon {addon_name} is active and healthy"
                elif status in ["CREATING", "UPDATING"]:
                    results[addon_name]["check_status"] = "WARN"
                    results[addon_name][
                        "message"
                    ] = f"Addon {addon_name} is {status.lower()}"
                elif status == "DEGRADED":
                    results[addon_name]["check_status"] = "FAIL"
                    results[addon_name]["message"] = f"Addon {addon_name} is degraded"
                else:
                    results[addon_name]["check_status"] = "FAIL"
                    results[addon_name][
                        "message"
                    ] = f"Addon {addon_name} status: {status}"

            # Check for essential addons
            essential_addons = ["coredns", "kube-proxy", "vpc-cni"]
            missing_essential = []

            for essential in essential_addons:
                if essential not in addon_names:
                    missing_essential.append(essential)

            if missing_essential:
                results["missing_essential_addons"] = {
                    "check_status": "FAIL",
                    "message": f"Missing essential addons: {missing_essential}",
                    "missing": missing_essential,
                }

            return results

        except Exception as e:
            logger.error(f"Failed to check EKS addons: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check EKS addons: {e}",
                "error": str(e),
            }

    def check_coredns_addon(self) -> Dict[str, Any]:
        """Check CoreDNS addon specifically"""
        try:
            # Check if CoreDNS is installed as EKS addon
            addon_response = self.eks_client.describe_addon(
                clusterName=self.env_config.cluster_name, addonName="coredns"
            )

            addon = addon_response["addon"]
            status = addon["status"]
            version = addon["addonVersion"]

            result = {
                "addon_version": version,
                "status": status,
                "configuration_values": addon.get("configurationValues"),
            }

            if status == "ACTIVE":
                result["check_status"] = "PASS"
                result["message"] = f"CoreDNS addon is active (version {version})"
            else:
                result["check_status"] = "FAIL"
                result["message"] = f"CoreDNS addon status: {status}"

            return result

        except self.eks_client.exceptions.ResourceNotFoundException:
            # CoreDNS might be installed as a regular deployment
            return {
                "check_status": "INFO",
                "message": "CoreDNS not installed as EKS addon, checking deployment...",
                "addon_installed": False,
            }
        except Exception as e:
            logger.error(f"Failed to check CoreDNS addon: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check CoreDNS addon: {e}",
                "error": str(e),
            }

    def check_kube_proxy_addon(self) -> Dict[str, Any]:
        """Check kube-proxy addon specifically"""
        try:
            addon_response = self.eks_client.describe_addon(
                clusterName=self.env_config.cluster_name, addonName="kube-proxy"
            )

            addon = addon_response["addon"]
            status = addon["status"]
            version = addon["addonVersion"]

            result = {
                "addon_version": version,
                "status": status,
                "configuration_values": addon.get("configurationValues"),
            }

            if status == "ACTIVE":
                result["check_status"] = "PASS"
                result["message"] = f"kube-proxy addon is active (version {version})"
            else:
                result["check_status"] = "FAIL"
                result["message"] = f"kube-proxy addon status: {status}"

            return result

        except self.eks_client.exceptions.ResourceNotFoundException:
            return {
                "check_status": "INFO",
                "message": "kube-proxy not installed as EKS addon",
                "addon_installed": False,
            }
        except Exception as e:
            logger.error(f"Failed to check kube-proxy addon: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check kube-proxy addon: {e}",
                "error": str(e),
            }

    def check_vpc_cni_addon(self) -> Dict[str, Any]:
        """Check VPC CNI addon specifically"""
        try:
            addon_response = self.eks_client.describe_addon(
                clusterName=self.env_config.cluster_name, addonName="vpc-cni"
            )

            addon = addon_response["addon"]
            status = addon["status"]
            version = addon["addonVersion"]

            result = {
                "addon_version": version,
                "status": status,
                "configuration_values": addon.get("configurationValues"),
            }

            if status == "ACTIVE":
                result["check_status"] = "PASS"
                result["message"] = f"VPC CNI addon is active (version {version})"
            else:
                result["check_status"] = "FAIL"
                result["message"] = f"VPC CNI addon status: {status}"

            return result

        except self.eks_client.exceptions.ResourceNotFoundException:
            return {
                "check_status": "INFO",
                "message": "VPC CNI not installed as EKS addon",
                "addon_installed": False,
            }
        except Exception as e:
            logger.error(f"Failed to check VPC CNI addon: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check VPC CNI addon: {e}",
                "error": str(e),
            }

    def check_addon_versions(self) -> Dict[str, Any]:
        """Check addon versions for compatibility"""
        try:
            response = self.eks_client.list_addons(
                clusterName=self.env_config.cluster_name
            )

            addon_names = response.get("addons", [])
            version_check = {}

            for addon_name in addon_names:
                addon_response = self.eks_client.describe_addon(
                    clusterName=self.env_config.cluster_name, addonName=addon_name
                )

                addon = addon_response["addon"]
                version = addon["addonVersion"]

                # Get available versions for this addon
                versions_response = self.eks_client.describe_addon_versions(
                    addonName=addon_name,
                    kubernetesVersion=self.env_config.cluster_name,
                )

                available_versions = [
                    v["addonVersion"]
                    for v in versions_response.get("addons", [{}])[0].get(
                        "addonVersions", []
                    )
                ]

                # Check if current version is the latest
                if available_versions:
                    latest_version = max(available_versions)
                    is_latest = version == latest_version

                    version_check[addon_name] = {
                        "current_version": version,
                        "latest_version": latest_version,
                        "is_latest": is_latest,
                        "check_status": "PASS" if is_latest else "WARN",
                        "message": (
                            f"Version {version} is "
                            f"{'current' if is_latest else 'outdated'}"
                        ),
                    }
                else:
                    version_check[addon_name] = {
                        "current_version": version,
                        "check_status": "INFO",
                        "message": "Unable to determine latest version",
                    }

            return version_check

        except Exception as e:
            logger.error(f"Failed to check addon versions: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check addon versions: {e}",
                "error": str(e),
            }

    def get_addon_recommendations(self) -> Dict[str, Any]:
        """Provide recommendations for addon management"""
        try:
            response = self.eks_client.list_addons(
                clusterName=self.env_config.cluster_name
            )

            addon_names = response.get("addons", [])
            recommendations = []

            # Essential addons that should be installed
            essential_addons = ["coredns", "kube-proxy", "vpc-cni"]
            installed_addons = set(addon_names)

            missing_essential = set(essential_addons) - installed_addons
            if missing_essential:
                recommendations.append(
                    {
                        "type": "missing_essential",
                        "message": (
                            f"Install missing essential addons: "
                            f"{list(missing_essential)}"
                        ),
                        "addons": list(missing_essential),
                    }
                )

            # Check for outdated addons
            version_check = self.check_addon_versions()
            outdated_addons = [
                name
                for name, info in version_check.items()
                if info.get("check_status") == "WARN"
            ]

            if outdated_addons:
                recommendations.append(
                    {
                        "type": "outdated_versions",
                        "message": f"Update outdated addons: {outdated_addons}",
                        "addons": outdated_addons,
                    }
                )

            return {
                "recommendations": recommendations,
                "total_recommendations": len(recommendations),
                "check_status": "PASS" if not recommendations else "WARN",
                "message": f"Found {len(recommendations)} addon recommendations",
            }

        except Exception as e:
            logger.error(f"Failed to generate addon recommendations: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to generate addon recommendations: {e}",
                "error": str(e),
            }
