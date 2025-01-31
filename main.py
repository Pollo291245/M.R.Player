import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                            QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QLineEdit, QComboBox, QFileDialog, QProgressBar,
                            QListWidget, QSlider, QCheckBox, QTextEdit, QDialog,
                            QMessageBox, QListWidgetItem, QGroupBox, QScrollArea, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer
from PyQt5.QtGui import QIcon, QFont
import vlc
from styles import STYLES
from downloader import Downloader
from music_player import MusicPlayer
from video_player import VideoPlayerWindow
from utils import create_download_folders, get_media_files
import os

class DownloadItemWidget(QWidget):
    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url
        self.setObjectName("DownloadItemWidget")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Info superior
        top_layout = QHBoxLayout()
        self.title_label = QLabel("Obteniendo información...")
        self.cancel_btn = QPushButton("❌")
        self.cancel_btn.setFixedSize(24, 24)
        self.cancel_btn.setProperty("class", "cancel-button")

        top_layout.addWidget(self.title_label, stretch=1)
        top_layout.addWidget(self.cancel_btn)

        # Barra de progreso
        self.progress_bar = QProgressBar()

        # Estado
        self.status_label = QLabel("Iniciando...")
        self.status_label.setProperty("class", "status-label")

        layout.addLayout(top_layout)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)


class ConsoleWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Consola del Programador")
        self.setMinimumSize(600, 400)
        self.setStyleSheet(STYLES)

        layout = QVBoxLayout()
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setObjectName("ConsoleTextEdit") #Added objectName
        layout.addWidget(self.console)
        self.setLayout(layout)

class ConsoleRedirect(QObject):
    output_written = pyqtSignal(str)

    def write(self, text):
        self.output_written.emit(str(text))
        sys.__stdout__.write(text)

    def flush(self):
        sys.__stdout__.flush()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media Downloader")
        self.setMinimumSize(800, 600)
        self.setStyleSheet(STYLES)

        # Crear carpetas necesarias
        self.base_download_path = os.path.join(os.path.expanduser("~"), "Downloads", "MediaDownloader")
        create_download_folders(self.base_download_path)

        # Inicializar componentes
        self.downloader = Downloader()
        self.music_player = MusicPlayer()
        self.download_thread = None
        self.video_window = None
        self.console_window = None
        self.console_redirect = ConsoleRedirect()
        self.console_redirect.output_written.connect(self._update_console)
        sys.stdout = self.console_redirect
        sys.stderr = self.console_redirect
        self.download_widgets = {} # Added for download queue

        self.init_ui()

        # Conectar señales del downloader
        self.downloader.progress_signal.connect(self._update_download_progress)
        self.downloader.finished_signal.connect(self._download_finished)
        self.downloader.error_signal.connect(self._download_error)
        self.downloader.status_signal.connect(self._update_download_status)
        self.downloader.title_signal.connect(self._update_download_title)


    def init_ui(self):
        # Widget principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()

        # Checkbox para mostrar modo programador y botón de eliminar
        top_layout = QHBoxLayout()
        top_layout.addStretch()

        right_controls = QHBoxLayout()
        self.console_checkbox = QCheckBox("Programador")
        self.console_checkbox.setObjectName("DeveloperCheckbox") #Added objectName
        # Botón de eliminar global
        self.delete_btn = QPushButton("Eliminar Seleccionados")
        self.delete_btn.setProperty("class", "danger-button")
        self.delete_btn.hide()  # Ocultar inicialmente
        self.delete_btn.clicked.connect(self._delete_selected_items)

        right_controls.addWidget(self.console_checkbox)
        right_controls.addWidget(self.delete_btn)
        top_layout.addLayout(right_controls)

        # Crear pestañas
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabBar::tab { height: 30px; }")

        # Agregar pestañas
        self.tabs = tabs  # Guardar referencia a las pestañas
        tabs.addTab(self.create_downloader_tab(), "Downloader")
        tabs.addTab(self.create_videos_tab(), "Videos")
        tabs.addTab(self.create_music_tab(), "Música")
        tabs.addTab(self.create_movies_tab(), "Películas")

        main_layout.addLayout(top_layout)
        main_layout.addWidget(tabs)
        main_widget.setLayout(main_layout)

        # Conectar cambio de pestaña para actualizar botón eliminar
        tabs.currentChanged.connect(self._update_delete_button)
        self.console_checkbox.stateChanged.connect(self._toggle_developer_mode)

    def _toggle_developer_mode(self, state):
        """Activa/desactiva el modo desarrollador"""
        if state == Qt.Checked:
            if not self.console_window:
                self.console_window = ConsoleWindow(self)
            self.console_window.show()
            print("Modo desarrollador activado")
        else:
            if self.console_window:
                self.console_window.hide()
            print("Modo desarrollador desactivado")

    def _update_console(self, text):
        """Actualiza la consola con nuevo texto"""
        if self.console_window:
            self.console_window.console.append(text.rstrip())

    def _update_delete_button(self):
        """Actualiza la visibilidad del botón de eliminar según la pestaña actual"""
        current_tab = self.tabs.currentWidget()
        list_widget = None

        if hasattr(current_tab, 'findChild'):
            list_widget = current_tab.findChild(QListWidget)

        if list_widget:
            has_checked = False
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                widget = list_widget.itemWidget(item)
                checkbox = widget.findChild(QCheckBox) if widget else None
                if checkbox and checkbox.isChecked():
                    has_checked = True
                    break
            self.delete_btn.setVisible(has_checked)

    def _delete_selected_items(self):
        """Elimina los elementos seleccionados de la lista actual"""
        current_tab = self.tabs.currentWidget()
        list_widget = None
        media_type = ""

        # Determinar la lista actual y el tipo de medio
        if hasattr(current_tab, 'findChild'):
            list_widget = current_tab.findChild(QListWidget)
            if list_widget == self.video_list:
                media_type = "Videos"
            elif list_widget == self.music_list:
                media_type = "Música"
            elif list_widget == self.movies_list:
                media_type = "Películas"

        if not list_widget or not media_type:
            return

        items_to_delete = []
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            widget = list_widget.itemWidget(item)
            checkbox = widget.findChild(QCheckBox) if widget else None
            if checkbox and checkbox.isChecked():
                name_label = widget.findChild(QLabel) if widget else None
                if name_label:
                    items_to_delete.append((i, name_label.text()))

        if not items_to_delete:
            return

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("¿Estás seguro de que deseas eliminar los archivos seleccionados?")
        msg.setInformativeText("Esta acción no se puede deshacer.")
        msg.setWindowTitle("Confirmar eliminación")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        if msg.exec_() == QMessageBox.Yes:
            for index, file_name in reversed(items_to_delete):
                file_path = os.path.join(self.base_download_path, media_type, file_name)
                try:
                    os.remove(file_path)
                    list_widget.takeItem(index)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"No se pudo eliminar {file_name}: {str(e)}")

            # Actualizar visibilidad del botón después de eliminar
            self._update_delete_button()

    def create_custom_list_item(self, text):
        """Crea un item personalizado con checkbox para las listas"""
        # Crear el item principal
        item = QListWidgetItem()
        
        # Crear el widget contenedor
        widget = QWidget()
        widget.setObjectName("ListItemWidget")
        
        # Crear el layout principal sin márgenes
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)
        
        # Crear checkbox
        checkbox = QCheckBox()
        checkbox.setFixedSize(20, 20)
        checkbox.stateChanged.connect(self._update_delete_button)
        
        # Crear label
        name_label = QLabel(text)
        name_label.setObjectName("ListItemLabel")
        
        # Agregar widgets al layout
        layout.addWidget(checkbox)
        layout.addWidget(name_label, 1)
        layout.addStretch()
        
        # Establecer una altura fija para el widget
        widget.setFixedHeight(32)
        
        # Configurar el tamaño del item para que coincida con el widget
        item.setSizeHint(widget.sizeHint())
        
        return item, widget

    def _on_track_double_clicked(self, item):
        """Reproduce una pista de música"""
        widget = self.music_list.itemWidget(item)
        if not widget:
            return

        name_label = widget.findChild(QLabel)
        if name_label:
            clicked_track = name_label.text()
            # Cargar toda la lista de reproducción
            music_path = os.path.join(self.base_download_path, "Música")
            all_tracks = []
            current_index = 0

            for i in range(self.music_list.count()):
                item_widget = self.music_list.itemWidget(self.music_list.item(i))
                track_label = item_widget.findChild(QLabel) if item_widget else None
                if track_label:
                    track_name = track_label.text()
                    track_path = os.path.join(music_path, track_name)
                    all_tracks.append(track_path)
                    if track_name == clicked_track:
                        current_index = i

            # Actualizar la lista de reproducción y reproducir la pista seleccionada
            if all_tracks:
                self.music_player.current_playlist = all_tracks
                self.music_player.play_track(current_index)


    def create_downloader_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # URL input y controles (mantener el código existente)
        url_layout = QHBoxLayout()
        url_label = QLabel("URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Pega aquí el enlace del video/audio...")
        self.url_input.textChanged.connect(self._on_url_changed)
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)

        # Plataforma detectada
        platform_layout = QHBoxLayout()
        platform_label = QLabel("Plataforma:")
        self.platform_detected = QLabel("--")
        self.platform_detected.setObjectName("PlatformDetectedLabel") #Added objectName
        platform_layout.addWidget(platform_label)
        platform_layout.addWidget(self.platform_detected)
        platform_layout.addStretch()

        # Tipo de medio
        type_layout = QHBoxLayout()
        type_label = QLabel("Tipo:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Videos", "Música", "Películas"])
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)

        # Botón de descarga
        download_btn = QPushButton("Añadir a Cola")
        download_btn.setProperty("class", "primary-button")
        download_btn.clicked.connect(self.start_download)

        controls_layout = QHBoxLayout()
        controls_layout.addLayout(type_layout)
        controls_layout.addWidget(download_btn)

        # Lista de descargas activas
        downloads_group = QGroupBox("Descargas Activas")
        downloads_layout = QVBoxLayout()
        self.downloads_list = QWidget()
        self.downloads_list.setObjectName("downloads_list")
        self.downloads_list_layout = QVBoxLayout(self.downloads_list)
        self.downloads_list_layout.setSpacing(10)
        self.downloads_list_layout.addStretch()

        downloads_scroll = QScrollArea()
        downloads_scroll.setWidget(self.downloads_list)
        downloads_scroll.setWidgetResizable(True)
        downloads_scroll.setObjectName("DownloadsScrollArea")

        downloads_layout.addWidget(downloads_scroll)
        downloads_group.setLayout(downloads_layout)

        # Agregar todo al layout principal
        layout.addLayout(url_layout)
        layout.addLayout(platform_layout)
        layout.addLayout(controls_layout)
        layout.addWidget(downloads_group)

        tab.setLayout(layout)
        return tab

    def create_videos_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Filtros y lista como antes
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Ordenar por:")
        self.video_filter_combo = QComboBox()
        self.video_filter_combo.addItems(["Alfabético", "Fecha", "Aleatorio"])
        self.video_filter_combo.currentTextChanged.connect(self._update_video_list)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.video_filter_combo)

        # Lista de videos
        self.video_list = QListWidget()
        self.video_list.itemDoubleClicked.connect(self._play_video)
        self.video_list.setObjectName("VideoList") #Added objectName

        layout.addLayout(filter_layout)
        layout.addWidget(self.video_list)

        self._load_videos()
        tab.setLayout(layout)
        return tab

    def create_music_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Filtros
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Ordenar por:")
        self.music_filter_combo = QComboBox()
        self.music_filter_combo.addItems(["Alfabético", "Fecha", "Aleatorio"])
        self.music_filter_combo.currentTextChanged.connect(self._update_music_list)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.music_filter_combo)

        # Lista de reproducción
        self.music_list = QListWidget()
        self.music_list.itemDoubleClicked.connect(self._on_track_double_clicked)
        self.music_list.setObjectName("MusicList") #Added objectName

        # Controles de reproducción
        controls_layout = QHBoxLayout()

        prev_btn = QPushButton("⏮")
        play_btn = QPushButton("⏯")
        next_btn = QPushButton("⏭")

        prev_btn.clicked.connect(self.music_player.previous_track)
        play_btn.clicked.connect(self.music_player.play_pause)
        next_btn.clicked.connect(self.music_player.next_track)

        # Control de volumen
        volume_layout = QHBoxLayout()
        volume_label = QLabel("🔈")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.valueChanged.connect(
            lambda v: self.music_player.set_volume(v / 100)
        )

        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_slider)

        controls_layout.addStretch()
        controls_layout.addWidget(prev_btn)
        controls_layout.addWidget(play_btn)
        controls_layout.addWidget(next_btn)
        controls_layout.addLayout(volume_layout)
        controls_layout.addStretch()

        # Tiempo y slider
        time_layout = QHBoxLayout()
        self.current_time = QLabel("00:00")
        self.total_time = QLabel("00:00")
        self.time_slider = QSlider(Qt.Horizontal)

        time_layout.addWidget(self.current_time)
        time_layout.addWidget(self.time_slider)
        time_layout.addWidget(self.total_time)

        # Conectar señales del reproductor
        self.music_player.position_changed.connect(self._on_position_changed)
        self.music_player.duration_changed.connect(self._on_duration_changed)
        self.music_player.track_changed.connect(self._on_track_changed)
        self.time_slider.sliderMoved.connect(self.music_player.seek)

        # Marco para los controles de música
        music_controls_frame = QFrame()
        music_controls_frame.setObjectName("MusicPlayerFrame")
        music_controls_layout = QVBoxLayout(music_controls_frame)

        # Agregar los controles existentes al frame
        music_controls_layout.addLayout(time_layout)
        music_controls_layout.addLayout(controls_layout)


        # Cargar música existente
        self._load_music_files()

        layout.addLayout(filter_layout)
        layout.addWidget(self.music_list)
        layout.addWidget(music_controls_frame)

        tab.setLayout(layout)
        return tab

    def create_movies_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Filtros
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Ordenar por:")
        self.movies_filter_combo = QComboBox()
        self.movies_filter_combo.addItems(["Alfabético", "Fecha", "Aleatorio"])
        self.movies_filter_combo.currentTextChanged.connect(self._update_movies_list)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.movies_filter_combo)

        # Lista de películas
        self.movies_list = QListWidget()
        self.movies_list.itemDoubleClicked.connect(self._play_movie)
        self.movies_list.setObjectName("MoviesList") #Added objectName

        layout.addLayout(filter_layout)
        layout.addWidget(self.movies_list)

        self._load_movies()
        tab.setLayout(layout)
        return tab

    def _play_video(self, item):
        """Reproduce un video"""
        media_type = "Videos"
        widget = self.video_list.itemWidget(item)
        name_label = widget.findChild(QLabel) if widget else None
        if name_label:
            video_name = name_label.text()
            video_path = os.path.join(self.base_download_path, media_type, video_name)
            self.video_window = VideoPlayerWindow(video_path, self)
            self.video_window.show()

    def _play_movie(self, item):
        """Reproduce una película"""
        media_type = "Películas"
        widget = self.movies_list.itemWidget(item)
        name_label = widget.findChild(QLabel) if widget else None
        if name_label:
            movie_name = name_label.text()
            movie_path = os.path.join(self.base_download_path, media_type, movie_name)
            self.video_window = VideoPlayerWindow(movie_path, self)
            self.video_window.show()

    def _load_videos(self):
        video_path = os.path.join(self.base_download_path, "Videos")
        files = get_media_files(video_path, self.video_filter_combo.currentText())
        self._add_items_to_list(self.video_list, files)

    def _load_movies(self):
        movies_path = os.path.join(self.base_download_path, "Películas")
        files = get_media_files(movies_path, self.movies_filter_combo.currentText())
        self._add_items_to_list(self.movies_list, files)

    def _update_video_list(self):
        self._load_videos()

    def _update_movies_list(self):
        self._load_movies()

    def start_download(self):
        url = self.url_input.text()
        if not url:
            QMessageBox.warning(self, "Error", "Por favor ingrese una URL")
            return

        media_type = self.type_combo.currentText()
        download_path = os.path.join(self.base_download_path, media_type)

        # Crear widget para esta descarga
        download_widget = DownloadItemWidget(url)
        download_widget.cancel_btn.clicked.connect(lambda: self.cancel_specific_download(url))

        # Insertar al inicio de la lista
        self.downloads_list_layout.insertWidget(0, download_widget)
        self.download_widgets[url] = download_widget

        # Iniciar descarga
        self.downloader.add_to_queue(url, download_path, media_type)
        self.url_input.clear()

    def cancel_download(self):
        """Cancela la descarga actual"""
        if self.downloader:
            self.downloader.cancel_download()
            self.cancel_btn.setEnabled(False)

    def cancel_specific_download(self, url):
        """Cancela una descarga específica"""
        self.downloader.cancel_download(url)
        if url in self.download_widgets:
            widget = self.download_widgets[url]
            widget.status_label.setText("Cancelado")
            widget.status_label.setProperty("class", "error-label") #Added to use styles.py
            widget.progress_bar.setEnabled(False)
            # Programar la eliminación del widget después de un tiempo
            QTimer.singleShot(5000, lambda: self._remove_download_widget(url))

    def _remove_download_widget(self, url):
        """Elimina el widget de la descarga de la interfaz"""
        if url in self.download_widgets:
            widget = self.download_widgets[url]
            self.downloads_list_layout.removeWidget(widget)
            widget.deleteLater()
            del self.download_widgets[url]


    def _on_thread_finished(self):
        if self.download_thread:
            self.download_thread.deleteLater()
            self.download_thread = None

    def _update_download_progress(self, url, progress):
        """Actualiza el progreso de una descarga específica"""
        if url in self.download_widgets:
            widget = self.download_widgets[url]
            widget.progress_bar.setValue(progress)

    def _download_finished(self, url, filename):
        """Maneja la finalización de una descarga específica"""
        if url in self.download_widgets:
            widget = self.download_widgets[url]
            widget.status_label.setText(f"Completado: {filename}")
            widget.status_label.setProperty("class", "success-label") #Added to use styles.py
            widget.progress_bar.setValue(100)
            widget.cancel_btn.setEnabled(False)
            # Programar la eliminación del widget después de un tiempo
            QTimer.singleShot(5000, lambda: self._remove_download_widget(url))

            # Actualizar listas de medios
            self._load_videos()
            self._load_movies()
            self._load_music_files()

    def _download_error(self, url, error):
        """Maneja errores de una descarga específica"""
        if url in self.download_widgets:
            widget = self.download_widgets[url]
            widget.status_label.setText(f"Error: {error}")
            widget.status_label.setProperty("class", "error-label") #Added to use styles.py
            widget.progress_bar.setEnabled(False)
            widget.cancel_btn.setEnabled(False)
            # Programar la eliminación del widget después de un tiempo
            QTimer.singleShot(5000, lambda: self._remove_download_widget(url))

    def _update_download_status(self, url, status):
        """Actualiza el estado de una descarga específica"""
        if url in self.download_widgets:
            widget = self.download_widgets[url]
            widget.status_label.setText(status)

    def _update_download_title(self, url, title):
        """Actualiza el título de una descarga específica"""
        if url in self.download_widgets:
            widget = self.download_widgets[url]
            widget.title_label.setText(title)

    def update_progress(self, progress):
        self.progress_bar.setValue(progress)

    def update_status(self, status):
        self.status_label.setText(status)
        self.status_label.setStyleSheet("color: #007BFF;")

    def download_finished(self, filename):
        self.progress_bar.setVisible(False)
        self.cancel_btn.setEnabled(False)
        self.status_label.setText(f"Descarga completada: {filename}")
        self.status_label.setStyleSheet("color: #00C853;")
        self.url_input.clear()

        # Actualizar listas
        self._load_videos()
        self._load_movies()
        self._load_music_files()

    def download_error(self, error):
        self.progress_bar.setVisible(False)
        self.cancel_btn.setEnabled(False)
        self.status_label.setText(f"Error: {error}")
        self.status_label.setStyleSheet("color: #FF3B30;")

    def _load_music_files(self):
        self._update_music_list()

    def _on_position_changed(self, position):
        self.time_slider.setValue(position)
        self.current_time.setText(self.music_player.format_time(position))

    def _on_duration_changed(self, duration):
        self.time_slider.setRange(0, duration)
        self.total_time.setText(self.music_player.format_time(duration))

    def _on_track_changed(self, track_name):
        # Encuentra y selecciona la pista actual en la lista
        items = self.music_list.findItems(track_name, Qt.MatchExactly)
        if items:
            self.music_list.setCurrentItem(items[0])

    def _update_music_list(self):
        sort_by = self.music_filter_combo.currentText()
        music_path = os.path.join(self.base_download_path, "Música")
        files = get_media_files(music_path, sort_by)
        self._add_items_to_list(self.music_list, files)

    def _update_position(self):
        """Actualiza la posición actual durante la reproducción"""
        if self.music_player.is_playing():
            position = int(self.music_player.get_position() * self.music_player.get_length())
            self.music_player.position_changed.emit(position)

            # Verificar si la canción terminó
            if self.music_player.get_state() == vlc.State.Ended:
                self.music_player.next_track()

    def _on_url_changed(self):
        """Detectar plataforma cuando cambia la URL"""
        url = self.url_input.text()
        if url:
            platform = self.downloader.detect_platform(url)
            self.platform_detected.setText(platform)

            # Ajustar tipo automáticamente según la plataforma
            if platform in ['YouTube', 'Facebook', 'Twitter', 'Instagram', 'TikTok']:
                self.type_combo.setCurrentText('Videos')
            elif platform == 'Cuevana':
                self.type_combo.setCurrentText('Películas')
            elif 'playlist' in url.lower() and 'youtube.com' in url.lower():
                self.type_combo.setCurrentText('Música')

    def _add_items_to_list(self, list_widget, files):
        """Agrega items con checkbox a una lista"""
        list_widget.clear()
        for file in files:
            if isinstance(file, dict):
                name = file['name']
            else:
                name = os.path.basename(file)

            item, widget = self.create_custom_list_item(name)
            list_widget.addItem(item)
            list_widget.setItemWidget(item, widget)



class DownloaderThread(QThread):
    def __init__(self, downloader, url, path, type):
        super().__init__()
        self.downloader = downloader
        self.url = url
        self.path = path
        self.type = type

    def run(self):
        self.downloader.download(self.url, self.path, self.type)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == '__main__':
    main()