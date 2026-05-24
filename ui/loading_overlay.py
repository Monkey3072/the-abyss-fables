from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen
from ui.theme_manager import get_theme


class SpinnerWidget(QWidget):
    def __init__(self, parent=None, color="", size=40):
        super().__init__(parent)
        tm = get_theme()
        self._color = QColor(color or tm.colors['accent'])
        self._size = size
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self.setFixedSize(size + 8, size + 8)

    def start(self):
        self._angle = 0
        self._timer.start(30)
        self.show()

    def stop(self):
        self._timer.stop()
        self.hide()

    def _rotate(self):
        self._angle = (self._angle + 15) % 360
        self.update()

    def paintEvent(self, event):
        import math
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2
        r = self._size / 2
        for i in range(8):
            alpha = max(30, 255 - i * 30)
            a_rad = math.radians(self._angle - i * 20)
            x1 = cx + r * 0.3 * math.cos(a_rad)
            y1 = cy + r * 0.3 * math.sin(a_rad)
            x2 = cx + r * 0.7 * math.cos(a_rad)
            y2 = cy + r * 0.7 * math.sin(a_rad)
            col = QColor(self._color)
            col.setAlpha(alpha)
            painter.setPen(QPen(col, 2.5))
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        painter.end()


class LoadingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tm = get_theme()
        c = self.tm.colors
        fs = self.tm.font_size
        self.setStyleSheet("background-color: rgba(0,0,0,0.6);")
        self.setVisible(False)

        outer_layout = QVBoxLayout(self)
        outer_layout.setAlignment(Qt.AlignCenter)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        self._content_card = QWidget()
        pb = c['panel_bg']
        pbr, pbg, pbb = int(pb[1:3], 16), int(pb[3:5], 16), int(pb[5:7], 16)
        border_c = c['border']
        border_r, border_g, border_b = int(border_c[1:3], 16), int(border_c[3:5], 16), int(border_c[5:7], 16)
        self._content_card.setStyleSheet(f"""
            background-color: rgba({pbr}, {pbg}, {pbb}, 0.85);
            border: 1px solid rgba({border_r}, {border_g}, {border_b}, 0.3);
            border-radius: 12px;
        """)
        self._content_card.setMinimumWidth(280)
        self._content_card.setMaximumWidth(380)

        card_layout = QVBoxLayout(self._content_card)
        card_layout.setAlignment(Qt.AlignCenter)
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(32, 28, 32, 28)

        self._spinner = SpinnerWidget(self._content_card, color=c['accent'], size=44)
        spinner_container = QWidget()
        spinner_layout = QVBoxLayout(spinner_container)
        spinner_layout.setAlignment(Qt.AlignCenter)
        spinner_layout.addWidget(self._spinner)
        card_layout.addWidget(spinner_container)

        self._label = QLabel("请稍候...")
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet(f"color: {c['text']}; font-size: {fs}px; background: transparent;")
        self._label.setWordWrap(True)
        card_layout.addWidget(self._label)

        outer_layout.addWidget(self._content_card)

    def show_with_text(self, text: str, accent_color: str = ""):
        self._spinner._color = QColor(accent_color or self.tm.colors['accent'])
        self._label.setText(text)
        if self.parent():
            self.setGeometry(self.parent().rect())
        self.show()
        self._spinner.start()

    def update_text(self, text: str):
        self._label.setText(text)

    def hide_overlay(self):
        self._spinner.stop()
        self.hide()

    def resizeEvent(self, event):
        if self.parent():
            self.setGeometry(self.parent().rect())
        super().resizeEvent(event)
