"""
Gerador de ícone da aplicação
Cria um ícone de controle de videogame
"""
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QIcon
from PyQt6.QtCore import Qt, QRect


def create_app_icon(size: int = 64) -> QIcon:
    """Cria ícone de controle para a aplicação"""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Cores
    bg_color = QColor("#1b2838")
    border_color = QColor("#5c7e10")
    detail_color = QColor("#8fbc8f")
    
    # Corpo do controle
    painter.setPen(QPen(border_color, 2))
    painter.setBrush(bg_color)
    
    # Corpo principal (retângulo arredondado)
    body_rect = QRect(int(size * 0.15), int(size * 0.3), int(size * 0.7), int(size * 0.45))
    painter.drawRoundedRect(body_rect, size * 0.15, size * 0.15)
    
    # Gatilhos superiores (L/R)
    painter.setPen(QPen(border_color, 1.5))
    # Gatilho esquerdo
    painter.drawRect(int(size * 0.2), int(size * 0.15), int(size * 0.2), int(size * 0.12))
    # Gatilho direito
    painter.drawRect(int(size * 0.6), int(size * 0.15), int(size * 0.2), int(size * 0.12))
    
    painter.setPen(QPen(detail_color, 2))
    
    # D-pad (esquerda)
    dpad_x = int(size * 0.28)
    dpad_y = int(size * 0.45)
    dpad_size = int(size * 0.12)
    
    # Vertical
    painter.drawLine(
        dpad_x + dpad_size // 2, dpad_y,
        dpad_x + dpad_size // 2, dpad_y + dpad_size
    )
    # Horizontal
    painter.drawLine(
        dpad_x, dpad_y + dpad_size // 2,
        dpad_x + dpad_size, dpad_y + dpad_size // 2
    )
    
    # Botões (direita) - estilo ABXY
    button_x = int(size * 0.62)
    button_y = int(size * 0.45)
    button_radius = int(size * 0.05)
    
    painter.setBrush(detail_color)
    
    # Botão cima (Y)
    painter.drawEllipse(
        button_x + button_radius, button_y,
        button_radius * 2, button_radius * 2
    )
    # Botão direita (B)
    painter.drawEllipse(
        button_x + button_radius * 2, button_y + button_radius,
        button_radius * 2, button_radius * 2
    )
    # Botão baixo (A)
    painter.drawEllipse(
        button_x + button_radius, button_y + button_radius * 2,
        button_radius * 2, button_radius * 2
    )
    # Botão esquerda (X)
    painter.drawEllipse(
        button_x, button_y + button_radius,
        button_radius * 2, button_radius * 2
    )
    
    # Analógicos (pequenos círculos)
    painter.setBrush(bg_color)
    painter.setPen(QPen(detail_color, 1.5))
    
    # Analógico esquerdo
    painter.drawEllipse(
        int(size * 0.35), int(size * 0.58),
        int(size * 0.1), int(size * 0.1)
    )
    
    # Analógico direito
    painter.drawEllipse(
        int(size * 0.55), int(size * 0.58),
        int(size * 0.1), int(size * 0.1)
    )
    
    painter.end()
    
    return QIcon(pixmap)
