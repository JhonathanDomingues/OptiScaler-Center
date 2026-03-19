"""
Use Case: Instalar OptiScaler em um jogo
"""
import shutil
import tempfile
from pathlib import Path
from typing import Optional
from datetime import datetime

try:
    import py7zr
    HAS_PY7ZR = True
except ImportError:
    HAS_PY7ZR = False

from utils.logger import LoggerMixin
from utils.constants import FSR4_SDK_DIR
from domain.repositories.game_repository import GameRepository
from domain.repositories.version_repository import VersionRepository
from domain.repositories.installation_repository import InstallationRepository
from domain.repositories.backup_repository import BackupRepository
from domain.entities.installation import Installation
from domain.entities.backup import Backup
from infrastructure.database.db_service import DatabaseService

# Nomes de DLL suportados pelo OptiScaler como loader
SUPPORTED_LOADER_DLLS = [
    "dxgi.dll",
    "winmm.dll",
    "d3d12.dll",
    "dbghelp.dll",
    "version.dll",
    "wininet.dll",
    "winhttp.dll",
]

# Variantes do FSR4 SDK
FSR4_VARIANTS = {
    "standard": FSR4_SDK_DIR / "standard",
    "int8": FSR4_SDK_DIR / "int8",
}


class InstallOptiScalerUseCase(LoggerMixin):
    """
    Caso de uso: Instalação do OptiScaler
    Extrai todos os arquivos do .7z para a pasta do jogo e renomeia OptiScaler.dll
    para o nome loader escolhido. Opcionalmente copia o FSR4 SDK.
    """

    def __init__(
        self,
        db_service: DatabaseService,
        backup_root: Path
    ):
        self.db_service = db_service
        self.backup_root = backup_root
        self.backup_root.mkdir(parents=True, exist_ok=True)

    def execute(
        self,
        game_id: int,
        version_id: int,
        loader_dll: str = "dxgi.dll",
        fsr4_variant: Optional[str] = None
    ) -> bool:
        """
        Instala OptiScaler em um jogo.

        Args:
            game_id: ID do jogo
            version_id: ID da versão do OptiScaler
            loader_dll: Nome do DLL loader (ex: dxgi.dll, winmm.dll)
            fsr4_variant: Variante FSR4 SDK a copiar: "standard", "int8" ou None

        Returns:
            True se sucesso, False caso contrário
        """
        if not HAS_PY7ZR:
            self.logger.error(
                "py7zr não está instalado. Execute: pip install py7zr"
            )
            return False

        try:
            with self.db_service.get_connection() as conn:
                game_repo = GameRepository(conn)
                version_repo = VersionRepository(conn)
                install_repo = InstallationRepository(conn)
                backup_repo = BackupRepository(conn)

                game = game_repo.find_by_id(game_id)
                if not game:
                    self.logger.error(f"Jogo {game_id} não encontrado")
                    return False

                version = version_repo.find_by_id(version_id)
                if not version:
                    self.logger.error(f"Versão {version_id} não encontrada")
                    return False

                if not version.is_downloaded or not version.local_path:
                    self.logger.error(f"Versão {version.tag_name} não está baixada")
                    return False

                existing = install_repo.find_active_by_game(game_id)
                if existing:
                    self.logger.warning(f"Jogo {game.name} já possui OptiScaler instalado")
                    return False

                self.logger.info("=" * 60)
                self.logger.info(f"Instalando OptiScaler {version.tag_name}")
                self.logger.info(f"Jogo: {game.name}")
                self.logger.info(f"Loader: {loader_dll}")
                if fsr4_variant:
                    self.logger.info(f"FSR4 SDK: {fsr4_variant}")
                self.logger.info("=" * 60)

                game_dir = game.path

                # 1. Extrair para pasta temporária
                self.logger.info("[1/4] Extraindo OptiScaler...")
                with tempfile.TemporaryDirectory() as tmp_str:
                    tmp_dir = Path(tmp_str)
                    self._extract_7z(version.local_path, tmp_dir)

                    # Arquivos que serão copiados para o jogo
                    files_to_copy = self._collect_files(tmp_dir)
                    if not files_to_copy:
                        self.logger.error("Nenhum arquivo encontrado no arquivo")
                        return False
                    self.logger.info(f"✓ {len(files_to_copy)} arquivos extraídos")

                    # 2. Backup de arquivos existentes
                    self.logger.info("[2/4] Criando backup...")
                    backup = self._create_backup(game, files_to_copy, loader_dll)
                    backup_repo.save(backup)
                    self.logger.info(f"✓ Backup criado em: {backup.backup_path.name}")

                    # 3. Copiar arquivos para o jogo
                    self.logger.info("[3/4] Copiando arquivos...")
                    try:
                        self._copy_files_to_game(tmp_dir, files_to_copy, game_dir, loader_dll)
                    except Exception as copy_err:
                        self.logger.error(f"Erro ao copiar arquivos: {copy_err}")
                        self._restore_backup(backup, game_dir)
                        return False

                    # Copiar FSR4 SDK se solicitado
                    if fsr4_variant:
                        self._copy_fsr4_sdk(game_dir, fsr4_variant)

                    self.logger.info("✓ Arquivos instalados")

                # 4. Registrar instalação
                self.logger.info("[4/4] Registrando instalação...")
                installation = Installation(
                    game_id=game_id,
                    version=version.tag_name,
                    backup_path=backup.backup_path,
                    status='active',
                    install_date=datetime.now()
                )
                install_repo.save(installation)

                self.logger.info("=" * 60)
                self.logger.info("✓ INSTALAÇÃO CONCLUÍDA COM SUCESSO")
                self.logger.info("=" * 60)
                return True

        except Exception as e:
            self.logger.error(f"Erro durante instalação: {e}", exc_info=True)
            return False

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _extract_7z(self, archive_path: Path, dest_dir: Path):
        """Extrai o arquivo .7z para dest_dir."""
        with py7zr.SevenZipFile(archive_path, mode='r') as z:
            z.extractall(path=dest_dir)

    def _collect_files(self, tmp_dir: Path) -> list:
        """Coleta arquivos relevantes do diretório extraído (DLL, INI, JSON)."""
        relevant_exts = {'.dll', '.ini', '.json', '.asi'}
        files = []
        for f in tmp_dir.rglob('*'):
            if f.is_file() and f.suffix.lower() in relevant_exts:
                files.append(f)
        return files

    def _create_backup(self, game, files_to_copy: list, loader_dll: str) -> Backup:
        """
        Faz backup dos arquivos que serão sobreescritos no diretório do jogo
        e do arquivo loader se já existir.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        game_id_str = str(game.appid or game.id)
        backup_dir = self.backup_root / f"{game_id_str}_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        total_size = 0
        file_count = 0
        game_dir = game.path

        # Backup dos arquivos que existirem no jogo e serão substituídos
        filenames_to_copy = {f.name.lower() for f in files_to_copy}
        # Adicionar o loader dll ao conjunto de arquivos a verificar
        filenames_to_copy.add(loader_dll.lower())

        for fname_lower in filenames_to_copy:
            candidate = game_dir / fname_lower
            # Tentar com capitalização exata e também lowercase
            for p in [candidate, *game_dir.glob(fname_lower)]:
                if p.is_file():
                    dest = backup_dir / p.name
                    shutil.copy2(p, dest)
                    total_size += p.stat().st_size
                    file_count += 1
                    break

        return Backup(
            game_id=game.id,
            backup_path=backup_dir,
            backup_date=datetime.now(),
            file_count=file_count,
            total_size=total_size,
            notes=f"Backup antes de instalar OptiScaler. Loader: {loader_dll}"
        )

    def _copy_files_to_game(
        self,
        tmp_dir: Path,
        files_to_copy: list,
        game_dir: Path,
        loader_dll: str
    ):
        """
        Copia os arquivos extraídos para o diretório do jogo.
        Renomeia 'OptiScaler.dll' para o nome loader escolhido.
        """
        for src in files_to_copy:
            dest_name = src.name
            if src.name.lower() == 'optiscaler.dll':
                dest_name = loader_dll
            dest = game_dir / dest_name
            shutil.copy2(src, dest)
            self.logger.debug(f"  Copiado: {dest_name}")

    def _copy_fsr4_sdk(self, game_dir: Path, variant: str):
        """Copia os arquivos do FSR4 SDK para o diretório do jogo."""
        sdk_dir = FSR4_VARIANTS.get(variant)
        if not sdk_dir or not sdk_dir.exists():
            self.logger.warning(f"FSR4 SDK '{variant}' não encontrado em {sdk_dir}")
            return
        count = 0
        for dll in sdk_dir.glob('*.dll'):
            shutil.copy2(dll, game_dir / dll.name)
            self.logger.debug(f"  FSR4 SDK: {dll.name}")
            count += 1
        self.logger.info(f"✓ {count} arquivo(s) FSR4 SDK ({variant}) copiado(s)")

    def _restore_backup(self, backup: Backup, game_dir: Path):
        """Restaura arquivos do backup em caso de erro."""
        try:
            if not backup.backup_path.exists():
                return
            for f in backup.backup_path.iterdir():
                dest = game_dir / f.name
                shutil.copy2(f, dest)
                self.logger.info(f"  Restaurado: {f.name}")
            self.logger.info("Backup restaurado após falha")
        except Exception as e:
            self.logger.error(f"Erro ao restaurar backup: {e}")
        except Exception as e:
            self.logger.error(f"Erro ao limpar arquivos: {e}")
