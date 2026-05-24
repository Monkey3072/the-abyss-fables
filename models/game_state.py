"""
游戏状态数据模型
包含完整的游戏运行状态
"""
from dataclasses import dataclass, field
from models.character import Character
from models.inventory import Inventory, Item
from models.memory import MemoryChain


@dataclass
class GameState:
    seed: dict = field(default_factory=dict)
    protagonist: Character = field(default_factory=Character)
    companions: list = field(default_factory=list)
    enemies: list = field(default_factory=list)
    inventory: Inventory = field(default_factory=lambda: Inventory(owner_name="主角"))
    memory_chain: MemoryChain = field(default_factory=MemoryChain)
    turn: int = 0
    day: int = 1
    time_of_day: str = "早晨"
    location: str = "未知之地"
    weather: str = "晴朗"
    story_history: list = field(default_factory=list)
    current_choices: list = field(default_factory=list)
    current_story: str = ""
    game_over: bool = False
    game_over_reason: str = ""

    def to_dict(self):
        return {
            "seed": self.seed,
            "protagonist": self.protagonist.to_dict(),
            "companions": [c.to_dict() for c in self.companions],
            "enemies": [e.to_dict() for e in self.enemies],
            "inventory": self.inventory.to_dict(),
            "memory_chain": self.memory_chain.to_dict(),
            "turn": self.turn,
            "day": self.day,
            "time_of_day": self.time_of_day,
            "location": self.location,
            "weather": self.weather,
            "story_history": self.story_history,
            "current_choices": self.current_choices,
            "current_story": self.current_story,
            "game_over": self.game_over,
            "game_over_reason": self.game_over_reason,
        }

    @classmethod
    def from_dict(cls, data: dict):
        state = cls()
        state.seed = data.get("seed", {})
        if "protagonist" in data:
            state.protagonist = Character.from_dict(data["protagonist"])
        state.companions = [Character.from_dict(c) for c in data.get("companions", [])]
        state.enemies = [Character.from_dict(e) for e in data.get("enemies", [])]
        state.inventory = Inventory.from_dict(data.get("inventory", {"owner_name": "主角"}))
        state.memory_chain = MemoryChain.from_dict(data.get("memory_chain", {}))
        state.turn = data.get("turn", 0)
        state.day = data.get("day", 1)
        state.time_of_day = data.get("time_of_day", "早晨")
        state.location = data.get("location", "未知之地")
        state.weather = data.get("weather", "晴朗")
        state.story_history = data.get("story_history", [])
        state.current_choices = data.get("current_choices", [])
        state.current_story = data.get("current_story", "")
        state.game_over = data.get("game_over", False)
        state.game_over_reason = data.get("game_over_reason", "")
        return state

    def add_story_entry(self, story_text: str, choices_made: list):
        entry = {
            "turn": self.turn,
            "story": story_text,
            "choices": choices_made,
            "location": self.location,
            "day": self.day,
            "time_of_day": self.time_of_day,
        }
        self.story_history.append(entry)

    def get_character_by_name(self, name: str):
        for c in self.companions:
            if c.name == name:
                return c
        for e in self.enemies:
            if e.name == name:
                return e
        return None
