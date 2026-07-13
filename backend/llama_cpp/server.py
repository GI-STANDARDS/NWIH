"""
llama-server subprocess manager with comprehensive health diagnostics, live metrics, and startup log capture.
"""
import json
import os
import socket
import subprocess
import sys
import time
import threading
from pathlib import Path
from typing import Optional

import httpx

from backend.config import LLAMA_CPP_N_CTX, LLAMA_CPP_N_THREADS, LLAMA_CPP_N_GPU_LAYERS
from backend.llama_cpp.binary import get_binary_path
from backend.llama_cpp.models import get_model_path, MODELS_DIR
from backend.logging_system import logs

# ─── Loading States ─────────────────────────────────────────────────────
LOADING_STATE_INIT = "initializing"
LOADING_STATE_TOKENIZER = "loading_tokenizer"
LOADING_STATE_MEMORY = "allocating_memory"
LOADING_STATE_WEIGHTS = "loading_weights"
LOADING_STATE_KV_CACHE = "building_kv_cache"
LOADING_STATE_READY = "ready"
LOADING_STATE_FAILED = "failed"
LOADING_STATE_UNLOADED = "unloaded"

LOADING_STATE_LABELS = {
    "initializing": "Initializing",
    "loading_tokenizer": "Loading tokenizer",
    "allocating_memory": "Allocating memory",
    "loading_weights": "Loading weights",
    "building_kv_cache": "Building KV cache",
    "ready": "Ready",
    "failed": "Failed",
    "unloaded": "Unloaded",
}


class LoadingError(Exception):
    def __init__(self, reason: str, detail: str = "", fix: str = ""):
        self.reason = reason
        self.detail = detail
        self.fix = fix
        super().__init__(f"{reason}: {detail}")


class ServerManager:
    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._port: int = 0
        self._model_path: Optional[str] = None
        self._lock = threading.Lock()
        self._loading_state: str = LOADING_STATE_UNLOADED
        self._loading_error: Optional[dict] = None
        self._start_time: float = 0.0
        self._ready_time: float = 0.0
        self._metrics: dict = {
            "tokens_per_sec": 0,
            "prompt_tokens": 0,
            "generated_tokens": 0,
            "context_used": 0,
            "context_remaining": 0,
            "active_requests": 0,
            "uptime_seconds": 0,
            "model_load_duration": 0,
        }
        self._last_heartbeat: float = 0.0
        self._startup_logs: list = []
        self._metrics_thread_running = False
        self._metrics_thread: Optional[threading.Thread] = None
        self._stderr_capture: list = []
        self._stderr_thread: Optional[threading.Thread] = None

    # ── Properties ──────────────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        if self._process is None:
            return False
        rc = self._process.poll()
        return rc is None

    @property
    def port(self) -> int:
        return self._port

    @property
    def loading_state(self) -> str:
        return self._loading_state

    @property
    def loading_error(self) -> Optional[dict]:
        return self._loading_error

    @property
    def startup_logs(self) -> list:
        return list(self._startup_logs)

    # ── Internal helpers ────────────────────────────────────────────────

    def _set_state(self, state: str):
        self._loading_state = state
        label = LOADING_STATE_LABELS.get(state, state)
        self._add_startup_log(label)
        logs.info("llama_server", f"State: {label}",
                   {"state": state, "model": Path(self._model_path).name if self._model_path else None})

    def _add_startup_log(self, message: str):
        self._startup_logs.append({"time": time.time(), "message": message})

    def _set_error(self, reason: str, detail: str = "", fix: str = ""):
        self._loading_state = LOADING_STATE_FAILED
        self._loading_error = {"reason": reason, "detail": detail, "fix": fix, "timestamp": time.time()}
        self._add_startup_log(f"ERROR: {reason} — {detail}")
        logs.error("llama_server", f"{reason}: {detail}", {"reason": reason, "fix": fix})

    def _find_free_port(self) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    def _is_port_open(self, port: int, host: str = "127.0.0.1") -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex((host, port)) == 0

    # ── Stderr capture thread ──────────────────────────────────────────

    def _capture_stderr(self):
        if not self._process or not self._process.stderr:
            return
        try:
            for line in iter(self._process.stderr.readline, ""):
                if not line:
                    break
                line = line.strip()
                if line:
                    self._stderr_capture.append(line)
                    if len(self._stderr_capture) > 500:
                        self._stderr_capture[:250] = []
        except (ValueError, OSError):
            pass

    # ── Live metrics polling ────────────────────────────────────────────

    def _poll_metrics_loop(self):
        """Background thread: polls llama-server /slots and /health every 2s."""
        while self.is_running:
            try:
                # Get slots info for active requests
                r = httpx.get(f"http://127.0.0.1:{self._port}/slots", timeout=3)
                if r.status_code == 200:
                    slots = r.json()
                    if isinstance(slots, list):
                        active = sum(1 for s in slots if s.get("state") == "active")
                        n_ctx = max((s.get("n_ctx", 0) for s in slots if s.get("n_ctx")), default=0)
                        n_past = max((s.get("n_past", 0) for s in slots if s.get("n_past")), default=0)
                        self._metrics["active_requests"] = active
                        self._metrics["context_used"] = n_past
                        self._metrics["context_remaining"] = max(0, n_ctx - n_past)
                        # Tokens from last generation
                        for s in slots:
                            if s.get("prompt_tokens"):
                                self._metrics["prompt_tokens"] = max(self._metrics["prompt_tokens"], s["prompt_tokens"])
                            if s.get("predicted_tokens"):
                                self._metrics["generated_tokens"] = max(self._metrics["generated_tokens"], s["predicted_tokens"])

                # Health check updates heartbeat
                r2 = httpx.get(f"http://127.0.0.1:{self._port}/health", timeout=2)
                if r2.status_code == 200:
                    self._last_heartbeat = time.time()

            except httpx.ConnectError:
                pass
            except Exception:
                pass
            time.sleep(2)

    # ── Core operations ─────────────────────────────────────────────────

    def start(self, model_path: str = "") -> bool:
        with self._lock:
            if self.is_running:
                if model_path and model_path != self._model_path:
                    self.stop()
                else:
                    self._set_state(LOADING_STATE_READY)
                    return True

            self._startup_logs = []
            self._stderr_capture = []
            self._set_state(LOADING_STATE_INIT)
            self._loading_error = None
            self._start_time = time.time()
            self._ready_time = 0
            self._metrics = {k: 0 for k in self._metrics}

            # Validate binary
            bin_path = get_binary_path()
            if not bin_path:
                self._set_error("Missing dependency", "llama.cpp binary not found",
                                "Go to AI Manager and download the llama.cpp binary.")
                return False

            # Validate model
            model = model_path or str(get_model_path() or "")
            if not model or not Path(model).exists():
                self._set_error("File not found", f"Model file not found: {model}",
                                "Download a GGUF model or browse for a local .gguf file.")
                return False

            self._set_state(LOADING_STATE_TOKENIZER)
            self._port = self._find_free_port()
            self._model_path = model

            # Build command
            gpu_layers = LLAMA_CPP_N_GPU_LAYERS
            ctx_size = LLAMA_CPP_N_CTX

            cmd = [
                str(bin_path),
                "--model", model,
                "--host", "127.0.0.1",
                "--port", str(self._port),
                "--ctx-size", str(ctx_size),
                "--threads", str(LLAMA_CPP_N_THREADS),
            ]

            if gpu_layers == 0:
                cmd.append("--no-cuda")
                self._add_startup_log("GPU disabled (--no-cuda)")
            else:
                ngl = gpu_layers if gpu_layers > 0 else 99
                cmd.extend(["--n-gpu-layers", str(ngl)])
                self._add_startup_log(f"Using GPU (--n-gpu-layers {ngl})")

            self._add_startup_log(f"Starting on port {self._port}")
            self._add_startup_log(f"Model: {Path(model).name}")
            self._add_startup_log(f"Context: {ctx_size}, Threads: {LLAMA_CPP_N_THREADS}")
            logs.info("llama_server", f"Starting on port {self._port} with {Path(model).name}",
                       {"cmd": " ".join(str(c) for c in cmd)})

            # Launch process
            try:
                self._process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                )
                # Start stderr capture thread
                self._stderr_thread = threading.Thread(target=self._capture_stderr, daemon=True)
                self._stderr_thread.start()
            except FileNotFoundError:
                self._set_error("Missing dependency", f"Binary not found at {bin_path}",
                                "Re-download the llama.cpp binary.")
                return False
            except Exception as e:
                self._set_error("Start failed", str(e), "Check system permissions.")
                return False

            # Wait for readiness (up to 60s)
            self._set_state(LOADING_STATE_MEMORY)
            self._set_state(LOADING_STATE_WEIGHTS)

            for i in range(120):  # 60s total
                if self._process.poll() is not None:
                    rc = self._process.returncode
                    stderr_text = "\n".join(self._stderr_capture[-20:])
                    if rc == -11:
                        self._set_error("Out of memory", f"Process crashed (SIGSEGV). "
                                        f"Last logs: {stderr_text[:500]}",
                                        "Reduce --ctx-size or use a smaller model.")
                    elif rc == -9:
                        self._set_error("Out of memory", f"Process killed (SIGKILL). "
                                        f"Last logs: {stderr_text[:500]}",
                                        "Reduce model size or increase system RAM.")
                    elif rc == -6:
                        self._set_error("Corrupted model", f"Process aborted (SIGABRT). "
                                        f"Last logs: {stderr_text[:500]}",
                                        "Re-download the GGUF model file.")
                    else:
                        self._set_error("Process exited", f"Exit code {rc}. "
                                        f"Last logs: {stderr_text[:500]}",
                                        "Check server logs for details.")
                    self._process = None
                    return False

                try:
                    r = httpx.get(f"http://127.0.0.1:{self._port}/health", timeout=2)
                    if r.status_code == 200:
                        self._set_state(LOADING_STATE_KV_CACHE)
                        time.sleep(0.3)
                        self._set_state(LOADING_STATE_READY)
                        self._ready_time = time.time()
                        self._last_heartbeat = time.time()
                        load_time = self._ready_time - self._start_time
                        self._metrics["model_load_duration"] = round(load_time, 1)
                        self._add_startup_log(f"Server ready in {load_time:.1f}s")
                        logs.info("llama_server", f"Ready (loaded in {load_time:.1f}s)")

                        # Start background metrics polling
                        if not self._metrics_thread_running:
                            self._metrics_thread_running = True
                            self._metrics_thread = threading.Thread(target=self._poll_metrics_loop, daemon=True)
                            self._metrics_thread.start()
                        return True
                except httpx.ConnectError:
                    if i == 30:
                        self._set_state(LOADING_STATE_KV_CACHE)
                        self._add_startup_log("Still loading (KV cache)...")
                except Exception:
                    pass
                time.sleep(0.5)

            self._set_error("Timeout", "Server did not become ready within 60s. "
                            f"Last stderr: {''.join(self._stderr_capture[-30:])[:500]}",
                            "Try a smaller model or reduce context size.")
            self.stop()
            return False

    def stop(self):
        with self._lock:
            if self._process:
                logs.info("llama_server", f"Stopping server on port {self._port}")
                try:
                    self._process.terminate()
                    self._process.wait(timeout=10)
                except Exception:
                    try:
                        self._process.kill()
                        self._process.wait(timeout=5)
                    except Exception:
                        pass
                self._process = None
                self._port = 0
                self._model_path = None
                self._set_state(LOADING_STATE_UNLOADED)
                self._last_heartbeat = 0.0
                self._metrics_thread_running = False

    # ── Comprehensive health check ─────────────────────────────────────

    def health_check(self) -> dict:
        """Full diagnostic across 8 dimensions. Never assumes state."""
        results = {
            "healthy": False,
            "checks": {},
            "summary": [],
        }

        # 1. Process running
        proc_running = self._process is not None and self._process.poll() is None
        results["checks"]["process_running"] = {
            "status": "pass" if proc_running else "fail",
            "detail": f"PID {self._process.pid}" if proc_running else "No process running",
        }

        # 2. Port reachable
        port_reachable = self._is_port_open(self._port) if self._port > 0 else False
        results["checks"]["port_reachable"] = {
            "status": "pass" if port_reachable else "fail",
            "detail": f"127.0.0.1:{self._port} is {'open' if port_reachable else 'closed'}",
        }

        # 3. API reachable
        api_reachable = False
        api_data = None
        if port_reachable:
            try:
                r = httpx.get(f"http://127.0.0.1:{self._port}/health", timeout=3)
                if r.status_code == 200:
                    api_reachable = True
                    api_data = r.json()
            except Exception as e:
                api_reachable = False
                api_data = str(e)
        results["checks"]["api_reachable"] = {
            "status": "pass" if api_reachable else "fail",
            "detail": f"Health endpoint: {'OK' if api_reachable else str(api_data)}",
        }

        # 4. Model loaded
        model_loaded = self._model_path is not None and Path(self._model_path).exists()
        results["checks"]["model_loaded"] = {
            "status": "pass" if model_loaded else "fail",
            "detail": Path(self._model_path).name if model_loaded else "No model path configured",
        }

        # 5. Context initialized (query /slots)
        context_ok = False
        if api_reachable:
            try:
                r = httpx.get(f"http://127.0.0.1:{self._port}/slots", timeout=3)
                if r.status_code == 200:
                    slots = r.json()
                    context_ok = isinstance(slots, list) and len(slots) > 0
            except Exception:
                pass
        results["checks"]["context_initialized"] = {
            "status": "pass" if context_ok else "info",
            "detail": "Server slots allocated" if context_ok else "Server running, awaiting first request",
        }

        # 6. Disk accessible
        models_dir = MODELS_DIR
        disk_ok = models_dir.exists()
        results["checks"]["disk_accessible"] = {
            "status": "pass" if disk_ok else "fail",
            "detail": f"Models directory: {models_dir} {'exists' if disk_ok else 'missing'}",
        }

        # 7. Binary exists
        bin_path = get_binary_path()
        bin_ok = bin_path is not None and Path(bin_path).exists()
        results["checks"]["binary_exists"] = {
            "status": "pass" if bin_ok else "fail",
            "detail": f"llama.cpp binary: {bin_path or 'not found'}",
        }

        # 8. Configuration valid
        config_ok = True
        config_issues = []
        if LLAMA_CPP_N_CTX < 128:
            config_issues.append(f"Context size too small: {LLAMA_CPP_N_CTX}")
            config_ok = False
        if LLAMA_CPP_N_THREADS < 1:
            config_issues.append(f"Invalid thread count: {LLAMA_CPP_N_THREADS}")
            config_ok = False
        results["checks"]["configuration_valid"] = {
            "status": "pass" if config_ok else "fail",
            "detail": "; ".join(config_issues) if config_issues else f"ctx={LLAMA_CPP_N_CTX}, threads={LLAMA_CPP_N_THREADS}, gpu_layers={LLAMA_CPP_N_GPU_LAYERS}",
        }

        # Overall
        critical = ["process_running", "port_reachable", "api_reachable", "model_loaded", "disk_accessible", "binary_exists"]
        passed = all(results["checks"][c]["status"] == "pass" for c in critical)
        if api_reachable:
            self._last_heartbeat = time.time()
        results["healthy"] = passed
        results["summary"] = [f"{k}: {v['status']}" for k, v in results["checks"].items()]
        return results

    # ── Inference ──────────────────────────────────────────────────────

    def generate(self, prompt: str, system: str = "",
                 temperature: float = 0.3, max_tokens: int = 2048) -> str:
        if not self.is_running:
            raise RuntimeError("Server not running")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        try:
            self._metrics["active_requests"] += 1
            r = httpx.post(
                f"http://127.0.0.1:{self._port}/v1/chat/completions",
                json=payload,
                timeout=120,
            )
            r.raise_for_status()
            data = r.json()
            usage = data.get("usage", {})
            self._metrics["prompt_tokens"] += usage.get("prompt_tokens", 0)
            self._metrics["generated_tokens"] += usage.get("completion_tokens", 0)
            if usage.get("completion_tokens", 0) > 0 and usage.get("prompt_tokens", 0) > 0:
                self._metrics["tokens_per_sec"] = round(
                    usage["completion_tokens"] / max(usage.get("time", 1), 1) * 1000, 1
                )
            return data["choices"][0]["message"]["content"].strip()
        except httpx.TimeoutException:
            raise RuntimeError("Timeout: Request exceeded 120s")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 503:
                raise RuntimeError("Out of memory: Context window full")
            raise RuntimeError(f"HTTP {e.response.status_code}: {e.response.text[:200]}")
        except Exception as e:
            raise RuntimeError(f"llama-server inference failed: {e}")
        finally:
            self._metrics["active_requests"] = max(0, self._metrics["active_requests"] - 1)

    # ── Status ─────────────────────────────────────────────────────────

    def get_status(self) -> dict:
        running = self.is_running
        now = time.time()
        uptime = now - self._start_time if running and self._start_time > 0 else 0
        load_duration = self._ready_time - self._start_time if self._ready_time > 0 else 0
        return {
            "running": running,
            "port": self._port,
            "model": self._model_path,
            "model_name": Path(self._model_path).name if self._model_path else None,
            "loading_state": self._loading_state,
            "loading_state_label": LOADING_STATE_LABELS.get(self._loading_state, self._loading_state),
            "loading_error": self._loading_error,
            "uptime_seconds": round(uptime, 1) if running else 0,
            "last_heartbeat": self._last_heartbeat,
            "loading_duration_seconds": round(load_duration, 1) if load_duration > 0 else None,
            "metrics": dict(self._metrics) if running else {},
            "startup_logs": self._startup_logs[-50:],
            "stderr_tail": self._stderr_capture[-20:],
        }
