"""
debug_log.py - Sistema de logging para rastrear errores y eventos
"""
import logging
from pathlib import Path
from datetime import datetime

# Configurar logging
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

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
