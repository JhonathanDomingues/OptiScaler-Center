"""
Serviço para interagir com GitHub API
Download de releases do OptiScaler
"""
import re
import requests
from pathlib import Path
from typing import List, Optional, Dict, Callable
from datetime import datetime
import shutil

from utils.logger import LoggerMixin
from domain.entities.optiscaler_version import OptiScalerVersion


class GitHubService(LoggerMixin):
    """Gerencia downloads de releases do GitHub"""
    
    REPO_OWNER = "cdozdil"
    REPO_NAME = "OptiScaler"
    API_BASE = "https://api.github.com"
    
    def __init__(self, cache_dir: Path, token: str = ""):
        """
        Inicializa o serviço
        
        Args:
            cache_dir: Diretório para cache de downloads
            token: GitHub Personal Access Token (opcional, necessário para artefatos de Actions)
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._token = token
        
        # Headers para API do GitHub
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'OptiScaler-Center'
        }
        self._update_auth_headers()

    def set_token(self, token: str):
        """Define/atualiza o token de autenticação."""
        self._token = token
        self._update_auth_headers()

    def set_repo(self, repo: str):
        """Define/atualiza o repositório estável (formato 'owner/name')."""
        if '/' in repo:
            owner, name = repo.split('/', 1)
            self.REPO_OWNER = owner
            self.REPO_NAME = name

    def _update_auth_headers(self):
        """Atualiza headers com token de autenticação, se disponível."""
        if self._token:
            self.headers['Authorization'] = f'Bearer {self._token}'
        else:
            self.headers.pop('Authorization', None)
    
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

    # ------------------------------------------------------------------
    # GitHub Actions — betas / workflow artifacts
    # ------------------------------------------------------------------

    def fetch_beta_builds(
        self,
        repo: str = "cdozdil/OptiScaler",
        workflow: str = "release_debug.yml",
        branch_pattern: str = r'release/0\.[0-9].*',
        limit: int = 20
    ) -> List[OptiScalerVersion]:
        """
        Busca betas a partir de runs do workflow GitHub Actions.

        Requer token configurado (set_token) para baixar artefatos.
        Sem token, apenas lista os artefatos disponíveis.

        Args:
            repo:           "owner/repo" do repositório
            workflow:       nome do arquivo de workflow (ex: release_debug.yml)
            branch_pattern: regex para filtrar branches (ex: r'release/0\\.[0-9].*')
            limit:          número máximo de runs a inspecionar
        Returns:
            Lista de OptiScalerVersion representando os betas encontrados
        """
        owner, name = repo.split('/', 1) if '/' in repo else (self.REPO_OWNER, self.REPO_NAME)
        self.logger.info(f"Buscando betas via Actions ({repo} / {workflow})...")

        # 1. Listar workflow runs
        url = f"{self.API_BASE}/repos/{owner}/{name}/actions/workflows/{workflow}/runs"
        params = {"status": "success", "per_page": min(limit, 100)}
        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=15)
            resp.raise_for_status()
            runs = resp.json().get("workflow_runs", [])
        except requests.RequestException as e:
            self.logger.error(f"Erro ao listar workflow runs: {e}")
            return []

        # 2. Filtrar por branch
        try:
            pat = re.compile(branch_pattern)
        except re.error:
            pat = re.compile(re.escape(branch_pattern))

        versions: List[OptiScalerVersion] = []
        seen_branches: set = set()

        for run in runs:
            branch = run.get("head_branch", "")
            if not pat.search(branch):
                continue
            if branch in seen_branches:
                continue
            seen_branches.add(branch)

            run_id = run["id"]
            created_at = datetime.strptime(run["created_at"], '%Y-%m-%dT%H:%M:%SZ')
            tag = branch.replace("/", "-")  # ex: release-0.9.5

            # 3. Listar artefatos do run
            arts_url = f"{self.API_BASE}/repos/{owner}/{name}/actions/runs/{run_id}/artifacts"
            try:
                arts_resp = requests.get(arts_url, headers=self.headers, timeout=10)
                arts_resp.raise_for_status()
                artifacts = arts_resp.json().get("artifacts", [])
            except requests.RequestException as e:
                self.logger.warning(f"Erro ao listar artefatos do run {run_id}: {e}")
                artifacts = []

            # Preferir artefato com zip ou nome contendo "OptiScaler"
            art = None
            for a in artifacts:
                aname = a["name"].lower()
                if "optiscaler" in aname or aname.endswith(".zip") or aname.endswith(".7z"):
                    art = a
                    break
            if not art and artifacts:
                art = artifacts[0]

            if art:
                filename = f"{art['name']}.zip"
                cache_path = self.cache_dir / filename
                is_downloaded = cache_path.exists()

                version = OptiScalerVersion(
                    tag_name=tag,
                    name=f"Beta: {branch} ({run['head_sha'][:7]})",
                    description=f"Build de workflow: {branch}\nRun: {run_id}",
                    release_date=created_at,
                    is_prerelease=True,
                    download_url=art.get("archive_download_url", ""),
                    total_size=art.get("size_in_bytes", 0),
                    cache_path=cache_path if is_downloaded else None,
                    is_downloaded=is_downloaded,
                )
                # Guarda ID do artefato para download posterior
                version.github_id = art["id"]
                versions.append(version)

        self.logger.info(f"✓ {len(versions)} betas encontrados")
        return versions

    def download_artifact(
        self,
        artifact_id: int,
        output_path: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Optional[Path]:
        """
        Faz download de um artefato do GitHub Actions.

        Requer token de autenticação configurado via set_token().

        Args:
            artifact_id:       ID numérico do artefato
            output_path:       Caminho destino do arquivo
            progress_callback: Callback (bytes_baixados, total)
        Returns:
            Path do arquivo ou None em caso de erro
        """
        if not self._token:
            self.logger.error("Token GitHub não configurado — necessário para baixar artefatos de Actions")
            return None

        url = f"{self.API_BASE}/repos/{self.REPO_OWNER}/{self.REPO_NAME}/actions/artifacts/{artifact_id}/zip"
        self.logger.info(f"Baixando artefato {artifact_id}...")

        try:
            resp = requests.get(url, headers=self.headers, stream=True, timeout=30, allow_redirects=True)
            resp.raise_for_status()

            total = int(resp.headers.get('content-length', 0))
            downloaded = 0
            temp = output_path.with_suffix('.tmp')

            with open(temp, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total)

            temp.rename(output_path)
            self.logger.info(f"✓ Artefato baixado: {output_path.name}")
            return output_path

        except requests.RequestException as e:
            self.logger.error(f"Erro ao baixar artefato: {e}")
            temp = output_path.with_suffix('.tmp')
            if temp.exists():
                temp.unlink()
            return None

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
