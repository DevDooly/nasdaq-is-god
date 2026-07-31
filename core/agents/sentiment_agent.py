"""
소셜 & 뉴스 감성 분석 에이전트 (Sentiment Analyst Agent) 모듈.
"""

import logging
from core.sentiment_engine import SentimentEngine
from core.agents.schema import AgentSignal, AgentRole

logger = logging.getLogger("sentiment_agent")

class SentimentAgent:
    """
    뉴스, StockTwits 및 소셜 게시글의 LLM 기반 감성 점수를 수집하여 센티먼트 시그널을 생성하는 에이전트 클래스.
    """

    def __init__(self, sentiment_engine: SentimentEngine):
        """
        SentimentAgent 초기화.

        :param sentiment_engine: 뉴스 및 소셜 감성 분석 엔진
        """
        self.sentiment_engine = sentiment_engine

    async def analyze(self, symbol: str) -> AgentSignal:
        """
        종목에 대한 최신 소셜/뉴스 감성 점수와 요약을 가져옵니다.

        :param symbol: 주식 종목 티커
        :return: AgentSignal 분석 결과 개체
        """
        try:
            res = await self.sentiment_engine.analyze_combined_sentiment(symbol)
            score = float(res.get("sentiment_score", 50.0))
            summary = res.get("summary", "감성 정보 부족")
            reason = res.get("reason", "")

            recommendation = "HOLD"
            if score >= 65.0:
                recommendation = "BUY"
            elif score <= 35.0:
                recommendation = "SELL"

            rationale = f"뉴스/소셜 AI 감성 점수 {score:.0f}점 ({recommendation}). 요약: {summary} ({reason})"

            return AgentSignal(
                agent_name="Sentiment Analyst",
                role=AgentRole.SENTIMENT,
                symbol=symbol,
                score=score,
                recommendation=recommendation,
                confidence=0.75,
                rationale=rationale,
                details={
                    "summary": summary,
                    "reason": reason
                }
            )
        except Exception as e:
            logger.error(f"SentimentAgent analyze error for {symbol}: {e}")
            return AgentSignal(
                agent_name="Sentiment Analyst",
                role=AgentRole.SENTIMENT,
                symbol=symbol,
                score=50.0,
                recommendation="HOLD",
                confidence=0.3,
                rationale=f"소셜 센티먼트 분석 예외 발생: {str(e)}",
                details={}
            )
