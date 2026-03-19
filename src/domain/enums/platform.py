"""
Enums para plataformas de jogos
"""
from enum import Enum
import platform as system_platform


class Platform(str, Enum):
    """Plataformas de distribuição de jogos"""
    STEAM = "steam"
    EPIC = "epic"
    GOG = "gog"
    ORIGIN = "origin"
    UBISOFT = "ubisoft"
    XBOX = "xbox"
    MANUAL = "manual"
    UNKNOWN = "unknown"
    
    def __str__(self):
        return self.value
    
    @property
    def display_name(self) -> str:
        """Nome para exibição"""
        names = {
            self.STEAM: "Steam",
            self.EPIC: "Epic Games Store",
            self.GOG: "GOG",
            self.ORIGIN: "EA App (Origin)",
            self.UBISOFT: "Ubisoft Connect",
            self.XBOX: "Xbox Game Pass",
            self.MANUAL: "Adicionado Manualmente",
            self.UNKNOWN: "Desconhecido"
        }
        return names.get(self, self.value)
    
    @property
    def color(self) -> str:
        """Cor associada à plataforma"""
        colors = {
            self.STEAM: "#1B2838",
            self.EPIC: "#0078F2",
            self.GOG: "#B9A6FF",
            self.ORIGIN: "#F56C2D",
            self.UBISOFT: "#0080FF",
            self.XBOX: "#107C10",
            self.MANUAL: "#808080",
            self.UNKNOWN: "#9e9e9e"
        }
        return colors.get(self, "#808080")


class OperatingSystem(str, Enum):
    """Sistemas operacionais suportados"""
    WINDOWS = "windows"
    LINUX = "linux"
    UNKNOWN = "unknown"
    
    def __str__(self):
        return self.value
    
    @classmethod
    def detect(cls) -> 'OperatingSystem':
        """Detecta o SO atual"""
        system = system_platform.system().lower()
        
        if 'windows' in system:
            return cls.WINDOWS
        elif 'linux' in system:
            return cls.LINUX
        else:
            return cls.UNKNOWN
