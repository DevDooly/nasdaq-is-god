import json
import logging
from typing import Dict, Any, Optional
from core.indicator_service import IndicatorService
from core.sentiment_engine import SentimentEngine
from core.backtest_engine import BacktestEngine

logger = logging.getLogger("hybrid_strategy")

class HybridStrategyEngine:
    def __init__(self, indicator_service: IndicatorService, sentiment_engine: SentimentEngine):
        self.indicator_service = indicator_service
        self.sentiment_engine = sentiment_engine
        self.backtest_engine = BacktestEngine()

    async def calculate_technical_score(self, symbol: str, strategy_type: str = "HYBRID_RSI", params: Optional[Dict[str, Any]] = None) -> float:
        """
        기술적 지표를 바탕으로 0 ~ 100점 점수 산출
        """
        params = params or {}
        indicators = await self.indicator_service.get_indicators(symbol)
        if "error" in indicators:
            return 50.0

        rsi = indicators.get("rsi")
        macd = indicators.get("macd", {})
        bollinger = indicators.get("bollinger", {})
        current_price = indicators.get("current_price", 100.0)

        # 1. RSI 기반 스코어링 (RSI가 30 이하이면 100점에 가깝고, 70 이상이면 0점에 가깝도록)
        rsi_score = 50.0
        if rsi is not None:
            # rsi=30 -> 85점, rsi=70 -> 15점, rsi=50 -> 50점
            rsi_score = max(0.0, min(100.0, 100.0 - rsi))

        # 2. MACD 기반 스코어링
        macd_score = 50.0
        hist = macd.get("hist", 0.0)
        if hist > 0:
            macd_score = min(100.0, 50.0 + (hist * 10))
        elif hist < 0:
            macd_score = max(0.0, 50.0 + (hist * 10))

        # 3. 볼린저 밴드 기반 스코어링
        bb_score = 50.0
        upper = bollinger.get("upper")
        lower = bollinger.get("lower")
        if upper and lower and upper > lower:
            # 현재 가격의 밴드 내 상대 위치 % (하단 0%, 상단 100%)
            percent_b = (current_price - lower) / (upper - lower) * 100.0
            # 하단에 가까울수록 매수 우위 스코어
            bb_score = max(0.0, min(100.0, 100.0 - percent_b))

        if strategy_type == "HYBRID_RSI":
            return round(rsi_score, 1)
        elif strategy_type == "HYBRID_MACD":
            return round(macd_score, 1)
        elif strategy_type == "HYBRID_BOLLINGER":
            return round(bb_score, 1)
        else: # HYBRID_ALL (평균)
            return round((rsi_score + macd_score + bb_score) / 3.0, 1)

    async def evaluate_hybrid_signal(
        self,
        symbol: str,
        strategy_type: str = "HYBRID_ALL",
        tech_weight: float = 0.6,
        buy_threshold: float = 70.0,
        sell_threshold: float = 35.0,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        기술적 지표 점수 + AI 센티먼트 점수를 가중 조합하여 최종 하이브리드 시그널(BUY, SELL, HOLD) 반환
        """
        params = params or {}
        tech_weight = max(0.0, min(1.0, tech_weight))
        sent_weight = 1.0 - tech_weight

        # 1. 기술적 지표 점수 계산
        tech_score = await self.calculate_technical_score(symbol, strategy_type, params)

        # 2. AI 센티먼트 점수 계산
        sentiment_res = await self.sentiment_engine.analyze_combined_sentiment(symbol)
        sent_score = float(sentiment_res.get("sentiment_score", 50.0))

        # 3. 하이브리드 점수 산출
        hybrid_score = (tech_score * tech_weight) + (sent_score * sent_weight)
        hybrid_score = round(hybrid_score, 1)

        # 4. 액션 결정
        action = "HOLD"
        if hybrid_score >= buy_threshold:
            action = "BUY"
        elif hybrid_score <= sell_threshold:
            action = "SELL"

        return {
            "symbol": symbol,
            "strategy_type": strategy_type,
            "action": action,
            "hybrid_score": hybrid_score,
            "technical_score": tech_score,
            "sentiment_score": sent_score,
            "weights": {
                "technical": round(tech_weight, 2),
                "sentiment": round(sent_weight, 2)
            },
            "thresholds": {
                "buy": buy_threshold,
                "sell": sell_threshold
            },
            "sentiment_summary": sentiment_res.get("summary", ""),
            "sentiment_reason": sentiment_res.get("reason", "")
        }
