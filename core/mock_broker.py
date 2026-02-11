from typing import Dict, Any, Optional
from core.broker import TradingBroker
from bot.config import logger

class MockBroker(TradingBroker):
    """테스트 및 개발을 위한 모의 브로커 (실제 주문을 넣지 않음)"""

    async def get_balance(self) -> Dict[str, Any]:
        return {
            "cash": 100000.0,
            "currency": "USD",
            "equity": 100000.0
        }

    async def place_order(
        self, 
        symbol: str, 
        quantity: float, 
        side: str, 
        order_type: str = "market", 
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        logger.info(f"[MOCK ORDER] {side} {quantity} {symbol} at {price or 'market price'}")
        return {
            "order_id": "mock_order_12345",
            "status": "filled",
            "symbol": symbol,
            "quantity": quantity,
            "price": price or 150.0,  # 가상의 체결가
            "executed_at": "2026-02-11T12:00:00Z"
        }

    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        return {"order_id": order_id, "status": "filled"}

    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        return {"order_id": order_id, "status": "canceled"}
