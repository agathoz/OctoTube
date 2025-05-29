import os
import re
import sys
import platform
from typing import Union

def sanitize_name(name: str) -> str:
    """Limpia caracteres inválidos para nombres de archivo"""
    return re.sub(r'[^\w\-_\. ]', '', name)[:100].strip()

def get_os_config() -> dict:
    """Obtiene configuración específica del SO"""
    return {
        'windows': {'clear': 'cls', 'ffmpeg': 'ffmpeg.exe'},
        'linux': {'clear': 'clear', 'ffmpeg': 'ffmpeg'},
        'darwin': {'clear': 'clear', 'ffmpeg': 'ffmpeg'}
    }.get(platform.system().lower(), {})

def clear_screen():
    """Limpia la pantalla según el SO"""
    os.system(get_os_config().get('clear', 'clear'))

def create_directory(path: str) -> str:
    """Crea un directorio si no existe y retorna la ruta"""
    os.makedirs(path, exist_ok=True)
    return path