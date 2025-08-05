"""
Widget de Stock para AlmacénPro
Gestión completa de inventario, productos y movimientos de stock
"""

import logging
from datetime import datetime, date
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

logger = logging.getLogger(__name__)

class StockWidget(QWidget):
    """Widget principal para gestionar stock e inventario"""
    
    def __init__(self, product_manager, provider_manager, user_manager, parent=None):
        super().__init__(parent)
        self.product_manager = product_manager
        self.provider_manager = provider_manager
        self.user_manager = user_manager
        
        self.init_ui()
        self.setup_filters()
        self.load_products()
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header con título y estadísticas
        header_widget = self.create_header()
        main_layout.addWidget(header_widget)
        
        # Barra de herramientas y filtros
        toolbar_widget = self.create_toolbar()
        main_layout.addWidget(toolbar_widget)
        
        # Panel principal con tabs
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
        title = QLabel("📦 Gestión de Stock")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2E86AB;")
        title_layout.addWidget(title)
        
        subtitle = QLabel("Control completo de inventario y productos")
        subtitle.setStyleSheet("color: #666; font-size: 12px;")
        title_layout.addWidget(subtitle)
        
        layout.addLayout(title_layout)
        
        layout.addStretch()
        
        # Cards de estadísticas
        stats_layout = QHBoxLayout()
        
        # Total de productos
        self.total_products_card = self.create_stat_card("Total Productos", "0", "📦", "#2E86AB")
        stats_layout.addWidget(self.total_products_card)
        
        # Stock bajo
        self.low_stock_card = self.create_stat_card("Stock Bajo", "0", "⚠️", "#ff9800")
        stats_layout.addWidget(self.low_stock_card)
        
        # Sin stock
        self.no_stock_card = self.create_stat_card("Sin Stock", "0", "❌", "#f44336")
        stats_layout.addWidget(self.no_stock_card)
        
        # Valor del stock
        self.stock_value_card = self.create_stat_card("Valor Stock", "$0", "💰", "#4caf50")
        stats_layout.addWidget(self.stock_value_card)
        
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
    
    def create_toolbar(self) -> QWidget:
        """Crear barra de herramientas"""
        toolbar = QWidget()
        layout = QVBoxLayout(toolbar)
        
        # Primera fila: Acciones principales
        actions_layout = QHBoxLayout()
        
        add_product_btn = QPushButton("➕ Agregar Producto")
        add_product_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 8px 16px;")
        add_product_btn.clicked.connect(self.add_product)
        actions_layout.addWidget(add_product_btn)
        
        import_btn = QPushButton("📥 Importar")
        import_btn.clicked.connect(self.import_products)
        actions_layout.addWidget(import_btn)
        
        export_btn = QPushButton("📤 Exportar")
        export_btn.clicked.connect(self.export_products)
        actions_layout.addWidget(export_btn)
        
        stock_adjustment_btn = QPushButton("📊 Ajuste de Stock")
        stock_adjustment_btn.clicked.connect(self.stock_adjustment)
        actions_layout.addWidget(stock_adjustment_btn)
        
        inventory_btn = QPushButton("📋 Inventario")
        inventory_btn.clicked.connect(self.inventory_report)
        actions_layout.addWidget(inventory_btn)
        
        actions_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Actualizar")
        refresh_btn.clicked.connect(self.refresh_data)
        actions_layout.addWidget(refresh_btn)
        
        layout.addLayout(actions_layout)
        
        # Segunda fila: Filtros y búsqueda
        filters_layout = QHBoxLayout()
        
        # Búsqueda
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Buscar:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombre, código...")
        self.search_input.textChanged.connect(self.filter_products)
        search_layout.addWidget(self.search_input)
        
        filters_layout.addLayout(search_layout)
        
        # Filtro por categoría
        filters_layout.addWidget(QLabel("Categoría:"))
        self.category_filter = QComboBox()
        self.category_filter.currentTextChanged.connect(self.filter_products)
        filters_layout.addWidget(self.category_filter)
        
        # Filtro por estado de stock
        filters_layout.addWidget(QLabel("Estado:"))
        self.stock_status_filter = QComboBox()
        self.stock_status_filter.addItems([
            "Todos", "Stock OK", "Stock Bajo", "Sin Stock", "Inactivos"
        ])
        self.stock_status_filter.currentTextChanged.connect(self.filter_products)
        filters_layout.addWidget(self.stock_status_filter)
        
        # Filtro por proveedor
        filters_layout.addWidget(QLabel("Proveedor:"))
        self.provider_filter = QComboBox()
        self.provider_filter.currentTextChanged.connect(self.filter_products)
        filters_layout.addWidget(self.provider_filter)
        
        filters_layout.addStretch()
        
        layout.addLayout(filters_layout)
        
        return toolbar
    
    def create_tabs(self) -> QWidget:
        """Crear tabs principales"""
        tab_widget = QTabWidget()
        
        # Tab 1: Lista de productos
        products_tab = self.create_products_tab()
        tab_widget.addTab(products_tab, "📦 Productos")
        
        # Tab 2: Movimientos de stock
        movements_tab = self.create_movements_tab()
        tab_widget.addTab(movements_tab, "📊 Movimientos")
        
        # Tab 3: Alertas
        alerts_tab = self.create_alerts_tab()
        tab_widget.addTab(alerts_tab, "⚠️ Alertas")
        
        # Tab 4: Valorización
        valuation_tab = self.create_valuation_tab()
        tab_widget.addTab(valuation_tab, "💰 Valorización")
        
        return tab_widget
    
    def create_products_tab(self) -> QWidget:
        """Crear tab de productos"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Tabla de productos
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(10)
        self.products_table.setHorizontalHeaderLabels([
            "Código", "Producto", "Categoría", "Stock", "Mín.", "Precio", 
            "Estado", "Proveedor", "Ubicación", "Acciones"
        ])
        
        # Configurar tabla
        header = self.products_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Producto
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Categoría
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Stock
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Mín
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Precio
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Estado
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Proveedor
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)  # Ubicación
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents)  # Acciones
        
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.products_table.setSortingEnabled(True)
        
        # Menú contextual
        self.products_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.products_table.customContextMenuRequested.connect(self.show_product_context_menu)
        
        layout.addWidget(self.products_table)
        
        return widget
    
    def create_movements_tab(self) -> QWidget:
        """Crear tab de movimientos"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filtros para movimientos
        movements_filters = QHBoxLayout()
        
        movements_filters.addWidget(QLabel("Desde:"))
        self.movements_start_date = QDateEdit()
        self.movements_start_date.setDate(QDate.currentDate().addDays(-30))
        self.movements_start_date.setCalendarPopup(True)
        movements_filters.addWidget(self.movements_start_date)
        
        movements_filters.addWidget(QLabel("Hasta:"))
        self.movements_end_date = QDateEdit()
        self.movements_end_date.setDate(QDate.currentDate())
        self.movements_end_date.setCalendarPopup(True)
        movements_filters.addWidget(self.movements_end_date)
        
        movements_filters.addWidget(QLabel("Tipo:"))
        self.movement_type_filter = QComboBox()
        self.movement_type_filter.addItems(["Todos", "ENTRADA", "SALIDA", "AJUSTE"])
        movements_filters.addWidget(self.movement_type_filter)
        
        load_movements_btn = QPushButton("Cargar Movimientos")
        load_movements_btn.clicked.connect(self.load_movements)
        movements_filters.addWidget(load_movements_btn)
        
        movements_filters.addStretch()
        
        layout.addLayout(movements_filters)
        
        # Tabla de movimientos
        self.movements_table = QTableWidget()
        self.movements_table.setColumnCount(8)
        self.movements_table.setHorizontalHeaderLabels([
            "Fecha", "Producto", "Tipo", "Motivo", "Cantidad", "Stock Anterior", "Stock Nuevo", "Usuario"
        ])
        
        # Configurar tabla de movimientos
        movements_header = self.movements_table.horizontalHeader()
        movements_header.setSectionResizeMode(1, QHeaderView.Stretch)
        movements_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        
        self.movements_table.setAlternatingRowColors(True)
        self.movements_table.setSortingEnabled(True)
        
        layout.addWidget(self.movements_table)
        
        return widget
    
    def create_alerts_tab(self) -> QWidget:
        """Crear tab de alertas"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Configuración de alertas
        alerts_config = QGroupBox("Configuración de Alertas")
        config_layout = QFormLayout(alerts_config)
        
        self.low_stock_threshold = QSpinBox()
        self.low_stock_threshold.setMinimum(0)
        self.low_stock_threshold.setMaximum(100)
        self.low_stock_threshold.setValue(5)
        config_layout.addRow("Umbral Stock Bajo:", self.low_stock_threshold)
        
        self.expiry_warning_days = QSpinBox()
        self.expiry_warning_days.setMinimum(1)
        self.expiry_warning_days.setMaximum(365)
        self.expiry_warning_days.setValue(30)
        config_layout.addRow("Días Alerta Vencimiento:", self.expiry_warning_days)
        
        layout.addWidget(alerts_config)
        
        # Lista de alertas
        alerts_list = QGroupBox("Alertas Activas")
        alerts_layout = QVBoxLayout(alerts_list)
        
        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(5)
        self.alerts_table.setHorizontalHeaderLabels([
            "Tipo", "Producto", "Mensaje", "Prioridad", "Fecha"
        ])
        
        alerts_header = self.alerts_table.horizontalHeader()
        alerts_header.setSectionResizeMode(1, QHeaderView.Stretch)
        alerts_header.setSectionResizeMode(2, QHeaderView.Stretch)
        
        self.alerts_table.setAlternatingRowColors(True)
        alerts_layout.addWidget(self.alerts_table)
        
        # Botones de alertas
        alerts_buttons = QHBoxLayout()
        
        refresh_alerts_btn = QPushButton("🔄 Actualizar Alertas")
        refresh_alerts_btn.clicked.connect(self.load_alerts)
        alerts_buttons.addWidget(refresh_alerts_btn)
        
        resolve_alert_btn = QPushButton("✅ Resolver Seleccionada")
        resolve_alert_btn.clicked.connect(self.resolve_alert)
        alerts_buttons.addWidget(resolve_alert_btn)
        
        alerts_buttons.addStretch()
        alerts_layout.addLayout(alerts_buttons)
        
        layout.addWidget(alerts_list)
        
        return widget
    
    def create_valuation_tab(self) -> QWidget:
        """Crear tab de valorización"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Resumen de valorización
        valuation_summary = QGroupBox("Resumen de Valorización")
        summary_layout = QGridLayout(valuation_summary)
        
        # Métricas de valorización
        self.total_products_label = QLabel("0")
        self.total_products_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2E86AB;")
        summary_layout.addWidget(QLabel("Total Productos:"), 0, 0)
        summary_layout.addWidget(self.total_products_label, 0, 1)
        
        self.total_units_label = QLabel("0")
        self.total_units_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2E86AB;")
        summary_layout.addWidget(QLabel("Total Unidades:"), 0, 2)
        summary_layout.addWidget(self.total_units_label, 0, 3)
        
        self.purchase_value_label = QLabel("$0.00")
        self.purchase_value_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ff9800;")
        summary_layout.addWidget(QLabel("Valor Compra:"), 1, 0)
        summary_layout.addWidget(self.purchase_value_label, 1, 1)
        
        self.sale_value_label = QLabel("$0.00")
        self.sale_value_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4caf50;")
        summary_layout.addWidget(QLabel("Valor Venta:"), 1, 2)
        summary_layout.addWidget(self.sale_value_label, 1, 3)
        
        self.profit_margin_label = QLabel("$0.00")
        self.profit_margin_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #17a2b8;")
        summary_layout.addWidget(QLabel("Ganancia Potencial:"), 2, 0)
        summary_layout.addWidget(self.profit_margin_label, 2, 1)
        
        layout.addWidget(valuation_summary)
        
        # Valorización por categoría
        category_valuation = QGroupBox("Valorización por Categoría")
        category_layout = QVBoxLayout(category_valuation)
        
        self.category_valuation_table = QTableWidget()
        self.category_valuation_table.setColumnCount(6)
        self.category_valuation_table.setHorizontalHeaderLabels([
            "Categoría", "Productos", "Unidades", "Valor Compra", "Valor Venta", "Ganancia"
        ])
        
        category_header = self.category_valuation_table.horizontalHeader()
        category_header.setSectionResizeMode(0, QHeaderView.Stretch)
        
        self.category_valuation_table.setAlternatingRowColors(True)
        category_layout.addWidget(self.category_valuation_table)
        
        layout.addWidget(category_valuation)
        
        # Botón para actualizar valorización
        update_valuation_btn = QPushButton("🔄 Actualizar Valorización")
        update_valuation_btn.clicked.connect(self.update_valuation)
        layout.addWidget(update_valuation_btn)
        
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
            
            QLineEdit, QComboBox, QSpinBox, QDateEdit {
                padding: 6px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
            
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {
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
    
    def setup_filters(self):
        """Configurar filtros de búsqueda"""
        try:
            # Cargar categorías
            categories = self.product_manager.get_categories()
            self.category_filter.addItem("Todas las categorías", None)
            for category in categories:
                self.category_filter.addItem(category['nombre'], category['id'])
            
            # Cargar proveedores
            providers = self.provider_manager.get_all_providers()
            self.provider_filter.addItem("Todos los proveedores", None)
            for provider in providers:
                self.provider_filter.addItem(provider['nombre'], provider['id'])
                
        except Exception as e:
            logger.error(f"Error configurando filtros: {e}")
    
    def load_products(self):
        """Cargar productos en la tabla"""
        try:
            products = self.product_manager.get_all_products(active_only=False)
            
            self.products_table.setRowCount(len(products))
            
            for i, product in enumerate(products):
                # Código
                code = product.get('codigo_barras') or product.get('codigo_interno', '')
                self.products_table.setItem(i, 0, QTableWidgetItem(code))
                
                # Nombre
                self.products_table.setItem(i, 1, QTableWidgetItem(product['nombre']))
                
                # Categoría
                category = product.get('categoria_nombre', 'Sin categoría')
                self.products_table.setItem(i, 2, QTableWidgetItem(category))
                
                # Stock
                stock_item = QTableWidgetItem(str(product['stock_actual']))
                stock_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
                # Colorear según estado del stock
                if product['stock_actual'] <= 0:
                    stock_item.setForeground(QColor('#f44336'))
                elif product['stock_actual'] <= product.get('stock_minimo', 0):
                    stock_item.setForeground(QColor('#ff9800'))
                else:
                    stock_item.setForeground(QColor('#4caf50'))
                
                self.products_table.setItem(i, 3, stock_item)
                
                # Stock mínimo
                min_stock_item = QTableWidgetItem(str(product.get('stock_minimo', 0)))
                min_stock_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.products_table.setItem(i, 4, min_stock_item)
                
                # Precio
                price_item = QTableWidgetItem(f"${product.get('precio_venta', 0):.2f}")
                price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.products_table.setItem(i, 5, price_item)
                
                # Estado
                if not product.get('activo', True):
                    status = "Inactivo"
                    status_color = QColor('#6c757d')
                elif product['stock_actual'] <= 0:
                    status = "Sin Stock"
                    status_color = QColor('#f44336')
                elif product['stock_actual'] <= product.get('stock_minimo', 0):
                    status = "Stock Bajo"
                    status_color = QColor('#ff9800')
                else:
                    status = "OK"
                    status_color = QColor('#4caf50')
                
                status_item = QTableWidgetItem(status)
                status_item.setForeground(status_color)
                self.products_table.setItem(i, 6, status_item)
                
                # Proveedor
                provider = product.get('proveedor_nombre', 'Sin proveedor')
                self.products_table.setItem(i, 7, QTableWidgetItem(provider))
                
                # Ubicación
                location = product.get('ubicacion', '')
                self.products_table.setItem(i, 8, QTableWidgetItem(location))
                
                # Botones de acción
                actions_widget = self.create_action_buttons(product)
                self.products_table.setCellWidget(i, 9, actions_widget)
            
            # Actualizar estadísticas
            self.update_statistics()
            
        except Exception as e:
            logger.error(f"Error cargando productos: {e}")
            QMessageBox.critical(self, "Error", f"Error cargando productos: {str(e)}")
    
    def create_action_buttons(self, product) -> QWidget:
        """Crear botones de acción para cada producto"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # Botón editar
        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(25, 25)
        edit_btn.setToolTip("Editar producto")
        edit_btn.clicked.connect(lambda: self.edit_product(product))
        layout.addWidget(edit_btn)
        
        # Botón ajustar stock
        adjust_btn = QPushButton("📊")
        adjust_btn.setFixedSize(25, 25)
        adjust_btn.setToolTip("Ajustar stock")
        adjust_btn.clicked.connect(lambda: self.adjust_product_stock(product))
        layout.addWidget(adjust_btn)
        
        # Botón ver movimientos
        movements_btn = QPushButton("📋")
        movements_btn.setFixedSize(25, 25)
        movements_btn.setToolTip("Ver movimientos")
        movements_btn.clicked.connect(lambda: self.view_product_movements(product))
        layout.addWidget(movements_btn)
        
        return widget
    
    def filter_products(self):
        """Filtrar productos según criterios"""
        search_text = self.search_input.text().lower()
        category_id = self.category_filter.currentData()
        status_filter = self.stock_status_filter.currentText()
        provider_id = self.provider_filter.currentData()
        
        for row in range(self.products_table.rowCount()):
            show_row = True
            
            # Filtro de búsqueda
            if search_text:
                product_name = self.products_table.item(row, 1).text().lower()
                product_code = self.products_table.item(row, 0).text().lower()
                if search_text not in product_name and search_text not in product_code:
                    show_row = False
            
            # Filtro de estado
            if status_filter != "Todos":
                status = self.products_table.item(row, 6).text()
                if status_filter == "Stock OK" and status != "OK":
                    show_row = False
                elif status_filter == "Stock Bajo" and status != "Stock Bajo":
                    show_row = False
                elif status_filter == "Sin Stock" and status != "Sin Stock":
                    show_row = False
                elif status_filter == "Inactivos" and status != "Inactivo":
                    show_row = False
            
            self.products_table.setRowHidden(row, not show_row)
    
    def update_statistics(self):
        """Actualizar estadísticas del header"""
        try:
            # Obtener estadísticas de productos
            stats = self.product_manager.get_product_stats()
            
            # Actualizar cards
            self.total_products_card.value_label.setText(str(stats.get('productos_activos', 0)))
            self.low_stock_card.value_label.setText(str(stats.get('stock_bajo', 0)))
            self.no_stock_card.value_label.setText(str(stats.get('sin_stock', 0)))
            
            # Valor del stock
            stock_value = stats.get('valor_stock', {})
            value_text = f"${stock_value.get('valor_venta', 0):,.0f}"
            self.stock_value_card.value_label.setText(value_text)
            
        except Exception as e:
            logger.error(f"Error actualizando estadísticas: {e}")
    
    def show_product_context_menu(self, position):
        """Mostrar menú contextual para productos"""
        if self.products_table.itemAt(position) is None:
            return
        
        menu = QMenu(self)
        
        edit_action = menu.addAction("✏️ Editar Producto")
        adjust_action = menu.addAction("📊 Ajustar Stock")
        movements_action = menu.addAction("📋 Ver Movimientos")
        menu.addSeparator()
        duplicate_action = menu.addAction("📋 Duplicar Producto")
        deactivate_action = menu.addAction("❌ Desactivar Producto")
        
        action = menu.exec_(self.products_table.mapToGlobal(position))
        
        row = self.products_table.currentRow()
        if row >= 0:
            # Aquí se implementarían las acciones según la selección
            if action == edit_action:
                # self.edit_product_at_row(row)
                pass
            elif action == adjust_action:
                # self.adjust_stock_at_row(row)
                pass
            # ... etc
    
    def load_movements(self):
        """Cargar movimientos de stock"""
        try:
            start_date = self.movements_start_date.date().toString('yyyy-MM-dd')
            end_date = self.movements_end_date.date().toString('yyyy-MM-dd')
            
            movements = self.product_manager.get_stock_movements(days=30)
            
            self.movements_table.setRowCount(len(movements))
            
            for i, movement in enumerate(movements):
                # Fecha
                date_str = movement['fecha_movimiento'][:16].replace('T', ' ')
                self.movements_table.setItem(i, 0, QTableWidgetItem(date_str))
                
                # Producto
                self.movements_table.setItem(i, 1, QTableWidgetItem(movement.get('producto_nombre', '')))
                
                # Tipo
                tipo_item = QTableWidgetItem(movement['tipo_movimiento'])
                if movement['tipo_movimiento'] == 'ENTRADA':
                    tipo_item.setForeground(QColor('#4caf50'))
                elif movement['tipo_movimiento'] == 'SALIDA':
                    tipo_item.setForeground(QColor('#f44336'))
                else:
                    tipo_item.setForeground(QColor('#ff9800'))
                self.movements_table.setItem(i, 2, tipo_item)
                
                # Motivo
                self.movements_table.setItem(i, 3, QTableWidgetItem(movement.get('motivo', '')))
                
                # Cantidad
                cantidad_item = QTableWidgetItem(str(movement['cantidad_movimiento']))
                cantidad_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.movements_table.setItem(i, 4, cantidad_item)
                
                # Stock anterior
                if movement.get('cantidad_anterior') is not None:
                    anterior_item = QTableWidgetItem(str(movement['cantidad_anterior']))
                    anterior_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.movements_table.setItem(i, 5, anterior_item)
                
                # Stock nuevo
                if movement.get('cantidad_nueva') is not None:
                    nuevo_item = QTableWidgetItem(str(movement['cantidad_nueva']))
                    nuevo_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.movements_table.setItem(i, 6, nuevo_item)
                
                # Usuario
                self.movements_table.setItem(i, 7, QTableWidgetItem(movement.get('usuario_nombre', '')))
            
        except Exception as e:
            logger.error(f"Error cargando movimientos: {e}")
            QMessageBox.critical(self, "Error", f"Error cargando movimientos: {str(e)}")
    
    def load_alerts(self):
        """Cargar alertas de stock"""
        try:
            alerts = []
            
            # Productos con stock bajo
            low_stock_products = self.product_manager.get_low_stock_products()
            for product in low_stock_products:
                if product['stock_actual'] <= 0:
                    alert_type = "Sin Stock"
                    priority = "ALTA"
                    message = f"Producto sin stock: {product['nombre']}"
                else:
                    alert_type = "Stock Bajo"
                    priority = "MEDIA"
                    message = f"Stock bajo: {product['stock_actual']} unidades (mín: {product['stock_minimo']})"
                
                alerts.append({
                    'tipo': alert_type,
                    'producto': product['nombre'],
                    'mensaje': message,
                    'prioridad': priority,
                    'fecha': datetime.now().strftime('%Y-%m-%d %H:%M')
                })
            
            # Actualizar tabla de alertas
            self.alerts_table.setRowCount(len(alerts))
            
            for i, alert in enumerate(alerts):
                self.alerts_table.setItem(i, 0, QTableWidgetItem(alert['tipo']))
                self.alerts_table.setItem(i, 1, QTableWidgetItem(alert['producto']))
                self.alerts_table.setItem(i, 2, QTableWidgetItem(alert['mensaje']))
                
                priority_item = QTableWidgetItem(alert['prioridad'])
                if alert['prioridad'] == 'ALTA':
                    priority_item.setForeground(QColor('#f44336'))
                elif alert['prioridad'] == 'MEDIA':
                    priority_item.setForeground(QColor('#ff9800'))
                else:
                    priority_item.setForeground(QColor('#4caf50'))
                self.alerts_table.setItem(i, 3, priority_item)
                
                self.alerts_table.setItem(i, 4, QTableWidgetItem(alert['fecha']))
            
        except Exception as e:
            logger.error(f"Error cargando alertas: {e}")
    
    def update_valuation(self):
        """Actualizar valorización del stock"""
        try:
            # Valorización general
            stock_value = self.product_manager.calculate_stock_value()
            
            self.total_products_label.setText(str(stock_value.get('total_productos', 0)))
            self.total_units_label.setText(f"{stock_value.get('total_unidades', 0):,}")
            self.purchase_value_label.setText(f"${stock_value.get('valor_compra', 0):,.2f}")
            self.sale_value_label.setText(f"${stock_value.get('valor_venta', 0):,.2f}")
            self.profit_margin_label.setText(f"${stock_value.get('ganancia_potencial', 0):,.2f}")
            
            # Valorización por categoría (placeholder)
            # Aquí se implementaría la lógica para calcular por categoría
            
        except Exception as e:
            logger.error(f"Error actualizando valorización: {e}")
    
    # Métodos de acción (placeholders)
    def add_product(self):
        """Agregar nuevo producto"""
        QMessageBox.information(self, "Agregar Producto", "Función de agregar producto en desarrollo")
    
    def edit_product(self, product):
        """Editar producto"""
        QMessageBox.information(self, "Editar Producto", f"Editar producto: {product['nombre']}")
    
    def adjust_product_stock(self, product):
        """Ajustar stock de producto"""
        QMessageBox.information(self, "Ajustar Stock", f"Ajustar stock: {product['nombre']}")
    
    def view_product_movements(self, product):
        """Ver movimientos de producto"""
        QMessageBox.information(self, "Movimientos", f"Movimientos: {product['nombre']}")
    
    def import_products(self):
        """Importar productos desde archivo"""
        QMessageBox.information(self, "Importar", "Función de importar productos en desarrollo")
    
    def export_products(self):
        """Exportar productos a archivo"""
        QMessageBox.information(self, "Exportar", "Función de exportar productos en desarrollo")
    
    def stock_adjustment(self):
        """Ajuste masivo de stock"""
        QMessageBox.information(self, "Ajuste Stock", "Función de ajuste masivo en desarrollo")
    
    def inventory_report(self):
        """Generar reporte de inventario"""
        QMessageBox.information(self, "Inventario", "Función de reporte de inventario en desarrollo")
    
    def resolve_alert(self):
        """Resolver alerta seleccionada"""
        current_row = self.alerts_table.currentRow()
        if current_row >= 0:
            QMessageBox.information(self, "Resolver", "Función de resolver alerta en desarrollo")
    
    def refresh_data(self):
        """Actualizar todos los datos"""
        self.load_products()
        self.load_movements()
        self.load_alerts()
        self.update_valuation()