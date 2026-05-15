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
from tkinter import ttk
from tkinter import font as tkfont
import threading
from pathlib import Path
import sys
import datetime
from datetime import datetime as dt

from config import (
    PARADA_ACTUAL, LINEAS_A_PROBAR, SCROLL_SPEED, MAX_SCROLL_SPEED,
    REFRESH_MS, TITLE_FONT, HEADER_FONT, PARADA_BIKI_ACTUAL
)
from version_manager import check_and_update_on_startup, check_for_updates
from api_handler import (
    format_bus_time, fetch_bike_availability,
    get_parada_name, LineaNoPasaPorParadaError
)
from ui_components import (
    draw_centered_text, draw_line_badge, create_label_with_wrapping,
    create_header_canvas, show_splash_screen
)
from views import ViewManager, LockscreenView, MainView, add_click_bindings_to_view

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

tiempo_labels = {}
bikis_labels = {}
linea_widgets = {}
linea_visible = {}  # Rastrear visibilidad de líneas
canvas_scroll = None
inner_frame = None
root = None
parada_titulo_var = None
secondary_titulo_var = None
update_available = False
update_versions = {'local': None, 'github': None}

# Sistema de vistas
view_manager = None
main_frame = None
empty_frame = None
secondary_frame = None

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
            root.after(0, lambda: parada_titulo_var.set(titulo))
    except Exception as e:
        log_error(f"Error actualizando título de parada: {e}")
        if root:
            error_msg = str(e)
            root.after(0, lambda msg=error_msg: parada_titulo_var.set(f"Error: {msg}"))


def update_bike_station_title(parada):
    """Actualiza el nombre de la estación de bikis en el título"""
    try:
        bikis_data = fetch_bike_availability(parada)
        nombre = bikis_data.get('name', 'Estación desconocida')
        if root:
            root.after(0, lambda: secondary_titulo_var.set(nombre))
    except Exception as e:
        log_error(f"Error actualizando título de estación bikis: {e}")
        if root:
            error_msg = str(e)
            root.after(0, lambda msg=error_msg: secondary_titulo_var.set(f"Error: {msg}"))


def load_and_display_bus_times():
    """Obtiene tiempos de autobús en un hilo separado y actualiza la GUI"""
    updates = {}
    try:
        for linea in LINEAS_A_PROBAR:
            try:
                updates[linea] = format_bus_time(PARADA_ACTUAL, linea)
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
                global linea_visible
                for linea, tiempo in updates.items():
                    if linea not in tiempo_labels:
                        # La línea aún no existe en la GUI, crearla
                        row_index = len(linea_widgets)
                        create_bus_line_row(inner_frame, row_index, linea, tiempo)
                    
                    # Actualizar tiempo
                    try:
                        tiempo_labels[linea].set(tiempo)
                    except Exception as e:
                        log_error(f"No se pudo actualizar tiempo para {linea}: {e}")
                    
                    # Mostrar u ocultar según si hay tiempo
                    tiene_tiempo = tiempo.strip() != "" and tiempo.strip() != "?"
                    if linea in linea_widgets:
                        try:
                            if tiene_tiempo and not linea_visible.get(linea, False):
                                # Mostrar línea
                                linea_widgets[linea]['badge'].grid()
                                linea_widgets[linea]['tiempo'].grid()
                                linea_visible[linea] = True
                                log_info(f"Línea {linea} mostrada (tiempo: {tiempo})")
                            elif not tiene_tiempo and linea_visible.get(linea, False):
                                # Ocultar línea
                                linea_widgets[linea]['badge'].grid_remove()
                                linea_widgets[linea]['tiempo'].grid_remove()
                                linea_visible[linea] = False
                                log_info(f"Línea {linea} ocultada (no pasa por parada)")
                        except Exception as e:
                            log_error(f"No se pudo alternar visibilidad de {linea}: {e}")
                
                # Recalcular scroll
                if canvas_scroll and inner_frame:
                    inner_frame.update_idletasks()
                    canvas_scroll.config(scrollregion=canvas_scroll.bbox('all'))
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
        if root:
            try:
                if 'FIT' in bikis_labels:
                    bikis_labels['FIT'].set(f"{bikis_data['FIT']}")
                if 'EFIT' in bikis_labels:
                    bikis_labels['EFIT'].set(f"{bikis_data['EFIT']}")
            except Exception as e:
                log_error(f"No se pudo actualizar etiquetas de bikis: {e}")
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
# CREACIÓN DE INTERFAZ
# ============================================================================

def create_bus_line_row(parent, row_index, linea, tiempo_inicial):
    """Crea una fila con badge de línea y tiempo"""
    global linea_widgets
    
    badge_canvas = tk.Canvas(parent, height=42, highlightthickness=0, bd=0)
    badge_canvas.grid(column=1, row=row_index, sticky=(tk.W, tk.E, tk.N, tk.S))
    badge_canvas.bind("<Configure>", lambda event, canvas=badge_canvas, line=linea: draw_line_badge(canvas, line))
    root.after(0, lambda canvas=badge_canvas, line=linea: draw_line_badge(canvas, line))

    tiempo_var = tk.StringVar(value=tiempo_inicial)
    tiempo_labels[linea] = tiempo_var

    tiempo_canvas = tk.Canvas(parent, height=42, highlightthickness=0, bd=0)
    tiempo_canvas.grid(column=2, row=row_index, sticky=(tk.W, tk.E, tk.N, tk.S))

    linea_widgets[linea] = {'badge': badge_canvas, 'tiempo': tiempo_canvas}

    def draw_tiempo(event=None):
        draw_centered_text(tiempo_canvas, tiempo_var.get(), tkfont.Font(family="Segoe UI", size=10))

    draw_tiempo()
    tiempo_var.trace("w", lambda *args: draw_tiempo())
    tiempo_canvas.bind("<Configure>", draw_tiempo)


def create_bike_info_grid(parent):
    """Crea el grid de 2x2 en el panel secundario"""
    image_files = ["images/Bicicleta verde.png", "images/Bicicleta naranja.png"]
    
    photo_images_original = {}
    photo_images_scaled = {}
    
    for j in range(min(2, len(image_files))):
        img_canvas = tk.Canvas(parent, height=60, width=60, highlightthickness=1, relief=tk.SUNKEN)
        img_canvas.grid(column=j, row=1, sticky=(tk.N, tk.S, tk.E, tk.W), padx=5, pady=5)

        def draw_image(event=None, canvas=img_canvas, img_index=j, img_path=image_files[j]):
            FACTOR_ESCALADO = 0.7
            canvas.delete("all")
            try:
                if img_index not in photo_images_original:
                    photo = tk.PhotoImage(file=str(img_path))
                    photo_images_original[img_index] = photo
                else:
                    photo = photo_images_original[img_index]
                
                canvas_width = canvas.winfo_width() if canvas.winfo_width() > 1 else 60
                canvas_height = canvas.winfo_height() if canvas.winfo_height() > 1 else 60
                img_width = photo.width()
                img_height = photo.height()
                
                scale_x = (canvas_width / img_width) * FACTOR_ESCALADO if img_width > 0 else 1
                scale_y = (canvas_height / img_height) * FACTOR_ESCALADO if img_height > 0 else 1
                scale = min(scale_x, scale_y)
                
                if scale < 1:
                    factor = int(1 / scale) if scale > 0 else 1
                    photo_scaled = photo.subsample(factor, factor)
                elif scale > 1:
                    factor = int(scale)
                    photo_scaled = photo.zoom(factor, factor)
                else:
                    photo_scaled = photo
                
                photo_images_scaled[img_index] = photo_scaled
                canvas.create_image(canvas_width // 2, canvas_height // 2, image=photo_scaled)
            except Exception as e:
                log_error(f"Error cargando imagen PNG {img_index}: {e}")

        draw_image()
        img_canvas.bind("<Configure>", draw_image)

    bikis_types = ['FIT', 'EFIT']
    for j, bike_type in enumerate(bikis_types):
        cell_canvas = tk.Canvas(parent, height=50, highlightthickness=0, bd=0)
        cell_canvas.grid(column=j, row=2, sticky=(tk.N, tk.S, tk.E, tk.W), padx=5, pady=5)

        bikis_var = tk.StringVar(value=f"{bike_type}: 0")
        bikis_labels[bike_type] = bikis_var

        def draw_cell(event=None, canvas=cell_canvas, var=bikis_var):
            canvas.delete("all")
            cell_font = tkfont.Font(family="Segoe UI", size=10)
            draw_centered_text(canvas, var.get(), cell_font)

        draw_cell()
        bikis_var.trace("w", lambda *args, c=cell_canvas, v=bikis_var: draw_cell(canvas=c, var=v))
        cell_canvas.bind("<Configure>", lambda event, c=cell_canvas, v=bikis_var: draw_cell(canvas=c, var=v))


def setup_main_frame(root_widget):
    """Configura el frame principal con título y datos con scroll automático"""
    global parada_titulo_var, canvas_scroll, inner_frame

    mainframe = ttk.Frame(root_widget, padding=(3, 3, 12, 12))
    mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
    mainframe.rowconfigure(2, weight=1)
    mainframe.columnconfigure(1, weight=1)
    mainframe.columnconfigure(2, weight=1)

    parada_titulo_var = tk.StringVar(value=f"Parada {PARADA_ACTUAL}")
    create_label_with_wrapping(mainframe, 0, 1, 2, parada_titulo_var, TITLE_FONT)

    create_header_canvas(mainframe, 1, 1, "Línea")
    create_header_canvas(mainframe, 1, 2, "Tiempo")

    canvas_scroll = tk.Canvas(mainframe, highlightthickness=0)
    canvas_scroll.grid(column=1, row=2, columnspan=2, sticky=(tk.N, tk.S, tk.E, tk.W))

    inner_frame = tk.Frame(canvas_scroll)
    window_id = canvas_scroll.create_window(0, 0, window=inner_frame, anchor=tk.NW)

    row_index = 0
    for linea in LINEAS_A_PROBAR:
        try:
            tiempo = format_bus_time(PARADA_ACTUAL, linea)
            mostrar = True
        except LineaNoPasaPorParadaError:
            tiempo = ""
            mostrar = False
        except Exception as e:
            log_error(f"Error obteniendo tiempo para {linea}: {e}")
            tiempo = "?"
            mostrar = True
        
        create_bus_line_row(inner_frame, row_index, linea, tiempo)
        
        # Marcar visibilidad inicial
        linea_visible[linea] = mostrar
        if not mostrar:
            # Ocultar líneas que no pasan por la parada
            linea_widgets[linea]['badge'].grid_remove()
            linea_widgets[linea]['tiempo'].grid_remove()
        
        row_index += 1

    inner_frame.columnconfigure(1, weight=1)
    inner_frame.columnconfigure(2, weight=1)

    def on_canvas_configure(event):
        canvas_scroll.itemconfig(window_id, width=event.width)
    
    canvas_scroll.bind("<Configure>", on_canvas_configure)

    def start_scroll():
        inner_frame.update_idletasks()
        canvas_scroll.update()
        
        canvas_width = canvas_scroll.winfo_width()
        canvas_scroll.itemconfig(window_id, width=canvas_width)
        inner_frame.config(width=canvas_width)
        inner_frame.update_idletasks()
        
        canvas_scroll.config(scrollregion=canvas_scroll.bbox("all"))
        
        direction = [1]
        accumulated_scroll = [0.0]
        pause_counter = [0]
        PAUSE_FRAMES = 40

        def animate():
            inner_frame.update_idletasks()
            view = canvas_scroll.yview()
            visible_proportion = view[1] - view[0]
            
            if visible_proportion < 1.0:
                max_scroll_proportion = 1.0 - visible_proportion
                current_position = min(view[0], max_scroll_proportion)
                
                if pause_counter[0] > 0:
                    pause_counter[0] -= 1
                else:
                    increment = (SCROLL_SPEED) * max_scroll_proportion * direction[0]
                    accumulated_scroll[0] += increment
                    max_acc = MAX_SCROLL_SPEED * direction[0]
                    accumulated_scroll[0] = max(min(accumulated_scroll[0], abs(max_acc)), -abs(max_acc))
                    new_position = current_position + accumulated_scroll[0]
                    
                    if new_position >= max_scroll_proportion:
                        new_position = max_scroll_proportion
                        accumulated_scroll[0] = 0.0
                        direction[0] = -1
                        pause_counter[0] = PAUSE_FRAMES
                    elif new_position <= 0.0:
                        new_position = 0.0
                        accumulated_scroll[0] = 0.0
                        direction[0] = 1
                        pause_counter[0] = PAUSE_FRAMES
                    
                    canvas_scroll.yview_moveto(new_position)
            
            root.after(50, animate)

        animate()

    root.after(150, start_scroll)

    return mainframe


def setup_secondary_frame(root_widget):
    """Configura el panel secundario"""
    global secondary_titulo_var

    empty_frame = tk.Frame(root_widget)
    empty_frame.grid(column=0, row=1, sticky=(tk.N, tk.W, tk.E, tk.S))

    secondary_frame = ttk.Frame(empty_frame, padding=(3, 3, 12, 12))
    secondary_frame.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E))

    secondary_titulo_var = tk.StringVar(value="Información Adicional")
    create_label_with_wrapping(secondary_frame, 0, 0, 2, secondary_titulo_var, TITLE_FONT)

    create_bike_info_grid(secondary_frame)

    empty_frame.columnconfigure(0, weight=1)
    empty_frame.rowconfigure(0, weight=0)
    secondary_frame.columnconfigure(0, weight=1)
    secondary_frame.columnconfigure(1, weight=1)
    secondary_frame.rowconfigure(1, weight=0)
    secondary_frame.rowconfigure(2, weight=0)

    return empty_frame, secondary_frame


def setup_window_weights(root_widget):
    """Configura los pesos de expansión de la ventana"""
    root_widget.columnconfigure(0, weight=1)
    root_widget.rowconfigure(0, weight=1)
    root_widget.rowconfigure(1, weight=0)


# ============================================================================
# SISTEMA DE LOCKSCREEN
# ============================================================================

# ============================================================================
# SISTEMA DE VISTAS
# ============================================================================

def main():
    global root, main_frame, empty_frame, secondary_frame, view_manager

    check_and_update_on_startup()

    root = tk.Tk()
    root.title("Auvasa AppBus")
    #root.attributes('-fullscreen', True)
    
    splash = show_splash_screen(root)

    setup_window_weights(root)
    main_frame = setup_main_frame(root)
    empty_frame, secondary_frame = setup_secondary_frame(root)

    # ===== INICIALIZAR SISTEMA DE VISTAS =====
    view_manager = ViewManager.initialize(root)
    
    # Registrar vistas
    main_view = MainView(root, main_frame, empty_frame, secondary_frame)
    lockscreen_view = LockscreenView(root)
    
    view_manager.register_view(main_view)
    view_manager.register_view(lockscreen_view)
    
    # Agregar callback para actualizar el reloj
    view_manager.register_update_callback(lockscreen_view.update_clock)
    
    # Agregar bindings de click para ir a lockscreen
    add_click_bindings_to_view(main_frame, 'lockscreen')
    add_click_bindings_to_view(empty_frame, 'lockscreen')
    
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
