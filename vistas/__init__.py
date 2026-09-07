"""API pública del sistema de vistas."""
from .base import View
from .bindings import add_click_bindings_to_view
from .lockscreen import LockscreenView
from .main import MainView
from .manager import ViewManager
from .settings import SettingsView

__all__ = [
    "View", "ViewManager", "MainView", "LockscreenView",
    "SettingsView", "add_click_bindings_to_view",
]
