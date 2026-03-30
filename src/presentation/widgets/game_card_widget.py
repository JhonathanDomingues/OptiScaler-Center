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
from utils.i18n import tr


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
        
        # Tamanho do card - responsivo com min/max
        self.setMinimumSize(180, 300)
        self.setMaximumSize(240, 380)
        
        self._init_ui()
    
    def _init_ui(self):
        """Inicializa interface do card"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Imagem do jogo - formato vertical responsivo
        self.image_label = QLabel()
        self.image_label.setObjectName("gameImage")
        self.image_label.setMinimumHeight(240)
        self.image_label.setSizePolicy(
            self.sizePolicy().Policy.Expanding,
            self.sizePolicy().Policy.Expanding
        )
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
            installed_label = QLabel(tr("card_installed"))
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
            uninstall_btn = QPushButton(tr("card_btn_uninstall"))
            uninstall_btn.setObjectName("danger")
            uninstall_btn.setMaximumWidth(130)
            uninstall_btn.clicked.connect(lambda: self.uninstall_requested.emit(self.game))
            button_layout.addWidget(uninstall_btn)
        else:
            # Mostrar botão para todos os jogos — OptiScaler é compatível com
            # jogos UE4/UE5 mesmo sem DLLs de upscaling detectadas.
            install_btn = QPushButton(tr("card_btn_install"))
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
                    # Redimensionar mantendo proporção
                    card_width = max(200, self.width())
                    card_height = max(280, int(card_width * 1.4))
                    
                    pixmap = pixmap.scaled(
                        card_width, card_height,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    
                    # Se a imagem for menor que o card, centralizar em fundo escuro
                    if pixmap.width() < card_width or pixmap.height() < card_height:
                        final_pixmap = QPixmap(card_width, card_height)
                        final_pixmap.fill(QColor("#0e1419"))
                        
                        painter = QPainter(final_pixmap)
                        x_offset = (card_width - pixmap.width()) // 2
                        y_offset = (card_height - pixmap.height()) // 2
                        painter.drawPixmap(x_offset, y_offset, pixmap)
                        painter.end()
                        
                        self.image_label.setPixmap(final_pixmap)
                    else:
                        self.image_label.setPixmap(pixmap)
                    
                    return
            except Exception as e:
                print(f"Erro ao carregar imagem de {image_path}: {e}")
        
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
                # Buscar cada tipo de imagem em ordem de prioridade (vertical primeiro)
                # library_capsule.jpg é SEMPRE vertical (300x450) - prioridade máxima
                capsule_images = list(appid_dir.rglob('library_capsule.jpg'))
                if capsule_images:
                    return capsule_images[0]
                
                # portrait.png também é vertical
                portrait_images = list(appid_dir.rglob('portrait.png'))
                if portrait_images:
                    return portrait_images[0]
                
                # Verificar dimensões das outras imagens para preferir verticais
                for img_name in ['library_hero.jpg', 'library_header.jpg', 'logo.png']:
                    found_images = list(appid_dir.rglob(img_name))
                    if found_images:
                        # Verificar se é vertical ou pelo menos não muito horizontal
                        img_path = found_images[0]
                        try:
                            test_pixmap = QPixmap(str(img_path))
                            if not test_pixmap.isNull():
                                width = test_pixmap.width()
                                height = test_pixmap.height()
                                # Aceitar imagens verticais (altura >= largura)
                                # OU imagens não muito horizontais (largura <= 2.5x altura)
                                # Isso aceita 640x360, 1920x1080 mas rejeita 1920x620
                                if height >= width or width <= (height * 2.5):
                                    return img_path
                        except:
                            pass
                
                # Se não encontrou nenhuma adequada, usar placeholder ao invés de horizontal
            
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
        """Cria imagem placeholder responsivo"""
        card_width = max(200, self.width())
        card_height = max(280, int(card_width * 1.4))
        
        pixmap = QPixmap(card_width, card_height)
        pixmap.fill(QColor("#0e1419"))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Desenhar borda
        pen = QPen(QColor("#2a475e"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(1, 1, card_width - 2, card_height - 2)
        
        # Desenhar texto com nome do jogo
        painter.setPen(QColor("#8f98a0"))
        from PyQt6.QtGui import QFont
        from PyQt6.QtCore import QRect
        
        font = QFont()
        font.setPixelSize(14)
        font.setBold(True)
        painter.setFont(font)
        
        game_name = self.game.name[:40] + ("..." if len(self.game.name) > 40 else "")
        text_margin = int(card_width * 0.05)
        painter.drawText(
            QRect(text_margin, text_margin, card_width - text_margin * 2, card_height - text_margin * 2),
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter,
            game_name
        )
        
        painter.end()
        self.image_label.setPixmap(pixmap)
    
    def resizeEvent(self, event):
        """Recarrega imagem quando o card é redimensionado"""
        super().resizeEvent(event)
        # Recarregar imagem apenas se o tamanho mudou significativamente
        if hasattr(self, '_last_size'):
            width_diff = abs(event.size().width() - self._last_size.width())
            if width_diff > 20:  # Mudança significativa
                self._load_game_image()
        self._last_size = event.size()
    
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
        install_action = menu.addAction(tr("card_menu_install"))
        uninstall_action = menu.addAction(tr("card_menu_uninstall"))
        menu.addSeparator()
        configure_action = menu.addAction(tr("card_menu_settings"))
        change_image_action = menu.addAction(tr("card_menu_image"))
        menu.addSeparator()
        info_action = menu.addAction(tr("card_menu_details"))
        
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
            tr("card_img_dialog_title"),
            str(Path.home()),
            tr("card_img_dialog_filter")
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
                tr("error_title"),
                tr("card_img_error_msg", error=e)
            )
