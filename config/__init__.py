from config.defaults import (
    APP_NAME, VERSION, AUTHOR, BASE_DIR, ASSETS_DIR, START_IMAGE, DEFAULT_CONFIG,
    SAVES_DIR, SEEDS_DIR, LOGS_DIR,
)
from config.io import load_config, save_config, get_config_path
from config.themes import UI_COLORS, CURRENT_THEME, get_colors
from config.fonts import FONT_DISPLAY_NAMES, EXTRA_FONT_KEYWORDS, get_chinese_fonts
