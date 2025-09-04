#!/bin/bash
# VPC Discovery Helper Script
# This script helps discover VPC configuration for all environments

set -e

echo "🔍 EKS VPC Discovery Helper"
echo "============================"

# Check if Python script exists
if [ ! -f "discover_vpc.py" ]; then
    echo "❌ discover_vpc.py not found. Please ensure the VPC discovery script is in the current directory."
    exit 1
fi

# Function to discover VPC for an environment
discover_env() {
    local env=$1
    local cluster=$2
    local region=$3
    local profile=$4

    echo ""
    echo "🔍 Discovering VPC for $env environment..."
    echo "----------------------------------------"

    if [ -n "$profile" ]; then
        python discover_vpc.py --cluster "$cluster" --region "$region" --profile "$profile" --env "$env"
    else
        python discover_vpc.py --cluster "$cluster" --region "$region" --env "$env"
    fi
}

# Example usage - modify these values for your environments
echo "📋 Example commands for your environments:"
echo ""
echo "# Test Environment:"
echo "python discover_vpc.py --cluster 'your-test-cluster' --region 'us-east-1' --profile 'test-profile' --env 'test'"
echo ""
echo "# UAT Environment:"
echo "python discover_vpc.py --cluster 'your-uat-cluster' --region 'us-east-1' --profile 'uat-profile' --env 'uat'"
echo ""
echo "# Production Environment:"
echo "python discover_vpc.py --cluster 'your-prod-cluster' --region 'us-east-1' --profile 'prod-profile' --env 'prod'"
echo ""

echo "💡 To run discovery for all environments, execute the commands above one by one."
echo "💡 Then copy the generated config entries to your config.yaml file."
echo ""
echo "🔧 Make sure you have:"
echo "   - AWS CLI configured with appropriate profiles"
echo "   - Access to the EKS clusters"
echo "   - Python and boto3 installed"
echo ""
echo "📝 After discovery, update your config.yaml with the actual values."
