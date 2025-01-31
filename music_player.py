from PyQt5.QtCore import QObject, pyqtSignal, QUrl, QTime, QTimer
import vlc
import os

class MusicPlayer(QObject):
    position_changed = pyqtSignal(int)
    duration_changed = pyqtSignal(int)
    track_changed = pyqtSignal(str)
    state_changed = pyqtSignal(bool)  # True for playing, False for paused
    volume_changed = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.current_playlist = []
        self.current_index = -1
        self.current_position = 0
        self._volume = 1.0  # 100% volumen por defecto

        # Timer para actualizar la posición
        self.timer = QTimer()
        self.timer.setInterval(1000)  # Update every second
        self.timer.timeout.connect(self._update_position)

        # Configurar manejador de eventos de VLC
        self.event_manager = self.player.event_manager()
        self.event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_end_reached)

    def load_directory(self, directory, sort_by="Alfabético"):
        """Carga todas las canciones MP3 del directorio"""
        self.current_playlist = []
        files = []
        for file in os.listdir(directory):
            if file.lower().endswith('.mp3'):
                path = os.path.join(directory, file)
                files.append({
                    'name': file,
                    'path': path,
                    'date': os.path.getctime(path)
                })

        # Aplicar filtro
        if sort_by == "Fecha":
            files.sort(key=lambda x: x['date'], reverse=True)
        elif sort_by == "Alfabético":
            files.sort(key=lambda x: x['name'].lower())
        elif sort_by == "Aleatorio":
            import random
            random.shuffle(files)

        self.current_playlist = [file['path'] for file in files]

    def play_pause(self):
        """Alterna entre reproducir y pausar"""
        if self.player.is_playing():
            self.player.pause()
            self.timer.stop()
            self.state_changed.emit(False)
        else:
            self.player.play()
            self.timer.start()
            self.state_changed.emit(True)

    def play_track(self, index):
        """Reproduce una pista específica"""
        if 0 <= index < len(self.current_playlist):
            self.player.stop()
            self.current_index = index

            media = self.instance.media_new(self.current_playlist[index])
            self.player.set_media(media)

            # Reproducir después de que el medio esté listo
            self.player.play()
            self.current_position = 0
            self.timer.start()

            # Emitir información de la pista
            self.track_changed.emit(os.path.basename(self.current_playlist[index]))
            self.state_changed.emit(True)

            # Obtener y emitir duración después de un breve retraso
            QTimer.singleShot(500, self._emit_duration)

    def _emit_duration(self):
        """Emite la duración de la pista actual"""
        if self.player.get_length() > 0:
            self.duration_changed.emit(self.player.get_length())

    def _on_end_reached(self, event):
        """Manejador del evento de fin de pista"""
        # Usar QTimer.singleShot para asegurar que el cambio ocurra en el hilo principal
        QTimer.singleShot(0, self.next_track)

    def next_track(self):
        """Reproduce la siguiente pista"""
        if self.current_playlist:
            next_index = (self.current_index + 1) % len(self.current_playlist)
            self.play_track(next_index)

    def previous_track(self):
        """Reproduce la pista anterior"""
        if self.current_playlist:
            prev_index = (self.current_index - 1) % len(self.current_playlist)
            self.play_track(prev_index)

    def seek(self, position):
        """Busca una posición específica en la pista actual"""
        if self.player:
            length = self.player.get_length()
            if length > 0:
                self.player.set_position(float(position) / length)
                self.current_position = position

    def set_volume(self, volume):
        """Establece el volumen (0.0 a 1.0)"""
        self._volume = max(0.0, min(1.0, volume))
        if self.player:
            self.player.audio_set_volume(int(self._volume * 100))
        self.volume_changed.emit(self._volume)

    def _update_position(self):
        """Actualiza la posición actual durante la reproducción"""
        if self.player.is_playing():
            length = self.player.get_length()
            if length > 0:
                current_pos = int(self.player.get_position() * length)
                self.position_changed.emit(current_pos)

    def format_time(self, ms):
        """Formatea el tiempo en milisegundos a formato MM:SS"""
        total_seconds = ms // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"