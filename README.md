## Puesta en funcionamiento
El proyecto depende de tener una api [api-auvasa](https://www.auvasa.es/datos-abiertos/) disponible a la que consultar. Durante el desarrollo se hizo con una ejecucion local en [docker](https://github.com/VallaBus/api-auvasa?tab=readme-ov-file#despliegue-en-producci%C3%B3n), aunque en app_config.json se puede esoger de donde se quieren recoger estos datos, usando por defecto [https://gtfs.vallabus.com](https://gtfs.vallabus.com).

La parada y las líneas a consultar al igual que la parada de bikis se configuran en `app_config.json`:

```json
{
	"parada_actual": "625",
	"lineas_a_probar": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "C1", "C2", "H"]
}
```

`parada_actual` es el código de parada (puedes consultarlo en [el mapa oficial de auvasa](https://www.auvasa.es/mapa-de-servicios/)).

Este sistema esta pensado para ser ejecutado en un entorno tipo kiosko, especificamente una raspberry con pantalla táctil, aunque funciona tambien como aplicacion python normal, seria preferente cambiar partes del código que se encargan de forzar la pantalla completa sin bordes, y que todavia no estan añadidas al archivo de configuración.

# Sistema de Vistas Modular - Guía de Uso

El sistema de vistas proporciona una arquitectura escalable y fácil de mantener para manejar múltiples vistas en la aplicación.

## Arquitectura

### Componentes Principales

1. **`View` (Clase Base Abstracta)**
   - Define la interfaz que todas las vistas deben implementar
   - Métodos: `_setup_frame()`, `show()`, `hide()`, `is_visible()`
   - Atributos: `root`, `name`, `frame`

2. **`ViewManager` (Singleton)**
   - Gestor central de vistas
   - Maneja transiciones entre vistas
   - Ejecuta callbacks de actualización cada segundo
   - Una única instancia en toda la aplicación

3. **Vistas Específicas**
   - `MainView`: Vista principal de la aplicación
   - `LockscreenView`: Lockscreen con reloj (con redimensionamiento dinámico)

### LockscreenView - Características Especiales

La `LockscreenView` incluye redimensionamiento dinámico de textos con límites seguros:

**Font Sizes**
- **Reloj**: `min(120, max(10, altura_ventana * 0.12))` pt
- **Texto desbloquear**: `min(32, max(8, altura_ventana * 0.04))` pt

**Rangos de Font**
- Reloj: 10-120 pt (escalable, pero con límite máximo)
- Texto: 8-32 pt (escalable, pero con límite máximo)

**Text Wrapping**
- El texto de desbloquear se ajusta automáticamente a 80% del ancho de la ventana
- Mínimo 200px para activar wrapping

**Padding Dinámico**
- Se recalcula como `max(10, altura_ventana * 0.08)` px

**Actualización Automática**
- Los fonts se recalculan cada vez que la ventana cambia de tamaño (evento `<Configure>`)
- También se actualizan cuando se muestra la vista (150ms después)

## Cómo Agregar una Nueva Vista

### Paso 1: Crear una Nueva Clase Vista

```python
from views import View, ViewManager

class MiNuevaVista(View):
    """Descripción de la nueva vista"""
    
    def __init__(self, root):
        super().__init__(root, 'mi_vista')  # 'mi_vista' es el identificador
    
    def _setup_frame(self):
        """Crea y configura el frame de la vista"""
        try:
            self.frame = tk.Frame(self.root, bg='#ffffff')
            self.frame.grid(column=0, row=0, columnspan=2, rowspan=2, 
                          sticky=(tk.N, tk.S, tk.E, tk.W))
            self.frame.grid_remove()  # Inicialmente oculta
            
            # Agregar widgets aquí
            label = tk.Label(self.frame, text="Mi Nueva Vista")
            label.pack()
            
            # Agregar binding para cambiar de vista
            label.bind("<Button-1>", lambda e: 
                      ViewManager.get_instance().switch_view('main'))
            
        except Exception as e:
            log_error(f"Error configurando mi_vista: {e}")
    
    def actualizar(self):
        """Método opcional para actualizar la vista cada segundo"""
        # Este método será llamado automáticamente cada segundo
        # si lo registras como callback
        pass
```

### Paso 2: Registrar la Vista en `main()`

```python
def main():
    global view_manager
    
    # ... código existente ...
    
    # Inicializar ViewManager
    view_manager = ViewManager.initialize(root)
    
    # Crear vistas
    main_view = MainView(root, main_frame, empty_frame, secondary_frame)
    lockscreen_view = LockscreenView(root)
    mi_nueva_vista = MiNuevaVista(root)  # ← Nueva vista
    
    # Registrar vistas
    view_manager.register_view(main_view)
    view_manager.register_view(lockscreen_view)
    view_manager.register_view(mi_nueva_vista)  # ← Registrar
    
    # Registrar callbacks de actualización (opcional)
    view_manager.register_update_callback(lockscreen_view.update_clock)
    view_manager.register_update_callback(mi_nueva_vista.actualizar)  # ← Si tiene
    
    # Establecer vista inicial
    view_manager.set_initial_view('main')
```

### Paso 3: Cambiar de Vista

```python
# En cualquier lugar del código donde haya un evento o botón:
ViewManager.get_instance().switch_view('mi_vista')
```

## Ejemplo Completo: Vista de Configuración

```python
class SettingsView(View):
    """Vista de configuración de la aplicación"""
    
    def __init__(self, root):
        super().__init__(root, 'settings')
    
    def _setup_frame(self):
        try:
            self.frame = tk.Frame(self.root, bg='#f0f0f0')
            self.frame.grid(column=0, row=0, columnspan=2, rowspan=2, 
                          sticky=(tk.N, tk.S, tk.E, tk.W))
            self.frame.grid_remove()
            
            # Título
            title = tk.Label(self.frame, text="Configuración", 
                           font=("Arial", 24, "bold"))
            title.pack(pady=20)
            
            # Opción 1
            option1 = tk.Button(self.frame, text="Opción 1",
                              command=lambda: self._on_option1())
            option1.pack(pady=10)
            
            # Botón Atrás
            back_btn = tk.Button(self.frame, text="← Volver",
                               command=lambda: self._go_back())
            back_btn.pack(pady=10)
            
        except Exception as e:
            log_error(f"Error en SettingsView: {e}")
    
    def _on_option1(self):
        log_info("Opción 1 seleccionada")
    
    def _go_back(self):
        ViewManager.get_instance().switch_view('main')
```

## Sistema de Callbacks

Los callbacks se ejecutan cada segundo para actualizar contenido dinámico:

```python
# En la definición de tu vista:
class MiVista(View):
    def actualizar(self):
        """Llamado cada segundo automáticamente"""
        # Actualizar widgets dinámicos
        self.label.config(text=f"Hora: {datetime.now().strftime('%H:%M:%S')}")

# En main():
view_manager.register_update_callback(mi_vista.actualizar)
```

## Referencia Rápida

```python
# Obtener instancia del ViewManager
view_manager = ViewManager.get_instance()

# Cambiar de vista
view_manager.switch_view('lockscreen')

# Registrar nueva vista
view_manager.register_view(mi_vista)

# Registrar callback de actualización
view_manager.register_update_callback(mi_vista.actualizar)

# Obtener vista actual
current_view = view_manager.current_view
```

## Flujo de Transición

```
[MainView] 
    ↓ click
[LockscreenView] 
    ↓ click
[MainView]
    ↓ ...
```

Para agregar una nueva vista:

```
[MainView] ←→ [LockscreenView]
    ↓ click
[SettingsView]
    ↓ click
[MainView]
```

---

El sistema está diseñado para ser extensible. Puedes agregar tantas vistas como necesites sin modificar el código base.
