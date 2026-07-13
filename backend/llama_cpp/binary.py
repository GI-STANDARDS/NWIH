"""
Self-contained llama.cpp binary manager.
Downloads pre-built llama.cpp binaries from GitHub releases so the system
has zero external runtime dependencies (no Ollama, no llama-cpp-python pip package).
"""
import io
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Optional

import httpx

from backend.config import BASE_DIR

LLAMA_CPP_DIR = BASE_DIR / "llama.cpp"
LLAMA_CPP_DIR.mkdir(exist_ok=True)


# Pre-built release info
# We download the latest llama.cpp release binaries from GitHub
GITHUB_REPO = "ggml-org/llama.cpp"
RELEASE_TAG = "b9873"  # pinned stable release

WIN_GPU_URL = f"https://github.com/{GITHUB_REPO}/releases/download/{RELEASE_TAG}/llama-{RELEASE_TAG}-bin-win-cuda-12.4-x64.zip"
WIN_CPU_URL = f"https://github.com/{GITHUB_REPO}/releases/download/{RELEASE_TAG}/llama-{RELEASE_TAG}-bin-win-cpu-x64.zip"
LINUX_URL = f"https://github.com/{GITHUB_REPO}/releases/download/{RELEASE_TAG}/llama-{RELEASE_TAG}-bin-ubuntu-x64.tar.gz"
MAC_URL = f"https://github.com/{GITHUB_REPO}/releases/download/{RELEASE_TAG}/llama-{RELEASE_TAG}-bin-macos-arm64.tar.gz"

SERVER_EXE = "llama-server.exe" if sys.platform == "win32" else "llama-server"


def _download_url(url: str, dest: Path, timeout: int = 120):
    """Download a file with progress."""
    print(f"[llama_cpp] Downloading {url.split('/')[-1]}...")
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        dest.write_bytes(response.content)
    print(f"[llama_cpp] Saved to {dest}")


def _get_binary_url() -> str:
    """Get appropriate download URL for current platform."""
    system = platform.system()
    if system == "Windows":
        # Check for CUDA
        try:
            result = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return WIN_GPU_URL
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return WIN_CPU_URL
    elif system == "Linux":
        return LINUX_URL
    elif system == "Darwin":
        return MAC_URL
    raise RuntimeError(f"Unsupported platform: {system}")


def download_binary(force: bool = False) -> Path:
    """
    Download and extract llama.cpp binaries.
    Returns path to llama-server executable.
    """
    server_path = LLAMA_CPP_DIR / SERVER_EXE
    if server_path.exists() and not force:
        print(f"[llama_cpp] Binary already exists at {server_path}")
        return server_path

    url = _get_binary_url()
    zip_path = LLAMA_CPP_DIR / "llama.zip"

    print(f"[llama_cpp] Downloading llama.cpp binaries from GitHub...")
    _download_url(url, zip_path)

    print(f"[llama_cpp] Extracting...")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(LLAMA_CPP_DIR)

    zip_path.unlink()

    # Find the server binary
    if not server_path.exists():
        # Search in extracted folder
        for f in LLAMA_CPP_DIR.rglob(SERVER_EXE):
            shutil.move(str(f), str(server_path))
            break

    if not server_path.exists():
        raise RuntimeError(f"llama-server not found after extraction at {server_path}")

    # Make executable
    if sys.platform != "win32":
        server_path.chmod(0o755)

    print(f"[llama_cpp] Binary ready at {server_path}")
    return server_path


def ensure_binary(force: bool = False) -> Path:
    """Ensure llama.cpp binary is available, downloading if needed."""
    server_path = LLAMA_CPP_DIR / SERVER_EXE
    if server_path.exists() and not force:
        return server_path
    return download_binary(force)


def get_binary_path() -> Optional[Path]:
    """Get path to llama-server binary, or None if not downloaded."""
    p = LLAMA_CPP_DIR / SERVER_EXE
    return p if p.exists() else None


def is_available() -> bool:
    """Check if llama.cpp binary is downloaded."""
    return get_binary_path() is not None
