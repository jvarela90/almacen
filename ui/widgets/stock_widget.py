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
    
    # Señales personalizadas
    product_updated = pyqtSignal(dict)
    stock_updated = pyqtSignal(int, float)
    
    def __init__(self, product_manager, provider_manager, user_manager, parent=None):
        super().__init__(parent)
        self.product_manager = product_manager
        self.provider_manager = provider_manager
        self.user_manager = user_manager
        
        # Estado actual
        self.current_products = []
        self.selected_product = None
        
        self.init_ui()
        self.setup_filters()
        self.load_products()
        self.setup_refresh_timer()
    
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
        
        # Cartas de estadísticas
        self.stats_layout = QHBoxLayout()
        
        # Crear cartas de métricas
        self.total_products_card = self.create_metric_card("Total Productos", "0", "#3498db")
        self.low_stock_card = self.create_metric_card("Stock Bajo", "0", "#e74c3c")
        self.stock_value_card = self.create_metric_card("Valor Stock", "$0", "#27ae60")
        
        self.stats_layout.addWidget(self.total_products_card)
        self.stats_layout.addWidget(self.low_stock_card)
        self.stats_layout.addWidget(self.stock_value_card)
        
        layout.addLayout(self.stats_layout)
        
        return header
    
    def create_metric_card(self, title: str, value: str, color: str) -> QWidget:
        """Crear carta de métrica"""
        card = QFrame()
        card.setFrameStyle(QFrame.StyledPanel)
        card.setObjectName("metric_card")
        
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)
        
        # Título
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 11px; color: #7f8c8d; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Valor
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet(f"font-size: 24px; color: {color}; font-weight: bold;")
        layout.addWidget(value_label)
        
        # Guardar referencia para actualizar
        setattr(card, 'value_label', value_label)
        
        return card
    
    def create_toolbar(self) -> QWidget:
        """Crear barra de herramientas"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setSpacing(10)
        
        # Búsqueda
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Buscar:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Código, nombre o código interno...")
        self.search_input.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_input)
        
        search_btn = QPushButton("🔍")
        search_btn.setMaximumWidth(30)
        search_btn.clicked.connect(self.search_products)
        search_layout.addWidget(search_btn)
        
        layout.addLayout(search_layout)
        
        # Filtro por categoría
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("Categoría:"))
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("Todas las categorías", None)
        self.load_categories()
        self.category_combo.currentIndexChanged.connect(self.filter_products)
        category_layout.addWidget(self.category_combo)
        
        layout.addLayout(category_layout)
        
        # Filtro por stock
        stock_filter_layout = QHBoxLayout()
        stock_filter_layout.addWidget(QLabel("Stock:"))
        
        self.stock_filter_combo = QComboBox()
        self.stock_filter_combo.addItems([
            "Todos", "Stock Normal", "Stock Bajo", "Sin Stock"
        ])
        self.stock_filter_combo.currentIndexChanged.connect(self.filter_products)
        stock_filter_layout.addWidget(self.stock_filter_combo)
        
        layout.addLayout(stock_filter_layout)
        
        layout.addStretch()
        
        # Botones de acción
        self.add_product_btn = QPushButton("➕ Nuevo Producto")
        self.add_product_btn.clicked.connect(self.add_new_product)
        layout.addWidget(self.add_product_btn)
        
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setToolTip("Actualizar")
        self.refresh_btn.setMaximumWidth(30)
        self.refresh_btn.clicked.connect(self.refresh_data)
        layout.addWidget(self.refresh_btn)
        
        return toolbar
    
    def create_tabs(self) -> QWidget:
        """Crear tabs principales"""
        tabs = QTabWidget()
        
        # Tab de productos
        products_tab = self.create_products_tab()
        tabs.addTab(products_tab, "📋 Productos")
        
        # Tab de movimientos
        movements_tab = self.create_movements_tab()
        tabs.addTab(movements_tab, "📊 Movimientos")
        
        # Tab de reportes
        reports_tab = self.create_reports_tab()
        tabs.addTab(reports_tab, "📈 Reportes")
        
        return tabs
    
    def create_products_tab(self) -> QWidget:
        """Crear tab de productos"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # Panel izquierdo: Lista de productos
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Tabla de productos
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(8)
        self.products_table.setHorizontalHeaderLabels([
            "Código", "Nombre", "Categoría", "Stock Actual", 
            "Stock Mín.", "Precio Venta", "Estado", "Acciones"
        ])
        
        # Configurar tabla
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.products_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.products_table.selectionModel().selectionChanged.connect(self.on_product_selected)
        
        # Ajustar columnas
        header = self.products_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Nombre se estira
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        left_layout.addWidget(self.products_table)
        layout.addWidget(left_panel, 2)
        
        # Panel derecho: Detalles del producto
        right_panel = self.create_product_details_panel()
        layout.addWidget(right_panel, 1)
        
        return tab
    
    def create_product_details_panel(self) -> QWidget:
        """Crear panel de detalles del producto"""
        panel = QGroupBox("Detalles del Producto")
        layout = QVBoxLayout(panel)
        
        # Información básica
        info_group = QGroupBox("Información Básica")
        info_layout = QGridLayout(info_group)
        
        # Campos de información (solo lectura inicialmente)
        self.detail_labels = {}
        
        fields = [
            ("Código de Barras:", "codigo_barras"),
            ("Código Interno:", "codigo_interno"),
            ("Nombre:", "nombre"),
            ("Descripción:", "descripcion"),
            ("Categoría:", "categoria_nombre"),
            ("Proveedor:", "proveedor_nombre")
        ]
        
        for i, (label, field) in enumerate(fields):
            info_layout.addWidget(QLabel(label), i, 0)
            value_label = QLabel("-")
            value_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
            info_layout.addWidget(value_label, i, 1)
            self.detail_labels[field] = value_label
        
        layout.addWidget(info_group)
        
        # Stock y precios
        stock_group = QGroupBox("Stock y Precios")
        stock_layout = QGridLayout(stock_group)
        
        stock_fields = [
            ("Stock Actual:", "stock_actual"),
            ("Stock Mínimo:", "stock_minimo"),
            ("Stock Máximo:", "stock_maximo"),
            ("Precio Compra:", "precio_compra"),
            ("Precio Venta:", "precio_venta"),
            ("Precio Mayorista:", "precio_mayorista")
        ]
        
        for i, (label, field) in enumerate(stock_fields):
            stock_layout.addWidget(QLabel(label), i, 0)
            value_label = QLabel("-")
            value_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
            stock_layout.addWidget(value_label, i, 1)
            self.detail_labels[field] = value_label
        
        layout.addWidget(stock_group)
        
        # Botones de acción
        actions_layout = QHBoxLayout()
        
        self.edit_product_btn = QPushButton("✏️ Editar")
        self.edit_product_btn.setEnabled(False)
        self.edit_product_btn.clicked.connect(self.edit_selected_product)
        actions_layout.addWidget(self.edit_product_btn)
        
        self.adjust_stock_btn = QPushButton("📊 Ajustar Stock")
        self.adjust_stock_btn.setEnabled(False)
        self.adjust_stock_btn.clicked.connect(self.adjust_stock)
        actions_layout.addWidget(self.adjust_stock_btn)
        
        layout.addLayout(actions_layout)
        
        layout.addStretch()
        
        return panel
    
    def create_movements_tab(self) -> QWidget:
        """Crear tab de movimientos de stock"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Filtros de movimientos
        filters_widget = QWidget()
        filters_layout = QHBoxLayout(filters_widget)
        
        # Filtro por fecha
        filters_layout.addWidget(QLabel("Desde:"))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        filters_layout.addWidget(self.date_from)
        
        filters_layout.addWidget(QLabel("Hasta:"))
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        filters_layout.addWidget(self.date_to)
        
        # Filtro por tipo de movimiento
        filters_layout.addWidget(QLabel("Tipo:"))
        self.movement_type_combo = QComboBox()
        self.movement_type_combo.addItems([
            "Todos", "ENTRADA", "SALIDA", "AJUSTE"
        ])
        filters_layout.addWidget(self.movement_type_combo)
        
        filter_btn = QPushButton("Filtrar")
        filter_btn.clicked.connect(self.load_movements)
        filters_layout.addWidget(filter_btn)
        
        filters_layout.addStretch()
        layout.addWidget(filters_widget)
        
        # Tabla de movimientos
        self.movements_table = QTableWidget()
        self.movements_table.setColumnCount(7)
        self.movements_table.setHorizontalHeaderLabels([
            "Fecha", "Producto", "Tipo", "Cantidad", "Stock Anterior", 
            "Stock Nuevo", "Usuario"
        ])
        
        self.movements_table.setAlternatingRowColors(True)
        self.movements_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.movements_table)
        
        return tab
    
    def create_reports_tab(self) -> QWidget:
        """Crear tab de reportes"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Botones de reportes
        reports_group = QGroupBox("Reportes Disponibles")
        reports_layout = QGridLayout(reports_group)
        
        report_buttons = [
            ("📊 Reporte de Inventario", self.generate_inventory_report),
            ("⚠️ Productos con Stock Bajo", self.generate_low_stock_report),
            ("💰 Valorización de Stock", self.generate_stock_valuation_report),
            ("📈 Movimientos por Período", self.generate_movements_report)
        ]
        
        for i, (text, callback) in enumerate(report_buttons):
            btn = QPushButton(text)
            btn.setMinimumHeight(50)
            btn.clicked.connect(callback)
            reports_layout.addWidget(btn, i // 2, i % 2)
        
        layout.addWidget(reports_group)
        
        # Área de resultados
        self.reports_area = QTextEdit()
        self.reports_area.setReadOnly(True)
        self.reports_area.setPlaceholderText("Los resultados de los reportes aparecerán aquí...")
        layout.addWidget(self.reports_area)
        
        return tab
    
    def setup_filters(self):
        """Configurar filtros iniciales"""
        # Configurar búsqueda con delay
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.search_products)
    
    def setup_refresh_timer(self):
        """Configurar timer de actualización automática"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_stats)
        self.refresh_timer.start(300000)  # 5 minutos
    
    def load_categories(self):
        """Cargar categorías en el combo"""
        try:
            categories = self.product_manager.db.execute_query("""
                SELECT id, nombre FROM categorias WHERE activo = 1 ORDER BY nombre
            """)
            
            for category in categories:
                self.category_combo.addItem(category['nombre'], category['id'])
                
        except Exception as e:
            logger.error(f"Error cargando categorías: {e}")
    
    def load_products(self):
        """Cargar productos en la tabla"""
        try:
            # Obtener filtros actuales
            search_term = self.search_input.text().strip()
            category_id = self.category_combo.currentData()
            
            if search_term:
                products = self.product_manager.search_products(search_term, limit=200)
            else:
                products = self.product_manager.get_all_products(page_size=200)
            
            # Aplicar filtros adicionales
            if category_id:
                products = [p for p in products if p.get('categoria_id') == category_id]
            
            # Filtro por stock
            stock_filter = self.stock_filter_combo.currentText()
            if stock_filter == "Stock Bajo":
                products = [p for p in products if p.get('stock_actual', 0) <= p.get('stock_minimo', 0)]
            elif stock_filter == "Sin Stock":
                products = [p for p in products if p.get('stock_actual', 0) == 0]
            elif stock_filter == "Stock Normal":
                products = [p for p in products if p.get('stock_actual', 0) > p.get('stock_minimo', 0)]
            
            self.current_products = products
            self.populate_products_table(products)
            self.update_stats()
            
        except Exception as e:
            logger.error(f"Error cargando productos: {e}")
            QMessageBox.warning(self, "Error", f"Error cargando productos: {e}")
    
    def populate_products_table(self, products: list):
        """Poblar tabla de productos"""
        self.products_table.setRowCount(len(products))
        
        for row, product in enumerate(products):
            # Código
            code_item = QTableWidgetItem(product.get('codigo_barras', ''))
            self.products_table.setItem(row, 0, code_item)
            
            # Nombre
            name_item = QTableWidgetItem(product.get('nombre', ''))
            self.products_table.setItem(row, 1, name_item)
            
            # Categoría
            category_item = QTableWidgetItem(product.get('categoria_nombre', 'Sin categoría'))
            self.products_table.setItem(row, 2, category_item)
            
            # Stock actual
            stock_actual = float(product.get('stock_actual', 0))
            stock_item = QTableWidgetItem(f"{stock_actual:.2f}")
            stock_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            # Colorear según stock
            stock_min = float(product.get('stock_minimo', 0))
            if stock_actual == 0:
                stock_item.setBackground(QColor("#fadbd8"))  # Rojo claro
            elif stock_actual <= stock_min and stock_min > 0:
                stock_item.setBackground(QColor("#fef9e7"))  # Amarillo claro
            
            self.products_table.setItem(row, 3, stock_item)
            
            # Stock mínimo
            stock_min_item = QTableWidgetItem(f"{stock_min:.2f}")
            stock_min_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.products_table.setItem(row, 4, stock_min_item)
            
            # Precio venta
            price = float(product.get('precio_venta', 0))
            price_item = QTableWidgetItem(f"${price:.2f}")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.products_table.setItem(row, 5, price_item)
            
            # Estado
            if stock_actual == 0:
                status = "Sin Stock"
                status_color = QColor("#e74c3c")
            elif stock_actual <= stock_min and stock_min > 0:
                status = "Stock Bajo"
                status_color = QColor("#f39c12")
            else:
                status = "Normal"
                status_color = QColor("#27ae60")
            
            status_item = QTableWidgetItem(status)
            status_item.setForeground(QBrush(status_color))
            self.products_table.setItem(row, 6, status_item)
            
            # Botones de acción
            actions_widget = self.create_product_actions(product)
            self.products_table.setCellWidget(row, 7, actions_widget)
        
        # Ajustar altura de filas
        self.products_table.resizeRowsToContents()
    
    def create_product_actions(self, product: dict) -> QWidget:
        """Crear botones de acción para producto"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # Botón editar
        edit_btn = QPushButton("✏️")
        edit_btn.setMaximumWidth(25)
        edit_btn.setToolTip("Editar producto")
        edit_btn.clicked.connect(lambda: self.edit_product(product))
        layout.addWidget(edit_btn)
        
        # Botón ajustar stock
        stock_btn = QPushButton("📊")
        stock_btn.setMaximumWidth(25)
        stock_btn.setToolTip("Ajustar stock")
        stock_btn.clicked.connect(lambda: self.adjust_product_stock(product))
        layout.addWidget(stock_btn)
        
        return widget
    
    def update_stats(self):
        """Actualizar estadísticas del header"""
        try:
            # Total productos
            total_products = len(self.current_products)
            self.total_products_card.value_label.setText(str(total_products))
            
            # Productos con stock bajo
            low_stock_count = len([
                p for p in self.current_products 
                if float(p.get('stock_actual', 0)) <= float(p.get('stock_minimo', 0))
                and float(p.get('stock_minimo', 0)) > 0
            ])
            self.low_stock_card.value_label.setText(str(low_stock_count))
            
            # Valor total del stock
            total_value = sum(
                float(p.get('stock_actual', 0)) * float(p.get('precio_venta', 0))
                for p in self.current_products
            )
            self.stock_value_card.value_label.setText(f"${total_value:,.2f}")
            
        except Exception as e:
            logger.error(f"Error actualizando estadísticas: {e}")
    
    def on_search_changed(self):
        """Manejar cambio en búsqueda con delay"""
        self.search_timer.stop()
        self.search_timer.start(500)  # 500ms delay
    
    def search_products(self):
        """Buscar productos"""
        self.load_products()
    
    def filter_products(self):
        """Filtrar productos"""
        self.load_products()
    
    def on_product_selected(self):
        """Manejar selección de producto"""
        current_row = self.products_table.currentRow()
        if current_row >= 0 and current_row < len(self.current_products):
            self.selected_product = self.current_products[current_row]
            self.update_product_details()
            self.edit_product_btn.setEnabled(True)
            self.adjust_stock_btn.setEnabled(True)
        else:
            self.selected_product = None
            self.clear_product_details()
            self.edit_product_btn.setEnabled(False)
            self.adjust_stock_btn.setEnabled(False)
    
    def update_product_details(self):
        """Actualizar panel de detalles"""
        if not self.selected_product:
            return
        
        for field, label in self.detail_labels.items():
            value = self.selected_product.get(field, '-')
            if field in ['precio_compra', 'precio_venta', 'precio_mayorista'] and value != '-':
                label.setText(f"${float(value):.2f}")
            elif field in ['stock_actual', 'stock_minimo', 'stock_maximo'] and value != '-':
                label.setText(f"{float(value):.2f}")
            else:
                label.setText(str(value) if value is not None else '-')
    
    def clear_product_details(self):
        """Limpiar panel de detalles"""
        for label in self.detail_labels.values():
            label.setText('-')
    
    def add_new_product(self):
        """Agregar nuevo producto"""
        try:
            dialog = ProductDialog(
                self.product_manager, 
                self.provider_manager,
                parent=self
            )
            
            if dialog.exec_() == QDialog.Accepted:
                self.refresh_data()
                
        except Exception as e:
            logger.error(f"Error abriendo diálogo de producto: {e}")
            QMessageBox.warning(self, "Error", f"Error abriendo diálogo: {e}")
    
    def edit_selected_product(self):
        """Editar producto seleccionado"""
        if self.selected_product:
            self.edit_product(self.selected_product)
    
    def edit_product(self, product: dict):
        """Editar producto específico"""
        try:
            dialog = ProductDialog(
                self.product_manager,
                self.provider_manager,
                product=product,
                parent=self
            )
            
            if dialog.exec_() == QDialog.Accepted:
                self.refresh_data()
                
        except Exception as e:
            logger.error(f"Error editando producto: {e}")
            QMessageBox.warning(self, "Error", f"Error editando producto: {e}")
    
    def adjust_stock(self):
        """Ajustar stock del producto seleccionado"""
        if self.selected_product:
            self.adjust_product_stock(self.selected_product)
    
    def adjust_product_stock(self, product: dict):
        """Ajustar stock de producto específico"""
        try:
            dialog = StockAdjustmentDialog(
                self.product_manager,
                product,
                parent=self
            )
            
            if dialog.exec_() == QDialog.Accepted:
                self.refresh_data()
                self.stock_updated.emit(product['id'], dialog.get_new_stock())
                
        except Exception as e:
            logger.error(f"Error ajustando stock: {e}")
            QMessageBox.warning(self, "Error", f"Error ajustando stock: {e}")
    
    def load_movements(self):
        """Cargar movimientos de stock"""
        try:
            date_from = self.date_from.date().toPython()
            date_to = self.date_to.date().toPython()
            
            movements = self.product_manager.get_stock_movements(
                date_from=date_from,
                date_to=date_to,
                limit=500
            )
            
            # Filtrar por tipo si es necesario
            movement_type = self.movement_type_combo.currentText()
            if movement_type != "Todos":
                movements = [m for m in movements if m['tipo_movimiento'] == movement_type]
            
            self.populate_movements_table(movements)
            
        except Exception as e:
            logger.error(f"Error cargando movimientos: {e}")
            QMessageBox.warning(self, "Error", f"Error cargando movimientos: {e}")
    
    def populate_movements_table(self, movements: list):
        """Poblar tabla de movimientos"""
        self.movements_table.setRowCount(len(movements))
        
        for row, movement in enumerate(movements):
            # Fecha
            fecha = movement.get('fecha_movimiento', '')[:16]  # Sin segundos
            self.movements_table.setItem(row, 0, QTableWidgetItem(fecha))
            
            # Producto
            producto = movement.get('producto_nombre', '')
            self.movements_table.setItem(row, 1, QTableWidgetItem(producto))
            
            # Tipo
            tipo = movement.get('tipo_movimiento', '')
            tipo_item = QTableWidgetItem(tipo)
            
            # Colorear según tipo
            if tipo == 'ENTRADA':
                tipo_item.setForeground(QBrush(QColor("#27ae60")))
            elif tipo == 'SALIDA':
                tipo_item.setForeground(QBrush(QColor("#e74c3c")))
            else:  # AJUSTE
                tipo_item.setForeground(QBrush(QColor("#f39c12")))
            
            self.movements_table.setItem(row, 2, tipo_item)
            
            # Cantidad
            cantidad = float(movement.get('cantidad_movimiento', 0))
            cantidad_item = QTableWidgetItem(f"{cantidad:+.2f}")
            cantidad_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.movements_table.setItem(row, 3, cantidad_item)
            
            # Stock anterior
            stock_ant = float(movement.get('cantidad_anterior', 0))
            stock_ant_item = QTableWidgetItem(f"{stock_ant:.2f}")
            stock_ant_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.movements_table.setItem(row, 4, stock_ant_item)
            
            # Stock nuevo
            stock_new = float(movement.get('cantidad_nueva', 0))
            stock_new_item = QTableWidgetItem(f"{stock_new:.2f}")
            stock_new_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.movements_table.setItem(row, 5, stock_new_item)
            
            # Usuario
            usuario = movement.get('usuario_nombre', '')
            self.movements_table.setItem(row, 6, QTableWidgetItem(usuario))
    
    def refresh_data(self):
        """Actualizar todos los datos"""
        self.load_products()
        self.load_movements()
    
    def refresh_stats(self):
        """Actualizar solo estadísticas"""
        self.update_stats()
    
    def setup_styles(self):
        """Configurar estilos CSS"""
        self.setStyleSheet("""
            #header {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 10px;
            }
            
            #metric_card {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                min-width: 120px;
                max-width: 150px;
                padding: 10px;
            }
            
            #metric_card:hover {
                border-color: #3498db;
                box-shadow: 0 2px 4px rgba(52, 152, 219, 0.2);
            }
        """)
    
    # Métodos de reportes (placeholder)
    def generate_inventory_report(self):
        """Generar reporte de inventario"""
        self.reports_area.setText("Generando reporte de inventario...\n(Funcionalidad en desarrollo)")
    
    def generate_low_stock_report(self):
        """Generar reporte de stock bajo"""
        self.reports_area.setText("Generando reporte de stock bajo...\n(Funcionalidad en desarrollo)")
    
    def generate_stock_valuation_report(self):
        """Generar reporte de valorización"""
        self.reports_area.setText("Generando reporte de valorización...\n(Funcionalidad en desarrollo)")
    
    def generate_movements_report(self):
        """Generar reporte de movimientos"""
        self.reports_area.setText("Generando reporte de movimientos...\n(Funcionalidad en desarrollo)")


# Diálogos auxiliares (versiones simplificadas)
class ProductDialog(QDialog):
    """Diálogo para crear/editar productos"""
    
    def __init__(self, product_manager, provider_manager, product=None, parent=None):
        super().__init__(parent)
        self.product_manager = product_manager
        self.provider_manager = provider_manager
        self.product = product
        
        self.setWindowTitle("Editar Producto" if product else "Nuevo Producto")
        self.setModal(True)
        self.resize(500, 400)
        
        # Por ahora solo un placeholder
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Diálogo de producto\n(En desarrollo)"))
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class StockAdjustmentDialog(QDialog):
    """Diálogo para ajustar stock"""
    
    def __init__(self, product_manager, product, parent=None):
        super().__init__(parent)
        self.product_manager = product_manager
        self.product = product
        self.new_stock = 0
        
        self.setWindowTitle(f"Ajustar Stock - {product['nombre']}")
        self.setModal(True)
        self.resize(400, 300)
        
        # Por ahora solo un placeholder
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Ajustar stock de: {product['nombre']}"))
        layout.addWidget(QLabel(f"Stock actual: {product.get('stock_actual', 0)}"))
        layout.addWidget(QLabel("Diálogo de ajuste de stock\n(En desarrollo)"))
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_new_stock(self):
        """Obtener nuevo stock (placeholder)"""
        return self.product.get('stock_actual', 0)