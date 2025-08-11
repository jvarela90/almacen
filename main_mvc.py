#!/usr/bin/env python3
"""
AlmacénPro v2.0 MVC - Sistema ERP/POS Completo
Archivo principal con arquitectura MVC y Qt Designer

Migración completa a:
- Arquitectura MVC (Model-View-Controller)
- Interfaces con Qt Designer (.ui files)
- Controladores especializados
- Modelos de datos separados

Desarrollado en Python 3.8+ con PyQt5
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
from ui.dialogs.login_dialog import LoginDialog

# Configuración global de logging
def setup_logging():
    """Configurar sistema de logging"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"almacen_pro_mvc_{datetime.now().strftime('%Y%m%d')}.log"
    
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
    logger.info("=== INICIANDO ALMACÉNPRO V2.0 MVC ===")
    logger.info(f"Archivo de log: {log_file}")
    
    return logger

class InitializationThread(QThread):
    """Hilo para inicialización de componentes pesados"""
    
    progress_updated = pyqtSignal(str, int)
    initialization_completed = pyqtSignal(dict)
    initialization_failed = pyqtSignal(str)
    
    def __init__(self, db_path=None):
        super().__init__()
        self.db_path = db_path
        self.logger = logging.getLogger(f"{__name__}.InitializationThread")
    
    def run(self):
        """Ejecutar inicialización en hilo separado"""
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
            
            # Sales Manager
            managers['sales'] = SalesManager(db_manager, managers['product'])
            self.progress_updated.emit("Gestor de ventas listo", 40)
            
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
                managers['predictive'] = PredictiveAnalysisManager(db_manager)
                managers['predictive'].create_prediction_tables()
                self.progress_updated.emit("Análisis predictivo listo", 65)
            except Exception as e:
                self.logger.warning(f"Análisis predictivo no disponible: {e}")
            
            # 4. Otros managers
            self.progress_updated.emit("Inicializando otros gestores...", 70)
            
            managers['purchase'] = PurchaseManager(db_manager, managers['product'])
            managers['provider'] = ProviderManager(db_manager)
            managers['financial'] = FinancialManager(db_manager)
            managers['inventory'] = InventoryManager(db_manager)
            managers['report'] = ReportManager(db_manager)
            
            self.progress_updated.emit("Gestores básicos listos", 80)
            
            # 5. Utilidades
            self.progress_updated.emit("Inicializando utilidades...", 85)
            
            managers['backup'] = BackupManager(db_manager.db_path)
            managers['notification'] = NotificationManager()
            
            # Communication Manager
            try:
                managers['communication'] = CommunicationManager(db_manager)
                self.progress_updated.emit("Sistema de comunicación listo", 90)
            except Exception as e:
                self.logger.warning(f"Sistema de comunicación no disponible: {e}")
            
            # 6. Finalizar
            self.progress_updated.emit("Finalizando inicialización...", 95)
            
            # Verificar integridad de managers críticos
            critical_managers = ['database', 'user', 'product', 'customer', 'sales']
            for manager_name in critical_managers:
                if manager_name not in managers:
                    raise Exception(f"Manager crítico {manager_name} no fue inicializado")
            
            self.progress_updated.emit("Inicialización completada", 100)
            self.initialization_completed.emit(managers)
            
            self.logger.info("Inicialización de managers completada exitosamente")
            
        except Exception as e:
            error_msg = f"Error en inicialización: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            self.initialization_failed.emit(error_msg)

class AlmacenProMVCApp:
    """Aplicación principal con arquitectura MVC"""
    
    def __init__(self):
        self.app = None
        self.splash = None
        self.main_controller = None
        self.managers = {}
        self.current_user = None
        self.init_thread = None
        
        self.logger = setup_logging()
        
        # Configurar aplicación Qt
        self.setup_application()
    
    def setup_application(self):
        """Configurar aplicación Qt"""
        try:
            # Crear aplicación
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("AlmacénPro MVC")
            self.app.setApplicationVersion("2.0")
            self.app.setOrganizationName("AlmacénPro")
            
            # Configurar fuente por defecto
            font = QFont("Segoe UI", 9)
            self.app.setFont(font)
            
            # Aplicar tema por defecto
            StyleManager.apply_theme(self.app, "default")
            
            self.logger.info("Aplicación Qt configurada")
            
        except Exception as e:
            self.logger.error(f"Error configurando aplicación: {e}")
            raise
    
    def show_splash(self):
        """Mostrar splash screen"""
        try:
            # Crear splash screen
            splash_pixmap = QPixmap(400, 300)
            splash_pixmap.fill(Qt.white)
            
            self.splash = QSplashScreen(splash_pixmap)
            self.splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.SplashScreen)
            self.splash.show()
            
            # Mensaje inicial
            self.splash.showMessage("Inicializando AlmacénPro v2.0 MVC...", 
                                   Qt.AlignBottom | Qt.AlignCenter, Qt.black)
            
            self.app.processEvents()
            
        except Exception as e:
            self.logger.warning(f"No se pudo mostrar splash screen: {e}")
    
    def initialize_system(self):
        """Inicializar sistema completo"""
        try:
            self.show_splash()
            
            # Configurar settings
            settings = Settings()
            db_path = settings.get_database_path()
            
            # Inicializar en hilo separado
            self.init_thread = InitializationThread(db_path)
            self.init_thread.progress_updated.connect(self.update_splash)
            self.init_thread.initialization_completed.connect(self.on_initialization_completed)
            self.init_thread.initialization_failed.connect(self.on_initialization_failed)
            
            self.init_thread.start()
            
        except Exception as e:
            self.logger.error(f"Error en inicialización del sistema: {e}")
            self.show_critical_error("Error de Inicialización", str(e))
    
    def update_splash(self, message: str, progress: int):
        """Actualizar splash screen con progreso"""
        if self.splash:
            self.splash.showMessage(f"{message} ({progress}%)", 
                                  Qt.AlignBottom | Qt.AlignCenter, Qt.black)
            self.app.processEvents()
    
    def on_initialization_completed(self, managers: dict):
        """Manejar inicialización completada"""
        try:
            self.managers = managers
            self.logger.info("Managers inicializados correctamente")
            
            # Cerrar splash
            if self.splash:
                self.splash.close()
            
            # Mostrar login
            self.show_login()
            
        except Exception as e:
            self.logger.error(f"Error completando inicialización: {e}")
            self.show_critical_error("Error", str(e))
    
    def on_initialization_failed(self, error_message: str):
        """Manejar fallo en inicialización"""
        if self.splash:
            self.splash.close()
        
        self.show_critical_error("Error de Inicialización", error_message)
    
    def show_login(self):
        """Mostrar diálogo de login"""
        try:
            # Verificar que el user manager esté disponible
            user_manager = self.managers.get('user')
            if not user_manager:
                raise Exception("Gestor de usuarios no disponible")
            
            # Crear y mostrar diálogo de login
            login_dialog = LoginDialog(user_manager, parent=None)
            
            result = login_dialog.exec_()
            
            if result == LoginDialog.Accepted:
                # Login exitoso
                self.current_user = login_dialog.get_logged_user()
                self.logger.info(f"Usuario logueado: {self.current_user.get('username', 'unknown')}")
                
                # Inicializar interfaz principal
                self.initialize_main_interface()
            else:
                # Login cancelado o fallido
                self.logger.info("Login cancelado por el usuario")
                self.app.quit()
                
        except Exception as e:
            self.logger.error(f"Error en login: {e}")
            self.show_critical_error("Error de Autenticación", str(e))
    
    def initialize_main_interface(self):
        """Inicializar interfaz principal con controlador MVC"""
        try:
            # Crear controlador principal
            self.main_controller = MainController(self.managers, self.current_user)
            
            # Conectar señales de aplicación
            self.main_controller.application_closing.connect(self.on_application_closing)
            self.main_controller.user_logged_out.connect(self.on_user_logged_out)
            
            # Mostrar ventana principal
            self.main_controller.show()
            
            self.logger.info("Interfaz principal inicializada (arquitectura MVC)")
            
        except Exception as e:
            self.logger.error(f"Error inicializando interfaz principal: {e}")
            self.show_critical_error("Error de Interfaz", str(e))
    
    def on_application_closing(self):
        """Manejar cierre de aplicación"""
        try:
            self.logger.info("Cerrando aplicación...")
            
            # Limpiar recursos si es necesario
            if self.init_thread and self.init_thread.isRunning():
                self.init_thread.quit()
                self.init_thread.wait()
            
            # Guardar configuraciones finales si es necesario
            
            self.logger.info("Aplicación cerrada correctamente")
            
        except Exception as e:
            self.logger.error(f"Error cerrando aplicación: {e}")
    
    def on_user_logged_out(self):
        """Manejar logout de usuario"""
        try:
            self.logger.info("Usuario cerró sesión")
            
            # Cerrar controlador principal
            if self.main_controller:
                self.main_controller.close()
            
            # Limpiar usuario actual
            self.current_user = None
            
            # Mostrar login nuevamente
            self.show_login()
            
        except Exception as e:
            self.logger.error(f"Error en logout: {e}")
    
    def show_critical_error(self, title: str, message: str):
        """Mostrar error crítico y salir"""
        self.logger.critical(f"Error crítico: {message}")
        
        if self.splash:
            self.splash.close()
        
        QMessageBox.critical(None, title, f"{message}\n\nLa aplicación se cerrará.")
        
        if self.app:
            self.app.quit()
        
        sys.exit(1)
    
    def run(self):
        """Ejecutar aplicación"""
        try:
            # Inicializar sistema
            self.initialize_system()
            
            # Ejecutar loop de aplicación
            return self.app.exec_()
            
        except Exception as e:
            self.logger.error(f"Error ejecutando aplicación: {e}")
            self.logger.error(traceback.format_exc())
            self.show_critical_error("Error Fatal", str(e))
            return 1

def main():
    """Función principal"""
    try:
        # Crear y ejecutar aplicación
        app = AlmacenProMVCApp()
        return app.run()
        
    except KeyboardInterrupt:
        print("\nAplicación interrumpida por el usuario")
        return 0
    except Exception as e:
        print(f"Error fatal: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())