"""
Serviço para interagir com GitHub API
Download de releases do OptiScaler
"""
import requests
from pathlib import Path
from typing import List, Optional, Dict, Callable
from datetime import datetime
import shutil

from utils.logger import LoggerMixin
from domain.entities.optiscaler_version import OptiScalerVersion


class GitHubService(LoggerMixin):
    """Gerencia downloads de releases do GitHub"""
    
    REPO_OWNER = "optiscaler"
    REPO_NAME = "OptiScaler"
    API_BASE = "https://api.github.com"
    
    def __init__(self, cache_dir: Path):
        """
        Inicializa o serviço
        
        Args:
            cache_dir: Diretório para cache de downloads
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Headers para API do GitHub
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'OptiScaler-Center'
        }
    
    def fetch_releases(self, include_prerelease: bool = True) -> List[OptiScalerVersion]:
        """
        Busca lista de releases do OptiScaler
        
        Args:
            include_prerelease: Se deve incluir pré-releases
        
        Returns:
            Lista de OptiScalerVersion objetos
        """
        self.logger.info("Buscando releases do OptiScaler no GitHub...")
        
        url = f"{self.API_BASE}/repos/{self.REPO_OWNER}/{self.REPO_NAME}/releases"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            releases_data = response.json()
            releases = []
            
            for release in releases_data:
                # Filtrar pré-releases se necessário
                if not include_prerelease and release['prerelease']:
                    continue
                
                version = self._parse_release(release)
                if version:
                    releases.append(version)
            
            self.logger.info(f"✓ Encontradas {len(releases)} releases")
            return releases
        
        except requests.RequestException as e:
            self.logger.error(f"Erro ao buscar releases: {e}")
            return []
    
    def fetch_latest_release(self, include_prerelease: bool = False) -> Optional[OptiScalerVersion]:
        """
        Busca última release do OptiScaler
        
        Args:
            include_prerelease: Se deve considerar pré-releases
        
        Returns:
            OptiScalerVersion ou None
        """
        self.logger.info("Buscando última release do OptiScaler...")
        
        if include_prerelease:
            # Buscar todas e pegar a primeira
            releases = self.fetch_releases(include_prerelease=True)
            return releases[0] if releases else None
        
        else:
            # Endpoint específico para última release estável
            url = f"{self.API_BASE}/repos/{self.REPO_OWNER}/{self.REPO_NAME}/releases/latest"
            
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                
                release_data = response.json()
                version = self._parse_release(release_data)
                
                if version:
                    self.logger.info(f"✓ Última release: {version.tag_name}")
                
                return version
            
            except requests.RequestException as e:
                self.logger.error(f"Erro ao buscar última release: {e}")
                return None
    
    def download_release(
        self,
        version: OptiScalerVersion,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Optional[Path]:
        """
        Faz download de uma release
        
        Args:
            version: OptiScalerVersion para baixar
            progress_callback: Callback para progresso (bytes_downloaded, total_bytes)
        
        Returns:
            Path do arquivo baixado ou None em caso de erro
        """
        if not version.download_url:
            self.logger.error(f"URL de download não disponível para {version.tag_name}")
            return None
        
        # Nome do arquivo
        filename = version.download_url.split('/')[-1]
        output_path = self.cache_dir / filename
        
        # Verificar se já existe
        if output_path.exists():
            self.logger.info(f"Arquivo já existe: {output_path.name}")
            return output_path
        
        self.logger.info(f"Baixando {version.tag_name}...")
        self.logger.info(f"  URL: {version.download_url}")
        
        try:
            # Fazer download com stream
            response = requests.get(
                version.download_url,
                headers=self.headers,
                stream=True,
                timeout=30
            )
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            # Arquivo temporário
            temp_path = output_path.with_suffix('.tmp')
            
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Callback de progresso
                        if progress_callback:
                            progress_callback(downloaded, total_size)
            
            # Renomear temporário para final
            temp_path.rename(output_path)
            
            self.logger.info(f"✓ Download concluído: {output_path.name}")
            return output_path
        
        except requests.RequestException as e:
            self.logger.error(f"Erro ao baixar release: {e}")
            
            # Limpar arquivo temporário
            temp_path = output_path.with_suffix('.tmp')
            if temp_path.exists():
                temp_path.unlink()
            
            return None
    
    def delete_cached_file(self, file_path: Path) -> bool:
        """
        Remove arquivo do cache
        
        Args:
            file_path: Path do arquivo
        
        Returns:
            True se removido, False caso contrário
        """
        try:
            if file_path.exists():
                file_path.unlink()
                self.logger.info(f"Cache removido: {file_path.name}")
                return True
            
            return False
        
        except Exception as e:
            self.logger.error(f"Erro ao remover cache: {e}")
            return False
    
    def get_cache_size(self) -> int:
        """
        Calcula tamanho total do cache
        
        Returns:
            Tamanho em bytes
        """
        total_size = 0
        
        for file in self.cache_dir.iterdir():
            if file.is_file():
                total_size += file.stat().st_size
        
        return total_size
    
    def clear_cache(self):
        """Remove todo o cache de downloads"""
        try:
            for file in self.cache_dir.iterdir():
                if file.is_file():
                    file.unlink()
            
            self.logger.info("Cache limpo")
        
        except Exception as e:
            self.logger.error(f"Erro ao limpar cache: {e}")
    
    def _parse_release(self, release_data: Dict) -> Optional[OptiScalerVersion]:
        """
        Parseia dados de release do GitHub para OptiScalerVersion
        
        Args:
            release_data: Dict com dados da API
        
        Returns:
            OptiScalerVersion ou None
        """
        try:
            # Encontrar asset principal (zip ou 7z)
            assets = release_data.get('assets', [])
            main_asset = None
            
            for asset in assets:
                name = asset['name'].lower()
                if (name.endswith('.zip') or name.endswith('.7z')) and 'optiscaler' in name:
                    main_asset = asset
                    break
            
            # Se não encontrou específico, pegar primeiro zip ou 7z
            if not main_asset and assets:
                for asset in assets:
                    name = asset['name'].lower()
                    if name.endswith('.zip') or name.endswith('.7z'):
                        main_asset = asset
                        break
            
            if not main_asset:
                self.logger.warning(f"Release sem asset válido: {release_data['tag_name']}")
                return None
            
            # Parsear data de publicação
            published_at = datetime.strptime(
                release_data['published_at'],
                '%Y-%m-%dT%H:%M:%SZ'
            )
            
            # Verificar se já está baixado
            filename = main_asset['name']
            cache_path = self.cache_dir / filename
            is_downloaded = cache_path.exists()
            
            return OptiScalerVersion(
                tag_name=release_data['tag_name'],
                name=release_data['name'] or release_data['tag_name'],
                description=release_data['body'] or "",
                release_date=published_at,
                is_prerelease=release_data['prerelease'],
                download_url=main_asset['browser_download_url'],
                total_size=main_asset['size'],
                cache_path=cache_path if is_downloaded else None,
                is_downloaded=is_downloaded
            )
        
        except Exception as e:
            self.logger.error(f"Erro ao parsear release: {e}")
            return None
    
    def verify_download_integrity(self, version: OptiScalerVersion) -> bool:
        """
        Verifica integridade do arquivo baixado
        
        Args:
            version: OptiScalerVersion para verificar
        
        Returns:
            True se íntegro, False caso contrário
        """
        if not version.local_path or not version.local_path.exists():
            return False
        
        # Verificar tamanho
        actual_size = version.local_path.stat().st_size
        
        if actual_size != version.file_size:
            self.logger.warning(
                f"Tamanho incorreto: esperado {version.file_size}, "
                f"atual {actual_size}"
            )
            return False
        
        return True
