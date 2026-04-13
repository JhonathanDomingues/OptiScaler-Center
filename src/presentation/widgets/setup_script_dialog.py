"""
Diálogo para configuração interativa de mods do OptiScaler.

Exibe as perguntas extraídas dos scripts setup.sh / setup.bat e
coleta as respostas do usuário para serem enviadas ao script via stdin.
"""
from typing import List

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QCheckBox, QDialogButtonBox,
    QScrollArea, QWidget, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from application.services.setup_script_parser import SetupQuestion
from utils.i18n import tr


class SetupScriptDialog(QDialog):
    """
    Exibe as perguntas do script de configuração e coleta as respostas.

    Uso::

        questions = install_uc.get_setup_questions(version_id)
        if questions:
            dlg = SetupScriptDialog(script_name, questions, parent)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                answers = dlg.answers   # List[str] na ordem das perguntas
    """

    def __init__(
        self,
        script_name: str,
        questions: List[SetupQuestion],
        parent=None,
    ):
        super().__init__(parent)
        self.questions = questions
        self._widgets: list = []   # widgets de resposta, na ordem das perguntas
        self.answers: List[str] = []

        self.setWindowTitle(tr("setup_dialog_title", script=script_name))
        self.setMinimumWidth(520)
        self.setMaximumHeight(700)
        self._init_ui(script_name)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _init_ui(self, script_name: str):
        root = QVBoxLayout(self)
        root.setSpacing(12)

        # Cabeçalho
        header_lbl = QLabel(tr("setup_dialog_header", script=script_name))
        header_lbl.setWordWrap(True)
        header_font = QFont()
        header_font.setBold(True)
        header_lbl.setFont(header_font)
        root.addWidget(header_lbl)

        hint_lbl = QLabel(tr("setup_dialog_hint"))
        hint_lbl.setWordWrap(True)
        hint_lbl.setStyleSheet("color: #888; font-size: 11px;")
        root.addWidget(hint_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2a475e;")
        root.addWidget(sep)

        # Área rolável com as perguntas
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(16)
        form_layout.setContentsMargins(4, 4, 4, 4)

        for q in self.questions:
            widget = self._build_question_widget(q, form_layout)
            self._widgets.append((q, widget))

        form_layout.addStretch()
        scroll.setWidget(form_widget)
        root.addWidget(scroll)

        # Botões
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(
            tr("setup_dialog_apply_btn")
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _build_question_widget(
        self, q: SetupQuestion, parent_layout: QVBoxLayout
    ) -> QWidget:
        """Cria o widget de resposta para uma pergunta e adiciona ao layout."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        # Texto da pergunta
        prompt_lbl = QLabel(q.prompt)
        prompt_lbl.setWordWrap(True)
        prompt_lbl.setStyleSheet("font-weight: bold;")
        layout.addWidget(prompt_lbl)

        if q.is_choice:
            # ComboBox com as opções
            combo = QComboBox()
            for opt in q.options:
                combo.addItem(f"{opt.key}) {opt.label}", opt.key)
            layout.addWidget(combo)
            parent_layout.addWidget(container)
            return combo

        if q.is_yesno:
            # Sim / Não em ComboBox
            combo = QComboBox()
            combo.addItem(tr("setup_dialog_yes"), "y")
            combo.addItem(tr("setup_dialog_no"), "n")
            layout.addWidget(combo)
            parent_layout.addWidget(container)
            return combo

        # Campo de texto livre
        edit = QLineEdit()
        if q.default:
            edit.setText(q.default)
        edit.setPlaceholderText(tr("setup_dialog_text_placeholder"))
        layout.addWidget(edit)
        parent_layout.addWidget(container)
        return edit

    # ------------------------------------------------------------------
    # Coleta de respostas
    # ------------------------------------------------------------------

    def _on_accept(self):
        self.answers = []
        for q, widget in self._widgets:
            if isinstance(widget, QComboBox):
                # Retorna a chave (1, 2, y, n…)
                self.answers.append(widget.currentData() or widget.currentText())
            elif isinstance(widget, QLineEdit):
                self.answers.append(widget.text())
            else:
                self.answers.append("")
        self.accept()
