from pathlib import Path

APP_NAME = "渊索寓言"
VERSION = "1.0.0"
AUTHOR = "Monkey3072"

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "素材"
START_IMAGE = ASSETS_DIR / "start.png"
SAVES_DIR = BASE_DIR / "saves"
SEEDS_DIR = BASE_DIR / "seeds"
LOGS_DIR = BASE_DIR / "logs"

ASSETS_DIR.mkdir(exist_ok=True)
SAVES_DIR.mkdir(exist_ok=True)
SEEDS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

DEFAULT_CONFIG = {
    "api": {
        "base_url": "https://api.deepseek.com",
        "api_key": "",
        "model": "deepseek-v4-flash",
    },
    "display": {
        "resolution": "1280x720",
        "font_family": "Microsoft YaHei",
        "font_size": 12,
        "ui_color": "暗夜蓝",
        "background_image": "",
    },
    "audio": {
        "music_volume": 80,
        "sfx_volume": 80,
    },
}
