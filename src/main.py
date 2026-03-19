"""
OptiScaler Center - Entry Point
Gerenciador visual para instalação do OptiScaler em jogos
"""
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logger
from utils.constants import APP_NAME, APP_VERSION
from infrastructure.config.config_service import ConfigService
from infrastructure.database.db_service import DatabaseService
from presentation.main_window import MainWindow
from presentation.resources.app_icon import create_app_icon


def main():
    """Função principal da aplicação"""
    # Configurar logger
    logger = setup_logger()
    logger.info(f"Iniciando {APP_NAME} v{APP_VERSION}")
    
    # Inicializar serviços
    logger.info("Inicializando serviços...")
    config_service = ConfigService()
    db_service = DatabaseService()
    
    # Criar aplicação Qt
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    
    # Definir ícone da aplicação
    app.setWindowIcon(create_app_icon(64))
    
    # High DPI é habilitado por padrão no PyQt6
    
    # Carregar configurações
    theme = config_service.get('general.theme', 'dark')
    
    # Criar e exibir janela principal
    logger.info("Criando janela principal...")
    main_window = MainWindow(config_service, db_service)
    main_window.show()
    
    logger.info("Aplicação iniciada com sucesso")
    
    # Executar loop de eventos
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
