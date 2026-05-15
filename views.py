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
        self.clock_canvas = None
        self.clock_text_id = None
        self.info_canvas = None
        self.info_text_id = None
        self.middle_frame = None
        self.bottom_frame = None
        super().__init__(root, 'lockscreen')
    
    def _setup_frame(self):
        """Crea el frame del lockscreen con Canvas para textos dinámicos"""
        try:
            self.frame = tk.Frame(self.root, bg='#1a1a1a')
            self.frame.grid(column=0, row=0, columnspan=2, rowspan=2, 
                          sticky=(tk.N, tk.S, tk.E, tk.W))
            self.frame.columnconfigure(0, weight=1)
            self.frame.rowconfigure(0, weight=1)  # Top spacer
            self.frame.rowconfigure(1, weight=2)  # Middle (reloj)
            self.frame.rowconfigure(2, weight=1)  # Bottom (desbloquear)
            
            # INICIALMENTE OCULTO
            self.frame.grid_remove()
            
            # Agregar binding para detectar cambios de tamaño
            self.frame.bind("<Configure>", self._on_frame_resize)
            
            # Hacer que cualquier click cambie de vista
            self.frame.bind("<Button-1>", lambda event: 
                           ViewManager.get_instance().switch_view('main'))
            
            # ===== TOP SPACER =====
            top_spacer = tk.Frame(self.frame, bg='#1a1a1a')
            top_spacer.grid(column=0, row=0, sticky=(tk.N, tk.S, tk.E, tk.W))
            top_spacer.bind("<Button-1>", lambda event: 
                           ViewManager.get_instance().switch_view('main'))
            
            # ===== MIDDLE FRAME (RELOJ CON CANVAS) =====
            self.middle_frame = tk.Frame(self.frame, bg='#1a1a1a')
            self.middle_frame.grid(column=0, row=1, sticky=(tk.N, tk.S, tk.E, tk.W))
            self.middle_frame.columnconfigure(0, weight=1)
            self.middle_frame.rowconfigure(0, weight=1)
            
            # Canvas para el reloj (mejor escalabilidad)
            self.clock_canvas = tk.Canvas(
                self.middle_frame,
                bg='#1a1a1a',
                highlightthickness=0,
                highlightbackground='#1a1a1a'
            )
            self.clock_canvas.grid(column=0, row=0, sticky=(tk.N, tk.S, tk.E, tk.W))
            self.clock_canvas.bind("<Configure>", self._on_frame_resize)
            
            # Crear texto en el canvas
            self.clock_text_id = self.clock_canvas.create_text(
                0, 0,
                text="00:00:00",
                font=("Courier", 20, "bold"),
                fill="white",
                anchor=tk.CENTER
            )
            
            self.clock_canvas.bind("<Button-1>", lambda event: 
                                 ViewManager.get_instance().switch_view('main'))
            self.middle_frame.bind("<Button-1>", lambda event: 
                             ViewManager.get_instance().switch_view('main'))
            
            # ===== BOTTOM FRAME (TEXTO CON CANVAS) =====
            self.bottom_frame = tk.Frame(self.frame, bg='#1a1a1a')
            self.bottom_frame.grid(column=0, row=2, sticky=(tk.N, tk.S, tk.E, tk.W))
            self.bottom_frame.columnconfigure(0, weight=1)
            self.bottom_frame.rowconfigure(0, weight=1)
            
            # Canvas para el texto de desbloqueo (mejor escalabilidad)
            self.info_canvas = tk.Canvas(
                self.bottom_frame,
                bg='#1a1a1a',
                highlightthickness=0,
                highlightbackground='#1a1a1a'
            )
            self.info_canvas.grid(column=0, row=0, sticky=(tk.N, tk.S, tk.E, tk.W))
            self.info_canvas.bind("<Configure>", self._on_frame_resize)
            
            # Crear texto en el canvas
            self.info_text_id = self.info_canvas.create_text(
                0, 0,
                text="15/05/2026",
                font=("Arial", 16),
                fill="white",
                justify=tk.CENTER,
                anchor=tk.CENTER
            )
            
            self.info_canvas.bind("<Button-1>", lambda event: 
                           ViewManager.get_instance().switch_view('main'))
            self.bottom_frame.bind("<Button-1>", lambda event: 
                             ViewManager.get_instance().switch_view('main'))
            
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
            # Obtener dimensiones de los canvas y del frame
            frame_width = self.frame.winfo_width()
            frame_height = self.frame.winfo_height()
            
            if frame_width <= 1 or frame_height <= 1:
                return
            
            clock_width = self.clock_canvas.winfo_width() if self.clock_canvas else 0
            clock_height = self.clock_canvas.winfo_height() if self.clock_canvas else 0
            info_width = self.info_canvas.winfo_width() if self.info_canvas else 0
            info_height = self.info_canvas.winfo_height() if self.info_canvas else 0
            
            # Evitar cálculos si no está inicializado
            if clock_width <= 1 or clock_height <= 1 or info_width <= 1 or info_height <= 1:
                return
            
            # Calcular font sizes dinámicamente
            # Reloj: 10-120pt (proporcional a altura)
            clock_font_size = min(max(10, int(clock_width * 0.1)), max(10, int(clock_height * 0.5)))
            # Texto: 8-32pt (proporcional a altura)
            info_font_size = min(max(8, int(info_width * 0.05)), max(8, int(info_height * 0.1)))
            
            # Calcular ancho de wrapping para el texto inferior
            wrap_width = max(50, int(frame_width * 0.75))
            
            # Actualizar fonts en Canvas
            if self.clock_canvas and self.clock_text_id:
                self.clock_canvas.itemconfig(
                    self.clock_text_id,
                    font=("Courier", clock_font_size, "bold")
                )
                self.clock_canvas.coords(self.clock_text_id, clock_width // 2, clock_height // 2)
            
            if self.info_canvas and self.info_text_id:
                self.info_canvas.itemconfig(
                    self.info_text_id,
                    font=("Arial", info_font_size),
                    width=wrap_width
                )
                self.info_canvas.coords(self.info_text_id, info_width // 2, info_height // 2)
                self.info_canvas.update_idletasks()
                
        except Exception as e:
            log_error(f"Error actualizando fonts: {e}")
    
    def update_clock(self):
        """Actualiza la hora en el reloj"""
        try:
            if self.clock_canvas and self.clock_text_id:
                hora_actual = dt.now().strftime("%H:%M:%S")
                self.clock_canvas.itemconfig(self.clock_text_id, text=hora_actual)
        except Exception as e:
            log_error(f"Error actualizando reloj: {e}")


    def update_date(self):
        """Actualiza la fecha en el reloj"""
        try:
            if self.clock_canvas and self.clock_text_id:
                fecha_actual = dt.now().strftime("%d/%m/%Y")
                self.clock_canvas.itemconfig(self.info_text_id, text=fecha_actual)
        except Exception as e:
            log_error(f"Error actualizando reloj: {e}")

    


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
