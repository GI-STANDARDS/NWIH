"""
GGUF model downloader and manager.
Downloads models from Hugging Face so the system needs no external model service.
"""
import json
import os
import sys
from pathlib import Path
from typing import Generator, Optional

import httpx

from backend.config import BASE_DIR

MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)
MODELS_INDEX = MODELS_DIR / "models.json"

# Recommended GGUF models for the system
# These are small, fast quantized models suitable for cluster analysis
RECOMMENDED_MODELS = [
    {
        "id": "lmstudio-community/Llama-3.2-3B-Instruct-GGUF",
        "file": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "name": "Llama 3.2 3B (Q4_K_M)",
        "size_gb": 2.0,
        "description": "Best balance of speed & quality for cluster analysis",
        "default": True,
    },
    {
        "id": "QuantFactory/Meta-Llama-3-8B-Instruct-GGUF",
        "file": "Meta-Llama-3-8B-Instruct.Q4_K_M.gguf",
        "name": "Llama 3 8B (Q4_K_M)",
        "size_gb": 4.5,
        "description": "Higher quality, needs more RAM",
        "default": False,
    },
    {
        "id": "bartowski/Llama-3.2-1B-Instruct-GGUF",
        "file": "Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        "name": "Llama 3.2 1B (Q4_K_M)",
        "size_gb": 0.7,
        "description": "Fastest option, minimal RAM usage",
        "default": False,
    },
]


def _load_index() -> dict:
    if MODELS_INDEX.exists():
        return json.loads(MODELS_INDEX.read_text())
    return {"models": []}


def _save_index(data: dict):
    MODELS_INDEX.write_text(json.dumps(data, indent=2))


def list_available_models() -> list:
    """List models that have been downloaded (scans filesystem)."""
    idx = _load_index()
    indexed = {m["filename"] for m in idx.get("models", [])}
    found = []
    if MODELS_DIR.exists():
        for f in sorted(MODELS_DIR.iterdir()):
            if f.suffix == ".gguf":
                info = get_model_info(f)
                entry = {
                    "id": f.stem,
                    "filename": f.name,
                    "path": str(f),
                    "size_bytes": f.stat().st_size,
                    "size_mb": round(f.stat().st_size / (1024 * 1024), 1),
                    "size_gb": round(f.stat().st_size / (1024 ** 3), 1),
                    "quantization": info.get("quantization", f.stem.split("-")[-1] if "-" in f.stem else "unknown"),
                    "architecture": info.get("architecture", "unknown"),
                }
                if f.name in indexed:
                    m = next(m2 for m2 in idx["models"] if m2["filename"] == f.name)
                    entry.setdefault("default", m.get("default", False))
                found.append(entry)
    return found


def list_recommended() -> list:
    """List recommended models available for download."""
    return RECOMMENDED_MODELS


def get_model_path(model_id: str = "") -> Optional[Path]:
    """
    Get path to a downloaded GGUF model file.
    If model_id is empty, returns the default model (or first found).
    Scans filesystem if models.json index is empty.
    """
    # 1. Check index
    idx = _load_index()
    for m in idx.get("models", []):
        if not model_id and m.get("default"):
            p = MODELS_DIR / m["filename"]
            if p.exists():
                return p
        if m["id"] == model_id or m["filename"] == model_id:
            p = MODELS_DIR / m["filename"]
            if p.exists():
                return p
    if model_id == "":
        for m in idx.get("models", []):
            p = MODELS_DIR / m["filename"]
            if p.exists():
                return p
    # 2. Scan filesystem as fallback
    if MODELS_DIR.exists():
        for f in sorted(MODELS_DIR.iterdir()):
            if f.suffix == ".gguf":
                if not model_id or model_id == f.stem or model_id == f.name:
                    return f
    return None


def is_model_available(model_id: str = "") -> bool:
    """Check if a model file exists on disk."""
    return get_model_path(model_id) is not None


def download_model(
    model_id: str = "",
    hf_repo: str = "",
    filename: str = "",
    progress_callback=None,
) -> Generator[dict, None, None]:
    """
    Download a GGUF model from Hugging Face.
    Yields progress dicts for SSE streaming.

    If model_id matches a recommended model, downloads that one.
    Otherwise provide hf_repo + filename explicitly.
    """
    # Look up recommended model
    if model_id:
        for rec in RECOMMENDED_MODELS:
            if rec["id"] == model_id or rec["name"] == model_id:
                hf_repo = rec["id"]
                filename = rec["file"]
                break

    if not hf_repo or not filename:
        yield {"error": "Model not found. Provide hf_repo and filename."}
        return

    dest_path = MODELS_DIR / filename

    if dest_path.exists():
        yield {"message": f"Model already exists: {filename}", "progress": 100}
        return

    hf_url = f"https://huggingface.co/{hf_repo}/resolve/main/{filename}"
    yield {"message": f"Downloading {filename} from Hugging Face...", "progress": 5}

    try:
        with httpx.Client(timeout=600, follow_redirects=True) as client:
            with client.stream("GET", hf_url) as response:
                response.raise_for_status()
                total = int(response.headers.get("content-length", 0))
                downloaded = 0

                with open(dest_path, "wb") as f:
                    for chunk in response.iter_bytes(8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            pct = int(downloaded / total * 85) + 5
                            yield {
                                "message": f"Downloading {filename} ({downloaded // 1024 // 1024}MB / {total // 1024 // 1024}MB)",
                                "progress": min(pct, 90),
                            }

        # Register in index
        idx = _load_index()
        # Remove old entry if exists
        idx["models"] = [m for m in idx["models"] if m["filename"] != filename]
        entry = {
            "id": hf_repo,
            "filename": filename,
            "name": next((r["name"] for r in RECOMMENDED_MODELS if r["file"] == filename), filename),
            "size_bytes": dest_path.stat().st_size,
            "default": len(idx["models"]) == 0,
        }
        idx["models"].append(entry)
        _save_index(idx)

        yield {
            "message": f"Model downloaded: {filename} ({dest_path.stat().st_size // 1024 // 1024}MB)",
            "progress": 100,
            "model_path": str(dest_path),
        }

    except Exception as e:
        if dest_path.exists():
            dest_path.unlink()
        yield {"error": f"Download failed: {e}", "progress": 0}


def set_default_model(filename: str):
    """Mark a model as the default."""
    idx = _load_index()
    for m in idx.get("models", []):
        m["default"] = m["filename"] == filename
    _save_index(idx)


def delete_model(filename: str):
    """Remove a downloaded model."""
    p = MODELS_DIR / filename
    if p.exists():
        p.unlink()
    idx = _load_index()
    idx["models"] = [m for m in idx["models"] if m["filename"] != filename]
    if idx["models"]:
        idx["models"][0]["default"] = True
    _save_index(idx)


def ensure_model() -> str:
    """Ensure at least one model is available. Returns model path or empty string."""
    path = get_model_path()
    if path:
        return str(path)
    return ""


def get_model_info(file_path: str = "") -> dict:
    """Get info about a specific GGUF file on disk, or all models if path is empty."""
    if file_path:
        p = Path(file_path)
        if not p.exists() or p.suffix != ".gguf":
            return {}
        size_mb = round(p.stat().st_size / 1024 / 1024, 1)
        return {
            "filename": p.name,
            "path": str(p),
            "size_bytes": p.stat().st_size,
            "size_mb": size_mb,
            "size_gb": round(size_mb / 1024, 2),
            "quantization": _guess_quant(p.name),
            "architecture": _guess_arch(p.name),
        }
    idx = _load_index()
    models = idx.get("models", [])
    default = get_model_path()
    return {
        "models": models,
        "default_model": str(default) if default else None,
        "default_name": default.name if default else None,
        "count": len(models),
        "recommended": RECOMMENDED_MODELS,
    }


def _guess_quant(filename: str) -> str:
    parts = filename.upper().split(".")
    for p in parts:
        if "Q4_" in p or "Q5_" in p or "Q8_" in p or "Q2_" in p or "Q3_" in p or "Q6_" in p:
            return p
    return "Unknown"


def _guess_arch(filename: str) -> str:
    f = filename.lower()
    if "llama-3.2" in f or "llama3.2" in f:
        return "Llama 3.2"
    if "llama-3" in f or "llama3" in f:
        return "Llama 3"
    if "llama-2" in f or "llama2" in f:
        return "Llama 2"
    if "mistral" in f:
        return "Mistral"
    if "gemma" in f:
        return "Gemma"
    if "phi" in f:
        return "Phi"
    if "qwen" in f:
        return "Qwen"
    return "Unknown"
