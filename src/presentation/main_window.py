"""
Janela principal do OptiScaler Center
"""
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStatusBar, QTabWidget, QTextEdit, QCheckBox, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
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
from utils.i18n import tr, get_service


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
        self.setMinimumSize(1100, 700)
        
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
        self.tabs = self._create_tabs()
        main_layout.addWidget(self.tabs)

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

        # Seletor de idioma
        lang_label = QLabel(tr("language_label"))
        layout.addWidget(lang_label)

        self.lang_combo = QComboBox()
        i18n = get_service()
        if i18n:
            for code, name in i18n.available_languages().items():
                self.lang_combo.addItem(name, code)
            current_code = i18n.get_language()
            idx = self.lang_combo.findData(current_code)
            if idx >= 0:
                self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        layout.addWidget(self.lang_combo)

        # Botões de ação rápida
        scan_btn = QPushButton(tr("header_scan_btn"))
        scan_btn.clicked.connect(self._on_scan_games)
        layout.addWidget(scan_btn)

        settings_btn = QPushButton(tr("header_settings_btn"))
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
        tabs.addTab(self.library_widget, tr("tab_library"))

        # Aba Downloads
        self.downloads_widget = DownloadsManagerWidget(
            self.fetch_versions_uc,
            self.download_version_uc,
            self.database
        )
        tabs.addTab(self.downloads_widget, tr("tab_downloads"))

        # Aba Logs
        logs_tab = self._create_logs_tab()
        tabs.addTab(logs_tab, tr("tab_logs"))
        
        return tabs
    
    def _create_logs_tab(self) -> QWidget:
        """Cria aba de logs com visualizador do arquivo de log"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Toolbar da aba de logs
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel(tr("logs_title"))
        title_font = QFont()
        title_font.setBold(True)
        title.setFont(title_font)
        toolbar_layout.addWidget(title)

        toolbar_layout.addStretch()

        self._log_auto_scroll = QCheckBox(tr("logs_auto_scroll"))
        self._log_auto_scroll.setChecked(True)
        toolbar_layout.addWidget(self._log_auto_scroll)

        refresh_btn = QPushButton(tr("logs_refresh_btn"))
        refresh_btn.clicked.connect(self._refresh_logs)
        toolbar_layout.addWidget(refresh_btn)

        clear_btn = QPushButton(tr("logs_clear_btn"))
        clear_btn.clicked.connect(lambda: self._log_view.clear())
        toolbar_layout.addWidget(clear_btn)

        layout.addWidget(toolbar)

        # Área de texto dos logs
        self._log_view = QTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setStyleSheet(
            "QTextEdit { background-color: #0d1117; color: #c9d1d9; "
            "font-family: monospace; font-size: 12px; border: 1px solid #30363d; }"
        )
        layout.addWidget(self._log_view)

        # Carregar logs imediatamente e configurar timer de atualização
        self._refresh_logs()
        self._log_timer = QTimer(self)
        self._log_timer.timeout.connect(self._refresh_logs)
        self._log_timer.start(5000)  # Atualiza a cada 5 segundos

        return widget

    def _refresh_logs(self):
        """Recarrega o arquivo de log e exibe no viewer"""
        from utils.constants import LOGS_DIR, APP_NAME
        log_file = LOGS_DIR / f"{APP_NAME.lower().replace(' ', '_')}.log"

        try:
            if not log_file.exists():
                self._log_view.setPlainText(tr("logs_empty"))
                return

            content = log_file.read_text(encoding='utf-8', errors='replace')
            # Mostrar apenas as últimas 500 linhas para não sobrecarregar
            lines = content.splitlines()
            if len(lines) > 500:
                lines = lines[-500:]
                content = "\n".join(lines)

            current = self._log_view.toPlainText()
            if current != content:
                self._log_view.setPlainText(content)
                if self._log_auto_scroll.isChecked():
                    scrollbar = self._log_view.verticalScrollBar()
                    scrollbar.setValue(scrollbar.maximum())

        except Exception as e:
            self.logger.warning(f"Erro ao ler arquivo de log: {e}")
    
    def _create_status_bar(self):
        """Cria a barra de status"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.showMessage(tr("app_ready"))
    
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
        self.statusBar().showMessage(tr("settings_wip"))

    def _on_language_changed(self, _index: int):
        """Salva o idioma selecionado e pede para reiniciar"""
        i18n = get_service()
        if not i18n:
            return
        code = self.lang_combo.currentData()
        if code and code != i18n.get_language():
            i18n.set_language(code)
            self.config.set('general.language', code)
            self.logger.info(f"Idioma alterado para: {code}")
            QMessageBox.information(
                self,
                tr("restart_required_title"),
                tr("restart_required_msg")
            )
    
    def closeEvent(self, event):
        """Handler para fechamento da janela"""
        # Salvar estado da janela
        self.config.set("window.width", self.width())
        self.config.set("window.height", self.height())
        
        self.logger.info("Encerrando aplicação")
        event.accept()
