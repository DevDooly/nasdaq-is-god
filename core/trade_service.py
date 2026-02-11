from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from core.models import User, StockAsset, TradeLog
from core.broker import TradingBroker
from core.stock_service import get_stock_info
from bot.config import logger
from datetime import datetime
import asyncio

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
                logger.error(f"Not enough quantity to sell: {symbol}")
                return {"error": "Insufficient quantity"}
            
            asset.quantity -= quantity
            asset.updated_at = datetime.utcnow()
            
            if asset.quantity <= 0:
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
        """사용자의 전체 포트폴리오 조회 (최적화 버전)"""
        statement = select(StockAsset).where(StockAsset.user_id == user.id)
        result = await session.execute(statement)
        assets = result.scalars().all()
        
        if not assets:
            return []

        # 💡 각 자산의 현재가를 병렬로 빠르게 조회
        async def enrich_asset(asset):
            try:
                # 타임아웃을 적용하여 전체 조회가 무한정 대기하지 않도록 보호
                stock_data = await asyncio.wait_for(get_stock_info(asset.symbol), timeout=5.0)
                current_price = stock_data.get("currentPrice", asset.average_price)
                
                asset_dict = asset.dict()
                asset_dict["current_price"] = current_price
                
                # 수익률 계산
                profit = (current_price - asset.average_price) * asset.quantity
                profit_rate = ((current_price / asset.average_price) - 1) * 100 if asset.average_price > 0 else 0
                asset_dict["profit"] = profit
                asset_dict["profit_rate"] = profit_rate
                return asset_dict
            except Exception as e:
                logger.warning(f"Failed to enrich asset {asset.symbol}: {e}")
                # 실패 시 기본 정보라도 반환
                asset_dict = asset.dict()
                asset_dict["current_price"] = asset.average_price
                asset_dict["profit"] = 0.0
                asset_dict["profit_rate"] = 0.0
                return asset_dict

        # 병렬 실행으로 전체 응답 속도 대폭 개선
        enriched_assets = await asyncio.gather(*[enrich_asset(a) for a in assets])
        return enriched_assets

    async def get_trade_history(self, session: AsyncSession, user: User):
        """사용자의 전체 매매 내역 조회 (페이징 없이 최신순)"""
        statement = select(TradeLog).where(TradeLog.user_id == user.id).order_by(TradeLog.executed_at.desc())
        result = await session.execute(statement)
        logs = result.scalars().all()
        return logs
