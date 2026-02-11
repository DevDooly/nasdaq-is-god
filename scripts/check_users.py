import asyncio
from sqlmodel import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from core.models import User
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/nasdaq_god")

async def list_users():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        statement = select(User)
        result = await session.execute(statement)
        users = result.scalars().all()
        print(f"Total users found: {len(users)}")
        for user in users:
            print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(list_users())