"""
WhatsApp Clipboard Helper - Direct PDF share via Ctrl+V

Windows-specific helper that puts the ACTUAL FILE (not just a path) on the
clipboard so that pressing Ctrl+V inside WhatsApp Desktop / WhatsApp Web
pastes the PDF as a ready-to-send attachment.

Also provides a "direct chat" opener that lands the user straight inside the
customer's chat (WhatsApp Desktop deep-link, falling back to wa.me web).

CRASH FIX: QMimeData must stay alive for the entire lifetime of the clipboard
operation. We keep a module-level reference (_mime_keep_alive) so Python's
garbage collector never deletes the C++ object while Qt still holds a pointer.
"""
import time
import webbrowser
from urllib.parse import quote

# ── Module-level reference to prevent GC of QMimeData ──────────────────────
# PySide6 crash: "Internal C++ object (PySide6.QtCore.QMimeData) already deleted"
# Root cause: Python drops the QMimeData reference (mime object goes out of scope)
# before Qt's clipboard is done with it.  Keeping a strong reference here fixes it.
_mime_keep_alive = None


def copy_file_to_clipboard(file_path: str) -> bool:
    """
    Copy a real file to the Windows clipboard (like pressing Ctrl+C in Explorer).

    After this, Ctrl+V in WhatsApp Desktop/Web pastes the file as an attachment.

    Args:
        file_path: Absolute path to the file (PDF, image, etc.)

    Returns:
        True if the file was placed on the clipboard successfully.
    """
    global _mime_keep_alive

    import os
    if not file_path or not os.path.exists(file_path):
        print(f"❌ Clipboard copy failed: file not found -> {file_path}")
        return False

    abs_path = os.path.abspath(file_path)

    # ── Preferred: Qt clipboard with Windows on-disk file format ────────────
    try:
        from PySide6.QtCore import QMimeData, QUrl
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is not None:
            mime = QMimeData()
            mime.setUrls([QUrl.fromLocalFile(abs_path)])

            # CRITICAL: assign to module-level BEFORE handing to clipboard.
            # This guarantees the C++ QMimeData object is never deleted by
            # Python while Qt still holds a raw pointer to it.
            _mime_keep_alive = mime

            clipboard = QApplication.clipboard()
            clipboard.setMimeData(mime)

            # Process events so the clipboard operation completes synchronously.
            app.processEvents()

            print(f"✅ File copied to clipboard (Qt): {os.path.basename(abs_path)}")
            return True

    except Exception as qt_err:
        print(f"⚠️ Qt clipboard copy failed ({qt_err}), trying win32...")

    # ── Fallback: native win32 CF_HDROP (real Explorer-style copy) ──────────
    try:
        import win32clipboard
        import win32con
        import struct

        # DROPFILES structure: offset(4) + pt(8) + fNC(4) + fWide(4) = 20 bytes
        files = abs_path.encode("utf-16-le") + b"\x00\x00"
        data = struct.pack("iiiII", 20, 0, 0, 0, 1) + files

        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_HDROP, data)
        finally:
            win32clipboard.CloseClipboard()

        print(f"✅ File copied to clipboard (win32): {os.path.basename(abs_path)}")
        return True

    except Exception as win32_err:
        print(f"❌ win32 clipboard also failed: {win32_err}")

    return False


def open_direct_chat(phone: str) -> bool:
    """
    Open the customer's WhatsApp chat DIRECTLY (chat window open, ready to paste).

    Order of attempts:
      1. WhatsApp Desktop deep-link  ->  whatsapp://send?phone=...
      2. WhatsApp Web / wa.me        ->  https://wa.me/<phone>

    Args:
        phone: Phone number (with or without country code)

    Returns:
        True if a chat window was opened.
    """
    try:
        from utils.whatsapp_helper import WhatsAppHelper

        clean_phone = WhatsAppHelper.clean_phone_number(phone)
        if not clean_phone:
            print("❌ Invalid phone number for WhatsApp chat")
            return False

        # 1) WhatsApp Desktop app (opens straight into the chat)
        desktop_url = f"whatsapp://send?phone={clean_phone}"
        if webbrowser.open(desktop_url):
            print(f"✅ WhatsApp Desktop chat opened for {clean_phone}")
            return True

        # 2) Fallback: wa.me in browser (WhatsApp Web chat opens there)
        web_url = f"{WhatsAppHelper.BASE_URL}/{clean_phone}"
        webbrowser.open(web_url)
        print(f"✅ WhatsApp Web chat opened for {clean_phone}")
        return True

    except Exception as e:
        print(f"❌ Error opening WhatsApp chat: {e}")
        return False


def open_direct_chat_with_message(
    phone: str,
    message: str,
    paste_file: bool = True,
    file_path: str = None,
) -> bool:
    """
    Full direct-share sequence:
      1. Copy the PDF file to clipboard (Ctrl+V ready)
      2. Open the customer's chat directly
      3. Auto-paste (Ctrl+V) into the focused chat window
      4. Auto-press Enter to send

    Args:
        phone:      Customer phone number
        message:    Pre-filled caption/message
        paste_file: Whether to auto-paste the attachment
        file_path:  PDF path (required when paste_file is True)

    Returns:
        True if the chat was opened successfully.
    """
    try:
        from utils.whatsapp_helper import WhatsAppHelper

        clean_phone = WhatsAppHelper.clean_phone_number(phone)
        if not clean_phone:
            return False

        # Step 1: put the real file on the clipboard FIRST (before opening chat)
        if paste_file and file_path:
            if not copy_file_to_clipboard(file_path):
                paste_file = False   # clipboard failed, fall back to text link

        # Step 2: open the chat directly
        if not open_direct_chat(clean_phone):
            return False

        # Step 3: give the chat window time to appear, then paste + send
        if paste_file and file_path:
            import threading

            def _paste_and_send():
                try:
                    time.sleep(2.5)       # wait for WhatsApp window focus
                    _press_ctrl_v()
                    time.sleep(1.0)       # wait for attachment preview to load
                    _press_enter()
                    print("✅ Auto-paste done - PDF attached in WhatsApp")
                except Exception as exc:
                    print(f"⚠️ Auto-paste skipped: {exc}")

            threading.Thread(target=_paste_and_send, daemon=True).start()

        elif message:
            # No auto-paste: fall back to wa.me pre-filled text link
            url = f"{WhatsAppHelper.BASE_URL}/{clean_phone}?text={quote(message.strip())}"
            webbrowser.open(url)

        return True

    except Exception as e:
        print(f"❌ Error in direct WhatsApp share: {e}")
        return False


def share_pdf_via_whatsapp(phone: str, pdf_path: str, message: str = "") -> bool:
    """
    Convenience wrapper: copy PDF to clipboard and open WhatsApp chat in one call.
    This is the recommended entry point for invoice sharing from the UI.

    Args:
        phone:    Customer phone number
        pdf_path: Absolute path to the generated PDF file
        message:  Optional text message/caption

    Returns:
        True if the operation succeeded.
    """
    return open_direct_chat_with_message(
        phone=phone,
        message=message,
        paste_file=True,
        file_path=pdf_path,
    )


# ── Internal keyboard simulation ────────────────────────────────────────────

def _press_ctrl_v():
    """Simulate Ctrl+V on the focused window (Windows)."""
    import ctypes
    user32 = ctypes.windll.user32
    VK_CONTROL, VK_V = 0x11, 0x56
    user32.keybd_event(VK_CONTROL, 0, 0, 0)    # Ctrl down
    user32.keybd_event(VK_V, 0, 0, 0)          # V down
    user32.keybd_event(VK_V, 0, 2, 0)          # V up   (KEYEVENTF_KEYUP)
    user32.keybd_event(VK_CONTROL, 0, 2, 0)    # Ctrl up


def _press_enter():
    """Simulate Enter on the focused window (Windows)."""
    import ctypes
    user32 = ctypes.windll.user32
    VK_RETURN = 0x0D
    user32.keybd_event(VK_RETURN, 0, 0, 0)
    user32.keybd_event(VK_RETURN, 0, 2, 0)
