import os
from datetime import datetime
import random

def create_download_folders(base_path):
    """Crea las carpetas necesarias para las descargas"""
    folders = ["Videos", "Música", "Películas"]

    try:
        if not os.path.exists(base_path):
            os.makedirs(base_path)

        for folder in folders:
            folder_path = os.path.join(base_path, folder)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
    except Exception as e:
        print(f"Error creando carpetas: {str(e)}")

def get_media_files(directory, sort_by="Alfabético"):
    """Obtiene la lista de archivos multimedia ordenados según el criterio especificado"""
    if not os.path.exists(directory):
        return []

    files = []
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            files.append({
                'name': file,
                'path': file_path,
                'date': datetime.fromtimestamp(os.path.getctime(file_path)),
                'size': os.path.getsize(file_path)
            })

    if sort_by == "Fecha":
        files.sort(key=lambda x: x['date'], reverse=True)
    elif sort_by == "Alfabético":
        files.sort(key=lambda x: x['name'].lower())
    elif sort_by == "Aleatorio":
        random.shuffle(files)

    return files