"""
Use Case: Instalar OptiScaler em um jogo
"""
import shutil
import zipfile
from pathlib import Path
from typing import Optional
from datetime import datetime

from utils.logger import LoggerMixin
from domain.repositories.game_repository import GameRepository
from domain.repositories.version_repository import VersionRepository
from domain.repositories.installation_repository import InstallationRepository
from domain.repositories.backup_repository import BackupRepository
from domain.entities.installation import Installation
from domain.entities.backup import Backup
from domain.enums.dll_type import DLLType
from infrastructure.database.db_service import DatabaseService


class InstallOptiScalerUseCase(LoggerMixin):
    """
    Caso de uso: Instalação do OptiScaler
    Faz backup, extrai arquivos e instala DLLs
    """
    
    def __init__(
        self,
        db_service: DatabaseService,
        backup_root: Path
    ):
        """
        Inicializa o use case
        
        Args:
            db_service: DatabaseService para banco
            backup_root: Diretório raiz para backups
        """
        self.db_service = db_service
        self.backup_root = backup_root
        self.backup_root.mkdir(parents=True, exist_ok=True)
    
    def execute(
        self,
        game_id: int,
        version_id: int,
        target_dll_type: DLLType
    ) -> bool:
        """
        Instala OptiScaler em um jogo
        
        Args:
            game_id: ID do jogo
            version_id: ID da versão do OptiScaler
            target_dll_type: Tipo de DLL a substituir (DLSS/FSR/XeSS)
        
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            with self.db_service.get_connection() as conn:
                game_repo = GameRepository(conn)
                version_repo = VersionRepository(conn)
                install_repo = InstallationRepository(conn)
                backup_repo = BackupRepository(conn)
                
                # Buscar jogo
                game = game_repo.find_by_id(game_id)
                if not game:
                    self.logger.error(f"Jogo {game_id} não encontrado")
                    return False
                
                # Buscar versão
                version = version_repo.find_by_id(version_id)
                if not version:
                    self.logger.error(f"Versão {version_id} não encontrada")
                    return False
                
                if not version.is_downloaded or not version.local_path:
                    self.logger.error(f"Versão {version.tag_name} não está baixada")
                    return False
                
                # Verificar se já tem instalação ativa
                existing_install = install_repo.find_active_by_game(game_id)
                if existing_install:
                    self.logger.warning(f"Jogo {game.name} já possui OptiScaler instalado")
                    return False
                
                # Verificar se jogo suporta o tipo de DLL alvo
                if target_dll_type.value not in game.supported_dlls:
                    self.logger.error(
                        f"Jogo {game.name} não possui DLL {target_dll_type.display_name}"
                    )
                    return False
                
                self.logger.info("=" * 60)
                self.logger.info(f"Instalando OptiScaler {version.tag_name}")
                self.logger.info(f"Jogo: {game.name}")
                self.logger.info(f"DLL alvo: {target_dll_type.display_name}")
                self.logger.info("=" * 60)
                
                # 1. Criar backup
                self.logger.info("[1/4] Criando backup...")
                backup = self._create_backup(game, target_dll_type)
                if not backup:
                    self.logger.error("Falha ao criar backup")
                    return False
                
                backup_repo.save(backup)
                self.logger.info(f"✓ Backup criado: {backup.backup_path.name}")
                
                # 2. Extrair OptiScaler
                self.logger.info("[2/4] Extraindo OptiScaler...")
                extracted_files = self._extract_optiscaler(version.local_path, game.path)
                if not extracted_files:
                    self.logger.error("Falha ao extrair OptiScaler")
                    self._restore_backup(backup)
                    return False
                
                self.logger.info(f"✓ {len(extracted_files)} arquivos extraídos")
                
                # 3. Copiar DLLs
                self.logger.info("[3/4] Instalando DLLs...")
                dll_installed = self._install_dlls(game, target_dll_type, extracted_files)
                if not dll_installed:
                    self.logger.error("Falha ao instalar DLLs")
                    self._restore_backup(backup)
                    self._cleanup_extracted_files(extracted_files)
                    return False
                
                self.logger.info("✓ DLLs instaladas")
                
                # 4. Registrar instalação
                self.logger.info("[4/4] Registrando instalação...")
                installation = Installation(
                    game_id=game_id,
                    version_id=version_id,
                    dll_type=target_dll_type,
                    backup_id=backup.id,
                    status='installed',
                    installed_at=datetime.now()
                )
                
                install_repo.save(installation)
                
                self.logger.info("=" * 60)
                self.logger.info("✓ INSTALAÇÃO CONCLUÍDA COM SUCESSO")
                self.logger.info("=" * 60)
                
                return True
        
        except Exception as e:
            self.logger.error(f"Erro durante instalação: {e}")
            return False
    
    def _create_backup(self, game, target_dll_type: DLLType) -> Optional[Backup]:
        """Cria backup das DLLs originais"""
        try:
            dll_info = game.supported_dlls[target_dll_type.value]
            
            # Criar pasta de backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{game.appid}_{target_dll_type.value}_{timestamp}"
            backup_path = self.backup_root / backup_name
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Copiar DLL original
            dll_backup = backup_path / dll_info.path.name
            shutil.copy2(dll_info.path, dll_backup)
            
            files = [dll_backup]
            total_size = dll_backup.stat().st_size
            
            return Backup(
                game_id=game.id,
                backup_path=backup_path,
                files=files,
                total_size=total_size,
                status='active',
                created_at=datetime.now()
            )
        
        except Exception as e:
            self.logger.error(f"Erro ao criar backup: {e}")
            return None
    
    def _extract_optiscaler(self, zip_path: Path, target_dir: Path) -> Optional[list]:
        """Extrai arquivos do OptiScaler"""
        try:
            extracted = []
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Listar arquivos
                file_list = zip_ref.namelist()
                
                # Extrair apenas DLLs e arquivos essenciais
                for file_name in file_list:
                    if file_name.lower().endswith(('.dll', '.ini', '.json')):
                        zip_ref.extract(file_name, target_dir)
                        extracted.append(target_dir / file_name)
            
            return extracted
        
        except Exception as e:
            self.logger.error(f"Erro ao extrair: {e}")
            return None
    
    def _install_dlls(self, game, target_dll_type: DLLType, extracted_files: list) -> bool:
        """Instala DLLs do OptiScaler"""
        try:
            dll_info = game.supported_dlls[target_dll_type.value]
            target_dll_path = dll_info.path
            
            # Encontrar DLL principal do OptiScaler nos arquivos extraídos
            optiscaler_dll = None
            
            for file_path in extracted_files:
                # OptiScaler se apresenta como nvngx_dlss.dll geralmente
                if file_path.name.lower() == 'nvngx_dlss.dll':
                    optiscaler_dll = file_path
                    break
            
            if not optiscaler_dll:
                self.logger.error("DLL principal do OptiScaler não encontrada")
                return False
            
            # Copiar DLL do OptiScaler sobre a original
            shutil.copy2(optiscaler_dll, target_dll_path)
            
            return True
        
        except Exception as e:
            self.logger.error(f"Erro ao instalar DLLs: {e}")
            return False
    
    def _restore_backup(self, backup: Backup):
        """Restaura backup em caso de erro"""
        try:
            for backup_file in backup.files:
                # Implementar restauração
                pass
        except Exception as e:
            self.logger.error(f"Erro ao restaurar backup: {e}")
    
    def _cleanup_extracted_files(self, files: list):
        """Remove arquivos extraídos"""
        try:
            for file_path in files:
                if file_path.exists():
                    file_path.unlink()
        except Exception as e:
            self.logger.error(f"Erro ao limpar arquivos: {e}")
