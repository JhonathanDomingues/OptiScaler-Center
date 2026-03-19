"""
Widget de Card de Jogo
Card individual para exibição em grid, estilo Steam
"""
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QCursor
from pathlib import Path
from typing import Optional

from domain.entities.game import Game
from domain.enums.installation_status import InstallationStatus
from presentation.styles.modern_theme import GAME_CARD_STYLE


class GameCardWidget(QFrame):
    """Card de jogo para exibição em grid"""
    
    # Sinais
    clicked = pyqtSignal(Game)
    install_requested = pyqtSignal(Game)
    uninstall_requested = pyqtSignal(Game)
    
    def __init__(self, game: Game, parent=None):
        super().__init__(parent)
        
        self.game = game
        self.setObjectName("gameCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Aplicar estilo
        self.setStyleSheet(GAME_CARD_STYLE)
        
        # Tamanho do card
        self.setFixedSize(280, 380)
        
        self._init_ui()
    
    def _init_ui(self):
        """Inicializa interface do card"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Imagem do jogo
        self.image_label = QLabel()
        self.image_label.setObjectName("gameImage")
        self.image_label.setFixedSize(280, 135)
        self.image_label.setScaledContents(True)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Carregar imagem ou placeholder
        self._load_game_image()
        
        layout.addWidget(self.image_label)
        
        # Container de informações
        info_container = QWidget()
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(12, 12, 12, 12)
        info_layout.setSpacing(8)
        
        # Nome do jogo
        self.name_label = QLabel(self.game.name)
        self.name_label.setObjectName("gameName")
        self.name_label.setWordWrap(True)
        self.name_label.setMaximumHeight(50)
        info_layout.addWidget(self.name_label)
        
        # Status de instalação
        if self.game.installation_status == InstallationStatus.INSTALLED:
            installed_label = QLabel("✓ OptiScaler Instalado")
            installed_label.setObjectName("installed")
            info_layout.addWidget(installed_label)
        
        # Badges de tecnologias suportadas
        tech_layout = QHBoxLayout()
        tech_layout.setSpacing(6)
        
        if self.game.has_dlss:
            dlss_badge = self._create_tech_badge("DLSS", "DLSS")
            tech_layout.addWidget(dlss_badge)
        
        if self.game.has_fsr:
            fsr_badge = self._create_tech_badge("FSR", "FSR")
            tech_layout.addWidget(fsr_badge)
        
        if self.game.has_xess:
            xess_badge = self._create_tech_badge("XeSS", "XeSS")
            tech_layout.addWidget(xess_badge)
        
        tech_layout.addStretch()
        info_layout.addLayout(tech_layout)
        
        info_layout.addStretch()
        
        # Botões de ação
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        if self.game.installation_status == InstallationStatus.INSTALLED:
            # Botão de desinstalar
            uninstall_btn = QPushButton("Desinstalar")
            uninstall_btn.setObjectName("danger")
            uninstall_btn.setMaximumWidth(130)
            uninstall_btn.clicked.connect(lambda: self.uninstall_requested.emit(self.game))
            button_layout.addWidget(uninstall_btn)
        else:
            # Botão de instalar
            if len(self.game.supported_dlls) > 0:
                install_btn = QPushButton("Instalar")
                install_btn.setMaximumWidth(130)
                install_btn.clicked.connect(lambda: self.install_requested.emit(self.game))
                button_layout.addWidget(install_btn)
        
        button_layout.addStretch()
        info_layout.addLayout(button_layout)
        
        info_container.setLayout(info_layout)
        layout.addWidget(info_container)
        
        self.setLayout(layout)
    
    def _create_tech_badge(self, text: str, tech_type: str) -> QLabel:
        """Cria badge de tecnologia"""
        badge = QLabel(text)
        badge.setObjectName("techBadge")
        badge.setProperty("tech", tech_type)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(GAME_CARD_STYLE)
        return badge
    
    def _load_game_image(self):
        """Carrega imagem do jogo ou cria placeholder"""
        # Tentar carregar imagem da cache do Steam
        image_path = self._get_steam_grid_image()
        
        if image_path and image_path.exists():
            pixmap = QPixmap(str(image_path))
            self.image_label.setPixmap(pixmap)
        else:
            # Criar placeholder
            self._create_placeholder()
    
    def _get_steam_grid_image(self) -> Optional[Path]:
        """Obtém caminho da imagem grid do Steam"""
        if not self.game.appid:
            return None
        
        # Padrão: Steam/appcache/librarycache/{appid}_library_600x900.jpg
        # Também tentar: Steam/appcache/librarycache/{appid}_header.jpg
        
        possible_paths = [
            Path.home() / ".steam" / "steam" / "appcache" / "librarycache" / f"{self.game.appid}_library_600x900.jpg",
            Path.home() / ".local" / "share" / "Steam" / "appcache" / "librarycache" / f"{self.game.appid}_library_600x900.jpg",
            Path.home() / ".steam" / "steam" / "appcache" / "librarycache" / f"{self.game.appid}_header.jpg",
            Path.home() / ".local" / "share" / "Steam" / "appcache" / "librarycache" / f"{self.game.appid}_header.jpg",
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    def _create_placeholder(self):
        """Cria imagem placeholder"""
        pixmap = QPixmap(280, 135)
        pixmap.fill(QColor("#0e1419"))
        
        # Desenhar ícone de jogo
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Desenhar borda
        pen = QPen(QColor("#2a475e"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(0, 0, 280, 135)
        
        # Desenhar texto
        painter.setPen(QColor("#8f98a0"))
        painter.drawText(
            pixmap.rect(),
            Qt.AlignmentFlag.AlignCenter,
            "🎮\n" + self.game.name[:30] + ("..." if len(self.game.name) > 30 else "")
        )
        
        painter.end()
        
        self.image_label.setPixmap(pixmap)
    
    def mousePressEvent(self, event):
        """Evento de clique no card"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.game)
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.pos())
        
        super().mousePressEvent(event)
    
    def _show_context_menu(self, pos):
        """Mostra menu de contexto"""
        menu = QMenu(self)
        
        # Ações
        install_action = menu.addAction("⚙ Instalar OptiScaler")
        uninstall_action = menu.addAction("✗ Desinstalar OptiScaler")
        menu.addSeparator()
        info_action = menu.addAction("ℹ Ver Detalhes")
        
        # Habilitar/desabilitar baseado no estado
        install_action.setEnabled(
            self.game.installation_status != InstallationStatus.INSTALLED
            and len(self.game.supported_dlls) > 0
        )
        uninstall_action.setEnabled(
            self.game.installation_status == InstallationStatus.INSTALLED
        )
        
        # Conectar ações
        install_action.triggered.connect(lambda: self.install_requested.emit(self.game))
        uninstall_action.triggered.connect(lambda: self.uninstall_requested.emit(self.game))
        info_action.triggered.connect(lambda: self.clicked.emit(self.game))
        
        # Mostrar menu
        menu.exec(self.mapToGlobal(pos))
