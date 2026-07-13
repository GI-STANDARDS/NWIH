"""
AI Model Manager — self-contained llama.cpp inference with persistent state.
"""
import json
import os
import threading
import time
from pathlib import Path
from typing import Optional

from backend.config import MODEL_MANAGER_IDLE_TIMEOUT
from backend.llama_cpp.binary import get_binary_path, is_available as binary_available
from backend.llama_cpp.models import get_model_path, is_model_available
from backend.llama_cpp.server import ServerManager, LOADING_STATE_READY, LOADING_STATE_FAILED, LOADING_STATE_UNLOADED
from backend.logging_system import logs


STATE_FILE = Path(__file__).resolve().parent.parent / "data" / "model_state.json"


class ModelManager:
    def __init__(self, idle_timeout: int = MODEL_MANAGER_IDLE_TIMEOUT):
        self.idle_timeout = idle_timeout
        self._server = ServerManager()
        self._lock = threading.Lock()
        self._loaded_model: Optional[str] = None
        self._last_use: float = 0.0
        self._active: bool = False
        self._unload_timer: Optional[threading.Timer] = None
        self._restore_state()

    def status(self) -> dict:
        with self._lock:
            srv = self._server.get_status()
            return {
                "backend": "llama.cpp",
                "loaded": self._loaded_model is not None and self._server.is_running,
                "active": self._active,
                "server_running": srv["running"],
                "server_port": srv["port"],
                "model_name": Path(self._loaded_model).name if self._loaded_model else None,
                "binary_available": binary_available(),
                "model_available": is_model_available(),
                "idle_timeout": self.idle_timeout,
                "idle_remaining": max(0, self.idle_timeout - (time.time() - self._last_use)) if self._active else 0,
                "loading_state": srv["loading_state"],
                "loading_state_label": srv["loading_state_label"],
                "loading_error": srv["loading_error"],
                "uptime_seconds": srv["uptime_seconds"],
                "last_heartbeat": srv["last_heartbeat"],
                "loading_duration_seconds": srv.get("loading_duration_seconds"),
                "startup_logs": srv.get("startup_logs", []),
                "server_metrics": srv["metrics"],
            }

    def is_loaded(self) -> bool:
        return self._loaded_model is not None and self._server.is_running

    def is_ready(self) -> bool:
        return binary_available() and is_model_available()

    def load_model(self, model_path: str = "") -> bool:
        with self._lock:
            self._cancel_unload_timer()

            if self._server.is_running:
                if not model_path or model_path == self._loaded_model:
                    self._active = True
                    self._last_use = time.time()
                    return True
                self._server.stop()
                self._loaded_model = None

            # Resolve model path: if it's just a filename, look up via get_model_path
            if model_path:
                if not Path(model_path).is_absolute() and not model_path.startswith("."):
                    resolved = get_model_path(model_path)
                    path = str(resolved) if resolved else model_path
                else:
                    path = model_path
            else:
                path = str(get_model_path() or "")

            if not path or not Path(path).exists():
                logs.error("model_manager", "No model available",
                           {"fix": "Download a GGUF model or upload one."})
                return False

            ok = self._server.start(path)
            if ok:
                self._loaded_model = path
                self._active = True
                self._last_use = time.time()
                logs.info("model_manager", f"Loaded: {Path(path).name}")
                self._save_state()
            else:
                self._loaded_model = None
                self._active = False
                self._save_state()
            return ok

    def unload_model(self):
        with self._lock:
            self._cancel_unload_timer()
            self._server.stop()
            self._loaded_model = None
            self._active = False
            import gc
            gc.collect()
            logs.info("model_manager", "Model unloaded")
            self._save_state()

    def warm_up(self):
        with self._lock:
            if not self._server.is_running:
                return
            try:
                self._server.generate("Say 'ready' in one word.", max_tokens=10)
            except Exception:
                pass

    def generate(self, prompt: str, system: str = "",
                 temperature: float = 0.3, max_tokens: int = 2048) -> str:
        self._ensure_loaded()
        with self._lock:
            self._active = True
            self._last_use = time.time()
            result = self._server.generate(prompt, system, temperature, max_tokens)
            self._schedule_unload()
            return result

    def analyze_cluster(self, cluster_data: dict) -> dict:
        samples = "\n".join(f"- {s}" for s in cluster_data.get("sample_comments", [])[:5])
        prompt = f"""Analyze this cluster of comments and identify the main themes, pain points, requests, confusions, and opportunities.

Cluster: {cluster_data.get('label', 'Unknown')}
Size: {cluster_data.get('size', 0)} comments
Frequency: {cluster_data.get('frequency_pct', 0)}%
Sentiment: {cluster_data.get('sentiment_positive_pct', 0):.1f}% positive, {cluster_data.get('sentiment_negative_pct', 0):.1f}% negative

Sample comments:
{samples}

Return ONLY this JSON structure (no extra text):
{{
  "key_themes": "main topics discussed or null",
  "pain_point": "main problem described or null",
  "request": "main request or null",
  "confusion": "main confusion or uncertainty expressed or null",
  "opportunity": "potential opportunity or null",
  "hidden_need": "unstated underlying need or null",
  "urgency": "high|medium|low",
  "demand_score": 0-100
}}"""
        raw = self.generate(prompt)
        try:
            start = raw.find("{")
            end = raw.rfind("}")
            return json.loads(raw[start:end+1]) if start != -1 and end != -1 else {"error": "no JSON"}
        except (json.JSONDecodeError, ValueError):
            return {"pain_point": cluster_data.get("label", "Unknown")}

    def generate_insights(self, clusters_data: list) -> dict:
        summary = "\n".join(
            f"- {c.get('label', '?')}: {c.get('size', 0)} comments, demand {c.get('demand_score', 0)}"
            for c in clusters_data[:8]
        )
        prompt = f"""Based on these clustered comments, generate data-driven insights about user needs, confusion, and opportunities.

Clusters:
{summary}

Return ONLY this JSON:
{{
  "top_topics": ["topic1", "topic2", "topic3"],
  "top_pain_points": ["pain1", "pain2", "pain3"],
  "top_requests": ["request1", "request2", "request3"],
  "top_confusions": ["confusion1", "confusion2", "confusion3"],
  "opportunities": ["opportunity1", "opportunity2", "opportunity3"]
}}"""
        raw = self.generate(prompt)
        try:
            start = raw.find("{")
            end = raw.rfind("}")
            return json.loads(raw[start:end+1]) if start != -1 and end != -1 else {"error": "no JSON"}
        except (json.JSONDecodeError, ValueError):
            return {"error": "LLM parse failed"}

    def generate_roadmap(self, clusters_data: list) -> dict:
        summary = "\n".join(
            f"- {c.get('label', '?')}: {c.get('size', 0)} comments"
            for c in clusters_data[:5]
        )
        prompt = f"""Given these user comment clusters, suggest a product roadmap.

Clusters:
{summary}

Return ONLY this JSON:
{{
  "roadmap": [
    {{"version": "v1", "features": ["feat1","feat2"], "rationale": "why"}}
  ]
}}"""
        raw = self.generate(prompt)
        try:
            start = raw.find("{")
            end = raw.rfind("}")
            return json.loads(raw[start:end+1]) if start != -1 and end != -1 else {"error": "no JSON"}
        except (json.JSONDecodeError, ValueError):
            return {"roadmap": []}

    def _ensure_loaded(self):
        if not self.is_loaded():
            ok = self.load_model()
            if not ok:
                err = self._server.loading_error
                if err:
                    raise RuntimeError(f"{err['reason']}: {err['detail']}")
                raise RuntimeError("Failed to load AI model")

    def _schedule_unload(self):
        self._cancel_unload_timer()
        self._unload_timer = threading.Timer(self.idle_timeout, self._idle_unload)
        self._unload_timer.daemon = True
        self._unload_timer.start()

    def _cancel_unload_timer(self):
        if self._unload_timer:
            self._unload_timer.cancel()
            self._unload_timer = None

    def _idle_unload(self):
        with self._lock:
            elapsed = time.time() - self._last_use
            if elapsed >= self.idle_timeout:
                self._server.stop()
                self._loaded_model = None
                self._active = False
                self._unload_timer = None
                import gc
                gc.collect()
                self._save_state()

    def _save_state(self):
        try:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(STATE_FILE, "w") as f:
                json.dump({
                    "loaded_model": self._loaded_model,
                    "model_name": Path(self._loaded_model).name if self._loaded_model else None,
                    "timestamp": time.time(),
                }, f)
        except Exception:
            pass

    def _restore_state(self):
        try:
            if STATE_FILE.exists():
                with open(STATE_FILE) as f:
                    data = json.load(f)
                mp = data.get("loaded_model")
                if mp and Path(mp).exists():
                    self._loaded_model = mp
                    logs.info("model_manager", f"Restored state: {Path(mp).name}")
                    if self._server.is_running:
                        self._active = True
                        self._last_use = time.time()
        except Exception:
            pass


manager = ModelManager()
