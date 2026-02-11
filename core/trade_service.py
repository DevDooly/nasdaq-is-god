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
        """매매 실행 및 DB 업데이트 (잔고 체크 + 로그 기록 + 자산 업데이트)"""
        
        # 💡 최신 사용자 정보 가져오기 (잔고 확인용)
        statement = select(User).where(User.id == user.id)
        result = await session.execute(statement)
        db_user = result.scalar_one()

        # 1. 브로커를 통한 실제 주가 조회 (Mock인 경우에도 실제가 사용)
        stock_data = await get_stock_info(symbol)
        if "error" in stock_data:
            return {"error": f"Failed to fetch price for {symbol}"}
        
        current_price = stock_data["currentPrice"]
        total_amount = current_price * quantity

        # 2. 잔고 확인 (매수 시)
        if side.upper() == "BUY":
            if db_user.cash_balance < total_amount:
                return {"error": f"Insufficient balance. Required: ${total_amount:.2f}, Available: ${db_user.cash_balance:.2f}"}
            
            # 실제 주문 실행 (브로커)
            order_result = await self.broker.place_order(symbol, quantity, side, price=current_price)
            if order_result.get("status") != "filled":
                return {"error": "Order execution failed"}
            
            # 잔고 차감
            db_user.cash_balance -= total_amount

        elif side.upper() == "SELL":
            # 보유 수량 확인
            asset_statement = select(StockAsset).where(StockAsset.user_id == user.id, StockAsset.symbol == symbol)
            asset_result = await session.execute(asset_statement)
            asset = asset_result.scalar_one_or_none()

            if not asset or asset.quantity < quantity:
                return {"error": "Insufficient stock quantity"}

            # 실제 주문 실행
            order_result = await self.broker.place_order(symbol, quantity, side, price=current_price)
            if order_result.get("status") != "filled":
                return {"error": "Order execution failed"}

            # 잔고 가산
            db_user.cash_balance += total_amount

        # 3. 거래 로그 기록 (TradeLog)
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

        # 4. 사용자 자산 업데이트 (StockAsset)
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
        # 최신 사용자 정보
        user_statement = select(User).where(User.id == user.id)
        user_result = await session.execute(user_statement)
        db_user = user_result.scalar_one()

        # 자산 목록
        asset_statement = select(StockAsset).where(StockAsset.user_id == user.id)
        asset_result = await session.execute(asset_statement)
        assets = asset_result.scalars().all()
        
        total_market_value = 0.0
        total_unrealized_profit = 0.0
        
        # 각 자산의 현재가 조회 및 수익 계산
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

        # 💡 최종 수익률 계산 로직
        # 원금(Initial Balance) 대비 (현재 잔고 + 현재 주식 가치)
        initial_balance = 100000.0 # 기본 설정값
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