"""
Background Workers Controller - API Endpoints

Provides endpoints for managing background jobs and workers
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime

from packages.core.database import get_db
from packages.core.security import get_current_user
from packages.core.identity.background_workers.models import BackgroundWorker, BackgroundJob
from packages.core.identity.background_workers.schemas import (
    BackgroundWorkerCreate, BackgroundWorkerUpdate, BackgroundWorkerResponse,
    BackgroundJobCreate, BackgroundJobUpdate, BackgroundJobResponse
)
from packages.core.identity.background_workers.job_manager import JobManager
from packages.core.identity.background_workers.worker import process_background_jobs_sync
from packages.core.logging import get_logger

logger = get_logger("background_workers_controller")

router = APIRouter(prefix="/background-workers", tags=["background-workers"])

# ============================================================================
# Worker Management Endpoints
# ============================================================================

@router.post("/workers/", response_model=BackgroundWorkerResponse)
async def create_background_worker(
    worker_create: BackgroundWorkerCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new background worker"""
    # Verify user has permission to create background worker
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Create background worker
    db_worker = BackgroundWorker(
        id=str(uuid4()),
        organization_id=current_user["organization_id"],
        name=worker_create.name,
        type=worker_create.type,
        config=worker_create.config,
        is_active=worker_create.is_active,
        status="idle",
        tasks_processed=0,
        tasks_failed=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_worker)
    db.commit()
    db.refresh(db_worker)
    
    logger.info(
        "Background worker created",
        extra={
            "worker_id": db_worker.id,
            "organization_id": current_user["organization_id"],
            "worker_type": worker_create.type
        }
    )
    
    return BackgroundWorkerResponse.from_orm(db_worker)


@router.get("/workers/", response_model=List[BackgroundWorkerResponse])
async def get_background_workers(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get a list of background workers for the organization"""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    workers = db.query(BackgroundWorker).filter(
        BackgroundWorker.organization_id == current_user["organization_id"]
    ).offset(skip).limit(limit).all()
    
    return [BackgroundWorkerResponse.from_orm(worker) for worker in workers]


@router.get("/workers/{worker_id}", response_model=BackgroundWorkerResponse)
async def get_background_worker(
    worker_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific background worker"""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    worker = db.query(BackgroundWorker).filter(
        BackgroundWorker.id == worker_id,
        BackgroundWorker.organization_id == current_user["organization_id"]
    ).first()
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Background worker not found"
        )
    
    return BackgroundWorkerResponse.from_orm(worker)


@router.put("/workers/{worker_id}", response_model=BackgroundWorkerResponse)
async def update_background_worker(
    worker_id: str,
    worker_update: BackgroundWorkerUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a background worker"""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    worker = db.query(BackgroundWorker).filter(
        BackgroundWorker.id == worker_id,
        BackgroundWorker.organization_id == current_user["organization_id"]
    ).first()
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Background worker not found"
        )
    
    # Update fields
    if worker_update.name is not None:
        worker.name = worker_update.name
    if worker_update.type is not None:
        worker.type = worker_update.type
    if worker_update.config is not None:
        worker.config = worker_update.config
    if worker_update.is_active is not None:
        worker.is_active = worker_update.is_active
    if worker_update.status is not None:
        worker.status = worker_update.status
    
    worker.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(worker)
    
    logger.info(
        "Background worker updated",
        extra={
            "worker_id": worker_id,
            "organization_id": current_user["organization_id"]
        }
    )
    
    return BackgroundWorkerResponse.from_orm(worker)


@router.delete("/workers/{worker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_background_worker(
    worker_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a background worker"""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    worker = db.query(BackgroundWorker).filter(
        BackgroundWorker.id == worker_id,
        BackgroundWorker.organization_id == current_user["organization_id"]
    ).first()
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Background worker not found"
        )
    
    db.delete(worker)
    db.commit()
    
    logger.info(
        "Background worker deleted",
        extra={
            "worker_id": worker_id,
            "organization_id": current_user["organization_id"]
        }
    )


# ============================================================================
# Job Management Endpoints
# ============================================================================

@router.get("/jobs/", response_model=List[BackgroundJobResponse])
async def get_background_jobs(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """Get background jobs for the organization"""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    query = db.query(BackgroundJob).filter(
        BackgroundJob.organization_id == current_user["organization_id"]
    )
    
    if status_filter:
        query = query.filter(BackgroundJob.status == status_filter)
    
    jobs = query.order_by(BackgroundJob.created_at.desc()).offset(skip).limit(limit).all()
    
    return [BackgroundJobResponse.from_orm(job) for job in jobs]


@router.get("/jobs/{job_id}", response_model=BackgroundJobResponse)
async def get_background_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific background job"""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    job = db.query(BackgroundJob).filter(
        BackgroundJob.id == job_id,
        BackgroundJob.organization_id == current_user["organization_id"]
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Background job not found"
        )
    
    return BackgroundJobResponse.from_orm(job)


# ============================================================================
# Worker Processing Endpoints
# ============================================================================

@router.post("/process", status_code=status.HTTP_200_OK)
async def process_jobs(
    batch_size: int = 10,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Manually trigger background job processing
    
    This endpoint processes pending jobs from the queue.
    Typically called by scheduled tasks or worker processes.
    
    Note: Only organization admins can trigger this
    """
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # TODO: Add admin check
    # if not current_user.get("is_admin"):
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Admin access required"
    #     )
    
    try:
        processed = process_background_jobs_sync(db, batch_size)
        
        logger.info(
            "Background jobs processed manually",
            extra={
                "organization_id": current_user["organization_id"],
                "processed_count": processed,
                "batch_size": batch_size
            }
        )
        
        return {
            "status": "success",
            "processed_count": processed,
            "batch_size": batch_size
        }
    
    except Exception as e:
        logger.exception(
            "Error processing background jobs",
            extra={
                "organization_id": current_user["organization_id"],
                "error": str(e)
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing jobs: {str(e)}"
        )


@router.post("/jobs/{job_id}/retry", response_model=BackgroundJobResponse)
async def retry_failed_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Manually retry a failed job"""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    job = db.query(BackgroundJob).filter(
        BackgroundJob.id == job_id,
        BackgroundJob.organization_id == current_user["organization_id"]
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Background job not found"
        )
    
    if job.status != "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only failed jobs can be retried"
        )
    
    # Reset job for retry
    job.status = "pending"
    job.retry_count = max(0, job.retry_count - 1)  # Don't count this manual retry against limit
    job.started_at = None
    job.completed_at = None
    job.error = None
    job.result = None
    job.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(job)
    
    logger.info(
        "Job marked for retry",
        extra={
            "job_id": job_id,
            "organization_id": current_user["organization_id"]
        }
    )
    
    return BackgroundJobResponse.from_orm(job)


# ============================================================================
# Job Statistics Endpoints
# ============================================================================

@router.get("/stats/summary", status_code=status.HTTP_200_OK)
async def get_job_statistics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get statistics on background jobs"""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    org_id = current_user["organization_id"]
    
    # Count jobs by status
    pending_count = db.query(BackgroundJob).filter(
        BackgroundJob.organization_id == org_id,
        BackgroundJob.status.in_(["pending", "retried"])
    ).count()
    
    running_count = db.query(BackgroundJob).filter(
        BackgroundJob.organization_id == org_id,
        BackgroundJob.status == "running"
    ).count()
    
    completed_count = db.query(BackgroundJob).filter(
        BackgroundJob.organization_id == org_id,
        BackgroundJob.status == "completed"
    ).count()
    
    failed_count = db.query(BackgroundJob).filter(
        BackgroundJob.organization_id == org_id,
        BackgroundJob.status == "failed"
    ).count()
    
    return {
        "organization_id": org_id,
        "pending": pending_count,
        "running": running_count,
        "completed": completed_count,
        "failed": failed_count,
        "total": pending_count + running_count + completed_count + failed_count
    }
