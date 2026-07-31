"""
월가 투자 거장 페르소나 에이전트 (Guru Investor Persona Agent) 모듈.
"""

import logging
from typing import Dict, Any, List
from core.agents.schema import AgentSignal, AgentRole

logger = logging.getLogger("guru_agent")

class GuruAgent:
    """
    Warren Buffett, Cathie Wood, Michael Burry 등 전설적 투자자 프롬프트/시각을 투영하여 종목을 조망하는 에이전트 클래스.
    """

    async def analyze(self, symbol: str, tech_signal: AgentSignal, val_signal: AgentSignal, sent_signal: AgentSignal) -> AgentSignal:
        """
        기술적, 밸류에이션, 센티먼트 데이터를 결합하여 거장 페르소나들의 앙상블 투표 결과를 도출합니다.

        :param symbol: 종목 티커
        :param tech_signal: TechnicalAgent 결과
        :param val_signal: ValuationAgent 결과
        :param sent_signal: SentimentAgent 결과
        :return: AgentSignal 투자 거장 종합 결과
        """
        try:
            # 1. Warren Buffett (가치, 안전지대, 적정 PER 및 긍정 센티먼트)
            buffett_score = (val_signal.score * 0.6) + (tech_signal.score * 0.2) + (sent_signal.score * 0.2)

            # 2. Cathie Wood (모멘텀, 소셜 화제성, 매출 성장에 우대)
            wood_score = (sent_signal.score * 0.5) + (tech_signal.score * 0.3) + (val_signal.score * 0.2)

            # 3. Michael Burry (역발상, 과매도 및 밸류에이션 저평가 시 고득점)
            burry_score = (val_signal.score * 0.5) + ((100.0 - tech_signal.score) * 0.3) + ((100.0 - sent_signal.score) * 0.2)

            guru_score = round((buffett_score + wood_score + burry_score) / 3.0, 1)

            recommendation = "HOLD"
            if guru_score >= 65.0:
                recommendation = "BUY"
            elif guru_score <= 35.0:
                recommendation = "SELL"

            buffett_verdict = "BUY" if buffett_score >= 60 else ("SELL" if buffett_score <= 40 else "HOLD")
            wood_verdict = "BUY" if wood_score >= 60 else ("SELL" if wood_score <= 40 else "HOLD")
            burry_verdict = "BUY" if burry_score >= 60 else ("SELL" if burry_score <= 40 else "HOLD")

            rationale = (
                f"투자 거장 3인 앙상블 평점 {guru_score}점 ({recommendation}). "
                f"버핏({buffett_verdict}:{buffett_score:.0f}점), "
                f"캐시우드({wood_verdict}:{wood_score:.0f}점), "
                f"마이클버리({burry_verdict}:{burry_score:.0f}점)"
            )

            return AgentSignal(
                agent_name="WallStreet Gurus Ensemble",
                role=AgentRole.GURU,
                symbol=symbol,
                score=guru_score,
                recommendation=recommendation,
                confidence=0.8,
                rationale=rationale,
                details={
                    "buffett_score": round(buffett_score, 1),
                    "wood_score": round(wood_score, 1),
                    "burry_score": round(burry_score, 1),
                    "buffett_verdict": buffett_verdict,
                    "wood_verdict": wood_verdict,
                    "burry_verdict": burry_verdict
                }
            )
        except Exception as e:
            logger.error(f"GuruAgent analyze error for {symbol}: {e}")
            return AgentSignal(
                agent_name="WallStreet Gurus Ensemble",
                role=AgentRole.GURU,
                symbol=symbol,
                score=50.0,
                recommendation="HOLD",
                confidence=0.5,
                rationale=f"거장 페르소나 평점 산출 중 오차 발생: {str(e)}",
                details={}
            )
