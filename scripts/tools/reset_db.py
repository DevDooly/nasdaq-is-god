import asyncio
import os
import sys

# 프로젝트 경로 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import engine
from main_api import ensure_default_user, ensure_default_gurus
from sqlmodel import SQLModel

async def reset_database():
    print("🔄 [Nasdaq is God] 데이터베이스 초기화를 진행합니다...")
    async with engine.begin() as conn:
        print("🗑️ 기존 데이터베이스 테이블을 모두 삭제 중...")
        await conn.run_sync(SQLModel.metadata.drop_all)
        print("✨ 새 데이터베이스 테이블을 생성 중...")
        await conn.run_sync(SQLModel.metadata.create_all)
    
    print("🔐 기본 계정(admin) 및 AI 대가 분석(Guru) 임시데이터 시딩 중...")
    await ensure_default_user()
    await ensure_default_gurus()
    print("✅ 데이터베이스 및 테스트 데이터 시딩이 처음부터 성공적으로 완료되었습니다!")

if __name__ == "__main__":
    asyncio.run(reset_database())
