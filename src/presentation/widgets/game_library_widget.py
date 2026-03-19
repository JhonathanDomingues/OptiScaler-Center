"""
Widget de biblioteca de jogos
Interface principal para gerenciar jogos e instalações do OptiScaler
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QGroupBox, QLabel,
    QPushButton, QComboBox, QProgressBar, QMessageBox,
    QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from pathlib import Path
from typing import Optional

from utils.logger import LoggerMixin
from domain.entities.game import Game
from domain.enums.dll_type import DLLType
from application.use_cases.scan_games import ScanGamesUseCase
from application.use_cases.fetch_versions import FetchVersionsUseCase
from application.use_cases.download_version import DownloadVersionUseCase
from application.use_cases.install_optiscaler import InstallOptiScalerUseCase
from application.use_cases.uninstall_optiscaler import UninstallOptiScalerUseCase


class GameLibraryWidget(QWidget, LoggerMixin):
    """Widget principal da biblioteca de jogos"""
    
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
        self.games = []
        
        self._init_ui()
    
    def _init_ui(self):
        """Inicializa interface"""
        layout = QVBoxLayout()
        
        # Barra de ferramentas superior
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # Splitter principal (lista + detalhes)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Lista de jogos (esquerda)
        self.game_list = QListWidget()
        self.game_list.itemClicked.connect(self._on_game_selected)
        splitter.addWidget(self.game_list)
        
        # Painel de detalhes (direita)
        details_panel = self._create_details_panel()
        splitter.addWidget(details_panel)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        self.setLayout(layout)
    
    def _create_toolbar(self) -> QWidget:
        """Cria barra de ferramentas"""
        toolbar = QWidget()
        layout = QHBoxLayout()
        
        # Botão varrer jogos
        self.scan_btn = QPushButton("🔍 Varrer Jogos")
        self.scan_btn.clicked.connect(self._scan_games)
        layout.addWidget(self.scan_btn)
        
        # Botão atualizar versões
        self.fetch_btn = QPushButton("📥 Atualizar Versões")
        self.fetch_btn.clicked.connect(self._fetch_versions)
        layout.addWidget(self.fetch_btn)
        
        # Filtro
        layout.addWidget(QLabel("Filtro:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "Todos os jogos",
            "Com DLSS",
            "Com FSR",
            "Com XeSS",
            "Com qualquer upscaling"
        ])
        self.filter_combo.currentIndexChanged.connect(self._apply_filter)
        layout.addWidget(self.filter_combo)
        
        layout.addStretch()
        
        # Contador de jogos
        self.game_count_label = QLabel("0 jogos")
        layout.addWidget(self.game_count_label)
        
        toolbar.setLayout(layout)
        return toolbar
    
    def _create_details_panel(self) -> QWidget:
        """Cria painel de detalhes do jogo"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Informações do jogo
        self.info_group = QGroupBox("Informações do Jogo")
        info_layout = QVBoxLayout()
        
        self.game_name_label = QLabel("Nenhum jogo selecionado")
        self.game_name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        info_layout.addWidget(self.game_name_label)
        
        self.game_path_label = QLabel("")
        self.game_path_label.setWordWrap(True)
        info_layout.addWidget(self.game_path_label)
        
        self.game_appid_label = QLabel("")
        info_layout.addWidget(self.game_appid_label)
        
        self.info_group.setLayout(info_layout)
        layout.addWidget(self.info_group)
        
        # DLLs detectadas
        self.dll_group = QGroupBox("DLLs Detectadas")
        dll_layout = QVBoxLayout()
        
        self.dll_info_text = QTextEdit()
        self.dll_info_text.setReadOnly(True)
        self.dll_info_text.setMaximumHeight(120)
        dll_layout.addWidget(self.dll_info_text)
        
        self.dll_group.setLayout(dll_layout)
        layout.addWidget(self.dll_group)
        
        # Instalação do OptiScaler
        self.install_group = QGroupBox("OptiScaler")
        install_layout = QVBoxLayout()
        
        # Status da instalação
        self.install_status_label = QLabel("Não instalado")
        install_layout.addWidget(self.install_status_label)
        
        # Seletor de versão
        version_layout = QHBoxLayout()
        version_layout.addWidget(QLabel("Versão:"))
        self.version_combo = QComboBox()
        version_layout.addWidget(self.version_combo)
        install_layout.addLayout(version_layout)
        
        # Seletor de DLL alvo
        dll_target_layout = QHBoxLayout()
        dll_target_layout.addWidget(QLabel("DLL Alvo:"))
        self.dll_target_combo = QComboBox()
        dll_target_layout.addWidget(self.dll_target_combo)
        install_layout.addLayout(dll_target_layout)
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        install_layout.addWidget(self.progress_bar)
        
        # Botões de ação
        buttons_layout = QHBoxLayout()
        
        self.download_btn = QPushButton("📥 Baixar Versão")
        self.download_btn.clicked.connect(self._download_version)
        self.download_btn.setEnabled(False)
        buttons_layout.addWidget(self.download_btn)
        
        self.install_btn = QPushButton("✓ Instalar")
        self.install_btn.clicked.connect(self._install_optiscaler)
        self.install_btn.setEnabled(False)
        buttons_layout.addWidget(self.install_btn)
        
        self.uninstall_btn = QPushButton("✗ Desinstalar")
        self.uninstall_btn.clicked.connect(self._uninstall_optiscaler)
        self.uninstall_btn.setEnabled(False)
        buttons_layout.addWidget(self.uninstall_btn)
        
        install_layout.addLayout(buttons_layout)
        
        self.install_group.setLayout(install_layout)
        layout.addWidget(self.install_group)
        
        layout.addStretch()
        
        panel.setLayout(layout)
        return panel
    
    def _scan_games(self):
        """Varre jogos Steam"""
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("Varrendo...")
        
        try:
            # Executar varredura
            self.games = self.scan_games_uc.execute()
            
            # Atualizar lista
            self._refresh_game_list()
            
            QMessageBox.information(
                self,
                "Varredura Concluída",
                f"Encontrados {len(self.games)} jogos"
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
            
            # Atualizar combo de versões
            self.version_combo.clear()
            for version in versions:
                status = " ✓" if version.is_downloaded else ""
                self.version_combo.addItem(
                    f"{version.tag_name}{status}",
                    version.id
                )
            
            QMessageBox.information(
                self,
                "Atualização Concluída",
                f"Encontradas {len(versions)} versões"
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
            self.fetch_btn.setText("📥 Atualizar Versões")
    
    def _download_version(self):
        """Baixa versão selecionada"""
        version_id = self.version_combo.currentData()
        if not version_id:
            return
        
        self.download_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        try:
            def progress_callback(downloaded, total):
                if total > 0:
                    percent = int((downloaded / total) * 100)
                    self.progress_bar.setValue(percent)
            
            success = self.download_version_uc.execute(version_id, progress_callback)
            
            if success:
                QMessageBox.information(self, "Sucesso", "Download concluído!")
                self._fetch_versions()  # Atualizar lista
            else:
                QMessageBox.warning(self, "Aviso", "Falha no download")
        
        except Exception as e:
            self.logger.error(f"Erro ao baixar: {e}")
            QMessageBox.critical(self, "Erro", f"Falha:\n{e}")
        
        finally:
            self.download_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def _install_optiscaler(self):
        """Instala OptiScaler no jogo"""
        if not self.current_game:
            return
        
        version_id = self.version_combo.currentData()
        dll_type_str = self.dll_target_combo.currentData()
        
        if not version_id or not dll_type_str:
            QMessageBox.warning(self, "Aviso", "Selecione versão e DLL alvo")
            return
        
        dll_type = DLLType(dll_type_str)
        
        reply = QMessageBox.question(
            self,
            "Confirmar Instalação",
            f"Instalar OptiScaler em {self.current_game.name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            success = self.install_uc.execute(
                self.current_game.id,
                version_id,
                dll_type
            )
            
            if success:
                QMessageBox.information(self, "Sucesso", "Instalação concluída!")
                self._on_game_selected(self.game_list.currentItem())
            else:
                QMessageBox.warning(self, "Aviso", "Falha na instalação")
        
        except Exception as e:
            self.logger.error(f"Erro ao instalar: {e}")
            QMessageBox.critical(self, "Erro", f"Falha:\n{e}")
    
    def _uninstall_optiscaler(self):
        """Desinstala OptiScaler do jogo"""
        if not self.current_game:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirmar Desinstalação",
            f"Desinstalar OptiScaler de {self.current_game.name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            success = self.uninstall_uc.execute(self.current_game.id)
            
            if success:
                QMessageBox.information(self, "Sucesso", "Desinstalação concluída!")
                self._on_game_selected(self.game_list.currentItem())
            else:
                QMessageBox.warning(self, "Aviso", "Falha na desinstalação")
        
        except Exception as e:
            self.logger.error(f"Erro ao desinstalar: {e}")
            QMessageBox.critical(self, "Erro", f"Falha:\n{e}")
    
    def _on_game_selected(self, item: QListWidgetItem):
        """Callback quando jogo é selecionado"""
        game_index = self.game_list.row(item)
        self.current_game = self.games[game_index]
        
        # Atualizar informações
        self.game_name_label.setText(self.current_game.name)
        self.game_path_label.setText(f"📁 {self.current_game.path}")
        self.game_appid_label.setText(f"AppID: {self.current_game.appid}")
        
        # Atualizar DLLs
        dll_text = ""
        for dll_type_str, dll_info in self.current_game.supported_dlls.items():
            dll_text += f"• {dll_info.dll_type.display_name}\n"
            dll_text += f"  {dll_info.path.name}\n"
            dll_text += f"  {dll_info.size / 1024 / 1024:.1f} MB\n\n"
        
        self.dll_info_text.setText(dll_text if dll_text else "Nenhuma DLL detectada")
        
        # Atualizar combo de DLL alvo
        self.dll_target_combo.clear()
        for dll_type_str in self.current_game.supported_dlls.keys():
            dll_type = DLLType(dll_type_str)
            self.dll_target_combo.addItem(dll_type.display_name, dll_type_str)
        
        # Habilitar botões
        has_dlls = len(self.current_game.supported_dlls) > 0
        self.download_btn.setEnabled(has_dlls)
        self.install_btn.setEnabled(has_dlls)
    
    def _refresh_game_list(self):
        """Atualiza lista de jogos"""
        self.game_list.clear()
        
        for game in self.games:
            # Ícones de suporte
            icons = []
            if game.has_dlss:
                icons.append("DLSS")
            if game.has_fsr:
                icons.append("FSR")
            if game.has_xess:
                icons.append("XeSS")
            
            icon_str = f" [{', '.join(icons)}]" if icons else ""
            
            item = QListWidgetItem(f"{game.name}{icon_str}")
            self.game_list.addItem(item)
        
        self.game_count_label.setText(f"{len(self.games)} jogos")
    
    def _apply_filter(self):
        """Aplica filtro na lista"""
        filter_idx = self.filter_combo.currentIndex()
        
        if filter_idx == 0:  # Todos
            self.games = self.scan_games_uc.get_all_games()
        elif filter_idx in [1, 2, 3]:  # DLSS, FSR, XeSS
            dll_types = [DLLType.DLSS, DLLType.FSR, DLLType.XESS]
            # Implementar filtro por tecnologia
            self.games = self.scan_games_uc.get_all_games()
        else:  # Com qualquer upscaling
            self.games = self.scan_games_uc.get_games_with_upscaling()
        
        self._refresh_game_list()
