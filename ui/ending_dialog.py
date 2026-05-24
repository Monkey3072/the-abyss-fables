"""
故事结算/完结界面
显示故事摘要，支持导出种子
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QTextEdit, QPushButton, QMessageBox, QFileDialog,
                             QLineEdit, QWidget)
from PyQt5.QtCore import Qt
from core.event_bus import event_bus
from ui.theme_manager import get_theme
import json


class EndingDialog(QDialog):
    def __init__(self, game_state, game_engine, parent=None, template_response: str = ""):
        super().__init__(parent)
        self.game_state = game_state
        self.engine = game_engine
        self.template_response = template_response
        self.template_seed = None
        self.tm = get_theme()

        if template_response:
            self._parse_template(template_response)

        self.setWindowTitle("故事完结")
        self.setMinimumSize(500, 480)
        self._setup_ui()

    def _parse_template(self, response: str):
        try:
            import json
            tank = response.split("```json")
            if len(tank) >= 2:
                self.template_seed = json.loads(tank[1].split("```")[0])
            else:
                self.template_seed = json.loads(response)
        except Exception:
            self.template_seed = None

    def _setup_ui(self):
        c = self.tm.colors
        fs = self.tm.font_size
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("故事完结")
        title.setStyleSheet(f"color: {c['accent']}; font-size: {fs + 4}px; font-weight: bold;")
        layout.addWidget(title)

        info = QLabel(f"故事名称：{self.game_state.seed.get('name', '未知')}\n"
                      f"总回合数：{self.game_state.turn}\n"
                      f"经过天数：{self.game_state.day}\n"
                      f"结束原因：{self.game_state.game_over_reason}")
        info.setStyleSheet(f"color: {c['text_dim']}; font-size: {fs}px; padding: 8px;")
        layout.addWidget(info)

        summary_label = QLabel("故事回顾：")
        summary_label.setStyleSheet(f"color: {c['accent']}; font-weight: bold; font-size: {fs + 4}px;")
        layout.addWidget(summary_label)

        summary_text = QTextEdit()
        summary_text.setReadOnly(True)
        summary_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {c['input_bg']};
                color: {c['text']};
                border: 1px solid {c['border']};
                border-radius: 4px;
                padding: 8px;
                font-size: {fs}px;
            }}
        """)

        summary_content = ""
        for entry in self.game_state.story_history:
            s = entry.get("story", "")
            turn = entry.get("turn", "?")
            if len(s) > 200:
                s = s[:200] + "..."
            summary_content += f"\n━━ 第{turn}回合 ━━\n{s}\n"

        summary_text.setText(summary_content or "无记录")
        layout.addWidget(summary_text)

        if self.template_seed:
            template_container = QWidget()
            template_container.setVisible(False)
            container_layout = QVBoxLayout(template_container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(4)

            export_label = QLabel("AI已为你生成故事模板：")
            export_label.setStyleSheet(f"color: {c['success']}; font-weight: bold; margin-top: 8px; font-size: {fs}px;")
            container_layout.addWidget(export_label)

            template_text = QTextEdit()
            template_text.setReadOnly(True)
            template_text.setText(json.dumps(self.template_seed, ensure_ascii=False, indent=2))
            template_text.setMaximumHeight(120)
            template_text.setStyleSheet(f"""
                QTextEdit {{
                    background-color: {c['input_bg']};
                    color: {c['text']};
                    border: 1px solid {c['success']};
                    border-radius: 4px;
                    padding: 8px;
                    font-size: {fs}px;
                }}
            """)
            container_layout.addWidget(template_text)

            layout.addWidget(template_container)

        btn_layout = QHBoxLayout()

        self.export_seed_btn = QPushButton("导出为种子文件")
        self.export_seed_btn.clicked.connect(self._export_seed)
        btn_layout.addWidget(self.export_seed_btn)

        if not self.template_seed:
            self.generate_template_btn = QPushButton("AI生成故事模板")
            self.generate_template_btn.clicked.connect(self._generate_template)
            btn_layout.addWidget(self.generate_template_btn)

        btn_layout.addStretch()

        self.replay_btn = QPushButton("以模板重新开始")
        self.replay_btn.clicked.connect(self._replay_with_template)
        self.replay_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['accent']};
                color: white;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: {fs}px;
            }}
            QPushButton:hover {{
                background-color: {self.tm._hlight(c['accent'])};
            }}
        """)
        btn_layout.addWidget(self.replay_btn)

        menu_btn = QPushButton("返回主菜单")
        menu_btn.clicked.connect(self._return_to_menu)
        btn_layout.addWidget(menu_btn)

        layout.addLayout(btn_layout)

        btn_qss = f"""
            QPushButton {{
                background-color: {c['secondary']};
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 14px;
                font-size: {fs}px;
            }}
            QPushButton:hover {{
                background-color: {self.tm._hlight(c['secondary'])};
            }}
        """
        self.export_seed_btn.setStyleSheet(btn_qss)
        if hasattr(self, 'generate_template_btn'):
            self.generate_template_btn.setStyleSheet(btn_qss)
        menu_btn.setStyleSheet(btn_qss)

        self.setStyleSheet(self.tm.base_dialog_qss())

    def _generate_template(self):
        try:
            response = self.engine.generate_ending_template()
            self._parse_template(response)
            self.template_response = response

            QMessageBox.information(self, "成功", "AI已成功生成故事模板")

            self.close()
            dialog = EndingDialog(self.game_state, self.engine, self.parent(), response)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "生成失败", str(e))

    def _export_seed(self):
        seed_to_export = self.template_seed or self.game_state.seed
        if not seed_to_export:
            QMessageBox.warning(self, "提示", "没有可导出的种子")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出种子", f"{seed_to_export.get('name', 'story')}.seed",
            "种子文件 (*.seed)")
        if not filepath:
            return

        use_password = QMessageBox.question(
            self, "加密", "是否对种子文件加密？",
            QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes

        password = ""
        if use_password:
            from PyQt5.QtWidgets import QInputDialog
            password, ok = QInputDialog.getText(
                self, "设置密码", "请输入加密密码：", QLineEdit.Password)
            if not ok:
                return

        try:
            self.engine.seed_manager.export_seed(seed_to_export, filepath, password)
            QMessageBox.information(self, "成功", f"种子已导出到：\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))

    def _replay_with_template(self):
        seed = self.template_seed or self.game_state.seed
        if seed:
            self.accept()
            event_bus.request_new_game_with_seed.emit(seed)

    def _return_to_menu(self):
        self.accept()
        event_bus.return_to_menu_requested.emit()