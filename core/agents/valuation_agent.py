"""
펀더멘털 및 밸류에이션 평가 에이전트 (Valuation Analyst Agent) 모듈.
"""

import logging
import asyncio
import yfinance as yf
from typing import Dict, Any
from core.agents.schema import AgentSignal, AgentRole

logger = logging.getLogger("valuation_agent")

class ValuationAgent:
    """
    기업의 PER, PBR, 매출 성장률 및 밸류에이션 지표를 분석하여 내재가치와 투자 시그널을 계산하는 에이전트 클래스.
    """

    async def analyze(self, symbol: str) -> AgentSignal:
        """
        종목의 펀더멘털 지표를 수집하고 밸류에이션 평가를 수행합니다.

        :param symbol: 주식 종목 티커
        :return: AgentSignal 분석 결과 개체
        """
        loop = asyncio.get_event_loop()
        try:
            # yfinance info 조회를 비동기로 실행
            info = await loop.run_in_executor(None, self._fetch_ticker_info, symbol)

            pe_ratio = info.get("trailingPE") or info.get("forwardPE")
            pb_ratio = info.get("priceToBook")
            revenue_growth = info.get("revenueGrowth") # e.g. 0.15 = 15%
            profit_margins = info.get("profitMargins") # e.g. 0.20 = 20%

            score = 50.0
            reasons = []

            # 1. PER 평가 (PER 15~25 적정, 15 이하 저평가 고득점)
            if pe_ratio:
                if pe_ratio < 15:
                    score += 15
                    reasons.append(f"PER({pe_ratio:.1f}) 저평가 구간")
                elif pe_ratio > 40:
                    score -= 15
                    reasons.append(f"PER({pe_ratio:.1f}) 고평가 우려")
                else:
                    reasons.append(f"PER({pe_ratio:.1f}) 적정 구간")
            
            # 2. 매출 성장률 평가 (10% 이상 고득점)
            if revenue_growth:
                growth_pct = revenue_growth * 100
                if growth_pct >= 20:
                    score += 15
                    reasons.append(f"매출성장률({growth_pct:.1f}%) 우수")
                elif growth_pct < 0:
                    score -= 10
                    reasons.append(f"매출 감소({growth_pct:.1f}%) 역성장")

            # 3. 순이익률 평가
            if profit_margins:
                margin_pct = profit_margins * 100
                if margin_pct >= 15:
                    score += 10
                    reasons.append(f"순이익률({margin_pct:.1f}%) 견조")

            final_score = max(0.0, min(100.0, score))
            recommendation = "HOLD"
            if final_score >= 65.0:
                recommendation = "BUY"
            elif final_score <= 35.0:
                recommendation = "SELL"

            rationale_text = ", ".join(reasons) if reasons else "기본 펀더멘털 데이터 수집 한계로 중립 평가."
            rationale = f"밸류에이션 종합 점수 {final_score:.0f}점. {rationale_text}"

            return AgentSignal(
                agent_name="Valuation Analyst",
                role=AgentRole.VALUATION,
                symbol=symbol,
                score=final_score,
                recommendation=recommendation,
                confidence=0.8,
                rationale=rationale,
                details={
                    "pe_ratio": pe_ratio,
                    "pb_ratio": pb_ratio,
                    "revenue_growth": revenue_growth,
                    "profit_margins": profit_margins
                }
            )
        except Exception as e:
            logger.error(f"ValuationAgent analyze error for {symbol}: {e}")
            return AgentSignal(
                agent_name="Valuation Analyst",
                role=AgentRole.VALUATION,
                symbol=symbol,
                score=50.0,
                recommendation="HOLD",
                confidence=0.4,
                rationale=f"펀더멘털 수집 및 평가 중 중립 처리: {str(e)}",
                details={}
            )

    def _fetch_ticker_info(self, symbol: str) -> Dict[str, Any]:
        ticker = yf.Ticker(symbol)
        return ticker.info or {}
