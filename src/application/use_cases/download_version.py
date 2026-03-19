"""
Use Case: Fazer download de versão do OptiScaler
"""
from pathlib import Path
from typing import Optional, Callable

from utils.logger import LoggerMixin
from infrastructure.github.github_service import GitHubService
from domain.repositories.version_repository import VersionRepository
from domain.entities.optiscaler_version import OptiScalerVersion
from infrastructure.database.db_service import DatabaseService


class DownloadVersionUseCase(LoggerMixin):
    """
    Caso de uso: Download de versão do OptiScaler
    Faz download do GitHub e atualiza banco
    """
    
    def __init__(
        self,
        github_service: GitHubService,
        db_service: DatabaseService
    ):
        """
        Inicializa o use case
        
        Args:
            github_service: GitHubService para download
            db_service: DatabaseService para banco
        """
        self.github_service = github_service
        self.db_service = db_service
    
    def execute(
        self,
        version_id: int,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Faz download de uma versão
        
        Args:
            version_id: ID da versão no banco
            progress_callback: Callback para progresso (bytes_downloaded, total_bytes)
        
        Returns:
            True se sucesso, False caso contrário
        """
        with self.db_service.get_connection() as conn:
            version_repo = VersionRepository(conn)
            
            # Buscar versão
            version = version_repo.find_by_id(version_id)
            
            if not version:
                self.logger.error(f"Versão {version_id} não encontrada")
                return False
            
            if version.is_downloaded:
                self.logger.info(f"Versão {version.tag_name} já está baixada")
                return True
            
            self.logger.info(f"Baixando {version.tag_name}...")
            
            # Fazer download
            downloaded_path = self.github_service.download_release(
                version,
                progress_callback
            )
            
            if not downloaded_path:
                self.logger.error(f"Falha ao baixar {version.tag_name}")
                return False
            
            # Verificar integridade
            if not self.github_service.verify_download_integrity(version):
                self.logger.error("Falha na verificação de integridade")
                downloaded_path.unlink()
                return False
            
            # Atualizar versão no banco
            version.local_path = downloaded_path
            version.is_downloaded = True
            version_repo.save(version)
            
            self.logger.info(f"✓ Download concluído: {version.tag_name}")
            return True
    
    def download_by_tag(
        self,
        tag_name: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Faz download de versão por tag
        
        Args:
            tag_name: Tag da versão (ex: v0.7.1)
            progress_callback: Callback para progresso
        
        Returns:
            True se sucesso, False caso contrário
        """
        with self.db_service.get_connection() as conn:
            version_repo = VersionRepository(conn)
            
            version = version_repo.find_by_tag(tag_name)
            
            if not version:
                self.logger.error(f"Versão {tag_name} não encontrada no banco")
                return False
            
            return self.execute(version.id, progress_callback)
    
    def delete_downloaded_version(self, version_id: int) -> bool:
        """
        Remove versão baixada
        
        Args:
            version_id: ID da versão
        
        Returns:
            True se removido, False caso contrário
        """
        with self.db_service.get_connection() as conn:
            version_repo = VersionRepository(conn)
            
            version = version_repo.find_by_id(version_id)
            
            if not version or not version.is_downloaded:
                return False
            
            # Deletar arquivo
            if version.local_path and version.local_path.exists():
                success = self.github_service.delete_cached_file(version.local_path)
                
                if success:
                    # Atualizar banco
                    version.local_path = None
                    version.is_downloaded = False
                    version_repo.save(version)
                
                return success
            
            return False
    
    def get_cache_size(self) -> int:
        """
        Retorna tamanho total do cache
        
        Returns:
            Tamanho em bytes
        """
        return self.github_service.get_cache_size()
    
    def clear_all_cache(self):
        """Remove todo o cache de downloads"""
        self.github_service.clear_cache()
        
        # Atualizar todas as versões no banco
        with self.db_service.get_connection() as conn:
            version_repo = VersionRepository(conn)
            versions = version_repo.find_downloaded()
            
            for version in versions:
                version.local_path = None
                version.is_downloaded = False
                version_repo.save(version)
        
        self.logger.info("Cache limpo e banco atualizado")
