"""
Real-time job progress tracking with SSE event streaming.
Thread-safe, per-job state with event log for incremental frontend updates.
"""
import time
import json
import threading
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field, asdict


STAGE_ORDER = [
    "queued",
    "connecting",
    "fetching_info",
    "downloading",
    "parsing",
    "cleaning",
    "embedding",
    "clustering",
    "building_index",
    "analysis",
    "sentiment",
    "spam",
    "duplicates",
    "topics",
    "stats",
    "llm_analysis",
    "finalizing",
    "completed",
]

STAGE_LABELS = {
    "queued": "Queued",
    "connecting": "Connecting to source...",
    "fetching_info": "Fetching video information...",
    "downloading": "Downloading comments...",
    "parsing": "Parsing comments...",
    "cleaning": "Cleaning data...",
    "embedding": "Generating embeddings...",
    "clustering": "Clustering...",
    "building_index": "Building vector index...",
    "analysis": "Running analytics...",
    "sentiment": "Detecting sentiment...",
    "spam": "Detecting spam...",
    "duplicates": "Finding duplicate comments...",
    "topics": "Detecting topics...",
    "stats": "Calculating statistics...",
    "llm_analysis": "AI analysis...",
    "finalizing": "Finalizing report...",
    "completed": "Completed!",
    "error": "Error",
}


@dataclass
class ProgressState:
    job_id: str
    status: str = "queued"
    progress: float = 0.0
    stage: str = "queued"
    completed_stages: list = field(default_factory=list)
    stage_start_time: float = 0.0
    error: str = ""

    # Counters
    comments_downloaded: int = 0
    comments_processed: int = 0
    comments_analyzed: int = 0
    comments_failed: int = 0
    comments_skipped: int = 0
    comments_remaining: int = 0
    total_comments: int = 0

    # Metrics
    download_speed: float = 0.0
    process_speed: float = 0.0
    memory_mb: float = 0.0
    cpu_percent: float = 0.0

    # Activity log (timestamped)
    activities: list = field(default_factory=list)

    # Control
    cancel_requested: bool = False
    paused: bool = False

    # Event sequence (monotonic, for SSE consumers)
    event_seq: int = 0

    # Result (set when completed)
    result_ready: bool = False
    result_job_id: str = ""

    def to_dict(self):
        d = asdict(self)
        d["stage_label"] = STAGE_LABELS.get(self.stage, self.stage)
        d["elapsed"] = round(time.time() - self.stage_start_time, 1) if self.stage_start_time else 0
        return d


class ProgressTracker:
    """Thread-safe per-job progress tracking with event streaming."""

    def __init__(self):
        self._lock = threading.Lock()
        self._jobs: dict[str, ProgressState] = {}
        self._event_queues: dict[str, list] = {}  # job_id -> list of events

    def create_job(self, job_id: str) -> ProgressState:
        with self._lock:
            state = ProgressState(job_id=job_id, stage_start_time=time.time())
            self._jobs[job_id] = state
            self._event_queues[job_id] = []
            return state

    def get_state(self, job_id: str) -> Optional[ProgressState]:
        with self._lock:
            return self._jobs.get(job_id)

    def set_stage(self, job_id: str, stage: str):
        with self._lock:
            state = self._jobs.get(job_id)
            if not state:
                return
            if state.stage and state.stage not in state.completed_stages:
                state.completed_stages.append(state.stage)
            state.stage = stage
            state.stage_start_time = time.time()
            state.event_seq += 1
            self._emit(job_id, "stage", {
                "stage": stage,
                "stage_label": STAGE_LABELS.get(stage, stage),
                "completed_stages": list(state.completed_stages),
                "elapsed": round(time.time() - state.stage_start_time, 1),
            })

    def set_progress(self, job_id: str, progress: float):
        with self._lock:
            state = self._jobs.get(job_id)
            if not state:
                return
            state.progress = round(progress, 1)
            state.event_seq += 1
            self._emit(job_id, "progress", {"progress": state.progress})

    def set_status(self, job_id: str, status: str):
        with self._lock:
            state = self._jobs.get(job_id)
            if not state:
                return
            state.status = status
            state.event_seq += 1
            self._emit(job_id, "status", {"status": status})

    def set_error(self, job_id: str, error: str):
        with self._lock:
            state = self._jobs.get(job_id)
            if not state:
                return
            state.status = "error"
            state.error = error
            state.event_seq += 1
            self._emit(job_id, "error", {"error": error})

    def set_result_ready(self, job_id: str):
        with self._lock:
            state = self._jobs.get(job_id)
            if not state:
                return
            state.result_ready = True
            state.result_job_id = job_id
            state.event_seq += 1
            self._emit(job_id, "result", {"job_id": job_id})

    def set_counter(self, job_id: str, counter: str, value: int):
        with self._lock:
            state = self._jobs.get(job_id)
            if not state:
                return
            setattr(state, counter, value)
            state.event_seq += 1
            self._emit(job_id, "counter", {
                "counter": counter,
                "value": value,
                "comments_downloaded": state.comments_downloaded,
                "comments_processed": state.comments_processed,
                "comments_analyzed": state.comments_analyzed,
                "comments_failed": state.comments_failed,
                "comments_skipped": state.comments_skipped,
                "comments_remaining": state.comments_remaining,
            })

    def inc_counter(self, job_id: str, counter: str, delta: int = 1):
        with self._lock:
            state = self._jobs.get(job_id)
            if not state:
                return
            cur = getattr(state, counter, 0)
            setattr(state, counter, cur + delta)
            state.event_seq += 1
            self._emit(job_id, "counter", {
                "counter": counter,
                "value": cur + delta,
                "comments_downloaded": state.comments_downloaded,
                "comments_processed": state.comments_processed,
                "comments_analyzed": state.comments_analyzed,
                "comments_failed": state.comments_failed,
                "comments_skipped": state.comments_skipped,
                "comments_remaining": state.comments_remaining,
            })

    def add_activity(self, job_id: str, icon: str, message: str):
        with self._lock:
            state = self._jobs.get(job_id)
            if not state:
                return
            entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "icon": icon,
                "message": message,
            }
            state.activities.append(entry)
            state.event_seq += 1
            self._emit(job_id, "activity", entry)

    def set_metrics(self, job_id: str, metrics: dict):
        with self._lock:
            state = self._jobs.get(job_id)
            if not state:
                return
            for k, v in metrics.items():
                if hasattr(state, k):
                    setattr(state, k, v)
            state.event_seq += 1
            self._emit(job_id, "metrics", {
                "download_speed": state.download_speed,
                "process_speed": state.process_speed,
                "memory_mb": state.memory_mb,
                "cpu_percent": state.cpu_percent,
            })

    def request_cancel(self, job_id: str):
        with self._lock:
            state = self._jobs.get(job_id)
            if not state:
                return
            state.cancel_requested = True
            state.event_seq += 1
            self._emit(job_id, "control", {"cancel_requested": True})

    def is_cancelled(self, job_id: str) -> bool:
        with self._lock:
            state = self._jobs.get(job_id)
            return state.cancel_requested if state else False

    def request_pause(self, job_id: str):
        with self._lock:
            state = self._jobs.get(job_id)
            if not state:
                return
            state.paused = True
            state.event_seq += 1
            self._emit(job_id, "control", {"paused": True})

    def clear_cancel(self, job_id: str):
        with self._lock:
            state = self._jobs.get(job_id)
            if not state:
                return
            state.cancel_requested = False
            state.event_seq += 1

    def request_resume(self, job_id: str):
        with self._lock:
            state = self._jobs.get(job_id)
            if not state:
                return
            state.paused = False
            state.cancel_requested = False
            state.event_seq += 1
            self._emit(job_id, "control", {"paused": False})

    def _emit(self, job_id: str, event_type: str, data: dict):
        """Append event to the job's event queue for SSE consumers."""
        queue = self._event_queues.get(job_id)
        if queue is not None:
            queue.append({
                "type": event_type,
                "data": data,
                "seq": self._jobs[job_id].event_seq if job_id in self._jobs else 0,
            })
            # Keep max 1000 events in memory
            if len(queue) > 1000:
                queue[:500] = []

    def get_new_events(self, job_id: str, last_seq: int = 0) -> list:
        """Get events for a job since the given sequence number."""
        with self._lock:
            queue = self._event_queues.get(job_id, [])
            return [e for e in queue if e["seq"] > last_seq]

    def get_latest_seq(self, job_id: str) -> int:
        with self._lock:
            state = self._jobs.get(job_id)
            return state.event_seq if state else 0

    def cleanup(self, job_id: str):
        with self._lock:
            self._jobs.pop(job_id, None)
            self._event_queues.pop(job_id, None)


# Global singleton
tracker = ProgressTracker()
