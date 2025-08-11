"""
Controlador Principal - AlmacénPro v2.0 MVC
Controlador principal que gestiona la ventana principal y coordina todos los módulos
"""

import os
import logging
import sys
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from .base_controller import BaseController
from .sales_controller import SalesController
from .customers_controller import CustomersController

logger = logging.getLogger(__name__)

class MainController(QMainWindow):
    """Controlador principal de la aplicación"""
    
    # Señales de aplicación
    application_closing = pyqtSignal()
    user_logged_out = pyqtSignal()
    module_changed = pyqtSignal(str)
    
    def __init__(self, managers: Dict, current_user: Dict, parent=None):
        super().__init__(parent)
        
        # Referencias principales
        self.managers = managers
        self.current_user = current_user
        
        # Controladores de módulos
        self.module_controllers = {}
        self.current_module_controller = None
        
        # Estado de la aplicación
        self.is_initialized = False
        self.is_closing = False
        
        # Setup logging
        self.logger = logging.getLogger(__name__ + ".MainController")
        
        # Configurar interfaz principal
        self.setup_main_window()
        self.create_menu_bar()
        self.create_toolbar()
        self.create_status_bar()
        
        # Crear área de contenido
        self.setup_content_area()
        
        # Inicializar módulos
        self.initialize_modules()
        
        # Configurar shortcuts globales
        self.setup_global_shortcuts()
        
        # Estado inicial
        self.load_initial_module()
        
        self.is_initialized = True
        self.logger.info("Controlador principal inicializado")
    
    def setup_main_window(self):
        """Configurar ventana principal"""
        self.setWindowTitle(f"AlmacénPro v2.0 - {self.current_user.get('nombre_completo', 'Usuario')}")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        # Centrar ventana
        self.center_window()
        
        # Icono de aplicación (si existe)
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'views', 'resources', 'icons', 'app_icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Aplicar estilos
        self.apply_main_window_styles()
    
    def center_window(self):
        """Centrar ventana en la pantalla"""
        frame_gm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        center_point = QApplication.desktop().screenGeometry(screen).center()
        frame_gm.moveCenter(center_point)
        self.move(frame_gm.topLeft())
    
    def apply_main_window_styles(self):
        """Aplicar estilos a la ventana principal"""
        from utils.style_manager import StyleManager
        try:
            StyleManager.apply_default_styles(self)
        except ImportError:
            # Estilos básicos si no existe StyleManager
            self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            
            QMenuBar {
                background-color: #2c3e50;
                color: white;
                font-weight: bold;
            }
            
            QMenuBar::item:selected {
                background-color: #34495e;
            }
            
            QToolBar {
                background-color: #ecf0f1;
                border: none;
                spacing: 4px;
                padding: 4px;
            }
            
            QStatusBar {
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
            }
            """)
    
    def create_menu_bar(self):
        """Crear barra de menú"""
        menubar = self.menuBar()
        
        # Menú Archivo
        file_menu = menubar.addMenu('&Archivo')
        
        # Nueva Venta
        new_sale_action = QAction('&Nueva Venta', self)
        new_sale_action.setShortcut('Ctrl+N')
        new_sale_action.setStatusTip('Iniciar nueva venta')
        new_sale_action.triggered.connect(lambda: self.switch_to_module('sales'))
        file_menu.addAction(new_sale_action)
        
        file_menu.addSeparator()
        
        # Salir
        exit_action = QAction('&Salir', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Salir de la aplicación')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menú Clientes
        customers_menu = menubar.addMenu('&Clientes')
        
        # Gestión de Clientes
        manage_customers_action = QAction('&Gestionar Clientes', self)
        manage_customers_action.setShortcut('Ctrl+G')
        manage_customers_action.setStatusTip('Gestionar clientes')
        manage_customers_action.triggered.connect(lambda: self.switch_to_module('customers'))
        customers_menu.addAction(manage_customers_action)
        
        # Nuevo Cliente
        new_customer_action = QAction('&Nuevo Cliente', self)
        new_customer_action.setShortcut('Ctrl+Shift+N')
        new_customer_action.setStatusTip('Crear nuevo cliente')
        new_customer_action.triggered.connect(self.create_new_customer)
        customers_menu.addAction(new_customer_action)
        
        # Menú Inventario
        inventory_menu = menubar.addMenu('&Inventario')
        
        # Gestión de Productos
        manage_products_action = QAction('&Gestionar Productos', self)
        manage_products_action.setShortcut('Ctrl+P')
        manage_products_action.setStatusTip('Gestionar productos')
        manage_products_action.triggered.connect(lambda: self.switch_to_module('inventory'))
        inventory_menu.addAction(manage_products_action)
        
        # Menú Reportes
        reports_menu = menubar.addMenu('&Reportes')
        
        # Reporte de Ventas
        sales_report_action = QAction('&Reporte de Ventas', self)
        sales_report_action.setStatusTip('Ver reporte de ventas')
        sales_report_action.triggered.connect(lambda: self.switch_to_module('reports'))
        reports_menu.addAction(sales_report_action)
        
        # Menú Herramientas
        tools_menu = menubar.addMenu('&Herramientas')
        
        # Configuraciones
        settings_action = QAction('&Configuraciones', self)
        settings_action.setStatusTip('Configurar aplicación')
        settings_action.triggered.connect(self.open_settings)
        tools_menu.addAction(settings_action)
        
        # Backup
        backup_action = QAction('&Backup', self)
        backup_action.setStatusTip('Crear backup de datos')
        backup_action.triggered.connect(self.create_backup)
        tools_menu.addAction(backup_action)
        
        # Menú Ayuda
        help_menu = menubar.addMenu('A&yuda')
        
        # Acerca de
        about_action = QAction('&Acerca de', self)
        about_action.setStatusTip('Acerca de AlmacénPro')
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Crear barra de herramientas"""
        toolbar = self.addToolBar('Principal')
        toolbar.setObjectName('main_toolbar')
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        
        # Botón Nueva Venta
        sales_action = toolbar.addAction('🛒 Ventas')
        sales_action.setStatusTip('Módulo de ventas')
        sales_action.triggered.connect(lambda: self.switch_to_module('sales'))
        
        # Botón Clientes
        customers_action = toolbar.addAction('👥 Clientes')
        customers_action.setStatusTip('Módulo de clientes')
        customers_action.triggered.connect(lambda: self.switch_to_module('customers'))
        
        # Botón Inventario
        inventory_action = toolbar.addAction('📦 Inventario')
        inventory_action.setStatusTip('Módulo de inventario')
        inventory_action.triggered.connect(lambda: self.switch_to_module('inventory'))
        
        # Botón Reportes
        reports_action = toolbar.addAction('📊 Reportes')
        reports_action.setStatusTip('Módulo de reportes')
        reports_action.triggered.connect(lambda: self.switch_to_module('reports'))
        
        toolbar.addSeparator()
        
        # Información del usuario
        user_info = f"Usuario: {self.current_user.get('nombre_completo', 'Usuario')}"
        user_label = QLabel(user_info)
        user_label.setStyleSheet("margin: 5px; font-weight: bold;")
        toolbar.addWidget(user_label)
        
        toolbar.addSeparator()
        
        # Botón Cerrar Sesión
        logout_action = toolbar.addAction('🚪 Salir')
        logout_action.setStatusTip('Cerrar sesión')
        logout_action.triggered.connect(self.logout)
    
    def create_status_bar(self):
        """Crear barra de estado"""
        self.status_bar = self.statusBar()
        
        # Mensaje inicial
        self.status_bar.showMessage('Listo')
        
        # Etiquetas permanentes
        self.status_user_label = QLabel(f"Usuario: {self.current_user.get('username', 'Usuario')}")
        self.status_bar.addPermanentWidget(self.status_user_label)
        
        self.status_time_label = QLabel()
        self.status_bar.addPermanentWidget(self.status_time_label)
        
        # Timer para actualizar hora
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_status_time)
        self.time_timer.start(1000)  # Actualizar cada segundo
        self.update_status_time()
    
    def update_status_time(self):
        """Actualizar hora en status bar"""
        from datetime import datetime
        current_time = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        self.status_time_label.setText(current_time)
    
    def setup_content_area(self):
        """Configurar área de contenido principal"""
        # Widget central
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Layout principal
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Stack para los diferentes módulos
        self.module_stack = QStackedWidget()
        self.main_layout.addWidget(self.module_stack)
    
    def initialize_modules(self):
        """Inicializar todos los módulos"""
        try:
            # Módulo de Ventas
            self.initialize_sales_module()
            
            # Módulo de Clientes
            self.initialize_customers_module()
            
            # Otros módulos se pueden agregar aquí
            # self.initialize_inventory_module()
            # self.initialize_reports_module()
            
            self.logger.info("Módulos inicializados exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error inicializando módulos: {e}")
            self.show_critical_error("Error de Inicialización", 
                                   f"Error inicializando módulos: {str(e)}")
    
    def initialize_sales_module(self):
        """Inicializar módulo de ventas"""
        try:
            sales_controller = SalesController(self.managers, self.current_user, self)
            sales_controller.initialize()
            
            # Conectar señales
            sales_controller.sale_completed.connect(self.on_sale_completed)
            sales_controller.product_added.connect(self.on_product_added_to_cart)
            
            self.module_controllers['sales'] = sales_controller
            self.module_stack.addWidget(sales_controller)
            
            self.logger.info("Módulo de ventas inicializado")
            
        except Exception as e:
            self.logger.error(f"Error inicializando módulo de ventas: {e}")
            raise
    
    def initialize_customers_module(self):
        """Inicializar módulo de clientes"""
        try:
            customers_controller = CustomersController(self.managers, self.current_user, self)
            customers_controller.initialize()
            
            # Conectar señales
            customers_controller.customer_created.connect(self.on_customer_created)
            customers_controller.customer_updated.connect(self.on_customer_updated)
            customers_controller.customer_selected_for_sale.connect(self.on_customer_selected_for_sale)
            
            self.module_controllers['customers'] = customers_controller
            self.module_stack.addWidget(customers_controller)
            
            self.logger.info("Módulo de clientes inicializado")
            
        except Exception as e:
            self.logger.error(f"Error inicializando módulo de clientes: {e}")
            raise
    
    def load_initial_module(self):
        """Cargar módulo inicial"""
        # Por defecto, cargar módulo de ventas
        self.switch_to_module('sales')
    
    def setup_global_shortcuts(self):
        """Configurar atajos globales de la aplicación"""
        # F1 - Ayuda
        QShortcut(QKeySequence("F1"), self, self.show_help)
        
        # F11 - Pantalla completa
        QShortcut(QKeySequence("F11"), self, self.toggle_fullscreen)
        
        # Alt+F4 - Cerrar
        QShortcut(QKeySequence("Alt+F4"), self, self.close)
        
        # Ctrl+1, Ctrl+2, etc. - Cambiar módulos
        QShortcut(QKeySequence("Ctrl+1"), self, lambda: self.switch_to_module('sales'))
        QShortcut(QKeySequence("Ctrl+2"), self, lambda: self.switch_to_module('customers'))
        QShortcut(QKeySequence("Ctrl+3"), self, lambda: self.switch_to_module('inventory'))
        QShortcut(QKeySequence("Ctrl+4"), self, lambda: self.switch_to_module('reports'))
    
    # === MÉTODOS PÚBLICOS ===
    
    def switch_to_module(self, module_name: str):
        """Cambiar a un módulo específico"""
        try:
            if module_name in self.module_controllers:
                controller = self.module_controllers[module_name]
                self.module_stack.setCurrentWidget(controller)
                self.current_module_controller = controller
                
                # Actualizar status
                module_display_names = {
                    'sales': 'Punto de Venta',
                    'customers': 'Gestión de Clientes',
                    'inventory': 'Inventario',
                    'reports': 'Reportes'
                }
                
                display_name = module_display_names.get(module_name, module_name)
                self.status_bar.showMessage(f"Módulo activo: {display_name}")
                
                # Emitir señal
                self.module_changed.emit(module_name)
                
                self.logger.info(f"Cambiado a módulo: {module_name}")
            else:
                self.logger.warning(f"Módulo no encontrado: {module_name}")
                self.show_warning("Módulo No Disponible", 
                                f"El módulo '{module_name}' no está disponible.")
                
        except Exception as e:
            self.logger.error(f"Error cambiando a módulo {module_name}: {e}")
            self.show_error("Error", f"Error cambiando de módulo: {str(e)}")
    
    def get_current_module_controller(self):
        """Obtener controlador del módulo actual"""
        return self.current_module_controller
    
    def show_status_message(self, message: str, timeout: int = 3000):
        """Mostrar mensaje temporal en status bar"""
        self.status_bar.showMessage(message, timeout)
    
    def set_loading_state(self, loading: bool):
        """Establecer estado de carga global"""
        if loading:
            QApplication.setOverrideCursor(Qt.WaitCursor)
        else:
            QApplication.restoreOverrideCursor()
    
    # === SLOTS DE ACCIONES ===
    
    @pyqtSlot()
    def create_new_customer(self):
        """Crear nuevo cliente desde menú"""
        self.switch_to_module('customers')
        if 'customers' in self.module_controllers:
            self.module_controllers['customers'].on_new_customer()
    
    @pyqtSlot()
    def open_settings(self):
        """Abrir configuraciones"""
        self.show_info("Configuraciones", "Configuraciones en desarrollo.")
    
    @pyqtSlot()
    def create_backup(self):
        """Crear backup"""
        try:
            backup_manager = self.managers.get('backup')
            if backup_manager:
                # Crear backup
                backup_file = backup_manager.create_backup("Backup manual desde menú")
                if backup_file:
                    self.show_info("Backup Exitoso", f"Backup creado: {backup_file}")
                else:
                    self.show_error("Error", "No se pudo crear el backup")
            else:
                self.show_warning("Backup No Disponible", "Gestor de backup no disponible")
                
        except Exception as e:
            self.logger.error(f"Error creando backup: {e}")
            self.show_error("Error", f"Error creando backup: {str(e)}")
    
    @pyqtSlot()
    def show_about(self):
        """Mostrar diálogo Acerca de"""
        about_text = """
        <h2>AlmacénPro v2.0</h2>
        <p><b>Sistema ERP/POS para gestión de almacenes</b></p>
        <p>Arquitectura MVC con Qt Designer</p>
        <p>© 2024 - Desarrollado con PyQt5</p>
        
        <p><b>Características:</b></p>
        <ul>
        <li>Punto de venta completo</li>
        <li>Gestión de clientes e inventario</li>
        <li>Análisis predictivo</li>
        <li>Reportes avanzados</li>
        <li>Sistema de backup automático</li>
        </ul>
        
        <p><b>Usuario actual:</b> {}</p>
        <p><b>Rol:</b> {}</p>
        """.format(
            self.current_user.get('nombre_completo', 'Usuario'),
            self.current_user.get('rol_nombre', 'Usuario')
        )
        
        QMessageBox.about(self, "Acerca de AlmacénPro", about_text)
    
    @pyqtSlot()
    def show_help(self):
        """Mostrar ayuda"""
        help_text = """
        <h3>Ayuda Rápida - AlmacénPro v2.0</h3>
        
        <p><b>Atajos de Teclado:</b></p>
        <ul>
        <li><b>Ctrl+1:</b> Módulo de Ventas</li>
        <li><b>Ctrl+2:</b> Módulo de Clientes</li>
        <li><b>Ctrl+3:</b> Módulo de Inventario</li>
        <li><b>Ctrl+4:</b> Módulo de Reportes</li>
        <li><b>Ctrl+N:</b> Nueva Venta</li>
        <li><b>Ctrl+G:</b> Gestionar Clientes</li>
        <li><b>F5:</b> Actualizar</li>
        <li><b>F11:</b> Pantalla Completa</li>
        <li><b>Ctrl+Q:</b> Salir</li>
        </ul>
        
        <p><b>Navegación:</b></p>
        <ul>
        <li>Use la barra de herramientas para cambiar entre módulos</li>
        <li>Use los menús para acceder a funcionalidades específicas</li>
        <li>La barra de estado muestra información del módulo actual</li>
        </ul>
        """
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Ayuda - AlmacénPro")
        msg_box.setText(help_text)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.exec_()
    
    @pyqtSlot()
    def toggle_fullscreen(self):
        """Alternar pantalla completa"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    @pyqtSlot()
    def logout(self):
        """Cerrar sesión"""
        reply = QMessageBox.question(
            self, 
            "Cerrar Sesión", 
            "¿Está seguro que desea cerrar la sesión?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.user_logged_out.emit()
            self.close()
    
    # === SLOTS DE MÓDULOS ===
    
    @pyqtSlot(dict)
    def on_sale_completed(self, sale_data: Dict):
        """Manejar venta completada"""
        self.show_status_message(f"Venta #{sale_data.get('sale_id')} completada exitosamente")
        self.logger.info(f"Venta completada: {sale_data}")
    
    @pyqtSlot(dict)
    def on_product_added_to_cart(self, product_data: Dict):
        """Manejar producto agregado al carrito"""
        product_name = product_data.get('name', 'Producto')
        self.show_status_message(f"Agregado: {product_name}")
    
    @pyqtSlot(dict)
    def on_customer_created(self, customer_data: Dict):
        """Manejar cliente creado"""
        customer_name = customer_data.get('nombre', 'Cliente')
        self.show_status_message(f"Cliente creado: {customer_name}")
        self.logger.info(f"Cliente creado: {customer_data}")
    
    @pyqtSlot(dict)
    def on_customer_updated(self, customer_data: Dict):
        """Manejar cliente actualizado"""
        customer_name = customer_data.get('nombre', 'Cliente')
        self.show_status_message(f"Cliente actualizado: {customer_name}")
    
    @pyqtSlot(dict)
    def on_customer_selected_for_sale(self, customer_data: Dict):
        """Manejar cliente seleccionado para venta"""
        # Cambiar a módulo de ventas y establecer cliente
        self.switch_to_module('sales')
        # Aquí se podría pasar la información del cliente al módulo de ventas
    
    # === MÉTODOS DE UTILIDAD ===
    
    def show_info(self, title: str, message: str):
        """Mostrar mensaje informativo"""
        QMessageBox.information(self, title, message)
    
    def show_warning(self, title: str, message: str):
        """Mostrar mensaje de advertencia"""
        QMessageBox.warning(self, title, message)
    
    def show_error(self, title: str, message: str):
        """Mostrar mensaje de error"""
        QMessageBox.critical(self, title, message)
    
    def show_critical_error(self, title: str, message: str):
        """Mostrar error crítico y salir"""
        QMessageBox.critical(self, title, message)
        sys.exit(1)
    
    def show_question(self, title: str, message: str) -> bool:
        """Mostrar pregunta de confirmación"""
        reply = QMessageBox.question(self, title, message, 
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        return reply == QMessageBox.Yes
    
    # === EVENTOS ===
    
    def closeEvent(self, event):
        """Manejar evento de cierre"""
        try:
            if self.is_closing:
                event.accept()
                return
            
            # Confirmar cierre
            reply = QMessageBox.question(
                self, 
                "Confirmar Cierre", 
                "¿Está seguro que desea salir de AlmacénPro?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.is_closing = True
                
                # Limpiar recursos
                self.cleanup()
                
                # Emitir señal
                self.application_closing.emit()
                
                event.accept()
                self.logger.info("Aplicación cerrada correctamente")
            else:
                event.ignore()
                
        except Exception as e:
            self.logger.error(f"Error cerrando aplicación: {e}")
            event.accept()  # Forzar cierre en caso de error
    
    def cleanup(self):
        """Limpiar recursos antes del cierre"""
        try:
            # Detener timers
            if hasattr(self, 'time_timer'):
                self.time_timer.stop()
            
            # Limpiar controladores de módulos
            for module_name, controller in self.module_controllers.items():
                try:
                    if hasattr(controller, 'cleanup'):
                        controller.cleanup()
                except Exception as e:
                    self.logger.error(f"Error limpiando módulo {module_name}: {e}")
            
            self.logger.info("Recursos limpiados")
            
        except Exception as e:
            self.logger.error(f"Error en cleanup: {e}")
    
    def resizeEvent(self, event):
        """Manejar evento de redimensionamiento"""
        super().resizeEvent(event)
        # Aquí se pueden manejar ajustes de tamaño si es necesario
    
    def changeEvent(self, event):
        """Manejar cambios de estado de la ventana"""
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                # La ventana fue minimizada
                pass
            elif self.isMaximized():
                # La ventana fue maximizada
                pass
        
        super().changeEvent(event)