# daily_report.py
import asyncio
from datetime import datetime, timedelta
from config import ADMIN_ID
from loader import bot  # loader.py ichida bot va dp bo‘lishi kerak
from scheduler import get_report_data  # get_report_data shu faylda bo‘lsa

async def send_report():
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=1)

    report = await get_report_data(start_date, end_date)

    text = (
        f"📊 Kunlik hisobot\n"
        f"📅 {start_date.strftime('%Y-%m-%d')} — {end_date.strftime('%Y-%m-%d')}\n"
        f"👥 Yangi foydalanuvchilar: {report['new_users']}\n"
        f"💰 Umumiy daromad: {report['total_sum']:,} so'm"
    )
    await bot.send_message(ADMIN_ID, text)

async def start_scheduler():
    while True:
        await send_report()
        await asyncio.sleep(24 * 60 * 60)  # Har 24 soatda
