"""
database.py

SQLAlchemy ORM models and synchronous helper functions used across handlers.
This file provides:
- User and PendingPayment models
- Session factory and Session alias
- Helper CRUD functions used by handlers (create_user, get_user_by_tg, create_pending_payment, update_pending_payment, get_latest_pending_by_user, activate_tariff, bonus helpers, etc.)

All session usage is safe (session closed in finally blocks).
"""
from pathlib import Path
from typing import Optional, Dict, Any
import datetime as dt

from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, func
)
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "bot.db"
ENGINE = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False)

Base = declarative_base()

REFERRAL_BONUS = 1000  # amount to credit to referrer (adjust as needed)


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
    referred_by = Column(Integer, nullable=True)  # referrer user.id
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


class UsefulFreeClaim(Base):
    __tablename__ = "useful_free_claims"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, unique=True)
    claimed = Column(Integer, default=1)  # 1 == claimed


class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    user_tg = Column(Integer, nullable=False)
    text = Column(String, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    answered_at = Column(DateTime, nullable=True)
    answer_snippet = Column(String, nullable=True)


# Create tables if they don't exist
Base.metadata.create_all(bind=ENGINE)

# Expose Session alias for code that expects `Session`
Session = SessionLocal


# --------------------
# Helper functions
# --------------------
def get_user_by_tg(tg_id: int) -> Optional[User]:
    session = SessionLocal()
    try:
        return session.query(User).filter(User.telegram_id == int(tg_id)).first()
    finally:
        session.close()


def create_question(user_tg: int, text: str) -> int:
    session = SessionLocal()
    try:
        q = Question(user_tg=int(user_tg), text=text)
        session.add(q)
        session.commit()
        session.refresh(q)
        return int(q.id)
    finally:
        session.close()


def get_question(qid: int) -> Optional[Dict[str, Any]]:
    session = SessionLocal()
    try:
        q = session.query(Question).filter(Question.id == int(qid)).first()
        if not q:
            return None
        return {
            "id": q.id,
            "user_tg": q.user_tg,
            "text": q.text,
            "created_at": q.created_at,
            "answered_at": q.answered_at,
            "answer_snippet": q.answer_snippet,
        }
    finally:
        session.close()


def mark_question_answered(qid: int, answer_snippet: str = None) -> None:
    session = SessionLocal()
    try:
        q = session.query(Question).filter(Question.id == int(qid)).first()
        if not q:
            return
        q.answered_at = dt.datetime.utcnow()
        if answer_snippet:
            q.answer_snippet = (answer_snippet[:240])
        session.add(q)
        session.commit()
    finally:
        session.close()


def get_user_by_phone(phone: str) -> Optional[User]:
    session = SessionLocal()
    try:
        return session.query(User).filter(User.phone == phone).first()
    finally:
        session.close()


def create_user(tg_id: int, full_name: str = None, phone: str = None, device_id: str = None, referred_by: int = None) -> User:
    """
    Create a new user if not exists. Returns existing user if present.
    If referred_by is set (telegram id of referrer), credit that referrer with referral bonus.
    """
    session = SessionLocal()
    try:
        existing = session.query(User).filter(User.telegram_id == int(tg_id)).first()
        if existing:
            return existing

        # New users: give them free access by default (pro-level quotas) per admin request
        now = dt.datetime.utcnow()
        future = now + dt.timedelta(days=3650)  # 10 years free access
        user = User(
            telegram_id=int(tg_id),
            full_name=full_name,
            phone=phone,
            tariff='pro',
            tariff_start=now,
            tariff_end=future,
            daily_remaining=999,
            weekly_remaining=9999,
            monthly_remaining=99999,
            referrals_added=0,
            referrals_registered=0,
            bonus_balance=0,
            referred_by=None,
            device_id=device_id,
            created_at=dt.datetime.utcnow()
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # Process referral if present (referred_by is expected to be referrer's telegram id)
        if referred_by:
            try:
                ref = session.query(User).filter(User.telegram_id == int(referred_by)).first()
                if ref:
                    ref.referrals_added = (ref.referrals_added or 0) + 1
                    ref.referrals_registered = (ref.referrals_registered or 0) + 1
                    ref.bonus_balance = (ref.bonus_balance or 0) + REFERRAL_BONUS
                    session.add(ref)
                    # link the new user's referred_by to ref.id (DB-level referential)
                    user.referred_by = ref.id
                    session.add(user)
                    session.commit()
            except Exception:
                # best-effort, don't break user creation
                session.rollback()
        return user
    finally:
        session.close()


def get_user_bonus(user_db_id: int) -> int:
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == int(user_db_id)).first()
        return int(user.bonus_balance or 0) if user else 0
    finally:
        session.close()


def set_user_bonus(user_db_id: int, amount: int) -> None:
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == int(user_db_id)).first()
        if not user:
            return
        user.bonus_balance = int(amount)
        session.add(user)
        session.commit()
    finally:
        session.close()


def process_referral(ref_code: str, new_user: User) -> None:
    """
    ref_code: expected to be referrer's telegram id (as string) or user id code.
    Credit the referrer with REFERRAL_BONUS and increment counters.
    Link new_user.referred_by to referrer.id
    """
    if not ref_code:
        return
    try:
        ref_tg = int(ref_code)
    except Exception:
        return
    session = SessionLocal()
    try:
        referrer = session.query(User).filter(User.telegram_id == ref_tg).first()
        if not referrer:
            return
        # increment stats
        referrer.referrals_added = (referrer.referrals_added or 0) + 1
        referrer.referrals_registered = (referrer.referrals_registered or 0) + 1
        referrer.bonus_balance = (referrer.bonus_balance or 0) + REFERRAL_BONUS
        # link new user
        target = session.query(User).filter(User.telegram_id == new_user.telegram_id).first()
        if target:
            target.referred_by = referrer.id
        session.add(referrer)
        session.add(target)
        session.commit()
    finally:
        session.close()


# PendingPayment helpers
def create_pending_payment(payload: Dict[str, Any]) -> int:
    session = SessionLocal()
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
    session = SessionLocal()
    try:
        pp = session.query(PendingPayment).filter(PendingPayment.id == int(pid)).first()
        if not pp:
            return None
        return {
            "id": pp.id,
            "user_tg": pp.user_tg,
            "tariff": pp.tariff,
            "plan": pp.plan,
            "label": pp.label,
            "base_price": pp.base_price,
            "bonus_applied": pp.bonus_applied,
            "payable": pp.payable,
            "status": pp.status,
            "created_at": pp.created_at,
            "receipt_file_id": pp.receipt_file_id,
            "payer_last4": pp.payer_last4,
            "approved_at": pp.approved_at,
            "declined_at": pp.declined_at
        }
    finally:
        session.close()


def update_pending_payment(pid: int, updates: Dict[str, Any]) -> None:
    session = SessionLocal()
    try:
        pp = session.query(PendingPayment).filter(PendingPayment.id == int(pid)).first()
        if not pp:
            return
        for k, v in updates.items():
            if hasattr(pp, k):
                setattr(pp, k, v)
        session.add(pp)
        session.commit()
    finally:
        session.close()


def get_latest_pending_by_user(tg_id: int) -> Optional[Dict[str, Any]]:
    """
    Return the latest pending/under_review/awaiting_receipt payment dict for a Telegram user.
    Returns None if not found.
    """
    session = SessionLocal()
    try:
        pp = session.query(PendingPayment).filter(
            PendingPayment.user_tg == int(tg_id),
            PendingPayment.status.in_(["under_review", "awaiting_receipt", "awaiting_payment"])
        ).order_by(PendingPayment.created_at.desc()).first()
        if not pp:
            return None
        return {
            "id": pp.id,
            "user_tg": pp.user_tg,
            "tariff": pp.tariff,
            "plan": pp.plan,
            "label": pp.label,
            "base_price": pp.base_price,
            "bonus_applied": pp.bonus_applied,
            "payable": pp.payable,
            "status": pp.status,
            "created_at": pp.created_at,
            "receipt_file_id": pp.receipt_file_id,
            "payer_last4": pp.payer_last4,
            "approved_at": pp.approved_at,
            "declined_at": pp.declined_at
        }
    finally:
        session.close()


def activate_tariff(user_db_id: int, tariff: str, days: int) -> None:
    """
    Activate a tariff for a user and set reasonable quotas/dates.
    This mirrors the business logic used by handlers.
    """
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == int(user_db_id)).first()
        if not user:
            return
        now = dt.datetime.utcnow()
        user.tariff = tariff
        user.tariff_start = now
        user.tariff_end = now + dt.timedelta(days=int(days))

        # Set remaining quotas based on tariff type
        if tariff == "free":
            user.daily_remaining = 0
            user.weekly_remaining = 2
            user.monthly_remaining = 2
        elif tariff == "pro":
            user.daily_remaining = 19
            user.weekly_remaining = 133
            user.monthly_remaining = 570
        elif tariff == "premium":
            user.daily_remaining = 49
            user.weekly_remaining = 343
            user.monthly_remaining = 1470
        elif tariff == "pregnancy":
            if int(days) == 30:
                user.daily_remaining = 20
                user.weekly_remaining = 140
                user.monthly_remaining = 599
            else:
                user.daily_remaining = 22
                user.weekly_remaining = 154
                user.monthly_remaining = 666
        elif tariff == "planning":
            user.daily_remaining = 149
            user.weekly_remaining = 1043
            user.monthly_remaining = 4470
        else:
            user.daily_remaining = max(0, int(days))
            user.weekly_remaining = max(0, int(days) // 7)
            user.monthly_remaining = max(0, int(days) // 30)

        session.add(user)
        session.commit()
    finally:
        session.close()


def update_last_active(user_id: int) -> None:
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == int(user_id)).first()
        if user:
            user.last_active = dt.datetime.utcnow()
            session.commit()
    finally:
        session.close()


# --------------------
# Admin / reporting helpers
# --------------------
def get_all_users():
    session = SessionLocal()
    try:
        return session.query(User).all()
    finally:
        session.close()


def get_useful_subscribers():
    """
    Return users who subscribed to useful tips. For now consider users with tariff not null
    or with a special flag in profile; as we don't have that flag, return all users.
    """
    session = SessionLocal()
    try:
        # Placeholder: return all users. Modify if you have a specific subscribers table.
        return session.query(User).all()
    finally:
        session.close()


def deactivate_expired_tariffs():
    """
    Find users with tariff_end in the past, clear their tariff and return list of affected users.
    """
    session = SessionLocal()
    try:
        now = dt.datetime.utcnow()
        expired = session.query(User).filter(User.tariff_end != None, User.tariff_end <= now).all()
        for u in expired:
            u.tariff = None
            u.tariff_start = None
            u.tariff_end = None
            u.daily_remaining = 0
            u.weekly_remaining = 0
            u.monthly_remaining = 0
            session.add(u)
        session.commit()
        return expired
    finally:
        session.close()


def get_report_data(start_date: dt.datetime, end_date: dt.datetime) -> Dict[str, Any]:
    """
    Build a simple report between start_date and end_date.
    Returns dict with keys: start, end, new_users, total_sum, tariff_sales, useful_sales
    Note: total_sum and tariff_sales computed from pending_payments approved in range.
    """
    session = SessionLocal()
    try:
        new_users = session.query(func.count(User.id)).filter(User.created_at >= start_date, User.created_at <= end_date).scalar() or 0

        # total_sum: sum of approved pending payments in the range
        total_sum = session.query(func.coalesce(func.sum(PendingPayment.payable), 0)).filter(
            PendingPayment.status == "approved",
            PendingPayment.approved_at != None,
            PendingPayment.approved_at >= start_date,
            PendingPayment.approved_at <= end_date,
        ).scalar() or 0

        # tariff sales breakdown by tariff and by plan (more detailed)
        rows = session.query(PendingPayment.tariff, PendingPayment.plan, func.count(PendingPayment.id)).filter(
            PendingPayment.status == "approved",
            PendingPayment.approved_at != None,
            PendingPayment.approved_at >= start_date,
            PendingPayment.approved_at <= end_date,
        ).group_by(PendingPayment.tariff, PendingPayment.plan).all()
        # Build nested dict: { tariff: { plan: count, ... }, ... }
        tariff_sales = {}
        for tariff, plan, cnt in rows:
            t = tariff or "unknown"
            tariff_sales.setdefault(t, {})
            tariff_sales[t][plan] = int(cnt)

        # useful_sales placeholder: count of users (replace with real data if available)
        useful_sales = {"subscribers": session.query(func.count(User.id)).scalar() or 0}

        # compute overall user counts: total, purchased (tariff != None), not purchased
        total_users = session.query(func.count(User.id)).scalar() or 0
        purchased = session.query(func.count(User.id)).filter(User.tariff != None).scalar() or 0
        not_purchased = int(total_users) - int(purchased)

        return {
            "start": start_date,
            "end": end_date,
            "new_users": int(new_users),
            "total_sum": int(total_sum),
            "tariff_sales": tariff_sales,
            "useful_sales": useful_sales,
            "total_users": int(total_users),
            "purchased": int(purchased),
            "not_purchased": int(not_purchased),
        }
    finally:
        session.close()


def get_top_referrer():
    """Return the user who referred the most registered users."""
    session = SessionLocal()
    try:
        row = session.query(User, func.count(User.id).label("cnt")).filter(User.referred_by != None).join(User, User.id == User.referred_by)
        # Fallback: compute by scanning users
        # Simple approach: count referrals by referred_by id
        referral_counts = {}
        users = session.query(User).all()
        for u in users:
            if u.referred_by:
                referral_counts[u.referred_by] = referral_counts.get(u.referred_by, 0) + 1
        if not referral_counts:
            return None
        top_id = max(referral_counts, key=referral_counts.get)
        ref = session.query(User).filter(User.id == top_id).first()
        return {"id": ref.id, "name": ref.full_name, "phone": ref.phone, "count": referral_counts[top_id]} if ref else None
    finally:
        session.close()


def get_referral_counts(user_db_id: int) -> Dict[str, int]:
    """Return referrals_added and referrals_registered for a user id."""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == int(user_db_id)).first()
        if not user:
            return {"added": 0, "registered": 0}
        return {"added": int(user.referrals_added or 0), "registered": int(user.referrals_registered or 0)}
    finally:
        session.close()


def has_claimed_free_useful(user_db_id: int) -> bool:
    session = SessionLocal()
    try:
        row = session.query(UsefulFreeClaim).filter(UsefulFreeClaim.user_id == int(user_db_id)).first()
        return bool(row)
    finally:
        session.close()


def mark_claimed_free_useful(user_db_id: int) -> None:
    session = SessionLocal()
    try:
        existing = session.query(UsefulFreeClaim).filter(UsefulFreeClaim.user_id == int(user_db_id)).first()
        if existing:
            return
        row = UsefulFreeClaim(user_id=int(user_db_id), claimed=1)
        session.add(row)
        session.commit()
    finally:
        session.close()
