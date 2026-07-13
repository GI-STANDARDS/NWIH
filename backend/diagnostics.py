"""
System diagnostics â€” CPU, RAM, GPU, VRAM, driver detection with dependency help.
"""
import os
import sys
import time
import threading
import subprocess
from typing import Optional

# â”€â”€â”€ psutil detection with install instructions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
try:
    import psutil
    HAS_PSUTIL = True
    PSUTIL_INSTALL = ""
except ImportError:
    HAS_PSUTIL = False
    PSUTIL_INSTALL = "pip install psutil"

# â”€â”€â”€ GPU cache â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_cached_gpu: Optional[dict] = None
_last_gpu_check: float = 0
_gpu_lock = threading.Lock()


def _run_nvidia_smi(*args, timeout=5):
    try:
        r = subprocess.run(
            ["nvidia-smi"] + list(args),
            capture_output=True, text=True, timeout=timeout
        )
        if r.returncode == 0:
            return r.stdout.strip().split("\n")
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return None


def _detect_gpu():
    global _cached_gpu, _last_gpu_check
    now = time.time()
    if now - _last_gpu_check < 5 and _cached_gpu is not None:
        return _cached_gpu
    with _gpu_lock:
        info = {
            "available": False,
            "vendor": None,
            "name": None,
            "driver_version": None,
            "cuda_version": None,
            "memory_total_mb": 0,
            "memory_used_mb": 0,
            "memory_free_mb": 0,
            "utilization_percent": None,
            "power_watts": None,
            "details": [],
        }

        # Try nvidia-smi first
        lines = _run_nvidia_smi(
            "--query-gpu=name,driver_version,memory.total,memory.used,memory.free,utilization.gpu,power.draw,temperature.gpu",
            "--format=csv,noheader,nounits"
        )
        if lines and lines[0]:
            parts = [p.strip() for p in lines[0].split(", ")]
            if len(parts) >= 1:
                info["available"] = True
                info["vendor"] = "NVIDIA"
                info["name"] = parts[0]
                info["driver_version"] = parts[1] if len(parts) > 1 else None
                info["memory_total_mb"] = int(float(parts[2])) if len(parts) > 2 and parts[2] else 0
                info["memory_used_mb"] = int(float(parts[3])) if len(parts) > 3 and parts[3] else 0
                info["memory_free_mb"] = int(float(parts[4])) if len(parts) > 4 and parts[4] else 0
                try:
                    info["utilization_percent"] = int(float(parts[5]))
                except (ValueError, IndexError):
                    pass
                info["power_watts"] = parts[6] if len(parts) > 6 else None
                # Detect CUDA version
                cuda_out = _run_nvidia_smi("--version")
                if cuda_out:
                    for line in cuda_out:
                        if "CUDA Version" in line:
                            info["cuda_version"] = line.split(":")[-1].strip()
                            break
                # Multi-GPU: collect all
                if len(lines) > 1:
                    for extra_line in lines[1:]:
                        info["details"].append(extra_line.strip())

        _cached_gpu = info
        _last_gpu_check = now
        return info


def get_system_diagnostics():
    """Return full system diagnostics with dependency status."""
    result = {
        "cpu": {
            "percent": 0,
            "count": os.cpu_count() or 1,
            "available": HAS_PSUTIL,
            "missing_dep": "psutil" if not HAS_PSUTIL else None,
            "install_cmd": PSUTIL_INSTALL,
        },
        "ram": {
            "total_mb": 0,
            "available_mb": 0,
            "used_mb": 0,
            "percent": 0,
            "available": HAS_PSUTIL,
            "missing_dep": "psutil" if not HAS_PSUTIL else None,
            "install_cmd": PSUTIL_INSTALL,
        },
        "gpu": _detect_gpu(),
        "dependencies": {
            "psutil": {
                "installed": HAS_PSUTIL,
                "version": psutil.__version__ if HAS_PSUTIL else None,
                "feature": "CPU/RAM monitoring, process management",
                "install_cmd": PSUTIL_INSTALL,
            },
        },
    }
    if HAS_PSUTIL:
        result["cpu"]["percent"] = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        result["ram"]["total_mb"] = round(mem.total / 1024 / 1024, 1)
        result["ram"]["available_mb"] = round(mem.available / 1024 / 1024, 1)
        result["ram"]["used_mb"] = round(mem.used / 1024 / 1024, 1)
        result["ram"]["percent"] = mem.percent
    return result


def install_dependency(name: str) -> dict:
    """Install a Python package. Returns success status and message."""
    global HAS_PSUTIL, PSUTIL_INSTALL
    if name == "psutil" and HAS_PSUTIL:
        return {"success": True, "message": "Already installed"}
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", name, "-q"],
            timeout=120
        )
        if name == "psutil":
            import importlib
            importlib.invalidate_caches()
            global psutil
            import psutil
            HAS_PSUTIL = True
            PSUTIL_INSTALL = ""
        return {"success": True, "message": f"{name} installed successfully"}
    except Exception as e:
        return {"success": False, "message": f"Installation failed: {e}"}
