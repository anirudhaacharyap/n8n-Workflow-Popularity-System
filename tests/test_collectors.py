import pytest
from app.core.normalization import Normalizer
from app.collectors.youtube import YouTubeCollector

def test_normalization():
    norm = Normalizer()
    assert norm.normalize_workflow_name("Google Sheets -> Slack") == "google sheets slack"
    assert norm.normalize_workflow_name("n8n   Automation!!!") == "n8n automation"

def test_engagement_calculation():
    collector = YouTubeCollector()
    # Formula: (likes * 2 + comments * 3) / views * 10000
    # (10*2 + 5*3) / 1000 * 10000 = (20 + 15) / 1000 * 10000 = 35 / 1000 * 10000 = 350.0
    score = collector.calculate_engagement_score(views=1000, likes=10, comments=5)
    assert score == 350.0

def test_engagement_zero_views():
    collector = YouTubeCollector()
    score = collector.calculate_engagement_score(views=0, likes=10, comments=5)
    assert score == 0.0
