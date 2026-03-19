"""
Use Case: Buscar versões do OptiScaler no GitHub
"""
from typing import List, Optional

from utils.logger import LoggerMixin
from infrastructure.github.github_service import GitHubService
from domain.repositories.version_repository import VersionRepository
from domain.entities.optiscaler_version import OptiScalerVersion
from infrastructure.database.db_service import DatabaseService


class FetchVersionsUseCase(LoggerMixin):
    """
    Caso de uso: Buscar versões do OptiScaler
    Consulta GitHub API e salva no banco
    """
    
    def __init__(
        self,
        github_service: GitHubService,
        db_service: DatabaseService
    ):
        """
        Inicializa o use case
        
        Args:
            github_service: GitHubService para API
            db_service: DatabaseService para banco
        """
        self.github_service = github_service
        self.db_service = db_service
    
    def execute(self, include_prerelease: bool = True) -> List[OptiScalerVersion]:
        """
        Busca todas as versões do GitHub e salva no banco
        
        Args:
            include_prerelease: Se deve incluir pré-releases
        
        Returns:
            Lista de versões
        """
        self.logger.info("Buscando versões do OptiScaler...")
        
        # Buscar do GitHub
        versions = self.github_service.fetch_releases(include_prerelease)
        
        if not versions:
            self.logger.warning("Nenhuma versão encontrada no GitHub")
            return []
        
        # Salvar no banco
        with self.db_service.get_connection() as conn:
            version_repo = VersionRepository(conn)
            
            for version in versions:
                try:
                    version_repo.save(version)
                except Exception as e:
                    self.logger.error(f"Erro ao salvar versão {version.tag_name}: {e}")
        
        self.logger.info(f"✓ {len(versions)} versões salvas")
        return versions
    
    def get_latest_version(self, include_prerelease: bool = False) -> Optional[OptiScalerVersion]:
        """
        Busca última versão disponível
        
        Args:
            include_prerelease: Se deve considerar pré-releases
        
        Returns:
            OptiScalerVersion ou None
        """
        # Buscar do GitHub
        version = self.github_service.fetch_latest_release(include_prerelease)
        
        if not version:
            return None
        
        # Salvar no banco
        with self.db_service.get_connection() as conn:
            version_repo = VersionRepository(conn)
            version_repo.save(version)
        
        return version
    
    def get_all_versions_from_db(self, include_prerelease: bool = True) -> List[OptiScalerVersion]:
        """
        Busca versões salvas no banco
        
        Args:
            include_prerelease: Se deve incluir pré-releases
        
        Returns:
            Lista de versões
        """
        with self.db_service.get_connection() as conn:
            version_repo = VersionRepository(conn)
            return version_repo.find_all(include_prerelease)
    
    def get_downloaded_versions(self) -> List[OptiScalerVersion]:
        """
        Busca versões já baixadas
        
        Returns:
            Lista de versões
        """
        with self.db_service.get_connection() as conn:
            version_repo = VersionRepository(conn)
            return version_repo.find_downloaded()
