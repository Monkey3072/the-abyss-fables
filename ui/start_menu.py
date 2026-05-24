"""
开始菜单界面
背景使用start.png，覆盖可调色滤镜，支持分辨率自适应
左侧一级选项 + 右侧子内容，同色背景竖线分隔
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QSpacerItem, QSizePolicy,
                             QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QLinearGradient
from config import START_IMAGE, APP_NAME, VERSION
from config.io import load_config
from ui.theme_manager import get_theme


class StartMenu(QWidget):
    new_game_clicked = pyqtSignal()
    load_game_clicked = pyqtSignal()
    import_seed_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    tech_credit_clicked = pyqtSignal()

    def __init__(self, parent=None, font_size=12, colors=None):
        super().__init__(parent)
        self.bg_pixmap = None
        self.tm = get_theme()
        self._nav_buttons = []
        self._active_index = 0
        self._font_size = font_size
        self._colors = colors or {}
        c = self.tm.colors
        bg = QColor(c.get('background', colors.get('background', '#0a0a1a') if colors else '#0a0a1a'))
        bg.setAlpha(100)
        self.filter_color = bg
        self._load_background()
        self._setup_ui()

    def _load_background(self):
        custom_path = load_config().get("display", {}).get("background_image", "")
        if custom_path:
            from pathlib import Path
            p = Path(custom_path)
            if p.exists():
                self.bg_pixmap = QPixmap(str(p))
                return

        if START_IMAGE.exists():
            self.bg_pixmap = QPixmap(str(START_IMAGE))
            return

        c = self.tm.colors
        self.bg_pixmap = QPixmap(1280, 720)
        self.bg_pixmap.fill(QColor(c.get('background', '#0a0a1a')))
        painter = QPainter(self.bg_pixmap)
        gradient = QLinearGradient(0, 0, 0, 720)
        gradient.setColorAt(0, QColor(c.get('panel_bg', '#16213e')))
        gradient.setColorAt(1, QColor(c.get('background', '#0a0a1a')))
        painter.fillRect(0, 0, 1280, 720, gradient)
        painter.end()

    def _setup_ui(self):
        c = self.tm.colors
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        outer.addStretch(2)

        card = QFrame()
        card.setFixedSize(640, 320)
        panel_bg = c.get("panel_bg", "#16213e")
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {panel_bg};
                border-radius: 12px;
            }}
        """)

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        left_panel = self._build_left_panel()
        card_layout.addWidget(left_panel)

        divider = QFrame()
        divider.setFrameShape(QFrame.VLine)
        divider.setFixedWidth(1)
        divider_border = c.get("secondary", "#34495e")
        divider.setStyleSheet(f"color: {divider_border};")
        card_layout.addWidget(divider)

        right_panel = self._build_right_panel()
        card_layout.addWidget(right_panel, stretch=1)

        outer.addWidget(card, alignment=Qt.AlignCenter)
        outer.addStretch(3)

    def _build_left_panel(self):
        c = self.tm.colors
        fs = self.tm.font_size
        panel = QFrame()
        panel.setFixedWidth(190)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 24, 10, 20)
        layout.setSpacing(4)

        logo = QLabel(APP_NAME)
        logo.setFont(QFont("Microsoft YaHei", fs + 3, QFont.Bold))
        logo.setStyleSheet(f"color: {c.get('text', '#ecf0f1')};")
        layout.addWidget(logo)

        sub = QLabel("The Abyss Fables")
        sub.setStyleSheet(f"color: {c.get('text_dim', '#7f8c8d')}; font-size: {fs - 3}px; padding-bottom: 10px;")
        layout.addWidget(sub)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {c.get('secondary', '#34495e')};")
        layout.addWidget(sep)
        layout.addSpacing(6)

        nav_items = [
            ("🎮", "开始游戏", self._on_new_game),
            ("📂", "加载存档", self._on_load_game),
            ("🌱", "导入种子", self._on_import_seed),
            ("⚙️", "设置", self._on_settings),
            ("🔧", "技术支持", self._on_tech_credit),
        ]

        for i, (icon, label, handler) in enumerate(nav_items):
            btn = QPushButton(f" {icon}  {label}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(36)
            btn.clicked.connect(handler)
            self._nav_buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        ver = QLabel(f"v{VERSION}")
        ver.setStyleSheet(f"color: {c.get('text_dim', '#7f8c8d')}; font-size: {max(8, fs - 3)}px;")
        layout.addWidget(ver)

        self._update_nav(0)
        return panel

    def _update_nav(self, index: int):
        c = self.tm.colors
        fs = self.tm.font_size
        self._active_index = index
        accent = c.get("accent", "#3498db")
        text = c.get("text", "#ecf0f1")
        text_dim = c.get("text_dim", "#bdc3c7")
        for i, btn in enumerate(self._nav_buttons):
            if i == index:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        color: {text}; border: none; border-radius: 6px;
                        font-size: {fs}px; text-align: left;
                        background-color: {self.tm.accent_rgba(0.35)};
                        font-weight: bold; padding: 6px 10px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        color: {text_dim}; border: none; border-radius: 6px;
                        font-size: {fs}px; text-align: left;
                        background-color: transparent; padding: 6px 10px;
                    }}
                    QPushButton:hover {{
                        background-color: {self.tm.accent_rgba(0.2)};
                        color: {text};
                    }}
                """)

    def _build_right_panel(self):
        c = self.tm.colors
        fs = self.tm.font_size
        panel = QFrame()

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(28, 24, 20, 24)

        self.right_title = QLabel()
        self.right_title.setStyleSheet(f"color: {c.get('text', '#ecf0f1')}; font-size: {fs + 5}px; font-weight: bold;")
        layout.addWidget(self.right_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: transparent; width: 6px; margin: 2px 0 2px 0;
            }}
            QScrollBar::handle:vertical {{
                background: {c.get('secondary', '#34495e')};
                border-radius: 3px; min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        self.right_content = QLabel()
        self.right_content.setWordWrap(True)
        self.right_content.setStyleSheet(f"color: {c.get('text_dim', '#bdc3c7')}; font-size: {fs}px; line-height: 1.8;")
        self.right_content.setAlignment(Qt.AlignTop)
        self.right_content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll.setWidget(self.right_content)
        layout.addWidget(scroll, stretch=1)

        self._show_welcome()
        return panel

    def _show_welcome(self):
        self.right_title.setText("🏰 欢迎来到渊索寓言")
        self.right_content.setText(
            "一个由 AI 驱动的无限文字冒险世界。\n\n"
            "在这里，你可以：\n"
            "• 自由创造任何类型的故事世界\n"
            "• 扮演你心中的角色，做出关键抉择\n"
            "• 与 AI 共同编织独一无二的剧情\n"
            "• 保存、分享和重玩你的冒险\n\n"
            "点击左侧菜单开始你的旅程吧 ✨"
        )

    def _on_new_game(self):
        self._update_nav(0)
        self.right_title.setText("🎮 开始游戏")
        self.right_content.setText(
            "创建你的冒险世界。\n\n"
            "在种子编辑器中，你可以设定：\n"
            "• 故事类型与风格\n"
            "• 主角设定与背景\n"
            "• 世界观与规则\n"
            "• AI 倾向与道德要求\n\n"
            "也可以留空，让 AI 为你随机生成。"
        )
        self.new_game_clicked.emit()

    def _on_load_game(self):
        self._update_nav(1)
        self.right_title.setText("📂 加载存档")
        self.right_content.setText(
            "从之前的游戏进度继续冒险。\n\n"
            "存档文件保存在 saves 目录下，\n"
            "选择存档后将恢复全部游戏状态。"
        )
        self.load_game_clicked.emit()

    def _on_import_seed(self):
        self._update_nav(2)
        self.right_title.setText("🌱 导入种子文件")
        self.right_content.setText(
            "导入 .seed 种子文件来开始预设的故事。\n\n"
            "种子文件包含完整的世界设定和角色信息。\n"
            "支持明文和加密两种格式。"
        )
        self.import_seed_clicked.emit()

    def _on_settings(self):
        self._update_nav(3)
        self.right_title.setText("⚙️ 设置")
        self.right_content.setText(
            "配置游戏参数。\n\n"
            "• API 连接：设置 DeepSeek 密钥和模型\n"
            "• 显示：调整分辨率、字体大小和主题\n"
            "• 音频：音量控制\n\n"
            "首次使用请务必先配置 API 密钥。"
        )
        self.settings_clicked.emit()

    def _on_tech_credit(self):
        self._update_nav(4)
        self.right_title.setText("🔧 技术支持")
        self.right_content.setText(
            "本游戏由以下技术构建：\n\n"
            "▸ Python — 编程语言\n"
            "  (PSF License, python.org)\n\n"
            "▸ PyQt5 — 图形界面框架\n"
            "  (GPL / Riverbank Computing)\n\n"
            "▸ Trae IDE — 集成开发环境\n"
            "  (trae.ai)\n\n"
            "▸ DeepSeek — AI 大语言模型\n"
            "  (deepseek.com)\n\n"
            "▸ openai — API 客户端库\n"
            "  (MIT License)\n\n"
            "▸ loguru — 结构化日志\n"
            "  (MIT License)\n\n"
            "▸ cryptography — 加密库\n"
            "  (Apache 2.0 / PSF)\n\n"
            "▸ pydantic — 数据校验\n"
            "  (MIT License)\n\n"
            "▸ tiktoken — Token 预估\n"
            "  (MIT License)\n\n"
            "▸ qasync — Qt 异步事件循环\n"
            "  (BSD License)\n\n"
            "▸ ChatGPT — AI 图片生成\n"
            "  (openai.com)\n\n"
            "▸ DouBao (豆包) — AI 图片生成\n"
            "  (bytedance.com)\n\n"
            "开发者：Monkey3072\n"
            "感谢所有开源项目及其贡献者。"
        )
        self.tech_credit_clicked.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        if self.bg_pixmap:
            scaled = self.bg_pixmap.scaled(
                self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

        painter.setBrush(self.filter_color)
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())
        painter.end()
