"""
ESC菜单界面
上帝模式、设置、保存/加载、完结故事等功能
左侧一级选项 + 右侧子内容 布局
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTextEdit, QGroupBox, QFormLayout,
                             QFileDialog, QMessageBox, QListWidget, QLineEdit,
                             QFrame, QWidget, QStackedWidget)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont
from ui.memory_anchor import MemoryAnchorDialog
from ui.theme_manager import get_theme


class EscMenu(QDialog):
    god_mode_submitted = pyqtSignal(str)
    ending_requested = pyqtSignal()

    def __init__(self, game_engine, main_window_ref, parent=None):
        super().__init__(parent)
        self.engine = game_engine
        self.main_window = main_window_ref
        self.tm = get_theme()
        self.setWindowTitle("菜单")
        self.setMinimumSize(620, 440)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self._nav_buttons = []
        self._setup_ui()

    def _setup_ui(self):
        c = self.tm.colors
        fs = self.tm.font_size
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        left_panel = self._build_left_panel()
        main_layout.addWidget(left_panel)

        vline = QFrame()
        vline.setFrameShape(QFrame.VLine)
        vline.setStyleSheet(f"color: {c['border']};")
        main_layout.addWidget(vline)

        right_panel = self._build_right_panel()
        main_layout.addWidget(right_panel, stretch=1)

        self.setStyleSheet(self.tm.base_dialog_qss())

    def _build_left_panel(self):
        c = self.tm.colors
        fs = self.tm.font_size
        panel = QFrame()
        panel.setFixedWidth(180)
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {c['panel_bg']};
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 16, 8, 16)
        layout.setSpacing(4)

        title = QLabel("   游戏菜单")
        title.setStyleSheet(f"color: {c['text']}; font-size: {fs + 4}px; font-weight: bold; padding: 4px 8px;")
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {c['border']};")
        layout.addWidget(sep)
        layout.addSpacing(4)

        nav_items = [
            ("", "继续游戏", 0, self.close),
            ("", "上帝模式", 1, self._show_god_mode),
            ("", "", -1, None),
            ("", "保存存档", 3, self._show_save),
            ("", "加载存档", 4, self._show_load),
            ("", "保存种子", 5, self._show_export_seed),
            ("", "记忆锚点", 6, self._show_memory),
            ("", "Token 消耗", 7, self._show_token_stats),
            ("", "", -1, None),
            ("", "设置", 8, self._show_settings),
            ("", "", -1, None),
            ("", "完结故事", 10, self._show_end_story),
            ("", "退出到主菜单", 11, self._show_quit),
        ]

        for icon, label, idx, handler in nav_items:
            if not label:
                sep2 = QFrame()
                sep2.setFrameShape(QFrame.HLine)
                sep2.setStyleSheet(f"color: {c['border']};")
                layout.addWidget(sep2)
                layout.addSpacing(4)
                continue

            btn = QPushButton(f"    {label}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(34)
            btn.setStyleSheet(self._nav_style(c))
            if handler is not None:
                btn.clicked.connect(handler)
            self._nav_buttons.append((btn, idx))
            layout.addWidget(btn)

        layout.addStretch()
        return panel

    def _nav_style(self, c):
        fs = self.tm.font_size
        return f"""
            QPushButton {{
                color: {c['text_dim']};
                border: none;
                border-radius: 5px;
                font-size: {fs}px;
                text-align: left;
                background-color: transparent;
                padding-left: 4px;
            }}
            QPushButton:hover {{
                background-color: {c['accent']};
                color: white;
            }}
        """

    def _build_right_panel(self):
        c = self.tm.colors
        fs = self.tm.font_size
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {c['panel_bg']};
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 20, 24, 20)

        self.right_title = QLabel(" 继续游戏")
        self.right_title.setStyleSheet(f"color: {c['text']}; font-size: {fs + 4}px; font-weight: bold;")
        layout.addWidget(self.right_title)

        self.right_content = QLabel(
            "返回游戏，继续你的冒险旅程。\n\n"
            "当前故事进度将被保留。"
        )
        self.right_content.setWordWrap(True)
        self.right_content.setAlignment(Qt.AlignTop)
        self.right_content.setStyleSheet(f"color: {c['text_dim']}; font-size: {fs}px; line-height: 1.7;")
        layout.addWidget(self.right_content, stretch=1)

        self.action_btn = QPushButton(" 继续游戏")
        self.action_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['success']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 28px;
                font-size: {fs}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.tm._hlight(c['success'])};
            }}
        """)
        self.action_btn.clicked.connect(self.close)
        layout.addWidget(self.action_btn, alignment=Qt.AlignRight)

        return panel

    def _show_god_mode(self):
        c = self.tm.colors
        self.right_title.setText(" 上帝模式")
        self.right_content.setText(
            "上帝模式允许你强行干预故事走向。\n\n"
            "输入的指令将被作为最高优先级发送给AI，\n"
            "AI会尽力将其融入故事发展中。\n\n"
            " 滥用可能破坏故事的连贯性。"
        )
        self.action_btn.setText(" 激活上帝指令")
        self.action_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['danger']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 28px;
                font-size: {self.tm.font_size}px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {self.tm._hlight(c['danger'])}; }}
        """)
        self.action_btn.clicked.disconnect()
        self.action_btn.clicked.connect(self._execute_god_mode)

    def _execute_god_mode(self):
        from PyQt5.QtWidgets import QInputDialog
        text, ok = QInputDialog.getMultiLineText(
            self, "上帝模式", "输入要强制修改的故事内容：", ""
        )
        if ok and text.strip():
            self.close()
            self.god_mode_submitted.emit(text.strip())

    def _show_save(self):
        c = self.tm.colors
        fs = self.tm.font_size
        self.right_title.setText(" 保存存档")
        self.right_content.setText(
            "将当前游戏进度保存到本地文件。\n\n"
            "存档文件保存在 saves 目录下，\n"
            "包含完整的角色状态、物品和故事历史。"
        )
        self.action_btn.setText(" 保存当前进度")
        self.action_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['accent']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 28px;
                font-size: {fs}px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {self.tm._hlight(c['accent'])}; }}
        """)
        self.action_btn.clicked.disconnect()
        self.action_btn.clicked.connect(self._save_game)

    def _show_load(self):
        c = self.tm.colors
        fs = self.tm.font_size
        self.right_title.setText(" 加载存档")
        self.right_content.setText(
            "从之前保存的存档继续游戏。\n\n"
            " 当前未保存的进度将被覆盖。"
        )
        self.action_btn.setText(" 选择存档")
        self.action_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['accent']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 28px;
                font-size: {fs}px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {self.tm._hlight(c['accent'])}; }}
        """)
        self.action_btn.clicked.disconnect()
        self.action_btn.clicked.connect(self._load_game)

    def _show_export_seed(self):
        c = self.tm.colors
        fs = self.tm.font_size
        self.right_title.setText(" 保存种子")
        self.right_content.setText(
            "将当前故事的种子配置导出为 .seed 文件。\n\n"
            "可设置密码对种子文件进行加密。\n"
            "保存的种子可以在主菜单重新导入。"
        )
        self.action_btn.setText(" 导出种子文件")
        self.action_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['accent']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 28px;
                font-size: {fs}px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {self.tm._hlight(c['accent'])}; }}
        """)
        self.action_btn.clicked.disconnect()
        self.action_btn.clicked.connect(self._export_seed)

    def _export_seed(self):
        from PyQt5.QtWidgets import QInputDialog
        state = self.main_window.get_game_state()
        if state is None or not state.seed:
            QMessageBox.warning(self, "提示", "当前游戏没有种子数据可导出")
            return
        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出种子文件", state.seed.get("name", "story") + ".seed",
            "种子文件 (*.seed);;所有文件 (*)")
        if not filepath:
            return
        password, ok = QInputDialog.getText(
            self, "加密密码", "如需加密请输入密码（留空则为明文）：",
            QLineEdit.Password)
        if ok:
            try:
                self.engine.seed_manager.export_seed(state.seed, filepath, password)
                QMessageBox.information(self, "成功", f"种子已导出到：{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", str(e))

    def _show_memory(self):
        c = self.tm.colors
        fs = self.tm.font_size
        self.right_title.setText(" 记忆锚点")
        self.right_content.setText(
            "查看故事的重要事件时间线。\n\n"
            "可以从任意记忆锚点分支新存档，\n"
            "重新体验不同的故事走向。\n\n"
            "分支存档不具有旧存档后面的记忆。"
        )
        self.action_btn.setText(" 打开记忆锚点")
        self.action_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['accent']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 28px;
                font-size: {fs}px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {self.tm._hlight(c['accent'])}; }}
        """)
        self.action_btn.clicked.disconnect()
        self.action_btn.clicked.connect(self._open_memory_anchor)

    def _show_token_stats(self):
        from core.token_counter import estimate_cost
        c = self.tm.colors
        fs = self.tm.font_size
        self.right_title.setText(" Token 消耗")
        prompt_tokens, completion_tokens = self.engine.get_session_tokens()
        total_tokens = prompt_tokens + completion_tokens
        model = self.engine.config["api"]["model"]
        cost = estimate_cost(prompt_tokens, completion_tokens or 500, model=model)

        self.right_content.setText(
            f"本存档至今的 Token 消耗统计：\n\n"
            f"  输入 Tokens（Prompt）：{prompt_tokens:,}\n"
            f"  输出 Tokens（Completion）：{completion_tokens:,}\n"
            f"  总计 Tokens：{total_tokens:,}\n\n"
            f"  预估费用：约 ¥{cost:.4f}\n\n"
            f"  当前模型：{model}"
        )
        self.action_btn.setText(" 继续游戏")
        self.action_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['success']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 28px;
                font-size: {fs}px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {self.tm._hlight(c['success'])}; }}
        """)
        self.action_btn.clicked.disconnect()
        self.action_btn.clicked.connect(self.close)

    def _show_settings(self):
        c = self.tm.colors
        fs = self.tm.font_size
        self.right_title.setText(" 设置")
        self.right_content.setText(
            "配置游戏参数。\n\n"
            "  API 连接：DeepSeek 密钥和模型选择\n"
            "  显示：分辨率、字体大小、主题颜色\n"
            "  音频：音量控制（后续版本支持）"
        )
        self.action_btn.setText(" 打开设置")
        self.action_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['accent']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 28px;
                font-size: {fs}px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {self.tm._hlight(c['accent'])}; }}
        """)
        self.action_btn.clicked.disconnect()
        self.action_btn.clicked.connect(self._open_settings)

    def _show_end_story(self):
        c = self.tm.colors
        fs = self.tm.font_size
        self.right_title.setText(" 完结故事")
        self.right_content.setText(
            "结束当前故事并进入结算界面。\n\n"
            "AI将尝试为故事生成结局。\n"
            "你可以在结算界面导出故事种子，\n"
            "以便日后重新体验或分享给他人。\n\n"
            " 此操作不可撤销。"
        )
        self.action_btn.setText(" 完结故事")
        self.action_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['warning']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 28px;
                font-size: {fs}px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {self.tm._hlight(c['warning'])}; }}
        """)
        self.action_btn.clicked.disconnect()
        self.action_btn.clicked.connect(self._end_story)

    def _show_quit(self):
        c = self.tm.colors
        fs = self.tm.font_size
        self.right_title.setText(" 退出到主菜单")
        self.right_content.setText(
            "返回主菜单。\n\n"
            " 未保存的进度将会丢失！\n"
            "建议先保存存档再退出。"
        )
        self.action_btn.setText(" 退出到主菜单")
        self.action_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['text_dim']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 28px;
                font-size: {fs}px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {self.tm._hlight(c['text_dim'])}; }}
        """)
        self.action_btn.clicked.disconnect()
        self.action_btn.clicked.connect(self._quit_to_menu)

    def _save_game(self):
        state = self.main_window.get_game_state()
        if state is None:
            QMessageBox.warning(self, "提示", "没有进行中的游戏")
            return

        d = QDialog(self)
        d.setWindowTitle("保存存档")
        d.setMinimumWidth(360)
        d.setStyleSheet(self.tm.base_dialog_qss())
        dl = QVBoxLayout(d)
        dl.addWidget(QLabel("存档名称（留空则自动命名）："))
        name_input = QLineEdit()
        name_input.setPlaceholderText("可选：输入自定义名称")
        name_input.setStyleSheet("padding: 6px;")
        dl.addWidget(name_input)
        btns = QHBoxLayout()
        ok_btn = QPushButton("保存")
        ok_btn.clicked.connect(d.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(d.reject)
        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(ok_btn)
        dl.addLayout(btns)

        if d.exec_() != QDialog.Accepted:
            return

        custom_name = name_input.text().strip()
        try:
            filepath = self.engine.save_manager.save(state, custom_name)
            QMessageBox.information(self, "成功", f"存档已保存：\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))

    def _load_game(self):
        saves = self.engine.save_manager.list_saves()
        if not saves:
            QMessageBox.information(self, "提示", "没有找到存档文件")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("选择存档")
        dialog.setMinimumSize(400, 300)
        dialog.setStyleSheet(self.tm.base_dialog_qss())
        d_layout = QVBoxLayout(dialog)

        list_widget = QListWidget()
        for s in saves:
            list_widget.addItem(f"{s['name']}  [{s['modified']}]")
        d_layout.addWidget(list_widget)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("加载")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(lambda: self._delete_save(list_widget, saves))
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        d_layout.addLayout(btn_layout)

        if dialog.exec_() == QDialog.Accepted and list_widget.currentRow() >= 0:
            try:
                filepath = saves[list_widget.currentRow()]["path"]
                state = self.engine.save_manager.load(filepath)
                self.main_window.load_game_state(state)
                self.close()
            except Exception as e:
                QMessageBox.critical(self, "加载失败", str(e))

    def _delete_save(self, list_widget, saves):
        idx = list_widget.currentRow()
        if idx < 0:
            return
        reply = QMessageBox.question(self, "确认", "确定删除此存档吗？")
        if reply == QMessageBox.Yes:
            try:
                self.engine.save_manager.delete_save(saves[idx]["path"])
                list_widget.takeItem(idx)
            except Exception as e:
                QMessageBox.critical(self, "错误", str(e))

    def _load_seed(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "加载种子文件", "", "种子文件 (*.seed);;所有文件 (*)")
        if not filepath:
            return

        if self.engine.seed_manager.is_encrypted(filepath):
            from PyQt5.QtWidgets import QInputDialog
            password, ok = QInputDialog.getText(self, "密码", "此种子已加密，请输入密码：",
                                                 QLineEdit.Password)
            if not ok:
                return
        else:
            password = ""

        try:
            seed = self.engine.seed_manager.import_seed(filepath, password)
            self.main_window.start_new_game_with_seed(seed)
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "加载失败", str(e))

    def _open_memory_anchor(self):
        state = self.main_window.get_game_state()
        if state is None:
            QMessageBox.warning(self, "提示", "没有进行中的游戏")
            return
        dialog = MemoryAnchorDialog(state, self.engine.save_manager, self)
        dialog.exec_()

    def _open_settings(self):
        from ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.engine, self)
        dialog.exec_()

    def _end_story(self):
        reply = QMessageBox.question(
            self, "完结故事",
            "确定要完结当前故事吗？\n系统会尝试让AI生成故事结局。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        state = self.main_window.get_game_state()
        if state is None:
            return

        state.game_over = True
        state.game_over_reason = "玩家选择完结故事"

        self.close()
        self.ending_requested.emit()

    def _quit_to_menu(self):
        reply = QMessageBox.question(
            self, "退出", "确定退出到主菜单吗？\n未保存的进度将会丢失。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.main_window.return_to_menu()
            self.close()
