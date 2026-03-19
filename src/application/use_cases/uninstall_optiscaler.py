"""
Use Case: Desinstalar OptiScaler de um jogo
"""
import shutil
from pathlib import Path
from typing import Optional

from utils.logger import LoggerMixin
from domain.repositories.game_repository import GameRepository
from domain.repositories.installation_repository import InstallationRepository
from domain.repositories.backup_repository import BackupRepository
from infrastructure.database.db_service import DatabaseService


class UninstallOptiScalerUseCase(LoggerMixin):
    """
    Caso de uso: Desinstalação do OptiScaler
    Restaura DLLs originais do backup
    """
    
    def __init__(self, db_service: DatabaseService):
        """
        Inicializa o use case
        
        Args:
            db_service: DatabaseService para banco
        """
        self.db_service = db_service
    
    def execute(self, game_id: int) -> bool:
        """
        Desinstala OptiScaler de um jogo
        
        Args:
            game_id: ID do jogo
        
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            with self.db_service.get_connection() as conn:
                game_repo = GameRepository(conn)
                install_repo = InstallationRepository(conn)
                backup_repo = BackupRepository(conn)
                
                # Buscar jogo
                game = game_repo.find_by_id(game_id)
                if not game:
                    self.logger.error(f"Jogo {game_id} não encontrado")
                    return False
                
                # Buscar instalação ativa
                installation = install_repo.find_active_by_game(game_id)
                if not installation:
                    self.logger.warning(f"Jogo {game.name} não possui OptiScaler instalado")
                    return False
                
                # Buscar backup
                backup = backup_repo.find_by_id(installation.backup_id)
                if not backup:
                    self.logger.error(f"Backup não encontrado para instalação {installation.id}")
                    return False
                
                self.logger.info("=" * 60)
                self.logger.info(f"Desinstalando OptiScaler")
                self.logger.info(f"Jogo: {game.name}")
                self.logger.info("=" * 60)
                
                # 1. Restaurar backup
                self.logger.info("[1/3] Restaurando DLLs originais...")
                dll_info = game.supported_dlls[installation.dll_type.value]
                
                for backup_file in backup.files:
                    if backup_file.exists():
                        # Restaurar DLL original
                        shutil.copy2(backup_file, dll_info.path)
                        self.logger.info(f"✓ Restaurado: {dll_info.path.name}")
                
                # 2. Remover arquivos do OptiScaler
                self.logger.info("[2/3] Removendo arquivos do OptiScaler...")
                self._cleanup_optiscaler_files(game.path)
                
                # 3. Atualizar status
                self.logger.info("[3/3] Atualizando banco de dados...")
                installation.status = 'uninstalled'
                install_repo.save(installation)
                
                backup.status = 'restored'
                backup_repo.save(backup)
                
                self.logger.info("=" * 60)
                self.logger.info("✓ DESINSTALAÇÃO CONCLUÍDA COM SUCESSO")
                self.logger.info("=" * 60)
                
                return True
        
        except Exception as e:
            self.logger.error(f"Erro durante desinstalação: {e}")
            return False
    
    def _cleanup_optiscaler_files(self, game_dir: Path):
        """Remove arquivos do OptiScaler"""
        try:
            # Arquivos comuns do OptiScaler
            optiscaler_files = [
                'nvngx.ini',
                'EnableSignatureOverride.reg',
                'DisableSignatureOverride.reg'
            ]
            
            for filename in optiscaler_files:
                file_path = game_dir / filename
                if file_path.exists():
                    file_path.unlink()
                    self.logger.debug(f"Removido: {filename}")
        
        except Exception as e:
            self.logger.error(f"Erro ao limpar arquivos: {e}")
