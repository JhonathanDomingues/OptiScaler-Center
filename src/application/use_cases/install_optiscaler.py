"""
Use Case: Instalar OptiScaler em um jogo
"""
import sys
import shutil
import subprocess
import platform as _platform
import tempfile
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime

try:
    import libarchive
    HAS_LIBARCHIVE = True
except ImportError:
    HAS_LIBARCHIVE = False

try:
    import py7zr
    HAS_PY7ZR = True
except ImportError:
    HAS_PY7ZR = False

from utils.logger import LoggerMixin
from utils.constants import FSR4_SDK_DIR, FSR4_USER_SDK_DIR
from application.services.setup_script_parser import parse_script, SetupQuestion
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

# Variantes do FSR4 SDK (somente-leitura, embutidas)
FSR4_VARIANTS = {
    "standard": FSR4_SDK_DIR / "standard",
    "int8":     FSR4_SDK_DIR / "int8",
}


def _pick_int8_dll(directory: Path) -> Optional[Path]:
    """
    Escolhe a DLL int8 correta dentro de um diretório de versão.
    Prioriza amd_fidelityfx_upscaler_dx12.dll (a única que o int8 substitui).
    """
    dlls = list(directory.glob("*.dll"))
    if not dlls:
        return None
    # Preferir a DLL de upscaler pelo nome
    for dll in dlls:
        if 'upscaler' in dll.name.lower():
            return dll
    return dlls[0]


def _scan_int8_dir(base_dir: Path, versions: dict, prefix: str = ""):
    """
    Varre um diretório por versões int8.
    Suporta:
      - subpastas versionadas: {version}/ contendo *.dll
      - DLLs diretas na raiz (fallback "bundled")
    Não sobrescreve versões já encontradas (prioridade de chamada).
    """
    if not base_dir.exists():
        return

    has_subdirs = False
    for d in sorted(base_dir.iterdir()):
        if d.is_dir():
            dll = _pick_int8_dll(d)
            if dll:
                has_subdirs = True
                key = f"{prefix}{d.name}" if prefix else d.name
                if key not in versions:
                    versions[key] = dll

    # Fallback: DLLs diretas na raiz (sem subpastas de versão)
    if not has_subdirs:
        dll = _pick_int8_dll(base_dir)
        if dll:
            key = f"{prefix}bundled" if prefix else "bundled"
            if key not in versions:
                versions[key] = dll


def get_int8_versions(custom_versions: dict = None) -> dict:
    """
    Retorna todas as versões int8 disponíveis.

    Busca em (em ordem de prioridade):
      1. resources/fsr4_sdk/int8/  (embutido — subpastas versionadas ou DLL direta)
      2. SDK DLL/DLL INT8/          (pasta de desenvolvimento, apenas modo não-frozen)
      3. ~/.local/share/optiscaler-center/fsr4_sdk/int8/  (adicionadas pelo usuário)
      4. Versões customizadas via config (caminhos diretos)

    Returns:
        {version_name: Path} — versões disponíveis
    """
    versions: dict = {}

    # 1. Embutido (resources/fsr4_sdk/int8/)
    _scan_int8_dir(FSR4_SDK_DIR / "int8", versions)

    # 2. Desenvolvimento: "SDK DLL/DLL INT8/" na raiz do projeto (não-frozen apenas)
    if not getattr(sys, 'frozen', False):
        dev_int8 = FSR4_SDK_DIR.parent.parent / "SDK DLL" / "DLL INT8"
        _scan_int8_dir(dev_int8, versions)

    # 3. Versões adicionadas pelo usuário
    _scan_int8_dir(FSR4_USER_SDK_DIR / "int8", versions, prefix="user/")

    # 4. Versões customizadas via config (caminhos diretos)
    if custom_versions:
        for name, path_str in custom_versions.items():
            p = Path(path_str)
            if p.exists() and p.suffix.lower() == '.dll':
                versions[name] = p

    return versions


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

    def get_setup_questions(self, version_id: int) -> List[SetupQuestion]:
        """
        Extrai as perguntas interativas dos scripts de configuração (setup.sh / setup.bat)
        contidos no arquivo da versão, sem instalar nada.

        Retorna lista vazia se a versão não contiver scripts de configuração.
        """
        try:
            with self.db_service.get_connection() as conn:
                version_repo = VersionRepository(conn)
                version = version_repo.find_by_id(version_id)

            if not version or not version.is_downloaded or not version.local_path:
                return []

            questions: List[SetupQuestion] = []
            with tempfile.TemporaryDirectory() as tmp_str:
                tmp_dir = Path(tmp_str)
                try:
                    self._extract_7z(version.local_path, tmp_dir)
                except Exception as e:
                    self.logger.warning(f"[Setup] Falha ao extrair para análise: {e}")
                    return []

                for script in self._find_setup_scripts(tmp_dir):
                    parsed = parse_script(script)
                    if parsed:
                        self.logger.info(
                            f"[Setup] '{script.name}' → {len(parsed)} pergunta(s) encontrada(s)"
                        )
                    questions.extend(parsed)

            return questions

        except Exception as e:
            self.logger.error(f"[Setup] Erro ao analisar scripts: {e}")
            return []

    def execute(
        self,
        game_id: int,
        version_id: int,
        loader_dll: str = "dxgi.dll",
        fsr4_variant: Optional[str] = None,
        fsr4_int8_version: Optional[str] = None,
        custom_int8_versions: dict = None,
        custom_standard_dlls: dict = None,
        setup_answers: Optional[List[str]] = None,
    ) -> bool:
        """
        Instala OptiScaler em um jogo.

        Args:
            game_id:               ID do jogo
            version_id:            ID da versão do OptiScaler
            loader_dll:            Nome do DLL loader (ex: dxgi.dll, winmm.dll)
            fsr4_variant:          "standard" (instala as 3 DLLs padrão), ou None
            fsr4_int8_version:     Versão int8 a sobrepor sobre o upscaler padrão (ex: "4.0.2c").
                                   Requer fsr4_variant="standard". None = não sobrepor.
            custom_int8_versions:  Dict {nome: caminho} para versões int8 customizadas.
            custom_standard_dlls:  Dict {dll_name: path} para substituir DLLs padrão individuais.
            setup_answers:         Respostas às perguntas dos scripts de configuração
                                   (obtidas via UI). Se None e scripts forem encontrados,
                                   fallback para terminal interativo.

        Returns:
            True se sucesso, False caso contrário
        """
        if not HAS_LIBARCHIVE and not HAS_PY7ZR:
            self.logger.error(
                "Nenhum extrator disponível. Execute: pip install libarchive-c"
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

                game_dir = self._determine_install_directory(game.path)
                self.logger.info(f"Diretório de instalação: {game_dir}")

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
                        installed_names = self._copy_files_to_game(tmp_dir, files_to_copy, game_dir, loader_dll)
                    except Exception as copy_err:
                        self.logger.error(f"Erro ao copiar arquivos: {copy_err}")
                        self._restore_backup(backup, game_dir)
                        return False

                    # 3b. Executar setup scripts (configuração pós-cópia)
                    setup_scripts = self._find_setup_scripts(tmp_dir)
                    if setup_scripts:
                        self.logger.info(
                            f"[Setup] {len(setup_scripts)} script(s) de configuração encontrado(s)"
                        )
                        for script in setup_scripts:
                            self.logger.info(f"[Setup] Executando: {script.name}")
                            ok = self._run_setup_script(
                                script, game_dir, answers=setup_answers
                            )
                            if not ok:
                                self.logger.warning(
                                    f"[Setup] Script '{script.name}' encerrado com erro ou cancelado."
                                )

                    # Copiar FSR4 SDK se solicitado
                    if fsr4_variant:
                        # 1. Sempre instalar as 3 DLLs padrão (com possíveis substituições)
                        fsr4_names = self._copy_fsr4_standard(
                            game_dir, custom_dlls=custom_standard_dlls or {}
                        )
                        installed_names.extend(fsr4_names)

                        # 2. Se quiser int8, sobrepor o upscaler (mesmo nome → sobrescreve)
                        if fsr4_int8_version:
                            int8_names = self._copy_fsr4_int8(
                                game_dir, fsr4_int8_version, custom_int8_versions or {}
                            )
                            installed_names.extend(int8_names)

                    # Salvar manifesto dos arquivos instalados no backup
                    self._save_manifest(backup.backup_path, installed_names, loader_dll)

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
        """Extrai o arquivo .7z para dest_dir.
        
        Usa libarchive (suporta BCJ2) como primário, py7zr como fallback.
        """
        if HAS_LIBARCHIVE:
            self._extract_with_libarchive(archive_path, dest_dir)
        elif HAS_PY7ZR:
            self.logger.warning("Usando py7zr — pode falhar com filtro BCJ2")
            with py7zr.SevenZipFile(archive_path, mode='r') as z:
                z.extractall(path=dest_dir)
        else:
            raise RuntimeError("Nenhum extrator disponível")

    def _extract_with_libarchive(self, archive_path: Path, dest_dir: Path):
        """Extrai usando libarchive (suporta todos os filtros do 7-zip)."""
        import libarchive
        with libarchive.file_reader(str(archive_path)) as archive:
            for entry in archive:
                # Ignorar entradas de diretório
                if entry.isdir:
                    dest = dest_dir / entry.pathname
                    dest.mkdir(parents=True, exist_ok=True)
                    continue
                dest = dest_dir / entry.pathname
                dest.parent.mkdir(parents=True, exist_ok=True)
                with open(dest, 'wb') as f:
                    for block in entry.get_blocks():
                        f.write(block)

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
    ) -> list:
        """
        Copia os arquivos extraídos para o diretório do jogo.
        Renomeia 'OptiScaler.dll' para o nome loader escolhido.
        Retorna lista de nomes de arquivos instalados.
        """
        installed = []
        for src in files_to_copy:
            dest_name = src.name
            if src.name.lower() == 'optiscaler.dll':
                dest_name = loader_dll
            dest = game_dir / dest_name
            shutil.copy2(src, dest)
            installed.append(dest_name)
            self.logger.debug(f"  Copiado: {dest_name}")
        return installed

    def _copy_fsr4_standard(self, game_dir: Path, custom_dlls: dict = None) -> list:
        """
        Copia as 3 DLLs padrão do FSR4 SDK para o diretório do jogo.

        Args:
            game_dir:    Diretório de destino
            custom_dlls: Dict {dll_name: path_str} para substituir DLLs individuais.
                         Exemplo: {'amd_fidelityfx_upscaler_dx12.dll': '/path/nova.dll'}
        """
        sdk_dir = FSR4_VARIANTS["standard"]
        if not sdk_dir or not sdk_dir.exists():
            self.logger.warning(f"FSR4 SDK 'standard' não encontrado em {sdk_dir}")
            return []

        installed = []
        for dll in sorted(sdk_dir.glob('*.dll')):
            # Verificar se há substituição configurada para esta DLL
            if custom_dlls and dll.name in custom_dlls:
                custom_path = Path(custom_dlls[dll.name])
                if custom_path.exists():
                    shutil.copy2(custom_path, game_dir / dll.name)
                    installed.append(dll.name)
                    self.logger.info(f"  FSR4 padrão (custom): {dll.name} ← {custom_path.name}")
                    continue
                else:
                    self.logger.warning(f"  Caminho custom não encontrado para {dll.name}: {custom_path}. Usando bundled.")
            shutil.copy2(dll, game_dir / dll.name)
            installed.append(dll.name)
            self.logger.debug(f"  FSR4 padrão: {dll.name}")
        self.logger.info(f"✓ {len(installed)} DLL(s) FSR4 padrão copiada(s)")
        return installed

    def _copy_fsr4_int8(self, game_dir: Path, version_name: str, custom_versions: dict) -> list:
        """
        Substitui o upscaler padrão pela versão int8 escolhida.

        Procura a versão em:
          1. Dicionário custom_versions {nome: Path}
          2. Subpastas de resources/fsr4_sdk/int8/
          3. Subpastas de user_data/fsr4_sdk/int8/
        """
        int8_versions = get_int8_versions(
            {k: str(v) for k, v in custom_versions.items()} if custom_versions else {}
        )
        dll_path = int8_versions.get(version_name)

        if not dll_path or not dll_path.exists():
            self.logger.warning(f"Versão int8 '{version_name}' não encontrada. Disponíveis: {list(int8_versions.keys())}")
            return []

        dest_name = dll_path.name  # amd_fidelityfx_upscaler_dx12.dll
        shutil.copy2(dll_path, game_dir / dest_name)
        self.logger.info(f"✓ FSR4 int8 '{version_name}' copiado ({dest_name})")
        return [dest_name]

    def _copy_fsr4_sdk(self, game_dir: Path, variant: str) -> list:
        """Mantido para compatibilidade retroativa. Use _copy_fsr4_standard/_copy_fsr4_int8."""
        if variant == "standard":
            return self._copy_fsr4_standard(game_dir)
        elif variant == "int8":
            # modo legado: pega a versão mais recente disponível
            versions = get_int8_versions()
            if not versions:
                self.logger.warning("Nenhuma versão int8 disponível")
                return []
            latest = sorted(versions.keys())[-1]
            return self._copy_fsr4_int8(game_dir, latest, {})
        return []

    def _save_manifest(self, backup_dir: Path, installed_names: list, loader_dll: str):
        """Salva manifesto JSON com lista de arquivos instalados."""
        manifest = {
            "loader_dll": loader_dll,
            "installed_files": installed_names
        }
        (backup_dir / "optiscaler_manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding='utf-8'
        )

    def _determine_install_directory(self, game_path: Path) -> Path:
        """
        Determina o diretório correto de instalação do OptiScaler para o jogo.
        Aplica heurísticas para jogos com estrutura Unreal Engine (Binaries/Win64 ou similar).

        Prioridade:
          1. Phoenix/Binaries/Win64 (jogos UE5 como Satisfactory, etc.)
          2. <GameName>/Binaries/Win64
          3. Binaries/Win64 diretamente
          4. Diretório do executável principal (maior score por tamanho + DLLs de upscaling)
          5. Fallback por DLLs conhecidas (quando não há .exe no diretório escolhido)
          6. game_path como fallback final
        """
        # Regra 1: estrutura Phoenix (UE5)
        phoenix_path = game_path / "Phoenix" / "Binaries" / "Win64"
        if phoenix_path.exists() and any(phoenix_path.glob("*.exe")):
            self.logger.info(f"Detectada estrutura Phoenix UE5: {phoenix_path}")
            return phoenix_path

        # Regra 2: Binaries/Win64 direto ou <Sub>/Binaries/Win64
        for candidate in [
            game_path / "Binaries" / "Win64",
            *(p / "Binaries" / "Win64" for p in game_path.iterdir() if p.is_dir()),
        ]:
            try:
                if candidate.exists() and any(candidate.glob("*.exe")):
                    self.logger.info(f"Detectada estrutura UE Binaries: {candidate}")
                    return candidate
            except PermissionError:
                continue

        # Regra 3: diretório do executável principal (heurística por score)
        best_dir = self._find_best_exe_dir(game_path)
        if best_dir:
            return best_dir

        # Regra 4: fallback por DLLs conhecidas quando não há .exe
        dll_dir = self._find_dir_by_known_dlls(game_path)
        if dll_dir:
            self.logger.info(
                f"Nenhum .exe encontrado — usando diretório com DLLs conhecidas: {dll_dir}"
            )
            return dll_dir

        return game_path

    def _find_dir_by_known_dlls(self, game_path: Path) -> Optional[Path]:
        """
        Busca o diretório correto de instalação procurando por DLLs conhecidas de upscaling
        quando não há executável (.exe) detectável.

        Procura em ordem de prioridade:
          1. amd_fidelityfx_upscaler_dx12.dll  (FSR4 SDK)
          2. nvngx_dlss.dll / nvngx.dll         (DLSS)
          3. libxess.dll                         (XeSS)
          4. amd_fidelityfx_dx12.dll            (FSR2/FSR3)
          5. dxgi.dll                            (loader genérico — menor prioridade)

        Returns:
            Diretório pai da primeira DLL encontrada, ou None.
        """
        KNOWN_DLLS = [
            "amd_fidelityfx_upscaler_dx12.dll",
            "nvngx_dlss.dll",
            "nvngx.dll",
            "libxess.dll",
            "amd_fidelityfx_dx12.dll",
            "dxgi.dll",
        ]
        try:
            for dll_name in KNOWN_DLLS:
                matches = list(game_path.rglob(dll_name))
                if matches:
                    found = matches[0].parent
                    self.logger.info(f"DLL de referência encontrada: {dll_name} → {found}")
                    return found
        except PermissionError:
            pass
        return None

    def _find_best_exe_dir(self, game_path: Path) -> Optional[Path]:
        """Encontra o diretório do executável principal usando heurística de score."""
        try:
            exe_files = list(game_path.rglob("*.exe"))
        except PermissionError:
            return None

        SKIP_NAMES = {
            "unins", "setup", "installer", "crash", "redist",
            "prerequisites", "unrealeditor", "unrealcefsubprocess",
        }

        UPSCALING_DLLS = {
            "nvngx_dlss.dll", "nvngx.dll", "amd_fidelityfx_dx12.dll",
            "ffx_fsr2_api_dx12_x64.dll", "libxess.dll",
        }

        best_score = -1
        best_dir: Optional[Path] = None

        for exe in exe_files:
            name = exe.stem.lower()
            if any(skip in name for skip in SKIP_NAMES):
                continue

            score = 0
            try:
                if exe.stat().st_size > 5 * 1024 * 1024:
                    score += 10
            except OSError:
                pass

            exe_dir = exe.parent
            try:
                dir_dlls = {f.name.lower() for f in exe_dir.glob("*.dll")}
                if dir_dlls & UPSCALING_DLLS:
                    score += 25
            except PermissionError:
                pass

            if "binaries" in str(exe_dir).lower():
                score += 5

            if score > best_score:
                best_score = score
                best_dir = exe_dir

        return best_dir

    # ------------------------------------------------------------------
    # Setup scripts (mods com configuração interativa)
    # ------------------------------------------------------------------

    def _find_setup_scripts(self, tmp_dir: Path) -> List[Path]:
        """
        Detecta scripts de configuração no diretório extraído.

        Critério:
          - Linux/macOS: arquivos cujo nome contenha "setup" e extensão .sh
          - Windows:     arquivos cujo nome contenha "setup" e extensão .bat

        Retorna lista ordenada (o script na raiz tem prioridade sobre subpastas).
        """
        system = _platform.system().lower()
        ext = ".bat" if system == "windows" else ".sh"

        found: List[Path] = []
        try:
            for f in tmp_dir.rglob(f"*{ext}"):
                if "setup" in f.stem.lower():
                    found.append(f)
        except PermissionError:
            pass

        # Prioriza scripts mais próximos da raiz
        found.sort(key=lambda p: len(p.parts))
        return found

    def _run_setup_script(
        self,
        script: Path,
        game_dir: Path,
        answers: Optional[List[str]] = None,
    ) -> bool:
        """
        Executa um script de configuração.

        Se *answers* for fornecido (lista de respostas no mesmo ordem das
        perguntas), o script é executado com as respostas enviadas via stdin —
        sem abrir janela de terminal.

        Se *answers* for None, tenta abrir um emulador de terminal gráfico
        interativo (fallback para execução direta sem janela quando nenhum
        emulador estiver disponível).

        Retorna True se o processo encerrou com código 0.
        """
        system = _platform.system().lower()
        cwd = str(game_dir)

        try:
            if system == "windows":
                if answers is not None:
                    stdin_data = "\r\n".join(answers).encode("utf-8")
                    result = subprocess.run(
                        ["cmd.exe", "/c", str(script)],
                        cwd=cwd,
                        input=stdin_data,
                    )
                else:
                    result = subprocess.run(
                        ["cmd.exe", "/c", str(script)],
                        cwd=cwd,
                    )
                return result.returncode == 0

            # ---- Linux / macOS ----
            try:
                script.chmod(script.stat().st_mode | 0o111)
            except OSError:
                pass

            script_cmd = ["bash", str(script)]

            if answers is not None:
                # Respostas coletadas pela UI → pipe via stdin (sem terminal)
                stdin_data = "\n".join(answers).encode("utf-8")
                result = subprocess.run(
                    script_cmd,
                    cwd=cwd,
                    input=stdin_data,
                )
                return result.returncode == 0

            # Modo interativo: abrir terminal gráfico
            TERMINAL_CANDIDATES = [
                ["konsole", "--noclose", "-e"] + script_cmd,
                ["gnome-terminal", "--wait", "--"] + script_cmd,
                ["xfce4-terminal", "--disable-server", "--hold", "-x"] + script_cmd,
                ["mate-terminal", "--"] + script_cmd,
                ["tilix", "-e"] + script_cmd,
                ["alacritty", "-e"] + script_cmd,
                ["xterm", "-hold", "-e"] + script_cmd,
            ]

            for cmd in TERMINAL_CANDIDATES:
                try:
                    result = subprocess.run(cmd, cwd=cwd)
                    return result.returncode == 0
                except FileNotFoundError:
                    continue

            self.logger.warning(
                "[Setup] Nenhum emulador de terminal encontrado. "
                "Executando script sem janela interativa."
            )
            result = subprocess.run(script_cmd, cwd=cwd)
            return result.returncode == 0

        except Exception as exc:
            self.logger.error(f"[Setup] Erro ao executar script '{script.name}': {exc}")
            return False

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
