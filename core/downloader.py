from pytubefix import YouTube, Playlist
from pytubefix.exceptions import VideoUnavailable
import requests
import os
from core.config import Config
from core import utils

def get_content(url: str) -> dict:
    try:
        if "list=" in url:
            playlist = Playlist(url)
            return {
                'type': 'playlist',
                'title': utils.sanitize_name(playlist.title),
                'videos': playlist.videos
            }
        else:
            video = YouTube(url)
            return {
                'type': 'video',
                'title': utils.sanitize_name(video.title),
                'videos': [video]
            }
    except Exception as e:
        return {
            'type': 'error',
            'message': f"No se pudo obtener contenido: {str(e)}",
            'videos': []
        }

def download_thumbnail(url: str, path: str) -> bool:
    for quality in Config.THUMBNAIL_QUALITIES:
        thumb_url = url
        for q in Config.THUMBNAIL_QUALITIES:
            if q in thumb_url:
                thumb_url = thumb_url.replace(q, quality)
        try:
            response = requests.get(thumb_url, stream=True, timeout=10)
            if response.status_code == 200:
                with open(path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
        except Exception:
            continue
    return False

def process_video(video, options: dict) -> dict:
    try:
        title = utils.sanitize_name(video.title)
        output_dir = options['output_dir']
        media_type = options['media_type']
        verbose = options.get('verbose', True)
        quality = options.get('quality')

        # Extensión según tipo
        ext = media_type
        filename = f"{title}.{ext}"
        file_path = os.path.join(output_dir, filename)
        download_thumb = options.get('download_thumb', True)
        thumb_path = os.path.join(output_dir, f"{title}.jpg")
        if download_thumb:
            download_thumbnail(video.thumbnail_url, thumb_path)
        else:
            thumb_path = None  # No se usará

        # Descargar contenido
        if media_type == 'mp3':
            stream = video.streams.get_audio_only()
            if not stream:
                return {'status': 'error', 'title': title, 'message': "No se encontró stream de audio"}
            temp_file = stream.download(output_path=output_dir, filename=title + ".mp4")
            # Convertir a mp3
            import subprocess
            subprocess.run([
                "ffmpeg", "-y", "-i", temp_file, "-vn", "-ab", "192k", "-ar", "44100", "-f", "mp3", file_path
            ], check=True)
            os.remove(temp_file)
        elif media_type == 'wav':
            stream = video.streams.get_audio_only()
            if not stream:
                return {'status': 'error', 'title': title, 'message': "No se encontró stream de audio"}
            temp_file = stream.download(output_path=output_dir, filename=title + ".mp4")
            import subprocess
            subprocess.run([
                "ffmpeg", "-y", "-i", temp_file, "-vn", "-ar", "44100", "-ac", "2", "-f", "wav", file_path
            ], check=True)
            os.remove(temp_file)
        elif media_type == 'mp4':
            # Elegir calidad
            if quality:
                stream = video.streams.filter(progressive=True, file_extension="mp4", resolution=quality).first()
            else:
                stream = video.streams.get_highest_resolution()
            if not stream:
                return {'status': 'error', 'title': title, 'message': "No se encontró stream de video"}
            file_path = stream.download(output_path=output_dir, filename=filename)
        elif media_type == 'mkv':
            # Descargar mejor calidad de audio y video por separado y unirlos
            video_stream = video.streams.filter(adaptive=True, only_video=True).order_by('resolution').desc().first()
            audio_stream = video.streams.filter(adaptive=True, only_audio=True).order_by('abr').desc().first()
            if not video_stream or not audio_stream:
                return {'status': 'error', 'title': title, 'message': "No se encontró stream de video/audio"}
            temp_video = os.path.join(output_dir, title + "_video.mp4")
            temp_audio = os.path.join(output_dir, title + "_audio.mp4")
            video_stream.download(output_path=output_dir, filename=title + "_video.mp4")
            audio_stream.download(output_path=output_dir, filename=title + "_audio.mp4")
            import subprocess
            subprocess.run([
                "ffmpeg", "-y", "-i", temp_video, "-i", temp_audio, "-c", "copy", file_path
            ], check=True)
            os.remove(temp_video)
            os.remove(temp_audio)

        from core.metadata import add_metadata
        add_metadata(file_path, {'title': title, 'artist': video.author}, thumb_path)

        return {'status': 'success', 'title': title}
    except Exception as e:
        return {'status': 'error', 'title': title, 'message': str(e)}
