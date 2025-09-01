# Export keyboards and helper to return the right menu for a user
from .default import main_menu_keyboard, admin_keyboard, doctor_keyboard
from .start_keyboard import start_keyboard
from config import ADMIN_ID, DOCTOR_ID

def get_menu_for(user_id: int):
	"""Return the appropriate main menu keyboard for the given user id.

	- Admin users get `admin_keyboard`.
	- Doctor users get `doctor_keyboard`.
	- Everyone else gets the regular `main_menu_keyboard`.
	"""
	try:
		uid = int(user_id or 0)
	except Exception:
		uid = 0
	if uid == ADMIN_ID:
		return admin_keyboard
	if uid == DOCTOR_ID:
		return doctor_keyboard
	return main_menu_keyboard

__all__ = ["main_menu_keyboard", "start_keyboard", "admin_keyboard", "doctor_keyboard", "get_menu_for"]
