"""
ui_components.py - Componentes y utilidades de interfaz gráfica
"""
import tkinter as tk
from tkinter import font as tkfont
from pathlib import Path

from config import LINE_COLORS, DATA_FONT, HEADER_FONT


# ============================================================================
# FUNCIONES DE DIBUJO EN CANVAS
# ============================================================================

def draw_centered_text(canvas, text, font, color="black"):
    """Dibuja texto centrado en un canvas"""
    width = max(canvas.winfo_width(), 1)
    height = max(canvas.winfo_height(), 1)
    center_x = width / 2
    center_y = height / 2

    canvas.delete("all")
    canvas.create_text(center_x, center_y, text=text, fill=color, font=font)


def get_line_badge_color(numero_linea):
    """Obtiene el color de badge para una línea"""
    return LINE_COLORS.get(str(numero_linea), "#6D4C41")


def draw_line_badge(canvas, linea):
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
    badge_color = get_line_badge_color(linea)

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
# COMPONENTES DE INTERFAZ
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
        draw_centered_text(canvas, text, header_font)

    draw_header()
    canvas.bind("<Configure>", draw_header)
    return canvas


def show_splash_screen(root_window):
    """Muestra una pantalla de carga (splashscreen) que ocupa toda la pantalla"""
    try:
        # Cargar imagen PNG nativamente con tk.PhotoImage()
        splash_image_path = Path(__file__).parent / "images" / "splash.png"
        photo = tk.PhotoImage(file=str(splash_image_path))
        
        # Crear ventana splashscreen
        splash = tk.Toplevel(root_window)
        splash.overrideredirect(True)  # Sin bordes ni decoraciones
        
        # Obtener dimensiones de pantalla
        screen_width = splash.winfo_screenwidth()
        screen_height = splash.winfo_screenheight()
        
        # Establecer ventana a tamaño completo
        splash.geometry(f"{screen_width}x{screen_height}+0+0")
        splash.update_idletasks()
        
        # Calcular factor de escala para que la imagen ocupe toda la pantalla
        img_width = photo.width()
        img_height = photo.height()
        scale_x = screen_width / img_width
        scale_y = screen_height / img_height
        scale = max(scale_x, scale_y)  # Usar el mayor para cubrir toda la pantalla
        
        # Escalar la imagen si es necesario
        if scale > 1:
            scale_int = int(scale)
            photo = photo.zoom(scale_int, scale_int)
        elif scale < 1:
            scale_int = max(1, int(1 / scale))
            photo = photo.subsample(scale_int, scale_int)
        
        # Crear canvas para mostrar la imagen
        canvas = tk.Canvas(splash, highlightthickness=0, bd=0, bg="black")
        canvas.pack(fill=tk.BOTH, expand=True)
        canvas.create_image(screen_width // 2, screen_height // 2, image=photo, anchor=tk.CENTER)
        
        # Mostrar ventana inmediatamente
        splash.update()
        
        # Mantener referencia de la imagen para evitar garbage collection
        splash.photo_ref = photo
        
        return splash
    except Exception as e:
        print(f"Error al crear splashscreen: {e}")
        return None
