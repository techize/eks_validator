"""
Networking validation checker for EKS clusters
"""

import boto3
from typing import Dict, List, Any
from loguru import logger


class NetworkingChecker:
    """Checks networking components including load balancers, DNS, and connectivity"""

    def __init__(
        self, ec2_client: boto3.client, elbv2_client: boto3.client, env_config
    ):
        self.ec2_client = ec2_client
        self.elbv2_client = elbv2_client
        self.env_config = env_config

        # Extract VPC configuration - support both new nested
        # structure and legacy fields
        self.vpc_config = env_config.vpc if env_config.vpc else {}
        self.vpc_id = self.vpc_config.get("vpc_id") or env_config.vpc_id
        self.subnet_ids = self.vpc_config.get("subnet_ids", []) or env_config.subnet_ids
        self.security_groups = (
            self.vpc_config.get("security_groups", []) or env_config.security_groups
        )
        self.load_balancers = (
            self.vpc_config.get("load_balancers", []) or env_config.load_balancersent
        )
        self.env_config = env_config

        # Extract VPC configuration - support both new nested structure
        # and legacy fields
        self.vpc_config = env_config.vpc if env_config.vpc else {}
        self.vpc_id = self.vpc_config.get("vpc_id") or env_config.vpc_id
        self.subnet_ids = self.vpc_config.get("subnet_ids", []) or env_config.subnet_ids
        self.security_groups = (
            self.vpc_config.get("security_groups", []) or env_config.security_groups
        )
        self.load_balancers = (
            self.vpc_config.get("load_balancers", []) or env_config.load_balancers
        )

    def check_all(self) -> Dict[str, Any]:
        """Run all networking checks"""
        return {
            "load_balancers": self.check_load_balancers(),
            "security_groups": self.check_security_group_rules(),
            "network_acls": self.check_network_acls(),
            "route_tables": self.check_route_tables(),
            "internet_gateway": self.check_internet_gateway(),
            "nat_gateways": self.check_nat_gateways(),
        }

    def check_load_balancers(self) -> Dict[str, Any]:
        """Check load balancer configuration and health"""
        try:
            results = {}

            # Check ALBs/NLBs
            if self.load_balancers:
                for lb_name in self.load_balancers:
                    try:
                        # Describe load balancer
                        lb_response = self.elbv2_client.describe_load_balancers(
                            Names=[lb_name]
                        )

                        if lb_response["LoadBalancers"]:
                            lb = lb_response["LoadBalancers"][0]
                            lb_arn = lb["LoadBalancerArn"]
                            lb_dns = lb["DNSName"]
                            lb_state = lb["State"]["Code"]
                            lb_type = lb["Type"]
                            lb_scheme = lb["Scheme"]

                            results[lb_name] = {
                                "dns_name": lb_dns,
                                "state": lb_state,
                                "type": lb_type,
                                "scheme": lb_scheme,
                                "vpc_id": lb["VpcId"],
                                "availability_zones": [
                                    az["ZoneName"] for az in lb["AvailabilityZones"]
                                ],
                            }

                            # Check target groups and health
                            tg_response = self.elbv2_client.describe_target_groups(
                                LoadBalancerArn=lb_arn
                            )

                            target_groups = []
                            for tg in tg_response["TargetGroups"]:
                                tg_arn = tg["TargetGroupArn"]
                                health_response = (
                                    self.elbv2_client.describe_target_health(
                                        TargetGroupArn=tg_arn
                                    )
                                )

                                healthy_count = sum(
                                    1
                                    for target in health_response[
                                        "TargetHealthDescriptions"
                                    ]
                                    if target["TargetHealth"]["State"] == "healthy"
                                )

                                total_count = len(
                                    health_response["TargetHealthDescriptions"]
                                )

                                target_groups.append(
                                    {
                                        "name": tg["TargetGroupName"],
                                        "protocol": tg["Protocol"],
                                        "port": tg["Port"],
                                        "healthy_targets": healthy_count,
                                        "total_targets": total_count,
                                        "health_status": (
                                            f"{healthy_count}/{total_count} healthy"
                                        ),
                                    }
                                )

                            results[lb_name]["target_groups"] = target_groups

                            # Determine check status
                            if lb_state == "active":
                                all_healthy = all(
                                    tg["healthy_targets"] == tg["total_targets"]
                                    for tg in target_groups
                                )
                                if all_healthy and target_groups:
                                    results[lb_name]["check_status"] = "PASS"
                                    results[lb_name]["message"] = (
                                        "Load balancer "
                                        + lb_name
                                        + " is active with all targets healthy"
                                    )
                                else:
                                    results[lb_name]["check_status"] = "WARN"
                                    results[lb_name]["message"] = (
                                        "Load balancer "
                                        + lb_name
                                        + " is active but some targets unhealthy"
                                    )
                            else:
                                results[lb_name]["check_status"] = "FAIL"
                                results[lb_name][
                                    "message"
                                ] = f"Load balancer {lb_name} state: {lb_state}"
                        else:
                            results[lb_name] = {
                                "check_status": "FAIL",
                                "message": f"Load balancer {lb_name} not found",
                            }

                    except self.elbv2_client.exceptions.LoadBalancerNotFoundException:
                        results[lb_name] = {
                            "check_status": "FAIL",
                            "message": f"Load balancer {lb_name} not found",
                        }
                    except Exception as e:
                        results[lb_name] = {
                            "check_status": "FAIL",
                            "message": f"Failed to check load balancer {lb_name}: {e}",
                        }
            else:
                results["no_load_balancers"] = {
                    "check_status": "INFO",
                    "message": "No load balancers configured for validation",
                }

            return results

        except Exception as e:
            logger.error(f"Failed to check load balancers: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check load balancers: {e}",
                "error": str(e),
            }

    def check_security_group_rules(self) -> Dict[str, Any]:
        """Check security group rules for proper configuration"""
        try:
            results = {}

            if not self.security_groups:
                return {
                    "check_status": "WARN",
                    "message": "No security groups configured for validation",
                }

            for sg_id in self.security_groups:
                try:
                    sg_response = self.ec2_client.describe_security_groups(
                        GroupIds=[sg_id]
                    )

                    sg = sg_response["SecurityGroups"][0]
                    sg_name = sg.get("GroupName", "N/A")

                    # Analyze inbound rules
                    inbound_rules = sg.get("IpPermissions", [])
                    inbound_analysis = self._analyze_security_group_rules(
                        inbound_rules, "inbound"
                    )

                    # Analyze outbound rules
                    outbound_rules = sg.get("IpPermissionsEgress", [])
                    outbound_analysis = self._analyze_security_group_rules(
                        outbound_rules, "outbound"
                    )

                    results[sg_id] = {
                        "name": sg_name,
                        "inbound_rules_count": len(inbound_rules),
                        "outbound_rules_count": len(outbound_rules),
                        "inbound_analysis": inbound_analysis,
                        "outbound_analysis": outbound_analysis,
                    }

                    # Determine if rules look reasonable
                    has_ssh = any(
                        rule.get("FromPort") == 22 or rule.get("ToPort") == 22
                        for rule in inbound_rules
                    )
                    has_https = any(
                        rule.get("FromPort") == 443 or rule.get("ToPort") == 443
                        for rule in inbound_rules
                    )

                    if has_ssh and has_https:
                        results[sg_id]["check_status"] = "PASS"
                        results[sg_id][
                            "message"
                        ] = f"Security group {sg_name} has appropriate access rules"
                    elif has_ssh or has_https:
                        results[sg_id]["check_status"] = "WARN"
                        results[sg_id][
                            "message"
                        ] = f"Security group {sg_name} has limited access rules"
                    else:
                        results[sg_id]["check_status"] = "WARN"
                        results[sg_id][
                            "message"
                        ] = f"Security group {sg_name} may have restricted access"

                except Exception as e:
                    results[sg_id] = {
                        "check_status": "FAIL",
                        "message": f"Failed to check security group {sg_id}: {e}",
                    }

            return results

        except Exception as e:
            logger.error(f"Failed to check security group rules: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check security group rules: {e}",
                "error": str(e),
            }

    def _analyze_security_group_rules(
        self, rules: List[Dict], direction: str
    ) -> Dict[str, Any]:
        """Analyze security group rules for common patterns"""
        analysis = {
            "total_rules": len(rules),
            "open_to_world": False,
            "has_specific_ips": False,
            "has_security_group_refs": False,
            "common_ports": [],
        }

        for rule in rules:
            from_port = rule.get("FromPort")
            to_port = rule.get("ToPort")

            # Check for open to world (0.0.0.0/0)
            for ip_range in rule.get("IpRanges", []):
                if ip_range.get("CidrIp") == "0.0.0.0/0":
                    analysis["open_to_world"] = True
                    break

            # Check for specific IP ranges
            if rule.get("IpRanges") and len(rule.get("IpRanges")) > 0:
                analysis["has_specific_ips"] = True

            # Check for security group references
            if rule.get("UserIdGroupPairs"):
                analysis["has_security_group_refs"] = True

            # Track common ports
            if from_port == to_port:  # Single port
                port = from_port
            elif from_port and to_port:  # Port range
                port = f"{from_port}-{to_port}"
            else:
                port = None

            if port and port not in analysis["common_ports"]:
                analysis["common_ports"].append(port)

        return analysis

    def check_network_acls(self) -> Dict[str, Any]:
        """Check Network ACL configuration"""
        try:
            if not self.vpc_id:
                return {
                    "check_status": "WARN",
                    "message": "VPC ID not configured, cannot check Network ACLs",
                }

            # Get subnets first to find associated NACLs
            subnet_response = self.ec2_client.describe_subnets(
                Filters=[{"Name": "vpc-id", "Values": [self.vpc_id]}]
            )

            nacl_ids = set()
            for subnet in subnet_response["Subnets"]:
                if subnet.get("NetworkAclId"):
                    nacl_ids.add(subnet["NetworkAclId"])

            if not nacl_ids:
                return {
                    "check_status": "WARN",
                    "message": "No Network ACLs found for VPC subnets",
                }

            results = {}
            for nacl_id in nacl_ids:
                nacl_response = self.ec2_client.describe_network_acls(
                    NetworkAclIds=[nacl_id]
                )

                nacl = nacl_response["NetworkAcls"][0]
                nacl_name = None
                for tag in nacl.get("Tags", []):
                    if tag["Key"] == "Name":
                        nacl_name = tag["Value"]
                        break

                results[nacl_id] = {
                    "name": nacl_name or "N/A",
                    "is_default": nacl.get("IsDefault", False),
                    "entries_count": len(nacl.get("Entries", [])),
                    "associated_subnets": len(nacl.get("Associations", [])),
                }

                # Basic validation
                results[nacl_id]["check_status"] = "PASS"
                results[nacl_id][
                    "message"
                ] = f"Network ACL {nacl_name or nacl_id} is configured"

            return results

        except Exception as e:
            logger.error(f"Failed to check Network ACLs: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check Network ACLs: {e}",
                "error": str(e),
            }

    def check_route_tables(self) -> Dict[str, Any]:
        """Check route table configuration"""
        try:
            if not self.vpc_id:
                return {
                    "check_status": "WARN",
                    "message": "VPC ID not configured, cannot check route tables",
                }

            rt_response = self.ec2_client.describe_route_tables(
                Filters=[{"Name": "vpc-id", "Values": [self.vpc_id]}]
            )

            results = {}
            for rt in rt_response["RouteTables"]:
                rt_id = rt["RouteTableId"]
                rt_name = None
                for tag in rt.get("Tags", []):
                    if tag["Key"] == "Name":
                        rt_name = tag["Value"]
                        break

                routes = rt.get("Routes", [])
                has_igw_route = any(
                    route.get("GatewayId", "").startswith("igw-") for route in routes
                )
                has_nat_route = any(
                    route.get("NatGatewayId", "").startswith("nat-") for route in routes
                )

                results[rt_id] = {
                    "name": rt_name or "N/A",
                    "routes_count": len(routes),
                    "has_internet_gateway": has_igw_route,
                    "has_nat_gateway": has_nat_route,
                    "associated_subnets": len(rt.get("Associations", [])),
                    "main_table": rt.get("Main", False),
                }

                # Basic validation
                results[rt_id]["check_status"] = "PASS"
                results[rt_id][
                    "message"
                ] = f"Route table {rt_name or rt_id} is configured"

            return results

        except Exception as e:
            logger.error(f"Failed to check route tables: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check route tables: {e}",
                "error": str(e),
            }

    def check_internet_gateway(self) -> Dict[str, Any]:
        """Check Internet Gateway configuration"""
        try:
            if not self.vpc_id:
                return {
                    "check_status": "WARN",
                    "message": "VPC ID not configured, cannot check Internet Gateway",
                }

            igw_response = self.ec2_client.describe_internet_gateways(
                Filters=[{"Name": "attachment.vpc-id", "Values": [self.vpc_id]}]
            )

            if not igw_response["InternetGateways"]:
                return {
                    "check_status": "WARN",
                    "message": "No Internet Gateway attached to VPC",
                }

            igw = igw_response["InternetGateways"][0]
            igw_id = igw["InternetGatewayId"]
            igw_name = None
            for tag in igw.get("Tags", []):
                if tag["Key"] == "Name":
                    igw_name = tag["Value"]
                    break

            return {
                "internet_gateway_id": igw_id,
                "name": igw_name or "N/A",
                "state": igw.get("Attachments", [{}])[0].get("State", "unknown"),
                "check_status": "PASS",
                "message": f"Internet Gateway {igw_name or igw_id} is attached to VPC",
            }

        except Exception as e:
            logger.error(f"Failed to check Internet Gateway: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check Internet Gateway: {e}",
                "error": str(e),
            }

    def check_nat_gateways(self) -> Dict[str, Any]:
        """Check NAT Gateway configuration"""
        try:
            if not self.vpc_id:
                return {
                    "check_status": "WARN",
                    "message": "VPC ID not configured, cannot check NAT Gateways",
                }

            nat_response = self.ec2_client.describe_nat_gateways(
                Filters=[{"Name": "vpc-id", "Values": [self.vpc_id]}]
            )

            results = {}
            for nat in nat_response["NatGateways"]:
                nat_id = nat["NatGatewayId"]
                state = nat["State"]
                nat_type = nat.get("ConnectivityType", "public")

                results[nat_id] = {
                    "state": state,
                    "type": nat_type,
                    "subnet_id": nat.get("SubnetId"),
                    "allocation_id": nat.get("NatGatewayAddresses", [{}])[0].get(
                        "AllocationId"
                    ),
                }

                if state == "available":
                    results[nat_id]["check_status"] = "PASS"
                    results[nat_id]["message"] = f"NAT Gateway {nat_id} is available"
                elif state == "pending":
                    results[nat_id]["check_status"] = "WARN"
                    results[nat_id][
                        "message"
                    ] = f"NAT Gateway {nat_id} is still creating"
                else:
                    results[nat_id]["check_status"] = "FAIL"
                    results[nat_id]["message"] = f"NAT Gateway {nat_id} state: {state}"

            if not results:
                return {
                    "check_status": "INFO",
                    "message": "No NAT Gateways found in VPC",
                }

            return results

        except Exception as e:
            logger.error(f"Failed to check NAT Gateways: {e}")
            return {
                "check_status": "FAIL",
                "message": f"Failed to check NAT Gateways: {e}",
                "error": str(e),
            }
