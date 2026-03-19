"""
Entidade DLLInfo - Informações sobre uma DLL detectada
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from domain.enums.dll_type import DLLType, APIType


@dataclass
class DLLInfo:
    """Informações sobre uma DLL de upscaling"""
    dll_type: DLLType
    path: Path
    size: int
    hash: str
    version: Optional[str] = None
    api_type: APIType = APIType.UNKNOWN
    
    @property
    def filename(self) -> str:
        """Nome do arquivo"""
        return self.path.name
    
    @property
    def display_name(self) -> str:
        """Nome para exibição"""
        return self.dll_type.display_name
    
    def __str__(self):
        return f"DLLInfo({self.dll_type}, {self.filename})"
    
    def __repr__(self):
        return self.__str__()
