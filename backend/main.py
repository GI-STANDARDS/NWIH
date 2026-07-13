"""
FastAPI Backend — YouTube Comment AI Analytics Engine
PHP frontend communicates ONLY through this API.
"""
import json
import uuid
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.database import get_db, init_db
from backend.database.models import Job, Comment, Cluster
from backend.extractor.youtube import extract_video_id, get_channel_videos, get_playlist_videos
from backend.job_queue.worker import start_worker_thread
from backend.job_queue.tasks import task_llm_analyze_job
from backend.export.exporter import export_job_result
from backend.analysis.competitors import count_term_mentions
from backend.analysis.insights import analyze_insights
from backend.export.txt_exporter import save_comments, save_clusters, save_job_result, save_llm_analysis
from backend import setup_manager as sm
from backend.model_manager import manager as model_manager
from backend.diagnostics import get_system_diagnostics
from backend.logging_system import logs
from backend.progress import tracker as progress_tracker


# ─── App Setup ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_worker_thread()
    logs.info("system", "Backend started. ML pipeline ready, LLM available if GGUF loaded.")
    yield

app = FastAPI(title="YT Comment AI Analytics API", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


# ─── Pydantic Schemas ──────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    youtube_url: str
    max_comments: int = 50000
    source_type: str = "video"

class BatchRequest(BaseModel):
    urls: list[str]
    max_comments_per_video: int = 10000

class InstallGroup(BaseModel):
    group: str = "all"

class ModelDownloadRequest(BaseModel):
    model_id: str = ""


# ─── Helper ────────────────────────────────────────────────────────────────────

def _make_job(video_id: str, url: str, source_type: str = "video",
              max_comments: int = 50000, db: Session = None) -> Job:
    job = Job(
        job_id=str(uuid.uuid4()),
        video_id=video_id,
        video_url=url,
        video_title="",
        channel="",
        source_type=source_type,
        total_comments=max_comments,
        status="queued",
        progress=0.0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    state = progress_tracker.create_job(job.job_id)
    state.total_comments = max_comments
    progress_tracker.add_activity(job.job_id, "🎬", "Job queued. Waiting for worker...")
    return job


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 1: ML ANALYSIS PIPELINE (no GGUF/LLM required)
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/analyze")
def start_analysis(req: AnalyzeRequest, db: Session = Depends(get_db)):
    video_id = extract_video_id(req.youtube_url)
    if not video_id:
        raise HTTPException(400, "Invalid YouTube URL")
    job = _make_job(video_id, req.youtube_url, req.source_type, req.max_comments, db)
    logs.info("ml_pipeline", f"Analysis queued ({job.job_id[:8]}...)")
    return {
        "job_id": job.job_id, "video_id": video_id,
        "video_title": "", "channel": "",
        "status": "queued",
        "message": "Analysis started. Poll /status/{job_id} for updates.",
    }

@app.post("/analyze/batch")
def start_batch_analysis(req: BatchRequest, db: Session = Depends(get_db)):
    results = []
    for url in req.urls:
        video_id = extract_video_id(url)
        if not video_id:
            results.append({"url": url, "error": "Invalid URL", "job_id": None})
            continue
        job = _make_job(video_id, url, "video", req.max_comments_per_video, db)
        results.append({"url": url, "video_id": video_id, "job_id": job.job_id, "status": "queued"})
    return {"results": results, "total": len(results)}

@app.post("/analyze/channel")
def start_channel_analysis(channel_url: str, max_videos: int = 10,
                           max_comments_per_video: int = 10000,
                           db: Session = Depends(get_db)):
    videos = get_channel_videos(channel_url, max_videos=max_videos)
    results = []
    for v in videos:
        job = _make_job(v["video_id"], v["url"], "channel", max_comments_per_video, db)
        results.append({"video_id": v["video_id"], "title": "", "job_id": job.job_id})
    return {"channel_url": channel_url, "videos_found": len(videos), "jobs": results}

@app.post("/analyze/playlist")
def start_playlist_analysis(playlist_url: str, max_videos: int = 10,
                            max_comments_per_video: int = 10000,
                            db: Session = Depends(get_db)):
    videos = get_playlist_videos(playlist_url, max_videos=max_videos)
    results = []
    for v in videos:
        job = _make_job(v["video_id"], v["url"], "playlist", max_comments_per_video, db)
        results.append({"video_id": v["video_id"], "title": "", "job_id": job.job_id})
    return {"playlist_url": playlist_url, "videos_found": len(videos), "jobs": results}

@app.get("/status/{job_id}")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    return {
        "job_id": job.job_id, "video_title": job.video_title,
        "status": job.status, "progress": job.progress,
        "comments_extracted": job.comments_extracted,
        "comments_embedded": job.comments_embedded,
        "clusters_found": job.clusters_found,
        "error": job.error,
        "created_at": str(job.created_at) if job.created_at else None,
        "completed_at": str(job.completed_at) if job.completed_at else None,
        "result_ready": job.status == "completed" and job.result is not None,
    }

@app.get("/result/{job_id}")
def get_job_result(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status != "completed":
        raise HTTPException(400, f"Job not completed. Status: {job.status}")
    if not job.result:
        clusters = db.query(Cluster).filter(Cluster.job_id == job_id).all()
        comments = db.query(Comment).filter(
            Comment.job_id == job_id, Comment.is_spam == False
        ).limit(10000).all()
        competitors = count_term_mentions(comments)
        clusters_payload = [{"cluster_id": c.cluster_id, "label": c.label, "size": c.size,
              "frequency_pct": c.frequency_pct, "demand_score": c.demand_score,
              "urgency": c.urgency, "sentiment_positive_pct": c.sentiment_positive_pct,
              "sentiment_negative_pct": c.sentiment_negative_pct,
              "purchase_intent_count": c.purchase_intent_count,
              "keywords": c.keywords, "sample_comments": c.sample_comments,
              "llm_analysis": c.llm_analysis if c.llm_analysis else {}} for c in clusters]
        insights = analyze_insights(clusters_payload, comments)
        result = export_job_result(
            {"video_title": job.video_title, "video_url": job.video_url,
             "total_comments": job.total_comments, "comments_extracted": job.comments_extracted},
            clusters_payload,
            competitors,
            insights,
        )
    else:
        result = job.result
    return JSONResponse(content={
        "job_id": job.job_id, "video_title": job.video_title,
        "video_url": job.video_url, "status": job.status, "result": result,
    })

@app.get("/analyze/{job_id}/ai-analysis")
def get_ai_analysis(job_id: str, db: Session = Depends(get_db)):
    """Get AI-powered intent and opportunity analysis for a completed job."""
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status != "completed":
        raise HTTPException(400, f"Job not completed. Status: {job.status}")
    
    clusters = db.query(Cluster).filter(Cluster.job_id == job_id).all()
    comments = db.query(Comment).filter(
        Comment.job_id == job_id, Comment.is_spam == False
    ).limit(10000).all()
    
    if not clusters or not comments:
        raise HTTPException(400, "Job has no data to analyze")
    
    # Convert to dicts for analyzer
    clusters_payload = [{
        "cluster_id": c.cluster_id,
        "label": c.label,
        "size": c.size,
        "frequency_pct": c.frequency_pct,
        "demand_score": c.demand_score,
        "urgency": c.urgency,
        "sentiment_positive_pct": c.sentiment_positive_pct,
        "sentiment_negative_pct": c.sentiment_negative_pct,
        "purchase_intent_count": c.purchase_intent_count,
        "keywords": c.keywords,
        "sample_comments": c.sample_comments,
    } for c in clusters]
    
    comments_payload = [{
        "text_original": c.text_original,
        "text_cleaned": c.text_cleaned,
        "sentiment_label": c.sentiment_label,
    } for c in comments]
    
    # Generate AI summary — try multi-agent reasoning if LLM available
    ai_analysis = None
    try:
        from backend.analysis.agents import run_multi_agent_pipeline
        from backend.model_manager import manager as model_manager
        if model_manager.is_ready():
            model_manager.load_model()
            reasoning = run_multi_agent_pipeline(model_manager, comments_payload)
            if "error" not in reasoning:
                ai_analysis = {
                    "summary": {
                        "what_users_want": [i.get("label","") for i in
                            reasoning.get("agents",{}).get("intent_analysis",{}).get("intents",[])[:3]],
                        "key_trends": [p.get("problem","") for p in
                            reasoning.get("agents",{}).get("pain_analysis",{}).get("problems",[])[:3]],
                        "market_gaps": [o.get("opportunity","") for o in
                            reasoning.get("agents",{}).get("opportunity_analysis",{}).get("opportunities",[])[:3]],
                    },
                    "user_intents": {"top_intents": [
                        [i.get("intent","?"), int(i.get("estimated_percentage",0))]
                        for i in reasoning.get("agents",{}).get("intent_analysis",{}).get("intents",[])
                    ]},
                    "trending_topics": {"trending_topics": [
                        {"topic": v.get("title",""), "trend_score": v.get("demand",0),
                         "size": 0, "frequency": "", "positive_sentiment": "",
                         "keywords": v.get("why","")}
                        for v in reasoning.get("agents",{}).get("video_ideas",{}).get("videos",[])[:5]
                    ]},
                    "market_opportunities": {"opportunities": [
                        {"type": o.get("opportunity",""), "opportunity": o.get("why","")}
                        for o in reasoning.get("agents",{}).get("opportunity_analysis",{}).get("opportunities",[])
                    ], "skill_demand": {}},
                    "_reasoning": reasoning,
                }
    except Exception as e:
        print(f"[ai-analysis] Multi-agent pipeline failed: {e}")
        ai_analysis = None
    
    if not ai_analysis:
        ai_analysis = generate_ai_summary({}, clusters_payload, comments_payload)
    
    return JSONResponse(content={
        "job_id": job_id,
        "video_title": job.video_title,
        "analysis": ai_analysis,
    })

@app.get("/jobs")
def list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(Job).order_by(Job.created_at.desc()).limit(50).all()
    return [{"job_id": j.job_id, "video_title": j.video_title, "video_url": j.video_url,
             "video_id": j.video_id, "channel": j.channel, "status": j.status,
             "progress": j.progress, "comments_extracted": j.comments_extracted,
             "total_comments": j.total_comments, "clusters_found": j.clusters_found,
             "error": j.error,
             "created_at": str(j.created_at) if j.created_at else None,
             "updated_at": str(j.updated_at) if j.updated_at else None,
             "completed_at": str(j.completed_at) if j.completed_at else None,
             "result_ready": j.status == "completed"} for j in jobs]

@app.get("/stream/{job_id}")
def stream_job_progress(job_id: str):
    """SSE endpoint for live job progress streaming."""
    from fastapi.responses import StreamingResponse
    import asyncio

    # Initialize progress tracking for this job
    state = progress_tracker.get_state(job_id)
    if not state:
        progress_tracker.create_job(job_id)

    async def event_generator():
        last_seq = 0
        try:
            while True:
                state = progress_tracker.get_state(job_id)
                if not state:
                    yield f"event: done\ndata: {{}}\n\n"
                    break

                events = progress_tracker.get_new_events(job_id, last_seq)
                for event in events:
                    yield f"event: {event['type']}\ndata: {json.dumps(event['data'])}\n\n"
                    last_seq = event["seq"]

                # Send heartbeat every 2s
                yield f"event: heartbeat\ndata: {json.dumps({'seq': last_seq})}\n\n"

                # Check if job finished
                if state.status in ("completed", "error"):
                    # Send final state
                    yield f"event: done\ndata: {json.dumps({'status': state.status, 'job_id': job_id})}\n\n"
                    break

                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            pass

    return StreamingResponse(event_generator(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "Connection": "keep-alive",
                                      "X-Accel-Buffering": "no"})

@app.get("/cancel/{job_id}")
@app.post("/cancel/{job_id}")
def cancel_job(job_id: str):
    """Request cancellation of a running job."""
    from backend.database.models import Job
    from backend.database.database import SessionLocal
    progress_tracker.request_cancel(job_id)
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if job and job.status in ("queued", "pending", "processing", "extracting", "embedding", "clustering"):
            job.status = "cancelled"
            job.progress = 0
            job.updated_at = datetime.utcnow()
            db.commit()
            return {"status": "cancelled", "job_id": job_id}
        return {"status": "not_found_or_already_done", "job_id": job_id}
    finally:
        db.close()

@app.delete("/jobs/{job_id}")
def delete_job(job_id: str):
    """Delete a job and all its associated comments and clusters."""
    from backend.database.models import Comment, Cluster
    from backend.database.database import SessionLocal
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if not job:
            raise HTTPException(404, "Job not found")
        db.query(Comment).filter(Comment.job_id == job_id).delete()
        db.query(Cluster).filter(Cluster.job_id == job_id).delete()
        db.delete(job)
        db.commit()
        return {"status": "deleted", "job_id": job_id}
    finally:
        db.close()

@app.post("/jobs/{job_id}/pause")
def pause_job(job_id: str):
    """Pause a running or queued job."""
    from backend.database.database import SessionLocal
    progress_tracker.request_cancel(job_id)
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if not job:
            raise HTTPException(404, "Job not found")
        if job.status in ("queued", "pending", "processing", "extracting", "embedding", "clustering"):
            job.status = "paused"
            job.updated_at = datetime.utcnow()
            db.commit()
            return {"status": "paused", "job_id": job_id}
        return {"status": "cannot_pause", "job_id": job_id, "current_status": job.status}
    finally:
        db.close()

@app.post("/jobs/{job_id}/process")
def process_job(job_id: str):
    """Manually trigger AI processing on extracted comments."""
    from backend.database.database import SessionLocal
    from backend.queue.tasks import task_clean_and_embed, task_cluster_and_analyze
    import threading
    
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if not job:
            raise HTTPException(404, "Job not found")
        
        if job.comments_extracted == 0:
            raise HTTPException(400, "No comments extracted to process")
        
        if job.status in ("processing", "embedding", "clustering", "finalizing"):
            return {"status": "already_processing", "job_id": job_id}
        
        # Clear cancellation flag from any prior pause
        progress_tracker.clear_cancel(job_id)
        
        # Mark as processing in DB so frontend shows active state
        job.status = "processing"
        job.updated_at = datetime.utcnow()
        db.commit()
        
        # Trigger AI processing in background
        def process_extracted():
            try:
                progress_tracker.add_activity(job_id, "🧠", "Processing extracted comments with AI...")
                task_clean_and_embed(job_id)
                task_cluster_and_analyze(job_id, use_llm=False)
                progress_tracker.add_activity(job_id, "✅", "AI processing complete for extracted comments")
            except Exception as e:
                print(f"[process] AI processing error: {e}")
                progress_tracker.add_activity(job_id, "❌", f"AI processing error: {e}")
        
        thread = threading.Thread(target=process_extracted, daemon=True)
        thread.start()
        
        return {"status": "processing_started", "job_id": job_id, "comments_to_process": job.comments_extracted}
    finally:
        db.close()

@app.post("/jobs/{job_id}/resume")
def resume_job(job_id: str):
    """Resume a paused job back to queued."""
    from backend.database.database import SessionLocal
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if not job:
            raise HTTPException(404, "Job not found")
        if job.status == "paused":
            job.status = "queued"
            job.updated_at = datetime.utcnow()
            db.commit()
            progress_tracker.clear_cancel(job_id)
            return {"status": "queued", "job_id": job_id}
        return {"status": "cannot_resume", "job_id": job_id, "current_status": job.status}
    finally:
        db.close()

@app.post("/jobs/{job_id}/restart")
def restart_job(job_id: str):
    """Reset a failed or completed job back to queued for reprocessing."""
    from backend.database.database import SessionLocal
    from backend.database.models import Comment, Cluster
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if not job:
            raise HTTPException(404, "Job not found")
        db.query(Comment).filter(Comment.job_id == job_id).delete()
        db.query(Cluster).filter(Cluster.job_id == job_id).delete()
        job.status = "queued"
        job.progress = 0
        job.error = None
        job.comments_extracted = 0
        job.comments_embedded = 0
        job.total_comments = 0
        job.clusters_found = 0
        job.result = None
        job.updated_at = datetime.utcnow()
        db.commit()
        progress_tracker.clear_cancel(job_id)
        return {"status": "restarted", "job_id": job_id}
    finally:
        db.close()

@app.post("/jobs/{job_id}/export-text")
def export_job_text(job_id: str, db: Session = Depends(get_db)):
    """Export job data to text files on demand."""
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    try:
        comments = db.query(Comment).filter(
            Comment.job_id == job_id, Comment.is_spam == False
        ).order_by(Comment.created_at.asc()).all()
        if comments:
            save_comments(job_id,
                [{"text_original": c.text_original} for c in comments],
                phase="raw")
        clusters = db.query(Cluster).filter(Cluster.job_id == job_id).all()
        if clusters:
            clusters_data = []
            for c in clusters:
                cd = {k: v for k, v in c.__dict__.items() if not k.startswith("_")}
                for f in ("keywords", "sample_comments", "comment_ids", "cluster_intents"):
                    if isinstance(cd.get(f), str):
                        try: cd[f] = json.loads(cd[f])
                        except: pass
                clusters_data.append(cd)
            save_clusters(job_id, clusters_data)
        result = {k: v for k, v in job.__dict__.items() if not k.startswith("_")}
        for k, v in result.items():
            if isinstance(v, str):
                try: result[k] = json.loads(v)
                except: pass
        save_job_result(job_id, result)
        return {"status": "exported", "job_id": job_id}
    except Exception as e:
        raise HTTPException(500, f"Export failed: {e}")

@app.get("/ml/status")
def ml_pipeline_status():
    """ML pipeline component status — no LLM dependency."""
    from backend.embeddings.embedder import is_available as emb_avail
    from backend.clustering.cluster import is_available as cluster_avail
    return {
        "comment_extractor": True,
        "sentiment_analysis": True,
        "spam_detection": True,
        "sentence_transformers": emb_avail(),
        "hdbscan": cluster_avail(),
        "umap": True,
        "faiss": True,
        "pipeline_ready": emb_avail() and cluster_avail(),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 2: LLM PIPELINE (optional, GGUF required)
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/analyze/{job_id}/llm-analyze")
def analyze_llm(job_id: str, db: Session = Depends(get_db)):
    """Run LLM analysis on an already-completed job (optional AI enhancement)."""
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status not in ("completed", "clustering", "finalizing"):
        raise HTTPException(400, f"Job must be completed first. Status: {job.status}")
    if not model_manager.is_ready():
        raise HTTPException(400, "AI features require a GGUF model. Core ML analysis remains fully available.")
    count = task_llm_analyze_job(job_id)
    if count < 0:
        raise HTTPException(500, "Failed to run LLM analysis")
    return {"status": "ok", "clusters_analyzed": count, "message": f"AI analysis complete for {count} clusters"}


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 3: SYSTEM STATUS & DIAGNOSTICS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "YT Comment AI Analytics API", "version": "2.0.0",
            "ml_pipeline": True, "llm_available": model_manager.is_ready()}

@app.get("/system/diagnostics")
def system_diagnostics():
    return get_system_diagnostics()

@app.get("/system/status")
def system_status():
    """Aggregated status of all system components."""
    from backend.embeddings.embedder import is_available as emb_avail
    from backend.clustering.cluster import is_available as cluster_avail
    ml_ready = emb_avail() and cluster_avail()
    return {
        "api": {"status": "online", "online": True},
        "database": {"status": "online", "online": True},
        "worker": {"status": "online", "online": True},
        "comment_extractor": {"status": "online", "online": True},
        "embedding_engine": {"status": "online" if emb_avail() else "offline", "online": emb_avail()},
        "vector_database": {"status": "online" if emb_avail() else "offline", "online": emb_avail()},
        "analytics_engine": {"status": "online" if ml_ready else "offline", "online": ml_ready},
        "llama_server": {"status": "online" if model_manager._server.is_running else "offline",
                          "online": model_manager._server.is_running},
        "gguf_model": {"status": "online" if model_manager.is_loaded() else "offline",
                        "online": model_manager.is_loaded()},
        "ai_chat": {"status": "online" if model_manager.is_loaded() else "offline",
                     "online": model_manager.is_loaded()},
    }


@app.get("/system/config-validate")
def config_validate():
    """Validate all system configuration."""
    from pathlib import Path
    from backend.llama_cpp.binary import get_binary_path
    from backend.llama_cpp.models import MODELS_DIR
    from backend.config import LLAMA_CPP_N_CTX, LLAMA_CPP_N_THREADS, LLAMA_CPP_N_GPU_LAYERS, \
        EXTRACT_BATCH_SIZE, MAX_COMMENTS_PER_JOB
    issues = []
    checks = {}

    # Binary path
    bin_path = get_binary_path()
    if bin_path:
        checks["llama_binary"] = {"status": "pass", "detail": str(bin_path)}
    else:
        checks["llama_binary"] = {"status": "fail", "detail": "Binary not found"}
        issues.append("llama.cpp binary missing — download from AI Control Center")

    # Models directory
    if MODELS_DIR.exists():
        gguf_files = list(MODELS_DIR.glob("*.gguf"))
        checks["models_dir"] = {"status": "pass" if gguf_files else "warn",
                                "detail": f"{MODELS_DIR} ({len(gguf_files)} .gguf files)"}
        if not gguf_files:
            issues.append("No GGUF models found — upload a model or scan folder")
    else:
        checks["models_dir"] = {"status": "fail", "detail": f"Directory not found: {MODELS_DIR}"}
        issues.append("Models directory missing")

    # Context size
    if LLAMA_CPP_N_CTX >= 128:
        checks["context_size"] = {"status": "pass", "detail": f"{LLAMA_CPP_N_CTX} tokens"}
    else:
        checks["context_size"] = {"status": "fail", "detail": f"Too small: {LLAMA_CPP_N_CTX}"}
        issues.append("Context size too small (minimum 128)")

    # Thread count
    if 1 <= LLAMA_CPP_N_THREADS <= 64:
        checks["thread_count"] = {"status": "pass", "detail": f"{LLAMA_CPP_N_THREADS} threads"}
    else:
        checks["thread_count"] = {"status": "warn", "detail": f"Unusual: {LLAMA_CPP_N_THREADS}"}

    # GPU layers
    checks["gpu_layers"] = {"status": "info", "detail": f"{'GPU disabled' if LLAMA_CPP_N_GPU_LAYERS == 0 else 'Auto/all' if LLAMA_CPP_N_GPU_LAYERS < 0 else str(LLAMA_CPP_N_GPU_LAYERS) + ' layers'}"}

    # Max comments
    checks["max_comments"] = {"status": "info", "detail": f"{MAX_COMMENTS_PER_JOB:,}"}

    # Batch size
    checks["batch_size"] = {"status": "info", "detail": f"{EXTRACT_BATCH_SIZE}/batch"}

    return {"healthy": len([c for c in checks.values() if c['status'] == 'fail']) == 0,
            "issues": issues, "checks": checks}

def _get_version(mod, pkg_name=None):
    """Get package version from module or via importlib.metadata."""
    ver = getattr(mod, "__version__", None)
    if ver:
        return ver
    try:
        from importlib.metadata import version as _iv
        return _iv(pkg_name or mod.__name__)
    except Exception:
        return "unknown"

@app.get("/system/dependency-status")
def dependency_status():
    """Check status of all optional Python dependencies."""
    deps = {}
    # psutil
    try:
        import psutil
        deps["psutil"] = {"installed": True, "version": _get_version(psutil), "feature": "CPU/RAM monitoring"}
    except ImportError:
        deps["psutil"] = {"installed": False, "version": None, "feature": "CPU/RAM monitoring", "install_cmd": "pip install psutil"}
    # sentence-transformers
    try:
        import sentence_transformers
        deps["sentence-transformers"] = {"installed": True, "version": _get_version(sentence_transformers), "feature": "Text embeddings"}
    except ImportError:
        deps["sentence-transformers"] = {"installed": False, "version": None, "feature": "Text embeddings"}
    # hdbscan
    try:
        import hdbscan
        deps["hdbscan"] = {"installed": True, "version": _get_version(hdbscan, "hdbscan"), "feature": "Clustering"}
    except ImportError:
        deps["hdbscan"] = {"installed": False, "version": None, "feature": "Clustering"}
    # faiss
    try:
        import faiss
        deps["faiss"] = {"installed": True, "version": _get_version(faiss, "faiss"), "feature": "Vector search"}
    except ImportError:
        deps["faiss"] = {"installed": False, "version": None, "feature": "Vector search"}
    # nvidia-ml-py (GPU monitoring)
    try:
        import pynvml
        deps["nvidia-ml-py"] = {"installed": True, "version": _get_version(pynvml, "nvidia-ml-py"), "feature": "GPU monitoring"}
    except ImportError:
        deps["nvidia-ml-py"] = {"installed": False, "version": None, "feature": "GPU monitoring"}
    return deps

@app.post("/system/install-dependency")
def install_dependency(name: str = ""):
    """Install a Python dependency via pip."""
    if not name:
        raise HTTPException(400, "name parameter required")
    allowed = ["psutil", "nvidia-ml-py"]
    if name not in allowed:
        raise HTTPException(400, f"Dependency '{name}' not in allowed list: {allowed}")
    from backend.diagnostics import install_dependency
    result = install_dependency(name)
    return result

# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 4: LOGGING
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/logs")
def get_logs(channel: str = "", count: int = 50, severity: int = 0, search: str = ""):
    return {
        "logs": logs.get_logs(channel if channel else None, count, severity, search),
        "channels": logs.list_channels(),
    }

@app.post("/logs/clear")
def clear_logs(channel: str = ""):
    if channel:
        logs.clear_channel(channel)
    else:
        logs.clear_all()
    return {"status": "ok"}


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 5: SETUP / TOOLS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/setup/status")
def setup_status():
    return sm.get_installation_status()

@app.get("/setup/detect-cuda")
def setup_detect_cuda():
    return sm.detect_cuda()

@app.get("/llama/binary/download")
def llama_download_binary():
    from fastapi.responses import StreamingResponse
    def _stream():
        for event in sm.download_llama_binary():
            yield f"data: {json.dumps(event, default=str)}\n\n"
    return StreamingResponse(_stream(), media_type="text/event-stream")

@app.post("/llama/model/download")
def llama_download_model(req: ModelDownloadRequest):
    from fastapi.responses import StreamingResponse
    def _stream():
        for event in sm.download_llama_model(req.model_id):
            yield f"data: {json.dumps(event, default=str)}\n\n"
    return StreamingResponse(_stream(), media_type="text/event-stream")

@app.get("/llama/models")
def llama_list_models():
    from backend.llama_cpp import models as lm
    return {"downloaded": lm.list_available_models(), "recommended": lm.list_recommended()}

@app.delete("/llama/models")
@app.delete("/llama/models/delete")
def llama_delete_model(filename: str = ""):
    from backend.llama_cpp import models as lm
    if not filename:
        raise HTTPException(400, "filename required")
    lm.delete_model(filename)
    return {"status": "deleted", "model": filename}

@app.post("/setup/install")
def setup_install(req: InstallGroup):
    from fastapi.responses import StreamingResponse
    def _stream():
        for event in sm.install_package_group(req.group):
            yield f"data: {json.dumps(event, default=str)}\n\n"
    return StreamingResponse(_stream(), media_type="text/event-stream")


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION 6: MODEL MANAGEMENT (DETAILED)
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/model/status")
def model_status():
    return model_manager.status()

@app.post("/model/load")
def model_load(model_name: str = ""):
    ok = model_manager.load_model(model_name)
    if not ok:
        err = model_manager._server.loading_error
        if err:
            raise HTTPException(500, json.dumps(err))
        raise HTTPException(500, "Failed to load model")
    return {"status": "loaded", "model": model_name or "default"}

@app.post("/model/load_file")
async def model_load_file(file: UploadFile = File(...)):
    from backend.llama_cpp.models import MODELS_DIR
    import shutil
    if not file.filename or not file.filename.endswith(".gguf"):
        raise HTTPException(400, "Only .gguf files are accepted")
    dest = MODELS_DIR / file.filename
    logs.info("model_manager", f"[upload] Saving {file.filename} ({file.size} bytes)")
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    logs.info("model_manager", f"[upload] Saved {file.filename} to {dest}")
    ok = model_manager.load_model(str(dest))
    if not ok:
        err = model_manager._server.loading_error
        if err:
            raise HTTPException(500, json.dumps(err))
        raise HTTPException(500, "Failed to load model from file")
    return {"status": "loaded", "model": file.filename}

@app.post("/model/unload")
def model_unload():
    model_manager.unload_model()
    return {"status": "unloaded"}

@app.post("/model/warm")
def model_warm():
    model_manager.warm_up()
    return {"status": "warmed"}

@app.get("/model/health")
def model_health():
    return model_manager._server.health_check()

@app.get("/model/logs")
def model_logs(count: int = 50):
    from backend.logging_system import logs as _logs
    entries = _logs.get_logs(channel="model_manager", count=count)
    return {"logs": [e["message"] for e in entries]}

@app.get("/model/scan")
def model_scan():
    """Scan models folder and return detailed info about each GGUF file."""
    from backend.llama_cpp.models import MODELS_DIR, get_model_info
    files = []
    if MODELS_DIR.exists():
        for f in sorted(MODELS_DIR.iterdir()):
            if f.suffix == ".gguf":
                info = get_model_info(str(f))
                files.append(info)
    return {"models": files, "count": len(files)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
