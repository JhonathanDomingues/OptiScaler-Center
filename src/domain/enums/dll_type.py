"""
Enums para tipos de DLL detectadas em jogos
"""
from enum import Enum, auto


class DLLType(str, Enum):
    """Tipos de DLL de upscaling suportadas"""
    DLSS = "DLSS"
    FSR = "FSR"
    XESS = "XeSS"
    UNKNOWN = "UNKNOWN"
    
    def __str__(self):
        return self.value
    
    @property
    def display_name(self) -> str:
        """Nome para exibição"""
        names = {
            self.DLSS: "NVIDIA DLSS",
            self.FSR: "AMD FSR",
            self.XESS: "Intel XeSS",
            self.UNKNOWN: "Unknown"
        }
        return names.get(self, self.value)
    
    @property
    def color(self) -> str:
        """Cor associada ao tipo"""
        colors = {
            self.DLSS: "#76B900",  # NVIDIA Green
            self.FSR: "#ED1C24",   # AMD Red
            self.XESS: "#0071C5",  # Intel Blue
            self.UNKNOWN: "#808080"
        }
        return colors.get(self, "#808080")


class APIType(str, Enum):
    """APIs gráficas suportadas"""
    DX11 = "DX11"
    DX12 = "DX12"
    VULKAN = "Vulkan"
    OPENGL = "OpenGL"
    UNKNOWN = "UNKNOWN"
    
    def __str__(self):
        return self.value
