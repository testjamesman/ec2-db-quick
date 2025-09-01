#!/bin/bash
#
# This script automates the deletion of the EC2 instance and related resources
# created by the aws_deploy.sh script.

# --- Configuration & Safety ---
# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error when substituting.
set -u
# Pipelines fail if any command fails, not just the last one.
set -o pipefail

# --- Environment Variable Check ---
if [ -z "${AWS_REGION-}" ]; then
  echo "❌ Error: The AWS_REGION environment variable is not set."
  echo "Please export AWS_REGION to the same region you deployed to."
  exit 1
fi

echo "✅ Using AWS Region: $AWS_REGION"
echo "---"

# --- AWS CLI Commands ---
SG_NAME="ec2-db-quick-sg"
INSTANCE_NAME_TAG="ec2-db-quick-app"

echo "--> Searching for instance with tag 'Name=$INSTANCE_NAME_TAG'..."
INSTANCE_ID=$(aws ec2 describe-instances --filters "Name=tag:Name,Values=$INSTANCE_NAME_TAG" "Name=instance-state-name,Values=running,pending" --query "Reservations[].Instances[].InstanceId" --output text --region "$AWS_REGION")

if [ -z "$INSTANCE_ID" ]; then
    echo "🤷 No running instances found with the tag 'Name=$INSTANCE_NAME_TAG'. Exiting."
    exit 0
fi

echo "--> Found Instance ID: $INSTANCE_ID"
echo "--> Terminating EC2 instance..."
aws ec2 terminate-instances --instance-ids "$INSTANCE_ID" --region "$AWS_REGION" > /dev/null

echo "--> Waiting for instance to be fully terminated..."
aws ec2 wait instance-terminated --instance-ids "$INSTANCE_ID" --region "$AWS_REGION"
echo "✅ Instance terminated successfully."

echo "--> Deleting Security Group '$SG_NAME'..."
aws ec2 delete-security-group --group-name "$SG_NAME" --region "$AWS_REGION"
echo "✅ Security Group deleted."

echo "========================================================================"
echo "✅ Cleanup Complete!"
echo "========================================================================"
