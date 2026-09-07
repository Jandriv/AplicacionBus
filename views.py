"""Compatibilidad con el antiguo módulo monolítico de vistas.

La implementación vive ahora en la carpeta ``vistas``.
"""
from vistas import (
    View,
    ViewManager,
    MainView,
    LockscreenView,
    SettingsView,
    add_click_bindings_to_view,
)

__all__ = [
    "View",
    "ViewManager",
    "MainView",
    "LockscreenView",
    "SettingsView",
    "add_click_bindings_to_view",
]
