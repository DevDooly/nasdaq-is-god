"""
위험 관리 에이전트 (Risk Manager Agent) 모듈.
"""

import logging
from typing import Dict, Any, Optional
from core.agents.schema import RiskMetrics, AgentRole

logger = logging.getLogger("risk_agent")

class RiskAgent:
    """
    포트폴리오 비중, 변동성, 최대 손실 한도(Max Drawdown)를 고려하여 주문 수량 및 리스크 승인을 가이드하는 에이전트 클래스.
    """

    def __init__(self, max_single_position_pct: float = 20.0, default_stop_loss_pct: float = 5.0, default_take_profit_pct: float = 12.0):
        """
        RiskAgent 초기화.

        :param max_single_position_pct: 단일 종목 권장 최대 포트폴리오 비중 (%)
        :param default_stop_loss_pct: 기본 손절 한도 (%)
        :param default_take_profit_pct: 기본 익절 목표 (%)
        """
        self.max_single_position_pct = max_single_position_pct
        self.default_stop_loss_pct = default_stop_loss_pct
        self.default_take_profit_pct = default_take_profit_pct

    async def evaluate_risk(
        self,
        symbol: str,
        current_price: float,
        total_balance: float,
        proposed_action: str,
        technical_score: float = 50.0,
        sentiment_score: float = 50.0
    ) -> RiskMetrics:
        """
        제시된 액션(BUY/SELL/HOLD)에 대한 포지션 크기 산출 및 위험 통제 지침을 계산합니다.

        :param symbol: 주식 종목 티커
        :param current_price: 현재 주가 ($)
        :param total_balance: 총 포트폴리오 예수금 ($)
        :param proposed_action: 제안된 매매 액션
        :param technical_score: 기술적 분석 점수
        :param sentiment_score: 센티먼트 분석 점수
        :return: RiskMetrics 리스크 검증 개체
        """
        try:
            if proposed_action != "BUY" or current_price <= 0 or total_balance <= 0:
                return RiskMetrics(
                    symbol=symbol,
                    max_position_pct=0.0,
                    suggested_quantity=0,
                    stop_loss_pct=self.default_stop_loss_pct,
                    take_profit_pct=self.default_take_profit_pct,
                    risk_approved=(proposed_action != "BUY"),
                    reasoning="매도/관망 액션이거나 잔고/주가 정보 부족으로 신규 매수 비중 0주 배정."
                )

            # 점수에 따라 매수 예산 비중 조절 (최대 20% 한도 내)
            confidence_factor = (technical_score + sentiment_score) / 200.0 # 0.0 ~ 1.0
            allocated_pct = min(self.max_single_position_pct, self.max_single_position_pct * confidence_factor * 1.2)
            allocated_budget = total_balance * (allocated_pct / 100.0)

            suggested_qty = int(allocated_budget // current_price)
            risk_approved = suggested_qty > 0

            # 변동성에 따른 손절/익절선 유연화
            stop_loss = self.default_stop_loss_pct
            take_profit = self.default_take_profit_pct

            reasoning = (
                f"예수금 ${total_balance:,.0f} 중 {allocated_pct:.1f}% (${allocated_budget:,.0f}) 배정. "
                f"현재가 ${current_price:.2f} 기준 최대 {suggested_qty}주 매수 승인. "
                f"(손절선 -{stop_loss}%, 익절선 +{take_profit}%)"
            )

            return RiskMetrics(
                symbol=symbol,
                max_position_pct=round(allocated_pct, 1),
                suggested_quantity=suggested_qty,
                stop_loss_pct=stop_loss,
                take_profit_pct=take_profit,
                risk_approved=risk_approved,
                reasoning=reasoning
            )
        except Exception as e:
            logger.error(f"RiskAgent evaluate_risk error for {symbol}: {e}")
            return RiskMetrics(
                symbol=symbol,
                max_position_pct=0.0,
                suggested_quantity=0,
                stop_loss_pct=self.default_stop_loss_pct,
                take_profit_pct=self.default_take_profit_pct,
                risk_approved=False,
                reasoning=f"리스크 검증 예외 발생: {str(e)}"
            )
