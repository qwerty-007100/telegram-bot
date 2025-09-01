from aiogram import Router, types, Dispatcher
from keyboards import get_menu_for
from keyboards.tariffs import (
    tariff_main_keyboard,
    weekly_monthly_keyboard,
    homiladorlik_keyboard
)
from loader import answer_with_sticker
from config import STICKER_TARIFF
from database import get_user_by_tg  # check registration

router = Router()

from aiogram.fsm.context import FSMContext
from handlers.purchase import start_purchase, PurchaseFSM

# 1️⃣ Tariflar haqida umumiy ma'lumot
@router.message(lambda m: m.text in ["Tariflar haqida", "📌 Tariflar haqida"])
async def tariffs_info(message: types.Message, state: FSMContext):
    # Tariff section disabled — all users have open access now.
    try:
        await state.clear()
    except Exception:
        pass
    await answer_with_sticker(message, "� Tariflar bo'limi vaqtincha oʻchirildi. Hozircha barcha foydalanuvchilar uchun savollar cheksiz ochiq.", sticker_file_id=STICKER_TARIFF, reply_markup=get_menu_for(message.from_user.id))


# 2️⃣ Tarif sotib olish menyusi
@router.message(lambda m: m.text in ["🏷 Tarif sotib olish", "Tarif sotib olish"])
async def buy_tariff(message: types.Message, state: FSMContext):
    """Start the purchase FSM in the purchase handler by delegating with the current FSM context."""
    from handlers.purchase import start_purchase
    # delegate to purchase.start_purchase which expects (msg, state)
    try:
        await state.clear()
    except Exception:
        pass
    await start_purchase(message, state)


# 3️⃣ Tarif turlari bo‘yicha tanlovlar
@router.message(lambda m: m.text == "💰 Pro")
async def pro_selected(message: types.Message, state: FSMContext):
    # Start purchase flow and preselect Pro
    await start_purchase(message, state)
    await state.update_data(tariff="pro")
    await state.set_state(PurchaseFSM.choose_plan)
    await answer_with_sticker(message, "Qaysi reja kerak?", sticker_file_id=STICKER_TARIFF, reply_markup=weekly_monthly_keyboard)


@router.message(lambda m: m.text == "💎 Premium")
async def premium_selected(message: types.Message, state: FSMContext):
    await start_purchase(message, state)
    await state.update_data(tariff="premium")
    await state.set_state(PurchaseFSM.choose_plan)
    await answer_with_sticker(message, "Qaysi reja kerak?", sticker_file_id=STICKER_TARIFF, reply_markup=weekly_monthly_keyboard)


@router.message(lambda m: m.text == "👪 Farzand ko‘rishni rejalashtirish")
async def family_selected(message: types.Message, state: FSMContext):
    await start_purchase(message, state)
    await state.update_data(tariff="farzand ko‘rishni rejalashtirish")
    await state.set_state(PurchaseFSM.choose_plan)
    await answer_with_sticker(message, "Qaysi reja kerak?", sticker_file_id=STICKER_TARIFF, reply_markup=weekly_monthly_keyboard)


@router.message(lambda m: m.text == "🤰 Homiladorlik")
async def pregnancy_selected(message: types.Message, state: FSMContext):
    await start_purchase(message, state)
    await state.update_data(tariff="pregnancy")
    await state.set_state(PurchaseFSM.choose_plan)
    await answer_with_sticker(message, "Homiladorlik uchun reja tanlang:", sticker_file_id=STICKER_TARIFF, reply_markup=homiladorlik_keyboard)


# 4️⃣ Orqaga qaytish
@router.message(lambda m: m.text == "Orqaga")
async def go_back(message: types.Message, state: FSMContext):
    # If in purchase FSM -> go back in purchase, otherwise return to main menu
    from handlers.purchase import start_purchase
    try:
        # clear any stray FSM and show main menu
        await state.clear()
        await answer_with_sticker(message, "Bosh menyuga qaytildi.", reply_markup=get_menu_for(message.from_user.id))
        return
    except Exception:
        pass

    try:
        await start_purchase(message, state)
    except Exception:
        await answer_with_sticker(message, "Bosh menyuga qaytildi.", reply_markup=get_menu_for(message.from_user.id))


# 5️⃣ Yakuniy tanlov
@router.message(lambda m: m.text in ["1 haftalik", "1 oylik", "Homiladorlik 1 oy", "Homiladorlik 9 oy"])
async def plan_selected(message: types.Message, state: FSMContext):
    # Delegate plan selection to purchase.choose_plan which manages creating pending payment and next steps
    from handlers.purchase import choose_plan
    # Do NOT clear the state here: tariff must remain stored in FSM data.
    await choose_plan(message, state)


# 🔹 Main.py uchun ro‘yxatdan o‘tkazish funksiyasi
def register_tariff_handlers(dp: Dispatcher):
    dp.include_router(router)
