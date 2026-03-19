"""
Entidade OptiScalerVersion - Versão do OptiScaler
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime


@dataclass
class OptiScalerVersion:
    """Versão do OptiScaler disponível ou em cache"""
    id: Optional[int] = None
    version: str = ""
    tag_name: str = ""
    name: str = ""  # Nome da release no GitHub
    description: str = ""  # Descrição/changelog da release
    release_date: Optional[datetime] = None
    download_date: Optional[datetime] = None
    cache_path: Optional[Path] = None
    changelog: str = ""
    file_count: int = 0
    total_size: int = 0
    download_url: str = ""
    is_downloaded: bool = False  # Flag se está baixada
    
    # Metadados do GitHub release
    is_prerelease: bool = False
    github_id: Optional[int] = None
    
    @property
    def local_path(self) -> Optional[Path]:
        """Alias para cache_path (compatibilidade)"""
        return self.cache_path
    
    @local_path.setter
    def local_path(self, value: Optional[Path]):
        """Setter para loca_path (compatibilidade)"""
        self.cache_path = value
    
    @property
    def file_size(self) -> int:
        """Alias para total_size (compatibilidade)"""
        return self.total_size
    
    @file_size.setter
    def file_size(self, value: int):
        """Setter para file_size (compatibilidade)"""
        self.total_size = value
    
    @property
    def is_cached(self) -> bool:
        """Verifica se a versão está em cache"""
        return self.cache_path is not None and self.cache_path.exists()
    
    @property
    def display_name(self) -> str:
        """Nome para exibição"""
        return f"v{self.version}"
    
    @property
    def size_mb(self) -> float:
        """Tamanho em MB"""
        return self.total_size / (1024 * 1024)
    
    def __str__(self):
        cached = "cached" if self.is_cached else "not cached"
        return f"OptiScalerVersion({self.version}, {cached})"
    
    def __repr__(self):
        return self.__str__()
    
    def __lt__(self, other):
        """Comparação para ordenação por versão"""
        if not isinstance(other, OptiScalerVersion):
            return NotImplemented
        
        # Comparação simples por string de versão
        # Para comparação mais robusta, usar packaging.version
        return self.version < other.version
