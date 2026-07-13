"""
Setup Manager — handles package checking, CUDA detection, on-demand installs,
and llama.cpp self-contained binary + model management.
"""
import subprocess
import sys
import os
from pathlib import Path
from typing import Generator

from backend.config import BASE_DIR


VENV_DIR = BASE_DIR / ".venv"

PACKAGE_GROUPS = {
    "embeddings": ["sentence-transformers"],
    "clustering": ["hdbscan", "umap-learn"],
    "vector_db": ["faiss-cpu"],
    "all": ["sentence-transformers", "hdbscan", "umap-learn", "faiss-cpu"],
}


def _python() -> str:
    if sys.platform == "win32":
        return str(VENV_DIR / "Scripts" / "python.exe")
    return str(VENV_DIR / "bin" / "python")


def _pip() -> str:
    if sys.platform == "win32":
        return str(VENV_DIR / "Scripts" / "pip.exe")
    return str(VENV_DIR / "bin" / "pip")


def check_package_installed(package_name: str) -> bool:
    return _pip_show(package_name)["installed"]

def _pip_show(package_name: str) -> dict:
    """Single pip show call returning {installed, version}."""
    try:
        result = subprocess.run(
            [_pip(), "show", package_name],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            version = "unknown"
            for line in result.stdout.split("\n"):
                if line.startswith("Version:"):
                    version = line.split(":", 1)[1].strip()
                    break
            return {"installed": True, "version": version}
    except Exception:
        pass
    return {"installed": False, "version": None}


def get_installation_status() -> dict:
    """Return full setup status."""
    venv_ok = VENV_DIR.exists() and (VENV_DIR / "Scripts" / "python.exe").exists()

    packages = {}
    for pkg in ["sentence-transformers", "hdbscan", "umap-learn", "faiss-cpu", "torch"]:
        packages[pkg] = _pip_show(pkg)

    cuda = detect_cuda()

    # llama.cpp status
    from backend.llama_cpp.binary import is_available as llm_bin_avail
    from backend.llama_cpp.models import get_model_info

    llama_binary = llm_bin_avail()
    model_info = get_model_info()

    return {
        "venv_exists": venv_ok,
        "cuda": cuda,
        "packages": packages,
        "all_heavy_installed": all(
            packages[pkg]["installed"] for pkg in ["sentence-transformers", "hdbscan", "umap-learn", "faiss-cpu"]
        ),
        "llama_cpp": {
            "binary_available": llama_binary,
            "models": model_info,
        },
    }


def detect_cuda() -> dict:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,driver_version,memory.total",
             "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            gpus = []
            for line in result.stdout.strip().split("\n"):
                parts = [p.strip() for p in line.split(",")]
                gpus.append({
                    "name": parts[0] if len(parts) > 0 else "Unknown",
                    "driver": parts[1] if len(parts) > 1 else "N/A",
                    "memory": parts[2] if len(parts) > 2 else "N/A",
                })
            return {"available": True, "gpus": gpus}
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
        pass
    return {"available": False, "gpus": []}


def install_package_group(
    group: str,
) -> Generator[dict, None, None]:
    """Install a package group, yielding progress dicts."""
    packages = PACKAGE_GROUPS.get(group)
    if not packages:
        yield {"error": f"Unknown group: {group}"}
        return

    total = len(packages)
    yield {"step": group, "message": f"Installing {group} packages...", "progress": 0}

    for i, pkg in enumerate(packages):
        yield {"step": group, "message": f"Installing {pkg}...", "progress": int(i / total * 80)}

        process = subprocess.Popen(
            [_pip(), "install", pkg, "--quiet"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
        for line in process.stdout or []:
            line = line.strip()
            if line and not line.startswith(("Requirement already", "Collecting", "  ")):
                yield {"step": group, "message": line, "progress": int((i + 0.5) / total * 80)}

        process.wait()
        if process.returncode != 0:
            yield {"step": group, "error": f"Failed to install {pkg}", "progress": 0}
            return

        if check_package_installed(pkg):
            yield {"step": group, "message": f"{pkg} installed successfully", "progress": int((i + 1) / total * 100)}
        else:
            yield {"step": group, "error": f"{pkg} installation verification failed", "progress": 0}
            return

    yield {"step": group, "message": f"{group} complete", "progress": 100}


def download_llama_binary() -> Generator[dict, None, None]:
    """Download llama.cpp binary, yielding progress."""
    from backend.llama_cpp.binary import download_binary
    yield {"step": "llama_binary", "message": "Downloading llama.cpp binary...", "progress": 10}
    try:
        path = download_binary()
        yield {"step": "llama_binary", "message": f"llama.cpp binary ready: {path}", "progress": 100}
    except Exception as e:
        yield {"step": "llama_binary", "error": f"Failed: {e}", "progress": 0}


def download_llama_model(model_id: str = "") -> Generator[dict, None, None]:
    """Download a GGUF model, yielding progress."""
    from backend.llama_cpp.models import download_model
    yield from download_model(model_id=model_id)
