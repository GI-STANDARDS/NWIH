"""
Optional Redis-backed job queue for production scalability.
When Redis is available, this replaces the DB polling worker.
Usage:
  from backend.job_queue.redis_queue import RedisQueue
  q = RedisQueue()
  q.enqueue(job_id, video_url)
  q.worker_loop()

Requires: pip install redis
"""
import json
import os
import time
from datetime import datetime
from typing import Optional

from backend.config import MAX_COMMENTS_PER_JOB

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_QUEUE_KEY = os.getenv("REDIS_QUEUE_KEY", "yt:jobs:queue")


class RedisQueue:
    """Redis-backed FIFO queue for job distribution across workers."""

    def __init__(self, host: str = REDIS_HOST, port: int = REDIS_PORT,
                 db: int = REDIS_DB, queue_key: str = REDIS_QUEUE_KEY):
        self.queue_key = queue_key
        self._available = False
        self._r = None
        try:
            import redis
            self._r = redis.Redis(host=host, port=port, db=db,
                                  decode_responses=True, socket_timeout=3)
            self._r.ping()
            self._available = True
        except Exception:
            pass

    def is_available(self) -> bool:
        return self._available

    def enqueue(self, job_id: str, video_url: str, max_comments: int = MAX_COMMENTS_PER_JOB):
        if not self._available:
            raise RuntimeError("Redis not available")
        payload = json.dumps({"job_id": job_id, "video_url": video_url,
                              "max_comments": max_comments, "enqueued_at": datetime.utcnow().isoformat()})
        self._r.rpush(self.queue_key, payload)

    def dequeue(self, timeout: int = 5) -> Optional[dict]:
        if not self._available:
            return None
        result = self._r.blpop(self.queue_key, timeout=timeout)
        if result:
            return json.loads(result[1])
        return None

    def queue_length(self) -> int:
        if not self._available:
            return 0
        return self._r.llen(self.queue_key)

    def clear(self):
        if self._available:
            self._r.delete(self.queue_key)

    def worker_loop(self):
        """Run worker loop consuming from Redis queue."""
        from backend.queue.worker import process_job
        from backend.database.database import init_db, SessionLocal
        from backend.database.models import Job

        init_db()
        print("[redis_worker] Started. Waiting for jobs...")

        while True:
            try:
                item = self.dequeue(timeout=5)
                if item:
                    jid = item["job_id"]
                    print(f"[redis_worker] Processing job {jid}")
                    db = SessionLocal()
                    job = db.query(Job).filter(Job.job_id == jid).first()
                    db.close()
                    if job:
                        process_job(job)
                    print(f"[redis_worker] Job {jid} completed")
            except Exception as e:
                print(f"[redis_worker] Error: {e}")
                time.sleep(5)
