import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from core.social_service import SocialService
from core.sentiment_engine import SentimentEngine
from core.ai_service import AIService

@pytest.mark.asyncio
async def test_social_service_stocktwits_fallback():
    social_service = SocialService()
    # Mock StockTwits API failure gracefully
    with patch("httpx.AsyncClient.get", side_effect=Exception("API connection timeout")):
        messages = await social_service.fetch_stocktwits_messages("TSLA")
        assert messages == []

@pytest.mark.asyncio
async def test_social_service_guru_tweets():
    social_service = SocialService()
    posts = await social_service.fetch_guru_tweets("AAPL")
    assert len(posts) > 0
    assert any("Elon Musk" in p["guru"] for p in posts)

@pytest.mark.asyncio
async def test_sentiment_engine_analyze_combined():
    mock_ai = MagicMock(spec=AIService)
    mock_ai.analyze_sentiment_with_rotation = AsyncMock(return_value={
        "score": 85,
        "sentiment": "Bullish",
        "summary": "긍정적 시장 분위기",
        "reason": "신제품 호조 및 대가 매수세"
    })
    
    mock_social = MagicMock(spec=SocialService)
    mock_social.get_aggregated_social_data = AsyncMock(return_value={
        "symbol": "NVDA",
        "stocktwits": {"messages": [], "sentiment_score": 75.0},
        "guru_posts": [],
        "news_count": 2
    })

    with patch("core.sentiment_engine.get_stock_news", return_value=[{"title": "NVDA Record Earnings"}]):
        engine = SentimentEngine(mock_ai, mock_social)
        result = await engine.analyze_combined_sentiment("NVDA")

        assert result["symbol"] == "NVDA"
        assert result["sentiment_score"] == 85
        assert result["sentiment"] == "Bullish"
        assert "social_metrics" in result
