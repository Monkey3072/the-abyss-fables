"""
人物状态面板
显示主角状态、同伴角色、物品栏等
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTextEdit,
                             QTabWidget, QPushButton, QHBoxLayout,
                             QListWidget, QListWidgetItem, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from ui.theme_manager import get_theme


_ITEM_TYPE_NAMES = {
    "weapon": "武器",
    "armor": "防具",
    "consumable": "消耗品",
    "key_item": "关键物品",
    "material": "材料",
    "misc": "杂物",
}


class StatusPanel(QWidget):
    transfer_item_requested = pyqtSignal(str, str)
    item_action_requested = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tm = get_theme()
        self._setup_ui()

    def _setup_ui(self):
        c = self.tm.colors
        fs = self.tm.font_size
        ff = self.tm.font_family
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                background-color: {c['panel_bg']};
                border: 1px solid {c['border']};
                border-radius: 4px;
            }}
            QTabBar::tab {{
                background-color: {c['input_bg']};
                color: {c['text_dim']};
                padding: 6px 12px;
                border-radius: 4px 4px 0 0;
                margin-right: 2px;
                font-size: {fs + 4}px;
            }}
            QTabBar::tab:selected {{
                background-color: {c['panel_bg']};
                color: {c['text']};
            }}
        """)

        self.status_tab = QWidget()
        self.status_layout = QVBoxLayout(self.status_tab)
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setFont(self.tm.make_font(-1))
        self.status_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {c['panel_bg']};
                color: {c['text']};
                border: none;
                line-height: 1.6;
            }}
        """)
        self.status_layout.addWidget(self.status_text)
        self.tabs.addTab(self.status_tab, " 状态")

        self.inventory_tab = QWidget()
        inv_layout = QVBoxLayout(self.inventory_tab)
        self.inv_list = QListWidget()
        self.inv_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {c['panel_bg']};
                color: {c['text']};
                border: none;
                font-size: {fs}px;
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
        """)
        inv_layout.addWidget(self.inv_list)

        btn_layout = QHBoxLayout()
        btn_style = f"""
            QPushButton {{
                background-color: {c['accent']};
                color: white;
                border: none;
                border-radius: 3px;
                padding: 4px 8px;
                font-size: {fs}px;
            }}
            QPushButton:hover {{
                background-color: {self.tm._hlight(c['accent'])};
            }}
        """
        self.use_btn = QPushButton("使用")
        self.use_btn.setStyleSheet(btn_style)
        self.use_btn.clicked.connect(self._on_use_item)
        self.drop_btn = QPushButton("丢弃")
        self.drop_btn.setStyleSheet(btn_style)
        self.drop_btn.clicked.connect(self._on_discard_item)
        btn_layout.addWidget(self.use_btn)
        btn_layout.addWidget(self.drop_btn)
        btn_layout.addStretch()
        inv_layout.addLayout(btn_layout)
        self.tabs.addTab(self.inventory_tab, " 物品")

        self.characters_tab = QWidget()
        char_layout = QVBoxLayout(self.characters_tab)
        char_layout.setContentsMargins(2, 2, 2, 2)
        self.char_display = QTextEdit()
        self.char_display.setReadOnly(True)
        self.char_display.setFont(self.tm.make_font(-1))
        self.char_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: {c['panel_bg']};
                color: {c['text']};
                border: none;
                padding: 4px;
            }}
            QScrollBar:vertical {{
                background: {c['background']};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {c['border']};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        char_layout.addWidget(self.char_display)
        self.tabs.addTab(self.characters_tab, " 人物")

        layout.addWidget(self.tabs)

    def update_status(self, game_state):
        if game_state is None:
            self.status_text.setText("等待游戏开始...")
            return

        text = game_state.protagonist.status_summary()
        text += f"\n\n 位置：{game_state.location}"
        text += f"\n 天气：{game_state.weather}"
        text += f"\n 时间：第{game_state.day}天 {game_state.time_of_day}"
        text += f"\n 回合：{game_state.turn}"

        if game_state.game_over:
            text += f"\n\n 游戏结束：{game_state.game_over_reason}"

        self.status_text.setText(text)

    def update_inventory(self, game_state):
        self.inv_list.clear()
        if game_state is None or not game_state.inventory.items:
            self.inv_list.addItem("（空）")
            return
        for item in game_state.inventory.items:
            type_name = _ITEM_TYPE_NAMES.get(item.item_type, item.item_type)
            label = f"{item.name} x{item.quantity} [{type_name}]"
            if item.is_key_item:
                label = " " + label
            self.inv_list.addItem(label)

    def update_characters(self, game_state):
        c = self.tm.colors
        fs = self.tm.font_size

        if game_state is None or not game_state.companions:
            self.char_display.setHtml(
                f'<p style="color:{c["text_dim"]};font-size:{fs}px;line-height:1.8;">（无角色）</p>'
            )
            return

        companions = []
        enemies = []
        others = []

        companion_kw = ['同伴', '队友', '伙伴', 'friend', 'ally']
        enemy_kw = ['敌人', '敌对', '敌', 'enemy', 'antagonist']

        for ch in game_state.companions:
            role_lower = ch.role.lower()

            if any(kw in role_lower for kw in companion_kw):
                companions.append(ch)
            elif any(kw in role_lower for kw in enemy_kw):
                enemies.append(ch)
            elif not ch.hidden:
                companions.append(ch)
            else:
                others.append(ch)

        html = ""
        for group_name, chars in [("同伴", companions), ("敌人", enemies), ("其他角色", others)]:
            if not chars:
                continue
            html += f'<p style="color:{c["accent"]};font-size:{fs + 2}px;font-weight:bold;line-height:1.8;margin:4px 0;">── {group_name} ──</p>'
            for ch in chars:
                html += f'<p style="line-height:1.8;margin:3px 0;"><span style="color:{c["text"]};font-weight:bold;font-size:{fs}px;">{ch.name}</span> '
                html += f'<span style="color:{c["accent"]};font-size:{fs - 1}px;">[{ch.role}]</span></p>'
                if ch.description:
                    html += f'<p style="color:{c["text_dim"]};font-size:{fs}px;line-height:1.7;margin-left:12px;">{ch.description}</p>'
        self.char_display.setHtml(html)

    def update_companions(self, game_state):
        self.update_characters(game_state)

    def _get_selected_item_name(self) -> str:
        item = self.inv_list.currentItem()
        if not item:
            return ""
        raw = item.text().strip()
        if " [" in raw:
            raw = raw[: raw.rindex(" [")]
        if " x" in raw:
            raw = raw[: raw.rindex(" x")]
        return raw.strip()

    def _on_use_item(self):
        item_name = self._get_selected_item_name()
        if not item_name:
            QMessageBox.warning(self, "提示", "请先选择一个物品")
            return
        self.item_action_requested.emit("use", item_name)

    def _on_discard_item(self):
        item_name = self._get_selected_item_name()
        if not item_name:
            QMessageBox.warning(self, "提示", "请先选择一个物品")
            return
        reply = QMessageBox.question(
            self, "确认丢弃", f"确定要丢弃「{item_name}」吗？\n此操作将在下回合生效。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.item_action_requested.emit("discard", item_name)
