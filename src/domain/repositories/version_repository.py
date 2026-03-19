"""
Repository para gerenciar versões do OptiScaler
"""
import sqlite3
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from utils.logger import LoggerMixin
from domain.entities.optiscaler_version import OptiScalerVersion


class VersionRepository(LoggerMixin):
    """Repository para operações CRUD de versões"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """
        Inicializa o repository
        
        Args:
            db_connection: Conexão SQLite ativa
        """
        self.conn = db_connection
    
    def save(self, version: OptiScalerVersion) -> int:
        """
        Salva ou atualiza uma versão
        
        Args:
            version: OptiScalerVersion objeto
        
        Returns:
            ID da versão salva
        """
        cursor = self.conn.cursor()
        
        try:
            # Verificar se já existe
            existing = self.find_by_tag(version.tag_name)
            
            if existing:
                # Atualizar
                cursor.execute("""
                    UPDATE optiscaler_versions SET
                        name = ?,
                        description = ?,
                        is_prerelease = ?,
                        download_url = ?,
                        file_size = ?,
                        local_path = ?,
                        is_downloaded = ?,
                        updated_at = ?
                    WHERE tag_name = ?
                """, (
                    version.name,
                    version.description,
                    version.is_prerelease,
                    version.download_url,
                    version.file_size,
                    str(version.local_path) if version.local_path else None,
                    version.is_downloaded,
                    datetime.now().isoformat(),
                    version.tag_name
                ))
                
                version_id = existing.id
            
            else:
                # Inserir nova
                cursor.execute("""
                    INSERT INTO optiscaler_versions (
                        tag_name, name, description, release_date,
                        is_prerelease, download_url, file_size,
                        local_path, is_downloaded, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    version.tag_name,
                    version.name,
                    version.description,
                    version.release_date.isoformat(),
                    version.is_prerelease,
                    version.download_url,
                    version.file_size,
                    str(version.local_path) if version.local_path else None,
                    version.is_downloaded,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
                version_id = cursor.lastrowid
                version.id = version_id
            
            self.conn.commit()
            self.logger.debug(f"Versão salva: {version.tag_name} (ID: {version_id})")
            return version_id
        
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Erro ao salvar versão {version.tag_name}: {e}")
            raise
    
    def find_by_id(self, version_id: int) -> Optional[OptiScalerVersion]:
        """
        Busca versão por ID
        
        Args:
            version_id: ID da versão
        
        Returns:
            OptiScalerVersion objeto ou None
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM optiscaler_versions WHERE id = ?", (version_id,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_version(row)
        
        return None
    
    def find_by_tag(self, tag_name: str) -> Optional[OptiScalerVersion]:
        """
        Busca versão por tag
        
        Args:
            tag_name: Nome da tag (ex: v0.7.1)
        
        Returns:
            OptiScalerVersion objeto ou None
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM optiscaler_versions WHERE tag_name = ?", (tag_name,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_version(row)
        
        return None
    
    def find_all(self, include_prerelease: bool = True) -> List[OptiScalerVersion]:
        """
        Busca todas as versões
        
        Args:
            include_prerelease: Se deve incluir pré-releases
        
        Returns:
            Lista de OptiScalerVersion objetos
        """
        cursor = self.conn.cursor()
        
        if include_prerelease:
            cursor.execute("""
                SELECT * FROM optiscaler_versions 
                ORDER BY release_date DESC
            """)
        else:
            cursor.execute("""
                SELECT * FROM optiscaler_versions 
                WHERE is_prerelease = 0
                ORDER BY release_date DESC
            """)
        
        rows = cursor.fetchall()
        return [self._row_to_version(row) for row in rows]
    
    def find_latest(self, include_prerelease: bool = False) -> Optional[OptiScalerVersion]:
        """
        Busca versão mais recente
        
        Args:
            include_prerelease: Se deve considerar pré-releases
        
        Returns:
            OptiScalerVersion objeto ou None
        """
        cursor = self.conn.cursor()
        
        if include_prerelease:
            cursor.execute("""
                SELECT * FROM optiscaler_versions 
                ORDER BY release_date DESC
                LIMIT 1
            """)
        else:
            cursor.execute("""
                SELECT * FROM optiscaler_versions 
                WHERE is_prerelease = 0
                ORDER BY release_date DESC
                LIMIT 1
            """)
        
        row = cursor.fetchone()
        
        if row:
            return self._row_to_version(row)
        
        return None
    
    def find_downloaded(self) -> List[OptiScalerVersion]:
        """
        Busca versões já baixadas
        
        Returns:
            Lista de OptiScalerVersion objetos
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM optiscaler_versions 
            WHERE is_downloaded = 1
            ORDER BY release_date DESC
        """)
        
        rows = cursor.fetchall()
        return [self._row_to_version(row) for row in rows]
    
    def delete(self, version_id: int) -> bool:
        """
        Remove uma versão do banco
        
        Args:
            version_id: ID da versão
        
        Returns:
            True se removido, False caso contrário
        """
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("DELETE FROM optiscaler_versions WHERE id = ?", (version_id,))
            self.conn.commit()
            
            if cursor.rowcount > 0:
                self.logger.debug(f"Versão removida: ID {version_id}")
                return True
            
            return False
        
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Erro ao deletar versão {version_id}: {e}")
            raise
    
    def count(self) -> int:
        """
        Conta total de versões
        
        Returns:
            Número de versões
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM optiscaler_versions")
        return cursor.fetchone()[0]
    
    def _row_to_version(self, row: sqlite3.Row) -> OptiScalerVersion:
        """
        Converte linha do banco para objeto OptiScalerVersion
        
        Args:
            row: Linha SQLite
        
        Returns:
            OptiScalerVersion objeto
        """
        release_date = datetime.fromisoformat(row['release_date'])
        
        return OptiScalerVersion(
            id=row['id'],
            tag_name=row['tag_name'],
            name=row['name'] or "",
            description=row['description'] or "",
            release_date=release_date,
            is_prerelease=bool(row['is_prerelease']),
            download_url=row['download_url'] or "",
            total_size=row['file_size'] or 0,
            cache_path=Path(row['local_path']) if row['local_path'] else None,
            is_downloaded=bool(row['is_downloaded'])
        )
