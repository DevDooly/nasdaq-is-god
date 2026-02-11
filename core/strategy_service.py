import json
from typing import List, Dict, Any
from core.models import TradingStrategy
from core.indicator_service import IndicatorService
from bot.config import logger

class StrategyService:
    def __init__(self, indicator_service: IndicatorService):
        self.indicator_service = indicator_service

    async def evaluate_strategy(self, strategy: TradingStrategy) -> str:
        """
        전략을 평가하여 액션(BUY, SELL, HOLD)을 반환합니다.
        """
        symbol = strategy.symbol
        params = json.loads(strategy.parameters)
        
        # 최신 지표 데이터 가져오기
        indicators = await self.indicator_service.get_indicators(symbol)
        if "error" in indicators:
            logger.error(f"Strategy eval failed for {symbol}: {indicators['error']}")
            return "HOLD"

        rsi = indicators.get("rsi")
        
        # 1. RSI 기반 전략 (예시)
        if strategy.strategy_type == "RSI_LIMIT":
            buy_threshold = params.get("buy_rsi", 30)
            sell_threshold = params.get("sell_rsi", 70)
            
            if rsi is not None:
                if rsi <= buy_threshold:
                    return "BUY"
                elif rsi >= sell_threshold:
                    return "SELL"
        
        # 2. 고정 익절/손절 전략 (추후 확장 가능)
        # ... 
        
        return "HOLD"
