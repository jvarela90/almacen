"""
Controlador MVC para Sales Widget - AlmacénPro v2.0
Gestión del punto de venta con arquitectura MVC
"""

import logging
from decimal import Decimal
from datetime import datetime, date
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from controllers.base_controller import BaseController
from models.sales_model import SalesModel

logger = logging.getLogger(__name__)

class SalesWidgetController(BaseController):
    """Controlador MVC para el widget de ventas (POS)"""
    
    # Señales personalizadas
    sale_completed = pyqtSignal(dict)
    product_added = pyqtSignal(dict)
    cart_updated = pyqtSignal()
    
    def __init__(self, managers, current_user, parent=None):
        super().__init__(managers, current_user, parent)
        self.sales_manager = managers.get('sales')
        self.product_manager = managers.get('product')
        self.financial_manager = managers.get('financial')
        self.customer_manager = managers.get('customer')
        
        # Modelo de datos
        self.sales_model = SalesModel(
            sales_manager=self.sales_manager,
            product_manager=self.product_manager,
            customer_manager=self.customer_manager,
            parent=self
        )
        
        # Estado del carrito de compras
        self.cart_items = []
        self.current_customer = None
        self.current_sale_id = None
        
        # Totales actuales
        self.subtotal = 0.0
        self.tax_amount = 0.0
        self.discount_amount = 0.0
        self.total_amount = 0.0
        
        # Cargar UI y configurar
        self.load_ui()
        self.setup_ui()
        self.connect_signals()
        self.setup_shortcuts()
        self.setup_scanner()
        
        # Timer para auto-guardar carrito
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self.autosave_cart)
        self.autosave_timer.start(30000)  # 30 segundos
    
    def get_ui_file_path(self) -> str:
        """Retorna la ruta al archivo .ui"""
        return "views/forms/sales_widget.ui"
    
    def setup_ui(self):
        """Configurar elementos específicos de la UI después de cargar"""
        # Configurar tabla de productos
        if hasattr(self, 'tblProductos'):
            self.setup_products_table()
        
        # Configurar tabla de carrito
        if hasattr(self, 'tblCarrito'):
            self.setup_cart_table()
        
        # Configurar campos de totales
        self.update_totals_display()
        
        # Cargar datos iniciales
        self.load_initial_data()
    
    def connect_signals(self):
        """Conectar señales específicas del controlador"""
        # Conectar botones de acción
        if hasattr(self, 'btnAgregarProducto'):
            self.btnAgregarProducto.clicked.connect(self.add_product_to_cart)
        
        if hasattr(self, 'btnProcesarVenta'):
            self.btnProcesarVenta.clicked.connect(self.process_sale)
        
        if hasattr(self, 'btnLimpiarCarrito'):
            self.btnLimpiarCarrito.clicked.connect(self.clear_cart)
        
        if hasattr(self, 'btnSeleccionarCliente'):
            self.btnSeleccionarCliente.clicked.connect(self.select_customer)
        
        # Conectar campos de búsqueda
        if hasattr(self, 'lineEditBuscar'):
            self.lineEditBuscar.textChanged.connect(self.search_products)
            self.lineEditBuscar.returnPressed.connect(self.search_and_add_first)
        
        # Conectar eventos de tabla
        if hasattr(self, 'tblProductos'):
            self.tblProductos.itemDoubleClicked.connect(self.on_product_double_click)
        
        if hasattr(self, 'tblCarrito'):
            self.tblCarrito.itemDoubleClicked.connect(self.on_cart_item_double_click)
    
    def setup_shortcuts(self):
        """Configurar atajos de teclado"""
        # Atajo para procesar venta (F2)
        shortcut_process = QShortcut(QKeySequence("F2"), self)
        shortcut_process.activated.connect(self.process_sale)
        
        # Atajo para limpiar carrito (F3)
        shortcut_clear = QShortcut(QKeySequence("F3"), self)
        shortcut_clear.activated.connect(self.clear_cart)
        
        # Atajo para búsqueda (F4)
        shortcut_search = QShortcut(QKeySequence("F4"), self)
        shortcut_search.activated.connect(lambda: self.lineEditBuscar.setFocus() if hasattr(self, 'lineEditBuscar') else None)
    
    def setup_scanner(self):
        """Configurar scanner de códigos de barras"""
        # Configurar para recibir input del scanner
        if hasattr(self, 'lineEditBuscar'):
            self.lineEditBuscar.setPlaceholderText("Buscar producto o escanear código...")
    
    def setup_products_table(self):
        """Configurar tabla de productos"""
        if not hasattr(self, 'tblProductos'):
            return
            
        headers = ["ID", "Código", "Nombre", "Precio", "Stock", "Categoría"]
        self.tblProductos.setColumnCount(len(headers))
        self.tblProductos.setHorizontalHeaderLabels(headers)
        
        # Configurar columnas
        header = self.tblProductos.horizontalHeader()
        header.setStretchLastSection(True)
        header.resizeSection(0, 50)   # ID
        header.resizeSection(1, 100)  # Código
        header.resizeSection(2, 200)  # Nombre
        header.resizeSection(3, 80)   # Precio
        header.resizeSection(4, 60)   # Stock
        
        # Configurar selección
        self.tblProductos.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tblProductos.setAlternatingRowColors(True)
    
    def setup_cart_table(self):
        """Configurar tabla de carrito"""
        if not hasattr(self, 'tblCarrito'):
            return
            
        headers = ["Producto", "Cantidad", "Precio", "Total"]
        self.tblCarrito.setColumnCount(len(headers))
        self.tblCarrito.setHorizontalHeaderLabels(headers)
        
        # Configurar columnas
        header = self.tblCarrito.horizontalHeader()
        header.setStretchLastSection(True)
        header.resizeSection(0, 200)  # Producto
        header.resizeSection(1, 80)   # Cantidad
        header.resizeSection(2, 80)   # Precio
        
        # Configurar selección
        self.tblCarrito.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tblCarrito.setAlternatingRowColors(True)
    
    def load_initial_data(self):
        """Cargar datos iniciales"""
        self.load_products()
        self.update_customer_display()
    
    def load_products(self):
        """Cargar productos en la tabla"""
        if not self.product_manager or not hasattr(self, 'tblProductos'):
            return
        
        try:
            products = self.product_manager.get_all_products()
            self.tblProductos.setRowCount(len(products))
            
            for row, product in enumerate(products):
                self.tblProductos.setItem(row, 0, QTableWidgetItem(str(product.get('id', ''))))
                self.tblProductos.setItem(row, 1, QTableWidgetItem(str(product.get('codigo', ''))))
                self.tblProductos.setItem(row, 2, QTableWidgetItem(str(product.get('nombre', ''))))
                self.tblProductos.setItem(row, 3, QTableWidgetItem(f"${product.get('precio', 0):.2f}"))
                self.tblProductos.setItem(row, 4, QTableWidgetItem(str(product.get('stock', 0))))
                self.tblProductos.setItem(row, 5, QTableWidgetItem(str(product.get('categoria', ''))))
        
        except Exception as e:
            logger.error(f"Error cargando productos: {e}")
    
    def search_products(self, text):
        """Buscar productos por texto"""
        if not text.strip():
            self.load_products()
            return
        
        try:
            products = self.product_manager.search_products(text)
            self.tblProductos.setRowCount(len(products))
            
            for row, product in enumerate(products):
                self.tblProductos.setItem(row, 0, QTableWidgetItem(str(product.get('id', ''))))
                self.tblProductos.setItem(row, 1, QTableWidgetItem(str(product.get('codigo', ''))))
                self.tblProductos.setItem(row, 2, QTableWidgetItem(str(product.get('nombre', ''))))
                self.tblProductos.setItem(row, 3, QTableWidgetItem(f"${product.get('precio', 0):.2f}"))
                self.tblProductos.setItem(row, 4, QTableWidgetItem(str(product.get('stock', 0))))
                self.tblProductos.setItem(row, 5, QTableWidgetItem(str(product.get('categoria', ''))))
        
        except Exception as e:
            logger.error(f"Error buscando productos: {e}")
    
    def add_product_to_cart(self):
        """Agregar producto seleccionado al carrito"""
        if not hasattr(self, 'tblProductos'):
            return
            
        current_row = self.tblProductos.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Selección", "Seleccione un producto para agregar")
            return
        
        try:
            product_id = int(self.tblProductos.item(current_row, 0).text())
            product = self.product_manager.get_product_by_id(product_id)
            
            if not product:
                QMessageBox.warning(self, "Error", "Producto no encontrado")
                return
            
            # Verificar stock
            if product.get('stock', 0) <= 0:
                QMessageBox.warning(self, "Stock", "Producto sin stock disponible")
                return
            
            # Agregar al carrito
            cart_item = {
                'product_id': product_id,
                'nombre': product.get('nombre', ''),
                'precio': float(product.get('precio', 0)),
                'cantidad': 1,
                'total': float(product.get('precio', 0))
            }
            
            self.cart_items.append(cart_item)
            self.update_cart_display()
            self.update_totals()
            
            self.product_added.emit(cart_item)
            self.cart_updated.emit()
            
        except Exception as e:
            logger.error(f"Error agregando producto al carrito: {e}")
            QMessageBox.critical(self, "Error", f"Error agregando producto: {e}")
    
    def update_cart_display(self):
        """Actualizar display del carrito"""
        if not hasattr(self, 'tblCarrito'):
            return
            
        self.tblCarrito.setRowCount(len(self.cart_items))
        
        for row, item in enumerate(self.cart_items):
            self.tblCarrito.setItem(row, 0, QTableWidgetItem(item['nombre']))
            self.tblCarrito.setItem(row, 1, QTableWidgetItem(str(item['cantidad'])))
            self.tblCarrito.setItem(row, 2, QTableWidgetItem(f"${item['precio']:.2f}"))
            self.tblCarrito.setItem(row, 3, QTableWidgetItem(f"${item['total']:.2f}"))
    
    def update_totals(self):
        """Actualizar totales de la venta"""
        self.subtotal = sum(item['total'] for item in self.cart_items)
        self.tax_amount = self.subtotal * 0.21  # IVA 21%
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
        
        self.update_totals_display()
    
    def update_totals_display(self):
        """Actualizar display de totales"""
        if hasattr(self, 'lblSubtotal'):
            self.lblSubtotal.setText(f"${self.subtotal:.2f}")
        if hasattr(self, 'lblImpuestos'):
            self.lblImpuestos.setText(f"${self.tax_amount:.2f}")
        if hasattr(self, 'lblDescuento'):
            self.lblDescuento.setText(f"${self.discount_amount:.2f}")
        if hasattr(self, 'lblTotal'):
            self.lblTotal.setText(f"${self.total_amount:.2f}")
    
    def clear_cart(self):
        """Limpiar carrito de compras"""
        if not self.cart_items:
            return
            
        reply = QMessageBox.question(
            self, "Limpiar Carrito",
            "¿Está seguro que desea limpiar el carrito?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.cart_items.clear()
            self.current_customer = None
            self.discount_amount = 0.0
            
            self.update_cart_display()
            self.update_totals()
            self.update_customer_display()
            
            self.cart_updated.emit()
    
    def process_sale(self):
        """Procesar venta actual"""
        if not self.cart_items:
            QMessageBox.warning(self, "Carrito Vacío", "Agregue productos al carrito antes de procesar la venta")
            return
        
        try:
            # Datos de la venta
            sale_data = {
                'customer_id': self.current_customer['id'] if self.current_customer else None,
                'user_id': self.current_user['id'],
                'items': self.cart_items,
                'subtotal': self.subtotal,
                'tax_amount': self.tax_amount,
                'discount_amount': self.discount_amount,
                'total_amount': self.total_amount,
                'payment_method': 'efectivo',  # Por defecto
                'fecha': datetime.now()
            }
            
            # Procesar venta
            sale_result = self.sales_manager.create_sale(sale_data)
            
            if sale_result['success']:
                QMessageBox.information(self, "Venta Procesada", 
                                      f"Venta #{sale_result['sale_id']} procesada exitosamente")
                
                # Limpiar carrito
                self.clear_cart()
                
                # Actualizar productos (stock)
                self.load_products()
                
                self.sale_completed.emit(sale_result)
            else:
                QMessageBox.critical(self, "Error", f"Error procesando venta: {sale_result['message']}")
        
        except Exception as e:
            logger.error(f"Error procesando venta: {e}")
            QMessageBox.critical(self, "Error", f"Error procesando venta: {e}")
    
    def select_customer(self):
        """Seleccionar cliente para la venta"""
        # Aquí se abriría un diálogo de selección de clientes
        # Por ahora implementamos una versión simplificada
        QMessageBox.information(self, "Seleccionar Cliente", 
                               "Funcionalidad de selección de cliente en desarrollo")
    
    def update_customer_display(self):
        """Actualizar display del cliente actual"""
        if hasattr(self, 'lblCliente'):
            if self.current_customer:
                self.lblCliente.setText(f"Cliente: {self.current_customer['nombre']}")
            else:
                self.lblCliente.setText("Cliente: No seleccionado")
    
    def autosave_cart(self):
        """Auto-guardar carrito (funcionalidad futura)"""
        # Implementar auto-guardado del carrito si es necesario
        pass
    
    def search_and_add_first(self):
        """Buscar y agregar primer resultado (para scanner)"""
        if hasattr(self, 'lineEditBuscar') and self.lineEditBuscar.text().strip():
            # Simular selección del primer producto y agregar
            if hasattr(self, 'tblProductos') and self.tblProductos.rowCount() > 0:
                self.tblProductos.setCurrentCell(0, 0)
                self.add_product_to_cart()
    
    def on_product_double_click(self, item):
        """Manejar doble click en producto"""
        self.add_product_to_cart()
    
    def on_cart_item_double_click(self, item):
        """Manejar doble click en item del carrito"""
        # Permitir editar cantidad o eliminar item
        row = item.row()
        if 0 <= row < len(self.cart_items):
            # Mostrar diálogo para editar cantidad o eliminar
            QMessageBox.information(self, "Editar Item", 
                                   "Funcionalidad de edición de items en desarrollo")