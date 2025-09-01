from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Text

router = Router()

@router.message(F.text)
async def handle_question(message: types.Message, state: FSMContext):
    # process the text
    await message.reply("Thanks for your question: " + message.text)