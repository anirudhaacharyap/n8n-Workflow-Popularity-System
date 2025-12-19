import logging
import asyncio
from typing import List, Dict, Any
from datetime import datetime, timedelta
from pytrends.request import TrendReq
from app.core.config import settings

logger = logging.getLogger(__name__)

class TrendsCollector:
    def __init__(self):
        # hl='en-US', tz=360 to align with US time
        self.pytrends = TrendReq(hl='en-US', tz=360, retries=3, backoff_factor=1)

    async def get_trends_data(self, keyword: str, country_code: str = 'US') -> Dict[str, Any]:
        """
        Fetch trends data for a single keyword (or list of keywords, but pytrends handles 5 max).
        """
        # Pytrends is synchronous, so we might want to wrap in run_in_executor if used in async context extensively.
        # But for daily scheduled jobs, blocking briefly is acceptable or we run it in a thread.
        try:
            # Run in a thread to avoid blocking the event loop
            return await asyncio.to_thread(self._fetch_pytrends, keyword, country_code)
        except Exception as e:
            logger.error(f"Error serving trends for {keyword}: {str(e)}")
            return {}

    def _fetch_pytrends(self, keyword: str, country_code: str) -> Dict[str, Any]:
        try:
            self.pytrends.build_payload([keyword], cat=0, timeframe='today 3-m', geo=country_code, gprop='')
            
            # Interest over time
            interest_over_time_df = self.pytrends.interest_over_time()
            if interest_over_time_df.empty:
                return {}

            # Calculate metrics
            mean_interest = float(interest_over_time_df[keyword].mean())
            last_value = int(interest_over_time_df[keyword].iloc[-1])
            
            # Calculate trend percentage (last 30 days vs previous 30 days roughly)
            # data is usually weekly or daily depending on timeframe. 'today 3-m' is daily.
            if len(interest_over_time_df) > 60:
                recent = interest_over_time_df[keyword].iloc[-30:].mean()
                previous = interest_over_time_df[keyword].iloc[-60:-30].mean()
                trend_percent = ((recent - previous) / previous * 100) if previous > 0 else 0.0
            else:
                trend_percent = 0.0

            # Related queries (Rising)
            related_queries = self.pytrends.related_queries()
            related_top = []
            if related_queries and keyword in related_queries:
                top_df = related_queries[keyword]['top']
                if top_df is not None:
                    related_top = top_df['query'].head(5).tolist()

            return {
                'interest_score': int(mean_interest), # Average interest over 3 months
                'current_interest': last_value,
                'trend_percentage': round(trend_percent, 2),
                'related_queries': related_top
            }
        except Exception as e:
            logger.warning(f"Failed to fetch pytrends for {keyword} in {country_code}: {e}")
            return {}

    async def collect_workflows(self, keywords: List[str], countries: List[str] = ['US', 'IN']) -> List[Dict[str, Any]]:
        """
        Collect trends for a list of keywords.
        """
        results = []
        
        for country in countries:
            for keyword in keywords:
                # Add a small delay to be nice to Google's rate limits
                await asyncio.sleep(2) 
                
                logger.info(f"Fetching Google Trends for '{keyword}' in {country}...")
                data = await self.get_trends_data(keyword, country_code=country)
                
                if not data:
                    continue
                
                workflow_data = {
                    'platform': 'google',
                    'country': country,
                    'workflow_name': keyword, # For Trends, the "workflow" is essentially the search term
                    'description': f"Related: {', '.join(data.get('related_queries', []))}",
                    'source_url': f"https://trends.google.com/trends/explore?q={keyword}&geo={country}",
                    'created_at': datetime.utcnow(),
                    
                    'metrics': {
                        'search_volume': 0, # pytrends doesn't give absolute volume without reference
                        'interest_score': data.get('interest_score', 0),
                        'trend_percentage': data.get('trend_percentage', 0.0),
                        'engagement_score': data.get('current_interest', 0) # Use current interest as proxy
                    }
                }
                results.append(workflow_data)
        
        return results
