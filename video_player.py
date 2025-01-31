import sys
from PyQt5.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QSlider, QSizePolicy,
                           QFrame, QComboBox, QApplication)
from PyQt5.QtCore import Qt, QTimer, QTime, QPoint
import vlc

class VideoPlayerWindow(QDialog):
    def __init__(self, video_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reproductor de Video")
        self.resize(800, 600)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        self.setObjectName("VideoPlayerWindow")
        self.setMouseTracking(True)  # Habilitar seguimiento del mouse

        # Timer para ocultar controles
        self.hide_controls_timer = QTimer(self)
        self.hide_controls_timer.setInterval(3000)  # 3 segundos
        self.hide_controls_timer.timeout.connect(self.hide_controls)

        # Variables de control
        self.controls_visible = True
        self.mouse_pos = QPoint()

        layout = QVBoxLayout()

        # Contenedor de video
        self.video_container = QWidget()
        self.video_container.setObjectName("VideoContainer")
        self.video_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_container.setMouseTracking(True)

        # Inicializar reproductor
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        if sys.platform == "linux":
            self.player.set_xwindow(self.video_container.winId())
        elif sys.platform == "win32":
            self.player.set_hwnd(self.video_container.winId())
        elif sys.platform == "darwin":
            self.player.set_nsobject(int(self.video_container.winId()))

        # Panel de controles
        self.controls_frame = QFrame()
        self.controls_frame.setObjectName("ControlsFrame")
        controls_layout = QVBoxLayout(self.controls_frame)

        # Barra de progreso
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setObjectName("ProgressSlider")
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.sliderMoved.connect(self._seek)

        # Controles principales
        main_controls = QHBoxLayout()

        # Botones de control
        self.play_button = QPushButton("⏯")
        self.play_button.setObjectName("PlayButton")
        self.stop_button = QPushButton("⏹")
        self.stop_button.setObjectName("StopButton")
        self.pip_button = QPushButton("🗗")  # Botón PiP
        self.pip_button.setObjectName("PipButton")
        self.pip_button.setToolTip("Picture in Picture")

        # Control de velocidad
        self.speed_combo = QComboBox()
        self.speed_combo.setObjectName("SpeedCombo")
        self.speed_combo.addItems(["0.25x", "0.5x", "1.0x", "1.5x", "2.0x"])
        self.speed_combo.setCurrentText("1.0x")
        self.speed_combo.currentTextChanged.connect(self._change_speed)

        # Volumen
        volume_layout = QHBoxLayout()
        self.volume_label = QLabel("🔈")
        self.volume_label.setObjectName("VolumeLabel")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setObjectName("VolumeSlider")
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)

        # Etiqueta de tiempo
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setObjectName("TimeLabel")

        # Conectar señales
        self.play_button.clicked.connect(self.toggle_play)
        self.stop_button.clicked.connect(self.stop)
        self.pip_button.clicked.connect(self.toggle_pip)
        self.volume_slider.valueChanged.connect(lambda v: self.player.audio_set_volume(v))

        # Timer para actualizar progreso
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(500)
        self.update_timer.timeout.connect(self._update_progress)
        self.update_timer.start()

        # Variables de estado
        self.is_pip_mode = False
        self.original_geometry = None

        # Organizar controles
        main_controls.addWidget(self.play_button)
        main_controls.addWidget(self.stop_button)
        main_controls.addWidget(self.pip_button)
        main_controls.addWidget(self.speed_combo)
        main_controls.addWidget(self.time_label)
        main_controls.addStretch()
        main_controls.addWidget(self.volume_label)
        main_controls.addWidget(self.volume_slider)

        controls_layout.addWidget(self.progress_slider)
        controls_layout.addLayout(main_controls)

        # Agregar widgets al layout principal
        layout.addWidget(self.video_container, stretch=1)
        layout.addWidget(self.controls_frame)

        self.setLayout(layout)

        # Reproducir video
        media = self.instance.media_new(video_path)
        self.player.set_media(media)
        self.player.play()

        # Conectar eventos del mouse
        self.installEventFilter(self)
        self.video_container.installEventFilter(self)

        # Iniciar timer
        self.hide_controls_timer.start()


    def toggle_pip(self):
        """Alternar modo Picture in Picture"""
        if not self.is_pip_mode:
            self.original_geometry = self.geometry()
            screen = QApplication.primaryScreen().geometry()
            pip_width = 320
            pip_height = 180
            self.setGeometry(
                screen.width() - pip_width - 20,
                screen.height() - pip_height - 20,
                pip_width,
                pip_height
            )
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setGeometry(self.original_geometry)
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)

        self.is_pip_mode = not self.is_pip_mode
        self.show()

    def _change_speed(self, speed_text):
        """Cambiar velocidad de reproducción"""
        speed = float(speed_text.replace('x', ''))
        self.player.set_rate(speed)

    def toggle_play(self):
        if self.player.is_playing():
            self.player.pause()
            self.play_button.setText("▶")
        else:
            self.player.play()
            self.play_button.setText("⏸")

    def stop(self):
        self.player.stop()
        self.play_button.setText("▶")

    def _seek(self, position):
        """Buscar posición en el video"""
        if self.player.get_length() > 0:
            pos = position / 1000.0
            self.player.set_position(pos)

    def _update_progress(self):
        """Actualizar barra de progreso y tiempo"""
        if not self.player.is_playing():
            return

        length = self.player.get_length()
        if length > 0:
            position = self.player.get_position()
            self.progress_slider.setValue(int(position * 1000))

            # Actualizar etiqueta de tiempo
            current_ms = int(position * length)
            length_ms = length

            current_time = QTime(0, 0)
            current_time = current_time.addMSecs(current_ms)

            total_time = QTime(0, 0)
            total_time = total_time.addMSecs(length_ms)

            time_format = "mm:ss"
            time_text = f"{current_time.toString(time_format)} / {total_time.toString(time_format)}"
            self.time_label.setText(time_text)

    def closeEvent(self, event):
        self.update_timer.stop()
        self.hide_controls_timer.stop()
        self.player.stop()
        event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.player:
            self.player.video_set_scale(0)  # Auto-scale

    def eventFilter(self, obj, event):
        if event.type() == event.MouseMove:
            self.show_controls()
            self.hide_controls_timer.start()  # Reiniciar timer
        return super().eventFilter(obj, event)

    def show_controls(self):
        if not self.controls_visible:
            self.controls_frame.show()
            self.controls_visible = True

    def hide_controls(self):
        if self.controls_visible:
            self.controls_frame.hide()
            self.controls_visible = False