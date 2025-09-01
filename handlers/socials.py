from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from loader import bot, answer_with_sticker
from config import STICKER_SOCIALS, ADMIN_ID
from keyboards.inline.social_links import social_links_kb
from database import get_user_by_tg, get_user_bonus, set_user_bonus

router = Router()

BONUS_SOCIALS = 29000


@router.message(F.text == "Mirsaid BAKUMOVning ijtimoiy tarmoqlari")
async def socials_info(message: Message):
    text = (
        "🌐 Mirsaid BAKUMOVning ijtimoiy tarmoqlari:\n\n"
        "📢 Telegram kanal\n"
        "👥 Telegram guruh\n"
        "📷 Instagram sahifasi\n"
        "▶️ YouTube kanali\n\n"
        "⬇ Havolalardan barchasiga a'zo bo‘ling va 'Tekshirish' tugmasini bosing. "
        f"Agar hammasiga a'zo bo‘lsangiz, {BONUS_SOCIALS:,} so‘m bonus olasiz."
    )
    await answer_with_sticker(message, text, sticker_file_id=STICKER_SOCIALS, reply_markup=social_links_kb())


@router.callback_query(F.data == "check_socials")
async def check_socials(callback: CallbackQuery):
    user = get_user_by_tg(callback.from_user.id)
    if not user:
        await answer_with_sticker(callback.message, "❗ Iltimos, avval ro'yxatdan o'ting.", sticker_file_id=STICKER_SOCIALS)
        await callback.answer()
        return

    # Verify membership in required channels/groups
    joined_all = False
    try:
        channel_member = await bot.get_chat_member(chat_id="@MirsaidKanal", user_id=callback.from_user.id)
        group_member = await bot.get_chat_member(chat_id="@MirsaidGuruh", user_id=callback.from_user.id)
        if channel_member.status not in ("left", "kicked") and group_member.status not in ("left", "kicked"):
            joined_all = True
    except Exception:
        joined_all = False

    if joined_all:
        try:
            curr = get_user_bonus(user.id)
            set_user_bonus(user.id, curr + BONUS_SOCIALS)
        except Exception:
            pass
        await answer_with_sticker(callback.message, f"🎉 Tabriklaymiz! Siz barcha sahifalarga a'zo bo'ldingiz.\n{BONUS_SOCIALS:,} so'm bonus qo'shildi.", sticker_file_id=STICKER_SOCIALS)
    else:
        await answer_with_sticker(callback.message, "❌ Siz barcha sahifalarga a'zo emassiz. Tekshirib, qayta urinib ko'ring.", sticker_file_id=STICKER_SOCIALS)

    await callback.answer()
