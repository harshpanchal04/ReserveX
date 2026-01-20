#!/bin/bash
set -e

echo "🚀 Starting Server Setup (K3s Bootstrap)..."

# 1. Update System
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install Essentials
sudo apt-get install -y curl unzip git

# 3. Install K3s (Lightweight Kubernetes)
# We disable traefik to keep it simple and light
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--disable=traefik" sh -

# 4. Configure Permissions
# Allow 'ubuntu' user to run kubectl without sudo
sudo mkdir -p /home/ubuntu/.kube
sudo cp /etc/rancher/k3s/k3s.yaml /home/ubuntu/.kube/config
sudo chown ubuntu:ubuntu /home/ubuntu/.kube/config
sudo chmod 644 /home/ubuntu/.kube/config

# Add K3s config to environment
echo "export KUBECONFIG=~/.kube/config" >> /home/ubuntu/.bashrc

# 5. Firewall Setup (UFW)
# Allow SSH, K8s API, and NodePort 30001
sudo ufw allow 22/tcp
sudo ufw allow 6443/tcp
sudo ufw allow 30001/tcp
sudo ufw --force enable

echo "✅ Server Setup Complete! Re-login to use kubectl."
