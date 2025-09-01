# handlers/admin/broadcast.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from config import ADMIN_ID, STICKER_TARIFF
from database import get_all_users
from loader import bot, answer_with_sticker
import logging

logger = logging.getLogger(__name__)

router = Router()


class BroadcastStates(StatesGroup):
    text = State()


@router.callback_query(F.data == "broadcast_all")
async def broadcast_start(call: CallbackQuery, state: FSMContext):
    """Ask admin to enter broadcast text and set FSM state."""
    try:
        caller = call.from_user.id
        logger.info("broadcast_start requested by %s", caller)
        if caller != ADMIN_ID:
            from config import DOCTOR_ID
            if caller != DOCTOR_ID:
                return await call.answer("⛔ Siz admin emassiz!", show_alert=True)

        # acknowledge callback to remove loading spinner
        try:
            await call.answer()
        except Exception:
            pass

        try:
            await answer_with_sticker(call.message, "✏️ Barcha foydalanuvchilarga yuboriladigan xabar matnini kiriting:", sticker_file_id=STICKER_TARIFF)
        except Exception as e:
            logger.exception("Failed to prompt admin for broadcast text: %s", e)
            try:
                await call.message.answer("✏️ Barcha foydalanuvchilarga yuboriladigan xabar matnini kiriting:")
            except Exception:
                pass

        await state.set_state(BroadcastStates.text)
    except Exception as exc:
        logger.exception("Error in broadcast_start: %s", exc)
        try:
            await call.answer("Xatolik yuz berdi", show_alert=True)
        except Exception:
            pass


@router.message(BroadcastStates.text)
async def broadcast_process(message: Message, state: FSMContext):
    """Send provided message.text to all users returned by get_all_users()."""
    try:
        users = get_all_users()
        if not users:
            await message.answer("Foydalanuvchi topilmadi. Test sifatida xabar adminga yuboriladi.")
            # Send to admin for verification
            try:
                await bot.send_message(ADMIN_ID, f"[TEST BROADCAST]\n{message.text}")
            except Exception:
                pass
            await state.clear()
            return

        count = 0
        for user in users:
            user_id = getattr(user, "telegram_id", None)
            if not user_id:
                continue
            try:
                if STICKER_TARIFF:
                    try:
                        await bot.send_sticker(user_id, STICKER_TARIFF)
                    except Exception:
                        pass
                # prepend a clinic/doctor signature to make the broadcast look official
                signature = "Doctor Mirsaid"
                await bot.send_message(user_id, f"{signature}: {message.text}")
                count += 1
            except Exception as e:
                # log and continue on per-user failures
                logger.exception("Failed to send broadcast to %s: %s", user_id, e)
                continue

        if count == 0:
            # no successful sends, send a test copy to admin so they can see text
            try:
                await bot.send_message(ADMIN_ID, f"[TEST BROADCAST]\n{message.text}")
            except Exception:
                pass
        await answer_with_sticker(message, f"✅ {count} ta foydalanuvchiga xabar yuborildi.", sticker_file_id=STICKER_TARIFF)
    except Exception as exc:
        logger.exception("Error during broadcast_process: %s", exc)
        await message.answer("Xatolik yuz berdi: broadcast amalga oshirilmadi.")
    finally:
        try:
            await state.clear()
        except Exception:
            pass

