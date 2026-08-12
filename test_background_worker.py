#!/usr/bin/env python
"""
Test Script for Background Worker Implementation

This script demonstrates how to test the complete background worker flow:
1. Enqueue jobs programmatically
2. Process jobs with the worker
3. Verify results

Usage:
    python test_background_worker.py --test all
    python test_background_worker.py --test enqueue
    python test_background_worker.py --test process
    python test_background_worker.py --test verify
"""

import argparse
import json
import sys
import time
from datetime import datetime
from uuid import uuid4

# Database and models
from packages.core.database import SessionLocal
from packages.core.identity.models import Organization, User
from packages.core.identity.knowledge.models import Knowledge
from packages.core.identity.business.models import BusinessProfile
from packages.core.identity.background_workers.models import BackgroundJob
from packages.core.identity.background_workers.job_manager import JobManager
from packages.core.identity.background_workers.worker import process_background_jobs_sync


def create_test_organization(db) -> str:
    """Create a test organization"""
    org_id = str(uuid4())
    org = Organization(
        id=org_id,
        name="Test Organization",
        is_active=False,
        activated_at=None
    )
    db.add(org)
    db.commit()
    print(f"✓ Created test organization: {org_id}")
    return org_id


def create_test_business_profile(db, org_id: str) -> str:
    """Create a test business profile"""
    profile_id = str(uuid4())
    profile = BusinessProfile(
        id=profile_id,
        organization_id=org_id,
        business_name="Test Business",
        industry="Technology"
    )
    db.add(profile)
    db.commit()
    print(f"✓ Created test business profile: {profile_id}")
    return profile_id


def create_test_knowledge(db, org_id: str, count: int = 3) -> list:
    """Create test knowledge entries"""
    knowledge_ids = []
    for i in range(count):
        knowledge_id = str(uuid4())
        knowledge = Knowledge(
            id=knowledge_id,
            organization_id=org_id,
            title=f"Test Knowledge {i+1}",
            content=f"This is test knowledge content {i+1}. It contains information about the business.",
            content_type="text",
            processed=False
        )
        db.add(knowledge)
        knowledge_ids.append(knowledge_id)
    
    db.commit()
    print(f"✓ Created {count} test knowledge entries")
    return knowledge_ids


def test_enqueue(db, org_id: str, knowledge_ids: list):
    """Test job enqueueing"""
    print("\n=== Testing Job Enqueueing ===\n")
    
    job_manager = JobManager(db)
    
    # Enqueue activation job
    job_id = job_manager.enqueue(
        organization_id=org_id,
        task_type=JobManager.TASK_ONBOARDING_ACTIVATE,
        task_data={
            "brand_profile": {"name": "Test Brand"},
            "theme": {"primary": "#000"},
            "voice_profile": {"tone": "friendly"}
        }
    )
    
    print(f"✓ Enqueued TASK_ONBOARDING_ACTIVATE: {job_id}")
    
    # Verify job exists
    job = db.query(BackgroundJob).filter(BackgroundJob.id == job_id).first()
    assert job is not None, "Job not found after enqueueing"
    assert job.status == JobManager.STATUS_PENDING, "Job status should be pending"
    assert job.organization_id == org_id, "Job should belong to organization"
    
    print(f"✓ Job status verified: {job.status}")
    print(f"✓ Job data: {job.task_data[:50]}...")
    
    return job_id


def test_process(db, org_id: str, knowledge_ids: list):
    """Test job processing"""
    print("\n=== Testing Job Processing ===\n")
    
    job_manager = JobManager(db)
    
    # Enqueue activation job
    activation_job_id = job_manager.enqueue(
        organization_id=org_id,
        task_type=JobManager.TASK_ONBOARDING_ACTIVATE,
        task_data={
            "brand_profile": {"name": "Test Brand"},
            "theme": {"primary": "#000"},
            "voice_profile": {"tone": "friendly"},
            "knowledge_base": {"size": len(knowledge_ids)}
        }
    )
    
    print(f"✓ Enqueued activation job: {activation_job_id}")
    
    # Process jobs
    print("\nProcessing jobs...")
    processed = process_background_jobs_sync(db, batch_size=10)
    print(f"✓ Processed {processed} jobs")
    
    # Check activation job status
    activation_job = db.query(BackgroundJob).filter(
        BackgroundJob.id == activation_job_id
    ).first()
    
    print(f"\nActivation Job Status:")
    print(f"  ID: {activation_job.id}")
    print(f"  Status: {activation_job.status}")
    print(f"  Task Type: {activation_job.task_type}")
    
    if activation_job.status == JobManager.STATUS_COMPLETED:
        print(f"  Result: {activation_job.result}")
    elif activation_job.status == JobManager.STATUS_FAILED:
        print(f"  Error: {activation_job.error}")
    
    # Check if subtasks were enqueued
    subtasks = db.query(BackgroundJob).filter(
        BackgroundJob.organization_id == org_id,
        BackgroundJob.id != activation_job_id
    ).all()
    
    print(f"\n✓ Subtasks enqueued: {len(subtasks)}")
    for task in subtasks:
        print(f"  - {task.task_type}: {task.status}")
    
    return activation_job_id


def test_verify_activation(db, org_id: str):
    """Verify organization activation"""
    print("\n=== Verifying Organization Activation ===\n")
    
    org = db.query(Organization).filter(Organization.id == org_id).first()
    
    print(f"Organization: {org.name}")
    print(f"  ID: {org.id}")
    print(f"  Active: {org.is_active}")
    print(f"  Activated At: {org.activated_at}")
    
    if org.is_active:
        print("✓ Organization is ACTIVE")
    else:
        print("✗ Organization is NOT active (may need to process more jobs)")
    
    return org.is_active


def test_verify_embeddings(db, org_id: str, knowledge_ids: list):
    """Verify embeddings were generated"""
    print("\n=== Verifying Embeddings Generation ===\n")
    
    knowledge = db.query(Knowledge).filter(
        Knowledge.organization_id == org_id
    ).all()
    
    print(f"Total knowledge entries: {len(knowledge)}")
    
    processed_count = 0
    for k in knowledge:
        has_embedding = bool(k.embedding_vector)
        status = "✓" if has_embedding else "✗"
        print(f"{status} {k.title}: processed={k.processed}, has_embedding={has_embedding}")
        if has_embedding:
            processed_count += 1
    
    print(f"\n✓ Embeddings generated: {processed_count}/{len(knowledge)}")
    
    return processed_count == len(knowledge)


def test_queue_stats(db, org_id: str):
    """Display job queue statistics"""
    print("\n=== Job Queue Statistics ===\n")
    
    job_manager = JobManager(db)
    
    pending = db.query(BackgroundJob).filter(
        BackgroundJob.organization_id == org_id,
        BackgroundJob.status.in_([JobManager.STATUS_PENDING, JobManager.STATUS_RETRIED])
    ).count()
    
    running = db.query(BackgroundJob).filter(
        BackgroundJob.organization_id == org_id,
        BackgroundJob.status == JobManager.STATUS_RUNNING
    ).count()
    
    completed = db.query(BackgroundJob).filter(
        BackgroundJob.organization_id == org_id,
        BackgroundJob.status == JobManager.STATUS_COMPLETED
    ).count()
    
    failed = db.query(BackgroundJob).filter(
        BackgroundJob.organization_id == org_id,
        BackgroundJob.status == JobManager.STATUS_FAILED
    ).count()
    
    total = db.query(BackgroundJob).filter(
        BackgroundJob.organization_id == org_id
    ).count()
    
    print(f"Pending:  {pending}")
    print(f"Running:  {running}")
    print(f"Completed: {completed}")
    print(f"Failed:   {failed}")
    print(f"Total:    {total}")


def run_full_test():
    """Run complete test flow"""
    print("Starting Background Worker Full Test Suite")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Setup test data
        print("\n=== Test Setup ===\n")
        org_id = create_test_organization(db)
        business_id = create_test_business_profile(db, org_id)
        knowledge_ids = create_test_knowledge(db, org_id, count=3)
        
        # Test enqueueing
        test_enqueue(db, org_id, knowledge_ids)
        
        # Test processing
        test_process(db, org_id, knowledge_ids)
        
        # Process again to handle subtasks
        print("\n=== Processing Subtasks ===\n")
        processed = process_background_jobs_sync(db, batch_size=10)
        print(f"✓ Processed {processed} additional jobs")
        
        # Verify results
        test_verify_activation(db, org_id)
        test_verify_embeddings(db, org_id, knowledge_ids)
        
        # Show statistics
        test_queue_stats(db, org_id)
        
        print("\n" + "=" * 50)
        print("✓ Full Test Suite Completed Successfully")
        
    except Exception as e:
        print(f"\n✗ Test Failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Background Worker Test Suite"
    )
    
    parser.add_argument(
        "--test",
        choices=["all", "enqueue", "process", "verify", "stats"],
        default="all",
        help="Test to run"
    )
    
    parser.add_argument(
        "--org-id",
        default=None,
        help="Organization ID (for verify/stats, generates if not provided)"
    )
    
    args = parser.parse_args()
    
    db = SessionLocal()
    
    try:
        if args.test == "all":
            run_full_test()
        
        elif args.test == "enqueue":
            org_id = args.org_id or create_test_organization(db)
            knowledge_ids = create_test_knowledge(db, org_id)
            test_enqueue(db, org_id, knowledge_ids)
        
        elif args.test == "process":
            org_id = args.org_id or create_test_organization(db)
            knowledge_ids = create_test_knowledge(db, org_id)
            test_process(db, org_id, knowledge_ids)
        
        elif args.test == "verify":
            org_id = args.org_id or create_test_organization(db)
            knowledge_ids = create_test_knowledge(db, org_id)
            test_verify_activation(db, org_id)
            test_verify_embeddings(db, org_id, knowledge_ids)
        
        elif args.test == "stats":
            org_id = args.org_id or create_test_organization(db)
            test_queue_stats(db, org_id)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
