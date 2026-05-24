"""
全局主题管理器（单例）
所有窗口统一获取颜色、字体、QSS的唯一入口
"""
from PyQt5.QtWidgets import QWidget, QLabel, QCheckBox, QPushButton
from PyQt5.QtWidgets import QLineEdit, QTextEdit, QComboBox, QSpinBox, QListWidget
from PyQt5.QtGui import QFont
from config.themes import UI_COLORS, CURRENT_THEME


class ThemeManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._colors = UI_COLORS.get("暗夜蓝", UI_COLORS["暗夜蓝"])
            cls._instance._font_family = "Microsoft YaHei"
            cls._instance._font_size = 12
        return cls._instance

    @property
    def colors(self):
        return self._colors

    @property
    def font_family(self):
        return self._font_family

    @property
    def font_size(self):
        return self._font_size

    def sync_from_engine(self, engine):
        theme = engine.config.get("display", {}).get("ui_color", "暗夜蓝")
        self._colors = UI_COLORS.get(theme, UI_COLORS["暗夜蓝"])
        self._font_family = engine.config.get("display", {}).get("font_family", "Microsoft YaHei")
        self._font_size = engine.config.get("display", {}).get("font_size", 12)
        CURRENT_THEME = theme

    def make_font(self, delta=0):
        return QFont(self._font_family, self._font_size + delta)

    def make_bold_font(self, delta=0):
        f = QFont(self._font_family, self._font_size + delta)
        f.setBold(True)
        return f

    def base_dialog_qss(self, extra=""):
        c = self._colors
        fs = self._font_size
        return f"""
            QDialog {{
                background-color: {c['background']};
            }}
            QLabel {{
                color: {c['text']};
                font-size: {fs}px;
            }}
            QGroupBox {{
                color: {c['text']};
                font-size: {fs + 1}px;
                font-weight: bold;
                border: 1px solid {c['border']};
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 14px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
            }}
            QLineEdit, QTextEdit, QComboBox, QSpinBox {{
                background-color: {c['input_bg']};
                color: {c['text']};
                font-size: {fs}px;
                border: 1px solid {c['border']};
                border-radius: 3px;
                padding: 5px 6px;
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border-color: {c['accent']};
            }}
            QComboBox QAbstractItemView {{
                background-color: {c['panel_bg']};
                color: {c['text']};
                selection-background-color: {c['accent']};
            }}
            QPushButton {{
                background-color: {c['accent']};
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 14px;
                font-size: {fs}px;
            }}
            QPushButton:hover {{
                background-color: {self._hlight(c['accent'])};
            }}
            QScrollArea {{
                border: none;
                background: transparent;
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
            QSlider::groove:horizontal {{
                height: 6px;
                background: {c['border']};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {c['accent']};
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }}
            QListWidget {{
                background-color: {c['panel_bg']};
                color: {c['text']};
                border: none;
            }}
            QListWidget::item {{
                padding: 4px;
                border-bottom: 1px solid {c['secondary']};
            }}
            QListWidget::item:hover {{
                background-color: {c['secondary']};
            }}
            QListWidget::item:selected {{
                background-color: {c['accent']};
            }}
            QCheckBox {{
                color: {c['text']};
                font-size: {fs}px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {c['border']};
                border-radius: 3px;
                background-color: {c['input_bg']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {c['accent']};
                border-color: {c['accent']};
            }}
            {extra}
        """

    def dark_panel_qss(self):
        c = self._colors
        return f"""
            QFrame {{
                background-color: {c['panel_bg']};
                border-radius: 8px;
            }}
        """

    @property
    def global_qss(self):
        c = self._colors
        fs = self._font_size
        return f"""
            QMessageBox {{
                background-color: {c['background']};
                color: {c['text']};
                font-size: {fs}px;
            }}
            QMessageBox QLabel {{
                color: {c['text']};
                font-size: {fs}px;
            }}
            QMessageBox QPushButton {{
                background-color: {c['accent']};
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 16px;
                font-size: {fs}px;
                min-width: 60px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {self._hlight(c['accent'])};
            }}
            QInputDialog {{
                background-color: {c['background']};
                color: {c['text']};
                font-size: {fs}px;
            }}
            QInputDialog QLabel {{
                color: {c['text']};
                font-size: {fs}px;
            }}
            QInputDialog QLineEdit, QInputDialog QTextEdit, QInputDialog QPlainTextEdit {{
                background-color: {c['input_bg']};
                color: {c['text']};
                border: 1px solid {c['border']};
                border-radius: 3px;
                padding: 5px 6px;
                font-size: {fs}px;
            }}
            QInputDialog QPushButton {{
                background-color: {c['accent']};
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 16px;
                font-size: {fs}px;
                min-width: 60px;
            }}
            QInputDialog QPushButton:hover {{
                background-color: {self._hlight(c['accent'])};
            }}
        """

    def apply_to_widget(self, widget):
        c = self._colors
        if isinstance(widget, QLabel):
            return
        if isinstance(widget, QCheckBox):
            widget.setStyleSheet(f"""
                QCheckBox {{
                    color: {c['text']};
                    font-size: {self._font_size}px;
                    spacing: 8px;
                }}
                QCheckBox::indicator {{
                    width: 16px; height: 16px;
                    border: 1px solid {c['border']};
                    border-radius: 3px;
                    background-color: {c['input_bg']};
                }}
                QCheckBox::indicator:checked {{
                    background-color: {c['accent']};
                    border-color: {c['accent']};
                }}
            """)
        elif isinstance(widget, (QLineEdit, QTextEdit)):
            widget.setStyleSheet(f"""
                background-color: {c['input_bg']};
                color: {c['text']};
                border: 1px solid {c['border']};
                border-radius: 3px;
                padding: 5px 6px;
                font-size: {self._font_size}px;
            """)
        elif isinstance(widget, (QComboBox, QSpinBox)):
            widget.setStyleSheet(f"""
                background-color: {c['input_bg']};
                color: {c['text']};
                border: 1px solid {c['border']};
                border-radius: 3px;
                padding: 5px 6px;
                font-size: {self._font_size}px;
            """)
        elif isinstance(widget, QListWidget):
            widget.setStyleSheet(f"""
                QListWidget {{
                    background-color: {c['panel_bg']};
                    color: {c['text']};
                    border: none;
                    font-size: {self._font_size}px;
                }}
                QListWidget::item {{
                    padding: 4px;
                    border-bottom: 1px solid {c['secondary']};
                }}
                QListWidget::item:hover {{ background-color: {c['secondary']}; }}
                QListWidget::item:selected {{ background-color: {c['accent']}; }}
            """)

        f = QFont(self._font_family, self._font_size)
        widget.setFont(f)

        for child in widget.children():
            if isinstance(child, QWidget) and not child.isWindow():
                self.apply_to_widget(child)

    def _hlight(self, hex_color):
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            r = min(255, r + 40)
            g = min(255, g + 40)
            b = min(255, b + 40)
            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, IndexError):
            return hex_color

    def accent_rgba(self, alpha=0.35):
        c = self.colors['accent']
        r, g, b = int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"


def get_theme():
    return ThemeManager()
