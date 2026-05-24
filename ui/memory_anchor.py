"""
记忆锚点界面
显示故事大事件时间线，支持分支存档
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QListWidget, QListWidgetItem, QPushButton,
                             QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt
from models.memory import MemoryChain
from ui.theme_manager import get_theme


class MemoryAnchorDialog(QDialog):
    def __init__(self, game_state, save_manager, parent=None):
        super().__init__(parent)
        self.game_state = game_state
        self.save_manager = save_manager
        self.tm = get_theme()
        self.setWindowTitle("记忆锚点")
        self.setMinimumSize(480, 500)
        self._setup_ui()
        self._load_anchors()

    def _setup_ui(self):
        c = self.tm.colors
        fs = self.tm.font_size
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("故事记忆链")
        title.setStyleSheet(f"color: {c['text']}; font-size: {fs + 2}px; font-weight: bold;")
        layout.addWidget(title)

        desc = QLabel("点击某一锚点可以从该时间点分支新存档，重新体验不同的故事走向。\n分支存档不具有旧存档后面的记忆。")
        desc.setStyleSheet(f"color: {c['text_dim']}; font-size: {max(fs - 2, 10)}px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.anchor_list = QListWidget()
        self.anchor_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {c['input_bg']};
                color: {c['text']};
                border: 1px solid {c['border']};
                border-radius: 4px;
                font-size: {fs}px;
            }}
            QListWidget::item {{
                padding: 6px;
                border-bottom: 1px solid {c['border']};
            }}
            QListWidget::item:hover {{
                background-color: {c['secondary']};
            }}
            QListWidget::item:selected {{
                background-color: {c['accent']};
            }}
        """)
        layout.addWidget(self.anchor_list)

        btn_layout = QHBoxLayout()
        self.branch_btn = QPushButton("从此锚点分支")
        self.branch_btn.clicked.connect(self._branch_from_anchor)
        btn_layout.addWidget(self.branch_btn)
        btn_layout.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        btn_qss = f"""
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
        """
        self.branch_btn.setStyleSheet(btn_qss)
        close_btn.setStyleSheet(btn_qss)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {c['background']};
            }}
        """)

    def _load_anchors(self):
        self.anchor_list.clear()
        if self.game_state is None:
            return

        chain = self.game_state.memory_chain
        if not chain.anchors:
            self.anchor_list.addItem("（尚无记忆锚点）")
            return

        sorted_anchors = sorted(chain.anchors, key=lambda a: a.turn)
        for anchor in sorted_anchors:
            item_text = f"第{anchor.turn}回合（第{anchor.day}天）\n{anchor.title}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, anchor.id)
            self.anchor_list.addItem(item)

    def _branch_from_anchor(self):
        current_item = self.anchor_list.currentItem()
        if current_item is None:
            QMessageBox.warning(self, "提示", "请选择一个记忆锚点")
            return

        anchor_id = current_item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "分支存档",
            f"确定要从该锚点分支新存档吗？\n新存档将从该时间节点重新开始，不具有此后的记忆。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            filepath = self.save_manager.save(self.game_state)
            QMessageBox.information(self, "成功", f"分支存档已保存：\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))
