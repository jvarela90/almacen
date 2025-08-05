#!/usr/bin/env python3
"""
AlmacénPro - Sistema ERP/POS Completo
Punto de entrada principal de la aplicación

Desarrollado en Python con arquitectura modular
"""

import sys
import os
import logging
from pathlib import Path

# Agregar directorio raíz al path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('almacen_pro.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def check_dependencies():
    """Verificar dependencias necesarias"""
    required_modules = ['PyQt5', 'sqlite3', 'json', 'datetime']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        logger.error(f"Módulos faltantes: {', '.join(missing_modules)}")
        print(f"Error: Instale los módulos faltantes: {', '.join(missing_modules)}")
        print("Ejecute: pip install PyQt5")
        return False
    
    return True

def create_directories():
    """Crear directorios necesarios"""
    directories = [
        'data',
        'backups',
        'logs',
        'temp',
        'exports'
    ]
    
    for directory in directories:
        dir_path = ROOT_DIR / directory
        dir_path.mkdir(exist_ok=True)
        logger.info(f"Directorio verificado: {dir_path}")

def main():
    """Función principal"""
    logger.info("=" * 50)
    logger.info("Iniciando AlmacénPro v2.0")
    logger.info("=" * 50)
    
    # Verificar dependencias
    if not check_dependencies():
        sys.exit(1)
    
    # Crear directorios necesarios
    create_directories()
    
    try:
        # Importar PyQt5 después de verificar dependencias
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QIcon, QFont
        
        # Importar configuraciones
        from config.settings import AppSettings
        
        # Importar ventana principal
        from ui.main_window import MainWindow
        
        # Crear aplicación
        app = QApplication(sys.argv)
        app.setApplicationName("AlmacénPro")
        app.setApplicationVersion("2.0")
        app.setOrganizationName("AlmacénPro Solutions")
        
        # Configurar estilo
        app.setStyle('Fusion')
        
        # Configurar fuente por defecto
        font = QFont("Segoe UI", 9)
        app.setFont(font)
        
        # Cargar configuraciones
        settings = AppSettings()
        
        # Crear y mostrar ventana principal
        window = MainWindow(settings)
        
        # Aplicar tema si está configurado
        if settings.get('ui_theme') == 'dark':
            apply_dark_theme(app)
        
        window.show()
        
        logger.info("Aplicación iniciada correctamente")
        
        # Ejecutar aplicación
        exit_code = app.exec_()
        
        logger.info(f"Aplicación finalizada con código: {exit_code}")
        sys.exit(exit_code)
        
    except ImportError as e:
        logger.error(f"Error importando módulos: {e}")
        print(f"Error: No se pudieron importar los módulos necesarios: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        print(f"Error inesperado: {e}")
        sys.exit(1)

def apply_dark_theme(app):
    """Aplicar tema oscuro"""
    dark_stylesheet = """
    QMainWindow {
        background-color: #2b2b2b;
        color: #ffffff;
    }
    QWidget {
        background-color: #2b2b2b;
        color: #ffffff;
    }
    QPushButton {
        background-color: #3c3c3c;
        border: 1px solid #555555;
        padding: 8px;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #4c4c4c;
    }
    QPushButton:pressed {
        background-color: #1c1c1c;
    }
    QLineEdit, QTextEdit, QComboBox {
        background-color: #3c3c3c;
        border: 1px solid #555555;
        padding: 5px;
        border-radius: 3px;
    }
    QTableWidget {
        background-color: #3c3c3c;
        alternate-background-color: #454545;
    }
    QHeaderView::section {
        background-color: #555555;
        padding: 4px;
        border: 1px solid #777777;
    }
    """
    app.setStyleSheet(dark_stylesheet)

if __name__ == '__main__':
    main()