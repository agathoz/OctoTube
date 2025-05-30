import os
import re
import sys
import platform
from typing import Union

def sanitize_name(name: str) -> str:
    return re.sub(r'[^\w\-_\. ]', '', name)[:100].strip()

def get_os_config() -> dict:
    return {
        'windows': {'clear': 'cls', 'ffmpeg': 'ffmpeg.exe'},
        'linux': {'clear': 'clear', 'ffmpeg': 'ffmpeg'},
        'darwin': {'clear': 'clear', 'ffmpeg': 'ffmpeg'}
    }.get(platform.system().lower(), {})

def clear_screen():
    os.system(get_os_config().get('clear', 'clear'))

def create_directory(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path
