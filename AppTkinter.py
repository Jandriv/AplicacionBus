"""
AppTkinter.py - Aplicación principal de Auvasa AppBus

Estructura modular:
- config.py: Constantes y configuración
- version_manager.py: Sistema de actualizaciones
- api_handler.py: Integración con APIs
- ui_components.py: Componentes de interfaz
- AppTkinter.py: Lógica de aplicación (este archivo)
"""
import tkinter as tk
import threading
import sys

from config import (
    PARADA_ACTUAL, LINEAS_A_PROBAR, REFRESH_MS, PARADA_BIKI_ACTUAL
)
from version_manager import check_and_update_on_startup, check_for_updates
from api_handler import (
    format_bus_time, fetch_bike_availability,
    get_parada_name, LineaNoPasaPorParadaError
)
from ui_components import show_splash_screen
from views import ViewManager, LockscreenView, SettingsView, add_click_bindings_to_view
from vistas.main import MainView
from theme import apply_theme, set_theme

# Intentar importar debug_log, si falla usar print
try:
    from debug_log import log_error, log_info
except ImportError:
    def log_error(msg):
        print(f"[ERROR] {msg}", file=sys.stderr)
    def log_info(msg):
        print(f"[INFO] {msg}")

# ============================================================================
# ESTADO GLOBAL
# ============================================================================

main_view = None
root = None
update_available = False
update_versions = {'local': None, 'github': None}

# Sistema de vistas
view_manager = None
main_frame = None
empty_frame = None
secondary_frame = None
settings_button = None
config_generation = 0

# ============================================================================
# ACTUALIZACIÓN DE DATOS
# ============================================================================

def update_bus_stop_title(parada):
    """Actualiza el nombre de la parada en el título"""
    try:
        nombre = get_parada_name(parada)
        if root:
            if update_available:
                titulo = f"⚠️ Actualización disponible ({update_versions['github']}) |\n {nombre}"
            else:
                titulo = nombre
            root.after(0, lambda: main_view.set_stop_title(titulo))
    except Exception as e:
        log_error(f"Error actualizando título de parada: {e}")
        if root:
            error_msg = str(e)
            root.after(0, lambda msg=error_msg: main_view.set_stop_title(f"Error: {msg}"))


def update_bike_station_title(parada):
    """Actualiza el nombre de la estación de bikis en el título"""
    try:
        bikis_data = fetch_bike_availability(parada)
        nombre = bikis_data.get('name', 'Estación desconocida')
        if root:
            root.after(0, lambda: main_view.set_bike_title(nombre))
    except Exception as e:
        log_error(f"Error actualizando título de estación bikis: {e}")
        if root:
            error_msg = str(e)
            root.after(0, lambda msg=error_msg: main_view.set_bike_title(f"Error: {msg}"))


def load_and_display_bus_times():
    """Obtiene tiempos de autobús en un hilo separado y actualiza la GUI"""
    generation = config_generation
    parada = PARADA_ACTUAL
    lineas = list(LINEAS_A_PROBAR)
    updates = {}
    try:
        for linea in lineas:
            try:
                updates[linea] = format_bus_time(parada, linea)
            except LineaNoPasaPorParadaError:
                updates[linea] = ""
            except Exception as e:
                log_error(f"Excepción actualizando línea {linea}: {e}")
                updates[linea] = "?"
    except Exception as e:
        log_error(f"Excepción en load_and_display_bus_times: {e}")
        return
    
    if root and updates:
        def update_gui():
            try:
                if generation != config_generation:
                    return
                main_view.update_bus_times(updates)
            except Exception as e:
                log_error(f"Excepción en update_gui: {e}")
        
        try:
            root.after(0, update_gui)
        except Exception as e:
            log_error(f"No se pudo programar update_gui: {e}")


def schedule_bus_times_refresh():
    """Actualiza los tiempos de todas las líneas en un hilo separado"""
    try:
        thread = threading.Thread(target=load_and_display_bus_times, daemon=True)
        thread.start()
    except Exception as e:
        log_error(f"No se pudo iniciar hilo de actualización: {e}")
    finally:
        try:
            root.after(REFRESH_MS, schedule_bus_times_refresh)
        except Exception as e:
            log_error(f"No se pudo programar próximo refresh: {e}")


def apply_runtime_config(config):
    """Aplica la configuración guardada sin reiniciar la aplicación."""
    global PARADA_ACTUAL, LINEAS_A_PROBAR, PARADA_BIKI_ACTUAL
    global config_generation

    config_generation += 1
    generation = config_generation

    PARADA_ACTUAL = str(config.get('parada_actual', PARADA_ACTUAL))
    LINEAS_A_PROBAR = [str(linea) for linea in config.get('lineas_a_probar', LINEAS_A_PROBAR)]
    PARADA_BIKI_ACTUAL = str(config.get('parada_biki_actual', PARADA_BIKI_ACTUAL))

    if main_view:
        def load_new_rows():
            updates = {}
            for linea in LINEAS_A_PROBAR:
                try:
                    updates[linea] = (format_bus_time(PARADA_ACTUAL, linea), True)
                except LineaNoPasaPorParadaError:
                    updates[linea] = ('', False)
                except Exception as error:
                    log_error(f"Error actualizando línea {linea}: {error}")
                    updates[linea] = ('?', True)
            root.after(0, lambda: main_view.replace_bus_rows(LINEAS_A_PROBAR, updates) if generation == config_generation else None)

        threading.Thread(target=load_new_rows, daemon=True).start()

    if main_view:
        main_view.set_stop_title(f'Parada {PARADA_ACTUAL}')
    threading.Thread(target=update_bus_stop_title, args=(PARADA_ACTUAL,), daemon=True).start()
    threading.Thread(target=update_bike_station_title, args=(PARADA_BIKI_ACTUAL,), daemon=True).start()
    log_info('Configuración aplicada sin reiniciar la aplicación')


def apply_runtime_theme(config):
    """Aplica el tema visual y refresca los canvas existentes."""
    theme_name = config.get('theme')
    if theme_name is None:
        theme_name = 'dark' if config.get('dark_mode', False) else 'light'
    set_theme(theme_name)
    apply_theme(root)
    if root:
        root.update_idletasks()
        for widget in root.winfo_children():
            _refresh_canvas_widgets(widget)
        if main_view:
            main_view.realign()
            main_view.refresh_line_canvases()


def _refresh_canvas_widgets(widget):
    if isinstance(widget, tk.Canvas):
        try:
            widget.event_generate('<Configure>')
        except tk.TclError:
            pass
    for child in widget.winfo_children():
        _refresh_canvas_widgets(child)


def apply_runtime_settings(config):
    """Aplica todos los ajustes guardados sin reiniciar."""
    apply_runtime_theme(config)
    apply_runtime_config(config)


def schedule_bus_stop_title_refresh():
    """Actualiza el título de la parada en un hilo separado"""
    try:
        thread = threading.Thread(target=update_bus_stop_title, args=(PARADA_ACTUAL,), daemon=True)
        thread.start()
    except Exception as e:
        log_error(f"No se pudo iniciar hilo de título: {e}")
    finally:
        try:
            root.after(REFRESH_MS, schedule_bus_stop_title_refresh)
        except Exception as e:
            log_error(f"No se pudo programar próximo refresh de título: {e}")


def load_and_display_bike_data():
    """Obtiene datos de bikis en un hilo separado y actualiza la GUI"""
    try:
        bikis_data = fetch_bike_availability(PARADA_BIKI_ACTUAL)
        if root and main_view:
            main_view.set_bike_data(bikis_data)
    except Exception as e:
        log_error(f"Excepción en load_and_display_bike_data: {e}")


def schedule_bikes_refresh():
    """Actualiza los datos de cantidad de bikis disponibles en un hilo separado"""
    try:
        thread = threading.Thread(target=load_and_display_bike_data, daemon=True)
        thread.start()
    except Exception as e:
        log_error(f"No se pudo iniciar hilo de bikis: {e}")
    finally:
        try:
            root.after(REFRESH_MS, schedule_bikes_refresh)
        except Exception as e:
            log_error(f"No se pudo programar próximo refresh de bikis: {e}")


def schedule_bikis_title_refresh():
    """Actualiza el título de la estación de bikis en un hilo separado"""
    try:
        thread = threading.Thread(target=update_bike_station_title, args=(PARADA_BIKI_ACTUAL,), daemon=True)
        thread.start()
    except Exception as e:
        log_error(f"No se pudo iniciar hilo de título bikis: {e}")
    finally:
        try:
            root.after(REFRESH_MS, schedule_bikis_title_refresh)
        except Exception as e:
            log_error(f"No se pudo programar próximo refresh de título bikis: {e}")


def notify_update_available(local_version, github_version):
    """Marca que hay una actualización disponible"""
    global update_available, update_versions
    update_available = True
    update_versions['local'] = local_version
    update_versions['github'] = github_version
    # La actualización del título ocurrirá en el siguiente refresh de update_bus_stop_title


def _check_and_notify_updates():
    """Verifica actualizaciones en un hilo separado"""
    has_updates, local_ver, github_ver = check_for_updates()
    if has_updates and root:
        root.after(0, lambda: notify_update_available(local_ver, github_ver))


def check_updates_periodic():
    """Comprueba periódicamente si hay actualizaciones disponibles (cada 24 horas)"""
    try:
        thread = threading.Thread(target=_check_and_notify_updates, daemon=True)
        thread.start()
    except Exception as e:
        log_error(f"No se pudo iniciar hilo de actualización: {e}")
    finally:
        try:
            root.after(86400000, check_updates_periodic)
        except Exception as e:
            log_error(f"No se pudo programar próximo check: {e}")


# ============================================================================
# SISTEMA DE LOCKSCREEN
# ============================================================================

# ============================================================================
# SISTEMA DE VISTAS
# ============================================================================

def main():
    global root, main_view, main_frame, empty_frame, secondary_frame, view_manager, settings_button

    check_and_update_on_startup()

    root = tk.Tk()
    root.title("Auvasa AppBus")
    root.attributes('-fullscreen', True)
    
    splash = show_splash_screen(root)

    MainView.configure_window(root)
    main_view = MainView(root, LINEAS_A_PROBAR, lambda _parada, linea: format_bus_time(PARADA_ACTUAL, linea))
    main_frame = main_view.main_frame
    empty_frame = main_view.empty_frame
    secondary_frame = main_view.secondary_frame
    settings_button = main_view.settings_button

    # ===== INICIALIZAR SISTEMA DE VISTAS =====
    view_manager = ViewManager.initialize(root)
    
    # Registrar vistas
    lockscreen_view = LockscreenView(root)
    settings_view = SettingsView(root, on_saved=apply_runtime_settings)
    apply_runtime_theme(settings_view._read_config())
    
    view_manager.register_view(main_view)
    view_manager.register_view(lockscreen_view)
    view_manager.register_view(settings_view)
    
    # Agregar callback para actualizar el reloj
    view_manager.register_update_callback(lockscreen_view.update_clock)
    
    # Agregar bindings de click para ir a lockscreen
    add_click_bindings_to_view(main_frame, 'lockscreen')
    add_click_bindings_to_view(empty_frame, 'lockscreen')
    # El botón de configuración debe conservar su acción propia.
    settings_button.unbind('<Button-1>')
    settings_button.bind(
        '<Button-1>',
        lambda event: (view_manager.switch_view('settings'), 'break')[1]
    )
    
    # Establecer vista inicial
    view_manager.set_initial_view('main')

    thread_parada = threading.Thread(target=update_bus_stop_title, args=(PARADA_ACTUAL,), daemon=True)
    thread_bikis_titulo = threading.Thread(target=update_bike_station_title, args=(PARADA_BIKI_ACTUAL,), daemon=True)
    thread_bus_times = threading.Thread(target=load_and_display_bus_times, daemon=True)
    thread_bikis_data = threading.Thread(target=load_and_display_bike_data, daemon=True)
    
    thread_parada.start()
    thread_bikis_titulo.start()
    thread_bus_times.start()
    thread_bikis_data.start()

    if splash:
        root.after(2000, splash.destroy)

    root.after(REFRESH_MS, schedule_bus_times_refresh)
    root.after(REFRESH_MS, schedule_bus_stop_title_refresh)
    root.after(REFRESH_MS, schedule_bikes_refresh)
    root.after(REFRESH_MS, schedule_bikis_title_refresh)
    
    thread_check_updates = threading.Thread(target=_check_and_notify_updates, daemon=True)
    thread_check_updates.start()
    
    root.after(REFRESH_MS, check_updates_periodic)
    root.mainloop()


if __name__ == "__main__":
    main()
