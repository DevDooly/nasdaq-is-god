import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.hybrid_strategy import HybridStrategyEngine
from core.indicator_service import IndicatorService
from core.sentiment_engine import SentimentEngine
from core.strategy_service import StrategyService
from core.models import TradingStrategy

@pytest.mark.asyncio
async def test_hybrid_strategy_engine_calculate_score():
    mock_indicator = MagicMock(spec=IndicatorService)
    mock_indicator.get_indicators = AsyncMock(return_value={
        "rsi": 25.0, # 과매도 -> RSI 스코어 = 75점
        "macd": {"hist": 2.0},
        "bollinger": {"upper": 120.0, "lower": 80.0},
        "current_price": 85.0
    })
    
    mock_sentiment = MagicMock(spec=SentimentEngine)
    mock_sentiment.analyze_combined_sentiment = AsyncMock(return_value={
        "sentiment_score": 80.0,
        "summary": "호재 다수",
        "reason": "실적 호조"
    })
    
    engine = HybridStrategyEngine(mock_indicator, mock_sentiment)
    result = await engine.evaluate_hybrid_signal(
        symbol="AAPL",
        strategy_type="HYBRID_RSI",
        tech_weight=0.6,
        buy_threshold=70.0,
        sell_threshold=35.0
    )
    
    assert result["symbol"] == "AAPL"
    # Tech Score = 75.0, Sent Score = 80.0 -> Hybrid Score = (75*0.6) + (80*0.4) = 45 + 32 = 77.0 >= 70.0 -> BUY
    assert result["technical_score"] == 75.0
    assert result["sentiment_score"] == 80.0
    assert result["hybrid_score"] == 77.0
    assert result["action"] == "BUY"

@pytest.mark.asyncio
async def test_strategy_service_hybrid_integration():
    mock_indicator = MagicMock(spec=IndicatorService)
    mock_hybrid = MagicMock(spec=HybridStrategyEngine)
    mock_hybrid.evaluate_hybrid_signal = AsyncMock(return_value={"action": "BUY"})
    
    service = StrategyService(mock_indicator, hybrid_engine=mock_hybrid)
    strategy = TradingStrategy(
        id=1,
        user_id=1,
        name="Test Hybrid",
        symbol="TSLA",
        strategy_type="HYBRID_ALL",
        parameters='{"tech_weight": 0.5, "buy_threshold": 70}',
        is_active=True
    )
    
    action = await service.evaluate_strategy(strategy)
    assert action == "BUY"
