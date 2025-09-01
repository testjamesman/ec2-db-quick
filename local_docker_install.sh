#!/bin/bash
# This script installs Docker and Docker Compose on an Amazon Linux 2023 host.
set -e

echo "--> Updating all packages..."
sudo dnf update -y

echo "--> Installing Docker..."
sudo dnf install -y docker

echo "--> Starting and enabling the Docker service..."
sudo systemctl start docker
sudo systemctl enable docker

echo "--> Adding ec2-user to the docker group..."
sudo usermod -aG docker ec2-user

echo "--> Installing Docker Compose..."
# Download the latest Docker Compose binary to the correct plugin directory
sudo curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" -o /usr/libexec/docker/cli-plugins/docker-compose
# Make the Docker Compose binary executable
sudo chmod +x /usr/libexec/docker/cli-plugins/docker-compose

echo "--> Restarting Docker service..."
sudo systemctl restart docker

echo "✅ Docker and Docker Compose installation complete."
sudo newgrp docker && docker --version && docker compose version
