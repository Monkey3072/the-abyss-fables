import json
import copy
from pathlib import Path
from config.defaults import DEFAULT_CONFIG
from models.validators import validate_config, ConfigValidator
from pydantic import ValidationError


def get_config_path():
    return Path(__file__).resolve().parent.parent / "config_data" / "config.json"


def _deep_update(base, override):
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_update(base[key], value)
        else:
            base[key] = value


def load_config():
    config_path = get_config_path()
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            cfg = copy.deepcopy(DEFAULT_CONFIG)
            _deep_update(cfg, saved)
            return validate_config(cfg)
        except (ValidationError, Exception):
            return copy.deepcopy(DEFAULT_CONFIG)
    return copy.deepcopy(DEFAULT_CONFIG)


def save_config(config):
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
