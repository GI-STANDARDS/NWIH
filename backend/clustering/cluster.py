from typing import Optional, Tuple
import numpy as np
from sklearn.preprocessing import StandardScaler
from backend.config import CLUSTER_MIN_CLUSTER_SIZE


def is_available() -> bool:
    try:
        import hdbscan  # noqa
        return True
    except ImportError:
        return False


def reduce_dimensions(embeddings: np.ndarray, n_components: int = 50) -> np.ndarray:
    try:
        import umap
        reducer = umap.UMAP(n_components=n_components, random_state=42, n_neighbors=15, min_dist=0.0)
        return reducer.fit_transform(embeddings)
    except ImportError:
        from sklearn.decomposition import PCA
        n = min(n_components, embeddings.shape[1], embeddings.shape[0])
        reducer = PCA(n_components=n)
        return reducer.fit_transform(embeddings)


def cluster_embeddings(
    embeddings: np.ndarray,
    min_cluster_size: int = CLUSTER_MIN_CLUSTER_SIZE,
) -> Tuple[np.ndarray, Optional[object]]:
    if len(embeddings) < min_cluster_size:
        return np.full(len(embeddings), -1), None

    reduced = reduce_dimensions(embeddings, n_components=min(50, embeddings.shape[1]))
    scaled = StandardScaler().fit_transform(reduced)

    try:
        import hdbscan
        clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, metric="euclidean",
                                     cluster_selection_epsilon=0.5, prediction_data=True)
        labels = clusterer.fit_predict(scaled)
        return labels, clusterer
    except ImportError:
        from sklearn.cluster import KMeans
        n = max(2, min(20, len(embeddings) // 100))
        clusterer = KMeans(n_clusters=n, random_state=42, n_init="auto")
        labels = clusterer.fit_predict(scaled)
        return labels, clusterer
