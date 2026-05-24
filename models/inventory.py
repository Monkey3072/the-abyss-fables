"""
物品栏数据模型
管理物品的创建、存储、使用和转移
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Item:
    name: str = ""
    item_type: str = "杂物"
    description: str = ""
    quantity: int = 1
    effects: dict = field(default_factory=dict)
    is_key_item: bool = False

    def to_dict(self):
        return {
            "name": self.name,
            "item_type": self.item_type,
            "description": self.description,
            "quantity": self.quantity,
            "effects": self.effects,
            "is_key_item": self.is_key_item,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**{k: data.get(k, v) for k, v in cls().__dict__.items()})


@dataclass
class Inventory:
    owner_name: str = ""
    items: list = field(default_factory=list)
    max_slots: int = 20

    def add_item(self, item: Item):
        for existing in self.items:
            if existing.name == item.name and not existing.is_key_item:
                existing.quantity += item.quantity
                return
        if len(self.items) < self.max_slots:
            self.items.append(item)
        else:
            raise ValueError("物品栏已满")

    def remove_item(self, item_name: str, quantity: int = 1):
        for item in self.items:
            if item.name == item_name:
                if item.quantity <= quantity:
                    self.items.remove(item)
                else:
                    item.quantity -= quantity
                return item
        return None

    def has_item(self, item_name: str):
        for item in self.items:
            if item.name == item_name:
                return True
        return False

    def get_item(self, item_name: str) -> Optional[Item]:
        for item in self.items:
            if item.name == item_name:
                return item
        return None

    def to_dict(self):
        return {
            "owner_name": self.owner_name,
            "items": [item.to_dict() for item in self.items],
            "max_slots": self.max_slots,
        }

    @classmethod
    def from_dict(cls, data: dict):
        inv = cls(
            owner_name=data.get("owner_name", ""),
            max_slots=data.get("max_slots", 20),
        )
        for item_data in data.get("items", []):
            inv.items.append(Item.from_dict(item_data))
        return inv

    def summary(self):
        if not self.items:
            return f"📦 {self.owner_name}的背包是空的"
        lines = [f"📦 {self.owner_name}的背包（{len(self.items)}/{self.max_slots}）："]
        for i, item in enumerate(self.items, 1):
            qty = f"x{item.quantity}" if item.quantity > 1 else ""
            key = "🔑" if item.is_key_item else ""
            lines.append(f"  {i}. {key}{item.name} {qty} [{item.item_type}]")
        return "\n".join(lines)
