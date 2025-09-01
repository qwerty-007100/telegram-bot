"""
Async-safe DB wrappers.

Wrap synchronous `database.py` helpers using asyncio.to_thread so they can be
awaited from aiogram handlers without blocking the event loop.
"""
import asyncio
from typing import Any, Dict, Optional

from data.db import db  # Import the in-memory database instance


async def create_pending_payment(payload: Dict[str, Any]) -> int:
    """Create a pending payment record (delegates to sync_db.create_pending_payment)."""
    return await asyncio.to_thread(db.start_payment, **payload)


async def get_pending_payment(pid: int) -> Optional[Dict[str, Any]]:
    """Fetch pending payment by id (delegates to sync_db.get_pending_payment)."""
    user = await asyncio.to_thread(db.get_user, pid)
    if user and user.payment_pending:
        return user.payment_info
    return None


async def update_pending_payment(pid: int, updates: Dict[str, Any]) -> None:
    """Update pending payment record (delegates to sync_db.update_pending_payment)."""
    user = await asyncio.to_thread(db.get_user, pid)
    if user and user.payment_pending:
        for key, value in updates.items():
            if key in user.payment_info:
                user.payment_info[key] = value


async def get_user_by_tg(tg_id: int) -> Optional[Any]:
    """Return user DB object (delegates to sync_db.get_user_by_tg)."""
    return await asyncio.to_thread(db.get_user, tg_id)


async def create_user(tg_id: int, full_name: str = None, phone: str = None) -> Any:
    """Create user if missing (delegates to sync_db.create_user)."""
    return await asyncio.to_thread(db.add_user, tg_id, full_name, phone)


async def get_user_bonus(user_db_id: int) -> int:
    """Return user's bonus balance (delegates to sync_db.get_user_bonus)."""
    user = await asyncio.to_thread(db.get_user, user_db_id)
    return user.bonus if user else 0


async def set_user_bonus(user_db_id: int, amount: int) -> None:
    """Set user's bonus balance (delegates to sync_db.set_user_bonus)."""
    return await asyncio.to_thread(db.update_bonus, user_db_id, amount)


async def activate_tariff(user_db_id: int, tariff: str, days: int) -> None:
    """Activate tariff for a user (delegates to sync_db.activate_tariff)."""
    user = await asyncio.to_thread(db.get_user, user_db_id)
    if user:
        user.active_tariff = tariff  # In-memory DB doesn't track expiry, etc.


async def get_latest_pending_by_user(tg_id: int) -> Optional[Dict[str, Any]]:
    """Return the latest pending payment for a Telegram user."""
    user = await asyncio.to_thread(db.get_user, tg_id)
    if user and user.payment_pending:
        return user.payment_info
    return None
