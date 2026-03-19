"""
Testes para VDFParser
"""
import pytest
from pathlib import Path
from infrastructure.steam.vdf_parser import VDFParser


class TestVDFParser:
    """Testes do parser VDF"""
    
    def test_parse_simple_vdf(self, temp_dir):
        """Testa parse de VDF simples"""
        vdf_file = temp_dir / "test.vdf"
        vdf_file.write_text('''
"root"
{
    "key1"  "value1"
    "key2"  "value2"
}
''')
        
        parser = VDFParser()
        data = parser.parse_file(vdf_file)
        
        assert "root" in data
        assert data["root"]["key1"] == "value1"
        assert data["root"]["key2"] == "value2"
    
    def test_parse_nested_vdf(self, temp_dir):
        """Testa parse de VDF com estrutura aninhada"""
        vdf_file = temp_dir / "nested.vdf"
        vdf_file.write_text('''
"root"
{
    "section1"
    {
        "inner_key"  "inner_value"
    }
    "section2"
    {
        "another_key"  "another_value"
    }
}
''')
        
        parser = VDFParser()
        data = parser.parse_file(vdf_file)
        
        assert "root" in data
        assert "section1" in data["root"]
        assert data["root"]["section1"]["inner_key"] == "inner_value"
        assert data["root"]["section2"]["another_key"] == "another_value"
    
    def test_parse_library_folders(self, temp_dir):
        """Testa parse de libraryfolders.vdf"""
        vdf_file = temp_dir / "libraryfolders.vdf"
        vdf_file.write_text('''
"libraryfolders"
{
    "0"
    {
        "path"  "/home/user/.steam/steam"
        "label" ""
        "contentid" "123456"
    }
    "1"
    {
        "path"  "/mnt/games/SteamLibrary"
        "label" "Games"
        "contentid" "789012"
    }
}
''')
        
        parser = VDFParser()
        data = parser.parse_file(vdf_file)
        
        assert "libraryfolders" in data
        assert "0" in data["libraryfolders"]
        assert "1" in data["libraryfolders"]
        assert "/home/user/.steam/steam" in data["libraryfolders"]["0"]["path"]
    
    def test_parse_app_manifest(self, temp_dir):
        """Testa parse de appmanifest"""
        manifest = temp_dir / "appmanifest_480.acf"
        manifest.write_text('''
"AppState"
{
    "appid"  "480"
    "Universe"  "1"
    "name"  "Spacewar"
    "StateFlags"  "4"
    "installdir"  "Spacewar"
    "LastUpdated"  "1234567890"
    "SizeOnDisk"  "1024000"
    "buildid"  "999"
}
''')
        
        parser = VDFParser()
        data = parser.parse_file(manifest)
        
        assert "AppState" in data
        app_state = data["AppState"]
        assert app_state["appid"] == "480"
        assert app_state["name"] == "Spacewar"
        assert app_state["installdir"] == "Spacewar"
    
    def test_parse_file_not_found(self):
        """Testa parse de arquivo inexistente"""
        parser = VDFParser()
        
        # Deve lançar FileNotFoundError
        with pytest.raises(FileNotFoundError):
            parser.parse_file(Path("/fake/path/file.vdf"))
    
    def test_parse_malformed_vdf(self, temp_dir):
        """Testa parse de VDF malformado"""
        vdf_file = temp_dir / "bad.vdf"
        vdf_file.write_text('''
"root"
{
    "key1"  "value1
    missing_quote
}
''')
        
        parser = VDFParser()
        
        # Deve lançar ValueError
        with pytest.raises(ValueError):
            parser.parse_file(vdf_file)
