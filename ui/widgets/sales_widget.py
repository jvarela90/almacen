"""
Widget de Ventas para AlmacénPro
Interfaz principal de punto de venta (POS) con scanner, carrito y facturación
"""

import logging
from decimal import Decimal
from datetime import datetime, date
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

logger = logging.getLogger(__name__)

class SalesWidget(QWidget):
    """Widget principal para gestionar ventas (POS)"""
    
    # Señales personalizadas
    sale_completed = pyqtSignal(dict)
    product_added = pyqtSignal(dict)
    cart_updated = pyqtSignal()
    
    def __init__(self, sales_manager, product_manager, user_manager, parent=None):
        super().__init__(parent)
        self.sales_manager = sales_manager
        self.product_manager = product_manager
        self.user_manager = user_manager
        
        # Estado del carrito de compras
        self.cart_items = []
        self.current_customer = None
        self.current_sale_id = None
        
        # Totales actuales
        self.subtotal = 0.0
        self.tax_amount = 0.0
        self.discount_amount = 0.0
        self.total_amount = 0.0
        
        self.init_ui()
        self.setup_shortcuts()
        self.setup_scanner()
        
        # Timer para auto-guardar carrito
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self.autosave_cart)
        self.autosave_timer.start(30000)  # 30 segundos
    
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
        header = QWidget()
        header.setObjectName("sales_header")
        header_layout = QHBoxLayout(header)
        
        title = QLabel("🛒 Punto de Venta")
        title.setObjectName("sales_title")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Información del usuario
        user_info = QLabel(f"Cajero: {self.user_manager.current_user.get('nombre_completo', 'Usuario')}")
        user_info.setObjectName("user_info")
        header_layout.addWidget(user_info)
        
        layout.addWidget(header)
        
        # Scanner/Búsqueda de productos
        scanner_group = QGroupBox("Buscar Producto")
        scanner_layout = QVBoxLayout(scanner_group)
        
        # Campo de búsqueda/scanner
        search_layout = QHBoxLayout()
        
        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText("Escanear código o buscar producto...")
        self.product_search.returnPressed.connect(self.search_or_scan_product)
        self.product_search.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.product_search)
        
        search_btn = QPushButton("🔍")
        search_btn.setMaximumWidth(40)
        search_btn.clicked.connect(self.search_or_scan_product)
        search_layout.addWidget(search_btn)
        
        scanner_layout.addLayout(search_layout)
        
        # Lista de resultados de búsqueda
        self.search_results = QListWidget()
        self.search_results.setMaximumHeight(200)
        self.search_results.itemDoubleClicked.connect(self.add_selected_product)
        self.search_results.hide()  # Oculto inicialmente
        
        scanner_layout.addWidget(self.search_results)
        layout.addWidget(scanner_group)
        
        # Accesos rápidos a productos
        quick_access_group = QGroupBox("Accesos Rápidos")
        quick_layout = QGridLayout(quick_access_group)
        
        # Botones de productos frecuentes (placeholder)
        quick_products = [
            ("🥤 Bebidas", self.quick_add_beverage),
            ("🍫 Golosinas", self.quick_add_candy),
            ("🍞 Panadería", self.quick_add_bakery),
            ("🧴 Limpieza", self.quick_add_cleaning)
        ]
        
        for i, (text, callback) in enumerate(quick_products):
            btn = QPushButton(text)
            btn.setMinimumHeight(60)
            btn.clicked.connect(callback)
            quick_layout.addWidget(btn, i // 2, i % 2)
        
        layout.addWidget(quick_access_group)
        
        # Información adicional
        info_group = QGroupBox("Información")
        info_layout = QVBoxLayout(info_group)
        
        self.sales_info = QLabel("Ventas de hoy: Cargando...")
        self.sales_info.setStyleSheet("color: #2c3e50; font-size: 12px;")
        info_layout.addWidget(self.sales_info)
        
        layout.addWidget(info_group)
        
        layout.addStretch()
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Crear panel derecho con carrito y checkout"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Información del cliente
        customer_group = QGroupBox("Cliente")
        customer_layout = QHBoxLayout(customer_group)
        
        self.customer_label = QLabel("Cliente General")
        self.customer_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        customer_layout.addWidget(self.customer_label)
        
        customer_layout.addStretch()
        
        select_customer_btn = QPushButton("👤 Seleccionar")
        select_customer_btn.clicked.connect(self.select_customer)
        customer_layout.addWidget(select_customer_btn)
        
        layout.addWidget(customer_group)
        
        # Carrito de compras
        cart_group = QGroupBox("Carrito de Compras")
        cart_layout = QVBoxLayout(cart_group)
        
        # Tabla del carrito
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(6)
        self.cart_table.setHorizontalHeaderLabels([
            "Producto", "Cant.", "Precio Unit.", "Desc.", "IVA", "Total"
        ])
        
        # Configurar tabla
        self.cart_table.setAlternatingRowColors(True)
        self.cart_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cart_table.verticalHeader().setVisible(False)
        
        # Ajustar columnas
        header = self.cart_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Producto
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Cantidad
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Precio
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Descuento
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # IVA
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Total
        
        cart_layout.addWidget(self.cart_table)
        
        # Botones del carrito
        cart_buttons_layout = QHBoxLayout()
        
        clear_cart_btn = QPushButton("🗑️ Limpiar Carrito")
        clear_cart_btn.clicked.connect(self.clear_cart)
        cart_buttons_layout.addWidget(clear_cart_btn)
        
        cart_buttons_layout.addStretch()
        
        remove_item_btn = QPushButton("➖ Quitar Item")
        remove_item_btn.clicked.connect(self.remove_selected_item)
        cart_buttons_layout.addWidget(remove_item_btn)
        
        cart_layout.addLayout(cart_buttons_layout)
        layout.addWidget(cart_group)
        
        # Panel de totales
        totals_group = QGroupBox("Totales")
        totals_layout = QGridLayout(totals_group)
        
        # Labels de totales
        self.subtotal_label = QLabel("$0.00")
        self.tax_label = QLabel("$0.00")
        self.discount_label = QLabel("$0.00")
        self.total_label = QLabel("$0.00")
        
        # Estilos para totales
        self.subtotal_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.tax_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.discount_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #e74c3c;")
        self.total_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #27ae60;")
        
        totals_layout.addWidget(QLabel("Subtotal:"), 0, 0)
        totals_layout.addWidget(self.subtotal_label, 0, 1)
        totals_layout.addWidget(QLabel("Descuentos:"), 1, 0)
        totals_layout.addWidget(self.discount_label, 1, 1)
        totals_layout.addWidget(QLabel("IVA:"), 2, 0)
        totals_layout.addWidget(self.tax_label, 2, 1)
        
        # Línea separadora
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        totals_layout.addWidget(line, 3, 0, 1, 2)
        
        totals_layout.addWidget(QLabel("TOTAL:"), 4, 0)
        totals_layout.addWidget(self.total_label, 4, 1)
        
        layout.addWidget(totals_group)
        
        # Botones de acción principal
        actions_layout = QHBoxLayout()
        
        # Botón de descuento
        discount_btn = QPushButton("💸 Descuento")
        discount_btn.setMinimumHeight(50)
        discount_btn.clicked.connect(self.apply_discount)
        actions_layout.addWidget(discount_btn)
        
        # Botón de pago
        pay_btn = QPushButton("💳 COBRAR")
        pay_btn.setMinimumHeight(50)
        pay_btn.setObjectName("pay_button")
        pay_btn.clicked.connect(self.process_payment)
        actions_layout.addWidget(pay_btn)
        
        layout.addLayout(actions_layout)
        
        return panel
    
    def setup_shortcuts(self):
        """Configurar atajos de teclado"""
        shortcuts = [
            ("F1", self.show_help),
            ("F2", self.process_payment),
            ("F3", self.apply_discount),
            ("F4", self.select_customer),
            ("F5", self.clear_cart),
            ("Ctrl+F", lambda: self.product_search.setFocus()),
            ("Escape", self.clear_search_or_cart),
            ("Delete", self.remove_selected_item),
            ("Enter", self.search_or_scan_product)
        ]
        
        for shortcut_key, callback in shortcuts:
            shortcut = QShortcut(QKeySequence(shortcut_key), self)
            shortcut.activated.connect(callback)
    
    def setup_scanner(self):
        """Configurar scanner de código de barras"""
        # El scanner generalmente envía el código seguido de Enter
        # Ya manejado por returnPressed del QLineEdit
        pass
    
    def on_search_changed(self, text: str):
        """Manejar cambio en búsqueda"""
        if len(text) >= 3:  # Buscar después de 3 caracteres
            self.search_products(text)
        elif len(text) == 0:
            self.search_results.hide()
    
    def search_products(self, search_term: str):
        """Buscar productos"""
        try:
            products = self.product_manager.search_products(search_term, limit=10)
            
            self.search_results.clear()
            
            if products:
                for product in products:
                    item_text = f"{product['nombre']} - ${product['precio_venta']:.2f}"
                    if product.get('codigo_barras'):
                        item_text += f" ({product['codigo_barras']})"
                    
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, product)
                    self.search_results.addItem(item)
                
                self.search_results.show()
            else:
                self.search_results.hide()
                
        except Exception as e:
            logger.error(f"Error buscando productos: {e}")
    
    def search_or_scan_product(self):
        """Buscar o escanear producto"""
        search_term = self.product_search.text().strip()
        
        if not search_term:
            return
        
        try:
            # Primero intentar por código de barras exacto
            product = self.product_manager.get_product_by_barcode(search_term)
            
            if product:
                self.add_product_to_cart(product)
                self.product_search.clear()
                self.search_results.hide()
            else:
                # Si no es código exacto, buscar por nombre
                self.search_products(search_term)
                
        except Exception as e:
            logger.error(f"Error buscando producto: {e}")
            QMessageBox.warning(self, "Error", f"Error buscando producto: {e}")
    
    def add_selected_product(self):
        """Agregar producto seleccionado de la lista"""
        current_item = self.search_results.currentItem()
        if current_item:
            product = current_item.data(Qt.UserRole)
            self.add_product_to_cart(product)
            self.product_search.clear()
            self.search_results.hide()
    
    def add_product_to_cart(self, product: dict, quantity: float = 1.0):
        """Agregar producto al carrito"""
        try:
            # Verificar stock disponible
            if not product.get('permite_venta_sin_stock', False):
                if product.get('stock_actual', 0) < quantity:
                    QMessageBox.warning(
                        self, 
                        "Stock Insuficiente", 
                        f"Stock disponible: {product.get('stock_actual', 0)}"
                    )
                    return
            
            # Buscar si el producto ya está en el carrito
            existing_item = None
            for item in self.cart_items:
                if item['producto_id'] == product['id']:
                    existing_item = item
                    break
            
            if existing_item:
                # Incrementar cantidad
                new_quantity = existing_item['cantidad'] + quantity
                
                # Verificar stock nuevamente
                if not product.get('permite_venta_sin_stock', False):
                    if product.get('stock_actual', 0) < new_quantity:
                        QMessageBox.warning(
                            self, 
                            "Stock Insuficiente", 
                            f"No se puede agregar más. Stock disponible: {product.get('stock_actual', 0)}"
                        )
                        return
                
                existing_item['cantidad'] = new_quantity
            else:
                # Agregar nuevo item
                cart_item = {
                    'producto_id': product['id'],
                    'nombre': product['nombre'],
                    'codigo_barras': product.get('codigo_barras', ''),
                    'cantidad': quantity,
                    'precio_unitario': float(product['precio_venta']),
                    'descuento_porcentaje': 0.0,
                    'descuento_importe': 0.0,
                    'impuesto_porcentaje': float(product.get('iva_porcentaje', 21)),
                    'impuesto_importe': 0.0
                }
                
                self.cart_items.append(cart_item)
            
            self.update_cart_display()
            self.calculate_totals()
            
            # Emitir señal
            self.product_added.emit(product)
            
            # Sonido de confirmación (opcional)
            QApplication.beep()
            
        except Exception as e:
            logger.error(f"Error agregando producto al carrito: {e}")
            QMessageBox.warning(self, "Error", f"Error agregando producto: {e}")
    
    def update_cart_display(self):
        """Actualizar visualización del carrito"""
        self.cart_table.setRowCount(len(self.cart_items))
        
        for row, item in enumerate(self.cart_items):
            # Producto
            product_item = QTableWidgetItem(item['nombre'])
            self.cart_table.setItem(row, 0, product_item)
            
            # Cantidad (editable)
            quantity_item = QTableWidgetItem(f"{item['cantidad']:.2f}")
            quantity_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.cart_table.setItem(row, 1, quantity_item)
            
            # Precio unitario
            price_item = QTableWidgetItem(f"${item['precio_unitario']:.2f}")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.cart_table.setItem(row, 2, price_item)
            
            # Descuento
            discount_text = f"{item['descuento_porcentaje']:.1f}%" if item['descuento_porcentaje'] > 0 else "-"
            discount_item = QTableWidgetItem(discount_text)
            discount_item.setTextAlignment(Qt.AlignCenter)
            self.cart_table.setItem(row, 3, discount_item)
            
            # IVA
            tax_text = f"{item['impuesto_porcentaje']:.1f}%"
            tax_item = QTableWidgetItem(tax_text)
            tax_item.setTextAlignment(Qt.AlignCenter)
            self.cart_table.setItem(row, 4, tax_item)
            
            # Total del item
            item_total = self.calculate_item_total(item)
            total_item = QTableWidgetItem(f"${item_total:.2f}")
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            total_item.setFont(QFont("", -1, QFont.Bold))
            self.cart_table.setItem(row, 5, total_item)
        
        # Ajustar altura de filas
        self.cart_table.resizeRowsToContents()
        
        # Emitir señal de actualización
        self.cart_updated.emit()
    
    def calculate_item_total(self, item: dict) -> float:
        """Calcular total de un item del carrito"""
        subtotal = item['cantidad'] * item['precio_unitario']
        descuento = subtotal * (item['descuento_porcentaje'] / 100)
        base_imponible = subtotal - descuento
        impuesto = base_imponible * (item['impuesto_porcentaje'] / 100)
        
        # Actualizar impuesto calculado en el item
        item['impuesto_importe'] = impuesto
        item['descuento_importe'] = descuento
        
        return base_imponible + impuesto
    
    def calculate_totals(self):
        """Calcular totales de la venta"""
        self.subtotal = 0.0
        self.tax_amount = 0.0
        self.discount_amount = 0.0
        
        for item in self.cart_items:
            item_subtotal = item['cantidad'] * item['precio_unitario']
            item_discount = item_subtotal * (item['descuento_porcentaje'] / 100)
            item_tax = (item_subtotal - item_discount) * (item['impuesto_porcentaje'] / 100)
            
            self.subtotal += item_subtotal
            self.discount_amount += item_discount
            self.tax_amount += item_tax
        
        self.total_amount = self.subtotal - self.discount_amount + self.tax_amount
        
        # Actualizar labels
        self.subtotal_label.setText(f"${self.subtotal:.2f}")
        self.discount_label.setText(f"${self.discount_amount:.2f}")
        self.tax_label.setText(f"${self.tax_amount:.2f}")
        self.total_label.setText(f"${self.total_amount:.2f}")
    
    def remove_selected_item(self):
        """Remover item seleccionado del carrito"""
        current_row = self.cart_table.currentRow()
        if current_row >= 0 and current_row < len(self.cart_items):
            # Confirmar eliminación
            item_name = self.cart_items[current_row]['nombre']
            reply = QMessageBox.question(
                self, 
                "Confirmar", 
                f"¿Remover '{item_name}' del carrito?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                del self.cart_items[current_row]
                self.update_cart_display()
                self.calculate_totals()
    
    def clear_cart(self):
        """Limpiar carrito completamente"""
        if self.cart_items:
            reply = QMessageBox.question(
                self, 
                "Confirmar", 
                "¿Limpiar todo el carrito?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.cart_items.clear()
                self.update_cart_display()
                self.calculate_totals()
    
    def clear_search_or_cart(self):
        """Limpiar búsqueda o carrito según contexto"""
        if self.product_search.text():
            self.product_search.clear()
            self.search_results.hide()
        elif self.cart_items:
            self.clear_cart()
    
    def select_customer(self):
        """Seleccionar cliente"""
        # Por ahora un diálogo simple
        customer_name, ok = QInputDialog.getText(
            self, 
            "Seleccionar Cliente", 
            "Nombre del cliente:",
            text="Cliente General"
        )
        
        if ok and customer_name.strip():
            self.current_customer = {
                'id': None,
                'nombre': customer_name.strip()
            }
            self.customer_label.setText(customer_name.strip())
    
    def apply_discount(self):
        """Aplicar descuento"""
        if not self.cart_items:
            QMessageBox.information(self, "Información", "No hay productos en el carrito")
            return
        
        # Diálogo simple para descuento
        discount_percent, ok = QInputDialog.getDouble(
            self, 
            "Aplicar Descuento", 
            "Porcentaje de descuento:",
            value=0.0, min=0.0, max=50.0, decimals=1
        )
        
        if ok and discount_percent > 0:
            # Aplicar descuento a todos los items
            for item in self.cart_items:
                item['descuento_porcentaje'] = discount_percent
            
            self.update_cart_display()
            self.calculate_totals()
    
    def process_payment(self):
        """Procesar pago"""
        if not self.cart_items:
            QMessageBox.information(self, "Información", "No hay productos en el carrito")
            return
        
        if self.total_amount <= 0:
            QMessageBox.warning(self, "Error", "El total debe ser mayor a cero")
            return
        
        try:
            # Mostrar diálogo de pago
            payment_dialog = PaymentDialog(self.total_amount, self)
            
            if payment_dialog.exec_() == QDialog.Accepted:
                payment_info = payment_dialog.get_payment_info()
                self.complete_sale(payment_info)
                
        except Exception as e:
            logger.error(f"Error procesando pago: {e}")
            QMessageBox.critical(self, "Error", f"Error procesando pago: {e}")
    
    def complete_sale(self, payment_info: dict):
        """Completar venta"""
        try:
            # Preparar datos de la venta
            sale_data = {
                'cliente_id': self.current_customer.get('id') if self.current_customer else None,
                'tipo_comprobante': 'TICKET',
                'subtotal': self.subtotal,
                'descuento_importe': self.discount_amount,
                'impuestos_importe': self.tax_amount,
                'total': self.total_amount
            }
            
            # Preparar items
            sale_items = []
            for item in self.cart_items:
                sale_items.append({
                    'producto_id': item['producto_id'],
                    'cantidad': item['cantidad'],
                    'precio_unitario': item['precio_unitario'],
                    'descuento_porcentaje': item['descuento_porcentaje'],
                    'descuento_importe': item['descuento_importe'],
                    'impuesto_porcentaje': item['impuesto_porcentaje'],
                    'impuesto_importe': item['impuesto_importe']
                })
            
            # Preparar pagos
            payments = [{
                'metodo_pago': payment_info['method'],
                'importe': payment_info['amount'],
                'referencia': payment_info.get('reference', ''),
                'observaciones': payment_info.get('notes', '')
            }]
            
            # Crear venta
            success, message, sale_id = self.sales_manager.create_sale(
                sale_data, sale_items, payments, 
                self.user_manager.current_user['id']
            )
            
            if success:
                # Venta exitosa
                self.current_sale_id = sale_id
                
                # Mostrar confirmación
                self.show_sale_confirmation(sale_id, payment_info)
                
                # Limpiar carrito
                self.cart_items.clear()
                self.current_customer = None
                self.customer_label.setText("Cliente General")
                self.update_cart_display()
                self.calculate_totals()
                
                # Emitir señal
                self.sale_completed.emit({
                    'id': sale_id,
                    'total': self.total_amount,
                    'items': len(sale_items),
                    'customer': self.current_customer
                })
                
                # Foco en búsqueda para próxima venta
                self.product_search.setFocus()
                
            else:
                QMessageBox.critical(self, "Error", f"Error completando venta: {message}")
                
        except Exception as e:
            logger.error(f"Error completando venta: {e}")
            QMessageBox.critical(self, "Error", f"Error completando venta: {e}")
    
    def show_sale_confirmation(self, sale_id: int, payment_info: dict):
        """Mostrar confirmación de venta"""
        change_amount = payment_info.get('change', 0)
        
        confirmation_text = f"""
        ✅ VENTA COMPLETADA
        
        Número de Venta: #{sale_id}
        Total: ${self.total_amount:.2f}
        Método de Pago: {payment_info['method']}
        Pago Recibido: ${payment_info['amount']:.2f}
        """
        
        if change_amount > 0:
            confirmation_text += f"Cambio: ${change_amount:.2f}"
        
        confirmation_text += f"\n\n¿Desea imprimir el ticket?"
        
        reply = QMessageBox.question(
            self, 
            "Venta Completada", 
            confirmation_text,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            self.print_ticket(sale_id)
    
    def print_ticket(self, sale_id: int):
        """Imprimir ticket de venta"""
        try:
            # Por ahora solo mostrar mensaje
            QMessageBox.information(
                self, 
                "Imprimir Ticket", 
                f"Enviando ticket #{sale_id} a impresora...\n(Funcionalidad en desarrollo)"
            )
            
        except Exception as e:
            logger.error(f"Error imprimiendo ticket: {e}")
            QMessageBox.warning(self, "Error", f"Error imprimiendo ticket: {e}")
    
    def autosave_cart(self):
        """Auto-guardar carrito para recuperación"""
        try:
            if self.cart_items:
                # Guardar en configuración temporal
                cart_data = {
                    'items': self.cart_items,
                    'customer': self.current_customer,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Por ahora solo log, en futuro guardar en archivo temporal
                logger.debug(f"Auto-guardando carrito: {len(self.cart_items)} items")
                
        except Exception as e:
            logger.error(f"Error auto-guardando carrito: {e}")
    
    def load_daily_sales_info(self):
        """Cargar información de ventas del día"""
        try:
            today_stats = self.sales_manager.get_daily_summary()
            
            if 'error' not in today_stats:
                sales_text = f"Ventas de hoy: {today_stats.get('total_ventas', 0)} | ${today_stats.get('monto_total', 0):.2f}"
                self.sales_info.setText(sales_text)
            else:
                self.sales_info.setText("Ventas de hoy: Error cargando datos")
                
        except Exception as e:
            logger.error(f"Error cargando info de ventas: {e}")
            self.sales_info.setText("Ventas de hoy: Error cargando datos")
    
    def setup_styles(self):
        """Configurar estilos CSS"""
        self.setStyleSheet("""
            #sales_header {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #27ae60, stop:1 #2ecc71);
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 10px;
            }
            
            #sales_title {
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
            
            #user_info {
                color: #d5f4e6;
                font-size: 12px;
                font-weight: bold;
            }
            
            #pay_button {
                background-color: #27ae60;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            
            #pay_button:hover {
                background-color: #2ecc71;
            }
            
            #pay_button:pressed {
                background-color: #229954;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #2c3e50;
            }
        """)
    
    # Métodos de accesos rápidos (placeholder)
    def quick_add_beverage(self):
        """Acceso rápido a bebidas"""
        self.product_search.setText("bebida")
        self.search_or_scan_product()
    
    def quick_add_candy(self):
        """Acceso rápido a golosinas"""
        self.product_search.setText("dulce")
        self.search_or_scan_product()
    
    def quick_add_bakery(self):
        """Acceso rápido a panadería"""
        self.product_search.setText("pan")
        self.search_or_scan_product()
    
    def quick_add_cleaning(self):
        """Acceso rápido a limpieza"""
        self.product_search.setText("limpieza")
        self.search_or_scan_product()
    
    def show_help(self):
        """Mostrar ayuda de atajos"""
        help_text = """
        ATAJOS DE TECLADO:
        
        F1 - Mostrar esta ayuda
        F2 - Procesar pago
        F3 - Aplicar descuento
        F4 - Seleccionar cliente
        F5 - Limpiar carrito
        
        Ctrl+F - Buscar producto
        Enter - Buscar/Escanear
        Escape - Limpiar búsqueda o carrito
        Delete - Quitar item seleccionado
        """
        
        QMessageBox.information(self, "Ayuda - Atajos de Teclado", help_text)
    
    def refresh_data(self):
        """Actualizar datos del widget"""
        self.load_daily_sales_info()
    
    def closeEvent(self, event):
        """Manejar cierre del widget"""
        # Detener timer de auto-guardado
        if hasattr(self, 'autosave_timer'):
            self.autosave_timer.stop()
        
        # Advertir si hay carrito con items
        if self.cart_items:
            reply = QMessageBox.question(
                self, 
                "Confirmar Cierre", 
                "Hay productos en el carrito. ¿Desea cerrar sin completar la venta?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
        
        event.accept()


class PaymentDialog(QDialog):
    """Diálogo para procesar pago"""
    
    def __init__(self, total_amount: float, parent=None):
        super().__init__(parent)
        self.total_amount = total_amount
        self.payment_info = {}
        
        self.setWindowTitle("Procesar Pago")
        self.setModal(True)
        self.resize(400, 300)
        
        self.init_ui()
    
    def init_ui(self):
        """Inicializar interfaz"""
        layout = QVBoxLayout(self)
        
        # Total a pagar
        total_label = QLabel(f"TOTAL A PAGAR: ${self.total_amount:.2f}")
        total_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #27ae60;")
        total_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(total_label)
        
        # Método de pago
        method_group = QGroupBox("Método de Pago")
        method_layout = QVBoxLayout(method_group)
        
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            "EFECTIVO", "TARJETA_DEBITO", "TARJETA_CREDITO", 
            "TRANSFERENCIA", "CUENTA_CORRIENTE"
        ])
        method_layout.addWidget(self.method_combo)
        
        layout.addWidget(method_group)
        
        # Monto recibido
        amount_group = QGroupBox("Monto Recibido")
        amount_layout = QVBoxLayout(amount_group)
        
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMaximum(999999.99)
        self.amount_input.setDecimals(2)
        self.amount_input.setValue(self.total_amount)
        self.amount_input.valueChanged.connect(self.calculate_change)
        amount_layout.addWidget(self.amount_input)
        
        layout.addWidget(amount_group)
        
        # Cambio
        self.change_label = QLabel("Cambio: $0.00")
        self.change_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #e74c3c;")
        layout.addWidget(self.change_label)
        
        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Calcular cambio inicial
        self.calculate_change()
    
    def calculate_change(self):
        """Calcular cambio"""
        received = self.amount_input.value()
        change = received - self.total_amount
        
        if change >= 0:
            self.change_label.setText(f"Cambio: ${change:.2f}")
            self.change_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #27ae60;")
        else:
            self.change_label.setText(f"Falta: ${abs(change):.2f}")
            self.change_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #e74c3c;")
    
    def accept(self):
        """Aceptar pago"""
        received = self.amount_input.value()
        
        if received < self.total_amount:
            QMessageBox.warning(self, "Error", "El monto recibido es insuficiente")
            return
        
        self.payment_info = {
            'method': self.method_combo.currentText(),
            'amount': received,
            'change': received - self.total_amount,
            'total': self.total_amount
        }
        
        super().accept()
    
    def get_payment_info(self) -> dict:
        """Obtener información del pago"""
        return self.payment_info