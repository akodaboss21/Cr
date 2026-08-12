# Deployment Runbook — Carai AI Receptionist

## Purpose
Quick runbook for deploying the backend and performing the initial production rollout.

## Prerequisites
- Production environment variables configured (DATABASE_URL, SECRET_KEY, SENTRY_DSN, STRIPE keys, SMTP settings)
- Database migrated and reachable
- Secrets stored in secret manager or environment
- Monitoring (Sentry DSN) configured if available

## Deploy Steps
1. Pull latest `main` branch and build container

```bash
git checkout main
git pull origin main
# Build image
docker build -t carai-receptionist:latest .
```

2. Run migrations (example using alembic)

```bash
# adjust for your migration tool
alembic upgrade head
```

3. Start the service (example)

```bash
docker run -e DATABASE_URL="$DATABASE_URL" -e SECRET_KEY="$SECRET_KEY" -e SENTRY_DSN="$SENTRY_DSN" -p 8000:8000 carai-receptionist:latest
```

4. Health check

```bash
curl -sS http://localhost:8000/health | jq
```

5. Verify logs and Sentry
- Check logs for errors
- Confirm Sentry events (if configured)

## Rollout Plan
- Stage 1: 10% of traffic for 24h
- Stage 2: 50% of traffic for 48h
- Stage 3: Full rollout

If errors > 1% or response latency p95 > 1s, rollback to previous image and investigate.

## Rollback
1. Stop current container
2. Start previous image tag
3. Notify stakeholders

## Contact Points
- On-call: backend-team@example.com
- SRE: sre-team@example.com

## Troubleshooting
- DB connection errors: check DATABASE_URL and network access
- Auth errors: validate SECRET_KEY and JWT configuration
- High error rate: check Sentry for stack traces

