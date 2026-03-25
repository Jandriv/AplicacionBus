import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
import datetime, subprocess, json

PARADA_ACTUAL = "625"
LINEAS_A_PROBAR = [str(numero) for numero in range(1, 10)] + ["C1", "C2", "H"]
REFRESH_MS = 5000  # 5 segundos

tiempo_labels = {}

class LineaNoPasaPorParadaError(Exception):
    pass

def get_tiempo_text(parada, linea):
    return get_tiempo_con_linea(parada, linea) + '"'

def refresh_data():
    for linea in LINEAS_A_PROBAR:
        if linea in tiempo_labels:
            try:
                tiempo_labels[linea].set(get_tiempo_text(PARADA_ACTUAL, linea))
            except LineaNoPasaPorParadaError:
                pass

    root.after(REFRESH_MS, refresh_data)

def get_tiempo_con_linea(parada, linea):
    #result = subprocess.run(['curl', '-X', 'GET', 'http://localhost:3000/status'], stdout=subprocess.PIPE)
    comando = 'http://localhost:3000/parada/' + parada + '/' + linea + '/' + datetime.datetime.now().strftime('%Y%m%d') #Append current date as 'YYYYMMDD'
    result = subprocess.run(['curl', '-X', 'GET', comando], stdout=subprocess.PIPE)
    result_json = json.loads(result.stdout.decode('utf-8'))
    tiempoRestante = -1
    i = -1
    while tiempoRestante < 0:
        i += 1
        if len(result_json['lineas']) == 0:
            raise LineaNoPasaPorParadaError("La linea no pasa por esta parada")
        if (i >= len(result_json['lineas'][0]['horarios']) - 1):
            tiempoRestante = "No hay mas buses hoy"
            break
        tiempoRestante = result_json['lineas'][0]['horarios'][i]['tiempoRestante']
        #print(str(tiempoRestante) + " minutos X'")
    return str(tiempoRestante)

def get_bikis(parada, linea):
    #result = subprocess.run(['curl', '-X', 'GET', 'http://localhost:3000/status'], stdout=subprocess.PIPE)
    comando = 'http://localhost:3000/parada/' + parada + '/' + linea + '/' + datetime.datetime.now().strftime('%Y%m%d') #Append current date as 'YYYYMMDD'
    result = subprocess.run(['curl', '-X', 'GET', comando], stdout=subprocess.PIPE)
    result_json = json.loads(result.stdout.decode('utf-8'))
    tiempoRestante = -1
    i = -1
    while tiempoRestante < 0:
        i += 1
        if len(result_json['lineas']) == 0:
            raise LineaNoPasaPorParadaError("La linea no pasa por esta parada")
        if (i >= len(result_json['lineas'][0]['horarios']) - 1):
            tiempoRestante = "No hay mas buses hoy"
            break
        tiempoRestante = result_json['lineas'][0]['horarios'][i]['tiempoRestante']
        #print(str(tiempoRestante) + " minutos X'")
    return str(tiempoRestante)

def get_badge_color(numero_linea):
    colores_por_linea = {
        "1": "#E53935",
        "2": "#1E88E5",
        "3": "#43A047",
        "4": "#8E24AA", 
        "5": "#FB8C00",
        "6": "#00897B",
        "7": "#6D4C41",
        "8": "#546E7A",
        "9": "#F4511E",
        "C1": "#7B1FA2",
        "C2": "#D81B60",
        "H": "#455A64"
    }
    return colores_por_linea.get(str(numero_linea), "#6D4C41")

def draw_badge(canvas, linea):
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

    center_x = width / 2
    center_y = height / 2
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
            x1 + radius,
            y1,
            x2 - radius,
            y2,
            fill=badge_color,
            outline=badge_color
        )
        canvas.create_oval(
            x1,
            y1,
            x1 + (2 * radius),
            y2,
            fill=badge_color,
            outline=badge_color
        )
        canvas.create_oval(
            x2 - (2 * radius),
            y1,
            x2,
            y2,
            fill=badge_color,
            outline=badge_color
        )

    canvas.create_text(
        center_x,
        center_y,
        text=text_value,
        fill="white",
        font=text_font
    )

def create_line_row(parent, row_index, linea, tiempo_inicial):
    badge_canvas = tk.Canvas(parent, width=90, height=42, highlightthickness=0, bd=0)
    badge_canvas.grid(column=1, row=row_index, sticky=(tk.W, tk.E))
    badge_canvas.bind("<Configure>", lambda event, canvas=badge_canvas, line=linea: draw_badge(canvas, line))
    root.after(0, lambda canvas=badge_canvas, line=linea: draw_badge(canvas, line))

    tiempo_var = tk.StringVar(value=tiempo_inicial)
    tiempo_labels[linea] = tiempo_var
    ttk.Label(parent, textvariable=tiempo_var).grid(column=2, row=row_index, sticky=tk.W)

root = tk.Tk()
root.title("Auvasa AppBus")

mainframe = ttk.Frame(root, padding=(3, 3, 12, 12))
mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))

ttk.Label(mainframe, text="Línea", font=("Segoe UI", 10, "bold")).grid(column=1, row=0, sticky=tk.W)
ttk.Label(mainframe, text="Tiempo", font=("Segoe UI", 10, "bold")).grid(column=2, row=0, sticky=tk.W)

row_index = 1
for linea in LINEAS_A_PROBAR:
    try:
        tiempo = get_tiempo_text(PARADA_ACTUAL, linea)
    except LineaNoPasaPorParadaError:
        continue

    create_line_row(mainframe, row_index, linea, tiempo)
    row_index += 1

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
mainframe.columnconfigure(1, weight=1)
mainframe.columnconfigure(2, weight=1)
for child in mainframe.winfo_children(): 
    child.grid_configure(padx=5, pady=5)

root.after(REFRESH_MS, refresh_data)
root.mainloop()