#!/usr/bin/env bash
set -e

echo "Creating kind cluster..."
kind create cluster --name reliability-cluster --config - <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
EOF

echo "Building local Docker image..."
docker build -t reliability-agent-platform:local -f deploy/docker/Dockerfile .

echo "Loading image into kind..."
kind load docker-image reliability-agent-platform:local --name reliability-cluster

echo "Deploying Postgres and Redis..."
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: pgvector/pgvector:pg16
          env:
            - name: POSTGRES_USER
              value: postgres
            - name: POSTGRES_PASSWORD
              value: postgres
            - name: POSTGRES_DB
              value: reliability
          ports:
            - containerPort: 5432
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  ports:
    - port: 5432
  selector:
    app: postgres
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          ports:
            - containerPort: 6379
---
apiVersion: v1
kind: Service
metadata:
  name: redis
spec:
  ports:
    - port: 6379
  selector:
    app: redis
EOF

echo "Waiting for Postgres and Redis..."
kubectl wait --for=condition=available --timeout=60s deployment/postgres
kubectl wait --for=condition=available --timeout=60s deployment/redis

echo "Installing Helm chart..."
helm install reliability-app deploy/helm/reliability \
  --set image.repository=reliability-agent-platform \
  --set image.tag=local \
  --set image.pullPolicy=Never

echo "Waiting for API deployment..."
kubectl wait --for=condition=available --timeout=60s deployment/reliability-app-api

echo "Running smoke test..."
kubectl port-forward svc/reliability-app 8000:8000 &
PF_PID=$!
sleep 3

curl -f http://localhost:8000/health && echo "Smoke test passed successfully!"
kill $PF_PID
