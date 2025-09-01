#!/bin/bash

# This script automates the setup of the EC2 DB Quick Test application environment
# using Docker and Docker Compose.

set -e

# --- Banner ---
echo "============================================================"
echo "🚀 Starting Docker Compose Deployment for EC2 DB Quick 🚀"
echo "============================================================"

# --- 1. System Updates and Docker Installation ---
echo "--> Updating system packages and installing Docker..."
sudo yum update -y
sudo yum install -y docker
echo "✅ Docker installed."

# --- 2. Docker Service ---
echo "--> Starting Docker service and adding user to the docker group..."
sudo service docker start
sudo usermod -a -G docker ec2-user
echo "✅ Docker started. IMPORTANT: You need to log out and log back in for docker group changes to take effect."

# --- 3. Docker Compose Installation ---
echo "--> Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
echo "✅ Docker Compose installed. Version: $(docker-compose --version)"

# --- Final Instructions ---
echo "============================================================"
echo "✅ Deployment script finished!"
echo ""
echo "MANUAL STEPS REQUIRED:"
echo "1. IMPORTANT: LOG OUT and LOG BACK IN to apply Docker permissions."
echo "2. Install your observability agent on the host (see the README)."
echo "3. From the 'ec2-db-quick' directory, run the application using Docker Compose:"
echo "   docker-compose up --build -d"
echo ""
echo "To stop the application, run:"
echo "   docker-compose down"
echo "============================================================"
