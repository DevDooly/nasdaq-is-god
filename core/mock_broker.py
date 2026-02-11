from typing import Dict, Any, Optional
from core.broker import TradingBroker
from core.stock_service import get_stock_info
from bot.config import logger
from datetime import datetime

class MockBroker(TradingBroker):
    """테스트 및 개발을 위한 모의 브로커 (실제 주가 연동)"""

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
        """주문 실행 (모의 매매지만 실제 주가를 가져와 체결)"""
        
        # 지정가 주문이 아닐 경우(시장가), 실제 현재가를 가져옴
        if price is None:
            stock_data = await get_stock_info(symbol)
            if "error" in stock_data:
                logger.error(f"Failed to fetch price for {symbol} during mock trade")
                price = 150.0 # 최종 폴백
            else:
                price = stock_data["currentPrice"]
        
        logger.info(f"[MOCK ORDER] {side} {quantity} {symbol} at {price:.2f}")
        
        return {
            "order_id": f"mock_{int(datetime.now().timestamp())}",
            "status": "filled",
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "executed_at": datetime.utcnow().isoformat()
        }

    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        return {"order_id": order_id, "status": "filled"}

    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        return {"order_id": order_id, "status": "canceled"}