#!/bin/bash
#
# This script automates the creation of an EC2 instance and its dependencies
# using the AWS CLI for the EC2 DB Quick Test application.

# --- Configuration & Safety ---
# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error when substituting.
set -u
# Pipelines fail if any command fails, not just the last one.
set -o pipefail

# --- Environment Variable Check ---
# Check for required environment variables and provide guidance if they are missing.
if [ -z "${KEY_PAIR_NAME-}" ] || [ -z "${REPO_URL-}" ] || [ -z "${AWS_REGION-}" ]; then
  echo "❌ Error: Required environment variables are not set."
  echo "Please export AWS_REGION, KEY_PAIR_NAME, and REPO_URL before running."
  exit 1
fi

echo "✅ Configuration loaded from environment variables."
echo "---"
echo "Using the following configuration:"
echo "  AWS_REGION:    $AWS_REGION"
echo "  KEY_PAIR_NAME: $KEY_PAIR_NAME"
echo "  REPO_URL:      $REPO_URL"
echo "---"

# --- Environment Setup ---
echo "--> Fetching your public IP address..."
# Attempt to get IP from primary source, with a fallback to prevent script failure.
MY_IP=$(curl -s http://checkip.amazonaws.com || curl -s https://ifconfig.me/ip)
if [ -z "$MY_IP" ]; then
    echo "❌ Error: Could not determine public IP address. Please check your network connection."
    exit 1
fi

echo "🔑 Using Key Pair: $KEY_PAIR_NAME"
echo "🌍 Your public IP for SSH access is: $MY_IP"
echo "📍 Deploying to AWS Region: $AWS_REGION"

# --- AWS CLI Commands ---
SG_NAME="ec2-db-quick-sg"
echo "--> Checking for existing Security Group '$SG_NAME'..."

# Check if the security group already exists to avoid errors on re-runs.
SG_ID=$(aws ec2 describe-security-groups --group-names "$SG_NAME" --query "SecurityGroups[0].GroupId" --output text --region "$AWS_REGION" 2>/dev/null || true)

if [ -z "$SG_ID" ]; then
    echo "--> Security Group not found. Creating '$SG_NAME'..."
    SG_ID=$(aws ec2 create-security-group --group-name "$SG_NAME" --description "Allow SSH and HTTP for test app" --region "$AWS_REGION" --query "GroupId" --output text)
    echo "--> Authorizing inbound rules for new Security Group..."
    aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 22 --cidr "$MY_IP/32" --region "$AWS_REGION"
    aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 8000 --cidr 0.0.0.0/0 --region "$AWS_REGION"
else
    echo "--> Security Group '$SG_NAME' already exists with ID: $SG_ID. Ensuring rules are present."
    # Idempotently add rules; this will only add them if they don't already exist.
    aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 22 --cidr "$MY_IP/32" --region "$AWS_REGION" 2>/dev/null || true
    aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 8000 --cidr 0.0.0.0/0 --region "$AWS_REGION" 2>/dev/null || true
fi


echo "--> Launching EC2 instance (t3.medium with Amazon Linux 2023)..."

# UserData script to be executed on instance launch
USER_DATA=$(cat <<'EOF'
#!/bin/bash
# Install git and clone the repository
yum update -y
yum install -y git
cd /home/ec2-user
git clone "$REPO_URL"
EOF
)

# Replace the placeholder in UserData with the actual REPO_URL
USER_DATA_FINAL=$(echo "$USER_DATA" | sed "s|\$REPO_URL|$REPO_URL|g")

INSTANCE_ID=$(aws ec2 run-instances \
  --image-id resolve:ssm:/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-x86_64 \
  --instance-type t3.medium \
  --key-name "$KEY_PAIR_NAME" \
  --security-group-ids "$SG_ID" \
  --user-data "$USER_DATA_FINAL" \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ec2-db-quick-app}]' \
  --region "$AWS_REGION" \
  --query "Instances[0].InstanceId" \
  --output text)

echo "✅ EC2 instance is launching with ID: $INSTANCE_ID"
echo "--> Waiting for instance to enter the 'running' state..."
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$AWS_REGION"

PUBLIC_IP=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --query "Reservations[0].Instances[0].PublicIpAddress" --region "$AWS_REGION" --output text)

echo "========================================================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo ""
echo "Instance Public IP: $PUBLIC_IP"
echo ""
echo "To connect via SSH:"
echo "ssh -i /path/to/your/$KEY_PAIR_NAME.pem ec2-user@$PUBLIC_IP"
echo ""
echo "Next, run the Docker installer on the EC2 instance, then start the app."
echo "See the README.md for the next steps."
echo "========================================================================"

