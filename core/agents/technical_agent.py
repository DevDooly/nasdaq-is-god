"""
기술적 지표 분석 에이전트 (Technical Analyst Agent) 모듈.
"""

import logging
from typing import Dict, Any, Optional
from core.indicator_service import IndicatorService
from core.agents.schema import AgentSignal, AgentRole

logger = logging.getLogger("technical_agent")

class TechnicalAgent:
    """
    RSI, MACD, 볼린저 밴드 등 이동평균/모멘텀 지표를 종합 분석하여 매매 시그널을 생성하는 에이전트 클래스.
    """

    def __init__(self, indicator_service: IndicatorService):
        """
        TechnicalAgent 초기화.

        :param indicator_service: 기술적 지표 조회 서비스
        """
        self.indicator_service = indicator_service

    async def analyze(self, symbol: str) -> AgentSignal:
        """
        종목의 기술적 지표를 산출하고 분석 점수와 매매 시그널을 반환합니다.

        :param symbol: 주식 종목 티커
        :return: AgentSignal 분석 결과 개체
        """
        try:
            indicators = await self.indicator_service.get_indicators(symbol)
            if "error" in indicators:
                return AgentSignal(
                    agent_name="Technical Analyst",
                    role=AgentRole.TECHNICAL,
                    symbol=symbol,
                    score=50.0,
                    recommendation="HOLD",
                    confidence=0.5,
                    rationale=f"기술적 지표 수집 실패: {indicators.get('error')}",
                    details={}
                )

            rsi = indicators.get("rsi", 50.0)
            macd = indicators.get("macd", {})
            bollinger = indicators.get("bollinger", {})
            current_price = indicators.get("current_price", 100.0)

            # 1. RSI 스코어 (과매도 30 이하 -> 고득점, 과매수 70 이상 -> 저득점)
            rsi_score = max(0.0, min(100.0, 100.0 - rsi)) if rsi is not None else 50.0

            # 2. MACD 스코어 (히스토그램 기반)
            macd_score = 50.0
            hist = macd.get("hist", 0.0)
            if hist > 0:
                macd_score = min(100.0, 50.0 + (hist * 10))
            elif hist < 0:
                macd_score = max(0.0, 50.0 + (hist * 10))

            # 3. 볼린저 밴드 스코어
            bb_score = 50.0
            upper = bollinger.get("upper")
            lower = bollinger.get("lower")
            if upper and lower and upper > lower:
                percent_b = (current_price - lower) / (upper - lower) * 100.0
                bb_score = max(0.0, min(100.0, 100.0 - percent_b))

            total_score = round((rsi_score + macd_score + bb_score) / 3.0, 1)

            recommendation = "HOLD"
            if total_score >= 65.0:
                recommendation = "BUY"
            elif total_score <= 35.0:
                recommendation = "SELL"

            rationale = (
                f"기술적 종합 점수 {total_score}점. "
                f"RSI({rsi:.1f}) {rsi_score:.0f}점, MACD 히스토그램({hist:.2f}) {macd_score:.0f}점, "
                f"볼린저밴드 상대위치 기준 {bb_score:.0f}점 도출."
            )

            return AgentSignal(
                agent_name="Technical Analyst",
                role=AgentRole.TECHNICAL,
                symbol=symbol,
                score=total_score,
                recommendation=recommendation,
                confidence=0.85,
                rationale=rationale,
                details={
                    "rsi": rsi,
                    "macd_hist": hist,
                    "current_price": current_price,
                    "rsi_score": rsi_score,
                    "macd_score": macd_score,
                    "bb_score": bb_score
                }
            )
        except Exception as e:
            logger.error(f"TechnicalAgent analyze error for {symbol}: {e}")
            return AgentSignal(
                agent_name="Technical Analyst",
                role=AgentRole.TECHNICAL,
                symbol=symbol,
                score=50.0,
                recommendation="HOLD",
                confidence=0.3,
                rationale=f"기술 지표 분석 오류 발생: {str(e)}",
                details={}
            )
