"""
Ventana principal de AlmacénPro
Integra todos los módulos y componentes del sistema
"""

import sys
import logging
from typing import Optional
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Importar componentes del sistema
from database.manager import DatabaseManager
from managers.user_manager import UserManager
from managers.product_manager import ProductManager
from managers.sales_manager import SalesManager
from managers.purchase_manager import PurchaseManager
from managers.provider_manager import ProviderManager
from managers.report_manager import ReportManager
from utils.backup_manager import BackupManager
from ui.dialogs.login_dialog import LoginDialog
from ui.dialogs.backup_dialog import BackupDialog

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Ventana principal del sistema AlmacénPro"""
    
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        
        # Inicializar componentes del sistema
        self.init_system_components()
        
        # Mostrar login y configurar UI si es exitoso
        if self.show_login():
            self.init_ui()
            self.init_backup_system()
            self.setup_window_properties()
            logger.info("Ventana principal inicializada correctamente")
        else:
            sys.exit(1)
    
    def init_system_components(self):
        """Inicializar todos los componentes del sistema"""
        try:
            # Base de datos
            self.db_manager = DatabaseManager(self.settings)
            
            # Gestores de negocio
            self.user_manager = UserManager(self.db_manager)
            self.product_manager = ProductManager(self.db_manager)
            self.sales_manager = SalesManager(self.db_manager, self.product_manager)
            self.purchase_manager = PurchaseManager(self.db_manager, self.product_manager)
            self.provider_manager = ProviderManager(self.db_manager)
            self.report_manager = ReportManager(self.db_manager)
            
            # Sistema de backup
            self.backup_manager = BackupManager(self.settings)
            
            logger.info("Componentes del sistema inicializados")
            
        except Exception as e:
            logger.error(f"Error inicializando componentes: {e}")
            QMessageBox.critical(None, "Error Crítico", 
                f"No se pudieron inicializar los componentes del sistema:\n{str(e)}")
            sys.exit(1)
    
    def show_login(self) -> bool:
        """Mostrar diálogo de login"""
        try:
            login_dialog = LoginDialog(self.user_manager)
            result = login_dialog.exec_()
            
            if result == QDialog.Accepted:
                logger.info(f"Login exitoso: {self.user_manager.current_user['username']}")
                return True
            else:
                logger.info("Login cancelado")
                return False
                
        except Exception as e:
            logger.error(f"Error en login: {e}")
            QMessageBox.critical(None, "Error de Login", 
                f"Error durante el proceso de login:\n{str(e)}")
            return False
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        self.setWindowTitle("AlmacénPro v2.0 - Sistema de Gestión Completo")
        self.setWindowIcon(QIcon())  # Aquí se puede agregar un icono
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Barra de estado del usuario
        self.create_user_status_bar()
        main_layout.addWidget(self.user_status_widget)
        
        # Pestañas principales
        self.create_main_tabs()
        main_layout.addWidget(self.tab_widget)
        
        # Barra de estado
        self.create_status_bar()
        
        # Configurar menús
        self.create_menus()
        
        # Configurar shortcuts
        self.setup_shortcuts()
    
    def create_user_status_bar(self):
        """Crear barra de información del usuario"""
        self.user_status_widget = QWidget()
        self.user_status_widget.setFixedHeight(40)
        self.user_status_widget.setStyleSheet("""
            QWidget {
                background-color: #2E86AB;
                color: white;
                border-radius: 5px;
            }
            QLabel {
                font-weight: bold;
                padding: 5px;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 3px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        
        layout = QHBoxLayout(self.user_status_widget)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Información del usuario
        user_info = QLabel(
            f"👤 {self.user_manager.current_user['nombre_completo']} | "
            f"📋 {self.user_manager.current_user.get('rol_nombre', 'Sin rol')} | "
            f"🕐 {QDateTime.currentDateTime().toString('dd/MM/yyyy hh:mm')}"
        )
        layout.addWidget(user_info)
        
        layout.addStretch()
        
        # Botones de acceso rápido
        backup_btn = QPushButton("💾 Backup")
        backup_btn.setToolTip("Sistema de Backup")
        backup_btn.clicked.connect(self.show_backup_dialog)
        layout.addWidget(backup_btn)
        
        settings_btn = QPushButton("⚙️ Config")
        settings_btn.setToolTip("Configuraciones")
        settings_btn.clicked.connect(self.show_settings_dialog)
        layout.addWidget(settings_btn)
        
        logout_btn = QPushButton("🚪 Salir")
        logout_btn.setToolTip("Cerrar Sesión")
        logout_btn.clicked.connect(self.logout)
        layout.addWidget(logout_btn)
    
    def create_main_tabs(self):
        """Crear pestañas principales según permisos del usuario"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #C0C0C0;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #E0E0E0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #2E86AB;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #4A9BC7;
                color: white;
            }
        """)
        
        # Crear pestañas según permisos
        if self.user_manager.has_permission('ventas'):
            self.create_sales_tab()
        
        if self.user_manager.has_permission('stock'):
            self.create_stock_tab()
        
        if self.user_manager.has_permission('compras'):
            self.create_purchases_tab()
        
        if self.user_manager.has_permission('reportes'):
            self.create_reports_tab()
        
        # Dashboard siempre visible
        self.create_dashboard_tab()
        
        if self.user_manager.has_permission('all'):
            self.create_admin_tab()
    
    def create_sales_tab(self):
        """Crear pestaña de ventas"""
        sales_widget = QWidget()
        layout = QVBoxLayout(sales_widget)
        
        # Mensaje temporal
        temp_label = QLabel("🛒 Módulo de Ventas")
        temp_label.setAlignment(Qt.AlignCenter)
        temp_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #2E86AB; 
            padding: 50px;
        """)
        layout.addWidget(temp_label)
        
        info_label = QLabel("""
        <p><b>Funcionalidades disponibles:</b></p>
        <ul>
        <li>✅ Scanner de códigos de barras integrado</li>
        <li>✅ Carrito de compras inteligente</li>
        <li>✅ Múltiples métodos de pago</li>
        <li>✅ Cuenta corriente de clientes</li>
        <li>✅ Impresión de tickets</li>
        <li>✅ Gestión de descuentos</li>
        </ul>
        <p><i>La interfaz completa se está migrando al nuevo sistema modular...</i></p>
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addStretch()
        
        self.tab_widget.addTab(sales_widget, "🛒 Ventas")
    
    def create_stock_tab(self):
        """Crear pestaña de stock"""
        stock_widget = QWidget()
        layout = QVBoxLayout(stock_widget)
        
        # Barra de herramientas
        toolbar = QHBoxLayout()
        
        add_product_btn = QPushButton("➕ Agregar Producto")
        add_product_btn.clicked.connect(self.add_product)
        toolbar.addWidget(add_product_btn)
        
        import_products_btn = QPushButton("📥 Importar Productos")
        import_products_btn.clicked.connect(self.import_products)
        toolbar.addWidget(import_products_btn)
        
        stock_alerts_btn = QPushButton("⚠️ Alertas de Stock")
        stock_alerts_btn.clicked.connect(self.show_stock_alerts)
        toolbar.addWidget(stock_alerts_btn)
        
        toolbar.addStretch()
        
        refresh_btn = QPushButton("🔄 Actualizar")
        refresh_btn.clicked.connect(self.refresh_stock)
        toolbar.addWidget(refresh_btn)
        
        layout.addLayout(toolbar)
        
        # Tabla de productos
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(8)
        self.stock_table.setHorizontalHeaderLabels([
            "Código", "Producto", "Categoría", "Stock", "Stock Mín.", 
            "Precio Venta", "Estado", "Acciones"
        ])
        
        # Configurar tabla
        header = self.stock_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        
        layout.addWidget(self.stock_table)
        
        # Cargar datos iniciales
        self.load_stock_data()
        
        self.tab_widget.addTab(stock_widget, "📦 Stock")
    
    def create_purchases_tab(self):
        """Crear pestaña de compras"""
        purchases_widget = QWidget()
        layout = QVBoxLayout(purchases_widget)
        
        # Sub-pestañas para compras
        purchases_subtabs = QTabWidget()
        
        # Nueva Compra
        new_purchase_widget = QWidget()
        new_purchase_layout = QVBoxLayout(new_purchase_widget)
        new_purchase_layout.addWidget(QLabel("🛍️ Nueva Orden de Compra"))
        purchases_subtabs.addTab(new_purchase_widget, "Nueva Compra")
        
        # Órdenes Pendientes
        pending_orders_widget = QWidget()
        pending_orders_layout = QVBoxLayout(pending_orders_widget)
        pending_orders_layout.addWidget(QLabel("📋 Órdenes Pendientes"))
        purchases_subtabs.addTab(pending_orders_widget, "Órdenes")
        
        # Proveedores
        providers_widget = QWidget()
        providers_layout = QVBoxLayout(providers_widget)
        providers_layout.addWidget(QLabel("👥 Gestión de Proveedores"))
        purchases_subtabs.addTab(providers_widget, "Proveedores")
        
        layout.addWidget(purchases_subtabs)
        
        self.tab_widget.addTab(purchases_widget, "🛍️ Compras")
    
    def create_reports_tab(self):
        """Crear pestaña de reportes"""
        reports_widget = QWidget()
        layout = QVBoxLayout(reports_widget)
        
        # Grid de reportes disponibles
        reports_grid = QGridLayout()
        
        # Reportes de ventas
        sales_reports_group = QGroupBox("📊 Reportes de Ventas")
        sales_reports_layout = QVBoxLayout(sales_reports_group)
        
        daily_sales_btn = QPushButton("Ventas Diarias")
        daily_sales_btn.clicked.connect(lambda: self.generate_report('daily_sales'))
        sales_reports_layout.addWidget(daily_sales_btn)
        
        monthly_sales_btn = QPushButton("Ventas Mensuales")
        monthly_sales_btn.clicked.connect(lambda: self.generate_report('monthly_sales'))
        sales_reports_layout.addWidget(monthly_sales_btn)
        
        top_products_btn = QPushButton("Productos Más Vendidos")
        top_products_btn.clicked.connect(lambda: self.generate_report('top_products'))
        sales_reports_layout.addWidget(top_products_btn)
        
        reports_grid.addWidget(sales_reports_group, 0, 0)
        
        # Reportes de stock
        stock_reports_group = QGroupBox("📦 Reportes de Stock")
        stock_reports_layout = QVBoxLayout(stock_reports_group)
        
        low_stock_btn = QPushButton("Stock Bajo")
        low_stock_btn.clicked.connect(lambda: self.generate_report('low_stock'))
        stock_reports_layout.addWidget(low_stock_btn)
        
        stock_valuation_btn = QPushButton("Valorización de Stock")
        stock_valuation_btn.clicked.connect(lambda: self.generate_report('stock_valuation'))
        stock_reports_layout.addWidget(stock_valuation_btn)
        
        reports_grid.addWidget(stock_reports_group, 0, 1)
        
        # Reportes financieros
        financial_reports_group = QGroupBox("💰 Reportes Financieros")
        financial_reports_layout = QVBoxLayout(financial_reports_group)
        
        accounts_receivable_btn = QPushButton("Cuentas por Cobrar")
        accounts_receivable_btn.clicked.connect(lambda: self.generate_report('accounts_receivable'))
        financial_reports_layout.addWidget(accounts_receivable_btn)
        
        profit_analysis_btn = QPushButton("Análisis de Rentabilidad")
        profit_analysis_btn.clicked.connect(lambda: self.generate_report('profit_analysis'))
        financial_reports_layout.addWidget(profit_analysis_btn)
        
        reports_grid.addWidget(financial_reports_group, 1, 0)
        
        # Reportes personalizados
        custom_reports_group = QGroupBox("🔧 Reportes Personalizados")
        custom_reports_layout = QVBoxLayout(custom_reports_group)
        
        custom_query_btn = QPushButton("Consulta Personalizada")
        custom_query_btn.clicked.connect(lambda: self.generate_report('custom_query'))
        custom_reports_layout.addWidget(custom_query_btn)
        
        export_data_btn = QPushButton("Exportar Datos")
        export_data_btn.clicked.connect(lambda: self.generate_report('export_data'))
        custom_reports_layout.addWidget(export_data_btn)
        
        reports_grid.addWidget(custom_reports_group, 1, 1)
        
        layout.addLayout(reports_grid)
        layout.addStretch()
        
        self.tab_widget.addTab(reports_widget, "📊 Reportes")
    
    def create_dashboard_tab(self):
        """Crear pestaña de dashboard ejecutivo"""
        dashboard_widget = QWidget()
        layout = QVBoxLayout(dashboard_widget)
        
        # Título del dashboard
        title = QLabel("📈 Dashboard Ejecutivo")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2E86AB; padding: 10px;")
        layout.addWidget(title)
        
        # Métricas principales en cards
        metrics_layout = QHBoxLayout()
        
        # Card de ventas de hoy
        today_sales_card = self.create_metric_card("Ventas Hoy", "$0", "🛒", "#4CAF50")
        metrics_layout.addWidget(today_sales_card)
        
        # Card de productos en stock bajo
        low_stock_card = self.create_metric_card("Stock Bajo", "0", "⚠️", "#FF9800")
        metrics_layout.addWidget(low_stock_card)
        
        # Card de clientes con deuda
        debt_card = self.create_metric_card("Cuentas por Cobrar", "$0", "💳", "#2196F3")
        metrics_layout.addWidget(debt_card)
        
        # Card de órdenes pendientes
        pending_orders_card = self.create_metric_card("Órdenes Pendientes", "0", "📋", "#9C27B0")
        metrics_layout.addWidget(pending_orders_card)
        
        layout.addLayout(metrics_layout)
        
        # Gráficos (placeholder)
        charts_layout = QHBoxLayout()
        
        # Gráfico de ventas semanales
        sales_chart_group = QGroupBox("Ventas de la Semana")
        sales_chart_layout = QVBoxLayout(sales_chart_group)
        sales_chart_placeholder = QLabel("📊 Gráfico de ventas semanales\n(Próximamente)")
        sales_chart_placeholder.setAlignment(Qt.AlignCenter)
        sales_chart_placeholder.setStyleSheet("padding: 50px; border: 2px dashed #ccc;")
        sales_chart_layout.addWidget(sales_chart_placeholder)
        charts_layout.addWidget(sales_chart_group)
        
        # Gráfico de productos más vendidos
        products_chart_group = QGroupBox("Top 10 Productos")
        products_chart_layout = QVBoxLayout(products_chart_group)
        products_chart_placeholder = QLabel("📈 Top productos más vendidos\n(Próximamente)")
        products_chart_placeholder.setAlignment(Qt.AlignCenter)
        products_chart_placeholder.setStyleSheet("padding: 50px; border: 2px dashed #ccc;")
        products_chart_layout.addWidget(products_chart_placeholder)
        charts_layout.addWidget(products_chart_group)
        
        layout.addLayout(charts_layout)
        
        # Cargar datos del dashboard
        self.update_dashboard_metrics()
        
        self.tab_widget.addTab(dashboard_widget, "📈 Dashboard")
    
    def create_admin_tab(self):
        """Crear pestaña de administración"""
        admin_widget = QWidget()
        layout = QVBoxLayout(admin_widget)
        
        # Secciones de administración
        admin_sections = QGridLayout()
        
        # Gestión de usuarios
        users_group = QGroupBox("👥 Gestión de Usuarios")
        users_layout = QVBoxLayout(users_group)
        
        manage_users_btn = QPushButton("Gestionar Usuarios")
        manage_users_btn.clicked.connect(self.manage_users)
        users_layout.addWidget(manage_users_btn)
        
        manage_roles_btn = QPushButton("Gestionar Roles")
        manage_roles_btn.clicked.connect(self.manage_roles)
        users_layout.addWidget(manage_roles_btn)
        
        admin_sections.addWidget(users_group, 0, 0)
        
        # Configuración del sistema
        system_group = QGroupBox("⚙️ Configuración del Sistema")
        system_layout = QVBoxLayout(system_group)
        
        company_config_btn = QPushButton("Datos de la Empresa")
        company_config_btn.clicked.connect(self.configure_company)
        system_layout.addWidget(company_config_btn)
        
        backup_config_btn = QPushButton("Configurar Backup")
        backup_config_btn.clicked.connect(self.show_backup_dialog)
        system_layout.addWidget(backup_config_btn)
        
        admin_sections.addWidget(system_group, 0, 1)
        
        # Mantenimiento
        maintenance_group = QGroupBox("🔧 Mantenimiento")
        maintenance_layout = QVBoxLayout(maintenance_group)
        
        db_stats_btn = QPushButton("Estadísticas de BD")
        db_stats_btn.clicked.connect(self.show_db_stats)
        maintenance_layout.addWidget(db_stats_btn)
        
        optimize_db_btn = QPushButton("Optimizar Base de Datos")
        optimize_db_btn.clicked.connect(self.optimize_database)
        maintenance_layout.addWidget(optimize_db_btn)
        
        admin_sections.addWidget(maintenance_group, 1, 0)
        
        # Logs y auditoría
        audit_group = QGroupBox("📋 Auditoría y Logs")
        audit_layout = QVBoxLayout(audit_group)
        
        view_logs_btn = QPushButton("Ver Logs del Sistema")
        view_logs_btn.clicked.connect(self.view_system_logs)
        audit_layout.addWidget(view_logs_btn)
        
        audit_trail_btn = QPushButton("Pista de Auditoría")
        audit_trail_btn.clicked.connect(self.show_audit_trail)
        audit_layout.addWidget(audit_trail_btn)
        
        admin_sections.addWidget(audit_group, 1, 1)
        
        layout.addLayout(admin_sections)
        layout.addStretch()
        
        self.tab_widget.addTab(admin_widget, "⚙️ Admin")
    
    def create_metric_card(self, title: str, value: str, icon: str, color: str) -> QWidget:
        """Crear tarjeta de métrica para el dashboard"""
        card = QWidget()
        card.setFixedSize(200, 120)
        card.setStyleSheet(f"""
            QWidget {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 10px;
                margin: 5px;
            }}
            QLabel {{
                color: {color};
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)
        
        # Icono
        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 24px;")
        layout.addWidget(icon_label)
        
        # Valor
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(value_label)
        
        # Título
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(title_label)
        
        return card
    
    def create_menus(self):
        """Crear menús de la aplicación"""
        menubar = self.menuBar()
        
        # Menú Archivo
        file_menu = menubar.addMenu('📁 Archivo')
        
        backup_action = QAction('💾 Sistema de Backup', self)
        backup_action.triggered.connect(self.show_backup_dialog)
        file_menu.addAction(backup_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('🚪 Salir', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menú Herramientas
        tools_menu = menubar.addMenu('🔧 Herramientas')
        
        calculator_action = QAction('🧮 Calculadora', self)
        calculator_action.triggered.connect(self.open_calculator)
        tools_menu.addAction(calculator_action)
        
        # Menú Ayuda
        help_menu = menubar.addMenu('❓ Ayuda')
        
        about_action = QAction('ℹ️ Acerca de', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_status_bar(self):
        """Crear barra de estado"""
        self.status_bar = self.statusBar()
        
        # Mensaje por defecto
        self.status_bar.showMessage("Listo")
        
        # Widget de estado de conexión BD
        self.db_status_label = QLabel("🟢 BD: Conectada")
        self.status_bar.addPermanentWidget(self.db_status_label)
        
        # Widget de estado de backup
        self.backup_status_label = QLabel("💾 Backup: Activo")
        self.status_bar.addPermanentWidget(self.backup_status_label)
        
        # Reloj
        self.clock_label = QLabel()
        self.update_clock()
        self.status_bar.addPermanentWidget(self.clock_label)
        
        # Timer para actualizar reloj
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)  # Actualizar cada segundo
    
    def setup_shortcuts(self):
        """Configurar atajos de teclado"""
        # Atajo para backup rápido
        backup_shortcut = QShortcut(QKeySequence("Ctrl+B"), self)
        backup_shortcut.activated.connect(self.quick_backup)
        
        # Atajo para buscar productos
        search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        search_shortcut.activated.connect(self.focus_search)
        
        # Atajo para nueva venta
        new_sale_shortcut = QShortcut(QKeySequence("F2"), self)
        new_sale_shortcut.activated.connect(self.new_sale)
    
    def setup_window_properties(self):
        """Configurar propiedades de la ventana"""
        # Tamaño y posición
        if self.settings.get('ui.window_maximized', True):
            self.showMaximized()
        else:
            size = self.settings.get('ui.last_window_size', [1200, 800])
            pos = self.settings.get('ui.last_window_position', [100, 100])
            self.resize(size[0], size[1])
            self.move(pos[0], pos[1])
        
        # Icono de la ventana
        self.setWindowIcon(QIcon())  # Aquí se puede agregar un icono personalizado
    
    def init_backup_system(self):
        """Inicializar sistema de backup automático"""
        try:
            if self.settings.is_backup_enabled():
                self.backup_manager.start_automatic_backup()
                self.backup_status_label.setText("💾 Backup: Activo")
                logger.info("Sistema de backup automático iniciado")
            else:
                self.backup_status_label.setText("💾 Backup: Inactivo")
                logger.info("Sistema de backup automático deshabilitado")
        except Exception as e:
            logger.error(f"Error iniciando sistema de backup: {e}")
            self.backup_status_label.setText("💾 Backup: Error")
    
    # ==================== SLOTS Y MÉTODOS DE EVENTOS ====================
    
    def show_backup_dialog(self):
        """Mostrar diálogo de gestión de backup"""
        try:
            dialog = BackupDialog(self.settings, self.backup_manager, self)
            dialog.exec_()
        except Exception as e:
            logger.error(f"Error mostrando diálogo de backup: {e}")
            QMessageBox.critical(self, "Error", f"Error abriendo sistema de backup:\n{str(e)}")
    
    def show_settings_dialog(self):
        """Mostrar diálogo de configuraciones"""
        QMessageBox.information(self, "Configuraciones", "Diálogo de configuraciones en desarrollo")
    
    def logout(self):
        """Cerrar sesión"""
        reply = QMessageBox.question(
            self, "Cerrar Sesión", 
            "¿Está seguro de que desea cerrar la sesión?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Guardar configuraciones de ventana
            self.save_window_settings()
            
            # Detener sistema de backup
            if hasattr(self, 'backup_manager'):
                self.backup_manager.stop_automatic_backup()
            
            # Cerrar base de datos
            if hasattr(self, 'db_manager'):
                self.db_manager.close()
            
            logger.info("Sesión cerrada por el usuario")
            self.close()
    
    def update_clock(self):
        """Actualizar reloj en la barra de estado"""
        current_time = QDateTime.currentDateTime().toString('hh:mm:ss')
        self.clock_label.setText(f"🕐 {current_time}")
    
    def update_dashboard_metrics(self):
        """Actualizar métricas del dashboard"""
        # Aquí se implementará la actualización de métricas reales
        pass
    
    def load_stock_data(self):
        """Cargar datos de stock en la tabla"""
        try:
            products = self.product_manager.get_all_products()
            
            self.stock_table.setRowCount(len(products))
            
            for i, product in enumerate(products):
                # Código de barras
                self.stock_table.setItem(i, 0, QTableWidgetItem(product.get('codigo_barras', '')))
                
                # Nombre del producto
                self.stock_table.setItem(i, 1, QTableWidgetItem(product['nombre']))
                
                # Categoría
                self.stock_table.setItem(i, 2, QTableWidgetItem(product.get('categoria_nombre', '')))
                
                # Stock actual
                stock_item = QTableWidgetItem(str(product['stock_actual']))
                if product['stock_actual'] <= 0:
                    stock_item.setForeground(QColor('red'))
                elif product['stock_actual'] <= product.get('stock_minimo', 0):
                    stock_item.setForeground(QColor('orange'))
                self.stock_table.setItem(i, 3, stock_item)
                
                # Stock mínimo
                self.stock_table.setItem(i, 4, QTableWidgetItem(str(product.get('stock_minimo', 0))))
                
                # Precio de venta
                self.stock_table.setItem(i, 5, QTableWidgetItem(f"${product.get('precio_venta', 0):.2f}"))
                
                # Estado
                if product['stock_actual'] <= 0:
                    status = "SIN STOCK"
                    color = QColor('red')
                elif product['stock_actual'] <= product.get('stock_minimo', 0):
                    status = "STOCK BAJO"
                    color = QColor('orange')
                else:
                    status = "OK"
                    color = QColor('green')
                
                status_item = QTableWidgetItem(status)
                status_item.setForeground(color)
                self.stock_table.setItem(i, 6, status_item)
                
                # Botones de acción (placeholder)
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(5, 5, 5, 5)
                
                edit_btn = QPushButton("✏️")
                edit_btn.setFixedSize(30, 25)
                edit_btn.setToolTip("Editar producto")
                actions_layout.addWidget(edit_btn)
                
                self.stock_table.setCellWidget(i, 7, actions_widget)
                
        except Exception as e:
            logger.error(f"Error cargando datos de stock: {e}")
            QMessageBox.critical(self, "Error", f"Error cargando productos:\n{str(e)}")
    
    def save_window_settings(self):
        """Guardar configuraciones de la ventana"""
        try:
            self.settings.update_ui_settings(
                window_maximized=self.isMaximized(),
                last_window_size=[self.width(), self.height()],
                last_window_position=[self.x(), self.y()]
            )
        except Exception as e:
            logger.error(f"Error guardando configuraciones de ventana: {e}")
    
    # ==================== MÉTODOS PLACEHOLDER ====================
    # (Implementar según se vayan desarrollando los módulos)
    
    def add_product(self):
        QMessageBox.information(self, "Función", "Agregar producto - En desarrollo")
    
    def import_products(self):
        QMessageBox.information(self, "Función", "Importar productos - En desarrollo")
    
    def show_stock_alerts(self):
        QMessageBox.information(self, "Función", "Alertas de stock - En desarrollo")
    
    def refresh_stock(self):
        self.load_stock_data()
        self.status_bar.showMessage("Stock actualizado", 2000)
    
    def generate_report(self, report_type: str):
        QMessageBox.information(self, "Reportes", f"Reporte {report_type} - En desarrollo")
    
    def manage_users(self):
        QMessageBox.information(self, "Admin", "Gestión de usuarios - En desarrollo")
    
    def manage_roles(self):
        QMessageBox.information(self, "Admin", "Gestión de roles - En desarrollo")
    
    def configure_company(self):
        QMessageBox.information(self, "Config", "Configuración de empresa - En desarrollo")
    
    def show_db_stats(self):
        try:
            stats = self.db_manager.get_database_stats()
            stats_text = f"""
            Estadísticas de Base de Datos:
            
            Tamaño del archivo: {stats.get('file_size_mb', 0):.2f} MB
            
            Registros por tabla:
            • Productos: {stats.get('productos_count', 0)}
            • Ventas: {stats.get('ventas_count', 0)}
            • Compras: {stats.get('compras_count', 0)}
            • Clientes: {stats.get('clientes_count', 0)}
            • Proveedores: {stats.get('proveedores_count', 0)}
            • Usuarios: {stats.get('usuarios_count', 0)}
            """
            QMessageBox.information(self, "Estadísticas de BD", stats_text)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error obteniendo estadísticas:\n{str(e)}")
    
    def optimize_database(self):
        reply = QMessageBox.question(
            self, "Optimizar BD",
            "¿Desea optimizar la base de datos?\nEsto puede tardar unos minutos.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.db_manager.vacuum_database()
                QMessageBox.information(self, "Éxito", "Base de datos optimizada correctamente")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error optimizando BD:\n{str(e)}")
    
    def view_system_logs(self):
        QMessageBox.information(self, "Logs", "Visor de logs - En desarrollo")
    
    def show_audit_trail(self):
        QMessageBox.information(self, "Auditoría", "Pista de auditoría - En desarrollo")
    
    def open_calculator(self):
        try:
            import subprocess
            subprocess.Popen(['calc.exe'])
        except:
            QMessageBox.warning(self, "Calculadora", "No se pudo abrir la calculadora del sistema")
    
    def show_about(self):
        QMessageBox.about(self, "Acerca de AlmacénPro", 
            """
            <h2>AlmacénPro v2.0</h2>
            <p><b>Sistema ERP/POS Completo</b></p>
            <p>Desarrollado en Python con PyQt5</p>
            <p><b>Funcionalidades:</b></p>
            <ul>
            <li>✅ Sistema de ventas con scanner</li>
            <li>✅ Gestión completa de stock</li>
            <li>✅ Compras y proveedores</li>
            <li>✅ Reportes avanzados</li>
            <li>✅ Sistema de backup automático</li>
            <li>✅ Multi-usuario con permisos</li>
            </ul>
            <p><i>Arquitectura modular profesional</i></p>
            """)
    
    def quick_backup(self):
        """Crear backup rápido con atajo de teclado"""
        try:
            self.status_bar.showMessage("Creando backup rápido...")
            success, message, _ = self.backup_manager.create_backup("Backup manual rápido")
            
            if success:
                self.status_bar.showMessage("Backup creado exitosamente", 3000)
            else:
                self.status_bar.showMessage("Error creando backup", 3000)
                QMessageBox.critical(self, "Error de Backup", message)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error en backup rápido:\n{str(e)}")
    
    def focus_search(self):
        """Dar foco al campo de búsqueda"""
        # Cambiar a pestaña de ventas y enfocar búsqueda
        for i in range(self.tab_widget.count()):
            if "Ventas" in self.tab_widget.tabText(i):
                self.tab_widget.setCurrentIndex(i)
                break
    
    def new_sale(self):
        """Iniciar nueva venta"""
        self.focus_search()
    
    def closeEvent(self, event):
        """Manejar cierre de la aplicación"""
        reply = QMessageBox.question(
            self, "Salir de AlmacénPro",
            "¿Está seguro de que desea salir?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.save_window_settings()
            
            # Detener sistema de backup
            if hasattr(self, 'backup_manager'):
                self.backup_manager.stop_automatic_backup()
            
            # Cerrar base de datos
            if hasattr(self, 'db_manager'):
                self.db_manager.close()
            
            event.accept()
            logger.info("Aplicación cerrada correctamente")
        else:
            event.ignore()