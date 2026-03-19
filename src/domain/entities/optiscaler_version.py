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
    release_date: Optional[datetime] = None
    download_date: Optional[datetime] = None
    cache_path: Optional[Path] = None
    changelog: str = ""
    file_count: int = 0
    total_size: int = 0
    download_url: str = ""
    
    # Metadados do GitHub release
    is_prerelease: bool = False
    github_id: Optional[int] = None
    
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
