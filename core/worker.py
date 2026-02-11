import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from core.database import engine
from core.models import TradingStrategy, User
from core.strategy_service import StrategyService
from core.trade_service import TradeService
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
            # 1. 모든 사용자 정보 가져오기 (마스터 스위치 확인용)
            users_statement = select(User)
            users_result = await session.execute(users_statement)
            all_users = users_result.scalars().all()
            
            # 💡 각 사용자별 마스터 스위치 상태 맵 생성
            user_switch_map = {user.id: user.is_auto_trading_enabled for user in all_users}

            # 2. 자산 스냅샷 기록
            for user in all_users:
                try:
                    await self.trade_service.record_equity_snapshot(session, user)
                except Exception as e:
                    logger.error(f"Failed to save snapshot for {user.username}: {e}")

            # 3. 활성화된 전략 목록 가져오기
            statement = select(TradingStrategy).where(TradingStrategy.is_active == True)
            result = await session.execute(statement)
            active_strategies = result.scalars().all()
            
            logger.info(f"Checking {len(active_strategies)} active strategies...")

            for strategy in active_strategies:
                try:
                    # 💡 [핵심] 마스터 스위치가 꺼져있으면 해당 사용자의 전략 건너뜀
                    if not user_switch_map.get(strategy.user_id, True):
                        logger.info(f"⏸️ Skipping strategy {strategy.name} (User auto-trading DISABLED)")
                        continue

                    # 전략 평가 및 매매 실행
                    action = await self.strategy_service.evaluate_strategy(strategy)
                    if action in ["BUY", "SELL"]:
                        user = next((u for u in all_users if u.id == strategy.user_id), None)
                        if user:
                            await self.trade_service.execute_trade(session, user, strategy.symbol, 1.0, action)
                            logger.info(f"✅ Auto-Trade Executed: {action} {strategy.symbol}")
                
                except Exception as e:
                    logger.error(f"Error processing strategy {strategy.id}: {e}")

    async def start(self, interval_seconds: int = 60):
        self.is_running = True
        while self.is_running:
            await self.run_once()
            await asyncio.sleep(interval_seconds)

    def stop(self):
        self.is_running = False