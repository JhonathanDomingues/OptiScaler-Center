"""
Use Case: Varredura de jogos
Detecta jogos, analisa DLLs e salva no banco
"""
from typing import List, Optional
from pathlib import Path

from utils.logger import LoggerMixin
from application.services.game_scanner import GameScanner
from domain.repositories.game_repository import GameRepository
from domain.entities.game import Game
from domain.enums.platform import Platform
from infrastructure.database.db_service import DatabaseService


class ScanGamesUseCase(LoggerMixin):
    """
    Caso de uso: Varredura de jogos Steam
    Detecta, analisa e persiste jogos no banco de dados
    """
    
    def __init__(
        self,
        game_scanner: GameScanner,
        db_service: DatabaseService
    ):
        """
        Inicializa o use case
        
        Args:
            game_scanner: GameScanner para detectar jogos
            db_service: DatabaseService para acesso ao banco
        """
        self.game_scanner = game_scanner
        self.db_service = db_service
    
    def execute(self) -> List[Game]:
        """
        Executa varredura completa de jogos Steam
        
        Returns:
            Lista de jogos detectados e salvos
        """
        self.logger.info("Iniciando varredura de jogos...")
        
        # Varrer jogos Steam
        games = self.game_scanner.scan_steam_games()
        
        if not games:
            self.logger.warning("Nenhum jogo detectado")
            return []
        
        # Salvar no banco de dados
        saved_games = []

        with self.db_service.get_connection() as conn:
            game_repo = GameRepository(conn)

            # Remover jogos Steam que não estão mais instalados
            existing_steam_games = [
                g for g in game_repo.find_all()
                if g.platform == Platform.STEAM
            ]
            scanned_appids = {g.appid for g in games if g.appid}
            scanned_paths = {str(g.path) for g in games}

            for existing in existing_steam_games:
                still_installed = (
                    (existing.appid and existing.appid in scanned_appids) or
                    str(existing.path) in scanned_paths
                )
                if not still_installed:
                    self.logger.info(f"Removendo jogo desinstalado: {existing.name}")
                    game_repo.delete(existing.id)

            for game in games:
                try:
                    game_repo.save(game)
                    saved_games.append(game)

                except Exception as e:
                    self.logger.error(f"Erro ao salvar jogo {game.name}: {e}")

        self.logger.info(f"✓ Varredura concluída: {len(saved_games)} jogos salvos")
        
        # Imprimir relatório
        self.game_scanner.print_scan_report(saved_games)
        
        return saved_games
    
    def scan_single_game(self, appid: int) -> Optional[Game]:
        """
        Varre e salva um jogo específico
        
        Args:
            appid: Steam AppID do jogo
        
        Returns:
            Game objeto ou None
        """
        self.logger.info(f"Varrendo jogo AppID: {appid}")
        
        # Varrer jogo
        game = self.game_scanner.scan_single_game(appid)
        
        if not game:
            self.logger.warning(f"Jogo {appid} não encontrado")
            return None
        
        # Salvar no banco
        with self.db_service.get_connection() as conn:
            game_repo = GameRepository(conn)
            game_repo.save(game)
        
        self.logger.info(f"✓ Jogo salvo: {game.name}")
        return game
    
    def rescan_game(self, game_id: int) -> Optional[Game]:
        """
        Re-analisa DLLs de um jogo existente
        
        Args:
            game_id: ID do jogo no banco
        
        Returns:
            Game atualizado ou None
        """
        with self.db_service.get_connection() as conn:
            game_repo = GameRepository(conn)
            
            # Buscar jogo
            game = game_repo.find_by_id(game_id)
            
            if not game:
                self.logger.warning(f"Jogo {game_id} não encontrado no banco")
                return None
            
            # Re-analisar
            game = self.game_scanner.rescan_game(game)
            
            # Atualizar no banco
            game_repo.save(game)
        
        self.logger.info(f"✓ Jogo re-analisado: {game.name}")
        return game
    
    def get_all_games(self) -> List[Game]:
        """
        Busca todos os jogos do banco
        
        Returns:
            Lista de jogos
        """
        with self.db_service.get_connection() as conn:
            game_repo = GameRepository(conn)
            return game_repo.find_all()
    
    def get_games_with_upscaling(self) -> List[Game]:
        """
        Busca jogos com suporte a upscaling

        Returns:
            Lista de jogos
        """
        with self.db_service.get_connection() as conn:
            game_repo = GameRepository(conn)
            return game_repo.find_with_upscaling_support()

    def add_manual_game(self, name: str, path: Path) -> Optional[Game]:
        """
        Adiciona um jogo manualmente (não detectado pelo Steam).
        Analisa DLLs no diretório informado e persiste com platform=MANUAL.
        Jogos manuais são preservados mesmo após novas varreduras Steam.

        Args:
            name: Nome do jogo
            path: Caminho da pasta de instalação

        Returns:
            Game salvo ou None em caso de erro
        """
        self.logger.info(f"Adicionando jogo manual: {name} ({path})")

        try:
            detected_dlls = self.game_scanner.dll_analyzer.analyze_game(path)
        except Exception as e:
            self.logger.warning(f"Falha ao analisar DLLs de {path}: {e}")
            detected_dlls = {}

        game = Game(
            name=name,
            path=path,
            platform=Platform.MANUAL,
        )
        for dll_type, dll_info in detected_dlls.items():
            game.supported_dlls[dll_type] = dll_info

        with self.db_service.get_connection() as conn:
            game_repo = GameRepository(conn)
            game_repo.save(game)

        self.logger.info(
            f"✓ Jogo manual salvo: {name} "
            f"(DLSS={game.has_dlss}, FSR={game.has_fsr}, XeSS={game.has_xess})"
        )
        return game
