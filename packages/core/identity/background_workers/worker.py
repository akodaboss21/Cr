"""
Background Worker Processor

Processes background jobs from the queue.
Handles embeddings generation, agent configuration building, and activation.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy import select

from packages.core.logging import get_logger
from packages.core.identity.background_workers.job_manager import JobManager
from packages.core.identity.models import Organization
from packages.core.identity.knowledge.models import Knowledge
from packages.core.identity.business.models import BusinessProfile
from packages.core.ai.gateway import LLMGateway

logger = get_logger("background_worker")


class BackgroundWorker:
    """Processes background jobs from the queue"""
    
    def __init__(self, db_session: Session, job_manager: JobManager, llm_gateway: LLMGateway):
        """
        Initialize background worker
        
        Args:
            db_session: SQLAlchemy database session
            job_manager: Job manager instance
            llm_gateway: LLM gateway for embeddings
        """
        self.db = db_session
        self.job_manager = job_manager
        self.llm_gateway = llm_gateway
    
    async def process_jobs(self, batch_size: int = 10) -> int:
        """
        Process pending jobs from the queue
        
        Args:
            batch_size: Maximum number of jobs to process
            
        Returns:
            Number of jobs processed
        """
        jobs = self.job_manager.dequeue(batch_size)
        processed = 0
        
        for job in jobs:
            try:
                logger.info(
                    "Processing job",
                    extra={
                        "job_id": job.id,
                        "task_type": job.task_type,
                        "organization_id": job.organization_id
                    }
                )
                
                # Route to appropriate handler based on task type
                if job.task_type == JobManager.TASK_ONBOARDING_ACTIVATE:
                    await self._handle_onboarding_activate(job)
                elif job.task_type == JobManager.TASK_GENERATE_EMBEDDINGS:
                    await self._handle_generate_embeddings(job)
                elif job.task_type == JobManager.TASK_BUILD_AGENT_CONFIG:
                    await self._handle_build_agent_config(job)
                else:
                    raise ValueError(f"Unknown task type: {job.task_type}")
                
                processed += 1
            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                logger.exception(
                    "Job processing failed",
                    extra={
                        "job_id": job.id,
                        "task_type": job.task_type,
                        "organization_id": job.organization_id,
                        "error": error_msg
                    }
                )
                self.job_manager.mark_failed(job.id, error_msg, should_retry=True)
        
        logger.info(
            "Batch processing complete",
            extra={
                "batch_size": len(jobs),
                "processed": processed
            }
        )
        
        return processed
    
    async def _handle_onboarding_activate(self, job) -> None:
        """
        Handle onboarding activation job
        
        This is the main onboarding completion task that:
        1. Enqueues embedding generation for knowledge
        2. Enqueues agent configuration building
        3. Marks organization as active
        
        Args:
            job: BackgroundJob instance
        """
        task_data = json.loads(job.task_data) if job.task_data else {}
        organization_id = job.organization_id
        
        logger.info(
            "Starting onboarding activation",
            extra={
                "organization_id": organization_id,
                "job_id": job.id
            }
        )
        
        try:
            # Get organization
            org = self.db.query(Organization).filter(
                Organization.id == organization_id
            ).first()
            
            if not org:
                raise ValueError(f"Organization not found: {organization_id}")
            
            # Enqueue embedding generation job for all knowledge
            knowledge_entries = self.db.query(Knowledge).filter(
                Knowledge.organization_id == organization_id
            ).all()
            
            if knowledge_entries:
                logger.info(
                    "Enqueueing embedding generation",
                    extra={
                        "organization_id": organization_id,
                        "knowledge_count": len(knowledge_entries)
                    }
                )
                
                self.job_manager.enqueue(
                    organization_id=organization_id,
                    task_type=JobManager.TASK_GENERATE_EMBEDDINGS,
                    task_data={
                        "knowledge_ids": [k.id for k in knowledge_entries],
                        "parent_job_id": job.id
                    },
                    max_retries=3
                )
            
            # Enqueue agent configuration building
            logger.info(
                "Enqueueing agent config build",
                extra={
                    "organization_id": organization_id,
                    "job_id": job.id
                }
            )
            
            self.job_manager.enqueue(
                organization_id=organization_id,
                task_type=JobManager.TASK_BUILD_AGENT_CONFIG,
                task_data={
                    "parent_job_id": job.id
                },
                max_retries=3
            )
            
            # Mark this activation job as completed
            self.job_manager.mark_completed(
                job.id,
                result={
                    "status": "queued_subtasks",
                    "knowledge_count": len(knowledge_entries),
                    "organization_id": organization_id
                }
            )
            
            logger.info(
                "Onboarding activation queued subtasks",
                extra={
                    "organization_id": organization_id,
                    "job_id": job.id,
                    "knowledge_count": len(knowledge_entries)
                }
            )
        
        except Exception as e:
            raise
    
    async def _handle_generate_embeddings(self, job) -> None:
        """
        Generate embeddings for knowledge entries
        
        Args:
            job: BackgroundJob instance
        """
        task_data = json.loads(job.task_data) if job.task_data else {}
        organization_id = job.organization_id
        knowledge_ids = task_data.get("knowledge_ids", [])
        
        logger.info(
            "Starting embedding generation",
            extra={
                "organization_id": organization_id,
                "knowledge_count": len(knowledge_ids),
                "job_id": job.id
            }
        )
        
        # Fetch knowledge entries
        knowledge_entries = self.db.query(Knowledge).filter(
            Knowledge.id.in_(knowledge_ids),
            Knowledge.organization_id == organization_id
        ).all()
        
        if not knowledge_entries:
            logger.warning(
                "No knowledge entries found for embedding",
                extra={
                    "organization_id": organization_id,
                    "requested_ids": knowledge_ids
                }
            )
            self.job_manager.mark_completed(
                job.id,
                result={
                    "status": "no_knowledge",
                    "organization_id": organization_id
                }
            )
            return
        
        # Generate embeddings for all knowledge
        embedded_count = 0
        errors = []
        
        for knowledge in knowledge_entries:
            try:
                if knowledge.processed:
                    logger.debug(
                        "Knowledge already has embeddings",
                        extra={
                            "knowledge_id": knowledge.id,
                            "organization_id": organization_id
                        }
                    )
                    embedded_count += 1
                    continue
                
                # Combine title and content for embedding
                text_to_embed = f"{knowledge.title}\n{knowledge.content}"
                
                logger.debug(
                    "Generating embedding",
                    extra={
                        "knowledge_id": knowledge.id,
                        "text_length": len(text_to_embed)
                    }
                )
                
                # Generate embedding via LLM gateway
                response = await self.llm_gateway.embed(
                    texts=[text_to_embed],
                    model="text-embedding-3-small",
                    organization_id=organization_id
                )
                
                if response and getattr(response, "embeddings", None):
                    # Store embedding
                    knowledge.embedding_vector = json.dumps(response.embeddings[0])
                    knowledge.processed = True
                    knowledge.updated_at = datetime.utcnow()
                    embedded_count += 1
                    
                    logger.debug(
                        "Embedding generated successfully",
                        extra={
                            "knowledge_id": knowledge.id,
                            "embedding_size": len(response.embeddings[0])
                        }
                    )
            
            except Exception as e:
                error_msg = f"Failed to embed {knowledge.id}: {str(e)}"
                logger.exception(
                    error_msg,
                    extra={
                        "knowledge_id": knowledge.id,
                        "organization_id": organization_id
                    }
                )
                errors.append(error_msg)
        
        # Commit all changes
        self.db.commit()
        
        # Mark job as completed
        self.job_manager.mark_completed(
            job.id,
            result={
                "status": "completed",
                "embedded_count": embedded_count,
                "total_count": len(knowledge_entries),
                "errors": errors,
                "organization_id": organization_id
            }
        )
        
        logger.info(
            "Embedding generation completed",
            extra={
                "organization_id": organization_id,
                "embedded_count": embedded_count,
                "total_count": len(knowledge_entries),
                "error_count": len(errors),
                "job_id": job.id
            }
        )
    
    async def _handle_build_agent_config(self, job) -> None:
        """
        Build and finalize agent configuration
        
        Args:
            job: BackgroundJob instance
        """
        organization_id = job.organization_id
        
        logger.info(
            "Starting agent config build",
            extra={
                "organization_id": organization_id,
                "job_id": job.id
            }
        )
        
        try:
            # Get organization
            org = self.db.query(Organization).filter(
                Organization.id == organization_id
            ).first()
            
            if not org:
                raise ValueError(f"Organization not found: {organization_id}")
            
            # Get business profile
            business = self.db.query(BusinessProfile).filter(
                BusinessProfile.organization_id == organization_id
            ).first()
            
            if not business:
                raise ValueError(f"Business profile not found for org: {organization_id}")
            
            # Get all processed knowledge
            knowledge_entries = self.db.query(Knowledge).filter(
                Knowledge.organization_id == organization_id,
                Knowledge.processed.is_(True)
            ).all()
            
            # Build agent configuration
            agent_config = {
                "organization_id": organization_id,
                "business_id": business.id,
                "business_name": business.business_name or "",
                "knowledge_base_size": len(knowledge_entries),
                "knowledge_ids": [k.id for k in knowledge_entries],
                "created_at": datetime.utcnow().isoformat()
            }
            
            logger.info(
                "Agent configuration built",
                extra={
                    "organization_id": organization_id,
                    "config": agent_config,
                    "job_id": job.id
                }
            )
            
            # Store config in business profile or separate table
            # For now, we'll mark the organization as active
            org.is_active = True
            org.activated_at = datetime.utcnow()
            org.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Mark job as completed
            self.job_manager.mark_completed(
                job.id,
                result={
                    "status": "agent_configured",
                    "organization_id": organization_id,
                    "config": agent_config
                }
            )
            
            logger.info(
                "Agent configuration complete and organization activated",
                extra={
                    "organization_id": organization_id,
                    "is_active": True,
                    "activated_at": org.activated_at.isoformat(),
                    "job_id": job.id
                }
            )
        
        except Exception as e:
            raise


async def process_background_jobs(db: Session, batch_size: int = 10) -> int:
    """
    Process background jobs from the queue
    
    This is typically called from a scheduled task or worker process.
    
    Args:
        db: SQLAlchemy database session
        batch_size: Maximum jobs to process per batch
        
    Returns:
        Number of jobs processed
    """
    try:
        job_manager = JobManager(db)
        llm_gateway = LLMGateway()
        worker = BackgroundWorker(db, job_manager, llm_gateway)
        
        processed = await worker.process_jobs(batch_size)
        
        return processed
    
    except Exception as e:
        logger.exception(
            "Error in job processing loop",
            extra={"error": str(e)}
        )
        raise


# For synchronous CLI or scheduled tasks
def process_background_jobs_sync(db: Session, batch_size: int = 10) -> int:
    """
    Synchronous wrapper for background job processing
    
    Args:
        db: SQLAlchemy database session
        batch_size: Maximum jobs to process per batch
        
    Returns:
        Number of jobs processed
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(process_background_jobs(db, batch_size))
    finally:
        loop.close()
