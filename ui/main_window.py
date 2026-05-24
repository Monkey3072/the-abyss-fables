"""
游戏主窗口
集成故事面板、状态面板和选择面板
"""
import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QSplitter, QMessageBox, QApplication,
                             QLabel, QPushButton)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from core.game_engine import GameEngine
from core.ai_worker import AIWorker
from core.ai_worker_async import AsyncAIWorker
from core.event_bus import event_bus
from ui.story_panel import StoryPanel
from ui.status_panel import StatusPanel
from ui.choice_panel import ChoicePanel
from ui.esc_menu import EscMenu
from ui.warning_dialog import WarningDialog
from ui.start_menu import StartMenu
from ui.seed_editor import SeedEditorDialog
from ui.settings_dialog import SettingsDialog
from ui.theme_manager import get_theme
from ui.loading_overlay import LoadingOverlay
from core.token_counter import estimate_tokens


class MainWindow(QMainWindow):
    return_to_menu_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.engine = GameEngine()
        self._current_widget = None
        self._pending_god_text = ""
        self._ai_worker = None
        self._loading_overlay = None

        self.tm = get_theme()
        self.tm.sync_from_engine(self.engine)

        self.engine.callbacks["on_story_chunk"] = self._on_story_chunk
        self.engine.callbacks["on_turn_complete"] = self._on_turn_complete
        self.engine.callbacks["on_error"] = self._on_error

        event_bus.apply_settings_requested.connect(self._on_apply_settings)
        event_bus.request_new_game_with_seed.connect(self.start_new_game_with_seed)
        event_bus.return_to_menu_requested.connect(self.return_to_menu)

        self.setWindowTitle("渊索寓言 - The Abyss Fables")
        self.setMinimumSize(960, 600)
        self._apply_resolution()

        self._show_warning()

    def _apply_resolution(self):
        res_text = self.engine.config.get("display", {}).get("resolution", "1280x720")
        w, h = map(int, res_text.split("x"))
        self.resize(w, h)
        self.adjustSize()

    def _on_apply_settings(self):
        self._apply_resolution()
        self._apply_theme()
        self._apply_font()

    def _apply_font(self):
        self.tm.sync_from_engine(self.engine)
        fs = self.tm.font_size
        ff = self.tm.font_family
        app = QApplication.instance()
        if app:
            app.setStyleSheet(get_theme().global_qss)
            f = QFont(ff, fs)
            app.setFont(f)
            for widget in app.allWidgets():
                if not widget.isWindow() or widget is self:
                    widget.setFont(f)
        self.tm.apply_to_widget(self)

    def _apply_theme(self):
        self.tm.sync_from_engine(self.engine)
        state = self.engine.game_state
        if state is not None:
            story_entries = list(state.story_history)
            current_choices = list(state.current_choices)
            self._show_game_ui()
            for entry in story_entries:
                self.story_panel.text_area.append(entry["story"])
                choices_text = " | ".join(
                    c.get("text", "") for c in entry.get("choices", [])
                    if c.get("type") != "free"
                )
                if choices_text:
                    self.story_panel.text_area.append(f"\n[选择：{choices_text}]")
                self.story_panel.text_area.append(
                    "\n\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n")
            self.choice_panel.set_choices(current_choices)
            self.status_panel.update_status(state)
            self.status_panel.update_inventory(state)
            self.status_panel.update_companions(state)
        else:
            self._show_start_menu()

    def _show_warning(self):
        self.tm.sync_from_engine(self.engine)
        if not WarningDialog.show_warning(self):
            sys.exit(0)
        self._show_start_menu()

    def _show_start_menu(self):
        self._clear_central()
        menu = StartMenu(self, font_size=self.tm.font_size, colors=self.tm.colors)
        menu.new_game_clicked.connect(self._on_new_game)
        menu.load_game_clicked.connect(self._on_load_from_menu)
        menu.import_seed_clicked.connect(self._on_import_seed)
        menu.settings_clicked.connect(self._on_settings_from_menu)
        menu.tech_credit_clicked.connect(self._on_tech_credit)
        self.setCentralWidget(menu)
        self._current_widget = menu
        self.setStyleSheet(f"QMainWindow {{ background-color: {self.tm.colors['background']}; }}")

    def _clear_central(self):
        widget = self.centralWidget()
        if widget:
            widget.setParent(None)

    def _on_new_game(self):
        dialog = SeedEditorDialog(ai_client=self.engine.ai_client, parent=self)
        if dialog.exec_() == SeedEditorDialog.Accepted:
            seed = dialog.get_seed()
            if seed:
                self.start_new_game_with_seed(seed)

    def _on_load_from_menu(self):
        saves = self.engine.save_manager.list_saves()
        if not saves:
            QMessageBox.information(self, "提示", "没有找到存档文件")
            return
        from PyQt5.QtWidgets import QDialog, QListWidget, QPushButton
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
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(
            lambda: self._delete_save_from_menu(list_widget, saves))
        ok_btn = QPushButton("加载")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        d_layout.addLayout(btn_layout)
        if dialog.exec_() == QDialog.Accepted and list_widget.currentRow() >= 0:
            try:
                filepath = saves[list_widget.currentRow()]["path"]
                state = self.engine.save_manager.load(filepath)
                self.load_game_state(state)
            except Exception as e:
                QMessageBox.critical(self, "加载失败", str(e))

    def _delete_save_from_menu(self, list_widget, saves):
        idx = list_widget.currentRow()
        if idx < 0:
            return
        reply = QMessageBox.question(self, "确认", "确定删除此存档吗？此操作不可恢复。")
        if reply == QMessageBox.Yes:
            try:
                self.engine.save_manager.delete_save(saves[idx]["path"])
                list_widget.takeItem(idx)
            except Exception as e:
                QMessageBox.critical(self, "错误", str(e))

    def _on_import_seed(self):
        from PyQt5.QtWidgets import QFileDialog, QInputDialog, QLineEdit
        filepath, _ = QFileDialog.getOpenFileName(
            self, "导入种子文件", "", "种子文件 (*.seed);;所有文件 (*)")
        if not filepath:
            return
        if self.engine.seed_manager.is_encrypted(filepath):
            password, ok = QInputDialog.getText(self, "密码", "此种子已加密，请输入密码：", QLineEdit.Password)
            if not ok:
                return
        else:
            password = ""
        try:
            seed = self.engine.seed_manager.import_seed(filepath, password)
            self.start_new_game_with_seed(seed)
        except Exception as e:
            QMessageBox.critical(self, "导入错误", str(e))

    def _on_settings_from_menu(self):
        dialog = SettingsDialog(self.engine, self)
        dialog.exec_()

    def _on_tech_credit(self):
        pass

    def start_new_game_with_seed(self, seed: dict):
        try:
            self.engine.init_game_state(seed)
            self.engine.reset_session_tokens()
            self._show_game_ui()
            first_prompt = self.engine.build_first_turn_prompt(seed)
            prompt_tokens = estimate_tokens(
                self.engine.get_system_prompt() + first_prompt,
                self.engine.ai_client.model
            )
            self.engine.add_prompt_tokens(prompt_tokens)
            self._show_loading("正在连接AI生成初始故事...")
            self.story_panel.begin_streaming()

            try:
                import qasync
                import asyncio
                loop = asyncio.get_event_loop()
                worker = AsyncAIWorker(
                    self.engine.ai_client,
                    self.engine.get_system_prompt(),
                    self.engine.build_first_turn_prompt(seed),
                )
                worker.chunk.connect(self._on_worker_chunk)
                worker.finished.connect(lambda resp: self._on_first_turn_done(resp, seed))
                worker.error.connect(self._on_worker_error)
                worker.start(loop)
                self._ai_worker = worker
            except ImportError:
                self._ai_worker = AIWorker(
                    self.engine.ai_client,
                    self.engine.get_system_prompt(),
                    self.engine.build_first_turn_prompt(seed),
                    is_stream=True
                )
                self._ai_worker.chunk.connect(self._on_worker_chunk)
                self._ai_worker.finished.connect(lambda resp: self._on_first_turn_done(resp, seed))
                self._ai_worker.error.connect(self._on_worker_error)
                self._ai_worker.start()
        except Exception as e:
            self._hide_loading()
            self._show_start_menu()
            QMessageBox.critical(self, "游戏启动失败", str(e))

    def _on_worker_chunk(self, chunk, full):
        self.story_panel.append_chunk(chunk)

    def _on_worker_error(self, msg):
        self._hide_loading()
        self.choice_panel.setEnabled(True)
        self.submit_btn.setEnabled(True)
        QMessageBox.critical(self, "错误", msg)

    def _on_first_turn_done(self, full_response, seed):
        self.story_panel.finalize_turn()
        try:
            from core.response_parser import parse_ai_response
            completion_tokens = estimate_tokens(full_response, self.engine.ai_client.model)
            self.engine.add_completion_tokens(completion_tokens)
            parsed = parse_ai_response(full_response)
            gs_before = self.engine.game_state
            self.engine.apply_turn_result(parsed, is_first=True)
            self._hide_loading()
            if self.engine.game_state is gs_before and not gs_before.game_over:
                self._present_turn_result(parsed)
                self.choice_panel.setEnabled(True)
                self.submit_btn.setEnabled(True)
        except Exception as e:
            self._hide_loading()
            try:
                if hasattr(self, "choice_panel"):
                    self.choice_panel.setEnabled(True)
                    self.submit_btn.setEnabled(True)
            except RuntimeError:
                pass
            QMessageBox.critical(self, "游戏启动失败", str(e))

    def _show_loading(self, text):
        self._loading_overlay = LoadingOverlay(self)
        self._loading_overlay.show_with_text(text, accent_color=self.tm.colors["accent"])

    def _update_loading_text(self, text):
        if self._loading_overlay:
            self._loading_overlay.update_text(text)

    def _hide_loading(self):
        if self._loading_overlay:
            self._loading_overlay.hide_overlay()
            self._loading_overlay = None

    def _show_game_ui_if_needed(self):
        if not isinstance(self._current_widget, QSplitter):
            self._show_game_ui()

    def _show_game_ui(self):
        self._clear_central()
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setStyleSheet(f"QSplitter::handle {{ background-color: {self.tm.colors['border']}; width: 2px; }}")
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self.story_panel = StoryPanel(self)
        left_layout.addWidget(self.story_panel, stretch=3)
        self.choice_panel = ChoicePanel(self)
        self.choice_panel.turn_submitted.connect(self._on_turn_submitted)
        left_layout.addWidget(self.choice_panel, stretch=2)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)
        self.status_panel = StatusPanel(self)
        self.status_panel.item_action_requested.connect(self._on_item_action)
        right_layout.addWidget(self.status_panel, stretch=1)
        c = self.tm.colors
        fs = self.tm.font_size
        self.submit_btn = QPushButton("结束\n回合")
        self.submit_btn.setFixedSize(52, 52)
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['success']};
                color: white;
                border: none;
                border-radius: 26px;
                font-size: {fs - 1}px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {self.tm._hlight(c['success'])}; }}
            QPushButton:disabled {{ background-color: {c['border']}; color: {c['text_dim']}; }}
        """)
        self.submit_btn.clicked.connect(self.choice_panel.submit)
        right_layout.addWidget(self.submit_btn, alignment=Qt.AlignCenter)
        right_layout.addSpacing(8)
        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(right_widget)
        main_splitter.setStretchFactor(0, 3)
        main_splitter.setStretchFactor(1, 1)
        self.setCentralWidget(main_splitter)
        self._current_widget = main_splitter
        self.tm.apply_to_widget(self)

    def _on_turn_submitted(self, choices: list):
        self.choice_panel.setEnabled(False)
        self.submit_btn.setEnabled(False)
        self.story_panel.finalize_turn()
        self.story_panel.begin_streaming()
        god_text = self._pending_god_text
        self._pending_god_text = ""
        prompt = self.engine.build_turn_prompt_text(choices, god_text)
        prompt_tokens = estimate_tokens(
            self.engine.get_system_prompt() + prompt,
            self.engine.ai_client.model
        )
        self.engine.add_prompt_tokens(prompt_tokens)
        self._show_loading("AI正在构思剧情...")
        try:
            import qasync
            import asyncio
            loop = asyncio.get_event_loop()
            worker = AsyncAIWorker(
                self.engine.ai_client,
                self.engine.get_system_prompt(),
                prompt,
            )
            worker.chunk.connect(self._on_worker_chunk)
            worker.finished.connect(self._on_turn_worker_done)
            worker.error.connect(self._on_worker_error)
            worker.start(loop)
            self._ai_worker = worker
        except ImportError:
            self._ai_worker = AIWorker(
                self.engine.ai_client,
                self.engine.get_system_prompt(),
                prompt,
                is_stream=True
            )
            self._ai_worker.chunk.connect(self._on_worker_chunk)
            self._ai_worker.finished.connect(self._on_turn_worker_done)
            self._ai_worker.error.connect(self._on_worker_error)
            self._ai_worker.start()

    def _on_turn_worker_done(self, full_response):
        self._hide_loading()
        try:
            from core.response_parser import parse_ai_response
            completion_tokens = estimate_tokens(full_response, self.engine.ai_client.model)
            self.engine.add_completion_tokens(completion_tokens)
            parsed = parse_ai_response(full_response)
            gs_before = self.engine.game_state
            self.engine.apply_turn_result(parsed)
            if self.engine.game_state is gs_before and not gs_before.game_over:
                self._present_turn_result(parsed)
                self.choice_panel.setEnabled(True)
                self.submit_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "回合处理失败", str(e))
            try:
                if hasattr(self, "choice_panel"):
                    self.choice_panel.setEnabled(True)
                    self.submit_btn.setEnabled(True)
            except RuntimeError:
                pass

    def _on_story_chunk(self, chunk: str, full_response: str):
        self.story_panel.append_chunk(chunk)

    def _on_turn_complete(self, parsed: dict, game_state):
        self.status_panel.update_status(game_state)
        self.status_panel.update_inventory(game_state)
        self.status_panel.update_companions(game_state)
        self.choice_panel.set_choices(game_state.current_choices)
        self.choice_panel.setEnabled(True)
        self.submit_btn.setEnabled(True)
        if game_state.game_over:
            QMessageBox.information(self, "故事结束", f"故事已结束：{game_state.game_over_reason}")
            from ui.ending_dialog import EndingDialog
            dialog = EndingDialog(game_state, self.engine, self)
            dialog.exec_()

    def _on_error(self, error_msg: str):
        QMessageBox.critical(self, "错误", error_msg)
        if hasattr(self, "choice_panel"):
            self.choice_panel.setEnabled(True)
            self.submit_btn.setEnabled(True)

    def _present_turn_result(self, parsed: dict):
        story_text = parsed.get("story", "")
        choices = parsed.get("choices", [])
        turn_num = self.engine.game_state.turn if self.engine.game_state else "?"
        turn_header = f"\n\n━━━━━━━━ 第 {turn_num} 回合 ━━━━━━━\n\n"
        self.story_panel.start_new_turn()
        self.story_panel.end_streaming(turn_header + story_text)
        self.choice_panel.set_choices(choices)
        self.status_panel.update_status(self.engine.game_state)
        self.status_panel.update_inventory(self.engine.game_state)
        self.status_panel.update_companions(self.engine.game_state)

    def get_game_state(self):
        return self.engine.game_state

    def load_game_state(self, state):
        self.engine.game_state = state
        self.engine.reset_session_tokens()
        self._show_game_ui()
        self.story_panel.clear()
        for i, entry in enumerate(state.story_history, 1):
            self.story_panel.text_area.append(f"\n\n━━━━━━━━ 第 {i} 回合 ━━━━━━━\n\n")
            self.story_panel.text_area.append(entry["story"])
            choices_text = " | ".join(
                c.get("text", "") for c in entry.get("choices", []) if c.get("type") != "free"
            )
            if choices_text:
                self.story_panel.text_area.append(f"\n[选择：{choices_text}]")
        self.choice_panel.set_choices(state.current_choices)
        self.status_panel.update_status(state)
        self.status_panel.update_inventory(state)
        self.status_panel.update_companions(state)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._open_esc_menu()
        else:
            super().keyPressEvent(event)

    def _open_esc_menu(self):
        if self.engine.game_state is None:
            return
        menu = EscMenu(self.engine, self, None)
        menu.god_mode_submitted.connect(self._on_god_mode)
        menu.ending_requested.connect(self._start_ending_story)
        menu.setParent(None)
        menu.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        menu.setAttribute(Qt.WA_DeleteOnClose)
        menu.setWindowModality(Qt.ApplicationModal)
        main_geo = self.geometry()
        menu_size = menu.sizeHint()
        x = main_geo.x() + (main_geo.width() - menu_size.width()) // 2
        y = main_geo.y() + (main_geo.height() - menu_size.height()) // 2
        menu.move(x, y)
        menu.show()
        menu.raise_()
        menu.activateWindow()
        self._esc_menu = menu

    def _on_god_mode(self, text: str):
        self._pending_god_text = text
        QMessageBox.information(self, "上帝模式", f"上帝指令已接收。\n点击 按钮 后将与玩家选择一起发送给AI。\n\n指令内容：{text[:200]}")

    def _on_item_action(self, action: str, item_name: str):
        self.engine.add_item_action(action, item_name)
        self.status_panel.update_inventory(self.engine.game_state)
        action_label = "使用" if action == "use" else "丢弃"
        QMessageBox.information(self, "物品操作", f"已标记「{item_name}」为「{action_label}」，将在下回合发送给AI。")

    def show_ending(self, template_response: str = ""):
        from ui.ending_dialog import EndingDialog
        dialog = EndingDialog(self.engine.game_state, self.engine, self, template_response)
        dialog.exec_()

    def return_to_menu(self):
        self.engine.game_state = None
        self.engine.reset_session_tokens()
        self._show_start_menu()

    def _start_ending_story(self):
        if hasattr(self, '_ending_worker') and self._ending_worker is not None:
            if hasattr(self._ending_worker, 'isRunning') and self._ending_worker.isRunning():
                return
            try:
                self._ending_worker.finished.disconnect()
                self._ending_worker.error.disconnect()
            except Exception:
                pass

        self._show_loading("AI正在生成故事结局...")
        self.choice_panel.setEnabled(False)
        self.submit_btn.setEnabled(False)

        from prompts.system_prompts import build_ending_prompt
        ending_prompt = build_ending_prompt(self.engine.game_state.to_dict())

        try:
            from core.ai_worker_async import AsyncAIWorker
            if AsyncAIWorker.is_available():
                import asyncio
                loop = asyncio.get_event_loop()
                self._ending_worker = AsyncAIWorker(
                    self.engine.ai_client,
                    self.engine.get_system_prompt(),
                    ending_prompt,
                    self
                )
                self._ending_worker.finished.connect(self._on_ending_done)
                self._ending_worker.error.connect(self._on_ending_error)
                self._ending_worker.start(loop)
                return
        except Exception:
            pass

        from core.ai_worker import AIWorker
        self._ending_worker = AIWorker(
            self.engine.ai_client,
            self.engine.get_system_prompt(),
            ending_prompt,
            is_stream=True
        )
        self._ending_worker.finished.connect(self._on_ending_done)
        self._ending_worker.error.connect(self._on_ending_error)
        self._ending_worker.start()

    def _on_ending_done(self, template_response: str):
        self._hide_loading()
        self.show_ending(template_response)

    def _on_ending_error(self, error_msg: str):
        self._hide_loading()
        self.show_ending("")
