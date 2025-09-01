from aiogram import Router, types
from keyboards import main_menu_keyboard
from loader import answer_with_sticker
from config import STICKER_WELCOME, STICKER_TARIFF, ADMIN_ID

router = Router()


from aiogram.fsm.context import FSMContext


@router.message(lambda m: m.text in ["Admin bilan bog'lanish", "Admin bilan bog‘lanish", "📞 Admin bilan bog‘lanish"])
async def admin_contact(message: types.Message, state: FSMContext | None = None):
    if state is not None:
        try:
            await state.clear()
        except Exception:
            pass

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Adminga yozish (@homilayordami)", url="https://t.me/homilayordami")],
    # show phone via callback
    [InlineKeyboardButton(text="Telefon: +998 94 5623111", callback_data="admin_phone")],
    ])

    text = "📞 Admin bilan bog'lanish uchun quyidagi tugmalardan foydalaning:"
    sticker = STICKER_TARIFF or STICKER_WELCOME
    await answer_with_sticker(
        message,
        text,
        sticker_file_id=sticker,
        reply_markup=kb
    )


@router.callback_query(lambda c: c.data == "admin_phone")
async def _admin_phone_callback(callback: types.CallbackQuery):
    """Show admin phone number via alert to avoid using tel: URL (which Telegram blocks)."""
    phone = "+998 94 5623111"
    # show_alert=True will display the phone number in a popup to the user
    try:
        await callback.answer(text=f"Telefon: {phone}", show_alert=True)
    except Exception:
        # fallback: send plain message if alert fails
        await callback.message.answer(f"Telefon: {phone}")
