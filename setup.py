from setuptools import setup, find_packages

setup(
    name="yt-comment-intelligence",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[],  # managed by requirements-core.txt + on-demand installs
    extras_require={
        "cpu": [
            "sentence-transformers>=2.2.0",
            "hdbscan>=0.8.0",
            "umap-learn>=0.5.0",
        ],
        "cuda": [
            "torch>=2.0.0",
            "sentence-transformers>=2.2.0",
            "hdbscan>=0.8.0",
            "umap-learn>=0.5.0",
        ],
    },
    python_requires=">=3.10",
)
