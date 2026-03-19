"""
Serviço de integração com Steam
Detecta instalação do Steam e lista jogos instalados
"""
import platform
from pathlib import Path
from typing import List, Optional, Dict
import os

try:
    import winreg  # Windows only
except ImportError:
    winreg = None

from utils.logger import LoggerMixin
from utils.constants import (
    STEAM_PATHS_WINDOWS, 
    STEAM_PATHS_LINUX,
    STEAM_LIBRARY_FILE,
    STEAM_MANIFEST_PATTERN
)
from infrastructure.steam.vdf_parser import VDFParser


class SteamService(LoggerMixin):
    """Serviço para integração com Steam"""
    
    def __init__(self):
        self.vdf_parser = VDFParser()
        self._steam_path: Optional[Path] = None
        self._library_folders: List[Path] = []
    
    def detect_steam_path(self) -> Optional[Path]:
        """
        Detecta o caminho de instalação do Steam
        
        Returns:
            Path para o Steam ou None se não encontrado
        """
        if self._steam_path and self._steam_path.exists():
            return self._steam_path
        
        system = platform.system()
        self.logger.info(f"Detectando Steam no {system}...")
        
        if system == "Windows":
            paths = STEAM_PATHS_WINDOWS
            # Tentar registro do Windows
            steam_path = self._get_steam_path_from_registry()
            if steam_path:
                self._steam_path = steam_path
                return steam_path
        elif system == "Linux":
            paths = STEAM_PATHS_LINUX
        else:
            self.logger.warning(f"Sistema operacional não suportado: {system}")
            return None
        
        # Tentar paths padrão
        for path_str in paths:
            path = Path(path_str).expanduser()
            if path.exists() and path.is_dir():
                self.logger.info(f"Steam encontrado em: {path}")
                self._steam_path = path
                return path
        
        self.logger.warning("Steam não encontrado nos caminhos padrão")
        return None
    
    def _get_steam_path_from_registry(self) -> Optional[Path]:
        """
        Obtém caminho do Steam do registro do Windows
        
        Returns:
            Path ou None
        """
        if winreg is None:
            return None
        
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Wow6432Node\Valve\Steam"
            )
            install_path, _ = winreg.QueryValueEx(key, "InstallPath")
            winreg.CloseKey(key)
            
            path = Path(install_path)
            if path.exists():
                self.logger.debug(f"Steam path do registro: {path}")
                return path
        except (ImportError, OSError, FileNotFoundError):
            pass
        
        return None
    
    def get_library_folders(self) -> List[Path]:
        """
        Obtém lista de todas as bibliotecas Steam
        
        Returns:
            Lista de Paths para bibliotecas
        """
        if self._library_folders:
            return self._library_folders
        
        steam_path = self.detect_steam_path()
        if not steam_path:
            self.logger.warning("Steam não detectado, não é possível listar bibliotecas")
            return []
        
        # Caminho para libraryfolders.vdf
        library_file = steam_path / "steamapps" / STEAM_LIBRARY_FILE
        
        if not library_file.exists():
            self.logger.warning(f"Arquivo {STEAM_LIBRARY_FILE} não encontrado em {library_file}")
            # Adicionar pelo menos a biblioteca principal
            main_lib = steam_path / "steamapps"
            if main_lib.exists():
                self._library_folders = [main_lib.parent]
                return self._library_folders
            return []
        
        try:
            # Parsear libraryfolders.vdf
            libraries_dict = self.vdf_parser.parse_library_folders(library_file)
            self._library_folders = list(libraries_dict.values())
            
            self.logger.info(f"Encontradas {len(self._library_folders)} biblioteca(s) Steam")
            for lib in self._library_folders:
                self.logger.debug(f"  - {lib}")
            
            return self._library_folders
            
        except Exception as e:
            self.logger.error(f"Erro ao parsear bibliotecas Steam: {e}")
            return []
    
    def get_installed_games(self) -> List[Dict]:
        """
        Lista todos os jogos instalados em todas as bibliotecas Steam
        
        Returns:
            Lista de dicionários com informações dos jogos
        """
        libraries = self.get_library_folders()
        if not libraries:
            self.logger.warning("Nenhuma biblioteca Steam encontrada")
            return []
        
        all_games = []
        
        for library_path in libraries:
            steamapps_path = library_path / "steamapps"
            
            if not steamapps_path.exists():
                self.logger.warning(f"Pasta steamapps não encontrada em {library_path}")
                continue
            
            # Procurar por arquivos appmanifest_*.acf
            manifest_files = list(steamapps_path.glob("appmanifest_*.acf"))
            self.logger.debug(f"Encontrados {len(manifest_files)} manifests em {steamapps_path}")
            
            for manifest_file in manifest_files:
                try:
                    game_info = self.vdf_parser.parse_app_manifest(manifest_file)
                    
                    # Adicionar caminho completo do jogo
                    install_dir = game_info.get('installdir')
                    if install_dir:
                        game_path = steamapps_path / "common" / install_dir
                        game_info['install_path'] = game_path  # CORRIGIDO: era game_path
                        game_info['library_path'] = library_path
                        
                        # Verificar se pasta existe
                        if game_path.exists():
                            all_games.append(game_info)
                        else:
                            self.logger.warning(
                                f"Pasta do jogo não encontrada: {game_path} "
                                f"({game_info.get('name')})"
                            )
                    else:
                        self.logger.warning(
                            f"Jogo sem installdir: {game_info.get('name', 'Unknown')}"
                        )
                    
                except Exception as e:
                    self.logger.error(f"Erro ao processar {manifest_file.name}: {e}")
                    continue
        
        self.logger.info(f"Total de {len(all_games)} jogo(s) Steam detectado(s)")
        return all_games
    
    def find_game_executable(self, game_path: Path) -> Optional[Path]:
        """
        Tenta encontrar o executável principal de um jogo
        
        Args:
            game_path: Caminho para a pasta do jogo
        
        Returns:
            Path para o executável ou None
        """
        if not game_path.exists():
            return None
        
        # Procurar por .exe (Windows) ou binários (Linux)
        system = platform.system()
        
        if system == "Windows":
            exe_files = list(game_path.glob("*.exe"))
            # Filtrar executáveis comuns de launcher/uninstaller
            exe_files = [
                exe for exe in exe_files 
                if not any(skip in exe.name.lower() for skip in ['unins', 'crash', 'launcher'])
            ]
            
            if exe_files:
                # Heurística: maior arquivo ou nome similar à pasta
                game_name = game_path.name.lower().replace(' ', '')
                
                # Tentar encontrar por nome similar
                for exe in exe_files:
                    exe_name = exe.stem.lower().replace(' ', '')
                    if game_name in exe_name or exe_name in game_name:
                        return exe
                
                # Caso contrário, retornar o maior
                largest = max(exe_files, key=lambda p: p.stat().st_size)
                return largest
        
        elif system == "Linux":
            # Procurar por arquivos executáveis
            for file in game_path.iterdir():
                if file.is_file() and os.access(file, os.X_OK):
                    # Evitar scripts comuns
                    if file.suffix not in ['.sh', '.py']:
                        return file
        
        return None
