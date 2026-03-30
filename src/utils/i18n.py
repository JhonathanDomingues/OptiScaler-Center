"""
Serviço de internacionalização (i18n)
Suporta múltiplos idiomas com fallback automático para inglês.

Uso:
    from utils.i18n import tr
    label = QLabel(tr("scan_games_btn"))
    msg = tr("games_found", count=5)
"""
import json
from pathlib import Path
from typing import Optional


class TranslationService:
    """Gerencia traduções da aplicação"""

    SUPPORTED_LANGUAGES = {
        'pt_BR': 'Português (Brasil)',
        'en':    'English',
    }
    DEFAULT_LANGUAGE  = 'pt_BR'
    FALLBACK_LANGUAGE = 'en'

    def __init__(self, locales_dir: Path):
        self._locales_dir     = locales_dir
        self._current_lang    = self.DEFAULT_LANGUAGE
        self._translations: dict[str, dict] = {}
        self._load_all()

    # ------------------------------------------------------------------
    # Carregamento
    # ------------------------------------------------------------------

    def _load_all(self):
        """Carrega todos os arquivos .json disponíveis no diretório de locales."""
        for lang in self.SUPPORTED_LANGUAGES:
            path = self._locales_dir / f"{lang}.json"
            if path.exists():
                try:
                    self._translations[lang] = json.loads(path.read_text(encoding='utf-8'))
                except Exception:
                    self._translations[lang] = {}
            else:
                self._translations[lang] = {}

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def set_language(self, language: str):
        """Define o idioma atual. Ignora idiomas não suportados."""
        if language in self.SUPPORTED_LANGUAGES:
            self._current_lang = language

    def get_language(self) -> str:
        """Retorna o código do idioma atual."""
        return self._current_lang

    def get_language_name(self) -> str:
        """Retorna o nome do idioma atual."""
        return self.SUPPORTED_LANGUAGES.get(self._current_lang, self._current_lang)

    def available_languages(self) -> dict[str, str]:
        """Retorna {código: nome} para todos os idiomas suportados."""
        return dict(self.SUPPORTED_LANGUAGES)

    def tr(self, key: str, **kwargs) -> str:
        """
        Traduz uma chave para o idioma atual.
        Suporta formatação via kwargs: tr("games_found", count=5)
        Fallback: inglês → a própria chave.
        """
        text = (
            self._translations.get(self._current_lang, {}).get(key)
            or self._translations.get(self.FALLBACK_LANGUAGE, {}).get(key)
            or key
        )
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError):
                pass
        return text


# ---------------------------------------------------------------------------
# Singleton global
# ---------------------------------------------------------------------------

_service: Optional[TranslationService] = None


def init_i18n(locales_dir: Path, language: str = 'pt_BR'):
    """Inicializa o serviço de tradução. Deve ser chamado antes de criar widgets."""
    global _service
    _service = TranslationService(locales_dir)
    _service.set_language(language)


def tr(key: str, **kwargs) -> str:
    """Função global de tradução. Retorna a chave se o serviço não foi inicializado."""
    if _service is None:
        return key
    return _service.tr(key, **kwargs)


def get_service() -> Optional[TranslationService]:
    """Retorna a instância do serviço de tradução."""
    return _service
