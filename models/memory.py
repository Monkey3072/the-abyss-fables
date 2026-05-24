"""
记忆锚点数据模型
记录故事中的重大事件，支持分支存档
"""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MemoryAnchor:
    id: int = 0
    turn: int = 0
    day: int = 1
    title: str = ""
    summary: str = ""
    timestamp: str = ""
    parent_anchor_id: int = -1

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self):
        return {
            "id": self.id,
            "turn": self.turn,
            "day": self.day,
            "title": self.title,
            "summary": self.summary,
            "timestamp": self.timestamp,
            "parent_anchor_id": self.parent_anchor_id,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


@dataclass
class MemoryChain:
    anchors: list = field(default_factory=list)
    next_id: int = 0

    def add_anchor(self, turn: int, day: int, title: str, summary: str, parent_id: int = -1):
        anchor = MemoryAnchor(
            id=self.next_id,
            turn=turn,
            day=day,
            title=title,
            summary=summary,
            parent_anchor_id=parent_id if parent_id >= 0 else (self.next_id - 1 if self.anchors else -1),
        )
        self.anchors.append(anchor)
        self.next_id += 1
        return anchor

    def get_anchor(self, anchor_id: int):
        for a in self.anchors:
            if a.id == anchor_id:
                return a
        return None

    def to_dict(self):
        return {
            "anchors": [a.to_dict() for a in self.anchors],
            "next_id": self.next_id,
        }

    @classmethod
    def from_dict(cls, data: dict):
        chain = cls(next_id=data.get("next_id", 0))
        for a_data in data.get("anchors", []):
            chain.anchors.append(MemoryAnchor.from_dict(a_data))
        return chain

    def chain_display(self):
        if not self.anchors:
            return "📜 尚无记忆锚点"
        lines = ["📜 记忆锚点链："]
        sorted_anchors = sorted(self.anchors, key=lambda a: a.turn)
        for a in sorted_anchors:
            lines.append(f"  ● 第{a.turn}回合（第{a.day}天）：{a.title}")
        return "\n".join(lines)
