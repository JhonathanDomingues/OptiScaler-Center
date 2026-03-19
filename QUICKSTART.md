# 🚀 Quick Start - Desenvolvimento

Referência rápida para desenvolvedores do OptiScaler Center.

## ⚡ Comandos Rápidos

```bash
# Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Executar aplicação
python src/main.py

# Rodar testes
pytest tests/ -v

# Formatar código
black src/

# Verificar linting
flake8 src/

# Type checking
mypy src/

# Ver logs
tail -f logs/optiscaler_center.log
```

## 📂 Estrutura Rápida

```
src/
├── main.py                      # ← Entry point
├── presentation/                # UI
│   ├── main_window.py          # ← Janela principal
│   └── widgets/                # Widgets customizados
├── application/                 # Lógica de aplicação
│   ├── use_cases/              # Casos de uso
│   └── services/               # Serviços
├── domain/                      # Lógica de negócio
│   ├── entities/               # ← Entidades criadas
│   ├── enums/                  # ← Enums criados
│   └── repositories/           # Interfaces de repositórios
├── infrastructure/              # Implementações
│   ├── config/                 # ← ConfigService criado
│   ├── database/               # ← DatabaseService criado
│   ├── steam/                  # Próximo: SteamService
│   ├── github/                 # Próximo: GitHubService
│   └── filesystem/             # Próximo: FileSystemService
└── utils/
    ├── constants.py            # ← Constantes criadas
    └── logger.py               # ← Logger criado
```

## 🎯 Próximas Implementações

### 1. Steam Service (Prioridade Alta)

**Arquivo**: `src/infrastructure/steam/steam_service.py`

```python
class SteamService(LoggerMixin):
    def detect_steam_path(self) -> Optional[Path]:
        """Detecta instalação do Steam"""
        pass
    
    def get_library_folders(self) -> List[Path]:
        """Lista todas as bibliotecas Steam"""
        pass
    
    def get_installed_games(self) -> List[Dict]:
        """Lista jogos instalados"""
        pass
```

**Referência**: TECHNICAL_SPECS.md seção "Detecção de Jogos"

### 2. Game Scanner Service

**Arquivo**: `src/application/services/game_scanner.py`

```python
class GameScanner(LoggerMixin):
    def __init__(self, steam_service: SteamService):
        self.steam_service = steam_service
    
    def scan_steam_games(self) -> List[Game]:
        """Escaneia jogos do Steam"""
        pass
```

### 3. DLL Analyzer Service

**Arquivo**: `src/application/services/dll_analyzer.py`

```python
class DLLAnalyzer(LoggerMixin):
    def analyze_game(self, game_path: Path) -> Dict[str, DLLInfo]:
        """Analisa DLLs em um jogo"""
        pass
```

### 4. GitHub Service

**Arquivo**: `src/infrastructure/github/github_service.py`

```python
class GitHubService(LoggerMixin):
    def get_releases(self) -> List[OptiScalerVersion]:
        """Lista releases do OptiScaler"""
        pass
    
    async def download_version(self, version: str) -> Path:
        """Baixa uma versão"""
        pass
```

## 🔧 Padrões de Código

### Entidade

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class MinhaEntidade:
    """Descrição da entidade"""
    id: Optional[int] = None
    nome: str = ""
    
    def __str__(self):
        return f"MinhaEntidade({self.nome})"
```

### Serviço

```python
from utils.logger import LoggerMixin

class MeuServico(LoggerMixin):
    """Descrição do serviço"""
    
    def __init__(self, dependency: Dependency):
        self.dependency = dependency
    
    def fazer_algo(self) -> ResultType:
        """Descrição do método"""
        self.logger.info("Fazendo algo")
        # Implementação
        return resultado
```

### Use Case

```python
class MeuUseCase:
    """Caso de uso: Descrição"""
    
    def __init__(self, service: Service, repository: Repository):
        self.service = service
        self.repository = repository
    
    def execute(self, params: ParamType) -> ResultType:
        """Executa o caso de uso"""
        # 1. Validar
        # 2. Processar
        # 3. Persistir
        # 4. Retornar
        pass
```

### Repository

```python
from abc import ABC, abstractmethod
from typing import List, Optional

class GameRepository(ABC):
    """Interface para repositório de jogos"""
    
    @abstractmethod
    def add(self, game: Game) -> int:
        pass
    
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Game]:
        pass

class SQLiteGameRepository(GameRepository):
    """Implementação SQLite"""
    
    def __init__(self, db_service: DatabaseService):
        self.db = db_service
    
    def add(self, game: Game) -> int:
        # Implementação
        pass
```

### Widget PyQt6

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from utils.logger import LoggerMixin

class MeuWidget(QWidget, LoggerMixin):
    """Descrição do widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura interface"""
        layout = QVBoxLayout(self)
        # Adicionar componentes
```

## 🧪 Testes

### Teste Unitário

```python
# tests/unit/test_game_scanner.py
import pytest
from application.services.game_scanner import GameScanner

class TestGameScanner:
    @pytest.fixture
    def scanner(self, mock_steam_service):
        return GameScanner(mock_steam_service)
    
    def test_scan_games(self, scanner):
        games = scanner.scan_steam_games()
        assert len(games) > 0
        assert all(isinstance(g, Game) for g in games)
```

### Teste de Integração

```python
# tests/integration/test_steam_detection.py
def test_detect_real_steam_installation():
    service = SteamService()
    path = service.detect_steam_path()
    
    if path:  # Só testa se Steam estiver instalado
        assert path.exists()
        libraries = service.get_library_folders()
        assert len(libraries) > 0
```

## 📊 Debugging

### Logs

```python
# Em qualquer classe com LoggerMixin
self.logger.debug("Debug info")
self.logger.info("Info message")
self.logger.warning("Warning message")
self.logger.error("Error message")
```

### Breakpoints

```python
import pdb; pdb.set_trace()  # Python debugger
# ou
breakpoint()  # Python 3.7+
```

### VS Code

F5 para debug com configuração em `.vscode/launch.json`

## 🔄 Git Workflow

```bash
# Criar branch
git checkout -b feature/steam-scanner

# Fazer commits frequentes
git add src/infrastructure/steam/
git commit -m "Add: Steam library detection"

# Push
git push origin feature/steam-scanner

# Atualizar com main
git checkout main
git pull
git checkout feature/steam-scanner
git rebase main
```

## 📚 Referências Rápidas

- **Arquitetura**: [DOCUMENTATION.md#arquitetura](DOCUMENTATION.md#arquitetura-do-sistema)
- **Specs Técnicas**: [TECHNICAL_SPECS.md](TECHNICAL_SPECS.md)
- **APIs**:
  - PyQt6: https://doc.qt.io/qtforpython-6/
  - Requests: https://requests.readthedocs.io/
  - VDF: https://github.com/ValvePython/vdf
  - GitHub API: https://docs.github.com/en/rest

## 💡 Dicas

1. **Sempre use type hints**
   ```python
   def funcao(param: str) -> int:
   ```

2. **Docstrings são obrigatórias**
   ```python
   """Descrição breve.
   
   Descrição detalhada se necessário.
   """
   ```

3. **Trate exceções apropriadamente**
   ```python
   try:
       algo_perigoso()
   except EspecificException as e:
       self.logger.error(f"Erro: {e}")
       raise
   ```

4. **Use Path ao invés de strings**
   ```python
   from pathlib import Path
   caminho = Path("data") / "games.db"
   ```

5. **Configurações via ConfigService**
   ```python
   theme = self.config.get('general.theme', 'dark')
   self.config.set('general.theme', 'light')
   ```

## 🎨 UI Development

### Aplicar estilo
```python
widget.setStyleSheet("""
    QWidget {
        background-color: #2d2d2d;
        color: #ffffff;
    }
""")
```

### Signals/Slots
```python
button.clicked.connect(self.on_button_clicked)

def on_button_clicked(self):
    # Handler
    pass
```

### Threading
```python
from PyQt6.QtCore import QThread

class Worker(QThread):
    finished = pyqtSignal(list)
    
    def run(self):
        result = operacao_longa()
        self.finished.emit(result)

# Uso
worker = Worker()
worker.finished.connect(self.on_finished)
worker.start()
```

## 🚨 Common Issues

1. **Import circular**: Use type hints com strings
   ```python
   from typing import TYPE_CHECKING
   if TYPE_CHECKING:
       from other_module import OtherClass
   
   def method(self, param: 'OtherClass'):
       pass
   ```

2. **Qt event loop bloqueado**: Use QThread para operações longas

3. **Path não existe**: Sempre use `mkdir(parents=True, exist_ok=True)`

4. **Banco travado**: Use context manager do DatabaseService

---

**Pro tip**: Mantenha este arquivo aberto durante desenvolvimento! 📌
