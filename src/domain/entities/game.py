"""
Entidade Game - Representa um jogo gerenciado
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

from domain.enums.platform import Platform
from domain.enums.installation_status import InstallationStatus


@dataclass
class Game:
    """Entidade representando um jogo"""
    id: Optional[int] = None
    name: str = ""
    path: Path = field(default_factory=Path)
    executable: Optional[Path] = None
    platform: Platform = Platform.UNKNOWN
    appid: Optional[int] = None
    detected_date: datetime = field(default_factory=datetime.now)
    last_scanned: Optional[datetime] = None
    notes: str = ""
    
    # Relacionamentos (preenchidos separadamente)
    supported_dlls: Dict[str, 'DLLInfo'] = field(default_factory=dict)
    installation: Optional['Installation'] = None
    
    @property
    def installation_status(self) -> InstallationStatus:
        """Status da instalação do OptiScaler"""
        if not self.installation:
            return InstallationStatus.NOT_INSTALLED
        
        if self.installation.status == 'active':
            return InstallationStatus.INSTALLED
        
        return InstallationStatus.UNKNOWN
    
    @property
    def has_dlss(self) -> bool:
        """Verifica se o jogo suporta DLSS"""
        return 'DLSS' in self.supported_dlls
    
    @property
    def has_fsr(self) -> bool:
        """Verifica se o jogo suporta FSR"""
        return 'FSR' in self.supported_dlls
    
    @property
    def has_xess(self) -> bool:
        """Verifica se o jogo suporta XeSS"""
        return 'XeSS' in self.supported_dlls
    
    @property
    def supported_technologies(self) -> List[str]:
        """Lista de tecnologias suportadas"""
        return list(self.supported_dlls.keys())
    
    def __str__(self):
        return f"Game({self.name}, platform={self.platform})"
    
    def __repr__(self):
        return self.__str__()
