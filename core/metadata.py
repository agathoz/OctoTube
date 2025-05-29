from mutagen.id3 import ID3, APIC, TIT2, TPE1
from mutagen.mp4 import MP4, MP4Cover
import os
from pytube import YouTube

def add_metadata(file_path: str, metadata: dict, thumb_path: str):
    """Añade metadatos a archivos multimedia"""
    try:
        if file_path.endswith('.mp3'):
            audio = ID3()
            audio.add(TIT2(encoding=3, text=metadata['title']))
            audio.add(TPE1(encoding=3, text=metadata['artist']))
            
            if thumb_path and os.path.exists(thumb_path):
                with open(thumb_path, 'rb') as f:
                    audio.add(APIC(
                        encoding=3,
                        mime='image/jpeg',
                        type=3,  # 3 = cover(front)
                        desc='Cover',
                        data=f.read()
                    ))
            audio.save(file_path)
        
        elif file_path.endswith('.mp4'):
            video = MP4(file_path)
            video['\xa9nam'] = metadata['title']
            video['\xa9ART'] = metadata['artist']
            
            if os.path.exists(thumb_path):
                with open(thumb_path, 'rb') as f:
                    video['covr'] = [MP4Cover(f.read(), imageformat=MP4Cover.FORMAT_JPEG)]
            video.save()
        
        elif file_path.endswith('.wav'):
            # WAV: metadatos limitados, puedes usar mutagen.wave pero es muy básico
            pass
        
        elif file_path.endswith('.mkv'):
            # MKV: metadatos limitados, puedes usar mkvpropedit si está instalado
            import subprocess
            subprocess.run([
                "mkvpropedit", file_path,
                "--edit", "info",
                "--set", f"title={metadata['title']}"
            ], check=False)
    except Exception as e:
        print(f"Error añadiendo metadatos: {e}")

# Ejemplo de barra de progreso para pytube
def progress_func(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percent = int(bytes_downloaded / total_size * 100)
    bar = '#' * (percent // 2) + '-' * (50 - percent // 2)
    print(f"\rDescargando: [{bar}] {percent}%", end='')

def download_video(url, output_path='.'):
    try:
        yt = YouTube(url, on_progress_callback=progress_func)
        stream = yt.streams.filter(file_extension='mp4').first()
        if stream:
            print(f"\nDescargando video: {yt.title}")
            stream.download(output_path)
            print("\nDescarga completada.")
        else:
            print("No se encontró un stream adecuado para descargar.")
    except Exception as e:
        print(f"Error descargando el video: {e}")