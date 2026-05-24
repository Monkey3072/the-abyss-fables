from PyQt5.QtCore import QObject, pyqtSignal


class EventBus(QObject):
    theme_changed = pyqtSignal()
    resolution_changed = pyqtSignal(int, int)
    font_changed = pyqtSignal(str, int)
    game_ui_shown = pyqtSignal()
    start_menu_shown = pyqtSignal()
    game_over = pyqtSignal(str)
    request_new_game_with_seed = pyqtSignal(dict)
    return_to_menu_requested = pyqtSignal()
    apply_settings_requested = pyqtSignal()


_event_bus_instance = None


def get_event_bus():
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
    return _event_bus_instance


event_bus = get_event_bus()
