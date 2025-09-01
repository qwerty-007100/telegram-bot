# scheduler.py
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot
import aioschedule
from config import ADMIN_ID
from database import get_report_data
from loader import bot
from handlers.admin.panel import send_10_day_report, send_monthly_report, manage_expired_subscriptions

async def send_report(bot: Bot, admin_id: int):
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=1)
    report = get_report_data(start_date, end_date)

    text = (
        f"📊 Kunlik hisobot\n"
        f"⏱ {report['start'].strftime('%Y-%m-%d %H:%M')} — {report['end'].strftime('%Y-%m-%d %H:%M')}\n"
        f"👥 Yangi foydalanuvchilar: {report['new_users']}\n"
        f"💰 Yig'ilgan summa: {report['total_sum']:,} so'm"
    )
    await bot.send_message(admin_id, text)

def scheduler_job():
    """Synchronous wrapper scheduled by aioschedule.

    It creates asyncio tasks for the real async jobs instead of returning
    coroutines. This prevents aioschedule from passing raw coroutines to
    asyncio.wait (which raises TypeError on recent Python versions).
    """
    today = datetime.utcnow()
    # schedule async jobs as tasks so aioschedule.run_pending() doesn't
    # collect raw coroutine objects
    loop = asyncio.get_event_loop()
    if today.day in [10, 20, 30]:
        loop.create_task(send_10_day_report())
    if today.day == 1:
        loop.create_task(send_monthly_report())
    loop.create_task(manage_expired_subscriptions())

async def start_scheduler(bot: Bot):
    # schedule an explicit Task-returning lambda so aioschedule receives Tasks
    loop = asyncio.get_event_loop()

    async def _wrapper():
        # execute scheduler_job synchronously behaviour inside a coroutine
        try:
            # reuse existing helper to spawn tasks for daily jobs
            scheduler_job()
        except Exception as e:
            # surface exceptions
            import logging
            logging.getLogger(__name__).exception("scheduler wrapper failed: %s", e)

    # register a callable that returns a Task (not a coroutine) to avoid
    # 'Passing coroutines is forbidden' TypeError in asyncio.wait
    aioschedule.every().day.at("23:59").do(lambda: loop.create_task(_wrapper()))

    while True:
        # aioschedule.run_pending will now receive Tasks from our lambda
        await aioschedule.run_pending()
        await asyncio.sleep(1)
