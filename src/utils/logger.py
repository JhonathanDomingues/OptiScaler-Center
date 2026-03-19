"""
Sistema de logging configurável para OptiScaler Center
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False

from utils.constants import LOGS_DIR, APP_NAME


def setup_logger(name: str = APP_NAME, level: str = 'INFO') -> logging.Logger:
    """
    Configura o sistema de logging com saída para console e arquivo
    
    Args:
        name: Nome do logger
        level: Nível de log (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Logger configurado
    """
    # Criar diretório de logs se não existir
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Criar logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Evitar duplicação de handlers
    if logger.handlers:
        return logger
    
    # Formato detalhado para arquivo
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para arquivo com rotação
    log_file = LOGS_DIR / f"{APP_NAME.lower().replace(' ', '_')}.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Usar colorlog se disponível
    if HAS_COLORLOG:
        console_formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(name)s%(reset)s - %(message)s',
            datefmt='%H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
    else:
        console_formatter = logging.Formatter(
            '%(levelname)-8s %(name)s - %(message)s'
        )
    
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Obtém um logger com o nome especificado
    
    Args:
        name: Nome do logger (geralmente __name__)
    
    Returns:
        Logger
    """
    return logging.getLogger(name)


class LoggerMixin:
    """
    Mixin para adicionar logging a classes
    
    Usage:
        class MyClass(LoggerMixin):
            def my_method(self):
                self.logger.info("Log message")
    """
    @property
    def logger(self) -> logging.Logger:
        """Retorna logger para a classe"""
        return get_logger(self.__class__.__name__)


def log_exception(logger: logging.Logger, exc: Exception, message: str = "Exception occurred"):
    """
    Loga uma exceção com traceback completo
    
    Args:
        logger: Logger a usar
        exc: Exceção capturada
        message: Mensagem adicional
    """
    logger.error(f"{message}: {exc}", exc_info=True)


def create_operation_log(operation: str, game_name: str = None, status: str = "started"):
    """
    Cria um log de operação estruturado
    
    Args:
        operation: Tipo de operação (install, uninstall, scan, etc)
        game_name: Nome do jogo (opcional)
        status: Status da operação
    
    Returns:
        Logger para a operação
    """
    logger = get_logger(f"operation.{operation}")
    
    game_info = f" [{game_name}]" if game_name else ""
    logger.info(f"{operation.upper()}{game_info} - {status}")
    
    return logger


# Logger global da aplicação
app_logger = logging.getLogger(APP_NAME)
