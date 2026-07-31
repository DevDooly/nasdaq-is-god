"""
멀티 에이전트 헤지펀드 오케스트레이터 (Multi-Agent Hedge Fund Orchestrator) 모듈.
"""

import logging
import asyncio
from typing import Dict, Any, Optional

from core.indicator_service import IndicatorService
from core.sentiment_engine import SentimentEngine
from core.agents.schema import PortfolioDecision, AgentSignal, RiskMetrics
from core.agents.technical_agent import TechnicalAgent
from core.agents.valuation_agent import ValuationAgent
from core.agents.sentiment_agent import SentimentAgent
from core.agents.guru_agent import GuruAgent
from core.agents.risk_agent import RiskAgent
from core.agents.portfolio_manager import PortfolioManagerAgent

logger = logging.getLogger("multi_agent_orchestrator")

class MultiAgentOrchestrator:
    """
    모든 에이전트를 조율하고 병렬 실행하여 최종 헤지펀드 이사회 의사결정(PortfolioDecision)을 도출하는 오케스트레이터.
    """

    def __init__(self, indicator_service: IndicatorService, sentiment_engine: SentimentEngine):
        """
        MultiAgentOrchestrator 초기화.

        :param indicator_service: 기술적 지표 서비스
        :param sentiment_engine: 센티먼트 분석 엔진
        """
        self.technical_agent = TechnicalAgent(indicator_service)
        self.valuation_agent = ValuationAgent()
        self.sentiment_agent = SentimentAgent(sentiment_engine)
        self.guru_agent = GuruAgent()
        self.risk_agent = RiskAgent()
        self.pm_agent = PortfolioManagerAgent()

    async def run_hedge_fund_pipeline(
        self,
        symbol: str,
        total_balance: float = 10000.0,
        weights: Optional[Dict[str, float]] = None
    ) -> PortfolioDecision:
        """
        종목에 대한 멀티 에이전트 투자 분석 파이프라인을 비동기로 전체 실행합니다.

        :param symbol: 주식 종목 티커
        :param total_balance: 가용 예수금 ($)
        :param weights: 에이전트별 의사결정 가중치
        :return: PortfolioDecision 최종 의사결정 및 각 에이전트 리포트
        """
        logger.info(f"Starting Multi-Agent Hedge Fund Pipeline for {symbol} (Balance: ${total_balance})...")

        # 1. 1차 분석가 에이전트 병렬 수행 (Technical, Valuation, Sentiment)
        tech_task = asyncio.create_task(self.technical_agent.analyze(symbol))
        val_task = asyncio.create_task(self.valuation_agent.analyze(symbol))
        sent_task = asyncio.create_task(self.sentiment_agent.analyze(symbol))

        tech_sig, val_sig, sent_sig = await asyncio.gather(tech_task, val_task, sent_task)

        # 2. 2차 거장 앙상블 에이전트 수행
        guru_sig = await self.guru_agent.analyze(symbol, tech_sig, val_sig, sent_sig)

        agent_signals = {
            "TECHNICAL": tech_sig,
            "VALUATION": val_sig,
            "SENTIMENT": sent_sig,
            "GURU": guru_sig
        }

        # 가중 종합 점수 및 리스크 매니저 평가 준비
        current_price = tech_sig.details.get("current_price", 100.0)
        tentative_score = (tech_sig.score * 0.35) + (val_sig.score * 0.25) + (sent_sig.score * 0.2) + (guru_sig.score * 0.2)
        proposed_action = "BUY" if tentative_score >= 65.0 else ("SELL" if tentative_score <= 35.0 else "HOLD")

        # 3. 리스크 매니저 검증 수행
        risk_metrics = await self.risk_agent.evaluate_risk(
            symbol=symbol,
            current_price=current_price,
            total_balance=total_balance,
            proposed_action=proposed_action,
            technical_score=tech_sig.score,
            sentiment_score=sent_sig.score
        )

        # 4. 포트폴리오 매니저 최종 결정
        decision = await self.pm_agent.decide(
            symbol=symbol,
            agent_signals=agent_signals,
            risk_metrics=risk_metrics,
            weights=weights
        )

        logger.info(f"Multi-Agent Pipeline completed for {symbol}: Action={decision.final_action}, Qty={decision.target_quantity}, Score={decision.confidence_score}")
        return decision
