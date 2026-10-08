"""
Technician View - PySide6 Technician Management
Enterprise workforce management dashboard with performance tracking
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea,
    QSizePolicy, QSplitter, QMessageBox, QFormLayout, QComboBox,
    QTextEdit, QGroupBox, QDateEdit, QDialog, QDialogButtonBox,
    QGridLayout, QGraphicsDropShadowEffect, QSpacerItem, QFileDialog
)
from PySide6.QtCore import Qt, QDate, QPropertyAnimation, QEasingCurve, Property, QUrl, QTimer
from PySide6.QtGui import QFont, QColor, QPixmap, QDesktopServices
from datetime import datetime, timedelta

from utils.unified_theme import UnifiedTheme
from views.base_window import BaseView
from utils.formatters import Formatters
import os

CHEVRON_ICON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "icons", "chevron_down.png"
).replace("\\", "/")

FONT_FAMILY = "'Inter', 'Segoe UI', sans-serif"

# Pure White Enterprise Design Tokens (Matching Customer Section)
ENTERPRISE_COLORS = {
    'bg': '#f8fafc',
    'card': '#ffffff',
    'card_hover': '#f8fafc',
    'primary': '#2563eb',
    'primary_hover': '#1d4ed8',
    'primary_light': '#eff6ff',
    'primary_border': '#bfdbfe',
    'success': '#059669',
    'success_light': '#ecfdf5',
    'success_border': '#a7f3d0',
    'warning': '#d97706',
    'warning_light': '#fffbeb',
    'warning_border': '#fde68a',
    'danger': '#dc2626',
    'danger_light': '#fef2f2',
    'danger_border': '#fecaca',
    'info': '#0284c7',
    'info_light': '#f0f9ff',
    'info_border': '#bae6fd',
    'text': '#0f172a',
    'text_secondary': '#475569',
    'text_muted': '#64748b',
    'border': '#e2e8f0',
    'border_light': '#f1f5f9',
    'divider': '#e2e8f0',
    'table_header': '#f8fafc',
    'table_stripe': '#fafbfd',
    'shadow': 'rgba(15, 23, 42, 0.08)',
    'shadow_hover': 'rgba(15, 23, 42, 0.12)',
}


class TechStatusBadge(QLabel):
    """Clean enterprise status badge for technician availability"""

    def __init__(self, text, status_type="info", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(26)
        type_map = {
            "available": (ENTERPRISE_COLORS['success'], ENTERPRISE_COLORS['success_light'], ENTERPRISE_COLORS['success_border']),
            "busy": (ENTERPRISE_COLORS['warning'], ENTERPRISE_COLORS['warning_light'], ENTERPRISE_COLORS['warning_border']),
            "on leave": (ENTERPRISE_COLORS['danger'], ENTERPRISE_COLORS['danger_light'], ENTERPRISE_COLORS['danger_border']),
            "off duty": (ENTERPRISE_COLORS['text_muted'], ENTERPRISE_COLORS['border_light'], ENTERPRISE_COLORS['border']),
            "info": (ENTERPRISE_COLORS['info'], ENTERPRISE_COLORS['info_light'], ENTERPRISE_COLORS['info_border']),
        }
        fg, bg, brd = type_map.get(status_type, type_map["info"])
        self.setStyleSheet(f"""
            background-color: {bg};
            color: {fg};
            border: 1px solid {brd};
            border-radius: 6px;
            padding: 3px 12px;
            font-size: 8.5pt;
            font-weight: 700;
            font-family: {FONT_FAMILY};
        """)


class TechTimelineNode(QFrame):
    """Single timeline node for technician activity events in White Theme"""

    def __init__(self, event_type, date_str, description, is_first, is_last, parent=None):
        super().__init__(parent)
        self._event_type = event_type
        self._date_str = date_str
        self._description = description
        self._is_first = is_first
        self._is_last = is_last
        self._setup_ui()

    def _setup_ui(self):
        type_cfg = {
            'assigned': {'color': '#2563eb', 'bg': '#eff6ff', 'border': '#bfdbfe', 'icon': '📋', 'label': 'ASSIGNED'},
            'started': {'color': '#d97706', 'bg': '#fffbeb', 'border': '#fde68a', 'icon': '🔧', 'label': 'STARTED'},
            'completed': {'color': '#059669', 'bg': '#ecfdf5', 'border': '#a7f3d0', 'icon': '✅', 'label': 'COMPLETED'},
            'payment': {'color': '#7c3aed', 'bg': '#f5f3ff', 'border': '#c4b5fd', 'icon': '💳', 'label': 'PAYMENT'},
            'feedback': {'color': '#f59e0b', 'bg': '#fffbeb', 'border': '#fde68a', 'icon': '⭐', 'label': 'FEEDBACK'},
            'followup': {'color': '#ec4899', 'bg': '#fdf2f8', 'border': '#fbcfe8', 'icon': '📅', 'label': 'FOLLOW-UP'},
        }
        cfg = type_cfg.get(self._event_type, {'color': '#64748b', 'bg': '#f8fafc', 'border': '#e2e8f0', 'icon': '📌', 'label': 'EVENT'})

        self.setStyleSheet("background: transparent; border: none;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        col = QVBoxLayout()
        col.setSpacing(0)
        col.setAlignment(Qt.AlignmentFlag.AlignTop)

        if not self._is_first:
            t = QFrame()
            t.setFixedSize(2, 10)
            t.setStyleSheet(f"background-color: {cfg['border']}; border: none;")
            col.addWidget(t, alignment=Qt.AlignmentFlag.AlignHCenter)
        else:
            s = QFrame()
            s.setFixedHeight(10)
            s.setStyleSheet("background: transparent; border: none;")
            col.addWidget(s, alignment=Qt.AlignmentFlag.AlignHCenter)

        dot = QFrame()
        dot.setFixedSize(36, 36)
        dot.setStyleSheet(f"""
            QFrame {{
                background-color: {cfg['bg']};
                border: 2px solid {cfg['border']};
                border-radius: 18px;
            }}
        """)
        dl = QVBoxLayout(dot)
        dl.setContentsMargins(0, 0, 0, 0)
        dl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        di = QLabel(cfg['icon'])
        di.setStyleSheet("font-size: 11pt; background: transparent;")
        di.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dl.addWidget(di)
        col.addWidget(dot, alignment=Qt.AlignmentFlag.AlignHCenter)

        if not self._is_last:
            b = QFrame()
            b.setFixedSize(2, 10)
            b.setStyleSheet(f"background-color: {cfg['border']}; border: none;")
            col.addWidget(b, alignment=Qt.AlignmentFlag.AlignHCenter)
        else:
            s2 = QFrame()
            s2.setFixedHeight(10)
            s2.setStyleSheet("background: transparent; border: none;")
            col.addWidget(s2, alignment=Qt.AlignmentFlag.AlignHCenter)

        layout.addLayout(col)

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {ENTERPRISE_COLORS['card']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 10px;
            }}
            QFrame:hover {{
                background-color: {cfg['bg']};
                border: 1px solid {cfg['border']};
            }}
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(14, 10, 14, 10)
        cl.setSpacing(6)

        hr = QHBoxLayout()
        hr.setSpacing(8)
        badge = QLabel(cfg['label'])
        badge.setStyleSheet(f"""
            font-size: 7.5pt; font-weight: 700;
            color: {cfg['color']};
            background-color: {cfg['bg']};
            border: 1px solid {cfg['border']};
            border-radius: 4px;
            padding: 2px 8px;
            font-family: {FONT_FAMILY};
        """)
        hr.addWidget(badge)
        hr.addStretch()
        dlbl = QLabel(self._date_str)
        dlbl.setStyleSheet(f"font-size: 8pt; color: {ENTERPRISE_COLORS['text_muted']}; background: transparent; font-family: {FONT_FAMILY};")
        hr.addWidget(dlbl)
        cl.addLayout(hr)

        desc = QLabel(self._description)
        desc.setWordWrap(True)
        desc.setStyleSheet(f"font-size: 9.5pt; color: {ENTERPRISE_COLORS['text']}; background: transparent; font-family: {FONT_FAMILY};")
        cl.addWidget(desc)

        layout.addWidget(card, 1)


class TechnicianView(BaseView):
    """Enterprise workforce management dashboard for technicians (White Theme)"""

    def __init__(self):
        super().__init__()
        self.selected_technician_id = None
        self.technician_list = []
        self.photo_path = None

        self._setup_ui()
        self.load_technicians()

    def update_theme_colors(self):
        """Technician section is locked to enterprise White Theme per user requirement"""
        self.setStyleSheet(f"background-color: {ENTERPRISE_COLORS['bg']}; font-family: {FONT_FAMILY};")
        for table in ['technician_table', 'services_table', 'customers_table']:
            if hasattr(self, table):
                self._style_white_table(getattr(self, table))
        self.load_technicians()

    def _style_white_table(self, table):
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {ENTERPRISE_COLORS['card']};
                color: {ENTERPRISE_COLORS['text']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 10px;
                gridline-color: {ENTERPRISE_COLORS['border_light']};
                selection-background-color: {ENTERPRISE_COLORS['primary_light']};
                selection-color: {ENTERPRISE_COLORS['primary']};
                outline: none;
                alternate-background-color: {ENTERPRISE_COLORS['table_stripe']};
                font-size: 9.5pt;
                font-family: {FONT_FAMILY};
            }}
            QTableWidget::item {{
                padding: 12px 10px;
                border: none;
                color: {ENTERPRISE_COLORS['text']};
                background-color: transparent;
                border-bottom: 1px solid {ENTERPRISE_COLORS['border_light']};
            }}
            QTableWidget::item:selected {{
                background-color: {ENTERPRISE_COLORS['primary_light']};
                color: {ENTERPRISE_COLORS['primary']};
                border-left: 3px solid {ENTERPRISE_COLORS['primary']};
            }}
            QTableWidget::item:hover {{
                background-color: {ENTERPRISE_COLORS['primary_light']}80;
            }}
            QTableWidget::item:alternate {{
                background-color: {ENTERPRISE_COLORS['table_stripe']};
                border-bottom: 1px solid {ENTERPRISE_COLORS['border_light']};
            }}
            QTableWidget::item:alternate:selected {{
                background-color: {ENTERPRISE_COLORS['primary_light']};
                color: {ENTERPRISE_COLORS['primary']};
                border-left: 3px solid {ENTERPRISE_COLORS['primary']};
            }}
            QTableWidget::item:alternate:hover {{
                background-color: {ENTERPRISE_COLORS['primary_light']}80;
            }}
            QHeaderView::section {{
                background-color: {ENTERPRISE_COLORS['table_header']};
                color: {ENTERPRISE_COLORS['text_muted']};
                padding: 12px 10px;
                border: none;
                border-bottom: 2px solid {ENTERPRISE_COLORS['divider']};
                border-right: 1px solid {ENTERPRISE_COLORS['border_light']};
                font-weight: 700;
                font-size: 8.5pt;
                text-transform: uppercase;
                letter-spacing: 0.8px;
                font-family: {FONT_FAMILY};
            }}
            QHeaderView::section:first {{
                border-top-left-radius: 10px;
            }}
            QHeaderView::section:last {{
                border-top-right-radius: 10px;
                border-right: none;
            }}
            QHeaderView::section:hover {{
                background-color: {ENTERPRISE_COLORS['card_hover']};
                color: {ENTERPRISE_COLORS['text']};
            }}
        """)

    def _setup_ui(self):
        self.setStyleSheet(f"background-color: {ENTERPRISE_COLORS['bg']}; font-family: {FONT_FAMILY};")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 24, 28, 24)
        main_layout.setSpacing(20)

        self._create_header(main_layout)
        self._create_controls(main_layout)
        self._create_kpi_cards(main_layout)
        self._create_content(main_layout)

    def _apply_card_shadow(self, widget, blur=20, offset=2, opacity=18):
        # Lightweight styling avoids heavy software rasterization passes
        return None

    def _create_header(self, layout):
        header = QFrame()
        header.setStyleSheet("background: transparent; border: none;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)

        icon_frame = QFrame()
        icon_frame.setFixedSize(52, 52)
        icon_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {ENTERPRISE_COLORS['primary']}, stop:1 #1d4ed8);
                border-radius: 14px;
            }}
        """)
        il = QVBoxLayout(icon_frame)
        il.setContentsMargins(0, 0, 0, 0)
        il.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ilbl = QLabel("🔧")
        ilbl.setStyleSheet("font-size: 22pt; background: transparent; color: #fff;")
        ilbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        il.addWidget(ilbl)
        hl.addWidget(icon_frame)
        hl.addSpacing(18)

        tc = QVBoxLayout()
        tc.setSpacing(4)
        title = QLabel("Technician Management")
        title.setStyleSheet(f"""
            font-size: 26pt; font-weight: 700;
            color: {ENTERPRISE_COLORS['text']};
            letter-spacing: -0.5px;
            background: transparent;
            font-family: {FONT_FAMILY};
        """)
        tc.addWidget(title)
        subtitle = QLabel("Workforce tracking, job dispatching, collections, and commission payouts")
        subtitle.setStyleSheet(f"""
            font-size: 11pt;
            color: {ENTERPRISE_COLORS['text_muted']};
            background: transparent;
            font-family: {FONT_FAMILY};
        """)
        tc.addWidget(subtitle)
        hl.addLayout(tc)
        hl.addStretch()

        layout.addWidget(header)

    def _create_controls(self, layout):
        control_frame = QFrame()
        control_frame.setObjectName("techControlFrame")
        control_frame.setStyleSheet(f"""
            QFrame#techControlFrame {{
                background-color: {ENTERPRISE_COLORS['card']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 14px;
            }}
        """)
        self._apply_card_shadow(control_frame, blur=24, offset=2, opacity=15)

        cl = QHBoxLayout(control_frame)
        cl.setContentsMargins(18, 14, 18, 14)
        cl.setSpacing(12)

        search_container = QFrame()
        search_container.setStyleSheet(f"""
            QFrame {{
                background-color: {ENTERPRISE_COLORS['bg']};
                border: 2px solid {ENTERPRISE_COLORS['border']};
                border-radius: 10px;
            }}
            QFrame:hover {{
                border-color: {ENTERPRISE_COLORS['primary']}60;
            }}
        """)
        sl = QHBoxLayout(search_container)
        sl.setContentsMargins(14, 0, 14, 0)
        sl.setSpacing(8)

        search_icon = QLabel("🔍")
        search_icon.setStyleSheet(f"font-size: 12pt; background: transparent; color: {ENTERPRISE_COLORS['text_muted']};")
        sl.addWidget(search_icon)

        self.tech_search_input = QLineEdit()
        self.tech_search_input.setPlaceholderText("Search by technician name or mobile...")
        self.tech_search_input.setClearButtonEnabled(True)
        self.tech_search_input.setMinimumWidth(220)
        self.tech_search_input.setMaximumHeight(38)
        self._tech_search_timer = QTimer(self)
        self._tech_search_timer.setSingleShot(True)
        self._tech_search_timer.setInterval(200)
        self._tech_search_timer.timeout.connect(self.load_technicians)
        self.tech_search_input.textChanged.connect(lambda: self._tech_search_timer.start())
        self.tech_search_input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent; border: none;
                color: {ENTERPRISE_COLORS['text']}; font-size: 10pt;
                font-family: {FONT_FAMILY};
                padding: 0px;
            }}
            QLineEdit::placeholder {{
                color: {ENTERPRISE_COLORS['text_muted']}; font-style: normal;
            }}
        """)
        sl.addWidget(self.tech_search_input)
        cl.addWidget(search_container)

        # Territory filter
        self.territory_combo = QComboBox()
        self.territory_combo.addItem("All Territories")
        self.territory_combo.setMinimumWidth(140)
        self.territory_combo.setMaximumHeight(38)
        self.territory_combo.currentTextChanged.connect(self.load_technicians)
        self.territory_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {ENTERPRISE_COLORS['bg']};
                color: {ENTERPRISE_COLORS['text']};
                border: 2px solid {ENTERPRISE_COLORS['border']};
                border-radius: 10px;
                padding: 6px 28px 6px 12px;
                font-size: 9.5pt;
                font-weight: 500;
                font-family: {FONT_FAMILY};
            }}
            QComboBox:hover {{
                border-color: {ENTERPRISE_COLORS['primary']}60;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                border: none;
                width: 26px;
            }}
            QComboBox::down-arrow {{
                image: url("{CHEVRON_ICON_PATH}");
                width: 12px;
                height: 12px;
                margin-right: 6px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {ENTERPRISE_COLORS['card']};
                color: {ENTERPRISE_COLORS['text']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                selection-background-color: {ENTERPRISE_COLORS['primary_light']};
                selection-color: {ENTERPRISE_COLORS['primary']};
                padding: 4px;
            }}
        """)
        cl.addWidget(self.territory_combo)

        # Status filter
        self.status_combo = QComboBox()
        self.status_combo.addItems(["All Status", "Available", "Busy", "On Leave", "Off Duty"])
        self.status_combo.setMinimumWidth(130)
        self.status_combo.setMaximumHeight(38)
        self.status_combo.currentTextChanged.connect(self.load_technicians)
        self.status_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {ENTERPRISE_COLORS['bg']};
                color: {ENTERPRISE_COLORS['text']};
                border: 2px solid {ENTERPRISE_COLORS['border']};
                border-radius: 10px;
                padding: 6px 28px 6px 12px;
                font-size: 9.5pt;
                font-weight: 500;
                font-family: {FONT_FAMILY};
            }}
            QComboBox:hover {{
                border-color: {ENTERPRISE_COLORS['primary']}60;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                border: none;
                width: 26px;
            }}
            QComboBox::down-arrow {{
                image: url("{CHEVRON_ICON_PATH}");
                width: 12px;
                height: 12px;
                margin-right: 6px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {ENTERPRISE_COLORS['card']};
                color: {ENTERPRISE_COLORS['text']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                selection-background-color: {ENTERPRISE_COLORS['primary_light']};
                selection-color: {ENTERPRISE_COLORS['primary']};
                padding: 4px;
            }}
        """)
        cl.addWidget(self.status_combo)

        # Date range
        date_container = QFrame()
        date_container.setStyleSheet(f"""
            QFrame {{
                background-color: {ENTERPRISE_COLORS['bg']};
                border: 2px solid {ENTERPRISE_COLORS['border']};
                border-radius: 10px;
            }}
        """)
        dl = QHBoxLayout(date_container)
        dl.setContentsMargins(10, 0, 10, 0)
        dl.setSpacing(6)

        cal_icon = QLabel("📅")
        cal_icon.setStyleSheet(f"font-size: 11pt; background: transparent; color: {ENTERPRISE_COLORS['text_muted']};")
        dl.addWidget(cal_icon)

        self.start_date_input = QDateEdit()
        self.start_date_input.setDate(QDate.currentDate().addDays(-30))
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDisplayFormat("dd-MM-yy")
        self.start_date_input.setMaximumHeight(38)
        self.start_date_input.setStyleSheet(f"""
            QDateEdit {{
                background: transparent; border: none;
                color: {ENTERPRISE_COLORS['text']}; font-size: 9.5pt;
                font-family: {FONT_FAMILY};
                padding: 0px;
            }}
        """)
        dl.addWidget(self.start_date_input)

        sep = QLabel("to")
        sep.setStyleSheet(f"color: {ENTERPRISE_COLORS['text_muted']}; font-size: 9pt; background: transparent; padding: 0 2px;")
        dl.addWidget(sep)

        self.end_date_input = QDateEdit()
        self.end_date_input.setDate(QDate.currentDate())
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDisplayFormat("dd-MM-yy")
        self.end_date_input.setMaximumHeight(38)
        self.end_date_input.setStyleSheet(f"""
            QDateEdit {{
                background: transparent; border: none;
                color: {ENTERPRISE_COLORS['text']}; font-size: 9.5pt;
                font-family: {FONT_FAMILY};
                padding: 0px;
            }}
        """)
        dl.addWidget(self.end_date_input)
        cl.addWidget(date_container)

        filter_btn = QPushButton("  🔍 Filter")
        filter_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        filter_btn.clicked.connect(self.load_technicians)
        filter_btn.setMinimumHeight(38)
        filter_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ENTERPRISE_COLORS['primary_light']};
                color: {ENTERPRISE_COLORS['primary']};
                border: 1.5px solid {ENTERPRISE_COLORS['primary_border']};
                border-radius: 10px;
                padding: 8px 14px;
                font-weight: 600; font-size: 9pt;
                font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: #dbeafe;
                border-color: {ENTERPRISE_COLORS['primary']};
            }}
        """)
        cl.addWidget(filter_btn)

        cl.addStretch()

        add_btn = QPushButton("  ➕ Add Technician")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self.add_technician)
        add_btn.setMinimumHeight(40)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #059669, stop:1 #047857);
                color: #fff; border: none; border-radius: 10px;
                padding: 10px 22px; font-weight: 600; font-size: 9.5pt;
                font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #10b981, stop:1 #059669);
            }}
            QPushButton:pressed {{
                background: #047857;
            }}
        """)
        cl.addWidget(add_btn)

        export_btn = QPushButton("  📤 Export")
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.clicked.connect(self.export_to_excel)
        export_btn.setMinimumHeight(40)
        export_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {ENTERPRISE_COLORS['primary']};
                border: 2px solid {ENTERPRISE_COLORS['primary']}50;
                border-radius: 10px;
                padding: 10px 18px;
                font-weight: 600; font-size: 9.5pt;
                font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['primary_light']};
                border: 2px solid {ENTERPRISE_COLORS['primary']};
            }}
        """)
        cl.addWidget(export_btn)

        layout.addWidget(control_frame)

    def _create_kpi_cards(self, layout):
        cards_frame = QFrame()
        cards_frame.setStyleSheet("background: transparent; border: none;")

        cards_layout = QHBoxLayout(cards_frame)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(14)

        kpi_data = [
            ('total_technicians', 'Total Technicians', '0', '👥', ENTERPRISE_COLORS['primary']),
            ('active_technicians', 'Available on Duty', '0', '🔧', ENTERPRISE_COLORS['success']),
            ('total_services', 'Services Completed', '0', '📋', ENTERPRISE_COLORS['info']),
            ('revenue_collected', 'Revenue Collected', '₹0', '💰', ENTERPRISE_COLORS['warning']),
            ('pending_collections', 'Pending Collections', '₹0', '⚠️', ENTERPRISE_COLORS['danger']),
            ('avg_rating', 'Workforce Rating', '0.0 ★★★★★', '⭐', '#f59e0b'),
        ]

        self.tech_kpi_labels = {}
        for key, label, default, icon, color in kpi_data:
            card = QFrame()
            card.setMinimumHeight(84)
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {ENTERPRISE_COLORS['card']};
                    border: 1px solid {ENTERPRISE_COLORS['border']};
                    border-radius: 12px;
                }}
                QFrame:hover {{
                    border-color: {color}40;
                    background-color: {color}04;
                }}
            """)
            self._apply_card_shadow(card, blur=18, offset=2, opacity=12)

            inner = QHBoxLayout(card)
            inner.setContentsMargins(16, 12, 16, 12)
            inner.setSpacing(14)

            icon_box = QFrame()
            icon_box.setFixedSize(42, 42)
            icon_box.setStyleSheet(f"""
                QFrame {{
                    background-color: {color}12;
                    border-radius: 10px;
                    border: 1px solid {color}25;
                }}
            """)
            il = QVBoxLayout(icon_box)
            il.setContentsMargins(0, 0, 0, 0)
            il.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ibl = QLabel(icon)
            ibl.setStyleSheet(f"font-size: 16pt; background: transparent; color: {color};")
            ibl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            il.addWidget(ibl)
            inner.addWidget(icon_box)

            text_col = QVBoxLayout()
            text_col.setSpacing(2)
            val_lbl = QLabel(default)
            val_lbl.setStyleSheet(f"""
                font-size: 17pt; font-weight: 700;
                color: {ENTERPRISE_COLORS['text']}; background: transparent;
                font-family: {FONT_FAMILY};
            """)
            text_col.addWidget(val_lbl)
            lbl_lbl = QLabel(label)
            lbl_lbl.setStyleSheet(f"""
                font-size: 8.5pt; color: {ENTERPRISE_COLORS['text_muted']};
                font-weight: 500; background: transparent;
                font-family: {FONT_FAMILY};
            """)
            text_col.addWidget(lbl_lbl)
            inner.addLayout(text_col)
            inner.addStretch()

            cards_layout.addWidget(card)
            self.tech_kpi_labels[key] = val_lbl

        layout.addWidget(cards_frame)

    def _update_summary_bar(self):
        techs = getattr(self, 'technician_list', [])
        total = len(techs)
        active = sum(1 for t in techs if t.get('availability_status') == 'Available')
        svc = sum(int(t.get('total_services', 0) or 0) for t in techs)
        col = sum(float(t.get('collected_amount', 0) or 0) for t in techs)
        pen = sum(float(t.get('pending_amount', 0) or 0) for t in techs)

        total_rating = 0
        rating_count = 0
        for t in techs:
            s = int(t.get('total_services', 0) or 0)
            if s > 0:
                if s > 50:
                    r = 5
                elif s > 30:
                    r = 4
                elif s > 15:
                    r = 3
                elif s > 5:
                    r = 2
                else:
                    r = 1
                total_rating += r
                rating_count += 1
        avg_rating = round(total_rating / rating_count, 1) if rating_count > 0 else 0
        stars = '\u2605' * round(avg_rating) + '\u2606' * (5 - round(avg_rating))

        if hasattr(self, 'tech_kpi_labels'):
            self.tech_kpi_labels['total_technicians'].setText(str(total))
            self.tech_kpi_labels['active_technicians'].setText(str(active))
            self.tech_kpi_labels['total_services'].setText(str(svc))
            self.tech_kpi_labels['revenue_collected'].setText(f'\u20b9{col:,.0f}')
            self.tech_kpi_labels['pending_collections'].setText(f'\u20b9{pen:,.0f}')
            self.tech_kpi_labels['avg_rating'].setText(f'{avg_rating} {stars}')

    def _create_content(self, layout):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(8)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {ENTERPRISE_COLORS['border']};
                border-radius: 4px;
                margin: 8px 0px;
            }}
            QSplitter::handle:hover {{
                background-color: {ENTERPRISE_COLORS['primary']}60;
            }}
        """)

        left_pane = self._create_technician_list()
        splitter.addWidget(left_pane)

        right_pane = self._create_technician_details()
        splitter.addWidget(right_pane)

        splitter.setStretchFactor(0, 62)
        splitter.setStretchFactor(1, 38)
        splitter.setSizes([720, 440])

        layout.addWidget(splitter, 1)

    def _create_technician_list(self):
        pane = QFrame()
        pane.setObjectName("techListPane")
        pane.setStyleSheet(f"""
            QFrame#techListPane {{
                background-color: {ENTERPRISE_COLORS['card']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 14px;
            }}
        """)
        self._apply_card_shadow(pane, blur=24, offset=2, opacity=15)

        layout = QVBoxLayout(pane)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(16)

        header_row = QHBoxLayout()
        header_row.setSpacing(12)
        hi_box = QFrame()
        hi_box.setFixedSize(36, 36)
        hi_box.setStyleSheet(f"""
            QFrame {{
                background-color: {ENTERPRISE_COLORS['primary_light']};
                border: 1px solid {ENTERPRISE_COLORS['primary_border']};
                border-radius: 10px;
            }}
        """)
        hi_l = QVBoxLayout(hi_box)
        hi_l.setContentsMargins(0, 0, 0, 0)
        hi_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hi = QLabel("👥")
        hi.setStyleSheet("font-size: 14pt; background: transparent;")
        hi.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hi_l.addWidget(hi)
        header_row.addWidget(hi_box)

        hlbl = QLabel("Technician Directory")
        hlbl.setStyleSheet(f"""
            font-size: 16pt; font-weight: 700;
            color: {ENTERPRISE_COLORS['text']};
            letter-spacing: -0.3px;
            background: transparent;
            font-family: {FONT_FAMILY};
        """)
        header_row.addWidget(hlbl)

        self.tech_count_label = QLabel("0 technicians")
        self.tech_count_label.setStyleSheet(f"""
            font-size: 9.5pt; font-weight: 600;
            color: {ENTERPRISE_COLORS['primary']};
            background-color: {ENTERPRISE_COLORS['primary_light']};
            border: 1px solid {ENTERPRISE_COLORS['primary_border']};
            border-radius: 12px;
            padding: 4px 12px;
            font-family: {FONT_FAMILY};
        """)
        header_row.addWidget(self.tech_count_label)
        header_row.addStretch()
        layout.addLayout(header_row)

        self.technician_table = QTableWidget()
        self.technician_table.setColumnCount(8)
        self.technician_table.setHorizontalHeaderLabels([
            'Status', 'Technician', 'Mobile', 'Territory',
            'Jobs', 'Done', 'Collected', 'Rating'
        ])

        h = self.technician_table.horizontalHeader()
        h.setMinimumSectionSize(70)
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

        self.technician_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.technician_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.technician_table.setAlternatingRowColors(True)
        self.technician_table.verticalHeader().setVisible(False)
        self.technician_table.itemSelectionChanged.connect(self.on_technician_select)

        self._style_white_table(self.technician_table)
        layout.addWidget(self.technician_table)

        self.tech_empty_label = QLabel("No technicians found. Click '+ Add Technician' to get started.")
        self.tech_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tech_empty_label.setStyleSheet(f"color: {ENTERPRISE_COLORS['text_muted']}; font-size: 10pt; padding: 20px; background: transparent; font-family: {FONT_FAMILY};")
        self.tech_empty_label.setVisible(False)
        layout.addWidget(self.tech_empty_label)

        return pane

    def _create_technician_details(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setObjectName("techDetailsScroll")
        scroll.setStyleSheet(f"""
            QScrollArea#techDetailsScroll {{
                background-color: {ENTERPRISE_COLORS['card']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 14px;
            }}
            QScrollBar:vertical {{
                background-color: {ENTERPRISE_COLORS['bg']}; width: 6px;
                border-radius: 3px; margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {ENTERPRISE_COLORS['border']};
                border-radius: 3px; min-height: 30px; margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {ENTERPRISE_COLORS['text_muted']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        cl = QVBoxLayout(content_widget)
        cl.setContentsMargins(24, 24, 24, 24)
        cl.setSpacing(0)

        # ---- Profile Header with Avatar ----
        avatar_frame = QFrame()
        avatar_frame.setFixedSize(76, 76)
        avatar_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {ENTERPRISE_COLORS['primary']}, stop:1 #1d4ed8);
                border-radius: 24px;
            }}
        """)
        al = QVBoxLayout(avatar_frame)
        al.setContentsMargins(0, 0, 0, 0)
        al.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_label = QLabel("?")
        self.avatar_label.setStyleSheet(f"""
            font-size: 30pt; font-weight: 700;
            color: #ffffff; background: transparent;
        """)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        al.addWidget(self.avatar_label)

        profile_top = QHBoxLayout()
        profile_top.addWidget(avatar_frame)
        profile_top.addSpacing(18)

        profile_info = QVBoxLayout()
        profile_info.setSpacing(6)

        name_status_row = QHBoxLayout()
        name_status_row.setSpacing(10)
        self.tech_name_label = QLabel("Select a Technician")
        self.tech_name_label.setStyleSheet(f"""
            font-size: 19pt; font-weight: 700;
            color: {ENTERPRISE_COLORS['text']};
            letter-spacing: -0.3px;
            background: transparent;
            font-family: {FONT_FAMILY};
        """)
        name_status_row.addWidget(self.tech_name_label)
        self.tech_status_badge = TechStatusBadge("Unknown", "info")
        self.tech_status_badge.hide()
        name_status_row.addWidget(self.tech_status_badge)
        name_status_row.addStretch()
        profile_info.addLayout(name_status_row)

        hint = QLabel("Click a technician from the list to view 360° profile")
        hint.setStyleSheet(f"font-size: 9.5pt; color: {ENTERPRISE_COLORS['text_muted']}; background: transparent; font-family: {FONT_FAMILY};")
        profile_info.addWidget(hint)
        profile_top.addLayout(profile_info)
        profile_top.addStretch()
        cl.addLayout(profile_top)
        cl.addSpacing(24)

        # ---- Contact Section ----
        cl.addWidget(self._make_section_divider("Contact & Employment Information"))
        cl.addSpacing(14)

        self.tech_phone_label = QLabel("---")
        self.tech_email_label = QLabel("---")
        self.tech_address_label = QLabel("---")
        self.tech_territory_label = QLabel("---")
        self.tech_joining_label = QLabel("---")
        self.tech_experience_label = QLabel("---")
        self.tech_commission_label = QLabel("10%")
        self.tech_address_label.setWordWrap(True)

        contact_items = [
            ("📱", "Phone Number", self.tech_phone_label),
            ("✉️", "Email Address", self.tech_email_label),
            ("📍", "Address", self.tech_address_label),
            ("🗺️", "Service Territory", self.tech_territory_label),
            ("📅", "Joining Date", self.tech_joining_label),
            ("⭐", "Experience", self.tech_experience_label),
            ("🏷️", "Commission Rate", self.tech_commission_label),
        ]

        for icon, label, value_label in contact_items:
            row = QHBoxLayout()
            row.setSpacing(12)
            ic = QFrame()
            ic.setFixedSize(34, 34)
            ic.setStyleSheet(f"""
                QFrame {{
                    background-color: {ENTERPRISE_COLORS['primary_light']};
                    border-radius: 9px;
                }}
            """)
            il = QVBoxLayout(ic)
            il.setContentsMargins(0, 0, 0, 0)
            il.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ibl = QLabel(icon)
            ibl.setStyleSheet("font-size: 12pt; background: transparent;")
            ibl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            il.addWidget(ibl)
            row.addWidget(ic)
            tc = QVBoxLayout()
            tc.setSpacing(2)
            tl = QLabel(label.upper())
            tl.setStyleSheet(f"""
                font-size: 7.5pt; color: {ENTERPRISE_COLORS['text_muted']};
                font-weight: 700; letter-spacing: 0.6px; background: transparent;
                font-family: {FONT_FAMILY};
            """)
            tc.addWidget(tl)
            value_label.setStyleSheet(f"""
                font-size: 10.5pt; color: {ENTERPRISE_COLORS['text']};
                background: transparent; font-family: {FONT_FAMILY};
            """)
            tc.addWidget(value_label)
            row.addLayout(tc)
            row.addStretch()
            cl.addLayout(row)
            cl.addSpacing(8)

        cl.addSpacing(18)

        # ---- Performance Mini Cards (2x2) ----
        cl.addWidget(self._make_section_divider("Performance Metrics"))
        cl.addSpacing(14)

        perf_grid = QFrame()
        perf_grid.setStyleSheet("background: transparent; border: none;")
        pgl = QGridLayout(perf_grid)
        pgl.setContentsMargins(0, 0, 0, 0)
        pgl.setSpacing(10)

        perf_items = [
            ("Services Completed", "0", "📋", ENTERPRISE_COLORS['primary']),
            ("Revenue Collected", "₹0", "💰", ENTERPRISE_COLORS['success']),
            ("Customer Rating", "☆☆☆☆☆", "⭐", ENTERPRISE_COLORS['warning']),
            ("Pending Collections", "₹0", "⚠️", ENTERPRISE_COLORS['danger']),
        ]
        self.perf_value_labels = []
        for idx, (label, val, icon, color) in enumerate(perf_items):
            sc = QFrame()
            sc.setStyleSheet(f"""
                QFrame {{
                    background-color: {ENTERPRISE_COLORS['card']};
                    border: 1px solid {ENTERPRISE_COLORS['border']};
                    border-radius: 10px;
                }}
                QFrame:hover {{
                    background-color: {color}08;
                    border: 1px solid {color}35;
                }}
            """)
            scl = QHBoxLayout(sc)
            scl.setContentsMargins(12, 10, 12, 10)
            scl.setSpacing(10)
            sif = QFrame()
            sif.setFixedSize(32, 32)
            sif.setStyleSheet(f"""
                QFrame {{
                    background-color: {color}12;
                    border-radius: 8px;
                    border: 1px solid {color}25;
                }}
            """)
            sil = QVBoxLayout(sif)
            sil.setContentsMargins(0, 0, 0, 0)
            sil.setAlignment(Qt.AlignmentFlag.AlignCenter)
            si_lbl = QLabel(icon)
            si_lbl.setStyleSheet(f"font-size: 12pt; background: transparent; color: {color};")
            si_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sil.addWidget(si_lbl)
            scl.addWidget(sif)
            svl = QVBoxLayout()
            svl.setSpacing(2)
            vl = QLabel(val)
            vl.setStyleSheet(f"font-size: 14pt; font-weight: 700; color: {color}; background: transparent; font-family: {FONT_FAMILY};")
            svl.addWidget(vl)
            self.perf_value_labels.append(vl)
            ll = QLabel(label)
            ll.setStyleSheet(f"font-size: 7.5pt; color: {ENTERPRISE_COLORS['text_muted']}; font-weight: 600; background: transparent; font-family: {FONT_FAMILY};")
            svl.addWidget(ll)
            scl.addLayout(svl)
            scl.addStretch()
            pgl.addWidget(sc, idx // 2, idx % 2)

        cl.addWidget(perf_grid)
        cl.addSpacing(20)

        # ---- Quick Actions ----
        cl.addWidget(self._make_section_divider("Quick Actions"))
        cl.addSpacing(14)

        btn_frame = QFrame()
        btn_frame.setStyleSheet("background: transparent; border: none;")
        bl = QHBoxLayout(btn_frame)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(10)

        actions = [
            ("  💬  WhatsApp", "#16a34a", self._whatsapp_technician, False),
            ("  💰  Record Payout", ENTERPRISE_COLORS['info'], self._record_payout, False),
            ("  ✏️  Edit", ENTERPRISE_COLORS['primary'], self.edit_technician, False),
            ("  🗑️  Delete", ENTERPRISE_COLORS['danger'], self.delete_technician, True),
        ]

        for text, color, callback, is_outline in actions:
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(36)
            btn.clicked.connect(callback)
            if is_outline:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: {color};
                        border: 1.5px solid {color}50;
                        border-radius: 8px;
                        padding: 8px 14px;
                        font-weight: 600;
                        font-size: 9pt;
                        font-family: {FONT_FAMILY};
                    }}
                    QPushButton:hover {{
                        background-color: {color}12;
                        border: 1.5px solid {color};
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color};
                        color: #fff;
                        border: none;
                        border-radius: 8px;
                        padding: 8px 16px;
                        font-weight: 600;
                        font-size: 9pt;
                        font-family: {FONT_FAMILY};
                    }}
                    QPushButton:hover {{
                        background-color: {color}dd;
                    }}
                """)
            bl.addWidget(btn)

        bl.addStretch()
        cl.addWidget(btn_frame)
        cl.addSpacing(22)

        # ---- Service Assignments Table ----
        cl.addWidget(self._make_section_divider("Service Assignments"))
        cl.addSpacing(14)

        self.services_table = QTableWidget()
        self.services_table.setColumnCount(5)
        self.services_table.setHorizontalHeaderLabels([
            'Invoice', 'Customer', 'Date', 'Amount', 'Status'
        ])
        hdr = self.services_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.services_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.services_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.services_table.setAlternatingRowColors(True)
        self.services_table.verticalHeader().setVisible(False)
        self.services_table.setMinimumHeight(140)
        self.services_table.setMaximumHeight(220)
        self._style_white_table(self.services_table)
        cl.addWidget(self.services_table)
        cl.addSpacing(22)

        # ---- Customers Served Table ----
        cl.addWidget(self._make_section_divider("Customers Served"))
        cl.addSpacing(14)

        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(5)
        self.customers_table.setHorizontalHeaderLabels([
            'Customer Name', 'Mobile', 'Address', 'Service Date', 'Service Type'
        ])
        hdr2 = self.customers_table.horizontalHeader()
        hdr2.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr2.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr2.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr2.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr2.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.customers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.customers_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.customers_table.setAlternatingRowColors(True)
        self.customers_table.verticalHeader().setVisible(False)
        self.customers_table.setMinimumHeight(150)
        self.customers_table.setMaximumHeight(220)
        self._style_white_table(self.customers_table)
        cl.addWidget(self.customers_table)
        cl.addSpacing(22)

        # ---- Activity Timeline ----
        cl.addWidget(self._make_section_divider("Activity Timeline"))
        cl.addSpacing(14)

        self.timeline_widget = QFrame()
        self.timeline_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {ENTERPRISE_COLORS['bg']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 12px;
            }}
        """)
        tl = QVBoxLayout(self.timeline_widget)
        tl.setContentsMargins(16, 14, 16, 14)
        tl.setSpacing(0)

        self.timeline_scroll = QScrollArea()
        self.timeline_scroll.setWidgetResizable(True)
        self.timeline_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.timeline_scroll.setMinimumHeight(180)
        self.timeline_scroll.setMaximumHeight(300)
        self.timeline_scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{
                background: transparent; width: 5px;
                border-radius: 2px; margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {ENTERPRISE_COLORS['border']};
                border-radius: 2px; min-height: 20px; margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {ENTERPRISE_COLORS['text_muted']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

        self.timeline_content = QWidget()
        self.timeline_content.setStyleSheet("background: transparent;")
        self.timeline_content_layout = QVBoxLayout(self.timeline_content)
        self.timeline_content_layout.setSpacing(0)
        self.timeline_content_layout.setContentsMargins(0, 0, 0, 0)

        no_data = QLabel("Select a technician to view activity timeline")
        no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
        no_data.setStyleSheet(f"color: {ENTERPRISE_COLORS['text_muted']}; padding: 30px; font-size: 10pt; background: transparent; font-family: {FONT_FAMILY};")
        self.timeline_content_layout.addWidget(no_data)
        self.timeline_content_layout.addStretch()

        self.timeline_scroll.setWidget(self.timeline_content)
        tl.addWidget(self.timeline_scroll)
        cl.addWidget(self.timeline_widget)
        cl.addStretch()

        scroll.setWidget(content_widget)
        return scroll

    def _make_section_divider(self, title):
        frame = QFrame()
        frame.setStyleSheet("background: transparent; border: none;")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        label = QLabel(title.upper())
        label.setStyleSheet(f"""
            font-size: 8pt; font-weight: 700;
            color: {ENTERPRISE_COLORS['text_muted']};
            letter-spacing: 1.2px; background: transparent;
            font-family: {FONT_FAMILY};
        """)
        layout.addWidget(label)
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background-color: {ENTERPRISE_COLORS['divider']}; border: none;")
        layout.addWidget(line, 1)
        return frame

    def _update_stat_widget(self, idx, value):
        if hasattr(self, 'perf_value_labels') and idx < len(self.perf_value_labels):
            self.perf_value_labels[idx].setText(value)

    def _update_analytics_widget(self, idx, value):
        if hasattr(self, 'analytics_value_labels') and idx < len(self.analytics_value_labels):
            self.analytics_value_labels[idx].setText(value)

    def _render_timeline(self, timeline_events):
        while self.timeline_content_layout.count():
            item = self.timeline_content_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        if not timeline_events:
            nd = QLabel("No recent activity for this technician")
            nd.setAlignment(Qt.AlignmentFlag.AlignCenter)
            nd.setStyleSheet(f"color: {self.theme_manager.get_colors()['muted']}; padding: 30px; font-size: 10pt; background: transparent;")
            self.timeline_content_layout.addWidget(nd)
            self.timeline_content_layout.addStretch()
            return

        count = len(timeline_events)
        for idx, event in enumerate(timeline_events):
            is_first = (idx == 0)
            is_last = (idx == count - 1)
            node = TechTimelineNode(
                event['type'],
                event['date_str'],
                event['description'],
                is_first,
                is_last
            )
            self.timeline_content_layout.addWidget(node)

        self.timeline_content_layout.addStretch()

    def load_technicians(self):
        start_date = self.start_date_input.date().toString("yyyy-MM-dd")
        end_date = self.end_date_input.date().toString("yyyy-MM-dd")
        search = self.tech_search_input.text().strip()
        territory_filter = self.territory_combo.currentText()
        status_filter = self.status_combo.currentText()
        self.run_in_thread(
            lambda: self._load_technicians_thread(start_date, end_date, search, territory_filter, status_filter),
            self._update_technician_list
        )

    def _load_technicians_thread(self, start_date, end_date, search, territory_filter, status_filter):
        from database.db_connection import DatabaseContext

        with DatabaseContext() as db:
            query = """
            SELECT
                t.id, t.name, t.mobile, t.territory, t.availability_status,
                t.email, t.address, t.joining_date, t.commission_rate,
                (SELECT COUNT(*) FROM invoices i
                 WHERE i.technician_id = t.id AND i.is_active = TRUE
                 AND DATE(i.created_at) BETWEEN %s AND %s) as total_services,
                (SELECT COUNT(*) FROM invoices i
                 WHERE i.technician_id = t.id AND i.is_active = TRUE
                 AND i.payment_status = 'Paid'
                 AND DATE(i.created_at) BETWEEN %s AND %s) as completed_services,
                (SELECT COALESCE(SUM(i.advance_payment), 0) FROM invoices i
                 WHERE i.technician_id = t.id AND i.is_active = TRUE
                 AND DATE(i.created_at) BETWEEN %s AND %s) as collected_amount,
                (SELECT COALESCE(SUM(i.balance_amount), 0) FROM invoices i
                 WHERE i.technician_id = t.id AND i.is_active = TRUE
                 AND DATE(i.created_at) BETWEEN %s AND %s) as pending_amount
            FROM technicians t
            WHERE t.is_active = TRUE
            """
            params = [start_date, end_date, start_date, end_date, start_date, end_date, start_date, end_date]

            if search:
                query += " AND (t.name LIKE %s OR t.mobile LIKE %s)"
                params.extend([f'%{search}%', f'%{search}%'])

            if territory_filter != "All Territories":
                query += " AND t.territory = %s"
                params.append(territory_filter)

            if status_filter != "All Status":
                query += " AND t.availability_status = %s"
                params.append(status_filter)

            query += " ORDER BY t.name"

            technicians = db.execute_query(query, tuple(params), fetch_all=True)

            territories = []
            if territory_filter == "All Territories":
                territories_data = db.execute_query(
                    "SELECT DISTINCT territory FROM technicians WHERE territory IS NOT NULL AND territory != '' AND is_active = TRUE ORDER BY territory",
                    fetch_all=True
                )
                territories = [t['territory'] for t in (territories_data or [])]

            return {'technicians': technicians, 'territories': territories}

    def _update_technician_list(self, result):
        if isinstance(result, dict):
            technicians = result.get('technicians') or []
            self._all_territories = result.get('territories', [])
        else:
            technicians = result or []
        self.technician_list = technicians
        self.technician_table.setRowCount(0)
        self._update_summary_bar()
        count = len(self.technician_list)
        self.tech_count_label.setText(f"Showing {count} technician{'s' if count != 1 else ''}")

        if hasattr(self, '_all_territories') and self._all_territories:
            current = self.territory_combo.currentText()
            self.territory_combo.blockSignals(True)
            self.territory_combo.clear()
            self.territory_combo.addItem("All Territories")
            for t in self._all_territories:
                self.territory_combo.addItem(t)
            idx = self.territory_combo.findText(current)
            if idx >= 0:
                self.territory_combo.setCurrentIndex(idx)
            self.territory_combo.blockSignals(False)

        self.technician_table.setUpdatesEnabled(False)
        try:
            self.technician_table.setRowCount(len(self.technician_list))
            for row, tech in enumerate(self.technician_list):
                status = tech.get('availability_status', 'Available')
                if status == 'Available':
                    status_display = '\U0001f7e2 ' + status
                elif status == 'Busy':
                    status_display = '\U0001f7e1 ' + status
                elif status == 'On Leave':
                    status_display = '\U0001f534 ' + status
                else:
                    status_display = '\u26aa ' + status
                status_item = QTableWidgetItem(status_display)
                status_item.setData(Qt.ItemDataRole.UserRole, tech['id'])
                f = QFont()
                f.setWeight(QFont.Weight.Medium)
                status_item.setFont(f)
                self.technician_table.setItem(row, 0, status_item)

                name_item = QTableWidgetItem(tech['name'])
                name_item.setData(Qt.ItemDataRole.UserRole, tech['id'])
                name_item.setFont(f)
                self.technician_table.setItem(row, 1, name_item)

                self.technician_table.setItem(row, 2, QTableWidgetItem(tech['mobile']))
                self.technician_table.setItem(row, 3, QTableWidgetItem(tech.get('territory') or 'N/A'))
                self.technician_table.setItem(row, 4, QTableWidgetItem(str(tech['total_services'])))

                completed = int(tech.get('completed_services', 0) or 0)
                self.technician_table.setItem(row, 5, QTableWidgetItem(str(completed)))

                rev_item = QTableWidgetItem(f'\u20b9{tech["collected_amount"]:,.0f}')
                rev_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.technician_table.setItem(row, 6, rev_item)

                svc_count = int(tech['total_services'])
                if svc_count > 50:
                    rating = '\u2605\u2605\u2605\u2605\u2605'
                elif svc_count > 30:
                    rating = '\u2605\u2605\u2605\u2605'
                elif svc_count > 15:
                    rating = '\u2605\u2605\u2605'
                elif svc_count > 5:
                    rating = '\u2605\u2605'
                else:
                    rating = '\u2605'
                rating_item = QTableWidgetItem(f'{rating}')
                rating_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.technician_table.setItem(row, 7, rating_item)
        finally:
            self.technician_table.setUpdatesEnabled(True)

        self.tech_empty_label.setVisible(len(self.technician_list) == 0)

    def on_technician_select(self):
        selected_rows = self.technician_table.selectedItems()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        technician = self.technician_list[row]
        self.selected_technician_id = technician['id']
        self.load_technician_details(technician['id'])

    def load_technician_details(self, technician_id):
        start_date = self.start_date_input.date().toString("yyyy-MM-dd")
        end_date = self.end_date_input.date().toString("yyyy-MM-dd")
        self.run_in_thread(
            lambda: self._load_technician_details_thread(technician_id, start_date, end_date),
            self._update_technician_details
        )

    def _load_technician_details_thread(self, technician_id, start_date, end_date):
        from database.db_connection import DatabaseContext

        with DatabaseContext() as db:
            query = """
            SELECT
                t.*,
                (SELECT COUNT(*) FROM invoices i
                 WHERE i.technician_id = t.id AND i.is_active = TRUE
                 AND DATE(i.created_at) BETWEEN %s AND %s) as total_services,
                (SELECT COUNT(*) FROM invoices i
                 WHERE i.technician_id = t.id AND i.is_active = TRUE
                 AND i.payment_status = 'Paid'
                 AND DATE(i.created_at) BETWEEN %s AND %s) as completed_services,
                (SELECT COALESCE(SUM(i.advance_payment), 0) FROM invoices i
                 WHERE i.technician_id = t.id AND i.is_active = TRUE
                 AND DATE(i.created_at) BETWEEN %s AND %s) as collected_amount,
                (SELECT COALESCE(SUM(i.balance_amount), 0) FROM invoices i
                 WHERE i.technician_id = t.id AND i.is_active = TRUE
                 AND DATE(i.created_at) BETWEEN %s AND %s) as pending_amount
            FROM technicians t
            WHERE t.id = %s
            """

            technician = db.execute_query(
                query,
                (start_date, end_date, start_date, end_date, start_date, end_date, start_date, end_date, technician_id),
                fetch_one=True
            )

            services_query = """
            SELECT
                i.invoice_number, c.name as customer_name,
                DATE(i.created_at) as service_date,
                i.total_amount, i.payment_status
            FROM invoices i
            JOIN customers c ON i.customer_id = c.id
            WHERE i.technician_id = %s AND i.is_active = TRUE
            AND DATE(i.created_at) BETWEEN %s AND %s
            ORDER BY i.created_at DESC
            LIMIT 20
            """

            services = db.execute_query(
                services_query,
                (technician_id, start_date, end_date),
                fetch_all=True
            )

            customers_query = """
            SELECT
                c.name as customer_name,
                c.mobile as customer_mobile,
                c.address as customer_address,
                MAX(DATE(i.created_at)) as service_date,
                GROUP_CONCAT(DISTINCT s.service_name ORDER BY s.service_name SEPARATOR ', ') as services_performed
            FROM invoices i
            JOIN customers c ON i.customer_id = c.id
            LEFT JOIN invoice_items ii ON i.id = ii.invoice_id
            LEFT JOIN services s ON ii.service_id = s.id
            WHERE i.technician_id = %s AND i.is_active = TRUE
            AND DATE(i.created_at) BETWEEN %s AND %s
            GROUP BY c.id, c.name, c.mobile, c.address
            ORDER BY service_date DESC
            LIMIT 50
            """

            customers = db.execute_query(
                customers_query,
                (technician_id, start_date, end_date),
                fetch_all=True
            )

            # Build timeline from services
            timeline = []
            for svc in (services or []):
                svc_date = svc['service_date']
                if svc_date and not isinstance(svc_date, datetime):
                    try: svc_date = datetime.strptime(str(svc_date)[:10], '%Y-%m-%d')
                    except: svc_date = None
                date_str = svc_date.strftime('%d-%b-%Y') if svc_date else 'Unknown'
                timeline.append({
                    'type': 'assigned',
                    'date_str': date_str,
                    'description': f"Service assigned - Invoice #{svc['invoice_number']} for {svc['customer_name']} (\u20b9{svc['total_amount']:,.0f})"
                })
                status = svc['payment_status']
                if status == 'Paid':
                    timeline.append({
                        'type': 'completed',
                        'date_str': date_str,
                        'description': f"Service completed and payment collected for Invoice #{svc['invoice_number']}"
                    })
                elif status == 'Pending':
                    timeline.insert(0, {
                        'type': 'started',
                        'date_str': date_str,
                        'description': f"Service in progress for Invoice #{svc['invoice_number']}"
                    })
                    timeline.append({
                        'type': 'followup',
                        'date_str': date_str,
                        'description': f"Payment follow-up required for Invoice #{svc['invoice_number']}"
                    })

            return {
                'technician': technician,
                'services': services,
                'customers': customers,
                'timeline': timeline
            }

    def _update_technician_details(self, data):
        technician = data['technician']
        services = data['services']
        customers = data.get('customers', [])
        timeline = data.get('timeline', [])

        if not technician:
            return

        name = technician['name']
        initial = name[0].upper() if name else '?'
        self.avatar_label.setText(initial)
        self.tech_name_label.setText(name)

        status_raw = technician.get('availability_status', 'Available') or 'Available'
        st = status_raw.lower().replace(' ', '')
        self.tech_status_badge.setText(status_raw)
        self.tech_status_badge.show()
        type_map = {
            'available': 'available', 'busy': 'busy',
            'onleave': 'on leave', 'offduty': 'off duty'
        }
        badge_type = 'info'
        for k, v in type_map.items():
            if k in st:
                badge_type = v
                break
        self.tech_status_badge.setStyleSheet(self._badge_style(badge_type))

        self.tech_phone_label.setText(technician['mobile'] or '---')
        self.tech_email_label.setText(technician.get('email') or 'No email on record')
        self.tech_address_label.setText(technician.get('address') or 'No address on record')
        self.tech_territory_label.setText(technician.get('territory') or '---')
        comm_val = technician.get('commission_rate', 10)
        self.tech_commission_label.setText(f"{comm_val}% Commission")

        jd = technician.get('joining_date')
        if jd:
            if not isinstance(jd, datetime):
                try: jd = datetime.strptime(str(jd)[:10], '%Y-%m-%d')
                except: jd = None
        if jd:
            date_str = jd.strftime('%d-%b-%Y')
            self.tech_joining_label.setText(date_str)
            delta = datetime.now().date() - jd
            years = delta.days // 365
            months = (delta.days % 365) // 30
            exp_parts = []
            if years > 0:
                exp_parts.append(f"{years} yr")
            if months > 0:
                exp_parts.append(f"{months} mon")
            self.tech_experience_label.setText(' '.join(exp_parts) if exp_parts else '< 1 mon')
        else:
            self.tech_joining_label.setText("---")
            self.tech_experience_label.setText("---")

        # Update performance mini cards
        svc_count = int(technician.get('total_services', 0) or 0)
        completed = int(technician.get('completed_services', 0) or 0)
        collected = float(technician.get('collected_amount', 0) or 0)
        pending = float(technician.get('pending_amount', 0) or 0)

        self._update_stat_widget(0, str(completed))
        self._update_stat_widget(1, f'\u20b9{collected:,.0f}')
        if svc_count > 0:
            if svc_count > 50:
                stars = '\u2605\u2605\u2605\u2605\u2605'
            elif svc_count > 30:
                stars = '\u2605\u2605\u2605\u2605'
            elif svc_count > 15:
                stars = '\u2605\u2605\u2605'
            elif svc_count > 5:
                stars = '\u2605\u2605'
            else:
                stars = '\u2605'
            self._update_stat_widget(2, stars)
        else:
            self._update_stat_widget(2, '\u2606\u2606\u2606\u2606\u2606')
        self._update_stat_widget(3, f'\u20b9{pending:,.0f}')

        # Update analytics
        completion_rate = f'{completed / svc_count * 100:.0f}%' if svc_count > 0 else '0%'
        self._update_analytics_widget(0, completion_rate)
        self._update_analytics_widget(1, 'N/A')
        coll_eff = f'{(collected / (collected + pending) * 100):.0f}%' if (collected + pending) > 0 else '0%'
        self._update_analytics_widget(2, coll_eff)
        self._update_analytics_widget(3, 'N/A')

        # Update services table
        self.services_table.setUpdatesEnabled(False)
        try:
            srv_list = services or []
            self.services_table.setRowCount(len(srv_list))
            for row, service in enumerate(srv_list):
                self.services_table.setItem(row, 0, QTableWidgetItem(service['invoice_number']))
                self.services_table.setItem(row, 1, QTableWidgetItem(service['customer_name']))
                self.services_table.setItem(row, 2, QTableWidgetItem(
                    Formatters.format_date(service.get('service_date')) or 'N/A'
                ))
                self.services_table.setItem(row, 3, QTableWidgetItem(f'\u20b9{service["total_amount"]:,.2f}'))

                ps = service['payment_status']
                status_display = ps
                if ps == 'Paid':
                    status_display = '\u2705 Paid'
                elif ps == 'Pending':
                    status_display = '\U0001f7e1 Pending'
                elif ps == 'Partial':
                    status_display = '\U0001f7e0 Partial'
                elif ps == 'Overdue':
                    status_display = '\U0001f534 Overdue'
                else:
                    status_display = '\u26ab ' + (ps or 'N/A')
                self.services_table.setItem(row, 4, QTableWidgetItem(status_display))
        finally:
            self.services_table.setUpdatesEnabled(True)

        # Update customers table
        self.customers_table.setUpdatesEnabled(False)
        try:
            cust_list = customers or []
            self.customers_table.setRowCount(len(cust_list))
            for row, customer in enumerate(cust_list):
                name_item = QTableWidgetItem(customer['customer_name'])
                name_item.setToolTip(customer['customer_name'])
                self.customers_table.setItem(row, 0, name_item)
                mobile_item = QTableWidgetItem(customer['customer_mobile'])
                mobile_item.setToolTip(f"Call: {customer['customer_mobile']}")
                self.customers_table.setItem(row, 1, mobile_item)
                address_item = QTableWidgetItem(customer['customer_address'] or 'N/A')
                address_item.setToolTip(customer['customer_address'] or 'No address')
                self.customers_table.setItem(row, 2, address_item)
                date_str = Formatters.format_date(customer.get('service_date')) or 'N/A'
                self.customers_table.setItem(row, 3, QTableWidgetItem(date_str))
                svc_text = customer['services_performed'] or 'General Service'
                svc_item = QTableWidgetItem(svc_text)
                svc_item.setToolTip(svc_text)
                self.customers_table.setItem(row, 4, svc_item)
        finally:
            self.customers_table.setUpdatesEnabled(True)

        # Render timeline
        self._render_timeline(timeline)

    def _badge_style(self, status_type):
        type_map = {
            "available": ("#dcfce7", "#15803d", "#86efac"),
            "busy": ("#fef3c7", "#b45309", "#fcd34d"),
            "on leave": ("#fee2e2", "#b91c1c", "#fca5a5"),
            "off duty": ("#f1f5f9", "#475569", "#cbd5e1"),
            "info": ("#e0f2fe", "#0369a1", "#7dd3fc"),
        }
        bg, fg, brd = type_map.get(status_type, type_map["info"])
        return f"""
            background-color: {bg};
            color: {fg};
            border: 1px solid {brd};
            border-radius: 6px;
            padding: 3px 10px;
            font-size: 8.5pt;
            font-weight: 600;
            font-family: {FONT_FAMILY};
        """

    def add_technician(self):
        dialog = AddTechnicianDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_technicians()
            self.show_success_message("Technician added successfully")

    def edit_technician(self):
        if not self.selected_technician_id:
            self.show_warning_message("Please select a technician to edit")
            return

        dialog = EditTechnicianDialog(self.selected_technician_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_technicians()
            if self.selected_technician_id:
                self.load_technician_details(self.selected_technician_id)
            self.show_success_message("Technician updated successfully")

    def delete_technician(self):
        if not self.selected_technician_id:
            self.show_warning_message("Please select a technician to delete")
            return

        if self.show_question("Are you sure you want to delete this technician?"):
            from database.db_connection import DatabaseContext

            with DatabaseContext() as db:
                db.execute_query(
                    "UPDATE technicians SET is_active = FALSE WHERE id = %s",
                    (self.selected_technician_id,)
                )

            self.selected_technician_id = None
            self.load_technicians()
            self.show_success_message("Technician deleted successfully")

    def _whatsapp_technician(self):
        if not self.selected_technician_id:
            self.show_warning_message("Please select a technician first")
            return
        from database.db_connection import DatabaseContext
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        import urllib.parse

        with DatabaseContext() as db:
            tech = db.execute_query(
                """
                SELECT t.name, t.mobile, t.territory,
                       (SELECT COUNT(*) FROM invoices i WHERE i.technician_id = t.id AND i.is_active = TRUE) as total_jobs,
                       (SELECT COALESCE(SUM(i.balance_amount), 0) FROM invoices i WHERE i.technician_id = t.id AND i.is_active = TRUE) as pending_amount
                FROM technicians t
                WHERE t.id = %s
                """,
                (self.selected_technician_id,),
                fetch_one=True
            )
        if not tech or not tech.get('mobile'):
            self.show_warning_message("Technician mobile number not available")
            return

        mobile = ''.join(filter(str.isdigit, str(tech['mobile'])))
        if len(mobile) == 10:
            mobile = '91' + mobile

        tech_name = tech.get('name', 'Technician')
        jobs = tech.get('total_jobs', 0)
        territory = tech.get('territory', 'General')
        msg = (
            f"Hello {tech_name},\n\n"
            f"This is regarding your HVAC service schedule with our service team.\n"
            f"Assigned Jobs: {jobs}\n"
            f"Territory: {territory}\n\n"
            f"Please check your pending jobs and update completion status."
        )
        encoded_msg = urllib.parse.quote(msg)
        wa_url = f"https://wa.me/{mobile}?text={encoded_msg}"
        QDesktopServices.openUrl(QUrl(wa_url))
        self.show_success_message(f"Opening WhatsApp chat for {tech_name} ({tech['mobile']})")

    def _record_payout(self):
        if not self.selected_technician_id:
            self.show_warning_message("Please select a technician first")
            return
        dialog = PayoutDialog(self.selected_technician_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_technicians()
            self.load_technician_details(self.selected_technician_id)
            self.show_success_message("Technician payout recorded successfully")

    def refresh_data(self):
        self.load_technicians()

    def export_to_excel(self):
        try:
            from utils.excel_helper import ExcelExporter
            from datetime import datetime

            start_date = self.start_date_input.date().toString("yyyy-MM-dd")
            end_date = self.end_date_input.date().toString("yyyy-MM-dd")

            from database.db_connection import DatabaseContext
            with DatabaseContext() as db:
                query = """
                SELECT
                    t.availability_status, t.name, t.mobile, t.territory, t.email,
                    t.address, t.commission_rate, t.joining_date, t.emergency_contact,
                    (SELECT COUNT(*) FROM invoices i
                     WHERE i.technician_id = t.id AND i.is_active = TRUE
                     AND DATE(i.created_at) BETWEEN %s AND %s) as total_services,
                    (SELECT COALESCE(SUM(i.advance_payment), 0) FROM invoices i
                     WHERE i.technician_id = t.id AND i.is_active = TRUE
                     AND DATE(i.created_at) BETWEEN %s AND %s) as collected_amount,
                    (SELECT COALESCE(SUM(i.balance_amount), 0) FROM invoices i
                     WHERE i.technician_id = t.id AND i.is_active = TRUE
                     AND DATE(i.created_at) BETWEEN %s AND %s) as pending_amount
                FROM technicians t
                WHERE t.is_active = TRUE
                ORDER BY t.name
                """
                technicians = db.execute_query(
                    query,
                    (start_date, end_date, start_date, end_date, start_date, end_date),
                    fetch_all=True
                ) or []

            rows = []
            total_services = total_collected = total_pending = 0
            for tech in technicians:
                jd = tech.get('joining_date')
                joining = Formatters.format_date(tech.get('joining_date'))
                svc = int(tech.get('total_services', 0) or 0)
                col = float(tech.get('collected_amount', 0) or 0)
                pen = float(tech.get('pending_amount', 0) or 0)
                rows.append([
                    tech.get('availability_status', 'Available'),
                    tech['name'], tech['mobile'],
                    tech.get('territory') or '', tech.get('email') or '',
                    tech.get('address') or '', float(tech.get('commission_rate', 10) or 10) / 100,
                    joining, tech.get('emergency_contact') or '',
                    svc, col, pen
                ])
                total_services += svc
                total_collected += col
                total_pending += pen

            headers = ['Status', 'Name', 'Mobile', 'Territory', 'Email', 'Address',
                       'Commission %', 'Joining Date', 'Emergency Contact',
                       'Total Services', 'Amount Collected', 'Pending Amount']
            number_cols = {7, 10, 11, 12}
            col_formats = {7: ExcelExporter.PERCENT_FMT}
            top_techs = rows[:15]
            charts_data = [{
                'type': 'bar', 'title': 'Collection vs Pending by Technician',
                'categories': [r[1][:15] for r in top_techs],
                'values': [('Collected', [r[10] for r in top_techs]),
                           ('Pending', [r[11] for r in top_techs])],
                'y_axis': 'Amount (\u20b9)'
            }]
            wb = ExcelExporter.build_excel(
                sheet_title='Technicians',
                title_text='Technician Performance Report',
                subtitle_text=f'Period: {start_date} to {end_date} | Total: {len(rows)} technicians | Generated: {datetime.now().strftime("%d-%m-%Y %H:%M")}',
                headers=headers, rows=rows,
                total_row=['', 'TOTAL', '', '', '', '', '', '', '', total_services, total_collected, total_pending],
                number_cols=number_cols,
                col_formats=col_formats,
                kpis=[
                    ('Total Technicians', len(rows)),
                    ('Total Services', total_services),
                    ('Amount Collected', total_collected),
                    ('Pending Amount', total_pending),
                    ('Avg per Technician', len(rows) and total_services // len(rows)),
                    ('Collection Rate', f'{total_collected and total_collected / (total_collected + total_pending) * 100:.1f}%'),
                ],
                charts_data=charts_data,
                freeze_col=True
            )

            from PySide6.QtWidgets import QFileDialog
            default_filename = f"Technician_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Technician Report", default_filename, "Excel Files (*.xlsx)"
            )
            if file_path:
                try:
                    wb.save(file_path)
                    self.show_success_message(f"Report exported: {file_path}")
                except Exception as e:
                    self.show_error_message(f"Save failed: {str(e)}")
        except Exception as e:
            self.show_error_message(f"Export failed: {str(e)}")


class PayoutDialog(QDialog):
    """Enterprise White Theme Dialog for Technician Commission / Payout settlement"""

    def __init__(self, technician_id, parent=None):
        super().__init__(parent)
        self.technician_id = technician_id
        self.parent_view = parent
        self.setWindowTitle("Record Technician Payout & Commission")
        self.setMinimumWidth(540)
        self.setMinimumHeight(560)
        self._apply_styles()
        self._setup_ui()
        self._load_technician_data()

    def _apply_styles(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {ENTERPRISE_COLORS['bg']};
                font-family: {FONT_FAMILY};
            }}
            QLabel {{
                color: {ENTERPRISE_COLORS['text']};
                font-size: 9.5pt;
                font-family: {FONT_FAMILY};
            }}
            QLineEdit, QComboBox, QTextEdit, QDateEdit {{
                background-color: {ENTERPRISE_COLORS['card']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                padding: 7px 12px;
                color: {ENTERPRISE_COLORS['text']};
                font-size: 9.5pt;
                font-family: {FONT_FAMILY};
            }}
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDateEdit:focus {{
                border: 1.5px solid {ENTERPRISE_COLORS['primary']};
                background-color: #ffffff;
            }}
            QPushButton {{
                border-radius: 8px;
                padding: 8px 18px;
                font-weight: 600;
                font-size: 9.5pt;
                font-family: {FONT_FAMILY};
            }}
            QPushButton#submitBtn {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {ENTERPRISE_COLORS['primary']}, stop:1 #1d4ed8);
                color: #ffffff;
                border: none;
                min-height: 36px;
            }}
            QPushButton#submitBtn:hover {{
                background: {ENTERPRISE_COLORS['primary_hover']};
            }}
            QPushButton#cancelBtn {{
                background-color: transparent;
                color: {ENTERPRISE_COLORS['text_muted']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                min-height: 36px;
            }}
            QPushButton#cancelBtn:hover {{
                background-color: {ENTERPRISE_COLORS['card']};
                color: {ENTERPRISE_COLORS['text']};
            }}
        """)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        self.header_card = QFrame()
        self.header_card.setStyleSheet(f"""
            QFrame {{
                background-color: {ENTERPRISE_COLORS['card']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 12px;
            }}
        """)
        hl = QVBoxLayout(self.header_card)
        hl.setSpacing(6)
        hl.setContentsMargins(16, 14, 16, 14)

        self.tech_title_label = QLabel("Technician: Loading...")
        self.tech_title_label.setStyleSheet(f"font-size: 13pt; font-weight: 700; color: {ENTERPRISE_COLORS['text']}; background: transparent;")
        hl.addWidget(self.tech_title_label)

        self.summary_calc_label = QLabel("Calculating commission details...")
        self.summary_calc_label.setStyleSheet(f"font-size: 9pt; color: {ENTERPRISE_COLORS['text_muted']}; background: transparent;")
        hl.addWidget(self.summary_calc_label)

        layout.addWidget(self.header_card)

        form_card = QFrame()
        form_card.setStyleSheet(f"""
            QFrame {{
                background-color: {ENTERPRISE_COLORS['card']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 12px;
            }}
        """)
        fl = QFormLayout(form_card)
        fl.setSpacing(12)
        fl.setContentsMargins(18, 18, 18, 18)

        self.payout_date_input = QDateEdit()
        self.payout_date_input.setDate(QDate.currentDate())
        self.payout_date_input.setCalendarPopup(True)
        self.payout_date_input.setDisplayFormat("dd-MM-yyyy")
        fl.addRow("Payout Date:", self.payout_date_input)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Enter payout amount (₹)")
        fl.addRow("Payout Amount (₹) *:", self.amount_input)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Cash", "UPI / Google Pay", "Bank Transfer / NEFT", "Cheque", "Other"])
        fl.addRow("Payment Mode:", self.mode_combo)

        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("Transaction ID / Cheque / UTR No.")
        fl.addRow("Reference No.:", self.ref_input)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Commission notes, period or job remarks...")
        self.notes_input.setMaximumHeight(75)
        fl.addRow("Remarks / Notes:", self.notes_input)

        layout.addWidget(form_card)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        submit_btn = QPushButton("💾 Record Payout")
        submit_btn.setObjectName("submitBtn")
        submit_btn.clicked.connect(self._save_payout)
        btn_layout.addWidget(submit_btn)

        layout.addLayout(btn_layout)

    def _load_technician_data(self):
        from database.db_connection import DatabaseContext
        with DatabaseContext() as db:
            tech = db.execute_query(
                """
                SELECT t.name, t.mobile, t.commission_rate,
                       (SELECT COALESCE(SUM(i.advance_payment), 0) FROM invoices i
                        WHERE i.technician_id = t.id AND i.is_active = TRUE) as collected,
                       (SELECT COALESCE(SUM(i.balance_amount), 0) FROM invoices i
                        WHERE i.technician_id = t.id AND i.is_active = TRUE) as pending,
                       (SELECT COUNT(*) FROM invoices i
                        WHERE i.technician_id = t.id AND i.is_active = TRUE) as total_jobs
                FROM technicians t
                WHERE t.id = %s
                """,
                (self.technician_id,),
                fetch_one=True
            )
        if tech:
            name = tech.get('name', 'Technician')
            rate = float(tech.get('commission_rate', 10) or 10)
            collected = float(tech.get('collected', 0) or 0)
            est_commission = (collected * rate) / 100.0

            self.tech_title_label.setText(f"{name} (Rate: {rate:g}%)")
            self.summary_calc_label.setText(
                f"Total Collected: ₹{collected:,.0f} | Est. Commission ({rate:g}%): ₹{est_commission:,.0f} | Jobs: {tech.get('total_jobs', 0)}"
            )
            self.amount_input.setText(f"{est_commission:.0f}" if est_commission > 0 else "")
            self.notes_input.setPlainText(f"Commission payout for service jobs. Rate applied: {rate:g}%.")

    def _save_payout(self):
        amount_str = self.amount_input.text().strip()
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except ValueError:
            QMessageBox.warning(self, "Invalid Amount", "Please enter a valid payout amount in ₹.")
            return

        date_str = self.payout_date_input.date().toString("yyyy-MM-dd")
        mode = self.mode_combo.currentText()
        ref = self.ref_input.text().strip() or "N/A"
        notes = self.notes_input.toPlainText().strip()

        from database.db_connection import DatabaseContext
        with DatabaseContext() as db:
            detail_msg = f"Paid ₹{amount:,.2f} via {mode} on {date_str}. Ref: {ref}. Notes: {notes}"
            db.execute_query(
                """
                INSERT INTO audit_log (user_id, username, action, entity_type, entity_id, details, created_at)
                VALUES (1, 'Admin', 'PAYOUT', 'TECHNICIAN', %s, %s, %s)
                """,
                (self.technician_id, detail_msg, f"{date_str} 12:00:00")
            )
        self.accept()


class AddTechnicianDialog(QDialog):
    """Dialog for adding new technician with enterprise white theme"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Technician")
        self.setMinimumWidth(600)
        self.setMinimumHeight(700)
        self.parent_view = parent
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {ENTERPRISE_COLORS['bg']};
                font-family: {FONT_FAMILY};
            }}
            QLabel {{
                color: {ENTERPRISE_COLORS['text']};
                font-size: 9.5pt;
                font-family: {FONT_FAMILY};
            }}
            QLineEdit, QDateEdit, QComboBox, QTextEdit {{
                background-color: {ENTERPRISE_COLORS['card']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                padding: 7px 12px;
                color: {ENTERPRISE_COLORS['text']};
                font-size: 9.5pt;
                font-family: {FONT_FAMILY};
            }}
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus, QTextEdit:focus {{
                border: 1.5px solid {ENTERPRISE_COLORS['primary']};
                background-color: #ffffff;
            }}
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QPushButton {{
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 9.5pt;
                font-family: {FONT_FAMILY};
            }}
            QPushButton#primaryButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {ENTERPRISE_COLORS['primary']}, stop:1 #1d4ed8);
                color: #ffffff;
                border: none;
            }}
            QPushButton#primaryButton:hover {{
                background: {ENTERPRISE_COLORS['primary_hover']};
            }}
            QPushButton#dangerButton {{
                background-color: #fef2f2;
                color: {ENTERPRISE_COLORS['danger']};
                border: 1px solid #fecaca;
            }}
            QPushButton#dangerButton:hover {{
                background-color: #fee2e2;
            }}
        """)
        self.photo_path = None
        self._saved_styles = {}
        self._setup_ui()

    def _copy_photo_to_assets(self, file_path):
        import os, shutil, time
        tech_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'technicians')
        os.makedirs(tech_dir, exist_ok=True)
        ext = os.path.splitext(file_path)[1]
        dest_name = f"tech_{int(time.time())}{ext}"
        dest_path = os.path.join(tech_dir, dest_name)
        try:
            shutil.copy2(file_path, dest_path)
            return dest_path
        except Exception:
            return file_path

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Photo section
        photo_layout = QHBoxLayout()
        self.photo_label = QLabel()
        self.photo_label.setFixedSize(150, 150)
        self.photo_label.setStyleSheet(f"""
            QLabel {{
                background-color: {ENTERPRISE_COLORS['card']};
                border: 2px dashed {ENTERPRISE_COLORS['border']};
                border-radius: 75px;
                color: {ENTERPRISE_COLORS['text_muted']};
                font-size: 9pt;
            }}
        """)
        self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_label.setText("No Photo\nSelected")
        photo_layout.addWidget(self.photo_label)

        photo_btn_layout = QVBoxLayout()
        upload_photo_btn = QPushButton("📷 Upload Photo")
        upload_photo_btn.setObjectName("primaryButton")
        upload_photo_btn.clicked.connect(self._upload_photo)
        photo_btn_layout.addWidget(upload_photo_btn)
        remove_photo_btn = QPushButton("❌ Remove Photo")
        remove_photo_btn.setObjectName("dangerButton")
        remove_photo_btn.clicked.connect(self._remove_photo)
        photo_btn_layout.addWidget(remove_photo_btn)
        photo_btn_layout.addStretch()
        photo_layout.addLayout(photo_btn_layout)
        layout.addLayout(photo_layout)

        # Scrollable form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        form_layout = QFormLayout(scroll_content)
        form_layout.setSpacing(15)

        self.name_input = QLineEdit()
        form_layout.addRow("Name *:", self.name_input)
        self.mobile_input = QLineEdit()
        form_layout.addRow("Mobile *:", self.mobile_input)
        self.email_input = QLineEdit()
        form_layout.addRow("Email:", self.email_input)
        self.territory_input = QLineEdit()
        form_layout.addRow("Territory/Area:", self.territory_input)
        self.availability_combo = QComboBox()
        from database.db_connection import DatabaseContext
        with DatabaseContext() as db:
            res = db.execute_query("SELECT status_name FROM technician_statuses WHERE is_active = TRUE", fetch_all=True)
            if res:
                self.availability_combo.clear()
                for r in res:
                    self.availability_combo.addItem(r['status_name'])
            else:
                self.availability_combo.addItems(['Available', 'Busy', 'On Leave', 'Off Duty'])
        form_layout.addRow("Availability Status:", self.availability_combo)
        self.joining_date_input = QDateEdit()
        self.joining_date_input.setDate(QDate.currentDate())
        self.joining_date_input.setCalendarPopup(True)
        self.joining_date_input.setDisplayFormat("dd-MM-yyyy")
        form_layout.addRow("Joining Date:", self.joining_date_input)
        self.emergency_contact_input = QLineEdit()
        form_layout.addRow("Emergency Contact:", self.emergency_contact_input)
        self.address_input = QTextEdit()
        self.address_input.setMaximumHeight(80)
        form_layout.addRow("Address:", self.address_input)
        self.commission_input = QLineEdit("10")
        form_layout.addRow("Commission Rate (%):", self.commission_input)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _upload_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Photo", "", "Images (*.png *.xpm *.jpg *.jpeg)"
        )
        if file_path:
            self.photo_path = self._copy_photo_to_assets(file_path)
            pixmap = QPixmap(self.photo_path).scaled(
                150, 150,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.photo_label.setPixmap(pixmap)
            self.photo_label.setText("")

    def _remove_photo(self):
        self.photo_path = None
        self.photo_label.clear()
        self.photo_label.setStyleSheet(f"""
            QLabel {{
                background-color: {ENTERPRISE_COLORS['card']};
                border: 2px dashed {ENTERPRISE_COLORS['border']};
                border-radius: 75px;
                color: {ENTERPRISE_COLORS['text_muted']};
                font-size: 9pt;
            }}
        """)
        self.photo_label.setText("No Photo\nSelected")

    def _mark_field_invalid(self, widget, invalid=True):
        if invalid:
            if widget not in self._saved_styles:
                self._saved_styles[widget] = widget.styleSheet()
            widget.setStyleSheet(f"""
                border: 2px solid {ENTERPRISE_COLORS['danger']};
                background-color: #fef2f2;
            """)
        else:
            if widget in self._saved_styles:
                widget.setStyleSheet(self._saved_styles[widget])
            else:
                widget.setStyleSheet("")

    def _validate_and_accept(self):
        valid = True
        name = self.name_input.text().strip()
        mobile = self.mobile_input.text().strip()
        territory = self.territory_input.text().strip()

        if not name:
            self._mark_field_invalid(self.name_input)
            valid = False
        else:
            self._mark_field_invalid(self.name_input, False)
        if not mobile:
            self._mark_field_invalid(self.mobile_input)
            valid = False
        else:
            self._mark_field_invalid(self.mobile_input, False)
        if not territory:
            self._mark_field_invalid(self.territory_input)
            valid = False
        else:
            self._mark_field_invalid(self.territory_input, False)

        if not valid:
            QMessageBox.warning(self, "Validation", "Name, Mobile and Territory are required")
            return

        from database.db_connection import DatabaseContext
        with DatabaseContext() as db:
            db.execute_query(
                """
                INSERT INTO technicians (
                    name, mobile, address, email, territory, availability_status,
                    joining_date, emergency_contact, commission_rate, photo, is_active
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                """,
                (
                    name, mobile,
                    self.address_input.toPlainText().strip() or None,
                    self.email_input.text().strip() or None,
                    territory or None,
                    self.availability_combo.currentText(),
                    self.joining_date_input.date().toString("yyyy-MM-dd"),
                    self.emergency_contact_input.text().strip() or None,
                    float(self.commission_input.text().strip() or 10),
                    self.photo_path
                )
            )
        self.accept()


class EditTechnicianDialog(QDialog):
    """Dialog for editing technician with enterprise white theme"""

    def __init__(self, technician_id, parent=None):
        super().__init__(parent)
        self.technician_id = technician_id
        self.setWindowTitle("Edit Technician")
        self.setMinimumWidth(600)
        self.setMinimumHeight(700)
        self.parent_view = parent
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {ENTERPRISE_COLORS['bg']};
                font-family: {FONT_FAMILY};
            }}
            QLabel {{
                color: {ENTERPRISE_COLORS['text']};
                font-size: 9.5pt;
                font-family: {FONT_FAMILY};
            }}
            QLineEdit, QDateEdit, QComboBox, QTextEdit {{
                background-color: {ENTERPRISE_COLORS['card']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                padding: 7px 12px;
                color: {ENTERPRISE_COLORS['text']};
                font-size: 9.5pt;
                font-family: {FONT_FAMILY};
            }}
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus, QTextEdit:focus {{
                border: 1.5px solid {ENTERPRISE_COLORS['primary']};
                background-color: #ffffff;
            }}
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QPushButton {{
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 9.5pt;
                font-family: {FONT_FAMILY};
            }}
            QPushButton#primaryButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {ENTERPRISE_COLORS['primary']}, stop:1 #1d4ed8);
                color: #ffffff;
                border: none;
            }}
            QPushButton#primaryButton:hover {{
                background: {ENTERPRISE_COLORS['primary_hover']};
            }}
            QPushButton#dangerButton {{
                background-color: #fef2f2;
                color: {ENTERPRISE_COLORS['danger']};
                border: 1px solid #fecaca;
            }}
            QPushButton#dangerButton:hover {{
                background-color: #fee2e2;
            }}
        """)
        self.photo_path = None
        self._saved_styles = {}
        self._setup_ui()
        self._load_technician()

    def _copy_photo_to_assets(self, file_path):
        import os, shutil, time
        tech_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'technicians')
        os.makedirs(tech_dir, exist_ok=True)
        ext = os.path.splitext(file_path)[1]
        dest_name = f"tech_{int(time.time())}{ext}"
        dest_path = os.path.join(tech_dir, dest_name)
        try:
            shutil.copy2(file_path, dest_path)
            return dest_path
        except Exception:
            return file_path

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        photo_layout = QHBoxLayout()
        self.photo_label = QLabel()
        self.photo_label.setFixedSize(150, 150)
        self.photo_label.setStyleSheet(f"""
            QLabel {{
                background-color: {ENTERPRISE_COLORS['card']};
                border: 2px dashed {ENTERPRISE_COLORS['border']};
                border-radius: 75px;
                color: {ENTERPRISE_COLORS['text_muted']};
                font-size: 9pt;
            }}
        """)
        self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_label.setText("Loading...")
        photo_layout.addWidget(self.photo_label)

        photo_btn_layout = QVBoxLayout()
        upload_photo_btn = QPushButton("📷 Upload Photo")
        upload_photo_btn.setObjectName("primaryButton")
        upload_photo_btn.clicked.connect(self._upload_photo)
        photo_btn_layout.addWidget(upload_photo_btn)
        remove_photo_btn = QPushButton("❌ Remove Photo")
        remove_photo_btn.setObjectName("dangerButton")
        remove_photo_btn.clicked.connect(self._remove_photo)
        photo_btn_layout.addWidget(remove_photo_btn)
        photo_btn_layout.addStretch()
        photo_layout.addLayout(photo_btn_layout)
        layout.addLayout(photo_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        form_layout = QFormLayout(scroll_content)
        form_layout.setSpacing(15)

        self.name_input = QLineEdit()
        form_layout.addRow("Name *:", self.name_input)
        self.mobile_input = QLineEdit()
        form_layout.addRow("Mobile *:", self.mobile_input)
        self.email_input = QLineEdit()
        form_layout.addRow("Email:", self.email_input)
        self.territory_input = QLineEdit()
        form_layout.addRow("Territory/Area:", self.territory_input)
        self.availability_combo = QComboBox()
        from database.db_connection import DatabaseContext
        with DatabaseContext() as db:
            res = db.execute_query("SELECT status_name FROM technician_statuses WHERE is_active = TRUE", fetch_all=True)
            if res:
                self.availability_combo.clear()
                for r in res:
                    self.availability_combo.addItem(r['status_name'])
            else:
                self.availability_combo.addItems(['Available', 'Busy', 'On Leave', 'Off Duty'])
        form_layout.addRow("Availability Status:", self.availability_combo)
        self.joining_date_input = QDateEdit()
        self.joining_date_input.setCalendarPopup(True)
        self.joining_date_input.setDisplayFormat("dd-MM-yyyy")
        form_layout.addRow("Joining Date:", self.joining_date_input)
        self.emergency_contact_input = QLineEdit()
        form_layout.addRow("Emergency Contact:", self.emergency_contact_input)
        self.address_input = QTextEdit()
        self.address_input.setMaximumHeight(80)
        form_layout.addRow("Address:", self.address_input)
        self.commission_input = QLineEdit()
        form_layout.addRow("Commission Rate (%):", self.commission_input)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _upload_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Photo", "", "Images (*.png *.xpm *.jpg *.jpeg)"
        )
        if file_path:
            self.photo_path = self._copy_photo_to_assets(file_path)
            pixmap = QPixmap(self.photo_path).scaled(
                150, 150,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.photo_label.setPixmap(pixmap)
            self.photo_label.setText("")

    def _remove_photo(self):
        self.photo_path = None
        self.photo_label.clear()
        self.photo_label.setStyleSheet(f"""
            QLabel {{
                background-color: {ENTERPRISE_COLORS['card']};
                border: 2px dashed {ENTERPRISE_COLORS['border']};
                border-radius: 75px;
                color: {ENTERPRISE_COLORS['text_muted']};
                font-size: 9pt;
            }}
        """)
        self.photo_label.setText("No Photo\nSelected")

    def _load_technician(self):
        from database.db_connection import DatabaseContext
        with DatabaseContext() as db:
            technician = db.execute_query(
                "SELECT * FROM technicians WHERE id = %s",
                (self.technician_id,),
                fetch_one=True
            )
            if technician:
                self.name_input.setText(technician['name'])
                self.mobile_input.setText(technician['mobile'])
                self.email_input.setText(technician.get('email') or '')
                self.territory_input.setText(technician.get('territory') or '')
                self.availability_combo.setCurrentText(technician.get('availability_status', 'Available'))
                if technician.get('joining_date'):
                    jd_str = Formatters.format_date(technician.get('joining_date'), '%Y-%m-%d')
                    jd = QDate.fromString(jd_str, 'yyyy-MM-dd')
                    self.joining_date_input.setDate(jd)
                self.emergency_contact_input.setText(technician.get('emergency_contact') or '')
                self.address_input.setText(technician.get('address') or '')
                self.commission_input.setText(str(technician.get('commission_rate', 10)))
                if technician.get('photo'):
                    pixmap = QPixmap(technician['photo']).scaled(
                        150, 150,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.photo_label.setPixmap(pixmap)
                    self.photo_label.setText("")
                    self.photo_path = technician['photo']
                else:
                    self.photo_label.setText("No Photo")

    def _mark_field_invalid(self, widget, invalid=True):
        if invalid:
            if widget not in self._saved_styles:
                self._saved_styles[widget] = widget.styleSheet()
            widget.setStyleSheet(f"""
                border: 2px solid {ENTERPRISE_COLORS['danger']};
                background-color: #fef2f2;
            """)
        else:
            if widget in self._saved_styles:
                widget.setStyleSheet(self._saved_styles[widget])
            else:
                widget.setStyleSheet("")

    def _validate_and_accept(self):
        valid = True
        name = self.name_input.text().strip()
        mobile = self.mobile_input.text().strip()
        territory = self.territory_input.text().strip()

        if not name:
            self._mark_field_invalid(self.name_input)
            valid = False
        else:
            self._mark_field_invalid(self.name_input, False)
        if not mobile:
            self._mark_field_invalid(self.mobile_input)
            valid = False
        else:
            self._mark_field_invalid(self.mobile_input, False)
        if not territory:
            self._mark_field_invalid(self.territory_input)
            valid = False
        else:
            self._mark_field_invalid(self.territory_input, False)

        if not valid:
            QMessageBox.warning(self, "Validation", "Name, Mobile and Territory are required")
            return

        from database.db_connection import DatabaseContext
        with DatabaseContext() as db:
            db.execute_query(
                """
                UPDATE technicians
                SET name = %s, mobile = %s, email = %s, territory = %s,
                    availability_status = %s, joining_date = %s,
                    emergency_contact = %s, address = %s,
                    commission_rate = %s, photo = %s, updated_at = NOW()
                WHERE id = %s
                """,
                (
                    name, mobile,
                    self.email_input.text().strip() or None,
                    territory or None,
                    self.availability_combo.currentText(),
                    self.joining_date_input.date().toString("yyyy-MM-dd"),
                    self.emergency_contact_input.text().strip() or None,
                    self.address_input.toPlainText().strip() or None,
                    float(self.commission_input.text().strip() or 10),
                    self.photo_path,
                    self.technician_id
                )
            )
        self.accept()

