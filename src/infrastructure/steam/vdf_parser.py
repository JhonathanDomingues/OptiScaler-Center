"""
Parser VDF (Valve Data Format) para arquivos da Steam
"""
import re
from pathlib import Path
from typing import Dict, Any, Union
import vdf

from utils.logger import LoggerMixin


class VDFParser(LoggerMixin):
    """Parser para arquivos VDF da Steam"""
    
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse arquivo VDF
        
        Args:
            file_path: Caminho para o arquivo .vdf ou .acf
        
        Returns:
            Dicionário com dados parseados
        
        Raises:
            FileNotFoundError: Se arquivo não existe
            ValueError: Se arquivo não pode ser parseado
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Usar biblioteca vdf
            data = vdf.loads(content)
            self.logger.debug(f"VDF parseado com sucesso: {file_path.name}")
            return data
            
        except Exception as e:
            self.logger.error(f"Erro ao parsear VDF {file_path}: {e}")
            raise ValueError(f"Não foi possível parsear arquivo VDF: {e}")
    
    def parse_library_folders(self, file_path: Path) -> Dict[str, Path]:
        """
        Parse libraryfolders.vdf e retorna dicionário de bibliotecas
        
        Args:
            file_path: Caminho para libraryfolders.vdf
        
        Returns:
            Dict com {index: Path} das bibliotecas
        """
        data = self.parse_file(file_path)
        libraries = {}
        
        # Estrutura: {"libraryfolders": {"0": {"path": "..."}, "1": {...}}}
        library_data = data.get('libraryfolders', {})
        
        for key, value in library_data.items():
            if key.isdigit() and isinstance(value, dict):
                path_str = value.get('path')
                if path_str:
                    libraries[key] = Path(path_str)
                    self.logger.debug(f"Biblioteca {key}: {path_str}")
        
        return libraries
    
    def parse_app_manifest(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse appmanifest_*.acf e retorna informações do jogo
        
        Args:
            file_path: Caminho para appmanifest_*.acf
        
        Returns:
            Dict com informações do jogo
        """
        data = self.parse_file(file_path)
        
        # Estrutura: {"AppState": {"appid": "...", "name": "...", ...}}
        app_state = data.get('AppState', {})
        
        game_info = {
            'appid': app_state.get('appid'),
            'name': app_state.get('name'),
            'installdir': app_state.get('installdir'),
            'last_updated': app_state.get('LastUpdated'),
            'size_on_disk': app_state.get('SizeOnDisk'),
            'buildid': app_state.get('buildid'),
            'state_flags': app_state.get('StateFlags')
        }
        
        self.logger.debug(f"App parseado: {game_info.get('name')} (AppID: {game_info.get('appid')})")
        
        return game_info
