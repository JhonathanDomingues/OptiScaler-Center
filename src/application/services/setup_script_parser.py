"""
Parser de scripts de configuração do OptiScaler (setup.sh / setup.bat).

Extrai as perguntas interativas definidas no script para que possam
ser apresentadas em uma interface gráfica, eliminando a necessidade de
abrir um terminal externo.

Padrões reconhecidos
--------------------
Shell (.sh):
  echo "Texto de prompt"          → contexto / título da pergunta
  echo "N) texto da opção"        → opção numerada (N = dígito)
  echo "N. texto da opção"        → opção numerada (alternativa)
  read -p "prompt" VARNAME        → pergunta (prompt na própria linha)
  read VARNAME                    → pergunta (usa echo anterior como prompt)

Batch (.bat):
  echo Texto de prompt            → contexto / título
  echo N. texto                   → opção numerada
  echo N) texto                   → opção numerada
  set /p VARNAME=prompt           → pergunta
  choice /C AB... /M "prompt"     → pergunta de múltipla escolha (letras)
"""
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


# ---------------------------------------------------------------------------
# Estruturas de dados
# ---------------------------------------------------------------------------

@dataclass
class SetupOption:
    """Uma opção de uma pergunta de múltipla escolha."""
    key: str    # "1", "2", "A", "B", etc.
    label: str  # Texto exibido para o usuário


@dataclass
class SetupQuestion:
    """Uma pergunta interativa extraída do script."""
    prompt: str                              # Texto da pergunta
    var_name: str                            # Nome da variável que receberá a resposta
    options: List[SetupOption] = field(default_factory=list)
    default: str = ""

    @property
    def is_choice(self) -> bool:
        """Pergunta com opções numeradas/letradas."""
        return len(self.options) > 0

    @property
    def is_yesno(self) -> bool:
        """Pergunta sim/não."""
        if len(self.options) == 2:
            keys = {o.key.lower() for o in self.options}
            return keys <= {'y', 'n', 's', 'yes', 'no', 'sim', 'não', 'nao'}
        return False


# ---------------------------------------------------------------------------
# Expressões regulares
# ---------------------------------------------------------------------------

# Shell: opção numerada — ex: "1) NVIDIA" ou "  2. AMD  "
_SH_OPTION = re.compile(r'^\s*(\d+)[).]\s+(.+)$')

# Shell: echo com string (aspas simples ou duplas, ou sem aspas)
_SH_ECHO = re.compile(r'^\s*echo\s+(?:"([^"]*)"\'?|\'([^\']*)\'|(.+))$', re.IGNORECASE)

# Shell: read com prompt inline:  read -p "texto" VARNAME
_SH_READ_P = re.compile(r'^\s*read\s+(?:-[a-z]\s+)*-p\s+(?:"([^"]*)"|\'([^\']*)\')\s+(\w+)', re.IGNORECASE)

# Shell: read simples:  read VARNAME
_SH_READ = re.compile(r'^\s*read\s+(\w+)\s*$', re.IGNORECASE)

# Batch: opção numerada — ex: "echo 1. NVIDIA" ou "echo 2) AMD"
_BAT_OPTION = re.compile(r'^\s*echo\s+(\d+)[).]\s+(.+)$', re.IGNORECASE)

# Batch: echo simples
_BAT_ECHO = re.compile(r'^\s*echo\s+(.+)$', re.IGNORECASE)

# Batch: set /p VARNAME=prompt
_BAT_SET_P = re.compile(r'^\s*set\s+/p\s+(\w+)=(.*)$', re.IGNORECASE)

# Batch: choice /C chars /M "prompt"
_BAT_CHOICE = re.compile(
    r'^\s*choice\s+.*?/c\s+([A-Za-z]+).*?/m\s+(?:"([^"]*)"|\'([^\']*)\').*$',
    re.IGNORECASE
)

# Linhas em branco / comentários / outras diretivas a ignorar
_SKIP_LINE = re.compile(r'^\s*(?:#|::|@echo|rem\s|pause|cls|@cls|exit|if\s|fi\s*$|else|then|do\s|done\s*$|case\s|esac\s*$|\[)', re.IGNORECASE)


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------

def parse_script(script_path: Path) -> List[SetupQuestion]:
    """
    Lê e analisa um script de configuração, retornando as perguntas encontradas.

    Args:
        script_path: Caminho para o arquivo .sh ou .bat

    Returns:
        Lista de SetupQuestion em ordem de aparição no script.
        Lista vazia se nenhuma pergunta interativa for encontrada.
    """
    script_path = Path(script_path)
    if not script_path.exists():
        return []

    suffix = script_path.suffix.lower()
    try:
        content = script_path.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return []

    if suffix == '.bat':
        return _parse_batch(content)
    else:
        return _parse_shell(content)


# ---------------------------------------------------------------------------
# Parsers internos
# ---------------------------------------------------------------------------

def _parse_shell(content: str) -> List[SetupQuestion]:
    """Analisa scripts shell (.sh)."""
    lines = content.splitlines()
    questions: List[SetupQuestion] = []

    # Contexto acumulado entre linhas
    pending_echoes: List[str] = []      # echos acumulados antes de um read
    pending_options: List[SetupOption] = []  # opções numeradas acumuladas

    def _flush_echoes() -> str:
        """Retorna o texto contextual acumulado e limpa o buffer."""
        text = " | ".join(t for t in pending_echoes if t)
        pending_echoes.clear()
        return text.strip()

    for line in lines:
        if _SKIP_LINE.match(line):
            # Se trocarmos de bloco, esvaziar opções sem read associado
            if not pending_options:
                pending_echoes.clear()
            continue

        # --- Opção numerada dentro de echo ---
        m = _SH_OPTION.match(line)
        if m:
            pending_options.append(SetupOption(key=m.group(1), label=m.group(2).strip()))
            continue

        # --- Linha de echo normal ---
        m = _SH_ECHO.match(line)
        if m:
            text = (m.group(1) or m.group(2) or m.group(3) or "").strip()
            # Se tem padrão de opção numerada no próprio echo (sem separação)
            mo = _SH_OPTION.match(text)
            if mo:
                pending_options.append(SetupOption(key=mo.group(1), label=mo.group(2).strip()))
            elif text:
                # Novo bloco de echo: se havia opções para outro read, resetar
                if pending_options and not any(
                    _SH_READ_P.match(l) or _SH_READ.match(l)
                    for l in lines[lines.index(line):lines.index(line) + 5]
                    if l
                ):
                    pending_options.clear()
                pending_echoes.append(text)
            continue

        # --- read -p "prompt" VARNAME ---
        m = _SH_READ_P.match(line)
        if m:
            inline_prompt = (m.group(1) or m.group(2) or "").strip()
            var_name = m.group(3)
            context = _flush_echoes()
            full_prompt = f"{context}: {inline_prompt}" if context else inline_prompt
            questions.append(SetupQuestion(
                prompt=full_prompt or var_name,
                var_name=var_name,
                options=list(pending_options),
            ))
            pending_options.clear()
            continue

        # --- read VARNAME ---
        m = _SH_READ.match(line)
        if m:
            var_name = m.group(1)
            context = _flush_echoes()
            questions.append(SetupQuestion(
                prompt=context or var_name,
                var_name=var_name,
                options=list(pending_options),
            ))
            pending_options.clear()
            continue

    return questions


def _parse_batch(content: str) -> List[SetupQuestion]:
    """Analisa scripts batch (.bat)."""
    lines = content.splitlines()
    questions: List[SetupQuestion] = []

    pending_echoes: List[str] = []
    pending_options: List[SetupOption] = []

    def _flush_echoes() -> str:
        text = " | ".join(t for t in pending_echoes if t)
        pending_echoes.clear()
        return text.strip()

    for line in lines:
        if _SKIP_LINE.match(line):
            continue

        # --- Opção numerada ---
        m = _BAT_OPTION.match(line)
        if m:
            pending_options.append(SetupOption(key=m.group(1), label=m.group(2).strip()))
            continue

        # --- choice /C /M ---
        m = _BAT_CHOICE.match(line)
        if m:
            chars = m.group(1).upper()
            prompt_text = (m.group(2) or m.group(3) or "").strip()
            context = _flush_echoes()
            full_prompt = f"{context}: {prompt_text}" if context else prompt_text
            opts = [SetupOption(key=c, label=c) for c in chars]
            questions.append(SetupQuestion(
                prompt=full_prompt or "choice",
                var_name="errorlevel",
                options=opts,
            ))
            pending_options.clear()
            continue

        # --- set /p VARNAME=prompt ---
        m = _BAT_SET_P.match(line)
        if m:
            var_name = m.group(1)
            inline_prompt = m.group(2).strip()
            context = _flush_echoes()
            full_prompt = f"{context}: {inline_prompt}" if context else inline_prompt
            questions.append(SetupQuestion(
                prompt=full_prompt or var_name,
                var_name=var_name,
                options=list(pending_options),
            ))
            pending_options.clear()
            continue

        # --- echo normal ---
        m = _BAT_ECHO.match(line)
        if m:
            text = m.group(1).strip()
            if text.lower() not in ('off', 'on', '.', ''):
                pending_echoes.append(text)
            continue

    return questions
