"""
渊索寓言（The Abyss Fables）- 主入口
AI驱动的文字冒险游戏
"""
import sys
import os

os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")


def main():
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QFont, QIcon
    from config import load_config
    from ui.main_window import MainWindow

    import ctypes
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("theabyss.fables")
    except Exception:
        pass

    app = QApplication(sys.argv)

    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "素材", "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    try:
        import qasync
        loop = qasync.QEventLoop(app)
        import asyncio
        asyncio.set_event_loop(loop)
    except ImportError:
        pass

    from ui.theme_manager import get_theme
    app.setStyleSheet(get_theme().global_qss)

    app.setApplicationName("渊索寓言")
    app.setOrganizationName("The Abyss Fables")

    config = load_config()
    font_family = config.get("display", {}).get("font_family", "Microsoft YaHei")
    font_size = config.get("display", {}).get("font_size", 12)
    font = QFont(font_family, font_size)
    app.setFont(font)

    window = MainWindow()
    window.show()

    try:
        import qasync
        with loop:
            loop.run_forever()
    except (ImportError, NameError):
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
