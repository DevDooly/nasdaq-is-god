"""
멀티 에이전트 헤지펀드 시스템 유닛 테스트 모듈.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.indicator_service import IndicatorService
from core.sentiment_engine import SentimentEngine
from core.agents import (
    TechnicalAgent,
    ValuationAgent,
    SentimentAgent,
    GuruAgent,
    RiskAgent,
    PortfolioManagerAgent,
    MultiAgentOrchestrator,
    AgentRole,
    AgentSignal,
    RiskMetrics
)


@pytest.mark.asyncio
async def test_technical_agent_analysis():
    mock_indicator = MagicMock(spec=IndicatorService)
    mock_indicator.get_indicators = AsyncMock(return_value={
        "rsi": 25.0, # 과매도 -> rsi_score = 75
        "macd": {"hist": 1.5}, # macd_score = 65
        "bollinger": {"upper": 100.0, "lower": 80.0},
        "current_price": 82.0 # bb_score = 90
    })

    agent = TechnicalAgent(mock_indicator)
    signal = await agent.analyze("AAPL")

    assert signal.role == AgentRole.TECHNICAL
    assert signal.recommendation == "BUY"
    assert signal.score >= 65.0
    assert "기술적 종합 점수" in signal.rationale


@pytest.mark.asyncio
async def test_sentiment_agent_analysis():
    mock_sentiment = MagicMock(spec=SentimentEngine)
    mock_sentiment.analyze_combined_sentiment = AsyncMock(return_value={
        "sentiment_score": 80.0,
        "summary": "호재 잇따라 발생",
        "reason": "실적 대폭 개선"
    })

    agent = SentimentAgent(mock_sentiment)
    signal = await agent.analyze("TSLA")

    assert signal.role == AgentRole.SENTIMENT
    assert signal.score == 80.0
    assert signal.recommendation == "BUY"


@pytest.mark.asyncio
async def test_risk_agent_evaluation():
    agent = RiskAgent(max_single_position_pct=20.0)
    risk_metrics = await agent.evaluate_risk(
        symbol="NVDA",
        current_price=100.0,
        total_balance=10000.0,
        proposed_action="BUY",
        technical_score=80.0,
        sentiment_score=80.0
    )

    assert risk_metrics.risk_approved is True
    assert risk_metrics.suggested_quantity > 0
    assert risk_metrics.max_position_pct <= 20.0


@pytest.mark.asyncio
async def test_multi_agent_orchestrator_pipeline():
    mock_indicator = MagicMock(spec=IndicatorService)
    mock_indicator.get_indicators = AsyncMock(return_value={
        "rsi": 30.0,
        "macd": {"hist": 1.0},
        "bollinger": {"upper": 120.0, "lower": 80.0},
        "current_price": 90.0
    })

    mock_sentiment = MagicMock(spec=SentimentEngine)
    mock_sentiment.analyze_combined_sentiment = AsyncMock(return_value={
        "sentiment_score": 75.0,
        "summary": "AI 수요 폭증",
        "reason": "신제품 발표"
    })

    orchestrator = MultiAgentOrchestrator(mock_indicator, mock_sentiment)

    with patch.object(ValuationAgent, "analyze", new_callable=AsyncMock) as mock_val:
        mock_val.return_value = AgentSignal(
            agent_name="Valuation Analyst",
            role=AgentRole.VALUATION,
            symbol="NVDA",
            score=70.0,
            recommendation="BUY",
            confidence=0.8,
            rationale="PER 적정 및 매출 성장 우수",
            details={}
        )

        decision = await orchestrator.run_hedge_fund_pipeline("NVDA", total_balance=10000.0)

        assert decision.symbol == "NVDA"
        assert decision.final_action in ["BUY", "HOLD", "SELL"]
        assert decision.confidence_score > 0
        assert "TECHNICAL" in decision.agent_signals
        assert "VALUATION" in decision.agent_signals
        assert "SENTIMENT" in decision.agent_signals
        assert "GURU" in decision.agent_signals
