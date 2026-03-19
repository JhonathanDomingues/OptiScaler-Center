"""
Entidade Backup - Registro de backup de DLLs
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime


@dataclass
class BackupFile:
    """Informações sobre um arquivo no backup"""
    original_path: Path
    backup_name: str
    size: int
    sha256: str
    dll_type: str


@dataclass
class Backup:
    """Registro de backup de DLLs de um jogo"""
    id: Optional[int] = None
    game_id: int = 0
    backup_path: Path = field(default_factory=Path)
    backup_date: datetime = field(default_factory=datetime.now)
    file_count: int = 0
    total_size: int = 0
    notes: str = ""
    files: List[BackupFile] = field(default_factory=list)
    
    @property
    def can_restore(self) -> bool:
        """Verifica se o backup pode ser restaurado"""
        return self.backup_path.exists() and self.file_count > 0
    
    @property
    def size_mb(self) -> float:
        """Tamanho em MB"""
        return self.total_size / (1024 * 1024)
    
    @property
    def timestamp(self) -> str:
        """Timestamp formatado"""
        return self.backup_date.strftime('%Y%m%d_%H%M%S')
    
    def __str__(self):
        return f"Backup(game_id={self.game_id}, date={self.backup_date.date()}, files={self.file_count})"
    
    def __repr__(self):
        return self.__str__()
