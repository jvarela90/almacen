"""
Widget de Compras para AlmacénPro
Gestión completa de órdenes de compra, proveedores y recepción de mercadería
"""

import logging
from datetime import datetime, date
from decimal import Decimal
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

logger = logging.getLogger(__name__)

class PurchasesWidget(QWidget):
    """Widget principal para gestionar compras"""
    
    def __init__(self, purchase_manager, provider_manager, product_manager, user_manager, parent=None):
        super().__init__(parent)
        self.purchase_manager = purchase_manager
        self.provider_manager = provider_manager
        self.product_manager = product_manager
        self.user_manager = user_manager
        
        # Estado de nueva orden
        self.current_order_items = []
        self.current_provider = None
        
        self.init_ui()
        self.load_orders()
        self.load_pending_orders()
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header con estadísticas
        header_widget = self.create_header()
        main_layout.addWidget(header_widget)
        
        # Tabs principales
        tabs_widget = self.create_tabs()
        main_layout.addWidget(tabs_widget)
        
        # Aplicar estilos
        self.setup_styles()
    
    def create_header(self) -> QWidget:
        """Crear header con estadísticas"""
        header = QWidget()
        header.setObjectName("header")
        layout = QHBoxLayout(header)
        
        # Título
        title_layout = QVBoxLayout()
        title = QLabel("🛍️ Gestión de Compras")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2E86AB;")
        title_layout.addWidget(title)
        
        subtitle = QLabel("Órdenes de compra, proveedores y recepción de mercadería")
        subtitle.setStyleSheet("color: #666; font-size: 12px;")
        title_layout.addWidget(subtitle)
        
        layout.addLayout(title_layout)
        
        layout.addStretch()
        
        # Cards de estadísticas
        stats_layout = QHBoxLayout()
        
        # Órdenes pendientes
        self.pending_orders_card = self.create_stat_card("Pendientes", "0", "⏳", "#ff9800")
        stats_layout.addWidget(self.pending_orders_card)
        
        # Órdenes del mes
        self.monthly_orders_card = self.create_stat_card("Este Mes", "0", "📊", "#2E86AB")
        stats_layout.addWidget(self.monthly_orders_card)
        
        # Total gastado
        self.total_spent_card = self.create_stat_card("Total Gastado", "$0", "💰", "#4caf50")
        stats_layout.addWidget(self.total_spent_card)
        
        # Proveedores activos
        self.active_providers_card = self.create_stat_card("Proveedores", "0", "👥", "#9c27b0")
        stats_layout.addWidget(self.active_providers_card)
        
        layout.addLayout(stats_layout)
        
        return header
    
    def create_stat_card(self, title: str, value: str, icon: str, color: str) -> QWidget:
        """Crear tarjeta de estadística"""
        card = QWidget()
        card.setFixedSize(140, 80)
        card.setStyleSheet(f"""
            QWidget {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 8px;
                margin: 2px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 5, 8, 5)
        
        # Valor
        value_layout = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 16px;")
        value_layout.addWidget(icon_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")
        value_label.setObjectName("value_label")
        value_layout.addWidget(value_label)
        
        layout.addLayout(value_layout)
        
        # Título
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 10px; color: #666;")
        layout.addWidget(title_label)
        
        # Guardar referencia al label del valor
        card.value_label = value_label
        
        return card
    
    def create_tabs(self) -> QWidget:
        """Crear tabs principales"""
        tab_widget = QTabWidget()
        
        # Tab 1: Nueva orden
        new_order_tab = self.create_new_order_tab()
        tab_widget.addTab(new_order_tab, "➕ Nueva Orden")
        
        # Tab 2: Órdenes
        orders_tab = self.create_orders_tab()
        tab_widget.addTab(orders_tab, "📋 Órdenes")
        
        # Tab 3: Recepción
        reception_tab = self.create_reception_tab()
        tab_widget.addTab(reception_tab, "📦 Recepción")
        
        # Tab 4: Proveedores
        providers_tab = self.create_providers_tab()
        tab_widget.addTab(providers_tab, "👥 Proveedores")
        
        return tab_widget
    
    def create_new_order_tab(self) -> QWidget:
        """Crear tab para nueva orden"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Panel izquierdo: Formulario de orden
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Información de la orden
        order_info_group = QGroupBox("Información de la Orden")
        order_info_layout = QFormLayout(order_info_group)
        
        # Proveedor
        self.provider_combo = QComboBox()
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        provider_layout = QHBoxLayout()
        provider_layout.addWidget(self.provider_combo)
        
        new_provider_btn = QPushButton("➕")
        new_provider_btn.setFixedWidth(30)
        new_provider_btn.setToolTip("Agregar nuevo proveedor")
        new_provider_btn.clicked.connect(self.add_new_provider)
        provider_layout.addWidget(new_provider_btn)
        
        provider_widget = QWidget()
        provider_widget.setLayout(provider_layout)
        order_info_layout.addRow("Proveedor *:", provider_widget)
        
        # Número de factura
        self.invoice_number_input = QLineEdit()
        self.invoice_number_input.setPlaceholderText("Número de factura del proveedor")
        order_info_layout.addRow("N° Factura:", self.invoice_number_input)
        
        # Fecha de factura
        self.invoice_date_input = QDateEdit()
        self.invoice_date_input.setDate(QDate.currentDate())
        self.invoice_date_input.setCalendarPopup(True)
        order_info_layout.addRow("Fecha Factura:", self.invoice_date_input)
        
        # Fecha de vencimiento
        self.due_date_input = QDateEdit()
        self.due_date_input.setDate(QDate.currentDate().addDays(30))
        self.due_date_input.setCalendarPopup(True)
        order_info_layout.addRow("Vencimiento:", self.due_date_input)
        
        left_layout.addWidget(order_info_group)
        
        # Búsqueda de productos
        product_search_group = QGroupBox("Agregar Productos")
        product_search_layout = QVBoxLayout(product_search_group)
        
        # Barra de búsqueda
        search_layout = QHBoxLayout()
        
        self.product_search_input = QLineEdit()
        self.product_search_input.setPlaceholderText("Buscar producto por nombre o código...")
        self.product_search_input.returnPressed.connect(self.search_products)
        self.product_search_input.textChanged.connect(self.search_products_realtime)
        search_layout.addWidget(self.product_search_input)
        
        search_btn = QPushButton("🔍")
        search_btn.setFixedWidth(40)
        search_btn.clicked.connect(self.search_products)
        search_layout.addWidget(search_btn)
        
        product_search_layout.addLayout(search_layout)
        
        # Lista de productos encontrados
        self.products_list = QListWidget()
        self.products_list.setMaximumHeight(150)
        self.products_list.itemDoubleClicked.connect(self.add_product_to_order)
        self.products_list.hide()
        product_search_layout.addWidget(self.products_list)
        
        left_layout.addWidget(product_search_group)
        
        # Información del proveedor seleccionado
        self.provider_info_group = QGroupBox("Información del Proveedor")
        provider_info_layout = QFormLayout(self.provider_info_group)
        
        self.provider_contact_label = QLabel("-")
        provider_info_layout.addRow("Contacto:", self.provider_contact_label)
        
        self.provider_phone_label = QLabel("-")
        provider_info_layout.addRow("Teléfono:", self.provider_phone_label)
        
        self.provider_terms_label = QLabel("-")
        provider_info_layout.addRow("Condiciones:", self.provider_terms_label)
        
        left_layout.addWidget(self.provider_info_group)
        
        left_layout.addStretch()
        
        layout.addWidget(left_panel, 1)
        
        # Panel derecho: Items de la orden
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Header del carrito
        order_header = QLabel("📋 Items de la Orden")
        order_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2E86AB; padding: 10px;")
        right_layout.addWidget(order_header)
        
        # Tabla de items
        self.order_items_table = QTableWidget()
        self.order_items_table.setColumnCount(6)
        self.order_items_table.setHorizontalHeaderLabels([
            "Producto", "Cantidad", "Precio", "Descuento", "Subtotal", "Acciones"
        ])
        
        # Configurar tabla
        header = self.order_items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        self.order_items_table.verticalHeader().setVisible(False)
        self.order_items_table.setAlternatingRowColors(True)
        right_layout.addWidget(self.order_items_table)
        
        # Totales
        totals_group = QGroupBox("Totales")
        totals_layout = QGridLayout(totals_group)
        
        # Subtotal
        totals_layout.addWidget(QLabel("Subtotal:"), 0, 0)
        self.subtotal_label = QLabel("$0.00")
        self.subtotal_label.setStyleSheet("font-weight: bold;")
        totals_layout.addWidget(self.subtotal_label, 0, 1, alignment=Qt.AlignRight)
        
        # Descuento general
        totals_layout.addWidget(QLabel("Descuento:"), 1, 0)
        self.order_discount_input = QDoubleSpinBox()
        self.order_discount_input.setMinimum(0)
        self.order_discount_input.setMaximum(100)
        self.order_discount_input.setSuffix(" %")
        self.order_discount_input.valueChanged.connect(self.calculate_order_totals)
        totals_layout.addWidget(self.order_discount_input, 1, 1)
        
        # IVA
        totals_layout.addWidget(QLabel("IVA:"), 2, 0)
        self.tax_label = QLabel("$0.00")
        self.tax_label.setStyleSheet("font-weight: bold;")
        totals_layout.addWidget(self.tax_label, 2, 1, alignment=Qt.AlignRight)
        
        # Total
        totals_layout.addWidget(QLabel("TOTAL:"), 3, 0)
        self.total_label = QLabel("$0.00")
        self.total_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2E86AB;")
        totals_layout.addWidget(self.total_label, 3, 1, alignment=Qt.AlignRight)
        
        right_layout.addWidget(totals_group)
        
        # Botones de acción
        actions_layout = QHBoxLayout()
        
        clear_order_btn = QPushButton("🗑️ Limpiar")
        clear_order_btn.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold;")
        clear_order_btn.clicked.connect(self.clear_order)
        actions_layout.addWidget(clear_order_btn)
        
        save_draft_btn = QPushButton("💾 Guardar Borrador")
        save_draft_btn.clicked.connect(self.save_order_draft)
        actions_layout.addWidget(save_draft_btn)
        
        create_order_btn = QPushButton("✅ CREAR ORDEN")
        create_order_btn.setStyleSheet("""
            background-color: #28a745; 
            color: white; 
            font-weight: bold; 
            font-size: 14px; 
            padding: 12px;
        """)
        create_order_btn.clicked.connect(self.create_purchase_order)
        actions_layout.addWidget(create_order_btn)
        
        right_layout.addLayout(actions_layout)
        
        layout.addWidget(right_panel, 1)
        
        # Cargar datos iniciales
        self.load_providers()
        
        return widget
    
    def create_orders_tab(self) -> QWidget:
        """Crear tab de órdenes"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filtros
        filters_layout = QHBoxLayout()
        
        filters_layout.addWidget(QLabel("Desde:"))
        self.orders_start_date = QDateEdit()
        self.orders_start_date.setDate(QDate.currentDate().addDays(-30))
        self.orders_start_date.setCalendarPopup(True)
        filters_layout.addWidget(self.orders_start_date)
        
        filters_layout.addWidget(QLabel("Hasta:"))
        self.orders_end_date = QDateEdit()
        self.orders_end_date.setDate(QDate.currentDate())
        self.orders_end_date.setCalendarPopup(True)
        filters_layout.addWidget(self.orders_end_date)
        
        filters_layout.addWidget(QLabel("Estado:"))
        self.orders_status_filter = QComboBox()
        self.orders_status_filter.addItems([
            "Todos", "PENDIENTE", "CONFIRMADA", "PARCIAL", "RECIBIDA", "CANCELADA"
        ])
        filters_layout.addWidget(self.orders_status_filter)
        
        filters_layout.addWidget(QLabel("Proveedor:"))
        self.orders_provider_filter = QComboBox()
        filters_layout.addWidget(self.orders_provider_filter)
        
        load_orders_btn = QPushButton("🔍 Buscar")
        load_orders_btn.clicked.connect(self.load_orders)
        filters_layout.addWidget(load_orders_btn)
        
        filters_layout.addStretch()
        
        layout.addLayout(filters_layout)
        
        # Tabla de órdenes
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(8)
        self.orders_table.setHorizontalHeaderLabels([
            "N° Orden", "Fecha", "Proveedor", "Total", "Estado", "N° Factura", "Vencimiento", "Acciones"
        ])
        
        # Configurar tabla
        orders_header = self.orders_table.horizontalHeader()
        orders_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        orders_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        orders_header.setSectionResizeMode(2, QHeaderView.Stretch)
        orders_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        orders_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        orders_header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        orders_header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        orders_header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        
        self.orders_table.setAlternatingRowColors(True)
        self.orders_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.orders_table.setSortingEnabled(True)
        
        layout.addWidget(self.orders_table)
        
        return widget
    
    def create_reception_tab(self) -> QWidget:
        """Crear tab de recepción"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Lista de órdenes pendientes de recepción
        pending_group = QGroupBox("Órdenes Pendientes de Recepción")
        pending_layout = QVBoxLayout(pending_group)
        
        self.pending_orders_table = QTableWidget()
        self.pending_orders_table.setColumnCount(6)
        self.pending_orders_table.setHorizontalHeaderLabels([
            "N° Orden", "Proveedor", "Fecha", "Total", "Items Pendientes", "Acciones"
        ])
        
        # Configurar tabla
        pending_header = self.pending_orders_table.horizontalHeader()
        pending_header.setSectionResizeMode(1, QHeaderView.Stretch)
        
        self.pending_orders_table.setAlternatingRowColors(True)
        self.pending_orders_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        pending_layout.addWidget(self.pending_orders_table)
        layout.addWidget(pending_group)
        
        # Historial de recepciones recientes
        recent_group = QGroupBox("Recepciones Recientes")
        recent_layout = QVBoxLayout(recent_group)
        
        self.recent_receptions_table = QTableWidget()
        self.recent_receptions_table.setColumnCount(5)
        self.recent_receptions_table.setHorizontalHeaderLabels([
            "Fecha", "N° Orden", "Proveedor", "Items Recibidos", "Usuario"
        ])
        
        recent_header = self.recent_receptions_table.horizontalHeader()
        recent_header.setSectionResizeMode(2, QHeaderView.Stretch)
        
        self.recent_receptions_table.setAlternatingRowColors(True)
        recent_layout.addWidget(self.recent_receptions_table)
        
        layout.addWidget(recent_group)
        
        return widget
    
    def create_providers_tab(self) -> QWidget:
        """Crear tab de proveedores"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Barra de herramientas de proveedores
        toolbar_layout = QHBoxLayout()
        
        add_provider_btn = QPushButton("➕ Agregar Proveedor")
        add_provider_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
        add_provider_btn.clicked.connect(self.add_new_provider)
        toolbar_layout.addWidget(add_provider_btn)
        
        import_providers_btn = QPushButton("📥 Importar")
        import_providers_btn.clicked.connect(self.import_providers)
        toolbar_layout.addWidget(import_providers_btn)
        
        export_providers_btn = QPushButton("📤 Exportar")
        export_providers_btn.clicked.connect(self.export_providers)
        toolbar_layout.addWidget(export_providers_btn)
        
        toolbar_layout.addStretch()
        
        refresh_providers_btn = QPushButton("🔄 Actualizar")
        refresh_providers_btn.clicked.connect(self.load_providers)
        toolbar_layout.addWidget(refresh_providers_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Tabla de proveedores
        self.providers_table = QTableWidget()
        self.providers_table.setColumnCount(8)
        self.providers_table.setHorizontalHeaderLabels([
            "Nombre", "CUIT", "Teléfono", "Email", "Calificación", "Última Compra", "Total Comprado", "Acciones"
        ])
        
        # Configurar tabla
        providers_header = self.providers_table.horizontalHeader()
        providers_header.setSectionResizeMode(0, QHeaderView.Stretch)
        providers_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        providers_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        providers_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        providers_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        providers_header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        providers_header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        providers_header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        
        self.providers_table.setAlternatingRowColors(True)
        self.providers_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.providers_table.setSortingEnabled(True)
        
        layout.addWidget(self.providers_table)
        
        # Cargar proveedores
        self.load_providers_table()
        
        return widget
    
    def setup_styles(self):
        """Configurar estilos CSS"""
        self.setStyleSheet("""
            QWidget#header {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 10px;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2E86AB;
            }
            
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
                padding: 6px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
            
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, 
            QDoubleSpinBox:focus, QDateEdit:focus {
                border-color: #2E86AB;
                outline: none;
            }
            
            QPushButton {
                padding: 8px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                background-color: #f8f9fa;
            }
            
            QPushButton:hover {
                background-color: #e9ecef;
            }
            
            QTableWidget {
                gridline-color: #e9ecef;
                background-color: white;
                alternate-background-color: #f8f9fa;
                selection-background-color: #2E86AB;
            }
            
            QTableWidget::item {
                padding: 6px;
            }
            
            QHeaderView::section {
                background-color: #e9ecef;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #ced4da;
                font-weight: bold;
            }
            
            QListWidget {
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
            
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f8f9fa;
            }
            
            QListWidget::item:hover {
                background-color: #e9ecef;
            }
            
            QListWidget::item:selected {
                background-color: #2E86AB;
                color: white;
            }
            
            QTabWidget::pane {
                border: 1px solid #ced4da;
                background-color: white;
                border-radius: 4px;
            }
            
            QTabBar::tab {
                background-color: #e9ecef;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
        """)
    
    def load_providers(self):
        """Cargar proveedores en combo"""
        try:
            providers = self.provider_manager.get_all_providers()
            
            self.provider_combo.clear()
            self.provider_combo.addItem("Seleccionar proveedor...", None)
            
            self.orders_provider_filter.clear()
            self.orders_provider_filter.addItem("Todos", None)
            
            for provider in providers:
                self.provider_combo.addItem(provider['nombre'], provider['id'])
                self.orders_provider_filter.addItem(provider['nombre'], provider['id'])
                
        except Exception as e:
            logger.error(f"Error cargando proveedores: {e}")
    
    def load_providers_table(self):
        """Cargar tabla de proveedores"""
        try:
            providers = self.provider_manager.get_all_providers(include_stats=True)
            
            self.providers_table.setRowCount(len(providers))
            
            for i, provider in enumerate(providers):
                # Nombre
                self.providers_table.setItem(i, 0, QTableWidgetItem(provider['nombre']))
                
                # CUIT
                cuit = provider.get('cuit_dni', '')
                self.providers_table.setItem(i, 1, QTableWidgetItem(cuit))
                
                # Teléfono
                phone = provider.get('telefono', '')
                self.providers_table.setItem(i, 2, QTableWidgetItem(phone))
                
                # Email
                email = provider.get('email', '')
                self.providers_table.setItem(i, 3, QTableWidgetItem(email))
                
                # Calificación
                rating = provider.get('calificacion', 5)
                rating_item = QTableWidgetItem("⭐" * rating)
                self.providers_table.setItem(i, 4, rating_item)
                
                # Última compra y total (placeholder)
                self.providers_table.setItem(i, 5, QTableWidgetItem("-"))
                self.providers_table.setItem(i, 6, QTableWidgetItem("$0.00"))
                
                # Botones de acción
                actions_widget = self.create_provider_action_buttons(provider)
                self.providers_table.setCellWidget(i, 7, actions_widget)
            
        except Exception as e:
            logger.error(f"Error cargando tabla de proveedores: {e}")
    
    def create_provider_action_buttons(self, provider) -> QWidget:
        """Crear botones de acción para proveedor"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # Botón editar
        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(25, 25)
        edit_btn.setToolTip("Editar proveedor")
        edit_btn.clicked.connect(lambda: self.edit_provider(provider))
        layout.addWidget(edit_btn)
        
        # Botón ver compras
        purchases_btn = QPushButton("📋")
        purchases_btn.setFixedSize(25, 25)
        purchases_btn.setToolTip("Ver compras")
        purchases_btn.clicked.connect(lambda: self.view_provider_purchases(provider))
        layout.addWidget(purchases_btn)
        
        return widget
    
    def on_provider_changed(self):
        """Manejar cambio de proveedor"""
        provider_id = self.provider_combo.currentData()
        if provider_id:
            try:
                provider = self.provider_manager.get_provider_by_id(provider_id)
                if provider:
                    self.current_provider = provider
                    self.update_provider_info(provider)
                else:
                    self.clear_provider_info()
            except Exception as e:
                logger.error(f"Error obteniendo proveedor: {e}")
        else:
            self.current_provider = None
            self.clear_provider_info()
    
    def update_provider_info(self, provider):
        """Actualizar información del proveedor"""
        self.provider_contact_label.setText(provider.get('contacto_principal', '-'))
        self.provider_phone_label.setText(provider.get('telefono', '-'))
        self.provider_terms_label.setText(provider.get('condiciones_pago', '-'))
    
    def clear_provider_info(self):
        """Limpiar información del proveedor"""
        self.provider_contact_label.setText("-")
        self.provider_phone_label.setText("-")
        self.provider_terms_label.setText("-")
    
    def search_products_realtime(self, search_term):
        """Buscar productos en tiempo real"""
        if len(search_term) < 2:
            self.products_list.hide()
            return
        
        try:
            products = self.product_manager.search_products(search_term, limit=10)
            
            self.products_list.clear()
            
            if products:
                for product in products:
                    item_text = f"{product['nombre']} - ${product.get('precio_compra', 0):.2f}"
                    if product.get('codigo_barras'):
                        item_text += f" ({product['codigo_barras']})"
                    
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, product)
                    self.products_list.addItem(item)
                
                self.products_list.show()
            else:
                self.products_list.hide()
                
        except Exception as e:
            logger.error(f"Error buscando productos: {e}")
    
    def search_products(self):
        """Buscar productos y mostrar el primero"""
        search_term = self.product_search_input.text().strip()
        
        if not search_term:
            return
        
        try:
            products = self.product_manager.search_products(search_term, limit=1)
            if products:
                self.add_product_to_order_direct(products[0])
                self.product_search_input.clear()
                self.products_list.hide()
        except Exception as e:
            logger.error(f"Error buscando productos: {e}")
    
    def add_product_to_order(self, item):
        """Agregar producto seleccionado a la orden"""
        product = item.data(Qt.UserRole)
        if product:
            self.add_product_to_order_direct(product)
            self.product_search_input.clear()
            self.products_list.hide()
    
    def add_product_to_order_direct(self, product, quantity=1):
        """Agregar producto directamente a la orden"""
        try:
            # Verificar si el producto ya está en la orden
            existing_item = None
            for item in self.current_order_items:
                if item['product']['id'] == product['id']:
                    existing_item = item
                    break
            
            if existing_item:
                # Aumentar cantidad
                existing_item['quantity'] += quantity
            else:
                # Agregar nuevo item
                order_item = {
                    'product': product,
                    'quantity': quantity,
                    'unit_price': float(product.get('precio_compra', 0)),
                    'discount_percent': 0,
                    'discount_amount': 0
                }
                self.current_order_items.append(order_item)
            
            self.update_order_display()
            
        except Exception as e:
            logger.error(f"Error agregando producto a la orden: {e}")
    
    def update_order_display(self):
        """Actualizar visualización de la orden"""
        try:
            self.order_items_table.setRowCount(len(self.current_order_items))
            
            for i, item in enumerate(self.current_order_items):
                product = item['product']
                quantity = item['quantity']
                unit_price = item['unit_price']
                discount_percent = item['discount_percent']
                
                # Calcular subtotal
                subtotal = quantity * unit_price
                discount_amount = subtotal * (discount_percent / 100)
                final_subtotal = subtotal - discount_amount
                
                item['discount_amount'] = discount_amount
                
                # Nombre del producto
                self.order_items_table.setItem(i, 0, QTableWidgetItem(product['nombre']))
                
                # Cantidad (editable)
                quantity_spin = QSpinBox()
                quantity_spin.setMinimum(1)
                quantity_spin.setMaximum(9999)
                quantity_spin.setValue(quantity)
                quantity_spin.valueChanged.connect(
                    lambda value, row=i: self.update_order_item_quantity(row, value)
                )
                self.order_items_table.setCellWidget(i, 1, quantity_spin)
                
                # Precio unitario (editable)
                price_spin = QDoubleSpinBox()
                price_spin.setMinimum(0.01)
                price_spin.setMaximum(999999.99)
                price_spin.setDecimals(2)
                price_spin.setPrefix("$ ")
                price_spin.setValue(unit_price)
                price_spin.valueChanged.connect(
                    lambda value, row=i: self.update_order_item_price(row, value)
                )
                self.order_items_table.setCellWidget(i, 2, price_spin)
                
                # Descuento (editable)
                discount_spin = QDoubleSpinBox()
                discount_spin.setMinimum(0)
                discount_spin.setMaximum(100)
                discount_spin.setSuffix("%")
                discount_spin.setValue(discount_percent)
                discount_spin.valueChanged.connect(
                    lambda value, row=i: self.update_order_item_discount(row, value)
                )
                self.order_items_table.setCellWidget(i, 3, discount_spin)
                
                # Subtotal
                subtotal_item = QTableWidgetItem(f"${final_subtotal:.2f}")
                subtotal_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.order_items_table.setItem(i, 4, subtotal_item)
                
                # Botón eliminar
                remove_btn = QPushButton("🗑️")
                remove_btn.setFixedSize(30, 25)
                remove_btn.setToolTip("Eliminar item")
                remove_btn.clicked.connect(lambda checked, row=i: self.remove_order_item(row))
                self.order_items_table.setCellWidget(i, 5, remove_btn)
            
            # Actualizar totales
            self.calculate_order_totals()
            
        except Exception as e:
            logger.error(f"Error actualizando orden: {e}")
    
    def update_order_item_quantity(self, row, new_quantity):
        """Actualizar cantidad de un item"""
        if row < len(self.current_order_items):
            self.current_order_items[row]['quantity'] = new_quantity
            self.update_order_display()
    
    def update_order_item_price(self, row, new_price):
        """Actualizar precio de un item"""
        if row < len(self.current_order_items):
            self.current_order_items[row]['unit_price'] = new_price
            self.update_order_display()
    
    def update_order_item_discount(self, row, new_discount):
        """Actualizar descuento de un item"""
        if row < len(self.current_order_items):
            self.current_order_items[row]['discount_percent'] = new_discount
            self.update_order_display()
    
    def remove_order_item(self, row):
        """Eliminar item de la orden"""
        if 0 <= row < len(self.current_order_items):
            del self.current_order_items[row]
            self.update_order_display()
    
    def calculate_order_totals(self):
        """Calcular totales de la orden"""
        try:
            subtotal = 0
            tax_total = 0
            
            for item in self.current_order_items:
                quantity = item['quantity']
                unit_price = item['unit_price']
                discount_percent = item['discount_percent']
                
                item_subtotal = quantity * unit_price
                item_discount = item_subtotal * (discount_percent / 100)
                item_final = item_subtotal - item_discount
                
                subtotal += item_final
                
                # Calcular IVA
                iva_percent = item['product'].get('iva_porcentaje', 21)
                item_tax = item_final * (iva_percent / 100)
                tax_total += item_tax
            
            # Descuento general
            general_discount_percent = self.order_discount_input.value()
            general_discount_amount = subtotal * (general_discount_percent / 100)
            
            # Total final
            final_subtotal = subtotal - general_discount_amount
            total = final_subtotal + tax_total
            
            # Actualizar labels
            self.subtotal_label.setText(f"${subtotal:.2f}")
            self.tax_label.setText(f"${tax_total:.2f}")
            self.total_label.setText(f"${total:.2f}")
            
        except Exception as e:
            logger.error(f"Error calculando totales: {e}")
    
    def clear_order(self):
        """Limpiar orden actual"""
        if self.current_order_items:
            reply = QMessageBox.question(self, "Limpiar Orden", 
                "¿Está seguro de que desea limpiar la orden actual?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                self.current_order_items.clear()
                self.current_provider = None
                self.provider_combo.setCurrentIndex(0)
                self.invoice_number_input.clear()
                self.order_discount_input.setValue(0)
                self.update_order_display()
    
    def create_purchase_order(self):
        """Crear orden de compra"""
        if not self.current_order_items:
            QMessageBox.warning(self, "Orden Vacía", "Agregue productos a la orden antes de crearla")
            return
        
        if not self.current_provider:
            QMessageBox.warning(self, "Proveedor Requerido", "Seleccione un proveedor")
            return
        
        try:
            # Preparar datos de la orden
            order_data = {
                'proveedor_id': self.current_provider['id'],
                'usuario_id': self.user_manager.current_user['id'],
                'numero_factura': self.invoice_number_input.text().strip() or None,
                'fecha_factura': self.invoice_date_input.date().toString('yyyy-MM-dd'),
                'fecha_vencimiento': self.due_date_input.date().toString('yyyy-MM-dd'),
                'descuento': 0,  # Se calculará en el manager
                'observaciones': '',
                'items': []
            }
            
            # Agregar items
            for order_item in self.current_order_items:
                item_data = {
                    'producto_id': order_item['product']['id'],
                    'cantidad': order_item['quantity'],
                    'precio_unitario': order_item['unit_price'],
                    'descuento_porcentaje': order_item['discount_percent'],
                    'iva_porcentaje': order_item['product'].get('iva_porcentaje', 21)
                }
                order_data['items'].append(item_data)
            
            # Crear orden
            success, message, order_id = self.purchase_manager.create_purchase_order(order_data)
            
            if success:
                QMessageBox.information(self, "Orden Creada", message)
                
                # Limpiar orden y recargar datos
                self.clear_order()
                self.load_orders()
                self.load_pending_orders()
            else:
                QMessageBox.critical(self, "Error", message)
                
        except Exception as e:
            logger.error(f"Error creando orden: {e}")
            QMessageBox.critical(self, "Error", f"Error creando orden: {str(e)}")
    
    def load_orders(self):
        """Cargar órdenes de compra"""
        try:
            start_date = self.orders_start_date.date().toString('yyyy-MM-dd')
            end_date = self.orders_end_date.date().toString('yyyy-MM-dd')
            status = self.orders_status_filter.currentText()
            provider_id = self.orders_provider_filter.currentData()
            
            status_filter = None if status == "Todos" else status
            
            orders = self.purchase_manager.get_purchases_by_date_range(
                start_date, end_date, provider_id, status_filter
            )
            
            self.orders_table.setRowCount(len(orders))
            
            for i, order in enumerate(orders):
                # N° Orden
                self.orders_table.setItem(i, 0, QTableWidgetItem(str(order['id'])))
                
                # Fecha
                date_str = order['fecha_compra'][:10]
                self.orders_table.setItem(i, 1, QTableWidgetItem(date_str))
                
                # Proveedor
                self.orders_table.setItem(i, 2, QTableWidgetItem(order.get('proveedor_nombre', '')))
                
                # Total
                total_item = QTableWidgetItem(f"${order['total']:.2f}")
                total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.orders_table.setItem(i, 3, total_item)
                
                # Estado
                status_item = QTableWidgetItem(order['estado'])
                if order['estado'] == 'PENDIENTE':
                    status_item.setForeground(QColor('#ff9800'))
                elif order['estado'] == 'RECIBIDA':
                    status_item.setForeground(QColor('#4caf50'))
                elif order['estado'] == 'CANCELADA':
                    status_item.setForeground(QColor('#f44336'))
                self.orders_table.setItem(i, 4, status_item)
                
                # N° Factura
                self.orders_table.setItem(i, 5, QTableWidgetItem(order.get('numero_factura', '')))
                
                # Vencimiento
                due_date = order.get('fecha_vencimiento', '')
                if due_date:
                    due_date = due_date[:10]
                self.orders_table.setItem(i, 6, QTableWidgetItem(due_date))
                
                # Botones de acción
                actions_widget = self.create_order_action_buttons(order)
                self.orders_table.setCellWidget(i, 7, actions_widget)
            
        except Exception as e:
            logger.error(f"Error cargando órdenes: {e}")
    
    def create_order_action_buttons(self, order) -> QWidget:
        """Crear botones de acción para orden"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # Botón ver
        view_btn = QPushButton("👁️")
        view_btn.setFixedSize(25, 25)
        view_btn.setToolTip("Ver detalles")
        view_btn.clicked.connect(lambda: self.view_order_details(order))
        layout.addWidget(view_btn)
        
        # Botón recibir (solo si está pendiente)
        if order['estado'] in ['PENDIENTE', 'CONFIRMADA', 'PARCIAL']:
            receive_btn = QPushButton("📦")
            receive_btn.setFixedSize(25, 25)
            receive_btn.setToolTip("Recibir mercadería")
            receive_btn.clicked.connect(lambda: self.receive_order(order))
            layout.addWidget(receive_btn)
        
        return widget
    
    def load_pending_orders(self):
        """Cargar órdenes pendientes de recepción"""
        try:
            # Placeholder - aquí se cargarían las órdenes pendientes
            # orders = self.purchase_manager.get_pending_orders()
            pass
        except Exception as e:
            logger.error(f"Error cargando órdenes pendientes: {e}")
    
    # Métodos placeholder para funciones adicionales
    def save_order_draft(self):
        """Guardar borrador de orden"""
        QMessageBox.information(self, "Borrador", "Función de guardar borrador en desarrollo")
    
    def add_new_provider(self):
        """Agregar nuevo proveedor"""
        QMessageBox.information(self, "Nuevo Proveedor", "Función de agregar proveedor en desarrollo")
    
    def edit_provider(self, provider):
        """Editar proveedor"""
        QMessageBox.information(self, "Editar Proveedor", f"Editar: {provider['nombre']}")
    
    def view_provider_purchases(self, provider):
        """Ver compras del proveedor"""
        QMessageBox.information(self, "Compras", f"Compras de: {provider['nombre']}")
    
    def view_order_details(self, order):
        """Ver detalles de orden"""
        QMessageBox.information(self, "Detalles", f"Orden #{order['id']}")
    
    def receive_order(self, order):
        """Recibir mercadería de orden"""
        QMessageBox.information(self, "Recepción", f"Recibir orden #{order['id']}")
    
    def import_providers(self):
        """Importar proveedores"""
        QMessageBox.information(self, "Importar", "Función de importar proveedores en desarrollo")
    
    def export_providers(self):
        """Exportar proveedores"""
        QMessageBox.information(self, "Exportar", "Función de exportar proveedores en desarrollo")