"""Vista principal de la aplicación."""
from .base import View
from debug_log import log_info


class MainView(View):
    """Vista principal compuesta por los frames existentes."""

    def __init__(self, root, main_frame, empty_frame, secondary_frame):
        self.main_frame = main_frame
        self.empty_frame = empty_frame
        self.secondary_frame = secondary_frame
        super().__init__(root, 'main')

    def _setup_frame(self):
        self.frame = self.main_frame
        log_info("Vista principal inicializada")

    def show(self):
        if self.main_frame:
            self.main_frame.grid()
        if self.empty_frame:
            self.empty_frame.grid()
        log_info("Vista 'main' mostrada")

    def hide(self):
        if self.main_frame:
            self.main_frame.grid_remove()
        if self.empty_frame:
            self.empty_frame.grid_remove()
        log_info("Vista 'main' ocultada")
