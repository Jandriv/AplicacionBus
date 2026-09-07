"""Clase base para las vistas de AppBus."""
from abc import ABC, abstractmethod

from debug_log import log_info


class View(ABC):
    """Interfaz común para todas las vistas."""

    def __init__(self, root, name):
        self.root = root
        self.name = name
        self.frame = None
        self._setup_frame()

    @abstractmethod
    def _setup_frame(self):
        pass

    def show(self):
        if self.frame:
            self.frame.grid()
            log_info(f"Vista '{self.name}' mostrada")

    def hide(self):
        if self.frame:
            self.frame.grid_remove()
            log_info(f"Vista '{self.name}' ocultada")

    def is_visible(self):
        return self.frame and self.frame.winfo_viewable() if self.frame else False
