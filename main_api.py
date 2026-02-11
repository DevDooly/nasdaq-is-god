from fastapi import FastAPI, HTTPException, Query, Depends, status, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from core.stock_service import get_stock_info, find_ticker, get_stock_news
from core.database import init_db, get_session
from core.models import User, UserCreate, UserRead, Token, TradingStrategy, StrategyCreate, StrategyRead, StockAsset, AISentimentHistory
from core.auth import get_password_hash, verify_password, create_access_token, decode_access_token
from core.trade_service import TradeService
from core.broker import TradingBroker
from core.mock_broker import MockBroker
from core.kis_broker import KISBroker
from core.indicator_service import IndicatorService
from core.strategy_service import StrategyService
from core.ai_service import AIService
from core.worker import TradingWorker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Set, Optional
import uvicorn
import os
import asyncio
import logging
import json

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_server")

# --- 서비스 초기화 ---
USE_REAL_BROKER = os.getenv("USE_REAL_BROKER", "false").lower() == "true"
broker = KISBroker() if USE_REAL_BROKER else MockBroker()
indicator_service = IndicatorService()
ai_service = AIService()
trade_service = TradeService(broker)
strategy_service = StrategyService(indicator_service)
trading_worker = TradingWorker(strategy_service, trade_service)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    worker_task = asyncio.create_task(trading_worker.start(interval_seconds=60))
    yield
    trading_worker.stop()
    worker_task.cancel()

app = FastAPI(title="Nasdaq is God API", lifespan=lifespan)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 의존성 ---
async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)) -> User:
    payload = decode_access_token(token)
    if not payload: raise HTTPException(status_code=401, detail="Invalid token")
    username: str = payload.get("sub")
    statement = select(User).where(User.username == username)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    if user is None: raise HTTPException(status_code=404, detail="User not found")
    return user

# --- Auth ---
@app.post("/login")
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
    if result.scalar_one_or_none(): raise HTTPException(status_code=400, detail="Already registered")
    db_user = User(username=user_data.username, email=user_data.email, hashed_password=get_password_hash(user_data.password))
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user

# --- AI ---
@app.get("/ai/models")
async def list_ai_models():
    """사용 가능한 Gemini 모델 리스트를 반환합니다."""
    return ai_service.list_available_models()

@app.get("/stock/{symbol}/sentiment")
async def get_stock_sentiment(
    symbol: str, 
    model: str = "models/gemini-2.0-flash",
    force_refresh: bool = False,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """특정 종목의 AI 분석 정보를 가져옵니다. (이력 우선 조회)"""
    if not force_refresh:
        # 1. 최근 1시간 이내의 이력이 있는지 확인
        statement = select(AISentimentHistory).where(
            AISentimentHistory.user_id == current_user.id,
            AISentimentHistory.symbol == symbol.upper()
        ).order_by(AISentimentHistory.timestamp.desc())
        result = await session.execute(statement)
        history = result.scalar_one_or_none()
        
        if history:
            return {
                "score": history.score,
                "sentiment": history.sentiment,
                "summary": history.summary,
                "reason": history.reason,
                "sources": json.loads(history.sources),
                "model_name": history.model_name,
                "timestamp": history.timestamp,
                "is_history": True
            }

    # 2. 이력이 없거나 강제 갱신인 경우 새로 분석
    news = await get_stock_news(symbol)
    analysis = await ai_service.analyze_sentiment(symbol, news, model_name=model)
    
    if "error" in analysis:
        raise HTTPException(status_code=500, detail=analysis["error"])

    # 3. 분석 결과 저장
    db_history = AISentimentHistory(
        user_id=current_user.id,
        symbol=symbol.upper(),
        score=analysis["score"],
        sentiment=analysis["sentiment"],
        summary=analysis["summary"],
        reason=analysis["reason"],
        sources=json.dumps(analysis.get("sources", [])),
        model_name=model
    )
    session.add(db_history)
    await session.commit()
    
    analysis["is_history"] = False
    analysis["model_name"] = model
    analysis["timestamp"] = db_history.timestamp
    return analysis

@app.get("/market/sentiment")
async def get_market_sentiment():
    tickers = ["^IXIC", "^GSPC", "NVDA", "AAPL", "MSFT"]
    all_news = []
    results = await asyncio.gather(*[get_stock_news(t) for t in tickers])
    for news_list in results: all_news.extend(news_list)
    unique_news = {n['uuid']: n for n in all_news}.values()
    sorted_news = sorted(unique_news, key=lambda x: x.get('providerPublishTime', 0), reverse=True)
    return await ai_service.analyze_market_outlook(list(sorted_news))

# --- Trade & Portfolio ---
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

@app.get("/portfolio/history")
async def get_portfolio_history(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    return await trade_service.get_equity_history(session, current_user)

# --- Strategies ---
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

@app.delete("/strategies/{strategy_id}")
async def delete_strategy(strategy_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    statement = select(TradingStrategy).where(TradingStrategy.id == strategy_id, TradingStrategy.user_id == current_user.id)
    result = await session.execute(statement)
    db_strategy = result.scalar_one_or_none()
    if not db_strategy: raise HTTPException(status_code=404, detail="Not found")
    await session.delete(db_strategy)
    await session.commit()
    return {"status": "success"}

@app.get("/")
async def root(): return {"message": "Nasdaq is God API - AI History Ready"}

if __name__ == "__main__": uvicorn.run(app, host="0.0.0.0", port=9000)