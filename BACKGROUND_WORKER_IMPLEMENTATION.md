# Background Worker Implementation Guide

## Overview

The background worker system handles asynchronous job processing for onboarding completion and other long-running tasks. It uses a database-backed job queue with persistence for reliability.

## Architecture

### Components

1. **Job Manager** (`packages/core/identity/background_workers/job_manager.py`)
   - Manages job enqueueing, dequeuing, and status tracking
   - Uses SQLAlchemy to store jobs in the database
   - Provides retry logic with exponential backoff

2. **Background Worker** (`packages/core/identity/background_workers/worker.py`)
   - Processes jobs from the queue
   - Handles specific task types:
     - `TASK_ONBOARDING_ACTIVATE`: Main activation job
     - `TASK_GENERATE_EMBEDDINGS`: Generate embeddings for knowledge
     - `TASK_BUILD_AGENT_CONFIG`: Build agent configuration
   - Runs embedding generation via LLM Gateway

3. **Models** (`packages/core/identity/background_workers/models.py`)
   - `BackgroundWorker`: Represents a worker instance
   - `BackgroundJob`: Represents a single job in the queue

4. **API Controller** (`packages/core/identity/background_workers/controllers/__init__.py`)
   - REST endpoints for job management
   - Job processing triggers
   - Statistics and monitoring

## Job Flow

### Onboarding Completion Flow

```
User completes onboarding
  ↓
OnboardingService.complete_onboarding() called
  ↓
_activate_receptionist_async() enqueues TASK_ONBOARDING_ACTIVATE job
  ↓
BackgroundWorker.process_jobs() dequeues and processes
  ↓
_handle_onboarding_activate() enqueues:
  - TASK_GENERATE_EMBEDDINGS for all knowledge
  - TASK_BUILD_AGENT_CONFIG
  ↓
_handle_generate_embeddings() generates embeddings for each knowledge entry
  ↓
_handle_build_agent_config() activates organization (sets is_active=True)
```

## Database Schema

### BackgroundJob Table

```sql
CREATE TABLE background_jobs (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) FOREIGN KEY,
    worker_id VARCHAR(36) FOREIGN KEY (nullable),
    task_type VARCHAR(100) NOT NULL,
    task_data TEXT (JSON),
    status VARCHAR(20) DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    scheduled_at DATETIME NOT NULL,
    started_at DATETIME (nullable),
    completed_at DATETIME (nullable),
    result TEXT (JSON),
    error TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Organization Activation Fields

```sql
ALTER TABLE organizations ADD COLUMN is_active BOOLEAN DEFAULT FALSE;
ALTER TABLE organizations ADD COLUMN activated_at DATETIME NULL;
```

## Usage

### 1. Enqueue a Job

```python
from packages.core.identity.background_workers.job_manager import JobManager
from packages.core.database import SessionLocal

db = SessionLocal()
job_manager = JobManager(db)

job_id = job_manager.enqueue(
    organization_id="org_123",
    task_type=JobManager.TASK_ONBOARDING_ACTIVATE,
    task_data={
        "brand_profile": {...},
        "theme": {...}
    }
)
```

### 2. Process Jobs (Programmatic)

```python
from packages.core.identity.background_workers.worker import process_background_jobs_sync

processed = process_background_jobs_sync(db, batch_size=10)
print(f"Processed {processed} jobs")
```

### 3. Process Jobs (API Endpoint)

```bash
# Manual job processing trigger
curl -X POST http://localhost:8000/api/v1/background-workers/process \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

### 4. Monitor Job Status

```python
from packages.core.identity.background_workers.job_manager import JobManager

job_manager = JobManager(db)
status = job_manager.get_job_status(job_id)
print(status)
```

## Running the Worker

### Option 1: Scheduled Task (APScheduler)

```python
from apscheduler.schedulers.background import BackgroundScheduler
from packages.core.identity.background_workers.worker import process_background_jobs_sync
from packages.core.database import SessionLocal

scheduler = BackgroundScheduler()

def worker_job():
    db = SessionLocal()
    try:
        process_background_jobs_sync(db, batch_size=10)
    finally:
        db.close()

scheduler.add_job(worker_job, 'interval', seconds=30)
scheduler.start()
```

### Option 2: CLI Command

```bash
# Create a CLI command in main.py or separate worker.py
python -m packages.core.identity.background_workers.cli --process --batch-size 10
```

### Option 3: Long-running Worker Process

```python
import asyncio
import time
from packages.core.identity.background_workers.worker import process_background_jobs

async def worker_loop():
    while True:
        db = SessionLocal()
        try:
            await process_background_jobs(db, batch_size=10)
        finally:
            db.close()
        await asyncio.sleep(30)  # Poll every 30 seconds

if __name__ == "__main__":
    asyncio.run(worker_loop())
```

## Job Types and Handlers

### TASK_ONBOARDING_ACTIVATE

**When**: Called on onboarding completion
**Input**:
```json
{
  "brand_profile": {...},
  "theme": {...},
  "voice_profile": {...},
  "knowledge_base": {...}
}
```
**Actions**:
- Enqueues TASK_GENERATE_EMBEDDINGS
- Enqueues TASK_BUILD_AGENT_CONFIG

### TASK_GENERATE_EMBEDDINGS

**When**: Called as subtask of activation
**Input**:
```json
{
  "knowledge_ids": ["id1", "id2", ...],
  "parent_job_id": "job_uuid"
}
```
**Actions**:
- Fetches all knowledge entries
- Generates embeddings via LLM Gateway
- Stores embeddings in knowledge.embedding_vector
- Sets knowledge.processed = True

### TASK_BUILD_AGENT_CONFIG

**When**: Called after embeddings complete
**Input**:
```json
{
  "parent_job_id": "job_uuid"
}
```
**Actions**:
- Builds agent configuration from business profile
- Marks organization as active (is_active = True)
- Stores activated_at timestamp

## Error Handling

### Retry Logic

- Jobs automatically retry up to `max_retries` (default: 3)
- Failed jobs are rescheduled 60 seconds later
- Job status progression: `pending` → `running` → `completed|failed|retried`

### Manual Retry

```bash
# Retry a failed job via API
curl -X POST http://localhost:8000/api/v1/background-workers/jobs/{job_id}/retry \
  -H "Authorization: Bearer <token>"
```

### Error Tracking

All errors are logged with:
- Job ID
- Organization ID
- Task type
- Error message
- Retry count
- Max retries

## Monitoring

### Job Statistics

```bash
curl -X GET http://localhost:8000/api/v1/background-workers/stats/summary \
  -H "Authorization: Bearer <token>"
```

Response:
```json
{
  "organization_id": "org_123",
  "pending": 2,
  "running": 1,
  "completed": 45,
  "failed": 1,
  "total": 49
}
```

### Job Status

```bash
curl -X GET http://localhost:8000/api/v1/background-workers/jobs/{job_id} \
  -H "Authorization: Bearer <token>"
```

## Configuration

### Environment Variables

```bash
# Optional: Redis-backed queue (future enhancement)
# REDIS_URL=redis://localhost:6379

# Logging
LOG_LEVEL=INFO

# LLM Gateway (for embeddings)
OPENAI_API_KEY=sk-...
```

### Database Settings

The worker uses the same database as the main application (SQLite by default, PostgreSQL via Supabase).

## Future Enhancements

1. **Redis Queue Backend**: Replace SQLAlchemy queries with Redis for better performance
2. **Celery Integration**: Use Celery for distributed job processing
3. **Job Priorities**: Add priority levels for jobs
4. **Dead Letter Queue**: Separate queue for permanently failed jobs
5. **Job Chains**: Support job dependencies and chaining
6. **Worker Health Check**: Monitor worker status and auto-restart
7. **Prometheus Metrics**: Export job metrics for monitoring

## Troubleshooting

### Jobs Not Processing

1. Check if background worker is running:
   ```bash
   # Check scheduled task
   ps aux | grep python
   ```

2. Check job queue status:
   ```bash
   curl -X GET http://localhost:8000/api/v1/background-workers/stats/summary
   ```

3. Check for errors:
   ```bash
   # View recent job errors
   curl -X GET "http://localhost:8000/api/v1/background-workers/jobs?status_filter=failed"
   ```

### Embedding Generation Fails

1. Verify LLM Gateway is configured:
   ```bash
   echo $OPENAI_API_KEY
   ```

2. Check Knowledge entries have content:
   ```python
   db.query(Knowledge).filter(Knowledge.organization_id == "org_id").all()
   ```

### Memory Issues

1. Reduce batch size:
   ```python
   process_background_jobs_sync(db, batch_size=5)
   ```

2. Add cleanup job:
   ```python
   job_manager.cleanup_old_jobs(days=7)
   ```

## Integration Checklist

- [x] Database models created (BackgroundJob, BackgroundWorker)
- [x] Job manager implemented (enqueue, dequeue, status tracking)
- [x] Background worker processor implemented
- [x] Task handlers implemented (activation, embeddings, agent config)
- [x] Onboarding service integration
- [x] API endpoints for job management
- [x] Error handling and retry logic
- [ ] Scheduled task setup (APScheduler or Celery)
- [ ] Monitoring and metrics collection
- [ ] Production deployment testing

## Next Steps

1. Set up scheduled task to run worker periodically
2. Configure LLM Gateway for embeddings
3. Test end-to-end onboarding flow
4. Monitor job processing in production
5. Consider Redis optimization if needed
