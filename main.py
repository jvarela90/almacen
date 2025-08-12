#!/usr/bin/env python3
"""
AlmacénPro v2.0 MVC - Sistema ERP/POS Completo
Archivo principal unificado con arquitectura MVC y Qt Designer

Características principales:
- Arquitectura MVC (Model-View-Controller)
- Interfaces con Qt Designer (.ui files)
- Controladores especializados
- Modelos de datos separados
- Managers de lógica de negocio

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

# Imports de configuración y base de datos
from config.settings import Settings
from database.manager import DatabaseManager

# Imports de managers (lógica de negocio)
from managers.user_manager import UserManager
from managers.product_manager import ProductManager
from managers.sales_manager import SalesManager
from managers.purchase_manager import PurchaseManager
from managers.provider_manager import ProviderManager
from managers.customer_manager import CustomerManager
from managers.financial_manager import FinancialManager
from managers.inventory_manager import InventoryManager
from managers.report_manager import ReportManager

# Managers adicionales
from managers.predictive_analysis_manager import PredictiveAnalysisManager
from managers.communication_manager import CommunicationManager
from managers.advanced_customer_manager import AdvancedCustomerManager
from managers.enterprise_user_manager import EnterpriseUserManager

# Imports de utilidades
from utils.backup_manager import BackupManager
from utils.notifications import NotificationManager
from utils.style_manager import StyleManager

# Imports de controladores MVC
from controllers.main_controller import MainController

# Diálogos que siguen siendo necesarios  
from controllers.login_controller import LoginController, show_login_dialog

# Configuración global de logging
def setup_logging():
    """Configurar sistema de logging MVC"""
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
    
    # Configurar logger principal
    logger = logging.getLogger(__name__)
    logger.info("=== INICIANDO ALMACÉNPRO V2.0 MVC UNIFICADO ===")
    logger.info(f"Archivo de log: {log_file}")
    
    return logger

class InitializationThread(QThread):
    """Hilo para inicialización de componentes MVC avanzada"""
    
    progress_updated = pyqtSignal(str, int)
    initialization_completed = pyqtSignal(dict)
    initialization_failed = pyqtSignal(str)
    
    def __init__(self, db_path=None):
        super().__init__()
        self.db_path = db_path
        self.logger = logging.getLogger(f"{__name__}.InitializationThread")
    
    def run(self):
        """Ejecutar inicialización MVC en hilo separado"""
        try:
            managers = {}
            
            # 1. Inicializar base de datos
            self.progress_updated.emit("Inicializando base de datos...", 10)
            db_manager = DatabaseManager(self.db_path)
            managers['database'] = db_manager
            
            # 2. Inicializar managers principales
            self.progress_updated.emit("Inicializando gestores principales...", 20)
            
            # User Manager
            managers['user'] = UserManager(db_manager)
            self.progress_updated.emit("Gestor de usuarios listo", 25)
            
            # Product Manager
            managers['product'] = ProductManager(db_manager)
            self.progress_updated.emit("Gestor de productos listo", 30)
            
            # Customer Manager
            managers['customer'] = CustomerManager(db_manager)
            self.progress_updated.emit("Gestor de clientes listo", 35)
            
            # Financial Manager
            managers['financial'] = FinancialManager(db_manager)
            self.progress_updated.emit("Gestor financiero listo", 38)
            
            # Sales Manager
            managers['sales'] = SalesManager(db_manager, managers['product'], managers['financial'])
            self.progress_updated.emit("Gestor de ventas listo", 40)
            
            # Purchase Manager  
            managers['purchase'] = PurchaseManager(db_manager, managers['product'])
            self.progress_updated.emit("Gestor de compras listo", 45)
            
            # Provider Manager
            managers['provider'] = ProviderManager(db_manager)
            self.progress_updated.emit("Gestor de proveedores listo", 47)
            
            # Inventory Manager
            managers['inventory'] = InventoryManager(db_manager)
            self.progress_updated.emit("Gestor de inventario listo", 48)
            
            # Report Manager
            managers['report'] = ReportManager(db_manager)
            self.progress_updated.emit("Gestor de reportes listo", 49)
            
            # 3. Inicializar managers avanzados
            self.progress_updated.emit("Inicializando gestores avanzados...", 50)
            
            # Advanced Customer Manager
            try:
                managers['advanced_customer'] = AdvancedCustomerManager(db_manager)
                self.progress_updated.emit("CRM avanzado listo", 55)
            except Exception as e:
                self.logger.warning(f"CRM avanzado no disponible: {e}")
            
            # Enterprise User Manager
            try:
                managers['enterprise_user'] = EnterpriseUserManager(db_manager)
                self.progress_updated.emit("Gestión empresarial lista", 60)
            except Exception as e:
                self.logger.warning(f"Gestión empresarial no disponible: {e}")
            
            # Predictive Analysis Manager
            try:
                managers['predictive_analysis'] = PredictiveAnalysisManager(db_manager)
                self.progress_updated.emit("Análisis predictivo listo", 65)
            except Exception as e:
                self.logger.warning(f"Análisis predictivo no disponible: {e}")
            
            # Communication Manager
            try:
                managers['communication'] = CommunicationManager(db_manager)
                self.progress_updated.emit("Gestor de comunicaciones listo", 70)
            except Exception as e:
                self.logger.warning(f"Comunicaciones no disponibles: {e}")
            
            # 4. Inicializar utilidades
            self.progress_updated.emit("Inicializando utilidades del sistema...", 75)
            
            # Backup Manager
            managers['backup'] = BackupManager(db_manager.db_path)
            self.progress_updated.emit("Sistema de backup listo", 80)
            
            # Notification Manager
            managers['notification'] = NotificationManager()
            self.progress_updated.emit("Sistema de notificaciones listo", 85)
            
            # Style Manager
            managers['style'] = StyleManager()
            self.progress_updated.emit("Gestor de estilos listo", 90)
            
            # 5. Verificación final
            self.progress_updated.emit("Verificando integridad del sistema...", 95)
            
            # Verificar managers críticos
            critical_managers = ['database', 'user', 'product', 'sales', 'customer']
            for manager_name in critical_managers:
                if manager_name not in managers:
                    raise Exception(f"Manager crítico no inicializado: {manager_name}")
            
            self.progress_updated.emit("Inicialización MVC completada", 100)
            self.logger.info("Todos los componentes MVC inicializados exitosamente")
            
            self.initialization_completed.emit(managers)
            
        except Exception as e:
            self.logger.error(f"Error durante inicialización MVC: {e}")
            self.logger.error(traceback.format_exc())
            self.initialization_failed.emit(str(e))

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
        """Inicializar componentes MVC del sistema"""
        self.init_thread = InitializationThread()
        
        # Conectar señales MVC  
        self.init_thread.progress_updated.connect(
            lambda message, progress: splash.showMessage(
                f"AlmacénPro v2.0 MVC\n\n{message}\n{progress}%",
                Qt.AlignCenter | Qt.AlignBottom,
                Qt.white
            )
        )
        
        self.init_thread.initialization_completed.connect(self.on_initialization_completed)
        self.init_thread.initialization_failed.connect(self.on_initialization_failed)
        
        # Iniciar hilo
        self.init_thread.start()
        
        return self.init_thread
    
    def on_initialization_completed(self, managers):
        """Callback cuando la inicialización MVC está completa"""
        self.managers = managers
        self.logger.info("Inicialización MVC completada exitosamente")
        
        # Proceder con login
        QTimer.singleShot(1000, self.show_login)
    
    def on_initialization_failed(self, error_message):
        """Callback cuando ocurre error en inicialización MVC"""
        self.logger.critical(f"Error crítico durante inicialización MVC: {error_message}")
        
        QMessageBox.critical(
            None,
            "Error Crítico MVC",
            f"No se pudo inicializar el sistema MVC:\n\n{error_message}\n\n"
            "Revise los logs para más detalles."
        )
        sys.exit(1)
    
    def show_login(self):
        """Mostrar diálogo de login MVC"""
        try:
            # Usar el nuevo LoginController MVC
            success, user_data = show_login_dialog(self.managers['user'])
            
            if success and user_data:
                self.current_user = user_data
                self.logger.info(f"Usuario autenticado MVC: {self.current_user['username']}")
                self.show_main_window()
            else:
                self.logger.info("Login cancelado por el usuario")
                sys.exit(0)
                
        except Exception as e:
            self.logger.error(f"Error en proceso de login MVC: {e}")
            QMessageBox.critical(
                None,
                "Error de Autenticación MVC",
                f"Error durante el proceso de login:\n{e}"
            )
            sys.exit(1)
    
    def show_main_window(self):
        """Mostrar ventana principal MVC"""
        try:
            # Usar MainController MVC en lugar de MainWindow directo
            self.main_controller = MainController(
                managers=self.managers,
                current_user=self.current_user
            )
            
            # Configurar eventos de aplicación MVC
            if hasattr(self.main_controller, 'logout_requested'):
                self.main_controller.logout_requested.connect(self.handle_logout)
            if hasattr(self.main_controller, 'app_exit_requested'):
                self.main_controller.app_exit_requested.connect(self.handle_exit)
            
            self.main_controller.show()
            self.logger.info("Ventana principal MVC mostrada exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error mostrando ventana principal MVC: {e}")
            QMessageBox.critical(
                None,
                "Error de Interfaz MVC",
                f"Error cargando la interfaz principal MVC:\n{e}"
            )
            sys.exit(1)
    
    def handle_logout(self):
        """Manejar cierre de sesión MVC"""
        self.logger.info(f"Cerrando sesión de usuario: {self.current_user['username']}")
        
        if hasattr(self, 'main_controller') and self.main_controller:
            self.main_controller.close()
        
        self.current_user = None
        self.show_login()
    
    def handle_exit(self):
        """Manejar salida de la aplicación MVC"""
        self.logger.info("Cerrando aplicación MVC")
        
        # Cerrar conexiones de base de datos
        if self.managers.get('database'):
            self.managers['database'].close_connection()
        
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