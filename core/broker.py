from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class TradingBroker(ABC):
    """주식 매매를 위한 브로커 추상 클래스"""

    @abstractmethod
    async def get_balance(self) -> Dict[str, Any]:
        """계좌 잔고 및 예수금 현황 조회"""
        pass

    @abstractmethod
    async def place_order(
        self, 
        symbol: str, 
        quantity: float, 
        side: str, 
        order_type: str = "market", 
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """주문 실행 (매수/매도)"""
        pass

    @abstractmethod
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """주문 상태 조회"""
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """주문 취소"""
        pass
