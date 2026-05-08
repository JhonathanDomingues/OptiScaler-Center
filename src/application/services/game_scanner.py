"""
Serviço de varredura de jogos
Orquestra detecção Steam + análise de DLLs + persistência
"""
import platform as _platform
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

from utils.logger import LoggerMixin
from infrastructure.steam.steam_service import SteamService
from application.services.dll_analyzer import DLLAnalyzer
from domain.entities.game import Game
from domain.entities.dll_info import DLLInfo
from domain.enums.dll_type import DLLType
from domain.enums.platform import Platform


class GameScanner(LoggerMixin):
    """Varredura completa de jogos Steam com análise de DLLs"""
    
    def __init__(
        self,
        steam_service: Optional[SteamService] = None,
        dll_analyzer: Optional[DLLAnalyzer] = None
    ):
        """
        Inicializa o scanner
        
        Args:
            steam_service: SteamService customizado (ou cria novo)
            dll_analyzer: DLLAnalyzer customizado (ou cria novo)
        """
        self.steam_service = steam_service or SteamService()
        self.dll_analyzer = dll_analyzer or DLLAnalyzer(max_depth=3)
    
    def scan_steam_games(self) -> List[Game]:
        """
        Varre todos os jogos Steam instalados
        
        Returns:
            Lista de objetos Game com DLLs detectadas
        """
        self.logger.info("=" * 60)
        self.logger.info("Iniciando varredura de jogos Steam")
        self.logger.info("=" * 60)
        
        # Detectar Steam
        steam_path = self.steam_service.detect_steam_path()
        if not steam_path:
            self.logger.error("Steam não detectado no sistema")
            return []
        
        self.logger.info(f"Steam detectado em: {steam_path}")
        
        # Listar jogos instalados
        installed_games = self.steam_service.get_installed_games()
        total_games = len(installed_games)
        
        if total_games == 0:
            self.logger.warning("Nenhum jogo Steam instalado encontrado")
            return []
        
        self.logger.info(f"Encontrados {total_games} jogos instalados")
        self.logger.info("-" * 60)
        
        # Analisar cada jogo
        games = []
        for idx, game_info in enumerate(installed_games, 1):
            self.logger.info(f"[{idx}/{total_games}] {game_info['name']}")

            if self._is_proton_or_runtime(game_info.get('name', '')):
                self.logger.info(f"  → Ignorado (Proton/runtime)")
                continue

            game = self._process_game(game_info)
            if game:
                games.append(game)
        
        self.logger.info("=" * 60)
        self.logger.info(f"Varredura concluída: {len(games)} jogos processados")
        self.logger.info("=" * 60)
        
        return games
    
    def scan_single_game(self, appid: int) -> Optional[Game]:
        """
        Varre um jogo específico pelo AppID
        
        Args:
            appid: Steam AppID
        
        Returns:
            Game objeto ou None se não encontrado
        """
        self.logger.info(f"Buscando jogo com AppID: {appid}")
        
        # Listar todos os jogos e filtrar
        installed_games = self.steam_service.get_installed_games()
        
        for game_info in installed_games:
            if game_info['appid'] == appid:
                return self._process_game(game_info)
        
        self.logger.warning(f"Jogo com AppID {appid} não encontrado")
        return None
    
    def rescan_game(self, game: Game) -> Game:
        """
        Re-analisa DLLs de um jogo existente
        
        Args:
            game: Game objeto para re-analisar
        
        Returns:
            Game atualizado
        """
        self.logger.info(f"Re-analisando jogo: {game.name}")
        
        # Analisar DLLs novamente
        detected_dlls = self.dll_analyzer.analyze_game(game.path)
        
        # Atualizar DLLs detectadas
        game.supported_dlls = detected_dlls
        
        self.logger.info(
            f"Re-análise concluída: "
            f"DLSS={game.has_dlss}, "
            f"FSR={game.has_fsr}, "
            f"XeSS={game.has_xess}"
        )
        
        return game
    
    _PROTON_PREFIXES = (
        "proton ",
        "proton experimental",
        "steam linux runtime",
        "steam play",
        "pressure vessel",
    )

    def _is_proton_or_runtime(self, name: str) -> bool:
        """Retorna True se o nome indica uma ferramenta Proton/runtime no Linux."""
        if _platform.system() != "Linux":
            return False
        lower = name.lower().strip()
        return any(lower.startswith(p) for p in self._PROTON_PREFIXES)

    def _process_game(self, game_info: Dict) -> Optional[Game]:
        """
        Processa informações de um jogo e cria objeto Game
        
        Args:
            game_info: Dict com metadados Steam
        
        Returns:
            Game objeto ou None em caso de erro
        """
        try:
            install_path = Path(game_info['install_path'])
            
            # Verificar se pasta existe
            if not install_path.exists():
                self.logger.warning(f"  ⚠ Pasta não encontrada: {install_path}")
                return None
            
            # Analisar DLLs — tenta pela raiz do jogo; se nada for encontrado,
            # tenta novamente a partir da subpasta de executável (estrutura UE4/UE5)
            detected_dlls = self.dll_analyzer.analyze_game(install_path)
            if not detected_dlls:
                ue_dir = self._find_ue_binaries_dir(install_path)
                if ue_dir:
                    self.logger.info(f"  Rescaneando a partir de {ue_dir.name} (UE4/UE5)")
                    detected_dlls = self.dll_analyzer.analyze_game(ue_dir)
            
            # Determinar suporte às tecnologias
            supports_dlss = DLLType.DLSS.value in detected_dlls
            supports_fsr = DLLType.FSR.value in detected_dlls
            supports_xess = DLLType.XESS.value in detected_dlls
            
            # Criar objeto Game com atributos corretos
            game = Game(
                name=game_info['name'],
                path=install_path,
                executable=game_info.get('executable_path'),
                platform=Platform.STEAM,
                appid=game_info['appid'],
                last_scanned=datetime.now()
            )
            
            # Adicionar DLLs detectadas ao dicionário supported_dlls
            # analyze_game() retorna Dict[str, DLLInfo], não Dict[str, List[DLLInfo]]
            for dll_type, dll_info in detected_dlls.items():
                game.supported_dlls[dll_type] = dll_info
            
            # Log resumo
            techs = []
            if supports_dlss:
                techs.append("DLSS")
            if supports_fsr:
                techs.append("FSR")
            if supports_xess:
                techs.append("XeSS")
            
            if techs:
                self.logger.info(f"  ✓ Suporte: {', '.join(techs)}")
            else:
                self.logger.info(f"  - Nenhuma tecnologia de upscaling detectada")
            
            return game
        
        except Exception as e:
            self.logger.error(f"  ✗ Erro ao processar jogo: {e}")
            return None
    
    def _find_ue_binaries_dir(self, game_path: Path) -> Optional[Path]:
        """
        Detecta a pasta Binaries/Win64 em jogos com estrutura Unreal Engine.
        Busca até 2 níveis de profundidade: <raiz>/Binaries/Win64 ou
        <raiz>/<Sub>/Binaries/Win64.
        Retorna None se não encontrado.
        """
        candidates: list[Path] = [game_path / "Binaries" / "Win64"]
        try:
            for sub in game_path.iterdir():
                if sub.is_dir():
                    candidates.append(sub / "Binaries" / "Win64")
        except PermissionError:
            pass
        for candidate in candidates:
            try:
                if candidate.exists() and candidate.is_dir():
                    return candidate
            except PermissionError:
                continue
        return None

    def get_scan_statistics(self, games: List[Game]) -> Dict:
        """
        Gera estatísticas da varredura
        
        Args:
            games: Lista de jogos escaneados
        
        Returns:
            Dict com estatísticas
        """
        stats = {
            'total_games': len(games),
            'with_dlss': sum(1 for g in games if g.has_dlss),
            'with_fsr': sum(1 for g in games if g.has_fsr),
            'with_xess': sum(1 for g in games if g.has_xess),
            'with_any_tech': sum(
                1 for g in games 
                if g.has_dlss or g.has_fsr or g.has_xess
            ),
            'without_tech': sum(
                1 for g in games 
                if not (g.has_dlss or g.has_fsr or g.has_xess)
            )
        }
        
        return stats
    
    def print_scan_report(self, games: List[Game]):
        """
        Imprime relatório formatado da varredura
        
        Args:
            games: Lista de jogos escaneados
        """
        stats = self.get_scan_statistics(games)
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info("RELATÓRIO DE VARREDURA")
        self.logger.info("=" * 60)
        self.logger.info(f"Total de jogos: {stats['total_games']}")
        self.logger.info(f"Com DLSS:       {stats['with_dlss']}")
        self.logger.info(f"Com FSR:        {stats['with_fsr']}")
        self.logger.info(f"Com XeSS:       {stats['with_xess']}")
        self.logger.info(f"Com alguma tecnologia: {stats['with_any_tech']}")
        self.logger.info(f"Sem tecnologia:        {stats['without_tech']}")
        self.logger.info("=" * 60 + "\n")
