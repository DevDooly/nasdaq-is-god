import asyncio
from sqlmodel import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from core.models import User
from core.auth import get_password_hash
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/nasdaq_god")

async def reset_password(username, new_password):
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        statement = select(User).where(User.username == username)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        
        if user:
            user.hashed_password = get_password_hash(new_password)
            session.add(user)
            await session.commit()
            print(f"Successfully reset password for user: {username} to {new_password}")
        else:
            print(f"User {username} not found.")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(reset_password("admin", "admin123"))
