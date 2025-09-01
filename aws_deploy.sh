#!/bin/bash

# This script automates the creation of an EC2 instance and its dependencies
# using the AWS CLI for the EC2 DB Quick Test application.
# It sources configuration from a .env file.

set -e

# --- Configuration ---
# Source environment variables from .env file if it exists
if [ -f .env ]; then
  # The tr command removes carriage returns to prevent issues with files edited on Windows
  export $(grep -v '^#' .env | tr -d '\r' | xargs)
fi

# Check for required environment variables
if [ -z "$KEY_PAIR_NAME" ] || [ -z "$REPO_URL" ] || [ -z "$AWS_REGION" ]; then
  echo "Error: Required environment variables are not set."
  echo "Please create a .env file from .env.sample and fill in the values."
  exit 1
fi

echo "✅ Configuration loaded from .env file."

# --- Environment Setup ---
# Get the user's public IP address for the security group
MY_IP=$(curl -s http://checkip.amazon.com)
echo "🔑 Using Key Pair: $KEY_PAIR_NAME"
echo "🌍 Your public IP for SSH access is: $MY_IP"
echo "📍 Deploying to AWS Region: $AWS_REGION"

# --- AWS CLI Commands ---
echo "--> Creating Security Group 'ec2-db-quick-sg'..."
SG_ID=$(aws ec2 create-security-group --group-name ec2-db-quick-sg --description "Allow SSH and HTTP for test app" --region $AWS_REGION --output text)

echo "--> Authorizing inbound rules for Security Group..."
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 22 --cidr "$MY_IP/32" --region $AWS_REGION
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8000 --cidr 0.0.0.0/0 --region $AWS_REGION

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
  --region $AWS_REGION \
  --query "Instances[0].InstanceId" \
  --output text)
  
echo "✅ EC2 instance is launching with ID: $INSTANCE_ID"
echo "--> Waiting for instance to enter the 'running' state..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $AWS_REGION

PUBLIC_IP=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query "Reservations[0].Instances[0].PublicIpAddress" --region $AWS_REGION --output text)

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
