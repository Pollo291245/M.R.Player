from PyQt5.QtCore import QObject, pyqtSignal
import yt_dlp
import os
import threading
import re
from queue import Queue
from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class DownloadItem:
    url: str
    path: str
    media_type: str
    title: Optional[str] = None
    status: str = "pending"  # pending, downloading, completed, error
    progress: int = 0
    download_thread: Optional[threading.Thread] = None

class Downloader(QObject):
    progress_signal = pyqtSignal(str, int)  # url, progress
    finished_signal = pyqtSignal(str, str)  # url, filename
    error_signal = pyqtSignal(str, str)     # url, error message
    status_signal = pyqtSignal(str, str)    # url, status message
    title_signal = pyqtSignal(str, str)     # url, clean title

    def __init__(self):
        super().__init__()
        self.downloads: Dict[str, DownloadItem] = {}
        self._lock = threading.Lock()

    def clean_filename(self, filename: str) -> str:
        """Limpia el nombre del archivo quitando códigos y extensiones"""
        # Quitar extensión
        name = os.path.splitext(filename)[0]
        # Quitar códigos típicos como [1080p], (720p), etc.
        name = re.sub(r'\[.*?\]|\(.*?\)|\{.*?\}', '', name)
        # Quitar caracteres especiales y espacios múltiples
        name = re.sub(r'[^\w\s-]', ' ', name)
        name = re.sub(r'\s+', ' ', name).strip()
        return name

    def add_to_queue(self, url: str, download_path: str, media_type: str):
        """Añade una nueva descarga a la cola"""
        with self._lock:
            if url in self.downloads:
                self.error_signal.emit(url, "Esta URL ya está en la cola")
                return

            download_item = DownloadItem(url=url, path=download_path, media_type=media_type)
            self.downloads[url] = download_item

            # Iniciar thread de descarga
            download_thread = threading.Thread(target=self._download_worker, args=(url,))
            download_thread.daemon = True
            self.downloads[url].download_thread = download_thread
            download_thread.start()

    def cancel_download(self, url: str):
        """Cancela una descarga específica"""
        with self._lock:
            if url in self.downloads:
                self.downloads[url].status = "cancelled"
                self.status_signal.emit(url, "Cancelando descarga...")

    def _download_worker(self, url: str):
        download_item = self.downloads[url]
        try:
            platform = self.detect_platform(url)
            self.status_signal.emit(url, f"Detectada plataforma: {platform}")

            ydl_opts = self.get_platform_options(platform, download_item.media_type)
            ydl_opts['progress_hooks'] = [lambda d: self._progress_hook(url, d)]
            ydl_opts['outtmpl'] = os.path.join(download_item.path, '%(title)s.%(ext)s')

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if download_item.status == "cancelled":
                    self.error_signal.emit(url, "Descarga cancelada")
                    return

                self.status_signal.emit(url, "Obteniendo información...")
                info = ydl.extract_info(url, download=False)

                # Emitir título limpio
                if info.get('title'):
                    clean_title = self.clean_filename(info['title'])
                    self.title_signal.emit(url, clean_title)
                    download_item.title = clean_title

                if download_item.status == "cancelled":
                    self.error_signal.emit(url, "Descarga cancelada")
                    return

                download_item.status = "downloading"
                ydl.download([url])

                if download_item.status != "cancelled":
                    download_item.status = "completed"
                    final_filename = f"{download_item.title}.{'mp3' if download_item.media_type == 'Música' else 'mp4'}"
                    self.finished_signal.emit(url, final_filename)

        except Exception as e:
            error_msg = str(e)
            if "unavailable video" in error_msg.lower():
                error_msg = "El video no está disponible o es privado"
            elif "copyright" in error_msg.lower():
                error_msg = "Contenido bloqueado por derechos de autor"
            elif "cookies" in error_msg.lower():
                error_msg = "Se requiere inicio de sesión para este contenido"

            download_item.status = "error"
            self.error_signal.emit(url, error_msg)
        finally:
            if download_item.status == "cancelled":
                del self.downloads[url]

    def _progress_hook(self, url: str, d):
        if d['status'] == 'downloading' and url in self.downloads:
            try:
                total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    progress = (downloaded / total) * 100
                    self.downloads[url].progress = int(progress)
                    self.progress_signal.emit(url, int(progress))

                    status_msg = f"Descargando... {int(progress)}%"
                    speed = d.get('speed', 0)
                    if speed:
                        speed_mb = speed / 1024 / 1024
                        status_msg += f" ({speed_mb:.1f} MB/s)"

                    self.status_signal.emit(url, status_msg)
            except Exception as e:
                print(f"Error en progress_hook: {str(e)}")

    def detect_platform(self, url):
        url = url.lower()
        streamers = {
            'streamwish.to': 'Streamwish',
            'filemoon.sx': 'Filemoon',
            'streamtape.com': 'Streamtape',
            'doodstream.com': 'Doodstream',
            'dooodster.com': 'Doodstream',  # Alias para doodstream
            'dood.': 'Doodstream',          # Captura todos los subdominios dood.*
            'streamlare.com': 'Streamlare',
            'uqload.com': 'Uqload',
            'voe.sx': 'Voe',
            'upstream.to': 'Upstream'
        }

        for domain, platform in streamers.items():
            if domain in url:
                return platform

        if 'tiktok.com' in url:
            return 'TikTok'
        elif 'instagram.com' in url:
            return 'Instagram'
        elif 'facebook.com' in url or 'fb.watch' in url:
            return 'Facebook'
        elif 'twitter.com' in url or 'x.com' in url:
            return 'Twitter'
        elif 'cuevana' in url:
            return 'Cuevana'
        elif 'youtube.com' in url or 'youtu.be' in url:
            return 'YouTube'
        else:
            return 'Unknown'

    def get_platform_options(self, platform, media_type):
        common_opts = {
            'quiet': False,  # Cambiado a False para ver logs
            'no_warnings': False,  # Cambiado a False para ver warnings
            #'progress_hooks': [self.progress_hook],
            'ignoreerrors': True,
        }

        if media_type == "Música":
            audio_opts = {
                'format': 'bestaudio/best',
                'extract_flat': False,  # Desactivar extracción plana para playlists
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            common_opts.update(audio_opts)
        else:
            video_opts = {'format': 'bestvideo+bestaudio/best'}

            platform_configs = {
                'TikTok': {'format': 'best'},
                'Instagram': {'format': 'best'},
                'Cuevana': {'format': 'bestvideo[height<=1080]+bestaudio/best'},
                'YouTube': {
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'extract_flat': False,  # Desactivar extracción plana
                    'extract_flat_playlist': False,  # Desactivar extracción plana para playlists
                },
                'Streamwish': {
                    'format': 'best[protocol^=http]',
                    'referer': 'https://streamwish.to/',
                },
                'Filemoon': {
                    'format': 'best[protocol^=http]',
                    'referer': 'https://filemoon.sx/',
                },
                'Streamtape': {
                    'format': 'best[protocol^=http]',
                    'referer': 'https://streamtape.com/',
                },
                'Doodstream': {
                    'format': 'best[protocol^=http]',
                    'referer': 'https://doodstream.com/',
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Sec-Fetch-User': '?1'
                    }
                },
            }

            if platform in platform_configs:
                video_opts.update(platform_configs[platform])

            common_opts.update(video_opts)

        if platform in ['Facebook', 'Instagram'] or platform in ['Streamwish', 'Filemoon', 'Streamtape', 'Doodstream']:
            common_opts.update({
                'cookiesfrombrowser': ['chrome'],
                'http_headers': platform_configs.get(platform, {}).get('http_headers', {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                })
            })

        return common_opts