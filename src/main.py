"""
OptiScaler Center - Entry Point
Gerenciador visual para instalação do OptiScaler em jogos
"""
import sys
import os
from pathlib import Path
import traceback

# Detectar se está rodando como executável PyInstaller
if getattr(sys, 'frozen', False):
    # PyInstaller empacota os módulos em sys._MEIPASS (_internal/)
    # Não manipulamos sys.path — PyInstaller já o configura corretamente
    # application_path = diretório onde o executável está
    application_path = Path(sys.executable).parent
    
    # Garantir que _MEIPASS está no path (PyInstaller faz isso automaticamente,
    # mas adicionamos explicitamente para ambientes AppImage que podem diferir)
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass and str(meipass) not in sys.path:
        sys.path.insert(0, str(meipass))
else:
    # Rodando como script Python normal
    application_path = Path(__file__).parent.parent
    sys.path.insert(0, str(Path(__file__).parent))

# Mudar para o diretório da aplicação apenas em modo script (evita problemas no AppImage)
if not getattr(sys, 'frozen', False):
    os.chdir(str(application_path))

try:
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from PyQt6.QtCore import Qt
    
    from utils.logger import setup_logger
    from utils.constants import APP_NAME, APP_VERSION
    from infrastructure.config.config_service import ConfigService
    from infrastructure.database.db_service import DatabaseService
    from presentation.main_window import MainWindow
    from presentation.resources.app_icon import create_app_icon
except Exception as e:
    # Se falhar ao importar, mostrar erro
    print(f"Erro ao importar módulos: {e}")
    print(f"Path: {sys.path}")
    print(f"Application path: {application_path}")
    traceback.print_exc()
    sys.exit(1)


def main():
    """Função principal da aplicação"""
    try:
        # Configurar logger
        logger = setup_logger()
        logger.info(f"Iniciando {APP_NAME} v{APP_VERSION}")
        logger.info(f"Diretório da aplicação: {application_path}")
        logger.info(f"Executável congelado: {getattr(sys, 'frozen', False)}")
        
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
            
    except Exception as e:
        # Capturar qualquer erro e mostrar ao usuário
        error_msg = f"Erro ao iniciar a aplicação:\n\n{str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        
        try:
            # Tentar mostrar caixa de diálogo de erro
            app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
            QMessageBox.critical(None, "Erro Fatal", error_msg)
        except:
            # Se falhar, apenas imprimir
            pass
        
        sys.exit(1)
