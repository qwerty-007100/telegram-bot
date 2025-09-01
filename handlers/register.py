from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from database import Session, User, get_user_by_tg, get_user_by_phone
from keyboards import start_keyboard, get_menu_for
from loader import answer_with_sticker, bot
from config import STICKER_WELCOME, ADMIN_ID
from aiogram.filters.command import Command
import hashlib

router = Router()


class RegisterForm(StatesGroup):
    full_name = State()
    birth_year = State()
    phone = State()
    address = State()


def hash_device_id(device_id: str) -> str:
    """Hash the device ID for privacy."""
    return hashlib.sha256(device_id.encode()).hexdigest()


# /start handler
@router.message(Command("start"))
async def start_command(message: Message):
    user = get_user_by_tg(message.from_user.id)
    if user:
        await answer_with_sticker(message, "Siz allaqal ro'yxatdan o'tgansiz!", sticker_file_id=STICKER_WELCOME, reply_markup=get_menu_for(message.from_user.id))
    else:
        await message.answer(
            "Assalomu alaykum! Ro'yxatdan o'tishingiz kerak. "
            "Boshlash uchun pastdagi tugmani bosing.",
            reply_markup=start_keyboard
        )


# Ro'yxatdan o'tishni boshlash tugmasi
@router.message(F.text == "Ro'yxatdan o'tish")
async def start_register(message: Message, state: FSMContext):
    user = get_user_by_tg(message.from_user.id)
    if user:
        await answer_with_sticker(
            message,
            "Siz allaqon ro'yxatdan o'tgansiz. Qo'shimcha bonus olish imkoni mavjud emas.",
            sticker_file_id=STICKER_WELCOME,
            reply_markup=main_menu_keyboard
        )
        return

    await state.set_state(RegisterForm.full_name)
    await message.answer("Iltimos, ismingiz va familiyangizni kiriting:")


# Foydalanuvchi ma'lumotlarini qabul qilish
@router.message(RegisterForm.full_name)
async def full_name_handler(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await state.set_state(RegisterForm.birth_year)
    await message.answer("Tug'ilgan yilingizni kiriting (YYYY formatda):")


@router.message(RegisterForm.birth_year)
async def birth_year_handler(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, faqat raqam kiriting!")
        return
    await state.update_data(birth_year=int(message.text))
    await state.set_state(RegisterForm.phone)
    await message.answer("Telefon raqamingizni kiriting:")


@router.message(RegisterForm.phone)
async def phone_handler(message: Message, state: FSMContext):
    session = Session()
    try:
        existing_user = get_user_by_phone(message.text)
        if existing_user:
            await answer_with_sticker(
                message,
                "Siz allaqon ro'yxatdan o'tgansiz. Qo'shimcha bonus olish imkoni mavjud emas.",
                sticker_file_id=STICKER_WELCOME,
                reply_markup=get_menu_for(message.from_user.id)
            )
            # Adminni shubhali faoliyat haqida xabardor qilish
            if ADMIN_ID:
                await bot.send_message(
                    ADMIN_ID,
                    f"⚠️ *Shubhali ko'p hisob qaydnomasi urinish:* \n\n"
                    f"👤 Ism: {existing_user.full_name}\n"
                    f"📞 Telefon: {existing_user.phone}\n"
                    f"🆔 Telegram ID: {message.from_user.id}\n"
                )
            return
    finally:
        session.close()

    await state.update_data(phone=message.text)
    await state.set_state(RegisterForm.address)
    await message.answer("Hozirda yashash manzilingizni kiriting:")


# Ro'yxatdan o‘tish tugagandan so‘ng
@router.message(RegisterForm.address)
async def address_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    session = Session()
    try:
        new_user = User(
            telegram_id=message.from_user.id,
            full_name=data['full_name'],
            birth_year=data['birth_year'],
            phone=data['phone'],
            address=message.text,
            device_id=hash_device_id(message.from_user.id)  # Qurilma ID sini xesh qilish misoli
        )
        session.add(new_user)
        session.commit()
    finally:
        session.close()

    await answer_with_sticker(
        message,
        "Ro'yxatdan muvaffaqiyatli o'tdingiz! Endi botdan foydalanishingiz mumkin.",
        sticker_file_id=STICKER_WELCOME,
        reply_markup=get_menu_for(message.from_user.id)
    )

