import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
import datetime
import subprocess
import json
from pathlib import Path

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

CONFIG_FILE_NAME = "app_config.json"
DEFAULT_PARADA_ACTUAL = "625"
DEFAULT_LINEAS_A_PROBAR = [str(numero) for numero in range(1, 10)] + ["C1", "C2", "H"]
REFRESH_MS = 5000  # 5 segundos
API_TIMEOUT = 5
PYTHON_TIMEOUT = 6
STRING_NO_HAY_MAS_BUSES = "No hay mas buses hoy"

# Colores de las líneas
LINE_COLORS = {
    "1": "#E53935", "2": "#1E88E5", "3": "#43A047", "4": "#8E24AA",
    "5": "#FB8C00", "6": "#00897B", "7": "#6D4C41", "8": "#546E7A",
    "9": "#F4511E", "C1": "#7B1FA2", "C2": "#D81B60", "H": "#455A64"
}

# Fuentes
TITLE_FONT = ("Segoe UI", 12, "bold")
HEADER_FONT = ("Segoe UI", 10, "bold")
DATA_FONT = ("Segoe UI", 10)

# ============================================================================
# EXCEPCIONES
# ============================================================================

class LineaNoPasaPorParadaError(Exception):
    """Excepción cuando una línea no pasa por una parada"""
    pass

# ============================================================================
# GESTIÓN DE CONFIGURACIÓN
# ============================================================================

def load_config():
    """Carga la configuración desde archivo JSON o valores por defecto"""
    config_path = Path(__file__).with_name(CONFIG_FILE_NAME)

    try:
        with open(config_path, "r", encoding="utf-8") as config_file:
            config = json.load(config_file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return DEFAULT_PARADA_ACTUAL, list(DEFAULT_LINEAS_A_PROBAR)

    parada_actual = str(config.get("parada_actual", DEFAULT_PARADA_ACTUAL))
    lineas_config = config.get("lineas_a_probar", DEFAULT_LINEAS_A_PROBAR)

    if not isinstance(lineas_config, list) or len(lineas_config) == 0:
        lineas_a_probar = list(DEFAULT_LINEAS_A_PROBAR)
    else:
        lineas_a_probar = [str(linea) for linea in lineas_config]

    return parada_actual, lineas_a_probar

PARADA_ACTUAL, LINEAS_A_PROBAR = load_config()

# ============================================================================
# API Y DATOS
# ============================================================================

def fetch_api(url):
    """Realiza petición HTTP con timeout"""
    try:
        result = subprocess.run(
            ['curl', '-X', 'GET', '--max-time', str(API_TIMEOUT), url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=PYTHON_TIMEOUT
        )
        if result.returncode != 0:
            raise Exception("Error en petición curl")
        return json.loads(result.stdout.decode('utf-8'))
    except (json.JSONDecodeError, subprocess.TimeoutExpired, Exception) as e:
        raise Exception(f"Error al obtener datos: {str(e)}")

def get_tiempo_con_linea(parada, linea):
    """Obtiene tiempo restante del próximo autobús"""
    url = f'http://localhost:3000/parada/{parada}/{linea}/{datetime.datetime.now().strftime("%Y%m%d")}'
    result_json = fetch_api(url)

    if not result_json.get('lineas') or len(result_json['lineas']) == 0:
        raise LineaNoPasaPorParadaError("La linea no pasa por esta parada")

    horarios = result_json['lineas'][0].get('horarios', [])
    for horario in horarios:
        tiempo = horario.get('tiempoRestante', -1)
        if tiempo >= 0:
            return str(tiempo)

    return STRING_NO_HAY_MAS_BUSES

def get_tiempo_text(parada, linea):
    """Obtiene tiempo formateado (h' min\" para >59 mins)"""
    tiempo = get_tiempo_con_linea(parada, linea)
    if tiempo == STRING_NO_HAY_MAS_BUSES:
        return tiempo

    minutos = int(tiempo)
    if minutos > 59:
        horas = minutos // 60
        mins = minutos % 60
        return f"{horas}' {mins}\""
    return f"{minutos}\""

# ============================================================================
# DIBUJO EN CANVAS
# ============================================================================

def draw_text_centered(canvas, text, font, color="black"):
    """Dibuja texto centrado en un canvas"""
    width = max(canvas.winfo_width(), 1)
    height = max(canvas.winfo_height(), 1)
    center_x = width / 2
    center_y = height / 2

    canvas.delete("all")
    canvas.create_text(center_x, center_y, text=text, fill=color, font=font)

def get_badge_color(numero_linea):
    """Obtiene el color de badge para una línea"""
    return LINE_COLORS.get(str(numero_linea), "#6D4C41")

def draw_badge(canvas, linea):
    """Dibuja un badge de línea en el canvas"""
    width = max(canvas.winfo_width(), 1)
    height = max(canvas.winfo_height(), 1)
    center_x = width / 2
    center_y = height / 2

    capsule_height = max(18, min(height * 0.78, height * 0.92))
    radius = capsule_height / 2
    max_capsule_width = width * 0.95
    min_capsule_width = capsule_height

    text_value = str(linea)
    font_size = max(10, int(capsule_height * 0.52))
    text_font = tkfont.Font(family="Segoe UI", size=font_size, weight="bold")
    text_width = text_font.measure(text_value)
    horizontal_padding = max(10, int(radius * 0.75))

    while font_size > 8 and (text_width + (horizontal_padding * 2) > max_capsule_width):
        font_size -= 1
        text_font = tkfont.Font(family="Segoe UI", size=font_size, weight="bold")
        text_width = text_font.measure(text_value)

    capsule_width = max(min_capsule_width, text_width + (horizontal_padding * 2))
    capsule_width = min(capsule_width, max_capsule_width)

    x1 = center_x - (capsule_width / 2)
    y1 = center_y - radius
    x2 = center_x + (capsule_width / 2)
    y2 = center_y + radius

    canvas.delete("all")
    badge_color = get_badge_color(linea)

    if capsule_width <= (radius * 2) + 1:
        canvas.create_oval(x1, y1, x2, y2, fill=badge_color, outline=badge_color)
    else:
        canvas.create_rectangle(
            x1 + radius, y1, x2 - radius, y2,
            fill=badge_color, outline=badge_color
        )
        canvas.create_oval(
            x1, y1, x1 + (2 * radius), y2,
            fill=badge_color, outline=badge_color
        )
        canvas.create_oval(
            x2 - (2 * radius), y1, x2, y2,
            fill=badge_color, outline=badge_color
        )

    canvas.create_text(
        center_x, center_y,
        text=text_value, fill="white", font=text_font
    )

# ============================================================================
# ESTADO GLOBAL
# ============================================================================

tiempo_labels = {}
root = None
parada_titulo_var = None
secondary_titulo_var = None

# ============================================================================
# ACTUALIZACIÓN DE DATOS
# ============================================================================

def mostrar_parada(parada):
    """Actualiza el nombre de la parada en el título"""
    try:
        result_json = fetch_api(f'http://localhost:3000/parada/{parada}')
        nombre = result_json.get('parada', [{}])[0].get('parada', 'Parada desconocida')
        parada_titulo_var.set(nombre)
    except Exception as e:
        parada_titulo_var.set(f"Error: {str(e)}")

def refresh_data():
    """Actualiza los tiempos de todas las líneas"""
    for linea in LINEAS_A_PROBAR:
        if linea in tiempo_labels:
            try:
                tiempo_labels[linea].set(get_tiempo_text(PARADA_ACTUAL, linea))
            except LineaNoPasaPorParadaError:
                pass

    root.after(REFRESH_MS, refresh_data)

# ============================================================================
# CREACIÓN DE INTERFAZ
# ============================================================================

def create_label_with_wrapping(parent, row, column, columnspan, text_var, font, sticky=(tk.W, tk.E)):
    """Crea un label con wrapping dinámico"""
    label = tk.Label(
        parent,
        textvariable=text_var,
        font=font,
        justify=tk.CENTER,
        relief=tk.FLAT,
        padx=10,
        pady=10
    )
    label.grid(column=column, row=row, columnspan=columnspan, sticky=sticky)

    def on_label_configure(event):
        label.config(wraplength=max(event.width - 20, 100))

    label.bind('<Configure>', on_label_configure)
    return label

def create_header_canvas(parent, row, column, text):
    """Crea un canvas para un header centrado"""
    canvas = tk.Canvas(parent, width=80, height=30, highlightthickness=0, bd=0)
    canvas.grid(column=column, row=row, sticky=(tk.W, tk.E))

    def draw_header(event=None):
        header_font = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        draw_text_centered(canvas, text, header_font)

    draw_header()
    canvas.bind("<Configure>", draw_header)
    return canvas

def create_line_row(parent, row_index, linea, tiempo_inicial):
    """Crea una fila con badge de línea y tiempo"""
    # Badge (línea)
    badge_canvas = tk.Canvas(parent, width=90, height=42, highlightthickness=0, bd=0)
    badge_canvas.grid(column=1, row=row_index, sticky=(tk.W, tk.E))
    badge_canvas.bind("<Configure>", lambda event, canvas=badge_canvas, line=linea: draw_badge(canvas, line))
    root.after(0, lambda canvas=badge_canvas, line=linea: draw_badge(canvas, line))

    # Tiempo
    tiempo_var = tk.StringVar(value=tiempo_inicial)
    tiempo_labels[linea] = tiempo_var

    tiempo_canvas = tk.Canvas(parent, width=80, height=42, highlightthickness=0, bd=0)
    tiempo_canvas.grid(column=2, row=row_index, sticky=(tk.W, tk.E))

    def draw_tiempo(event=None):
        draw_text_centered(tiempo_canvas, tiempo_var.get(), tkfont.Font(family="Segoe UI", size=10))

    draw_tiempo()
    tiempo_var.trace("w", lambda *args: draw_tiempo())
    tiempo_canvas.bind("<Configure>", draw_tiempo)

def create_secondary_grid(parent):
    """Crea el grid de 2x2 en el panel secundario"""
    for i in range(2):
        for j in range(2):
            cell_canvas = tk.Canvas(
                parent, width=150, height=50,
                highlightthickness=0, bd=0
            )
            cell_canvas.grid(column=j, row=i+1, sticky=(tk.N, tk.S, tk.E, tk.W), padx=5, pady=5)

            cell_num = i * 2 + j + 1

            def draw_cell(event=None, canvas=cell_canvas, num=cell_num):
                cell_font = tkfont.Font(family="Segoe UI", size=10)
                draw_text_centered(canvas, f"Celda {num}", cell_font)

            draw_cell()
            cell_canvas.bind("<Configure>", draw_cell)

def setup_main_frame(root):
    """Configura el frame principal con título y datos"""
    global parada_titulo_var

    mainframe = ttk.Frame(root, padding=(3, 3, 12, 12))
    mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E))

    # Título
    parada_titulo_var = tk.StringVar(value=f"Parada {PARADA_ACTUAL}")
    create_label_with_wrapping(mainframe, 0, 1, 2, parada_titulo_var, TITLE_FONT)

    # Headers
    ttk.Label(mainframe, text="Línea", font=HEADER_FONT).grid(column=1, row=1)
    create_header_canvas(mainframe, 1, 2, "Tiempo")

    # Filas de datos
    row_index = 2
    for linea in LINEAS_A_PROBAR:
        try:
            tiempo = get_tiempo_text(PARADA_ACTUAL, linea)
        except LineaNoPasaPorParadaError:
            continue

        create_line_row(mainframe, row_index, linea, tiempo)
        row_index += 1

    # Configurar expansión
    mainframe.columnconfigure(1, weight=1)
    mainframe.columnconfigure(2, weight=1)

    for child in mainframe.winfo_children():
        child.grid_configure(padx=5, pady=5)

    return mainframe

def setup_secondary_frame(root):
    """Configura el panel secundario"""
    global secondary_titulo_var

    empty_frame = tk.Frame(root)
    empty_frame.grid(column=0, row=1, sticky=(tk.N, tk.W, tk.E, tk.S))

    secondary_frame = ttk.Frame(empty_frame, padding=(3, 3, 12, 12))
    secondary_frame.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E))

    # Título
    secondary_titulo_var = tk.StringVar(value="Información Adicional")
    create_label_with_wrapping(secondary_frame, 0, 0, 2, secondary_titulo_var, TITLE_FONT)

    # Grid 2x2
    create_secondary_grid(secondary_frame)

    # Configurar expansión
    empty_frame.columnconfigure(0, weight=1)
    empty_frame.rowconfigure(0, weight=0)
    secondary_frame.columnconfigure(0, weight=1)
    secondary_frame.columnconfigure(1, weight=1)
    secondary_frame.rowconfigure(1, weight=0)
    secondary_frame.rowconfigure(2, weight=0)

    return empty_frame, secondary_frame

def setup_window_weights(root):
    """Configura los pesos de expansión de la ventana"""
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)  # mainframe expande verticalmente
    root.rowconfigure(1, weight=0)  # secondary_frame tiene tamaño fijo

# ============================================================================
# INICIO DE LA APLICACIÓN
# ============================================================================

def main():
    global root

    root = tk.Tk()
    root.title("Auvasa AppBus")

    setup_window_weights(root)
    setup_main_frame(root)
    setup_secondary_frame(root)

    mostrar_parada(PARADA_ACTUAL)

    root.after(REFRESH_MS, refresh_data)
    root.mainloop()

if __name__ == "__main__":
    main()