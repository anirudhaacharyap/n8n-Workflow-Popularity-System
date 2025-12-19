from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, UniqueConstraint, Numeric
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    workflow_name = Column(String, nullable=False)
    normalized_name = Column(String, index=True)
    description = Column(Text)
    platform = Column(String, nullable=False, index=True)  # 'youtube', 'forum', 'google'
    country = Column(String, nullable=False, index=True)   # 'US', 'IN'
    source_url = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    metrics = relationship("PopularityMetric", back_populates="workflow", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('normalized_name', 'platform', 'country', name='uq_workflow_platform_country'),
    )


class PopularityMetric(Base):
    __tablename__ = "popularity_metrics"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    metric_date = Column(DateTime, default=datetime.utcnow, index=True)

    # YouTube specific
    views = Column(Integer, nullable=True)
    likes = Column(Integer, nullable=True)
    comments = Column(Integer, nullable=True)
    like_to_view_ratio = Column(Float, nullable=True)
    comment_to_view_ratio = Column(Float, nullable=True)

    # Forum specific
    replies = Column(Integer, nullable=True)
    unique_contributors = Column(Integer, nullable=True)

    # Google Trends specific
    search_volume = Column(Integer, nullable=True)
    interest_score = Column(Integer, nullable=True)
    trend_percentage = Column(Float, nullable=True)

    # Universal
    engagement_score = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    workflow = relationship("Workflow", back_populates="metrics")
    
    __table_args__ = (
        UniqueConstraint('workflow_id', 'metric_date', name='uq_workflow_metric_date'),
    )


class DataCollectionLog(Base):
    __tablename__ = "data_collection_logs"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, nullable=False)
    country = Column(String, nullable=False)
    status = Column(String, nullable=False)  # 'success', 'failed', 'partial'
    workflows_collected = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
