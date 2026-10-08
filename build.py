"""
Build standalone EXE using PyInstaller
Usage:
    python build.py            # Recommended: Fast-startup directory build (starts in <1s)
    python build.py --onedir   # Fast-startup directory build
    python build.py --onefile  # Single standalone EXE file
"""
import os
import sys
import shutil
from pathlib import Path

APP_NAME = "AC_Billing_System"
PROJECT_DIR = Path(__file__).parent
DIST_DIR = PROJECT_DIR / "dist"
BUILD_DIR = PROJECT_DIR / "build"

def clean_build():
    for d in [DIST_DIR, BUILD_DIR]:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
    spec_file = PROJECT_DIR / f"{APP_NAME}.spec"
    if spec_file.exists():
        try:
            spec_file.unlink()
        except Exception:
            pass

def build():
    mode = "--onedir"
    if "--onefile" in sys.argv:
        mode = "--onefile"

    clean_build()

    import PyInstaller.__main__

    assets_dir = str(PROJECT_DIR / "assets")
    icon_path = str(PROJECT_DIR / "assets" / "app_icon.ico")

    args = [
        "--name", APP_NAME,
        mode,
        "--windowed",
        "--add-data", f"{assets_dir}{os.pathsep}assets",
        "--hidden-import", "PySide6.QtCore",
        "--hidden-import", "PySide6.QtGui",
        "--hidden-import", "PySide6.QtWidgets",
        "--hidden-import", "PySide6.QtPrintSupport",
        "--hidden-import", "PySide6.QtWebEngineWidgets",
        "--hidden-import", "PySide6.QtWebEngineCore",
        "--hidden-import", "PySide6.QtWebEngineQuick",
        "--hidden-import", "bcrypt",
        "--hidden-import", "reportlab",
        "--hidden-import", "openpyxl",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL._imagingtk",
        "--hidden-import", "dateutil",
        "--hidden-import", "dateutil.parser",
        "--hidden-import", "dateutil.relativedelta",
        "--hidden-import", "psutil",
        "--hidden-import", "schedule",
        "--hidden-import", "sqlite3",
        "--exclude-module", "tkinter",
        "--exclude-module", "pytest",
        "--exclude-module", "unittest",
        "--collect-all", "PySide6",
        "--noconfirm",
    ]

    if os.path.exists(icon_path):
        args.extend(["--icon", icon_path])

    args.append(str(PROJECT_DIR / "main.py"))

    print("=" * 60)
    print(f"Building {APP_NAME} ({mode})...")
    print(f"Python: {sys.version}")
    print(f"Icon: {icon_path if os.path.exists(icon_path) else 'Default'}")
    print("=" * 60)

    PyInstaller.__main__.run(args)

    if mode == "--onefile":
        dist_exe = DIST_DIR / f"{APP_NAME}.exe"
        if dist_exe.exists():
            print(f"\n{'=' * 60}")
            print(f"SUCCESS! Standalone Single EXE created at:")
            print(f"  {dist_exe}")
            print(f"Size: {dist_exe.stat().st_size / 1024 / 1024:.1f} MB")
            print(f"{'=' * 60}")
        else:
            print(f"\nERROR: EXE not found at {dist_exe}")
            sys.exit(1)
    else:
        dist_folder = DIST_DIR / APP_NAME
        dist_exe = dist_folder / f"{APP_NAME}.exe"
        if dist_exe.exists():
            print(f"\n{'=' * 60}")
            print(f"SUCCESS! Fast-launch desktop bundle created at:")
            print(f"  {dist_folder}")
            print(f"Main Executable: {dist_exe}")
            print(f"{'=' * 60}")
        else:
            print(f"\nERROR: Application bundle not found at {dist_folder}")
            sys.exit(1)

if __name__ == "__main__":
    build()
