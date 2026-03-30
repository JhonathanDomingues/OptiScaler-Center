"""
Diálogo de Configurações do OptiScaler Center
Permite gerenciar idioma, GitHub (token/betas) e DLLs FSR4.
"""
import shutil
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QLabel, QLineEdit,
    QPushButton, QCheckBox, QComboBox, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDialogButtonBox, QGroupBox, QFormLayout, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from infrastructure.config.config_service import ConfigService
from application.use_cases.install_optiscaler import get_int8_versions
from utils.constants import FSR4_SDK_DIR, FSR4_USER_SDK_DIR
from utils.i18n import tr, get_service


class SettingsDialog(QDialog):
    """Diálogo de configurações completo"""

    def __init__(self, config: ConfigService, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle(tr("settings_title"))
        self.setMinimumSize(620, 500)
        self._init_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_general(), tr("settings_tab_general"))
        self.tabs.addTab(self._tab_github(), tr("settings_tab_github"))
        self.tabs.addTab(self._tab_fsr4(), tr("settings_tab_fsr4"))
        layout.addWidget(self.tabs)

        # Botões
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._save_and_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    # ---- Aba Geral ---------------------------------------------------

    def _tab_general(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        form.setSpacing(12)

        # Idioma
        self.lang_combo = QComboBox()
        i18n = get_service()
        if i18n:
            for code, name in i18n.available_languages().items():
                self.lang_combo.addItem(name, code)
            current = self.config.get('general.language', 'pt_BR')
            idx = self.lang_combo.findData(current)
            if idx >= 0:
                self.lang_combo.setCurrentIndex(idx)
        form.addRow(tr("settings_language"), self.lang_combo)

        return w

    # ---- Aba GitHub --------------------------------------------------

    def _tab_github(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)

        # Repositório estável
        grp_stable = QGroupBox(tr("settings_github_stable"))
        f_stable = QFormLayout(grp_stable)
        self.stable_repo_edit = QLineEdit(self.config.get('github.stable_repo', 'cdozdil/OptiScaler'))
        f_stable.addRow(tr("settings_github_repo"), self.stable_repo_edit)
        layout.addWidget(grp_stable)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        # Betas via GitHub Actions
        grp_beta = QGroupBox(tr("settings_github_beta"))
        f_beta = QFormLayout(grp_beta)

        self.show_betas_check = QCheckBox()
        self.show_betas_check.setChecked(self.config.get('github.show_betas', False))
        f_beta.addRow(tr("settings_github_show_betas"), self.show_betas_check)

        self.beta_repo_edit = QLineEdit(self.config.get('github.beta_repo', 'cdozdil/OptiScaler'))
        f_beta.addRow(tr("settings_github_beta_repo"), self.beta_repo_edit)

        self.beta_workflow_edit = QLineEdit(self.config.get('github.beta_workflow', 'release_debug.yml'))
        f_beta.addRow(tr("settings_github_workflow"), self.beta_workflow_edit)

        self.beta_pattern_edit = QLineEdit(self.config.get('github.beta_branch_pattern', r'release/0\.[0-9].*'))
        f_beta.addRow(tr("settings_github_branch_pattern"), self.beta_pattern_edit)

        self.token_edit = QLineEdit(self.config.get('github.token', ''))
        self.token_edit.setPlaceholderText(tr("settings_github_token_placeholder"))
        self.token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        token_row = QWidget()
        token_layout = QHBoxLayout(token_row)
        token_layout.setContentsMargins(0, 0, 0, 0)
        token_layout.addWidget(self.token_edit)
        show_token_btn = QPushButton(tr("settings_github_token_show"))
        show_token_btn.setFixedWidth(80)
        show_token_btn.setCheckable(True)
        show_token_btn.toggled.connect(
            lambda on: self.token_edit.setEchoMode(
                QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password
            )
        )
        token_layout.addWidget(show_token_btn)
        f_beta.addRow(tr("settings_github_token"), token_row)

        hint = QLabel(tr("settings_github_token_hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #888; font-size: 11px;")
        f_beta.addRow("", hint)

        layout.addWidget(grp_beta)
        layout.addStretch()
        return w

    # ---- Aba FSR4 ----------------------------------------------------

    def _tab_fsr4(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(10)

        # DLLs padrão — editável: cada DLL pode ser substituída por versão personalizada
        grp_std = QGroupBox(tr("settings_fsr4_standard"))
        std_layout = QVBoxLayout(grp_std)

        hint_std = QLabel(tr("settings_fsr4_standard_hint"))
        hint_std.setWordWrap(True)
        hint_std.setStyleSheet("color: #888; font-size: 11px;")
        std_layout.addWidget(hint_std)

        self.std_table = QTableWidget(0, 3)
        self.std_table.setHorizontalHeaderLabels([
            tr("settings_fsr4_col_dll"),
            tr("settings_fsr4_col_source"),
            "",
        ])
        hdr_std = self.std_table.horizontalHeader()
        hdr_std.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr_std.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr_std.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.std_table.verticalHeader().setVisible(False)
        self.std_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.std_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        std_layout.addWidget(self.std_table)
        self._refresh_std_table()

        layout.addWidget(grp_std)

        # Versões int8
        grp_int8 = QGroupBox(tr("settings_fsr4_int8"))
        int8_layout = QVBoxLayout(grp_int8)

        self.int8_table = QTableWidget(0, 3)
        self.int8_table.setHorizontalHeaderLabels([
            tr("settings_fsr4_col_version"),
            tr("settings_fsr4_col_file"),
            tr("settings_fsr4_col_source"),
        ])
        hdr = self.int8_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.int8_table.verticalHeader().setVisible(False)
        self.int8_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.int8_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        int8_layout.addWidget(self.int8_table)
        self._refresh_int8_table()

        # Botões int8
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        add_btn = QPushButton(tr("settings_fsr4_add_int8"))
        add_btn.clicked.connect(self._add_int8_version)
        btn_layout.addWidget(add_btn)

        remove_btn = QPushButton(tr("settings_fsr4_remove_int8"))
        remove_btn.clicked.connect(self._remove_int8_version)
        btn_layout.addWidget(remove_btn)

        btn_layout.addStretch()
        int8_layout.addWidget(btn_row)

        hint_int8 = QLabel(tr("settings_fsr4_int8_hint"))
        hint_int8.setWordWrap(True)
        hint_int8.setStyleSheet("color: #888; font-size: 11px;")
        int8_layout.addWidget(hint_int8)

        layout.addWidget(grp_int8)
        layout.addStretch()
        return w

    # ------------------------------------------------------------------
    # Helpers — tabela DLLs padrão
    # ------------------------------------------------------------------

    def _refresh_std_table(self):
        """Popula/atualiza a tabela de DLLs padrão."""
        custom = dict(self.config.get('fsr4_sdk.custom_standard_dlls', {}) or {})
        std_dir = FSR4_SDK_DIR / "standard"

        self.std_table.setRowCount(0)
        if not std_dir.exists():
            return

        for dll in sorted(std_dir.glob("*.dll")):
            row = self.std_table.rowCount()
            self.std_table.insertRow(row)

            self.std_table.setItem(row, 0, QTableWidgetItem(dll.name))

            if dll.name in custom:
                src = custom[dll.name]
                self.std_table.setItem(row, 1, QTableWidgetItem(f"★ {src}"))
            else:
                self.std_table.setItem(row, 1, QTableWidgetItem(tr("settings_fsr4_source_bundled")))

            # Botões na coluna de ações
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            btn_layout.setSpacing(4)

            override_btn = QPushButton(tr("settings_fsr4_override_btn"))
            override_btn.setFixedHeight(24)
            override_btn.clicked.connect(lambda _, n=dll.name: self._override_std_dll(n))
            btn_layout.addWidget(override_btn)

            if dll.name in custom:
                reset_btn = QPushButton(tr("settings_fsr4_reset_btn"))
                reset_btn.setFixedHeight(24)
                reset_btn.clicked.connect(lambda _, n=dll.name: self._reset_std_dll(n))
                btn_layout.addWidget(reset_btn)

            btn_layout.addStretch()
            self.std_table.setCellWidget(row, 2, btn_widget)

        self.std_table.resizeRowsToContents()

    def _override_std_dll(self, dll_name: str):
        """Abre seletor de arquivo e registra substituição para uma DLL padrão."""
        title = tr("settings_fsr4_override_title", dll=dll_name)
        path, _ = QFileDialog.getOpenFileName(self, title, "", "DLL Files (*.dll);;All files (*)")
        if not path:
            return
        try:
            custom = dict(self.config.get('fsr4_sdk.custom_standard_dlls', {}) or {})
            custom[dll_name] = path
            self.config.set('fsr4_sdk.custom_standard_dlls', custom)
            self._refresh_std_table()
            QMessageBox.information(
                self, tr("settings_title"),
                tr("settings_fsr4_override_ok_msg", dll=dll_name, file=Path(path).name)
            )
        except Exception as e:
            QMessageBox.critical(self, tr("error_title"), tr("settings_fsr4_override_error_msg", error=e))

    def _reset_std_dll(self, dll_name: str):
        """Remove a substituição personalizada e volta ao bundled."""
        reply = QMessageBox.question(
            self, tr("settings_title"),
            tr("settings_fsr4_reset_msg", dll=dll_name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            custom = dict(self.config.get('fsr4_sdk.custom_standard_dlls', {}) or {})
            custom.pop(dll_name, None)
            self.config.set('fsr4_sdk.custom_standard_dlls', custom)
            self._refresh_std_table()
            QMessageBox.information(
                self, tr("settings_title"),
                tr("settings_fsr4_reset_ok_msg", dll=dll_name)
            )
        except Exception as e:
            QMessageBox.critical(self, tr("error_title"), tr("settings_fsr4_override_error_msg", error=e))

    # ------------------------------------------------------------------
    # Helpers — tabela int8
    # ------------------------------------------------------------------

    def _refresh_int8_table(self):
        custom = self.config.get('fsr4_sdk.custom_int8_versions', {}) or {}
        versions = get_int8_versions(custom)

        self.int8_table.setRowCount(0)
        for name, dll_path in versions.items():
            row = self.int8_table.rowCount()
            self.int8_table.insertRow(row)
            self.int8_table.setItem(row, 0, QTableWidgetItem(name))
            self.int8_table.setItem(row, 1, QTableWidgetItem(str(dll_path)))
            source = tr("settings_fsr4_source_custom") if name in custom else tr("settings_fsr4_source_bundled")
            self.int8_table.setItem(row, 2, QTableWidgetItem(source))


    def _add_int8_version(self):
        """Pede um arquivo DLL e uma versão, copia para user int8 dir."""
        dll_path, _ = QFileDialog.getOpenFileName(
            self,
            tr("settings_fsr4_add_int8_title"),
            "",
            "DLL Files (*.dll);;All files (*)"
        )
        if not dll_path:
            return

        dll_path = Path(dll_path)

        # Pedir nome de versão
        from PyQt6.QtWidgets import QInputDialog
        version_name, ok = QInputDialog.getText(
            self,
            tr("settings_fsr4_version_name_title"),
            tr("settings_fsr4_version_name_prompt"),
            text=dll_path.parent.name or "nova_versao"
        )
        if not ok or not version_name.strip():
            return

        version_name = version_name.strip()

        try:
            dest_dir = FSR4_USER_SDK_DIR / "int8" / version_name
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dll_path, dest_dir / dll_path.name)

            # Salvar na config
            custom = dict(self.config.get('fsr4_sdk.custom_int8_versions', {}) or {})
            custom[version_name] = str(dest_dir / dll_path.name)
            self.config.set('fsr4_sdk.custom_int8_versions', custom)

            self._refresh_int8_table()
            QMessageBox.information(
                self, tr("settings_fsr4_add_ok_title"),
                tr("settings_fsr4_add_ok_msg", version=version_name)
            )
        except Exception as e:
            QMessageBox.critical(self, tr("error_title"), tr("settings_fsr4_add_error_msg", error=e))

    def _remove_int8_version(self):
        """Remove versão int8 personalizada selecionada."""
        rows = self.int8_table.selectionModel().selectedRows()
        if not rows:
            return

        row = rows[0].row()
        name = self.int8_table.item(row, 0).text()
        source = self.int8_table.item(row, 2).text()

        if source != tr("settings_fsr4_source_custom"):
            QMessageBox.warning(self, tr("warning_title"), tr("settings_fsr4_remove_bundled_warn"))
            return

        reply = QMessageBox.question(
            self, tr("settings_fsr4_remove_title"),
            tr("settings_fsr4_remove_msg", version=name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            custom = dict(self.config.get('fsr4_sdk.custom_int8_versions', {}) or {})
            dll_path = Path(custom.pop(name, ""))
            self.config.set('fsr4_sdk.custom_int8_versions', custom)

            # Tentar remover a pasta versionada do user dir
            version_dir = FSR4_USER_SDK_DIR / "int8" / name
            if version_dir.exists():
                shutil.rmtree(version_dir, ignore_errors=True)

            self._refresh_int8_table()
        except Exception as e:
            QMessageBox.critical(self, tr("error_title"), tr("settings_fsr4_remove_error_msg", error=e))

    # ------------------------------------------------------------------
    # Salvar
    # ------------------------------------------------------------------

    def _save_and_accept(self):
        lang = self.lang_combo.currentData()
        if lang:
            i18n = get_service()
            if i18n:
                i18n.set_language(lang)
            self.config.set('general.language', lang)

        # GitHub
        self.config.set('github.stable_repo',        self.stable_repo_edit.text().strip())
        self.config.set('github.show_betas',          self.show_betas_check.isChecked())
        self.config.set('github.beta_repo',           self.beta_repo_edit.text().strip())
        self.config.set('github.beta_workflow',       self.beta_workflow_edit.text().strip())
        self.config.set('github.beta_branch_pattern', self.beta_pattern_edit.text().strip())
        self.config.set('github.token',               self.token_edit.text().strip())

        self.accept()
