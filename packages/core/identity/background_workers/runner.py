"""
Background Worker CLI / Scheduled Task Runner

This module provides the entry point for running the background worker
process. Can be run as:
- Standalone worker: python -m packages.core.identity.background_workers.runner
- Scheduled job: Added to APScheduler
- CLI command: python worker_runner.py --run --batch-size 10
"""
import argparse
import asyncio
import logging
import time
import sys
from datetime import datetime

from packages.core.database import SessionLocal
from packages.core.identity.background_workers.job_manager import JobManager
from packages.core.identity.background_workers.worker import (
    process_background_jobs,
    process_background_jobs_sync
)
from packages.core.logging import get_logger

logger = get_logger("worker_runner")


def setup_logging(level: str = "INFO"):
    """Configure logging for worker process"""
    logging.basicConfig(
        level=getattr(logging, level),
        format='[%(asctime)s] %(levelname)s - %(name)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/tmp/carai_worker.log')
        ]
    )


def run_once(batch_size: int = 10) -> int:
    """
    Process one batch of jobs and exit
    
    Args:
        batch_size: Number of jobs to process
        
    Returns:
        Number of jobs processed
    """
    print(f"[{datetime.now().isoformat()}] Starting background worker (batch mode)")
    print(f"Batch size: {batch_size}")
    
    db = SessionLocal()
    try:
        processed = process_background_jobs_sync(db, batch_size)
        print(f"[{datetime.now().isoformat()}] Processed {processed} jobs")
        return processed
    except Exception as e:
        print(f"[ERROR] Failed to process jobs: {str(e)}")
        logger.exception("Worker error in batch mode")
        return 0
    finally:
        db.close()


def run_loop(batch_size: int = 10, poll_interval: int = 30, max_iterations: int = None):
    """
    Run worker in continuous loop mode
    
    Args:
        batch_size: Number of jobs to process per iteration
        poll_interval: Seconds to wait between polling
        max_iterations: Maximum iterations before exit (None = infinite)
    """
    print(f"[{datetime.now().isoformat()}] Starting background worker (loop mode)")
    print(f"Batch size: {batch_size}")
    print(f"Poll interval: {poll_interval}s")
    if max_iterations:
        print(f"Max iterations: {max_iterations}")
    print("Press Ctrl+C to stop")
    
    iteration = 0
    try:
        while True:
            iteration += 1
            
            if max_iterations and iteration > max_iterations:
                print(f"[{datetime.now().isoformat()}] Max iterations reached")
                break
            
            db = SessionLocal()
            try:
                print(f"\n[{datetime.now().isoformat()}] Iteration {iteration}")
                processed = process_background_jobs_sync(db, batch_size)
                
                # Get queue status
                job_manager = JobManager(db)
                # Print stats (requires query)
                
                if processed == 0:
                    print("No jobs to process, sleeping...")
                else:
                    print(f"Processed {processed} jobs")
            
            except Exception as e:
                print(f"[ERROR] {str(e)}")
                logger.exception("Worker error in loop mode")
            
            finally:
                db.close()
            
            # Sleep before next poll
            if iteration < (max_iterations or float('inf')):
                time.sleep(poll_interval)
    
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().isoformat()}] Worker stopped by user")
        sys.exit(0)


async def run_async_loop(batch_size: int = 10, poll_interval: int = 30):
    """
    Run worker in async loop mode (for integration with async frameworks)
    
    Args:
        batch_size: Number of jobs to process per iteration
        poll_interval: Seconds to wait between polling
    """
    print(f"[{datetime.now().isoformat()}] Starting background worker (async loop mode)")
    print(f"Batch size: {batch_size}")
    print(f"Poll interval: {poll_interval}s")
    
    try:
        while True:
            db = SessionLocal()
            try:
                print(f"[{datetime.now().isoformat()}] Processing batch...")
                processed = await process_background_jobs(db, batch_size)
                print(f"Processed {processed} jobs")
            except Exception as e:
                print(f"[ERROR] {str(e)}")
                logger.exception("Worker error in async loop mode")
            finally:
                db.close()
            
            await asyncio.sleep(poll_interval)
    
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().isoformat()}] Worker stopped by user")


def main():
    """Main entry point for worker CLI"""
    parser = argparse.ArgumentParser(
        description="Background Worker - Process asynchronous jobs"
    )
    
    parser.add_argument(
        "--mode",
        choices=["once", "loop", "async-loop"],
        default="once",
        help="Worker mode (once=single batch, loop=continuous polling)"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of jobs to process per batch (default: 10)"
    )
    
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=30,
        help="Seconds between polls in loop mode (default: 30)"
    )
    
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Maximum iterations for loop mode (default: infinite)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Run worker based on mode
    if args.mode == "once":
        run_once(args.batch_size)
    elif args.mode == "loop":
        run_loop(args.batch_size, args.poll_interval, args.max_iterations)
    elif args.mode == "async-loop":
        asyncio.run(run_async_loop(args.batch_size, args.poll_interval))


if __name__ == "__main__":
    main()
