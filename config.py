"""
config.py - Configuración centralizada de la aplicación
"""
import json
from pathlib import Path
import sys
# Intentar importar debug_log, si falla usar print
try:
    from debug_log import log_error, log_info
except ImportError:
    def log_error(msg):
        print(f"[ERROR] {msg}", file=sys.stderr)
    def log_info(msg):
        print(f"[INFO] {msg}")

# ============================================================================
# CONFIGURACIÓN DE ARCHIVOS
# ============================================================================

CONFIG_FILE_NAME = "app_config.json"

# ============================================================================
# CONFIGURACIÓN DE PARADAS Y LÍNEAS
# ============================================================================

DEFAULT_PARADA_ACTUAL = "625"
DEFAULT_LINEAS_A_PROBAR = [str(numero) for numero in range(1, 11)] + ["C1", "C2", "H"]
DEFAULT_PARADA_BIKI_ACTUAL = "686"

# ============================================================================
# CONFIGURACIÓN DE API
# ============================================================================

SERVER_URL = "https://gtfs.vallabus.com"
API_TIMEOUT = 5
PYTHON_TIMEOUT = 6
STRING_NO_HAY_MAS_BUSES = "No hay mas buses hoy"
STRING_ERROR = "Error obteniendo datos"

# ============================================================================
# CONFIGURACIÓN DE INTERFAZ
# ============================================================================
BRIGHTNESS = 100  # Valor de brillo por defecto (0-100)
THEME = "dark"  # Tema por defecto ("light" o "dark")

REFRESH_MS = 5000  # 5 segundos
DEFAULT_SCROLL_SPEED = 4
DEFAULT_MAX_SCROLL_SPEED = 2  # Cap máximo de velocidad acumulada (proporciones)

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
# CONFIGURACIÓN DE ACTUALIZACIONES (GITHUB)
# ============================================================================

GITHUB_REPO = "Jandriv/AplicacionBus"  # Propietario/Repositorio
GITHUB_UPDATE_BRANCH = "main"  # Rama desde la que actualizar

# ============================================================================
# CARGA DE CONFIGURACIÓN DINÁMICA
# ============================================================================

def _default_config():
    return {
        "parada_actual": DEFAULT_PARADA_ACTUAL,
        "parada_biki_actual": DEFAULT_PARADA_BIKI_ACTUAL,
        "lineas_a_probar": list(DEFAULT_LINEAS_A_PROBAR),
        "scroll_speed": DEFAULT_SCROLL_SPEED,
        "max_scroll_speed": DEFAULT_MAX_SCROLL_SPEED,
        "server_url": SERVER_URL,
        "brightness": BRIGHTNESS,
        "theme": THEME,
    }


def load_config():
    """Carga, crea y completa la configuración con valores por defecto."""
    config_path = Path(__file__).with_name(CONFIG_FILE_NAME)
    default_config = _default_config()

    try:
        with open(config_path, "r", encoding="utf-8") as config_file:
            log_info(f"Cargando configuración desde {config_path}.")
            config = json.load(config_file)

        if not isinstance(config, dict):
            config = {}

    except (FileNotFoundError, json.JSONDecodeError, OSError):
        log_info(f"Archivo de configuración no encontrado o inválido. Creando uno nuevo en {config_path}.")
        config = {}

    # Completar las claves que falten
    config_updated = False
    for key, value in default_config.items():
        if key not in config:
            config[key] = value
            config_updated = True

    # Crear o actualizar el archivo de configuración
    if config_updated or not config_path.exists():
        try:
            with open(config_path, "w", encoding="utf-8") as config_file:
                log_info(f"Guardando configuración en {config_path}.")
                json.dump(config, config_file, indent=4, ensure_ascii=False)
        except OSError:
            log_error(f"No se pudo guardar la configuración en {config_path}.")
            pass

    parada_actual = str(config["parada_actual"])

    lineas_config = config["lineas_a_probar"]
    if not isinstance(lineas_config, list) or not lineas_config:
        lineas_a_probar = list(DEFAULT_LINEAS_A_PROBAR)
        config["lineas_a_probar"] = lineas_a_probar
    else:
        lineas_a_probar = [str(linea) for linea in lineas_config]

    scroll_speed = float(config["scroll_speed"]) / 1000
    max_scroll_speed = float(config["max_scroll_speed"]) / 1000
    server_url = str(config["server_url"])
    parada_biki = str(config["parada_biki_actual"])
    print(f"Configuración cargada: parada_actual={parada_actual}, lineas_a_probar={lineas_a_probar}, scroll_speed={scroll_speed}, max_scroll_speed={max_scroll_speed}, server_url={server_url}, parada_biki={parada_biki}")

    return (
        parada_actual,
        lineas_a_probar,
        scroll_speed,
        max_scroll_speed,
        server_url,
        parada_biki,
    )


# Cargar configuración al importar
PARADA_ACTUAL, LINEAS_A_PROBAR, SCROLL_SPEED, MAX_SCROLL_SPEED, SERVER_URL, PARADA_BIKI_ACTUAL = load_config()