"""
Testes para DLLAnalyzer
"""
import pytest
from pathlib import Path
from application.services.dll_analyzer import DLLAnalyzer
from domain.enums.dll_type import DLLType


class TestDLLAnalyzer:
    """Testes do analisador de DLLs"""
    
    def test_analyze_game_with_dlss(self, temp_dir):
        """Testa detecção de DLSS"""
        game_dir = temp_dir / "game"
        game_dir.mkdir()
        
        # Criar DLL DLSS fake com tamanho suficiente (>1MB)
        dll = game_dir / "nvngx_dlss.dll"
        dll.write_bytes(b"fake dlss content" * 100000)  # ~1.7MB
        
        analyzer = DLLAnalyzer(max_depth=2)
        result = analyzer.analyze_game(game_dir)
        
        assert DLLType.DLSS.value in result
        
        dll_info = result[DLLType.DLSS.value]
        assert dll_info.path == dll
        assert dll_info.size > 0
        assert dll_info.hash is not None
    
    def test_analyze_game_with_fsr(self, temp_dir):
        """Testa detecção de FSR"""
        game_dir = temp_dir / "game"
        game_dir.mkdir()
        
        # Criar DLL FSR fake com tamanho suficiente (>100KB)
        dll = game_dir / "amd_fidelityfx_vk.dll"
        dll.write_bytes(b"fake fsr content" * 10000)  # ~170KB
        
        analyzer = DLLAnalyzer(max_depth=2)
        result = analyzer.analyze_game(game_dir)
        
        assert DLLType.FSR.value in result
        assert result[DLLType.FSR.value] is not None
    
    def test_analyze_game_with_xess(self, temp_dir):
        """Testa detecção de XeSS"""
        game_dir = temp_dir / "game"
        game_dir.mkdir()
        
        # Criar DLL XeSS fake com tamanho suficiente (>1MB)
        dll = game_dir / "libxess.dll"
        dll.write_bytes(b"fake xess content" * 100000)  # ~1.8MB
        
        analyzer = DLLAnalyzer(max_depth=2)
        result = analyzer.analyze_game(game_dir)
        
        assert DLLType.XESS.value in result
        assert result[DLLType.XESS.value] is not None
    
    def test_analyze_game_no_dlls(self, temp_dir):
        """Testa jogo sem DLLs upscaling"""
        game_dir = temp_dir / "game"
        game_dir.mkdir()
        
        # Criar DLL genérica
        dll = game_dir / "random.dll"
        dll.write_bytes(b"not an upscaling dll")
        
        analyzer = DLLAnalyzer(max_depth=2)
        result = analyzer.analyze_game(game_dir)
        
        assert len(result) == 0
    
    def test_analyze_game_nested_dlls(self, temp_dir):
        """Testa detecção de DLLs em subpastas"""
        game_dir = temp_dir / "game"
        bin_dir = game_dir / "bin" / "x64"
        bin_dir.mkdir(parents=True)
        
        # Criar DLL em subpasta com tamanho suficiente
        dll = bin_dir / "nvngx_dlss.dll"
        dll.write_bytes(b"fake dlss in subfolder" * 100000)  # ~2.3MB
        
        analyzer = DLLAnalyzer(max_depth=3)
        result = analyzer.analyze_game(game_dir)
        
        assert DLLType.DLSS.value in result
        assert result[DLLType.DLSS.value] is not None
    
    def test_analyze_game_max_depth(self, temp_dir):
        """Testa limite de profundidade"""
        game_dir = temp_dir / "game"
        deep_dir = game_dir / "a" / "b" / "c" / "d"
        deep_dir.mkdir(parents=True)
        
        # DLL muito profunda com tamanho suficiente
        dll = deep_dir / "nvngx_dlss.dll"
        dll.write_bytes(b"too deep" * 200000)  # ~1.5MB
        
        # Com max_depth=2, não deve encontrar
        analyzer = DLLAnalyzer(max_depth=2)
        result = analyzer.analyze_game(game_dir)
        
        assert len(result) == 0
    
    def test_analyze_multiple_dlls_same_type(self, temp_dir):
        """Testa múltiplas DLLs do mesmo tipo - apenas a primeira é detectada"""
        game_dir = temp_dir / "game"
        game_dir.mkdir()
        
        # Criar múltiplas DLLs DLSS com tamanho suficiente
        dll1 = game_dir / "nvngx_dlss.dll"
        dll1.write_bytes(b"dlss 1" * 200000)  # ~1.2MB
        
        bin_dir = game_dir / "bin"
        bin_dir.mkdir()
        dll2 = bin_dir / "nvngx_dlss.dll"
        dll2.write_bytes(b"dlss 2" * 200000)  # ~1.2MB
        
        analyzer = DLLAnalyzer(max_depth=2)
        result = analyzer.analyze_game(game_dir)
        
        assert DLLType.DLSS.value in result
        # API retorna apenas uma DLL por tipo (a primeira encontrada)
        assert result[DLLType.DLSS.value].path in [dll1, dll2]
    
    def test_dll_hash_calculation(self, temp_dir):
        """Testa cálculo de hash SHA256"""
        game_dir = temp_dir / "game"
        game_dir.mkdir()
        
        dll = game_dir / "nvngx_dlss.dll"
        dll.write_bytes(b"test content for hash" * 100000)  # ~2MB
        
        analyzer = DLLAnalyzer(max_depth=2)
        result = analyzer.analyze_game(game_dir)
        
        dll_info = result[DLLType.DLSS.value]
        
        # Hash deve ser string hexadecimal de 64 caracteres
        assert isinstance(dll_info.hash, str)
        assert len(dll_info.hash) == 64
        assert all(c in "0123456789abcdef" for c in dll_info.hash)
