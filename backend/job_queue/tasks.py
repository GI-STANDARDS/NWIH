"""
Background task definitions for the processing pipeline.
Each function emits progress events for real-time SSE streaming.
"""
import json
import time
from datetime import datetime
from typing import Generator

from sqlalchemy.orm import Session

from backend.database.database import SessionLocal
from backend.database.models import Job, Comment, Cluster
from backend.extractor.youtube import extract_comments_batch
from backend.cleaning.normalize import clean_comment
from backend.analysis.sentiment import analyze_sentiment
from backend.analysis.demand import extract_features, detect_purchase_intent, assess_urgency, compute_demand_score
from backend.embeddings.embedder import generate_embeddings_batch, is_available as emb_available
from backend.clustering.cluster import cluster_embeddings, is_available as cluster_available
from backend.model_manager import manager as model_manager
from backend.analysis.competitors import count_term_mentions
from backend.vector_db.store import store as vector_store
from backend.export.exporter import export_job_result
from backend.analysis.insights import analyze_insights
from backend.config import EXTRACT_BATCH_SIZE, MAX_COMMENTS_PER_JOB
from backend.progress import tracker as progress_tracker



def update_job_progress(job_id: str, field: str, value, commit: bool = True):
    """Update job status in DB."""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if job:
            setattr(job, field, value)
            job.updated_at = datetime.utcnow()
            if commit:
                db.commit()
    finally:
        db.close()


def task_extract_comments(job_id: str, video_url: str, max_comments: int = MAX_COMMENTS_PER_JOB):
    """Phase 1: Extract comments in batches, clean + store. Emits live progress."""
    from backend.extractor.youtube import extract_video_id, extract_video_info
    video_id = extract_video_id(video_url)
    if not video_id:
        update_job_progress(job_id, "status", "error")
        update_job_progress(job_id, "error", "Invalid YouTube URL")
        progress_tracker.set_error(job_id, "Invalid YouTube URL")
        return

    # Fetch video metadata (title, channel)
    try:
        video_info = extract_video_info(video_url)
        video_title = video_info.get("title", "")
        channel = video_info.get("channel", "")
        update_job_progress(job_id, "video_title", video_title)
        update_job_progress(job_id, "channel", channel)
        progress_tracker.add_activity(job_id, "🎬", f"Video: {video_title[:50]}...")
    except Exception as e:
        print(f"[tasks] Failed to fetch video info: {e}")
        video_title = ""
        channel = ""

    update_job_progress(job_id, "status", "extracting")
    update_job_progress(job_id, "video_id", video_id)
    progress_tracker.set_stage(job_id, "fetching_info")
    progress_tracker.set_progress(job_id, 2)

    total_extracted = 0
    batch_num = 0
    db = SessionLocal()
    start_time = time.time()

    try:
        for batch in extract_comments_batch(video_id, max_comments=max_comments, batch_size=EXTRACT_BATCH_SIZE):
            if progress_tracker.is_cancelled(job_id):
                progress_tracker.add_activity(job_id, "⏹", "Download cancelled by user")
                db.close()
                return

            batch_num += 1
            comments_to_insert = []
            batch_start = time.time()

            for c in batch:
                if progress_tracker.is_cancelled(job_id):
                    break
                cleaned = clean_comment(c.get("text_original", ""))
                sl, ss = analyze_sentiment(cleaned["text_cleaned"])
                feats = extract_features(cleaned["text_cleaned"])
                pi = detect_purchase_intent(cleaned["text_cleaned"])
                urg = assess_urgency(cleaned["text_cleaned"])

                comments_to_insert.append(Comment(
                    job_id=job_id,
                    comment_id=c.get("comment_id"),
                    video_id=video_id,
                    batch_id=batch_num,
                    author=c.get("author"),
                    text_original=cleaned["text_original"],
                    text_cleaned=cleaned["text_cleaned"],
                    comment_length=cleaned["comment_length"],
                    language=cleaned["language"],
                    like_count=c.get("like_count", 0),
                    published_at=c.get("published_at"),
                    is_reply=c.get("is_reply", False),
                    is_spam=cleaned["is_spam"],
                    has_links=cleaned["has_links"],
                    sentiment_label=sl,
                    sentiment_score=ss,
                    feature_mentions=feats,
                    willingness_to_pay=pi["has_intent"],
                    wtp_amount=pi["amount"],
                    urgency=urg,
                ))

            # Batch insert (add_all ensures autoincrement works on SQLite)
            db.add_all(comments_to_insert)
            db.flush()
            db.commit()

            batch_count = len(comments_to_insert)
            total_extracted += batch_count
            batch_time = time.time() - batch_start
            speed = batch_count / max(batch_time, 0.001)
            elapsed = time.time() - start_time

            # Live counters
            progress_tracker.inc_counter(job_id, "comments_downloaded", batch_count)
            progress_tracker.inc_counter(job_id, "comments_processed", batch_count)
            progress_tracker.set_counter(job_id, "comments_remaining", max(0, max_comments - total_extracted))

            # Live metrics
            progress_tracker.set_metrics(job_id, {
                "download_speed": round(speed, 1),
                "process_speed": round(speed, 1),
            })

            # Stage progress (download = 0-25%)
            pct = min(total_extracted / max(max_comments, 1) * 25, 25)
            progress_tracker.set_progress(job_id, round(pct, 1))

            # Update DB — use commit=True so each update is persisted in its own session
            update_job_progress(job_id, "comments_extracted", total_extracted)
            update_job_progress(job_id, "progress", round(pct + 5, 1))
            update_job_progress(job_id, "status", "extracting")
            db.commit()

            # Activity every few batches
            if batch_num % 3 == 0:
                progress_tracker.add_activity(job_id, "📥",
                    f"Downloaded {total_extracted} comments ({speed:.0f}/sec)")

        progress_tracker.set_stage(job_id, "parsing")
        progress_tracker.add_activity(job_id, "✅",
            f"Download complete: {total_extracted} comments in {batch_num} batches")
        update_job_progress(job_id, "total_comments", total_extracted)
        update_job_progress(job_id, "progress", 30)

    except Exception as e:
        db.rollback()
        update_job_progress(job_id, "status", "error")
        update_job_progress(job_id, "error", str(e))
        progress_tracker.set_error(job_id, str(e))
    finally:
        db.close()


def task_clean_and_embed(job_id: str):
    """Phase 2: Clean and generate embeddings in batches. Emits live progress."""
    if not emb_available():
        update_job_progress(job_id, "status", "error")
        update_job_progress(job_id, "error", "sentence-transformers not installed")
        progress_tracker.set_error(job_id, "sentence-transformers not installed")
        return

    from backend.embeddings.embedder import generate_embeddings_batch

    progress_tracker.set_stage(job_id, "cleaning")
    update_job_progress(job_id, "status", "embedding")
    db = SessionLocal()
    start_time = time.time()
    try:
        offset = 0
        batch_size = 512
        total_embedded = 0

        while True:
            if progress_tracker.is_cancelled(job_id):
                progress_tracker.add_activity(job_id, "⏹", "Embedding cancelled by user")
                return

            comments = db.query(Comment).filter(
                Comment.job_id == job_id,
                Comment.is_spam == False,
                Comment.comment_length > 2,
            ).offset(offset).limit(batch_size).all()

            if not comments:
                break

            texts = [c.text_cleaned for c in comments]
            if texts:
                progress_tracker.set_stage(job_id, "embedding")
                batch_start = time.time()
                embeddings = generate_embeddings_batch(texts, batch_size=256)
                batch_time = time.time() - batch_start
                vector_store.add(embeddings, [c.id for c in comments])
                speed = len(comments) / max(batch_time, 0.001)
                progress_tracker.set_metrics(job_id, {"process_speed": round(speed, 1)})

            total_embedded += len(comments)
            offset += batch_size

            # Live counters
            progress_tracker.set_counter(job_id, "comments_analyzed", total_embedded)
            progress_tracker.set_counter(job_id, "comments_processed", total_embedded)

            job_total = db.query(Job).filter(Job.job_id == job_id).first()
            total = job_total.total_comments if job_total else 1
            pct = 30 + min(total_embedded / max(total, 1) * 30, 30)
            progress_tracker.set_progress(job_id, round(pct, 1))

            update_job_progress(job_id, "comments_embedded", total_embedded, commit=False)
            update_job_progress(job_id, "progress", round(pct, 1))

            if total_embedded % 1000 == 0:
                progress_tracker.add_activity(job_id, "🧠",
                    f"Embedded {total_embedded}/{total} comments ({speed:.0f}/sec)")

            db.commit()

        progress_tracker.set_stage(job_id, "building_index")
        progress_tracker.add_activity(job_id, "📦", f"Vector index built: {total_embedded} vectors")
        update_job_progress(job_id, "progress", 60)

    except Exception as e:
        db.rollback()
        update_job_progress(job_id, "status", "error")
        update_job_progress(job_id, "error", str(e))
        progress_tracker.set_error(job_id, str(e))
    finally:
        db.close()


def task_cluster_ml(job_id: str):
    """Phase 3: Cluster all embeddings (ML-only). Returns clusters_data list."""
    if not cluster_available():
        update_job_progress(job_id, "status", "error")
        update_job_progress(job_id, "error", "hdbscan not installed")
        progress_tracker.set_error(job_id, "hdbscan not installed")
        return []

    progress_tracker.set_stage(job_id, "clustering")
    update_job_progress(job_id, "status", "clustering")
    progress_tracker.add_activity(job_id, "🔄", "Starting clustering...")
    progress_tracker.set_progress(job_id, 62)

    db = SessionLocal()
    try:
        total_vecs = vector_store.total()
        if total_vecs == 0:
            update_job_progress(job_id, "status", "error")
            update_job_progress(job_id, "error", "No embeddings to cluster")
            progress_tracker.set_error(job_id, "No embeddings to cluster")
            return []

        all_embeddings = vector_store.get_all_embeddings()
        progress_tracker.add_activity(job_id, "🔢", f"Clustering {total_vecs} vectors...")
        progress_tracker.set_progress(job_id, 65)

        labels, clusterer = cluster_embeddings(all_embeddings)

        cluster_map = {}
        for idx, label in enumerate(labels):
            if label == -1:
                continue
            label = int(label)
            if label not in cluster_map:
                cluster_map[label] = []
            cluster_map[label].append(idx)

        total_comments = len(labels)
        num_clusters = len(cluster_map)
        progress_tracker.add_activity(job_id, "📊", f"Found {num_clusters} clusters from {total_comments} comments")
        progress_tracker.set_progress(job_id, 70)

        clusters_data = []

        for i, (cluster_id, member_indices) in enumerate(cluster_map.items()):
            if progress_tracker.is_cancelled(job_id):
                progress_tracker.add_activity(job_id, "⏹", "Clustering cancelled by user")
                return clusters_data

            size = len(member_indices)
            if size < 5:
                continue

            freq_pct = round(size / max(total_comments, 1) * 100, 1)
            member_ids = []
            for idx in member_indices:
                raw_id = vector_store._id_map.get(str(idx))
                if raw_id is not None:
                    member_ids.append(int(raw_id))

            comments = db.query(Comment).filter(Comment.id.in_(member_ids[:100])).all() if member_ids else []

            sentiments = [c.sentiment_label for c in comments]
            pos = sentiments.count("positive") / max(size, 1) * 100
            neg = sentiments.count("negative") / max(size, 1) * 100
            avg_likes = sum(c.like_count for c in comments) / max(size, 1)
            purchase_count = sum(1 for c in comments if c.willingness_to_pay)

            urgencies = [c.urgency for c in comments]
            urgency = "high" if urgencies.count("high") > size / 3 else \
                      "medium" if urgencies.count("medium") > size / 3 else "low"

            all_feats = {}
            for c in comments:
                if c.feature_mentions:
                    for f, cnt in c.feature_mentions.items():
                        all_feats[f] = all_feats.get(f, 0) + cnt

            sample = [c.text_original for c in comments[:5]]

            demand = compute_demand_score({
                "frequency_pct": freq_pct,
                "sentiment_negative_pct": round(neg, 1),
                "urgency": urgency,
                "purchase_intent_pct": round(purchase_count / max(size, 1) * 100, 1),
            })

            cluster_obj = Cluster(
                job_id=job_id,
                cluster_id=int(cluster_id),
                label=f"Cluster {cluster_id}",
                size=size,
                frequency_pct=freq_pct,
                sentiment_positive_pct=round(pos, 1),
                sentiment_negative_pct=round(neg, 1),
                sentiment_neutral_pct=round(100 - pos - neg, 1),
                avg_likes=round(avg_likes, 1),
                purchase_intent_count=purchase_count,
                urgency=urgency,
                demand_score=demand,
                keywords=all_feats,
                sample_comments=sample,
            )
            db.add(cluster_obj)
            db.flush()

            clusters_data.append({
                "id": cluster_obj.id,
                "cluster_id": cluster_id,
                "label": f"Cluster {cluster_id}",
                "size": size,
                "frequency_pct": freq_pct,
                "sentiment_positive_pct": round(pos, 1),
                "sentiment_negative_pct": round(neg, 1),
                "demand_score": demand,
                "urgency": urgency,
                "purchase_intent_count": purchase_count,
                "keywords": all_feats,
                "sample_comments": sample,
            })

            # Progress within clustering (70-80%)
            pct = 70 + min((i + 1) / max(len(cluster_map), 1) * 10, 10)
            progress_tracker.set_progress(job_id, round(pct, 1))

        db.commit()
        progress_tracker.set_stage(job_id, "sentiment")
        progress_tracker.add_activity(job_id, "📈", f"Sentiment analysis: {num_clusters} clusters profiled")
        update_job_progress(job_id, "clusters_found", len(clusters_data))
        update_job_progress(job_id, "progress", 80)
        progress_tracker.set_progress(job_id, 80)

        return clusters_data

    except Exception as e:
        db.rollback()
        update_job_progress(job_id, "status", "error")
        update_job_progress(job_id, "error", str(e))
        progress_tracker.set_error(job_id, str(e))
        return []
    finally:
        db.close()


def task_llm_analyze_clusters(job_id: str, clusters_data: list):
    """Phase 4: LLM analysis per cluster (optional, GGUF-dependent)."""
    if not clusters_data:
        return
    if not model_manager.is_ready():
        print(f"[tasks] LLM not available, skipping AI analysis for job {job_id}")
        progress_tracker.set_stage(job_id, "clustering")
        progress_tracker.add_activity(job_id, "⚡", "AI analysis skipped (no GGUF model loaded)")
        update_job_progress(job_id, "status", "clustering")
        return

    progress_tracker.set_stage(job_id, "llm_analysis")
    update_job_progress(job_id, "status", "analyzing")
    progress_tracker.add_activity(job_id, "🤖", "Starting AI cluster analysis...")
    db = SessionLocal()
    try:
        ok = model_manager.load_model()
        if not ok:
            progress_tracker.add_activity(job_id, "⚠️", "AI model failed to load, skipping LLM analysis")
            return
        for i, cd in enumerate(clusters_data):
            if progress_tracker.is_cancelled(job_id):
                return
            analysis = model_manager.analyze_cluster(cd)
            if analysis:
                db.query(Cluster).filter(Cluster.id == cd["id"]).update(
                    {"llm_analysis": analysis}
                )
                db.commit()
                progress_tracker.add_activity(job_id, "🧠",
                    f"AI analyzed cluster {i+1}/{len(clusters_data)}")
            pct = 80 + min((i + 1) / max(len(clusters_data), 1) * 15, 15)
            progress_tracker.set_progress(job_id, round(pct, 1))
        update_job_progress(job_id, "progress", 95)
        progress_tracker.add_activity(job_id, "✅", "AI analysis complete")
    except Exception as e:
        print(f"[tasks] LLM analysis error: {e}")
        progress_tracker.add_activity(job_id, "⚠️", f"AI analysis error: {e}")
    finally:
        db.close()


def task_cluster_and_analyze(job_id: str, use_llm: bool = False):
    """Phase 3+4+5: Cluster, optionally analyze with LLM, then finalize."""
    clusters_data = task_cluster_ml(job_id)
    if not clusters_data:
        return

    if use_llm:
        task_llm_analyze_clusters(job_id, clusters_data)

    if progress_tracker.is_cancelled(job_id):
        progress_tracker.add_activity(job_id, "⏹", "Processing cancelled")
        return

    _task_finalize(job_id)


def _task_finalize(job_id: str):
    """Phase 5: Generate final result and mark job completed."""
    progress_tracker.set_stage(job_id, "stats")
    update_job_progress(job_id, "status", "finalizing")
    progress_tracker.add_activity(job_id, "📊", "Calculating statistics...")
    progress_tracker.set_progress(job_id, 96)

    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.job_id == job_id).first()
        all_clusters = db.query(Cluster).filter(Cluster.job_id == job_id).all()

        all_comments = db.query(Comment).filter(
            Comment.job_id == job_id,
            Comment.is_spam == False,
        ).limit(10000).all()

        progress_tracker.add_activity(job_id, "🏷️", "Analyzing topic terms...")
        competitors = count_term_mentions(all_comments)

        progress_tracker.set_stage(job_id, "finalizing")
        progress_tracker.add_activity(job_id, "📝", "Generating report...")
        clusters_payload = [{"cluster_id": c.cluster_id, "label": c.label, "size": c.size,
              "frequency_pct": c.frequency_pct, "demand_score": c.demand_score,
              "urgency": c.urgency, "sentiment_positive_pct": c.sentiment_positive_pct,
              "sentiment_negative_pct": c.sentiment_negative_pct,
              "purchase_intent_count": c.purchase_intent_count,
              "keywords": c.keywords, "sample_comments": c.sample_comments,
              "llm_analysis": c.llm_analysis if c.llm_analysis else {}}
             for c in all_clusters]
        insights = analyze_insights(clusters_payload, all_comments)
        result = export_job_result(
            {"video_title": job.video_title, "video_url": job.video_url,
             "total_comments": job.total_comments, "comments_extracted": job.comments_extracted},
            clusters_payload,
            competitors,
            insights,
        )

        job.result = result
        job.status = "completed"
        job.progress = 100
        job.completed_at = datetime.utcnow()
        db.commit()

        progress_tracker.set_stage(job_id, "completed")
        progress_tracker.set_progress(job_id, 100)
        progress_tracker.set_result_ready(job_id)
        progress_tracker.add_activity(job_id, "🎉", "Processing complete! Report ready.")
    except Exception as e:
        db.rollback()
        update_job_progress(job_id, "status", "error")
        update_job_progress(job_id, "error", str(e))
        progress_tracker.set_error(job_id, str(e))
    finally:
        db.close()


def task_llm_analyze_job(job_id: str):
    """Run LLM analysis on an already-completed job."""
    db = SessionLocal()
    try:
        clusters = db.query(Cluster).filter(Cluster.job_id == job_id).all()
        if not clusters:
            return 0
        clusters_data = []
        for c in clusters:
            cd = {
                "id": c.id,
                "cluster_id": c.cluster_id,
                "label": c.label,
                "size": c.size,
                "frequency_pct": c.frequency_pct,
                "sentiment_positive_pct": c.sentiment_positive_pct,
                "sentiment_negative_pct": c.sentiment_negative_pct,
                "demand_score": c.demand_score,
                "urgency": c.urgency,
                "purchase_intent_count": c.purchase_intent_count,
                "keywords": c.keywords,
                "sample_comments": c.sample_comments,
            }
            clusters_data.append(cd)

        if not model_manager.is_ready():
            print(f"[tasks] LLM not available for job {job_id}")
            return -1
        ok = model_manager.load_model()
        if not ok:
            return -1
        count = 0
        for cd in clusters_data:
            analysis = model_manager.analyze_cluster(cd)
            if analysis:
                db.query(Cluster).filter(Cluster.id == cd["id"]).update(
                    {"llm_analysis": analysis}
                )
                db.commit()
                count += 1
        return count
    except Exception as e:
        print(f"[tasks] LLM job analysis error: {e}")
        return -1
    finally:
        db.close()
