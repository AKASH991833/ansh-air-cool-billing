"""
Base Window Class - Common functionality for all PySide6 views
Provides base class with theme support, common utilities, and worker thread handling
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QDialog, QMessageBox, QSizePolicy, QApplication
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QFont, QCursor
from utils.unified_theme import UnifiedTheme
from utils.language import _
import atexit
import threading

try:
    from utils.logger import get_loggers
    _loggers = get_loggers()
    _error_logger = _loggers['error']
except Exception:
    import logging
    _error_logger = logging.getLogger(__name__)


class WorkerSignals(QObject):
    """Signals for worker threads"""
    finished = Signal(object)  # Success result
    error = Signal(str)  # Error message
    progress = Signal(int)  # Progress update (0-100)


class WorkerThread(QThread):
    """Generic worker thread for running tasks without blocking UI"""
    
    # Class-level tracking of active threads
    _active_threads = []
    _active_threads_lock = threading.Lock()
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self._active = True
        self._cleaned_up = False
        
        # Track this thread (thread-safe)
        with WorkerThread._active_threads_lock:
            WorkerThread._active_threads.append(self)
        
        # Connect cleanup only to finished (mutually exclusive with error)
        self.signals.finished.connect(self._on_finished)
        self.signals.finished.connect(self._cleanup)
        self.signals.error.connect(self._cleanup)
    
    def run(self):
        """Execute the function in this thread"""
        try:
            result = self.func(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self._active = False
    
    def _on_finished(self):
        """Called when thread finishes execution"""
        pass
    
    def _cleanup(self):
        """Clean up thread references (guarded against double execution)"""
        if self._cleaned_up:
            return
        self._cleaned_up = True
        self._active = False
        with WorkerThread._active_threads_lock:
            if self in WorkerThread._active_threads:
                WorkerThread._active_threads.remove(self)
        # Disconnect signals to prevent memory leaks
        try:
            self.signals.finished.disconnect()
        except (TypeError, RuntimeError):
            pass
        try:
            self.signals.error.disconnect()
        except (TypeError, RuntimeError):
            pass
        # Guard deleteLater — QApplication may be destroyed at exit
        if QApplication.instance() is not None:
            self.deleteLater()
    
    def stop(self):
        """Request thread to stop"""
        self._active = False
        self.wait(1000)  # Wait up to 1 second


# Cleanup all threads on exit
@atexit.register
def cleanup_threads():
    """Clean up all active worker threads"""
    with WorkerThread._active_threads_lock:
        threads = WorkerThread._active_threads[:]
    for thread in threads:
        if thread.isRunning():
            thread._active = False
            thread.wait(500)  # Wait up to 500ms
    with WorkerThread._active_threads_lock:
        WorkerThread._active_threads.clear()


class MetricCard(QFrame):
    """Unified enterprise-grade metric card with auto-scaling typography, privacy shield & hover effects"""

    clicked = Signal(str)

    def __init__(self, title, value, icon, color, parent=None, is_financial=None):
        super().__init__(parent)
        self._title_text = str(title)
        self._raw_value_text = str(value)
        self.icon = icon
        self.color = color
        self._is_peeked = False
        
        # Auto-detect if this card holds sensitive financial data
        if is_financial is not None:
            self._is_financial = is_financial
        else:
            lower_title = self._title_text.lower()
            val_str = self._raw_value_text
            self._is_financial = (
                any(c in val_str for c in ['₹', '$', '€', '£', 'Rs']) or
                any(kw in lower_title for kw in ['revenue', 'income', 'billed', 'advance', 'profit', 'expense', 'dues', 'cost', 'amount', 'salary', 'settlement'])
            )

        self.theme_manager = UnifiedTheme()
        self.colors = self.theme_manager.get_colors()
        self._shadow = None
        self._setup_ui()
        
        # Connect to Global Event Bus for real-time Privacy Mode changes
        try:
            from utils.event_bus import EventBus
            EventBus().privacy_mode_toggled.connect(self._on_privacy_toggled)
        except Exception:
            pass

    def _setup_ui(self):
        self.setObjectName("metricCard")
        self.setMinimumSize(165, 108)
        self.setMaximumHeight(130)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Soft modern drop shadow for clean depth
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from PySide6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(QColor(15, 23, 42, 22))
        self.setGraphicsEffect(shadow)
        self._shadow = shadow

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 10)
        layout.setSpacing(6)

        top = QHBoxLayout()
        top.setSpacing(10)
        
        # Icon Frame with soft rounded badge
        icon_frame = QFrame()
        icon_frame.setFixedSize(40, 40)
        icon_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.color}18;
                border: 1px solid {self.color}30;
                border-radius: 20px;
            }}
        """)
        il = QVBoxLayout(icon_frame)
        il.setContentsMargins(0, 0, 0, 0)
        il.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl = QLabel(self.icon)
        icon_lbl.setStyleSheet(f"font-size: 15pt; color: {self.color}; background: transparent;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        il.addWidget(icon_lbl)
        top.addWidget(icon_frame)

        # Value container with auto-scaling label
        val_container = QVBoxLayout()
        val_container.setSpacing(0)
        self.value_label = QLabel()
        self.value_label.setObjectName("metricValue")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        val_container.addWidget(self.value_label)
        top.addLayout(val_container)
        layout.addLayout(top)

        # Card Title
        self.title_label = QLabel(self._title_text)
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet(f"""
            font-size: 8.5pt; color: {self.colors['muted']};
            font-weight: 600; background: transparent;
            letter-spacing: 0.2px;
        """)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.title_label)

        self._update_display()

    def _get_dynamic_font_size(self, text: str) -> int:
        """Dynamically scale font size so big numbers never clip or overflow."""
        length = len(text)
        if length <= 6:
            return 20
        elif length <= 9:
            return 17
        elif length <= 12:
            return 14
        elif length <= 15:
            return 12
        else:
            return 11

    def _get_display_text(self) -> str:
        """Compute the current text taking Privacy Mode into account."""
        try:
            from utils.privacy_manager import get_privacy_manager
            privacy_active = get_privacy_manager().is_privacy_enabled()
        except Exception:
            privacy_active = False

        if privacy_active and self._is_financial and not self._is_peeked:
            val = self._raw_value_text.strip()
            # Preserve currency symbol if present
            for sym in ['₹', '$', '€', '£', 'Rs.', 'Rs ']:
                if val.startswith(sym):
                    return f"{sym} ••••••"
            try:
                from utils.app_settings import get_setting
                sym = get_setting('currency_symbol', '₹')
            except Exception:
                sym = '₹'
            return f"{sym} ••••••"
        return self._raw_value_text

    def _update_display(self):
        disp_text = self._get_display_text()
        self.value_label.setText(disp_text)
        font_size = self._get_dynamic_font_size(disp_text)
        
        # Check privacy state for tooltip
        try:
            from utils.privacy_manager import get_privacy_manager
            if get_privacy_manager().is_privacy_enabled() and self._is_financial:
                self.setToolTip(f"{self._title_text}\n(Privacy Shield Active - Click to Peek)")
            else:
                self.setToolTip(f"{self._title_text}: {self._raw_value_text}")
        except Exception:
            self.setToolTip(f"{self._title_text}: {self._raw_value_text}")

        self.setStyleSheet(f"""
            QFrame#metricCard {{
                background-color: {self.colors['card_bg']};
                border: 1px solid {self.colors['border']};
                border-radius: 10px;
            }}
            QFrame#metricCard:hover {{
                background-color: {self.colors['hover']};
                border: 1.5px solid {self.color};
            }}
            QLabel#metricValue {{
                font-size: {font_size}pt;
                font-weight: 700;
                color: {self.color};
                background: transparent;
                padding: 0px;
                letter-spacing: -0.3px;
            }}
        """)

    def _on_privacy_toggled(self, enabled: bool):
        """Called automatically when global privacy state changes."""
        self._is_peeked = False
        self._update_display()

    def set_value(self, value):
        self._raw_value_text = str(value)
        # Update auto-detection if value changes
        if any(c in self._raw_value_text for c in ['₹', '$', '€', '£']):
            self._is_financial = True
        self._update_display()

    def set_color(self, color):
        self.color = color
        self._update_display()

    def enterEvent(self, event):
        disp_text = self._get_display_text()
        font_size = self._get_dynamic_font_size(disp_text)
        self.setStyleSheet(f"""
            QFrame#metricCard {{
                background-color: {self.colors['hover']};
                border: 1.5px solid {self.color};
                border-radius: 10px;
            }}
            QLabel#metricValue {{
                font-size: {font_size}pt;
                font-weight: 700;
                color: {self.color};
                background: transparent;
                padding: 0px;
                letter-spacing: -0.3px;
            }}
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._update_display()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # If in privacy mode, left-click can toggle a quick peek for this card
            try:
                from utils.privacy_manager import get_privacy_manager
                if get_privacy_manager().is_privacy_enabled() and self._is_financial:
                    self._is_peeked = not self._is_peeked
                    self._update_display()
            except Exception:
                pass
            self.clicked.emit(self._title_text)
        super().mousePressEvent(event)


class BaseView(QWidget):
    """Base class for all view widgets with common functionality"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_manager = UnifiedTheme()
        self._setup_base_style()
        self._workers = []  # Track workers for cleanup
        self._loading_overlay = None

        try:
            from utils.scroll_filter import install_scroll_protection
            install_scroll_protection()
        except Exception:
            pass

    def show_loading(self, message="Loading..."):
        """Show a loading overlay on this view"""
        if not self._loading_overlay:
            from PySide6.QtWidgets import QLabel, QVBoxLayout, QFrame, QWidget
            from PySide6.QtCore import Qt
            overlay = QWidget(self)
            overlay.setGeometry(0, 0, self.width(), self.height())
            overlay.setStyleSheet(f"background-color: {UnifiedTheme.get_colors()['bg']};")
            layout = QVBoxLayout(overlay)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            spinner = QLabel("⏳")
            spinner.setStyleSheet(f"font-size: 48pt; background: transparent; color: {UnifiedTheme.get_colors()['primary']};")
            spinner.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(spinner)
            msg_label = QLabel(message)
            msg_label.setStyleSheet(f"font-size: 14pt; color: {UnifiedTheme.get_colors()['fg']}; background: transparent; margin-top: 10px;")
            msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(msg_label)
            overlay.hide()
            self._loading_overlay = overlay
        self._loading_overlay.setGeometry(0, 0, self.width(), self.height())
        self._loading_overlay.show()
        self._loading_overlay.raise_()
        from PySide6.QtCore import QCoreApplication
        QCoreApplication.processEvents()

    def hide_loading(self):
        """Hide the loading overlay"""
        if self._loading_overlay:
            self._loading_overlay.hide()

    def resizeEvent(self, event):
        """Handle resize to update overlay size"""
        super().resizeEvent(event)
        if self._loading_overlay:
            self._loading_overlay.setGeometry(0, 0, self.width(), self.height())

    def _setup_base_style(self):
        """Apply base styling to the widget"""
        self.setAutoFillBackground(True)
        # Apply theme palette and stylesheet
        self.theme_manager.apply_palette(self)
        self.setStyleSheet(self.theme_manager.get_main_stylesheet())
    
    def run_in_thread(self, func, on_success, on_error=None, *args, **kwargs):
        """
        Run a function in a background thread

        Args:
            func: Function to run
            on_success: Callback function for success (receives result)
            on_error: Optional callback for error (receives error message) OR first arg to func
            *args, **kwargs: Arguments to pass to func
        """
        if on_error is not None and not callable(on_error):
            args = (on_error,) + args
            on_error = None

        worker = WorkerThread(func, *args, **kwargs)
        worker.signals.finished.connect(on_success)

        if callable(on_error):
            worker.signals.error.connect(on_error)

        if on_error is None or not callable(on_error):
            worker.signals.error.connect(self._default_error_handler)

        # Track worker for cleanup
        self._workers.append(worker)

        # Clean up completed workers
        self._cleanup_finished_workers()

        worker.start()
    
    def _cleanup_finished_workers(self):
        """Remove references to finished workers"""
        self._workers = [w for w in self._workers if w.isRunning()]
    
    def closeEvent(self, event):
        """Handle widget close event - cleanup workers"""
        self._cleanup_workers()
        super().closeEvent(event) if hasattr(super(), 'closeEvent') else None
    
    def _cleanup_workers(self):
        """Clean up all worker threads"""
        for worker in self._workers:
            if worker.isRunning():
                worker._active = False
                worker.wait(500)  # Wait up to 500ms
                if QApplication.instance() is not None:
                    worker.deleteLater()
        self._workers.clear()
    
    def _default_error_handler(self, error_msg):
        """Default error handler - logs error and shows QMessageBox"""
        _error_logger.error(f"Thread error in {self.__class__.__name__}: {error_msg}")
        QMessageBox.critical(self, "Error", error_msg)
    
    def show_success_message(self, message, title="Success"):
        """Show success message box"""
        QMessageBox.information(self, title, message)
    
    def show_error_message(self, message, title="Error"):
        """Show error message box"""
        QMessageBox.critical(self, title, message)
    
    def show_warning_message(self, message, title="Warning"):
        """Show warning message box"""
        QMessageBox.warning(self, title, message)
    
    def show_question(self, message, title="Confirm"):
        """Show question dialog, returns True if Yes"""
        result = QMessageBox.question(
            self, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return result == QMessageBox.StandardButton.Yes

    def get_colors(self):
        """Get colors for dark theme"""
        return self.theme_manager.get_colors()

    def _create_group_box(self, title, layout_type='vbox'):
        """
        Create styled group box - reusable across all views
        
        Args:
            title: Group box title
            layout_type: 'vbox' for QVBoxLayout, 'form' for QFormLayout
        
        Returns:
            QGroupBox with styled layout
        """
        from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QFormLayout
        colors = self.theme_manager.get_colors()
        
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 11pt;
                border: 1px solid {colors['border']};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
                background-color: {colors['card_bg']};
                color: {colors['fg']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                padding: 0 8px;
                color: {colors['primary']};
                font-size: 12pt;
            }}
        """)
        
        if layout_type == 'form':
            layout = QFormLayout(group)
            layout.setSpacing(12)
        else:
            layout = QVBoxLayout(group)
            layout.setSpacing(12)
        
        return group


class BaseDialog(QDialog):
    """Base class for all dialog windows"""

    def __init__(self, parent=None, title="Dialog"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.theme_manager = UnifiedTheme()
        self.setMinimumWidth(400)
        self._workers = []
        self._setup_base_style()
    
    def _setup_base_style(self):
        """Apply base styling — global enterprise theme"""
        self.theme_manager.apply_palette(self)
        self.setStyleSheet(self.theme_manager.get_main_stylesheet())
    
    def run_in_thread(self, func, on_success, on_error=None, *args, **kwargs):
        """Run function in background thread"""
        worker = WorkerThread(func, *args, **kwargs)
        worker.signals.finished.connect(on_success)
        if on_error:
            worker.signals.error.connect(on_error)
        else:
            worker.signals.error.connect(self._default_error_handler)
        
        self._workers.append(worker)
        worker.start()
    
    def _default_error_handler(self, error_msg):
        """Default error handler - logs error and shows QMessageBox"""
        _error_logger.error(f"Thread error in {self.__class__.__name__}: {error_msg}")
        QMessageBox.critical(self, "Error", error_msg)
    
    def _cleanup_workers(self):
        """Clean up all worker threads"""
        for worker in self._workers:
            if worker.isRunning():
                worker._active = False
                worker.wait(500)
                if QApplication.instance() is not None:
                    worker.deleteLater()
        self._workers.clear()
    
    def accept(self):
        """Override accept to cleanup worker threads"""
        self._cleanup_workers()
        super().accept()
    
    def reject(self):
        """Override reject to cleanup worker threads"""
        self._cleanup_workers()
        super().reject()
    
    def closeEvent(self, event):
        """Handle dialog close event"""
        self._cleanup_workers()
        super().closeEvent(event)
