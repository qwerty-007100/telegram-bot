from aiogram import Router, F
from loader import bot, answer_with_sticker
from keyboards import get_menu_for
from config import STICKER_TARIFF

router = Router()

@router.message(lambda m: m.text in ["➕ Botga odam qo‘shish", "Botga odam qo‘shish"])
async def invite_friend(message):
    user_id = message.from_user.id
    try:
        me = await bot.get_me()
        username = me.username
    except:
        username = None

    if username:
        ref_link = f"https://t.me/{username}?start={user_id}"
    else:
        ref_link = f"https://t.me/{user_id}"

    text = (
        "📢 Do‘stlaringizni botga taklif qiling va har bir ro‘yxatdan o‘tgan odam uchun 1000 so‘m bonus oling!\n\n"
        f"🔗 Sizning referal havolangiz:\n{ref_link}\n\n"
        "Do‘stlaringiz ushbu havola orqali botga kirishi kerak."
    )

    await answer_with_sticker(
        message,
        text,
        sticker_file_id=STICKER_TARIFF,
        reply_markup=get_menu_for(message.from_user.id)
    )
