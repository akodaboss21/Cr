"""
Background Worker Setup Guide

Instructions for integrating the background worker into the FastAPI application
and setting up job processing.
"""

# ============================================================================
# OPTION 1: APScheduler Integration (Recommended for Simple Setup)
# ============================================================================

# In apps/api/backend/main.py:

"""
from apscheduler.schedulers.background import BackgroundScheduler
from packages.core.identity.background_workers.worker import process_background_jobs_sync
from packages.core.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

def init_background_worker(app):
    \"\"\"Initialize background worker scheduler\"\"\"
    scheduler = BackgroundScheduler()
    
    def worker_task():
        db = SessionLocal()
        try:
            logger.info("Background worker processing jobs...")
            processed = process_background_jobs_sync(db, batch_size=10)
            logger.info(f"Processed {processed} background jobs")
        except Exception as e:
            logger.exception(f"Background worker error: {e}")
        finally:
            db.close()
    
    # Process jobs every 30 seconds
    scheduler.add_job(worker_task, 'interval', seconds=30)
    scheduler.start()
    
    # Shutdown scheduler with app
    def shutdown_scheduler(signum, frame):
        scheduler.shutdown()
    
    import atexit
    atexit.register(lambda: scheduler.shutdown())
    
    return scheduler


# In app startup:
@app.on_event("startup")
async def startup_event():
    init_background_worker(app)
"""

# ============================================================================
# OPTION 2: Separate Worker Process (Recommended for Production)
# ============================================================================

# Install dependencies:
# pip install apscheduler

# Create a separate worker script: worker.py
"""
#!/usr/bin/env python
import sys
sys.path.insert(0, '.')

from packages.core.identity.background_workers.runner import main

if __name__ == '__main__':
    main()
"""

# Run the worker in a separate terminal or via systemd/supervisor:
# python worker.py --mode loop --batch-size 10 --poll-interval 30

# Or as a systemd service:
"""
[Unit]
Description=Carai Background Worker
After=network.target

[Service]
Type=simple
User=carai
WorkingDirectory=/path/to/carai
ExecStart=python worker.py --mode loop --batch-size 10 --poll-interval 30
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

# ============================================================================
# OPTION 3: Celery Integration (Recommended for Large Scale)
# ============================================================================

# Install dependencies:
# pip install celery redis

# In packages/core/identity/background_workers/celery_worker.py:
"""
from celery import Celery
from packages.core.database import SessionLocal
from packages.core.identity.background_workers.worker import process_background_jobs_sync

app = Celery(
    'carai_workers',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)

@app.task
def process_jobs(batch_size=10):
    db = SessionLocal()
    try:
        return process_background_jobs_sync(db, batch_size)
    finally:
        db.close()

# In FastAPI app startup:
from celery.schedules import schedule
app.conf.beat_schedule = {
    'process-background-jobs': {
        'task': 'packages.core.identity.background_workers.celery_worker.process_jobs',
        'schedule': 30.0,  # Every 30 seconds
        'kwargs': {'batch_size': 10}
    },
}
"""

# Run Celery worker:
# celery -A packages.core.identity.background_workers.celery_worker worker --loglevel=info

# Run Celery beat scheduler:
# celery -A packages.core.identity.background_workers.celery_worker beat --loglevel=info

# ============================================================================
# SETUP CHECKLIST
# ============================================================================

"""
1. Database Setup
   [ ] Run migrations to create background_jobs and background_workers tables
   [ ] Add is_active and activated_at columns to organizations table
   
   Migration SQL:
   
   CREATE TABLE background_jobs (
       id VARCHAR(36) PRIMARY KEY,
       organization_id VARCHAR(36) NOT NULL,
       worker_id VARCHAR(36),
       task_type VARCHAR(100) NOT NULL,
       task_data TEXT,
       status VARCHAR(20) DEFAULT 'pending',
       retry_count INTEGER DEFAULT 0,
       max_retries INTEGER DEFAULT 3,
       scheduled_at DATETIME NOT NULL,
       started_at DATETIME,
       completed_at DATETIME,
       result TEXT,
       error TEXT,
       created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
       updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
       FOREIGN KEY (organization_id) REFERENCES organizations(id)
   );
   
   ALTER TABLE organizations ADD COLUMN is_active BOOLEAN DEFAULT FALSE;
   ALTER TABLE organizations ADD COLUMN activated_at DATETIME;

2. Code Integration
   [ ] Choose worker mode (APScheduler, Separate Process, or Celery)
   [ ] Update main.py with startup/shutdown handlers
   [ ] Test job enqueueing from onboarding service
   
3. Configuration
   [ ] Set LOG_LEVEL environment variable
   [ ] Configure OPENAI_API_KEY for embeddings
   [ ] Set poll interval and batch size based on load
   
4. Testing
   [ ] Test manual job processing: POST /api/v1/background-workers/process
   [ ] Monitor job statistics: GET /api/v1/background-workers/stats/summary
   [ ] Complete onboarding flow and verify activation
   [ ] Check organization.is_active is set to True
   [ ] Verify embeddings are generated for knowledge
   
5. Monitoring
   [ ] Set up logging aggregation
   [ ] Monitor /tmp/carai_worker.log
   [ ] Create alerts for failed jobs
   [ ] Set up metrics collection
   
6. Production Deployment
   [ ] Use separate worker process, not embedded APScheduler
   [ ] Run multiple workers for redundancy
   [ ] Set up load balancing for API and worker processes
   [ ] Use Redis for job queue (future enhancement)
   [ ] Monitor worker health and auto-restart
"""

# ============================================================================
# QUICK START: APScheduler in FastAPI
# ============================================================================

"""
1. Install: pip install apscheduler

2. Add to main.py:

from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from packages.core.identity.background_workers.worker import process_background_jobs_sync
from packages.core.database import SessionLocal
import logging

app = FastAPI()
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup():
    scheduler = BackgroundScheduler()
    
    def worker_task():
        db = SessionLocal()
        try:
            process_background_jobs_sync(db, batch_size=10)
        finally:
            db.close()
    
    scheduler.add_job(worker_task, 'interval', seconds=30, id='bg_worker')
    scheduler.start()
    app.state.scheduler = scheduler
    logger.info("Background worker started")

@app.on_event("shutdown")
async def shutdown():
    if hasattr(app.state, 'scheduler'):
        app.state.scheduler.shutdown()
        logger.info("Background worker stopped")

3. Test:
   - Complete onboarding flow
   - Check jobs are being processed
   - Monitor /tmp/carai_worker.log
"""

# ============================================================================
# TESTING THE WORKER
# ============================================================================

"""
1. Test Manual Processing:

curl -X POST http://localhost:8000/api/v1/background-workers/process \\
  -H "Authorization: Bearer <token>" \\
  -H "Content-Type: application/json"

Expected response:
{
  "status": "success",
  "processed_count": 5,
  "batch_size": 10
}

2. Test Job Status:

curl -X GET http://localhost:8000/api/v1/background-workers/jobs?status_filter=completed \\
  -H "Authorization: Bearer <token>"

3. Test Statistics:

curl -X GET http://localhost:8000/api/v1/background-workers/stats/summary \\
  -H "Authorization: Bearer <token>"

4. End-to-End Test:

python -c "
from packages.core.branding.onboarding_service import OnboardingService
from packages.core.database import SessionLocal

db = SessionLocal()
service = OnboardingService(db)
service.initialize_services()

# Simulate onboarding completion
result = service.complete_onboarding('onboarding_id')
print('Activation job enqueued:', result)

# Process the queued jobs
from packages.core.identity.background_workers.worker import process_background_jobs_sync
processed = process_background_jobs_sync(db, batch_size=10)
print(f'Processed {processed} jobs')

# Check organization status
from packages.core.identity.models import Organization
org = db.query(Organization).filter_by(id='org_id').first()
print(f'Organization active: {org.is_active}, activated at: {org.activated_at}')
"
"""

# ============================================================================
# TROUBLESHOOTING
# ============================================================================

"""
Issue: Jobs not processing
Solution:
1. Check if worker is running: ps aux | grep worker.py
2. Check job queue: curl http://localhost:8000/api/v1/background-workers/stats/summary
3. Check logs: tail -f /tmp/carai_worker.log
4. Try manual processing: curl -X POST http://localhost:8000/api/v1/background-workers/process

Issue: Embeddings generation fails
Solution:
1. Verify OPENAI_API_KEY is set
2. Check Knowledge has content
3. Check LLMGateway logs for API errors
4. Test embedding manually:
   from packages.core.ai.gateway import LLMGateway
   gateway = LLMGateway()
   response = await gateway.embed(["test text"])

Issue: Jobs stuck in "running" state
Solution:
1. Check if worker crashed
2. Manually mark job as failed and retry:
   curl -X POST http://localhost:8000/api/v1/background-workers/jobs/{job_id}/retry
3. Clean up old jobs:
   python -c "
   from packages.core.database import SessionLocal
   from packages.core.identity.background_workers.job_manager import JobManager
   db = SessionLocal()
   jm = JobManager(db)
   deleted = jm.cleanup_old_jobs(days=7)
   print(f'Deleted {deleted} old jobs')
   "

Issue: Memory usage increasing
Solution:
1. Reduce batch size: --batch-size 5
2. Clean up old jobs more frequently
3. Run multiple workers with smaller batch sizes
4. Monitor with: top -p $(pgrep -f worker.py)
"""

# ============================================================================
# PRODUCTION BEST PRACTICES
# ============================================================================

"""
1. Worker Redundancy
   - Run at least 2 worker processes
   - Use separate servers if possible
   - Load balancer to distribute jobs

2. Monitoring
   - Log all job processing
   - Alert on job failures
   - Track job processing time
   - Monitor worker process health

3. Configuration
   - Use environment variables for all settings
   - Set appropriate batch sizes
   - Tune poll intervals based on load
   - Set reasonable max_retries

4. Database
   - Index on status and scheduled_at
   - Clean up old jobs regularly
   - Use connection pooling

5. Error Handling
   - Implement dead letter queue
   - Log full stack traces
   - Notify on critical failures
   - Implement circuit breakers

6. Scaling
   - Use Redis for queue (future)
   - Implement Celery for distributed processing
   - Use message queue for high volume
   - Consider serverless functions (AWS Lambda)
"""
