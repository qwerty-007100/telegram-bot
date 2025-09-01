"""
Async DB module (SQLAlchemy + aiosqlite by default).

Provides:
- engine, async_session
- Base, User, PendingPayment ORM models
- init_db() to create tables
- get_session() async generator helper
"""

import os
from datetime import datetime
from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot.db")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    bonus_balance = Column(Integer, default=0)
    current_tariff = Column(String, nullable=True)
    tariff_started_at = Column(DateTime, nullable=True)
    tariff_ends_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PendingPayment(Base):
    __tablename__ = "pending_payments"
    id = Column(Integer, primary_key=True)
    user_tg = Column(Integer, nullable=False)
    tariff = Column(String, nullable=True)
    plan = Column(String, nullable=True)
    label = Column(String, nullable=True)
    base_price = Column(Integer, default=0)
    bonus_applied = Column(Integer, default=0)
    payable = Column(Integer, default=0)
    status = Column(String, default="pending")
    receipt_file_id = Column(String, nullable=True)
    payer_last4 = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    declined_at = Column(DateTime, nullable=True)


async def init_db():
    """Create database tables (async)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session():
    """Async generator to yield an AsyncSession instance."""
    async with async_session() as session:
        yield session
