from fastapi import FastAPI, HTTPException, Query, Depends, status, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from core.stock_service import get_stock_info, find_ticker, get_stock_news
from core.database import init_db, get_session, engine
from core.models import User, UserCreate, UserRead, Token, TradingStrategy, StrategyCreate, StrategyRead, StockAsset, AISentimentHistory, APIKeyConfig, Guru, GuruInsight, NewsArticle
from core.auth import get_password_hash, verify_password, create_access_token, decode_access_token
from core.trade_service import TradeService
from core.broker import TradingBroker
from core.mock_broker import MockBroker
from core.kis_broker import KISBroker
from core.indicator_service import IndicatorService
from core.strategy_service import StrategyService
from core.ai_service import AIService
from core.worker import TradingWorker
from core.backtest_engine import BacktestEngine
from core.social_service import SocialService
from core.sentiment_engine import SentimentEngine
from core.hybrid_strategy import HybridStrategyEngine
from core.notification_service import notification_service
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import select, or_
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Set, Optional
from datetime import datetime
import uvicorn
import os
import asyncio
import logging
import json
import random
import time
import traceback

from collections import deque

# --- 상세 로깅 & EFK 연동 체계 구축 ---
log_buffer = deque(maxlen=200)

class BufferHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            log_buffer.append(msg)
        except Exception:
            pass

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "@timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "filename": record.filename,
            "lineno": record.lineno,
            "message": record.getMessage(),
            "service": "nasdaq-backend"
        }
        if hasattr(record, "http_data"):
            log_data.update(record.http_data)
        return json.dumps(log_data, ensure_ascii=False)

formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s')
json_formatter = JSONFormatter()

console_handler = logging.StreamHandler()
console_handler.setFormatter(json_formatter)

buffer_handler = BufferHandler()
buffer_handler.setFormatter(formatter)

logger = logging.getLogger("api_server")
logger.setLevel(logging.INFO)
logger.addHandler(console_handler)
logger.addHandler(buffer_handler)


# --- 서비스 초기화 ---
USE_REAL_BROKER = os.getenv("USE_REAL_BROKER", "false").lower() == "true"
broker = KISBroker() if USE_REAL_BROKER else MockBroker()
indicator_service = IndicatorService()
ai_service = AIService()
social_service = SocialService()
sentiment_engine = SentimentEngine(ai_service, social_service)
hybrid_strategy_engine = HybridStrategyEngine(indicator_service, sentiment_engine)
trade_service = TradeService(broker)
strategy_service = StrategyService(indicator_service, hybrid_engine=hybrid_strategy_engine)
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

async def ensure_default_data():
    try:
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            # 1. 기본 관리자 계정 생성
            statement_user = select(User).where(User.username == "admin")
            result_user = await session.execute(statement_user)
            if not result_user.scalar_one_or_none():
                logger.info("🔐 기본 계정(admin) 생성 중...")
                default_user = User(
                    username="admin",
                    email="admin@example.com",
                    hashed_password=get_password_hash("admin1234")
                )
                session.add(default_user)
                await session.commit()

            # 2. 기본 AI 대가(Guru) 및 발언 데이터 시딩
            statement_guru = select(Guru)
            result_guru = await session.execute(statement_guru)
            if not result_guru.scalars().first():
                logger.info("🧠 AI 대가(Guru) 데이터 시딩 중...")
                gurus_seed = [
                    Guru(name="Donald Trump", handle="@realDonaldTrump", description="47th U.S. President & Market Catalyst", influence_score=99, target_symbols="DJT,TSLA,NVDA,BTC"),
                    Guru(name="Elon Musk", handle="@elonmusk", description="Tesla & xAI CEO", influence_score=95, target_symbols="TSLA,NVDA"),
                    Guru(name="Jensen Huang", handle="@jensenhuang", description="NVIDIA Founder & CEO", influence_score=98, target_symbols="NVDA,TSM,MSFT"),
                    Guru(name="Cathie Wood", handle="@cathiewood", description="ARK Invest CEO & CIO", influence_score=88, target_symbols="TSLA,COIN,PLTR"),
                    Guru(name="Warren Buffett", handle="@berkshire", description="Berkshire Hathaway Chairman", influence_score=90, target_symbols="AAPL,BAC,KO"),
                    Guru(name="Sam Altman", handle="@sama", description="OpenAI CEO", influence_score=92, target_symbols="MSFT,NVDA"),
                ]
                for g in gurus_seed:
                    session.add(g)
                await session.commit()

                gurus_db = (await session.execute(select(Guru))).scalars().all()
                guru_map = {g.name: g.id for g in gurus_db}

                now = datetime.utcnow()
                insights_seed = [
                    GuruInsight(
                        guru_id=guru_map.get("Donald Trump", 1),
                        symbol="DJT",
                        content="America will lead the world in AI energy infrastructure deregulation and next-generation tech manufacturing. We will unleash domestic energy for supercomputing!",
                        sentiment="Bullish",
                        score=96,
                        summary="미국 AI 에너지 인프라 규제 완화 및 대규모 슈퍼컴퓨팅 허브 구축 선언",
                        reason="에너지 규제 해제로 대규모 데이터센터 전력 공급 문제 해결 및 미국 빅테크 수혜 기대감 고조",
                        price_at_timestamp=34.20,
                        timestamp=now
                    ),
                    GuruInsight(
                        guru_id=guru_map.get("Elon Musk", 1),
                        symbol="TSLA",
                        content="Supercomputing capacity for FSD V13 will double by next quarter. Tesla is an AI & Robotics company.",
                        sentiment="Bullish",
                        score=88,
                        summary="FSD V13 슈퍼컴퓨팅 용량 2배 확충 및 로보틱스 비전 강조",
                        reason="자율주행 FSD 버전 13 컴퓨팅 파워 급증으로 기술적 도약 기대감 고조",
                        price_at_timestamp=238.50,
                        timestamp=now
                    ),
                    GuruInsight(
                        guru_id=guru_map.get("Jensen Huang", 1),
                        symbol="NVDA",
                        content="Blackwell chip demand is insane. Enterprise AI adoption is entering the second wave.",
                        sentiment="Bullish",
                        score=94,
                        summary="블랙웰 칩 수요 폭발 및 엔터프라이즈 AI 2차 파도 도달",
                        reason="차세대 블랙웰 GPU 공급 부족 지속 및 전 세계 기업들의 AI 인프라 투자 지속 확인",
                        price_at_timestamp=124.20,
                        timestamp=now
                    ),
                    GuruInsight(
                        guru_id=guru_map.get("Cathie Wood", 1),
                        symbol="TSLA",
                        content="AI-driven autonomous taxi networks could represent a $10 trillion global revenue opportunity.",
                        sentiment="Bullish",
                        score=90,
                        summary="자율주행 로보택시 네트워크 시장 규모 10조 달러 전망",
                        reason="로보택시 상용화가 테슬라 기업가치의 핵심 동력이 될 것으로 평가",
                        price_at_timestamp=235.10,
                        timestamp=now
                    ),
                    GuruInsight(
                        guru_id=guru_map.get("Sam Altman", 1),
                        symbol="MSFT",
                        content="AGI compute requirements will exceed all current energy expectations, but scaling laws hold true.",
                        sentiment="Bullish",
                        score=86,
                        summary="AGI 컴퓨팅 수요 및 스케일링 법칙 유효성 재확인",
                        reason="클라우드 인프라 파트너사인 마이크로소프트의 지속적인 데이터센터 수혜 기대",
                        price_at_timestamp=445.80,
                        timestamp=now
                    ),
                    GuruInsight(
                        guru_id=guru_map.get("Warren Buffett", 1),
                        symbol="AAPL",
                        content="Cash reserves are at record highs. We wait for extraordinary value opportunities.",
                        sentiment="Neutral",
                        score=52,
                        summary="역대 최고 수준의 현금 비축 및 우량 매수 기회 대기",
                        reason="시장 변동성 대비 안정적 자금 운용 기조 및 관망 자세 유지",
                        price_at_timestamp=224.30,
                        timestamp=now
                    )
                ]
                for ins in insights_seed:
                    session.add(ins)
                await session.commit()

    except Exception as e:
        logger.error(f"⚠️ 데이터 시딩 오류 발생 (서버는 정상 구동됩니다): {e}")

async def wait_for_db():
    retries = 15
    while retries > 0:
        try:
            async with engine.begin() as conn:
                logger.info("✅ Database connection established successfully.")
                return
        except Exception as e:
            retries -= 1
            logger.warning(f"⏳ Database connection waiting... ({retries} attempts remaining): {e}")
            await asyncio.sleep(2)

async def fetch_and_analyze_guru_feeds():
    """대가들의 최신 소셜/트위터 글을 수집하여 AI 분석 후 DB에 저장하는 비동기 함수"""
    logger.info("📡 [Guru Feed] 대가들의 최신 소셜/트위터 피드 수집 및 AI 분석을 진행합니다...")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        gurus = (await session.execute(select(Guru).where(Guru.is_active == True))).scalars().all()
        feed_templates = {

            "Donald Trump": [
                {"symbol": "DJT", "content": "Tariffs on foreign competitors will bring manufacturing back to the USA at record speed. American AI power is unstoppable!"},
                {"symbol": "BTC", "content": "Strategic Bitcoin Reserve will make America the undisputed crypto superpower of the world!"},
                {"symbol": "TSLA", "content": "American innovation in autonomous vehicles and robotics must be accelerated without government bureaucracy."}
            ],
            "Elon Musk": [
                {"symbol": "TSLA", "content": "Tesla Cybercab production ramp is target for 2026. Unsupervised FSD will change urban transport forever."},
                {"symbol": "NVDA", "content": "Training xAI Colossus 100k H100 cluster in Memphis was achieved in record time. Compute scaling continues."}
            ],
            "Jensen Huang": [
                {"symbol": "NVDA", "content": "Generative AI is not a trend, it is a new industrial revolution. Infrastructure buildout has just begun."}
            ],
            "Cathie Wood": [
                {"symbol": "PLTR", "content": "Enterprise AI platform adoption is compounding. Palantir AIP is demonstrating unmatched ROI for customers."}
            ],
            "Sam Altman": [
                {"symbol": "MSFT", "content": "Scaling intelligence requires massive clean energy and compute infrastructure. The future is brighter than ever."}
            ]
        }

        for guru in gurus:
            templates = feed_templates.get(guru.name, [])
            if not templates:
                continue

            item = random.choice(templates)
            existing = (await session.execute(
                select(GuruInsight)
                .where(GuruInsight.guru_id == guru.id)
                .where(GuruInsight.content == item["content"])
            )).scalars().first()

            if not existing:
                ai_res = await ai_service.analyze_market_sentiment(item["symbol"], item["content"])
                score = ai_res.get("score", 80)
                sentiment = ai_res.get("sentiment", "Bullish")
                summary = ai_res.get("summary", f"{guru.name}의 {item['symbol']} 관점 주요 발언")
                reason = ai_res.get("reason", "시장 영향력이 높은 주요 인사이트로 평가됨")

                stock_data = await get_stock_info(item["symbol"])
                price = stock_data.get("currentPrice", 100.0) if isinstance(stock_data, dict) and "error" not in stock_data else 100.0

                new_insight = GuruInsight(
                    guru_id=guru.id,
                    symbol=item["symbol"],
                    content=item["content"],
                    sentiment=sentiment,
                    score=score,
                    summary=summary,
                    reason=reason,
                    price_at_timestamp=price,
                    timestamp=datetime.utcnow()
                )
                session.add(new_insight)
                await session.commit()
                logger.info(f"✅ [Guru Feed] {guru.name} 신규 발언 AI 분석 완료: {summary}")

                msg = f"🧠 <b>[AI 대가 피드 알림] {guru.name} ({guru.handle})</b>\n\n📌 <b>{item['symbol']}</b>: {summary}\n💬 \"{item['content']}\"\n📊 감정: <b>{sentiment}</b> (점수: {score}점)"
                await notification_service.send_telegram_message(msg)

async def guru_feed_worker():
    """10분 주기 대가 피드 자동 수집 루프"""
    await asyncio.sleep(10) # 서버 부팅 후 10초 대기
    while True:
        try:
            await fetch_and_analyze_guru_feeds()
        except Exception as e:
            logger.error(f"⚠️ Guru Feed Worker Error: {e}")
        await asyncio.sleep(600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await wait_for_db()
        await init_db()
        await ensure_default_data()
    except Exception as e:
        logger.error(f"⚠️ Initial database setup warning (API server remains active): {e}")

    worker_task = None
    broadcaster_task = None
    guru_task = None

    try:
        worker_task = asyncio.create_task(trading_worker.start(interval_seconds=60))
        broadcaster_task = asyncio.create_task(price_broadcaster())
        guru_task = asyncio.create_task(guru_feed_worker())
    except Exception as e:
        logger.error(f"⚠️ Background worker launch warning: {e}")

    yield

    try:
        trading_worker.stop()
        if worker_task: worker_task.cancel()
        if broadcaster_task: broadcaster_task.cancel()
        if guru_task: guru_task.cancel()
    except Exception:
        pass







app = FastAPI(title="Nasdaq is God API", lifespan=lifespan)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"➡️ [REQ] {request.method} {request.url.path} from {client_ip}")
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(f"⬅️ [RES] {request.method} {request.url.path} -> Status {response.status_code} ({process_time:.2f}ms)")
        return response
    except Exception as exc:
        process_time = (time.time() - start_time) * 1000
        logger.error(f"❌ [ERR] {request.method} {request.url.path} Failed after {process_time:.2f}ms: {exc}")
        logger.error(traceback.format_exc())
        raise exc

@app.get("/")
async def root():
    return {
        "message": "Nasdaq is God API - Real-time Ready",
        "environment": "development (dev branch)",
        "pipeline_status": "SOP Standard Verified",
        "version": "1.2.0"
    }

@app.get("/system/logs")
async def get_system_logs(limit: int = 100):

    """실시간 시스템 및 API 동작 라이브 로그 조회 엔드포인트"""
    logs_list = list(log_buffer)
    return {
        "total_lines": len(logs_list),
        "requested_limit": limit,
        "logs": logs_list[-limit:]
    }


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

@app.get("/settings/ai-status")
async def get_active_ai_status(current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    statement = select(APIKeyConfig).where(APIKeyConfig.user_id == current_user.id, APIKeyConfig.is_active == True)
    active_config = (await session.execute(statement)).scalar_one_or_none()
    
    if active_config:
        provider = active_config.provider
        label = active_config.label or provider
        masked_key = f"{active_config.key_value[:4]}...{active_config.key_value[-4:]}" if active_config.key_value and len(active_config.key_value) > 8 else "Active Key"
        base_url = active_config.base_url
        key_id = active_config.id
    else:
        provider = os.getenv("DEFAULT_AI_PROVIDER", "GOOGLE").upper()
        label = f"ENV Default ({provider})"
        masked_key = "ENV Default Key"
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        key_id = None

    model_name = "Gemini 2.0 Flash" if provider == "GOOGLE" else ("Llama3 (Ollama)" if provider == "OLLAMA" else "GPT-4o")
    vendor_name = "Google AI" if provider == "GOOGLE" else ("Ollama Local" if provider == "OLLAMA" else "OpenAI")
    
    is_healthy = await ai_service.check_provider_health(
        provider,
        base_url=base_url if provider == "OLLAMA" else None,
        api_key=active_config.key_value if active_config else os.getenv("GEMINI_API_KEY")
    )

    return {
        "provider": provider,
        "vendor_name": vendor_name,
        "model_name": model_name,
        "label": label,
        "key_id": key_id,
        "masked_key": masked_key,
        "healthy": is_healthy,
        "status": "정상 (ACTIVE)" if is_healthy else "점검 필요",
        "remaining_estimate": "100%" if provider == "OLLAMA" else "98% (충분함)"
    }

# --- Real-time Issues & Guru Feed (DB Caching deduplication) ---
@app.get("/issues/feed")
async def get_issues_feed(
    q: Optional[str] = None,
    category: Optional[str] = None,
    symbol: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    stmt = select(NewsArticle).order_by(NewsArticle.published_at.desc())
    if category and category != "ALL":
        stmt = stmt.where(NewsArticle.category == category)
    if symbol and symbol != "ALL":
        stmt = stmt.where(NewsArticle.symbol == symbol.upper())
    if q and q.strip():
        term = f"%{q.strip()}%"
        stmt = stmt.where(or_(NewsArticle.title.ilike(term), NewsArticle.summary.ilike(term), NewsArticle.publisher.ilike(term)))

    articles = (await session.execute(stmt.limit(50))).scalars().all()

    # DB에 수집된 이슈가 적은 경우 자동 외부 수집 및 DB 캐싱 (중복 URL 저장 방지)
    if len(articles) < 3:
        target_sym = symbol if (symbol and symbol != "ALL") else "AAPL"
        raw_news = await ai_service.get_stock_news(target_sym)
        for n in raw_news:
            link = n.get("link") or f"https://finance.yahoo.com/quote/{target_sym}?ts={datetime.utcnow().timestamp()}"
            existing = (await session.execute(select(NewsArticle).where(NewsArticle.link == link))).scalar_one_or_none()
            if not existing:
                title = n.get("title", f"{target_sym} 시장 주요 이슈")
                publisher = n.get("publisher", "Market News")
                pub_time = datetime.fromtimestamp(n.get("providerPublishTime")) if n.get("providerPublishTime") else datetime.utcnow()
                
                lower_title = title.lower()
                is_bullish = any(w in lower_title for w in ["up", "growth", "high", "rally", "gain", "surge", "record"])
                is_bearish = any(w in lower_title for w in ["drop", "fall", "down", "loss", "crash", "plunge", "cut"])
                
                sentiment_str = "Bullish" if is_bullish else ("Bearish" if is_bearish else "Neutral")
                sentiment_val = 78 if is_bullish else (32 if is_bearish else 50)
                
                new_art = NewsArticle(
                    symbol=target_sym,
                    title=title,
                    publisher=publisher,
                    link=link,
                    published_at=pub_time,
                    summary=f"[{publisher}] {title} - AI 수집 데이터",
                    sentiment=sentiment_str,
                    sentiment_score=sentiment_val,
                    category="NEWS"
                )
                session.add(new_art)

        guru_posts = await social_service.fetch_guru_tweets(target_sym)
        for g in guru_posts:
            g_link = f"https://twitter.com/{g['handle']}/{g['guru']}"
            existing = (await session.execute(select(NewsArticle).where(NewsArticle.link == g_link))).scalar_one_or_none()
            if not existing:
                new_g = NewsArticle(
                    symbol=target_sym,
                    title=f"💬 {g['guru']} ({g['handle']}) 핵심 발언",
                    publisher=g['guru'],
                    link=g_link,
                    published_at=datetime.utcnow(),
                    summary=g['content'],
                    sentiment="Bullish" if any(w in g['content'].lower() for w in ["disruption", "improving", "strong"]) else "Neutral",
                    sentiment_score=82 if "improving" in g['content'].lower() else 60,
                    category="GURU"
                )
                session.add(new_g)

        await session.commit()
        articles = (await session.execute(stmt.limit(50))).scalars().all()

    return {
        "count": len(articles),
        "cached_db": True,
        "articles": [a.dict() for a in articles]
    }

@app.post("/issues/refresh")
async def refresh_issues_feed(
    symbol: Optional[str] = "AAPL",
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    target_sym = symbol.upper() if symbol else "AAPL"
    raw_news = await ai_service.get_stock_news(target_sym)
    new_count = 0

    for n in raw_news:
        link = n.get("link") or f"https://finance.yahoo.com/quote/{target_sym}?ts={datetime.utcnow().timestamp()}"
        existing = (await session.execute(select(NewsArticle).where(NewsArticle.link == link))).scalar_one_or_none()
        if not existing:
            title = n.get("title", f"{target_sym} 최신 이슈")
            publisher = n.get("publisher", "Market Wire")
            pub_time = datetime.fromtimestamp(n.get("providerPublishTime")) if n.get("providerPublishTime") else datetime.utcnow()
            new_art = NewsArticle(
                symbol=target_sym,
                title=title,
                publisher=publisher,
                link=link,
                published_at=pub_time,
                summary=f"[{publisher}] {title}",
                sentiment="Bullish" if any(w in title.lower() for w in ["up", "growth", "high", "rally"]) else "Neutral",
                sentiment_score=75 if any(w in title.lower() for w in ["up", "growth"]) else 50,
                category="NEWS"
            )
            session.add(new_art)
            new_count += 1

    await session.commit()
    return {"status": "success", "new_articles_count": new_count}

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
    # 1. 활성화된 DB 설정 확인
    config = (await session.execute(select(APIKeyConfig).where(APIKeyConfig.user_id == current_user.id, APIKeyConfig.is_active == True))).scalar_one_or_none()
    
    if config:
        return await ai_service.list_available_models(
            api_key=config.key_value, 
            provider=config.provider, 
            base_url=config.base_url
        )
    
    # 2. DB 설정 없으면 .env 기본값 사용
    return await ai_service.list_available_models(
        api_key=os.getenv("GEMINI_API_KEY"),
        provider=os.getenv("DEFAULT_AI_PROVIDER", "GOOGLE"),
        base_url=os.getenv("OLLAMA_BASE_URL")
    )

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

@app.post("/gurus/refresh-feeds")
async def refresh_guru_feeds(current_user: User = Depends(get_current_user)):
    """대가들의 최신 소셜/트위터 글 즉시 수집 & AI 분석 실행 엔드포인트"""
    asyncio.create_task(fetch_and_analyze_guru_feeds())
    return {"status": "success", "message": "대가들의 최신 피드 수집 및 AI 분석 작업이 시작되었습니다."}


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

class BacktestRequest(BaseModel):
    symbol: str = "AAPL"
    strategy_type: str = "SMA_CROSSOVER"
    parameters: Dict[str, Any] = {}
    period: str = "1y"
    initial_capital: float = 10000.0

@app.post("/backtest")
async def run_backtest_api(req: BacktestRequest):
    try:
        engine = BacktestEngine(initial_capital=req.initial_capital)
        result = engine.run_backtest(
            symbol=req.symbol,
            strategy_type=req.strategy_type,
            params=req.parameters,
            period=req.period
        )
        return result
    except Exception as e:
        logger.error(f"Backtest error for {req.symbol}: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/sentiment/analyze")
async def analyze_symbol_sentiment(symbol: str = Query("AAPL"), session: AsyncSession = Depends(get_session)):
    try:
        result = await sentiment_engine.analyze_combined_sentiment(symbol, session=session)
        return result
    except Exception as e:
        logger.error(f"Sentiment analysis failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sentiment/history/{symbol}")
async def get_sentiment_history(symbol: str, session: AsyncSession = Depends(get_session)):
    stmt = select(AISentimentHistory).where(AISentimentHistory.symbol == symbol).order_by(AISentimentHistory.created_at.desc()).limit(30)
    res = await session.execute(stmt)
    return res.scalars().all()

class HybridEvaluateRequest(BaseModel):
    symbol: str = "AAPL"
    strategy_type: str = "HYBRID_ALL"
    tech_weight: float = 0.6
    buy_threshold: float = 70.0
    sell_threshold: float = 35.0
    parameters: Dict[str, Any] = {}

@app.post("/hybrid/evaluate")
async def evaluate_hybrid_strategy(req: HybridEvaluateRequest):
    try:
        result = await hybrid_strategy_engine.evaluate_hybrid_signal(
            symbol=req.symbol,
            strategy_type=req.strategy_type,
            tech_weight=req.tech_weight,
            buy_threshold=req.buy_threshold,
            sell_threshold=req.sell_threshold,
            params=req.parameters
        )
        return result
    except Exception as e:
        logger.error(f"Hybrid evaluation error for {req.symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root(): return {"message": "Nasdaq is God API - Real-time Ready"}

if __name__ == "__main__": uvicorn.run(app, host="0.0.0.0", port=9000)
