from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from core.stock_service import get_stock_info, find_ticker
from core.database import init_db, get_session
from core.models import User, UserCreate, UserRead, Token
from core.auth import get_password_hash, verify_password, create_access_token, decode_access_token
from core.trade_service import TradeService
from core.mock_broker import MockBroker
from core.kis_broker import KISBroker
from core.indicator_service import IndicatorService
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from contextlib import asynccontextmanager
import uvicorn
import os
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_server")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시 실행
    logger.info("Initializing database...")
    await init_db()
    yield
    # 서버 종료 시 실행 (필요 시 추가)

app = FastAPI(title="Nasdaq is God API", lifespan=lifespan)

# 브로커 선택
USE_REAL_BROKER = os.getenv("USE_REAL_BROKER", "false").lower() == "true"
broker = KISBroker() if USE_REAL_BROKER else MockBroker()
trade_service = TradeService(broker)
indicator_service = IndicatorService()

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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username: str = payload.get("sub")
    statement = select(User).where(User.username == username)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"--- Login attempt: {form_data.username} ---")
    statement = select(User).where(User.username == form_data.username)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Login failed for: {form_data.username}")
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    logger.info(f"Login successful: {form_data.username}")
    return {"access_token": create_access_token(data={"sub": user.username}), "token_type": "bearer"}

@app.post("/signup", response_model=UserRead)
async def signup(user_data: UserCreate, session: AsyncSession = Depends(get_session)):
    statement = select(User).where(User.username == user_data.username)
    result = await session.execute(statement)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user_data.password)
    db_user = User(username=user_data.username, email=user_data.email, hashed_password=hashed_password)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user

@app.get("/users/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/stock/{symbol}/indicators")
async def get_stock_indicators(symbol: str):
    return await indicator_service.get_indicators(symbol)

@app.get("/portfolio")
async def get_portfolio(
    current_user: User = Depends(get_current_user), 
    session: AsyncSession = Depends(get_session)
):
    return await trade_service.get_user_portfolio(session, current_user)

@app.get("/")
async def root():
    return {"message": "API Running on Port 9000"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)