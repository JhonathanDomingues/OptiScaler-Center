"""
Widget de Card de Jogo
Card individual para exibição em grid, estilo Steam
"""
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QMenu, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QCursor
from pathlib import Path
from typing import Optional
import shutil

from domain.entities.game import Game
from domain.enums.installation_status import InstallationStatus
from presentation.styles.modern_theme import GAME_CARD_STYLE


class GameCardWidget(QFrame):
    """Card de jogo para exibição em grid"""
    
    # Sinais
    clicked = pyqtSignal(Game)
    install_requested = pyqtSignal(Game)
    uninstall_requested = pyqtSignal(Game)
    configure_requested = pyqtSignal(Game)
    change_image_requested = pyqtSignal(Game)
    
    def __init__(self, game: Game, parent=None):
        super().__init__(parent)
        
        self.game = game
        self.setObjectName("gameCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Aplicar estilo
        self.setStyleSheet(GAME_CARD_STYLE)
        
        # Tamanho do card - ajustado para formato vertical
        self.setFixedSize(200, 320)
        
        self._init_ui()
    
    def _init_ui(self):
        """Inicializa interface do card"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Imagem do jogo - formato vertical
        self.image_label = QLabel()
        self.image_label.setObjectName("gameImage")
        self.image_label.setFixedSize(200, 300)
        self.image_label.setScaledContents(False)
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
            try:
                pixmap = QPixmap(str(image_path))
                if not pixmap.isNull():
                    # Redimensionar mantendo proporção para preencher o card
                    pixmap = pixmap.scaled(
                        200, 300,
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    # Centralizar crop se necessário
                    if pixmap.width() > 200 or pixmap.height() > 300:
                        x_offset = (pixmap.width() - 200) // 2
                        y_offset = (pixmap.height() - 300) // 2
                        pixmap = pixmap.copy(x_offset, y_offset, 200, 300)
                    
                    self.image_label.setPixmap(pixmap)
                    return
            except Exception as e:
                print(f"Erro ao carregar imagem de {image_path}: {e}")
        
        # Debug: mostrar por que não carregou
        if self.game.appid:
            print(f"Imagem não encontrada para {self.game.name} (AppID: {self.game.appid})")
        else:
            print(f"Imagem não encontrada para {self.game.name} (sem AppID)")
        
        # Criar placeholder
        self._create_placeholder()
    
    def _get_steam_grid_image(self) -> Optional[Path]:
        """Obtém caminho da imagem grid do Steam"""
        if not self.game.appid:
            return None
        
        # Verificar cache customizado primeiro
        custom_image = self._get_custom_image_path()
        if custom_image and custom_image.exists():
            return custom_image
        
        import platform
        
        # Diretórios base do Steam
        steam_cache_dirs = []
        
        if platform.system() == "Linux":
            steam_cache_dirs = [
                Path.home() / ".local" / "share" / "Steam" / "appcache" / "librarycache",
                Path.home() / ".steam" / "steam" / "appcache" / "librarycache",
            ]
        elif platform.system() == "Windows":
            import os
            program_files = os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')
            steam_cache_dirs = [
                Path(program_files) / "Steam" / "appcache" / "librarycache",
            ]
        
        # Buscar imagens para este AppID
        for cache_dir in steam_cache_dirs:
            if not cache_dir.exists():
                continue
            
            # Nova estrutura: diretório por AppID com subdiretórios hash
            appid_dir = cache_dir / str(self.game.appid)
            if appid_dir.exists():
                # Priorizar library_capsule (300x450 - vertical perfeito)
                for img_name in ['library_capsule.jpg', 'portrait.png', 'library_hero.jpg', 'library_header.jpg', 'logo.png']:
                    found_images = list(appid_dir.rglob(img_name))
                    if found_images:
                        return found_images[0]
            
            # Estrutura antiga: arquivos diretos com padrão appid_tipo.jpg
            for img_pattern in [
                f"{self.game.appid}_library_600x900.jpg",
                f"{self.game.appid}_library_hero.jpg",
                f"{self.game.appid}_header.jpg",
            ]:
                img_path = cache_dir / img_pattern
                if img_path.exists():
                    return img_path
        
        return None
    
    def _create_placeholder(self):
        """Cria imagem placeholder"""
        pixmap = QPixmap(200, 300)
        pixmap.fill(QColor("#0e1419"))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Desenhar borda
        pen = QPen(QColor("#2a475e"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(1, 1, 198, 298)
        
        # Desenhar texto com nome do jogo
        painter.setPen(QColor("#8f98a0"))
        from PyQt6.QtGui import QFont
        from PyQt6.QtCore import QRect
        
        font = QFont()
        font.setPixelSize(14)
        font.setBold(True)
        painter.setFont(font)
        
        game_name = self.game.name[:40] + ("..." if len(self.game.name) > 40 else "")
        painter.drawText(
            QRect(10, 10, 180, 280),
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter,
            game_name
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
        configure_action = menu.addAction("⚙️ Configurações")
        change_image_action = menu.addAction("🖼️ Alterar Imagem")
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
        configure_action.triggered.connect(lambda: self.configure_requested.emit(self.game))
        change_image_action.triggered.connect(lambda: self._change_image())
        info_action.triggered.connect(lambda: self.clicked.emit(self.game))
        
        # Mostrar menu
        menu.exec(self.mapToGlobal(pos))
    
    def _get_custom_image_path(self) -> Optional[Path]:
        """Obtém caminho da imagem customizada"""
        # Cache de imagens customizadas em resources/game_images/
        from utils.constants import RESOURCES_DIR
        
        custom_images_dir = RESOURCES_DIR / "game_images"
        
        # Tentar por appid primeiro, depois por nome do jogo
        if self.game.appid:
            custom_path = custom_images_dir / f"{self.game.appid}.jpg"
            if custom_path.exists():
                return custom_path
            custom_path = custom_images_dir / f"{self.game.appid}.png"
            if custom_path.exists():
                return custom_path
        
        # Tentar por nome (sanitizado)
        safe_name = "".join(c for c in self.game.name if c.isalnum() or c in (' ', '-', '_')).strip()
        custom_path = custom_images_dir / f"{safe_name}.jpg"
        if custom_path.exists():
            return custom_path
        custom_path = custom_images_dir / f"{safe_name}.png"
        if custom_path.exists():
            return custom_path
        
        return None
    
    def _change_image(self):
        """Abre diálogo para selecionar nova imagem"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Imagem do Jogo",
            str(Path.home()),
            "Imagens (*.png *.jpg *.jpeg *.bmp);;Todos os arquivos (*)"
        )
        
        if file_path:
            self.set_custom_image(Path(file_path))
    
    def set_custom_image(self, image_path: Path):
        """Define imagem customizada para o jogo"""
        try:
            from utils.constants import RESOURCES_DIR
            
            # Criar diretório se não existir
            custom_images_dir = RESOURCES_DIR / "game_images"
            custom_images_dir.mkdir(parents=True, exist_ok=True)
            
            # Determinar nome do arquivo
            if self.game.appid:
                target_name = f"{self.game.appid}{image_path.suffix}"
            else:
                safe_name = "".join(c for c in self.game.name if c.isalnum() or c in (' ', '-', '_')).strip()
                target_name = f"{safe_name}{image_path.suffix}"
            
            target_path = custom_images_dir / target_name
            
            # Copiar imagem
            shutil.copy2(image_path, target_path)
            
            # Recarregar imagem
            self._load_game_image()
            
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Erro",
                f"Falha ao definir imagem:\n{e}"
            )
