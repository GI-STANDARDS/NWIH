"""
Utility to save task outputs to RAW_text directory.
Uses video title in filenames. Comments saved as raw text only (no metadata).
"""
import os
import json
import re

RAW_TEXT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "RAW_text"))

_ILGAL = re.compile(r'[<>:"/\\|?*]')

def _slug(title):
    parts = title.split('|', 1)
    base = parts[0].strip()
    if len(parts) > 1:
        base = base + ' -' + parts[1].strip()
    safe = _ILGAL.sub('', base).strip()
    safe = re.sub(r'\s+', ' ', safe)
    return safe[:120]

def _fetch_title(job_id):
    try:
        from backend.database.database import SessionLocal
        from backend.database.models import Job
        db = SessionLocal()
        job = db.query(Job).filter(Job.job_id == job_id).first()
        title = job.video_title or job.job_id if job else job_id
        db.close()
        return title
    except Exception:
        return job_id

def ensure_dir():
    os.makedirs(RAW_TEXT_DIR, exist_ok=True)

def save_comments(job_id, comments, phase="raw"):
    ensure_dir()
    title = _fetch_title(job_id)
    slug = _slug(title)
    path = os.path.join(RAW_TEXT_DIR, f"{slug}_text-only.txt")
    with open(path, "w", encoding="utf-8") as f:
        for c in comments:
            f.write(c.get("text_original", "") + "\n---\n")
    print(f"[txt_export] Saved {len(comments)} comments to {os.path.basename(path)}")

def save_clean_comments(job_id, comments):
    save_comments(job_id, comments, "cleaned")

def save_clusters(job_id, clusters_data):
    ensure_dir()
    title = _fetch_title(job_id)
    slug = _slug(title)
    path = os.path.join(RAW_TEXT_DIR, f"{slug}_clusters.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Clusters: {len(clusters_data)}\n\n")
        for cd in clusters_data:
            f.write(f"--- Cluster #{cd['cluster_id']} ---\n")
            f.write(f"Size: {cd['size']}  |  {cd['frequency_pct']}%\n")
            f.write(f"Demand: {cd['demand_score']}  |  Urgency: {cd['urgency']}\n")
            f.write(f"Positive: {cd.get('sentiment_positive_pct', 0)}%  |  "
                    f"Negative: {cd.get('sentiment_negative_pct', 0)}%\n")
            keywords = cd.get('keywords', {})
            if isinstance(keywords, dict):
                top_kw = sorted(keywords.items(), key=lambda x: -x[1])[:10]
                f.write(f"Keywords: {', '.join(f'{k}({v})' for k,v in top_kw)}\n")
            samples = cd.get('sample_comments', [])
            if samples:
                f.write(f"Samples:\n")
                for s in samples[:3]:
                    f.write(f"  - {s}\n")
            f.write(f"\n")
    print(f"[txt_export] Saved {len(clusters_data)} clusters to {os.path.basename(path)}")

def save_llm_analysis(job_id, cluster_id, analysis):
    ensure_dir()
    title = _fetch_title(job_id)
    slug = _slug(title)
    path = os.path.join(RAW_TEXT_DIR, f"{slug}_llm_analysis.txt")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"--- Cluster #{cluster_id} ---\n")
        f.write(f"{json.dumps(analysis, indent=2)}\n\n")

def save_job_result(job_id, result):
    ensure_dir()
    title = _fetch_title(job_id)
    slug = _slug(title)
    path = os.path.join(RAW_TEXT_DIR, f"{slug}_result.txt")
    with open(path, "w", encoding="utf-8") as f:
        if isinstance(result, dict):
            for key, value in result.items():
                if isinstance(value, (list, dict)):
                    f.write(f"{key}:\n{json.dumps(value, indent=2, ensure_ascii=False)}\n\n")
                else:
                    f.write(f"{key}: {value}\n")
        else:
            f.write(str(result))
    print(f"[txt_export] Saved result to {os.path.basename(path)}")
