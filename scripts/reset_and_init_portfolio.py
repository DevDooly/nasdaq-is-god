import asyncio
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from core.database import engine
from core.models import User, StockAsset, TradeLog
from core.stock_service import get_stock_info
from datetime import datetime

async def reset_and_init():
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    symbols = ["TSLA", "NVDA", "GOOGL"]
    quantity = 10.0
    initial_cash = 100000.0

    async with async_session() as session:
        # 1. admin 사용자 가져오기
        statement = select(User).where(User.username == "admin")
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ User 'admin' not found.")
            return

        print(f"🧹 Resetting data for user: {user.username}")

        # 2. 기존 자산 및 매매 이력 삭제
        asset_del_stmt = select(StockAsset).where(StockAsset.user_id == user.id)
        assets = (await session.execute(asset_del_stmt)).scalars().all()
        for a in assets: await session.delete(a)

        log_del_stmt = select(TradeLog).where(TradeLog.user_id == user.id)
        logs = (await session.execute(log_del_stmt)).scalars().all()
        for l in logs: await session.delete(l)

        # 3. 잔고 초기화
        user.cash_balance = initial_cash
        session.add(user)
        await session.commit()

        print(f"💰 Initial Balance set to ${initial_cash}")

        # 4. 새로운 종목 매수 진행
        for symbol in symbols:
            print(f"🌐 Fetching current price for {symbol}...")
            stock_data = await get_stock_info(symbol)
            if "error" in stock_data:
                print(f"❌ Failed to fetch price for {symbol}. Skipping.")
                continue
            
            price = stock_data["currentPrice"]
            total_cost = price * quantity
            
            if user.cash_balance < total_cost:
                print(f"❌ Insufficient funds for {symbol}")
                continue

            # 매매 이력 생성
            trade_log = TradeLog(
                user_id=user.id,
                symbol=symbol,
                side="BUY",
                quantity=quantity,
                price=price,
                total_amount=total_cost,
                executed_at=datetime.utcnow()
            )
            
            # 자산 생성
            asset = StockAsset(
                user_id=user.id,
                symbol=symbol,
                quantity=quantity,
                average_price=price,
                updated_at=datetime.utcnow()
            )
            
            # 잔고 차감
            user.cash_balance -= total_cost
            
            session.add(trade_log)
            session.add(asset)
            session.add(user)
            
            print(f"✅ Successfully bought {quantity} shares of {symbol} at ${price:.2f}")

        await session.commit()
        print("✨ Portfolio initialization complete!")

if __name__ == "__main__":
    asyncio.run(reset_and_init())
