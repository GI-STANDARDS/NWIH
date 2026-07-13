"""
Background worker that polls the database for pending jobs and processes them.
Can run as a separate process: python -m backend.queue.worker
"""
import time
import uuid
import threading
import signal
from datetime import datetime, timedelta

from backend.database.database import SessionLocal, init_db
from backend.database.models import Job
from backend.job_queue.tasks import task_extract_comments, task_clean_and_embed, task_cluster_and_analyze
from backend.config import MAX_COMMENTS_PER_JOB
from backend.progress import tracker as progress_tracker

JOB_TIMEOUT_MINUTES = 30  # max time a single job can run before being marked as error


def process_job(job_id: str, url: str, use_llm: bool = False):
    """Dispatch a job through the processing pipeline with live progress tracking."""
    # Initialize progress tracking
    progress_tracker.create_job(job_id)
    progress_tracker.set_stage(job_id, "connecting")
    progress_tracker.add_activity(job_id, "🔗", "Connecting to video source...")

    # Phase 1: Extract comments
    progress_tracker.set_stage(job_id, "downloading")
    progress_tracker.add_activity(job_id, "📥", "Starting comment download...")
    task_extract_comments(job_id, url, MAX_COMMENTS_PER_JOB)

    # Check if extraction failed or cancelled
    db = SessionLocal()
    try:
        j = db.query(Job).filter(Job.job_id == job_id).first()
        if j and j.status == "error":
            progress_tracker.set_error(job_id, j.error or "Extraction failed")
            progress_tracker.add_activity(job_id, "❌", f"Error: {j.error or 'Extraction failed'}")
            return
        if progress_tracker.is_cancelled(job_id):
            progress_tracker.add_activity(job_id, "⏹", "Cancelled by user")
            return
    finally:
        db.close()

    # Phase 2: Embeddings
    progress_tracker.set_stage(job_id, "embedding")
    progress_tracker.add_activity(job_id, "🧠", "Generating embeddings...")
    task_clean_and_embed(job_id)

    db = SessionLocal()
    try:
        j = db.query(Job).filter(Job.job_id == job_id).first()
        if j and j.status == "error":
            progress_tracker.set_error(job_id, j.error or "Embedding failed")
            progress_tracker.add_activity(job_id, "❌", f"Error: {j.error or 'Embedding failed'}")
            return
        if progress_tracker.is_cancelled(job_id):
            progress_tracker.add_activity(job_id, "⏹", "Cancelled by user")
            return
    finally:
        db.close()

    # Phase 3+4+5: Cluster (ML), optionally LLM, then finalize
    task_cluster_and_analyze(job_id, use_llm=use_llm)

    # Mark result ready for SSE
    db = SessionLocal()
    try:
        j = db.query(Job).filter(Job.job_id == job_id).first()
        if j and j.status == "completed":
            progress_tracker.set_result_ready(job_id)
    finally:
        db.close()


def worker_loop(poll_interval: int = 5):
    """Main worker loop - polls for pending jobs."""
    print(f"[worker] Started. Polling every {poll_interval}s")
    while True:
        try:
            db = SessionLocal()
            pending = db.query(Job).filter(
                Job.status.in_(["pending", "queued"])
            ).order_by(Job.created_at.asc()).first()

            if pending:
                # Read needed attributes BEFORE closing the session
                job_id = pending.job_id
                video_url = pending.video_url or ""
                video_title = pending.video_title or ""

                # Skip if cancelled before worker picked it up
                if progress_tracker.is_cancelled(job_id):
                    pending.status = "cancelled"
                    pending.updated_at = datetime.utcnow()
                    db.commit()
                    db.close()
                    continue

                print(f"[worker] Processing job {job_id}: {video_title or video_url}")
                pending.status = "processing"
                pending.updated_at = datetime.utcnow()
                db.commit()
                db.close()

                # Timeout guard — mark job as error if it exceeds the limit
                timeout_expired = False
                def mark_timed_out():
                    nonlocal timeout_expired
                    timeout_expired = True
                    try:
                        d2 = SessionLocal()
                        j2 = d2.query(Job).filter(Job.job_id == job_id).first()
                        if j2 and j2.status in ("processing", "extracting", "embedding", "clustering", "finalizing"):
                            j2.status = "error"
                            j2.error = f"Job timed out after {JOB_TIMEOUT_MINUTES} minutes"
                            j2.updated_at = datetime.utcnow()
                            d2.commit()
                        d2.close()
                    except Exception:
                        pass

                timer = threading.Timer(JOB_TIMEOUT_MINUTES * 60, mark_timed_out)
                timer.daemon = True
                timer.start()
                try:
                    process_job(job_id, video_url)
                finally:
                    timer.cancel()

                if timeout_expired:
                    print(f"[worker] Job {job_id} timed out")
                else:
                    print(f"[worker] Job {job_id} completed")
            else:
                db.close()
                time.sleep(poll_interval)
        except Exception as e:
            print(f"[worker] Error: {e}")
            time.sleep(poll_interval)


def start_worker_thread():
    """Start worker in a background thread (for development)."""
    t = threading.Thread(target=worker_loop, daemon=True)
    t.start()
    return t


if __name__ == "__main__":
    init_db()
    worker_loop()
