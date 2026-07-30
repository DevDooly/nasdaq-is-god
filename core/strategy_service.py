import json
from typing import List, Dict, Any, Optional
from core.models import TradingStrategy
from core.indicator_service import IndicatorService
from bot.config import logger

class StrategyService:
    def __init__(self, indicator_service: IndicatorService, hybrid_engine: Optional[Any] = None):
        self.indicator_service = indicator_service
        self.hybrid_engine = hybrid_engine

    async def evaluate_strategy(self, strategy: TradingStrategy) -> str:
        """
        전략을 평가하여 액션(BUY, SELL, HOLD)을 반환합니다.
        """
        symbol = strategy.symbol
        params = json.loads(strategy.parameters) if isinstance(strategy.parameters, str) else (strategy.parameters or {})
        
        # 하이브리드 전략 처리
        if strategy.strategy_type.startswith("HYBRID") and self.hybrid_engine:
            try:
                res = await self.hybrid_engine.evaluate_hybrid_signal(
                    symbol=symbol,
                    strategy_type=strategy.strategy_type,
                    tech_weight=float(params.get("tech_weight", 0.6)),
                    buy_threshold=float(params.get("buy_threshold", 70.0)),
                    sell_threshold=float(params.get("sell_threshold", 35.0)),
                    params=params
                )
                return res.get("action", "HOLD")
            except Exception as e:
                logger.error(f"Hybrid strategy evaluation error for {symbol}: {e}")
                return "HOLD"

        # 최신 기술적 지표 데이터 가져오기
        indicators = await self.indicator_service.get_indicators(symbol)
        if "error" in indicators:
            logger.error(f"Strategy eval failed for {symbol}: {indicators['error']}")
            return "HOLD"

        rsi = indicators.get("rsi")
        
        # 1. RSI 기반 전략
        if strategy.strategy_type in ["RSI_LIMIT", "RSI_REVERSAL"]:
            buy_threshold = float(params.get("buy_rsi", 30))
            sell_threshold = float(params.get("sell_rsi", 70))
            
            if rsi is not None:
                if rsi <= buy_threshold:
                    return "BUY"
                elif rsi >= sell_threshold:
                    return "SELL"
        
        # 2. 이동평균 크로스 전략
        elif strategy.strategy_type in ["SMA_CROSSOVER", "MA_CROSSOVER"]:
            # 간단 지표 스코어링 반환
            pass

        return "HOLD"
