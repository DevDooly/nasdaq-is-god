from fastapi import FastAPI, HTTPException, Query, Depends, status, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from core.stock_service import get_stock_info, find_ticker, get_stock_news
from core.database import init_db, get_session
from core.models import User, UserCreate, UserRead, Token, TradingStrategy, StrategyCreate, StrategyRead, StockAsset, AISentimentHistory, APIKeyConfig
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
from datetime import datetime
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

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

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

# --- AI API Keys ---
@app.get("/settings/api-keys")
async def list_api_keys(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    statement = select(APIKeyConfig).where(APIKeyConfig.user_id == current_user.id).order_by(APIKeyConfig.created_at.desc())
    keys = (await session.execute(statement)).scalars().all()
    return [{**k.dict(), "key_value": f"{k.key_value[:4]}...{k.key_value[-4:]}"} for k in keys]

@app.post("/settings/api-keys")
async def add_api_key(label: str, key: str, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    statement = select(APIKeyConfig).where(APIKeyConfig.user_id == current_user.id)
    is_first = (await session.execute(statement)).first() is None
    new_key = APIKeyConfig(user_id=current_user.id, label=label, key_value=key, is_active=is_first)
    session.add(new_key)
    await session.commit()
    return {"status": "success"}

@app.patch("/settings/api-keys/{key_id}/activate")
async def activate_api_key(key_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    statement = select(APIKeyConfig).where(APIKeyConfig.user_id == current_user.id, APIKeyConfig.is_active == True)
    active_keys = (await session.execute(statement)).scalars().all()
    for k in active_keys: k.is_active = False
    target = (await session.execute(select(APIKeyConfig).where(APIKeyConfig.id == key_id, APIKeyConfig.user_id == current_user.id))).scalar_one_or_none()
    if target: target.is_active = True
    await session.commit()
    return {"status": "success"}

@app.delete("/settings/api-keys/{key_id}")
async def delete_api_key(key_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    target = (await session.execute(select(APIKeyConfig).where(APIKeyConfig.id == key_id, APIKeyConfig.user_id == current_user.id))).scalar_one_or_none()
    if target: await session.delete(target)
    await session.commit()
    return {"status": "success"}

# --- AI Sentiment ---
@app.get("/stock/{symbol}/sentiment")
async def get_stock_sentiment(
    symbol: str, 
    model: str = "models/gemini-2.0-flash",
    force_refresh: bool = False,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    if not force_refresh:
        statement = select(AISentimentHistory).where(AISentimentHistory.user_id == current_user.id, AISentimentHistory.symbol == symbol.upper()).order_by(AISentimentHistory.timestamp.desc())
        history = (await session.execute(statement)).scalar_one_or_none()
        if history: return {**history.dict(), "sources": json.loads(history.sources), "is_history": True}

    # 💡 모든 키를 가져와서 로테이션 시도
    key_configs_stmt = select(APIKeyConfig).where(APIKeyConfig.user_id == current_user.id)
    key_configs = (await session.execute(key_configs_stmt)).scalars().all()
    configs_list = [k.dict() for k in key_configs] # 키 값 포함

    news = await get_stock_news(symbol)
    analysis = await ai_service.analyze_sentiment_with_rotation(symbol, news, configs_list, model_name=model)
    
    if "error" in analysis: return analysis

    # 성공한 키의 사용량 업데이트
    used_key_id = analysis.get("used_key_id")
    if used_key_id:
        used_key = (await session.execute(select(APIKeyConfig).where(APIKeyConfig.id == used_key_id))).scalar_one()
        used_key.usage_count += 1
        used_key.last_used_at = datetime.utcnow()
        session.add(used_key)

    db_history = AISentimentHistory(
        user_id=current_user.id, symbol=symbol.upper(), score=analysis["score"],
        sentiment=analysis["sentiment"], summary=analysis["summary"], reason=analysis["reason"],
        sources=json.dumps(analysis.get("sources", [])), model_name=model
    )
    session.add(db_history)
    await session.commit()
    return {**analysis, "is_history": False, "timestamp": db_history.timestamp}

@app.get("/ai/models")
async def list_ai_models(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    config = (await session.execute(select(APIKeyConfig).where(APIKeyConfig.user_id == current_user.id, APIKeyConfig.is_active == True))).scalar_one_or_none()
    return ai_service.list_available_models(api_key=config.key_value if config else None)

@app.get("/market/sentiment")
async def get_market_sentiment():
    tickers = ["^IXIC", "^GSPC", "NVDA", "AAPL", "MSFT"]
    results = await asyncio.gather(*[get_stock_news(t) for t in tickers])
    all_news = []
    for news_list in results: all_news.extend(news_list)
    unique_news = sorted({n['uuid']: n for n in all_news}.values(), key=lambda x: x.get('providerPublishTime', 0), reverse=True)
    return await ai_service.analyze_market_outlook(list(unique_news))

# --- Common ---
@app.get("/users/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_user)): return current_user

@app.patch("/users/me/auto-trading")
async def toggle_master_auto_trading(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    current_user.is_auto_trading_enabled = not current_user.is_auto_trading_enabled
    session.add(current_user)
    await session.commit()
    return {"is_auto_trading_enabled": current_user.is_auto_trading_enabled}

@app.get("/search")
async def search_stock(q: str = Query(..., min_length=1)):
    result = await find_ticker(q)
    if not result: raise HTTPException(status_code=404)
    return result

@app.get("/stock/{symbol}/indicators")
async def get_stock_indicators(symbol: str): return await indicator_service.get_indicators(symbol)

@app.post("/trade/order")
async def place_trade_order(symbol: str, quantity: float, side: str, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    result = await trade_service.execute_trade(session, current_user, symbol, quantity, side)
    if "error" in result: raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/trade/liquidate")
async def liquidate_positions(symbols: List[str] = Query(...), current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    results = []
    for symbol in symbols:
        asset = (await session.execute(select(StockAsset).where(StockAsset.user_id == current_user.id, StockAsset.symbol == symbol))).scalar_one_or_none()
        if asset and asset.quantity > 0:
            res = await trade_service.execute_trade(session, current_user, symbol, asset.quantity, "SELL")
            results.append({"symbol": symbol, "status": "liquidated"})
        else: results.append({"symbol": symbol, "status": "skipped"})
    return {"results": results}

@app.get("/portfolio")
async def get_portfolio(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)): return await trade_service.get_user_portfolio(session, current_user)

@app.get("/portfolio/history")
async def get_portfolio_history(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)): return await trade_service.get_equity_history(session, current_user)

@app.get("/trade/history")
async def get_trade_history(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)): return await trade_service.get_trade_history(session, current_user)

@app.post("/strategies", response_model=StrategyRead)
async def create_strategy(strategy: StrategyCreate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    db_strategy = TradingStrategy(**strategy.dict(), user_id=current_user.id)
    session.add(db_strategy)
    await session.commit()
    await session.refresh(db_strategy)
    return db_strategy

@app.get("/strategies", response_model=List[StrategyRead])
async def list_strategies(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    return (await session.execute(select(TradingStrategy).where(TradingStrategy.user_id == current_user.id))).scalars().all()

@app.patch("/strategies/{strategy_id}/toggle")
async def toggle_strategy(strategy_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    db_strategy = (await session.execute(select(TradingStrategy).where(TradingStrategy.id == strategy_id, TradingStrategy.user_id == current_user.id))).scalar_one_or_none()
    if not db_strategy: raise HTTPException(status_code=404)
    db_strategy.is_active = not db_strategy.is_active
    await session.commit()
    return {"status": "success", "is_active": db_strategy.is_active}

@app.delete("/strategies/{strategy_id}")
async def delete_strategy(strategy_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    db_strategy = (await session.execute(select(TradingStrategy).where(TradingStrategy.id == strategy_id, TradingStrategy.user_id == current_user.id))).scalar_one_or_none()
    if not db_strategy: raise HTTPException(status_code=404)
    await session.delete(db_strategy)
    await session.commit()
    return {"status": "success"}

@app.get("/")
async def root(): return {"message": "Nasdaq is God API - Auto-Rotation Ready"}

if __name__ == "__main__": uvicorn.run(app, host="0.0.0.0", port=9000)
