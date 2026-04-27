from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, Integer, Float, DateTime, Boolean, Text, BigInteger, select
from datetime import datetime
from typing import Optional
import json

from config import config

engine = create_async_engine(config.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()

# Модели данных
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(100))
    first_name: Mapped[str] = mapped_column(String(100))
    stars_balance: Mapped[float] = mapped_column(Float, default=0)
    crypto_wallet: Mapped[Optional[str]] = mapped_column(String(255))
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    total_trades: Mapped[int] = mapped_column(Integer, default=0)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)

class GiftListing(Base):
    __tablename__ = "gift_listings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    seller_id: Mapped[int] = mapped_column(BigInteger)
    gift_name: Mapped[str] = mapped_column(String(200))
    gift_year: Mapped[int] = mapped_column(Integer)
    gift_rarity: Mapped[str] = mapped_column(String(50))  # common, rare, epic, legendary
    price_stars: Mapped[float] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    verification_code: Mapped[Optional[str]] = mapped_column(String(100))  # код подтверждения подарка

class Transaction(Base):
    __tablename__ = "transactions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    type: Mapped[str] = mapped_column(String(50))  # buy_stars, sell_stars, buy_gift, sell_gift
    amount_stars: Mapped[float] = mapped_column(Float, default=0)
    amount_crypto: Mapped[float] = mapped_column(Float, default=0)
    fee: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    tx_hash: Mapped[Optional[str]] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class EscrowTrade(Base):
    __tablename__ = "escrow_trades"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trade_id: Mapped[str] = mapped_column(String(50), unique=True)
    seller_id: Mapped[int] = mapped_column(BigInteger)
    buyer_id: Mapped[int] = mapped_column(BigInteger)
    gift_id: Mapped[int] = mapped_column(Integer)
    amount: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, locked, completed, disputed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        return session

# CRUD операции
class UserDB:
    @staticmethod
    async def get(session: AsyncSession, user_id: int) -> Optional[User]:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_or_update(session: AsyncSession, user_id: int, username: str = None, first_name: str = None) -> User:
        user = await UserDB.get(session, user_id)
        if not user:
            user = User(id=user_id, username=username, first_name=first_name or str(user_id))
            session.add(user)
            await session.commit()
        return user
    
    @staticmethod
    async def update_balance(session: AsyncSession, user_id: int, delta: float) -> User:
        user = await UserDB.get(session, user_id)
        if user:
            user.stars_balance += delta
            await session.commit()
        return user