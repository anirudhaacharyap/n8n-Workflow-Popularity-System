import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.core.config import settings
from app.core.decorators import async_retry

logger = logging.getLogger(__name__)

class YouTubeCollector:
    def __init__(self):
        self.api_key = settings.YOUTUBE_API_KEY
        if not self.api_key:
            logger.warning("YOUTUBE_API_KEY is not set. YouTube collection will fail.")
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)

    @async_retry(max_retries=3, delay=1, backoff=2, exceptions=(HttpError,))
    async def search_videos(self, query: str, country_code: str = 'US', max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Search for videos matching the query and country code.
        """
        try:
            # Calculate publishedAfter date (e.g., last 30 days to keep it relevant, or none for all time)
            # For this project, we might want "all relevant" but let's stick to recent or relevance.
            # PRD implies finding "n8n workflow videos", could be any time.
            
            search_response = self.youtube.search().list(
                q=query,
                part='id,snippet',
                maxResults=max_results,
                type='video',
                regionCode=country_code,
                relevanceLanguage='en',
                order='relevance' 
            ).execute()

            videos = []
            for item in search_response.get('items', []):
                videos.append({
                    'video_id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'published_at': item['snippet']['publishedAt'],
                    'channel_title': item['snippet']['channelTitle'],
                    'thumbnail': item['snippet']['thumbnails']['high']['url']
                })
            return videos

        except HttpError as e:
            logger.error(f"An HTTP error %d occurred:\n%s", e.resp.status, e.content)
            return []
        except Exception as e:
            logger.error(f"Error searching YouTube videos: {str(e)}")
            return []

    @async_retry(max_retries=3, delay=1, backoff=2)
    async def get_video_statistics(self, video_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for a list of video IDs.
        YouTube API supports batching up to 50 IDs.
        """
        stats_map = {}
        
        # Process in chunks of 50
        chunk_size = 50
        for i in range(0, len(video_ids), chunk_size):
            chunk = video_ids[i:i + chunk_size]
            try:
                stats_response = self.youtube.videos().list(
                    part='statistics,contentDetails',
                    id=','.join(chunk)
                ).execute()

                for item in stats_response.get('items', []):
                    stats = item.get('statistics', {})
                    vid_id = item['id']
                    
                    # Parse duration if needed, but PRD focuses on simple metrics
                    view_count = int(stats.get('viewCount', 0))
                    like_count = int(stats.get('likeCount', 0))
                    comment_count = int(stats.get('commentCount', 0))
                    
                    stats_map[vid_id] = {
                        'views': view_count,
                        'likes': like_count,
                        'comments': comment_count
                    }
            except HttpError as e:
                logger.error(f"Error fetching stats for batch: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error fetching stats: {str(e)}")
        
        return stats_map

    def calculate_engagement_score(self, views: int, likes: int, comments: int) -> float:
        """
        Calculate engagement score based on PRD formula:
        engagement_score = (likes * 2 + comments * 3) / views * 10000
        """
        if views == 0:
            return 0.0
        
        score = (likes * 2 + comments * 3) / views * 10000
        return round(score, 4)

    async def collect_workflows(self, queries: List[str], countries: List[str] = ['US', 'IN']) -> List[Dict[str, Any]]:
        """
        Main method to collect workflows from YouTube for given queries and countries.
        """
        results = []
        
        for country in countries:
            for query in queries:
                logger.info(f"Searching YouTube for '{query}' in {country}...")
                videos = await self.search_videos(query, country_code=country)
                
                if not videos:
                    continue
                
                video_ids = [v['video_id'] for v in videos]
                stats_map = await self.get_video_statistics(video_ids)
                
                for video in videos:
                    vid_id = video['video_id']
                    if vid_id not in stats_map:
                        continue
                        
                    stats = stats_map[vid_id]
                    views = stats['views']
                    likes = stats['likes']
                    comments = stats['comments']
                    
                    # Filter out garbage
                    if views < 10:
                        continue

                    engagement_score = self.calculate_engagement_score(views, likes, comments)
                    
                    # Calculate ratios
                    like_to_view = (likes / views) if views > 0 else 0.0
                    comment_to_view = (comments / views) if views > 0 else 0.0

                    workflow_data = {
                        'platform': 'youtube',
                        'country': country,
                        'workflow_name': video['title'],
                        'description': video['description'],
                        'source_url': f"https://www.youtube.com/watch?v={vid_id}",
                        'created_at': video['published_at'], # This is published date
                        
                        'metrics': {
                            'views': views,
                            'likes': likes,
                            'comments': comments,
                            'engagement_score': engagement_score,
                            'like_to_view_ratio': round(like_to_view, 6),
                            'comment_to_view_ratio': round(comment_to_view, 6)
                        }
                    }
                    results.append(workflow_data)
        
        return results
