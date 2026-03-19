# Testes do OptiScaler Center

## Estrutura

```
tests/
├── __init__.py                  # Inicialização
├── conftest.py                  # Fixtures compartilhadas
├── test_steam_service.py        # Testes do SteamService
├── test_vdf_parser.py           # Testes do VDFParser
├── test_dll_analyzer.py         # Testes do DLLAnalyzer
├── test_game_scanner.py         # Testes do GameScanner
└── test_use_cases.py            # Testes dos Use Cases
```

## Instalação

```bash
# Instalar dependências de teste
pip install -r requirements-dev.txt
```

## Executando os Testes

### Todos os testes
```bash
pytest tests/
```

### Com cobertura
```bash
pytest tests/ --cov=src --cov-report=html
```

### Teste específico
```bash
pytest tests/test_steam_service.py
```

### Teste específico com verbose
```bash
pytest tests/test_steam_service.py -v
```

### Teste específico de uma classe
```bash
pytest tests/test_steam_service.py::TestSteamService
```

### Teste específico de um método
```bash
pytest tests/test_steam_service.py::TestSteamService::test_detect_steam_path_linux
```

## Fixtures Disponíveis

### `temp_dir`
Cria diretório temporário limpo para cada teste.

```python
def test_example(temp_dir):
    file = temp_dir / "test.txt"
    file.write_text("content")
```

### `mock_steam_library`
Cria estrutura completa de biblioteca Steam mock com:
- libraryfolders.vdf
- appmanifest_480.acf
- Pasta de jogo de teste
- DLL fake

```python
def test_example(mock_steam_library):
    service = SteamService()
    service.steam_path = mock_steam_library
```

### `mock_game_info`
Dict com informações de jogo de teste.

```python
def test_example(mock_game_info):
    assert mock_game_info["name"] == "Test Game"
```

### `mock_database`
DatabaseService temporário totalmente funcional.

```python
def test_example(mock_database):
    with mock_database.get_connection() as conn:
        repo = GameRepository(conn)
        # usar repo...
```

## Cobertura de Testes

### Componentes Testados

- ✅ **SteamService**: Detecção Steam, leitura bibliotecas, listagem jogos
- ✅ **VDFParser**: Parse VDF simples, aninhado, libraryfolders, manifests
- ✅ **DLLAnalyzer**: Detecção DLSS/FSR/XeSS, profundidade, hash
- ✅ **GameScanner**: Processamento jogos, scan completo, múltiplas DLLs
- ✅ **ScanGamesUseCase**: Scan e persistência, biblioteca vazia, updates
- ✅ **InstallOptiScalerUseCase**: Validação de requisitos
- ✅ **UninstallOptiScalerUseCase**: Validação de requisitos

### Casos de Teste

- ✅ Caminhos felizes (happy paths)
- ✅ Validação de erros
- ✅ Edge cases (arquivos não encontrados, dados inválidos)
- ✅ Profundidade de busca
- ✅ Múltiplos resultados
- ✅ Persistência de dados

## Executando Análise de Código

### Black (formatação)
```bash
black src/ tests/
```

### Flake8 (linting)
```bash
flake8 src/ tests/
```

### Mypy (type checking)
```bash
mypy src/
```

### Pylint (análise completa)
```bash
pylint src/
```

## CI/CD

Para integração contínua, adicione ao `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests
        run: pytest tests/ --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```
