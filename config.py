"""
config.py - Configuración centralizada de la aplicación
"""
import json
from pathlib import Path

# ============================================================================
# CONFIGURACIÓN DE ARCHIVOS
# ============================================================================

CONFIG_FILE_NAME = "app_config.json"

# ============================================================================
# CONFIGURACIÓN DE PARADAS Y LÍNEAS
# ============================================================================

DEFAULT_PARADA_ACTUAL = "625"
DEFAULT_LINEAS_A_PROBAR = [str(numero) for numero in range(1, 10)] + ["C1", "C2", "H"]
DEFAULT_PARADA_BIKI_ACTUAL = "686"

# ============================================================================
# CONFIGURACIÓN DE API
# ============================================================================

SERVER_URL = "https://gtf.vallabus.com"
API_TIMEOUT = 5
PYTHON_TIMEOUT = 6
STRING_NO_HAY_MAS_BUSES = "No hay mas buses hoy"
STRING_ERROR = "Error obteniendo datos"

# ============================================================================
# CONFIGURACIÓN DE INTERFAZ
# ============================================================================

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

def load_config():
    """Carga la configuración desde archivo JSON o valores por defecto"""
    config_path = Path(__file__).with_name(CONFIG_FILE_NAME)

    try:
        with open(config_path, "r", encoding="utf-8") as config_file:
            config = json.load(config_file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return (DEFAULT_PARADA_ACTUAL, list(DEFAULT_LINEAS_A_PROBAR), 
                DEFAULT_SCROLL_SPEED, DEFAULT_MAX_SCROLL_SPEED, 
                SERVER_URL, DEFAULT_PARADA_BIKI_ACTUAL)

    parada_actual = str(config.get("parada_actual", DEFAULT_PARADA_ACTUAL))
    lineas_config = config.get("lineas_a_probar", DEFAULT_LINEAS_A_PROBAR)
    scroll_speed = float(config.get("scroll_speed", DEFAULT_SCROLL_SPEED))
    max_scroll_speed = float(config.get("max_scroll_speed", DEFAULT_MAX_SCROLL_SPEED))
    server_url = config.get("server_url", SERVER_URL)
    parada_biki = config.get("parada_biki_actual", DEFAULT_PARADA_BIKI_ACTUAL)

    if not isinstance(lineas_config, list) or len(lineas_config) == 0:
        lineas_a_probar = list(DEFAULT_LINEAS_A_PROBAR)
    else:
        lineas_a_probar = [str(linea) for linea in lineas_config]

    return parada_actual, lineas_a_probar, scroll_speed/1000, max_scroll_speed/1000, server_url, parada_biki

# Cargar configuración al importar
PARADA_ACTUAL, LINEAS_A_PROBAR, SCROLL_SPEED, MAX_SCROLL_SPEED, SERVER_URL, PARADA_BIKI_ACTUAL = load_config()
