#!/usr/bin/env python3

import os
import sys
import traceback
import time
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed


current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    from core import utils
    from core.config import Config
    from core.downloader import get_content, process_video
except ImportError as e:
    print(f"❌ Import error: {str(e)}")
    print("Path details:")
    print(f" - Current directory: {os.getcwd()}")
    print(f" - Script path: {__file__}")
    print(f" - sys.path: {sys.path}")
    sys.exit(1)

def check_ffmpeg():
    ffmpeg_bin = utils.get_os_config().get('ffmpeg', 'ffmpeg')
    if shutil.which(ffmpeg_bin) is None:
        print("❌ 'ffmpeg' is not installed or not in PATH. Please install it before running OctoTube.")
        sys.exit(1)

class OctoTubeCLI:
    def __init__(self):
        self.styles = Config.CLI_STYLES
        utils.clear_screen()
        self.print_header()

    def print_header(self):
        try:
            title_style = self.styles['title']
            reset_style = self.styles['reset']
            info_style = self.styles['info']
            ascii_art = r"""     
 ██████\              ██\            █████████\       ██\                 
██  __██\             ██ |           \__██  __|       ██ |                
██ /  ██ | ███████\ ██████\    ██████\  ██ |██\   ██\ ███████\   ██████\  
██ |  ██ |██  _____|\_██  _|  ██  __██\ ██ |██ |  ██ |██  __██\ ██  __██\ 
██ |  ██ |██ /        ██ |    ██ /  ██ |██ |██ |  ██ |██ |  ██ |████████ |
██ |  ██ |██ |        ██ |██\ ██ |  ██ |██ |██ |  ██ |██ |  ██ |██   ____|
 ██████  |\████████\  \█████  |\██████  |██ |\██████  |███████ |█████████\ 
 \______/  \_______|   \____/   \______/ \__| \______/ \_______/ \_______|
"""
            print(f"{title_style}{ascii_art}{reset_style}")
            print(f"{info_style}YouTube Content Downloader v2.1{reset_style}")
            print(f"{info_style}{'='*40}{reset_style}\n")
        except Exception as e:
            print(f"❌ Error in header: {str(e)}")
            sys.exit(1)

    def get_user_input(self, prompt: str, validation_func=None) -> str:
        while True:
            try:
                user_input = input(f"{self.styles['info']}{prompt}{self.styles['reset']}").strip()
                if validation_func and not validation_func(user_input):
                    print(f"{self.styles['error']}Invalid input!{self.styles['reset']}")
                    continue
                return user_input
            except KeyboardInterrupt:
                print(f"\n{self.styles['warning']}Operation canceled by user{self.styles['reset']}")
                sys.exit(0)

    def select_menu(self, title: str, options: list) -> int:
        print(f"\n{self.styles['info']}{title}{self.styles['reset']}")
        for i, option in enumerate(options, 1):
            print(f"{self.styles['option']}{i:>2}. {option}{self.styles['reset']}")
        while True:
            try:
                choice = int(input(f"\n{self.styles['option']}Selection: {self.styles['reset']}"))
                if 1 <= choice <= len(options):
                    return choice
                print(f"{self.styles['error']}Invalid option! Enter 1 to {len(options)}{self.styles['reset']}")
            except ValueError:
                print(f"{self.styles['error']}Please enter a valid integer!{self.styles['reset']}")
            except KeyboardInterrupt:
                print(f"\n{self.styles['warning']}Selection canceled{self.styles['reset']}")
                sys.exit(0)

    def run_downloads(self, content: dict, media_type: str, output_dir: str, quality: str = None, download_thumb: bool = True):
        styles = self.styles
        if content['type'] == 'error':
            print(f"{styles['error']}❌ {content['message']}{styles['reset']}")
            return

        if content['type'] == 'playlist':
            print(f"\n{styles['success']}📚 Playlist detected:{styles['reset']} {content['title']}")
            print(f"{styles['info']}Videos in playlist: {len(content['videos'])}{styles['reset']}")
        else:
            print(f"\n{styles['success']}🎥 Single video detected:{styles['reset']} {content['title']}{styles['reset']}")

        videos = content['videos']
        total = len(videos)
        if total == 0:
            print(f"{styles['warning']}⚠ No videos to download{styles['reset']}")
            return

        print(f"\n{styles['info']}Starting download of {total} items...{styles['reset']}")
        success_count = 0
        total_size = 0
        total_time = 0

        start_time = time.time()
        for i, video in enumerate(videos, 1):
            t0 = time.time()
            try:
                result = process_video(video, {
                    'output_dir': output_dir,
                    'media_type': media_type,
                    'quality': quality,
                    'download_thumb': download_thumb
                })
                title = result.get('title', f"Video {i}")
            except Exception as e:
                result = {'status': 'error', 'title': f"Video {i}", 'message': str(e)}
                title = result['title']

            t1 = time.time()
            elapsed = t1 - t0

            file_size = 0
            if result['status'] == 'success':
                success_count += 1
                file_path = result.get('file_path')
                if file_path and os.path.exists(file_path):
                    file_size = os.path.getsize(file_path) // 1024  # KiB
                    total_size += file_size
            total_time += elapsed

            status_icon = f"{styles['success']}✓{styles['reset']}" if result['status'] == 'success' else f"{styles['error']}✗{styles['reset']}"
            print(f"[{i}/{total}] {status_icon} {title} | size: {file_size}KiB | time: {int(elapsed//60)}:{int(elapsed%60):02d}")
            if result['status'] != 'success' and 'message' in result:
                print(f"   → {styles['error']}{result['message']}{styles['reset']}")

        percent = 100
        bar = '-' * 20 + '>'
        print(f"{percent}% {bar} {total_size}KiB {int(total_time//60)}:{int(total_time%60):02d}")

        success_rate = (success_count / total) * 100 if total > 0 else 0
        print(f"\n{styles['success']}✅ Download completed!{styles['reset']}")
        print(f"{styles['info']}Results:{styles['reset']}")
        print(f" - {styles['success']}Success: {success_count}/{total}{styles['reset']}")
        print(f" - {styles['error']}Failed: {total - success_count}/{total}{styles['reset']}")
        print(f" - {styles['info']}Success rate: {success_rate:.2f}%{styles['reset']}")

    def run(self):
        try:
            check_ffmpeg()
            url = self.get_user_input("YouTube URL (video/playlist): ")
            output_dir = self.get_user_input("Download folder (leave empty for current): ")
            if not output_dir.strip():
                output_dir = "."
            else:
                output_dir = utils.create_directory(output_dir.strip())
            content = get_content(url)
            media_type_idx = self.select_menu(
                "Download format",
                [
                    "MP3 (Audio only)",
                    "MP4 (Full video)",
                    "WAV (Uncompressed audio)",
                    "MKV (Uncompressed video)"
                ]
            )
            media_types = ['mp3', 'mp4', 'wav', 'mkv']
            media_type = media_types[media_type_idx - 1]

            # Ask about downloading thumbnail
            download_thumb_choice = self.select_menu(
                "Download cover image (JPG)?",
                ["No", "Yes"]
            )
            download_thumb = download_thumb_choice == 2

            # Playlist: all or some?
            if content['type'] == 'playlist':
                total_videos = len(content['videos'])
                print(f"Playlist detected with {total_videos} videos.")
                all_or_some = self.select_menu("Download all videos?", ["Yes", "No"])
                if all_or_some == 2:
                    n = int(self.get_user_input(f"How many videos to download? (1-{total_videos}): ",
                                                lambda x: x.isdigit() and 1 <= int(x) <= total_videos))
                    content['videos'] = content['videos'][:n]
                output_dir = utils.create_directory(os.path.join(output_dir, content['title']))

            # Video quality selection
            quality = None
            if media_type in ['mp4', 'mkv']:
                video = content['videos'][0]
                streams = video.streams.filter(progressive=True, file_extension="mp4").order_by('resolution').desc()
                qualities = [stream.resolution for stream in streams]
                if not qualities:
                    print("No video qualities available.")
                    sys.exit(1)
                q_idx = self.select_menu("Select video quality", qualities)
                quality = qualities[q_idx - 1]

            self.run_downloads(content, media_type, output_dir, quality, download_thumb)
        except KeyboardInterrupt:
            print(f"\n{self.styles['warning']}⛔ Operation canceled by user{self.styles['reset']}")
            sys.exit(0)
        except Exception as e:
            print(f"\n{self.styles['error']}❌ Critical ERROR: {str(e)}{self.styles['reset']}")
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    try:
        app = OctoTubeCLI()
        app.run()
    except Exception as e:
        print(f"\n❌ ERROR TO START: {str(e)}")
        sys.exit(1)
