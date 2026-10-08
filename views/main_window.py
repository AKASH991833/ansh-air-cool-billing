"""
Main Application Window - PySide6 Professional UI
Modern sidebar navigation with stacked widget content area
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QPushButton, QStackedWidget, QScrollArea, QSizePolicy,
    QStatusBar, QMenu, QMessageBox, QGraphicsDropShadowEffect, QSpacerItem,
    QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPixmap, QIcon, QAction, QPalette, QColor, QShortcut, QKeySequence

from utils.unified_theme import UnifiedTheme
from utils.app_settings import get_setting
from views.base_window import BaseView
import os

# TYPE_CHECKING import to avoid circular dependency
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from views.enhanced_dashboard_view import EnhancedDashboardView


class MainWindow(QMainWindow):
    """Main application window with sidebar navigation - Modern Windows 11 Style"""

    logout_requested = Signal()

    def __init__(self, user_data, on_logout=None):
        super().__init__()
        self._destroyed = False
        self.user_data = user_data
        self.on_logout = on_logout
        self.theme_manager = UnifiedTheme()
        self.current_view_index = 0
        from utils.excel_helper import ExcelExporter
        ExcelExporter.CURRENT_USER = user_data.get('full_name', 'User')

        # Set window name and modern styling
        self.setObjectName("mainWindow")
        from utils.app_settings import get_setting
        app_title = get_setting('app_name', 'AC Service Billing')
        self.setWindowTitle(f"{app_title} | {user_data.get('full_name', 'User')}")
        self.setMinimumSize(1280, 720)
        self.resize(1440, 800)

        # Apply unified cyan/blue theme stylesheet
        self.setStyleSheet(self.theme_manager.get_main_stylesheet())

        # Enable acrylic-like effect (Windows 11 style)
        self._setup_modern_window_effects()

        # Center window
        self._center_window()

        # Setup UI
        self._setup_ui()

        # Show dashboard by default
        self._show_dashboard()

        # CRITICAL FIX: Set focus to sidebar after a short delay to ensure buttons are ready
        QTimer.singleShot(100, self._set_initial_focus)

        # Performance Pre-Warming: Pre-instantiate heavy views during idle time
        QTimer.singleShot(250, self._schedule_view_prewarming)
    
    def _set_initial_focus(self):
        """Set initial focus to first sidebar button"""
        if self.sidebar_buttons:
            # Focus the dashboard button by default
            dashboard_btn = self.sidebar_buttons.get("dashboard")
            if dashboard_btn:
                dashboard_btn.setFocus()
    
    def _center_window(self):
        """Center window on screen"""
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen is None:
            self.move(100, 100)
            return

        geometry = screen.availableGeometry()
        x = (geometry.width() - self.width()) // 2
        y = (geometry.height() - self.height()) // 2
        self.move(x, y)

    def _setup_modern_window_effects(self):
        """Setup modern window effects (shadows, transparency, etc.)."""
        colors = self.theme_manager.get_colors()
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(colors['bg']))
        self.setPalette(palette)
        # NOTE: QGraphicsDropShadowEffect on the root window causes a full-window
        # repaint on EVERY cursor move / mouse event — major performance cost.
        # Removed to keep the UI smooth and responsive.

    def _setup_ui(self):
        """Setup main application UI"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        self._create_header(main_layout)

        # Content area (sidebar + main content)
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        main_layout.addWidget(content_frame, 1)

        content_layout = QHBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Sidebar
        self._create_sidebar(content_layout)

        # Main content area
        self._create_content_area(content_layout)

        # Status bar
        self._create_status_bar()

        # Setup keyboard shortcuts
        self._setup_shortcuts()

        # Setup global event bus for real-time updates
        self._setup_event_bus()
    
    def _create_header(self, parent_layout):
        """Create application header"""
        colors = self.theme_manager.get_colors()
        
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_frame.setFixedHeight(70)
        header_frame.setStyleSheet(f"""
            QFrame#headerFrame {{
                background-color: {colors['card_bg']};
                border: 1px solid {colors['border']};
                border-bottom: 1px solid {colors['border']};
            }}
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 10, 20, 10)
        header_layout.setSpacing(20)
        
        # Logo and title (left)
        logo_layout = QHBoxLayout()
        logo_layout.setSpacing(12)
        
        try:
            from utils.logo_helper import get_logo_path
            from PySide6.QtGui import QPixmap
            from PySide6.QtCore import Qt
            import os
            logo_path = get_logo_path()
            if logo_path and os.path.exists(logo_path):
                logo_label = QLabel()
                pixmap = QPixmap(logo_path).scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                                    Qt.TransformationMode.SmoothTransformation)
                logo_label.setPixmap(pixmap)
                logo_layout.addWidget(logo_label)
            else:
                logo_label = QLabel("❄️")
                logo_label.setFont(QFont('Segoe UI', 20))
                logo_layout.addWidget(logo_label)
        except Exception:
            logo_label = QLabel("❄️")
            logo_label.setFont(QFont('Segoe UI', 20))
            logo_layout.addWidget(logo_label)
        
        app_name = get_setting('app_name', 'AC Service Billing')
        self.header_title_label = QLabel(app_name)
        self.header_title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 18pt;
                font-weight: bold;
                color: {colors['fg']};
            }}
        """)
        logo_layout.addWidget(self.header_title_label)
        header_layout.addLayout(logo_layout)

        # REMOVED: Top navigation buttons (now using sidebar only)
        # Navigation moved to sidebar for cleaner modern UI

        header_layout.addStretch()

        # Quick Customer Search
        from utils.search_widget import QuickCustomerSearch
        self.quick_search = QuickCustomerSearch()
        self.quick_search.customer_selected.connect(self._on_quick_customer_selected)
        header_layout.addWidget(self.quick_search)

        # Standout Universal "+ New Invoice" Button (Accessible anywhere)
        self.top_new_invoice_btn = QPushButton("➕  New Invoice")
        self.top_new_invoice_btn.setObjectName("newInvoiceHeaderBtn")
        self.top_new_invoice_btn.setFixedHeight(36)
        self.top_new_invoice_btn.setCursor(Qt.PointingHandCursor)
        self.top_new_invoice_btn.setToolTip("Create a new invoice immediately (Ctrl+N)")
        self.top_new_invoice_btn.clicked.connect(lambda: self._show_invoice())
        header_layout.addWidget(self.top_new_invoice_btn)

        # Enterprise Privacy Shield Toggle Button (Eye icon)
        from utils.privacy_manager import get_privacy_manager
        self.privacy_mgr = get_privacy_manager()
        self.btn_privacy_toggle = QPushButton()
        self.btn_privacy_toggle.setObjectName("privacyToggleBtn")
        self.btn_privacy_toggle.setFixedHeight(36)
        self.btn_privacy_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_privacy_toggle.clicked.connect(self._toggle_privacy_mode)
        self._update_privacy_button_ui()
        header_layout.addWidget(self.btn_privacy_toggle)

        header_layout.addSpacing(15)

        # Profile section (right)
        profile_layout = QHBoxLayout()
        profile_layout.setSpacing(15)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setObjectName("iconButton")
        refresh_btn.setStyleSheet(f"""
            QPushButton#iconButton {{
                background-color: {colors['hover']};
                color: {colors['fg']};
                border: 1px solid {colors['border']};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 9pt;
            }}
            QPushButton#iconButton:hover {{
                background-color: {colors['primary']}15;
                border-color: {colors['primary']};
            }}
        """)
        refresh_btn.clicked.connect(self._refresh_current_view)
        profile_layout.addWidget(refresh_btn)

        # Welcome label
        first_name = self.user_data.get('full_name', 'User').split()[0]
        welcome_label = QLabel(f"Welcome, {first_name}")
        welcome_label.setStyleSheet(f"color: {colors['fg']}; font-size: 10pt;")
        profile_layout.addWidget(welcome_label)

        # Profile menu button
        profile_btn = QPushButton()
        profile_btn.setObjectName("profileBtn")
        profile_btn.setFixedSize(42, 42)
        profile_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # Create icon label with emoji (avatar glyph for the profile menu)
        icon_label = QLabel("👤")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(f"color: {colors['fg']}; font-size: 16pt;")

        # Layout for button
        btn_layout = QVBoxLayout(profile_btn)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addWidget(icon_label)

        profile_btn.setStyleSheet(f"""
            QPushButton#profileBtn {{
                background-color: {colors['hover']};
                border: 1px solid {colors['border']};
                border-radius: 21px;
                padding: 0px;
            }}
            QPushButton#profileBtn:hover {{
                background-color: {colors['primary']}15;
                border-color: {colors['primary']};
            }}
            QPushButton#profileBtn:pressed {{
                background-color: {colors['primary']}25;
            }}
        """)
        
        # Profile menu
        self.profile_menu = QMenu(self)
        self.profile_menu.setStyleSheet("")

        profile_action = QAction("Profile Settings", self)
        profile_action.triggered.connect(self._show_profile_settings)
        self.profile_menu.addAction(profile_action)

        password_action = QAction("Change Password", self)
        password_action.triggered.connect(self._show_change_password)
        self.profile_menu.addAction(password_action)

        self.profile_menu.addSeparator()

        logout_action = QAction("🚪 Logout", self)
        logout_action.triggered.connect(self._confirm_logout)
        self.profile_menu.addAction(logout_action)

        profile_btn.setMenu(self.profile_menu)
        profile_layout.addWidget(profile_btn)
        
        header_layout.addLayout(profile_layout)
        
        parent_layout.addWidget(header_frame)
    
    def _create_sidebar(self, parent_layout):
        """Create sidebar navigation - enterprise style with icon + text, active indicator"""
        from utils.app_settings import get_setting
        colors = self.theme_manager.get_colors()

        self.sidebar_frame = QFrame()
        self.sidebar_frame.setObjectName("sidebarFrame")
        self.sidebar_frame.setFixedWidth(230)
        self.sidebar_frame.setStyleSheet(f"""
            QFrame#sidebarFrame {{
                background-color: {colors['sidebar']};
                border: none;
                border-right: 1px solid {colors['border']};
            }}
        """)
        self.sidebar_frame.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        sidebar_layout = QVBoxLayout(self.sidebar_frame)
        sidebar_layout.setContentsMargins(8, 16, 8, 16)
        sidebar_layout.setSpacing(2)

        # ---- App name / logo at top of sidebar ----
        top_wrapper = QFrame()
        top_wrapper.setObjectName("sidebarTop")
        top_layout = QVBoxLayout(top_wrapper)
        top_layout.setContentsMargins(8, 10, 8, 8)
        top_layout.setSpacing(4)
        top_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        app_name = get_setting('app_name', 'AC Service Billing')
        title_label = QLabel(app_name)
        title_label.setStyleSheet(f"""
            font-size: 11pt;
            font-weight: 700;
            color: {colors['fg']};
            font-family: 'Inter','Segoe UI',sans-serif;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(title_label)

        subtitle = QLabel("Billing System")
        subtitle.setStyleSheet(f"""
            font-size: 8pt;
            color: {colors['muted']};
            font-family: 'Inter','Segoe UI',sans-serif;
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(subtitle)

        sidebar_layout.addWidget(top_wrapper)

        # ---- Separator ----
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['border']};
                height: 1px;
            }}
        """)
        sep.setFixedHeight(1)
        sidebar_layout.addWidget(sep)

        # ---- Navigation buttons ----
        self.sidebar_buttons = {}
        self.current_button = None

        nav_items = [
            ("📊", "Dashboard", "dashboard"),
            ("📋", "Manage Invoices", "invoice management"),
            ("📝", "AMC Contracts", "amc"),
            ("👥", "Customers", "customers"),
            ("🔧", "Technicians", "technicians"),
            ("📋", "Daily Logs", "daily logs"),
            ("📦", "Inventory", "inventory"),
            ("📊", "Reports", "reports"),
            ("🗑️", "Deleted Items", "deleted"),
            ("⚙️", "Settings", "settings"),
        ]

        for icon, text, view_name in nav_items:
            btn = QPushButton()
            btn.setObjectName("sidebarButton")
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setMinimumHeight(40)
            btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            btn.setAutoDefault(False)
            btn.setDefault(False)
            btn.setProperty("view_name", view_name)

            # Icon + text in a horizontal layout inside button
            btn_layout = QHBoxLayout(btn)
            btn_layout.setContentsMargins(10, 0, 10, 0)
            btn_layout.setSpacing(10)
            btn_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

            icon_lbl = QLabel(icon)
            icon_lbl.setFixedSize(24, 24)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_lbl.setProperty("navIcon", True)
            btn_layout.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)

            text_lbl = QLabel(text)
            text_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            text_lbl.setProperty("navText", True)
            btn_layout.addWidget(text_lbl)

            btn_layout.addStretch()

            btn.pressed.connect(self._on_sidebar_button_pressed)
            sidebar_layout.addWidget(btn)
            self.sidebar_buttons[text.lower()] = btn

        sidebar_layout.addStretch()

        # ---- Bottom: version + user ----
        bottom_sep = QFrame()
        bottom_sep.setFrameShape(QFrame.Shape.HLine)
        bottom_sep.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['border']};
                height: 1px;
            }}
        """)
        bottom_sep.setFixedHeight(1)
        sidebar_layout.addWidget(bottom_sep)

        version_label = QLabel(get_setting('app_name', 'AC Service Billing') + "  v2.0")
        version_label.setStyleSheet(f"""
            color: {colors['muted']};
            font-size: 8pt;
            font-family: 'Inter','Segoe UI',sans-serif;
        """)
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(version_label)

        parent_layout.addWidget(self.sidebar_frame)

    def _on_sidebar_button_pressed(self):
        """Handle sidebar button pressed - use pressed instead of clicked for immediate response"""
        sender = self.sender()
        if sender:
            view_name = sender.property("view_name")
            if view_name:
                # Ensure button stays checked (autoExclusive handles the rest)
                sender.setChecked(True)
                self.current_button = sender
                self._switch_to_view(view_name)
    
    def _create_content_area(self, parent_layout):
        """Create main content area with stacked widget"""
        # Content frame
        content_frame = QFrame()
        content_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme_manager.get_colors()['bg']};
            }}
        """)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Stacked widget for views
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color: transparent;")
        content_layout.addWidget(self.stacked_widget)

        # O(1) view registry: class_name -> QWidget instance
        # Populated on first navigation to each view; avoids O(n) linear scan.
        self._view_registry: dict = {}

        parent_layout.addWidget(content_frame, 1)
    
    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.status_bar.setObjectName("statusBarFrame")
        self.status_bar.setStyleSheet(f"""
            QStatusBar#statusBarFrame {{
                background-color: {self.theme_manager.get_colors()['card_bg']};
                color: {self.theme_manager.get_colors()['fg']};
                border-top: 1px solid {self.theme_manager.get_colors()['border']};
            }}
        """)
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"color: {self.theme_manager.get_colors()['fg']}; font-weight: 600;")
        self.status_bar.addWidget(self.status_label)

        self.status_bar.addPermanentWidget(db_label := QLabel("● Database Connected"))
        db_label.setStyleSheet(f"color: {self.theme_manager.get_colors()['success']}; font-weight: bold;")
    
    def _clear_stacked_widget(self):
        """Clear all widgets from stacked widget"""
        while self.stacked_widget.count():
            widget = self.stacked_widget.widget(0)
            self.stacked_widget.removeWidget(widget)
            widget.deleteLater()
    
    # ── Fast O(1) view registry helper ──────────────────────────────────────
    def _get_or_create_view(self, class_name: str, factory, nav_key: str, status_text: str):
        """Switch to an existing view or create it, using O(1) dict lookup."""
        existing = self._view_registry.get(class_name)
        if existing is not None:
            self.stacked_widget.setCurrentWidget(existing)
            self._update_navigation(nav_key)
            self.status_label.setText(status_text)
            existing.raise_()
            if getattr(existing, '_needs_refresh', False):
                existing._needs_refresh = False
                if hasattr(existing, 'refresh_data'):
                    existing.refresh_data()
                if hasattr(existing, 'load_master_data'):
                    existing.load_master_data()
            return existing
        # First visit — instantiate and register
        view = factory()
        self._view_registry[class_name] = view
        self.stacked_widget.addWidget(view)
        self.stacked_widget.setCurrentWidget(view)
        self._update_navigation(nav_key)
        self.status_label.setText(status_text)
        view.raise_()
        return view

    # ── Background View Pre-Warming ──────────────────────────────────────────
    def _schedule_view_prewarming(self):
        """Pre-warm views progressively during idle periods.
        This completely eliminates first-click delays on all sidebar tabs."""
        if not self.isVisible() or getattr(self, '_destroyed', False):
            return
        views_to_warm = [
            ("InvoiceManagementView", self._warm_invoice_management),
            ("CustomerView", self._warm_customers),
            ("SettingsView", self._warm_settings),
            ("AMCView", self._warm_amc),
            ("InventoryView", self._warm_inventory),
            ("TechnicianView", self._warm_technicians),
            ("DailyLogView", self._warm_daily_logs),
            ("ReportView", self._warm_reports),
        ]
        delay = 200
        for class_name, warmer_fn in views_to_warm:
            QTimer.singleShot(delay, warmer_fn)
            delay += 200

    def _warm_invoice_management(self):
        if not self.isVisible() or getattr(self, '_destroyed', False):
            return
        if 'InvoiceManagementView' not in self._view_registry:
            try:
                from views.invoice_management_view import InvoiceManagementView
                view = InvoiceManagementView()
                self._view_registry['InvoiceManagementView'] = view
                self.stacked_widget.addWidget(view)
            except Exception:
                pass

    def _warm_customers(self):
        if not self.isVisible() or getattr(self, '_destroyed', False):
            return
        if 'CustomerView' not in self._view_registry:
            try:
                from views.customer_view import CustomerView
                view = CustomerView()
                self._view_registry['CustomerView'] = view
                self.stacked_widget.addWidget(view)
            except Exception:
                pass

    def _warm_settings(self):
        if not self.isVisible() or getattr(self, '_destroyed', False):
            return
        if 'SettingsView' not in self._view_registry:
            try:
                from views.settings_view import SettingsView
                view = SettingsView(self.user_data)
                view.settings_saved.connect(self._on_settings_saved)
                self._view_registry['SettingsView'] = view
                self.stacked_widget.addWidget(view)
            except Exception:
                pass

    def _warm_amc(self):
        if not self.isVisible() or getattr(self, '_destroyed', False):
            return
        if 'AMCView' not in self._view_registry:
            try:
                from views.amc_view import AMCView
                view = AMCView()
                self._view_registry['AMCView'] = view
                self.stacked_widget.addWidget(view)
            except Exception:
                pass

    def _warm_inventory(self):
        if not self.isVisible() or getattr(self, '_destroyed', False):
            return
        if 'InventoryView' not in self._view_registry:
            try:
                from views.inventory_view import InventoryView
                view = InventoryView()
                self._view_registry['InventoryView'] = view
                self.stacked_widget.addWidget(view)
            except Exception:
                pass

    def _warm_technicians(self):
        if not self.isVisible() or getattr(self, '_destroyed', False):
            return
        if 'TechnicianView' not in self._view_registry:
            try:
                from views.technician_view import TechnicianView
                view = TechnicianView()
                self._view_registry['TechnicianView'] = view
                self.stacked_widget.addWidget(view)
            except Exception:
                pass

    def _warm_daily_logs(self):
        if not self.isVisible() or getattr(self, '_destroyed', False):
            return
        if 'DailyLogView' not in self._view_registry:
            try:
                from views.daily_log_view import DailyLogView
                view = DailyLogView()
                self._view_registry['DailyLogView'] = view
                self.stacked_widget.addWidget(view)
            except Exception:
                pass

    def _warm_reports(self):
        if not self.isVisible() or getattr(self, '_destroyed', False):
            return
        if 'ReportView' not in self._view_registry:
            try:
                from views.report_view import ReportView
                view = ReportView()
                self._view_registry['ReportView'] = view
                self.stacked_widget.addWidget(view)
            except Exception:
                pass

    def _show_dashboard(self):
        """Show enhanced dashboard view with clickable cards."""
        existing = self._view_registry.get('EnhancedDashboardView')
        if existing is not None:
            self.stacked_widget.setCurrentWidget(existing)
            existing.refresh_data()
            self._update_navigation('dashboard')
            self.status_label.setText('Dashboard')
            existing.raise_()
            return

        from database.db_connection import DatabaseConnection
        from controllers.dashboard_controller import DashboardController
        from views.enhanced_dashboard_view import EnhancedDashboardView
        db = DatabaseConnection()
        controller = DashboardController(db)
        view = EnhancedDashboardView(self.user_data, db, controller)
        self._view_registry['EnhancedDashboardView'] = view
        self.stacked_widget.addWidget(view)
        self.stacked_widget.setCurrentWidget(view)
        self._update_navigation('dashboard')
        self.status_label.setText('Dashboard')
        view.raise_()

    def _show_invoice(self, customer_data=None):
        """Show invoice view and optionally pre-fill customer data."""
        def _factory():
            from views.invoice_view import InvoiceView
            return InvoiceView()
        view = self._get_or_create_view('InvoiceView', _factory, 'invoice', 'New Invoice')
        if customer_data and hasattr(view, 'set_customer_data'):
            view.set_customer_data(customer_data)

    def _show_amc(self):
        def _f():
            from views.amc_view import AMCView
            return AMCView()
        self._get_or_create_view('AMCView', _f, 'amc', 'AMC Contracts')

    def _show_customers(self):
        def _f():
            from views.customer_view import CustomerView
            return CustomerView()
        self._get_or_create_view('CustomerView', _f, 'customers', 'Customer Management')

    def _show_technicians(self):
        def _f():
            from views.technician_view import TechnicianView
            return TechnicianView()
        self._get_or_create_view('TechnicianView', _f, 'technicians', 'Technician Management')

    def _show_daily_logs(self):
        def _f():
            from views.daily_log_view import DailyLogView
            return DailyLogView()
        self._get_or_create_view('DailyLogView', _f, 'daily logs', 'Daily Logs')

    def _show_deleted_items(self):
        def _f():
            from views.deleted_items_view import DeletedItemsView
            return DeletedItemsView()
        v = self._get_or_create_view('DeletedItemsView', _f, 'deleted', 'Deleted Items')
        if hasattr(v, 'refresh_data'):
            v.refresh_data()

    def _show_inventory(self):
        def _f():
            from views.inventory_view import InventoryView
            return InventoryView()
        self._get_or_create_view('InventoryView', _f, 'inventory', 'Inventory Management')

    def _show_reports(self):
        def _f():
            from views.report_view import ReportView
            return ReportView()
        self._get_or_create_view('ReportView', _f, 'reports', 'Profit & Loss Reports')

    def _switch_to_view(self, view_name):
        """Helper to switch views with proper cleanup"""
        current_widget = self.stacked_widget.currentWidget()

        # Cleanup view timers if active (Dashboard, OnlineRequestView, etc.)
        if current_widget and hasattr(current_widget, 'cleanup'):
            try:
                current_widget.cleanup()
            except Exception as e:
                print(f"[WARN] Cleanup failed: {e}")

        # Now call the appropriate show method based on view name
        if view_name == "dashboard":
            self._show_dashboard()
        elif view_name == "invoice":
            self._show_invoice()
        elif view_name == "invoice management":
            self._show_invoice_management()
        elif view_name == "amc":
            self._show_amc()
        elif view_name == "customers":
            self._show_customers()
        elif view_name == "technicians":
            self._show_technicians()
        elif view_name == "daily logs":
            self._show_daily_logs()
        elif view_name == "inventory":
            self._show_inventory()
        elif view_name == "reports":
            self._show_reports()
        elif view_name == "deleted":
            self._show_deleted_items()
        elif view_name == "settings":
            self._show_settings()

    def _show_settings(self):
        def _f():
            from views.settings_view import SettingsView
            view = SettingsView(self.user_data)
            view.settings_saved.connect(self._on_settings_saved)
            return view
        self._get_or_create_view('SettingsView', _f, 'settings', 'Settings')

    def _show_invoice_management(self):
        def _f():
            from views.invoice_management_view import InvoiceManagementView
            return InvoiceManagementView()
        self._get_or_create_view('InvoiceManagementView', _f, 'invoice management', 'Manage Invoices')

    def _show_profile_settings(self):
        def _f():
            from views.settings_view import ProfileSettingsView
            return ProfileSettingsView(self.user_data)
        self._get_or_create_view('ProfileSettingsView', _f, 'settings', 'Profile Settings')
    
    def _on_quick_customer_selected(self, customer):
        """Handle quick customer search selection"""
        customer_id = customer.get('id')
        self.status_label.setText(f"Customer: {customer.get('name')} - {customer.get('mobile')}")

        # Ask what to do
        from PySide6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle("Customer Found")
        msg.setText(f"{customer.get('name')}\n{customer.get('mobile')}")
        msg.setInformativeText(f"Total Services: {customer.get('total_services', 0)}")
        new_invoice_btn = msg.addButton("New Invoice", QMessageBox.ButtonRole.AcceptRole)
        view_history_btn = msg.addButton("View History", QMessageBox.ButtonRole.ActionRole)
        msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        msg.exec()

        if msg.clickedButton() == new_invoice_btn:
            self._show_invoice(customer)
        elif msg.clickedButton() == view_history_btn:
            self._show_customer_history(customer)

    def _show_customer_history(self, customer):
        """Navigate to customer view and show specific customer"""
        self._switch_to_view("customers")
        for i in range(self.stacked_widget.count()):
            widget = self.stacked_widget.widget(i)
            if widget and hasattr(widget, 'show_customer_detail'):
                widget.show_customer_detail(customer.get('id'))
                break

    def _show_change_password(self):
        """Show change password dialog"""
        from views.settings_view import ChangePasswordDialog
        dialog = ChangePasswordDialog(self.user_data.get('id'), self)
        dialog.exec()

    def _refresh_current_view(self):
        """Refresh current view and apply theme"""
        current_widget = self.stacked_widget.currentWidget()
        if current_widget:
            # Call update_theme_colors if method exists (for InvoiceView and AMCView)
            if hasattr(current_widget, 'update_theme_colors'):
                current_widget.update_theme_colors()
                self.status_label.setText(f"Theme updated in {type(current_widget).__name__}")
            elif hasattr(current_widget, 'theme_manager'):
                # Apply theme to current widget
                colors = current_widget.theme_manager.get_colors()
                current_widget.setStyleSheet(
                    current_widget.theme_manager.get_main_stylesheet()
                )
                # Refresh data if method exists
                if hasattr(current_widget, 'refresh_data'):
                    current_widget.refresh_data()
                self.status_label.setText(f"Theme applied to {type(current_widget).__name__}")
            else:
                self.status_label.setText("View doesn't support theme refresh")
        else:
            self.status_label.setText("No active view to refresh")

    def _on_settings_saved(self):
        """Handle settings saved event - refresh dashboard data and update user_data"""
        print(f"[DEBUG] Settings saved signal received - refreshing dashboard")

        # CRITICAL: Refresh user_data from session manager to get latest profile data
        from utils.session_manager import get_session
        session = get_session()
        if session and session.get_current_user():
            updated_user = session.get_current_user()
            self.user_data = updated_user.copy()

        # REFRESH THEME IMMEDIATELY
        self.theme_manager.load_theme_mode()
        self.setStyleSheet(self.theme_manager.get_main_stylesheet())
        self.theme_manager.apply_palette(self)
        for i in range(self.stacked_widget.count()):
            widget = self.stacked_widget.widget(i)
            if widget and hasattr(widget, 'update_theme_colors'):
                widget.update_theme_colors()

        # Reload all UI settings from DB in real-time
        self.reload_ui_settings()

        # Refresh shortcuts
        self._setup_shortcuts()
        if hasattr(self, 'shortcut_mgr'):
            self.shortcut_mgr.apply_shortcuts_to_window(self, self._on_shortcut_triggered)

        self.status_label.setText("Settings saved - UI refreshed")

    def reload_ui_settings(self):
        """Reload UI settings from DB and update all open views in real-time"""
        app_name = get_setting('app_name', 'AC Service Billing')
        first_name = self.user_data.get('full_name', 'User').split()[0]
        self.setWindowTitle(f"{app_name} - Billing System | {first_name}")
        if hasattr(self, 'header_title_label'):
            self.header_title_label.setText(app_name)
        current = self.stacked_widget.currentWidget()
        for i in range(self.stacked_widget.count()):
            widget = self.stacked_widget.widget(i)
            if widget and hasattr(widget, 'reload_ui_settings'):
                widget.reload_ui_settings()
            if widget and widget is not current:
                setattr(widget, '_needs_refresh', True)

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts from ShortcutManager"""
        from utils.shortcut_manager import ShortcutManager, DEFAULT_SHORTCUTS
        from PySide6.QtGui import QShortcut, QKeySequence
        self.shortcut_mgr = ShortcutManager()
        self.shortcut_mgr.apply_shortcuts_to_window(self, self._on_shortcut_triggered)

        # Quick Privacy Shield Shortcut (Ctrl+H / Ctrl+Shift+P)
        self.sc_privacy = QShortcut(QKeySequence("Ctrl+H"), self)
        self.sc_privacy.activated.connect(self._toggle_privacy_mode)
        self.sc_privacy2 = QShortcut(QKeySequence("Ctrl+Shift+P"), self)
        self.sc_privacy2.activated.connect(self._toggle_privacy_mode)

    def _on_shortcut_triggered(self, shortcut_id, action_name):
        """Handle shortcut-triggered navigation"""
        nav_map = {
            'new_invoice': 'invoice',
            'dashboard': 'dashboard',
            'customers': 'customers',
            'settings': 'settings',
            'daily_logs': 'daily logs',
            'technicians': 'technicians',
            'invoice_mgmt': 'invoice management',
            'amc': 'amc',
        }
        if shortcut_id == 'search':
            self._focus_search()
        elif shortcut_id == 'refresh':
            self._refresh_current_view()
        elif shortcut_id == 'print':
            self._trigger_print()
        elif shortcut_id in nav_map:
            self._switch_to_view(nav_map[shortcut_id])

    def _trigger_print(self):
        """Try to print current view"""
        from PySide6.QtWidgets import QMessageBox
        current = self.stacked_widget.currentWidget()
        if hasattr(current, 'print_invoice') and callable(current.print_invoice):
            current.print_invoice()
        elif hasattr(current, 'print_invoices') and callable(current.print_invoices):
            current.print_invoices()
        elif hasattr(current, '_save_and_print_invoice') and callable(current._save_and_print_invoice):
            current._save_and_print_invoice()
        else:
            QMessageBox.information(self, "Info", "Print not available for current view")

    def _focus_search(self):
        """Focus search input in current view"""
        current = self.stacked_widget.currentWidget()
        if current:
            search_cls = self._get_search_widget_classes()
            for child in current.findChildren(search_cls):
                child.setFocus()
                child.selectAll()
                break

    @staticmethod
    def _get_search_widget_classes():
        from PySide6.QtWidgets import QLineEdit
        return QLineEdit

    def _toggle_privacy_mode(self):
        """Toggle privacy mode globally."""
        from utils.privacy_manager import get_privacy_manager
        new_state = get_privacy_manager().toggle_privacy()
        self._update_privacy_button_ui()

    def _update_privacy_button_ui(self):
        """Update the appearance of the Privacy Shield button based on state."""
        if not hasattr(self, 'btn_privacy_toggle') or self.btn_privacy_toggle is None:
            return
        from utils.privacy_manager import get_privacy_manager
        colors = self.theme_manager.get_colors()
        is_active = get_privacy_manager().is_privacy_enabled()

        if is_active:
            self.btn_privacy_toggle.setText("🔒 Privacy ON")
            self.btn_privacy_toggle.setToolTip("Privacy Shield ACTIVE (Ctrl+H)\nFinancial amounts are masked with '••••••'. Click to show.")
            self.btn_privacy_toggle.setStyleSheet(f"""
                QPushButton#privacyToggleBtn {{
                    background-color: #dc262618;
                    color: #dc2626;
                    border: 1.5px solid #dc2626;
                    border-radius: 8px;
                    padding: 0 12px;
                    font-size: 9pt;
                    font-weight: 700;
                }}
                QPushButton#privacyToggleBtn:hover {{
                    background-color: #dc262628;
                }}
            """)
        else:
            self.btn_privacy_toggle.setText("👁️ Privacy Shield")
            self.btn_privacy_toggle.setToolTip("Toggle Privacy Shield (Ctrl+H)\nMask income & financial amounts when opening in front of others.")
            self.btn_privacy_toggle.setStyleSheet(f"""
                QPushButton#privacyToggleBtn {{
                    background-color: {colors['hover']};
                    color: {colors['fg']};
                    border: 1px solid {colors['border']};
                    border-radius: 8px;
                    padding: 0 12px;
                    font-size: 9pt;
                    font-weight: 600;
                }}
                QPushButton#privacyToggleBtn:hover {{
                    background-color: {colors['primary']}15;
                    border-color: {colors['primary']};
                    color: {colors['primary']};
                }}
            """)

    def _setup_event_bus(self):
        """Setup global event bus for real-time updates across all views"""
        from utils.event_bus import get_event_bus
        
        self.event_bus = get_event_bus()
        
        # Connect event bus signals to refresh handlers
        self.event_bus.settings_updated.connect(self._on_global_settings_updated)
        self.event_bus.shop_details_updated.connect(self._on_global_shop_updated)
        self.event_bus.user_profile_updated.connect(self._on_global_profile_updated)
        self.event_bus.master_data_updated.connect(self._on_global_master_data_updated)
        self.event_bus.privacy_mode_toggled.connect(lambda enabled: self._update_privacy_button_ui())
        
        print("[EVENT_BUS] Global event handlers connected")

    def _on_global_settings_updated(self, settings_data):
        """Handle global settings update - refresh all affected views"""
        print(f"[EVENT_BUS] Settings updated: {settings_data}")
        self.reload_ui_settings()

    def _on_global_shop_updated(self, shop_data):
        """Handle shop details update - refresh invoice and other views"""
        print(f"[EVENT_BUS] Shop details updated: {shop_data}")
        self.reload_ui_settings()

    def _on_global_profile_updated(self, user_data):
        """Handle user profile update - update UI"""
        print(f"[EVENT_BUS] User profile updated: {user_data}")
        # Update window title
        first_name = user_data.get('full_name', 'User').split()[0]
        app_name = get_setting('app_name', 'AC Service Billing')
        self.setWindowTitle(f"{app_name} - Billing System | {first_name}")
        # Update welcome label
        header = self.findChild(QFrame, "headerFrame")
        if header:
            for widget in header.findChildren(QLabel):
                if widget.text().startswith("Welcome,"):
                    widget.setText(f"Welcome, {first_name}")
                    break

    def _on_global_master_data_updated(self, data_type):
        """Handle master data update - refresh invoice and active views smoothly"""
        print(f"[EVENT_BUS] Master data updated: {data_type}")
        current_widget = self.stacked_widget.currentWidget()
        for i in range(self.stacked_widget.count()):
            widget = self.stacked_widget.widget(i)
            if widget:
                if widget is current_widget:
                    if hasattr(widget, 'load_master_data'):
                        widget.load_master_data()
                    elif hasattr(widget, 'refresh_data'):
                        widget.refresh_data()
                else:
                    setattr(widget, '_needs_refresh', True)
        self.status_label.setText(f"Master data ({data_type}) updated")

    def _refresh_all_views(self):
        """Refresh active view immediately and mark other views for lazy refresh"""
        current_widget = self.stacked_widget.currentWidget()
        if current_widget and hasattr(current_widget, 'refresh_data'):
            current_widget.refresh_data()
        for i in range(self.stacked_widget.count()):
            widget = self.stacked_widget.widget(i)
            if widget and widget is not current_widget:
                setattr(widget, '_needs_refresh', True)
        self.status_label.setText("Data refreshed")
    
    def _confirm_logout(self):
        """Confirm and perform logout"""
        from PySide6.QtWidgets import QMessageBox
        
        result = QMessageBox.question(
            self, "Logout",
            "Are you sure you want to logout?\n\nAll unsaved changes will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            # Clear session
            from utils.session_manager import logout_user
            logout_user()
            
            print("[INFO] User logged out successfully")
            
            if self.on_logout:
                self.on_logout()
            self.logout_requested.emit()
    
    def _update_navigation(self, view_name):
        """Update navigation button states"""
        target = view_name.lower()
        if target == "invoice":
            target = "manage invoices"
        for name, btn in self.sidebar_buttons.items():
            btn.setChecked(name == target)

    def _cleanup_view(self, widget):
        """Properly cleanup a view widget to prevent memory leaks"""
        if widget is None:
            return
        
        # Cleanup workers if present
        if hasattr(widget, '_cleanup_workers'):
            try:
                widget._cleanup_workers()
            except Exception as e:
                print(f"[WARN] Worker cleanup failed: {e}")
        
        # Cleanup timers if present
        if hasattr(widget, '_timers'):
            for timer in widget._timers:
                try:
                    timer.stop()
                    timer.deleteLater()
                except Exception as e:
                    print(f"[WARN] Timer cleanup failed: {e}")
        
        # Disconnect signals to prevent dangling references
        try:
            from PySide6.QtCore import QObject
            for child in widget.findChildren(QObject):
                try:
                    child.deleteLater()
                except Exception:
                    pass
        except Exception as e:
            print(f"[WARN] Signal cleanup failed: {e}")
        
        # Remove from parent and delete
        try:
            widget.deleteLater()
        except Exception as e:
            print(f"[WARN] Widget deletion failed: {e}")

    def closeEvent(self, event):
        """Handle application close - cleanup all views to prevent memory leaks"""
        self._destroyed = True
        print("[INFO] Application closing, cleaning up resources...")
        
        # Clear stacked widget and properly cleanup all views
        while self.stacked_widget.count():
            widget = self.stacked_widget.currentWidget()
            if widget:
                self.stacked_widget.removeWidget(widget)
                self._cleanup_view(widget)
        
        # Clear sidebar button references
        if hasattr(self, 'sidebar_buttons'):
            for btn in self.sidebar_buttons.values():
                try:
                    btn.deleteLater()
                except Exception:
                    pass
            self.sidebar_buttons.clear()
        
        # Clear other references
        if hasattr(self, 'profile_menu'):
            try:
                self.profile_menu.clear()
                self.profile_menu.deleteLater()
            except Exception:
                pass
        
        # Force garbage collection
        import gc
        gc.collect()
        
        print("[INFO] Cleanup completed, closing application")
        super().closeEvent(event)
