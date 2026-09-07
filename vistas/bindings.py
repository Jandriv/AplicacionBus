"""Bindings compartidos entre vistas."""
from .manager import ViewManager
from debug_log import log_error


def add_click_bindings_to_view(widget, target_view='lockscreen'):
    """Cambia de vista al tocar un widget o cualquiera de sus hijos."""
    try:
        def on_click(event):
            ViewManager.get_instance().switch_view(target_view)
            return "break"

        widget.bind("<Button-1>", on_click)
        for child in widget.winfo_children():
            add_click_bindings_to_view(child, target_view)
    except Exception as error:
        log_error(f"Error agregando bindings: {error}")
