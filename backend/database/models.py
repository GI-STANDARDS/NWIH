import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, BigInteger
from sqlalchemy import Index
from backend.database.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), unique=True, index=True, nullable=False)
    video_id = Column(String(50), index=True)
    video_title = Column(String(500))
    video_url = Column(String(500))
    channel = Column(String(200))
    source_type = Column(String(20), default="video")
    total_comments = Column(Integer, default=0)
    comments_extracted = Column(Integer, default=0)
    comments_cleaned = Column(Integer, default=0)
    comments_embedded = Column(Integer, default=0)
    clusters_found = Column(Integer, default=0)
    status = Column(String(20), default="pending")
    progress = Column(Float, default=0.0)
    error = Column(Text)
    result = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), index=True, nullable=False)
    comment_id = Column(String(100), index=True)
    video_id = Column(String(50), index=True)
    batch_id = Column(Integer, default=0)
    author = Column(String(200))
    text_original = Column(Text)
    text_cleaned = Column(Text)
    comment_length = Column(Integer, default=0)
    language = Column(String(10))
    like_count = Column(Integer, default=0)
    published_at = Column(DateTime)
    is_reply = Column(Boolean, default=False)
    is_spam = Column(Boolean, default=False)
    has_links = Column(Boolean, default=False)
    sentiment_label = Column(String(20))
    sentiment_score = Column(Float)
    feature_mentions = Column(JSON)
    willingness_to_pay = Column(Boolean, default=False)
    wtp_amount = Column(Float)
    urgency = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_job_video", "job_id", "video_id"),
        Index("idx_job_spam", "job_id", "is_spam"),
    )


class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), index=True, nullable=False)
    cluster_id = Column(Integer)
    label = Column(String(200))
    summary = Column(Text)
    size = Column(Integer, default=0)
    frequency_pct = Column(Float)
    sentiment_positive_pct = Column(Float)
    sentiment_negative_pct = Column(Float)
    sentiment_neutral_pct = Column(Float)
    avg_likes = Column(Float)
    purchase_intent_count = Column(Integer)
    urgency = Column(String(20))
    demand_score = Column(Float)
    keywords = Column(JSON)
    sample_comments = Column(JSON)
    llm_analysis = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
