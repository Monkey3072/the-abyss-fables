"""
角色数据模型
管理主角和NPC的属性、状态、外观描述
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Character:
    name: str = "未命名"
    role: str = "主角"
    description: str = ""
    appearance: str = ""
    background: str = ""

    hp: int = 100
    max_hp: int = 100
    mp: int = 50
    max_mp: int = 50
    level: int = 1
    experience: int = 0

    strength: int = 10
    agility: int = 10
    intelligence: int = 10
    charisma: int = 10
    luck: int = 5

    status_effects: list = field(default_factory=list)
    hidden: bool = False

    def to_dict(self):
        return {
            "name": self.name,
            "role": self.role,
            "description": self.description,
            "appearance": self.appearance,
            "background": self.background,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "mp": self.mp,
            "max_mp": self.max_mp,
            "level": self.level,
            "experience": self.experience,
            "strength": self.strength,
            "agility": self.agility,
            "intelligence": self.intelligence,
            "charisma": self.charisma,
            "luck": self.luck,
            "status_effects": self.status_effects,
            "hidden": self.hidden,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**{k: data.get(k, v) for k, v in cls().__dict__.items()})

    def take_damage(self, amount: int):
        self.hp = max(0, self.hp - amount)

    def heal(self, amount: int):
        self.hp = min(self.max_hp, self.hp + amount)

    def is_alive(self):
        return self.hp > 0

    def status_summary(self):
        emojis = {"hp": "❤️", "mp": "💙", "strength": "💪", "agility": "🏃",
                  "intelligence": "🧠", "charisma": "🎭", "luck": "🍀"}
        _labels = {"strength": "力量", "agility": "敏捷", "intelligence": "智力", "charisma": "魅力", "luck": "运气"}
        lines = [f"🎯 {self.name}（{self.role}）"]
        for attr, emoji in emojis.items():
            if attr == "hp":
                lines.append(f"  {emoji} HP: {self.hp}/{self.max_hp}")
            elif attr == "mp":
                lines.append(f"  {emoji} MP: {self.mp}/{self.max_mp}")
            else:
                val = getattr(self, attr, 0)
                label = _labels.get(attr, attr)
                lines.append(f"  {emoji} {label}: {val}")
        if self.status_effects:
            lines.append(f"  ⚡ 状态: {', '.join(self.status_effects)}")
        return "\n".join(lines)
