"""
Tema moderno para OptiScaler Center
Estilo inspirado na interface da Steam
"""

MODERN_THEME = """
/* === Cores Base (Tema Bazzite) === */
QWidget {
    background-color: #0f172a;
    color: #c7d5e0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

/* === Barra de Ferramentas === */
QWidget#toolbar {
    background-color: #0a1020;
    border-bottom: 2px solid #1e3a5f;
    padding: 10px;
}

/* === Botões === */
QPushButton {
    background-color: #6b21a8;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #7c3aed;
}

QPushButton:pressed {
    background-color: #581c87;
}

QPushButton:disabled {
    background-color: #3a3f44;
    color: #666;
}

QPushButton#secondary {
    background-color: #1e3a5f;
}

QPushButton#secondary:hover {
    background-color: #2a4f7a;
}

QPushButton#danger {
    background-color: #c7402b;
}

QPushButton#danger:hover {
    background-color: #d74d35;
}

/* === ComboBox === */
QComboBox {
    background-color: #1e3a5f;
    color: #c7d5e0;
    border: 1px solid #0f172a;
    border-radius: 4px;
    padding: 6px 10px;
    min-width: 150px;
}

QComboBox:hover {
    border-color: #7c3aed;
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
    background-color: #1e3a5f;
    color: #c7d5e0;
    selection-background-color: #6b21a8;
    border: 1px solid #0f172a;
}

/* === ScrollArea e ScrollBar === */
QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollBar:vertical {
    background-color: #0f172a;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #4c1d95;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #7c3aed;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #0f172a;
    height: 12px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: #4c1d95;
    border-radius: 6px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #7c3aed;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* === GroupBox === */
QGroupBox {
    background-color: #0d1526;
    border: 1px solid #1e3a5f;
    border-radius: 6px;
    margin-top: 12px;
    padding: 15px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 5px 10px;
    background-color: #1e3a5f;
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
    background-color: #080e1a;
    color: #c7d5e0;
    border: 1px solid #1e3a5f;
    border-radius: 4px;
    padding: 8px;
}

/* === ProgressBar === */
QProgressBar {
    background-color: #080e1a;
    border: 1px solid #1e3a5f;
    border-radius: 4px;
    text-align: center;
    color: #c7d5e0;
    height: 20px;
}

QProgressBar::chunk {
    background-color: #6b21a8;
    border-radius: 3px;
}

/* === Splitter === */
QSplitter::handle {
    background-color: #1e3a5f;
    width: 2px;
}

QSplitter::handle:hover {
    background-color: #7c3aed;
}

/* === MessageBox === */
QMessageBox {
    background-color: #0f172a;
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
    background-color: #0d1526;
    border: 2px solid #1e3a5f;
    border-radius: 8px;
}

QFrame#gameCard:hover {
    border-color: #7c3aed;
    background-color: #111d33;
}

QLabel#gameName {
    font-size: 14px;
    font-weight: bold;
    color: #ffffff;
}

QLabel#gameImage {
    background-color: #080e1a;
    border-radius: 4px;
}

QLabel#techBadge {
    background-color: #1e3a5f;
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
    background-color: #6b21a8;
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
