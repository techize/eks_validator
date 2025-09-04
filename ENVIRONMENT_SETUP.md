# Environment Variable Setup Guide

## Quick Start
1. Copy .env.example to .env
2. Set your environment-specific variables
3. Run the validator

## Example .env file
```bash
# AWS Configuration
AWS_PROFILE=your-aws-profile
AWS_REGION=us-east-1

# Test Environment
EKS_TEST_VPC_ID=vpc-xxxxxxxxxxxxxxxxx
EKS_TEST_CLUSTER_NAME=your-test-cluster
EKS_TEST_SUBNET_IDS=subnet-xxxxxxxxx,subnet-xxxxxxxxx

# UAT Environment
EKS_UAT_VPC_ID=vpc-xxxxxxxxxxxxxxxxx
EKS_UAT_CLUSTER_NAME=your-uat-cluster
EKS_UAT_SUBNET_IDS=subnet-xxxxxxxxx,subnet-xxxxxxxxx

# Production Environment
EKS_PROD_VPC_ID=vpc-xxxxxxxxxxxxxxxxx
EKS_PROD_CLUSTER_NAME=your-prod-cluster
EKS_PROD_SUBNET_IDS=subnet-xxxxxxxxx,subnet-xxxxxxxxx
```

## Validation
Run `python test_config.py` to validate your configuration.
