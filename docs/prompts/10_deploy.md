# Prompt 10: Deployment and security scans

Tag the start: `git tag milestone-10-start`. Study guide row 9 (Docker, Kubernetes basics) first.

```
Milestone 10: production-style deployment, all free and local. All earlier milestones must be done.

Build:
1. Harden deploy/docker/Dockerfile: pinned base image tag, non-root user (already there), no dev
   dependencies in the runtime image, a smaller final image. Report the image size before and after.
2. Compose: profiles for `core`, `observability` and `ollama`; health checks on every service; resource
   limits; secrets read from environment, never baked into images.
3. Helm chart in deploy/helm/reliability/: Deployments for api and worker, Service, ConfigMap, Secret
   (values supplied at install time, never committed), readiness and liveness probes, resource requests
   and limits, an optional HorizontalPodAutoscaler, a migration Job. `helm lint` must pass.
4. scripts/kind_up.sh: create a kind cluster, load the image, install Postgres (pgvector) and Redis
   using plain manifests in deploy/k8s/ or a documented chart, then helm install and run a smoke test.
5. CI additions in .github/workflows/: Bandit on Python code, Trivy scan of the image and dependencies,
   `helm lint`, and on pushes to main build and push the image to GitHub Container Registry using the
   built-in GITHUB_TOKEN. Add .github/dependabot.yml for pip, docker and github-actions.
6. docs/deploy.md: how to run each level (Compose, kind) and how to roll back a bad release with
   `helm rollback`.

Acceptance criteria: `docker compose up` works from a clean clone with only `.env` created;
`scripts/kind_up.sh` ends with a passing smoke test (document the exact command and output); CI is green
with the new jobs; no secrets in the repo (run a secret scan such as gitleaks if you can); docs updated.

Out of scope: any paid cloud. If a public demo is wanted, document options but do not implement them.
Commit message: feat: hardened image, helm chart, kind deploy and security scans in CI
```
