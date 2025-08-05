"""
Widget de Ventas para AlmacénPro
Interfaz principal para procesar ventas con scanner, carrito y facturación
"""

import logging
from decimal import Decimal
from datetime import datetime, date
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

logger = logging.getLogger(__name__)

class SalesWidget(QWidget):
    """Widget principal para gestionar ventas"""
    
    def __init__(self, sales_manager, product_manager, user_manager, parent=None):
        super().__init__(parent)
        self.sales_manager = sales_manager
        self.product_manager = product_manager
        self.user_manager = user_manager
        
        # Estado del carrito de compras
        self.cart_items = []
        self.current_customer = None
        
        self.init_ui()
        self.setup_shortcuts()
        self.load_sales_history()
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Panel izquierdo: Scanner y productos
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 3)
        
        # Panel derecho: Carrito y checkout
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 2)
        
        # Aplicar estilos
        self.setup_styles()
    
    def create_left_panel(self) -> QWidget:
        """Crear panel izquierdo con scanner y búsqueda"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Header del panel
        header = QLabel("🛒 Proceso de Venta")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2E86AB; padding: 10px;")
        layout.addWidget(header)
        
        # Grupo: Scanner y búsqueda
        search_group = QGroupBox("Buscar Productos")
        search_layout = QVBoxLayout(search_group)
        
        # Campo de búsqueda/scanner
        search_bar_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Escanee código de barras o busque producto...")
        self.search_input.setStyleSheet("font-size: 14px; padding: 10px;")
        self.search_input.returnPressed.connect(self.search_or_add_product)
        self.search_input.textChanged.connect(self.search_products)
        search_bar_layout.addWidget(self.search_input)
        
        search_btn = QPushButton("🔍")
        search_btn.setFixedSize(40, 40)
        search_btn.setToolTip("Buscar producto")
        search_btn.clicked.connect(self.search_or_add_product)
        search_bar_layout.addWidget(search_btn)
        
        scanner_btn = QPushButton("📷")
        scanner_btn.setFixedSize(40, 40)
        scanner_btn.setToolTip("Activar scanner")
        scanner_btn.clicked.connect(self.activate_scanner)
        search_bar_layout.addWidget(scanner_btn)
        
        search_layout.addLayout(search_bar_layout)
        
        # Lista de productos encontrados
        self.products_list = QListWidget()
        self.products_list.setMaximumHeight(200)
        self.products_list.itemDoubleClicked.connect(self.add_selected_product)
        self.products_list.hide()  # Ocultar inicialmente
        search_layout.addWidget(self.products_list)
        
        layout.addWidget(search_group)
        
        # Grupo: Acciones rápidas
        quick_actions_group = QGroupBox("Acciones Rápidas")
        quick_actions_layout = QGridLayout(quick_actions_group)
        
        # Botones de acciones rápidas
        new_sale_btn = QPushButton("🆕 Nueva Venta")
        new_sale_btn.clicked.connect(self.new_sale)
        quick_actions_layout.addWidget(new_sale_btn, 0, 0)
        
        hold_sale_btn = QPushButton("⏸️ Suspender")
        hold_sale_btn.clicked.connect(self.hold_sale)
        quick_actions_layout.addWidget(hold_sale_btn, 0, 1)
        
        recall_sale_btn = QPushButton("▶️ Recuperar")
        recall_sale_btn.clicked.connect(self.recall_sale)
        quick_actions_layout.addWidget(recall_sale_btn, 1, 0)
        
        quick_product_btn = QPushButton("➕ Producto Rápido")
        quick_product_btn.clicked.connect(self.add_quick_product)
        quick_actions_layout.addWidget(quick_product_btn, 1, 1)
        
        layout.addWidget(quick_actions_group)
        
        # Grupo: Ventas recientes
        recent_sales_group = QGroupBox("Ventas Recientes")
        recent_sales_layout = QVBoxLayout(recent_sales_group)
        
        self.recent_sales_table = QTableWidget()
        self.recent_sales_table.setColumnCount(4)
        self.recent_sales_table.setHorizontalHeaderLabels(["Ticket", "Cliente", "Total", "Hora"])
        self.recent_sales_table.verticalHeader().setVisible(False)
        self.recent_sales_table.setAlternatingRowColors(True)
        self.recent_sales_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.recent_sales_table.doubleClicked.connect(self.view_sale_details)
        
        # Configurar columnas
        header = self.recent_sales_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        recent_sales_layout.addWidget(self.recent_sales_table)
        layout.addWidget(recent_sales_group)
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Crear panel derecho con carrito y checkout"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Header del carrito
        cart_header_layout = QHBoxLayout()
        
        cart_title = QLabel("🛒 Carrito de Compras")
        cart_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2E86AB;")
        cart_header_layout.addWidget(cart_title)
        
        cart_header_layout.addStretch()
        
        # Contador de items
        self.items_count_label = QLabel("0 items")
        self.items_count_label.setStyleSheet("color: #666; font-weight: bold;")
        cart_header_layout.addWidget(self.items_count_label)
        
        layout.addLayout(cart_header_layout)
        
        # Tabla del carrito
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(6)
        self.cart_table.setHorizontalHeaderLabels([
            "Producto", "Cant.", "Precio", "Desc.", "Subtotal", "Acciones"
        ])
        
        # Configurar tabla del carrito
        cart_header = self.cart_table.horizontalHeader()
        cart_header.setSectionResizeMode(0, QHeaderView.Stretch)
        cart_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        cart_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        cart_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        cart_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        cart_header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.setAlternatingRowColors(True)
        layout.addWidget(self.cart_table)
        
        # Información del cliente
        customer_group = QGroupBox("Cliente")
        customer_layout = QHBoxLayout(customer_group)
        
        self.customer_input = QLineEdit()
        self.customer_input.setPlaceholderText("Buscar cliente (opcional)")
        self.customer_input.textChanged.connect(self.search_customers)
        customer_layout.addWidget(self.customer_input)
        
        select_customer_btn = QPushButton("👤")
        select_customer_btn.setFixedSize(30, 30)
        select_customer_btn.setToolTip("Seleccionar cliente")
        select_customer_btn.clicked.connect(self.select_customer)
        customer_layout.addWidget(select_customer_btn)
        
        new_customer_btn = QPushButton("➕")
        new_customer_btn.setFixedSize(30, 30)
        new_customer_btn.setToolTip("Nuevo cliente")
        new_customer_btn.clicked.connect(self.add_new_customer)
        customer_layout.addWidget(new_customer_btn)
        
        layout.addWidget(customer_group)
        
        # Totales
        totals_group = QGroupBox("Totales")
        totals_layout = QGridLayout(totals_group)
        
        # Subtotal
        totals_layout.addWidget(QLabel("Subtotal:"), 0, 0)
        self.subtotal_label = QLabel("$0.00")
        self.subtotal_label.setStyleSheet("font-weight: bold;")
        totals_layout.addWidget(self.subtotal_label, 0, 1, alignment=Qt.AlignRight)
        
        # Descuento
        totals_layout.addWidget(QLabel("Descuento:"), 1, 0)
        discount_layout = QHBoxLayout()
        
        self.discount_input = QDoubleSpinBox()
        self.discount_input.setMinimum(0)
        self.discount_input.setMaximum(100)
        self.discount_input.setSuffix(" %")
        self.discount_input.valueChanged.connect(self.calculate_totals)
        discount_layout.addWidget(self.discount_input)
        
        self.discount_amount_label = QLabel("$0.00")
        self.discount_amount_label.setStyleSheet("color: #dc3545; font-weight: bold;")
        discount_layout.addWidget(self.discount_amount_label)
        
        discount_widget = QWidget()
        discount_widget.setLayout(discount_layout)
        totals_layout.addWidget(discount_widget, 1, 1)
        
        # IVA
        totals_layout.addWidget(QLabel("IVA:"), 2, 0)
        self.tax_label = QLabel("$0.00")
        self.tax_label.setStyleSheet("font-weight: bold;")
        totals_layout.addWidget(self.tax_label, 2, 1, alignment=Qt.AlignRight)
        
        # Total
        total_layout = QHBoxLayout()
        total_title = QLabel("TOTAL:")
        total_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        total_layout.addWidget(total_title)
        
        self.total_label = QLabel("$0.00")
        self.total_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #28a745;")
        total_layout.addWidget(self.total_label)
        
        total_widget = QWidget()
        total_widget.setLayout(total_layout)
        totals_layout.addWidget(total_widget, 3, 0, 1, 2)
        
        layout.addWidget(totals_group)
        
        # Método de pago
        payment_group = QGroupBox("Método de Pago")
        payment_layout = QGridLayout(payment_group)
        
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems([
            "EFECTIVO", "TARJETA_DEBITO", "TARJETA_CREDITO", 
            "TRANSFERENCIA", "CHEQUE", "CUENTA_CORRIENTE"
        ])
        payment_layout.addWidget(self.payment_method_combo, 0, 0, 1, 2)
        
        # Monto recibido (solo para efectivo)
        payment_layout.addWidget(QLabel("Recibido:"), 1, 0)
        self.received_input = QDoubleSpinBox()
        self.received_input.setMinimum(0)
        self.received_input.setMaximum(999999)
        self.received_input.setPrefix("$ ")
        self.received_input.valueChanged.connect(self.calculate_change)
        payment_layout.addWidget(self.received_input, 1, 1)
        
        # Vuelto
        payment_layout.addWidget(QLabel("Vuelto:"), 2, 0)
        self.change_label = QLabel("$0.00")
        self.change_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #17a2b8;")
        payment_layout.addWidget(self.change_label, 2, 1, alignment=Qt.AlignRight)
        
        layout.addWidget(payment_group)
        
        # Botones de acción
        actions_layout = QGridLayout()
        
        clear_cart_btn = QPushButton("🗑️ Limpiar")
        clear_cart_btn.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold;")
        clear_cart_btn.clicked.connect(self.clear_cart)
        actions_layout.addWidget(clear_cart_btn, 0, 0)
        
        cancel_sale_btn = QPushButton("❌ Cancelar")
        cancel_sale_btn.clicked.connect(self.cancel_sale)
        actions_layout.addWidget(cancel_sale_btn, 0, 1)
        
        process_sale_btn = QPushButton("💳 PROCESAR VENTA")
        process_sale_btn.setStyleSheet("""
            background-color: #28a745; 
            color: white; 
            font-weight: bold; 
            font-size: 14px; 
            padding: 12px;
        """)
        process_sale_btn.clicked.connect(self.process_sale)
        actions_layout.addWidget(process_sale_btn, 1, 0, 1, 2)
        
        layout.addLayout(actions_layout)
        
        return panel
    
    def setup_styles(self):
        """Configurar estilos CSS"""
        self.setStyleSheet("""
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
            
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                padding: 6px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
            
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #2E86AB;
                outline: none;
            }
            
            QPushButton {
                padding: 8px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                background-color: #f8f9fa;
            }
            
            QPushButton:hover {
                background-color: #e9ecef;
            }
            
            QPushButton:pressed {
                background-color: #dee2e6;
            }
            
            QTableWidget {
                gridline-color: #e9ecef;
                background-color: white;
                alternate-background-color: #f8f9fa;
                selection-background-color: #2E86AB;
            }
            
            QTableWidget::item {
                padding: 8px;
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
        """)
    
    def setup_shortcuts(self):
        """Configurar atajos de teclado"""
        # F1: Nueva venta
        QShortcut(QKeySequence("F1"), self, self.new_sale)
        
        # F2: Procesar venta
        QShortcut(QKeySequence("F2"), self, self.process_sale)
        
        # F3: Buscar producto
        QShortcut(QKeySequence("F3"), self, lambda: self.search_input.setFocus())
        
        # F4: Seleccionar cliente
        QShortcut(QKeySequence("F4"), self, self.select_customer)
        
        # Del: Eliminar item del carrito
        QShortcut(QKeySequence("Delete"), self, self.remove_selected_item)
        
        # Escape: Cancelar venta
        QShortcut(QKeySequence("Escape"), self, self.cancel_sale)
        
        # Enter: Buscar/agregar producto
        QShortcut(QKeySequence("Return"), self, self.search_or_add_product)
    
    def search_products(self, search_term):
        """Buscar productos en tiempo real"""
        if len(search_term) < 2:
            self.products_list.hide()
            return
        
        try:
            products = self.product_manager.search_products(search_term, limit=10)
            
            self.products_list.clear()
            
            if products:
                for product in products:
                    item_text = f"{product['nombre']} - ${product['precio_venta']:.2f}"
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
    
    def search_or_add_product(self):
        """Buscar producto y agregarlo al carrito"""
        search_term = self.search_input.text().strip()
        
        if not search_term:
            return
        
        try:
            # Primero intentar buscar por código de barras exacto
            product = self.product_manager.get_product_by_barcode(search_term)
            
            if not product:
                # Buscar por nombre o código interno
                products = self.product_manager.search_products(search_term, limit=1)
                if products:
                    product = products[0]
            
            if product:
                self.add_product_to_cart(product)
                self.search_input.clear()
                self.products_list.hide()
                self.search_input.setFocus()
            else:
                QMessageBox.information(self, "Producto no encontrado", 
                    f"No se encontró ningún producto con: '{search_term}'")
                
        except Exception as e:
            logger.error(f"Error agregando producto: {e}")
            QMessageBox.critical(self, "Error", f"Error agregando producto: {str(e)}")
    
    def add_selected_product(self, item):
        """Agregar producto seleccionado de la lista"""
        product = item.data(Qt.UserRole)
        if product:
            self.add_product_to_cart(product)
            self.search_input.clear()
            self.products_list.hide()
            self.search_input.setFocus()
    
    def add_product_to_cart(self, product, quantity=1):
        """Agregar producto al carrito"""
        try:
            # Verificar stock si es necesario
            if not product.get('permite_venta_sin_stock', False):
                if product['stock_actual'] < quantity:
                    QMessageBox.warning(self, "Stock Insuficiente", 
                        f"Stock disponible: {product['stock_actual']} unidades")
                    return
            
            # Verificar si el producto ya está en el carrito
            existing_item = None
            for item in self.cart_items:
                if item['product']['id'] == product['id']:
                    existing_item = item
                    break
            
            if existing_item:
                # Aumentar cantidad
                new_quantity = existing_item['quantity'] + quantity
                
                # Verificar stock para la nueva cantidad
                if not product.get('permite_venta_sin_stock', False):
                    if product['stock_actual'] < new_quantity:
                        QMessageBox.warning(self, "Stock Insuficiente", 
                            f"Stock disponible: {product['stock_actual']} unidades")
                        return
                
                existing_item['quantity'] = new_quantity
            else:
                # Agregar nuevo item
                cart_item = {
                    'product': product,
                    'quantity': quantity,
                    'unit_price': float(product['precio_venta']),
                    'discount_percent': 0,
                    'discount_amount': 0
                }
                self.cart_items.append(cart_item)
            
            self.update_cart_display()
            
        except Exception as e:
            logger.error(f"Error agregando producto al carrito: {e}")
    
    def update_cart_display(self):
        """Actualizar visualización del carrito"""
        try:
            self.cart_table.setRowCount(len(self.cart_items))
            
            for i, item in enumerate(self.cart_items):
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
                name_item = QTableWidgetItem(product['nombre'])
                self.cart_table.setItem(i, 0, name_item)
                
                # Cantidad (editable)
                quantity_spin = QSpinBox()
                quantity_spin.setMinimum(1)
                quantity_spin.setMaximum(9999)
                quantity_spin.setValue(quantity)
                quantity_spin.valueChanged.connect(
                    lambda value, row=i: self.update_item_quantity(row, value)
                )
                self.cart_table.setCellWidget(i, 1, quantity_spin)
                
                # Precio unitario
                price_item = QTableWidgetItem(f"${unit_price:.2f}")
                price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.cart_table.setItem(i, 2, price_item)
                
                # Descuento (editable)
                discount_spin = QDoubleSpinBox()
                discount_spin.setMinimum(0)
                discount_spin.setMaximum(100)
                discount_spin.setSuffix("%")
                discount_spin.setValue(discount_percent)
                discount_spin.valueChanged.connect(
                    lambda value, row=i: self.update_item_discount(row, value)
                )
                self.cart_table.setCellWidget(i, 3, discount_spin)
                
                # Subtotal
                subtotal_item = QTableWidgetItem(f"${final_subtotal:.2f}")
                subtotal_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.cart_table.setItem(i, 4, subtotal_item)
                
                # Botón eliminar
                remove_btn = QPushButton("🗑️")
                remove_btn.setFixedSize(30, 25)
                remove_btn.setToolTip("Eliminar item")
                remove_btn.clicked.connect(lambda checked, row=i: self.remove_cart_item(row))
                self.cart_table.setCellWidget(i, 5, remove_btn)
            
            # Actualizar contador de items
            total_items = sum(item['quantity'] for item in self.cart_items)
            self.items_count_label.setText(f"{total_items} items")
            
            # Actualizar totales
            self.calculate_totals()
            
        except Exception as e:
            logger.error(f"Error actualizando carrito: {e}")
    
    def update_item_quantity(self, row, new_quantity):
        """Actualizar cantidad de un item"""
        if row < len(self.cart_items):
            product = self.cart_items[row]['product']
            
            # Verificar stock
            if not product.get('permite_venta_sin_stock', False):
                if product['stock_actual'] < new_quantity:
                    QMessageBox.warning(self, "Stock Insuficiente", 
                        f"Stock disponible: {product['stock_actual']} unidades")
                    # Restaurar cantidad anterior
                    widget = self.cart_table.cellWidget(row, 1)
                    if widget:
                        widget.setValue(self.cart_items[row]['quantity'])
                    return
            
            self.cart_items[row]['quantity'] = new_quantity
            self.update_cart_display()
    
    def update_item_discount(self, row, new_discount):
        """Actualizar descuento de un item"""
        if row < len(self.cart_items):
            self.cart_items[row]['discount_percent'] = new_discount
            self.update_cart_display()
    
    def remove_cart_item(self, row):
        """Eliminar item del carrito"""
        if 0 <= row < len(self.cart_items):
            del self.cart_items[row]
            self.update_cart_display()
    
    def remove_selected_item(self):
        """Eliminar item seleccionado del carrito"""
        current_row = self.cart_table.currentRow()
        if current_row >= 0:
            self.remove_cart_item(current_row)
    
    def calculate_totals(self):
        """Calcular totales de la venta"""
        try:
            subtotal = 0
            tax_total = 0
            
            for item in self.cart_items:
                quantity = item['quantity']
                unit_price = item['unit_price']
                discount_percent = item['discount_percent']
                
                item_subtotal = quantity * unit_price
                item_discount = item_subtotal * (discount_percent / 100)
                item_final = item_subtotal - item_discount
                
                subtotal += item_final
                
                # Calcular IVA (simplificado - usar IVA del producto)
                iva_percent = item['product'].get('iva_porcentaje', 21)
                item_tax = item_final * (iva_percent / 100)
                tax_total += item_tax
            
            # Descuento general
            general_discount_percent = self.discount_input.value()
            general_discount_amount = subtotal * (general_discount_percent / 100)
            
            # Total final
            final_subtotal = subtotal - general_discount_amount
            total = final_subtotal + tax_total
            
            # Actualizar labels
            self.subtotal_label.setText(f"${subtotal:.2f}")
            self.discount_amount_label.setText(f"-${general_discount_amount:.2f}")
            self.tax_label.setText(f"${tax_total:.2f}")
            self.total_label.setText(f"${total:.2f}")
            
            # Actualizar monto recibido para efectivo
            if self.payment_method_combo.currentText() == "EFECTIVO":
                self.received_input.setValue(total)
            
            self.calculate_change()
            
        except Exception as e:
            logger.error(f"Error calculando totales: {e}")
    
    def calculate_change(self):
        """Calcular vuelto"""
        try:
            total_text = self.total_label.text().replace('$', '').replace(',', '')
            total = float(total_text)
            received = self.received_input.value()
            
            change = received - total
            self.change_label.setText(f"${change:.2f}")
            
            if change < 0:
                self.change_label.setStyleSheet("color: #dc3545; font-weight: bold;")
            else:
                self.change_label.setStyleSheet("color: #17a2b8; font-weight: bold;")
                
        except Exception as e:
            logger.error(f"Error calculando vuelto: {e}")
    
    def new_sale(self):
        """Iniciar nueva venta"""
        if self.cart_items:
            reply = QMessageBox.question(self, "Nueva Venta", 
                "¿Desea limpiar el carrito actual?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.No:
                return
        
        self.clear_cart()
        self.search_input.setFocus()
    
    def clear_cart(self):
        """Limpiar carrito de compras"""
        self.cart_items.clear()
        self.current_customer = None
        self.customer_input.clear()
        self.discount_input.setValue(0)
        self.received_input.setValue(0)
        self.update_cart_display()
    
    def cancel_sale(self):
        """Cancelar venta actual"""
        if self.cart_items:
            reply = QMessageBox.question(self, "Cancelar Venta", 
                "¿Está seguro de que desea cancelar la venta actual?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                self.clear_cart()
    
    def process_sale(self):
        """Procesar venta"""
        if not self.cart_items:
            QMessageBox.warning(self, "Carrito Vacío", "Agregue productos al carrito antes de procesar la venta")
            return
        
        try:
            # Validar vuelto para efectivo
            if self.payment_method_combo.currentText() == "EFECTIVO":
                change_text = self.change_label.text().replace('$', '').replace(',', '')
                if float(change_text) < 0:
                    QMessageBox.warning(self, "Monto Insuficiente", "El monto recibido es insuficiente")
                    return
            
            # Preparar datos de la venta
            sale_data = {
                'vendedor_id': self.user_manager.current_user['id'],
                'cliente_id': self.current_customer['id'] if self.current_customer else None,
                'metodo_pago': self.payment_method_combo.currentText(),
                'descuento': float(self.discount_amount_label.text().replace('-$', '').replace(',', '')),
                'observaciones': '',
                'items': []
            }
            
            # Agregar items del carrito
            for cart_item in self.cart_items:
                item_data = {
                    'producto_id': cart_item['product']['id'],
                    'cantidad': cart_item['quantity'],
                    'precio_unitario': cart_item['unit_price'],
                    'descuento_porcentaje': cart_item['discount_percent'],
                    'iva_porcentaje': cart_item['product'].get('iva_porcentaje', 21)
                }
                sale_data['items'].append(item_data)
            
            # Procesar venta
            success, message, sale_id = self.sales_manager.create_sale(sale_data)
            
            if success:
                QMessageBox.information(self, "Venta Procesada", message)
                
                # Preguntar si imprimir ticket
                reply = QMessageBox.question(self, "Imprimir Ticket", 
                    "¿Desea imprimir el ticket de venta?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                
                if reply == QMessageBox.Yes:
                    self.print_ticket(sale_id)
                
                # Limpiar carrito y cargar ventas recientes
                self.clear_cart()
                self.load_sales_history()
                self.search_input.setFocus()
            else:
                QMessageBox.critical(self, "Error", message)
                
        except Exception as e:
            logger.error(f"Error procesando venta: {e}")
            QMessageBox.critical(self, "Error", f"Error procesando venta: {str(e)}")
    
    def print_ticket(self, sale_id):
        """Imprimir ticket de venta"""
        # Placeholder para impresión de tickets
        QMessageBox.information(self, "Imprimir Ticket", 
            f"Función de impresión en desarrollo.\nTicket ID: {sale_id}")
    
    def load_sales_history(self):
        """Cargar historial de ventas recientes"""
        try:
            today = date.today().isoformat()
            sales = self.sales_manager.get_sales_by_date_range(today, today)
            
            self.recent_sales_table.setRowCount(len(sales[:10]))  # Últimas 10 ventas
            
            for i, sale in enumerate(sales[:10]):
                # Número de ticket
                ticket_item = QTableWidgetItem(sale.get('numero_ticket', ''))
                self.recent_sales_table.setItem(i, 0, ticket_item)
                
                # Cliente
                customer_name = sale.get('cliente_nombre', 'Cliente Ocasional')
                if sale.get('cliente_apellido'):
                    customer_name += f" {sale['cliente_apellido']}"
                customer_item = QTableWidgetItem(customer_name)
                self.recent_sales_table.setItem(i, 1, customer_item)
                
                # Total
                total_item = QTableWidgetItem(f"${sale['total']:.2f}")
                total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.recent_sales_table.setItem(i, 2, total_item)
                
                # Hora
                sale_time = datetime.fromisoformat(sale['fecha_venta']).strftime("%H:%M")
                time_item = QTableWidgetItem(sale_time)
                self.recent_sales_table.setItem(i, 3, time_item)
            
        except Exception as e:
            logger.error(f"Error cargando historial de ventas: {e}")
    
    def view_sale_details(self, index):
        """Ver detalles de una venta"""
        # Placeholder para ver detalles de venta
        QMessageBox.information(self, "Detalles", "Función de detalles de venta en desarrollo")
    
    # Métodos placeholder para funciones adicionales
    def activate_scanner(self):
        """Activar scanner de códigos de barras"""
        QMessageBox.information(self, "Scanner", "Scanner de códigos activado - Ingrese código manualmente")
        self.search_input.setFocus()
    
    def hold_sale(self):
        """Suspender venta actual"""
        QMessageBox.information(self, "Suspender", "Función de suspender venta en desarrollo")
    
    def recall_sale(self):
        """Recuperar venta suspendida"""
        QMessageBox.information(self, "Recuperar", "Función de recuperar venta en desarrollo")
    
    def add_quick_product(self):
        """Agregar producto rápido"""
        QMessageBox.information(self, "Producto Rápido", "Función de producto rápido en desarrollo")
    
    def search_customers(self, search_term):
        """Buscar clientes"""
        # Placeholder para búsqueda de clientes
        pass
    
    def select_customer(self):
        """Seleccionar cliente"""
        QMessageBox.information(self, "Seleccionar Cliente", "Función de selección de cliente en desarrollo")
    
    def add_new_customer(self):
        """Agregar nuevo cliente"""
        QMessageBox.information(self, "Nuevo Cliente", "Función de nuevo cliente en desarrollo")