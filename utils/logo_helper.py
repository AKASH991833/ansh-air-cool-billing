import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
try:
    from config import DATA_DIR, RESOURCE_DIR
    DEFAULT_LOGO = RESOURCE_DIR / 'assets' / 'Logo.png'
    LOGO_STORAGE = DATA_DIR
except Exception:
    DEFAULT_LOGO = BASE_DIR / 'assets' / 'Logo.png'
    LOGO_STORAGE = BASE_DIR / 'data'
CUSTOM_LOGO_NAME = 'custom_logo.png'


def get_logo_path():
    logo_path = LOGO_STORAGE / CUSTOM_LOGO_NAME
    if logo_path.exists():
        return str(logo_path)
    if DEFAULT_LOGO.exists():
        return str(DEFAULT_LOGO)
    return None


def save_uploaded_logo(source_path):
    LOGO_STORAGE.mkdir(exist_ok=True)
    import shutil
    dest = LOGO_STORAGE / CUSTOM_LOGO_NAME
    shutil.copy2(source_path, dest)
    return str(dest)


def get_logo_base64():
    import base64
    path = get_logo_path()
    if path and os.path.exists(path):
        with open(path, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None
