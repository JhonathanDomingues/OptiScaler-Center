"""
Serviço de banco de dados SQLite
"""
import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from utils.logger import LoggerMixin
from utils.constants import DATABASE_PATH, DATA_DIR


class DatabaseService(LoggerMixin):
    """Gerencia conexão e operações no banco de dados SQLite"""
    
    def __init__(self, db_path: Path = DATABASE_PATH):
        self.db_path = db_path
        self._ensure_database()
    
    def _ensure_database(self):
        """Garante que o banco de dados e as tabelas existam"""
        # Criar diretório se não existir
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Criar banco se não existir
        if not self.db_path.exists():
            self.logger.info(f"Criando banco de dados em {self.db_path}")
            self._create_tables()
        else:
            self.logger.info(f"Banco de dados encontrado em {self.db_path}")
            self._migrate_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexão com o banco"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Permite acesso por nome de coluna
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Erro no banco de dados: {e}")
            raise
        finally:
            conn.close()
    
    def _create_tables(self):
        """Cria todas as tabelas do banco"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabela de jogos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    path TEXT NOT NULL UNIQUE,
                    executable TEXT,
                    platform TEXT,
                    appid INTEGER,
                    detected_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_scanned DATETIME,
                    notes TEXT
                )
            ''')
            
            # Tabela de DLLs detectadas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS game_dlls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER NOT NULL,
                    dll_type TEXT NOT NULL,
                    dll_path TEXT NOT NULL,
                    dll_size INTEGER,
                    dll_hash TEXT,
                    version TEXT,
                    api_type TEXT,
                    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE,
                    UNIQUE(game_id, dll_type)
                )
            ''')
            
            # Tabela de instalações
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS installations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER NOT NULL,
                    version TEXT NOT NULL,
                    install_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    backup_path TEXT,
                    config_path TEXT,
                    status TEXT DEFAULT 'active',
                    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
                )
            ''')
            
            # Tabela de versões do OptiScaler
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS optiscaler_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tag_name TEXT NOT NULL UNIQUE,
                    name TEXT,
                    description TEXT,
                    release_date DATETIME,
                    is_prerelease INTEGER DEFAULT 0,
                    download_url TEXT,
                    file_size INTEGER,
                    local_path TEXT,
                    is_downloaded INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de backups
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER NOT NULL,
                    backup_path TEXT NOT NULL,
                    backup_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    file_count INTEGER,
                    total_size INTEGER,
                    notes TEXT,
                    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
                )
            ''')
            
            # Tabela de configurações
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela de logs de operações
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS operation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_type TEXT NOT NULL,
                    game_id INTEGER,
                    status TEXT,
                    message TEXT,
                    details TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE SET NULL
                )
            ''')
            
            # Índices para performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_games_platform ON games(platform)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_installations_game ON installations(game_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_installations_status ON installations(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_operation ON operation_logs(operation_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_created ON operation_logs(created_at)')
            
            self.logger.info("Tabelas criadas com sucesso")
    
    def _migrate_database(self):
        """Executa migrações necessárias no banco de dados"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Migração 1: Renomear steam_appid para appid na tabela games
                cursor.execute("PRAGMA table_info(games)")
                games_columns = [col[1] for col in cursor.fetchall()]
                
                if 'steam_appid' in games_columns and 'appid' not in games_columns:
                    self.logger.info("Migrando coluna steam_appid para appid...")
                    cursor.execute("ALTER TABLE games RENAME COLUMN steam_appid TO appid")
                    self.logger.info("✓ Migração steam_appid → appid concluída")
                
                # Migração 2: Verificar estrutura da tabela game_dlls
                cursor.execute("PRAGMA table_info(game_dlls)")
                dll_columns = {col[1]: col for col in cursor.fetchall()}
                
                # Se tiver dll_version em vez de version, recriar a tabela
                if 'dll_version' in dll_columns and 'version' not in dll_columns:
                    self.logger.info("Migrando estrutura da tabela game_dlls...")
                    
                    # Backup dos dados
                    cursor.execute("SELECT * FROM game_dlls")
                    old_data = cursor.fetchall()
                    
                    # Recriar tabela
                    cursor.execute("DROP TABLE IF EXISTS game_dlls")
                    cursor.execute('''
                        CREATE TABLE game_dlls (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            game_id INTEGER NOT NULL,
                            dll_type TEXT NOT NULL,
                            dll_path TEXT NOT NULL,
                            dll_size INTEGER,
                            dll_hash TEXT,
                            version TEXT,
                            api_type TEXT,
                            FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE,
                            UNIQUE(game_id, dll_type)
                        )
                    ''')
                    
                    # Restaurar dados
                    for row in old_data:
                        # Obter version de dll_version ou version
                        try:
                            version_value = row['dll_version']
                        except (KeyError, IndexError):
                            try:
                                version_value = row['version']
                            except (KeyError, IndexError):
                                version_value = None
                        
                        # Obter api_type com fallback
                        try:
                            api_type_value = row['api_type']
                        except (KeyError, IndexError):
                            api_type_value = None
                        
                        cursor.execute("""
                            INSERT INTO game_dlls 
                            (game_id, dll_type, dll_path, dll_size, dll_hash, version, api_type)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            row['game_id'], row['dll_type'], row['dll_path'],
                            row['dll_size'], row['dll_hash'], 
                            version_value,
                            api_type_value
                        ))
                    
                    self.logger.info("✓ Migração da tabela game_dlls concluída")
                
                # Migração 3: Atualizar estrutura da tabela optiscaler_versions
                cursor.execute("PRAGMA table_info(optiscaler_versions)")
                version_columns = {col[1]: col for col in cursor.fetchall()}
                
                # Se tiver 'version' em vez de ter todas as colunas necessárias
                required_columns = ['tag_name', 'name', 'description', 'is_prerelease', 
                                   'download_url', 'file_size', 'local_path', 'is_downloaded']
                missing_columns = [col for col in required_columns if col not in version_columns]
                
                if missing_columns or 'version' in version_columns:
                    self.logger.info("Migrando estrutura da tabela optiscaler_versions...")
                    
                    # Backup dos dados se houver
                    cursor.execute("SELECT * FROM optiscaler_versions")
                    old_data = cursor.fetchall()
                    
                    # Recriar tabela
                    cursor.execute("DROP TABLE IF EXISTS optiscaler_versions")
                    cursor.execute('''
                        CREATE TABLE optiscaler_versions (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            tag_name TEXT NOT NULL UNIQUE,
                            name TEXT,
                            description TEXT,
                            release_date DATETIME,
                            is_prerelease INTEGER DEFAULT 0,
                            download_url TEXT,
                            file_size INTEGER,
                            local_path TEXT,
                            is_downloaded INTEGER DEFAULT 0,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    
                    self.logger.info("✓ Migração da tabela optiscaler_versions concluída")
                
        except Exception as e:
            self.logger.warning(f"Erro durante migração: {e}")
            # Se a migração falhar, continuar mesmo assim
    
    def execute(self, query: str, params: tuple = ()):
        """
        Executa uma query e retorna o cursor
        
        Args:
            query: Query SQL
            params: Parâmetros da query
        
        Returns:
            Cursor com resultados
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor
    
    def execute_many(self, query: str, params_list: list):
        """
        Executa múltiplas queries
        
        Args:
            query: Query SQL
            params_list: Lista de tuplas de parâmetros
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
