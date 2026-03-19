"""
Testes para SteamService
"""
import pytest
from pathlib import Path
from infrastructure.steam.steam_service import SteamService


class TestSteamService:
    """Testes do serviço Steam"""
    
    def test_detect_steam_path_linux(self, monkeypatch, temp_dir):
        """Testa detecção de Steam no Linux"""
        # Mock home directory
        steam_path = temp_dir / ".steam" / "steam"
        steam_path.mkdir(parents=True)
        
        monkeypatch.setattr(Path, "home", lambda: temp_dir)
        
        service = SteamService()
        detected = service.detect_steam_path()
        
        assert detected is not None
        assert detected.exists()
    
    def test_get_library_folders(self, mock_steam_library, monkeypatch):
        """Testa leitura de bibliotecas Steam"""
        service = SteamService()
        
        # Mock detect_steam_path para retornar nossa biblioteca mock
        monkeypatch.setattr(service, 'detect_steam_path', lambda: mock_steam_library)
        service.steam_path = mock_steam_library
        
        libraries = service.get_library_folders()
        
        assert len(libraries) > 0
        assert all(isinstance(p, Path) for p in libraries)
    
    def test_get_installed_games(self, mock_steam_library, monkeypatch):
        """Testa listagem de jogos instalados"""
        service = SteamService()
        
        # Mock detect_steam_path
        monkeypatch.setattr(service, 'detect_steam_path', lambda: mock_steam_library)
        service.steam_path = mock_steam_library
        
        games = service.get_installed_games()
        
        assert len(games) > 0
        
        # Verificar estrutura do primeiro jogo
        game = games[0]
        assert "appid" in game
        assert "name" in game
        assert "install_path" in game
        assert isinstance(game["install_path"], Path)
    
    def test_get_installed_games_validates_installdir(self, temp_dir, monkeypatch):
        """Testa que jogos sem installdir são tratados corretamente"""
        # Criar estrutura Steam mock
        steam_path = temp_dir / "steam"
        steamapps = steam_path / "steamapps"
        steamapps.mkdir(parents=True)
        
        # Criar libraryfolders.vdf
        library_vdf = steamapps / "libraryfolders.vdf"
        library_vdf.write_text(f'''
"libraryfolders"
{{
    "0"
    {{
        "path"  "{steam_path}"
    }}
}}
''')
        
        # Criar manifest válido
        valid_manifest = steamapps / "appmanifest_480.acf"
        valid_manifest.write_text('''
"AppState"
{
    "appid"  "480"
    "name"  "Valid Game"
    "installdir"  "ValidGame"
}
''')
        
        # Criar pasta do jogo
        game_dir = steamapps / "common" / "ValidGame"
        game_dir.mkdir(parents=True)
        
        # Criar manifest inválido sem installdir
        invalid_manifest = steamapps / "appmanifest_999.acf"
        invalid_manifest.write_text('''
"AppState"
{
    "appid"  "999"
    "name"  "Invalid Game"
}
''')
        
        service = SteamService()
        monkeypatch.setattr(service, 'detect_steam_path', lambda: steam_path)
        service.steam_path = steam_path
        
        games = service.get_installed_games()
        
        # Deve ter apenas o jogo válido, não o inválido
        assert all(g.get("appid") != "999" for g in games)
        assert any(g.get("appid") == "480" for g in games)
    
    def test_steam_path_not_found(self, temp_dir, monkeypatch):
        """Testa quando Steam não está instalado"""
        # Mock detect_steam_path para retornar None
        def mock_detect():
            return None
        
        service = SteamService()
        monkeypatch.setattr(service, 'detect_steam_path', mock_detect)
        
        # Tentar buscar jogos sem Steam
        games = service.get_installed_games()
        
        # Deve retornar lista vazia
        assert games == []
