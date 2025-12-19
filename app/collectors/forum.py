import logging
import aiohttp
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.decorators import async_retry

logger = logging.getLogger(__name__)

class ForumCollector:
    BASE_URL = "https://community.n8n.io"
    
    def __init__(self):
        self.api_key = settings.DISCOURSE_API_KEY
        self.headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            self.headers["Api-Key"] = self.api_key
            # Most Discourse installs also require Api-Username
            # We'll assume public access for now unless specified
    
    @async_retry(max_retries=3, delay=1, backoff=2)
    async def fetch_latest_topics(self, page: int = 0) -> Dict[str, Any]:
        """
        Fetch latest topics from the forum.
        """
        url = f"{self.BASE_URL}/latest.json?page={page}"
        if not self.api_key:
             # Basic rate limiting for public access (heuristic)
            await asyncio.sleep(1) 

        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Error fetching forum topics: {response.status}")
                        return {}
        except Exception as e:
            logger.error(f"Exception fetching forum topics: {str(e)}")
            return {}

    @async_retry(max_retries=3, delay=1, backoff=2)
    async def get_topic_details(self, topic_id: int) -> Dict[str, Any]:
        """
        Get detailed stats for a specific topic.
        """
        url = f"{self.BASE_URL}/t/{topic_id}.json"
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Error fetching topic {topic_id}: {response.status}")
                        return {}
        except Exception as e:
            logger.error(f"Exception fetching topic {topic_id}: {str(e)}")
            return {}

    def calculate_metrics(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and calculate popularity metrics from a topic object.
        """
        views = topic.get('views', 0)
        reply_count = topic.get('reply_count', 0) # Discourse uses reply_count
        like_count = topic.get('like_count', 0)
        posts_count = topic.get('posts_count', 0)
        
        # Calculate engagement ratio: (replies + likes) / views
        engagement_ratio = 0.0
        if views > 0:
            engagement_ratio = (reply_count + like_count) / views
            
        # Unique contributors is harder to get without iterating posts, 
        # but sometimes 'details' has participant count.
        # For 'latest' endpoint, we might just get basic stats.
        # If we fetch topic details, we can get 'participant_count'.
        unique_contributors = topic.get('participant_count', 0)

        return {
            'views': views,
            'replies': reply_count,
            'likes': like_count,
            'posts_count': posts_count,
            'unique_contributors': unique_contributors,
            'engagement_score': round(engagement_ratio * 1000, 4) # Scale up essentially
        }

    async def collect_workflows(self, pages: int = 5) -> List[Dict[str, Any]]:
        """
        Collect workflows from the latest topics.
        """
        results = []
        
        logger.info(f"Collecting N8N forum topics for {pages} pages...")

        for page in range(pages):
            data = await self.fetch_latest_topics(page)
            if not data:
                break
                
            users = {u['id']: u['username'] for u in data.get('users', [])}
            topics = data.get('topic_list', {}).get('topics', [])
            
            for topic in topics:
                # Filter for relevant categories if needed. 
                # n8n has a 'Questions' category (id 4 or similar) and 'Share your workflow'
                # Let's collect all for popularity analysis but prioritized 'Share your workflow' is likely ID 12 or 10.
                # We won't filter hard yet, just collect data.
                
                metrics = self.calculate_metrics(topic)
                
                # Normalize data
                created_at_str = topic.get('created_at')
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00')) if created_at_str else datetime.utcnow()

                workflow_data = {
                    'platform': 'forum',
                    'country': 'US', # Forums are global, defaulting to US for schema or "Global" logic
                    'workflow_name': topic.get('title'),
                    'description': f"Category ID: {topic.get('category_id')}",
                    'source_url': f"{self.BASE_URL}/t/{topic.get('slug')}/{topic.get('id')}",
                    'created_at': created_at,
                    
                    'metrics': metrics
                }
                
                # Add duplicate entry for IN to satisfy the US/IN requirement if we treat forum as global source?
                # PRD mentions "Data Collection ... Country Filtering". 
                # Forums don't easily filter by country.
                # PRD says "Country Segmentation: Set geo parameter to US and IN" for Google, 
                # and "Country Filtering: Use regionCode" for YouTube.
                # For Forum, it just marks "Country Filtering" under YouTube. 
                # We will probably store it as 'US' (or 'Global' if schema allowed, but it's restricted to VARCHAR(2)).
                # Let's store as a primary record (US) and maybe later duplicate logic or just keep one.
                # I'll stick to 'US' as default since it's the primary market, or we can look for location data (hard).
                
                results.append(workflow_data)
        
        logger.info(f"Collected {len(results)} forum topics.")
        return results
