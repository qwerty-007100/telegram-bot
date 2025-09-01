import importlib, sys, traceback
sys.path.insert(0, r'C:\TelegramBot')
try:
    importlib.import_module('scheduler')
    print('imported scheduler OK')
except Exception:
    traceback.print_exc()
