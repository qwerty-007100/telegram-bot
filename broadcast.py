from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from db import async_session  # Assuming async_session is a sessionmaker configured elsewhere and imported here

async def send_broadcast(bot: Bot, text: str):
    async with async_session() as session:  # noqa: N806
        async with session.begin():
            # Retrieve recipients, then send messages
            recipients = await get_recipients(session)  
    for user_id in recipients:
        await bot.send_message(user_id, text)