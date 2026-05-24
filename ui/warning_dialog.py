"""
警告/免责声明界面
"""
import sys
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QCheckBox, QPushButton, QTextEdit)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from config import APP_NAME, VERSION, AUTHOR
from ui.theme_manager import get_theme


class WarningDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tm = get_theme()
        self.setWindowTitle(f"{APP_NAME} - 免责声明")
        self.setFixedSize(540, 380)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self._accepted = False
        self._setup_ui()

    def _setup_ui(self):
        c = self.tm.colors
        fs = self.tm.font_size
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(14)

        header = QLabel()
        header.setFixedHeight(44)
        header.setStyleSheet(f"""
            QLabel {{
                background-color: {c['danger']};
                border-radius: 6px;
                color: white;
                font-size: {fs + 4}px;
                font-weight: bold;
                padding: 0 16px;
            }}
        """)
        header.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setText(f"   {APP_NAME}  免责声明")
        layout.addWidget(header)

        warning_text = QTextEdit()
        warning_text.setReadOnly(True)
        warning_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {c['panel_bg']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                padding: 16px;
                color: {c['text']};
                font-size: {fs}px;
            }}
            QScrollBar:vertical {{
                background: {c['background']}; width: 8px; border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {c['border']}; border-radius: 4px; min-height: 20px;
            }}
        """)
        warning_text.setHtml(f"""
        <div style="color: {c['text']}; line-height: 2.0; margin: 0; padding: 0;">
            1. 本游戏的故事内容<b>完全由AI生成</b>，与程序作者无关。<br/>
            2. 用户应严格遵守所在地的<b style="color: {c['danger']};">法律法规</b>，否则后果自负。<br/>
            3. 使用AI服务会产生Token消耗，请注意<b style="color: {c['warning']};">消耗费用</b>。<br/>
            4. 请在DeepSeek开发平台获取API密钥。<br/>
            5. 程序作者保留一切权利。<br/>
            <br/>
            <span style="color: {c['text_dim']}; font-size: {fs}px;">
                {APP_NAME}（The Abyss Fables） 版本：{VERSION} | 作者：{AUTHOR}
            </span>
        </div>
        """)
        layout.addWidget(warning_text)

        self.checkbox = QCheckBox(" 我已阅读并理解以上声明，同意承担相关责任和费用")
        self.checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {c['text_dim']}; font-size: {fs}px; spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px; height: 18px;
                border: 1px solid {c['border']}; border-radius: 3px;
                background-color: {c['input_bg']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {c['success']}; border-color: {c['success']};
            }}
        """)
        layout.addWidget(self.checkbox)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        help_btn = QPushButton("获取密钥帮助")
        help_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; color: {c['accent']};
                border: 1px solid {c['accent']}; border-radius: 4px;
                padding: 8px 16px; font-size: {fs}px;
            }}
            QPushButton:hover {{ background-color: {self.tm.accent_rgba(0.15)}; }}
        """)
        help_btn.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://platform.deepseek.com")))
        btn_layout.addWidget(help_btn)

        btn_layout.addStretch()

        exit_btn = QPushButton("退出")
        exit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['border']}; color: white;
                border: none; border-radius: 4px;
                padding: 9px 24px; font-size: {fs}px;
            }}
            QPushButton:hover {{ background-color: {self.tm._hlight(c['border'])}; }}
        """)
        exit_btn.clicked.connect(self._on_exit)
        btn_layout.addWidget(exit_btn)

        self.continue_btn = QPushButton("确认并进入")
        self.continue_btn.setEnabled(False)
        self.continue_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['success']}; color: white;
                border: none; border-radius: 4px;
                padding: 9px 24px; font-size: {fs}px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {self.tm._hlight(c['success'])}; }}
            QPushButton:disabled {{ background-color: {c['border']}; color: {c['text_dim']}; }}
        """)
        self.continue_btn.clicked.connect(self._on_accept)
        btn_layout.addWidget(self.continue_btn)

        layout.addLayout(btn_layout)

        self.checkbox.stateChanged.connect(
            lambda state: self.continue_btn.setEnabled(state == Qt.Checked))

        self.setStyleSheet(self.tm.base_dialog_qss())

    def _on_exit(self):
        self._accepted = False
        self.reject()

    def _on_accept(self):
        self._accepted = True
        self.accept()

    @staticmethod
    def show_warning(parent=None) -> bool:
        dialog = WarningDialog(parent)
        dialog.exec_()
        return dialog._accepted
