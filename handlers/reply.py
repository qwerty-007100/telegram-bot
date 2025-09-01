from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from keyboards import get_menu_for
from loader import answer_with_sticker
from config import STICKER_WELCOME

router = Router()

# Return to main menu when user presses the reply keyboard "Bosh menuga qaytish"
@router.message(F.text == "Bosh menuga qaytish")
async def back_to_main(message: types.Message, state: FSMContext):
    # clear any FSM state and show main menu
    try:
        await state.clear()
    except Exception:
        pass
    await answer_with_sticker(message, "Bosh menyu", sticker_file_id=STICKER_WELCOME, reply_markup=get_menu_for(message.from_user.id))


# Note: Removed broad fallback to avoid capturing menu/button presses.
