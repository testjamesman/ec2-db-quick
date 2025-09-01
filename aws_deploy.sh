#!/bin/bash

# This script automates the creation of an EC2 instance and its dependencies
# using the AWS CLI for the EC2 DB Quick Test application.
# It reads configuration from environment variables.

set -e # Exit immediately if a command exits with a non-zero status.
set -o pipefail # Exit if any command in a pipeline fails.

# --- Configuration ---
# Check for required environment variables from the user's OS
if [ -z "$KEY_PAIR_NAME" ] || [ -z "$REPO_URL" ] || [ -z "$AWS_REGION" ]; then
  echo "❌ Error: Required environment variables are not set."
  echo "Please set AWS_REGION, KEY_PAIR_NAME, and REPO_URL in your environment."
  echo "See the README.md for instructions."
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
MY_IP=$(curl -s http://checkip.amazon.com)
if [ -z "$MY_IP" ]; then
    echo "❌ Error: Could not determine public IP address. Please check your internet connection."
    exit 1
fi

echo "🔑 Using Key Pair: $KEY_PAIR_NAME"
echo "🌍 Your public IP for SSH access is: $MY_IP"
echo "📍 Deploying to AWS Region: $AWS_REGION"

# --- AWS CLI Commands ---
SG_NAME="ec2-db-quick-sg"
echo "--> Checking for existing Security Group '$SG_NAME'..."
# Check if the security group already exists to prevent an error on re-running the script.
SG_ID=$(aws ec2 describe-security-groups --group-names "$SG_NAME" --region "$AWS_REGION" --query "SecurityGroups[0].GroupId" --output text 2>/dev/null || true)

if [ -z "$SG_ID" ]; then
  echo "--> Security Group not found. Creating '$SG_NAME'..."
  SG_ID=$(aws ec2 create-security-group --group-name "$SG_NAME" --description "Allow SSH and HTTP for test app" --region "$AWS_REGION" --output text)
  echo "--> Authorizing inbound rules for new Security Group..."
  aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 22 --cidr "$MY_IP/32" --region "$AWS_REGION"
  aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 8000 --cidr 0.0.0.0/0 --region "$AWS_REGION"
else
  echo "--> Security Group '$SG_NAME' already exists with ID: $SG_ID. Skipping creation."
fi

echo "--> Launching EC2 instance (t2.micro with Amazon Linux 2023)..."

# UserData script to be executed on instance launch
# This script sets up Docker, clones the repo, and starts the application.
USER_DATA=$(cat <<EOF
#!/bin/bash
yum update -y
yum install -y docker git
service docker start
usermod -a -G docker ec2-user
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
cd /home/ec2-user
git clone $REPO_URL
REPO_NAME=\$(basename $REPO_URL .git)
chown -R ec2-user:ec2-user \$REPO_NAME
# Run docker-compose as the ec2-user
su - ec2-user -c "cd /home/ec2-user/\$REPO_NAME && docker-compose up --build -d"
EOF
)

INSTANCE_ID=$(aws ec2 run-instances \
  --image-id resolve:ssm:/aws/service/ami-amazon-linux-latest/amzn2023-ami-hvm-x86_64-gp2 \
  --instance-type t2.micro \
  --key-name "$KEY_PAIR_NAME" \
  --security-group-ids "$SG_ID" \
  --user-data "$USER_DATA" \
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
echo "Access the application (it may take a minute or two to start up):"
echo "http://$PUBLIC_IP:8000"
echo "========================================================================"
