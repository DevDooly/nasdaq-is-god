from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship
import json

class UserBase(SQLModel):
    username: str = Field(index=True, unique=True)
    email: Optional[str] = None
    # 💡 기본 잔고 추가 (기본값 $100,000)
    cash_balance: float = Field(default=100000.0)

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    assets: List["StockAsset"] = Relationship(back_populates="user")
    trades: List["TradeLog"] = Relationship(back_populates="user")
    strategies: List["TradingStrategy"] = Relationship(back_populates="user")

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    created_at: datetime

class Token(SQLModel):
    access_token: str
    token_type: str

class StockAsset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    symbol: str = Field(index=True)
    quantity: float
    average_price: float
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: User = Relationship(back_populates="assets")

class TradeLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    symbol: str = Field(index=True)
    side: str
    quantity: float
    price: float
    total_amount: float
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: User = Relationship(back_populates="trades")

class TradingStrategyBase(SQLModel):
    name: str
    symbol: str
    is_active: bool = Field(default=False)
    strategy_type: str
    parameters: str = Field(default="{}")

class TradingStrategy(TradingStrategyBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="strategies")

class StrategyCreate(TradingStrategyBase):
    pass

class StrategyRead(TradingStrategyBase):
    id: int
    user_id: int
    created_at: datetime
