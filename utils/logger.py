try:
    import sys
    from loguru import logger as _logger
    _logger.remove()
    _logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG",
    )
    _logger.add(
        "logs/game_{time:YYYY-MM-DD}.log",
        rotation="10 MB",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
    )
    logger = _logger
except ImportError:
    import logging as _logging
    import os as _os
    _os.makedirs("logs", exist_ok=True)
    _logging.basicConfig(
        level=_logging.DEBUG,
        format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        handlers=[
            _logging.StreamHandler(sys.stderr),
            _logging.FileHandler("logs/game.log", encoding="utf-8"),
        ],
    )
    logger = _logging.getLogger("GAME")
