"""
Use Case: Desinstalar OptiScaler de um jogo
"""
import shutil
import json
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
    Restaura arquivos originais do backup e remove arquivos do OptiScaler
    """

    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    def execute(self, game_id: int) -> bool:
        """
        Desinstala OptiScaler de um jogo.

        Args:
            game_id: ID do jogo

        Returns:
            True se sucesso, False caso contrário
        """
        try:
            with self.db_service.get_connection() as conn:
                game_repo = GameRepository(conn)
                install_repo = InstallationRepository(conn)

                game = game_repo.find_by_id(game_id)
                if not game:
                    self.logger.error(f"Jogo {game_id} não encontrado")
                    return False

                installation = install_repo.find_active_by_game(game_id)
                if not installation:
                    self.logger.warning(f"Jogo {game.name} não possui OptiScaler instalado")
                    return False

                backup_path: Optional[Path] = installation.backup_path
                game_dir: Path = game.path

                self.logger.info("=" * 60)
                self.logger.info(f"Desinstalando OptiScaler de: {game.name}")
                self.logger.info("=" * 60)

                # 1. Ler manifesto dos arquivos instalados
                installed_files, loader_dll = self._read_manifest(backup_path)
                self.logger.info(f"[1/3] {len(installed_files)} arquivo(s) para remover")

                # 2. Remover arquivos do OptiScaler do jogo
                self.logger.info("[2/3] Removendo arquivos do OptiScaler...")
                self._remove_installed_files(game_dir, installed_files)

                # 3. Restaurar arquivos originais do backup
                self.logger.info("[3/3] Restaurando arquivos originais...")
                restored = self._restore_backup(backup_path, game_dir)
                self.logger.info(f"✓ {restored} arquivo(s) restaurado(s)")

                # 4. Marcar instalação como removida
                installation.status = 'removed'
                install_repo.save(installation)

                self.logger.info("=" * 60)
                self.logger.info("✓ DESINSTALAÇÃO CONCLUÍDA COM SUCESSO")
                self.logger.info("=" * 60)
                return True

        except Exception as e:
            self.logger.error(f"Erro durante desinstalação: {e}", exc_info=True)
            return False

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _read_manifest(self, backup_path: Optional[Path]):
        """Lê o manifesto salvo pela instalação. Retorna (lista_de_arquivos, loader_dll)."""
        if not backup_path:
            return [], None

        manifest_file = backup_path / "optiscaler_manifest.json"
        if not manifest_file.exists():
            self.logger.warning("Manifesto não encontrado — remoção pode ser incompleta")
            return [], None

        try:
            data = json.loads(manifest_file.read_text(encoding='utf-8'))
            return data.get("installed_files", []), data.get("loader_dll")
        except Exception as e:
            self.logger.error(f"Erro ao ler manifesto: {e}")
            return [], None

    def _remove_installed_files(self, game_dir: Path, installed_files: list):
        """Remove os arquivos instalados pelo OptiScaler do diretório do jogo."""
        for fname in installed_files:
            target = game_dir / fname
            if target.exists():
                target.unlink()
                self.logger.debug(f"  Removido: {fname}")

    def _restore_backup(self, backup_path: Optional[Path], game_dir: Path) -> int:
        """Copia todos os arquivos do diretório de backup para o jogo. Retorna contagem."""
        if not backup_path or not backup_path.exists():
            return 0

        restored = 0
        for src in backup_path.iterdir():
            # Ignorar o manifesto
            if src.name == "optiscaler_manifest.json":
                continue
            if src.is_file():
                dest = game_dir / src.name
                shutil.copy2(src, dest)
                self.logger.info(f"  Restaurado: {src.name}")
                restored += 1
        return restored

