# Kubernetes Setup Guide

To enable the CD pipeline to deploy to a real Kubernetes cluster, follow these steps.

## 1. Create a Kubernetes Cluster
You can use any provider (AWS EKS, GKE, DigitalOcean) or a local cluster accessible via tunnel (like ngrok for local Minikube, though cloud is recommended for GitHub Actions).

**Recommended for Demo:** Use a small DigitalOcean K8s cluster or Civo (fast spin up).

## 2. Get Kubeconfig
Get the `kubeconfig` file that allows `kubectl` to access your cluster.
- **Minikube**: `~/.kube/config` (ensure the server URL is publicly accessible)
- **Cloud**: Download from the provider dashboard.

## 3. Configure GitHub Secret
1. Go to your GitHub Repository -> **Settings** -> **Secrets and variables** -> **Actions**.
2. Create a new Repository Secret:
   - **Name**: `KUBE_CONFIG`
   - **Value**: Paste the entire content of your `kubeconfig` file.

## 4. (Optional) Configure Environments
To enable "Manual Approval" for Production:
1. Go to **Settings** -> **Environments**.
2. Click **New environment** -> Create "production".
3. Click "Required reviewers" and select yourself.

## 5. Namespaces
The pipeline will automatically attempt to create `staging` and `production` namespaces, but you can create them manually to be sure:
```bash
kubectl create namespace staging
kubectl create namespace production
```
