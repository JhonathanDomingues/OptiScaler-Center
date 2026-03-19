"""
Widget para gerenciamento de downloads do OptiScaler
"""
from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
    QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from application.use_cases.fetch_versions import FetchVersionsUseCase
from application.use_cases.download_version import DownloadVersionUseCase
from domain.entities.optiscaler_version import OptiScalerVersion
from domain.repositories.version_repository import VersionRepository
from infrastructure.database.db_service import DatabaseService
from utils.logger import LoggerMixin


class DownloadThread(QThread):
    """Thread para download em background"""
    progress = pyqtSignal(int, int)  # downloaded, total
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, download_uc: DownloadVersionUseCase, version: OptiScalerVersion):
        super().__init__()
        self.download_uc = download_uc
        self.version = version
    
    def run(self):
        """Executa download"""
        try:
            def progress_callback(downloaded: int, total: int):
                self.progress.emit(downloaded, total)
            
            success = self.download_uc.download_by_tag(
                self.version.tag_name,
                progress_callback=progress_callback
            )
            
            if success:
                self.finished.emit(True, f"Download de {self.version.tag_name} concluído!")
            else:
                self.finished.emit(False, "Erro ao fazer download")
        
        except Exception as e:
            self.finished.emit(False, f"Erro: {str(e)}")


class DownloadsManagerWidget(QWidget, LoggerMixin):
    """Widget para gerenciar downloads do OptiScaler"""
    
    def __init__(
        self,
        fetch_versions_uc: FetchVersionsUseCase,
        download_version_uc: DownloadVersionUseCase,
        db_service: DatabaseService
    ):
        super().__init__()
        self.fetch_versions_uc = fetch_versions_uc
        self.download_version_uc = download_version_uc
        self.db_service = db_service
        
        self.current_download: Optional[DownloadThread] = None
        self.versions = []
        
        self._setup_ui()
        self._load_versions()
    
    def _setup_ui(self):
        """Configura interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Info de cache
        self.cache_info_label = QLabel()
        self.cache_info_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.cache_info_label)
        
        # Tabela de versões
        self.versions_table = self._create_versions_table()
        layout.addWidget(self.versions_table)
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # Botões de ação
        actions = self._create_actions()
        layout.addWidget(actions)
    
    def _create_header(self) -> QWidget:
        """Cria cabeçalho"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Título
        title = QLabel("📥 Gerenciador de Downloads do OptiScaler")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Botão atualizar
        refresh_btn = QPushButton("🔄 Atualizar Lista")
        refresh_btn.clicked.connect(self._fetch_versions)
        layout.addWidget(refresh_btn)
        
        return widget
    
    def _create_versions_table(self) -> QTableWidget:
        """Cria tabela de versões"""
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Versão", "Nome", "Data", "Tamanho", "Status", "Ação"
        ])
        
        # Configurar colunas
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(5, 155)  # Largura fixa para coluna de ação
        
        # Configurar altura das linhas
        table.verticalHeader().setDefaultSectionSize(46)
        table.verticalHeader().setVisible(False)
        
        # Estilo customizado - tema escuro
        table.setStyleSheet("""
            QTableWidget {
                background-color: #16202d;
                alternate-background-color: #1b2838;
                gridline-color: #2a475e;
                font-size: 13px;
                color: #c7d5e0;
                border: 1px solid #2a475e;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 10px 8px;
                color: #c7d5e0;
            }
            QTableWidget::item:selected {
                background-color: #2a475e;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #171a21;
                color: #c7d5e0;
                font-weight: bold;
                font-size: 13px;
                padding: 10px 8px;
                border: none;
                border-bottom: 2px solid #2a475e;
                border-right: 1px solid #2a475e;
            }
        """)
        
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        return table
    
    def _create_actions(self) -> QWidget:
        """Cria botões de ação"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Info
        info = QLabel("💡 Baixe versões do OptiScaler para instalá-las em seus jogos sem precisar consultar o GitHub toda vez.")
        info.setWordWrap(True)
        info.setStyleSheet("color: #666; font-size: 11px; padding: 10px;")
        layout.addWidget(info)
        
        layout.addStretch()
        
        # Botão limpar cache
        clear_btn = QPushButton("🗑️ Limpar Cache")
        clear_btn.clicked.connect(self._clear_cache)
        layout.addWidget(clear_btn)
        
        return widget
    
    def _load_versions(self):
        """Carrega versões do banco de dados"""
        self.logger.info("Carregando versões do banco de dados")
        
        try:
            with self.db_service.get_connection() as conn:
                version_repo = VersionRepository(conn)
                self.versions = version_repo.find_all(include_prerelease=True)
            
            self._update_table()
            self._update_cache_info()
            
            if not self.versions:
                # Se não tem versões, buscar automaticamente
                self._fetch_versions()
        
        except Exception as e:
            self.logger.error(f"Erro ao carregar versões: {e}")
            QMessageBox.warning(self, "Erro", f"Erro ao carregar versões: {e}")
    
    def _fetch_versions(self):
        """Busca versões do GitHub"""
        self.logger.info("Buscando versões do GitHub")
        
        try:
            # Desabilitar botão
            sender = self.sender()
            if sender:
                sender.setEnabled(False)
                sender.setText("⏳ Buscando...")
            
            # Buscar versões
            count = self.fetch_versions_uc.execute(include_prerelease=True)
            
            if count > 0:
                self.logger.info(f"✓ {count} versões encontradas")
                self._load_versions()
                QMessageBox.information(
                    self,
                    "Sucesso",
                    f"✓ {count} versões encontradas no GitHub"
                )
            else:
                self.logger.warning("Nenhuma versão encontrada")
                QMessageBox.warning(
                    self,
                    "Aviso",
                    "Nenhuma versão encontrada no GitHub"
                )
        
        except Exception as e:
            self.logger.error(f"Erro ao buscar versões: {e}")
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao buscar versões:\n{str(e)}"
            )
        
        finally:
            # Reabilitar botão
            if sender:
                sender.setEnabled(True)
                sender.setText("🔄 Atualizar Lista")
    
    def _update_table(self):
        """Atualiza tabela com versões"""
        self.versions_table.setRowCount(0)
        
        for version in self.versions:
            row = self.versions_table.rowCount()
            self.versions_table.insertRow(row)
            
            # Tag
            tag_item = QTableWidgetItem(version.tag_name)
            if version.is_prerelease:
                tag_item.setText(f"{version.tag_name} 🧪")
            self.versions_table.setItem(row, 0, tag_item)
            
            # Nome
            name_item = QTableWidgetItem(version.name or version.tag_name)
            self.versions_table.setItem(row, 1, name_item)
            
            # Data
            date_str = version.release_date.strftime("%d/%m/%Y")
            date_item = QTableWidgetItem(date_str)
            self.versions_table.setItem(row, 2, date_item)
            
            # Tamanho
            size_mb = version.file_size / (1024 * 1024)
            size_item = QTableWidgetItem(f"{size_mb:.1f} MB")
            self.versions_table.setItem(row, 3, size_item)
            
            # Status
            if version.is_downloaded:
                status_item = QTableWidgetItem("✓ Baixado")
                status_item.setForeground(QColor("#6c9010"))  # Verde claro
            else:
                status_item = QTableWidgetItem("⬇ Não baixado")
                status_item.setForeground(QColor("#8b939c"))  # Cinza claro
            self.versions_table.setItem(row, 4, status_item)
            
            # Botão de ação — dentro de container para margens corretas
            if version.is_downloaded:
                btn = QPushButton("🗑️ Remover")
                btn.clicked.connect(lambda checked, v=version: self._delete_version(v))
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #c93434;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        font-size: 13px;
                        font-weight: bold;
                    }
                    QPushButton:hover { background-color: #d94545; }
                    QPushButton:pressed { background-color: #a52828; }
                """)
            else:
                btn = QPushButton("⬇ Baixar")
                btn.clicked.connect(lambda checked, v=version: self._download_version(v))
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #5c7e10;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        font-size: 13px;
                        font-weight: bold;
                    }
                    QPushButton:hover { background-color: #6c9010; }
                    QPushButton:pressed { background-color: #4a6609; }
                """)
            
            container = QWidget()
            container.setStyleSheet("background-color: transparent;")
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(8, 7, 8, 7)
            container_layout.addWidget(btn)
            
            self.versions_table.setCellWidget(row, 5, container)
    
    def _update_cache_info(self):
        """Atualiza informações do cache"""
        downloaded = sum(1 for v in self.versions if v.is_downloaded)
        total = len(self.versions)
        
        total_size = sum(v.file_size for v in self.versions if v.is_downloaded)
        size_mb = total_size / (1024 * 1024)
        
        self.cache_info_label.setText(
            f"📊 {downloaded}/{total} versões baixadas | "
            f"💾 {size_mb:.1f} MB em cache"
        )
    
    def _download_version(self, version: OptiScalerVersion):
        """Faz download de uma versão"""
        if self.current_download and self.current_download.isRunning():
            QMessageBox.warning(
                self,
                "Aviso",
                "Já existe um download em andamento"
            )
            return
        
        self.logger.info(f"Iniciando download de {version.tag_name}")
        
        # Mostrar barra de progresso
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Criar thread de download
        self.current_download = DownloadThread(self.download_version_uc, version)
        self.current_download.progress.connect(self._on_download_progress)
        self.current_download.finished.connect(self._on_download_finished)
        self.current_download.start()
    
    def _on_download_progress(self, downloaded: int, total: int):
        """Handler para progresso do download"""
        if total > 0:
            percentage = int((downloaded / total) * 100)
            self.progress_bar.setValue(percentage)
            
            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            self.progress_bar.setFormat(f"{downloaded_mb:.1f}/{total_mb:.1f} MB ({percentage}%)")
    
    def _on_download_finished(self, success: bool, message: str):
        """Handler para conclusão do download"""
        self.progress_bar.setVisible(False)
        
        if success:
            self.logger.info(message)
            QMessageBox.information(self, "Sucesso", message)
            self._load_versions()
        else:
            self.logger.error(message)
            QMessageBox.critical(self, "Erro", message)
    
    def _delete_version(self, version: OptiScalerVersion):
        """Remove uma versão baixada"""
        reply = QMessageBox.question(
            self,
            "Confirmar Remoção",
            f"Deseja remover {version.tag_name} do cache?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if version.local_path and version.local_path.exists():
                    version.local_path.unlink()
                    self.logger.info(f"✓ Versão {version.tag_name} removida")
                    
                    # Atualizar banco
                    version.is_downloaded = False
                    version.local_path = None
                    
                    with self.db_service.get_connection() as conn:
                        version_repo = VersionRepository(conn)
                        version_repo.update(version)
                    
                    self._load_versions()
                    QMessageBox.information(
                        self,
                        "Sucesso",
                        f"✓ {version.tag_name} removido do cache"
                    )
            
            except Exception as e:
                self.logger.error(f"Erro ao remover versão: {e}")
                QMessageBox.critical(self, "Erro", f"Erro ao remover: {e}")
    
    def _clear_cache(self):
        """Limpa todo o cache"""
        downloaded = sum(1 for v in self.versions if v.is_downloaded)
        
        if downloaded == 0:
            QMessageBox.information(self, "Info", "Não há versões baixadas no cache")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirmar Limpeza",
            f"Deseja remover TODAS as {downloaded} versões baixadas?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                removed = 0
                with self.db_service.get_connection() as conn:
                    version_repo = VersionRepository(conn)
                    
                    for version in self.versions:
                        if version.is_downloaded and version.local_path:
                            if version.local_path.exists():
                                version.local_path.unlink()
                                removed += 1
                            
                            version.is_downloaded = False
                            version.local_path = None
                            version_repo.update(version)
                
                self.logger.info(f"✓ {removed} versões removidas do cache")
                self._load_versions()
                
                QMessageBox.information(
                    self,
                    "Sucesso",
                    f"✓ {removed} versões removidas do cache"
                )
            
            except Exception as e:
                self.logger.error(f"Erro ao limpar cache: {e}")
                QMessageBox.critical(self, "Erro", f"Erro ao limpar cache: {e}")
