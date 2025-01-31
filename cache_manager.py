import os
import json
import shutil
from datetime import datetime, timedelta
import hashlib

class CacheManager:
    def __init__(self, cache_dir=None):
        if cache_dir is None:
            cache_dir = os.path.join(os.path.expanduser("~"), ".media_downloader_cache")
        self.cache_dir = cache_dir
        self.metadata_file = os.path.join(cache_dir, "metadata.json")
        self.max_cache_age = timedelta(days=7)  # Caché expira después de 7 días
        self.max_cache_size = 5 * 1024 * 1024 * 1024  # 5 GB máximo
        self._init_cache()

    def _init_cache(self):
        """Inicializa el directorio de caché y su metadata"""
        os.makedirs(self.cache_dir, exist_ok=True)
        if not os.path.exists(self.metadata_file):
            self._save_metadata({})
        self._clean_old_cache()

    def _save_metadata(self, metadata):
        """Guarda la metadata del caché"""
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f)

    def _load_metadata(self):
        """Carga la metadata del caché"""
        try:
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _get_cache_key(self, url, media_type):
        """Genera una clave única para el caché basada en la URL y el tipo de medio"""
        return hashlib.md5(f"{url}:{media_type}".encode()).hexdigest()

    def _clean_old_cache(self):
        """Limpia archivos viejos del caché"""
        metadata = self._load_metadata()
        current_time = datetime.now()
        total_size = 0
        files_to_remove = []

        # Ordenar archivos por fecha de último acceso
        cache_files = [(k, v) for k, v in metadata.items()]
        cache_files.sort(key=lambda x: x[1].get('last_accessed', ''))

        for cache_key, info in cache_files:
            file_path = os.path.join(self.cache_dir, cache_key)
            if not os.path.exists(file_path):
                files_to_remove.append(cache_key)
                continue

            last_accessed = datetime.fromisoformat(info.get('last_accessed', '2000-01-01'))
            file_size = os.path.getsize(file_path)

            # Remover archivos viejos o si el caché excede el tamaño máximo
            if (current_time - last_accessed) > self.max_cache_age or \
               total_size + file_size > self.max_cache_size:
                files_to_remove.append(cache_key)
                try:
                    os.remove(file_path)
                except OSError:
                    pass
            else:
                total_size += file_size

        # Actualizar metadata
        for key in files_to_remove:
            metadata.pop(key, None)
        self._save_metadata(metadata)

    def get_cached_file(self, url, media_type):
        """Obtiene un archivo del caché si existe y es válido"""
        cache_key = self._get_cache_key(url, media_type)
        metadata = self._load_metadata()
        
        if cache_key in metadata:
            file_path = os.path.join(self.cache_dir, cache_key)
            if os.path.exists(file_path):
                # Actualizar último acceso
                metadata[cache_key]['last_accessed'] = datetime.now().isoformat()
                self._save_metadata(metadata)
                return file_path
        return None

    def cache_file(self, url, media_type, file_path):
        """Guarda un archivo en el caché"""
        cache_key = self._get_cache_key(url, media_type)
        cached_path = os.path.join(self.cache_dir, cache_key)
        
        try:
            shutil.copy2(file_path, cached_path)
            metadata = self._load_metadata()
            metadata[cache_key] = {
                'url': url,
                'media_type': media_type,
                'original_path': file_path,
                'cached_date': datetime.now().isoformat(),
                'last_accessed': datetime.now().isoformat()
            }
            self._save_metadata(metadata)
            return True
        except (IOError, OSError):
            return False

    def clear_cache(self):
        """Limpia todo el caché"""
        try:
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir)
            self._save_metadata({})
            return True
        except OSError:
            return False
