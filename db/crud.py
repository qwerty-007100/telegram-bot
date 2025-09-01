from typing import Optional, Dict, Any
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import datetime as dt
from .models import Base, User, PendingPayment
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bot.db"
ENGINE = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False)
Base.metadata.create_all(bind=ENGINE)

REFERRAL_BONUS = 1000

def get_session():
    return SessionLocal()

def get_user_by_tg(tg_id: int) -> Optional[User]:
    session = get_session()
    try:
        return session.query(User).filter(User.telegram_id == int(tg_id)).first()
    finally:
        session.close()

def get_user_by_phone(phone: str) -> Optional[User]:
    session = get_session()
    try:
        return session.query(User).filter(User.phone == phone).first()
    finally:
        session.close()

def create_user(tg_id: int, full_name: str = None, phone: str = None, device_id: str = None, referred_by: int = None) -> User:
    session = get_session()
    try:
        existing = session.query(User).filter(User.telegram_id == int(tg_id)).first()
        if existing:
            return existing
        user = User(telegram_id=int(tg_id), full_name=full_name, phone=phone, device_id=device_id, created_at=dt.datetime.utcnow())
        session.add(user)
        session.commit()
        session.refresh(user)
        if referred_by:
            ref = session.query(User).filter(User.telegram_id == int(referred_by)).first()
            if ref:
                ref.referrals_added = (ref.referrals_added or 0) + 1
                ref.referrals_registered = (ref.referrals_registered or 0) + 1
                ref.bonus_balance = (ref.bonus_balance or 0) + REFERRAL_BONUS
                user.referred_by = ref.id
                session.commit()
        return user
    finally:
        session.close()

def create_pending_payment(payload: Dict[str, Any]) -> int:
    session = get_session()
    try:
        pp = PendingPayment(
            user_tg=int(payload["user_tg"]),
            tariff=payload["tariff"],
            plan=payload["plan"],
            label=payload.get("label"),
            base_price=int(payload.get("base_price", 0)),
            bonus_applied=int(payload.get("bonus_applied", 0)),
            payable=int(payload.get("payable", 0)),
            status=payload.get("status", "awaiting_receipt"),
            created_at=payload.get("created_at", dt.datetime.utcnow()),
            receipt_file_id=payload.get("receipt_file_id"),
            payer_last4=payload.get("payer_last4")
        )
        session.add(pp)
        session.commit()
        session.refresh(pp)
        return int(pp.id)
    finally:
        session.close()

def get_pending_payment(pid: int) -> Optional[Dict[str, Any]]:
    session = get_session()
    try:
        pp = session.query(PendingPayment).filter(PendingPayment.id == int(pid)).first()
        if not pp:
            return None
        return {
            "id": pp.id, "user_tg": pp.user_tg, "tariff": pp.tariff, "plan": pp.plan,
            "label": pp.label, "base_price": pp.base_price, "bonus_applied": pp.bonus_applied,
            "payable": pp.payable, "status": pp.status, "created_at": pp.created_at,
            "receipt_file_id": pp.receipt_file_id, "payer_last4": pp.payer_last4,
            "approved_at": pp.approved_at, "declined_at": pp.declined_at
        }
    finally:
        session.close()

def update_pending_payment(pid: int, updates: Dict[str, Any]) -> None:
    session = get_session()
    try:
        pp = session.query(PendingPayment).filter(PendingPayment.id == int(pid)).first()
        if not pp:
            return
        for k, v in updates.items():
            if hasattr(pp, k):
                setattr(pp, k, v)
        session.commit()
    finally:
        session.close()

def get_latest_pending_by_user(tg_id: int) -> Optional[Dict[str, Any]]:
    session = get_session()
    try:
        pp = session.query(PendingPayment).filter(
            PendingPayment.user_tg == int(tg_id),
            PendingPayment.status.in_(["under_review", "awaiting_receipt", "awaiting_payment"])
        ).order_by(PendingPayment.created_at.desc()).first()
        if not pp:
            return None
        return get_pending_payment(pp.id)
    finally:
        session.close()

def activate_tariff(user_db_id: int, tariff: str, days: int) -> None:
    session = get_session()
    try:
        user = session.query(User).filter(User.id == int(user_db_id)).first()
        if not user:
            return
        now = dt.datetime.utcnow()
        user.tariff = tariff
        user.tariff_start = now
        user.tariff_end = now + dt.timedelta(days=int(days))
        # quotas (same as business logic)
        if tariff == "free":
            user.daily_remaining = 0; user.weekly_remaining = 2; user.monthly_remaining = 8
        elif tariff == "pro":
            user.daily_remaining = 19; user.weekly_remaining = 133; user.monthly_remaining = 570
        elif tariff == "premium":
            user.daily_remaining = 49; user.weekly_remaining = 343; user.monthly_remaining = 1470
        elif tariff == "pregnancy":
            if int(days) == 30:
                user.daily_remaining = 20; user.weekly_remaining = 140; user.monthly_remaining = 599
            else:
                user.daily_remaining = 22; user.weekly_remaining = 154; user.monthly_remaining = 666
        elif tariff == "planning":
            user.daily_remaining = 149; user.weekly_remaining = 1043; user.monthly_remaining = 4470
        session.commit()
    finally:
        session.close()
