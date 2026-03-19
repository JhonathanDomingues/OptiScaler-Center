"""
Repository para gerenciar jogos no banco de dados
"""
import json
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

from utils.logger import LoggerMixin
from domain.entities.game import Game
from domain.entities.installation import Installation
from domain.entities.dll_info import DLLInfo
from domain.enums.dll_type import DLLType, APIType
from domain.enums.platform import Platform


class GameRepository(LoggerMixin):
    """Repository para operações CRUD de jogos"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """
        Inicializa o repository
        
        Args:
            db_connection: Conexão SQLite ativa
        """
        self.conn = db_connection
    
    def save(self, game: Game) -> int:
        """
        Salva ou atualiza um jogo no banco
        
        Args:
            game: Game objeto
        
        Returns:
            ID do jogo salvo
        """
        cursor = self.conn.cursor()
        
        try:
            # Verificar se já existe (por appid ou por path)
            existing = None
            if game.appid:
                existing = self.find_by_appid(game.appid)
            if not existing and game.path:
                existing = self.find_by_path(game.path)
            
            if existing:
                # Atualizar
                cursor.execute("""
                    UPDATE games SET
                        name = ?,
                        path = ?,
                        platform = ?,
                        executable = ?,
                        appid = ?,
                        last_scanned = ?,
                        notes = ?
                    WHERE id = ?
                """, (
                    game.name,
                    str(game.path),
                    game.platform.value if hasattr(game.platform, 'value') else str(game.platform),
                    str(game.executable) if game.executable else None,
                    game.appid,
                    game.last_scanned.isoformat() if game.last_scanned else None,
                    game.notes,
                    existing.id
                ))
                
                game_id = existing.id
                game.id = game_id
                self.logger.debug(f"Jogo atualizado: {game.name} (ID: {game_id})")
            
            else:
                # Inserir novo
                cursor.execute("""
                    INSERT INTO games (
                        name, path, platform, executable, appid,
                        detected_date, last_scanned, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    game.name,
                    str(game.path),
                    game.platform.value if hasattr(game.platform, 'value') else str(game.platform),
                    str(game.executable) if game.executable else None,
                    game.appid,
                    game.detected_date.isoformat() if game.detected_date else datetime.now().isoformat(),
                    game.last_scanned.isoformat() if game.last_scanned else None,
                    game.notes
                ))
                
                game_id = cursor.lastrowid
                game.id = game_id
                self.logger.debug(f"Jogo salvo: {game.name} (ID: {game_id})")
            
            # Salvar DLLs detectadas
            self._save_detected_dlls(game_id, game.supported_dlls)
            
            self.conn.commit()
            return game_id
        
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Erro ao salvar jogo {game.name}: {e}")
            raise
    
    def find_by_id(self, game_id: int) -> Optional[Game]:
        """
        Busca jogo por ID
        
        Args:
            game_id: ID do jogo
        
        Returns:
            Game objeto ou None
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM games WHERE id = ?", (game_id,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_game(row)
        
        return None
    
    def find_by_appid(self, appid: int) -> Optional[Game]:
        """
        Busca jogo por Steam AppID
        
        Args:
            appid: Steam AppID
        
        Returns:
            Game objeto ou None
        """
        if not appid:
            return None
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM games WHERE appid = ?", (appid,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_game(row)
        
        return None
    
    def find_by_path(self, path: Path) -> Optional[Game]:
        """
        Busca jogo por caminho de instalação
        
        Args:
            path: Caminho do jogo
        
        Returns:
            Game objeto ou None
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM games WHERE path = ?", (str(path),))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_game(row)
        
        return None
    
    def find_all(self) -> List[Game]:
        """
        Busca todos os jogos
        
        Returns:
            Lista de Game objetos
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM games ORDER BY name ASC")
        rows = cursor.fetchall()
        
        return [self._row_to_game(row) for row in rows]
    
    def find_with_upscaling_support(self) -> List[Game]:
        """
        Busca jogos com suporte a alguma tecnologia de upscaling
        
        Returns:
            Lista de Game objetos
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT g.* FROM games g
            INNER JOIN game_dlls d ON g.id = d.game_id
            ORDER BY g.name ASC
        """)
        rows = cursor.fetchall()
        
        return [self._row_to_game(row) for row in rows]
    
    def find_by_technology(self, dll_type: DLLType) -> List[Game]:
        """
        Busca jogos com suporte a tecnologia específica
        
        Args:
            dll_type: Tipo de DLL (DLSS, FSR, XeSS)
        
        Returns:
            Lista de Game objetos
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT g.* FROM games g
            INNER JOIN game_dlls d ON g.id = d.game_id
            WHERE d.dll_type = ?
            ORDER BY g.name ASC
        """, (dll_type.value,))
        
        rows = cursor.fetchall()
        
        return [self._row_to_game(row) for row in rows]
    
    def delete(self, game_id: int) -> bool:
        """
        Remove um jogo do banco
        
        Args:
            game_id: ID do jogo
        
        Returns:
            True se removido, False caso contrário
        """
        cursor = self.conn.cursor()
        
        try:
            # Deletar DLLs associadas
            cursor.execute("DELETE FROM game_dlls WHERE game_id = ?", (game_id,))
            
            # Deletar jogo
            cursor.execute("DELETE FROM games WHERE id = ?", (game_id,))
            
            self.conn.commit()
            
            if cursor.rowcount > 0:
                self.logger.debug(f"Jogo removido: ID {game_id}")
                return True
            
            return False
        
        except Exception as e:
            self.conn.rollback()
            self.logger.error(f"Erro ao deletar jogo {game_id}: {e}")
            raise
    
    def count(self) -> int:
        """
        Conta total de jogos
        
        Returns:
            Número de jogos
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM games")
        return cursor.fetchone()[0]
    
    def _row_to_game(self, row: sqlite3.Row) -> Game:
        """
        Converte linha do banco para objeto Game
        
        Args:
            row: Linha SQLite
        
        Returns:
            Game objeto
        """
        # Helper para acessar valores de Row com segurança
        def get_row_value(row, key, default=None):
            try:
                return row[key]
            except (KeyError, IndexError):
                return default
        
        # Carregar DLLs detectadas
        supported_dlls = self._load_detected_dlls(row['id'])
        
        # Parsear datas
        last_scanned = None
        last_scanned_str = get_row_value(row, 'last_scanned')
        if last_scanned_str:
            try:
                last_scanned = datetime.fromisoformat(last_scanned_str)
            except:
                pass
        
        detected_date = datetime.now()
        detected_date_str = get_row_value(row, 'detected_date')
        if detected_date_str:
            try:
                detected_date = datetime.fromisoformat(detected_date_str)
            except:
                pass
        
        # Parsear platform
        platform = Platform.UNKNOWN
        platform_str = get_row_value(row, 'platform')
        if platform_str:
            try:
                platform = Platform(platform_str)
            except:
                platform = Platform.UNKNOWN
        
        # Parsear executable
        executable = None
        executable_str = get_row_value(row, 'executable')
        if executable_str:
            executable = Path(executable_str)
        
        return Game(
            id=row['id'],
            appid=get_row_value(row, 'appid'),
            name=row['name'],
            path=Path(row['path']),
            platform=platform,
            executable=executable,
            supported_dlls=supported_dlls,
            installation=self._load_active_installation(row['id']),
            last_scanned=last_scanned,
            detected_date=detected_date,
            notes=get_row_value(row, 'notes', '')
        )
    
    def _load_active_installation(self, game_id: int) -> Optional['Installation']:
        """Carrega a instalação ativa do jogo, se houver."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM installations WHERE game_id = ? AND status = 'active' ORDER BY install_date DESC LIMIT 1",
                (game_id,)
            )
            row = cursor.fetchone()
            if row:
                from domain.entities.installation import Installation
                install_date = None
                if row['install_date']:
                    try:
                        install_date = datetime.fromisoformat(row['install_date'])
                    except Exception:
                        pass
                backup_path = Path(row['backup_path']) if row['backup_path'] else None
                return Installation(
                    id=row['id'],
                    game_id=row['game_id'],
                    version=row['version'],
                    install_date=install_date,
                    backup_path=backup_path,
                    status=row['status']
                )
        except Exception as e:
            self.logger.warning(f"Erro ao carregar instalação ativa do jogo {game_id}: {e}")
        return None

    def _save_detected_dlls(self, game_id: int, detected_dlls: Dict[str, DLLInfo]):
        """
        Salva DLLs detectadas na tabela game_dlls
        
        Args:
            game_id: ID do jogo
            detected_dlls: Dict {dll_type: DLLInfo}
        """
        cursor = self.conn.cursor()
        
        # Deletar DLLs antigas
        cursor.execute("DELETE FROM game_dlls WHERE game_id = ?", (game_id,))
        
        # Inserir novas
        for dll_type_str, dll_info in detected_dlls.items():
            cursor.execute("""
                INSERT INTO game_dlls (
                    game_id, dll_type, dll_path, dll_size, dll_hash,
                    version, api_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                game_id,
                dll_type_str,
                str(dll_info.path),
                dll_info.size,
                dll_info.hash,
                dll_info.version,
                dll_info.api_type.value if dll_info.api_type else None
            ))
    
    def _load_detected_dlls(self, game_id: int) -> Dict[str, DLLInfo]:
        """
        Carrega DLLs detectadas da tabela game_dlls
        
        Args:
            game_id: ID do jogo
        
        Returns:
            Dict {dll_type: DLLInfo}
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM game_dlls WHERE game_id = ?
        """, (game_id,))
        
        rows = cursor.fetchall()
        detected_dlls = {}
        
        for row in rows:
            try:
                # Helper para acessar valores de Row com segurança
                def get_row_value(key, default=None):
                    try:
                        return row[key]
                    except (KeyError, IndexError):
                        return default
                
                dll_type = DLLType(row['dll_type'])
                api_type_str = get_row_value('api_type')
                api_type = APIType(api_type_str) if api_type_str else APIType.UNKNOWN
                
                dll_info = DLLInfo(
                    dll_type=dll_type,
                    path=Path(row['dll_path']),
                    size=row['dll_size'],
                    hash=row['dll_hash'],
                    version=get_row_value('version'),
                    api_type=api_type
                )
                
                detected_dlls[row['dll_type']] = dll_info
            
            except Exception as e:
                self.logger.warning(f"Erro ao carregar DLL: {e}")
        
        return detected_dlls
