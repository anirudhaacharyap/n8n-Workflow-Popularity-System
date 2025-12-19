from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

# --- Metrics Schemas ---
class MetricsBase(BaseModel):
    views: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    like_to_view_ratio: Optional[float] = None
    comment_to_view_ratio: Optional[float] = None
    replies: Optional[int] = None
    unique_contributors: Optional[int] = None
    search_volume: Optional[int] = None
    interest_score: Optional[int] = None
    trend_percentage: Optional[float] = None
    engagement_score: Optional[float] = None

class MetricsOut(MetricsBase):
    metric_date: datetime

    class Config:
        from_attributes = True

# --- Workflow Schemas ---
class WorkflowBase(BaseModel):
    workflow: str
    description: Optional[str] = None
    platform: str
    country: str
    source_url: Optional[str] = None

class WorkflowOut(WorkflowBase):
    id: int
    created_at: datetime
    updated_at: datetime
    popularity_metrics: Optional[MetricsOut] = None

    class Config:
        from_attributes = True

class WorkflowList(BaseModel):
    total: int
    items: List[WorkflowOut]
    page: int
    size: int

# --- Platform Stats Schema ---
class PlatformStat(BaseModel):
    platform: str
    total_workflows: int
    countries: dict[str, int]
    avg_engagement: float

class PlatformStatsResponse(BaseModel):
    platforms: List[PlatformStat]
