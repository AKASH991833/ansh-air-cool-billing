"""
Global Mouse Wheel & Touchpad Scroll Protection for Desktop Software.

Prevents accidental increment/decrement of values in QSpinBox, QDoubleSpinBox,
QDateEdit, QTimeEdit, and QComboBox when the user is scrolling through a form,
dialog, or table with a mouse wheel or touchpad two-finger gesture.

Instead of modifying price, quantity, tax, discount, or selection unnoticed,
the wheel event is blocked on the control and seamlessly forwarded to the
enclosing scrollable container (QScrollArea, QTableWidget, QListView, etc.),
ensuring smooth page navigation without unintended data changes.

Values can only be deliberately changed by:
1. Direct typing / text editing with keyboard
2. Clicking the on-screen Up / Down stepper buttons
3. Pressing the Up / Down arrow keys on the keyboard
"""
from PySide6.QtCore import QObject, QEvent
from PySide6.QtWidgets import (
    QAbstractSpinBox, QComboBox, QAbstractScrollArea, QApplication
)


class PreventAccidentalScrollFilter(QObject):
    """
    Global event filter that blocks wheel events on spinboxes and comboboxes,
    redirecting them to the parent scrollable view so scrolling never alters numbers.
    """

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel:
            if isinstance(obj, (QAbstractSpinBox, QComboBox)):
                # Ignore the event on the input widget so its value does not change
                event.ignore()

                # Seamlessly forward the wheel event to the nearest scrollable container
                # (e.g. QScrollArea, QTableWidget, QListView) so the user's page continues to scroll
                parent = obj.parentWidget()
                while parent:
                    if isinstance(parent, QAbstractScrollArea):
                        target = parent.viewport() if hasattr(parent, 'viewport') and parent.viewport() else parent
                        QApplication.sendEvent(target, event)
                        return True
                    parent = parent.parentWidget()

                return True

        return super().eventFilter(obj, event)


_scroll_protection_filter = None


def install_scroll_protection(app=None):
    """
    Install the scroll protection filter globally on the QApplication instance.
    Safe to call multiple times (singleton filter).
    """
    global _scroll_protection_filter
    if app is None:
        app = QApplication.instance()
    if app is None:
        return

    if _scroll_protection_filter is None:
        _scroll_protection_filter = PreventAccidentalScrollFilter()
        app.installEventFilter(_scroll_protection_filter)
