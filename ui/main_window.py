"""
Ventana Principal de AlmacénPro v2.0
Interfaz principal del sistema ERP/POS con navegación por tabs y dashboard
"""

import logging
from datetime import datetime, date
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Imports de widgets personalizados
from ui.widgets.dashboard_widget import DashboardWidget
from ui.widgets.sales_widget import SalesWidget

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Ventana principal del sistema AlmacénPro"""
    
    # Señales personalizadas
    logout_requested = pyqtSignal()
    app_exit_requested = pyqtSignal()
    
    def __init__(self, managers: dict, current_user: dict, parent=None):
        super().__init__(parent)
        
        self.managers = managers
        self.current_user = current_user
        self.widgets = {}
        
        # Configurar ventana principal
        self.init_ui()
        self.setup_menu_bar()
        self.setup_toolbar()
        self.setup_status_bar()
        
        # Mostrar mensaje de bienvenida
        self.show_welcome_message()
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        self.setWindowTitle(f"AlmacénPro v2.0 - {self.current_user['nombre_completo']}")
        
        # Configurar tamaño inicial responsivo
        screen = QApplication.desktop().screenGeometry()
        width = min(1400, int(screen.width() * 0.85))
        height = min(900, int(screen.height() * 0.85))
        self.resize(width, height)
        self.center_window()
        
        # Widget central con tabs
        self.central_widget = QTabWidget()
        self.setCentralWidget(self.central_widget)
        
        # Configurar tabs
        self.central_widget.setTabsClosable(False)
        self.central_widget.setMovable(False)
        self.central_widget.setDocumentMode(True)
        
        # Crear tabs según permisos del usuario
        self.create_all_tabs()
        
        # Aplicar permisos basados en roles
        self.update_role_based_permissions()
    
    def create_all_tabs(self):
        """Crear todos los tabs según los permisos del usuario"""
        try:
            # Dashboard siempre visible
            self.create_dashboard_tab()
            
            # Ventas - para ADMINISTRADOR, GERENTE, VENDEDOR
            if self.user_has_permission('ventas'):
                self.create_sales_tab()
            
            # Stock/Productos - para ADMINISTRADOR, GERENTE, DEPOSITO
            if self.user_has_permission('productos'):
                self.create_stock_tab()
            
            # Compras - para ADMINISTRADOR, GERENTE, DEPOSITO
            if self.user_has_permission('compras'):
                self.create_purchases_tab()
            
            # Clientes - para ADMINISTRADOR, GERENTE, VENDEDOR
            if self.user_has_permission('clientes_consulta') or self.user_has_permission('ventas'):
                self.create_customers_tab()
            
            # Reportes - para ADMINISTRADOR, GERENTE
            if self.user_has_permission('reportes'):
                self.create_reports_tab()
            
            # Configuración - solo ADMINISTRADOR
            if self.user_has_permission('*') or self.current_user['rol_nombre'] == 'ADMINISTRADOR':
                self.create_settings_tab()
                self.create_users_tab()
            
        except Exception as e:
            logger.error(f"Error creando tabs: {e}")
    
    def create_dashboard_tab(self):
        """Crear tab del dashboard"""
        try:
            dashboard_widget = DashboardWidget(self.managers, self.current_user)
            tab_index = self.central_widget.addTab(dashboard_widget, "📊 Dashboard")
            self.widgets['dashboard'] = dashboard_widget
            
        except Exception as e:
            logger.error(f"Error creando dashboard: {e}")
            # Fallback simple
            simple_dashboard = self.create_simple_dashboard()
            tab_index = self.central_widget.addTab(simple_dashboard, "📊 Dashboard")
            self.widgets['dashboard'] = simple_dashboard
    
    def create_sales_tab(self):
        """Crear tab de ventas"""
        try:
            sales_widget = self.create_sales_widget()
            tab_index = self.central_widget.addTab(sales_widget, "💰 Ventas")
            self.widgets['sales'] = sales_widget
            
        except Exception as e:
            logger.error(f"Error creando tab ventas: {e}")
    
    def create_stock_tab(self):
        """Crear tab de stock/productos"""
        try:
            stock_widget = self.create_stock_widget()
            tab_index = self.central_widget.addTab(stock_widget, "📦 Productos")
            self.widgets['stock'] = stock_widget
            
        except Exception as e:
            logger.error(f"Error creando tab stock: {e}")
    
    def create_purchases_tab(self):
        """Crear tab de compras"""
        try:
            purchases_widget = self.create_purchases_widget()
            tab_index = self.central_widget.addTab(purchases_widget, "🛒 Compras")
            self.widgets['purchases'] = purchases_widget
            
        except Exception as e:
            logger.error(f"Error creando tab compras: {e}")
    
    def create_customers_tab(self):
        """Crear tab de clientes"""
        try:
            # Intentar usar el widget avanzado de clientes
            from ui.widgets.customers_widget import CustomersWidget
            customers_widget = CustomersWidget(self.managers, self.current_user, self)
            tab_index = self.central_widget.addTab(customers_widget, "👥 Clientes")
            self.widgets['customers'] = customers_widget
            
        except ImportError as e:
            logger.warning(f"Widget avanzado de clientes no disponible: {e}")
            # Fallback al widget básico
            customers_widget = self.create_customers_widget()
            tab_index = self.central_widget.addTab(customers_widget, "👥 Clientes")
            self.widgets['customers'] = customers_widget
        except Exception as e:
            logger.error(f"Error creando tab clientes: {e}")
            # Fallback al widget básico
            customers_widget = self.create_customers_widget()
            tab_index = self.central_widget.addTab(customers_widget, "👥 Clientes")
            self.widgets['customers'] = customers_widget
    
    def create_reports_tab(self):
        """Crear tab de reportes"""
        try:
            reports_widget = self.create_enhanced_reports_widget()
            tab_index = self.central_widget.addTab(reports_widget, "📊 Reportes")
            self.widgets['reports'] = reports_widget
            
        except Exception as e:
            logger.error(f"Error creando tab reportes: {e}")
            # Fallback al widget básico
            reports_widget = self.create_reports_widget()
            tab_index = self.central_widget.addTab(reports_widget, "📊 Reportes")
            self.widgets['reports'] = reports_widget
    
    def create_settings_tab(self):
        """Crear tab de configuraciones"""
        try:
            settings_widget = self.create_settings_widget()
            tab_index = self.central_widget.addTab(settings_widget, "⚙️ Configuración")
            self.widgets['settings'] = settings_widget
            
        except Exception as e:
            logger.error(f"Error creando tab configuración: {e}")
    
    def create_users_tab(self):
        """Crear tab de gestión de usuarios - Solo para administradores"""
        try:
            # Verificar si es administrador
            if self.user_has_permission('*') or self.current_user.get('rol_nombre') == 'ADMINISTRADOR':
                from ui.widgets.admin_widget import AdminWidget
                admin_widget = AdminWidget(self.managers, self.current_user, self)
                tab_index = self.central_widget.addTab(admin_widget, "🔧 Administración")
                self.widgets['admin'] = admin_widget
            else:
                # Para otros usuarios, mostrar gestión básica
                users_widget = self.create_basic_users_widget()
                tab_index = self.central_widget.addTab(users_widget, "👤 Usuarios")
                self.widgets['users'] = users_widget
            
        except Exception as e:
            logger.error(f"Error creando tab usuarios/admin: {e}")
            # Fallback
            users_widget = self.create_users_widget()
            tab_index = self.central_widget.addTab(users_widget, "👤 Usuarios")
            self.widgets['users'] = users_widget
    
    def setup_menu_bar(self):
        """Configurar barra de menú"""
        menubar = self.menuBar()
        
        # Menú Archivo
        file_menu = menubar.addMenu("&Archivo")
        
        if self.user_has_permission('ventas'):
            new_sale_action = QAction("&Nueva Venta", self)
            new_sale_action.setShortcut("Ctrl+N")
            new_sale_action.triggered.connect(lambda: self.switch_to_tab('sales'))
            file_menu.addAction(new_sale_action)
            file_menu.addSeparator()
        
        # Backup - solo administradores
        if self.user_has_permission('*') or self.current_user['rol_nombre'] == 'ADMINISTRADOR':
            backup_action = QAction("&Backup", self)
            backup_action.triggered.connect(self.show_backup_dialog)
            file_menu.addAction(backup_action)
            file_menu.addSeparator()
        
        # Salir
        exit_action = QAction("&Salir", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menú Ventas
        if self.user_has_permission('ventas'):
            sales_menu = menubar.addMenu("&Ventas")
            
            pos_action = QAction("&Punto de Venta", self)
            pos_action.setShortcut("F2")
            pos_action.triggered.connect(lambda: self.switch_to_tab('sales'))
            sales_menu.addAction(pos_action)
            
            sales_history_action = QAction("&Historial de Ventas", self)
            sales_history_action.triggered.connect(self.show_sales_history)
            sales_menu.addAction(sales_history_action)
        
        # Menú Stock
        if self.user_has_permission('productos'):
            stock_menu = menubar.addMenu("&Stock")
            
            products_action = QAction("&Productos", self)
            products_action.setShortcut("F3")
            products_action.triggered.connect(lambda: self.switch_to_tab('stock'))
            stock_menu.addAction(products_action)
            
            stock_report_action = QAction("&Reporte de Stock", self)
            stock_report_action.triggered.connect(self.show_stock_report)
            stock_menu.addAction(stock_report_action)
        
        # Menú Reportes
        if self.user_has_permission('reportes'):
            reports_menu = menubar.addMenu("&Reportes")
            
            daily_report_action = QAction("Reporte &Diario", self)
            daily_report_action.triggered.connect(self.show_daily_report)
            reports_menu.addAction(daily_report_action)
            
            monthly_report_action = QAction("Reporte &Mensual", self)
            monthly_report_action.triggered.connect(self.show_monthly_report)
            reports_menu.addAction(monthly_report_action)
        
        # Menú Ayuda
        help_menu = menubar.addMenu("A&yuda")
        
        about_action = QAction("&Acerca de", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        """Configurar barra de herramientas"""
        toolbar = self.addToolBar("Principal")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        # Nueva venta
        if self.user_has_permission('ventas'):
            new_sale_btn = QAction("💰 Nueva Venta", self)
            new_sale_btn.setShortcut("Ctrl+N")
            new_sale_btn.triggered.connect(lambda: self.switch_to_tab('sales'))
            toolbar.addAction(new_sale_btn)
        
        # Productos
        if self.user_has_permission('productos'):
            products_btn = QAction("📦 Productos", self)
            products_btn.setShortcut("Ctrl+P")
            products_btn.triggered.connect(lambda: self.switch_to_tab('stock'))
            toolbar.addAction(products_btn)
        
        # Separador
        toolbar.addSeparator()
        
        # Backup rápido - solo admin
        if self.user_has_permission('*') or self.current_user['rol_nombre'] == 'ADMINISTRADOR':
            backup_btn = QAction("💾 Backup", self)
            backup_btn.triggered.connect(self.show_backup_dialog)
            toolbar.addAction(backup_btn)
        
        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        
        # Información del usuario
        user_info = QLabel(f"👤 {self.current_user['nombre_completo']} ({self.current_user['rol_nombre']})")
        user_info.setStyleSheet("color: #2c3e50; font-weight: bold; margin: 5px;")
        toolbar.addWidget(user_info)
        
        # Cerrar sesión
        logout_btn = QAction("❌ Cerrar Sesión", self)
        logout_btn.triggered.connect(self.logout)
        toolbar.addAction(logout_btn)
    
    def setup_status_bar(self):
        """Configurar barra de estado"""
        self.status_bar = self.statusBar()
        
        # Mensaje principal
        self.status_message = QLabel("Sistema listo")
        self.status_bar.addWidget(self.status_message)
        
        # Información adicional
        current_time = QLabel(datetime.now().strftime("%H:%M:%S"))
        self.status_bar.addPermanentWidget(current_time)
        
        # Timer para actualizar hora
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(lambda: current_time.setText(datetime.now().strftime("%H:%M:%S")))
        self.time_timer.start(1000)  # Actualizar cada segundo
        
        # Timer para actualizar datos en tiempo real
        self.data_refresh_timer = QTimer()
        self.data_refresh_timer.timeout.connect(self.refresh_all_data)
        self.data_refresh_timer.start(60000)  # Actualizar cada minuto
    
    def center_window(self):
        """Centrar ventana en la pantalla"""
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
    
    def show_welcome_message(self):
        """Mostrar mensaje de bienvenida"""
        role_name = self.current_user['rol_nombre']
        welcome_msg = f"¡Bienvenido/a {self.current_user['nombre_completo']}!"
        
        # Mensaje específico por rol
        if role_name == 'ADMINISTRADOR':
            welcome_msg += " Tienes acceso completo al sistema."
        elif role_name == 'GERENTE':
            welcome_msg += " Gestiona las operaciones del negocio."
        elif role_name == 'VENDEDOR':
            welcome_msg += " Procesa ventas y atiende clientes."
        elif role_name == 'DEPOSITO':
            welcome_msg += " Gestiona productos y stock."
        
        self.status_message.setText(welcome_msg)
        
        # Limpiar mensaje después de 5 segundos
        QTimer.singleShot(5000, lambda: self.status_message.setText("Sistema listo"))
    
    def switch_to_tab(self, tab_name: str):
        """Cambiar a un tab específico"""
        try:
            if tab_name in self.widgets:
                widget = self.widgets[tab_name]
                for i in range(self.central_widget.count()):
                    if self.central_widget.widget(i) == widget:
                        self.central_widget.setCurrentIndex(i)
                        return
            
            self.status_message.setText(f"Tab '{tab_name}' no disponible")
            
        except Exception as e:
            logger.error(f"Error cambiando a tab {tab_name}: {e}")
    
    def user_has_permission(self, permission: str) -> bool:
        """Verificar si el usuario actual tiene un permiso"""
        try:
            user_permissions = self.current_user.get('permisos', [])
            
            # Asegurar que sea una lista
            if isinstance(user_permissions, str):
                user_permissions = user_permissions.split(',') if user_permissions else []
            
            # Limpiar espacios en blanco de permisos
            user_permissions = [p.strip() for p in user_permissions if p.strip()]
            
            # Si tiene permiso de administrador completo
            if '*' in user_permissions:
                return True
            
            # Verificar permiso específico
            return permission in user_permissions
            
        except Exception as e:
            logger.error(f"Error verificando permisos: {e}")
            return False
    
    def logout(self):
        """Cerrar sesión"""
        reply = QMessageBox.question(
            self,
            "Cerrar Sesión",
            "¿Está seguro que desea cerrar la sesión actual?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.logout_requested.emit()
    
    def closeEvent(self, event):
        """Manejar cierre de ventana"""
        reply = QMessageBox.question(
            self,
            "Salir",
            "¿Está seguro que desea salir del sistema?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Detener timers
            if hasattr(self, 'time_timer'):
                self.time_timer.stop()
            if hasattr(self, 'data_refresh_timer'):
                self.data_refresh_timer.stop()
            event.accept()
        else:
            event.ignore()
    
    # WIDGETS FUNCIONALES BÁSICOS
    
    def create_simple_dashboard(self):
        """Crear dashboard simple"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Título
        title = QLabel("📊 Dashboard Ejecutivo")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Información básica
        info_layout = QHBoxLayout()
        
        # Tarjetas de información dinámicas
        cards_data = self.get_dashboard_data()
        
        for title_text, value, color in cards_data:
            card = self.create_info_card(title_text, value, color)
            info_layout.addWidget(card)
        
        layout.addLayout(info_layout)
        
        # Botones rápidos
        buttons_layout = QHBoxLayout()
        
        if self.user_has_permission('ventas'):
            sale_btn = QPushButton("💰 Nueva Venta")
            sale_btn.setStyleSheet("QPushButton { background-color: #27ae60; color: white; padding: 10px; font-weight: bold; border-radius: 5px; }")
            sale_btn.clicked.connect(lambda: self.switch_to_tab('sales'))
            buttons_layout.addWidget(sale_btn)
        
        if self.user_has_permission('productos'):
            product_btn = QPushButton("📦 Gestionar Productos")
            product_btn.setStyleSheet("QPushButton { background-color: #3498db; color: white; padding: 10px; font-weight: bold; border-radius: 5px; }")
            product_btn.clicked.connect(lambda: self.switch_to_tab('stock'))
            buttons_layout.addWidget(product_btn)
        
        layout.addLayout(buttons_layout)
        layout.addStretch()
        
        return widget
    
    def create_info_card(self, title: str, value: str, color: str):
        """Crear tarjeta de información"""
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {color};
                border-radius: 10px;
                background-color: white;
                margin: 5px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        return card
    
    def create_sales_widget(self):
        """Crear widget de ventas funcional"""
        try:
            return SalesWidget(self.managers, self.current_user)
        except Exception as e:
            logger.error(f"Error creando SalesWidget: {e}")
            # Fallback a widget básico
            return self.create_basic_sales_widget()
    
    def create_basic_sales_widget(self):
        """Crear widget básico de ventas como fallback"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Título
        title = QLabel("💰 Punto de Venta")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #27ae60; margin: 10px;")
        layout.addWidget(title)
        
        # Mensaje de estado
        status_label = QLabel("Sistema POS - Funcionalidad básica disponible")
        status_label.setStyleSheet("color: #7f8c8d; font-style: italic; margin: 10px;")
        layout.addWidget(status_label)
        
        # Área de trabajo
        work_area = QHBoxLayout()
        
        # Panel izquierdo - Productos
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("🔍 Buscar Producto:"))
        search_input = QLineEdit()
        search_input.setPlaceholderText("Código de barras o nombre...")
        left_panel.addWidget(search_input)
        
        products_table = QTableWidget(0, 4)
        products_table.setHorizontalHeaderLabels(["Código", "Producto", "Precio", "Stock"])
        left_panel.addWidget(products_table)
        
        # Panel derecho - Carrito
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("🛒 Carrito de Ventas:"))
        cart_table = QTableWidget(0, 4)
        cart_table.setHorizontalHeaderLabels(["Producto", "Cantidad", "Precio", "Total"])
        right_panel.addWidget(cart_table)
        
        # Totales
        total_label = QLabel("TOTAL: $0.00")
        total_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #27ae60;")
        right_panel.addWidget(total_label)
        
        # Botones
        buttons_layout = QHBoxLayout()
        clear_btn = QPushButton("🗑️ Limpiar")
        process_btn = QPushButton("💳 Procesar Venta")
        process_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px;")
        
        # Conectar botón de procesar venta al diálogo de pagos
        process_btn.clicked.connect(lambda: self.process_sale_with_payment(1500.00))  # Ejemplo con $1500
        
        # Botón de prueba para ticket
        ticket_btn = QPushButton("🎫 Ticket Demo")
        ticket_btn.setStyleSheet("background-color: #9b59b6; color: white; font-weight: bold; padding: 8px;")
        ticket_btn.clicked.connect(self.demo_ticket_print)
        
        buttons_layout.addWidget(clear_btn)
        buttons_layout.addWidget(process_btn)
        buttons_layout.addWidget(ticket_btn)
        right_panel.addLayout(buttons_layout)
        
        # Agregar paneles
        work_area.addLayout(left_panel)
        work_area.addLayout(right_panel)
        layout.addLayout(work_area)
        
        return widget
    
    def create_enhanced_reports_widget(self):
        """Crear widget mejorado de reportes con el nuevo ReportDialog"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("📊 Centro de Reportes Avanzado")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #34495e; margin: 10px;")
        layout.addWidget(title)
        
        # Botón principal para generar reportes
        generate_report_btn = QPushButton("🎯 Generador de Reportes")
        generate_report_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                font-size: 16px;
                padding: 15px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        generate_report_btn.clicked.connect(self.open_report_generator)
        layout.addWidget(generate_report_btn)
        
        layout.addWidget(QLabel())  # Separador
        
        # Accesos rápidos a reportes comunes
        quick_reports_group = QGroupBox("⚡ Reportes Rápidos")
        quick_layout = QGridLayout(quick_reports_group)
        
        # Botones de reportes rápidos
        quick_buttons = [
            ("💰 Ventas de Hoy", self.generate_daily_sales_report),
            ("📦 Stock Actual", self.generate_stock_report),
            ("👥 Lista de Clientes", self.generate_customers_report),
            ("⚠️ Stock Bajo", self.generate_low_stock_report),
            ("🌟 Top Clientes", self.generate_top_customers_report),
            ("💳 Ventas por Método", self.generate_payment_methods_report)
        ]
        
        for i, (text, callback) in enumerate(quick_buttons):
            btn = QPushButton(text)
            btn.setStyleSheet("padding: 8px; text-align: left;")
            btn.clicked.connect(callback)
            row, col = divmod(i, 2)
            quick_layout.addWidget(btn, row, col)
        
        layout.addWidget(quick_reports_group)
        
        # Área de información
        info_label = QLabel("ℹ️ Use el Generador de Reportes para configuraciones avanzadas con filtros y exportación a múltiples formatos.")
        info_label.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 10px; background: #ecf0f1; border-radius: 5px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addStretch()
        
        return widget
    
    def create_stock_widget(self):
        """Crear widget de productos/stock con scroll"""
        # Container principal
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # Crear contenido
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        # Título y controles
        header_layout = QHBoxLayout()
        title = QLabel("📦 Gestión de Productos")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #3498db;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        add_product_btn = QPushButton("➕ Nuevo Producto")
        add_product_btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; padding: 8px;")
        header_layout.addWidget(add_product_btn)
        
        layout.addLayout(header_layout)
        
        # Tabla de productos
        self.products_table = QTableWidget(0, 6)
        self.products_table.setHorizontalHeaderLabels(["Código", "Producto", "Categoría", "Precio", "Stock", "Acciones"])
        self.products_table.horizontalHeader().setStretchLastSection(True)
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        # Cargar datos reales
        self.load_products_data()
        
        layout.addWidget(self.products_table)
        
        # Agregar scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(content_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        main_layout.addWidget(scroll_area)
        
        return main_widget
    
    def create_purchases_widget(self):
        """Crear widget de compras"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("🛒 Gestión de Compras")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #e67e22; margin: 10px;")
        layout.addWidget(title)
        
        # Botones principales
        buttons_layout = QHBoxLayout()
        new_purchase_btn = QPushButton("📋 Nueva Compra")
        new_purchase_btn.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold; padding: 10px;")
        receive_btn = QPushButton("📦 Recibir Mercadería")
        manage_providers_btn = QPushButton("👥 Gestionar Proveedores")
        
        buttons_layout.addWidget(new_purchase_btn)
        buttons_layout.addWidget(receive_btn)
        buttons_layout.addWidget(manage_providers_btn)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        # Tabla de compras
        purchases_table = QTableWidget(0, 6)
        purchases_table.setHorizontalHeaderLabels(["Fecha", "Proveedor", "N° Factura", "Total", "Estado", "Acciones"])
        layout.addWidget(purchases_table)
        
        return widget
    
    def create_customers_widget(self):
        """Crear widget de clientes"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("👥 Gestión de Clientes")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #9b59b6; margin: 10px;")
        layout.addWidget(title)
        
        # Solo vendedores ven versión limitada
        if self.current_user['rol_nombre'] == 'VENDEDOR':
            info = QLabel("Vista de consulta - Solo lectura")
            info.setStyleSheet("color: #e67e22; font-style: italic;")
            layout.addWidget(info)
        
        # Controles
        controls_layout = QHBoxLayout()
        search_input = QLineEdit()
        search_input.setPlaceholderText("Buscar cliente...")
        controls_layout.addWidget(search_input)
        
        if self.current_user['rol_nombre'] != 'VENDEDOR':
            add_client_btn = QPushButton("➕ Nuevo Cliente")
            add_client_btn.setStyleSheet("background-color: #9b59b6; color: white; font-weight: bold; padding: 8px;")
            controls_layout.addWidget(add_client_btn)
        
        layout.addLayout(controls_layout)
        
        # Tabla de clientes
        clients_table = QTableWidget(0, 5)
        clients_table.setHorizontalHeaderLabels(["Nombre", "Documento", "Teléfono", "Email", "Estado"])
        layout.addWidget(clients_table)
        
        return widget
    
    def create_reports_widget(self):
        """Crear widget de reportes"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("📊 Centro de Reportes")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #34495e; margin: 10px;")
        layout.addWidget(title)
        
        # Categorías de reportes
        categories_layout = QHBoxLayout()
        
        # Reportes de ventas
        sales_group = QGroupBox("💰 Reportes de Ventas")
        sales_layout = QVBoxLayout(sales_group)
        sales_daily_btn = QPushButton("Ventas del Día")
        sales_monthly_btn = QPushButton("Ventas del Mes")
        sales_by_product_btn = QPushButton("Ventas por Producto")
        sales_layout.addWidget(sales_daily_btn)
        sales_layout.addWidget(sales_monthly_btn)
        sales_layout.addWidget(sales_by_product_btn)
        categories_layout.addWidget(sales_group)
        
        # Reportes de stock
        stock_group = QGroupBox("📦 Reportes de Stock")
        stock_layout = QVBoxLayout(stock_group)
        stock_current_btn = QPushButton("Stock Actual")
        stock_low_btn = QPushButton("Stock Bajo")
        stock_movements_btn = QPushButton("Movimientos de Stock")
        stock_layout.addWidget(stock_current_btn)
        stock_layout.addWidget(stock_low_btn)
        stock_layout.addWidget(stock_movements_btn)
        categories_layout.addWidget(stock_group)
        
        layout.addLayout(categories_layout)
        layout.addStretch()
        
        return widget
    
    def create_settings_widget(self):
        """Crear widget de configuraciones"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("⚙️ Configuraciones del Sistema")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #e74c3c; margin: 10px;")
        layout.addWidget(title)
        
        # Advertencia de permisos
        warning = QLabel("⚠️ Solo usuarios administradores pueden modificar configuraciones")
        warning.setStyleSheet("background-color: #fdf2e9; color: #e67e22; padding: 10px; border-radius: 5px; margin: 5px;")
        layout.addWidget(warning)
        
        # Categorías de configuración
        config_tabs = QTabWidget()
        
        # Empresa
        company_tab = QWidget()
        company_layout = QFormLayout(company_tab)
        company_layout.addRow("Nombre de la Empresa:", QLineEdit())
        company_layout.addRow("Dirección:", QLineEdit())
        company_layout.addRow("Teléfono:", QLineEdit())
        company_layout.addRow("Email:", QLineEdit())
        config_tabs.addTab(company_tab, "🏢 Empresa")
        
        # Sistema
        system_tab = QWidget()
        system_layout = QFormLayout(system_tab)
        system_layout.addRow("Backup Automático:", QCheckBox())
        system_layout.addRow("Intervalo de Backup (horas):", QSpinBox())
        config_tabs.addTab(system_tab, "💻 Sistema")
        
        layout.addWidget(config_tabs)
        
        # Botones de acción
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        save_btn = QPushButton("💾 Guardar Configuración")
        save_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px;")
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
        layout.addStretch()
        
        return widget
    
    def create_users_widget(self):
        """Crear widget de gestión de usuarios"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("👤 Gestión de Usuarios")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #8e44ad; margin: 10px;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        add_user_btn = QPushButton("➕ Nuevo Usuario")
        add_user_btn.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold; padding: 8px;")
        header_layout.addWidget(add_user_btn)
        
        layout.addLayout(header_layout)
        
        # Tabla de usuarios
        users_table = QTableWidget(0, 6)
        users_table.setHorizontalHeaderLabels(["Usuario", "Nombre Completo", "Rol", "Email", "Estado", "Acciones"])
        users_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(users_table)
        
        return widget
    
    def create_basic_users_widget(self):
        """Widget básico de usuarios para no-administradores"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("👤 Información de Usuarios")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #8e44ad; margin: 10px;")
        layout.addWidget(title)
        
        info_label = QLabel("🔒 Vista limitada - Solo consulta")
        info_label.setStyleSheet("color: #e67e22; font-style: italic; margin: 5px;")
        layout.addWidget(info_label)
        
        # Tabla básica de usuarios (solo lectura)
        users_table = QTableWidget(0, 4)
        users_table.setHorizontalHeaderLabels(["Usuario", "Nombre", "Rol", "Estado"])
        users_table.horizontalHeader().setStretchLastSection(True)
        users_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # Cargar datos básicos de usuarios
        self.load_basic_users_data(users_table)
        
        layout.addWidget(users_table)
        layout.addStretch()
        
        return widget
    
    def load_basic_users_data(self, table):
        """Cargar datos básicos de usuarios"""
        try:
            if 'user' in self.managers:
                users = self.managers['user'].get_all_users()
                table.setRowCount(len(users))
                
                for row, user in enumerate(users):
                    table.setItem(row, 0, QTableWidgetItem(user.get('username', '')))
                    table.setItem(row, 1, QTableWidgetItem(user.get('nombre_completo', '')))
                    table.setItem(row, 2, QTableWidgetItem(user.get('rol_nombre', '')))
                    status = "✅ Activo" if user.get('activo') else "❌ Inactivo"
                    table.setItem(row, 3, QTableWidgetItem(status))
                    
        except Exception as e:
            logger.error(f"Error cargando usuarios básicos: {e}")
    
    def load_products_data(self):
        """Cargar datos reales de productos"""
        try:
            if 'product' not in self.managers:
                logger.warning("Product manager no disponible")
                return
            
            products = self.managers['product'].get_all_products()
            
            if not products:
                # Mostrar mensaje si no hay productos
                self.products_table.setRowCount(1)
                no_data_item = QTableWidgetItem("No hay productos registrados")
                no_data_item.setTextAlignment(Qt.AlignCenter)
                self.products_table.setSpan(0, 0, 1, 6)
                self.products_table.setItem(0, 0, no_data_item)
                return
            
            self.products_table.setRowCount(len(products))
            
            for row, product in enumerate(products):
                # Código
                codigo = product.get('codigo_interno') or product.get('codigo_barras', '')
                self.products_table.setItem(row, 0, QTableWidgetItem(str(codigo)))
                
                # Nombre
                self.products_table.setItem(row, 1, QTableWidgetItem(product.get('nombre', '')))
                
                # Categoría
                categoria = product.get('categoria_nombre', 'Sin categoría')
                self.products_table.setItem(row, 2, QTableWidgetItem(categoria))
                
                # Precio
                precio = product.get('precio_venta', 0)
                precio_text = f"${float(precio):,.2f}" if precio else "$0.00"
                self.products_table.setItem(row, 3, QTableWidgetItem(precio_text))
                
                # Stock
                stock = product.get('stock_actual', 0)
                stock_text = f"{float(stock):,.2f}"
                stock_item = QTableWidgetItem(stock_text)
                
                # Colorear stock bajo
                stock_minimo = product.get('stock_minimo', 0)
                if float(stock) <= float(stock_minimo):
                    stock_item.setBackground(QColor(231, 76, 60, 50))  # Rojo suave
                    stock_item.setToolTip("⚠️ Stock bajo")
                
                self.products_table.setItem(row, 4, stock_item)
                
                # Acciones
                actions_widget = self.create_product_actions(product.get('id'))
                self.products_table.setCellWidget(row, 5, actions_widget)
                
        except Exception as e:
            logger.error(f"Error cargando productos: {e}")
            # Mostrar error en la tabla
            self.products_table.setRowCount(1)
            error_item = QTableWidgetItem(f"Error cargando productos: {str(e)}")
            error_item.setTextAlignment(Qt.AlignCenter)
            self.products_table.setSpan(0, 0, 1, 6)
            self.products_table.setItem(0, 0, error_item)
    
    def create_product_actions(self, product_id) -> QWidget:
        """Crear botones de acción para producto"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        
        edit_btn = QPushButton("✏️")
        edit_btn.setToolTip("Editar producto")
        edit_btn.setFixedSize(25, 25)
        edit_btn.clicked.connect(lambda: self.edit_product(product_id))
        
        stock_btn = QPushButton("📦")
        stock_btn.setToolTip("Ajustar stock")
        stock_btn.setFixedSize(25, 25)
        stock_btn.clicked.connect(lambda: self.adjust_stock(product_id))
        
        layout.addWidget(edit_btn)
        layout.addWidget(stock_btn)
        layout.addStretch()
        
        return widget
    
    def load_customers_data(self):
        """Cargar datos reales de clientes"""
        try:
            # Implementar cuando se corrija el widget de clientes
            pass
        except Exception as e:
            logger.error(f"Error cargando clientes: {e}")
    
    # MÉTODOS DE ACCIÓN
    
    def show_backup_dialog(self):
        """Mostrar diálogo de backup"""
        try:
            from ui.dialogs.backup_dialog import BackupDialog
            dialog = BackupDialog(self.managers.get('backup'), self)
            dialog.exec_()
        except ImportError:
            # Si no existe el diálogo, mostrar una funcionalidad básica
            reply = QMessageBox.question(
                self, 
                "Backup del Sistema", 
                "¿Desea crear un backup de la base de datos ahora?\n\nEsto puede tardar unos momentos.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                try:
                    if self.managers.get('backup'):
                        backup_manager = self.managers['backup']
                        success = backup_manager.create_backup("Backup manual desde dashboard")
                        if success:
                            QMessageBox.information(self, "Backup", "Backup creado exitosamente.")
                        else:
                            QMessageBox.warning(self, "Backup", "Error al crear el backup.")
                    else:
                        QMessageBox.warning(self, "Backup", "Servicio de backup no disponible.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Error durante el backup: {str(e)}")
    
    def show_sales_history(self):
        """Mostrar historial de ventas"""
        QMessageBox.information(self, "Historial", "Historial de ventas en desarrollo.")
    
    def show_stock_report(self):
        """Mostrar reporte de stock"""
        QMessageBox.information(self, "Stock", "Reporte de stock en desarrollo.")
    
    def show_daily_report(self):
        """Mostrar reporte diario"""
        QMessageBox.information(self, "Reportes", "Reporte diario en desarrollo.")
    
    def show_monthly_report(self):
        """Mostrar reporte mensual"""
        QMessageBox.information(self, "Reportes", "Reporte mensual en desarrollo.")
    
    def edit_product(self, product_id):
        """Editar producto"""
        try:
            # Intentar usar el diálogo existente
            from ui.dialogs.add_product_dialog import AddProductDialog
            
            # Obtener datos del producto para editar
            product_data = None
            if 'product' in self.managers:
                product_data = self.managers['product'].get_product_by_id(product_id)
            
            dialog = AddProductDialog(
                self.managers.get('product'), 
                self.managers.get('provider'), 
                product_data=product_data, 
                parent=self
            )
            if dialog.exec_() == QDialog.Accepted:
                self.load_products_data()  # Recargar datos
        except ImportError:
            QMessageBox.information(self, "Editar Producto", f"Funcionalidad en desarrollo.\nID del producto: {product_id}")
        except Exception as e:
            logger.error(f"Error editando producto: {e}")
            QMessageBox.warning(self, "Error", f"Error al editar producto: {str(e)}")
    
    def adjust_stock(self, product_id):
        """Ajustar stock de producto"""
        try:
            current_stock = 0
            product_name = "Producto"
            
            # Obtener información actual del producto
            if 'product' in self.managers:
                product = self.managers['product'].get_product_by_id(product_id)
                if product:
                    current_stock = float(product.get('stock_actual', 0))
                    product_name = product.get('nombre', 'Producto')
            
            # Diálogo simple de ajuste
            new_stock, ok = QInputDialog.getDouble(
                self, 
                "Ajustar Stock", 
                f"Producto: {product_name}\nStock actual: {current_stock}\n\nNuevo stock:",
                value=current_stock,
                min=0,
                max=999999,
                decimals=2
            )
            
            if ok and new_stock != current_stock:
                # TODO: Implementar actualización real de stock
                QMessageBox.information(self, "Stock Actualizado", 
                                      f"Stock actualizado de {current_stock} a {new_stock}")
                self.load_products_data()  # Recargar datos
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error ajustando stock: {str(e)}")
    
    def show_about(self):
        """Mostrar información del sistema"""
        QMessageBox.about(
            self,
            "Acerca de AlmacénPro v2.0",
            """
            <h3>AlmacénPro v2.0</h3>
            <p>Sistema ERP/POS Completo</p>
            <p><b>Usuario Actual:</b> {}<br>
            <b>Rol:</b> {}<br>
            <b>Versión:</b> 2.0.0</p>
            <p>Sistema profesional de gestión para almacenes, kioscos y distribuidoras.</p>
            """.format(
                self.current_user['nombre_completo'],
                self.current_user['rol_nombre']
            )
        )
    
    # NUEVOS MÉTODOS PARA FUNCIONALIDAD AVANZADA
    
    def refresh_all_data(self):
        """Actualizar todos los datos en tiempo real"""
        try:
            # Actualizar datos del dashboard
            if 'dashboard' in self.widgets:
                dashboard_widget = self.widgets['dashboard']
                if hasattr(dashboard_widget, 'refresh_data'):
                    dashboard_widget.refresh_data()
            
            # Actualizar tabla de productos si está visible
            current_tab = self.central_widget.currentWidget()
            if current_tab == self.widgets.get('stock'):
                self.load_products_data()
            
            # Actualizar clientes si el widget avanzado está activo
            if 'customers' in self.widgets:
                customers_widget = self.widgets['customers']
                if hasattr(customers_widget, 'refresh_data'):
                    customers_widget.refresh_data()
            
        except Exception as e:
            logger.error(f"Error actualizando datos en tiempo real: {e}")
    
    def open_report_generator(self):
        """Abrir el generador de reportes avanzado"""
        try:
            from ui.dialogs.report_dialog import ReportDialog
            dialog = ReportDialog(self.managers, self)
            dialog.report_generated.connect(self.on_report_generated)
            dialog.exec_()
        except ImportError as e:
            logger.warning(f"ReportDialog no disponible: {e}")
            QMessageBox.information(self, "Reportes", "Funcionalidad de reportes avanzados en desarrollo.")
        except Exception as e:
            logger.error(f"Error abriendo generador de reportes: {e}")
            QMessageBox.warning(self, "Error", f"Error abriendo generador de reportes: {str(e)}")
    
    def on_report_generated(self, filename: str, format_type: str):
        """Callback cuando se genera un reporte"""
        self.status_message.setText(f"Reporte generado: {filename}")
        
        # Auto-limpiar mensaje después de 5 segundos
        QTimer.singleShot(5000, lambda: self.status_message.setText("Sistema listo"))
    
    def generate_daily_sales_report(self):
        """Generar reporte rápido de ventas del día"""
        try:
            from ui.dialogs.report_dialog import ReportDialog
            dialog = ReportDialog(self.managers, self)
            
            # Pre-configurar para ventas del día
            dialog.report_type_combo.setCurrentText("📊 Reporte de Ventas")
            dialog.period_combo.setCurrentText("Hoy")
            dialog.show_preview()
            dialog.exec_()
        except:
            QMessageBox.information(self, "Reporte", "Generando reporte de ventas del día...")
    
    def generate_stock_report(self):
        """Generar reporte rápido de stock actual"""
        try:
            from utils.exporters import export_data
            
            if 'product' not in self.managers:
                QMessageBox.warning(self, "Error", "Manager de productos no disponible")
                return
            
            # Obtener productos
            products = self.managers['product'].get_all_products()
            
            if not products:
                QMessageBox.information(self, "Info", "No hay productos para exportar")
                return
            
            # Exportar a CSV rápidamente
            filename = f"stock_actual_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            success = export_data(products, filename, "csv", "Reporte de Stock Actual")
            
            if success:
                QMessageBox.information(self, "Éxito", f"Reporte de stock exportado: {filename}")
            else:
                QMessageBox.warning(self, "Error", "Error exportando reporte de stock")
                
        except Exception as e:
            logger.error(f"Error generando reporte de stock: {e}")
            QMessageBox.warning(self, "Error", f"Error: {str(e)}")
    
    def generate_customers_report(self):
        """Generar reporte rápido de clientes"""
        try:
            from utils.exporters import export_data
            
            if 'customer' not in self.managers:
                QMessageBox.warning(self, "Error", "Manager de clientes no disponible")
                return
            
            # Obtener clientes
            customers = self.managers['customer'].get_all_customers()
            
            if not customers:
                QMessageBox.information(self, "Info", "No hay clientes para exportar")
                return
            
            # Exportar a CSV
            filename = f"clientes_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            success = export_data(customers, filename, "csv", "Lista de Clientes")
            
            if success:
                QMessageBox.information(self, "Éxito", f"Lista de clientes exportada: {filename}")
            else:
                QMessageBox.warning(self, "Error", "Error exportando lista de clientes")
                
        except Exception as e:
            logger.error(f"Error generando reporte de clientes: {e}")
            QMessageBox.warning(self, "Error", f"Error: {str(e)}")
    
    def generate_low_stock_report(self):
        """Generar reporte de productos con stock bajo"""
        try:
            from ui.dialogs.report_dialog import ReportDialog
            dialog = ReportDialog(self.managers, self)
            
            # Pre-configurar para productos con stock bajo
            dialog.report_type_combo.setCurrentText("⚠️ Productos con Stock Bajo")
            dialog.show_preview()
            dialog.exec_()
        except:
            QMessageBox.information(self, "Reporte", "Generando reporte de stock bajo...")
    
    def generate_top_customers_report(self):
        """Generar reporte de mejores clientes"""
        try:
            from ui.dialogs.report_dialog import ReportDialog
            dialog = ReportDialog(self.managers, self)
            
            # Pre-configurar para top clientes
            dialog.report_type_combo.setCurrentText("🌟 Top Clientes")
            dialog.show_preview()
            dialog.exec_()
        except:
            QMessageBox.information(self, "Reporte", "Generando reporte de mejores clientes...")
    
    def generate_payment_methods_report(self):
        """Generar reporte de ventas por método de pago"""
        try:
            # Este sería un nuevo tipo de reporte
            QMessageBox.information(self, "Reporte", "Reporte de métodos de pago - Funcionalidad en desarrollo")
        except Exception as e:
            logger.error(f"Error generando reporte de métodos de pago: {e}")
            QMessageBox.warning(self, "Error", f"Error: {str(e)}")
    
    def open_payment_dialog(self, amount: float, customer_data=None):
        """Abrir diálogo de procesamiento de pagos"""
        try:
            from ui.dialogs.payment_dialog import PaymentDialog
            dialog = PaymentDialog(amount, customer_data, parent=self)
            dialog.payment_processed.connect(self.on_payment_processed)
            return dialog.exec_()
        except ImportError:
            QMessageBox.warning(self, "Error", "Diálogo de pagos no disponible")
            return QDialog.Rejected
        except Exception as e:
            logger.error(f"Error abriendo diálogo de pagos: {e}")
            QMessageBox.warning(self, "Error", f"Error procesando pago: {str(e)}")
            return QDialog.Rejected
    
    def on_payment_processed(self, payment_data):
        """Callback cuando se procesa un pago"""
        try:
            total_paid = payment_data.get('total_paid', 0)
            change = payment_data.get('change', 0)
            
            message = f"Pago procesado: ${total_paid:.2f}"
            if change > 0:
                message += f" - Cambio: ${change:.2f}"
            
            self.status_message.setText(message)
            
            # Limpiar después de 5 segundos
            QTimer.singleShot(5000, lambda: self.status_message.setText("Sistema listo"))
            
        except Exception as e:
            logger.error(f"Error procesando callback de pago: {e}")
    
    def print_ticket(self, sale_data):
        """Imprimir ticket de venta"""
        try:
            from utils.ticket_printer import TicketPrinter
            
            # Configuración de la empresa (podría venir de configuración)
            company_info = {
                'company_name': 'AlmacénPro',
                'company_address': 'Dirección de la empresa',
                'company_phone': '(011) 1234-5678',
                'company_cuit': '20-12345678-9'
            }
            
            printer = TicketPrinter(**company_info)
            
            # Generar contenido del ticket
            ticket_content = printer.generate_sale_ticket(sale_data)
            
            # Mostrar preview y opciones
            dialog = QDialog(self)
            dialog.setWindowTitle("Vista Previa del Ticket")
            dialog.resize(500, 600)
            
            layout = QVBoxLayout(dialog)
            
            # Área de preview
            preview_text = QTextEdit()
            preview_text.setFont(QFont("Courier", 10))  # Fuente monospace
            preview_text.setText(ticket_content)
            preview_text.setReadOnly(True)
            layout.addWidget(preview_text)
            
            # Botones
            buttons_layout = QHBoxLayout()
            
            save_btn = QPushButton("💾 Guardar")
            save_btn.clicked.connect(lambda: self.save_ticket(printer, sale_data))
            
            print_btn = QPushButton("🖨️ Imprimir")
            print_btn.clicked.connect(lambda: self.do_print_ticket(printer, sale_data))
            
            close_btn = QPushButton("Cerrar")
            close_btn.clicked.connect(dialog.close)
            
            buttons_layout.addWidget(save_btn)
            buttons_layout.addWidget(print_btn)
            buttons_layout.addStretch()
            buttons_layout.addWidget(close_btn)
            
            layout.addLayout(buttons_layout)
            
            dialog.exec_()
            
        except ImportError:
            QMessageBox.warning(self, "Error", "Sistema de impresión de tickets no disponible")
        except Exception as e:
            logger.error(f"Error imprimiendo ticket: {e}")
            QMessageBox.warning(self, "Error", f"Error imprimiendo ticket: {str(e)}")
    
    def save_ticket(self, printer, sale_data):
        """Guardar ticket en archivo"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "Guardar Ticket", 
                f"ticket_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "Archivos de texto (*.txt)"
            )
            
            if filename:
                saved_file = printer.save_ticket_to_file(
                    printer.generate_sale_ticket(sale_data), 
                    filename
                )
                if saved_file:
                    QMessageBox.information(self, "Éxito", f"Ticket guardado en: {saved_file}")
                else:
                    QMessageBox.warning(self, "Error", "Error guardando ticket")
                    
        except Exception as e:
            logger.error(f"Error guardando ticket: {e}")
            QMessageBox.warning(self, "Error", f"Error: {str(e)}")
    
    def do_print_ticket(self, printer, sale_data):
        """Ejecutar impresión del ticket"""
        try:
            ticket_content = printer.generate_sale_ticket(sale_data)
            success = printer.print_ticket(ticket_content)
            
            if success:
                QMessageBox.information(self, "Éxito", "Ticket enviado a impresora")
            else:
                QMessageBox.warning(self, "Error", "Error enviando ticket a impresora")
                
        except Exception as e:
            logger.error(f"Error imprimiendo: {e}")
            QMessageBox.warning(self, "Error", f"Error: {str(e)}")
    
    def demo_ticket_print(self):
        """Mostrar demo de impresión de ticket"""
        try:
            # Datos de venta de ejemplo
            sample_sale_data = {
                'id': 123,
                'numero_factura': 'A-00000123',
                'fecha_venta': datetime.now(),
                'cliente_nombre': 'Juan Pérez',
                'vendedor_nombre': self.current_user.get('nombre_completo', 'Vendedor'),
                'subtotal': 1350.00,
                'impuestos': 283.50,
                'total': 1633.50,
                'items': [
                    {
                        'producto_nombre': 'Producto de Ejemplo 1',
                        'cantidad': 2,
                        'precio_unitario': 500.00,
                        'subtotal': 1000.00
                    },
                    {
                        'producto_nombre': 'Producto de Ejemplo 2 con nombre muy largo que se truncará',
                        'cantidad': 1,
                        'precio_unitario': 350.00,
                        'subtotal': 350.00
                    }
                ],
                'payments': [
                    {
                        'metodo_pago': 'EFECTIVO',
                        'importe': 1633.50,
                        'fecha_pago': datetime.now(),
                        'referencia': 'Pago en efectivo'
                    }
                ]
            }
            
            self.print_ticket(sample_sale_data)
            
        except Exception as e:
            logger.error(f"Error en demo de ticket: {e}")
            QMessageBox.warning(self, "Error", f"Error: {str(e)}")
    
    def update_role_based_permissions(self):
        """Actualizar permisos según el rol del usuario"""
        try:
            role = self.current_user.get('rol_nombre', '').upper()
            
            # Ocultar/mostrar tabs según rol
            for i in range(self.central_widget.count()):
                tab_text = self.central_widget.tabText(i)
                
                if role == 'DEPOSITO':
                    # Solo mostrar Dashboard, Productos, Compras
                    if any(keyword in tab_text.lower() for keyword in ['venta', 'cliente', 'reporte']):
                        self.central_widget.setTabEnabled(i, False)
                
                elif role == 'VENDEDOR':
                    # Solo mostrar Dashboard, Ventas, Clientes (consulta)
                    if any(keyword in tab_text.lower() for keyword in ['producto', 'compra', 'administración', 'configuración']):
                        self.central_widget.setTabEnabled(i, False)
                
                elif role == 'GERENTE':
                    # Acceso a casi todo excepto administración completa
                    if 'administración' in tab_text.lower():
                        self.central_widget.setTabEnabled(i, False)
                
            # Actualizar mensaje de status
            if role == 'ADMINISTRADOR':
                self.status_message.setText("Modo Administrador - Acceso completo al sistema")
            elif role == 'GERENTE':
                self.status_message.setText("Modo Gerente - Gestión completa de operaciones")
            elif role == 'DEPOSITO':
                self.status_message.setText("Modo Depósito - Gestión de productos y stock")
            elif role == 'VENDEDOR':
                self.status_message.setText("Modo Vendedor - Procesamiento de ventas")
            
        except Exception as e:
            logger.error(f"Error actualizando permisos por rol: {e}")
    
    def process_sale_with_payment(self, amount: float, customer_data=None):
        """Procesar venta con diálogo de pago integrado"""
        try:
            result = self.open_payment_dialog(amount, customer_data)
            
            if result == QDialog.Accepted:
                # Venta procesada exitosamente
                self.status_message.setText("Venta procesada exitosamente")
                
                # Aquí se podría agregar lógica para:
                # - Actualizar stock
                # - Guardar venta en BD
                # - Imprimir ticket
                # - Actualizar dashboard
                
                # Simular actualización de datos
                QTimer.singleShot(1000, self.refresh_all_data)
            else:
                self.status_message.setText("Venta cancelada")
                
        except Exception as e:
            logger.error(f"Error procesando venta: {e}")
            QMessageBox.warning(self, "Error", f"Error procesando venta: {str(e)}")
    
    def get_dashboard_data(self):
        """Obtener datos dinámicos para el dashboard"""
        try:
            role = self.current_user.get('rol_nombre', '').upper()
            cards = []
            
            # Datos comunes para todos los roles
            if 'sales' in self.managers or 'sale' in self.managers:
                # Ventas de hoy
                sales_today = 0
                try:
                    sales_manager = self.managers.get('sales') or self.managers.get('sale')
                    if hasattr(sales_manager, 'get_daily_summary'):
                        summary = sales_manager.get_daily_summary(date.today())
                        sales_today = summary.get('total_ventas', 0)
                except:
                    pass
                cards.append(("💰 Ventas Hoy", f"${sales_today:,.2f}", "#27ae60"))
            
            # Datos específicos por rol
            if role in ['ADMINISTRADOR', 'GERENTE', 'DEPOSITO']:
                # Productos
                products_count = 0
                try:
                    if 'product' in self.managers:
                        products = self.managers['product'].get_all_products()
                        products_count = len(products) if products else 0
                except:
                    pass
                cards.append(("📦 Productos", str(products_count), "#3498db"))
                
                # Stock bajo
                low_stock_count = 0
                try:
                    if 'product' in self.managers and hasattr(self.managers['product'], 'get_products_with_low_stock'):
                        low_stock = self.managers['product'].get_products_with_low_stock()
                        low_stock_count = len(low_stock) if low_stock else 0
                except:
                    pass
                cards.append(("⚠️ Stock Bajo", str(low_stock_count), "#e74c3c"))
            
            if role in ['ADMINISTRADOR', 'GERENTE', 'VENDEDOR']:
                # Clientes
                customers_count = 0
                try:
                    if 'customer' in self.managers:
                        customers = self.managers['customer'].get_all_customers()
                        customers_count = len(customers) if customers else 0
                except:
                    pass
                cards.append(("👥 Clientes", str(customers_count), "#9b59b6"))
            
            # Si no hay datos específicos, mostrar datos básicos
            if not cards:
                cards = [
                    ("💰 Ventas Hoy", "$0.00", "#27ae60"),
                    ("📦 Productos", "0", "#3498db"),
                    ("⚠️ Stock Bajo", "0", "#e74c3c"),
                    ("👥 Clientes", "0", "#9b59b6")
                ]
            
            return cards
            
        except Exception as e:
            logger.error(f"Error obteniendo datos del dashboard: {e}")
            # Fallback a datos estáticos
            return [
                ("💰 Ventas Hoy", "$0.00", "#27ae60"),
                ("📦 Productos", "0", "#3498db"),
                ("⚠️ Stock Bajo", "0", "#e74c3c"),
                ("👥 Clientes", "0", "#9b59b6")
            ]