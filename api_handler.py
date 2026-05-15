"""
api_handler.py - Manejador de APIs para datos de autobuses y bikis
"""
import subprocess
import json
import datetime
from config import SERVER_URL, API_TIMEOUT, PYTHON_TIMEOUT, STRING_NO_HAY_MAS_BUSES, STRING_ERROR

# Intentar importar debug_log, si falla usar print
try:
    from debug_log import log_error, log_info
except ImportError:
    def log_error(msg):
        print(f"[ERROR] {msg}")
    def log_info(msg):
        print(f"[INFO] {msg}")


# ============================================================================
# EXCEPCIONES PERSONALIZADAS
# ============================================================================

class LineaNoPasaPorParadaError(Exception):
    """Excepción cuando una línea no pasa por una parada"""
    pass


# ============================================================================
# FUNCIONES DE API
# ============================================================================

def fetch_api(url):
    """Realiza petición HTTP con timeout"""
    try:
        result = subprocess.run(
            ['curl', '-X', 'GET', '--max-time', str(API_TIMEOUT), url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=PYTHON_TIMEOUT
        )
        if result.returncode != 0:
            raise Exception("Error en petición curl")
        return json.loads(result.stdout.decode('utf-8'))
    except (json.JSONDecodeError, subprocess.TimeoutExpired, Exception) as e:
        raise Exception(f"Error al obtener datos: {str(e)}")


def fetch_bus_arrival_time(parada, linea):
    """Obtiene tiempo restante del próximo autobús"""
    url = f'{SERVER_URL}/parada/{parada}/{linea}/{datetime.datetime.now().strftime("%Y%m%d")}'
    try:
        result_json = fetch_api(url)
    except Exception as e:
        log_error(f"Error obteniendo tiempo para línea {linea}: {e}")
        return STRING_ERROR

    if not result_json.get('lineas') or len(result_json['lineas']) == 0:
        raise LineaNoPasaPorParadaError("La linea no pasa por esta parada")

    horarios = result_json['lineas'][0].get('horarios', [])
    for horario in horarios:
        tiempo = horario.get('tiempoRestante', -1)
        if tiempo >= 0:
            return str(tiempo)

    return STRING_NO_HAY_MAS_BUSES


def format_bus_time(parada, linea):
    """Obtiene tiempo formateado (h' min\" para >59 mins)"""
    tiempo = fetch_bus_arrival_time(parada, linea)
    if tiempo == STRING_NO_HAY_MAS_BUSES or tiempo == STRING_ERROR:
        return tiempo

    minutos = int(tiempo)
    if minutos > 59:
        horas = minutos // 60
        mins = minutos % 60
        return f"{horas}' {mins}\"" 
    return f"{minutos}\""


def fetch_bike_availability(parada):
    """Obtiene cantidad de bikis FIT y EFIT disponibles en una estación específica"""
    url = f'{SERVER_URL}/gbfs/paradas'
    try:
        result_json = fetch_api(url)
        
        # Buscar la estación que coincida con el parámetro parada
        if isinstance(result_json, list) and len(result_json) > 0:
            station = None
            
            # Buscar por station_id, short_name u obcn
            for st in result_json:
                if (str(st.get('station_id')) == str(parada) or 
                    str(st.get('short_name')) == str(parada)):
                    station = st
                    break
            
            if not station:
                # Si no encuentra coincidencia, usar la primera (fallback)
                station = result_json[0]
            
            station_name = station.get('name', 'Estación desconocida')
            vehicle_types = station.get('vehicle_types_available', [])
            
            fit_count = 0
            efit_count = 0
            
            for vehicle in vehicle_types:
                if vehicle.get('vehicle_type_id') == 'FIT':
                    fit_count = vehicle.get('count', 0)
                elif vehicle.get('vehicle_type_id') == 'EFIT':
                    efit_count = vehicle.get('count', 0)
            
            return {'name': station_name, 'FIT': fit_count, 'EFIT': efit_count}
        else:
            return {'name': 'Estación desconocida', 'FIT': 0, 'EFIT': 0}
    except Exception as e:
        log_error(f"Error obteniendo cantidad de bikis: {e}")
        return {'name': 'Error cargando estación', 'FIT': 0, 'EFIT': 0}


def get_parada_name(parada):
    """Obtiene el nombre de una parada desde la API"""
    try:
        result_json = fetch_api(f'{SERVER_URL}/parada/{parada}')
        nombre = result_json.get('parada', [{}])[0].get('parada', 'Parada desconocida')
        return nombre
    except Exception as e:
        log_error(f"Error obteniendo nombre de parada: {e}")
        return "Parada desconocida"
