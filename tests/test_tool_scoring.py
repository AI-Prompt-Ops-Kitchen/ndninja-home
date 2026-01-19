import pytest
from scripts.tool_discovery.scorer import ToolScorer

def test_exact_keyword_match():
    """Test exact keyword match scores +10"""
    scorer = ToolScorer()
    tool = {
        'data': {
            'keywords': ['docker', 'container', 'debug']
        }
    }
    topics = ['docker environment issues']
    score = scorer.score_tool(tool, topics)
    assert score >= 10

def test_partial_keyword_match():
    """Test partial keyword match scores +5"""
    scorer = ToolScorer()
    tool = {
        'data': {
            'keywords': ['multi-model', 'analysis']
        }
    }
    topics = ['need multi-model comparison']
    score = scorer.score_tool(tool, topics)
    assert score >= 5

def test_recently_used_bonus():
    """Test recent usage adds +3 bonus"""
    from datetime import datetime, timedelta
    scorer = ToolScorer()
    recent_date = datetime.now() - timedelta(days=3)
    tool = {
        'data': {
            'keywords': ['test'],
            'last_used': recent_date.strftime('%Y-%m-%d')
        }
    }
    topics = ['test']
    score = scorer.score_tool(tool, topics)
    assert score >= 13  # 10 (exact) + 3 (recent)

def test_high_usage_bonus():
    """Test high use count adds +2 bonus"""
    scorer = ToolScorer()
    tool = {
        'data': {
            'keywords': ['test'],
            'use_count': 15
        }
    }
    topics = ['test']
    score = scorer.score_tool(tool, topics)
    assert score >= 12  # 10 (exact) + 2 (high usage)
