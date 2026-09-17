"""Construcción y gestión de la interfaz principal de AppBus."""
import tkinter as tk
from tkinter import font as tkfont, ttk

from api_handler import LineaNoPasaPorParadaError
from config import MAX_SCROLL_SPEED, SCROLL_SPEED, TITLE_FONT
from debug_log import log_error, log_info
from theme import get_theme
from ui_components import create_header_canvas, create_label_with_wrapping, draw_centered_text, draw_line_badge
from .base import View
from .manager import ViewManager


class MainView(View):
    """Vista principal y propietaria de todos sus widgets."""

    def __init__(self, root, lines, time_provider):
        self.lines = list(lines)
        self.time_provider = time_provider
        self.time_vars, self.line_widgets, self.line_visible = {}, {}, {}
        self.bike_vars = {}
        self.stop_title_var = self.bike_title_var = None
        self.canvas_scroll = self.inner_frame = self.main_window_id = None
        self.settings_button = None
        super().__init__(root, 'main')

    @staticmethod
    def configure_window(root):
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        root.rowconfigure(1, weight=0)

    def _setup_frame(self):
        self._create_main_frame()
        self._create_secondary_frame()
        self.frame = self.main_frame
        log_info('Vista principal inicializada')

    def _create_main_frame(self):
        frame = ttk.Frame(self.root, padding=(3, 3, 12, 12))
        frame.grid(column=0, row=0, sticky='nsew')
        frame.rowconfigure(3, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)
        self.main_frame = frame

        self.stop_title_var = tk.StringVar(value='Parada')

        create_label_with_wrapping(frame, 1, 1, 2, self.stop_title_var, TITLE_FONT)
        create_header_canvas(frame, 2, 1, 'Línea')
        create_header_canvas(frame, 2, 2, 'Tiempo')

        self.canvas_scroll = tk.Canvas(frame, highlightthickness=0)
        self.canvas_scroll.grid(column=1, row=3, columnspan=2, sticky='nsew')
        self.inner_frame = tk.Frame(self.canvas_scroll)
        self.main_window_id = self.canvas_scroll.create_window(0, 0, window=self.inner_frame, anchor=tk.NW)
        self.inner_frame.columnconfigure(0, weight=1)
        self.inner_frame.columnconfigure(1, weight=1)
        self.canvas_scroll.bind('<Configure>', self._resize_main_canvas)

        for row, line in enumerate(self.lines):
            try:
                value = self.time_provider('', line)
                visible = True
            except LineaNoPasaPorParadaError:
                value, visible = '', False
            except Exception as error:
                log_error(f'Error obteniendo tiempo para {line}: {error}')
                value, visible = '?', True
            self._create_line_row(row, line, value)
            self.line_visible[line] = visible
            self._set_line_visible(line, visible)

        self.root.after(150, self._start_scroll_animation)

    def _create_secondary_frame(self):
        self.empty_frame = tk.Frame(self.root)
        self.empty_frame.grid(column=0, row=1, sticky='nsew')
        self.secondary_frame = ttk.Frame(self.empty_frame, padding=(3, 3, 12, 12))
        self.secondary_frame.grid(column=0, row=0, sticky='nsew')
        self.bike_title_var = tk.StringVar(value='Información Adicional')
        create_label_with_wrapping(self.secondary_frame, 0, 0, 2, self.bike_title_var, TITLE_FONT)
        self.settings_button = tk.Button(
                    self.empty_frame, text='Configuración', font=('Segoe UI', 11, 'bold'),
                    bg='#1769aa', fg='white', activebackground='#0d527f',
                    activeforeground='white', relief=tk.RAISED, bd=2, padx=12, pady=6,
                    command=lambda: ViewManager.get_instance().switch_view('settings')
                )
        self.settings_button.grid(row=1, column=0, columnspan=2, padx=4, pady=(2, 6), sticky='ew')
        self._create_bike_info_grid()
        self.empty_frame.columnconfigure(0, weight=1)
        self.secondary_frame.columnconfigure(0, weight=1)
        self.secondary_frame.columnconfigure(1, weight=1)
        self.settings_button.lift()

    def _create_line_row(self, row, line, initial_value):
        badge = tk.Canvas(self.inner_frame, height=42, highlightthickness=0, bd=0)
        badge.grid(column=0, row=row, sticky='nsew')
        time_canvas = tk.Canvas(self.inner_frame, height=42, highlightthickness=0, bd=0)
        time_canvas.grid(column=1, row=row, sticky='nsew')
        time_var = tk.StringVar(value=initial_value)
        self.time_vars[line] = time_var
        self.line_widgets[line] = {'badge': badge, 'tiempo': time_canvas}

        def draw_badge(event=None):
            try:
                if badge.winfo_exists():
                    draw_line_badge(badge, line)
            except tk.TclError:
                pass

        def draw_time(event=None):
            try:
                if time_canvas.winfo_exists():
                    draw_centered_text(time_canvas, time_var.get(), tkfont.Font(family='Segoe UI', size=10))
            except tk.TclError:
                pass

        badge.bind('<Configure>', draw_badge)
        time_canvas.bind('<Configure>', draw_time)
        time_var.trace_add('write', lambda *_: draw_time())
        self.root.after(0, draw_badge)
        draw_time()

    def _create_bike_info_grid(self):
        originals, scaled = {}, {}
        for index, path in enumerate(('images/Bicicleta verde.png', 'images/Bicicleta naranja.png')):
            canvas = tk.Canvas(self.secondary_frame, height=60, width=60, highlightthickness=1, relief=tk.SUNKEN)
            canvas.grid(column=index, row=1, sticky='nsew', padx=5, pady=5)

            def draw_image(event=None, canvas=canvas, index=index, path=path):
                canvas.delete('all')
                try:
                    originals.setdefault(index, tk.PhotoImage(file=path))
                    photo = originals[index]
                    width, height = max(canvas.winfo_width(), 60), max(canvas.winfo_height(), 60)
                    scale = min(width / photo.width(), height / photo.height()) * .7
                    image = photo.subsample(max(1, int(1 / scale))) if scale < 1 else photo.zoom(max(1, int(scale))) if scale > 1 else photo
                    scaled[index] = image
                    canvas.create_image(width // 2, height // 2, image=image)
                except Exception as error:
                    log_error(f'Error cargando imagen PNG {index}: {error}')

            canvas.bind('<Configure>', draw_image)
            draw_image()

        for index, kind in enumerate(('FIT', 'EFIT')):
            canvas = tk.Canvas(self.secondary_frame, height=50, highlightthickness=0, bd=0)
            canvas.grid(column=index, row=2, sticky='nsew', padx=5, pady=5)
            variable = tk.StringVar(value=f'{kind}: 0')
            self.bike_vars[kind] = variable
            variable.trace_add('write', lambda *_args, canvas=canvas, variable=variable: self._draw_bike_value(canvas, variable))
            canvas.bind('<Configure>', lambda _event, canvas=canvas, variable=variable: self._draw_bike_value(canvas, variable))
            self._draw_bike_value(canvas, variable)

    @staticmethod
    def _draw_bike_value(canvas, variable):
        canvas.delete('all')
        draw_centered_text(canvas, variable.get(), tkfont.Font(family='Segoe UI', size=10))

    def _resize_main_canvas(self, event):
        self.canvas_scroll.itemconfigure(self.main_window_id, width=event.width)

    def _start_scroll_animation(self):
        self.inner_frame.update_idletasks()
        self.canvas_scroll.update()
        width = self.canvas_scroll.winfo_width()
        self.canvas_scroll.itemconfigure(self.main_window_id, width=width)
        self.inner_frame.configure(width=width)
        self._update_scroll_region()
        direction, accumulated, pause = 1, 0.0, 0

        def animate():
            nonlocal direction, accumulated, pause
            view = self.canvas_scroll.yview()
            visible = view[1] - view[0]
            if visible < 1:
                maximum = 1 - visible
                position = min(view[0], maximum)
                if pause:
                    pause -= 1
                else:
                    accumulated += SCROLL_SPEED * maximum * direction
                    accumulated = max(min(accumulated, abs(MAX_SCROLL_SPEED)), -abs(MAX_SCROLL_SPEED))
                    position += accumulated
                    if position >= maximum or position <= 0:
                        position = max(0, min(position, maximum))
                        accumulated, direction, pause = 0.0, -direction, 40
                    self.canvas_scroll.yview_moveto(position)
            self.root.after(50, animate)

        animate()

    def _set_line_visible(self, line, visible):
        widgets = self.line_widgets.get(line)
        if widgets:
            (widgets['badge'].grid if visible else widgets['badge'].grid_remove)()
            (widgets['tiempo'].grid if visible else widgets['tiempo'].grid_remove)()

    def update_bus_times(self, updates):
        for line, value in updates.items():
            if line not in self.time_vars:
                self._create_line_row(len(self.line_widgets), line, value)
            self.time_vars[line].set(value)
            self.line_visible[line] = value.strip() not in ('', '?')
            self._set_line_visible(line, self.line_visible[line])
        self._update_scroll_region()

    def replace_bus_rows(self, lines, updates):
        for child in self.inner_frame.winfo_children():
            child.destroy()
        self.time_vars.clear()
        self.line_widgets.clear()
        self.line_visible.clear()
        self.lines = list(lines)
        for row, line in enumerate(self.lines):
            value, visible = updates.get(line, ('?', True))
            self._create_line_row(row, line, value)
            self.line_visible[line] = visible
            self._set_line_visible(line, visible)
        self._update_scroll_region()

    def _update_scroll_region(self):
        self.inner_frame.update_idletasks()
        self.canvas_scroll.configure(scrollregion=self.canvas_scroll.bbox('all'))

    def set_stop_title(self, value):
        self.stop_title_var.set(value)

    def set_bike_title(self, value):
        self.bike_title_var.set(value)

    def set_bike_data(self, data):
        for key, variable in self.bike_vars.items():
            if key in data:
                variable.set(str(data[key]))

    def realign(self):
        width = self.canvas_scroll.winfo_width()
        if width > 1:
            self.canvas_scroll.itemconfigure(self.main_window_id, width=width)
            self.inner_frame.configure(width=width)
            self._update_scroll_region()

    def refresh_line_canvases(self):
        surface = get_theme()['surface']
        for line, widgets in self.line_widgets.items():
            try:
                widgets['badge'].configure(background=surface)
                draw_line_badge(widgets['badge'], line)
                widgets['tiempo'].configure(background=surface)
                draw_centered_text(widgets['tiempo'], self.time_vars[line].get(), tkfont.Font(family='Segoe UI', size=10))
            except tk.TclError:
                pass

    def show(self):
        self.main_frame.grid()
        self.empty_frame.grid()
        log_info("Vista 'main' mostrada")

    def hide(self):
        self.main_frame.grid_remove()
        self.empty_frame.grid_remove()
        log_info("Vista 'main' ocultada")
