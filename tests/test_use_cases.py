"""
Testes para Use Cases
"""
import pytest
from pathlib import Path
from application.use_cases.scan_games import ScanGamesUseCase
from application.services.game_scanner import GameScanner
from infrastructure.steam.steam_service import SteamService
from application.services.dll_analyzer import DLLAnalyzer


class TestScanGamesUseCase:
    """Testes do caso de uso ScanGames"""
    
    def test_scan_and_persist_games(self, mock_database, mock_steam_library):
        """Testa scan e persistência de jogos"""
        # Setup
        steam_service = SteamService()
        steam_service.steam_path = mock_steam_library
        
        dll_analyzer = DLLAnalyzer(max_depth=2)
        game_scanner = GameScanner(steam_service, dll_analyzer)
        
        use_case = ScanGamesUseCase(game_scanner, mock_database)
        
        # Executar
        games = use_case.execute()
        
        # Verificar
        assert len(games) > 0
        
        # Verificar que foi salvo no banco
        from domain.repositories.game_repository import GameRepository
        with mock_database.get_connection() as conn:
            repo = GameRepository(conn)
            saved_games = repo.find_all()
            
            assert len(saved_games) > 0
    
    def test_scan_empty_library(self, mock_database, temp_dir):
        """Testa scan de biblioteca vazia"""
        # Setup com Steam vazio
        steam_service = SteamService()
        steam_service.steam_path = temp_dir / "empty_steam"
        
        dll_analyzer = DLLAnalyzer(max_depth=2)
        game_scanner = GameScanner(steam_service, dll_analyzer)
        
        use_case = ScanGamesUseCase(game_scanner, mock_database)
        
        # Executar
        games = use_case.execute()
        
        # Deve retornar lista vazia sem erros
        assert games == []
    
    def test_scan_updates_existing_games(self, mock_database, mock_steam_library):
        """Testa que re-scan atualiza jogos existentes"""
        # Setup
        steam_service = SteamService()
        steam_service.steam_path = mock_steam_library
        
        dll_analyzer = DLLAnalyzer(max_depth=2)
        game_scanner = GameScanner(steam_service, dll_analyzer)
        
        use_case = ScanGamesUseCase(game_scanner, mock_database)
        
        # Primeiro scan
        games1 = use_case.execute()
        count1 = len(games1)
        
        # Segundo scan
        games2 = use_case.execute()
        count2 = len(games2)
        
        # Não deve duplicar jogos
        assert count1 == count2


class TestFetchVersionsUseCase:
    """Testes do caso de uso FetchVersions"""
    
    @pytest.mark.skip(reason="Requer conexão com GitHub API")
    def test_fetch_from_github(self, mock_database, temp_dir):
        """Testa busca de versões no GitHub"""
        from infrastructure.github.github_service import GitHubService
        from application.use_cases.fetch_versions import FetchVersionsUseCase
        
        github_service = GitHubService(temp_dir / "cache")
        use_case = FetchVersionsUseCase(github_service, mock_database)
        
        versions = use_case.execute()
        
        # Deve retornar lista de versões
        assert isinstance(versions, list)


class TestInstallOptiScalerUseCase:
    """Testes do caso de uso Install"""
    
    def test_install_requires_valid_game(self, mock_database, temp_dir):
        """Testa que instalação requer jogo válido"""
        from application.use_cases.install_optiscaler import InstallOptiScalerUseCase
        from domain.enums.dll_type import DLLType
        
        use_case = InstallOptiScalerUseCase(mock_database, temp_dir / "backups")
        
        # Tentar instalar em jogo inexistente
        result = use_case.execute(
            game_id=99999,
            version_id=1,
            target_dll_type=DLLType.DLSS
        )
        
        # Deve falhar
        assert result == False


class TestUninstallOptiScalerUseCase:
    """Testes do caso de uso Uninstall"""
    
    def test_uninstall_requires_valid_game(self, mock_database):
        """Testa que desinstalação requer jogo válido"""
        from application.use_cases.uninstall_optiscaler import UninstallOptiScalerUseCase
        
        use_case = UninstallOptiScalerUseCase(mock_database)
        
        # Tentar desinstalar de jogo inexistente
        result = use_case.execute(game_id=99999)
        
        # Deve falhar
        assert result == False
