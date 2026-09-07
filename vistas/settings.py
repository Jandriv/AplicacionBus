"""Vista táctil de configuración."""
import json
import tkinter as tk
from pathlib import Path
from tkinter import font as tkfont

from brightness import BrightnessController
from config import CONFIG_FILE_NAME, DEFAULT_LINEAS_A_PROBAR
from debug_log import log_error, log_info
from .base import View
from .manager import ViewManager


class SettingsView(View):
    """Configuración de paradas, líneas, brillo y tema."""

    def __init__(self, root, on_saved=None):
        self.on_saved = on_saved
        self.fields, self.line_vars = {}, {}
        self.lines_widgets, self.action_buttons = [], []
        self.lines_frame = self.lines_toggle = None
        self.keyboard = self.active_field = None
        self.status_var = self.brightness_var = self.theme_var = None
        self.settings_canvas = self.settings_content = self.status_label = None
        self.form = None
        self._settings_font_bases = {}
        self.lines_expanded = False
        self.brightness_controller = BrightnessController()
        super().__init__(root, 'settings')

    def _setup_frame(self):
        try:
            self.frame = tk.Frame(self.root, bg='#f0f2f5')
            self.frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.frame.place_forget()
            self.frame.columnconfigure(0, weight=1)
            self.frame.rowconfigure(0, weight=1)
            self.settings_canvas = tk.Canvas(self.frame, bg='#f0f2f5', highlightthickness=0)
            self.settings_canvas.grid(row=0, column=0, sticky='nsew')
            self.settings_content = tk.Frame(self.settings_canvas, bg='#f0f2f5')
            self.settings_content.columnconfigure(0, weight=1)
            window_id = self.settings_canvas.create_window((0, 0), window=self.settings_content, anchor='nw')

            def update_scroll(event=None):
                self.settings_canvas.configure(scrollregion=self.settings_canvas.bbox('all'))
                self.settings_canvas.itemconfigure(window_id, width=self.settings_canvas.winfo_width())

            self.settings_content.bind('<Configure>', update_scroll)
            self.settings_canvas.bind('<Configure>', update_scroll)
            self.frame.bind('<Configure>', self._scale_settings)

            tk.Label(self.settings_content, text='Configuración', font=('Segoe UI', 24, 'bold'),
                     bg='#f0f2f5', fg='#202124').grid(row=0, column=0, pady=(18, 12))
            form = tk.Frame(self.settings_content, bg='#ffffff', padx=18, pady=12)
            self.form = form
            form.grid(row=1, column=0, padx=12, pady=8, sticky='ew')
            form.columnconfigure(1, weight=1)
            config = self._read_config()
            self._create_fields(form, config)
            self._create_brightness(form, config)
            self._create_lines(form, config)
            self._create_theme(form, config)
            self._create_keyboard(form)
            self.settings_canvas.bind('<Configure>', self._resize_form, add='+')
            self.root.after_idle(self._layout_responsive_controls)
            self._create_actions()
            self._create_status()
            self._bind_scroll_events(self.settings_content)
        except Exception as error:
            log_error(f'Error configurando settings: {error}')

    def _create_fields(self, form, config):
        fields = (
            ('parada_actual', 'Parada de autobús', config.get('parada_actual', '625')),
            ('parada_biki_actual', 'Parada de bikis', config.get('parada_biki_actual', '686')),
        )
        for row, (key, label, value) in enumerate(fields):
            tk.Label(form, text=label, anchor='w', bg='#ffffff', fg='#30343b',
                     font=('Segoe UI', 11, 'bold')).grid(row=row * 2, column=0, columnspan=2,
                     padx=4, pady=(8, 2), sticky='w')
            self.fields[key] = tk.StringVar(value=str(value))
            entry = tk.Entry(form, textvariable=self.fields[key], font=('Segoe UI', 11), relief=tk.SOLID, bd=1)
            entry.grid(row=row * 2 + 1, column=0, columnspan=2, padx=4, pady=(0, 6), sticky='ew')
            entry.bind('<Button-1>', lambda event, field=entry: self._show_keyboard(field))

    def _create_brightness(self, form, config):
        self._section_label(form, 'Brillo de pantalla', 4)
        self.brightness_var = tk.IntVar(value=int(config.get('brightness', 100)))
        tk.Scale(form, from_=10, to=100, orient=tk.HORIZONTAL, variable=self.brightness_var,
                 showvalue=True, resolution=5, length=280, bg='#ffffff', highlightthickness=0,
                 font=('Segoe UI', 10), command=self._set_brightness).grid(
                     row=5, column=0, columnspan=2, padx=4, pady=(0, 6), sticky='ew')
        self.brightness_controller.set(self.brightness_var.get())

    def _create_lines(self, form, config):
        self._section_label(form, 'Líneas mostradas', 6)
        self.lines_toggle = tk.Button(form, text='Mostrar líneas', command=self._toggle_lines,
                                       font=('Segoe UI', 11, 'bold'), relief=tk.FLAT,
                                       anchor='w', padx=10)
        self.lines_toggle.grid(row=7, column=0, columnspan=2, padx=4, pady=(0, 4), sticky='ew')
        self.lines_frame = tk.Frame(form, bg='#ffffff')
        self.lines_frame.grid(row=8, column=0, columnspan=2, padx=4, pady=(0, 8), sticky='ew')
        selected = {str(line) for line in config.get('lineas_a_probar', [])}
        available = list(dict.fromkeys(DEFAULT_LINEAS_A_PROBAR + list(selected)))
        for line in available:
            variable = tk.BooleanVar(value=str(line) in selected)
            self.line_vars[str(line)] = variable
            self.lines_widgets.append(tk.Checkbutton(
                self.lines_frame, text=str(line), variable=variable, bg='#ffffff',
                activebackground='#ffffff', font=('Segoe UI', 11), padx=8, pady=5))
        self.lines_frame.grid_remove()

    def _create_theme(self, form, config):
        self._section_label(form, 'Tema de la aplicación', 9)
        theme = config.get('theme', 'dark' if config.get('dark_mode', False) else 'light')
        self.theme_var = tk.StringVar(value=theme)
        tk.OptionMenu(form, self.theme_var, 'light', 'dark').grid(
            row=10, column=0, columnspan=2, padx=4, pady=(0, 8), sticky='ew')

    @staticmethod
    def _section_label(parent, text, row):
        tk.Label(parent, text=text, anchor='w', bg='#ffffff', fg='#30343b',
                 font=('Segoe UI', 11, 'bold')).grid(
                     row=row, column=0, columnspan=2, padx=4, pady=(8, 2), sticky='w')

    def _create_actions(self):
        actions = tk.Frame(self.settings_content, bg='#f0f2f5')
        actions.grid(row=2, column=0, pady=(0, 12))
        self.action_buttons = [
            tk.Button(actions, text='Guardar cambios', command=self._save_config,
                      bg='#1769aa', fg='white', activebackground='#0d527f',
                      activeforeground='white', relief=tk.FLAT, padx=18, pady=8,
                      font=('Segoe UI', 11, 'bold')),
            tk.Button(actions, text='Restaurar valores', command=self._load_fields,
                      relief=tk.FLAT, padx=18, pady=8, font=('Segoe UI', 11)),
            tk.Button(actions, text='Volver', command=self._go_back,
                      relief=tk.FLAT, padx=18, pady=8, font=('Segoe UI', 11)),
        ]
        self._layout_responsive_controls()

    def _create_status(self):
        self.status_var = tk.StringVar(value='Los cambios se aplican inmediatamente al guardar.')
        self.status_label = tk.Label(self.settings_content, textvariable=self.status_var,
                                     bg='#f0f2f5', fg='#5f6368', font=('Segoe UI', 10), justify=tk.CENTER)
        self.status_label.grid(row=3, column=0, padx=12, pady=(0, 14), sticky='ew')
        self._update_status_wrap()

    def _create_keyboard(self, parent):
        self.keyboard = tk.Frame(parent, bg='#e8eaed', padx=8, pady=8)
        self.keyboard.grid(row=12, column=0, columnspan=2, pady=(18, 0), sticky='nsew')
        for row, keys in enumerate(('1 2 3 4 5', '6 7 8 9 0')):
            frame = tk.Frame(self.keyboard, bg='#e8eaed')
            frame.grid(row=row, column=0, sticky='ew')
            frame.columnconfigure(tuple(range(5)), weight=1)
            for column, key in enumerate(keys.split()):
                tk.Button(frame, text=key, command=lambda value=key: self._keyboard_insert(value),
                          font=('Segoe UI', 12, 'bold'), height=1).grid(row=0, column=column, padx=2, pady=2, sticky='ew')
        controls = tk.Frame(self.keyboard, bg='#e8eaed')
        controls.grid(row=2, column=0, sticky='ew')
        controls.columnconfigure((0, 1, 2), weight=1)
        for column, (label, command) in enumerate((
            ('Borrar', self._keyboard_backspace), ('Limpiar', self._keyboard_clear), ('Ocultar', self._hide_keyboard))):
            tk.Button(controls, text=label, command=command, font=('Segoe UI', 11, 'bold')).grid(
                row=0, column=column, padx=2, pady=(4, 0), sticky='ew')
        self._hide_keyboard()

    def _resize_form(self, event=None):
        self.form.configure(width=max(self.settings_canvas.winfo_width() - 24, 1))
        self._layout_responsive_controls()

    def _layout_responsive_controls(self):
        if not self.form or not self.settings_canvas:
            return
        width = max(self.settings_canvas.winfo_width() - 48, 180)
        self.form.configure(width=width)
        columns = max(1, min(5, width // 82))
        self.lines_frame.configure(width=width)
        for column in range(5):
            self.lines_frame.columnconfigure(column, weight=column < columns)
        for index, widget in enumerate(self.lines_widgets):
            widget.grid(row=index // columns, column=index % columns, padx=4, pady=4, sticky='ew')
        columns = max(1, min(3, width // 150))
        actions = self.action_buttons[0].master if self.action_buttons else None
        if actions:
            for column in range(columns):
                actions.columnconfigure(column, weight=1)
            for index, button in enumerate(self.action_buttons):
                button.grid(row=index // columns, column=index % columns, padx=6, pady=4, sticky='ew')

    def _scale_settings(self, event=None):
        width, height = self.settings_canvas.winfo_width(), self.settings_canvas.winfo_height()
        if width <= 1 or height <= 1:
            return
        self._layout_responsive_controls()
        self._update_status_wrap()
        scale = max(.7, min(1.2, min(width / 600, height / 700)))
        widgets = [self.settings_content]
        while widgets:
            widget = widgets.pop()
            widgets.extend(widget.winfo_children())
            try:
                value = widget.cget('font')
                if value and widget not in self._settings_font_bases:
                    font = tkfont.Font(font=value)
                    self._settings_font_bases[widget] = (font.actual('family'), abs(font.actual('size')), font.actual('weight'))
                if value:
                    family, size, weight = self._settings_font_bases[widget]
                    widget.configure(font=(family, max(8, round(size * scale)), weight))
            except (tk.TclError, TypeError):
                pass

    def _update_status_wrap(self):
        if self.status_label:
            self.status_label.configure(wraplength=max(160, self.settings_canvas.winfo_width() - 36))

    def _bind_scroll_events(self, widget):
        widget.bind('<ButtonPress-1>', self._start_scroll, add='+')
        widget.bind('<B1-Motion>', self._scroll_content, add='+')
        widget.bind('<MouseWheel>', self._on_mousewheel, add='+')
        for child in widget.winfo_children():
            self._bind_scroll_events(child)

    def _start_scroll(self, event):
        self.settings_canvas.scan_mark(event.x_root - self.settings_canvas.winfo_rootx(), event.y_root - self.settings_canvas.winfo_rooty())

    def _scroll_content(self, event):
        self.settings_canvas.scan_dragto(event.x_root - self.settings_canvas.winfo_rootx(), event.y_root - self.settings_canvas.winfo_rooty(), gain=1)

    def _on_mousewheel(self, event):
        self.settings_canvas.yview_scroll(-1 if event.delta > 0 else 1, 'units')

    def _show_keyboard(self, field):
        self.active_field = field
        self.keyboard.grid()
        field.focus_set()
        field.icursor(tk.END)

    def _keyboard_insert(self, value):
        if self.active_field:
            self.active_field.insert(tk.INSERT, value)
            self.active_field.focus_set()

    def _keyboard_backspace(self):
        if self.active_field:
            position = self.active_field.index(tk.INSERT)
            if position > 0:
                self.active_field.delete(position - 1, position)
                self.active_field.focus_set()

    def _keyboard_clear(self):
        if self.active_field:
            self.active_field.delete(0, tk.END)
            self.active_field.focus_set()

    def _hide_keyboard(self):
        self.active_field = None
        if self.keyboard:
            self.keyboard.grid_remove()
        self.frame.focus_set()

    def _set_brightness(self, value):
        success, message = self.brightness_controller.set(value)
        self.status_var.set(f'Brillo: {int(float(value))}%' if success else message)

    def _toggle_lines(self):
        self.lines_expanded = not self.lines_expanded
        if self.lines_expanded:
            self.lines_frame.grid()
            self.lines_toggle.config(text='Ocultar líneas')
        else:
            self.lines_frame.grid_remove()
            self.lines_toggle.config(text='Mostrar líneas')
        self._layout_responsive_controls()

    def _config_path(self):
        return Path(__file__).parent.parent / CONFIG_FILE_NAME

    def _read_config(self):
        try:
            with self._config_path().open(encoding='utf-8') as file:
                value = json.load(file)
            return value if isinstance(value, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError, OSError) as error:
            log_error(f'No se pudo leer la configuración: {error}')
            return {}

    def _load_fields(self):
        config = self._read_config()
        self.fields['parada_actual'].set(config.get('parada_actual', '625'))
        self.fields['parada_biki_actual'].set(config.get('parada_biki_actual', '686'))
        self.brightness_var.set(int(config.get('brightness', 100)))
        self.brightness_controller.set(self.brightness_var.get())
        self.theme_var.set(config.get('theme', 'dark' if config.get('dark_mode', False) else 'light'))
        selected = {str(line) for line in config.get('lineas_a_probar', [])}
        for line, variable in self.line_vars.items():
            variable.set(line in selected)
        self.status_var.set('Valores restaurados desde el archivo de configuración.')

    def _save_config(self):
        try:
            lines = [line for line, variable in self.line_vars.items() if variable.get()]
            if not lines:
                raise ValueError('Debe indicar al menos una línea.')
            config = self._read_config()
            config.update({
                'parada_actual': self.fields['parada_actual'].get().strip(),
                'lineas_a_probar': lines,
                'parada_biki_actual': self.fields['parada_biki_actual'].get().strip(),
                'brightness': int(self.brightness_var.get()),
                'theme': self.theme_var.get(),
            })
            with self._config_path().open('w', encoding='utf-8') as file:
                json.dump(config, file, indent=2, ensure_ascii=False)
                file.write('\n')
            if self.on_saved:
                self.on_saved(config)
            self.status_var.set('Configuración guardada y aplicada.')
            self._hide_keyboard()
            log_info('Configuración guardada desde la vista settings')
        except (OSError, ValueError) as error:
            self.status_var.set(f'No se pudo guardar: {error}')
            log_error(f'Error guardando configuración: {error}')

    def _go_back(self):
        self._load_fields()
        self._hide_keyboard()
        ViewManager.get_instance().switch_view('main')

    def show(self):
        self.frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.frame.lift()
        self._scale_settings()
        log_info("Vista 'settings' mostrada")

    def hide(self):
        self.frame.place_forget()
        log_info("Vista 'settings' ocultada")
