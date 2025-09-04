"""
Infrastructure validation checker for EKS clusters
"""

import boto3
from typing import Dict, Any
from loguru import logger


class InfrastructureChecker:
    """Checks EKS infrastructure components including cluster, nodes, and VPC"""

    def __init__(self, eks_client: boto3.client, ec2_client: boto3.client, env_config):
        self.eks_client = eks_client
        self.ec2_client = ec2_client
        self.env_config = env_config

        # Extract VPC configuration - support both new nested
        # structure and legacy fields
        self.vpc_config = env_config.vpc if env_config.vpc else {}
        self.vpc_id = self.vpc_config.get("vpc_id") or env_config.vpc_id
        self.subnet_ids = self.vpc_config.get("subnet_ids", []) or env_config.subnet_ids
        self.security_groups = (
            self.vpc_config.get("security_groups", []) or env_config.security_groups
        )

    def check_all(self) -> Dict[str, Any]:
        """Run all infrastructure checks"""
        return {
            "cluster": self.check_cluster_status(),
            "node_groups": self.check_node_groups(),
            "vpc": self.check_vpc_configuration(),
            "subnets": self.check_subnets(),
            "security_groups": self.check_security_groups(),
            "iam": self.check_iam_roles(),
        }

    def check_cluster_status(self) -> Dict[str, Any]:
        """Check EKS cluster status and configuration"""
        try:
            response = self.eks_client.describe_cluster(
                name=self.env_config.cluster_name
            )

            cluster = response["cluster"]
            status = cluster["status"]
            version = cluster["version"]

            result = {
                "name": cluster["name"],
                "status": status,
                "version": version,
                "platform_version": cluster.get("platformVersion"),
                "endpoint": cluster.get("endpoint"),
                "role_arn": cluster.get("roleArn"),
                "vpc_id": cluster.get("resourcesVpcConfig", {}).get("vpcId"),
                "subnet_ids": cluster.get("resourcesVpcConfig", {}).get(
                    "subnetIds", []
                ),
                "security_group_ids": cluster.get("resourcesVpcConfig", {}).get(
                    "securityGroupIds", []
                ),
            }

            # Determine check status
            if status == "ACTIVE":
                result["check_status"] = "PASS"
                result["message"] = (
                    f"Cluster {self.env_config.cluster_name} is healthy and active"
                )
            elif status == "CREATING":
                result["check_status"] = "WARN"
                result["message"] = (
                    f"Cluster {self.env_config.cluster_name} is still creating"
                )
            elif status == "FAILED":
                result["check_status"] = "FAIL"
                result["message"] = f"Cluster {self.env_config.cluster_name} has failed"
            else:
                result["check_status"] = "WARN"
                result["message"] = (
                    f"Cluster {self.env_config.cluster_name} status: {status}"
                )

            return result

        except Exception as e:
            logger.error(f"Failed to check cluster status: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check cluster status: {e}",
                "error": str(e),
            }

    def check_node_groups(self) -> Dict[str, Any]:
        """Check EKS managed node groups"""
        try:
            response = self.eks_client.list_nodegroups(
                clusterName=self.env_config.cluster_name
            )

            nodegroups = response.get("nodegroups", [])
            results = {}

            for ng_name in nodegroups:
                ng_response = self.eks_client.describe_nodegroup(
                    clusterName=self.env_config.cluster_name, nodegroupName=ng_name
                )

                nodegroup = ng_response["nodegroup"]
                status = nodegroup["status"]

                results[ng_name] = {
                    "status": status,
                    "instance_type": nodegroup.get("instanceTypes", []),
                    "desired_capacity": nodegroup.get("scalingConfig", {}).get(
                        "desiredSize"
                    ),
                    "min_size": nodegroup.get("scalingConfig", {}).get("minSize"),
                    "max_size": nodegroup.get("scalingConfig", {}).get("maxSize"),
                    "ami_type": nodegroup.get("amiType"),
                    "version": nodegroup.get("version"),
                }

                # Determine check status
                if status == "ACTIVE":
                    results[ng_name]["check_status"] = "PASS"
                    results[ng_name]["message"] = f"Node group {ng_name} is healthy"
                elif status in ["CREATING", "UPDATING"]:
                    results[ng_name]["check_status"] = "WARN"
                    results[ng_name][
                        "message"
                    ] = f"Node group {ng_name} is {status.lower()}"
                else:
                    results[ng_name]["check_status"] = "FAIL"
                    results[ng_name][
                        "message"
                    ] = f"Node group {ng_name} status: {status}"

            # Check if expected node groups exist
            expected_ngs = set(self.env_config.node_groups)
            actual_ngs = set(nodegroups)

            if expected_ngs and not expected_ngs.issubset(actual_ngs):
                missing = expected_ngs - actual_ngs
                results["missing_nodegroups"] = {
                    "check_status": "FAIL",
                    "message": f"Missing expected node groups: {list(missing)}",
                    "missing": list(missing),
                }

            return results

        except Exception as e:
            logger.error(f"Failed to check node groups: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check node groups: {e}",
                "error": str(e),
            }

    def check_vpc_configuration(self) -> Dict[str, Any]:
        """Check VPC configuration for the cluster"""
        try:
            if not self.vpc_id:
                return {
                    "check_status": "WARN",
                    "message": "VPC ID not configured in environment settings",
                }

            response = self.ec2_client.describe_vpcs(VpcIds=[self.vpc_id])

            vpc = response["Vpcs"][0]
            state = vpc["State"]

            result = {
                "vpc_id": vpc["VpcId"],
                "state": state,
                "cidr_block": vpc["CidrBlock"],
                "is_default": vpc.get("IsDefault", False),
                "tags": vpc.get("Tags", []),
            }

            if state == "available":
                result["check_status"] = "PASS"
                result["message"] = f"VPC {self.vpc_id} is available"
            else:
                result["check_status"] = "FAIL"
                result["message"] = f"VPC {self.vpc_id} state: {state}"

            return result

        except Exception as e:
            logger.error(f"Failed to check VPC configuration: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check VPC configuration: {e}",
                "error": str(e),
            }

    def check_subnets(self) -> Dict[str, Any]:
        """Check subnet configuration"""
        try:
            if not self.subnet_ids:
                return {
                    "check_status": "WARN",
                    "message": "No subnet IDs configured in environment settings",
                }

            response = self.ec2_client.describe_subnets(SubnetIds=self.subnet_ids)

            results = {}
            for subnet in response["Subnets"]:
                subnet_id = subnet["SubnetId"]
                state = subnet["State"]
                availability_zone = subnet["AvailabilityZone"]

                results[subnet_id] = {
                    "state": state,
                    "availability_zone": availability_zone,
                    "cidr_block": subnet["CidrBlock"],
                    "available_ip_address_count": subnet.get(
                        "AvailableIpAddressCount", 0
                    ),
                    "vpc_id": subnet["VpcId"],
                }

                if state == "available":
                    results[subnet_id]["check_status"] = "PASS"
                    results[subnet_id]["message"] = f"Subnet {subnet_id} is available"
                else:
                    results[subnet_id]["check_status"] = "FAIL"
                    results[subnet_id]["message"] = f"Subnet {subnet_id} state: {state}"

            return results

        except Exception as e:
            logger.error(f"Failed to check subnets: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check subnets: {e}",
                "error": str(e),
            }

    def check_security_groups(self) -> Dict[str, Any]:
        """Check security group configuration"""
        try:
            if not self.security_groups:
                return {
                    "check_status": "WARN",
                    "message": "No security groups configured in environment settings",
                }

            response = self.ec2_client.describe_security_groups(
                GroupIds=self.security_groups
            )

            results = {}
            for sg in response["SecurityGroups"]:
                sg_id = sg["GroupId"]
                sg_name = sg.get("GroupName", "N/A")

                results[sg_id] = {
                    "name": sg_name,
                    "description": sg.get("GroupDescription", ""),
                    "vpc_id": sg["VpcId"],
                    "inbound_rules": len(sg.get("IpPermissions", [])),
                    "outbound_rules": len(sg.get("IpPermissionsEgress", [])),
                    "tags": sg.get("Tags", []),
                }

                # Basic validation - check if security group exists
                results[sg_id]["check_status"] = "PASS"
                results[sg_id]["message"] = f"Security group {sg_name} ({sg_id}) exists"

            return results

        except Exception as e:
            logger.error(f"Failed to check security groups: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check security groups: {e}",
                "error": str(e),
            }

    def check_iam_roles(self) -> Dict[str, Any]:
        """Check IAM roles associated with the cluster"""
        try:
            # Get cluster IAM role
            cluster_response = self.eks_client.describe_cluster(
                name=self.env_config.cluster_name
            )

            cluster_role_arn = cluster_response["cluster"].get("roleArn")

            result = {
                "cluster_role_arn": cluster_role_arn,
                "cluster_role_exists": False,
                "node_group_roles": {},
            }

            # Check cluster IAM role
            if cluster_role_arn:
                iam_client = boto3.client("iam", region_name=self.env_config.region)
                role_name = cluster_role_arn.split("/")[-1]

                try:
                    iam_client.get_role(RoleName=role_name)
                    result["cluster_role_exists"] = True
                    result["cluster_check_status"] = "PASS"
                    result["cluster_message"] = f"Cluster IAM role {role_name} exists"
                except iam_client.exceptions.NoSuchEntityException:
                    result["cluster_check_status"] = "FAIL"
                    result["cluster_message"] = (
                        f"Cluster IAM role {role_name} does not exist"
                    )
                except Exception as e:
                    result["cluster_check_status"] = "WARN"
                    result["cluster_message"] = (
                        f"Could not verify cluster IAM role: {e}"
                    )

            # Check node group roles
            ng_response = self.eks_client.list_nodegroups(
                clusterName=self.env_config.cluster_name
            )

            for ng_name in ng_response.get("nodegroups", []):
                ng_details = self.eks_client.describe_nodegroup(
                    clusterName=self.env_config.cluster_name, nodegroupName=ng_name
                )

                node_role_arn = ng_details["nodegroup"].get("nodeRole")
                if node_role_arn:
                    role_name = node_role_arn.split("/")[-1]
                    result["node_group_roles"][ng_name] = {
                        "role_arn": node_role_arn,
                        "role_name": role_name,
                        "check_status": "PASS",  # Assume exists if configured
                        "message": f"Node group {ng_name} has IAM role configured",
                    }

            return result

        except Exception as e:
            logger.error(f"Failed to check IAM roles: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check IAM roles: {e}",
                "error": str(e),
            }
