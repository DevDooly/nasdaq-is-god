import asyncio
import os
import sys

# 프로젝트 경로 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import engine
from sqlmodel import SQLModel

async def reset_database():
    print("🔄 [Nasdaq is God] 데이터베이스 초기화를 진행합니다...")
    async with engine.begin() as conn:
        print("🗑️ 기존 데이터베이스 테이블을 모두 삭제 중...")
        await conn.run_sync(SQLModel.metadata.drop_all)
        print("✨ 새 데이터베이스 테이블을 생성 중...")
        await conn.run_sync(SQLModel.metadata.create_all)
    print("✅ 데이터베이스가 성공적으로 처음부터 새로 초기화되었습니다!")

if __name__ == "__main__":
    asyncio.run(reset_database())
