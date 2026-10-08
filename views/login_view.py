"""
Login View - Professional Glassmorphism UI
Fixed: Background full window, Login card perfectly centered
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QLineEdit, QPushButton, QGraphicsDropShadowEffect,
    QSizePolicy, QCheckBox, QGridLayout
)
from PySide6.QtCore import Qt, QTimer, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPixmap, QColor
from utils.unified_theme import UnifiedTheme
from utils.app_settings import get_setting
import os


class LoginWindow(QMainWindow):
    """Professional login window with perfect centering"""

    login_success = Signal()

    def __init__(self, on_login_success=None):
        super().__init__()
        self.on_login_success = on_login_success
        self.theme_manager = UnifiedTheme()  # Use unified theme
        self._workers = []

        # Window setup
        self.setWindowTitle(f"{get_setting('app_name', 'AC Service Billing')} - Login")
        self.showMaximized()

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Use QGridLayout for perfect layering
        grid_layout = QGridLayout(central_widget)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(0)

        # Background label (row 0, col 0)
        self.bg_label = QLabel()
        self.bg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bg_label.setScaledContents(True)
        grid_layout.addWidget(self.bg_label, 0, 0)

        # Dark overlay for better text visibility (row 0, col 0)
        overlay_widget = QWidget()
        overlay_widget.setStyleSheet("background-color: rgba(0, 0, 0, 0.5);")
        grid_layout.addWidget(overlay_widget, 0, 0)

        # Overlay layout with centering
        overlay_layout = QVBoxLayout(overlay_widget)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setSpacing(0)
        
        # Center the login card vertically and horizontally
        overlay_layout.addStretch(1)
        
        card_layout = QHBoxLayout()
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create login card
        self.login_card = self._create_login_card()
        card_layout.addWidget(self.login_card)
        
        overlay_layout.addLayout(card_layout)
        overlay_layout.addStretch(1)

        # Apply unified theme stylesheet
        self.setStyleSheet(self.theme_manager.get_login_stylesheet())

        # Load background
        self._load_background()

        # Fade-in animation
        self._fade_in()

    def _create_login_card(self):
        """Create and return login card widget"""
        card = QFrame()
        card.setObjectName("loginCard")
        card.setMaximumWidth(450)
        card.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)

        # Enhanced shadow effect for glassmorphism
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(80)
        shadow.setXOffset(0)
        shadow.setYOffset(30)
        shadow.setColor(QColor(0, 0, 0, 180))
        card.setGraphicsEffect(shadow)

        # Card layout
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(45, 40, 45, 40)
        card_layout.setSpacing(16)

        # ===== Logo =====
        logo_container = QFrame()
        logo_container.setObjectName("logoContainer")
        logo_container.setFixedSize(120, 120)
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.setContentsMargins(0, 0, 0, 0)

        try:
            from utils.logo_helper import get_logo_path
            logo_path = get_logo_path()
            if logo_path and os.path.exists(logo_path):
                logo_label = QLabel()
                pixmap = QPixmap(logo_path).scaled(
                    70, 70,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                logo_label.setPixmap(pixmap)
                logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                logo_label.setContentsMargins(0, 0, 0, 0)
                logo_layout.addWidget(logo_label)
            else:
                logo_label = QLabel("❄️")
                logo_label.setFont(QFont('Segoe UI', 48))
                logo_label.setStyleSheet(f"color: {self.theme_manager.get_colors()['primary']};")
                logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                logo_layout.addWidget(logo_label)
        except Exception:
            logo_label = QLabel("❄️")
            logo_label.setFont(QFont('Segoe UI', 48))
            logo_label.setStyleSheet(f"color: {self.theme_manager.get_colors()['primary']};")
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_layout.addWidget(logo_label)

        card_layout.addWidget(logo_container)
        card_layout.addSpacing(5)

        # ===== Title =====
        title_label = QLabel(get_setting('app_name', 'AC Service Billing'))
        title_label.setObjectName("loginTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        card_layout.addWidget(title_label)

        # ===== Subtitle =====
        subtitle_label = QLabel("Sign in to your account to continue")
        subtitle_label.setObjectName("loginSubtitle")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setWordWrap(True)
        card_layout.addWidget(subtitle_label)

        card_layout.addSpacing(15)

        # ===== Separator =====
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent,
                stop:0.5 rgba(255, 255, 255, 0.2),
                stop:1 transparent);
            max-height: 1px;
        """)
        card_layout.addWidget(separator)
        card_layout.addSpacing(10)

        # ===== Error Label =====
        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        card_layout.addWidget(self.error_label)

        # ===== Username Input =====
        username_label = QLabel("USERNAME")
        username_label.setObjectName("inputLabel")
        card_layout.addWidget(username_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setClearButtonEnabled(True)
        self.username_input.returnPressed.connect(self._focus_password)
        card_layout.addWidget(self.username_input)

        # ===== Password Input =====
        password_label = QLabel("PASSWORD")
        password_label.setObjectName("inputLabel")
        card_layout.addWidget(password_label)

        password_layout = QHBoxLayout()
        password_layout.setSpacing(10)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setClearButtonEnabled(True)
        self.password_input.returnPressed.connect(self._perform_login)
        password_layout.addWidget(self.password_input, 1)

        # Toggle password visibility
        self.toggle_password_btn = QPushButton("👁️")
        self.toggle_password_btn.setObjectName("togglePasswordBtn")
        self.toggle_password_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_password_btn.setFixedSize(42, 42)
        self.toggle_password_btn.clicked.connect(self._toggle_password_visibility)
        password_layout.addWidget(self.toggle_password_btn)

        card_layout.addLayout(password_layout)

        # ===== Remember Me =====
        self.remember_checkbox = QCheckBox("Remember me")
        self.remember_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remember_checkbox.setObjectName("rememberCheckbox")
        card_layout.addWidget(self.remember_checkbox)

        card_layout.addSpacing(10)

        # ===== Login Button =====
        self.login_button = QPushButton("SIGN IN")
        self.login_button.setObjectName("loginButton")
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_button.setMinimumHeight(48)
        self.login_button.clicked.connect(self._perform_login)
        card_layout.addWidget(self.login_button)

        # ===== Footer =====
        from datetime import datetime
        app_name = get_setting('app_name', 'AC Service Billing')
        footer_label = QLabel(f"© {datetime.now().year} {app_name}. All rights reserved.")
        footer_label.setObjectName("footerLabel")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(footer_label)

        return card

    def _load_background(self):
        """Load fullscreen background with proper scaling"""
        try:
            from config import RESOURCE_DIR
            bg_path = os.path.join(str(RESOURCE_DIR), 'assets', 'login_page.png')
            if os.path.exists(bg_path):
                pixmap = QPixmap(bg_path)
                if not pixmap.isNull():
                    # Scale to cover entire window
                    scaled_pixmap = pixmap.scaled(
                        self.width(),
                        self.height(),
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.bg_label.setPixmap(scaled_pixmap)
                    self.bg_label.setStyleSheet(f"background-color: {self.theme_manager.get_colors()['bg']};")
                    return

            # Fallback gradient background
            self._set_gradient_background()

        except Exception as e:
            print(f"Background error: {e}")
            self._set_gradient_background()

    def _set_gradient_background(self):
        """Set professional gradient background"""
        c = self.theme_manager.get_colors()
        self.bg_label.setText("")
        self.bg_label.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {c['bg']},
                    stop:0.3 {c['card_bg']},
                    stop:0.6 {c['header']},
                    stop:1 {c['bg']}
                );
            }}
        """)

    def _fade_in(self):
        """Smooth fade-in animation on open"""
        self.show()
        self.setWindowOpacity(0.0)
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(400)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_animation.start()

    def resizeEvent(self, event):
        """Handle window resize - background scales automatically"""
        super().resizeEvent(event)
        QTimer.singleShot(50, self._load_background)

    def get_modern_stylesheet(self):
        """Modern SaaS Dark Glassmorphism stylesheet"""
        return """
        QMainWindow {
            background: transparent;
        }

        QWidget {
            font-family: 'Segoe UI', 'Arial', sans-serif;
        }

        /* Login Card - Enhanced Glassmorphism */
        QFrame#loginCard {
            background-color: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(148, 163, 184, 0.45);
            border-radius: 20px;
        }

        /* Logo Container */
        QFrame#logoContainer {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #0ea5e9,
                stop:1 #8b5cf6);
            border-radius: 60px;
            border: 2px solid rgba(255, 255, 255, 0.15);
        }

        /* Title - Pure White Bold */
        QLabel#loginTitle {
            font-size: 24pt;
            font-weight: 800;
            color: #0f172a;
            letter-spacing: -0.5px;
        }

        QLabel#loginSubtitle {
            font-size: 9pt;
            color: #475569;
            font-weight: 400;
        }

        /* Input Labels */
        QLabel#inputLabel {
            font-size: 7pt;
            font-weight: 700;
            color: #334155;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        QLineEdit {
            background-color: #f8fafc;
            border: 1px solid #cbd5e1;
            border-radius: 10px;
            padding: 12px 16px;
            color: #0f172a;
            font-size: 10pt;
            font-weight: 500;
            selection-background-color: rgba(37, 99, 235, 0.22);
        }

        QLineEdit:focus {
            border: 2px solid rgba(37, 99, 235, 0.8);
            background-color: #ffffff;
        }

        QLineEdit:hover {
            border: 1px solid rgba(37, 99, 235, 0.5);
            background-color: #ffffff;
        }

        /* Login Button - Gradient Blue to Purple */
        QPushButton#loginButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #0ea5e9,
                stop:1 #8b5cf6);
            border: none;
            border-radius: 12px;
            color: white;
            font-size: 10pt;
            font-weight: 700;
            letter-spacing: 1px;
            padding: 14px;
        }

        QPushButton#loginButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #38bdf8,
                stop:1 #a78bfa);
        }

        QPushButton#loginButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #0284c7,
                stop:1 #7c3aed);
        }

        QPushButton#loginButton:disabled {
            background: rgba(148, 163, 184, 0.3);
            color: rgba(255, 255, 255, 0.5);
        }

        /* Toggle Password Button */
        QPushButton#togglePasswordBtn {
            background-color: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 10px;
            color: rgba(255, 255, 255, 0.75);
            font-size: 13pt;
        }

        QPushButton#togglePasswordBtn:hover {
            background-color: rgba(14, 165, 233, 0.25);
            border: 1px solid rgba(14, 165, 233, 0.6);
            color: #ffffff;
        }

        /* Remember Me Checkbox */
        QCheckBox {
            color: #334155;
            font-size: 9pt;
            spacing: 8px;
        }

        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border-radius: 5px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            background-color: rgba(255, 255, 255, 0.08);
        }

        QCheckBox::indicator:checked {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #0ea5e9,
                stop:1 #8b5cf6);
            border: 1px solid rgba(255, 255, 255, 0.2);
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEgNEw0LjUgNy41TDExIDEiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+PC9zdmc+);
        }

        QCheckBox::indicator:hover {
            border: 1px solid rgba(14, 165, 233, 0.7);
        }

        /* Footer */
        QLabel#footerLabel {
            color: rgba(255, 255, 255, 0.35);
            font-size: 7pt;
        }

        /* Error Label */
        QLabel#errorLabel {
            color: #fecaca;
            font-size: 8pt;
            background-color: rgba(239, 68, 68, 0.15);
            border-radius: 8px;
            padding: 10px 14px;
            border: 1px solid rgba(239, 68, 68, 0.3);
            font-weight: 500;
        }
        """

    def _focus_password(self):
        """Focus password field on Enter"""
        self.password_input.setFocus()

    def _toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_password_btn.setText("🙈")
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_password_btn.setText("👁️")

    def _perform_login(self):
        """Perform login"""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        # Hide error
        self.error_label.hide()

        # Validation
        if not username or not password:
            self._show_error("Please enter both username and password")
            return

        # Disable button during login
        self.login_button.setEnabled(False)
        self.login_button.setText("Signing in...")
        self.username_input.setEnabled(False)
        self.password_input.setEnabled(False)

        # Run authentication in background
        self.run_in_thread(
            self._authenticate,
            self._on_login_result,
            self._on_login_error,
            username, password
        )

    def _authenticate(self, username, password):
        """Authenticate user (background thread)"""
        from controllers.auth_controller import AuthController
        from database.db_connection import DatabaseConnection

        db = DatabaseConnection()
        auth = AuthController(db)
        return auth.login(username, password)

    def _on_login_result(self, result):
        """Handle login result"""
        self._reset_login_state()

        user_data, error = result

        if error:
            self._show_error(error)
            self.password_input.clear()
            self.password_input.setFocus()
        elif user_data:
            # Start session
            from utils.session_manager import get_session
            session = get_session()
            session.login(user_data)

            # Handle "Remember Me"
            if self.remember_checkbox.isChecked():
                print("[INFO] Remember Me: Username will be saved for next login")

            if self.on_login_success:
                self.on_login_success(user_data)

    def _on_login_error(self, error_msg):
        """Handle login error"""
        self._reset_login_state()
        self._show_error(f"Login failed: {error_msg}")
        self.password_input.clear()
        self.password_input.setFocus()

    def _reset_login_state(self):
        """Reset login button state"""
        self.login_button.setEnabled(True)
        self.login_button.setText("SIGN IN")
        self.username_input.setEnabled(True)
        self.password_input.setEnabled(True)

    def _show_error(self, message):
        """Show error message"""
        self.error_label.setText(f"⚠ {message}")
        self.error_label.show()

    def run_in_thread(self, target, success_callback, error_callback, *args, **kwargs):
        """Run task in background thread using WorkerThread from base_window"""
        from views.base_window import WorkerThread
        worker = WorkerThread(target, *args, **kwargs)
        worker.signals.finished.connect(success_callback)
        worker.signals.error.connect(error_callback)
        self._workers.append(worker)
        worker.start()

    def _cleanup_workers(self):
        """Cleanup background workers"""
        from views.base_window import WorkerThread
        for worker in self._workers:
            try:
                if worker.isRunning():
                    worker._active = False
                    worker.wait(3000)
            except RuntimeError:
                pass
        for worker in self._workers:
            try:
                worker.deleteLater()
            except RuntimeError:
                pass
        self._workers.clear()

    def closeEvent(self, event):
        """Cleanup on close"""
        self._cleanup_workers()
        event.accept()
