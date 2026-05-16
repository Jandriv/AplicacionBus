"""
debug_log.py - Sistema de logging para rastrear errores y eventos
"""
import logging
from pathlib import Path
from datetime import datetime

# Configurar logging
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

def _cleanup_old_logs():
    """Elimina los logs más antiguos si hay más de 10 archivos"""
    log_files = sorted(LOG_DIR.glob("app_*.log"))
    
    # Si hay más de 10 logs, eliminar los más antiguos
    while len(log_files) > 9:
        oldest = log_files[0]
        try:
            oldest.unlink()
            log_files.pop(0)
        except Exception as e:
            print(f"Error al eliminar log antiguo {oldest}: {e}")

LOG_FILE = LOG_DIR / f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Limpiar logs antiguos después de crear el nuevo
_cleanup_old_logs()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        #logging.StreamHandler() # Descomentar para ver logs en consola
    ]
)

logger = logging.getLogger(__name__)

def log_error(message):
    """Registra un error"""
    logger.error(message)

def log_warning(message):
    """Registra un warning"""
    logger.warning(message)

def log_info(message):
    """Registra información"""
    logger.info(message)

def log_debug(message):
    """Registra debug"""
    logger.debug(message)

if __name__ == "__main__":
    log_info("Sistema de logging inicializado")
    print(f"Log guardado en: {LOG_FILE}")
