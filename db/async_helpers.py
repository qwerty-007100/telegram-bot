import asyncio
from typing import Optional, Dict, Any
from .crud import (
    get_user_by_tg as sync_get_user_by_tg,
    create_user as sync_create_user,
    create_pending_payment as sync_create_pending_payment,
    get_pending_payment as sync_get_pending_payment,
    update_pending_payment as sync_update_pending_payment,
    get_latest_pending_by_user as sync_get_latest_pending_by_user,
    activate_tariff as sync_activate_tariff,
)

async def get_user_by_tg(tg_id: int):
    return await asyncio.to_thread(sync_get_user_by_tg, tg_id)

async def create_user(tg_id: int, full_name=None, phone=None, device_id=None, referred_by=None):
    return await asyncio.to_thread(sync_create_user, tg_id, full_name, phone, device_id, referred_by)

async def create_pending_payment(payload: Dict[str, Any]) -> int:
    return await asyncio.to_thread(sync_create_pending_payment, payload)

async def get_pending_payment(pid: int) -> Optional[Dict[str, Any]]:
    return await asyncio.to_thread(sync_get_pending_payment, pid)

async def update_pending_payment(pid: int, updates: Dict[str, Any]) -> None:
    return await asyncio.to_thread(sync_update_pending_payment, pid, updates)

async def get_latest_pending_by_user(tg_id: int) -> Optional[Dict[str, Any]]:
    return await asyncio.to_thread(sync_get_latest_pending_by_user, tg_id)

async def activate_tariff(user_db_id: int, tariff: str, days: int) -> None:
    return await asyncio.to_thread(sync_activate_tariff, user_db_id, tariff, days)
