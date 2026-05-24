"""
玩家选择面板
显示多选题目、简答题、自由输入和答题卡导航
"""
from collections import OrderedDict
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTextEdit, QScrollArea, QFrame,
                             QCheckBox, QButtonGroup, QSizePolicy, QLineEdit,
                             QRadioButton, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from ui.theme_manager import get_theme


class ChoicePanel(QWidget):
    turn_submitted = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tm = get_theme()
        self._question_checkboxes = []
        self._question_group = QButtonGroup()
        self._question_group.setExclusive(False)
        self._card_buttons = []
        self._question_headers = []
        self._short_answer_inputs = []
        self._single_choice_groups = []
        self._question_widgets = []
        self._question_data = []
        self._current_question = 0
        self._all_choices = []
        self._setup_ui()

    def _setup_ui(self):
        c = self.tm.colors
        fs = self.tm.font_size
        ff = self.tm.font_family

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 4, 0, 0)
        main_layout.setSpacing(6)

        left_area = QWidget()
        left_layout = QVBoxLayout(left_area)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        header = QLabel(" 命运抉择")
        header.setFont(self.tm.make_font(1))
        header.setStyleSheet(f"color: {c['text']}; font-weight: bold;")
        left_layout.addWidget(header)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: {c['panel_bg']};
                border: 1px solid {c['border']};
                border-radius: 4px;
            }}
        """)

        self.choices_container = QWidget()
        self.choices_container.setStyleSheet(f"background-color: {c['panel_bg']};")
        self.choices_layout = QVBoxLayout(self.choices_container)
        self.choices_layout.setContentsMargins(8, 6, 8, 6)
        self.choices_layout.setSpacing(4)
        self.choices_layout.addStretch()

        self.scroll_area.setWidget(self.choices_container)
        left_layout.addWidget(self.scroll_area, stretch=4)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(6)

        self.free_edit = QTextEdit()
        self.free_edit.setPlaceholderText("请输入你的自由意志...也可以留空，AI会进行参考")
        self.free_edit.setMaximumHeight(54)
        self.free_edit.setFont(self.tm.make_font())
        self.free_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {c['input_bg']};
                color: {c['text']};
                border: 1px solid {c['secondary']};
                border-radius: 3px;
                padding: 4px;
                font-size: {fs}px;
            }}
        """)
        bottom_row.addWidget(self.free_edit, stretch=1)

        left_layout.addLayout(bottom_row)

        card_panel = QFrame()
        card_panel.setFixedWidth(52)
        card_panel.setStyleSheet(f"QFrame {{ background-color: {c['panel_bg']}; border-radius: 4px; }}")
        card_layout = QVBoxLayout(card_panel)
        card_layout.setContentsMargins(4, 6, 4, 6)
        card_layout.setSpacing(3)

        card_header = QLabel("答题卡")
        card_header.setAlignment(Qt.AlignCenter)
        card_header.setStyleSheet(f"color: {c['text']}; font-size: {fs}px; font-weight: bold;")
        card_layout.addWidget(card_header)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color: {c['secondary']};")
        card_layout.addWidget(line)

        self.cards_area = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_area)
        self.cards_layout.setContentsMargins(0, 2, 0, 2)
        self.cards_layout.setSpacing(2)
        self.cards_layout.addStretch()
        card_layout.addWidget(self.cards_area, stretch=1)

        main_layout.addWidget(left_area, stretch=1)
        main_layout.addWidget(card_panel)

    def submit(self):
        self._on_submit()

    def set_choices(self, choices: list):
        self._all_choices = choices
        self._question_checkboxes.clear()
        self._card_buttons.clear()
        self._question_headers.clear()
        self._short_answer_inputs.clear()
        self._single_choice_groups.clear()
        self._question_widgets.clear()
        self._question_data.clear()

        for cb in self._question_group.buttons():
            self._question_group.removeButton(cb)

        while self.choices_layout.count():
            item = self.choices_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

        c = self.tm.colors
        fs = self.tm.font_size

        choice_list = choices if choices else [{"text": "（无选项）", "type": "select"}]

        grouped = OrderedDict()
        group_order = []
        for ch in choice_list:
            if ch.get("type") == "free":
                continue
            q = ch.get("question", "") or ch.get("text", "")
            if q not in grouped:
                grouped[q] = []
                group_order.append(q)
            grouped[q].append(ch)

        for gi, q_key in enumerate(group_order):
            opts = grouped[q_key]
            q_label_text = q_key

            q_container = QWidget()
            q_container.setStyleSheet("background-color: transparent;")
            q_layout = QVBoxLayout(q_container)
            q_layout.setContentsMargins(0, 0, 0, 0)
            q_layout.setSpacing(4)

            q_header = QLabel(q_label_text)
            q_header.setFont(self.tm.make_font(1))
            q_header.setStyleSheet(f"""
                color: {c['accent']};
                font-size: {fs + 4}px;
                font-weight: bold;
                padding: 4px 2px 2px 2px;
            """)
            q_layout.addWidget(q_header)
            self._question_headers.append(q_header)

            is_single = opts[0].get("type") == "single_choice" if opts else False
            single_group = None
            if is_single:
                single_group = QButtonGroup(self)
                single_group.setExclusive(True)
                self._single_choice_groups.append(single_group)

            q_checkboxes = []
            q_short_answer = None

            for i, ch in enumerate(opts):
                ch_type = ch.get("type", "choice")

                if ch_type == "short_answer":
                    hint = QLabel(f"  （简答）")
                    hint.setFont(self.tm.make_font(-1))
                    hint.setStyleSheet(f"color: {c['text_dim']}; font-size: {fs}px; padding: 0 2px;")
                    q_layout.addWidget(hint)

                    sa_input = QLineEdit()
                    sa_input.setPlaceholderText("在此输入你的回答...")
                    sa_input.setFont(self.tm.make_font())
                    sa_input.setStyleSheet(f"""
                        QLineEdit {{
                            background-color: {c['input_bg']};
                            color: {c['text']};
                            border: 1px solid {c['secondary']};
                            border-radius: 3px;
                            padding: 6px 8px;
                            font-size: {fs}px;
                        }}
                    """)
                    q_layout.addWidget(sa_input)
                    self._short_answer_inputs.append((ch.get("text", ""), sa_input))
                    q_short_answer = sa_input
                else:
                    if is_single:
                        btn = QRadioButton(ch.get("text", f"选项 {i + 1}"))
                        single_group.addButton(btn)
                    else:
                        btn = QCheckBox(ch.get("text", f"选项 {i + 1}"))
                        self._question_group.addButton(btn)
                        self._question_checkboxes.append(btn)
                        q_checkboxes.append(btn)

                    btn.setFont(self.tm.make_font())
                    btn.setStyleSheet(f"""
                        {"QRadioButton" if is_single else "QCheckBox"} {{
                            color: {c['text']};
                            font-size: {fs}px;
                            spacing: 10px;
                            padding: 4px 2px;
                        }}
                        {"QRadioButton::indicator" if is_single else "QCheckBox::indicator"} {{
                            width: 18px; height: 18px;
                            border: 1px solid {c['border']};
                            border-radius: {"9px" if is_single else "3px"};
                            background-color: {c['input_bg']};
                        }}
                        {"QRadioButton::indicator:checked" if is_single else "QCheckBox::indicator:checked"} {{
                            background-color: {c['accent']};
                            border-color: {c['accent']};
                        }}
                    """)
                    q_layout.addWidget(btn)

            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setStyleSheet(f"color: {c['border']};")
            sep.setMaximumHeight(1)
            q_layout.addWidget(sep)

            self.choices_layout.addWidget(q_container)
            self._question_widgets.append(q_container)
            self._question_data.append({
                "checkboxes": q_checkboxes,
                "single_group": single_group,
                "short_answer": q_short_answer,
                "question_number": gi + 1,
            })

        self.choices_layout.addStretch()

        for gi in range(len(group_order)):
            card_btn = QPushButton(str(gi + 1))
            card_btn.setFixedSize(38, 24)
            card_btn.setCursor(Qt.PointingHandCursor)
            card_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c['input_bg']};
                    color: {c['text_dim']};
                    border: 1px solid {c['border']};
                    border-radius: 3px;
                    font-size: {fs}px;
                }}
                QPushButton:hover {{
                    background-color: {c['secondary']};
                    color: {c['text']};
                }}
            """)
            idx = gi
            card_btn.clicked.connect(lambda checked, x=idx: self._jump_to_card(x))
            self.cards_layout.addWidget(card_btn)
            self._card_buttons.append(card_btn)

        self.cards_layout.addStretch()

        if self._question_widgets:
            for i, w in enumerate(self._question_widgets):
                w.setVisible(i == 0)
            self._current_question = 0
        self._update_card_style()

    def _jump_to_card(self, index: int):
        if 0 <= index < len(self._question_widgets):
            self._question_widgets[self._current_question].setVisible(False)
            self._question_widgets[index].setVisible(True)
            self._current_question = index
            self.scroll_area.verticalScrollBar().setValue(0)
            self._update_card_style()

    def _update_card_style(self):
        c = self.tm.colors
        fs = self.tm.font_size
        for i, btn in enumerate(self._card_buttons):
            if i == self._current_question:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {c['accent']};
                        color: white;
                        border: none;
                        border-radius: 3px;
                        font-size: {fs}px;
                        font-weight: bold;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {c['input_bg']};
                        color: {c['text_dim']};
                        border: 1px solid {c['border']};
                        border-radius: 3px;
                        font-size: {fs}px;
                    }}
                    QPushButton:hover {{
                        background-color: {c['secondary']};
                        color: {c['text']};
                    }}
                """)

    def _on_submit(self):
        unanswered = []
        for qd in self._question_data:
            has_check = any(cb.isChecked() for cb in qd["checkboxes"])
            has_radio = qd["single_group"] is not None and qd["single_group"].checkedButton() is not None
            has_short = qd["short_answer"] is not None and qd["short_answer"].text().strip()
            if not has_check and not has_radio and not has_short:
                unanswered.append(qd["question_number"])

        if unanswered:
            nums = "、".join(f"第{n}题" for n in unanswered)
            reply = QMessageBox.question(
                self, "未完成题目",
                f"还有未完成的题目（{nums}），是否忽略？\n未完成的题目将由AI自行决定。",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        result = []
        for cb in self._question_checkboxes:
            if cb.isChecked():
                result.append({"text": cb.text(), "type": "choice"})
        for group in self._single_choice_groups:
            checked = group.checkedButton()
            if checked:
                result.append({"text": checked.text(), "type": "single_choice"})
        for q_text, sa_input in self._short_answer_inputs:
            answer = sa_input.text().strip()
            if answer:
                result.append({"text": f"问题：{q_text}\n回答：{answer}", "type": "short_answer"})
        free_text = self.free_edit.toPlainText().strip()
        if free_text:
            result.append({"text": free_text, "type": "free"})
        self.turn_submitted.emit(result)

    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        self.free_edit.setEnabled(enabled)
        for cb in self._question_checkboxes:
            cb.setEnabled(enabled)
        for group in self._single_choice_groups:
            for btn in group.buttons():
                btn.setEnabled(enabled)
        for _, sa_input in self._short_answer_inputs:
            sa_input.setEnabled(enabled)
