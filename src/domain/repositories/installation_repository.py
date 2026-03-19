"""
Repository para gerenciar instalações do OptiScaler
"""
import sqlite3
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from utils.logger import LoggerMixin
from domain.entities.installation import Installation


class InstallationRepository(LoggerMixin):
    """Repository para operações CRUD de instalações"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """
        Inicializa o repository
        
        Args:
            db_connection: Conexão SQLite ativa
        """
        self.conn = db_connection
    
    def save(self, installation: Installation) -> int:
        """
        Salva ou atualiza uma instalação
        
        Args:
            installation: Installation objeto
        
        Returns:
            ID da instalação salva
        """
        cursor = self.conn.cursor()
        
        try:
            if installation.id:
                # Atualizar existente
                cursor.execute("""
                    UPDATE installations SET
                        game_id = ?,
                        version = ?,
                        backup_path = ?,
                        config_path = ?,
                        status = ?
                    WHERE id = ?
                """, (
                    installation.game_id,
                    installation.version,
                    str(installation.backup_path) if installation.backup_path else None,
                    str(installation.config_path) if installation.config_path else None,
                    installation.status,
                    installation.id
                ))

                install_id = installation.id

            else:
                # Inserir nova
                install_date = installation.install_date or datetime.now()
                cursor.execute("""
                    INSERT INTO installations (
                        game_id, version, install_date,
                        backup_path, config_path, status
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    installation.game_id,
                    installation.version,
                    install_date.isoformat(),
                    str(installation.backup_path) if installation.backup_path else None,
                    str(installation.config_path) if installation.config_path else None,
                    installation.status
                ))
                
                install_id = cursor.lastrowid
                installation.id = install_id
            
            self.conn.commit()
            self.logger.debug(f"Instalação salva: ID {install_id}")
            return install_id
        
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Erro ao salvar instalação: {e}")
            raise
    
    def find_by_id(self, install_id: int) -> Optional[Installation]:
        """
        Busca instalação por ID
        
        Args:
            install_id: ID da instalação
        
        Returns:
            Installation objeto ou None
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM installations WHERE id = ?", (install_id,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_installation(row)
        
        return None
    
    def find_by_game(self, game_id: int) -> List[Installation]:
        """
        Busca instalações de um jogo

        Args:
            game_id: ID do jogo

        Returns:
            Lista de Installation objetos
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM installations
            WHERE game_id = ?
            ORDER BY install_date DESC
        """, (game_id,))
        
        rows = cursor.fetchall()
        return [self._row_to_installation(row) for row in rows]
    
    def find_active_by_game(self, game_id: int) -> Optional[Installation]:
        """
        Busca instalação ativa de um jogo

        Args:
            game_id: ID do jogo

        Returns:
            Installation objeto ou None
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM installations
            WHERE game_id = ? AND status = 'active'
            ORDER BY install_date DESC
            LIMIT 1
        """, (game_id,))
        
        row = cursor.fetchone()
        
        if row:
            return self._row_to_installation(row)
        
        return None
    
    def find_all(self) -> List[Installation]:
        """
        Busca todas as instalações

        Returns:
            Lista de Installation objetos
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM installations
            ORDER BY install_date DESC
        """)
        
        rows = cursor.fetchall()
        return [self._row_to_installation(row) for row in rows]
    
    def delete(self, install_id: int) -> bool:
        """
        Remove uma instalação do banco
        
        Args:
            install_id: ID da instalação
        
        Returns:
            True se removido, False caso contrário
        """
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("DELETE FROM installations WHERE id = ?", (install_id,))
            self.conn.commit()
            
            if cursor.rowcount > 0:
                self.logger.debug(f"Instalação removida: ID {install_id}")
                return True
            
            return False
        
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Erro ao deletar instalação {install_id}: {e}")
            raise
    
    def count_by_game(self, game_id: int) -> int:
        """
        Conta instalações de um jogo
        
        Args:
            game_id: ID do jogo
        
        Returns:
            Número de instalações
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM installations WHERE game_id = ?
        """, (game_id,))
        
        return cursor.fetchone()[0]
    
    def _row_to_installation(self, row: sqlite3.Row) -> Installation:
        """
        Converte linha do banco para objeto Installation
        
        Args:
            row: Linha SQLite
        
        Returns:
            Installation objeto
        """
        install_date = datetime.fromisoformat(row['install_date']) if row['install_date'] else datetime.now()

        return Installation(
            id=row['id'],
            game_id=row['game_id'],
            version=row['version'],
            install_date=install_date,
            backup_path=Path(row['backup_path']) if row['backup_path'] else None,
            config_path=Path(row['config_path']) if row['config_path'] else None,
            status=row['status']
        )
