"""
version_manager.py - Sistema de gestión de versiones y actualizaciones
"""
import subprocess
import json
import base64
from pathlib import Path
import sys
import os

from config import GITHUB_REPO, GITHUB_UPDATE_BRANCH, CONFIG_FILE_NAME, API_TIMEOUT, PYTHON_TIMEOUT


def get_local_version():
    """Obtiene la versión local del archivo VERSION"""
    try:
        version_path = Path(__file__).parent / "VERSION"
        with open(version_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except (FileNotFoundError, OSError):
        return "1.0.0"


def get_github_token():
    """Obtiene el token de GitHub desde app_config.json"""
    try:
        config_path = Path(__file__).with_name(CONFIG_FILE_NAME)
        with open(config_path, "r", encoding="utf-8") as config_file:
            config = json.load(config_file)
            return config.get("github_token")
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def get_latest_github_version():
    """Obtiene la última versión del repositorio GitHub usando token de app_config.json"""
    try:
        # Usar API de GitHub para obtener el contenido del archivo VERSION
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/VERSION?ref={GITHUB_UPDATE_BRANCH}"
        print(f"[DEBUG] Obteniendo versión remota de: {url}")
        
        # Preparar comando curl con autenticación si está disponible
        token = get_github_token()
        curl_cmd = ['curl', '-X', 'GET', '--max-time', str(API_TIMEOUT)]
        
        if token:
            # Usar autenticación Bearer para repositorio privado
            curl_cmd.extend(['-H', f'Authorization: Bearer {token}'])
            print("[DEBUG] Token de GitHub encontrado")
        else:
            print("[DEBUG] Sin token de GitHub")
        
        curl_cmd.extend([url])
        
        result = subprocess.run(
            curl_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=PYTHON_TIMEOUT
        )
        if result.returncode != 0:
            print(f"[DEBUG] Error curl: {result.returncode}")
            print(f"[DEBUG] stderr: {result.stderr.decode('utf-8')}")
            return None
        data = json.loads(result.stdout.decode('utf-8'))
        # El contenido está en base64 en la API de GitHub
        version = base64.b64decode(data['content']).decode('utf-8').strip()
        print(f"[DEBUG] Versión remota obtenida: {version}")
        return version
    except Exception as e:
        print(f"[DEBUG] Excepción en get_latest_github_version: {str(e)}")
        return None


def check_for_updates():
    """Comprueba si hay actualizaciones disponibles en GitHub"""
    local_version = get_local_version()
    print(f"[DEBUG] Versión local: {local_version}")
    github_version = get_latest_github_version()
    print(f"[DEBUG] Versión GitHub: {github_version}")
    
    if github_version is None:
        print("[DEBUG] GitHub version es None, sin actualizaciones disponibles")
        return False, None, None
    
    # Comparar versiones (formato semántico: X.Y.Z)
    try:
        local_parts = [int(x) for x in local_version.split('.')]
        github_parts = [int(x) for x in github_version.split('.')]
        print(f"[DEBUG] Partes locales: {local_parts}, Partes GitHub: {github_parts}")
        
        # Rellenar con ceros si es necesario
        while len(local_parts) < len(github_parts):
            local_parts.append(0)
        while len(github_parts) < len(local_parts):
            github_parts.append(0)
        
        if github_parts > local_parts:
            print(f"[DEBUG] Actualización disponible: {local_version} < {github_version}")
            return True, local_version, github_version
        else:
            print(f"[DEBUG] No hay actualización: {github_version} <= {local_version}")
    except (ValueError, AttributeError) as e:
        print(f"[DEBUG] Error comparando versiones: {str(e)}")
        return False, None, None
    
    return False, local_version, github_version


def perform_update():
    """Realiza la actualización sincronizándose con la rama remota"""
    try:
        project_dir = Path(__file__).parent
        
        print("⏳ Ejecutando git fetch origin...")
        fetch_result = subprocess.run(
            ['git', 'fetch', 'origin'],
            cwd=project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15
        )
        
        if fetch_result.returncode != 0:
            print(f"✗ Error en git fetch: {fetch_result.stderr.decode('utf-8')}")
            return False
        
        print(f"⏳ Sincronizando con origin/{GITHUB_UPDATE_BRANCH}...")
        reset_result = subprocess.run(
            ['git', 'reset', '--hard', f'origin/{GITHUB_UPDATE_BRANCH}'],
            cwd=project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        
        if reset_result.returncode == 0:
            print("✓ Actualización completada exitosamente")
            return True
        else:
            print(f"✗ Error en git reset: {reset_result.stderr.decode('utf-8')}")
            return False
    except subprocess.TimeoutExpired:
        print("✗ Timeout durante la actualización (>15s)")
        return False
    except Exception as e:
        print(f"✗ Error durante la actualización: {str(e)}")
        return False


def restart_application():
    """Reinicia la aplicación después de actualizar"""
    try:
        # Reiniciar el script Python
        python_executable = sys.executable
        script_path = Path(__file__).parent / "AppTkinter.py"
        os.execvp(python_executable, [python_executable, str(script_path)])
    except Exception as e:
        print(f"Error al reiniciar: {str(e)}")


def check_and_update_on_startup(app_root=None):
    """Verifica y actualiza en el inicio si hay una versión más nueva"""
    print("\n" + "="*60)
    print("Verificando actualizaciones...")
    print("="*60)
    has_updates, local_ver, github_ver = check_for_updates()
    if has_updates:
        print(f"\n📦 Actualización encontrada: {local_ver} → {github_ver}")
        print("⏳ Actualizando aplicación...\n")
        
        if perform_update():
            print("\n✓ Actualización completada, reiniciando...\n")
            import time
            time.sleep(1)
            restart_application()
        else:
            print("✗ Error durante la actualización, continuando con versión actual")
    else:
        print("\n✓ Aplicación ya está actualizada")
        print("="*60 + "\n")
