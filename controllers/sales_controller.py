"""
Controlador de Ventas - AlmacénPro v2.0 MVC
Controlador que gestiona la interfaz de ventas usando Qt Designer
"""

import os
import logging
from typing import Dict, List, Optional, Any
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from .base_controller import BaseController
from models.sales_model import SalesModel
from models.entities import Product, Customer, SaleItem

logger = logging.getLogger(__name__)

class SalesController(BaseController):
    """Controlador principal para gestionar ventas (POS)"""
    
    # Señales de comunicación con otros componentes
    sale_completed = pyqtSignal(dict)
    product_added = pyqtSignal(dict)
    customer_selected = pyqtSignal(dict)
    
    def __init__(self, managers: Dict, current_user: Dict, parent=None):
        # Managers específicos
        self.sales_manager = managers.get('sales')
        self.product_manager = managers.get('product')
        self.customer_manager = managers.get('customer')
        
        # Modelo de datos
        self.sales_model = SalesModel()
        
        # Estado del controlador
        self.available_products = []
        self.filtered_products = []
        
        # Inicializar controlador base
        super().__init__(managers, current_user, parent)
    
    def get_ui_file_path(self) -> str:
        """Retornar ruta al archivo .ui correspondiente"""
        return os.path.join(os.path.dirname(__file__), '..', 'views', 'forms', 'sales_widget.ui')
    
    def setup_ui(self):
        """Configurar elementos específicos de la UI"""
        # Configurar información del usuario
        self.lblUsuario.setText(f"Cajero: {self.current_user.get('nombre_completo', 'Usuario')}")
        
        # Configurar tablas
        self.setup_products_table()
        self.setup_cart_table()
        
        # Configurar validadores
        self.setup_validators()
        
        # Estado inicial
        self.reset_form()
        
        # Aplicar estilos específicos del módulo
        from utils.style_manager import StyleManager
        StyleManager.apply_module_styles(self, 'sales')
    
    def setup_products_table(self):
        """Configurar tabla de productos disponibles"""
        headers = ['Código', 'Nombre', 'Categoría', 'Precio', 'Stock', 'Descripción']
        column_widths = [80, -1, 120, 80, 60, 200]  # -1 = stretch, 0 = resize to contents
        
        self.setup_table_widget(self.tblProductosDisponibles, headers, column_widths)
        
        # Configurar ordenamiento
        self.tblProductosDisponibles.setSortingEnabled(True)
        self.tblProductosDisponibles.sortByColumn(1, Qt.AscendingOrder)  # Ordenar por nombre
    
    def setup_cart_table(self):
        """Configurar tabla del carrito"""
        headers = ['Código', 'Producto', 'Cantidad', 'Precio Unit.', 'Subtotal', 'Acciones']
        column_widths = [80, -1, 80, 100, 100, 80]
        
        self.setup_table_widget(self.tblCarrito, headers, column_widths)
    
    def setup_validators(self):
        """Configurar validadores de entrada"""
        # Validador para cantidad (solo enteros positivos)
        self.spinCantidadAgregar.setMinimum(1)
        self.spinCantidadAgregar.setMaximum(9999)
        self.spinCantidadAgregar.setValue(1)
        
        # Configurar campo de búsqueda
        self.lineEditBuscarProducto.setMaxLength(100)
    
    def connect_signals(self):
        """Conectar señales específicas del controlador"""
        # Búsqueda de productos
        self.lineEditBuscarProducto.textChanged.connect(self.on_search_products)
        self.lineEditBuscarProducto.returnPressed.connect(self.on_search_enter_pressed)
        self.btnBuscar.clicked.connect(self.on_search_clicked)
        self.btnLimpiarBusqueda.clicked.connect(self.on_clear_search)
        
        # Tabla de productos
        self.tblProductosDisponibles.itemSelectionChanged.connect(self.on_product_selected)
        self.tblProductosDisponibles.itemDoubleClicked.connect(self.on_add_product)
        
        # Carrito
        self.btnAgregarProducto.clicked.connect(self.on_add_product)
        self.btnEliminarDelCarrito.clicked.connect(self.on_remove_from_cart)
        self.btnLimpiarCarrito.clicked.connect(self.on_clear_cart)
        self.tblCarrito.itemSelectionChanged.connect(self.on_cart_item_selected)
        
        # Cliente
        self.btnSeleccionarCliente.clicked.connect(self.on_select_customer)
        
        # Acciones principales
        self.btnProcesarVenta.clicked.connect(self.on_process_sale)
        self.btnGuardarCarrito.clicked.connect(self.on_save_cart)
        self.btnCargarCarrito.clicked.connect(self.on_load_cart)
        self.btnNuevaVenta.clicked.connect(self.on_new_sale)
        
        # Señales del modelo
        self.sales_model.data_changed.connect(self.update_totals)
        self.sales_model.cart_updated.connect(self.refresh_cart_table)
        self.sales_model.customer_changed.connect(self.on_customer_changed)
        self.sales_model.error_occurred.connect(self.on_model_error)
    
    def setup_shortcuts(self):
        """Configurar atajos de teclado específicos"""
        super().setup_shortcuts()  # Atajos base
        
        # Atajos específicos de ventas
        QShortcut(QKeySequence("F1"), self, self.lineEditBuscarProducto.setFocus)
        QShortcut(QKeySequence("F2"), self, self.on_add_product)
        QShortcut(QKeySequence("F3"), self, self.on_select_customer)
        QShortcut(QKeySequence("F4"), self, self.on_process_sale)
        QShortcut(QKeySequence("Ctrl+N"), self, self.on_new_sale)
        QShortcut(QKeySequence("Delete"), self, self.on_remove_from_cart)
        QShortcut(QKeySequence("Escape"), self, self.on_clear_search)
    
    def load_initial_data(self):
        """Cargar datos iniciales"""
        try:
            self.load_all_products()
            self.logger.info("Datos iniciales cargados para ventas")
        except Exception as e:
            self.logger.error(f"Error cargando datos iniciales: {e}")
            self.show_error("Error", f"Error cargando productos: {str(e)}")
    
    # === SLOTS DE INTERFAZ ===
    
    @pyqtSlot(str)
    def on_search_products(self, text: str):
        """Buscar productos en tiempo real"""
        try:
            text = text.strip().lower()
            
            if len(text) >= 2:  # Buscar solo si hay al menos 2 caracteres
                self.search_products(text)
            elif not text:  # Si está vacío, mostrar todos
                self.show_all_products()
                
        except Exception as e:
            self.logger.error(f"Error en búsqueda: {e}")
    
    @pyqtSlot()
    def on_search_enter_pressed(self):
        """Manejar Enter en búsqueda"""
        try:
            text = self.lineEditBuscarProducto.text().strip()
            if text:
                # Si hay productos en la tabla, agregar el primero
                if self.tblProductosDisponibles.rowCount() > 0:
                    self.tblProductosDisponibles.selectRow(0)
                    self.on_add_product()
        except Exception as e:
            self.logger.error(f"Error en search enter: {e}")
    
    @pyqtSlot()
    def on_search_clicked(self):
        """Botón de búsqueda clickeado"""
        text = self.lineEditBuscarProducto.text().strip()
        if text:
            self.search_products(text.lower())
        else:
            self.show_all_products()
    
    @pyqtSlot()
    def on_clear_search(self):
        """Limpiar búsqueda y mostrar todos los productos"""
        self.lineEditBuscarProducto.clear()
        self.show_all_products()
        self.lineEditBuscarProducto.setFocus()
    
    @pyqtSlot()
    def on_product_selected(self):
        """Producto seleccionado en tabla"""
        selected_rows = self.tblProductosDisponibles.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        self.btnAgregarProducto.setEnabled(has_selection)
    
    @pyqtSlot()
    def on_add_product(self):
        """Agregar producto seleccionado al carrito"""
        try:
            current_row = self.tblProductosDisponibles.currentRow()
            if current_row < 0:
                self.show_warning("Advertencia", "Por favor, seleccione un producto.")
                return
            
            # Obtener datos del producto desde la tabla
            product_data = self.get_product_from_table_row(current_row)
            if not product_data:
                self.show_error("Error", "No se pudieron obtener los datos del producto.")
                return
            
            # Validar stock disponible
            quantity = self.spinCantidadAgregar.value()
            available_stock = product_data.get('stock', 0)
            
            if quantity > available_stock:
                self.show_warning("Stock Insuficiente", 
                                f"Stock disponible: {available_stock}\nCantidad solicitada: {quantity}")
                return
            
            # Preparar item del carrito
            cart_item = {
                'code': product_data['code'],
                'name': product_data['name'],
                'price': product_data['price'],
                'quantity': quantity,
                'product_id': product_data.get('id'),
                'category': product_data.get('category', ''),
                'description': product_data.get('description', '')
            }
            
            # Agregar al modelo
            if self.sales_model.add_item_to_cart(cart_item):
                # Emitir señal
                self.product_added.emit(cart_item)
                
                # Limpiar búsqueda y resetear cantidad
                self.lineEditBuscarProducto.clear()
                self.spinCantidadAgregar.setValue(1)
                self.lineEditBuscarProducto.setFocus()
                
                # Mostrar todos los productos nuevamente
                self.show_all_products()
                
                self.logger.info(f"Producto agregado: {product_data['name']} x{quantity}")
            else:
                self.show_error("Error", "No se pudo agregar el producto al carrito.")
            
        except Exception as e:
            self.logger.error(f"Error agregando producto: {e}")
            self.show_error("Error", f"Error agregando producto: {str(e)}")
    
    def get_product_from_table_row(self, row: int) -> Optional[Dict]:
        """Obtener datos de producto desde fila de tabla"""
        try:
            if row < 0 or row >= self.tblProductosDisponibles.rowCount():
                return None
            
            # Obtener datos de las celdas
            code = self.tblProductosDisponibles.item(row, 0).text()
            name = self.tblProductosDisponibles.item(row, 1).text()
            category = self.tblProductosDisponibles.item(row, 2).text()
            price_text = self.tblProductosDisponibles.item(row, 3).text()
            stock_text = self.tblProductosDisponibles.item(row, 4).text()
            description = self.tblProductosDisponibles.item(row, 5).text()
            
            # Convertir tipos
            price = self.safe_float_conversion(price_text.replace('$', ''))
            stock = self.safe_int_conversion(stock_text)
            
            # Buscar product_id en la lista original
            product_id = None
            for product in self.available_products:
                if product.get('codigo') == code:
                    product_id = product.get('id')
                    break
            
            return {
                'id': product_id,
                'code': code,
                'name': name,
                'category': category,
                'price': price,
                'stock': stock,
                'description': description
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo datos de producto: {e}")
            return None
    
    @pyqtSlot()
    def on_remove_from_cart(self):
        """Eliminar producto seleccionado del carrito"""
        try:
            current_row = self.tblCarrito.currentRow()
            if current_row < 0:
                self.show_warning("Advertencia", "Por favor, seleccione un item del carrito.")
                return
            
            # Obtener nombre del producto para confirmación
            product_name = self.tblCarrito.item(current_row, 1).text()
            
            # Confirmar eliminación
            if self.show_question("Confirmar", f"¿Eliminar '{product_name}' del carrito?"):
                if self.sales_model.remove_item_from_cart(current_row):
                    self.logger.info(f"Producto eliminado del carrito: {product_name}")
                else:
                    self.show_error("Error", "No se pudo eliminar el producto del carrito.")
            
        except Exception as e:
            self.logger.error(f"Error eliminando producto del carrito: {e}")
            self.show_error("Error", f"Error eliminando producto: {str(e)}")
    
    @pyqtSlot()
    def on_clear_cart(self):
        """Limpiar carrito completo"""
        try:
            if not self.sales_model.has_items():
                self.show_info("Información", "El carrito ya está vacío.")
                return
            
            if self.show_question("Confirmar", "¿Está seguro que desea limpiar todo el carrito?"):
                self.sales_model.clear_cart()
                self.logger.info("Carrito limpiado")
        except Exception as e:
            self.logger.error(f"Error limpiando carrito: {e}")
            self.show_error("Error", f"Error limpiando carrito: {str(e)}")
    
    @pyqtSlot()
    def on_cart_item_selected(self):
        """Item del carrito seleccionado"""
        selected_rows = self.tblCarrito.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        self.btnEliminarDelCarrito.setEnabled(has_selection)
    
    @pyqtSlot()
    def on_select_customer(self):
        """Seleccionar cliente para la venta"""
        try:
            # Crear y mostrar diálogo de selección de clientes
            from ui.dialogs.customer_selector_dialog import CustomerSelectorDialog
            
            dialog = CustomerSelectorDialog(self.customer_manager, self)
            if dialog.exec_() == QDialog.Accepted:
                customer_data = dialog.get_selected_customer()
                if customer_data:
                    # Crear objeto Customer
                    customer = Customer.from_dict(customer_data)
                    self.sales_model.set_customer(customer)
                    
                    self.customer_selected.emit(customer_data)
                    self.logger.info(f"Cliente seleccionado: {customer.nombre}")
        
        except ImportError:
            # Si no existe el diálogo, crear uno simple
            self.create_simple_customer_dialog()
        except Exception as e:
            self.logger.error(f"Error seleccionando cliente: {e}")
            self.show_error("Error", f"Error seleccionando cliente: {str(e)}")
    
    def create_simple_customer_dialog(self):
        """Crear diálogo simple de selección de cliente"""
        try:
            customers = self.customer_manager.get_all_customers()
            
            customer_names = ["Cliente General"] + [f"{c.get('nombre', '')} ({c.get('codigo', '')})" for c in customers]
            
            customer_name, ok = QInputDialog.getItem(
                self, 
                "Seleccionar Cliente", 
                "Seleccione un cliente:",
                customer_names,
                0,
                False
            )
            
            if ok and customer_name != "Cliente General":
                # Buscar cliente seleccionado
                for customer_data in customers:
                    display_name = f"{customer_data.get('nombre', '')} ({customer_data.get('codigo', '')})"
                    if display_name == customer_name:
                        customer = Customer.from_dict(customer_data)
                        self.sales_model.set_customer(customer)
                        
                        self.customer_selected.emit(customer_data)
                        self.logger.info(f"Cliente seleccionado: {customer.nombre}")
                        break
            elif ok:  # Cliente General seleccionado
                self.sales_model.set_customer(None)
                
        except Exception as e:
            self.logger.error(f"Error en diálogo simple de cliente: {e}")
            self.show_error("Error", f"Error seleccionando cliente: {str(e)}")
    
    @pyqtSlot()
    def on_process_sale(self):
        """Procesar venta actual"""
        try:
            if not self.sales_model.has_items():
                self.show_warning("Carrito Vacío", "Agregue productos al carrito antes de procesar la venta.")
                return
            
            # Preparar datos de la venta
            sale_data = self.sales_model.prepare_sale_data()
            sale_data['cashier_id'] = self.current_user.get('id')
            
            # Mostrar diálogo de confirmación con resumen
            if self.confirm_sale_processing(sale_data):
                # Procesar venta
                sale_id = self.sales_manager.create_sale(sale_data)
                
                if sale_id:
                    self.show_info("Venta Procesada", 
                                 f"Venta #{sale_id} procesada exitosamente.")
                    
                    # Emitir señal
                    self.sale_completed.emit({
                        'sale_id': sale_id, 
                        'total': sale_data['total'],
                        'customer': sale_data.get('customer_name', 'Cliente General')
                    })
                    
                    # Preguntar si imprimir ticket
                    if self.show_question("Imprimir Ticket", "¿Desea imprimir el ticket de venta?"):
                        self.print_ticket(sale_id)
                    
                    # Limpiar para nueva venta
                    self.on_new_sale()
                    
                else:
                    self.show_error("Error", "Error procesando la venta. Intente nuevamente.")
        
        except Exception as e:
            self.logger.error(f"Error procesando venta: {e}")
            self.show_error("Error", f"Error procesando venta: {str(e)}")
    
    def confirm_sale_processing(self, sale_data: Dict) -> bool:
        """Confirmar procesamiento de venta con resumen"""
        try:
            # Crear diálogo de confirmación
            dialog = QDialog(self)
            dialog.setWindowTitle("Confirmar Venta")
            dialog.setModal(True)
            dialog.resize(400, 300)
            
            layout = QVBoxLayout(dialog)
            
            # Título
            title = QLabel("Confirmar Procesamiento de Venta")
            title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
            layout.addWidget(title)
            
            # Resumen
            summary = QTextEdit()
            summary.setReadOnly(True)
            summary.setMaximumHeight(150)
            
            summary_text = f"""
Cliente: {sale_data.get('customer_name', 'Cliente General')}
Items: {len(sale_data['items'])} productos
Subtotal: ${sale_data['subtotal']:,.2f}
Descuento: ${sale_data['discount_amount']:,.2f}
Impuestos: ${sale_data['tax_amount']:,.2f}
TOTAL: ${sale_data['total']:,.2f}
            """
            summary.setText(summary_text.strip())
            layout.addWidget(summary)
            
            # Botones
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            return dialog.exec_() == QDialog.Accepted
            
        except Exception as e:
            self.logger.error(f"Error en confirmación de venta: {e}")
            return self.show_question("Confirmar", "¿Procesar la venta?")
    
    @pyqtSlot()
    def on_save_cart(self):
        """Guardar carrito actual"""
        try:
            if not self.sales_model.has_items():
                self.show_info("Información", "El carrito está vacío.")
                return
            
            # Solicitar nombre para el carrito guardado
            cart_name, ok = QInputDialog.getText(
                self, 
                "Guardar Carrito",
                "Ingrese un nombre para el carrito:",
                text=f"Carrito_{datetime.now().strftime('%Y%m%d_%H%M')}"
            )
            
            if ok and cart_name:
                if self.sales_model.save_cart(cart_name):
                    self.show_info("Guardado", "Carrito guardado exitosamente.")
                else:
                    self.show_error("Error", "No se pudo guardar el carrito.")
            
        except Exception as e:
            self.logger.error(f"Error guardando carrito: {e}")
            self.show_error("Error", f"Error guardando carrito: {str(e)}")
    
    @pyqtSlot()
    def on_load_cart(self):
        """Cargar carrito guardado"""
        try:
            # Por ahora, mostrar mensaje de funcionalidad pendiente
            self.show_info("Información", "Funcionalidad de carga de carrito en desarrollo.")
            
        except Exception as e:
            self.logger.error(f"Error cargando carrito: {e}")
            self.show_error("Error", f"Error cargando carrito: {str(e)}")
    
    @pyqtSlot()
    def on_new_sale(self):
        """Iniciar nueva venta"""
        try:
            if self.sales_model.has_items():
                if not self.show_question("Confirmar", 
                                        "¿Está seguro que desea iniciar una nueva venta?\n"
                                        "Se perderán los datos del carrito actual."):
                    return
            
            # Limpiar modelo
            self.sales_model.reset_to_defaults()
            
            # Resetear interfaz
            self.reset_form()
            
            # Focus en búsqueda
            self.lineEditBuscarProducto.setFocus()
            
            self.logger.info("Nueva venta iniciada")
            
        except Exception as e:
            self.logger.error(f"Error iniciando nueva venta: {e}")
            self.show_error("Error", f"Error iniciando nueva venta: {str(e)}")
    
    # === SLOTS DE MODELO ===
    
    @pyqtSlot(dict)
    def on_customer_changed(self, customer_data: Dict):
        """Manejar cambio de cliente"""
        if customer_data:
            self.lblClienteNombre.setText(customer_data.get('nombre', 'Cliente'))
        else:
            self.lblClienteNombre.setText("Cliente General")
    
    @pyqtSlot(str)
    def on_model_error(self, error_message: str):
        """Manejar errores del modelo"""
        self.logger.error(f"Error del modelo: {error_message}")
        # No mostrar todos los errores del modelo para no ser invasivo
    
    # === MÉTODOS DE APOYO ===
    
    def load_all_products(self):
        """Cargar todos los productos disponibles"""
        try:
            if not self.product_manager:
                self.logger.warning("Product manager no disponible")
                return
            
            self.available_products = self.product_manager.get_all_products()
            self.filtered_products = self.available_products.copy()
            
            self.populate_products_table(self.available_products)
            
        except Exception as e:
            self.logger.error(f"Error cargando productos: {e}")
            raise
    
    def show_all_products(self):
        """Mostrar todos los productos disponibles"""
        self.filtered_products = self.available_products.copy()
        self.populate_products_table(self.filtered_products)
    
    def search_products(self, search_term: str):
        """Buscar productos por término"""
        try:
            search_term = search_term.lower()
            
            self.filtered_products = []
            for product in self.available_products:
                # Buscar en código, nombre y descripción
                if (search_term in product.get('codigo', '').lower() or
                    search_term in product.get('nombre', '').lower() or
                    search_term in product.get('descripcion', '').lower() or
                    search_term in product.get('categoria', '').lower()):
                    
                    self.filtered_products.append(product)
            
            self.populate_products_table(self.filtered_products)
            
        except Exception as e:
            self.logger.error(f"Error buscando productos: {e}")
    
    def populate_products_table(self, products: List[Dict]):
        """Poblar tabla de productos"""
        try:
            self.tblProductosDisponibles.setRowCount(len(products))
            
            for row, product in enumerate(products):
                # Código
                self.tblProductosDisponibles.setItem(row, 0, QTableWidgetItem(product.get('codigo', '')))
                
                # Nombre
                self.tblProductosDisponibles.setItem(row, 1, QTableWidgetItem(product.get('nombre', '')))
                
                # Categoría
                self.tblProductosDisponibles.setItem(row, 2, QTableWidgetItem(product.get('categoria', '')))
                
                # Precio
                precio = self.safe_float_conversion(product.get('precio', 0))
                self.tblProductosDisponibles.setItem(row, 3, QTableWidgetItem(self.format_currency(precio)))
                
                # Stock
                stock = self.safe_int_conversion(product.get('stock_actual', 0))
                stock_item = QTableWidgetItem(str(stock))
                
                # Colorear según stock
                if stock <= 0:
                    stock_item.setBackground(QColor(255, 200, 200))  # Rojo claro
                elif stock <= product.get('stock_minimo', 0):
                    stock_item.setBackground(QColor(255, 255, 200))  # Amarillo claro
                
                self.tblProductosDisponibles.setItem(row, 4, stock_item)
                
                # Descripción
                self.tblProductosDisponibles.setItem(row, 5, QTableWidgetItem(product.get('descripcion', '')))
            
            # Ajustar columnas
            self.tblProductosDisponibles.resizeColumnsToContents()
            
        except Exception as e:
            self.logger.error(f"Error poblando tabla de productos: {e}")
    
    @pyqtSlot()
    def refresh_cart_table(self):
        """Actualizar tabla del carrito"""
        try:
            cart_items = self.sales_model.get_cart_items()
            self.tblCarrito.setRowCount(len(cart_items))
            
            for row, item in enumerate(cart_items):
                # Código
                self.tblCarrito.setItem(row, 0, QTableWidgetItem(str(item.get('code', ''))))
                
                # Nombre
                self.tblCarrito.setItem(row, 1, QTableWidgetItem(str(item.get('name', ''))))
                
                # Cantidad
                self.tblCarrito.setItem(row, 2, QTableWidgetItem(str(item.get('quantity', 0))))
                
                # Precio unitario
                price = float(item.get('price', 0))
                self.tblCarrito.setItem(row, 3, QTableWidgetItem(self.format_currency(price)))
                
                # Subtotal
                subtotal = float(item.get('subtotal', 0))
                self.tblCarrito.setItem(row, 4, QTableWidgetItem(self.format_currency(subtotal)))
                
                # Botón de eliminar
                btn_delete = QPushButton("🗑")
                btn_delete.setToolTip("Eliminar del carrito")
                btn_delete.setMaximumSize(30, 30)
                btn_delete.clicked.connect(lambda checked, r=row: self.remove_cart_item(r))
                self.tblCarrito.setCellWidget(row, 5, btn_delete)
            
        except Exception as e:
            self.logger.error(f"Error actualizando tabla del carrito: {e}")
    
    @pyqtSlot()
    def update_totals(self):
        """Actualizar displays de totales"""
        try:
            subtotal = self.sales_model.get_subtotal()
            discount = self.sales_model.get_discount_amount()
            tax = self.sales_model.get_tax_amount()
            total = self.sales_model.get_total()
            
            self.lblSubtotalValor.setText(self.format_currency(subtotal))
            self.lblDescuentoValor.setText(self.format_currency(discount))
            self.lblImpuestosValor.setText(self.format_currency(tax))
            self.lblTotalValor.setText(self.format_currency(total))
            
            # Habilitar/deshabilitar botón de procesar venta
            self.btnProcesarVenta.setEnabled(total > 0)
            
        except Exception as e:
            self.logger.error(f"Error actualizando totales: {e}")
    
    def reset_form(self):
        """Resetear formulario a estado inicial"""
        self.lblClienteNombre.setText("Cliente General")
        self.lineEditBuscarProducto.clear()
        self.spinCantidadAgregar.setValue(1)
        self.btnAgregarProducto.setEnabled(False)
        self.btnEliminarDelCarrito.setEnabled(False)
        self.btnProcesarVenta.setEnabled(False)
        
        # Limpiar tablas
        self.tblCarrito.setRowCount(0)
        
        # Actualizar totales
        self.update_totals()
    
    def remove_cart_item(self, row: int):
        """Eliminar item específico del carrito por fila"""
        try:
            if self.sales_model.remove_item_from_cart(row):
                self.logger.debug(f"Item eliminado del carrito en fila {row}")
        except Exception as e:
            self.logger.error(f"Error eliminando item del carrito: {e}")
    
    def print_ticket(self, sale_id: int):
        """Imprimir ticket de venta"""
        try:
            # Implementar impresión de ticket
            self.show_info("Impresión", f"Imprimiendo ticket de venta #{sale_id}...")
            
            # Aquí iría la lógica real de impresión
            # from utils.ticket_printer import TicketPrinter
            # printer = TicketPrinter()
            # sale_data = self.sales_manager.get_sale_details(sale_id)
            # printer.print_sale_ticket(sale_data)
            
        except Exception as e:
            self.logger.error(f"Error imprimiendo ticket: {e}")
            self.show_warning("Error de Impresión", 
                            f"No se pudo imprimir el ticket: {str(e)}")
    
    # === OVERRIDES ===
    
    @pyqtSlot()
    def on_save_shortcut(self):
        """Override del shortcut Ctrl+S"""
        self.on_save_cart()
    
    def save_state(self) -> Dict[str, Any]:
        """Guardar estado del controlador"""
        state = super().save_state()
        state.update({
            'search_text': self.lineEditBuscarProducto.text(),
            'quantity': self.spinCantidadAgregar.value(),
            'has_cart_items': self.sales_model.has_items()
        })
        return state
    
    def restore_state(self, state: Dict[str, Any]):
        """Restaurar estado del controlador"""
        super().restore_state(state)
        
        if 'search_text' in state:
            self.lineEditBuscarProducto.setText(state['search_text'])
        
        if 'quantity' in state:
            self.spinCantidadAgregar.setValue(state['quantity'])