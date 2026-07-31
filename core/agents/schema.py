"""
멀티 에이전트 헤지펀드 시스템 데이터 스키마 정의 모듈.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """에이전트 역할 구분 열거형"""
    TECHNICAL = "TECHNICAL"          # 기술적 지표 분석가
    VALUATION = "VALUATION"          # 펀더멘털 & 밸류에이션 분석가
    SENTIMENT = "SENTIMENT"          # 소셜 & 뉴스 감성 분석가
    GURU = "GURU"                    # 투자 거장 페르소나 (버핏, 우드, 버리 등)
    RISK_MANAGER = "RISK_MANAGER"    # 리스크 관리자
    PORTFOLIO_MANAGER = "PORTFOLIO_MANAGER" # 포트폴리오 매니저 (최종 의사결정자)


class AgentSignal(BaseModel):
    """개별 에이전트의 분석 시그널 개체"""
    agent_name: str = Field(..., description="에이전트 명칭")
    role: AgentRole = Field(..., description="에이전트 역할")
    symbol: str = Field(..., description="주식 종목 티커")
    score: float = Field(..., ge=0.0, le=100.0, description="분석 점수 (0~100점)")
    recommendation: str = Field(..., description="추천 의견 (BUY, SELL, HOLD)")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="신뢰도 (0.0~1.0)")
    rationale: str = Field(..., description="분석 결과 근거 요약 (한국어)")
    details: Dict[str, Any] = Field(default_factory=dict, description="세부 측정 지표 데이터")


class RiskMetrics(BaseModel):
    """리스크 관리 에이전트의 포지션 및 위험 분석 리포트"""
    symbol: str = Field(..., description="주식 종목 티커")
    max_position_pct: float = Field(..., description="권장 포트폴리오 최대 비중 (%)")
    suggested_quantity: int = Field(..., description="권장 매수 주식 수량")
    stop_loss_pct: float = Field(..., description="손절 가이드라인 (%)")
    take_profit_pct: float = Field(..., description="익절 가이드라인 (%)")
    risk_approved: bool = Field(..., description="리스크 검증 승인 여부")
    reasoning: str = Field(..., description="리스크 산출 근거 (한국어)")


class PortfolioDecision(BaseModel):
    """포트폴리오 매니저의 최종 투자 의사결정 개체"""
    symbol: str = Field(..., description="주식 종목 티커")
    final_action: str = Field(..., description="최종 의사결정 (BUY, SELL, HOLD)")
    target_quantity: int = Field(default=0, description="최종 주문 수량")
    confidence_score: float = Field(..., ge=0.0, le=100.0, description="종합 확신 점수 (0~100)")
    risk_approval: bool = Field(..., description="리스크 매니저 승인 여부")
    agent_signals: Dict[str, AgentSignal] = Field(default_factory=dict, description="참여한 에이전트별 시그널 레포트")
    risk_metrics: Optional[RiskMetrics] = Field(default=None, description="리스크 매니저 리포트")
    decision_rationale: str = Field(..., description="최종 의사결정 이유 및 이사회 요약 (한국어)")
