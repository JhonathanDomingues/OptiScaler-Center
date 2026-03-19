"""
Configurações e fixtures compartilhadas para testes
"""
import sys
from pathlib import Path
import pytest
import tempfile
import shutil

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def temp_dir():
    """Cria diretório temporário para testes"""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def mock_steam_library(temp_dir):
    """Cria estrutura de biblioteca Steam mock"""
    steam_path = temp_dir / ".steam" / "steam"
    steamapps = steam_path / "steamapps"
    steamapps.mkdir(parents=True)
    
    # Criar libraryfolders.vdf
    library_vdf = steamapps / "libraryfolders.vdf"
    library_vdf.write_text('''
"libraryfolders"
{
    "0"
    {
        "path"  "%s"
        "label" ""
        "contentid" "123"
    }
}
''' % str(steam_path))
    
    # Criar manifest de jogo de teste
    manifest = steamapps / "appmanifest_480.acf"
    manifest.write_text('''
"AppState"
{
    "appid"  "480"
    "name"  "Test Game"
    "installdir"  "TestGame"
    "StateFlags"  "4"
}
''')
    
    # Criar pasta do jogo
    game_dir = steamapps / "common" / "TestGame"
    game_dir.mkdir(parents=True)
    
    # Criar DLL fake
    dll = game_dir / "nvngx_dlss.dll"
    dll.write_bytes(b"fake dll content")
    
    return steam_path


@pytest.fixture
def mock_game_info():
    """Informações de jogo mock"""
    return {
        "appid": "480",
        "name": "Test Game",
        "install_path": Path("/fake/path/TestGame")
    }


@pytest.fixture
def mock_database(temp_dir):
    """Database temporário para testes"""
    from infrastructure.database.db_service import DatabaseService
    from pathlib import Path
    
    db_path = temp_dir / "test.db"
    db = DatabaseService(db_path)  # A inicialização é automática
    
    yield db
    
    # Não precisa chamar close() pois usamos context manager
