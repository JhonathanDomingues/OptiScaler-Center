"""
Repository para gerenciar backups de DLLs
"""
import sqlite3
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from utils.logger import LoggerMixin
from domain.entities.backup import Backup


class BackupRepository(LoggerMixin):
    """Repository para operações CRUD de backups"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """
        Inicializa o repository
        
        Args:
            db_connection: Conexão SQLite ativa
        """
        self.conn = db_connection
    
    def save(self, backup: Backup) -> int:
        """
        Salva ou atualiza um backup
        
        Args:
            backup: Backup objeto
        
        Returns:
            ID do backup salvo
        """
        cursor = self.conn.cursor()
        
        try:
            # Serializar lista de arquivos
            files_json = json.dumps([str(f) for f in backup.files])
            
            if backup.id:
                # Atualizar existente
                cursor.execute("""
                    UPDATE backups SET
                        game_id = ?,
                        backup_path = ?,
                        files = ?,
                        total_size = ?,
                        status = ?
                    WHERE id = ?
                """, (
                    backup.game_id,
                    str(backup.backup_path),
                    files_json,
                    backup.total_size,
                    backup.status,
                    backup.id
                ))
                
                backup_id = backup.id
            
            else:
                # Inserir novo
                cursor.execute("""
                    INSERT INTO backups (
                        game_id, backup_path, files, total_size,
                        status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    backup.game_id,
                    str(backup.backup_path),
                    files_json,
                    backup.total_size,
                    backup.status,
                    backup.created_at.isoformat()
                ))
                
                backup_id = cursor.lastrowid
                backup.id = backup_id
            
            self.conn.commit()
            self.logger.debug(f"Backup salvo: ID {backup_id}")
            return backup_id
        
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Erro ao salvar backup: {e}")
            raise
    
    def find_by_id(self, backup_id: int) -> Optional[Backup]:
        """
        Busca backup por ID
        
        Args:
            backup_id: ID do backup
        
        Returns:
            Backup objeto ou None
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM backups WHERE id = ?", (backup_id,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_backup(row)
        
        return None
    
    def find_by_game(self, game_id: int) -> List[Backup]:
        """
        Busca backups de um jogo
        
        Args:
            game_id: ID do jogo
        
        Returns:
            Lista de Backup objetos
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM backups 
            WHERE game_id = ?
            ORDER BY created_at DESC
        """, (game_id,))
        
        rows = cursor.fetchall()
        return [self._row_to_backup(row) for row in rows]
    
    def find_latest_by_game(self, game_id: int) -> Optional[Backup]:
        """
        Busca backup mais recente de um jogo
        
        Args:
            game_id: ID do jogo
        
        Returns:
            Backup objeto ou None
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM backups 
            WHERE game_id = ? AND status = 'active'
            ORDER BY created_at DESC
            LIMIT 1
        """, (game_id,))
        
        row = cursor.fetchone()
        
        if row:
            return self._row_to_backup(row)
        
        return None
    
    def find_all(self) -> List[Backup]:
        """
        Busca todos os backups
        
        Returns:
            Lista de Backup objetos
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM backups 
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        return [self._row_to_backup(row) for row in rows]
    
    def delete(self, backup_id: int) -> bool:
        """
        Remove um backup do banco
        
        Args:
            backup_id: ID do backup
        
        Returns:
            True se removido, False caso contrário
        """
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("DELETE FROM backups WHERE id = ?", (backup_id,))
            self.conn.commit()
            
            if cursor.rowcount > 0:
                self.logger.debug(f"Backup removido: ID {backup_id}")
                return True
            
            return False
        
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Erro ao deletar backup {backup_id}: {e}")
            raise
    
    def count_by_game(self, game_id: int) -> int:
        """
        Conta backups de um jogo
        
        Args:
            game_id: ID do jogo
        
        Returns:
            Número de backups
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM backups WHERE game_id = ?
        """, (game_id,))
        
        return cursor.fetchone()[0]
    
    def get_total_backup_size(self) -> int:
        """
        Calcula tamanho total de todos os backups
        
        Returns:
            Tamanho em bytes
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT SUM(total_size) FROM backups WHERE status = 'active'
        """)
        
        result = cursor.fetchone()[0]
        return result if result else 0
    
    def _row_to_backup(self, row: sqlite3.Row) -> Backup:
        """
        Converte linha do banco para objeto Backup
        
        Args:
            row: Linha SQLite
        
        Returns:
            Backup objeto
        """
        # Deserializar lista de arquivos
        files = []
        if row['files']:
            try:
                files_list = json.loads(row['files'])
                files = [Path(f) for f in files_list]
            except:
                pass
        
        created_at = datetime.fromisoformat(row['created_at'])
        
        return Backup(
            id=row['id'],
            game_id=row['game_id'],
            backup_path=Path(row['backup_path']),
            files=files,
            total_size=row['total_size'],
            status=row['status'],
            created_at=created_at
        )
