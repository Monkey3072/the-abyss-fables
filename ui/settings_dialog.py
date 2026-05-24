"""
设置对话框
配置API、显示、音频等
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QComboBox, QPushButton, QFormLayout,
                             QGroupBox, QSpinBox, QMessageBox, QSlider,
                             QFileDialog, QScrollArea, QWidget)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from config import load_config, save_config, UI_COLORS, get_chinese_fonts
from ui.theme_manager import get_theme
from core.event_bus import event_bus


class SettingsDialog(QDialog):
    def __init__(self, game_engine, parent=None):
        super().__init__(parent)
        self.engine = game_engine
        self.config = load_config()
        self.tm = get_theme()
        self.tm.sync_from_engine(game_engine)
        self.setWindowTitle(" 设置")
        self.setFixedSize(620, 520)
        self._setup_ui()
        self._load_config()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(10, 8, 10, 10)

        api_group = QGroupBox(" DeepSeek API 设置")
        api_form = QFormLayout()
        api_form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        api_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        api_form.setHorizontalSpacing(16)

        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("https://api.deepseek.com")
        api_form.addRow(self._fmt("API地址："), self.base_url_edit)

        key_layout = QHBoxLayout()
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("输入你的API Key")
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        key_layout.addWidget(self.api_key_edit)
        self.show_key_btn = QPushButton("")
        self.show_key_btn.setFixedWidth(32)
        self.show_key_btn.clicked.connect(self._toggle_key)
        key_layout.addWidget(self.show_key_btn)
        api_form.addRow(self._fmt("API密钥："), key_layout)

        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.addItems(["deepseek-v4-flash", "deepseek-v4-pro",
                                    "deepseek-chat", "deepseek-reasoner"])
        api_form.addRow(self._fmt("模型名称："), self.model_combo)

        help_row = QHBoxLayout()
        help_btn = QPushButton("获取密钥帮助")
        help_btn.setFixedWidth(110)
        help_btn.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://platform.deepseek.com")))
        help_row.addWidget(help_btn)
        test_btn = QPushButton("测试连接")
        test_btn.setFixedWidth(80)
        test_btn.clicked.connect(self._test_connection)
        help_row.addWidget(test_btn)
        help_row.addStretch()
        api_form.addRow("", help_row)
        api_group.setLayout(api_form)
        content_layout.addWidget(api_group)

        display_group = QGroupBox(" 显示设置")
        display_form = QFormLayout()
        display_form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        display_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        display_form.setHorizontalSpacing(16)

        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["1280x720", "1920x1080", "1366x768",
                                         "1600x900", "2560x1440"])
        display_form.addRow(self._fmt("分辨率："), self.resolution_combo)

        self.font_spin = QSpinBox()
        self.font_spin.setRange(8, 24)
        self.font_spin.setValue(12)
        display_form.addRow(self._fmt("字体大小："), self.font_spin)

        self.font_combo = QComboBox()
        self._populate_fonts()
        display_form.addRow(self._fmt("字体样式："), self.font_combo)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(UI_COLORS.keys()))
        display_form.addRow(self._fmt("UI颜色："), self.theme_combo)

        bg_layout = QHBoxLayout()
        bg_layout.setSpacing(6)
        bg_layout.setContentsMargins(0, 0, 0, 0)
        self.bg_path_edit = QLineEdit()
        self.bg_path_edit.setPlaceholderText("留空使用默认背景")
        self.bg_path_edit.setReadOnly(True)
        bg_layout.addWidget(self.bg_path_edit)
        bg_browse_btn = QPushButton("选择图片")
        bg_browse_btn.setFixedWidth(80)
        bg_browse_btn.clicked.connect(self._browse_background)
        bg_layout.addWidget(bg_browse_btn)
        bg_clear_btn = QPushButton("清除")
        bg_clear_btn.setFixedWidth(50)
        bg_clear_btn.clicked.connect(self._clear_background)
        bg_layout.addWidget(bg_clear_btn)
        display_form.addRow(self._fmt("背景图片："), bg_layout)

        display_group.setLayout(display_form)
        content_layout.addWidget(display_group)

        audio_group = QGroupBox(" 音频设置")
        audio_form = QFormLayout()
        audio_form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        audio_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        audio_form.setHorizontalSpacing(16)

        self.music_slider = QSlider(Qt.Horizontal)
        self.music_slider.setRange(0, 100)
        self.music_slider.setValue(80)
        audio_form.addRow(self._fmt("音乐音量："), self.music_slider)

        self.sfx_slider = QSlider(Qt.Horizontal)
        self.sfx_slider.setRange(0, 100)
        self.sfx_slider.setValue(80)
        audio_form.addRow(self._fmt("音效音量："), self.sfx_slider)

        audio_note = QLabel("音频功能将在后续版本中实现")
        audio_note.setStyleSheet(f"color: {self.tm.colors['warning']}; font-size: {self.tm.font_size}px; padding-left: 80px;")
        audio_form.addRow("", audio_note)
        audio_group.setLayout(audio_form)
        content_layout.addWidget(audio_group)

        content_layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        save_btn = QPushButton(" 保存设置")
        save_btn.clicked.connect(self._save_settings)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.tm.colors['success']};
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: {self.tm.font_size}px;
            }}
            QPushButton:hover {{ background-color: {self.tm._hlight(self.tm.colors['success'])}; }}
        """)
        btn_layout.addWidget(save_btn)
        main_layout.addLayout(btn_layout)

        c = self.tm.colors
        fs = self.tm.font_size
        qss = self.tm.base_dialog_qss("""
            QGroupBox { padding-top: 14px; }
        """)
        self.setStyleSheet(qss)

        content.setStyleSheet(f"""
            QWidget {{
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
                background-color: {self.tm._hlight(c['accent'])};
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
        """)

    def _populate_fonts(self):
        for display_name, family_name in get_chinese_fonts():
            self.font_combo.addItem(display_name, family_name)

    def _fmt(self, text):
        lbl = QLabel(text)
        lbl.setFixedWidth(90)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return lbl

    def _load_config(self):
        api = self.config.get("api", {})
        self.base_url_edit.setText(api.get("base_url", "https://api.deepseek.com"))
        self.api_key_edit.setText(api.get("api_key", ""))
        idx = self.model_combo.findText(api.get("model", "deepseek-v4-flash"))
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)
        else:
            self.model_combo.setEditText(api.get("model", "deepseek-v4-flash"))
        display = self.config.get("display", {})
        idx = self.resolution_combo.findText(display.get("resolution", "1280x720"))
        if idx >= 0:
            self.resolution_combo.setCurrentIndex(idx)
        self.font_spin.setValue(display.get("font_size", 12))
        ff = display.get("font_family", "Microsoft YaHei")
        idx = self.font_combo.findData(ff)
        if idx >= 0:
            self.font_combo.setCurrentIndex(idx)
        idx = self.theme_combo.findText(display.get("ui_color", "暗夜蓝"))
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        self.bg_path_edit.setText(display.get("background_image", ""))
        audio = self.config.get("audio", {})
        self.music_slider.setValue(audio.get("music_volume", 80))
        self.sfx_slider.setValue(audio.get("sfx_volume", 80))

    def _browse_background(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择背景图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp);;所有文件 (*)"
        )
        if path:
            self.bg_path_edit.setText(path)

    def _clear_background(self):
        self.bg_path_edit.setText("")

    def _toggle_key(self):
        if self.api_key_edit.echoMode() == QLineEdit.Password:
            self.api_key_edit.setEchoMode(QLineEdit.Normal)
            self.show_key_btn.setText("")
        else:
            self.api_key_edit.setEchoMode(QLineEdit.Password)
            self.show_key_btn.setText("")

    def _test_connection(self):
        self.engine.update_api_config(
            api_key=self.api_key_edit.text(),
            base_url=self.base_url_edit.text(),
            model=self.model_combo.currentText() or "deepseek-v4-flash",
        )
        success, msg = self.engine.test_connection()
        if success:
            QMessageBox.information(self, "连接成功", f"API连接正常\n响应：{msg[:200]}")
        else:
            QMessageBox.critical(self, "连接失败", msg)

    def _save_settings(self):
        self.config["api"]["base_url"] = self.base_url_edit.text()
        self.config["api"]["api_key"] = self.api_key_edit.text()
        self.config["api"]["model"] = self.model_combo.currentText() or "deepseek-v4-flash"
        self.config["display"]["resolution"] = self.resolution_combo.currentText()
        self.config["display"]["font_family"] = self.font_combo.currentData() or "Microsoft YaHei"
        self.config["display"]["font_size"] = self.font_spin.value()
        self.config["display"]["ui_color"] = self.theme_combo.currentText()
        self.config["display"]["background_image"] = self.bg_path_edit.text()
        self.config["audio"]["music_volume"] = self.music_slider.value()
        self.config["audio"]["sfx_volume"] = self.sfx_slider.value()
        save_config(self.config)

        self.engine.config = self.config
        self.engine.update_api_config(
            api_key=self.api_key_edit.text(),
            base_url=self.base_url_edit.text(),
            model=self.model_combo.currentText() or "deepseek-v4-flash",
        )

        event_bus.apply_settings_requested.emit()
        self.accept()
