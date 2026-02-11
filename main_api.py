from fastapi import FastAPI, HTTPException, Query, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from core.stock_service import get_stock_info, find_ticker
from core.database import init_db, get_session
from core.models import User, UserCreate, UserRead, Token, TradingStrategy, StrategyCreate, StrategyRead
from core.auth import get_password_hash, verify_password, create_access_token, decode_access_token
from core.trade_service import TradeService
from core.broker import TradingBroker
from core.mock_broker import MockBroker
from core.kis_broker import KISBroker
from core.indicator_service import IndicatorService
from core.strategy_service import StrategyService
from core.worker import TradingWorker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from contextlib import asynccontextmanager
from typing import List, Dict, Any
import uvicorn
import os
import asyncio
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_server")

# 서비스 초기화
USE_REAL_BROKER = os.getenv("USE_REAL_BROKER", "false").lower() == "true"
broker = KISBroker() if USE_REAL_BROKER else MockBroker()
indicator_service = IndicatorService()
trade_service = TradeService(broker)
strategy_service = StrategyService(indicator_service)
trading_worker = TradingWorker(strategy_service, trade_service)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시 실행
    logger.info("Initializing database...")
    await init_db()
    
    # 💡 자동매매 워커를 백그라운드 태스크로 실행
    worker_task = asyncio.create_task(trading_worker.start(interval_seconds=60))
    
    yield
    # 서버 종료 시 실행
    trading_worker.stop()
    worker_task.cancel()

app = FastAPI(title="Nasdaq is God API", lifespan=lifespan)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 의존성: 현재 로그인한 사용자 가져오기
async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    session: AsyncSession = Depends(get_session)
) -> User:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    username: str = payload.get("sub")
    statement = select(User).where(User.username == username)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_session)):
    statement = select(User).where(User.username == form_data.username)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    return {"access_token": create_access_token(data={"sub": user.username}), "token_type": "bearer"}

@app.post("/signup", response_model=UserRead)
async def signup(user_data: UserCreate, session: AsyncSession = Depends(get_session)):
    statement = select(User).where(User.username == user_data.username)
    result = await session.execute(statement)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already registered")
    db_user = User(username=user_data.username, email=user_data.email, hashed_password=get_password_hash(user_data.password))
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user

@app.get("/search")
async def search_stock(q: str = Query(..., min_length=1)):
    result = await find_ticker(q)
    if not result: raise HTTPException(status_code=404, detail="Not found")
    return result

@app.get("/stock/{symbol}/indicators")
async def get_stock_indicators(symbol: str):
    return await indicator_service.get_indicators(symbol)

@app.post("/trade/order")
async def place_trade_order(symbol: str, quantity: float, side: str, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    result = await trade_service.execute_trade(session, current_user, symbol, quantity, side)
    if "error" in result: raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/portfolio")
async def get_portfolio(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    return await trade_service.get_user_portfolio(session, current_user)

@app.get("/trade/history")
async def get_trade_history(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    return await trade_service.get_trade_history(session, current_user)

# --- 전략(Strategy) 관리 API ---

@app.post("/strategies", response_model=StrategyRead)
async def create_strategy(strategy: StrategyCreate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    db_strategy = TradingStrategy(**strategy.dict(), user_id=current_user.id)
    session.add(db_strategy)
    await session.commit()
    await session.refresh(db_strategy)
    return db_strategy

@app.get("/strategies", response_model=List[StrategyRead])
async def list_strategies(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    statement = select(TradingStrategy).where(TradingStrategy.user_id == current_user.id)
    result = await session.execute(statement)
    return result.scalars().all()

@app.patch("/strategies/{strategy_id}/toggle")
async def toggle_strategy(strategy_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    statement = select(TradingStrategy).where(TradingStrategy.id == strategy_id, TradingStrategy.user_id == current_user.id)
    result = await session.execute(statement)
    db_strategy = result.scalar_one_or_none()
    if not db_strategy: raise HTTPException(status_code=404, detail="Strategy not found")
    db_strategy.is_active = not db_strategy.is_active
    await session.commit()
    return {"status": "success", "is_active": db_strategy.is_active}

@app.delete("/strategies/{strategy_id}")
async def delete_strategy(strategy_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    statement = select(TradingStrategy).where(TradingStrategy.id == strategy_id, TradingStrategy.user_id == current_user.id)
    result = await session.execute(statement)
    db_strategy = result.scalar_one_or_none()
    if not db_strategy: raise HTTPException(status_code=404, detail="Strategy not found")
    await session.delete(db_strategy)
    await session.commit()
    return {"status": "success"}

@app.get("/")
async def root():
    return {"message": "Nasdaq is God API - Auto Trading Enabled"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)