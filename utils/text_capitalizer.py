"""
Global auto-capitalizer for text input fields.
Every word's first letter becomes uppercase, rest lowercase.
No changes needed to individual view files.
"""
import re
from PySide6.QtCore import QObject, QEvent
from PySide6.QtWidgets import QLineEdit, QTextEdit, QPlainTextEdit


def to_title_case(text: str) -> str:
    """Convert text to proper case: first letter of each word uppercase, rest lowercase."""
    if not text or not isinstance(text, str):
        return text or ''

    stripped = text.strip()
    if not stripped:
        return text

    # Skip structured codes: INV-2026-0001, AMCI-0001, etc.
    # These have letters + digits mixed with hyphens
    if re.match(r'^[A-Za-z]+[-_][A-Za-z0-9]+[-_0-9]*$', stripped):
        return text

    # Skip emails, URLs, paths
    if re.search(r'[@/\\]', stripped):
        return text

    # Skip if more than 40% is digits (likely phone/ID/code)
    digit_ratio = sum(1 for c in stripped if c.isdigit()) / max(len(stripped), 1)
    if digit_ratio > 0.4:
        return text

    # Capitalize each word: first letter upper, rest lower
    words = stripped.split()
    capitalized = []
    for word in words:
        if not word:
            continue
        if word.isdigit():
            capitalized.append(word)
        else:
            capitalized.append(word[0].upper() + word[1:].lower())

    return ' '.join(capitalized)


class AutoCapitalizeFilter(QObject):
    """Global event filter: auto-capitalizes text inputs on focus loss."""

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusOut:
            if isinstance(obj, (QLineEdit, QTextEdit, QPlainTextEdit)):
                self._capitalize(obj)
        return super().eventFilter(obj, event)

    def _capitalize(self, widget):
        text = widget.toPlainText() if isinstance(widget, (QTextEdit, QPlainTextEdit)) else widget.text()
        if not text:
            return

        # Skip password fields
        if isinstance(widget, QLineEdit) and widget.echoMode() == QLineEdit.EchoMode.Password:
            return

        # Skip login window fields (username/password should remain as-typed)
        top = widget.window()
        if top and 'login' in top.windowTitle().lower():
            return

        converted = to_title_case(text)
        if converted != text:
            if isinstance(widget, (QTextEdit, QPlainTextEdit)):
                widget.setPlainText(converted)
            else:
                widget.setText(converted)


# Singleton filter instance
_capitalize_filter = None


def install_auto_capitalize(app):
    """Install the auto-capitalize event filter on QApplication."""
    global _capitalize_filter
    if _capitalize_filter is None:
        _capitalize_filter = AutoCapitalizeFilter()
    app.installEventFilter(_capitalize_filter)
