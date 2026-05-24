"""
存档管理模块
负责保存和加载游戏进度
"""
import json
import os
from pathlib import Path
from datetime import datetime
from config import SAVES_DIR
from models.game_state import GameState

SAVE_EXTENSION = ".save"


class SaveManager:
    @staticmethod
    def list_saves():
        saves = []
        for f in SAVES_DIR.glob(f"*{SAVE_EXTENSION}"):
            try:
                stat = f.stat()
                saves.append({
                    "path": str(f),
                    "name": f.stem,
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                })
            except Exception:
                pass
        return sorted(saves, key=lambda s: s["modified"], reverse=True)

    @staticmethod
    def save(game_state: GameState, slot_name: str = ""):
        if not slot_name:
            slot_name = f"save_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        filepath = SAVES_DIR / f"{slot_name}{SAVE_EXTENSION}"
        data = game_state.to_dict()
        data["_save_meta"] = {
            "saved_at": datetime.now().isoformat(),
            "turn": game_state.turn,
            "day": game_state.day,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return str(filepath)

    @staticmethod
    def load(filepath: str) -> GameState:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"存档文件不存在: {filepath}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.pop("_save_meta", None)
        return GameState.from_dict(data)

    @staticmethod
    def delete_save(filepath: str):
        path = Path(filepath)
        if path.exists():
            os.remove(path)
