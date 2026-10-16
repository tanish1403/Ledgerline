# Deployment & Operations Guide

This document describes how to deploy the Reliability Agent Platform using Docker Compose and Kubernetes (Kind / Helm), along with rollback instructions.

## 1. Docker Compose Deployment

Ensure `.env` is configured (see `.env.example`).

To run the core application stack:
```bash
docker compose --profile core up --build
```

To run with local Ollama model server:
```bash
docker compose --profile core --profile ollama up --build
```

To run observability stack (Prometheus, Grafana, Jaeger, OTel Collector):
```bash
docker compose -f docker-compose.yml -f deploy/compose/observability.yml --profile core --profile observability up --build
```

## 2. Kubernetes / Kind Deployment & Smoke Test

To spin up a local Kind cluster, load the hardened container image, deploy Postgres and Redis, install the Helm chart, and execute a smoke test:
```bash
bash scripts/kind_up.sh
```

## 3. Rolling Back a Bad Release with Helm

If a newly deployed Helm release exhibits regressions or failures, roll back instantly using:
```bash
helm rollback reliability-app
```
To roll back to a specific revision number:
```bash
helm rollback reliability-app 1
```

## 4. Docker Image Hardening Report
- **Base Image**: Pinned to `python:3.12-slim-bookworm`.
- **User**: Runs as non-root user `appuser` (UID 10001).
- **Dependencies**: Runtime image excludes build tools and `[dev]` dependencies, reducing image size by ~180MB.
