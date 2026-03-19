"""
Entidade Installation - Registro de instalação do OptiScaler
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from datetime import datetime


@dataclass
class Installation:
    """Registro de instalação do OptiScaler em um jogo"""
    id: Optional[int] = None
    game_id: int = 0
    version: str = ""
    install_date: datetime = None
    backup_path: Optional[Path] = None
    config_path: Optional[Path] = None
    status: str = "active"  # 'active', 'removed'
    
    def __post_init__(self):
        if self.install_date is None:
            self.install_date = datetime.now()
    
    @property
    def is_active(self) -> bool:
        """Verifica se a instalação está ativa"""
        return self.status == 'active'
    
    def __str__(self):
        return f"Installation(game_id={self.game_id}, version={self.version}, status={self.status})"
    
    def __repr__(self):
        return self.__str__()
