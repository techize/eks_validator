#!/usr/bin/env python3
"""
VPC Discovery Script for EKS Cluster Validator

This script helps discover VPC configuration for EKS clusters
and generates the necessary configuration for config.yaml
"""

import boto3
from typing import Dict, Any
import argparse


def get_eks_cluster_vpc_info(
    cluster_name: str, region: str = "us-east-1", profile: str = None
) -> Dict[str, Any]:
    """Get VPC information for an EKS cluster"""

    # Create session with optional profile
    session = (
        boto3.Session(profile_name=profile, region_name=region)
        if profile
        else boto3.Session(region_name=region)
    )

    eks_client = session.client("eks")
    ec2_client = session.client("ec2")

    try:
        # Get cluster information
        cluster_response = eks_client.describe_cluster(name=cluster_name)
        cluster = cluster_response["cluster"]

        vpc_id = cluster["resourcesVpcConfig"]["vpcId"]
        subnet_ids = cluster["resourcesVpcConfig"]["subnetIds"]
        security_group_ids = cluster["resourcesVpcConfig"].get("securityGroupIds", [])

        print(f"🔍 Discovering VPC configuration for cluster: {cluster_name}")
        print(f"📍 Region: {region}")
        print(f"🏢 VPC ID: {vpc_id}")

        # Get VPC details
        vpc_response = ec2_client.describe_vpcs(VpcIds=[vpc_id])
        vpc = vpc_response["Vpcs"][0]
        vpc_cidr = vpc["CidrBlock"]

        print(f"🌐 VPC CIDR: {vpc_cidr}")

        # Get subnet details
        subnet_response = ec2_client.describe_subnets(SubnetIds=subnet_ids)
        subnets_info = []
        for subnet in subnet_response["Subnets"]:
            subnet_info = {
                "id": subnet["SubnetId"],
                "cidr": subnet["CidrBlock"],
                "az": subnet["AvailabilityZone"],
                "type": (
                    "public" if subnet.get("MapPublicIpOnLaunch", False) else "private"
                ),
            }
            subnets_info.append(subnet_info)
            print(
                f"📡 Subnet: {subnet_info['id']} "
                f"({subnet_info['type']}) - "
                f"{subnet_info['cidr']} in {subnet_info['az']}"
            )

        # Get security group details
        security_groups_info = []
        if security_group_ids:
            sg_response = ec2_client.describe_security_groups(
                GroupIds=security_group_ids
            )
            for sg in sg_response["SecurityGroups"]:
                sg_info = {
                    "id": sg["GroupId"],
                    "name": sg.get("GroupName", "N/A"),
                    "description": sg.get("GroupDescription", ""),
                }
                security_groups_info.append(sg_info)
                print(f"🔒 Security Group: {sg_info['id']} ({sg_info['name']})")

        # Get load balancers (if any)
        load_balancers = []
        try:
            elb_client = session.client("elbv2")
            lb_response = elb_client.describe_load_balancers()

            for lb in lb_response["LoadBalancers"]:
                if lb.get("VpcId") == vpc_id:
                    lb_info = {
                        "name": lb["LoadBalancerName"],
                        "arn": lb["LoadBalancerArn"],
                        "type": lb["Type"],
                        "dns_name": lb["DNSName"],
                    }
                    load_balancers.append(lb_info)
                    print(f"⚖️ Load Balancer: {lb_info['name']} ({lb_info['type']})")
        except Exception as e:
            print(f"⚠️ Could not retrieve load balancers: {e}")

        # Generate configuration
        vpc_config = {
            "vpc_id": vpc_id,
            "subnet_ids": subnet_ids,
            "security_groups": security_group_ids,
            "load_balancers": [lb["name"] for lb in load_balancers],
        }

        return {
            "cluster_name": cluster_name,
            "region": region,
            "vpc_config": vpc_config,
            "vpc_details": {
                "cidr": vpc_cidr,
                "subnets": subnets_info,
                "security_groups": security_groups_info,
                "load_balancers": load_balancers,
            },
        }

    except Exception as e:
        print(f"❌ Error discovering VPC info: {e}")
        return None


def generate_config_yaml_entry(env_name: str, vpc_info: Dict[str, Any]) -> str:
    """Generate a config.yaml entry for the environment"""

    config = f"""
  {env_name}:
    cluster_name: "{vpc_info['cluster_name']}"
    region: "{vpc_info['region']}"
    vpc:
      vpc_id: "{vpc_info['vpc_config']['vpc_id']}"
      subnet_ids: {vpc_info['vpc_config']['subnet_ids']}
      security_groups: {vpc_info['vpc_config']['security_groups']}
      load_balancers: {vpc_info['vpc_config']['load_balancers']}
"""

    return config


def main():
    parser = argparse.ArgumentParser(
        description="Discover VPC configuration for EKS clusters"
    )
    parser.add_argument("--cluster", "-c", required=True, help="EKS cluster name")
    parser.add_argument(
        "--region", "-r", default="us-east-1", help="AWS region (default: us-east-1)"
    )
    parser.add_argument("--profile", "-p", help="AWS profile to use")
    parser.add_argument("--env", "-e", help="Environment name for config generation")

    args = parser.parse_args()

    print("🚀 EKS VPC Discovery Tool")
    print("=" * 50)

    vpc_info = get_eks_cluster_vpc_info(args.cluster, args.region, args.profile)

    if vpc_info:
        print("\n✅ VPC Discovery Complete!")
        print("=" * 50)

        if args.env:
            config_entry = generate_config_yaml_entry(args.env, vpc_info)
            print(f"\n📝 Config.yaml entry for '{args.env}':")
            print(config_entry)

        print("\n💡 Next Steps:")
        print("1. Copy the VPC configuration above to your config.yaml")
        print("2. Replace the placeholder values in your config file")
        print("3. Test the validator with: python -m eks_validator.main --env test")
    else:
        print("\n❌ Failed to discover VPC information")


if __name__ == "__main__":
    main()
