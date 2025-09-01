from aiogram import Router, F
from aiogram.types import Message
from loader import bot
from database import Session, User, PendingPayment
from config import ADMIN_ID
from sqlalchemy import func
from datetime import datetime, timedelta

router = Router()

@router.message(F.text == "/dashboard")
async def admin_dashboard(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Siz admin emassiz!")
        return

    session = Session()
    try:
        # Active users in the last 15 minutes
        active_users = session.query(func.count(User.id)).filter(
            User.last_active >= datetime.utcnow() - timedelta(minutes=15)
        ).scalar()

        # Active subscriptions
        active_subscriptions = session.query(
            User.tariff, func.count(User.id)
        ).filter(User.tariff.isnot(None)).group_by(User.tariff).all()

        # Daily questions and answers
        daily_questions = session.query(func.count(PendingPayment.id)).filter(
            PendingPayment.created_at >= datetime.utcnow().date()
        ).scalar()

        # Build dashboard text
        text = (
            "📊 *Real-Time Dashboard*\n\n"
            f"👥 *Active Users*: {active_users}\n\n"
            "📦 *Active Subscriptions:*\n"
        )
        for tariff, count in active_subscriptions:
            text += f"  - {tariff}: {count}\n"

        text += f"\n💬 *Daily Questions*: {daily_questions}\n"

        await message.answer(text, parse_mode="Markdown")
    finally:
        session.close()
