"""
AI 헤지펀드 이사회 API 엔드포인트 유닛 테스트 모듈.
"""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from main_api import app
from core.agents.schema import PortfolioDecision, AgentSignal, AgentRole, RiskMetrics


@pytest.mark.asyncio
async def test_evaluate_hedge_fund_board_api():
    mock_decision = PortfolioDecision(
        symbol="AAPL",
        final_action="BUY",
        target_quantity=10,
        confidence_score=75.0,
        risk_approval=True,
        agent_signals={
            "TECHNICAL": AgentSignal(
                agent_name="Technical Analyst",
                role=AgentRole.TECHNICAL,
                symbol="AAPL",
                score=70.0,
                recommendation="BUY",
                confidence=0.8,
                rationale="RSI 과매도",
                details={}
            )
        },
        risk_metrics=RiskMetrics(
            symbol="AAPL",
            max_position_pct=15.0,
            suggested_quantity=10,
            stop_loss_pct=5.0,
            take_profit_pct=12.0,
            risk_approved=True,
            reasoning="예수금 15% 승인"
        ),
        decision_rationale="이사회 종합 평점 75점 (BUY)"
    )

    with patch("main_api.multi_agent_orchestrator.run_hedge_fund_pipeline", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_decision

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/agents/hedge-fund/evaluate", json={
                "symbol": "AAPL",
                "total_balance": 10000.0
            })

            assert response.status_code == 200
            data = response.json()
            assert data["symbol"] == "AAPL"
            assert data["final_action"] == "BUY"
            assert data["target_quantity"] == 10
            assert data["confidence_score"] == 75.0
