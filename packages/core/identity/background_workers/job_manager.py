"""
Background Job Queue Manager

Manages job enqueueing, status tracking, and queue processing.
Uses database-backed job queue for reliability.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from packages.core.identity.background_workers.models import BackgroundJob
from packages.core.logging import get_logger

logger = get_logger("job_manager")


class JobManager:
    """Manages background job queue and processing"""
    
    # Job status constants
    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_RETRIED = "retried"
    
    # Task type constants
    TASK_ONBOARDING_ACTIVATE = "onboarding_activate"
    TASK_GENERATE_EMBEDDINGS = "generate_embeddings"
    TASK_BUILD_AGENT_CONFIG = "build_agent_config"
    
    def __init__(self, db_session: Session):
        """
        Initialize job manager
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
    
    def enqueue(
        self,
        organization_id: str,
        task_type: str,
        task_data: Optional[Dict[str, Any]] = None,
        scheduled_at: Optional[datetime] = None,
        max_retries: int = 3
    ) -> str:
        """
        Enqueue a new background job
        
        Args:
            organization_id: Organization ID
            task_type: Type of task to perform
            task_data: Task-specific data as dict
            scheduled_at: When to run the job (default: now)
            max_retries: Maximum retry attempts
            
        Returns:
            Job ID
        """
        job_id = str(uuid4())
        scheduled_at = scheduled_at or datetime.utcnow()
        
        job = BackgroundJob(
            id=job_id,
            organization_id=organization_id,
            task_type=task_type,
            task_data=json.dumps(task_data) if task_data else None,
            status=self.STATUS_PENDING,
            retry_count=0,
            max_retries=max_retries,
            scheduled_at=scheduled_at,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        logger.info(
            "Job enqueued",
            extra={
                "job_id": job_id,
                "organization_id": organization_id,
                "task_type": task_type,
                "scheduled_at": scheduled_at.isoformat()
            }
        )
        
        return job_id
    
    def dequeue(self, batch_size: int = 10) -> List[BackgroundJob]:
        """
        Get pending jobs ready to process
        
        Args:
            batch_size: Maximum number of jobs to return
            
        Returns:
            List of pending BackgroundJob records
        """
        now = datetime.utcnow()
        
        jobs = self.db.query(BackgroundJob).filter(
            and_(
                BackgroundJob.status == self.STATUS_PENDING,
                BackgroundJob.scheduled_at <= now
            )
        ).order_by(BackgroundJob.created_at).limit(batch_size).all()
        
        # Mark jobs as running
        for job in jobs:
            job.status = self.STATUS_RUNNING
            job.started_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        logger.info(
            "Dequeued jobs",
            extra={
                "job_count": len(jobs),
                "batch_size": batch_size
            }
        )
        
        return jobs
    
    def mark_completed(self, job_id: str, result: Optional[Dict[str, Any]] = None) -> None:
        """
        Mark a job as completed
        
        Args:
            job_id: Job ID
            result: Optional result data
        """
        job = self.db.query(BackgroundJob).filter(BackgroundJob.id == job_id).first()
        if not job:
            logger.warning("Job not found for completion", extra={"job_id": job_id})
            return
        
        job.status = self.STATUS_COMPLETED
        job.completed_at = datetime.utcnow()
        job.result = json.dumps(result) if result else None
        job.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        logger.info(
            "Job completed",
            extra={
                "job_id": job_id,
                "organization_id": job.organization_id,
                "task_type": job.task_type
            }
        )
    
    def mark_failed(self, job_id: str, error: str, should_retry: bool = True) -> bool:
        """
        Mark a job as failed
        
        Args:
            job_id: Job ID
            error: Error message
            should_retry: Whether to retry the job
            
        Returns:
            True if job will be retried, False if max retries exceeded
        """
        job = self.db.query(BackgroundJob).filter(BackgroundJob.id == job_id).first()
        if not job:
            logger.warning("Job not found for failure marking", extra={"job_id": job_id})
            return False
        
        job.error = error
        job.updated_at = datetime.utcnow()
        
        # Check if we should retry
        if should_retry and job.retry_count < job.max_retries:
            job.retry_count += 1
            job.status = self.STATUS_RETRIED
            # Reschedule for retry in 60 seconds
            job.scheduled_at = datetime.utcnow() + timedelta(seconds=60)
            
            self.db.commit()
            
            logger.warning(
                "Job marked for retry",
                extra={
                    "job_id": job_id,
                    "organization_id": job.organization_id,
                    "retry_count": job.retry_count,
                    "max_retries": job.max_retries,
                    "error": error
                }
            )
            return True
        else:
            job.status = self.STATUS_FAILED
            job.completed_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.error(
                "Job failed permanently",
                extra={
                    "job_id": job_id,
                    "organization_id": job.organization_id,
                    "task_type": job.task_type,
                    "retry_count": job.retry_count,
                    "max_retries": job.max_retries,
                    "error": error
                }
            )
            return False
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a job
        
        Args:
            job_id: Job ID
            
        Returns:
            Job status info or None if not found
        """
        job = self.db.query(BackgroundJob).filter(BackgroundJob.id == job_id).first()
        if not job:
            return None
        
        return {
            "id": job.id,
            "status": job.status,
            "task_type": job.task_type,
            "retry_count": job.retry_count,
            "max_retries": job.max_retries,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error": job.error,
            "result": json.loads(job.result) if job.result else None
        }
    
    def get_pending_jobs(self, organization_id: str) -> List[BackgroundJob]:
        """
        Get all pending jobs for an organization
        
        Args:
            organization_id: Organization ID
            
        Returns:
            List of pending jobs
        """
        return self.db.query(BackgroundJob).filter(
            and_(
                BackgroundJob.organization_id == organization_id,
                BackgroundJob.status.in_([self.STATUS_PENDING, self.STATUS_RETRIED])
            )
        ).order_by(BackgroundJob.created_at).all()
    
    def cleanup_old_jobs(self, days: int = 30) -> int:
        """
        Clean up completed/failed jobs older than N days
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of jobs deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        deleted = self.db.query(BackgroundJob).filter(
            and_(
                BackgroundJob.completed_at < cutoff_date,
                BackgroundJob.status.in_([self.STATUS_COMPLETED, self.STATUS_FAILED])
            )
        ).delete()
        
        self.db.commit()
        
        logger.info(
            "Cleaned up old jobs",
            extra={
                "deleted_count": deleted,
                "days": days
            }
        )
        
        return deleted


def get_job_manager(db: Session) -> JobManager:
    """Get job manager instance"""
    return JobManager(db)
