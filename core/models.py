from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship
import json

class UserBase(SQLModel):
    username: str = Field(index=True, unique=True)
    email: Optional[str] = None
    cash_balance: float = Field(default=100000.0)
    is_auto_trading_enabled: bool = Field(default=True)

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    assets: List["StockAsset"] = Relationship(back_populates="user")
    trades: List["TradeLog"] = Relationship(back_populates="user")
    strategies: List["TradingStrategy"] = Relationship(back_populates="user")
    equity_history: List["EquitySnapshot"] = Relationship(back_populates="user")
    ai_histories: List["AISentimentHistory"] = Relationship(back_populates="user")
    api_keys: List["APIKeyConfig"] = Relationship(back_populates="user")

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

class EquitySnapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    total_equity: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="equity_history")

class AISentimentHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    symbol: str = Field(index=True)
    score: int
    sentiment: str
    summary: str
    reason: str
    sources: str
    model_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="ai_histories")

class Guru(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    handle: str = Field(unique=True) # 예: @elonmusk
    description: Optional[str] = None
    influence_score: int = Field(default=50) # 중요도 (1~100)
    target_symbols: str = Field(default="") # 관련 종목 (예: "TSLA,NVDA")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GuruInsight(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    guru_id: int = Field(foreign_key="guru.id", index=True)
    symbol: Optional[str] = Field(default=None, index=True)
    content: str # 발언 원문
    sentiment: str # Bullish, Bearish, Neutral
    score: int # 0-100
    summary: str
    reason: str
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    source_url: Optional[str] = None

# 💡 API 키 관리 테이블
class APIKeyConfig(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    provider: str = Field(default="Gemini")
    label: str
    key_value: str # 실제 API 키 (저장 시 마스킹 또는 암호화 고려)
    is_active: bool = Field(default=False)
    usage_count: int = Field(default=0)
    last_used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="api_keys")

class StrategyCreate(TradingStrategyBase):
    pass

class StrategyRead(TradingStrategyBase):
    id: int
    user_id: int
    created_at: datetime
