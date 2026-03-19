"""
Testes para GameScanner
"""
import pytest
from pathlib import Path
from application.services.game_scanner import GameScanner
from infrastructure.steam.steam_service import SteamService
from application.services.dll_analyzer import DLLAnalyzer
from domain.enums.platform import Platform


class TestGameScanner:
    """Testes do scanner de jogos"""
    
    def test_process_game_valid(self, mock_game_info, temp_dir):
        """Testa processamento de jogo válido"""
        # Criar diretório do jogo
        game_path = temp_dir / "TestGame"
        game_path.mkdir()
        
        # Atualizar game_info com path real
        mock_game_info["install_path"] = game_path
        
        # Criar DLL com tamanho suficiente (>1MB para DLSS)
        dll = game_path / "nvngx_dlss.dll"
        dll.write_bytes(b"fake dlss" * 200000)
        
        steam_service = SteamService()
        dll_analyzer = DLLAnalyzer(max_depth=2)
        scanner = GameScanner(steam_service, dll_analyzer)
        
        game = scanner._process_game(mock_game_info)
        
        assert game is not None
        assert game.name == "Test Game"
        assert game.steam_appid == "480"
        assert game.platform == Platform.STEAM
        assert game.path == game_path
        assert game.has_dlss == True
    
    def test_process_game_path_not_exists(self, mock_game_info):
        """Testa jogo com path inexistente"""
        steam_service = SteamService()
        dll_analyzer = DLLAnalyzer(max_depth=2)
        scanner = GameScanner(steam_service, dll_analyzer)
        
        game = scanner._process_game(mock_game_info)
        
        # Deve retornar None para path inexistente
        assert game is None
    
    def test_process_game_no_dlls(self, mock_game_info, temp_dir):
        """Testa jogo sem DLLs upscaling"""
        game_path = temp_dir / "TestGame"
        game_path.mkdir()
        
        mock_game_info["install_path"] = game_path
        
        steam_service = SteamService()
        dll_analyzer = DLLAnalyzer(max_depth=2)
        scanner = GameScanner(steam_service, dll_analyzer)
        
        game = scanner._process_game(mock_game_info)
        
        assert game is not None
        assert game.has_dlss == False
        assert game.has_fsr == False
        assert len(game.supported_dlls) == 0
    
    def test_scan_steam_games(self, mock_steam_library):
        """Testa scan completo de jogos Steam"""
        steam_service = SteamService()
        steam_service.steam_path = mock_steam_library
        
        dll_analyzer = DLLAnalyzer(max_depth=2)
        scanner = GameScanner(steam_service, dll_analyzer)
        
        games = scanner.scan_steam_games()
        
        assert len(games) > 0
        
        game = games[0]
        assert game.name is not None
        assert game.steam_appid is not None
        assert game.platform == Platform.STEAM
    
    def test_process_game_with_multiple_dlls(self, mock_game_info, temp_dir):
        """Testa jogo com múltiplos tipos de DLL"""
        game_path = temp_dir / "TestGame"
        game_path.mkdir()
        
        mock_game_info["install_path"] = game_path
        
        # Criar múltiplas DLLs com tamanhos adequados
        (game_path / "nvngx_dlss.dll").write_bytes(b"dlss" * 300000)  # ~1.2MB
        (game_path / "amd_fidelityfx_vk.dll").write_bytes(b"fsr" * 30000)  # ~120KB
        (game_path / "libxess.dll").write_bytes(b"xess" * 300000)  # ~1.2MB
        
        steam_service = SteamService()
        dll_analyzer = DLLAnalyzer(max_depth=2)
        scanner = GameScanner(steam_service, dll_analyzer)
        
        game = scanner._process_game(mock_game_info)
        
        assert game is not None
        assert game.has_dlss == True
        assert game.has_fsr == True
        assert len(game.supported_dlls) == 3
        # Verificar que as keys corretas existem
        assert 'DLSS' in game.supported_dlls
        assert 'FSR' in game.supported_dlls
        assert 'XeSS' in game.supported_dlls
