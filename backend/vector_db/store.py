"""
FAISS-based vector store for 1M-scale embeddings.
All operations are batch-based and memory-efficient.
"""
import json
import os
import numpy as np
from pathlib import Path
from typing import Optional, List

from backend.config import FAISS_INDEX_PATH, VECTOR_DIMENSION


class VectorStore:
    def __init__(self, index_path: str = str(FAISS_INDEX_PATH), dimension: int = VECTOR_DIMENSION):
        self.index_path = Path(index_path)
        self.dimension = dimension
        self._index = None
        self._id_map_path = self.index_path.with_suffix(".ids.json")
        self._id_map = {}

    def _get_index(self):
        if self._index is None:
            import faiss
            if self.index_path.exists():
                self._index = faiss.read_index(str(self.index_path))
                if self._id_map_path.exists():
                    with open(self._id_map_path) as f:
                        self._id_map = json.load(f)
            else:
                self._index = faiss.IndexFlatIP(self.dimension)
        return self._index

    def add(self, embeddings: np.ndarray, ids: Optional[List[int]] = None) -> int:
        """Add embeddings to index. Returns count added."""
        index = self._get_index()
        if ids:
            for i, cid in enumerate(ids):
                self._id_map[str(index.ntotal + i)] = cid
        index.add(embeddings.astype(np.float32))
        self._save()
        return len(embeddings)

    def search(self, query: np.ndarray, k: int = 10) -> tuple:
        """Search nearest neighbors. Returns (distances, indices)."""
        index = self._get_index()
        return index.search(query.astype(np.float32).reshape(1, -1), k)

    def total(self) -> int:
        return self._get_index().ntotal

    def _save(self):
        import faiss
        faiss.write_index(self._index, str(self.index_path))
        with open(self._id_map_path, "w") as f:
            json.dump(self._id_map, f)

    def clear(self):
        self._index = None
        if self.index_path.exists():
            self.index_path.unlink()
        if self._id_map_path.exists():
            self._id_map_path.unlink()
        self._id_map = {}

    def get_all_embeddings(self) -> np.ndarray:
        """Reconstruct full embedding matrix (for clustering)."""
        index = self._get_index()
        import faiss
        return index.reconstruct_n(0, index.ntotal)


store = VectorStore()
