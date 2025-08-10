"""
Diálogo para gestionar pagos de deudas de clientes
"""

import logging
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

logger = logging.getLogger(__name__)

class PaymentDebtDialog(QDialog):
    """Diálogo para procesar pagos de deudas de clientes"""
    
    def __init__(self, customer_manager, sales_manager, current_user, parent=None):
        super().__init__(parent)
        self.customer_manager = customer_manager
        self.sales_manager = sales_manager
        self.current_user = current_user
        self.selected_customer = None
        
        self.setWindowTitle("Gestión de Cuentas Corrientes")
        self.setModal(True)
        self.resize(900, 700)
        
        self.init_ui()
        self.load_customers_with_debt()
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Gestión de Cuentas Corrientes - Pagos de Deudas")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; padding: 10px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Panel superior con clientes
        customers_group = QGroupBox("Clientes con Saldo Pendiente")
        customers_layout = QVBoxLayout(customers_group)
        
        # Búsqueda de clientes
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Buscar cliente:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nombre, apellido o documento...")
        self.search_input.textChanged.connect(self.filter_customers)
        search_layout.addWidget(self.search_input)
        
        customers_layout.addLayout(search_layout)
        
        # Tabla de clientes con deudas
        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(6)
        self.customers_table.setHorizontalHeaderLabels([
            "ID", "Cliente", "Documento", "Teléfono", "Saldo Deudor", "Días Vencido"
        ])
        
        # Configurar tabla
        self.customers_table.setAlternatingRowColors(True)
        self.customers_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.customers_table.setSelectionMode(QAbstractItemView.SingleSelection)
        
        # Ajustar columnas
        header = self.customers_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Cliente
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Saldo
        
        self.customers_table.selectionModel().selectionChanged.connect(self.on_customer_selected)
        
        customers_layout.addWidget(self.customers_table)
        layout.addWidget(customers_group)
        
        # Panel inferior con detalles y pago
        details_layout = QHBoxLayout()
        
        # Panel izquierdo - Información del cliente
        info_group = QGroupBox("Información del Cliente")
        info_layout = QVBoxLayout(info_group)
        
        self.customer_info = QLabel("Seleccione un cliente para ver su información")
        self.customer_info.setWordWrap(True)
        self.customer_info.setStyleSheet("padding: 10px; background: #f8f9fa; border-radius: 5px;")
        info_layout.addWidget(self.customer_info)
        
        # Historial de movimientos
        self.movements_table = QTableWidget()
        self.movements_table.setColumnCount(4)
        self.movements_table.setHorizontalHeaderLabels([
            "Fecha", "Concepto", "Tipo", "Importe"
        ])
        self.movements_table.setMaximumHeight(200)
        info_layout.addWidget(QLabel("Movimientos Recientes:"))
        info_layout.addWidget(self.movements_table)
        
        details_layout.addWidget(info_group)
        
        # Panel derecho - Procesar pago
        payment_group = QGroupBox("Procesar Pago")
        payment_layout = QFormLayout(payment_group)
        
        self.debt_amount_label = QLabel("$0.00")
        self.debt_amount_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #e74c3c;")
        payment_layout.addRow("Deuda Total:", self.debt_amount_label)
        
        self.payment_amount = QDoubleSpinBox()
        self.payment_amount.setMaximum(999999.99)
        self.payment_amount.setDecimals(2)
        self.payment_amount.setMinimum(0.01)
        payment_layout.addRow("Monto a Pagar:", self.payment_amount)
        
        self.payment_method = QComboBox()
        self.payment_method.addItems([
            "EFECTIVO", "TARJETA_DEBITO", "TARJETA_CREDITO", "TRANSFERENCIA"
        ])
        payment_layout.addRow("Método de Pago:", self.payment_method)
        
        self.payment_reference = QLineEdit()
        self.payment_reference.setPlaceholderText("Número de comprobante (opcional)")
        payment_layout.addRow("Referencia:", self.payment_reference)
        
        self.payment_notes = QTextEdit()
        self.payment_notes.setMaximumHeight(60)
        self.payment_notes.setPlaceholderText("Observaciones del pago...")
        payment_layout.addRow("Observaciones:", self.payment_notes)
        
        # Botón de pago
        self.pay_button = QPushButton("💰 Procesar Pago")
        self.pay_button.setEnabled(False)
        self.pay_button.setMinimumHeight(40)
        self.pay_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.pay_button.clicked.connect(self.process_payment)
        payment_layout.addRow("", self.pay_button)
        
        details_layout.addWidget(payment_group)
        layout.addLayout(details_layout)
        
        # Botones de cierre
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.close)
        layout.addWidget(buttons)
    
    def load_customers_with_debt(self):
        """Cargar clientes que tienen deudas"""
        try:
            customers = self.customer_manager.get_all_customers()
            customers_with_debt = []
            
            for customer in customers:
                saldo = float(customer.get('saldo_cuenta_corriente', 0))
                if saldo > 0:  # Solo clientes con deuda
                    customers_with_debt.append(customer)
            
            self.customers_table.setRowCount(len(customers_with_debt))
            
            for row, customer in enumerate(customers_with_debt):
                # ID
                id_item = QTableWidgetItem(str(customer.get('id', '')))
                id_item.setData(Qt.UserRole, customer)
                self.customers_table.setItem(row, 0, id_item)
                
                # Cliente
                nombre_completo = f"{customer.get('nombre', '')} {customer.get('apellido', '')}"
                self.customers_table.setItem(row, 1, QTableWidgetItem(nombre_completo))
                
                # Documento
                self.customers_table.setItem(row, 2, QTableWidgetItem(customer.get('dni_cuit', '')))
                
                # Teléfono
                self.customers_table.setItem(row, 3, QTableWidgetItem(customer.get('telefono', '')))
                
                # Saldo deudor
                saldo = float(customer.get('saldo_cuenta_corriente', 0))
                saldo_item = QTableWidgetItem(f"${saldo:,.2f}")
                saldo_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                saldo_item.setBackground(QColor(255, 200, 200))  # Fondo rojo claro
                self.customers_table.setItem(row, 4, saldo_item)
                
                # Días vencido (placeholder)
                dias_item = QTableWidgetItem("15")  # TODO: Calcular días reales
                dias_item.setTextAlignment(Qt.AlignCenter)
                self.customers_table.setItem(row, 5, dias_item)
            
            # Ajustar tamaño de filas
            self.customers_table.resizeRowsToContents()
            
        except Exception as e:
            logger.error(f"Error cargando clientes con deudas: {e}")
            QMessageBox.warning(self, "Error", f"Error cargando clientes: {e}")
    
    def filter_customers(self, text):
        """Filtrar clientes por texto de búsqueda"""
        for row in range(self.customers_table.rowCount()):
            show_row = False
            
            if not text:  # Si no hay texto, mostrar todo
                show_row = True
            else:
                # Buscar en cliente y documento
                for col in [1, 2]:  # Cliente, Documento
                    item = self.customers_table.item(row, col)
                    if item and text.lower() in item.text().lower():
                        show_row = True
                        break
            
            self.customers_table.setRowHidden(row, not show_row)
    
    def on_customer_selected(self):
        """Manejar selección de cliente"""
        selected_items = self.customers_table.selectedItems()
        
        if selected_items:
            row = selected_items[0].row()
            customer_data = self.customers_table.item(row, 0).data(Qt.UserRole)
            
            if customer_data:
                self.selected_customer = customer_data
                self.load_customer_info()
                self.load_customer_movements()
                
                # Habilitar pago
                deuda = float(customer_data.get('saldo_cuenta_corriente', 0))
                if deuda > 0:
                    self.payment_amount.setMaximum(deuda)
                    self.payment_amount.setValue(deuda)  # Proponer pago completo
                    self.pay_button.setEnabled(True)
                else:
                    self.pay_button.setEnabled(False)
            else:
                self.selected_customer = None
                self.pay_button.setEnabled(False)
        else:
            self.selected_customer = None
            self.pay_button.setEnabled(False)
            self.customer_info.setText("Seleccione un cliente para ver su información")
    
    def load_customer_info(self):
        """Cargar información del cliente seleccionado"""
        if not self.selected_customer:
            return
        
        customer = self.selected_customer
        saldo = float(customer.get('saldo_cuenta_corriente', 0))
        limite = float(customer.get('limite_credito', 0))
        
        info_html = f"""
        <h3>{customer.get('nombre', '')} {customer.get('apellido', '')}</h3>
        <b>Documento:</b> {customer.get('dni_cuit', '')}<br>
        <b>Teléfono:</b> {customer.get('telefono', '')}<br>
        <b>Email:</b> {customer.get('email', '')}<br>
        <b>Dirección:</b> {customer.get('direccion', '')}<br>
        <b>Categoría:</b> {customer.get('categoria_cliente', '')}<br><br>
        
        <b>Límite de Crédito:</b> ${limite:,.2f}<br>
        """
        
        if saldo > 0:
            info_html += f'<b>Saldo Deudor:</b> <font color="red">${saldo:,.2f}</font><br>'
            credito_disponible = max(0, limite - saldo)
            info_html += f'<b>Crédito Disponible:</b> ${credito_disponible:,.2f}'
        else:
            info_html += f'<b>Saldo:</b> <font color="green">$0.00</font><br>'
            info_html += f'<b>Crédito Disponible:</b> ${limite:,.2f}'
        
        self.customer_info.setText(info_html)
        self.debt_amount_label.setText(f"${saldo:,.2f}")
    
    def load_customer_movements(self):
        """Cargar movimientos recientes del cliente"""
        if not self.selected_customer:
            return
        
        try:
            # Consultar movimientos de cuenta corriente
            movements = self.customer_manager.db.execute_query("""
                SELECT fecha_movimiento, concepto, tipo_movimiento, importe
                FROM cuenta_corriente
                WHERE cliente_id = ?
                ORDER BY fecha_movimiento DESC
                LIMIT 10
            """, (self.selected_customer['id'],))
            
            self.movements_table.setRowCount(len(movements))
            
            for row, movement in enumerate(movements):
                mov_dict = dict(movement)
                
                # Fecha
                fecha = mov_dict.get('fecha_movimiento', '')
                if isinstance(fecha, str):
                    try:
                        fecha_dt = datetime.fromisoformat(fecha.replace('Z', '+00:00'))
                        fecha_str = fecha_dt.strftime('%d/%m/%Y %H:%M')
                    except:
                        fecha_str = fecha
                else:
                    fecha_str = str(fecha)
                
                self.movements_table.setItem(row, 0, QTableWidgetItem(fecha_str))
                
                # Concepto
                self.movements_table.setItem(row, 1, QTableWidgetItem(mov_dict.get('concepto', '')))
                
                # Tipo
                tipo = mov_dict.get('tipo_movimiento', '')
                tipo_item = QTableWidgetItem(tipo)
                if tipo == 'DEBE':
                    tipo_item.setBackground(QColor(255, 200, 200))
                else:
                    tipo_item.setBackground(QColor(200, 255, 200))
                self.movements_table.setItem(row, 2, tipo_item)
                
                # Importe
                importe = float(mov_dict.get('importe', 0))
                importe_item = QTableWidgetItem(f"${importe:,.2f}")
                importe_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.movements_table.setItem(row, 3, importe_item)
            
            # Ajustar columnas
            self.movements_table.resizeColumnsToContents()
            
        except Exception as e:
            logger.error(f"Error cargando movimientos: {e}")
    
    def process_payment(self):
        """Procesar pago de deuda"""
        if not self.selected_customer:
            QMessageBox.warning(self, "Error", "Debe seleccionar un cliente")
            return
        
        amount = self.payment_amount.value()
        if amount <= 0:
            QMessageBox.warning(self, "Error", "El monto debe ser mayor a cero")
            return
        
        deuda_actual = float(self.selected_customer.get('saldo_cuenta_corriente', 0))
        if amount > deuda_actual:
            QMessageBox.warning(
                self, 
                "Error", 
                f"El monto no puede ser mayor a la deuda actual (${deuda_actual:,.2f})"
            )
            return
        
        # Confirmar pago
        reply = QMessageBox.question(
            self,
            "Confirmar Pago",
            f"¿Confirma el pago de ${amount:,.2f} para el cliente "
            f"{self.selected_customer.get('nombre', '')} {self.selected_customer.get('apellido', '')}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Procesar pago usando el SalesManager
                success = self.sales_manager.update_customer_account(
                    customer_id=self.selected_customer['id'],
                    amount=amount,
                    movement_type='HABER',  # HABER reduce la deuda
                    sale_id=None,  # No está asociado a una venta
                    user_id=self.current_user['id'],
                    notes=f"Pago por {self.payment_method.currentText()}: {self.payment_notes.toPlainText()}"
                )
                
                if success:
                    # Actualizar saldo del cliente en la BD
                    self.customer_manager.db.execute_update("""
                        UPDATE clientes 
                        SET saldo_cuenta_corriente = saldo_cuenta_corriente - ?
                        WHERE id = ?
                    """, (amount, self.selected_customer['id']))
                    
                    QMessageBox.information(
                        self,
                        "Pago Procesado",
                        f"Pago de ${amount:,.2f} procesado exitosamente.\n"
                        f"Nuevo saldo: ${deuda_actual - amount:,.2f}"
                    )
                    
                    # Recargar datos
                    self.load_customers_with_debt()
                    
                    # Limpiar formulario
                    self.payment_amount.setValue(0)
                    self.payment_reference.clear()
                    self.payment_notes.clear()
                    
                else:
                    QMessageBox.warning(self, "Error", "Error procesando el pago")
                    
            except Exception as e:
                logger.error(f"Error procesando pago: {e}")
                QMessageBox.critical(self, "Error", f"Error procesando pago: {e}")