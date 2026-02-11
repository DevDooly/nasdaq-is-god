from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from core.models import User, StockAsset, TradeLog
from core.broker import TradingBroker
from core.stock_service import get_stock_info
from bot.config import logger
from datetime import datetime

class TradeService:
    def __init__(self, broker: TradingBroker):
        self.broker = broker

    async def execute_trade(
        self, 
        session: AsyncSession, 
        user: User, 
        symbol: str, 
        quantity: float, 
        side: str
    ):
        """매매 실행 및 DB 업데이트 (로그 기록 + 자산 업데이트)"""
        
        # 1. 브로커를 통한 실제 주문 실행
        order_result = await self.broker.place_order(symbol, quantity, side)
        
        if order_result.get("status") != "filled":
            logger.error(f"Order failed: {order_result}")
            return {"error": "Order execution failed"}

        executed_price = order_result["price"]
        total_amount = executed_price * quantity

        # 2. 거래 로그 기록 (TradeLog)
        trade_log = TradeLog(
            user_id=user.id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=executed_price,
            total_amount=total_amount,
            executed_at=datetime.utcnow()
        )
        session.add(trade_log)

        # 3. 사용자 자산 업데이트 (StockAsset)
        statement = select(StockAsset).where(
            StockAsset.user_id == user.id, 
            StockAsset.symbol == symbol
        )
        result = await session.execute(statement)
        asset = result.scalar_one_or_none()

        if side.upper() == "BUY":
            if asset:
                # 평단가 재계산 및 수량 추가
                new_total_quantity = asset.quantity + quantity
                new_avg_price = (
                    (asset.average_price * asset.quantity) + total_amount
                ) / new_total_quantity
                asset.quantity = new_total_quantity
                asset.average_price = new_avg_price
                asset.updated_at = datetime.utcnow()
            else:
                # 새로운 자산 생성
                asset = StockAsset(
                    user_id=user.id,
                    symbol=symbol,
                    quantity=quantity,
                    average_price=executed_price,
                    updated_at=datetime.utcnow()
                )
                session.add(asset)
        
        elif side.upper() == "SELL":
            if not asset or asset.quantity < quantity:
                # 실제 환경에서는 주문 전 검증이 필요하지만, 여기서는 로그만 남김
                logger.error(f"Not enough quantity to sell: {symbol}")
                return {"error": "Insufficient quantity"}
            
            asset.quantity -= quantity
            asset.updated_at = datetime.utcnow()
            
            if asset.quantity == 0:
                await session.delete(asset)

        await session.commit()
        return {
            "status": "success",
            "order_id": order_result["order_id"],
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": executed_price
        }

    async def get_user_portfolio(self, session: AsyncSession, user: User):
        """사용자의 전체 포트폴리오 조회"""
        statement = select(StockAsset).where(StockAsset.user_id == user.id)
        result = await session.execute(statement)
        assets = result.scalars().all()
        return assets
