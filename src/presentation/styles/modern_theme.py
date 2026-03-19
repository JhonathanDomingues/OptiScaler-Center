"""
Tema moderno para OptiScaler Center
Estilo inspirado na interface da Steam
"""

MODERN_THEME = """
/* === Cores Base === */
QWidget {
    background-color: #1b2838;
    color: #c7d5e0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

/* === Barra de Ferramentas === */
QWidget#toolbar {
    background-color: #171a21;
    border-bottom: 2px solid #2a475e;
    padding: 10px;
}

/* === Botões === */
QPushButton {
    background-color: #5c7e10;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #6c9010;
}

QPushButton:pressed {
    background-color: #4a6609;
}

QPushButton:disabled {
    background-color: #3a3f44;
    color: #666;
}

QPushButton#secondary {
    background-color: #2a475e;
}

QPushButton#secondary:hover {
    background-color: #3a5770;
}

QPushButton#danger {
    background-color: #c7402b;
}

QPushButton#danger:hover {
    background-color: #d74d35;
}

/* === ComboBox === */
QComboBox {
    background-color: #2a475e;
    color: #c7d5e0;
    border: 1px solid #1b2838;
    border-radius: 4px;
    padding: 6px 10px;
    min-width: 150px;
}

QComboBox:hover {
    border-color: #5c7e10;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid #c7d5e0;
    width: 0;
    height: 0;
}

QComboBox QAbstractItemView {
    background-color: #2a475e;
    color: #c7d5e0;
    selection-background-color: #5c7e10;
    border: 1px solid #1b2838;
}

/* === ScrollArea e ScrollBar === */
QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollBar:vertical {
    background-color: #1b2838;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #3a5770;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #5c7e10;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #1b2838;
    height: 12px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: #3a5770;
    border-radius: 6px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #5c7e10;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* === GroupBox === */
QGroupBox {
    background-color: #16202d;
    border: 1px solid #2a475e;
    border-radius: 6px;
    margin-top: 12px;
    padding: 15px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 5px 10px;
    background-color: #2a475e;
    border-radius: 4px;
    color: #c7d5e0;
}

/* === Labels === */
QLabel {
    color: #c7d5e0;
    background-color: transparent;
}

QLabel#title {
    font-size: 18px;
    font-weight: bold;
    color: #ffffff;
}

QLabel#subtitle {
    font-size: 12px;
    color: #8f98a0;
}

/* === TextEdit === */
QTextEdit {
    background-color: #0e1419;
    color: #c7d5e0;
    border: 1px solid #2a475e;
    border-radius: 4px;
    padding: 8px;
}

/* === ProgressBar === */
QProgressBar {
    background-color: #0e1419;
    border: 1px solid #2a475e;
    border-radius: 4px;
    text-align: center;
    color: #c7d5e0;
    height: 20px;
}

QProgressBar::chunk {
    background-color: #5c7e10;
    border-radius: 3px;
}

/* === Splitter === */
QSplitter::handle {
    background-color: #2a475e;
    width: 2px;
}

QSplitter::handle:hover {
    background-color: #5c7e10;
}

/* === MessageBox === */
QMessageBox {
    background-color: #1b2838;
}

QMessageBox QLabel {
    color: #c7d5e0;
}

QMessageBox QPushButton {
    min-width: 80px;
}
"""

# Estilos específicos para Game Card
GAME_CARD_STYLE = """
QFrame#gameCard {
    background-color: #16202d;
    border: 2px solid #2a475e;
    border-radius: 8px;
}

QFrame#gameCard:hover {
    border-color: #5c7e10;
    background-color: #1d2a3a;
}

QLabel#gameName {
    font-size: 14px;
    font-weight: bold;
    color: #ffffff;
}

QLabel#gameImage {
    background-color: #0e1419;
    border-radius: 4px;
}

QLabel#techBadge {
    background-color: #2a475e;
    color: #c7d5e0;
    border-radius: 3px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: bold;
}

QLabel#techBadge[tech="DLSS"] {
    background-color: #76b900;
    color: #000000;
}

QLabel#techBadge[tech="FSR"] {
    background-color: #dc3545;
    color: #ffffff;
}

QLabel#techBadge[tech="XeSS"] {
    background-color: #0071c5;
    color: #ffffff;
}

QLabel#installed {
    background-color: #5c7e10;
    color: #ffffff;
    border-radius: 3px;
    padding: 2px 6px;
    font-size: 10px;
    font-weight: bold;
}
"""


def apply_modern_theme(app):
    """Aplica o tema moderno na aplicação"""
    app.setStyleSheet(MODERN_THEME)
