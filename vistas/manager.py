"""Gestor central de vistas."""
from debug_log import log_error, log_info


class ViewManager:
    """Singleton que coordina las vistas y sus callbacks periódicos."""

    _instance = None

    def __init__(self, root):
        self.root = root
        self.views = {}
        self.current_view = None
        self.update_callbacks = []
        self._start_update_loop()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            raise RuntimeError("ViewManager no ha sido inicializado")
        return cls._instance

    @classmethod
    def initialize(cls, root):
        if cls._instance is None:
            cls._instance = cls(root)
        return cls._instance

    def register_view(self, view):
        self.views[view.name] = view
        log_info(f"Vista '{view.name}' registrada")

    def register_update_callback(self, callback):
        self.update_callbacks.append(callback)

    def switch_view(self, view_name):
        if view_name not in self.views:
            log_error(f"Vista '{view_name}' no registrada")
            return
        if self.current_view:
            self.current_view.hide()
        self.views[view_name].show()
        self.current_view = self.views[view_name]
        log_info(f"Cambio de vista: {view_name}")

    def _start_update_loop(self):
        def update():
            for callback in self.update_callbacks:
                try:
                    callback()
                except Exception as error:
                    log_error(f"Error en callback de actualización: {error}")
            if self.root:
                self.root.after(1000, update)
        if self.root:
            self.root.after(1000, update)

    def set_initial_view(self, view_name):
        if view_name in self.views:
            self.switch_view(view_name)
            log_info(f"Vista inicial: {view_name}")
        else:
            log_error(f"Vista inicial '{view_name}' no existe")
