"""
Widget de biblioteca de jogos - Interface Moderna
Layout em grid com cards de jogos estilo Steam
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QGridLayout, QGroupBox, QLabel,QPushButton, QComboBox, QProgressBar, QMessageBox,
    QTextEdit, QDialog, QDialogButtonBox, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QIcon
from pathlib import Path
from typing import Optional, List

from utils.logger import LoggerMixin
from domain.entities.game import Game
from domain.enums.dll_type import DLLType
from domain.enums.installation_status import InstallationStatus
from application.use_cases.scan_games import ScanGamesUseCase
from application.use_cases.fetch_versions import FetchVersionsUseCase
from application.use_cases.download_version import DownloadVersionUseCase
from application.use_cases.install_optiscaler import InstallOptiScalerUseCase
from application.use_cases.uninstall_optiscaler import UninstallOptiScalerUseCase
from presentation.widgets.game_card_widget import GameCardWidget
from presentation.styles.modern_theme import MODERN_THEME


class GameLibraryWidget(QWidget, LoggerMixin):
    """Widget principal da biblioteca de jogos com interface moderna"""
    
    def __init__(
        self,
        scan_games_uc: ScanGamesUseCase,
        fetch_versions_uc: FetchVersionsUseCase,
        download_version_uc: DownloadVersionUseCase,
        install_uc: InstallOptiScalerUseCase,
        uninstall_uc: UninstallOptiScalerUseCase
    ):
        super().__init__()
        
        self.scan_games_uc = scan_games_uc
        self.fetch_versions_uc = fetch_versions_uc
        self.download_version_uc = download_version_uc
        self.install_uc = install_uc
        self.uninstall_uc = uninstall_uc
        
        self.current_game: Optional[Game] = None
        self.games: List[Game] = []
        self.filtered_games: List[Game] = []
        self.game_cards: List[GameCardWidget] = []
        
        self._init_ui()
        
        # Carregar jogos salvos
        self._load_existing_games()
    
    def _init_ui(self):
        """Inicializa interface"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Barra de ferramentas superior
        toolbar = self._create_toolbar()
        toolbar.setObjectName("toolbar")
        main_layout.addWidget(toolbar)
        
        # Container principal
        container = QWidget()
        container_layout = QHBoxLayout()
        container_layout.setContentsMargins(15, 15, 15, 15)
        
        # Scroll area para grid de jogos
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Widget container para o grid
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(15)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.grid_container.setLayout(self.grid_layout)
        
        scroll_area.setWidget(self.grid_container)
        container_layout.addWidget(scroll_area, 1)
        
        container.setLayout(container_layout)
        main_layout.addWidget(container)
        
        self.setLayout(main_layout)
        
        # Aplicar tema
        self.setStyleSheet(MODERN_THEME)
    
    def _create_toolbar(self) -> QWidget:
        """Cria barra de ferramentas moderna"""
        toolbar = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)
        
        # Título
        title = QLabel("Biblioteca de Jogos")
        title.setObjectName("title")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Filtro de tecnologia
        layout.addWidget(QLabel("Filtrar:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "Todos os jogos",
            "Com DLSS",
            "Com FSR",
            "Com XeSS",
            "Com qualquer tecnologia",
            "OptiScaler instalado"
        ])
        self.filter_combo.currentIndexChanged.connect(self._apply_filter)
        layout.addWidget(self.filter_combo)
        
        # Botão varrer jogos
        self.scan_btn = QPushButton("🔍 Varrer Jogos")
        self.scan_btn.clicked.connect(self._scan_games)
        layout.addWidget(self.scan_btn)
        
        # Botão atualizar versões
        self.fetch_btn = QPushButton("📥 Buscar Versões")
        self.fetch_btn.clicked.connect(self._fetch_versions)
        layout.addWidget(self.fetch_btn)
        
        # Contador de jogos
        self.game_count_label = QLabel("0 jogos")
        self.game_count_label.setObjectName("subtitle")
        layout.addWidget(self.game_count_label)
        
        toolbar.setLayout(layout)
        return toolbar
    
    def _load_existing_games(self):
        """Carrega jogos já salvos no banco"""
        try:
            self.games = self.scan_games_uc.get_all_games()
            self.filtered_games = self.games.copy()
            self._refresh_grid()
        except Exception as e:
            self.logger.warning(f"Nenhum jogo carregado: {e}")
    
    def _refresh_grid(self):
        """Atualiza grid de jogos"""
        # Limpar grid existente
        for card in self.game_cards:
            card.deleteLater()
        self.game_cards.clear()
        
        # Limpar layout
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Adicionar cards com cálculo responsivo
        # 280 (largura card) + 15 (spacing) = 295px por card
        available_width = self.grid_container.width()
        columns = max(1, available_width // 295)
        
        for idx, game in enumerate(self.filtered_games):
            row = idx // columns
            col = idx % columns
            
            card = GameCardWidget(game)
            card.clicked.connect(self._on_game_clicked)
            card.install_requested.connect(self._on_install_requested)
            card.uninstall_requested.connect(self._on_uninstall_requested)
            
            self.game_cards.append(card)
            self.grid_layout.addWidget(card, row, col)
        
        # Atualizar contador
        self.game_count_label.setText(f"{len(self.filtered_games)} jogos")
    
    def resizeEvent(self, event):
        """Reorganiza grid quando janela é redimensionada"""
        super().resizeEvent(event)
        
        # Reorganizar grid apenas se houver jogos
        if hasattr(self, 'game_cards') and self.game_cards and hasattr(self, 'grid_container'):
            # Agendar reorganização para evitar múltiplas chamadas
            from PyQt6.QtCore import QTimer
            if not hasattr(self, '_resize_timer'):
                self._resize_timer = QTimer()
                self._resize_timer.setSingleShot(True)
                self._resize_timer.timeout.connect(self._reorganize_grid)
            
            self._resize_timer.stop()
            self._resize_timer.start(100)  # 100ms delay
    
    def _reorganize_grid(self):
        """Reorganiza cards no grid baseado na largura atual"""
        if not hasattr(self, 'game_cards') or not self.game_cards:
            return
        
        # Calcular número de colunas baseado na largura disponível
        available_width = self.grid_container.width() - 30  # Margem
        columns = max(1, available_width // 295)  # 280 (card) + 15 (spacing)
        
        # Reorganizar apenas se mudou o número de colunas
        current_columns = getattr(self, '_current_columns', 0)
        if columns == current_columns:
            return
        
        self._current_columns = columns
        
        # Remover todos os widgets do layout
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)
        
        # Adicionar novamente na nova configuração
        for idx, card in enumerate(self.game_cards):
            row = idx // columns
            col = idx % columns
            self.grid_layout.addWidget(card, row, col)
    
    def _scan_games(self):
        """Varre jogos Steam"""
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("Varrendo...")
        
        try:
            # Executar varredura
            self.games = self.scan_games_uc.execute()
            self.filtered_games = self.games.copy()
            
            # Atualizar grid
            self._refresh_grid()
            
            QMessageBox.information(
                self,
                "Varredura Concluída",
                f"✓ Encontrados {len(self.games)} jogos\n"
                f"• Com DLSS: {sum(1 for g in self.games if g.has_dlss)}\n"
                f"• Com FSR: {sum(1 for g in self.games if g.has_fsr)}\n"
                f"• Com XeSS: {sum(1 for g in self.games if g.has_xess)}"
            )
        
        except Exception as e:
            self.logger.error(f"Erro ao varrer jogos: {e}")
            QMessageBox.critical(
                self,
                "Erro",
                f"Falha ao varrer jogos:\n{e}"
            )
        
        finally:
            self.scan_btn.setEnabled(True)
            self.scan_btn.setText("🔍 Varrer Jogos")
    
    def _fetch_versions(self):
        """Busca versões do OptiScaler"""
        self.fetch_btn.setEnabled(False)
        self.fetch_btn.setText("Buscando...")
        
        try:
            versions = self.fetch_versions_uc.execute(include_prerelease=True)
            
            QMessageBox.information(
                self,
                "Versões Atualizadas",
                f"✓ Encontradas {len(versions)} versões do OptiScaler\n"
                f"• Última estável: {versions[0].tag_name if versions else 'N/A'}\n"
                f"• Baixadas: {sum(1 for v in versions if v.is_downloaded)}"
            )
        
        except Exception as e:
            self.logger.error(f"Erro ao buscar versões: {e}")
            QMessageBox.critical(
                self,
                "Erro",
                f"Falha ao buscar versões:\n{e}"
            )
        
        finally:
            self.fetch_btn.setEnabled(True)
            self.fetch_btn.setText("📥 Buscar Versões")
    
    def _apply_filter(self):
        """Aplica filtro na lista de jogos"""
        filter_idx = self.filter_combo.currentIndex()
        
        if filter_idx == 0:  # Todos
            self.filtered_games = self.games.copy()
        elif filter_idx == 1:  # DLSS
            self.filtered_games = [g for g in self.games if g.has_dlss]
        elif filter_idx == 2:  # FSR
            self.filtered_games = [g for g in self.games if g.has_fsr]
        elif filter_idx == 3:  # XeSS
            self.filtered_games = [g for g in self.games if g.has_xess]
        elif filter_idx == 4:  # Qualquer tecnologia
            self.filtered_games = [g for g in self.games if g.has_dlss or g.has_fsr or g.has_xess]
        elif filter_idx == 5:  # OptiScaler instalado
            self.filtered_games = [g for g in self.games if g.installation_status == InstallationStatus.INSTALLED]
        
        self._refresh_grid()
    
    def _on_game_clicked(self, game: Game):
        """Callback quando jogo é clicado"""
        self.current_game = game
        self._show_game_details(game)
    
    def _show_game_details(self, game: Game):
        """Mostra detalhes do jogo em um diálogo"""
        dialog = GameDetailsDialog(game, self)
        dialog.exec()
    
    def _on_install_requested(self, game: Game):
        """Callback quando instalação é solicitada"""
        self.current_game = game
        
        # Mostrar diálogo de instalação
        dialog = InstallDialog(game, self.fetch_versions_uc, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            version_id = dialog.selected_version_id
            dll_type = dialog.selected_dll_type
            
            if version_id and dll_type:
                self._install_optiscaler(game, version_id, dll_type)
    
    def _on_uninstall_requested(self, game: Game):
        """Callback quando desinstalação é solicitada"""
        self.current_game = game
        
        reply = QMessageBox.question(
            self,
            "Confirmar Desinstalação",
            f"Desinstalar OptiScaler de:\n{game.name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._uninstall_optiscaler(game)
    
    def _install_optiscaler(self, game: Game, version_id: int, dll_type: DLLType):
        """Instala OptiScaler no jogo"""
        progress = QProgressBar()
        progress.setRange(0, 0)  # Indeterminado
        
        try:
            success = self.install_uc.execute(game.id, version_id, dll_type)
            
            if success:
                QMessageBox.information(
                    self,
                    "Instalação Concluída",
                    f"✓ OptiScaler instalado com sucesso em:\n{game.name}"
                )
                self._load_existing_games()
            else:
                QMessageBox.warning(self, "Aviso", "Falha na instalação")
        
        except Exception as e:
            self.logger.error(f"Erro ao instalar: {e}")
            QMessageBox.critical(self, "Erro", f"Falha na instalação:\n{e}")
    
    def _uninstall_optiscaler(self, game: Game):
        """Desinstala OptiScaler do jogo"""
        try:
            success = self.uninstall_uc.execute(game.id)
            
            if success:
                QMessageBox.information(
                    self,
                    "Desinstalação Concluída",
                    f"✓ OptiScaler removido com sucesso de:\n{game.name}"
                )
                self._load_existing_games()
            else:
                QMessageBox.warning(self, "Aviso", "Falha na desinstalação")
        
        except Exception as e:
            self.logger.error(f"Erro ao desinstalar: {e}")
            QMessageBox.critical(self, "Erro", f"Falha na desinstalação:\n{e}")
    
    def resizeEvent(self, event):
        """Reorganiza grid ao redimensionar"""
        super().resizeEvent(event)
        # Reorganizar grid dinamicamente para layout responsivo
        if hasattr(self, 'game_cards') and self.game_cards:
            self._refresh_grid()


class GameDetailsDialog(QDialog):
    """Diálogo com detalhes do jogo"""
    
    def __init__(self, game: Game, parent=None):
        super().__init__(parent)
        self.game = game
        
        self.setWindowTitle(f"Detalhes: {game.name}")
        self.setMinimumSize(500, 400)
        
        self._init_ui()
    
    def _init_ui(self):
        """Inicializa interface"""
        layout = QVBoxLayout()
        
        # Nome do jogo
        name_label = QLabel(self.game.name)
        name_label.setObjectName("title")
        layout.addWidget(name_label)
        
        # Informações
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        
        info = f"""
<b>AppID:</b> {self.game.appid or 'N/A'}<br>
<b>Plataforma:</b> {self.game.platform.value}<br>
<b>Caminho:</b> {self.game.path}<br>
<b>Executável:</b> {self.game.executable or 'N/A'}<br><br>

<b>Tecnologias Suportadas:</b><br>
"""
        
        if self.game.supported_dlls:
            for dll_type, dll_info in self.game.supported_dlls.items():
                info += f"• {dll_info.dll_type.display_name}<br>"
                info += f"  - Arquivo: {dll_info.path.name}<br>"
                info += f"  - Tamanho: {dll_info.size / 1024 / 1024:.2f} MB<br>"
                info += f"  - Versão: {dll_info.version or 'N/A'}<br><br>"
        else:
            info += "Nenhuma DLL detectada<br>"
        
        info_text.setHtml(info)
        layout.addWidget(info_text)
        
        # Botões
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
        
        self.setLayout(layout)


class InstallDialog(QDialog):
    """Diálogo de instalação do OptiScaler"""
    
    def __init__(self, game: Game, fetch_versions_uc, parent=None):
        super().__init__(parent)
        self.game = game
        self.fetch_versions_uc = fetch_versions_uc
        
        self.selected_version_id = None
        self.selected_dll_type = None
        
        self.setWindowTitle(f"Instalar OptiScaler: {game.name}")
        self.setMinimumWidth(400)
        
        self._init_ui()
        self._load_versions()
    
    def _init_ui(self):
        """Inicializa interface"""
        layout = QVBoxLayout()
        
        # Seletor de versão
        layout.addWidget(QLabel("Selecione a versão do OptiScaler:"))
        self.version_combo = QComboBox()
        layout.addWidget(self.version_combo)
        
        # Seletor de DLL alvo
        layout.addWidget(QLabel("Selecione a DLL alvo:"))
        self.dll_combo = QComboBox()
        for dll_type_str, dll_info in self.game.supported_dlls.items():
            self.dll_combo.addItem(dll_info.dll_type.display_name, dll_type_str)
        layout.addWidget(self.dll_combo)
        
        # Botões
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def _load_versions(self):
        """Carrega versões disponíveis"""
        try:
            versions = self.fetch_versions_uc.get_downloaded_versions()
            
            for version in versions:
                self.version_combo.addItem(version.tag_name, version.id)
        except Exception as e:
            QMessageBox.warning(self, "Aviso", f"Erro ao carregar versões:\n{e}")
    
    def _on_accept(self):
        """Confirma seleção"""
        self.selected_version_id = self.version_combo.currentData()
        dll_type_str = self.dll_combo.currentData()
        
        if dll_type_str:
            self.selected_dll_type = DLLType(dll_type_str)
        
        self.accept()
