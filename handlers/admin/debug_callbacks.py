from aiogram import Router, F
from aiogram.types import CallbackQuery
from config import ADMIN_ID
import logging

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query()
async def debug_any_callback(call: CallbackQuery):
    """Temporary debug handler: logs any callback_query and acknowledges it if from admin/doctor.

    This helps confirm whether callback queries reach the bot. Remove this file when debugging is done.
    """
    try:
        caller = call.from_user.id
        logger.info("DEBUG_CALLBACK received from %s: %s", caller, call.data)
        # Always acknowledge the callback query to remove the client's loading spinner.
        # For admin/doctor we include a short debug text, for others a silent ack.
        from config import DOCTOR_ID
        try:
            if caller in (ADMIN_ID, DOCTOR_ID):
                await call.answer("(debug) callback received")
            else:
                await call.answer()
            # best-effort visible debug message in the chat to show caller id and data
            try:
                if call.message:
                    await call.message.answer(f"DEBUG CALLBACK — from_id={caller} data={call.data}")
            except Exception:
                pass
        except Exception:
            # ignore if already answered by a more specific handler or Telegram rejects duplicate answers
            pass
    except Exception as e:
        logger.exception("Error in debug_any_callback: %s", e)
