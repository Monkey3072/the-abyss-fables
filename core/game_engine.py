"""
游戏引擎核心
负责协调AI调用、状态管理和回合推进
"""
from config import load_config, save_config
from core.ai_client import AIClient
from core.seed_manager import SeedManager
from core.save_manager import SaveManager
from core.response_parser import parse_ai_response
from prompts.system_prompts import build_system_prompt, build_turn_prompt, build_ending_prompt
from models.game_state import GameState
from models.character import Character
from models.inventory import Inventory, Item
from models.memory import MemoryChain


class GameEngine:
    def __init__(self):
        self.config = load_config()
        self.ai_client = AIClient(
            api_key=self.config["api"]["api_key"],
            base_url=self.config["api"]["base_url"],
            model=self.config["api"]["model"],
        )
        self.seed_manager = SeedManager()
        self.save_manager = SaveManager()
        self.game_state: GameState = None
        self.system_prompt = ""
        self._session_prompt_tokens = 0
        self._session_completion_tokens = 0
        self._pending_item_actions = []
        self.callbacks = {
            "on_story_chunk": None,
            "on_turn_complete": None,
            "on_error": None,
        }

    def update_api_config(self, api_key: str, base_url: str, model: str):
        self.config["api"]["api_key"] = api_key
        self.config["api"]["base_url"] = base_url
        self.config["api"]["model"] = model
        save_config(self.config)
        self.ai_client.update_config(api_key=api_key, base_url=base_url, model=model)

    def test_connection(self):
        return self.ai_client.test_connection()

    def init_game_state(self, seed: dict):
        self.game_state = GameState()
        self.game_state.seed = seed
        self.system_prompt = build_system_prompt(seed)

        p = seed.get("protagonist_setting", {})
        self.game_state.protagonist = Character(
            name=p.get("name", "冒险者"),
            role="主角",
            description=p.get("personality", ""),
            background=p.get("background", ""),
            appearance=p.get("appearance", ""),
        )
        self.game_state.inventory = Inventory(owner_name=self.game_state.protagonist.name)

    def get_system_prompt(self):
        return self.system_prompt

    def build_first_turn_prompt(self, seed: dict):
        return f"""开始新的冒险故事。

故事名称：{seed.get('name', '新的故事')}
故事背景：{seed.get('background', '')}
世界观设定：{seed.get('world_setting', '')}
主角信息：
- 姓名：{self.game_state.protagonist.name}
- 描述：{self.game_state.protagonist.description}
- 背景：{self.game_state.protagonist.background}
- 外貌：{self.game_state.protagonist.appearance}

难度：{seed.get('difficulty', '普通')}

请创作故事的开场，引入世界、角色和初始情境。"""

    def build_turn_prompt_text(self, choices: list, god_text: str = ""):
        if self.game_state is None:
            raise RuntimeError("没有进行中的游戏")
        self.game_state.turn += 1
        state_dict = self.game_state.to_dict()
        pending_actions = self._get_and_clear_item_actions()
        return build_turn_prompt(state_dict, choices, god_text, pending_actions)

    def apply_turn_result(self, parsed: dict, is_first: bool = False):
        story_text = parsed.get("story", "")
        self.game_state.current_story = story_text
        self.game_state.current_choices = parsed.get("choices", [])

        meta = parsed.get("meta", {})
        new_loc = meta.get("location")
        new_time = meta.get("time_of_day")
        new_weather = meta.get("weather")
        if new_loc:
            self.game_state.location = new_loc
        if new_time:
            self.game_state.time_of_day = new_time
        if new_weather:
            self.game_state.weather = new_weather

        if not is_first and self.game_state.turn > 0:
            times = ["早晨", "上午", "下午", "傍晚", "夜晚", "深夜"]
            current_idx = times.index(self.game_state.time_of_day) if self.game_state.time_of_day in times else 0
            if current_idx < len(times) - 1:
                self.game_state.time_of_day = times[current_idx + 1]
            else:
                self.game_state.time_of_day = times[0]
                self.game_state.day += 1

        char_status = parsed.get("character_status", {})
        if "hp" in char_status:
            self.game_state.protagonist.hp = char_status["hp"]
        if "mp" in char_status:
            self.game_state.protagonist.mp = char_status["mp"]
        if "status_effects" in char_status:
            self.game_state.protagonist.status_effects = char_status["status_effects"]

        events = parsed.get("events", [])
        if events:
            self.game_state.memory_chain.add_anchor(
                turn=self.game_state.turn,
                day=self.game_state.day,
                title=events[0][:50],
                summary="; ".join(events),
            )

        items_changed = parsed.get("items_changed", {})
        for item_data in items_changed.get("added", []):
            if isinstance(item_data, str):
                new_item = Item(name=item_data, item_type="物品")
            else:
                new_item = Item(**item_data)
            try:
                self.game_state.inventory.add_item(new_item)
            except ValueError:
                pass
        for item_name in items_changed.get("removed", []):
            self.game_state.inventory.remove_item(item_name)

        self.game_state.add_story_entry(story_text, self.game_state.current_choices)

        if meta.get("should_end", False):
            self.game_state.game_over = True
            self.game_state.game_over_reason = meta.get("ending_reason", "故事已完结")

        if self.callbacks.get("on_turn_complete"):
            self.callbacks["on_turn_complete"](parsed, self.game_state)

        return self.game_state

    def generate_ending_template(self):
        if self.game_state is None:
            raise RuntimeError("没有进行中的游戏")
        prompt = build_ending_prompt(self.game_state.to_dict())
        return self.ai_client.chat(self.system_prompt, prompt)

    def add_prompt_tokens(self, count: int):
        self._session_prompt_tokens += count

    def add_completion_tokens(self, count: int):
        self._session_completion_tokens += count

    def get_session_tokens(self) -> tuple:
        return (self._session_prompt_tokens, self._session_completion_tokens)

    def reset_session_tokens(self):
        self._session_prompt_tokens = 0
        self._session_completion_tokens = 0

    def add_item_action(self, action: str, item_name: str):
        self._pending_item_actions.append((action, item_name))
        if self.game_state:
            if action == "use":
                self.game_state.inventory.remove_item(item_name)
            elif action == "discard":
                self.game_state.inventory.remove_item(item_name)

    def _get_and_clear_item_actions(self) -> list:
        actions = list(self._pending_item_actions)
        self._pending_item_actions.clear()
        return actions

    def reset_item_actions(self):
        self._pending_item_actions.clear()
