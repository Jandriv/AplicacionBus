"""
views.py - Sistema modular de vistas para AppBus

Proporciona una arquitectura escalable para manejar múltiples vistas
y transiciones entre ellas.
"""
import tkinter as tk
from datetime import datetime as dt
from abc import ABC, abstractmethod

try:
    from debug_log import log_error, log_info
except ImportError:
    def log_error(msg):
        print(f"[ERROR] {msg}")
    def log_info(msg):
        print(f"[INFO] {msg}")


class View(ABC):
    """Clase base para todas las vistas"""
    
    def __init__(self, root, name):
        """
        Inicializa una vista
        
        Args:
            root: Widget raíz de Tkinter
            name: Identificador único de la vista (ej: 'main', 'lockscreen')
        """
        self.root = root
        self.name = name
        self.frame = None
        self._setup_frame()
    
    @abstractmethod
    def _setup_frame(self):
        """Crea y configura el frame de la vista. Debe ser implementado por subclases"""
        pass
    
    def show(self):
        """Muestra la vista"""
        if self.frame:
            self.frame.grid()
            log_info(f"Vista '{self.name}' mostrada")
    
    def hide(self):
        """Oculta la vista"""
        if self.frame:
            self.frame.grid_remove()
            log_info(f"Vista '{self.name}' ocultada")
    
    def is_visible(self):
        """Retorna si la vista está visible"""
        return self.frame and self.frame.winfo_viewable() if self.frame else False


class LockscreenView(View):
    """Vista de lockscreen con reloj digital y textos dinámicos usando Canvas"""
    
    def __init__(self, root):
        # Unified canvas implementation: a single canvas holds background + texts
        self.background_canvas = None
        self.background_original = None
        self.background_scaled = None
        self.background_image_id = None
        self.clock_text_id = None
        self.info_text_id = None
        super().__init__(root, 'lockscreen')
    
    def _setup_frame(self):
        """Crea el frame del lockscreen con Canvas para textos dinámicos"""
        try:
            self.frame = tk.Frame(self.root, bg='#1a1a1a')
            self.frame.grid(column=0, row=0, columnspan=2, rowspan=2, 
                          sticky=(tk.N, tk.S, tk.E, tk.W))
            self.frame.columnconfigure(0, weight=1)
            self.frame.rowconfigure(0, weight=1)
            
            # Un único canvas que actúa como fondo y contenedor de textos
            self.background_canvas = tk.Canvas(
                self.frame,
                bg='#1a1a1a',
                highlightthickness=0,
                highlightbackground='#1a1a1a'
            )
            # Ocupa todo el grid (3 filas)
            self.background_canvas.grid(column=0, row=0, rowspan=3, sticky=(tk.N, tk.S, tk.E, tk.W))
            # Eventos en el canvas (clic y resize)
            self.background_canvas.bind("<Button-1>", self._pass_click_to_frame)
            self.background_canvas.bind("<Configure>", self._on_frame_resize)

            # Cargar imagen base (si existe). soporta formatos nativos de Tkinter (ppm/png según compilación)
            try:
                self.background_original = tk.PhotoImage(file="fondos/fondo.png")
                # crear imagen vacía; se asigna/escala en _draw_background_image
                self.background_image_id = self.background_canvas.create_image(0, 0, anchor=tk.CENTER)
                log_info("Imagen de fondo cargada exitosamente")
            except Exception as e:
                self.background_original = None
                log_error(f"No se pudo cargar fondo fondos/fondo.png: {e}")

            # Textos sobre el fondo
            self.clock_text_id = self.background_canvas.create_text(
                0,
                0,
                text="00:00:00",
                font=("Courier", 20, "bold"),
                fill="white",
                anchor=tk.CENTER,
            )
            self.info_text_id = self.background_canvas.create_text(
                0,
                0,
                text=dt.now().strftime("%d/%m/%Y"),
                font=("Arial", 16),
                fill="white",
                justify=tk.CENTER,
                anchor=tk.CENTER,
            )

            # Compatibilidad con métodos existentes
            self.clock_canvas = self.background_canvas
            self.info_canvas = self.background_canvas
            
            # INICIALMENTE OCULTO
            self.frame.grid_remove()
            
            # El canvas de fondo gestiona redimensionado y clics; no necesitamos bindings duplicados en el frame
            
            # Actualizar reloj inmediatamente
            self.update_clock()
            self.update_date()
            # Programar primer redimensionamiento
            self.root.after(100, self._update_fonts)
            log_info("Lockscreen inicializado con Canvas")
            
        except Exception as e:
            log_error(f"Error configurando lockscreen: {e}")
    
    def _on_frame_resize(self, event=None):
        """Maneja el evento de redimensionamiento de la ventana"""
        try:
            self._update_fonts()
        except Exception as e:
            log_error(f"Error al redimensionar lockscreen: {e}")
    
    def show(self):
        """Muestra la vista del lockscreen y actualiza los fonts"""
        super().show()
        # Actualizar fonts cuando se muestra
        self.root.after(100, self._update_fonts)
    
    def _update_fonts(self):
        """Actualiza los tamaños de font basado en el tamaño de la ventana"""
        try:
            frame_width = self.frame.winfo_width()
            frame_height = self.frame.winfo_height()
            
            if frame_width <= 1 or frame_height <= 1:
                return

            canvas_width = self.background_canvas.winfo_width() if self.background_canvas else 0
            canvas_height = self.background_canvas.winfo_height() if self.background_canvas else 0
            if canvas_width <= 1 or canvas_height <= 1:
                return

            self._draw_background_image(canvas_width, canvas_height)

            clock_font_size = min(120, max(14, min(int(canvas_height * 0.18), int(canvas_width * 0.1))))
            info_font_size = min(42, max(10, min(int(canvas_height * 0.06), int(canvas_width * 0.04))))
            wrap_width = max(50, int(frame_width * 0.75))

            # Posicionar en la parte superior (primer tercio)
            clock_y = max(int(canvas_height * 0.22), int(clock_font_size))
            date_y = clock_y + max(int(clock_font_size * 0.55), 16)

            if self.background_canvas and self.clock_text_id:
                self.background_canvas.itemconfig(
                    self.clock_text_id,
                    font=("Courier", clock_font_size, "bold")
                )
                self.background_canvas.coords(self.clock_text_id, canvas_width // 2, clock_y)

            if self.background_canvas and self.info_text_id:
                self.background_canvas.itemconfig(
                    self.info_text_id,
                    font=("Arial", info_font_size),
                    width=wrap_width
                )
                self.background_canvas.coords(self.info_text_id, canvas_width // 2, date_y)
                # Asegurar que los textos quedan por encima del fondo
                try:
                    if self.background_image_id is not None:
                        self.background_canvas.tag_lower(self.background_image_id)
                except Exception:
                    pass
                self.background_canvas.tag_raise(self.info_text_id)
                self.background_canvas.tag_raise(self.clock_text_id)
                
        except Exception as e:
            log_error(f"Error actualizando fonts: {e}")

    def _draw_background_image(self, canvas_width, canvas_height):
        """Dibuja el fondo con escalado similar al usado en las imágenes de bicis."""
        if not self.background_canvas:
            return

        if not self.background_original:
            self.background_canvas.configure(bg="#1a1a1a")
            return

        try:
            img_width = self.background_original.width()
            img_height = self.background_original.height()
            if img_width <= 0 or img_height <= 0:
                return

            factor_escalado = 1.0
            scale_x = (canvas_width / img_width) * factor_escalado
            scale_y = (canvas_height / img_height) * factor_escalado
            scale = min(scale_x, scale_y)

            if scale < 1:
                factor = max(1, int(1 / scale))
                self.background_scaled = self.background_original.subsample(factor, factor)
            elif scale > 1:
                factor = max(1, int(scale))
                self.background_scaled = self.background_original.zoom(factor, factor)
            else:
                self.background_scaled = self.background_original

            if self.background_image_id is None:
                self.background_image_id = self.background_canvas.create_image(
                    canvas_width // 2,
                    canvas_height // 2,
                    image=self.background_scaled,
                    anchor=tk.CENTER,
                )
            else:
                self.background_canvas.itemconfig(self.background_image_id, image=self.background_scaled)
                self.background_canvas.coords(self.background_image_id, canvas_width // 2, canvas_height // 2)

            self.background_canvas.tag_lower(self.background_image_id)
        except Exception as e:
            log_error(f"Error dibujando fondo: {e}")
    
    def update_clock(self):
        """Actualiza la hora en el reloj"""
        try:
            if self.background_canvas and self.clock_text_id:
                hora_actual = dt.now().strftime("%H:%M:%S")
                self.background_canvas.itemconfig(self.clock_text_id, text=hora_actual)
        except Exception as e:
            log_error(f"Error actualizando reloj: {e}")


    def update_date(self):
        """Actualiza la fecha en el canvas de información"""
        try:
            if self.background_canvas and self.info_text_id:
                fecha_actual = dt.now().strftime("%d/%m/%Y")
                self.background_canvas.itemconfig(self.info_text_id, text=fecha_actual)
        except Exception as e:
            log_error(f"Error actualizando fecha: {e}")
    
    def _pass_click_to_frame(self, event=None):
        """Pasa el evento de clic del background canvas al frame para permitir cambiar de vista"""
        try:
            ViewManager.get_instance().switch_view('main')
            return "break"
        except Exception as e:
            log_error(f"Error en evento de clic: {e}")

    


class MainView(View):
    """Vista principal de la aplicación"""
    
    def __init__(self, root, main_frame, empty_frame, secondary_frame):
        self.main_frame = main_frame
        self.empty_frame = empty_frame
        self.secondary_frame = secondary_frame
        super().__init__(root, 'main')
    
    def _setup_frame(self):
        """Para la vista principal, reutilizamos los frames existentes"""
        # La vista principal es compuesta por múltiples frames
        # Solo necesitamos registrar que existen
        self.frame = self.main_frame  # Frame principal para referencia
        log_info("Vista principal inicializada")
    
    def show(self):
        """Muestra la vista principal (todos sus frames)"""
        if self.main_frame:
            self.main_frame.grid()
        if self.empty_frame:
            self.empty_frame.grid()
        log_info("Vista 'main' mostrada")
    
    def hide(self):
        """Oculta la vista principal (todos sus frames)"""
        if self.main_frame:
            self.main_frame.grid_remove()
        if self.empty_frame:
            self.empty_frame.grid_remove()
        log_info("Vista 'main' ocultada")


class ViewManager:
    """
    Gestor de vistas - Maneja la transición entre vistas y el ciclo de vida
    
    Singleton: Solo una instancia en toda la aplicación
    """
    _instance = None
    
    def __init__(self, root):
        self.root = root
        self.views = {}
        self.current_view = None
        self.update_callbacks = []  # Callbacks ejecutados cada frame
        self._start_update_loop()
    
    @classmethod
    def get_instance(cls):
        """Obtiene la instancia singleton del ViewManager"""
        if cls._instance is None:
            raise RuntimeError("ViewManager no ha sido inicializado")
        return cls._instance
    
    @classmethod
    def initialize(cls, root):
        """Inicializa el ViewManager singleton"""
        if cls._instance is None:
            cls._instance = cls(root)
        return cls._instance
    
    def register_view(self, view):
        """
        Registra una nueva vista
        
        Args:
            view: Instancia de una clase que hereda de View
        """
        self.views[view.name] = view
        log_info(f"Vista '{view.name}' registrada")
    
    def register_update_callback(self, callback):
        """
        Registra un callback que se ejecutará cada frame (para actualizar reloj, etc)
        
        Args:
            callback: Función que será llamada sin argumentos
        """
        self.update_callbacks.append(callback)
    
    def switch_view(self, view_name):
        """
        Cambia a una vista diferente
        
        Args:
            view_name: Nombre de la vista (ej: 'lockscreen', 'main')
        """
        if view_name not in self.views:
            log_error(f"Vista '{view_name}' no registrada")
            return
        
        # Ocultar vista actual
        if self.current_view:
            self.current_view.hide()
        
        # Mostrar nueva vista
        new_view = self.views[view_name]
        new_view.show()
        self.current_view = new_view
        
        log_info(f"Cambio de vista: {self.current_view.name}")
    
    def _start_update_loop(self):
        """Inicia el loop de actualización para callbacks"""
        def update():
            for callback in self.update_callbacks:
                try:
                    callback()
                except Exception as e:
                    log_error(f"Error en callback de actualización: {e}")
            
            if self.root:
                self.root.after(1000, update)  # Ejecutar cada segundo
        
        if self.root:
            self.root.after(1000, update)
    
    def set_initial_view(self, view_name):
        """Establece la vista inicial"""
        if view_name in self.views:
            self.switch_view(view_name)
            log_info(f"Vista inicial: {view_name}")
        else:
            log_error(f"Vista inicial '{view_name}' no existe")


def add_click_bindings_to_view(widget, target_view='lockscreen'):
    """
    Agrega bindings de click a un widget y sus hijos para cambiar de vista
    
    Args:
        widget: Widget principal
        target_view: Nombre de la vista a la que cambiar (por defecto: 'lockscreen')
    """
    try:
        def on_click(event):
            ViewManager.get_instance().switch_view(target_view)
            return "break"
        
        widget.bind("<Button-1>", on_click)
        
        # Recursivamente agregar bindings a widgets hijos
        for child in widget.winfo_children():
            add_click_bindings_to_view(child, target_view)
    except Exception as e:
        log_error(f"Error agregando bindings: {e}")
