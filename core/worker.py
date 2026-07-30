import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from core.database import engine
from core.models import TradingStrategy, User
from core.strategy_service import StrategyService
from core.trade_service import TradeService
from core.notification_service import notification_service
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
                    if not user_switch_map.get(strategy.user_id, True):
                        continue

                    # 전략 평가
                    action = await self.strategy_service.evaluate_strategy(strategy)
                    if action in ["BUY", "SELL"]:
                        user = next((u for u in all_users if u.id == strategy.user_id), None)
                        if user:
                            # 💡 [알림] 전략 발동 알림
                            await notification_service.notify_user(
                                user.id,
                                {
                                    "title": f"🚀 자동매매 전략 발동: {strategy.name}",
                                    "body": f"{strategy.symbol} 종목에 대해 {action} 시그널이 포착되어 주문을 실행합니다."
                                }
                            )
                            
                            await self.trade_service.execute_trade(session, user, strategy.symbol, 1.0, action)
                            logger.info(f"✅ Auto-Trade Executed: {action} {strategy.symbol}")
                
                except Exception as e:
                    logger.error(f"Error processing strategy {strategy.id}: {e}")

            # 4. 실시간 주요 이슈 및 인물 발언 주기적 스크랩 & DB 캐싱 (중복 방지)
            try:
                from core.news_scraper import news_scraper
                added = await news_scraper.run_batch_scrape(session)
                if added > 0:
                    logger.info(f"📰 [Batch Scraper] Cached {added} news & guru posts into DB.")
            except Exception as e:
                logger.error(f"Failed in batch news scraper: {e}")

    async def start(self, interval_seconds: int = 60):
        self.is_running = True
        while self.is_running:
            await self.run_once()
            await asyncio.sleep(interval_seconds)

    def stop(self):
        self.is_running = False
