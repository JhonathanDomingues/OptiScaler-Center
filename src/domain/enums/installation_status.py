"""
Enums para status de instalação do OptiScaler
"""
from enum import Enum


class InstallationStatus(str, Enum):
    """Status de instalação do OptiScaler em um jogo"""
    NOT_INSTALLED = "not_installed"
    INSTALLED = "installed"
    UPDATE_AVAILABLE = "update_available"
    ERROR = "error"
    UNKNOWN = "unknown"
    
    def __str__(self):
        return self.value
    
    @property
    def display_name(self) -> str:
        """Nome para exibição"""
        names = {
            self.NOT_INSTALLED: "Não Instalado",
            self.INSTALLED: "Instalado",
            self.UPDATE_AVAILABLE: "Atualização Disponível",
            self.ERROR: "Erro",
            self.UNKNOWN: "Desconhecido"
        }
        return names.get(self, self.value)
    
    @property
    def color(self) -> str:
        """Cor associada ao status"""
        colors = {
            self.NOT_INSTALLED: "#808080",
            self.INSTALLED: "#4caf50",
            self.UPDATE_AVAILABLE: "#ff9800",
            self.ERROR: "#f44336",
            self.UNKNOWN: "#9e9e9e"
        }
        return colors.get(self, "#808080")


class OperationStatus(str, Enum):
    """Status de operações (install, uninstall, etc)"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    
    def __str__(self):
        return self.value
