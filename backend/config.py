import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "yt_comments.db"
FAISS_INDEX_PATH = DATA_DIR / "faiss_index.bin"
JOB_STATUS_PATH = DATA_DIR / "jobs"

DATA_DIR.mkdir(exist_ok=True)
JOB_STATUS_PATH.mkdir(exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

EXTRACT_BATCH_SIZE = int(os.getenv("EXTRACT_BATCH_SIZE", "50"))
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "256"))
CLUSTER_MIN_CLUSTER_SIZE = int(os.getenv("CLUSTER_MIN_CLUSTER_SIZE", "10"))
MAX_COMMENTS_PER_JOB = int(os.getenv("MAX_COMMENTS_PER_JOB", "50000"))

VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", "384"))

# ─── Self-contained llama.cpp (no external dependencies) ─────────────────────
MODEL_MANAGER_IDLE_TIMEOUT = int(os.getenv("MODEL_MANAGER_IDLE_TIMEOUT", "60"))
LLAMA_CPP_N_GPU_LAYERS = int(os.getenv("LLAMA_CPP_N_GPU_LAYERS", "-1"))
LLAMA_CPP_N_CTX = int(os.getenv("LLAMA_CPP_N_CTX", "2048"))
LLAMA_CPP_N_THREADS = int(os.getenv("LLAMA_CPP_N_THREADS", "4"))
