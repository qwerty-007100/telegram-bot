from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

router = Router()

@router.message(F.text & ~F.command)
async def reply_text(message: types.Message, state: FSMContext):
    await message.reply("Received: " + message.text)