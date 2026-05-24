"""
故事展示面板
滚动显示游戏故事，支持流式输出追加，加载中显示闪烁条带
"""
from PyQt5.QtWidgets import QTextEdit, QVBoxLayout, QWidget, QScrollBar
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QTextCursor, QColor, QPainter
from ui.theme_manager import get_theme


class _WaveBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._alpha = 0
        self._rising = True
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._pulse)
        self.setFixedHeight(4)

    def start(self):
        self._alpha = 30
        self._rising = True
        self._timer.start(40)
        self.show()

    def stop(self):
        self._timer.stop()
        self.hide()

    def _pulse(self):
        if self._rising:
            self._alpha += 10
            if self._alpha >= 200:
                self._alpha = 200
                self._rising = False
        else:
            self._alpha -= 10
            if self._alpha <= 30:
                self._alpha = 30
                self._rising = True
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        tm = get_theme()
        tc = tm.colors['text']
        col = QColor(int(tc[1:3], 16), int(tc[3:5], 16), int(tc[5:7], 16), self._alpha)
        painter.setBrush(col)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(4, 0, self.width() - 8, self.height(), 2, 2)
        painter.end()


class StoryPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._turn_separators = []
        self._streaming = False
        self._pending_chunks = []
        self.tm = get_theme()
        self._setup_ui()

    def _setup_ui(self):
        c = self.tm.colors
        fs = self.tm.font_size
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setFont(QFont("Microsoft YaHei", fs - 1))

        self.text_area.setStyleSheet(f"""
            QTextEdit {{
                background-color: {c['panel_bg']};
                color: {c['text']};
                border: 1px solid {c['border']};
                border-radius: 4px;
                padding: 12px;
                line-height: 1.8;
            }}
            QScrollBar:vertical {{
                background: {c['background']};
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: {c['border']};
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        layout.addWidget(self.text_area)
        self._wave_bar = _WaveBar(self)
        self._wave_bar.hide()
        layout.addWidget(self._wave_bar)

    def clear(self):
        self.text_area.clear()
        self._turn_separators = []

    def start_new_turn(self):
        self._streaming = False
        self._pending_chunks = []
        self._wave_bar.stop()
        self._turn_separators = []

    def begin_streaming(self):
        self._streaming = True
        self._pending_chunks = []
        self._wave_bar.start()

    def append_chunk(self, chunk: str):
        if self._streaming:
            self._pending_chunks.append(chunk)
            return
        cursor = self.text_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(chunk)
        scrollbar = self.text_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def end_streaming(self, full_text: str = None):
        self._streaming = False
        self._wave_bar.stop()
        if full_text is None:
            full_text = "".join(self._pending_chunks)
        self._pending_chunks = []
        if full_text:
            cursor = self.text_area.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.insertText(full_text)
            scrollbar = self.text_area.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def finalize_turn(self):
        cursor = self.text_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText("\n\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n")

    def set_style(self, font_size: int, bg_color: str, text_color: str):
        c = self.tm.colors
        self.text_area.setFont(QFont("Microsoft YaHei", font_size))
        self.text_area.setStyleSheet(f"""
            QTextEdit {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {c['border']};
                border-radius: 4px;
                padding: 12px;
                line-height: 1.8;
            }}
        """)
