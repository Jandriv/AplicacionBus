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
DEFAULT_SCROLL_SPEED = 4
DEFAULT_MAX_SCROLL_SPEED = 2  # Cap máximo de velocidad acumulada (proporciones)
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
        return DEFAULT_PARADA_ACTUAL, list(DEFAULT_LINEAS_A_PROBAR), DEFAULT_SCROLL_SPEED, DEFAULT_MAX_SCROLL_SPEED

    parada_actual = str(config.get("parada_actual", DEFAULT_PARADA_ACTUAL))
    lineas_config = config.get("lineas_a_probar", DEFAULT_LINEAS_A_PROBAR)
    scroll_speed = float(config.get("scroll_speed", DEFAULT_SCROLL_SPEED))
    max_scroll_speed = float(config.get("max_scroll_speed", DEFAULT_MAX_SCROLL_SPEED))

    if not isinstance(lineas_config, list) or len(lineas_config) == 0:
        lineas_a_probar = list(DEFAULT_LINEAS_A_PROBAR)
    else:
        lineas_a_probar = [str(linea) for linea in lineas_config]

    return parada_actual, lineas_a_probar, scroll_speed/1000, max_scroll_speed/1000 

PARADA_ACTUAL, LINEAS_A_PROBAR, SCROLL_SPEED, MAX_SCROLL_SPEED = load_config()

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
    canvas = tk.Canvas(parent, height=30, highlightthickness=0, bd=0)
    canvas.grid(column=column, row=row, sticky=(tk.W, tk.E, tk.N, tk.S))

    def draw_header(event=None):
        header_font = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        draw_text_centered(canvas, text, header_font)

    draw_header()
    canvas.bind("<Configure>", draw_header)
    return canvas

def create_line_row(parent, row_index, linea, tiempo_inicial):
    """Crea una fila con badge de línea y tiempo"""
    # Badge (línea)
    badge_canvas = tk.Canvas(parent, height=42, highlightthickness=0, bd=0)
    badge_canvas.grid(column=1, row=row_index, sticky=(tk.W, tk.E, tk.N, tk.S))
    badge_canvas.bind("<Configure>", lambda event, canvas=badge_canvas, line=linea: draw_badge(canvas, line))
    root.after(0, lambda canvas=badge_canvas, line=linea: draw_badge(canvas, line))

    # Tiempo
    tiempo_var = tk.StringVar(value=tiempo_inicial)
    tiempo_labels[linea] = tiempo_var

    tiempo_canvas = tk.Canvas(parent, height=42, highlightthickness=0, bd=0)
    tiempo_canvas.grid(column=2, row=row_index, sticky=(tk.W, tk.E, tk.N, tk.S))

    def draw_tiempo(event=None):
        draw_text_centered(tiempo_canvas, tiempo_var.get(), tkfont.Font(family="Segoe UI", size=10))

    draw_tiempo()
    tiempo_var.trace("w", lambda *args: draw_tiempo())
    tiempo_canvas.bind("<Configure>", draw_tiempo)

def create_secondary_grid(parent):
    """Crea el grid de 2x2 en el panel secundario: fila 1 con imágenes, fila 2 con texto"""
    # Obtener imágenes PNG de la carpeta images
    images_folder = Path(__file__).parent / "images"
    image_files = ["images/Bicicleta verde.png", "images/Bicicleta naranja.png"]
    
    # Guardar referencias de imágenes originales y escaladas para evitar garbage collection
    photo_images_original = {}
    photo_images_scaled = {}
    
    # Primera fila: imágenes PNG
    for j in range(min(2, len(image_files))):
        img_canvas = tk.Canvas(
            parent, height=60, width=60,
            highlightthickness=1, relief=tk.SUNKEN
        )
        img_canvas.grid(column=j, row=1, sticky=(tk.N, tk.S, tk.E, tk.W), padx=5, pady=5)

        def draw_image(event=None, canvas=img_canvas, img_index=j, img_path=image_files[j]):
            FACTOR_ESCALADO = 0.7
            canvas.delete("all")
            try:
                # Cargar imagen PNG nativamente con tk.PhotoImage()
                if img_index not in photo_images_original:
                    photo = tk.PhotoImage(file=str(img_path))
                    photo_images_original[img_index] = photo
                else:
                    photo = photo_images_original[img_index]
                
                # Obtener dimensiones del canvas y la imagen
                canvas_width = canvas.winfo_width() if canvas.winfo_width() > 1 else 60
                canvas_height = canvas.winfo_height() if canvas.winfo_height() > 1 else 60
                img_width = photo.width()
                img_height = photo.height()
                
                # Calcular factor de escala para ajustarse al canvas manteniendo proporción
                scale_x = (canvas_width / img_width) * FACTOR_ESCALADO if img_width > 0 else 1
                scale_y = (canvas_height / img_height) * FACTOR_ESCALADO if img_height > 0 else 1
                scale = min(scale_x, scale_y)
                
                # Escalar la imagen
                if scale < 1:
                    # Reducir: usar subsample (inverso del zoom)
                    factor = int(1 / scale) if scale > 0 else 1
                    photo_scaled = photo.subsample(factor, factor)
                elif scale > 1:
                    # Aumentar: usar zoom
                    factor = int(scale)
                    photo_scaled = photo.zoom(factor, factor)
                else:
                    photo_scaled = photo
                
                photo_images_scaled[img_index] = photo_scaled  # Guardar referencia
                
                # Mostrar en canvas centrada
                canvas.create_image(
                    canvas_width // 2,
                    canvas_height // 2,
                    image=photo_scaled
                )
            except Exception as e:
                print(f"Error cargando imagen PNG {img_index}: {e}")
                # Fallback: mostrar nombre del archivo
                text_font = tkfont.Font(family="Segoe UI", size=9)
                img_name = img_path.stem[:15]
                canvas.create_text(
                    canvas.winfo_width() // 2,
                    canvas.winfo_height() // 2,
                    text=img_name,
                    font=text_font,
                    justify=tk.CENTER
                )

        draw_image()
        img_canvas.bind("<Configure>", draw_image)

    # Segunda fila: celdas de texto
    for j in range(2):
        cell_canvas = tk.Canvas(
            parent, height=50,
            highlightthickness=0, bd=0
        )
        cell_canvas.grid(column=j, row=2, sticky=(tk.N, tk.S, tk.E, tk.W), padx=5, pady=5)

        cell_num = j + 3  # Celda 3 y 4

        def draw_cell(event=None, canvas=cell_canvas, num=cell_num):
            canvas.delete("all")
            cell_font = tkfont.Font(family="Segoe UI", size=10)
            draw_text_centered(canvas, f"Celda {num}", cell_font)

        draw_cell()
        cell_canvas.bind("<Configure>", draw_cell)

def setup_main_frame(root):
    """Configura el frame principal con título y datos con scroll automático"""
    global parada_titulo_var

    mainframe = ttk.Frame(root, padding=(3, 3, 12, 12))
    mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
    mainframe.rowconfigure(2, weight=1)
    mainframe.columnconfigure(1, weight=1)
    mainframe.columnconfigure(2, weight=1)

    # Título
    parada_titulo_var = tk.StringVar(value=f"Parada {PARADA_ACTUAL}")
    create_label_with_wrapping(mainframe, 0, 1, 2, parada_titulo_var, TITLE_FONT)

    # Headers (fijos, no en scroll) - ambos usando canvas
    create_header_canvas(mainframe, 1, 1, "Línea")
    create_header_canvas(mainframe, 1, 2, "Tiempo")

    # Canvas para scroll automático (sin altura fija)
    canvas_scroll = tk.Canvas(mainframe, highlightthickness=0)
    canvas_scroll.grid(column=1, row=2, columnspan=2, sticky=(tk.N, tk.S, tk.E, tk.W))

    # Frame dentro del canvas
    inner_frame = tk.Frame(canvas_scroll)
    window_id = canvas_scroll.create_window(0, 0, window=inner_frame, anchor=tk.NW)

    # Filas de datos
    row_index = 0
    for linea in LINEAS_A_PROBAR:
        try:
            tiempo = get_tiempo_text(PARADA_ACTUAL, linea)
        except LineaNoPasaPorParadaError:
            continue

        create_line_row(inner_frame, row_index, linea, tiempo)
        row_index += 1

    # Configurar expansión del frame interior
    inner_frame.columnconfigure(1, weight=1)
    inner_frame.columnconfigure(2, weight=1)

    # Sincronizar ancho del canvas con el frame interior
    def on_canvas_configure(event):
        canvas_scroll.itemconfig(window_id, width=event.width)
    
    canvas_scroll.bind("<Configure>", on_canvas_configure)

    # Inicializar scroll automático
    def start_scroll():
        inner_frame.update_idletasks()
        canvas_scroll.update()
        
        canvas_width = canvas_scroll.winfo_width()
        canvas_height = canvas_scroll.winfo_height()
        frame_height = inner_frame.winfo_reqheight()
        
        # Sincronizar ancho: hacer que el Frame se expanda al ancho del canvas
        canvas_scroll.itemconfig(window_id, width=canvas_width)
        inner_frame.config(width=canvas_width)
        inner_frame.update_idletasks()
        
        # Configurar scrollregion
        canvas_scroll.config(scrollregion=canvas_scroll.bbox("all"))
        
        # Iniciar scroll automático continuo (usando proporciones 0.0-1.0)
        direction = [1]  # 1 para bajar, -1 para subir
        accumulated_scroll = [0.0]  # Acumulador para valores pequeños
        pause_counter = [0]  # Contador de frames de pausa
        PAUSE_FRAMES = 40  # 40 frames = 2 segundos (50ms por frame)

        def animate():
            # Obtener rango de scroll actual como proporciones
            view = canvas_scroll.yview()
            visible_proportion = view[1] - view[0]  # Fracción del contenido visible
            
            # Solo scrollear si hay contenido que no es visible
            if visible_proportion < 1.0:
                # Rango máximo de scroll en proporciones (0 a este valor)
                max_scroll_proportion = 1.0 - visible_proportion
                
                # Si estamos en pausa, solo contar frames
                if pause_counter[0] > 0:
                    pause_counter[0] -= 1
                else:
                    # Convertir SCROLL_SPEED a proporción del rango scrollable
                    # Dividir entre 1000 para suavizar, multiplicar por rango máximo
                    increment = (SCROLL_SPEED) * max_scroll_proportion * direction[0]
                    
                    # Acumular el incremento (importante para movimientos pequeños)
                    accumulated_scroll[0] += increment
                    
                    # Limitar el acumulador a la velocidad máxima permitida
                    max_acc = MAX_SCROLL_SPEED * direction[0]  # Positivo o negativo según dirección
                    accumulated_scroll[0] = max(min(accumulated_scroll[0], abs(max_acc)), -abs(max_acc))
                    
                    # Calcular nueva posición desde el acumulador
                    new_position = view[0] + accumulated_scroll[0]
                    
                    # Cambiar dirección y activar pausa al llegar a los límites
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