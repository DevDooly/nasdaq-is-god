import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from dotenv import load_dotenv

load_dotenv()

# 환경변수에서 DB URL 가져오기 (기본값은 docker-compose 설정과 맞춤)
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:password@localhost:5432/nasdaq_god"
)

engine = create_async_engine(DATABASE_URL, echo=True, future=True)

async def init_db():
    async with engine.begin() as conn:
        # RESET_DB=true 인 경우 기존 모든 테이블을 삭제 후 새로 생성
        if os.getenv("RESET_DB", "false").lower() == "true":
            print("⚠️ RESET_DB가 true로 설정되어 기존 모든 DB 테이블을 삭제하고 초기화합니다...")
            await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncSession:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
