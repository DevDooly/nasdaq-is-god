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

async def get_active_api_key(user: User, session: AsyncSession) -> Optional[str]:
    """사용자가 설정한 활성 API 키를 가져옵니다."""
    statement = select(APIKeyConfig).where(APIKeyConfig.user_id == user.id, APIKeyConfig.is_active == True)
    result = await session.execute(statement)
    config = result.scalar_one_or_none()
    return config.key_value if config else None

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

# --- AI 설정 API ---
@app.get("/settings/api-keys")
async def list_api_keys(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    statement = select(APIKeyConfig).where(APIKeyConfig.user_id == current_user.id).order_by(APIKeyConfig.created_at.desc())
    result = await session.execute(statement)
    keys = result.scalars().all()
    # 키 값은 마스킹하여 반환
    return [{**k.dict(), "key_value": f"{k.key_value[:4]}...{k.key_value[-4:]}"} for k in keys]

@app.post("/settings/api-keys")
async def add_api_key(label: str, key: str, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    # 첫 번째 키라면 자동으로 활성화
    statement = select(APIKeyConfig).where(APIKeyConfig.user_id == current_user.id)
    existing = await session.execute(statement)
    is_first = existing.first() is None
    
    new_key = APIKeyConfig(user_id=current_user.id, label=label, key_value=key, is_active=is_first)
    session.add(new_key)
    await session.commit()
    return {"status": "success"}

@app.patch("/settings/api-keys/{key_id}/activate")
async def activate_api_key(key_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    # 기존 활성 키 해제
    statement = select(APIKeyConfig).where(APIKeyConfig.user_id == current_user.id, APIKeyConfig.is_active == True)
    active_keys = (await session.execute(statement)).scalars().all()
    for k in active_keys: k.is_active = False
    
    # 새 키 활성화
    target_statement = select(APIKeyConfig).where(APIKeyConfig.id == key_id, APIKeyConfig.user_id == current_user.id)
    target = (await session.execute(target_statement)).scalar_one_or_none()
    if not target: raise HTTPException(status_code=404)
    target.is_active = True
    
    await session.commit()
    return {"status": "success"}

@app.delete("/settings/api-keys/{key_id}")
async def delete_api_key(key_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    statement = select(APIKeyConfig).where(APIKeyConfig.id == key_id, APIKeyConfig.user_id == current_user.id)
    key = (await session.execute(statement)).scalar_one_or_none()
    if not key: raise HTTPException(status_code=404)
    await session.delete(key)
    await session.commit()
    return {"status": "success"}

# --- AI 분석 API ---
@app.get("/ai/models")
async def list_ai_models(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    key = await get_active_api_key(current_user, session)
    return ai_service.list_available_models(api_key=key)

@app.get("/stock/{symbol}/sentiment")
async def get_stock_sentiment(
    symbol: str, 
    model: str = "models/gemini-2.0-flash",
    force_refresh: bool = False,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """특정 종목의 AI 분석 정보를 가져옵니다."""
    if not force_refresh:
        statement = select(AISentimentHistory).where(
            AISentimentHistory.user_id == current_user.id,
            AISentimentHistory.symbol == symbol.upper()
        ).order_by(AISentimentHistory.timestamp.desc())
        history = (await session.execute(statement)).scalar_one_or_none()
        
        if history:
            return {**history.dict(), "sources": json.loads(history.sources), "is_history": True}

    api_key = await get_active_api_key(current_user, session)
    news = await get_stock_news(symbol)
    analysis = await ai_service.analyze_sentiment(symbol, news, model_name=model, api_key=api_key)
    
    if "error" in analysis: return analysis

    # 사용량 카운트 및 이력 저장
    db_history = AISentimentHistory(
        user_id=current_user.id, symbol=symbol.upper(), score=analysis["score"],
        sentiment=analysis["sentiment"], summary=analysis["summary"], reason=analysis["reason"],
        sources=json.dumps(analysis.get("sources", [])), model_name=model
    )
    
    # 💡 API 키 사용량 업데이트
    key_stmt = select(APIKeyConfig).where(APIKeyConfig.user_id == current_user.id, APIKeyConfig.is_active == True)
    key_config = (await session.execute(key_stmt)).scalar_one_or_none()
    if key_config:
        key_config.usage_count += 1
        key_config.last_used_at = datetime.utcnow()
        session.add(key_config)

    session.add(db_history)
    await session.commit()
    return {**analysis, "is_history": False, "timestamp": db_history.timestamp}

# ... (나머지 엔드포인트 유지) ...
@app.get("/users/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.patch("/users/me/auto-trading")
async def toggle_master_auto_trading(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    current_user.is_auto_trading_enabled = not current_user.is_auto_trading_enabled
    session.add(current_user)
    await session.commit()
    return {"is_auto_trading_enabled": current_user.is_auto_trading_enabled}

@app.get("/search")
async def search_stock(q: str = Query(..., min_length=1)):
    result = await find_ticker(q)
    if not result: raise HTTPException(status_code=404, detail="Not found")
    return result

@app.get("/stock/{symbol}/indicators")
async def get_stock_indicators(symbol: str):
    return await indicator_service.get_indicators(symbol)

@app.get("/market/sentiment")
async def get_market_sentiment():
    tickers = ["^IXIC", "^GSPC", "NVDA", "AAPL", "MSFT"]
    all_news = []
    results = await asyncio.gather(*[get_stock_news(t) for t in tickers])
    for news_list in results: all_news.extend(news_list)
    unique_news = {n['uuid']: n for n in all_news}.values()
    sorted_news = sorted(unique_news, key=lambda x: x.get('providerPublishTime', 0), reverse=True)
    return await ai_service.analyze_market_outlook(list(sorted_news))

@app.post("/trade/order")
async def place_trade_order(symbol: str, quantity: float, side: str, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    result = await trade_service.execute_trade(session, current_user, symbol, quantity, side)
    if "error" in result: raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/trade/liquidate")
async def liquidate_positions(symbols: List[str] = Query(...), current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    results = []
    for symbol in symbols:
        asset_statement = select(StockAsset).where(StockAsset.user_id == current_user.id, StockAsset.symbol == symbol)
        asset = (await session.execute(asset_statement)).scalar_one_or_none()
        if asset and asset.quantity > 0:
            res = await trade_service.execute_trade(session, current_user, symbol, asset.quantity, "SELL")
            results.append({"symbol": symbol, "status": "liquidated", "detail": res})
        else: results.append({"symbol": symbol, "status": "skipped"})
    return {"results": results}

@app.get("/portfolio")
async def get_portfolio(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    return await trade_service.get_user_portfolio(session, current_user)

@app.get("/portfolio/history")
async def get_portfolio_history(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    return await trade_service.get_equity_history(session, current_user)

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
    db_strategy = (await session.execute(statement)).scalar_one_or_none()
    if not db_strategy: raise HTTPException(status_code=404)
    db_strategy.is_active = not db_strategy.is_active
    await session.commit()
    return {"status": "success", "is_active": db_strategy.is_active}

@app.delete("/strategies/{strategy_id}")
async def delete_strategy(strategy_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    statement = select(TradingStrategy).where(TradingStrategy.id == strategy_id, TradingStrategy.user_id == current_user.id)
    db_strategy = (await session.execute(statement)).scalar_one_or_none()
    if not db_strategy: raise HTTPException(status_code=404)
    await session.delete(db_strategy)
    await session.commit()
    return {"status": "success"}

@app.get("/")
async def root(): return {"message": "Nasdaq is God API - Multi-Key Ready"}

if __name__ == "__main__": uvicorn.run(app, host="0.0.0.0", port=9000)