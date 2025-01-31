# Estilos globales de la aplicación
STYLES = """
QMainWindow {
    background-color: #1E1E1E;
}

QWidget {
    background-color: transparent;
}

QGroupBox {
    background-color: #2D2D2D;
    border: 1px solid #3D3D3D;
    border-radius: 5px;
    margin-top: 1ex;
    color: #E0E0E0;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 3px;
    color: #E0E0E0;
}

QTabWidget::pane {
    border: 1px solid #3D3D3D;
    background: #2D2D2D;
}

QTabBar::tab {
    background: #2D2D2D;
    color: #E0E0E0;
    padding: 8px 20px;
    border: 1px solid #3D3D3D;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background: #007ACC;
}

QLabel {
    color: #E0E0E0;
    font-size: 14px;
}

QLineEdit {
    padding: 8px;
    border: 1px solid #3D3D3D;
    border-radius: 4px;
    background: #2D2D2D;
    color: #E0E0E0;
}

QComboBox {
    padding: 8px;
    border: 1px solid #3D3D3D;
    border-radius: 4px;
    background: #2D2D2D;
    color: #E0E0E0;
}

QComboBox:hover {
    background: #3D3D3D;
    border: 1px solid #4D4D4D;
}

QComboBox::drop-down {
    border: none;
}

QComboBox::down-arrow {
    image: none;
    border: none;
}

QPushButton {
    padding: 10px 20px;
    border-radius: 4px;
    font-weight: bold;
    background-color: #2D2D2D;
    color: #E0E0E0;
    border: 1px solid #3D3D3D;
}

QPushButton:hover {
    background-color: #3D3D3D;
    border: 1px solid #4D4D4D;
}

QPushButton[class="primary-button"] {
    background-color: #007ACC;
    color: #E0E0E0;
    border: none;
}

QPushButton[class="primary-button"]:hover {
    background-color: #0098FF;
}

QPushButton[class="danger-button"] {
    background-color: #FF3B30;
    color: #E0E0E0;
    border: none;
}

QPushButton[class="danger-button"]:hover {
    background-color: #FF6B60;
}

QProgressBar {
    border: 1px solid #3D3D3D;
    border-radius: 4px;
    text-align: center;
    background: #2D2D2D;
    color: #E0E0E0;
}

QProgressBar::chunk {
    background-color: #007ACC;
}

QListWidget {
    background: #2b2b2b;
    border: 1px solid #3d3d3d;
    outline: none;
    padding: 2px;
    border-radius: 8px;
}

QListWidget::item {
    padding: 0;
    margin: 1px 2px;
    background: transparent;
    border-radius: 6px;
}

QListWidget::item:selected {
    background: #0078d4;
    border-radius: 6px;
}

QListWidget::item:hover:!selected {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 6px;
}

QWidget#ListItemWidget {
    background: transparent;
    margin: 0;
    padding: 0;
    border-radius: 6px;
}

QLabel#ListItemLabel {
    background: transparent;
    color: white;
    padding: 0;
    margin: 0;
}

QCheckBox {
    background: transparent;
    padding: 0;
    margin: 0;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #666;
    background: transparent;
}

QCheckBox::indicator:checked {
    background: #0078d4;
    border: 1px solid #0078d4;
    image: url(check.png);  /* Puedes agregar un ícono de check si lo deseas */
}


/* Estilos para los widgets dentro de los items */
#ListItemLabel {
    color: #ffffff;
    background: transparent;
}

QListWidget::item:selected #ListItemLabel {
    color: white;
}

/* Checkbox dentro de los items */
QCheckBox {
    background: transparent;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #666;
}

QCheckBox::indicator:checked {
    background: #0078d4;
    border: 1px solid #0078d4;
}

/* Widget contenedor del item */
QWidget#ListItemWidget {
    background: transparent;
}

QWidget#ListItemWidget:selected {
    background: #0078d4;
}

/* Estilo específico para el label dentro del item */
QLabel#ListItemLabel {
    background-color: transparent;
    color: #E0E0E0;
}

QSlider::groove:horizontal {
    border: 1px solid #3D3D3D;
    height: 8px;
    background: #2D2D2D;
    margin: 2px 0;
    border-radius: 4px;
}

QSlider::handle:horizontal {
    background: #007ACC;
    border: 1px solid #0098FF;
    width: 18px;
    margin: -5px 0;
    border-radius: 9px;
}

QSlider::handle:horizontal:hover {
    background: #0098FF;
}

QCheckBox {
    color: #E0E0E0;
    padding: 5px;
    background-color: transparent;
}

QCheckBox::indicator {
    width: 15px;
    height: 15px;
    background-color: #2D2D2D;
    border: 1px solid #3D3D3D;
    border-radius: 2px;
}

QCheckBox::indicator:hover {
    border: 1px solid #007ACC;
}

QCheckBox::indicator:checked {
    background-color: #007ACC;
    border: 1px solid #007ACC;
}

QCheckBox::indicator:checked:hover {
    background-color: #0098FF;
    border: 1px solid #0098FF;
}

QScrollArea {
    border: 1px solid #3D3D3D;
    border-radius: 5px;
    background-color: #1E1E1E;
}

QTextEdit {
    background-color: #1E1E1E;
    color: #E0E0E0;
    font-family: 'Courier New', monospace;
    font-size: 12px;
    padding: 10px;
}

/* Estilos para el reproductor de video */
#VideoPlayerWindow {
    background-color: #1E1E1E;
    color: #E0E0E0;
}

#VideoContainer {
    background-color: black;
}

#ControlsFrame {
    background-color: rgba(45, 45, 45, 0.9);
    border-top: 1px solid #3D3D3D;
}

/* Estilos específicos para el área de descargas */
#downloads_list {
    background-color: #2D2D2D;
}

#downloads_list QWidget {
    background-color: #2D2D2D;
}

#DownloadsScrollArea {
    background-color: #2D2D2D;
    border: 1px solid #3D3D3D;
}

#DownloadsScrollArea QWidget {
    background-color: #2D2D2D;
}

/* Ajuste del marco de canciones activas */
QFrame#MusicPlayerFrame {
    background-color: #2D2D2D;
    border: 1px solid #3D3D3D;
    border-radius: 5px;
    margin: 5px;
    padding: 5px;
}
"""