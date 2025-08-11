"""
Diálogo de Gestión de Clientes - AlmacénPro v2.0
Interface completa para gestión de clientes y CRM
"""

import logging
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class CustomerDialog(QDialog):
    """Diálogo para crear/editar clientes"""
    
    customer_saved = pyqtSignal(dict)  # Señal emitida al guardar cliente
    
    def __init__(self, managers: dict, customer_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        
        self.managers = managers
        self.customer_id = customer_id
        self.customer_data = {}
        
        self.setWindowTitle("Nuevo Cliente" if customer_id is None else "Editar Cliente")
        self.setModal(True)
        self.resize(600, 500)
        
        self.init_ui()
        self.load_data()
        
        if customer_id:
            self.load_customer_data()
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        icon_label = QLabel("👤")
        icon_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon_label)
        
        title = QLabel("Gestión de Cliente")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Tabs para organizar información
        tabs = QTabWidget()
        
        # Tab 1: Información General
        general_tab = self.create_general_tab()
        tabs.addTab(general_tab, "📋 General")
        
        # Tab 2: Información Comercial
        commercial_tab = self.create_commercial_tab()
        tabs.addTab(commercial_tab, "💼 Comercial")
        
        # Tab 3: Direcciones y Contactos
        contact_tab = self.create_contact_tab()
        tabs.addTab(contact_tab, "📞 Contacto")
        
        layout.addWidget(tabs)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 Guardar")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        save_btn.clicked.connect(self.save_customer)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
    
    def create_general_tab(self) -> QWidget:
        """Crear tab de información general"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Tipo de cliente
        self.customer_type = QComboBox()
        self.customer_type.addItems(["Persona Física", "Empresa"])
        self.customer_type.currentTextChanged.connect(self.on_customer_type_changed)
        layout.addRow("Tipo de Cliente:", self.customer_type)
        
        # Nombre/Razón Social
        self.name_input = QLineEdit()
        self.name_input.setMaxLength(100)
        layout.addRow("Nombre:", self.name_input)
        
        self.business_name_input = QLineEdit()
        self.business_name_input.setMaxLength(100)
        layout.addRow("Razón Social:", self.business_name_input)
        
        # Documento
        doc_layout = QHBoxLayout()
        
        self.document_type = QComboBox()
        self.document_type.addItems(["DNI", "CUIT", "CUIL", "PASAPORTE", "OTRO"])
        doc_layout.addWidget(self.document_type, 1)
        
        self.document_number = QLineEdit()
        self.document_number.setMaxLength(20)
        self.document_number.setPlaceholderText("Número de documento")
        doc_layout.addWidget(self.document_number, 2)
        
        layout.addRow("Documento:", doc_layout)
        
        # Categoría de cliente
        self.category_combo = QComboBox()
        self.category_combo.addItem("Sin categoría", None)
        layout.addRow("Categoría:", self.category_combo)
        
        # Condición fiscal
        self.tax_condition = QComboBox()
        self.tax_condition.addItems([
            "CONSUMIDOR_FINAL",
            "RESPONSABLE_INSCRIPTO", 
            "MONOTRIBUTISTA",
            "EXENTO"
        ])
        layout.addRow("Condición Fiscal:", self.tax_condition)
        
        # Notas
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(100)
        self.notes_input.setPlaceholderText("Notas adicionales sobre el cliente...")
        layout.addRow("Notas:", self.notes_input)
        
        return widget
    
    def create_commercial_tab(self) -> QWidget:
        """Crear tab de información comercial"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Límite de crédito
        self.credit_limit = QDoubleSpinBox()
        self.credit_limit.setRange(0, 999999.99)
        self.credit_limit.setDecimals(2)
        self.credit_limit.setSuffix(" $")
        layout.addRow("Límite de Crédito:", self.credit_limit)
        
        # Términos de pago
        self.payment_terms = QSpinBox()
        self.payment_terms.setRange(0, 365)
        self.payment_terms.setSuffix(" días")
        layout.addRow("Términos de Pago:", self.payment_terms)
        
        # Descuento
        self.discount_percentage = QDoubleSpinBox()
        self.discount_percentage.setRange(0, 100)
        self.discount_percentage.setDecimals(2)
        self.discount_percentage.setSuffix(" %")
        layout.addRow("Descuento (%):", self.discount_percentage)
        
        # Lista de precios
        self.price_list = QComboBox()
        self.price_list.addItem("Lista General", None)
        layout.addRow("Lista de Precios:", self.price_list)
        
        # Información adicional
        info_group = QGroupBox("Información Comercial")
        info_layout = QVBoxLayout(info_group)
        
        # Estado del cliente (solo para edición)
        if self.customer_id:
            self.customer_stats = QLabel("Cargando estadísticas...")
            info_layout.addWidget(self.customer_stats)
        
        layout.addRow(info_group)
        
        return widget
    
    def create_contact_tab(self) -> QWidget:
        """Crear tab de contacto y dirección"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Teléfonos
        phone_group = QGroupBox("Teléfonos")
        phone_layout = QFormLayout(phone_group)
        
        self.phone_input = QLineEdit()
        self.phone_input.setMaxLength(20)
        self.phone_input.setPlaceholderText("(011) 4444-5555")
        phone_layout.addRow("Teléfono:", self.phone_input)
        
        self.mobile_input = QLineEdit()
        self.mobile_input.setMaxLength(20)
        self.mobile_input.setPlaceholderText("(011) 15-6666-7777")
        phone_layout.addRow("Celular:", self.mobile_input)
        
        layout.addRow(phone_group)
        
        # Email
        self.email_input = QLineEdit()
        self.email_input.setMaxLength(100)
        self.email_input.setPlaceholderText("cliente@email.com")
        layout.addRow("Email:", self.email_input)
        
        # Dirección
        address_group = QGroupBox("Dirección")
        address_layout = QFormLayout(address_group)
        
        self.address_input = QLineEdit()
        self.address_input.setMaxLength(200)
        self.address_input.setPlaceholderText("Calle 123, Ciudad")
        address_layout.addRow("Dirección:", self.address_input)
        
        location_layout = QHBoxLayout()
        
        self.city_input = QLineEdit()
        self.city_input.setMaxLength(50)
        self.city_input.setPlaceholderText("Ciudad")
        location_layout.addWidget(self.city_input, 2)
        
        self.postal_code_input = QLineEdit()
        self.postal_code_input.setMaxLength(10)
        self.postal_code_input.setPlaceholderText("CP")
        location_layout.addWidget(self.postal_code_input, 1)
        
        address_layout.addRow("Ciudad / CP:", location_layout)
        
        layout.addRow(address_group)
        
        return widget
    
    def load_data(self):
        """Cargar datos de combos"""
        try:
            # Cargar categorías de clientes predefinidas
            categories = [
                ('VIP', 'VIP'),
                ('MAYORISTA', 'MAYORISTA'), 
                ('MINORISTA', 'MINORISTA'),
                ('CORPORATIVO', 'CORPORATIVO'),
                ('DISTRIBUIDOR', 'DISTRIBUIDOR'),
                ('OCASIONAL', 'OCASIONAL'),
                ('GENERAL', 'GENERAL')
            ]
            
            for category_name, category_value in categories:
                self.category_combo.addItem(category_name, category_value)
            
        except Exception as e:
            logger.error(f"Error cargando datos: {e}")
    
    def load_customer_data(self):
        """Cargar datos del cliente para edición"""
        try:
            if not self.customer_id or 'customer' not in self.managers:
                return
            
            customer = self.managers['customer'].get_customer_by_id(self.customer_id)
            if not customer:
                QMessageBox.warning(self, "Error", "Cliente no encontrado")
                self.reject()
                return
            
            self.customer_data = customer
            
            # Llenar campos
            self.name_input.setText(customer.get('name', ''))
            self.business_name_input.setText(customer.get('business_name', ''))
            
            # Tipo de cliente
            if customer.get('business_name'):
                self.customer_type.setCurrentText("Empresa")
            else:
                self.customer_type.setCurrentText("Persona Física")
            
            # Documento
            if customer.get('document_type'):
                self.document_type.setCurrentText(customer['document_type'])
            self.document_number.setText(customer.get('document_number', ''))
            
            # Categoría
            if customer.get('category_id'):
                for i in range(self.category_combo.count()):
                    if self.category_combo.itemData(i) == customer['category_id']:
                        self.category_combo.setCurrentIndex(i)
                        break
            
            # Condición fiscal
            if customer.get('tax_condition'):
                self.tax_condition.setCurrentText(customer['tax_condition'])
            
            # Información comercial
            self.credit_limit.setValue(customer.get('credit_limit', 0))
            self.payment_terms.setValue(customer.get('payment_terms', 0))
            self.discount_percentage.setValue(customer.get('discount_percentage', 0))
            
            # Contacto
            self.phone_input.setText(customer.get('phone', ''))
            self.mobile_input.setText(customer.get('mobile', ''))
            self.email_input.setText(customer.get('email', ''))
            self.address_input.setText(customer.get('address', ''))
            self.city_input.setText(customer.get('city', ''))
            self.postal_code_input.setText(customer.get('postal_code', ''))
            
            # Notas
            self.notes_input.setPlainText(customer.get('notes', ''))
            
            # Estadísticas (si es edición)
            if hasattr(self, 'customer_stats'):
                stats = self.managers['customer'].get_customer_statistics(self.customer_id)
                stats_text = f"""
                Compras totales: {stats.get('total_purchases', 0)}
                Monto total: ${stats.get('total_spent', 0):,.2f}
                Compra promedio: ${stats.get('avg_purchase', 0):,.2f}
                Última compra: {stats.get('last_purchase_date', 'Nunca')}
                Balance cuenta: ${customer.get('account_balance', 0):,.2f}
                """
                self.customer_stats.setText(stats_text.strip())
            
        except Exception as e:
            logger.error(f"Error cargando datos del cliente: {e}")
            QMessageBox.critical(self, "Error", f"Error cargando cliente: {str(e)}")
    
    def on_customer_type_changed(self, customer_type: str):
        """Manejar cambio de tipo de cliente"""
        if customer_type == "Persona Física":
            self.name_input.setEnabled(True)
            self.business_name_input.setEnabled(False)
            self.business_name_input.clear()
            self.document_type.setCurrentText("DNI")
        else:  # Empresa
            self.name_input.setEnabled(False)
            self.name_input.clear()
            self.business_name_input.setEnabled(True)
            self.document_type.setCurrentText("CUIT")
    
    def validate_form(self) -> Dict:
        """Validar datos del formulario"""
        validation = {
            'valid': True,
            'errors': []
        }
        
        try:
            # Validar que tenga nombre o razón social
            if not self.name_input.text().strip() and not self.business_name_input.text().strip():
                validation['errors'].append("Debe proporcionar nombre o razón social")
            
            # Validar email si se proporciona
            email = self.email_input.text().strip()
            if email:
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, email):
                    validation['errors'].append("Formato de email inválido")
            
            # Validar documento si se proporciona
            document = self.document_number.text().strip()
            if document and len(document) < 6:
                validation['errors'].append("Número de documento muy corto")
            
            validation['valid'] = len(validation['errors']) == 0
            
        except Exception as e:
            logger.error(f"Error validando formulario: {e}")
            validation['errors'].append(f"Error en validación: {str(e)}")
            validation['valid'] = False
        
        return validation
    
    def save_customer(self):
        """Guardar cliente"""
        try:
            # Validar formulario
            validation = self.validate_form()
            if not validation['valid']:
                error_msg = "Errores encontrados:\\n" + "\\n".join(validation['errors'])
                QMessageBox.warning(self, "Errores de Validación", error_msg)
                return
            
            # Preparar datos
            customer_data = {
                'name': self.name_input.text().strip(),
                'business_name': self.business_name_input.text().strip(),
                'document_type': self.document_type.currentText(),
                'document_number': self.document_number.text().strip(),
                'phone': self.phone_input.text().strip(),
                'mobile': self.mobile_input.text().strip(),
                'email': self.email_input.text().strip(),
                'address': self.address_input.text().strip(),
                'city': self.city_input.text().strip(),
                'postal_code': self.postal_code_input.text().strip(),
                'category_id': self.category_combo.currentData(),
                'tax_condition': self.tax_condition.currentText(),
                'credit_limit': self.credit_limit.value(),
                'payment_terms': self.payment_terms.value(),
                'discount_percentage': self.discount_percentage.value(),
                'notes': self.notes_input.toPlainText().strip()
            }
            
            # Validación básica del manager (sin método específico)
            # El CustomerManager básico no tiene validate_customer_data
            # Se mantiene solo validación local
            
            # Guardar
            if self.customer_id is None:
                # Crear nuevo
                result_id = self.managers['customer'].create_customer(customer_data)
                if result_id:
                    customer_data['id'] = result_id
                    QMessageBox.information(self, "Éxito", "Cliente creado correctamente")
                else:
                    QMessageBox.critical(self, "Error", "Error al crear el cliente")
                    return
            else:
                # Actualizar existente
                customer_data['id'] = self.customer_id
                success = self.managers['customer'].update_customer(self.customer_id, customer_data)
                if success:
                    QMessageBox.information(self, "Éxito", "Cliente actualizado correctamente")
                else:
                    QMessageBox.critical(self, "Error", "Error al actualizar el cliente")
                    return
            
            # Emitir señal y cerrar
            self.customer_saved.emit(customer_data)
            self.accept()
            
        except Exception as e:
            logger.error(f"Error guardando cliente: {e}")
            QMessageBox.critical(self, "Error", f"Error guardando cliente: {str(e)}")

class CustomerSelectionDialog(QDialog):
    """Diálogo para seleccionar cliente"""
    
    customer_selected = pyqtSignal(dict)
    
    def __init__(self, managers: dict, parent=None):
        super().__init__(parent)
        
        self.managers = managers
        self.selected_customer = None
        
        self.setWindowTitle("Seleccionar Cliente")
        self.setModal(True)
        self.resize(800, 600)
        
        self.init_ui()
        self.load_customers()
    
    def init_ui(self):
        """Inicializar interfaz"""
        layout = QVBoxLayout(self)
        
        # Header con búsqueda
        header_layout = QHBoxLayout()
        
        search_label = QLabel("🔍 Buscar:")
        header_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nombre, documento, teléfono...")
        self.search_input.textChanged.connect(self.search_customers)
        header_layout.addWidget(self.search_input)
        
        new_customer_btn = QPushButton("➕ Nuevo Cliente")
        new_customer_btn.clicked.connect(self.create_new_customer)
        header_layout.addWidget(new_customer_btn)
        
        layout.addLayout(header_layout)
        
        # Tabla de clientes
        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(6)
        self.customers_table.setHorizontalHeaderLabels([
            "ID", "Nombre/Razón Social", "Documento", "Teléfono", "Email", "Balance"
        ])
        
        # Configurar tabla
        header = self.customers_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        
        self.customers_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.customers_table.setAlternatingRowColors(True)
        self.customers_table.doubleClicked.connect(self.select_customer)
        
        layout.addWidget(self.customers_table)
        
        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        select_btn = QPushButton("✅ Seleccionar")
        select_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
                border: none;
            }
        """)
        select_btn.clicked.connect(self.select_customer)
        buttons_layout.addWidget(select_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_customers(self):
        """Cargar lista de clientes"""
        try:
            if 'customer' not in self.managers:
                return
            
            customers = self.managers['customer'].get_all_customers(active_only=True)
            
            self.customers_table.setRowCount(len(customers))
            
            for row, customer in enumerate(customers):
                self.customers_table.setItem(row, 0, QTableWidgetItem(str(customer['id'])))
                
                # Nombre o razón social
                name = customer.get('business_name') or customer.get('name', '')
                self.customers_table.setItem(row, 1, QTableWidgetItem(name))
                
                # Documento
                doc_text = f"{customer.get('document_type', '')} {customer.get('document_number', '')}"
                self.customers_table.setItem(row, 2, QTableWidgetItem(doc_text.strip()))
                
                # Teléfono
                phone = customer.get('mobile') or customer.get('phone', '')
                self.customers_table.setItem(row, 3, QTableWidgetItem(phone))
                
                # Email
                self.customers_table.setItem(row, 4, QTableWidgetItem(customer.get('email', '')))
                
                # Balance
                balance = customer.get('account_balance', 0)
                balance_item = QTableWidgetItem(f"${balance:,.2f}")
                if balance > 0:
                    balance_item.setForeground(QColor('#e74c3c'))  # Rojo para deuda
                elif balance < 0:
                    balance_item.setForeground(QColor('#27ae60'))  # Verde para saldo a favor
                self.customers_table.setItem(row, 5, balance_item)
                
                # Guardar datos del cliente en la fila
                self.customers_table.item(row, 0).setData(Qt.UserRole, customer)
            
        except Exception as e:
            logger.error(f"Error cargando clientes: {e}")
    
    def search_customers(self):
        """Buscar clientes"""
        search_term = self.search_input.text().strip()
        
        try:
            if not search_term:
                self.load_customers()
                return
            
            if 'customer' not in self.managers:
                return
            
            customers = self.managers['customer'].search_customers(search_term)
            
            self.customers_table.setRowCount(len(customers))
            
            for row, customer in enumerate(customers):
                self.customers_table.setItem(row, 0, QTableWidgetItem(str(customer['id'])))
                
                name = customer.get('business_name') or customer.get('name', '')
                self.customers_table.setItem(row, 1, QTableWidgetItem(name))
                
                doc_text = f"{customer.get('document_type', '')} {customer.get('document_number', '')}"
                self.customers_table.setItem(row, 2, QTableWidgetItem(doc_text.strip()))
                
                phone = customer.get('mobile') or customer.get('phone', '')
                self.customers_table.setItem(row, 3, QTableWidgetItem(phone))
                
                self.customers_table.setItem(row, 4, QTableWidgetItem(customer.get('email', '')))
                
                balance = customer.get('account_balance', 0)
                balance_item = QTableWidgetItem(f"${balance:,.2f}")
                if balance > 0:
                    balance_item.setForeground(QColor('#e74c3c'))
                elif balance < 0:
                    balance_item.setForeground(QColor('#27ae60'))
                self.customers_table.setItem(row, 5, balance_item)
                
                self.customers_table.item(row, 0).setData(Qt.UserRole, customer)
                
        except Exception as e:
            logger.error(f"Error buscando clientes: {e}")
    
    def create_new_customer(self):
        """Crear nuevo cliente"""
        dialog = CustomerDialog(self.managers, parent=self)
        dialog.customer_saved.connect(self.on_customer_created)
        dialog.exec_()
    
    def on_customer_created(self, customer_data: dict):
        """Cliente creado exitosamente"""
        self.load_customers()  # Recargar lista
        
        # Seleccionar el nuevo cliente
        for row in range(self.customers_table.rowCount()):
            if self.customers_table.item(row, 0).text() == str(customer_data['id']):
                self.customers_table.selectRow(row)
                break
    
    def select_customer(self):
        """Seleccionar cliente"""
        current_row = self.customers_table.currentRow()
        if current_row >= 0:
            customer_item = self.customers_table.item(current_row, 0)
            if customer_item:
                customer_data = customer_item.data(Qt.UserRole)
                if customer_data:
                    self.customer_selected.emit(customer_data)
                    self.accept()
                    return
        
        QMessageBox.warning(self, "Selección", "Por favor seleccione un cliente")