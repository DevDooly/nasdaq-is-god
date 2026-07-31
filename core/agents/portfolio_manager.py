"""
포트폴리오 매니저 에이전트 (Portfolio Manager Agent) 모듈.
"""

import logging
from typing import Dict, Any
from core.agents.schema import AgentSignal, RiskMetrics, PortfolioDecision, AgentRole

logger = logging.getLogger("portfolio_manager")

class PortfolioManagerAgent:
    """
    모든 분석가 및 리스크 매니저의 보고서를 종합 판정하여 최종 매매 신호와 주문 수량을 결정하는 총괄 에이전트 클래스.
    """

    async def decide(
        self,
        symbol: str,
        agent_signals: Dict[str, AgentSignal],
        risk_metrics: RiskMetrics,
        weights: Dict[str, float] = None
    ) -> PortfolioDecision:
        """
        분석가들의 시그널과 리스크 관리 지침을 가중 산출하여 최종 포트폴리오 의사결정을 내립니다.

        :param symbol: 주식 종목 티커
        :param agent_signals: 참여 에이전트들의 시그널 맵
        :param risk_metrics: 리스크 매니저 리포트
        :param weights: 에이전트별 가중치 (기본값: Technical 0.35, Valuation 0.25, Sentiment 0.2, Guru 0.2)
        :return: PortfolioDecision 최종 의사결정 개체
        """
        try:
            default_weights = {
                "TECHNICAL": 0.35,
                "VALUATION": 0.25,
                "SENTIMENT": 0.20,
                "GURU": 0.20
            }
            weights = weights or default_weights

            total_weighted_score = 0.0
            total_weight = 0.0

            for sig_key, signal in agent_signals.items():
                role_str = signal.role.value if isinstance(signal.role, AgentRole) else str(signal.role)
                w = weights.get(role_str, 0.2)
                total_weighted_score += signal.score * w
                total_weight += w

            final_score = round(total_weighted_score / total_weight, 1) if total_weight > 0 else 50.0

            final_action = "HOLD"
            if final_score >= 65.0:
                final_action = "BUY"
            elif final_score <= 35.0:
                final_action = "SELL"

            # 리스크 매니저의 승인 여부 반영
            target_quantity = 0
            if final_action == "BUY":
                if risk_metrics.risk_approved and risk_metrics.suggested_quantity > 0:
                    target_quantity = risk_metrics.suggested_quantity
                else:
                    final_action = "HOLD" # 리스크 미승인 시 관망으로 전환

            summary_reasons = []
            for name, sig in agent_signals.items():
                summary_reasons.append(f"[{sig.agent_name}]: {sig.recommendation}({sig.score:.0f}점)")

            board_summary = " | ".join(summary_reasons)
            decision_rationale = (
                f"AI 이사회 종합 평점 {final_score}점 ➔ 최종 판정: {final_action} ({target_quantity}주). "
                f"각 에이전트 의견: {board_summary}. "
                f"리스크 검증: {risk_metrics.reasoning}"
            )

            return PortfolioDecision(
                symbol=symbol,
                final_action=final_action,
                target_quantity=target_quantity,
                confidence_score=final_score,
                risk_approval=risk_metrics.risk_approved,
                agent_signals=agent_signals,
                risk_metrics=risk_metrics,
                decision_rationale=decision_rationale
            )
        except Exception as e:
            logger.error(f"PortfolioManagerAgent decide error for {symbol}: {e}")
            return PortfolioDecision(
                symbol=symbol,
                final_action="HOLD",
                target_quantity=0,
                confidence_score=50.0,
                risk_approval=False,
                agent_signals=agent_signals,
                risk_metrics=risk_metrics,
                decision_rationale=f"포트폴리오 매니저 최종 결정 오류 발생 (HOLD 안전 처리): {str(e)}"
            )
