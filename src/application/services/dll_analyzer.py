"""
Analisador de DLLs de upscaling em jogos
Detecta DLSS, FSR, XeSS e outras DLLs relevantes
"""
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
import fnmatch

from utils.logger import LoggerMixin
from domain.entities.dll_info import DLLInfo
from domain.enums.dll_type import DLLType, APIType


class DLLAnalyzer(LoggerMixin):
    """Analisa pasta de jogo em busca de DLLs de upscaling"""
    
    # Padrões de DLLs para cada tipo
    DLL_PATTERNS = {
        DLLType.DLSS: [
            'nvngx_dlss.dll',
            'nvngx.dll',
            '_nvngx.dll',
            'nvngx_dlss*.dll'
        ],
        DLLType.FSR: [
            'amd_fidelityfx*.dll',
            'ffx_fsr*.dll',
            'amd_ags*.dll'
        ],
        DLLType.XESS: [
            'libxess.dll',
            'libxess*.dll'
        ]
    }
    
    # Tamanhos mínimos esperados (em bytes) para validação
    MIN_SIZES = {
        DLLType.DLSS: 1024 * 1024,  # 1 MB
        DLLType.FSR: 100 * 1024,     # 100 KB
        DLLType.XESS: 1024 * 1024    # 1 MB
    }
    
    def __init__(self, max_depth: int = 3):
        """
        Inicializa o analisador
        
        Args:
            max_depth: Profundidade máxima de busca em subpastas
        """
        self.max_depth = max_depth
    
    def analyze_game(self, game_path: Path) -> Dict[str, DLLInfo]:
        """
        Analisa pasta do jogo em busca de DLLs de upscaling
        
        Args:
            game_path: Caminho para a pasta do jogo
        
        Returns:
            Dict {dll_type: DLLInfo} com DLLs encontradas
        """
        if not game_path.exists() or not game_path.is_dir():
            self.logger.warning(f"Caminho inválido: {game_path}")
            return {}
        
        self.logger.info(f"Analisando DLLs em: {game_path.name}")
        
        # Procurar DLLs
        dll_files = self._find_dll_files(game_path)
        self.logger.debug(f"Encontradas {len(dll_files)} DLL(s)")
        
        # Categorizar DLLs
        detected_dlls = {}
        
        for dll_file in dll_files:
            dll_type = self._identify_dll_type(dll_file)
            
            if dll_type != DLLType.UNKNOWN:
                # Verificar tamanho mínimo
                if dll_file.stat().st_size < self.MIN_SIZES.get(dll_type, 0):
                    self.logger.debug(f"DLL muito pequena, ignorando: {dll_file.name}")
                    continue
                
                # Criar DLLInfo
                dll_info = self._create_dll_info(dll_file, dll_type)
                
                # Adicionar apenas se ainda não detectada
                if dll_type.value not in detected_dlls:
                    detected_dlls[dll_type.value] = dll_info
                    self.logger.info(f"✓ Detectado: {dll_type.display_name} ({dll_file.name})")
        
        return detected_dlls
    
    def _find_dll_files(self, root_path: Path, current_depth: int = 0) -> List[Path]:
        """
        Encontra todos os arquivos .dll recursivamente até max_depth
        
        Args:
            root_path: Pasta raiz
            current_depth: Profundidade atual
        
        Returns:
            Lista de Paths para DLLs
        """
        dll_files = []
        
        if current_depth > self.max_depth:
            return dll_files
        
        try:
            for item in root_path.iterdir():
                if item.is_file() and item.suffix.lower() == '.dll':
                    dll_files.append(item)
                elif item.is_dir() and current_depth < self.max_depth:
                    # Ignorar pastas comuns que não contêm DLLs de jogo
                    skip_dirs = ['__pycache__', '.git', 'localization', 'lang']
                    if item.name.lower() not in skip_dirs:
                        dll_files.extend(self._find_dll_files(item, current_depth + 1))
        
        except PermissionError:
            self.logger.warning(f"Sem permissão para acessar: {root_path}")
        
        return dll_files
    
    def _identify_dll_type(self, dll_path: Path) -> DLLType:
        """
        Identifica o tipo de DLL baseado no nome
        
        Args:
            dll_path: Caminho para a DLL
        
        Returns:
            DLLType identificado
        """
        dll_name = dll_path.name.lower()
        
        for dll_type, patterns in self.DLL_PATTERNS.items():
            for pattern in patterns:
                if fnmatch.fnmatch(dll_name, pattern.lower()):
                    return dll_type
        
        return DLLType.UNKNOWN
    
    def _create_dll_info(self, dll_path: Path, dll_type: DLLType) -> DLLInfo:
        """
        Cria objeto DLLInfo com informações da DLL
        
        Args:
            dll_path: Caminho para a DLL
            dll_type: Tipo da DLL
        
        Returns:
            DLLInfo com metadados
        """
        # Calcular hash SHA256
        dll_hash = self._calculate_hash(dll_path)
        
        # Obter tamanho
        size = dll_path.stat().st_size
        
        # Tentar detectar versão (futuro)
        version = self._extract_version(dll_path)
        
        # Tentar detectar API gráfica pelo nome
        api_type = self._detect_api_type(dll_path.name)
        
        return DLLInfo(
            dll_type=dll_type,
            path=dll_path,
            size=size,
            hash=dll_hash,
            version=version,
            api_type=api_type
        )
    
    def _calculate_hash(self, file_path: Path) -> str:
        """
        Calcula hash SHA256 de um arquivo
        
        Args:
            file_path: Caminho do arquivo
        
        Returns:
            Hash SHA256 em hexadecimal
        """
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                # Ler em chunks para arquivos grandes
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            return sha256_hash.hexdigest()
        
        except Exception as e:
            self.logger.error(f"Erro ao calcular hash de {file_path}: {e}")
            return ""
    
    def _extract_version(self, dll_path: Path) -> Optional[str]:
        """
        Tenta extrair versão da DLL
        
        Args:
            dll_path: Caminho para a DLL
        
        Returns:
            String com versão ou None
        """
        # Implementação futura: usar win32api no Windows
        # Por enquanto, retornar None
        return None
    
    def _detect_api_type(self, dll_name: str) -> APIType:
        """
        Tenta detectar API gráfica pelo nome da DLL
        
        Args:
            dll_name: Nome da DLL
        
        Returns:
            APIType detectado
        """
        dll_name_lower = dll_name.lower()
        
        if 'dx12' in dll_name_lower or 'd3d12' in dll_name_lower:
            return APIType.DX12
        elif 'dx11' in dll_name_lower or 'd3d11' in dll_name_lower:
            return APIType.DX11
        elif 'vk' in dll_name_lower or 'vulkan' in dll_name_lower:
            return APIType.VULKAN
        elif 'opengl' in dll_name_lower or 'gl' in dll_name_lower:
            return APIType.OPENGL
        
        return APIType.UNKNOWN
    
    def verify_dll_integrity(self, dll_info: DLLInfo) -> bool:
        """
        Verifica se DLL ainda existe e hash está correto
        
        Args:
            dll_info: DLLInfo para verificar
        
        Returns:
            True se íntegra, False caso contrário
        """
        if not dll_info.path.exists():
            self.logger.warning(f"DLL não encontrada: {dll_info.path}")
            return False
        
        current_hash = self._calculate_hash(dll_info.path)
        
        if current_hash != dll_info.hash:
            self.logger.warning(
                f"Hash da DLL mudou: {dll_info.path.name}\n"
                f"  Esperado: {dll_info.hash}\n"
                f"  Atual: {current_hash}"
            )
            return False
        
        return True
