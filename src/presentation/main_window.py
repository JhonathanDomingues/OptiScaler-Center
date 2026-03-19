"""
Janela principal do OptiScaler Center
"""
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStatusBar, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from infrastructure.config.config_service import ConfigService
from infrastructure.database.db_service import DatabaseService
from infrastructure.steam.steam_service import SteamService
from infrastructure.github.github_service import GitHubService
from application.services.dll_analyzer import DLLAnalyzer
from application.services.game_scanner import GameScanner
from application.use_cases.scan_games import ScanGamesUseCase
from application.use_cases.fetch_versions import FetchVersionsUseCase
from application.use_cases.download_version import DownloadVersionUseCase
from application.use_cases.install_optiscaler import InstallOptiScalerUseCase
from application.use_cases.uninstall_optiscaler import UninstallOptiScalerUseCase
from presentation.widgets.game_library_widget_modern import GameLibraryWidget
from presentation.widgets.downloads_manager_widget import DownloadsManagerWidget
from presentation.styles.modern_theme import apply_modern_theme, MODERN_THEME
from presentation.resources.app_icon import create_app_icon
from utils.logger import LoggerMixin
from utils.constants import APP_NAME, APP_VERSION, CACHE_DIR, BACKUPS_DIR


class MainWindow(QMainWindow, LoggerMixin):
    """Janela principal da aplicação"""
    
    def __init__(self, config: ConfigService, database: DatabaseService):
        super().__init__()
        self.config = config
        self.database = database
        
        self.logger.info("Inicializando janela principal")
        self._init_services()
        self._setup_ui()
        self._load_settings()
    
    def _init_services(self):
        """Inicializa todos os serviços e use cases"""
        # Serviços de infraestrutura
        self.steam_service = SteamService()
        self.github_service = GitHubService(CACHE_DIR)

        # Serviços de aplicação
        self.dll_analyzer = DLLAnalyzer(max_depth=3)
        self.game_scanner = GameScanner(self.steam_service, self.dll_analyzer)

        # Use Cases
        self.scan_games_uc = ScanGamesUseCase(self.game_scanner, self.database)
        self.fetch_versions_uc = FetchVersionsUseCase(self.github_service, self.database)
        self.download_version_uc = DownloadVersionUseCase(self.github_service, self.database)
        self.install_uc = InstallOptiScalerUseCase(self.database, BACKUPS_DIR)
        self.uninstall_uc = UninstallOptiScalerUseCase(self.database)
    
    def _setup_ui(self):
        """Configura a interface"""
        # Configurações da janela
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1000, 700)
        
        # Definir ícone da janela
        self.setWindowIcon(create_app_icon(64))
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Header
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Tabs
        tabs = self._create_tabs()
        main_layout.addWidget(tabs)
        
        # Status bar
        self._create_status_bar()
        
        # Aplicar tema
        self._apply_theme()
    
    def _create_header(self) -> QWidget:
        """Cria o cabeçalho"""
        header = QWidget()
        layout = QHBoxLayout(header)
        
        # Título
        title = QLabel(APP_NAME)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Botões de ação rápida
        scan_btn = QPushButton("🔍 Scanear Jogos")
        scan_btn.clicked.connect(self._on_scan_games)
        layout.addWidget(scan_btn)
        
        settings_btn = QPushButton("⚙️ Configurações")
        settings_btn.clicked.connect(self._on_settings)
        layout.addWidget(settings_btn)
        
        return header
    
    def _create_tabs(self) -> QTabWidget:
        """Cria as abas"""
        tabs = QTabWidget()
        
        # Aba Biblioteca (completa com GameLibraryWidget)
        self.library_widget = GameLibraryWidget(
            self.scan_games_uc,
            self.fetch_versions_uc,
            self.download_version_uc,
            self.install_uc,
            self.uninstall_uc
        )
        tabs.addTab(self.library_widget, "📚 Biblioteca")
        
        # Aba Downloads
        self.downloads_widget = DownloadsManagerWidget(
            self.fetch_versions_uc,
            self.download_version_uc,
            self.database
        )
        tabs.addTab(self.downloads_widget, "📥 Downloads")
        
        # Aba Logs (placeholder)
        logs_tab = self._create_logs_tab()
        tabs.addTab(logs_tab, "📋 Logs")
        
        return tabs
    
    def _create_logs_tab(self) -> QWidget:
        """Cria aba de logs"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Placeholder
        label = QLabel("Visualizador de Logs\n\n"
                      "Aqui você verá os logs das operações.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        return widget
    
    def _create_status_bar(self):
        """Cria a barra de status"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.showMessage("Pronto")
    
    def _apply_theme(self):
        """Aplica tema moderno"""
        self.setStyleSheet(MODERN_THEME)
    
    def _load_settings(self):
        """Carrega configurações salvas"""
        # Carregar tamanho e posição da janela
        window_state = self.config.get("window", {})
        if "width" in window_state and "height" in window_state:
            self.resize(window_state["width"], window_state["height"])
    
    def _on_scan_games(self):
        """Handler para scan de jogos"""
        self.logger.info("Iniciando scan manual de jogos")
        
        # Delegar para GameLibraryWidget
        if hasattr(self, 'library_widget'):
            self.library_widget._scan_games()
    
    def _on_settings(self):
        """Handler para configurações"""
        self.logger.info("Abrindo configurações")
        self.statusBar().showMessage("Configurações em desenvolvimento...")
    
    def closeEvent(self, event):
        """Handler para fechamento da janela"""
        # Salvar estado da janela
        self.config.set("window.width", self.width())
        self.config.set("window.height", self.height())
        
        self.logger.info("Encerrando aplicação")
        event.accept()
