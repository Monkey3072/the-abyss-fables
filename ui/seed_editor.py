"""
种子编辑器界面
左侧分类导航 + 右侧表单内容
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QTextEdit, QComboBox, QPushButton,
                             QFormLayout, QFileDialog, QMessageBox, QFrame,
                             QScrollArea, QProgressDialog, QApplication, QWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPainter, QColor
from core.seed_manager import SeedManager
from ui.theme_manager import get_theme
from ui.loading_overlay import LoadingOverlay


def _lighten(hex_color: str, factor: float = 0.55) -> str:
    try:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        return f"#{r:02x}{g:02x}{b:02x}"
    except (ValueError, IndexError):
        return hex_color


class SeedGenWorker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, ai_client, prompt):
        super().__init__()
        self.ai_client = ai_client
        self.prompt = prompt

    def run(self):
        try:
            response = self.ai_client.chat(
                system_prompt="你是一个专业的游戏策划和故事创作AI，善于创造引人入胜的故事设定。",
                user_prompt=self.prompt,
            )
            self.finished.emit(response)
        except Exception as e:
            self.error.emit(str(e))


class SeedEditorDialog(QDialog):
    def __init__(self, ai_client=None, parent=None):
        super().__init__(parent)
        self.seed_manager = SeedManager()
        self.ai_client = ai_client
        self._seed = None
        self._result_seed = None
        self._nav_buttons = []
        self._active_nav = 0
        self._custom_edits = {}
        self._encrypted_seed_bytes = None
        self._encrypted_seed_path = None
        self._password_verified = False
        self._lock_status_label = None
        self._password_confirm_btn = None
        self._locked_tabs = set()
        self.tm = get_theme()
        self.setWindowTitle("种子编辑器")
        self.setMinimumSize(720, 540)
        self._setup_ui()

    @property
    def _cs(self):
        c = self.tm.colors
        return {
            **c,
            "input_lit": _lighten(c["input_bg"], 0.40),
        }

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        left = self._build_nav()
        main_layout.addWidget(left)
        divider = QFrame()
        divider.setFrameShape(QFrame.VLine)
        divider.setFixedWidth(1)
        divider.setStyleSheet(f"color: {self.tm.colors['border']};")
        main_layout.addWidget(divider)
        main_layout.addWidget(self._build_content(), stretch=1)
        self.setStyleSheet(self.tm.base_dialog_qss())
        self._update_nav(0)

    def _build_nav(self):
        c = self.tm.colors
        panel = QFrame()
        panel.setFixedWidth(150)
        panel.setStyleSheet(f"QFrame {{ background-color: {c['input_bg']}; border-radius: 8px 0 0 8px; }}")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 16, 6, 16)
        layout.setSpacing(4)
        title = QLabel(" 种子编辑器")
        title.setStyleSheet(f"color: {c['text']}; font-size: {self.tm.font_size + 4}px; font-weight: bold; padding: 4px 2px;")
        layout.addWidget(title)
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {c['border']};")
        layout.addWidget(sep)
        layout.addSpacing(4)
        nav_items = [("基本信息",), ("主角设定",), ("世界与规则",), ("备注",)]
        for i, (label,) in enumerate(nav_items):
            btn = QPushButton(f"  {label}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(32)
            idx = i
            btn.clicked.connect(lambda checked, x=idx: self._switch_page(x))
            self._nav_buttons.append(btn)
            layout.addWidget(btn)
        layout.addStretch()
        tool_btns = [
            (" 导入", self._import_seed),
            (" AI生成", self._auto_generate),
            (" 导出", self._export_seed),
        ]
        for text_text, handler in tool_btns:
            btn = QPushButton(text_text)
            btn.setFixedHeight(28)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent; color: {c['text_dim']};
                    border: 1px solid {c['border']}; border-radius: 3px;
                    font-size: {self.tm.font_size}px; padding: 2px 6px;
                }}
                QPushButton:hover {{ background-color: {c['border']}; color: {c['text']}; }}
            """)
            btn.clicked.connect(handler)
            layout.addWidget(btn)
        return panel

    def _update_nav(self, index: int):
        c = self.tm.colors
        fs = self.tm.font_size
        self._active_nav = index
        for i, btn in enumerate(self._nav_buttons):
            if i == index:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        color: {c['text']}; border: none; border-radius: 5px;
                        font-size: {fs}px; text-align: left;
                        background-color: {self.tm.accent_rgba(0.35)};
                        font-weight: bold; padding: 4px 8px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        color: {c['text_dim']}; border: none; border-radius: 5px;
                        font-size: {fs}px; text-align: left;
                        background-color: transparent; padding: 4px 8px;
                    }}
                    QPushButton:hover {{
                        background-color: {self.tm.accent_rgba(0.2)}; color: {c['text']};
                    }}
                """)

    def _build_content(self):
        c = self.tm.colors
        fs = self.tm.font_size
        panel = QFrame()
        panel.setStyleSheet(f"QFrame {{ background-color: {c['panel_bg']}; border-radius: 0 8px 8px 0; }}")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 16, 20, 12)
        self.page_title = QLabel(" 基本信息")
        self.page_title.setStyleSheet(f"color: {c['text']}; font-size: {fs + 4}px; font-weight: bold;")
        layout.addWidget(self.page_title)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.pages_widget = QFrame()
        self.pages_layout = QVBoxLayout(self.pages_widget)
        self.pages_layout.setContentsMargins(0, 4, 0, 4)
        self.pages_layout.setSpacing(8)
        self._build_basic_page()
        self._build_char_page()
        self._build_world_page()
        self._build_notes_page()
        for i in range(self.pages_layout.count()):
            w = self.pages_layout.itemAt(i).widget()
            if w:
                w.setVisible(i == 0)
        scroll.setWidget(self.pages_widget)
        layout.addWidget(scroll, stretch=1)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        start_btn = QPushButton(" 开始游戏")
        start_btn.clicked.connect(self._start_game)
        start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['success']}; color: white;
                font-weight: bold; padding: 8px 20px; border-radius: 4px;
                font-size: {fs}px;
            }}
            QPushButton:hover {{ background-color: {self.tm._hlight(c['success'])}; }}
        """)
        btn_layout.addWidget(start_btn)
        layout.addLayout(btn_layout)
        return panel

    def _make_form(self):
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(7)
        return form

    def _add_row(self, form, label_text, widget):
        c = self.tm.colors
        fs = self.tm.font_size
        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"color: {c['text']}; font-size: {fs}px;")
        lbl.setFont(self.tm.make_font())
        form.addRow(lbl, widget)

    def _input_qss(self):
        cs = self._cs
        fs = self.tm.font_size
        return f"""
            background-color: {cs['input_lit']};
            color: {cs['text']};
            border: 1px solid {cs['secondary']};
            border-radius: 3px;
            padding: 5px 8px;
            font-size: {fs}px;
            font-family: "{self.tm.font_family}";
        """

    def _input_line(self, placeholder=""):
        w = QLineEdit()
        w.setPlaceholderText(placeholder)
        w.setStyleSheet(self._input_qss())
        w.setFont(self.tm.make_font())
        return w

    def _input_text(self, placeholder="", max_h=60):
        w = QTextEdit()
        w.setPlaceholderText(placeholder)
        w.setMaximumHeight(max_h)
        w.setStyleSheet(self._input_qss())
        w.setFont(self.tm.make_font())
        return w

    def _combo_qss(self):
        cs = self._cs
        fs = self.tm.font_size
        return f"""
            QComboBox {{
                background-color: {cs['input_lit']};
                color: {cs['text']};
                border: 1px solid {cs['secondary']};
                border-radius: 3px;
                padding: 5px 8px;
                font-size: {fs}px;
                font-family: "{self.tm.font_family}";
            }}
            QComboBox:disabled {{
                background-color: {cs['panel_bg']};
                color: {cs['text_dim']};
            }}
            QComboBox QAbstractItemView {{
                background-color: {cs['input_lit']};
                color: {cs['text']};
                selection-background-color: {cs['accent']};
                font-size: {fs}px;
            }}
        """

    def _add_combo_with_custom(self, form, label_text, items, custom_placeholder, key):
        c = self.tm.colors
        fs = self.tm.font_size
        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"color: {c['text']}; font-size: {fs}px;")
        lbl.setFont(self.tm.make_font())

        container = QWidget()
        hbox = QHBoxLayout(container)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(6)

        combo = QComboBox()
        combo.addItems(items)
        combo.setStyleSheet(self._combo_qss())
        combo.setFont(self.tm.make_font())

        custom_edit = QLineEdit()
        custom_edit.setPlaceholderText(custom_placeholder)
        custom_edit.setStyleSheet(self._input_qss())
        custom_edit.setFont(self.tm.make_font())

        hbox.addWidget(combo, stretch=1)
        hbox.addWidget(custom_edit, stretch=3)

        self._custom_edits[key] = (combo, custom_edit)

        def on_custom_text_changed(text):
            if text.strip():
                combo.setEnabled(False)
            else:
                combo.setEnabled(True)

        def on_combo_changed(idx):
            if combo.isEnabled():
                custom_edit.clear()

        custom_edit.textChanged.connect(on_custom_text_changed)
        combo.currentIndexChanged.connect(on_combo_changed)

        form.addRow(lbl, container)
        return combo, custom_edit

    def _build_basic_page(self):
        page = QFrame()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        form = self._make_form()

        self.name_edit = self._input_line("给你的故事起个名字")
        self._add_row(form, "故事名称：", self.name_edit)

        self.background_edit = self._input_text("描述故事背景...", 70)
        self._add_row(form, "故事背景：", self.background_edit)

        self.genre_combo, self.genre_custom = self._add_combo_with_custom(
            form, "故事类型：",
            ["奇幻冒险", "武侠江湖", "科幻探索", "悬疑解谜",
             "校园青春", "恐怖惊悚", "都市奇幻", "修仙问道",
             "末日生存", "神话史诗", "蒸汽朋克"],
            "输入自定义类型", "genre")

        self.style_combo, self.style_custom = self._add_combo_with_custom(
            form, "叙事风格：",
            ["传统叙事", "轻小说风", "文学诗意", "硬汉派",
             "口语化", "史诗体", "黑色幽默", "散文体"],
            "输入自定义风格", "style")

        self.tone_combo, self.tone_custom = self._add_combo_with_custom(
            form, "故事语调：",
            ["中性", "积极乐观", "阴暗低沉", "紧张刺激",
             "温馨治愈", "荒诞讽刺", "悲壮崇高"],
            "输入自定义语调", "tone")

        layout.addLayout(form)
        layout.addStretch()
        self.pages_layout.addWidget(page)
        self._basic_page = page

    def _build_char_page(self):
        page = QFrame()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        form = self._make_form()

        self.pname_edit = self._input_line("留空让AI决定")
        self._add_row(form, "主角姓名：", self.pname_edit)

        self.pgender_combo, self.pgender_custom = self._add_combo_with_custom(
            form, "性别：",
            ["未知", "男", "女", "其他"],
            "输入自定义性别", "pgender")

        self.page_edit = self._input_line("如：18岁")
        self._add_row(form, "年龄：", self.page_edit)

        self.ppersonality_edit = self._input_text("性格描述...", 45)
        self._add_row(form, "性格：", self.ppersonality_edit)

        self.pbg_edit = self._input_text("背景故事...", 45)
        self._add_row(form, "背景：", self.pbg_edit)

        self.pability_edit = self._input_text("如：剑术、魔法、科技...", 45)
        self._add_row(form, "能力：", self.pability_edit)

        self.pappearance_edit = self._input_text("外貌描述...", 45)
        self._add_row(form, "外貌：", self.pappearance_edit)

        layout.addLayout(form)
        layout.addStretch()
        self.pages_layout.addWidget(page)
        self._char_page = page

    def _build_world_page(self):
        page = QFrame()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        form = self._make_form()

        self.world_edit = self._input_text("世界观设定...", 50)
        self._add_row(form, "世界观：", self.world_edit)

        self.elements_edit = self._input_line("用逗号分隔，如：龙, 魔法, 远古遗迹")
        self._add_row(form, "关键元素：", self.elements_edit)

        self.moral_combo, self.moral_custom = self._add_combo_with_custom(
            form, "道德要求：",
            ["无特别限制", "PG-13", "全年龄向", "黑暗向",
             "避免血腥", "避免敏感话题"],
            "输入自定义要求", "moral")

        self.forbidden_edit = self._input_line("如：暴力描写、政治敏感...")
        self._add_row(form, "禁止内容：", self.forbidden_edit)

        self.ai_tendency_combo, self.ai_tendency_custom = self._add_combo_with_custom(
            form, "AI倾向：",
            ["平衡", "偏向主角", "偏向挑战", "随机",
             "戏剧性优先", "真实性优先"],
            "输入自定义倾向", "ai_tendency")

        self.length_combo, self.length_custom = self._add_combo_with_custom(
            form, "预期长度：",
            ["短篇", "中等", "长篇", "史诗"],
            "输入自定义长度", "length")

        self.difficulty_combo, self.difficulty_custom = self._add_combo_with_custom(
            form, "难度：",
            ["简单", "普通", "困难", "地狱"],
            "输入自定义难度", "difficulty")

        layout.addLayout(form)
        layout.addStretch()
        self.pages_layout.addWidget(page)
        self._world_page = page

    def _build_notes_page(self):
        c = self.tm.colors
        fs = self.tm.font_size
        page = QFrame()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel("其他备注：")
        label.setStyleSheet(f"color: {c['text_dim']}; font-size: {fs}px;")
        label.setFont(self.tm.make_font())
        layout.addWidget(label)
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("其他备注...")
        self.notes_edit.setStyleSheet(self._input_qss())
        self.notes_edit.setFont(self.tm.make_font())
        layout.addWidget(self.notes_edit, stretch=1)
        pwd_label_layout = QHBoxLayout()
        pwd_label = QLabel("种子加密密码（可选，留空则不加密）：")
        pwd_label.setStyleSheet(f"color: {c['text_dim']}; font-size: {fs}px; padding-top: 8px;")
        pwd_label.setFont(self.tm.make_font())
        pwd_label_layout.addWidget(pwd_label)
        pwd_label_layout.addStretch()
        self._lock_status_label = QLabel("🔒 密码已锁定")
        self._lock_status_label.setStyleSheet(f"color: {c['accent']}; font-size: {fs}px; font-weight: bold; padding-top: 8px;")
        self._lock_status_label.setFont(self.tm.make_font())
        pwd_label_layout.addWidget(self._lock_status_label)
        layout.addLayout(pwd_label_layout)
        pwd_layout = QHBoxLayout()
        self.pwd_edit = QLineEdit()
        self.pwd_edit.setEchoMode(QLineEdit.Password)
        self.pwd_edit.setPlaceholderText("输入密码")
        self.pwd_edit.setStyleSheet(self._input_qss())
        self.pwd_edit.setFont(self.tm.make_font())
        pwd_layout.addWidget(self.pwd_edit)
        self.pwd_confirm_edit = QLineEdit()
        self.pwd_confirm_edit.setEchoMode(QLineEdit.Password)
        self.pwd_confirm_edit.setPlaceholderText("确认密码")
        self.pwd_confirm_edit.setStyleSheet(self._input_qss())
        self.pwd_confirm_edit.setFont(self.tm.make_font())
        pwd_layout.addWidget(self.pwd_confirm_edit)
        self._password_confirm_btn = QPushButton("确认密码")
        self._password_confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['accent']}; color: white;
                font-weight: bold; padding: 6px 14px; border-radius: 4px;
                font-size: {fs}px;
            }}
            QPushButton:hover {{ background-color: {self.tm._hlight(c['accent'])}; }}
            QPushButton:disabled {{ background-color: {c['border']}; color: {c['text_dim']}; }}
        """)
        self._password_confirm_btn.setFont(self.tm.make_font())
        self._password_confirm_btn.clicked.connect(self._on_confirm_password)
        pwd_layout.addWidget(self._password_confirm_btn)
        layout.addLayout(pwd_layout)
        self.pages_layout.addWidget(page)
        self._notes_page = page

    def _switch_page(self, index: int):
        if index in self._locked_tabs:
            return
        self._update_nav(index)
        titles = [" 基本信息", " 主角设定", " 世界与规则", " 备注"]
        self.page_title.setText(titles[index])
        for i, p in enumerate([self._basic_page, self._char_page, self._world_page, self._notes_page]):
            p.setVisible(i == index)

    def _get_custom_value(self, key, combo, default_combo):
        combo_obj, custom_edit = self._custom_edits.get(key, (None, None))
        if custom_edit and custom_edit.text().strip():
            return custom_edit.text().strip()
        return default_combo

    def _collect_seed(self):
        genre = self._get_custom_value("genre", self.genre_combo, self.genre_combo.currentText())
        style = self._get_custom_value("style", self.style_combo, self.style_combo.currentText())
        tone = self._get_custom_value("tone", self.tone_combo, self.tone_combo.currentText())
        moral = self._get_custom_value("moral", self.moral_combo, self.moral_combo.currentText())
        ai_tendency = self._get_custom_value("ai_tendency", self.ai_tendency_combo, self.ai_tendency_combo.currentText())
        length = self._get_custom_value("length", self.length_combo, self.length_combo.currentText())
        difficulty = self._get_custom_value("difficulty", self.difficulty_combo, self.difficulty_combo.currentText())

        return {
            "name": self.name_edit.text() or "未命名故事",
            "background": self.background_edit.toPlainText(),
            "genre": genre,
            "style": style,
            "tone": tone,
            "elements": [e.strip() for e in self.elements_edit.text().split(",") if e.strip()],
            "protagonist_setting": {
                "name": self.pname_edit.text(),
                "gender": self._get_custom_value("pgender", self.pgender_combo, self.pgender_combo.currentText()),
                "age": self.page_edit.text(),
                "personality": self.ppersonality_edit.toPlainText(),
                "background": self.pbg_edit.toPlainText(),
                "abilities": self.pability_edit.toPlainText(),
                "appearance": self.pappearance_edit.toPlainText(),
            },
            "world_setting": self.world_edit.toPlainText(),
            "moral_requirements": moral,
            "forbidden_content": self.forbidden_edit.text(),
            "ai_tendency": ai_tendency,
            "expected_length": length,
            "difficulty": difficulty,
            "custom_notes": self.notes_edit.toPlainText(),
            "seed_password": self.pwd_edit.text() if self._password_verified else "",
        }

    def _fill_from_seed(self, seed: dict):
        self._seed = seed
        self.name_edit.setText(seed.get("name", ""))
        self.background_edit.setText(seed.get("background", ""))

        for key, combo in [
            ("genre", self.genre_combo), ("style", self.style_combo), ("tone", self.tone_combo),
        ]:
            val = seed.get(key, "")
            idx = combo.findText(val)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            else:
                _, custom_edit = self._custom_edits.get(key, (None, None))
                if custom_edit:
                    custom_edit.setText(val)

        p = seed.get("protagonist_setting", {})
        self.pname_edit.setText(p.get("name", ""))
        gender_val = p.get("gender", "")
        gidx = self.pgender_combo.findText(gender_val)
        if gidx >= 0:
            self.pgender_combo.setCurrentIndex(gidx)
        else:
            _, custom_edit = self._custom_edits.get("pgender", (None, None))
            if custom_edit:
                custom_edit.setText(gender_val)
        self.page_edit.setText(p.get("age", ""))
        self.ppersonality_edit.setText(p.get("personality", ""))
        self.pbg_edit.setText(p.get("background", ""))
        self.pability_edit.setText(p.get("abilities", ""))
        self.pappearance_edit.setText(p.get("appearance", ""))

        self.world_edit.setText(seed.get("world_setting", ""))
        self.elements_edit.setText(", ".join(seed.get("elements", [])))

        for key, combo in [
            ("moral", self.moral_combo), ("ai_tendency", self.ai_tendency_combo),
            ("length", self.length_combo), ("difficulty", self.difficulty_combo),
        ]:
            val = seed.get(
                {"moral": "moral_requirements", "ai_tendency": "ai_tendency",
                 "length": "expected_length", "difficulty": "difficulty"}[key], ""
            )
            idx = combo.findText(val)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            else:
                _, custom_edit = self._custom_edits.get(key, (None, None))
                if custom_edit:
                    custom_edit.setText(val)

        self.forbidden_edit.setText(seed.get("forbidden_content", ""))
        self.notes_edit.setText(seed.get("custom_notes", ""))
        self.pwd_edit.setText(seed.get("seed_password", ""))

    def _on_confirm_password(self):
        pwd = self.pwd_edit.text()
        if not pwd:
            QMessageBox.warning(self, "提示", "请先输入密码。")
            return
        if pwd != self.pwd_confirm_edit.text():
            QMessageBox.warning(self, "密码不匹配", "两次输入的密码不一致，请检查。")
            return

        if self._encrypted_seed_bytes is not None:
            try:
                seed = self.seed_manager.import_seed(self._encrypted_seed_path, pwd)
                self._fill_from_seed(seed)
                self._password_verified = True
                self._locked_tabs.clear()
                for i in (0, 1, 2):
                    self._nav_buttons[i].setEnabled(True)
                self._switch_page(0)
                if self._lock_status_label:
                    self._lock_status_label.setText("🔓 密码已解锁")
                if self._password_confirm_btn:
                    self._password_confirm_btn.setText("已确认")
                    self._password_confirm_btn.setEnabled(False)
            except Exception as e:
                QMessageBox.critical(self, "解密失败", f"密码错误或文件损坏: {str(e)}")
        else:
            self._password_verified = True
            if self._lock_status_label:
                self._lock_status_label.setText("🔓 密码已解锁")
            if self._password_confirm_btn:
                self._password_confirm_btn.setText("已确认")
                self._password_confirm_btn.setEnabled(False)

    def _import_seed(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "导入种子文件", "", "种子文件 (*.seed);;所有文件 (*)")
        if not filepath:
            return
        if self.seed_manager.is_encrypted(filepath):
            try:
                with open(filepath, "rb") as f:
                    self._encrypted_seed_bytes = f.read()
                self._encrypted_seed_path = filepath
                self._password_verified = False
                self._locked_tabs = {0, 1, 2}
                for i in (0, 1, 2):
                    self._nav_buttons[i].setEnabled(False)
                self._switch_page(3)
                if self._lock_status_label:
                    self._lock_status_label.setText("🔒 密码已锁定")
                if self._password_confirm_btn:
                    self._password_confirm_btn.setText("确认密码")
                    self._password_confirm_btn.setEnabled(True)
            except Exception as e:
                self._encrypted_seed_bytes = None
                self._encrypted_seed_path = None
                QMessageBox.critical(self, "导入错误", f"读取文件失败: {str(e)}")
            return
        try:
            seed = self.seed_manager.import_seed(filepath, "")
            self._fill_from_seed(seed)
        except Exception as e:
            QMessageBox.critical(self, "导入错误", str(e))

    def _auto_generate(self):
        if not self.ai_client or not self.ai_client.api_key:
            QMessageBox.warning(self, "提示", "没有API连接，请检查密钥设置。")
            return
        dialog = _AIGenerateDialog(self)
        if dialog.exec_() != QDialog.Accepted:
            return
        c = self.tm.colors
        overlay = LoadingOverlay(self)
        from core.token_counter import format_token_info
        prompt = _build_free_gen_prompt(dialog.get_input())
        token_info = format_token_info(prompt, self.ai_client.model)
        overlay.show_with_text(f"AI正在为您生成种子配置...\n{token_info}", accent_color=c["accent"])
        self._gen_worker = SeedGenWorker(self.ai_client, prompt)
        def on_gen_finished(response):
            overlay.hide_overlay()
            try:
                import json
                tank = response.split("```json")
                if len(tank) >= 2:
                    seed = json.loads(tank[1].split("```")[0].strip())
                else:
                    seed = json.loads(response)
                self._fill_from_seed(seed)
                QMessageBox.information(self, "成功", "AI已成功生成种子")
            except Exception as e:
                QMessageBox.critical(self, "生成错误", str(e))
        def on_gen_error(msg):
            overlay.hide_overlay()
            QMessageBox.critical(self, "生成错误", msg)
        self._gen_worker.finished.connect(on_gen_finished)
        self._gen_worker.error.connect(on_gen_error)
        self._gen_worker.start()

    def _export_seed(self):
        seed = self._collect_seed()
        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出种子", f"{seed['name']}.seed", "种子文件 (*.seed)")
        if not filepath:
            return
        password = seed.get("seed_password", "")
        if not password:
            use_password = QMessageBox.question(
                self, "加密", "是否对种子文件加密？", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes
            if use_password:
                from PyQt5.QtWidgets import QInputDialog
                password, ok = QInputDialog.getText(self, "设置密码", "请输入加密密码：", QLineEdit.Password)
                if not ok:
                    return
        try:
            self.seed_manager.export_seed(seed, filepath, password)
            QMessageBox.information(self, "成功", f"种子已导出到：\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "导出错误", str(e))

    def _start_game(self):
        pwd = self.pwd_edit.text()
        if pwd and not self._password_verified:
            QMessageBox.warning(self, "密码未确认", "请先点击「确认密码」按钮验证密码。")
            return
        if pwd and pwd != self.pwd_confirm_edit.text():
            QMessageBox.warning(self, "密码不匹配", "两次输入的密码不一致，请检查。")
            return

        seed = self._collect_seed()
        empty_fields = []
        field_checks = [
            ("故事名称", seed.get("name", "") in ("", "未命名故事")),
            ("故事背景", not seed.get("background", "").strip()),
            ("主角姓名", not seed.get("protagonist_setting", {}).get("name", "").strip()),
            ("主角性格", not seed.get("protagonist_setting", {}).get("personality", "").strip()),
            ("主角背景", not seed.get("protagonist_setting", {}).get("background", "").strip()),
            ("主角能力", not seed.get("protagonist_setting", {}).get("abilities", "").strip()),
            ("主角外貌", not seed.get("protagonist_setting", {}).get("appearance", "").strip()),
            ("世界观设定", not seed.get("world_setting", "").strip()),
            ("故事元素", len(seed.get("elements", [])) == 0),
        ]
        for label, is_empty in field_checks:
            if is_empty:
                empty_fields.append(label)

        if empty_fields:
            names = "、".join(empty_fields)
            reply = QMessageBox.warning(
                self, "内容未完成",
                f"以下栏目为空：\n\n{names}\n\n空白栏目将由AI随机创作，是否继续？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        self._result_seed = seed
        self.accept()

    def get_seed(self):
        return self._result_seed


class _AIGenerateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tm = get_theme()
        self.setWindowTitle(" AI生成种子")
        self.setMinimumSize(500, 320)
        self._setup_ui()

    def _setup_ui(self):
        c = self.tm.colors
        fs = self.tm.font_size
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        lit = _lighten(c["input_bg"], 0.40)
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("输入故事简短描述，也可以尝试粘贴整篇小说\n留空则让AI完全自由发挥")
        self.text_edit.setStyleSheet(f"""
            background-color: {lit};
            color: {c['text']};
            border: 1px solid {c['secondary']};
            border-radius: 3px;
            padding: 8px;
            font-size: {fs}px;
            font-family: "{self.tm.font_family}";
        """)
        self.text_edit.setFont(self.tm.make_font())
        layout.addWidget(self.text_edit, stretch=1)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        ok_btn = QPushButton(" 开始生成")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['danger']}; color: white;
                font-weight: bold; padding: 8px 20px; border-radius: 4px;
                font-size: {fs}px;
            }}
            QPushButton:hover {{ background-color: {self.tm._hlight(c['danger'])}; }}
        """)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)
        self.setStyleSheet(self.tm.base_dialog_qss())

    def get_input(self):
        return self.text_edit.toPlainText().strip()


def _build_free_gen_prompt(hint: str) -> str:
    hint_part = f"\n用户提示：{hint}" if hint.strip() else "\n请自由发挥，创造一个有趣的故事设定。"
    return f"""请为一个文字冒险游戏生成一个完整的种子配置。{hint_part}

请返回如下结构的JSON：
```json
{{
    "name": "故事名称",
    "background": "故事背景简述（100字以内）",
    "genre": "故事类型（奇幻冒险/武侠江湖/科幻探索/悬疑解谜/校园青春/恐怖惊悚/都市奇幻/修仙问道/末日生存/神话史诗/蒸汽朋克/自定义）",
    "style": "叙事风格（传统叙事/轻小说风/文学诗意/硬汉派/口语化/史诗体/黑色幽默/散文体）",
    "tone": "语调（中性/积极乐观/阴暗低沉/紧张刺激/温馨治愈/荒诞讽刺/悲壮崇高）",
    "elements": ["关键剧情元素1", "关键剧情元素2", "关键剧情元素3"],
    "protagonist_setting": {{
        "name": "主角名",
        "gender": "性别（未知/男/女/其他）",
        "age": "年龄",
        "personality": "性格描述",
        "background": "背景故事",
        "abilities": "能力",
        "appearance": "外貌描述"
    }},
    "world_setting": "世界观设定",
    "moral_requirements": "道德要求（无特别限制/PG-13/全年龄向/黑暗向/避免血腥/避免敏感话题）",
    "forbidden_content": "禁止内容",
    "ai_tendency": "AI倾向（平衡/偏向主角/偏向挑战/随机/戏剧性优先/真实性优先）",
    "expected_length": "预期长度（短篇/中等/长篇/史诗）",
    "difficulty": "难度（简单/普通/困难/地狱）",
    "custom_notes": "备注"
}}
```
只返回JSON，不要其他内容。确保所有字段的值都是合理的。"""
