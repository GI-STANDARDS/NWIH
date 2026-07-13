"""
LLM Analysis — delegates to the Model Manager singleton.
llama.cpp runs as a managed subprocess — zero external dependencies.
"""
from backend.model_manager import manager as model_manager


class LLMAnalyzer:
    """Thin wrapper around ModelManager for backwards compatibility."""

    def __init__(self, model: str = None, base_url: str = None):
        self._manager = model_manager
        if not self._manager.is_loaded():
            self._manager.load_model(model or "")

    def analyze_cluster(self, cluster_data: dict) -> dict:
        return self._manager.analyze_cluster(cluster_data)

    def generate_insights(self, clusters_data: list) -> dict:
        return self._manager.generate_insights(clusters_data)

    def generate_roadmap(self, clusters_data: list) -> dict:
        return self._manager.generate_roadmap(clusters_data)
