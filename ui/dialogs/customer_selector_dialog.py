"""
Diálogo para seleccionar clientes con información de cuenta corriente
"""

import logging
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

logger = logging.getLogger(__name__)

class CustomerSelectorDialog(QDialog):
    """Diálogo para seleccionar cliente con información de cuenta corriente"""
    
    def __init__(self, customer_manager, parent=None):
        super().__init__(parent)
        self.customer_manager = customer_manager
        self.selected_customer = None
        
        self.setWindowTitle("Seleccionar Cliente")
        self.setModal(True)
        self.resize(800, 600)
        
        self.init_ui()
        self.load_customers()
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        layout = QVBoxLayout(self)
        
        # Búsqueda
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Buscar cliente:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nombre, apellido o documento...")
        self.search_input.textChanged.connect(self.filter_customers)
        search_layout.addWidget(self.search_input)
        
        layout.addLayout(search_layout)
        
        # Tabla de clientes
        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(8)
        self.customers_table.setHorizontalHeaderLabels([
            "ID", "Nombre", "Apellido", "Documento", "Teléfono", 
            "Categoría", "Límite Crédito", "Saldo Actual"
        ])
        
        # Configurar tabla
        self.customers_table.setAlternatingRowColors(True)
        self.customers_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.customers_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.customers_table.setSortingEnabled(True)
        
        # Ajustar columnas
        header = self.customers_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Nombre
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Apellido
        
        self.customers_table.doubleClicked.connect(self.accept)
        
        layout.addWidget(self.customers_table)
        
        # Panel de información del cliente seleccionado
        info_group = QGroupBox("Información del Cliente")
        info_layout = QFormLayout(info_group)
        
        self.customer_info = QLabel("Seleccione un cliente para ver su información")
        self.customer_info.setWordWrap(True)
        self.customer_info.setStyleSheet("padding: 10px; background: #f0f0f0; border-radius: 5px;")
        info_layout.addRow(self.customer_info)
        
        layout.addWidget(info_group)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        # Botón para cliente sin registrar
        guest_btn = QPushButton("Cliente General (Sin registro)")
        guest_btn.clicked.connect(self.select_guest_customer)
        buttons_layout.addWidget(guest_btn)
        
        buttons_layout.addStretch()
        
        # Botones estándar
        self.select_btn = QPushButton("Seleccionar Cliente")
        self.select_btn.setEnabled(False)
        self.select_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(self.select_btn)
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        # Conectar selección de tabla
        self.customers_table.selectionModel().selectionChanged.connect(self.on_customer_selected)
    
    def load_customers(self):
        """Cargar lista de clientes"""
        try:
            customers = self.customer_manager.get_all_customers()
            
            self.customers_table.setRowCount(len(customers))
            
            for row, customer in enumerate(customers):
                # ID
                self.customers_table.setItem(row, 0, QTableWidgetItem(str(customer.get('id', ''))))
                
                # Nombre
                self.customers_table.setItem(row, 1, QTableWidgetItem(customer.get('nombre', '')))
                
                # Apellido  
                self.customers_table.setItem(row, 2, QTableWidgetItem(customer.get('apellido', '')))
                
                # Documento
                self.customers_table.setItem(row, 3, QTableWidgetItem(customer.get('dni_cuit', '')))
                
                # Teléfono
                self.customers_table.setItem(row, 4, QTableWidgetItem(customer.get('telefono', '')))
                
                # Categoría
                self.customers_table.setItem(row, 5, QTableWidgetItem(customer.get('categoria_cliente', '')))
                
                # Límite crédito
                limite = float(customer.get('limite_credito', 0))
                limite_item = QTableWidgetItem(f"${limite:,.2f}")
                limite_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.customers_table.setItem(row, 6, limite_item)
                
                # Saldo actual
                saldo = float(customer.get('saldo_cuenta_corriente', 0))
                saldo_item = QTableWidgetItem(f"${saldo:,.2f}")
                saldo_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
                # Color según saldo
                if saldo > 0:
                    saldo_item.setBackground(QColor(255, 200, 200))  # Rojo claro para deuda
                elif saldo < 0:
                    saldo_item.setBackground(QColor(200, 255, 200))  # Verde claro para saldo a favor
                
                self.customers_table.setItem(row, 7, saldo_item)
                
                # Guardar datos completos del cliente en la primera celda
                id_item = self.customers_table.item(row, 0)
                id_item.setData(Qt.UserRole, customer)
            
            # Ajustar tamaño de filas
            self.customers_table.resizeRowsToContents()
            
        except Exception as e:
            logger.error(f"Error cargando clientes: {e}")
            QMessageBox.warning(self, "Error", f"Error cargando clientes: {e}")
    
    def filter_customers(self, text):
        """Filtrar clientes por texto de búsqueda"""
        for row in range(self.customers_table.rowCount()):
            show_row = False
            
            if not text:  # Si no hay texto, mostrar todo
                show_row = True
            else:
                # Buscar en nombre, apellido y documento
                for col in [1, 2, 3]:  # Nombre, Apellido, Documento
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
                self.select_btn.setEnabled(True)
                
                # Mostrar información del cliente
                info_html = f"""
                <b>{customer_data.get('nombre', '')} {customer_data.get('apellido', '')}</b><br>
                <b>Documento:</b> {customer_data.get('dni_cuit', '')}<br>
                <b>Teléfono:</b> {customer_data.get('telefono', '')}<br>
                <b>Email:</b> {customer_data.get('email', '')}<br>
                <b>Dirección:</b> {customer_data.get('direccion', '')}<br>
                <b>Categoría:</b> {customer_data.get('categoria_cliente', '')}<br>
                <b>Límite de Crédito:</b> ${float(customer_data.get('limite_credito', 0)):,.2f}<br>
                <b>Saldo Actual:</b> ${float(customer_data.get('saldo_cuenta_corriente', 0)):,.2f}
                """
                
                saldo = float(customer_data.get('saldo_cuenta_corriente', 0))
                if saldo > 0:
                    info_html += f"<br><font color='red'><b>DEBE: ${saldo:,.2f}</b></font>"
                elif saldo < 0:
                    info_html += f"<br><font color='green'><b>SALDO A FAVOR: ${abs(saldo):,.2f}</b></font>"
                
                self.customer_info.setText(info_html)
            else:
                self.selected_customer = None
                self.select_btn.setEnabled(False)
                self.customer_info.setText("Error obteniendo datos del cliente")
        else:
            self.selected_customer = None
            self.select_btn.setEnabled(False)
            self.customer_info.setText("Seleccione un cliente para ver su información")
    
    def select_guest_customer(self):
        """Seleccionar cliente general (sin registro)"""
        self.selected_customer = {
            'id': None,
            'nombre': 'Cliente',
            'apellido': 'General',
            'dni_cuit': '',
            'limite_credito': 0,
            'saldo_cuenta_corriente': 0,
            'categoria_cliente': 'GENERAL'
        }
        self.accept()
    
    def get_selected_customer(self):
        """Obtener cliente seleccionado"""
        return self.selected_customer