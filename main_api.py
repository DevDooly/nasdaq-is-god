from fastapi import FastAPI, HTTPException, Query, Depends, status, Request, WebSocket, WebSocketDisconnect
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
from typing import List, Dict, Any, Set
import uvicorn
import os
import asyncio
import logging
import json

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_server")

# --- WebSocket 관리 클래스 ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Remaining: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.active_connections.remove(connection)

manager = ConnectionManager()

# 서비스 초기화
USE_REAL_BROKER = os.getenv("USE_REAL_BROKER", "false").lower() == "true"
broker = KISBroker() if USE_REAL_BROKER else MockBroker()
indicator_service = IndicatorService()
trade_service = TradeService(broker)
strategy_service = StrategyService(indicator_service)
trading_worker = TradingWorker(strategy_service, trade_service)

async def price_broadcaster():
    """실시간 시세를 주기적으로 브로드캐스팅하는 루프"""
    while True:
        if manager.active_connections:
            # 현재 관심있는 티커 목록 (임시로 주요 지수 및 일부 종목)
            # 실제로는 활성화된 전략이나 사용자의 포트폴리오를 기반으로 동적 생성 가능
            tickers = ["TSLA", "AAPL", "NVDA", "QQQ", "^IXIC"]
            updates = {}
            
            async def get_price(symbol):
                data = await get_stock_info(symbol)
                if "error" not in data:
                    return symbol, {
                        "price": data["currentPrice"],
                        "change": data["changePercent"]
                    }
                return symbol, None

            results = await asyncio.gather(*[get_price(t) for t in tickers])
            for symbol, val in results:
                if val:
                    updates[symbol] = val
            
            if updates:
                await manager.broadcast({"type": "price_update", "data": updates})
        
        await asyncio.sleep(10) # 10초마다 갱신

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    await init_db()
    
    # 워커 및 브로드캐스터 시작
    worker_task = asyncio.create_task(trading_worker.start(interval_seconds=60))
    broadcaster_task = asyncio.create_task(price_broadcaster())
    
    yield
    trading_worker.stop()
    worker_task.cancel()
    broadcaster_task.cancel()

app = FastAPI(title="Nasdaq is God API", lifespan=lifespan)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- WebSocket 엔드포인트 ---
@app.websocket("/ws/prices")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # 클라이언트로부터 메시지를 받을 필요는 없지만 연결 유지를 위해 대기
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# --- 기존 API들 ---

async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)) -> User:
    payload = decode_access_token(token)
    if not payload: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    username: str = payload.get("sub")
    statement = select(User).where(User.username == username)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    if user is None: raise HTTPException(status_code=404, detail="User not found")
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

async def get_portfolio(

    current_user: User = Depends(get_current_user), 

    session: AsyncSession = Depends(get_session)

):

    """사용자의 전체 포트폴리오 요약 및 자산 목록을 조회합니다."""

    return await trade_service.get_user_portfolio(session, current_user)



@app.get("/trade/history")
async def get_trade_history(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    return await trade_service.get_trade_history(session, current_user)

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
    return {"message": "Nasdaq is God API - WebSocket Enabled"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
