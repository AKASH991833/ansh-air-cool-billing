"""
Enterprise-Grade Inventory / Stock Management View
Modern UI with metric cards, stock tracking, low stock alerts & export
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QDialog, QFormLayout, QTextEdit, QDoubleSpinBox, QSpinBox, QMessageBox,
    QTabWidget, QComboBox, QProgressBar, QFileDialog, QMenu, QButtonGroup,
    QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QColor, QCursor

from utils.unified_theme import UnifiedTheme
from views.base_window import BaseView, MetricCard
from utils.app_settings import get_setting
from utils.formatters import Formatters
import os

CHEVRON_ICON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "icons", "chevron_down.png"
).replace("\\", "/")



class InventoryView(BaseView):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        QTimer.singleShot(100, self.load_data)

    def update_theme_colors(self):
        colors = self.theme_manager.get_colors()
        self.theme_manager.apply_palette(self)
        self.setStyleSheet(self.theme_manager.get_main_stylesheet())

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)
        colors = self.theme_manager.get_colors()
        self.currency_symbol = get_setting("currency_symbol", "₹")

        # ── Header ──
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)
        title_frame = QFrame()
        title_l = QVBoxLayout(title_frame)
        title_l.setContentsMargins(0, 0, 0, 0)
        title_l.setSpacing(2)
        title_lbl = QLabel("📦 Inventory Management")
        title_lbl.setStyleSheet(f"font-size: 20pt; font-weight: 700; color: {colors['fg']}; letter-spacing: 0.5px;")
        title_l.addWidget(title_lbl)
        subtitle_lbl = QLabel("Enterprise stock tracking, alerts & movement analysis")
        subtitle_lbl.setStyleSheet(f"font-size: 9pt; color: {colors['muted']}; letter-spacing: 0.3px;")
        title_l.addWidget(subtitle_lbl)
        header_layout.addWidget(title_frame)
        header_layout.addStretch()

        # Filter bar
        filter_frame = QFrame()
        filter_frame.setObjectName("filterBar")
        filter_frame.setStyleSheet(f"""
            QFrame#filterBar {{
                background-color: {colors['card_bg']};
                border: 1px solid {colors['border']};
                border-radius: 12px;
                padding: 6px;
            }}
        """)
        filter_l = QHBoxLayout(filter_frame)
        filter_l.setContentsMargins(10, 5, 10, 5)
        filter_l.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search parts...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMinimumWidth(180)
        self.search_input.setToolTip("Search parts by name")
        self.search_input.textChanged.connect(lambda: self.load_data())
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors['bg']}; color: {colors['fg']};
                border: 1px solid {colors['border']}; border-radius: 8px;
                padding: 7px 12px; font-size: 9pt;
            }}
            QLineEdit:focus {{ border: 1px solid {colors['primary']}; }}
        """)
        filter_l.addWidget(self.search_input)

        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories", None)
        self.category_filter.currentIndexChanged.connect(lambda: self.load_data())
        self.category_filter.setMinimumWidth(140)
        self.category_filter.setStyleSheet(f"""
            QComboBox {{
                background-color: {colors['bg']}; color: {colors['fg']};
                border: 1px solid {colors['border']}; border-radius: 6px;
                padding: 6px 26px 6px 10px; font-size: 9pt; min-height: 16px;
            }}
            QComboBox:hover {{
                border-color: {colors['primary']};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                border: none;
                width: 24px;
            }}
            QComboBox::down-arrow {{
                image: url("{CHEVRON_ICON_PATH}");
                width: 11px;
                height: 11px;
                margin-right: 6px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {colors['card_bg']}; color: {colors['fg']};
                border: 1px solid {colors['border']}; border-radius: 6px;
                selection-background-color: {colors['primary']}; selection-color: #ffffff;
            }}
        """)
        filter_l.addWidget(self.category_filter)

        self.low_stock_btn = QPushButton("⚠️ Low Stock")
        self.low_stock_btn.setCheckable(True)
        self.low_stock_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.low_stock_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; color: {colors['muted']};
                border: 1px solid {colors['border']}; border-radius: 6px;
                padding: 6px 12px; font-size: 9pt; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {colors['hover']}; color: {colors['fg']}; }}
            QPushButton:checked {{
                background-color: #f59e0b; color: #ffffff;
                border: 1px solid #f59e0b;
            }}
        """)
        self.low_stock_btn.clicked.connect(lambda: self.load_data())
        filter_l.addWidget(self.low_stock_btn)

        filter_l.addStretch()

        export_btn = QPushButton("  Export")
        export_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['primary']}; color: #ffffff;
                border: none; border-radius: 8px;
                padding: 8px 16px; font-size: 9pt; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {colors['primary_hover']}; }}
        """)
        export_menu = QMenu(self)
        export_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {colors['card_bg']}; border: 1px solid {colors['border']};
                border-radius: 8px; padding: 6px;
            }}
            QMenu::item {{ color: {colors['fg']}; padding: 8px 24px; border-radius: 4px; font-size: 9pt; }}
            QMenu::item:selected {{ background-color: {colors['primary']}; color: #ffffff; }}
        """)
        export_menu.addAction("📊 Export to Excel", lambda: self._export('excel'))
        export_menu.addAction("📄 Export to PDF", lambda: self._export('pdf'))
        export_btn.setMenu(export_menu)
        filter_l.addWidget(export_btn)

        add_btn = QPushButton("➕ Add Part")
        add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        add_btn.setToolTip("Add a new part to inventory")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #34d399; color: #ffffff;
                border: none; border-radius: 8px;
                padding: 8px 16px; font-size: 9pt; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: #059669; }}
        """)
        add_btn.clicked.connect(self.add_part)
        filter_l.addWidget(add_btn)

        header_layout.addWidget(filter_frame)
        main_layout.addLayout(header_layout)

        # ── Metric Cards ──
        card_frame = QFrame()
        card_frame.setObjectName("metricCardContainer")
        card_frame.setStyleSheet(f"""
            QFrame#metricCardContainer {{
                background-color: {colors['card_bg']};
                border: 1px solid {colors['border']};
                border-radius: 14px; padding: 14px;
            }}
        """)
        card_grid = QHBoxLayout(card_frame)
        card_grid.setSpacing(10)

        self.cards = {}
        metrics = [
            ('total_parts', 'Total Parts', '0', colors['primary']),
            ('low_stock', 'Low Stock', '0', '#f87171'),
            ('stock_value', 'Stock Value', f'{self.currency_symbol}0', '#34d399'),
            ('total_qty', 'Total Qty', '0', '#8b5cf6'),
        ]
        for key, label, default, color in metrics:
            card = MetricCard(label, default, self._get_icon(key), color)
            self.cards[key] = card
            card_grid.addWidget(card)
        main_layout.addWidget(card_frame)

        # ── Tabs ──
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {colors['border']};
                border-radius: 8px;
                background-color: {colors['card_bg']};
                top: -1px;
            }}
            QTabBar::tab {{
                background-color: transparent; color: {colors['muted']};
                padding: 10px 20px; font-weight: 600; font-size: 9pt;
                border: none; border-bottom: 2px solid transparent;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                color: {colors['primary']};
                border-bottom: 2px solid {colors['primary']};
                background-color: {colors['card_bg']};
            }}
            QTabBar::tab:hover:!selected {{
                color: {colors['fg']};
                background-color: {colors['hover']};
                border-radius: 6px 6px 0 0;
            }}
        """)

        self._build_parts_tab()
        self._build_movements_tab()
        self._build_low_stock_tab()

        main_layout.addWidget(self.tabs, 1)

    def _get_icon(self, key):
        icons = {
            'total_parts': '📦',
            'low_stock': '⚠️',
            'stock_value': '💰',
            'total_qty': '📊',
        }
        return icons.get(key, '📋')

    def _build_parts_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        info = QLabel("Complete parts inventory with stock levels, rates, and quick actions")
        info.setStyleSheet(f"font-size: 9pt; color: {self.theme_manager.get_colors()['muted']}; padding: 4px 0;")
        layout.addWidget(info)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            'Part Name', 'Category', f'Rate ({self.currency_symbol})', 'In Stock', 'Alert Level',
            'Health', 'Status', 'Actions'
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(42)
        self.table.setShowGrid(False)
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 8):
            h.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self.theme_manager.apply_table_theme(self.table)
        layout.addWidget(self.table)
        self.parts_empty_label = QLabel("No parts in inventory. Click '+ Add Part' to get started.")
        self.parts_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.parts_empty_label.setStyleSheet("color: #64748b; font-size: 12pt; padding: 20px;")
        self.parts_empty_label.setVisible(False)
        layout.addWidget(self.parts_empty_label)
        self.tabs.addTab(tab, "📋 Parts List")

    def _build_movements_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        info = QLabel("Stock movement history tracking additions, deductions, and adjustments")
        info.setStyleSheet(f"font-size: 9pt; color: {self.theme_manager.get_colors()['muted']}; padding: 4px 0;")
        layout.addWidget(info)

        self.movement_table = QTableWidget()
        self.movement_table.setColumnCount(6)
        self.movement_table.setHorizontalHeaderLabels([
            'Date & Time', 'Part', 'Change', 'Old Qty', 'New Qty', 'Reason'
        ])
        self.movement_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.movement_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.movement_table.setAlternatingRowColors(True)
        self.movement_table.verticalHeader().setVisible(False)
        self.movement_table.verticalHeader().setDefaultSectionSize(40)
        self.movement_table.setShowGrid(False)
        h2 = self.movement_table.horizontalHeader()
        h2.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h2.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for i in range(2, 6):
            h2.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self.theme_manager.apply_table_theme(self.movement_table)
        layout.addWidget(self.movement_table)
        self.movements_empty_label = QLabel("No stock movements recorded yet.")
        self.movements_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.movements_empty_label.setStyleSheet("color: #64748b; font-size: 12pt; padding: 20px;")
        self.movements_empty_label.setVisible(False)
        layout.addWidget(self.movements_empty_label)
        self.tabs.addTab(tab, "📈 Stock Movements")

    def _build_low_stock_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        info_bar = QFrame()
        info_bar.setStyleSheet(f"background: {self.theme_manager.get_colors()['bg']}; border-radius: 8px; padding: 8px 12px;")
        info_l = QHBoxLayout(info_bar)
        info_l.setContentsMargins(0, 0, 0, 0)
        info_icon = QLabel("⚠️")
        info_icon.setStyleSheet("font-size: 14pt; background: transparent;")
        info_l.addWidget(info_icon)
        info_text = QLabel("Critical low stock alerts - parts that need immediate reordering")
        info_text.setStyleSheet(f"font-size: 9pt; color: {self.theme_manager.get_colors()['muted']}; background: transparent;")
        info_l.addWidget(info_text)
        info_l.addStretch()
        layout.addWidget(info_bar)

        reorder_all_btn = QPushButton("📦 Reorder All Suggested")
        reorder_all_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        reorder_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #f59e0b; color: #ffffff;
                border: none; border-radius: 8px;
                padding: 8px 16px; font-size: 9pt; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: #d97706; }}
        """)
        reorder_all_btn.clicked.connect(self._reorder_all_suggested)
        layout.addWidget(reorder_all_btn)

        self.low_table = QTableWidget()
        self.low_table.setColumnCount(6)
        self.low_table.setHorizontalHeaderLabels([
            'Part Name', 'Category', 'In Stock', 'Alert Level', 'Urgency', 'Actions'
        ])
        self.low_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.low_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.low_table.setAlternatingRowColors(True)
        self.low_table.verticalHeader().setVisible(False)
        self.low_table.verticalHeader().setDefaultSectionSize(42)
        self.low_table.setShowGrid(False)
        h3 = self.low_table.horizontalHeader()
        h3.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        h3.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h3.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h3.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        h3.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        h3.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.theme_manager.apply_table_theme(self.low_table)
        layout.addWidget(self.low_table)
        self.low_stock_empty_label = QLabel("All parts are well-stocked! No low stock alerts.")
        self.low_stock_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.low_stock_empty_label.setStyleSheet("color: #64748b; font-size: 12pt; padding: 20px;")
        self.low_stock_empty_label.setVisible(False)
        layout.addWidget(self.low_stock_empty_label)
        self.tabs.addTab(tab, "⚠️ Low Stock Alerts")

    def _export(self, fmt='excel'):
        from database.db_connection import DatabaseContext
        from controllers.inventory_controller import InventoryController
        with DatabaseContext() as db:
            ic = InventoryController(db)
            parts = ic.get_all_parts()
            summary = ic.get_stock_summary()
        if not parts:
            self.show_warning_message("No inventory data to export")
            return

        headers = ['Part Name', 'Category', 'Rate', 'Stock Qty', 'Alert Level', 'Stock Value', 'Status']
        rows = []
        total_val = 0
        for p in parts:
            rate = float(p.get('default_rate', 0) or 0)
            qty = int(p.get('stock_quantity', 0) or 0)
            alert = int(p.get('stock_alert_level', 5) or 5)
            val = rate * qty
            status = "Low Stock" if qty <= alert else "OK"
            rows.append([p['part_name'], p.get('category', 'General') or 'General',
                        rate, qty, alert, val, status])
            total_val += val

        tab_name = "Inventory"
        if fmt == 'excel':
            from utils.excel_helper import ExcelExporter
            from datetime import datetime
            top_parts = sorted(rows, key=lambda x: -x[5])[:15]
            charts_data = [{
                'type': 'bar', 'title': 'Stock Value by Part',
                'categories': [r[0][:20] for r in top_parts],
                'values': [('Stock Value', [r[5] for r in top_parts])],
                'y_axis': f'Value ({self.currency_symbol})'
            }]
            low_count = sum(1 for r in rows if r[6] == 'Low Stock')
            ok_count = len(rows) - low_count
            charts_data.append({
                'type': 'pie', 'title': 'Stock Status Distribution',
                'categories': ['OK', 'Low Stock'],
                'values': [('Count', [ok_count, low_count])]
            })
            wb = ExcelExporter.build_excel(
                sheet_title='Inventory',
                title_text='Inventory / Parts Report',
                subtitle_text=f'Total: {len(rows)} parts | Stock Value: {self.currency_symbol}{total_val:,.0f} | Generated: {datetime.now().strftime("%d-%m-%Y %H:%M")}',
                headers=headers, rows=rows,
                total_row=['', '', '', '', '', total_val, ''],
                number_cols={3, 4, 6},
                cond_rules=[(7, 'low_stock')],
                kpis=[
                    ('Total Parts', len(rows)),
                    ('Stock Value', total_val),
                    ('Low Stock Items', summary['low_stock']),
                ],
                charts_data=charts_data
            )
            fp, _ = QFileDialog.getSaveFileName(self, 'Save Inventory Report',
                f"Inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", 'Excel Files (*.xlsx)')
            if fp:
                try:
                    wb.save(fp)
                    self.show_success_message(f"Inventory report exported: {fp}")
                except Exception as e:
                    self.show_error_message(f"Export failed: {str(e)}")
        elif fmt == 'pdf':
            self._export_pdf(tab_name, headers, rows)

    def _export_pdf(self, tab_name, headers, rows):
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.units import mm
        from datetime import datetime

        fp, _ = QFileDialog.getSaveFileName(self, 'Save PDF Report',
            f"Inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", 'PDF Files (*.pdf)')
        if not fp:
            return

        doc = SimpleDocTemplate(fp, pagesize=landscape(A4),
                                rightMargin=15*mm, leftMargin=15*mm,
                                topMargin=15*mm, bottomMargin=15*mm)
        styles = getSampleStyleSheet()
        elements = []
        title_style = ParagraphStyle('Title', parent=styles['Title'],
                                     fontSize=16, textColor=colors.HexColor('#0891B2'))
        sub_style = ParagraphStyle('Sub', parent=styles['Normal'],
                                   fontSize=9, textColor=colors.HexColor('#64748B'))
        elements.append(Paragraph("ANSH AIRCOOL - Inventory Report", title_style))
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M')}", sub_style))
        elements.append(Spacer(1, 6*mm))

        hdrs = [Paragraph(h, ParagraphStyle('h', fontSize=8, textColor=colors.white, fontName='Helvetica-Bold'))
                for h in headers]
        data_rows = [hdrs]
        for row in rows:
            sr = [Paragraph(str(c), ParagraphStyle('c', fontSize=7, textColor=colors.HexColor('#1E293B')))
                  for c in row]
            data_rows.append(sr)

        cw = [doc.width / len(headers)] * len(headers)
        t = Table(data_rows, colWidths=cw, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0891B2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t)
        doc.build(elements)
        self.show_success_message(f"PDF report saved: {fp}")

    def load_data(self):
        from database.db_connection import DatabaseContext
        from controllers.inventory_controller import InventoryController

        with DatabaseContext() as db:
            ic = InventoryController(db)
            search = self.search_input.text().strip()
            low_only = self.low_stock_btn.isChecked()
            cat = self.category_filter.currentData()
            parts = ic.get_all_parts(search=search if search else None, low_stock_only=low_only, category=cat)
            summary = ic.get_stock_summary()
            movements = ic.get_stock_movements(days=90)
            low_stock = ic.get_low_stock_parts()

        # Update categories dropdown
        current_cat = self.category_filter.currentData()
        self.category_filter.blockSignals(True)
        self.category_filter.clear()
        self.category_filter.addItem("All Categories", None)
        for c in summary.get('categories', []):
            self.category_filter.addItem(f"{c['category']} ({c['count']})", c['category'])
        if current_cat:
            idx = self.category_filter.findData(current_cat)
            if idx >= 0:
                self.category_filter.setCurrentIndex(idx)
        self.category_filter.blockSignals(False)

        # Update cards
        self.cards['total_parts'].set_value(str(summary['total_parts']))
        self.cards['low_stock'].set_value(str(summary['low_stock']))
        self.cards['stock_value'].set_value(f"{self.currency_symbol}{summary['stock_value']:,.0f}")
        self.cards['total_qty'].set_value(str(summary['total_quantity']))

        if summary['low_stock'] > 0:
            self.cards['low_stock'].set_color('#f87171')
        else:
            self.cards['low_stock'].set_color('#34d399')

        # ── Parts Table ──
        self.table.setRowCount(0)
        colors_local = self.theme_manager.get_colors()
        for p in parts:
            row = self.table.rowCount()
            self.table.insertRow(row)
            pname = p['part_name']
            cat_name = p.get('category', 'General') or 'General'
            rate = float(p.get('default_rate', 0) or 0)
            stock = int(p.get('stock_quantity', 0) or 0)
            alert = int(p.get('stock_alert_level', 5) or 5)
            stock_val = rate * stock
            ratio = (stock / max(alert, 1)) * 100

            self.table.setItem(row, 0, QTableWidgetItem(pname))
            cat_item = QTableWidgetItem(cat_name)
            cat_item.setForeground(QColor(colors_local['primary']))
            cat_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, cat_item)

            rate_item = QTableWidgetItem(f"{self.currency_symbol}{rate:,.0f}")
            rate_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 2, rate_item)

            sq = QTableWidgetItem(str(stock))
            sq.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if stock <= alert:
                sq.setForeground(QColor('#f87171'))
                sq.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.table.setItem(row, 3, sq)

            alert_item = QTableWidgetItem(str(alert))
            alert_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, alert_item)

            # Health bar
            health_frame = QFrame()
            health_l = QHBoxLayout(health_frame)
            health_l.setContentsMargins(6, 2, 6, 2)
            health_l.setSpacing(6)
            pb = QProgressBar()
            pb.setMinimum(0)
            pb.setMaximum(100)
            pb.setValue(min(int(ratio), 100))
            pb.setTextVisible(False)
            pb.setFixedHeight(10)
            pb.setFixedWidth(80)
            if ratio <= 25:
                health_color = '#f87171'
            elif ratio <= 50:
                health_color = '#f59e0b'
            elif ratio <= 75:
                health_color = colors_local['primary']
            else:
                health_color = '#34d399'
            pb.setStyleSheet(f"""
                QProgressBar {{ background-color: {colors_local['bg']}; border: none; border-radius: 5px; }}
                QProgressBar::chunk {{ background-color: {health_color}; border-radius: 5px; }}
            """)
            health_l.addWidget(pb)
            pct_lbl = QLabel(f"{min(ratio, 100):.0f}%")
            pct_lbl.setStyleSheet(f"color: {health_color}; font-size: 9pt; font-weight: bold; background: transparent;")
            health_l.addWidget(pct_lbl)
            health_l.addStretch()
            self.table.setCellWidget(row, 5, health_frame)

            status_frame = QFrame()
            status_frame.setStyleSheet(f"background: {colors_local['bg']}; border-radius: 10px; padding: 3px 10px;")
            status_l = QHBoxLayout(status_frame)
            status_l.setContentsMargins(0, 0, 0, 0)
            status_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_text = "✅ OK" if stock > alert else "🔴 Low"
            si = QLabel(status_text)
            si.setStyleSheet(f"color: {'#34d399' if stock > alert else '#f87171'}; font-size: 9pt; font-weight: 600; background: transparent;")
            status_l.addWidget(si)
            self.table.setCellWidget(row, 6, status_frame)

            # Actions
            act_frame = QFrame()
            act_l = QHBoxLayout(act_frame)
            act_l.setContentsMargins(4, 2, 4, 2)
            act_l.setSpacing(4)

            edit_b = QPushButton("✏️")
            edit_b.setFixedSize(28, 26)
            edit_b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            edit_b.setToolTip("Edit part details")
            edit_b.setStyleSheet(f"background: transparent; border: 1px solid {colors_local['border']}; border-radius: 4px; font-size: 11pt;")
            edit_b.clicked.connect(lambda checked, pid=p['id']: self.edit_part(pid))
            act_l.addWidget(edit_b)

            adj_b = QPushButton("📦")
            adj_b.setFixedSize(28, 26)
            adj_b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            adj_b.setToolTip("Adjust stock quantity")
            adj_b.setStyleSheet(f"background: transparent; border: 1px solid {colors_local['border']}; border-radius: 4px; font-size: 11pt;")
            adj_b.clicked.connect(lambda checked, pid=p['id'], pn=pname: self.adjust_stock(pid, pn))
            act_l.addWidget(adj_b)

            del_b = QPushButton("🗑️")
            del_b.setFixedSize(28, 26)
            del_b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            del_b.setToolTip("Delete part from inventory")
            del_b.setStyleSheet(f"background: transparent; border: 1px solid {colors_local['border']}; border-radius: 4px; font-size: 11pt;")
            del_b.clicked.connect(lambda checked, pid=p['id']: self.delete_part(pid))
            act_l.addWidget(del_b)

            act_l.addStretch()
            self.table.setCellWidget(row, 7, act_frame)

        self.parts_empty_label.setVisible(len(parts) == 0)

        # ── Movements Table ──
        self.movement_table.setRowCount(0)
        for m in movements:
            row = self.movement_table.rowCount()
            self.movement_table.insertRow(row)
            date_item = QTableWidgetItem(
                Formatters.format_datetime(m.get('created_at'), '%d-%m-%Y %H:%M'))
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.movement_table.setItem(row, 0, date_item)
            self.movement_table.setItem(row, 1, QTableWidgetItem(m.get('part_name', '')))
            change = int(m.get('quantity_change', 0) or 0)
            ci = QTableWidgetItem(f"{change:+d}")
            ci.setForeground(QColor('#34d399') if change > 0 else QColor('#f87171'))
            ci.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            ci.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.movement_table.setItem(row, 2, ci)
            old_item = QTableWidgetItem(str(m.get('old_quantity', '')))
            old_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.movement_table.setItem(row, 3, old_item)
            new_item = QTableWidgetItem(str(m.get('new_quantity', '')))
            new_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.movement_table.setItem(row, 4, new_item)
            self.movement_table.setItem(row, 5, QTableWidgetItem(m.get('reason', '') or ''))

        self.movements_empty_label.setVisible(len(movements) == 0)

        # ── Low Stock Table ──
        self.low_table.setRowCount(0)
        for p in low_stock:
            row = self.low_table.rowCount()
            self.low_table.insertRow(row)
            stock = int(p.get('stock_quantity', 0) or 0)
            alert = int(p.get('stock_alert_level', 5) or 5)
            urgency_ratio = (stock / max(alert, 1)) * 100
            if urgency_ratio <= 0:
                urgency_text = "🔴 Critical"
                urgency_color = '#dc2626'
            elif urgency_ratio <= 25:
                urgency_text = "🟠 High"
                urgency_color = '#f59e0b'
            elif urgency_ratio <= 50:
                urgency_text = "🟡 Medium"
                urgency_color = '#eab308'
            else:
                urgency_text = "🟢 Low"
                urgency_color = '#34d399'

            name_item = QTableWidgetItem(p['part_name'])
            name_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.low_table.setItem(row, 0, name_item)
            cat_i = QTableWidgetItem(p.get('category', 'General') or 'General')
            cat_i.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.low_table.setItem(row, 1, cat_i)
            sq = QTableWidgetItem(str(stock))
            sq.setForeground(QColor('#f87171'))
            sq.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            sq.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.low_table.setItem(row, 2, sq)
            alert_i = QTableWidgetItem(str(alert))
            alert_i.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.low_table.setItem(row, 3, alert_i)

            urgency_frame = QFrame()
            urgency_frame.setStyleSheet(f"background: {colors_local['bg']}; border-radius: 10px; padding: 3px 10px;")
            urgency_l = QHBoxLayout(urgency_frame)
            urgency_l.setContentsMargins(0, 0, 0, 0)
            urgency_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ui = QLabel(urgency_text)
            ui.setStyleSheet(f"color: {urgency_color}; font-size: 9pt; font-weight: 600; background: transparent;")
            urgency_l.addWidget(ui)
            self.low_table.setCellWidget(row, 4, urgency_frame)

            reorder_b = QPushButton("📦 Reorder")
            reorder_b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            reorder_b.setToolTip("Reorder stock for this part")
            reorder_b.setStyleSheet("""
                QPushButton { background-color: #f59e0b; color: white; border: none;
                    border-radius: 6px; padding: 6px 14px; font-weight: bold; font-size: 9pt; }
                QPushButton:hover { background-color: #d97706; }
            """)
            reorder_b.clicked.connect(lambda checked, pid=p['id'], pn=p['part_name']: self.reorder_stock(pid, pn))
            self.low_table.setCellWidget(row, 5, reorder_b)

        self.low_stock_empty_label.setVisible(len(low_stock) == 0)

    def add_part(self):
        dialog = PartDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

    def edit_part(self, part_id):
        from database.db_connection import DatabaseContext
        with DatabaseContext() as db:
            data = db.execute_query("SELECT * FROM parts WHERE id=%s", (part_id,), fetch_one=True)
        if data:
            dialog = PartDialog(self, data)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_data()

    def delete_part(self, part_id):
        if self.show_question("Delete this part from inventory?"):
            from database.db_connection import DatabaseContext
            from controllers.inventory_controller import InventoryController
            with DatabaseContext() as db:
                InventoryController(db).delete_part(part_id)
            self.load_data()

    def adjust_stock(self, part_id, part_name):
        from database.db_connection import DatabaseContext
        with DatabaseContext() as db:
            part = db.execute_query("SELECT id, part_name, stock_quantity, stock_alert_level FROM parts WHERE id=%s AND is_active=TRUE", (part_id,), fetch_one=True)
        if not part:
            self.show_warning_message("Part not found")
            return

        dialog = StockAdjustDialog(self, part)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

    def reorder_stock(self, part_id, part_name):
        from database.db_connection import DatabaseContext
        with DatabaseContext() as db:
            part = db.execute_query("SELECT id, part_name, stock_quantity, stock_alert_level FROM parts WHERE id=%s AND is_active=TRUE", (part_id,), fetch_one=True)
        if part:
            suggested = max(part['stock_alert_level'] - part['stock_quantity'], 1)
            dialog = StockAdjustDialog(self, part, suggested_qty=suggested)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_data()

    def _reorder_all_suggested(self):
        from database.db_connection import DatabaseContext
        from controllers.inventory_controller import InventoryController
        if not self.show_question("Reorder all low stock items to their alert level?"):
            return
        with DatabaseContext() as db:
            ic = InventoryController(db)
            suggestions = ic.get_reorder_suggestions()
            for s in suggestions:
                qty = int(s['suggested_order_qty'])
                if qty > 0:
                    ic.adjust_stock(s['id'], qty, 'Auto reorder')
        self.load_data()
        self.show_success_message(f"Reordered {len(suggestions)} items")


class PartDialog(QDialog):
    def __init__(self, parent, data=None):
        super().__init__(parent)
        self.data = data
        self.setWindowTitle("Edit Part" if data else "Add New Part")
        self.setMinimumWidth(500)
        self.setMaximumWidth(600)
        self.theme_manager = UnifiedTheme()
        colors = self.theme_manager.get_colors()
        self.setStyleSheet(f"QDialog {{ background-color: {colors['bg']}; }}")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        from utils.app_settings import get_setting
        self.currency_symbol = get_setting("currency_symbol", "\u20b9")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)
        colors = self.theme_manager.get_colors()

        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet(f"background: {colors['card_bg']}; border-radius: 10px; padding: 12px 16px;")
        header_l = QHBoxLayout(header_frame)
        header_l.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel("📦")
        icon_lbl.setStyleSheet("font-size: 20pt; background: transparent;")
        header_l.addWidget(icon_lbl)
        header_text = QVBoxLayout()
        header_text.setSpacing(2)
        title = QLabel("Edit Part" if self.data else "Add New Part")
        title.setStyleSheet(f"font-size: 15pt; font-weight: 700; color: {colors['fg']}; background: transparent;")
        header_text.addWidget(title)
        sub = QLabel("Add or update inventory parts with stock and pricing details")
        sub.setStyleSheet(f"font-size: 8pt; color: {colors['muted']}; background: transparent;")
        header_text.addWidget(sub)
        header_l.addLayout(header_text)
        header_l.addStretch()
        layout.addWidget(header_frame)

        input_style = f"""
            QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox, QSpinBox {{
                background: {colors['card_bg']}; color: {colors['fg']};
                border: 1px solid {colors['border']}; border-radius: 8px;
                padding: 8px 12px; font-size: 10pt;
            }}
            *:focus {{ border: 1px solid {colors['primary']}; }}
            QComboBox {{
                padding-right: 28px;
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
        """
        form_lbl_style = f"font-size: 9pt; font-weight: 600; color: {colors['fg']}; padding-right: 8px;"

        # Basic info section
        info_frame = QFrame()
        info_frame.setStyleSheet(f"background: {colors['card_bg']}; border: 1px solid {colors['border']}; border-radius: 10px; padding: 14px;")
        info_l = QVBoxLayout(info_frame)
        info_l.setSpacing(10)
        info_title = QLabel("📋 Part Information")
        info_title.setStyleSheet(f"font-size: 10pt; font-weight: 700; color: {colors['primary']}; background: transparent; letter-spacing: 0.3px;")
        info_l.addWidget(info_title)

        # Row 1: Name + Category
        row1 = QHBoxLayout()
        row1.setSpacing(12)
        c1 = QVBoxLayout()
        c1.setSpacing(6)
        l1 = QLabel("Part Name")
        l1.setStyleSheet(form_lbl_style)
        c1.addWidget(l1)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Compressor, PCB Board, Fan Motor...")
        self.name_input.setStyleSheet(input_style)
        c1.addWidget(self.name_input)
        row1.addLayout(c1)
        c2 = QVBoxLayout()
        c2.setSpacing(6)
        l2 = QLabel("Category")
        l2.setStyleSheet(form_lbl_style)
        c2.addWidget(l2)
        self.category_combo = QComboBox()
        self.category_combo.addItems(['General', 'Compressor', 'PCB/Board', 'Motor', 'Fan', 'Capacitor',
                                       'Sensor', 'Pipe', 'Gas', 'Remote', 'Filter', 'Other'])
        self.category_combo.setStyleSheet(input_style)
        c2.addWidget(self.category_combo)
        row1.addLayout(c2)
        info_l.addLayout(row1)

        # Row 2: Rate + Stock
        row2 = QHBoxLayout()
        row2.setSpacing(12)
        c3 = QVBoxLayout()
        c3.setSpacing(6)
        l3 = QLabel(f"Default Rate ({self.currency_symbol})")
        l3.setStyleSheet(form_lbl_style)
        c3.addWidget(l3)
        self.rate_input = QDoubleSpinBox()
        self.rate_input.setRange(0, 999999)
        self.rate_input.setPrefix(self.currency_symbol + " ")
        self.rate_input.setStyleSheet(input_style)
        c3.addWidget(self.rate_input)
        row2.addLayout(c3)
        c4 = QVBoxLayout()
        c4.setSpacing(6)
        l4 = QLabel("Stock Quantity")
        l4.setStyleSheet(form_lbl_style)
        c4.addWidget(l4)
        self.stock_input = QSpinBox()
        self.stock_input.setRange(0, 99999)
        self.stock_input.setStyleSheet(input_style)
        c4.addWidget(self.stock_input)
        row2.addLayout(c4)
        info_l.addLayout(row2)

        # Row 3: Alert + Unit
        row3 = QHBoxLayout()
        row3.setSpacing(12)
        c5 = QVBoxLayout()
        c5.setSpacing(6)
        l5 = QLabel("Alert Level")
        l5.setStyleSheet(form_lbl_style)
        c5.addWidget(l5)
        self.alert_input = QSpinBox()
        self.alert_input.setRange(1, 9999)
        self.alert_input.setValue(5)
        self.alert_input.setStyleSheet(input_style)
        c5.addWidget(self.alert_input)
        row3.addLayout(c5)
        c6 = QVBoxLayout()
        c6.setSpacing(6)
        l6 = QLabel("Unit")
        l6.setStyleSheet(form_lbl_style)
        c6.addWidget(l6)
        self.unit_combo = QComboBox()
        from database.db_connection import DatabaseContext
        with DatabaseContext() as db:
            res = db.execute_query("SELECT unit_name FROM inventory_units WHERE is_active = TRUE", fetch_all=True)
            if res:
                for r in res:
                    self.unit_combo.addItem(r['unit_name'])
            else:
                self.unit_combo.addItems(['pcs', 'units', 'kg', 'litre', 'meter', 'set'])
        self.unit_combo.setStyleSheet(input_style)
        c6.addWidget(self.unit_combo)
        row3.addLayout(c6)
        info_l.addLayout(row3)

        ld = QLabel("Description")
        ld.setStyleSheet(form_lbl_style)
        info_l.addWidget(ld)
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Description, specifications, compatible models...")
        self.desc_input.setMaximumHeight(60)
        self.desc_input.setStyleSheet(input_style)
        info_l.addWidget(self.desc_input)

        layout.addWidget(info_frame)

        if self.data:
            self.name_input.setText(self.data['part_name'])
            rate_val = float(self.data.get('default_rate', 0) or 0)
            self.rate_input.setValue(rate_val)
            self.stock_input.setValue(int(self.data.get('stock_quantity', 0) or 0))
            self.alert_input.setValue(int(self.data.get('stock_alert_level', 5) or 5))
            self.desc_input.setPlainText(self.data.get('description', '') or '')
            cat = self.data.get('category', 'General') or 'General'
            ci = self.category_combo.findText(cat)
            if ci >= 0:
                self.category_combo.setCurrentIndex(ci)
            unit = self.data.get('unit', 'pcs') or 'pcs'
            ui = self.unit_combo.findText(unit)
            if ui >= 0:
                self.unit_combo.setCurrentIndex(ui)

        # Buttons
        btn_l = QHBoxLayout()
        btn_l.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; color: {colors['muted']};
                border: 1px solid {colors['border']}; border-radius: 8px;
                padding: 10px 22px; font-size: 10pt; font-weight: 500;
            }}
            QPushButton:hover {{ background-color: {colors['hover']}; color: {colors['fg']}; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_l.addWidget(cancel_btn)
        save_btn = QPushButton("💾 Save Part")
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #34d399; color: #ffffff; border: none;
                border-radius: 8px; padding: 10px 28px; font-size: 10pt; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: #059669; }}
        """)
        save_btn.clicked.connect(self._save)
        btn_l.addWidget(save_btn)
        layout.addLayout(btn_l)

    def _mark_field_invalid(self, widget, invalid=True):
        colors = self.theme_manager.get_colors()
        if invalid:
            if not hasattr(self, '_saved_styles'):
                self._saved_styles = {}
            if widget not in self._saved_styles:
                self._saved_styles[widget] = widget.styleSheet()
            widget.setStyleSheet(f"""
                border: 2px solid {colors['danger']};
                background-color: rgba(248, 113, 113, 0.1);
            """)
        else:
            if hasattr(self, '_saved_styles') and widget in self._saved_styles:
                widget.setStyleSheet(self._saved_styles[widget])
            else:
                widget.setStyleSheet("")

    def _save(self):
        valid = True
        if not self.name_input.text().strip():
            self._mark_field_invalid(self.name_input)
            valid = False
        else:
            self._mark_field_invalid(self.name_input, False)
        
        if self.rate_input.value() <= 0:
            self._mark_field_invalid(self.rate_input)
            valid = False
        else:
            self._mark_field_invalid(self.rate_input, False)

        if not valid:
            QMessageBox.warning(self, "Validation Error", "Part name and rate are required")
            return

        from database.db_connection import DatabaseContext
        from controllers.inventory_controller import InventoryController
        data = {
            'name': self.name_input.text().strip(),
            'category': self.category_combo.currentText(),
            'rate': self.rate_input.value(),
            'stock_qty': self.stock_input.value(),
            'alert_level': self.alert_input.value(),
            'unit': self.unit_combo.currentText(),
            'description': self.desc_input.toPlainText().strip(),
        }
        with DatabaseContext() as db:
            ic = InventoryController(db)
            if self.data:
                ic.update_part(self.data['id'], data)
            else:
                ic.add_part(data)
        self.accept()


class StockAdjustDialog(QDialog):
    def __init__(self, parent, part, suggested_qty=None):
        super().__init__(parent)
        self.part = part
        self.suggested_qty = suggested_qty
        self.setWindowTitle(f"Adjust Stock: {part['part_name']}")
        self.setMinimumWidth(420)
        self.setMaximumWidth(500)
        self.theme_manager = UnifiedTheme()
        colors = self.theme_manager.get_colors()
        self.setStyleSheet(f"QDialog {{ background-color: {colors['bg']}; }}")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)
        colors = self.theme_manager.get_colors()

        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet(f"background: {colors['card_bg']}; border-radius: 10px; padding: 12px 16px;")
        header_l = QHBoxLayout(header_frame)
        header_l.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel("📦")
        icon_lbl.setStyleSheet("font-size: 22pt; background: transparent;")
        header_l.addWidget(icon_lbl)
        header_text = QVBoxLayout()
        header_text.setSpacing(2)
        title = QLabel(self.part['part_name'])
        title.setStyleSheet(f"font-size: 15pt; font-weight: 700; color: {colors['fg']}; background: transparent;")
        header_text.addWidget(title)
        stock_info = QLabel(f"Current: {self.part['stock_quantity']}  |  Alert: {self.part['stock_alert_level']}")
        stock_info.setStyleSheet(f"font-size: 8pt; color: {colors['muted']}; background: transparent;")
        header_text.addWidget(stock_info)
        header_l.addLayout(header_text)
        header_l.addStretch()
        layout.addWidget(header_frame)

        form_lbl_style = f"font-size: 9pt; font-weight: 600; color: {colors['fg']}; padding-right: 8px;"

        # Form section
        form_frame = QFrame()
        form_frame.setStyleSheet(f"background: {colors['card_bg']}; border: 1px solid {colors['border']}; border-radius: 10px; padding: 14px;")
        form_l = QVBoxLayout(form_frame)
        form_l.setSpacing(10)

        form_title = QLabel("✏️ Stock Adjustment")
        form_title.setStyleSheet(f"font-size: 10pt; font-weight: 700; color: {colors['primary']}; background: transparent; letter-spacing: 0.3px;")
        form_l.addWidget(form_title)

        ql = QLabel("Change Quantity (+ add / - remove)")
        ql.setStyleSheet(form_lbl_style)
        form_l.addWidget(ql)
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(-99999, 99999)
        if self.suggested_qty:
            self.qty_spin.setValue(self.suggested_qty)
            self.qty_spin.setPrefix("+")
        else:
            self.qty_spin.setValue(0)
        self.qty_spin.setStyleSheet(f"""
            QSpinBox {{ background: {colors['bg']}; color: {colors['fg']};
                border: 1px solid {colors['border']}; border-radius: 8px;
                padding: 9px 12px; font-size: 14pt; font-weight: bold; min-height: 24px; }}
            QSpinBox:focus {{ border: 1px solid {colors['primary']}; }}
        """)
        form_l.addWidget(self.qty_spin)

        rl = QLabel("Reason")
        rl.setStyleSheet(form_lbl_style)
        form_l.addWidget(rl)
        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("e.g., New shipment, Return, Damaged...")
        if self.suggested_qty:
            self.reason_input.setText("Reordered")
        self.reason_input.setStyleSheet(f"""
            QLineEdit {{ background: {colors['bg']}; color: {colors['fg']};
                border: 1px solid {colors['border']}; border-radius: 8px;
                padding: 9px 12px; font-size: 10pt; }}
            QLineEdit:focus {{ border: 1px solid {colors['primary']}; }}
        """)
        form_l.addWidget(self.reason_input)

        layout.addWidget(form_frame)

        # Preview
        preview_frame = QFrame()
        preview_frame.setStyleSheet(f"background: {colors['card_bg']}; border: 2px solid {colors['border']}; border-radius: 10px; padding: 14px;")
        preview_l = QVBoxLayout(preview_frame)
        preview_l.setSpacing(6)

        preview_title = QLabel("📊 Preview")
        preview_title.setStyleSheet(f"font-size: 9pt; font-weight: 700; color: {colors['muted']}; background: transparent; letter-spacing: 0.5px; text-transform: uppercase;")
        preview_l.addWidget(preview_title)

        preview_row = QHBoxLayout()
        old_q_lbl = QLabel(f"Current: {self.part['stock_quantity']}")
        old_q_lbl.setStyleSheet(f"font-size: 11pt; color: {colors['muted']}; background: transparent;")
        preview_row.addWidget(old_q_lbl)
        arrow_lbl = QLabel("→")
        arrow_lbl.setStyleSheet(f"font-size: 14pt; color: {colors['primary']}; background: transparent; padding: 0 8px;")
        preview_row.addWidget(arrow_lbl)
        self.new_qty_label = QLabel(f"{self.part['stock_quantity']}")
        self.new_qty_label.setStyleSheet(f"font-size: 18pt; font-weight: bold; color: {colors['primary']}; background: transparent;")
        preview_row.addWidget(self.new_qty_label)
        preview_row.addStretch()
        preview_l.addLayout(preview_row)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-size: 10pt; background: transparent;")
        preview_l.addWidget(self.status_label)

        self.qty_spin.valueChanged.connect(self._update_preview)
        layout.addWidget(preview_frame)

        # Buttons
        btn_l = QHBoxLayout()
        btn_l.addStretch()
        cancel_b = QPushButton("Cancel")
        cancel_b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_b.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {colors['muted']};
                border: 1px solid {colors['border']}; border-radius: 8px;
                padding: 10px 22px; font-size: 10pt; font-weight: 500;
            }}
            QPushButton:hover {{ background-color: {colors['hover']}; color: {colors['fg']}; }}
        """)
        cancel_b.clicked.connect(self.reject)
        btn_l.addWidget(cancel_b)
        save_b = QPushButton("✅ Apply Adjustment")
        save_b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_b.setStyleSheet(f"""
            QPushButton {{
                background-color: #34d399; color: #ffffff; border: none;
                border-radius: 8px; padding: 10px 28px; font-size: 10pt; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: #059669; }}
        """)
        save_b.clicked.connect(self._save)
        btn_l.addWidget(save_b)
        layout.addLayout(btn_l)

        self._update_preview()

    def _update_preview(self):
        colors = self.theme_manager.get_colors()
        change = self.qty_spin.value()
        new_qty = (self.part['stock_quantity'] or 0) + change
        if new_qty < 0:
            new_qty = 0
        self.new_qty_label.setText(f"New Quantity: {new_qty}")
        alert = self.part.get('stock_alert_level', 5) or 5
        if new_qty <= alert:
            self.status_label.setText("⚠️ Still below alert level - consider ordering more")
            self.status_label.setStyleSheet("font-size: 10pt; color: #f59e0b; background: transparent;")
        else:
            self.status_label.setText("✅ Stock level is healthy")
            self.status_label.setStyleSheet("font-size: 10pt; color: #34d399; background: transparent;")

    def _save(self):
        change = self.qty_spin.value()
        if change == 0:
            QMessageBox.warning(self, "No Change", "Quantity change cannot be 0")
            return
        reason = self.reason_input.text().strip() or 'Manual adjustment'
        from database.db_connection import DatabaseContext
        from controllers.inventory_controller import InventoryController
        with DatabaseContext() as db:
            InventoryController(db).adjust_stock(self.part['id'], change, reason)
        self.accept()
