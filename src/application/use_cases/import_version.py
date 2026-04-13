"""
Use Case: Importar arquivo compactado do OptiScaler de fonte local
Registra o arquivo como uma versão disponível para instalação.
"""
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from utils.logger import LoggerMixin
from utils.constants import CACHE_DIR
from domain.entities.optiscaler_version import OptiScalerVersion
from domain.repositories.version_repository import VersionRepository
from infrastructure.database.db_service import DatabaseService


# Extensões de arquivo aceitas na importação
SUPPORTED_EXTENSIONS = {'.7z', '.zip'}


class ImportVersionUseCase(LoggerMixin):
    """
    Caso de uso: Importar versão local do OptiScaler.

    Copia o arquivo para o cache e registra no banco com tag_name
    prefixado por "local-" para distinguir de versões do GitHub.
    Ao importar o mesmo nome de arquivo novamente, a entrada existente
    é atualizada (substituição no cache).
    """

    def __init__(self, db_service: DatabaseService, cache_dir: Path = CACHE_DIR):
        self.db_service = db_service
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def execute(self, source_path: Path) -> Optional[OptiScalerVersion]:
        """
        Importa um arquivo compactado como versão do OptiScaler.

        Args:
            source_path: Caminho para o arquivo .7z ou .zip a importar.

        Returns:
            OptiScalerVersion registrada, ou None em caso de erro.

        Raises:
            FileNotFoundError: Se o arquivo não existir.
            ValueError: Se a extensão não for suportada.
        """
        source_path = Path(source_path)

        if not source_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {source_path}")

        suffix = source_path.suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Formato não suportado: '{suffix}'. "
                f"Use {' ou '.join(SUPPORTED_EXTENSIONS)}."
            )

        stem = source_path.stem
        tag_name = f"local-{stem}"
        dest = self.cache_dir / source_path.name

        self.logger.info(f"Importando versão local: {source_path.name}")

        # Copiar para o cache (só se origem ≠ destino)
        if source_path.resolve() != dest.resolve():
            self.logger.info(f"  Copiando para cache: {dest}")
            shutil.copy2(source_path, dest)
        else:
            self.logger.info("  Arquivo já está no cache, apenas registrando.")

        file_size = dest.stat().st_size

        version = OptiScalerVersion(
            tag_name=tag_name,
            name=f"[Local] {stem}",
            description=f"Importado localmente em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            release_date=datetime.now(),
            is_prerelease=False,
            download_url="",
            total_size=file_size,
            cache_path=dest,
            is_downloaded=True,
        )

        with self.db_service.get_connection() as conn:
            repo = VersionRepository(conn)
            repo.save(version)

        self.logger.info(
            f"✓ Versão '{tag_name}' registrada "
            f"({file_size / (1024 * 1024):.1f} MB)"
        )
        return version

    def is_local_version(self, version: OptiScalerVersion) -> bool:
        """Retorna True se a versão foi importada localmente."""
        return version.tag_name.startswith("local-")
