# Production Deployment Guide

This guide takes the project from a clean clone to a production-grade cluster
serving 100,000+ users.

---

## 1. Prerequisites

- AWS account (or any cloud with managed Kubernetes)
- A managed PostgreSQL (or self-hosted on the cluster)
- A managed Redis (ElastiCache / Memorystore)
- Container registry (ECR / GCR / GHCR)
- DNS records for `app.mailguard.ai` pointing to your ingress
- TLS certificate (ACM / cert-manager + Let's Encrypt)

## 2. Provision infrastructure

Terraform module outline:

```hcl
module "mailguard" {
  source = "./infra"
  region = "ap-south-1"
  domain = "app.mailguard.ai"
  eks_version = "1.30"
  desired_capacity = 6
  db_instance_class = "db.r6g.2xlarge"
  redis_node_type = "cache.r6g.xlarge"
}
```

(For brevity, this skeleton is not committed — wire it to your Terraform
state. The K8s manifests in `infrastructure/k8s` are the source of truth for
workloads.)

## 3. Secrets

Create a k8s secret named `mailguard-secrets` in the `mailguard` namespace:

```bash
kubectl -n mailguard create secret generic mailguard-secrets \
  --from-literal=JWT_SECRET="$(openssl rand -hex 48)" \
  --from-literal=AES_SECRET="$(openssl rand -base64 32)" \
  --from-literal=DB_PASSWORD="$(openssl rand -hex 24)" \
  --from-literal=OPENAI_API_KEY="..." \
  --from-literal=GOOGLE_CLIENT_ID="..." \
  --from-literal=GOOGLE_CLIENT_SECRET="..." \
  --from-literal=MS_CLIENT_ID="..." \
  --from-literal=MS_CLIENT_SECRET="..." \
  --from-literal=WHATSAPP_TOKEN="..." \
  --from-literal=WHATSAPP_PHONE_ID="..." \
  --from-literal=TWILIO_ACCOUNT_SID="..." \
  --from-literal=TWILIO_AUTH_TOKEN="..."
```

(Replace `secrets.yaml` placeholders before applying the file directly.)

## 4. Apply manifests

```bash
kubectl apply -f infrastructure/k8s/namespace.yaml
kubectl apply -f infrastructure/k8s/configmap.yaml
kubectl apply -f infrastructure/k8s/secrets.yaml
kubectl apply -f infrastructure/k8s/postgres-statefulset.yaml
kubectl apply -f infrastructure/k8s/redis-deployment.yaml
kubectl apply -f infrastructure/k8s/backend-deployment.yaml
kubectl apply -f infrastructure/k8s/celery-worker-deployment.yaml
kubectl apply -f infrastructure/k8s/frontend-deployment.yaml
kubectl apply -f infrastructure/k8s/ingress.yaml
```

## 5. Run migrations

```bash
kubectl -n mailguard exec -it deploy/mailguard-api -- alembic upgrade head
```

(Or use a one-shot Job manifest for CI.)

## 6. Verify

```bash
curl -fsS https://app.mailguard.ai/health
curl -fsS https://app.mailguard.ai/api/v1/health
```

## 7. Observability

- Prometheus scrapes `/metrics` on the API.
- Sentry captures exceptions via `SENTRY_DSN` env var.
- Logs shipped via stdout → fluentbit → CloudWatch / OpenSearch.

## 8. Capacity planning (100k users)

- API: 8 replicas × 2 CPU = 16 CPU; ~3 GB RAM each.
- Workers: 12 replicas × 2 CPU = 24 CPU; auto-scaled by Celery queue depth.
- Postgres: db.r6g.2xlarge (8 vCPU, 64 GB RAM), 500 GB gp3.
- Redis: 3-node cluster, cache.r6g.large each.
- ChromaDB: 200 GB persistent volume, dedicated node group.

## 9. Disaster recovery

- Postgres: PITR enabled, daily snapshot.
- Redis: AOF + RDB.
- ChromaDB: rebuildable from Postgres (source of truth).
- Runbooks in `docs/runbooks/`.

## 10. CI/CD

- PRs run CI (lint + tests + docker build).
- Merges to `main` build, push images, and apply via ArgoCD / kubectl.
- Staging environment auto-deploys every PR.
