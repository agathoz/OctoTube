class Config:
    CLI_STYLES = {
        'title': '\033[1;35m',    # Magenta/Lila
        'dollar': '\033[1;36m',   # Cian
        'option': '\033[1;33m',   # Amarillo
        'success': '\033[1;32m',  # Verde
        'error': '\033[1;31m',    # Rojo
        'warning': '\033[1;33m',  # Amarillo
        'info': '\033[1;34m',     # Azul
        'reset': '\033[0m'        # Reset
    }
    
    THUMBNAIL_QUALITIES = ['maxresdefault', 'sddefault', 'hqdefault']
    MAX_WORKERS = 4
    AUDIO_QUALITY = 'highest'
    VIDEO_QUALITY = 'highest'