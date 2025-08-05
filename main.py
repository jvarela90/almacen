#!/usr/bin/env python3
"""
AlmacénPro v2.0 - Sistema ERP/POS Completo
Archivo principal de entrada al sistema

Desarrollado en Python 3.8+ con PyQt5
Sistema profesional de gestión para almacenes, kioscos, distribuidoras
"""

import sys
import os
import traceback
import logging
from pathlib import Path
from datetime import datetime

# Configurar el path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont

# Imports de módulos del proyecto
from config.settings import Settings
from database.manager import DatabaseManager
from managers.user_manager import UserManager
from managers.product_manager import ProductManager
from managers.sales_manager import SalesManager
from managers.purchase_manager import PurchaseManager
from managers.provider_manager import ProviderManager
from managers.report_manager import ReportManager
from utils.backup_manager import BackupManager
from utils.notifications import NotificationManager
from ui.main_window import MainWindow
from ui.dialogs.login_dialog import LoginDialog

# Configuración global de logging
def setup_logging():
    """Configurar sistema de logging"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"almacen_pro_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Configurar logger para errores críticos
    critical_logger = logging.getLogger('CRITICAL')
    critical_handler = logging.FileHandler(log_dir / "critical_errors.log", encoding='utf-8')
    critical_handler.setLevel(logging.CRITICAL)
    critical_logger.addHandler(critical_handler)
    
    return logging.getLogger(__name__)

class InitializationThread(QThread):
    """Hilo para inicialización asíncrona de componentes"""
    
    progress_updated = pyqtSignal(int, str)
    initialization_complete = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
    def run(self):
        """Ejecutar inicialización de componentes"""
        try:
            managers = {}
            
            # Paso 1: Base de datos
            self.progress_updated.emit(10, "Iniciando base de datos...")
            db_manager = DatabaseManager()
            managers['db'] = db_manager
            
            # Paso 2: Gestores de negocio
            self.progress_updated.emit(25, "Cargando gestores de usuario...")
            managers['user'] = UserManager(db_manager)
            
            self.progress_updated.emit(40, "Cargando gestores de productos...")
            managers['product'] = ProductManager(db_manager)
            
            self.progress_updated.emit(55, "Cargando gestores de ventas...")
            managers['sales'] = SalesManager(db_manager, managers['product'])
            
            self.progress_updated.emit(70, "Cargando gestores de compras...")
            managers['purchase'] = PurchaseManager(db_manager, managers['product'])
            
            self.progress_updated.emit(85, "Cargando proveedores y reportes...")
            managers['provider'] = ProviderManager(db_manager)
            managers['report'] = ReportManager(db_manager)
            
            # Paso 3: Utilidades
            self.progress_updated.emit(95, "Iniciando servicios auxiliares...")
            managers['backup'] = BackupManager(db_manager.db_path)
            managers['notification'] = NotificationManager()
            
            self.progress_updated.emit(100, "Inicialización completa")
            
            self.initialization_complete.emit(managers)
            
        except Exception as e:
            self.logger.error(f"Error durante inicialización: {e}")
            self.logger.error(traceback.format_exc())
            self.error_occurred.emit(str(e))

class AlmacenProApp:
    """Clase principal de la aplicación"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.app = None
        self.main_window = None
        self.managers = {}
        self.current_user = None
        
    def create_splash_screen(self):
        """Crear pantalla de splash"""
        splash_pix = QPixmap(400, 300)
        splash_pix.fill(Qt.white)
        
        splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
        splash.setMask(splash_pix.mask())
        splash.show()
        
        # Aplicar estilo
        splash.setStyleSheet("""
            QSplashScreen {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #2E86AB, stop:1 #A23B72);
                border: 2px solid #2E86AB;
                border-radius: 15px;
            }
        """)
        
        # Mostrar información de carga
        splash.showMessage(
            "AlmacénPro v2.0\n\nCargando sistema...",
            Qt.AlignCenter | Qt.AlignBottom,
            Qt.white
        )
        
        return splash
    
    def initialize_components(self, splash):
        """Inicializar componentes del sistema"""
        self.init_thread = InitializationThread()
        
        # Conectar señales
        self.init_thread.progress_updated.connect(
            lambda progress, message: splash.showMessage(
                f"AlmacénPro v2.0\n\n{message}\n{progress}%",
                Qt.AlignCenter | Qt.AlignBottom,
                Qt.white
            )
        )
        
        self.init_thread.initialization_complete.connect(self.on_initialization_complete)
        self.init_thread.error_occurred.connect(self.on_initialization_error)
        
        # Iniciar hilo
        self.init_thread.start()
        
        return self.init_thread
    
    def on_initialization_complete(self, managers):
        """Callback cuando la inicialización está completa"""
        self.managers = managers
        self.logger.info("Inicialización de componentes completada exitosamente")
        
        # Proceder con login
        QTimer.singleShot(1000, self.show_login)
    
    def on_initialization_error(self, error_message):
        """Callback cuando ocurre error en inicialización"""
        self.logger.critical(f"Error crítico durante inicialización: {error_message}")
        
        QMessageBox.critical(
            None,
            "Error Crítico",
            f"No se pudo inicializar el sistema:\n\n{error_message}\n\n"
            "Revise los logs para más detalles."
        )
        sys.exit(1)
    
    def show_login(self):
        """Mostrar diálogo de login"""
        try:
            login_dialog = LoginDialog(self.managers['user'])
            
            if login_dialog.exec_() == login_dialog.Accepted:
                self.current_user = login_dialog.get_authenticated_user()
                self.logger.info(f"Usuario autenticado: {self.current_user['username']}")
                self.show_main_window()
            else:
                self.logger.info("Login cancelado por el usuario")
                sys.exit(0)
                
        except Exception as e:
            self.logger.error(f"Error en proceso de login: {e}")
            QMessageBox.critical(
                None,
                "Error de Autenticación",
                f"Error durante el proceso de login:\n{e}"
            )
            sys.exit(1)
    
    def show_main_window(self):
        """Mostrar ventana principal"""
        try:
            self.main_window = MainWindow(
                managers=self.managers,
                current_user=self.current_user
            )
            
            # Configurar eventos de aplicación
            self.main_window.logout_requested.connect(self.handle_logout)
            self.main_window.app_exit_requested.connect(self.handle_exit)
            
            self.main_window.show()
            self.logger.info("Ventana principal mostrada exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error mostrando ventana principal: {e}")
            QMessageBox.critical(
                None,
                "Error de Interfaz",
                f"Error cargando la interfaz principal:\n{e}"
            )
            sys.exit(1)
    
    def handle_logout(self):
        """Manejar cierre de sesión"""
        self.logger.info(f"Cerrando sesión de usuario: {self.current_user['username']}")
        
        if self.main_window:
            self.main_window.close()
        
        self.current_user = None
        self.show_login()
    
    def handle_exit(self):
        """Manejar salida de la aplicación"""
        self.logger.info("Cerrando aplicación")
        
        # Cerrar conexiones de base de datos
        if self.managers.get('db'):
            self.managers['db'].close_connection()
        
        # Detener servicios
        if self.managers.get('backup'):
            self.managers['backup'].stop_automatic_backup()
        
        sys.exit(0)
    
    def run(self):
        """Ejecutar la aplicación"""
        try:
            # Crear aplicación Qt
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("AlmacénPro")
            self.app.setApplicationVersion("2.0")
            self.app.setOrganizationName("AlmacénPro Systems")
            
            # Configurar fuente global
            font = QFont("Segoe UI", 10)
            self.app.setFont(font)
            
            # Configurar estilo global
            self.app.setStyleSheet(self.load_global_styles())
            
            # Mostrar splash screen
            splash = self.create_splash_screen()
            
            # Inicializar componentes en hilo separado
            init_thread = self.initialize_components(splash)
            
            # Cerrar splash después de inicialización
            def close_splash():
                splash.close()
            
            init_thread.finished.connect(close_splash)
            
            # Ejecutar aplicación
            return self.app.exec_()
            
        except Exception as e:
            self.logger.critical(f"Error crítico en aplicación: {e}")
            self.logger.critical(traceback.format_exc())
            
            if hasattr(self, 'app') and self.app:
                QMessageBox.critical(
                    None,
                    "Error Crítico",
                    f"Error inesperado en la aplicación:\n\n{e}\n\n"
                    "La aplicación se cerrará."
                )
            
            return 1
    
    def load_global_styles(self):
        """Cargar estilos globales CSS"""
        return """
        QWidget {
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10pt;
        }
        
        QMainWindow {
            background-color: #f5f5f5;
        }
        
        QMenuBar {
            background-color: #2E86AB;
            color: white;
            border: none;
            padding: 4px;
        }
        
        QMenuBar::item {
            background-color: transparent;
            padding: 8px 12px;
            border-radius: 4px;
        }
        
        QMenuBar::item:selected {
            background-color: rgba(255, 255, 255, 0.2);
        }
        
        QStatusBar {
            background-color: #34495e;
            color: white;
            border: none;
        }
        
        QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #2980b9;
        }
        
        QPushButton:pressed {
            background-color: #21618c;
        }
        
        QPushButton:disabled {
            background-color: #bdc3c7;
            color: #7f8c8d;
        }
        
        QLineEdit, QTextEdit, QComboBox {
            border: 2px solid #bdc3c7;
            border-radius: 4px;
            padding: 8px;
            background-color: white;
        }
        
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
            border-color: #3498db;
        }
        
        QTableView {
            gridline-color: #ecf0f1;
            background-color: white;
            alternate-background-color: #f8f9fa;
            selection-background-color: #3498db;
            selection-color: white;
        }
        
        QHeaderView::section {
            background-color: #34495e;
            color: white;
            padding: 8px;
            border: none;
            font-weight: bold;
        }
        """

def main():
    """Función principal"""
    try:
        app = AlmacenProApp()
        return app.run()
        
    except KeyboardInterrupt:
        print("\nAplicación interrumpida por el usuario")
        return 0
        
    except Exception as e:
        print(f"Error inesperado: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())