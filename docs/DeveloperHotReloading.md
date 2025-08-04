# Developer Hot Reloading Guide

This guide explains how to set up a development environment that supports hot reloading of API code when running in Kubernetes infrastructure. This setup allows you to make changes to your local files and have them immediately reflected in the running K8s cluster's migration assistant container.

## Prerequisites

- Minikube installed and configured
- kubectl installed
- Helm installed
- Docker installed

## Setup Steps

### 1. Start Minikube with Local Directory Mount

Start by navigating to the k8s deployment directory and running the minikube local script:

```bash
cd deployment/k8s
./minikubeLocal.sh --start
```

This script starts minikube and mounts your local directory to `/opensearch-migrations` in the minikube VM, which is essential for the hot reloading functionality.

### 2. Build Docker Images

Build the necessary Docker images that will be used by the Kubernetes deployment:

```bash
./buildDockerImagesMini.sh
```

### 3. Update Helm Chart Dependencies

Ensure all Helm chart dependencies are up to date:

```bash
./update_deps.sh
```

### 4. Deploy Migration Assistant with Developer Mode Enabled

Deploy the Migration Assistant Helm chart with developer mode explicitly enabled:

```bash
helm install ma -n ma charts/aggregates/migrationAssistant --create-namespace --set migration-console.developerModeEnabled=true
```

Note: The `developerModeEnabled` parameter is set to `true` by default in the migration-console component chart, but we're setting it explicitly for clarity.

### 5. Port-Forward the API Service

The API runs inside the migration-console pod. You need to port-forward from the pod to your local machine:

```bash
# First, wait for the pod to be ready
kubectl -n ma wait --for=condition=ready pod -l app=ma-migration-console

# Then port-forward the API service (assuming it runs on port 8000 inside the container)
kubectl -n ma port-forward deployment/ma-migration-console 8000:8000
```

This makes the API available at http://localhost:8000 on your local machine.

### 6. Start Frontend Server Locally

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

This will start the frontend server on port 3000, which is already configured in the API's CORS settings to allow requests from http://localhost:3000.

## How It Works

When `developerModeEnabled` is true, the following happens:

1. The local repository directory at `/opensearch-migrations/TrafficCapture/dockerSolution/src/main/docker/migrationConsole/lib` is mounted into the container at `/root/lib`.
2. Any changes you make to the files in your local directory will be immediately available in the container.
3. The container runs `source /.venv/bin/activate && pipenv install -e ~/lib/console_link` at startup, which installs the console_link package in development mode.

## Verifying the Setup

To verify that hot reloading is working:

1. Make a change to a file in `TrafficCapture/dockerSolution/src/main/docker/migrationConsole/lib/console_link`
2. The change should be automatically reflected in the running container
3. Test the API through your frontend or directly via curl/browser

## Troubleshooting

### Restarting the API Server

If you need to restart the API server inside the container after making certain types of changes:

```bash
kubectl -n ma exec -it deployment/ma-migration-console -c console -- /bin/bash
# Inside the container
source /.venv/bin/activate
cd ~/lib/console_link
fastapi dev console_link/api/main.py
```

### Checking API Logs

To view the logs from the API server:

```bash
kubectl -n ma logs deployment/ma-migration-console -c console -f
```

### Re-deploying the Helm Chart

If you need to redeploy the chart with updated settings:

```bash
helm uninstall -n ma ma
helm install ma -n ma charts/aggregates/migrationAssistant --create-namespace --set migration-console.developerModeEnabled=true
```

## Cleanup

When you're done with development, you can clean up with:

```bash
# Remove the Helm deployment
helm uninstall -n ma ma

# Delete any persistent volume claims
kubectl -n ma delete pvc --all

# Stop minikube
./minikubeLocal.sh --delete
```
