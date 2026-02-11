import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from core.database import engine
from core.models import TradingStrategy, User
from core.strategy_service import StrategyService
from core.trade_service import TradeService
from core.indicator_service import IndicatorService
from core.mock_broker import MockBroker
from bot.config import logger
from sqlalchemy.orm import sessionmaker

class TradingWorker:
    def __init__(self, strategy_service: StrategyService, trade_service: TradeService):
        self.strategy_service = strategy_service
        self.trade_service = trade_service
        self.is_running = False

    async def run_once(self):
        """활성화된 모든 전략을 한 번씩 체크하고 필요시 매매 실행"""
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # 1. 활성화된 전략 목록 가져오기
            statement = select(TradingStrategy).where(TradingStrategy.is_active == True)
            result = await session.execute(statement)
            active_strategies = result.scalars().all()
            
            logger.info(f"Checking {len(active_strategies)} active strategies...")

            for strategy in active_strategies:
                try:
                    # 2. 전략 평가
                    action = await self.strategy_service.evaluate_strategy(strategy)
                    
                    if action in ["BUY", "SELL"]:
                        logger.info(f"🚩 Strategy Match! {strategy.name} ({strategy.symbol}) -> {action}")
                        
                        # 3. 사용자 정보 가져오기
                        user_statement = select(User).where(User.id == strategy.user_id)
                        user_result = await session.execute(user_statement)
                        user = user_result.scalar_one_or_none()
                        
                        if user:
                            # 4. 매매 실행 (기본 1주 예시)
                            # 실제로는 전략 파라미터에 수량을 넣어야 함
                            await self.trade_service.execute_trade(
                                session, user, strategy.symbol, 1.0, action
                            )
                            logger.info(f"✅ Auto-Trade Executed: {action} {strategy.symbol}")
                
                except Exception as e:
                    logger.error(f"Error processing strategy {strategy.id}: {e}")

    async def start(self, interval_seconds: int = 60):
        """주기적으로 워커 실행"""
        logger.info(f"Starting Trading Worker (Interval: {interval_seconds}s)...")
        self.is_running = True
        while self.is_running:
            await self.run_once()
            await asyncio.sleep(interval_seconds)

    def stop(self):
        self.is_running = False
        logger.info("Trading Worker Stopped.")
