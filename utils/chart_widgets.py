from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient, QConicalGradient, QBrush
from utils.app_settings import get_setting
import math


class BarChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = []
        self.currency_symbol = get_setting("currency_symbol", "₹")
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_data(self, data):
        self.data = data
        self.update()

    def _draw_empty_state(self, p):
        """Draw a centered empty-state message when there is no data"""
        p.setPen(QPen(QColor(148, 163, 184), 1))
        font = QFont("Segoe UI", 10)
        p.setFont(font)
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No data available yet")

    def paintEvent(self, event):
        if not self.data:
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            self._draw_empty_state(p)
            p.end()
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        margin_left = 50
        margin_right = 24
        margin_top = 28
        margin_bottom = 44

        chart_w = w - margin_left - margin_right
        chart_h = h - margin_top - margin_bottom

        if chart_w < 10 or chart_h < 10:
            p.end()
            return

        values = [float(d.get('value') or 0) for d in self.data]
        max_val = max(values) if values else 1

        if max_val <= 0:
            self._draw_empty_state(p)
            p.end()
            return
        min_val = 0.0
        val_range = max_val - min_val if max_val != min_val else 1

        n = len(self.data)
        bar_width = max(chart_w / n * 0.5, 4)
        gap = chart_w / n * 0.5

        # Dashed grid lines
        pen_grid = QPen(QColor(51, 65, 85), 1)
        pen_grid.setStyle(Qt.PenStyle.DashLine)
        p.setPen(pen_grid)
        num_grid = 4
        for i in range(num_grid + 1):
            y = margin_top + chart_h - (chart_h * i / num_grid)
            if i > 0:
                p.drawLine(int(margin_left), int(y), int(w - margin_right), int(y))
            val = min_val + (val_range * i / num_grid)
            p.setPen(QPen(QColor(100, 116, 139), 1))
            font = QFont("Segoe UI", 7)
            p.setFont(font)
            p.drawText(QRectF(0, int(y - 8), margin_left - 8, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"{self.currency_symbol}{val:,.0f}")
            p.setPen(pen_grid)

        # Bottom axis line
        p.setPen(QPen(QColor(71, 85, 105), 1))
        p.drawLine(int(margin_left), int(margin_top + chart_h), int(w - margin_right), int(margin_top + chart_h))

        # Bars
        for i, item in enumerate(self.data):
            val = float(item.get('value') or 0)
            label = item.get('label', '')
            bar_h = max((val - min_val) / val_range * chart_h, 2)
            x = margin_left + i * (bar_width + gap) + gap / 2
            y = margin_top + chart_h - bar_h

            color = item.get('color', QColor(34, 211, 238))
            if isinstance(color, str):
                color = QColor(color)

            # Gradient bar
            gradient = QLinearGradient(x, y, x, margin_top + chart_h)
            gradient.setColorAt(0, color.lighter(140))
            gradient.setColorAt(0.5, color)
            gradient.setColorAt(1, color.darker(130))
            p.setBrush(QBrush(gradient))
            p.setPen(QPen(color.darker(140), 1))
            p.drawRoundedRect(QRectF(x, y, bar_width, bar_h), 3, 3)

            # Bar highlight (top glow)
            glow_h = min(bar_h * 0.3, 18)
            glow = QLinearGradient(x, y, x, y + glow_h)
            glow.setColorAt(0, QColor(255, 255, 255, 50))
            glow.setColorAt(1, QColor(255, 255, 255, 0))
            p.setBrush(QBrush(glow))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRectF(x, y, bar_width, glow_h), 3, 3)

            # Value on top
            if bar_h > 22:
                p.setPen(QPen(color.lighter(160), 1))
                font = QFont("Segoe UI", 7, QFont.Weight.Bold)
                p.setFont(font)
                p.drawText(QRectF(int(x), int(y - 16), int(bar_width), 14), Qt.AlignmentFlag.AlignCenter, f"{self.currency_symbol}{val:,.0f}")

            # X-axis label
            p.setPen(QPen(QColor(148, 163, 184), 1))
            font = QFont("Segoe UI", 6 if n > 14 else 7)
            p.setFont(font)
            p.drawText(QRectF(int(x - 8), int(margin_top + chart_h + 5), int(bar_width + 16), 36), Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop, label)

        # "0" label at bottom
        p.setPen(QPen(QColor(100, 116, 139), 1))
        font = QFont("Segoe UI", 7)
        p.setFont(font)
        p.drawText(QRectF(0, int(margin_top + chart_h - 8), margin_left - 8, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"{self.currency_symbol}0")

        p.end()


class PieChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = []
        self.currency_symbol = get_setting("currency_symbol", "₹")
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_data(self, data):
        self.data = data
        self.update()

    def paintEvent(self, event):
        if not self.data:
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        total = sum(float(d.get('value') or 0) for d in self.data)
        if total == 0:
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No data")
            p.end()
            return

        # Pie - centered, proportional
        pie_size = min(w * 0.55, h * 0.85)
        pie_x = (w * 0.5 - pie_size) / 2
        pie_y = (h - pie_size) / 2

        # Shadow
        p.setBrush(QBrush(QColor(0, 0, 0, 50)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(pie_x + 3, pie_y + 3, pie_size, pie_size))

        start_angle = 90 * 16

        for i, item in enumerate(self.data):
            color = item.get('color', '#3498db')
            if isinstance(color, str):
                color = QColor(color)
            val = float(item.get('value') or 0)
            span = val / total * 360 * 16

            gradient = QConicalGradient(pie_x + pie_size / 2, pie_y + pie_size / 2, start_angle / 16)
            gradient.setColorAt(0, color.lighter(130))
            gradient.setColorAt(0.5, color)
            gradient.setColorAt(1, color.darker(130))
            p.setBrush(QBrush(gradient))
            p.setPen(QPen(color.darker(160), 1))
            p.drawPie(QRectF(pie_x, pie_y, pie_size, pie_size), int(start_angle), int(span))

            start_angle += int(span)

        # Center donut hole
        center_color = QColor(15, 23, 42)
        p.setBrush(QBrush(center_color))
        inner_size = pie_size * 0.42
        inner_x = pie_x + (pie_size - inner_size) / 2
        inner_y = pie_y + (pie_size - inner_size) / 2
        p.setPen(QPen(QColor(51, 65, 85), 2))
        p.drawEllipse(QRectF(inner_x, inner_y, inner_size, inner_size))

        # Center text
        p.setPen(QPen(QColor(255, 255, 255), 1))
        font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        p.setFont(font)
        p.drawText(QRectF(inner_x, inner_y + 2, inner_size, inner_size * 0.5), Qt.AlignmentFlag.AlignCenter, f"{self.currency_symbol}{total:,.0f}")

        p.setPen(QPen(QColor(148, 163, 184), 1))
        font = QFont("Segoe UI", 8)
        p.setFont(font)
        p.drawText(QRectF(inner_x, inner_y + inner_size * 0.5, inner_size, 18), Qt.AlignmentFlag.AlignCenter, "Total")

        p.end()


class HorizontalBarChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = []
        self.currency_symbol = get_setting("currency_symbol", "₹")
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_data(self, data):
        self.data = data
        self.update()

    def _draw_empty_state(self, p):
        """Draw a centered empty-state message when there is no data"""
        p.setPen(QPen(QColor(148, 163, 184), 1))
        font = QFont("Segoe UI", 10)
        p.setFont(font)
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No data available yet")

    def paintEvent(self, event):
        if not self.data:
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            self._draw_empty_state(p)
            p.end()
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        margin_left = 130
        margin_right = 70
        margin_top = 16
        margin_bottom = 20

        chart_w = w - margin_left - margin_right
        chart_h = h - margin_top - margin_bottom

        if chart_w < 10 or chart_h < 10:
            p.end()
            return

        values = [float(d.get('value') or 0) for d in self.data]
        max_val = max(values) if values else 1.0

        if max_val <= 0:
            self._draw_empty_state(p)
            p.end()
            return

        n = len(self.data)
        bar_h = min(chart_h / n * 0.55, 28)
        gap = min(chart_h / n * 0.4, 14)

        total_chart_h = n * (bar_h + gap)
        start_y = margin_top + (chart_h - total_chart_h) / 2

        # Dashed grid lines
        pen_grid = QPen(QColor(51, 65, 85), 1)
        pen_grid.setStyle(Qt.PenStyle.DashLine)
        p.setPen(pen_grid)
        for i in range(5):
            x = margin_left + chart_w * i / 4
            if i > 0:
                p.drawLine(int(x), margin_top, int(x), margin_top + chart_h)
            val = max_val * i / 4
            p.setPen(QPen(QColor(100, 116, 139), 1))
            font = QFont("Segoe UI", 7)
            p.setFont(font)
            p.drawText(QRectF(int(x - 30), int(margin_top + chart_h + 2), 60, 15), Qt.AlignmentFlag.AlignCenter, f"{self.currency_symbol}{val:,.0f}")
            p.setPen(pen_grid)

        # Axis lines
        p.setPen(QPen(QColor(71, 85, 105), 1))
        p.drawLine(int(margin_left), int(margin_top + chart_h), int(w - margin_right), int(margin_top + chart_h))
        p.drawLine(int(margin_left), margin_top, int(margin_left), int(margin_top + chart_h))

        for i, item in enumerate(self.data):
            val = float(item.get('value') or 0)
            bar_w = (val / max_val) * chart_w if max_val > 0 else 0
            y = start_y + i * (bar_h + gap)

            color = item.get('color', '#3498db')
            if isinstance(color, str):
                color = QColor(color)

            # Gradient bar
            gradient = QLinearGradient(margin_left, y, margin_left + bar_w, y)
            gradient.setColorAt(0, color.lighter(140))
            gradient.setColorAt(0.5, color)
            gradient.setColorAt(1, color.darker(120))
            p.setBrush(QBrush(gradient))
            p.setPen(QPen(color.darker(140), 1))
            p.drawRoundedRect(QRectF(margin_left, y, bar_w, bar_h), 3, 3)

            # Highlight on top
            if bar_w > 8:
                p.fillRect(QRectF(margin_left, y, bar_w, bar_h * 0.35), QColor(255, 255, 255, 28))

            # Label
            p.setPen(QPen(QColor(226, 232, 240), 1))
            font = QFont("Segoe UI", 8, QFont.Weight.Bold)
            p.setFont(font)
            label = item.get('label', '')
            if len(label) > 18:
                label = label[:16] + '..'
            p.drawText(QRectF(2, int(y), int(margin_left - 10), int(bar_h)), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label)

            # Value
            if bar_w > 30:
                p.setPen(QPen(QColor(255, 255, 255), 1))
                font = QFont("Segoe UI", 8, QFont.Weight.Bold)
                p.setFont(font)
                p.drawText(QRectF(int(margin_left + bar_w + 6), int(y), 80, int(bar_h)), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"{self.currency_symbol}{val:,.0f}")

        p.end()
