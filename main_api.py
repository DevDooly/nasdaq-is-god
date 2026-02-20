from fastapi import FastAPI, HTTPException, Query, Depends, status, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from core.stock_service import get_stock_info, find_ticker, get_stock_news
from core.database import init_db, get_session, engine
from core.models import User, UserCreate, UserRead, Token, TradingStrategy, StrategyCreate, StrategyRead, StockAsset, AISentimentHistory, APIKeyConfig, Guru, GuruInsight
from core.auth import get_password_hash, verify_password, create_access_token, decode_access_token
from core.trade_service import TradeService
from core.broker import TradingBroker
from core.mock_broker import MockBroker
from core.kis_broker import KISBroker
from core.indicator_service import IndicatorService
from core.strategy_service import StrategyService
from core.ai_service import AIService
from core.worker import TradingWorker
from core.notification_service import notification_service
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
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

async def price_broadcaster():
    """실시간 시세 브로드캐스트 루프"""
    while True:
        try:
            if notification_service.active_connections:
                tickers = ["TSLA", "AAPL", "NVDA", "QQQ", "^IXIC"]
                updates = {}
                async def get_price(symbol):
                    data = await get_stock_info(symbol)
                    if "error" not in data:
                        return symbol, {"price": data["currentPrice"], "change": data["changePercent"]}
                    return symbol, None
                results = await asyncio.gather(*[get_price(t) for t in tickers])
                for symbol, val in results:
                    if val: updates[symbol] = val
                if updates:
                    await notification_service.broadcast({"type": "price_update", "data": updates})
        except Exception as e:
            logger.error(f"Broadcaster error: {e}")
        await asyncio.sleep(10)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    worker_task = asyncio.create_task(trading_worker.start(interval_seconds=60))
    broadcaster_task = asyncio.create_task(price_broadcaster())
    yield
    trading_worker.stop()
    worker_task.cancel()
    broadcaster_task.cancel()

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

async def get_active_api_key(user: User, session: AsyncSession) -> Optional[str]:
    statement = select(APIKeyConfig).where(APIKeyConfig.user_id == user.id, APIKeyConfig.is_active == True)
    result = await session.execute(statement)
    config = result.scalar_one_or_none()
    return config.key_value if config else None

# --- WebSocket ---
@app.websocket("/ws/updates")
async def websocket_updates(websocket: WebSocket, token: str = Query(...)):
    """실시간 시세 및 알림을 위한 통합 WebSocket 엔드포인트"""
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    username = payload.get("sub")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        user = (await session.execute(select(User).where(User.username == username))).scalar_one_or_none()
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        await notification_service.connect(user.id, websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            notification_service.disconnect(user.id, websocket)

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

# --- AI API Keys ---
@app.get("/settings/api-keys")
async def list_api_keys(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    statement = select(APIKeyConfig).where(APIKeyConfig.user_id == current_user.id).order_by(APIKeyConfig.created_at.desc())
    keys = (await session.execute(statement)).scalars().all()
    # 키 값 마스킹 처리 (Ollama는 키가 없을 수 있음)
    return [{**k.dict(), "key_value": f"{k.key_value[:4]}...{k.key_value[-4:]}" if k.key_value else "N/A"} for k in keys]

@app.post("/settings/api-keys")
async def add_api_key(data: Dict[str, Any], current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    # data 예시: { "provider": "OLLAMA", "label": "My PC", "base_url": "http://192.168.0.10:11434", "key": "" }
    statement = select(APIKeyConfig).where(APIKeyConfig.user_id == current_user.id)
    is_first = (await session.execute(statement)).first() is None
    
    new_key = APIKeyConfig(
        user_id=current_user.id,
        provider=data.get("provider", "GOOGLE").upper(),
        label=data.get("label"),
        key_value=data.get("key"),
        base_url=data.get("base_url"),
        is_active=is_first
    )
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

@app.get("/settings/api-keys/{key_id}/check-health")
async def check_api_key_health(key_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    target = (await session.execute(select(APIKeyConfig).where(APIKeyConfig.id == key_id, APIKeyConfig.user_id == current_user.id))).scalar_one_or_none()
    if not target: raise HTTPException(status_code=404)
    
    is_healthy = await ai_service.check_provider_health(
        target.provider, 
        base_url=target.base_url, 
        api_key=target.key_value
    )
    return {"status": "ok" if is_healthy else "error", "healthy": is_healthy}

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

    key_configs = (await session.execute(select(APIKeyConfig).where(APIKeyConfig.user_id == current_user.id))).scalars().all()
    configs_list = [k.dict() for k in key_configs]

    news = await get_stock_news(symbol)
    analysis = await ai_service.analyze_sentiment_with_rotation(symbol, news, configs_list, model_name=model)
    
    if "error" in analysis: return analysis

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
    try:
        tickers = ["^IXIC", "^GSPC", "NVDA", "AAPL", "MSFT"]
        results = await asyncio.gather(*[get_stock_news(t) for t in tickers])
        all_news = []
        for news_list in results:
            if news_list:
                all_news.extend(news_list)
        
        # 뉴스 구조 처리 (yfinance 최신 버전 호환성)
        extracted_news = []
        for n in all_news:
            if not n: continue
            title = n.get('title')
            uuid = n.get('uuid') or n.get('id')
            pub_time = n.get('providerPublishTime', 0)
            
            # 신규 구조 handling
            if 'content' in n and isinstance(n['content'], dict):
                content = n['content']
                title = title or content.get('title')
                pub_time = pub_time or content.get('pubDate') or 0
            
            if title and uuid:
                extracted_news.append({
                    'uuid': uuid,
                    'title': title,
                    'providerPublishTime': pub_time
                })

        unique_news = sorted(
            {n['uuid']: n for n in extracted_news}.values(),
            key=lambda x: x.get('providerPublishTime', 0),
            reverse=True
        )
        return await ai_service.analyze_market_outlook(list(unique_news))
    except Exception as e:
        logger.error(f"Market sentiment error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": str(e)}

# --- Guru Watch (Social Sentiment Alpha) ---
@app.get("/gurus")
async def list_gurus(session: AsyncSession = Depends(get_session)):
    statement = select(Guru).order_by(Guru.influence_score.desc())
    return (await session.execute(statement)).scalars().all()

@app.post("/gurus")
async def add_guru(guru_data: Dict[str, Any], current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    new_guru = Guru(**guru_data)
    session.add(new_guru)
    await session.commit()
    return new_guru

@app.patch("/gurus/{guru_id}")
async def update_guru(guru_id: int, guru_data: Dict[str, Any], current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    target = (await session.execute(select(Guru).where(Guru.id == guru_id))).scalar_one_or_none()
    if not target: raise HTTPException(status_code=404)
    for k, v in guru_data.items(): setattr(target, k, v)
    await session.commit()
    return target

@app.delete("/gurus/{guru_id}")
async def delete_guru(guru_id: int, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    target = (await session.execute(select(Guru).where(Guru.id == guru_id))).scalar_one_or_none()
    if not target: raise HTTPException(status_code=404)
    await session.delete(target)
    await session.commit()
    return {"status": "success"}

@app.get("/gurus/insights")
async def list_guru_insights(limit: int = 20, session: AsyncSession = Depends(get_session)):
    statement = select(GuruInsight, Guru.name, Guru.handle).join(Guru).order_by(GuruInsight.timestamp.desc()).limit(limit)
    results = (await session.execute(statement)).all()
    return [{"insight": r[0], "guru_name": r[1], "guru_handle": r[2]} for r in results]

@app.post("/gurus/{guru_id}/analyze")
async def analyze_guru_statement(guru_id: int, content: str, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    guru = (await session.execute(select(Guru).where(Guru.id == guru_id))).scalar_one_or_none()
    if not guru: raise HTTPException(status_code=404)
    
    analysis = await ai_service.analyze_social_impact(guru.name, content, target_symbols=guru.target_symbols)
    
    insight = GuruInsight(
        guru_id=guru.id,
        content=content,
        sentiment=analysis["sentiment"],
        score=analysis["score"],
        summary=analysis["summary"],
        reason=analysis["reason"],
        symbol=analysis.get("main_symbol")
    )
    session.add(insight)
    await session.commit()
    return insight

# 💡 실시간 소셜 Webhook 수신기
@app.post("/webhook/guru-alpha")
async def guru_alpha_webhook(request: Request, session: AsyncSession = Depends(get_session)):
    # 1. 보안 인증
    secret = request.headers.get("X-Alpha-Secret")
    if secret != os.getenv("WEBHOOK_SECRET"):
        raise HTTPException(status_code=403, detail="Invalid Secret")

    # 2. 데이터 파싱
    data = await request.json()
    handle = data.get("handle") # 예: @elonmusk
    content = data.get("text")
    source_url = data.get("url")

    if not handle or not content:
        raise HTTPException(status_code=400, detail="Missing data")

    # 3. 구루 식별
    guru = (await session.execute(select(Guru).where(Guru.handle == handle))).scalar_one_or_none()
    if not guru or not guru.is_active:
        return {"status": "ignored", "reason": "Guru not found or inactive"}

    # 4. 즉시 AI 분석
    logger.info(f"⚡ [REAL-TIME] Analyzing post from {guru.name}...")
    analysis = await ai_service.analyze_social_impact(guru.name, content, target_symbols=guru.target_symbols)
    
    # 5. 가격 스냅샷
    current_price = None
    target_symbol = analysis.get("main_symbol") or (guru.target_symbols.split(",")[0] if guru.target_symbols else None)
    if target_symbol:
        try:
            p_data = await get_stock_info(target_symbol)
            current_price = p_data.get("currentPrice")
        except: pass

    # 6. DB 저장
    insight = GuruInsight(
        guru_id=guru.id, content=content,
        sentiment=analysis["sentiment"], score=analysis["score"],
        summary=analysis["summary"], reason=analysis["reason"],
        symbol=target_symbol, source_url=source_url,
        price_at_timestamp=current_price
    )
    session.add(insight)
    
    # 7. 🚨 [CRITICAL] 자동 매매 로직 연동
    execution_result = None
    if guru.is_auto_trade_enabled:
        # 임계치 설정: Bullish 90점 이상 또는 Bearish 10점 이하
        if analysis["score"] >= 90 or analysis["score"] <= 10:
            side = "BUY" if analysis["score"] >= 90 else "SELL"
            quantity = 1.0 
            # admin 사용자 계정으로 우선 실행 (데모용)
            admin = (await session.execute(select(User).where(User.username == "admin"))).scalar_one_or_none()
            if admin and admin.is_auto_trading_enabled:
                execution_result = await trade_service.execute_trade(session, admin, target_symbol, quantity, side)
                logger.info(f"🔥 [AUTO-EXECUTE] {side} {target_symbol} due to Guru Alpha!")

    await session.commit()

    # 8. 실시간 알림 전송
    alert_msg = {
        "title": f"📢 GURU ALPHA: {guru.name}",
        "body": f"[{analysis['sentiment']}] {analysis['summary']}\nScore: {analysis['score']}\nPrice: ${current_price}\nAuto-Trade: {'SUCCESS' if execution_result and 'status' in execution_result else 'OFF'}"
    }
    await notification_service.broadcast({"type": "notification", "data": alert_msg})
    # 텔레그램은 1번 사용자(admin)에게 전송
    await notification_service.notify_user(1, alert_msg)

    return {"status": "processed", "analysis": analysis, "execution": execution_result}

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
async def root(): return {"message": "Nasdaq is God API - Real-time Ready"}

if __name__ == "__main__": uvicorn.run(app, host="0.0.0.0", port=9000)
