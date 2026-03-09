from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from core.models import User, StockAsset, TradeLog, EquitySnapshot
from core.broker import TradingBroker
from core.stock_service import get_stock_info
from core.notification_service import notification_service
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
        """매매 실행 및 DB 업데이트 (잔고 체크 + 로그 기록 + 자산 업데이트)"""
        
        statement = select(User).where(User.id == user.id)
        result = await session.execute(statement)
        db_user = result.scalar_one()

        stock_data = await get_stock_info(symbol)
        if "error" in stock_data:
            return {"error": f"Failed to fetch price for {symbol}"}
        
        current_price = stock_data["currentPrice"]
        total_amount = current_price * quantity

        if side.upper() == "BUY":
            if db_user.cash_balance < total_amount:
                return {"error": f"Insufficient balance. Required: ${total_amount:.2f}, Available: ${db_user.cash_balance:.2f}"}
            
            order_result = await self.broker.place_order(symbol, quantity, side, price=current_price)
            if order_result.get("status") != "filled":
                return {"error": "Order execution failed"}
            
            db_user.cash_balance -= total_amount

        elif side.upper() == "SELL":
            asset_statement = select(StockAsset).where(StockAsset.user_id == user.id, StockAsset.symbol == symbol)
            asset_result = await session.execute(asset_statement)
            asset = asset_result.scalar_one_or_none()

            if not asset or asset.quantity < quantity:
                return {"error": "Insufficient stock quantity"}

            order_result = await self.broker.place_order(symbol, quantity, side, price=current_price)
            if order_result.get("status") != "filled":
                return {"error": "Order execution failed"}

            db_user.cash_balance += total_amount

        trade_log = TradeLog(
            user_id=user.id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=current_price,
            total_amount=total_amount,
            executed_at=datetime.utcnow()
        )
        session.add(trade_log)
        session.add(db_user)

        asset_statement = select(StockAsset).where(
            StockAsset.user_id == user.id, 
            StockAsset.symbol == symbol
        )
        asset_result = await session.execute(asset_statement)
        asset = asset_result.scalar_one_or_none()

        if side.upper() == "BUY":
            if asset:
                new_total_quantity = asset.quantity + quantity
                new_avg_price = ((asset.average_price * asset.quantity) + total_amount) / new_total_quantity
                asset.quantity = new_total_quantity
                asset.average_price = new_avg_price
                asset.updated_at = datetime.utcnow()
            else:
                asset = StockAsset(
                    user_id=user.id,
                    symbol=symbol,
                    quantity=quantity,
                    average_price=current_price,
                    updated_at=datetime.utcnow()
                )
                session.add(asset)
        
        elif side.upper() == "SELL":
            asset.quantity -= quantity
            asset.updated_at = datetime.utcnow()
            if asset.quantity <= 0:
                await session.delete(asset)

        await session.commit()

        # 💡 [알림] 매매 체결 알림 발송
        asyncio.create_task(notification_service.notify_user(
            user.id, 
            {
                "title": f"주문 체결 완료: {symbol}",
                "body": f"{side} {quantity}주가 ${current_price:.2f}에 체결되었습니다.\n잔고: ${db_user.cash_balance:.2f}"
            }
        ))

        return {
            "status": "success",
            "order_id": order_result["order_id"],
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": current_price,
            "remaining_cash": db_user.cash_balance
        }

    async def get_user_portfolio(self, session: AsyncSession, user: User):
        """사용자의 전체 포트폴리오 및 요약 정보 조회 (수익률 포함)"""
        user_statement = select(User).where(User.id == user.id)
        user_result = await session.execute(user_statement)
        db_user = user_result.scalar_one()

        asset_statement = select(StockAsset).where(StockAsset.user_id == user.id)
        asset_result = await session.execute(asset_statement)
        assets = asset_result.scalars().all()
        
        total_market_value = 0.0
        total_unrealized_profit = 0.0
        
        async def enrich_asset(asset):
            stock_data = await get_stock_info(asset.symbol)
            current_price = stock_data.get("currentPrice", asset.average_price)
            
            asset_dict = asset.dict()
            asset_dict["current_price"] = current_price
            profit = (current_price - asset.average_price) * asset.quantity
            profit_rate = ((current_price / asset.average_price) - 1) * 100 if asset.average_price > 0 else 0
            asset_dict["profit"] = profit
            asset_dict["profit_rate"] = profit_rate
            return asset_dict, (current_price * asset.quantity), profit

        results = await asyncio.gather(*[enrich_asset(a) for a in assets])
        
        enriched_assets = []
        for asset_data, market_val, profit in results:
            enriched_assets.append(asset_data)
            total_market_value += market_val
            total_unrealized_profit += profit

        initial_balance = 100000.0
        current_total_equity = db_user.cash_balance + total_market_value
        total_profit = current_total_equity - initial_balance
        total_profit_rate = (total_profit / initial_balance) * 100

        return {
            "assets": enriched_assets,
            "summary": {
                "cash_balance": db_user.cash_balance,
                "total_market_value": total_market_value,
                "total_equity": current_total_equity,
                "total_profit": total_profit,
                "total_profit_rate": total_profit_rate
            }
        }

    async def get_trade_history(self, session: AsyncSession, user: User):
        """사용자의 전체 매매 내역 조회"""
        statement = select(TradeLog).where(TradeLog.user_id == user.id).order_by(TradeLog.executed_at.desc())
        result = await session.execute(statement)
        logs = result.scalars().all()
        return logs

    async def record_equity_snapshot(self, session: AsyncSession, user: User):
        """현재 총 자산(현금+주식) 상태를 기록합니다."""
        portfolio = await self.get_user_portfolio(session, user)
        total_equity = portfolio["summary"]["total_equity"]
        
        snapshot = EquitySnapshot(user_id=user.id, total_equity=total_equity)
        session.add(snapshot)
        await session.commit()
        logger.info(f"💾 Saved equity snapshot for {user.username}: ${total_equity:.2f}")

    async def get_equity_history(self, session: AsyncSession, user: User, limit: int = 100):
        """사용자의 자산 변화 이력을 조회합니다. (최근 데이터 기준 제한)"""
        # 최근 100개 데이터만 가져와서 다시 시간순(ASC)으로 정렬
        statement = select(EquitySnapshot).where(EquitySnapshot.user_id == user.id).order_by(EquitySnapshot.timestamp.desc()).limit(limit)
        result = await session.execute(statement)
        history = result.scalars().all()
        return sorted(history, key=lambda x: x.timestamp)
