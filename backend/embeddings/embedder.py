from typing import List, Optional
import numpy as np
from backend.config import EMBEDDING_MODEL, EMBEDDING_BATCH_SIZE

_model = None


def get_model():
    global _model
    if _model is not None:
        return _model
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBEDDING_MODEL)
        return _model
    except ImportError:
        raise RuntimeError("sentence-transformers not installed. Run: pip install sentence-transformers")


def is_available() -> bool:
    try:
        import sentence_transformers  # noqa
        return True
    except ImportError:
        return False


def generate_embeddings_batch(
    texts: List[str],
    batch_size: int = EMBEDDING_BATCH_SIZE,
) -> np.ndarray:
    """Generate embeddings for a batch of texts. Returns float32 array."""
    model = get_model()
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        emb = model.encode(batch, normalize_embeddings=True, show_progress_bar=False)
        all_embeddings.append(emb)
    return np.vstack(all_embeddings).astype(np.float32) if all_embeddings else np.array([], dtype=np.float32)
