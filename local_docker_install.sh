#!/bin/bash
# This script installs Docker, Docker Compose, and database command-line clients
# on an Amazon Linux 2023 EC2 host.

set -e

echo "--- Updating system packages ---"
sudo dnf update -y

echo "--- Installing Docker and Docker Compose ---"
sudo dnf install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user

echo "--- Installing Docker Compose v2 ---"
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
sudo systemctl restart docker
echo "✅ Docker and Docker Compose installed."

echo "--- Installing Database CLI Tools ---"
# Install PostgreSQL client (psql)
echo "--> Installing PostgreSQL client..."
sudo dnf install -y postgresql15

# Install MySQL client (mysql)
echo "--> Installing MySQL client..."
sudo dnf install -y mariadb105

echo "============================================================"
echo "✅ Setup complete! Refreshing the shell session..."
echo "You can now run 'docker compose up --build -d' to start the application."
echo "============================================================"

# Create a new shell session for the ec2-user to apply group changes
# This allows docker commands to be run without sudo
newgrp docker <<'END'
