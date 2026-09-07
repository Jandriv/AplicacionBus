"""Vista de bloqueo con reloj y fecha."""
import tkinter as tk
from datetime import datetime as dt

from .base import View
from debug_log import log_error, log_info
from .manager import ViewManager


class LockscreenView(View):
    """Lockscreen con reloj digital y fondo escalable."""

    def __init__(self, root):
        self.background_canvas = None
        self.background_original = None
        self.background_scaled = None
        self.background_image_id = None
        self.clock_text_id = None
        self.info_text_id = None
        super().__init__(root, 'lockscreen')

    def _setup_frame(self):
        try:
            self.frame = tk.Frame(self.root, bg='#1a1a1a')
            self.frame.grid(column=0, row=0, columnspan=2, rowspan=2, sticky='nsew')
            self.frame.columnconfigure(0, weight=1)
            self.frame.rowconfigure(0, weight=1)
            self.background_canvas = tk.Canvas(
                self.frame, bg='#1a1a1a', highlightthickness=0,
                highlightbackground='#1a1a1a'
            )
            self.background_canvas.grid(column=0, row=0, rowspan=3, sticky='nsew')
            self.background_canvas.bind('<Button-1>', self._pass_click_to_frame)
            self.background_canvas.bind('<Configure>', self._on_frame_resize)

            try:
                self.background_original = tk.PhotoImage(file='fondos/fondo.png')
                self.background_image_id = self.background_canvas.create_image(0, 0, anchor=tk.CENTER)
                log_info('Imagen de fondo cargada exitosamente')
            except Exception as error:
                log_error(f'No se pudo cargar fondo fondos/fondo.png: {error}')

            self.clock_text_id = self.background_canvas.create_text(
                0, 0, text='00:00:00', font=('Courier', 20, 'bold'),
                fill='white', anchor=tk.CENTER
            )
            self.info_text_id = self.background_canvas.create_text(
                0, 0, text=dt.now().strftime('%d/%m/%Y'), font=('Arial', 16),
                fill='white', justify=tk.CENTER, anchor=tk.CENTER
            )
            self.clock_canvas = self.background_canvas
            self.info_canvas = self.background_canvas
            self.frame.grid_remove()
            self.update_clock()
            self.update_date()
            self.root.after(100, self._update_fonts)
            log_info('Lockscreen inicializado con Canvas')
        except Exception as error:
            log_error(f'Error configurando lockscreen: {error}')

    def _on_frame_resize(self, event=None):
        try:
            self._update_fonts()
        except Exception as error:
            log_error(f'Error al redimensionar lockscreen: {error}')

    def show(self):
        super().show()
        self.root.after(100, self._update_fonts)

    def _update_fonts(self):
        try:
            width = self.background_canvas.winfo_width()
            height = self.background_canvas.winfo_height()
            if width <= 1 or height <= 1:
                return
            self._draw_background_image(width, height)
            clock_size = min(120, max(14, min(int(height * .18), int(width * .1))))
            date_size = min(42, max(10, min(int(height * .06), int(width * .04))))
            clock_y = max(int(height * .22), clock_size)
            date_y = clock_y + max(int(clock_size * .55), 16)
            self.background_canvas.itemconfig(self.clock_text_id, font=('Courier', clock_size, 'bold'))
            self.background_canvas.coords(self.clock_text_id, width // 2, clock_y)
            self.background_canvas.itemconfig(self.info_text_id, font=('Arial', date_size), width=max(50, int(width * .75)))
            self.background_canvas.coords(self.info_text_id, width // 2, date_y)
            self.background_canvas.tag_raise(self.info_text_id)
            self.background_canvas.tag_raise(self.clock_text_id)
        except Exception as error:
            log_error(f'Error actualizando fonts: {error}')

    def _draw_background_image(self, width, height):
        if not self.background_original:
            self.background_canvas.configure(bg='#1a1a1a')
            return
        try:
            scale = min(width / self.background_original.width(), height / self.background_original.height())
            if scale < 1:
                factor = max(1, int(1 / scale))
                self.background_scaled = self.background_original.subsample(factor, factor)
            elif scale > 1:
                factor = max(1, int(scale))
                self.background_scaled = self.background_original.zoom(factor, factor)
            else:
                self.background_scaled = self.background_original
            self.background_canvas.itemconfig(self.background_image_id, image=self.background_scaled)
            self.background_canvas.coords(self.background_image_id, width // 2, height // 2)
            self.background_canvas.tag_lower(self.background_image_id)
        except Exception as error:
            log_error(f'Error dibujando fondo: {error}')

    def update_clock(self):
        try:
            self.background_canvas.itemconfig(self.clock_text_id, text=dt.now().strftime('%H:%M:%S'))
        except Exception as error:
            log_error(f'Error actualizando reloj: {error}')

    def update_date(self):
        try:
            self.background_canvas.itemconfig(self.info_text_id, text=dt.now().strftime('%d/%m/%Y'))
        except Exception as error:
            log_error(f'Error actualizando fecha: {error}')

    def _pass_click_to_frame(self, event=None):
        try:
            ViewManager.get_instance().switch_view('main')
            return 'break'
        except Exception as error:
            log_error(f'Error en evento de clic: {error}')
