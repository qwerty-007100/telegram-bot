from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
import datetime as dt

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    tariff = Column(String, nullable=True)
    tariff_start = Column(DateTime, nullable=True)
    tariff_end = Column(DateTime, nullable=True)
    daily_remaining = Column(Integer, default=0)
    weekly_remaining = Column(Integer, default=0)
    monthly_remaining = Column(Integer, default=0)
    referrals_added = Column(Integer, default=0)
    referrals_registered = Column(Integer, default=0)
    bonus_balance = Column(Integer, default=0)
    referred_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    device_id = Column(String, nullable=True)
    last_active = Column(DateTime, default=dt.datetime.utcnow)

class PendingPayment(Base):
    __tablename__ = "pending_payments"
    id = Column(Integer, primary_key=True, index=True)
    user_tg = Column(Integer, nullable=False)
    tariff = Column(String, nullable=False)
    plan = Column(String, nullable=False)
    label = Column(String, nullable=True)
    base_price = Column(Integer, nullable=False)
    bonus_applied = Column(Integer, default=0)
    payable = Column(Integer, nullable=False)
    status = Column(String, default="awaiting_receipt")
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    receipt_file_id = Column(String, nullable=True)
    payer_last4 = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    declined_at = Column(DateTime, nullable=True)
