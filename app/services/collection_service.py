import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from typing import List, Dict, Any

from app.models import Workflow, PopularityMetric, DataCollectionLog
from app.core.normalization import Normalizer
from app.collectors.youtube import YouTubeCollector
from app.collectors.forum import ForumCollector
from app.collectors.trends import TrendsCollector

logger = logging.getLogger(__name__)

class CollectionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.normalizer = Normalizer()
        self.youtube_collector = YouTubeCollector()
        self.forum_collector = ForumCollector()
        self.trends_collector = TrendsCollector()

    async def _save_workflow_data(self, data: Dict[str, Any]):
        """
        Save or update workflow and its metrics.
        """
        try:
            workflow_name = data['workflow_name']
            normalized_name = self.normalizer.normalize_workflow_name(workflow_name)
            platform = data['platform']
            country = data['country']
            
            # Check if workflow exists
            query = select(Workflow).where(
                Workflow.normalized_name == normalized_name,
                Workflow.platform == platform,
                Workflow.country == country
            )
            result = await self.db.execute(query)
            workflow = result.scalar_one_or_none()
            
            if not workflow:
                workflow = Workflow(
                    workflow_name=workflow_name,
                    normalized_name=normalized_name,
                    description=data.get('description'),
                    platform=platform,
                    country=country,
                    source_url=data.get('source_url'),
                    created_at=data.get('created_at')
                )
                self.db.add(workflow)
                await self.db.flush() # Get ID
            else:
                # Update basic fields if needed
                pass

            # Add Metrics
            metrics_data = data['metrics']
            metric = PopularityMetric(
                workflow_id=workflow.id,
                views=metrics_data.get('views'),
                likes=metrics_data.get('likes'),
                comments=metrics_data.get('comments'),
                like_to_view_ratio=metrics_data.get('like_to_view_ratio'),
                comment_to_view_ratio=metrics_data.get('comment_to_view_ratio'),
                replies=metrics_data.get('replies'),
                unique_contributors=metrics_data.get('unique_contributors'),
                search_volume=metrics_data.get('search_volume'),
                interest_score=metrics_data.get('interest_score'),
                trend_percentage=metrics_data.get('trend_percentage'),
                engagement_score=metrics_data.get('engagement_score')
            )
            self.db.add(metric)
            
        except IntegrityError:
            await self.db.rollback()
            logger.warning(f"Integrity Error saving {data.get('workflow_name')}")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error saving workflow {data.get('workflow_name')}: {str(e)}")

    async def collect_all(self):
        """
        Trigger collection for all platforms.
        """
        # 1. YouTube
        try:
            yt_queries = ["n8n workflow tutorial", "n8n automation", "n8n integration"]
            yt_data = await self.youtube_collector.collect_workflows(yt_queries)
            for item in yt_data:
                await self._save_workflow_data(item)
            await self._log_collection('youtube', 'US', 'success', len(yt_data))
        except Exception as e:
            await self._log_collection('youtube', 'US', 'failed', 0, str(e))

        # 2. Forum
        try:
            forum_data = await self.forum_collector.collect_workflows()
            for item in forum_data:
                await self._save_workflow_data(item)
            await self._log_collection('forum', 'US', 'success', len(forum_data))
        except Exception as e:
            await self._log_collection('forum', 'US', 'failed', 0, str(e))
        
        # 3. Trends
        try:
            trends_keywords = ["n8n", "n8n automation", "zapier vs n8n"]
            trends_data = await self.trends_collector.collect_workflows(trends_keywords)
            for item in trends_data:
                await self._save_workflow_data(item)
            await self._log_collection('google', 'US', 'success', len(trends_data))
        except Exception as e:
            await self._log_collection('google', 'US', 'failed', 0, str(e))
        
        await self.db.commit()

    async def _log_collection(self, platform, country, status, count, error=None):
        log = DataCollectionLog(
            platform=platform,
            country=country,
            status=status,
            workflows_collected=count,
            error_message=error
        )
        self.db.add(log)
        try:
            await self.db.commit()
        except:
            await self.db.rollback()
