"""
version_manager.py - Sistema de gestión de versiones y actualizaciones
"""
import subprocess
import json
import base64
from pathlib import Path
import sys
import os

from config import GITHUB_REPO, GITHUB_UPDATE_BRANCH, API_TIMEOUT, PYTHON_TIMEOUT

# Intentar importar debug_log, si falla usar print
try:
    from debug_log import log_error, log_info
except ImportError:
    def log_error(msg):
        print(f"[ERROR] {msg}")
    def log_info(msg):
        print(f"[INFO] {msg}")


def get_local_version():
    """Obtiene la versión local del archivo VERSION"""
    try:
        version_path = Path(__file__).parent / "VERSION"
        with open(version_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except (FileNotFoundError, OSError):
        return "1.0.0"


def get_latest_github_version():
    """Obtiene la última versión de un repositorio público de GitHub."""
    try:
        # Usar API de GitHub para obtener el contenido del archivo VERSION
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/VERSION?ref={GITHUB_UPDATE_BRANCH}"
        log_info(f"Obteniendo versión remota de: {url}")
        
        curl_cmd = ['curl', '-X', 'GET', '--max-time', str(API_TIMEOUT)]
        curl_cmd.extend([url])
        
        result = subprocess.run(
            curl_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=PYTHON_TIMEOUT
        )
        if result.returncode != 0:
            log_error(f"Error curl: {result.returncode}")
            log_error(f"stderr: {result.stderr.decode('utf-8')}")
            return None
        data = json.loads(result.stdout.decode('utf-8'))
        # El contenido está en base64 en la API de GitHub
        version = base64.b64decode(data['content']).decode('utf-8').strip()
        return version
    except Exception as e:
        log_error(f"Excepción en get_latest_github_version: {str(e)}")
        return None


def check_for_updates():
    """Comprueba si hay actualizaciones disponibles en GitHub"""
    local_version = get_local_version()
    github_version = get_latest_github_version()
    
    if github_version is None:
        return False, None, None
    
    # Comparar versiones (formato semántico: X.Y.Z)
    try:
        local_parts = [int(x) for x in local_version.split('.')]
        github_parts = [int(x) for x in github_version.split('.')]
        log_info(f"Partes locales: {local_parts}, Partes GitHub: {github_parts}")
        
        # Rellenar con ceros si es necesario
        while len(local_parts) < len(github_parts):
            local_parts.append(0)
        while len(github_parts) < len(local_parts):
            github_parts.append(0)
        
        if github_parts > local_parts:
            log_info(f"Actualización disponible: {local_version} < {github_version}")
            return True, local_version, github_version
        else:
            log_info(f"No hay actualización: {github_version} <= {local_version}")
    except (ValueError, AttributeError) as e:
        log_error(f"Error comparando versiones: {str(e)}")
        return False, None, None
    
    return False, local_version, github_version


def perform_update():
    """Realiza la actualización sincronizándose con la rama remota"""
    try:
        project_dir = Path(__file__).parent
        
        fetch_result = subprocess.run(
            ['git', 'fetch', 'origin'],
            cwd=project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15
        )
        
        if fetch_result.returncode != 0:
            log_error(f"Error en git fetch: {fetch_result.stderr.decode('utf-8')}")
            return False
        
        reset_result = subprocess.run(
            ['git', 'reset', '--hard', f'origin/{GITHUB_UPDATE_BRANCH}'],
            cwd=project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        
        if reset_result.returncode == 0:
            return True
        else:
            return False
    except subprocess.TimeoutExpired:
        log_error("Timeout durante la actualización (>15s)")
        return False
    except Exception as e:
        log_error(f"Error durante la actualización: {str(e)}")
        return False


def restart_application():
    """Reinicia la aplicación después de actualizar"""
    try:
        # Reiniciar el script Python
        python_executable = sys.executable
        script_path = Path(__file__).parent / "AppTkinter.py"
        os.execvp(python_executable, [python_executable, str(script_path)])
    except Exception as e:
        log_error(f"Error al reiniciar: {str(e)}")


def check_and_update_on_startup(app_root=None):
    """Verifica y actualiza en el inicio si hay una versión más nueva"""
    has_updates, local_ver, github_ver = check_for_updates()
    if has_updates:
        log_info(f"Actualización encontrada: {local_ver} → {github_ver}")
        if perform_update():
            log_info("Actualización completada, reiniciando...")
            import time
            time.sleep(1)
            restart_application()
        else:
            log_error("Error durante la actualización, continuando con versión actual")
    else:
        log_info("Aplicación ya está actualizada")
