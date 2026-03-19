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
from domain.enums.installation_status import InstallationStatus
from application.use_cases.scan_games import ScanGamesUseCase
from application.use_cases.fetch_versions import FetchVersionsUseCase
from application.use_cases.download_version import DownloadVersionUseCase
from application.use_cases.install_optiscaler import InstallOptiScalerUseCase, SUPPORTED_LOADER_DLLS
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
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Widget container para o grid
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(15)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.grid_container.setLayout(self.grid_layout)
        
        self.scroll_area.setWidget(self.grid_container)
        container_layout.addWidget(self.scroll_area, 1)
        
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
        
        # Calcular número de colunas baseado na largura disponível
        self._current_columns = self._calculate_columns()
        
        # Adicionar cards
        for idx, game in enumerate(self.filtered_games):
            row = idx // self._current_columns
            col = idx % self._current_columns
            
            card = GameCardWidget(game)
            card.clicked.connect(self._on_game_clicked)
            card.install_requested.connect(self._on_install_requested)
            card.uninstall_requested.connect(self._on_uninstall_requested)
            
            self.game_cards.append(card)
            self.grid_layout.addWidget(card, row, col)
        
        # Atualizar contador
        self.game_count_label.setText(f"{len(self.filtered_games)} jogos")
    
    def _calculate_columns(self) -> int:
        """Calcula número de colunas baseado na largura disponível"""
        if not hasattr(self, 'scroll_area'):
            return 3  # Valor padrão
        
        # Obter largura disponível do viewport
        available_width = self.scroll_area.viewport().width() - 30  # Margem
        
        # Largura mínima do card + espaçamento
        card_min_width = 200  # Card mínimo: 180 + margem
        spacing = self.grid_layout.spacing()
        
        # Calcular colunas (mínimo 1, máximo 6)
        columns = max(1, min(6, available_width // (card_min_width + spacing)))
        
        return columns
    
    def resizeEvent(self, event):
        """Reorganiza grid quando janela é redimensionada"""
        super().resizeEvent(event)
        
        # Reorganizar apenas se houver mudança significativa
        if hasattr(self, 'game_cards') and self.game_cards:
            from PyQt6.QtCore import QTimer
            # Agendar reorganização com delay para evitar múltiplas chamadas
            QTimer.singleShot(50, self._reorganize_grid)
    
    def _reorganize_grid(self):
        """Reorganiza cards no grid baseado na largura atual"""
        if not hasattr(self, 'game_cards') or not self.game_cards:
            return
        
        # Calcular novo número de colunas
        new_columns = self._calculate_columns()
        
        # Verificar se o número de colunas mudou
        if hasattr(self, '_current_columns') and self._current_columns == new_columns:
            return  # Não reorganizar se o número de colunas não mudou
        
        self._current_columns = new_columns
        
        # Remover todos os widgets do layout sem deletar
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item and item.widget():
                self.grid_layout.removeWidget(item.widget())
        
        # Adicionar novamente na nova configuração
        for idx, card in enumerate(self.game_cards):
            row = idx // new_columns
            col = idx % new_columns
            self.grid_layout.addWidget(card, row, col)
        
        # Forçar atualização do layout
        self.grid_layout.activate()
        self.grid_container.updateGeometry()
    
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
        
        # Verificar se existem versões baixadas
        try:
            downloaded_versions = self.fetch_versions_uc.get_downloaded_versions()
            
            if not downloaded_versions:
                reply = QMessageBox.question(
                    self,
                    "Nenhuma Versão Disponível",
                    "Você ainda não baixou nenhuma versão do OptiScaler.\n\n"
                    "Deseja ir para a aba de Downloads para baixar uma versão?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    # Mudar para aba de Downloads
                    parent_tabs = self.parent()
                    if parent_tabs and hasattr(parent_tabs, 'setCurrentIndex'):
                        parent_tabs.setCurrentIndex(1)  # Índice da aba Downloads
                
                return
        except Exception as e:
            self.logger.error(f"Erro ao verificar versões: {e}")
        
        # Mostrar diálogo de instalação
        dialog = InstallDialog(game, self.fetch_versions_uc, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            version_id = dialog.selected_version_id
            loader_dll = dialog.selected_loader
            fsr4_variant = dialog.selected_fsr4

            if version_id:
                self._install_optiscaler(game, version_id, loader_dll, fsr4_variant)
    
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
    
    def _install_optiscaler(self, game: Game, version_id: int, loader_dll: str = "dxgi.dll", fsr4_variant=None):
        """Instala OptiScaler no jogo"""
        try:
            success = self.install_uc.execute(
                game.id, version_id,
                loader_dll=loader_dll,
                fsr4_variant=fsr4_variant
            )
            
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
        self.selected_loader = "dxgi.dll"
        self.selected_fsr4 = None

        self.setWindowTitle(f"Instalar OptiScaler: {game.name}")
        self.setMinimumWidth(420)

        self._init_ui()
        self._load_versions()

    def _init_ui(self):
        """Inicializa interface"""
        layout = QVBoxLayout()

        # Seletor de versão
        layout.addWidget(QLabel("Versão do OptiScaler:"))
        self.version_combo = QComboBox()
        layout.addWidget(self.version_combo)

        # Seletor de loader DLL
        layout.addWidget(QLabel("Loader DLL (nome que o OptiScaler vai usar):"))
        self.loader_combo = QComboBox()
        for dll in SUPPORTED_LOADER_DLLS:
            self.loader_combo.addItem(dll, dll)
        layout.addWidget(self.loader_combo)

        # Seletor de FSR4 SDK
        layout.addWidget(QLabel("FSR4 SDK (opcional):"))
        self.fsr4_combo = QComboBox()
        self.fsr4_combo.addItem("Não incluir", None)
        self.fsr4_combo.addItem("Padrão — 3 DLLs (amd_fidelityfx_*.dll)", "standard")
        self.fsr4_combo.addItem("INT8 — apenas upscaler", "int8")
        layout.addWidget(self.fsr4_combo)

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
        self.selected_loader = self.loader_combo.currentData() or "dxgi.dll"
        self.selected_fsr4 = self.fsr4_combo.currentData()

        self.accept()
