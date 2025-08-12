"""
Controlador MVC para Customers Widget - AlmacénPro v2.0
Gestión de clientes con arquitectura MVC
"""

import logging
from datetime import datetime, date
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from controllers.base_controller import BaseController
from models.customer_model import CustomerModel

logger = logging.getLogger(__name__)

class CustomersWidgetController(BaseController):
    """Controlador MVC para el widget de gestión de clientes"""
    
    # Señales personalizadas
    customer_added = pyqtSignal(dict)
    customer_updated = pyqtSignal(dict)
    customer_deleted = pyqtSignal(int)
    customer_selected = pyqtSignal(dict)
    
    def __init__(self, managers, current_user, parent=None):
        super().__init__(managers, current_user, parent)
        self.customer_manager = managers.get('customer')
        self.advanced_customer_manager = managers.get('advanced_customer')
        
        # Modelo de datos
        self.customer_model = CustomerModel(
            customer_manager=self.customer_manager,
            parent=self
        )
        
        # Estado actual
        self.selected_customer = None
        self.customers_list = []
        self.filter_text = ""
        
        # Cargar UI y configurar
        self.load_ui()
        self.setup_ui()
        self.connect_signals()
        self.connect_model_signals()
        
        # Cargar datos iniciales
        self.load_initial_data()
    
    def get_ui_file_path(self) -> str:
        """Retorna la ruta al archivo .ui"""
        return "views/forms/customers_widget.ui"
    
    def setup_ui(self):
        """Configurar elementos específicos de la UI después de cargar"""
        # Configurar tabla de clientes
        if hasattr(self, 'tblClientes'):
            self.setup_customers_table()
        
        # Configurar formulario de cliente
        self.setup_customer_form()
        
        # Configurar métricas del dashboard
        self.setup_dashboard_metrics()
    
    def connect_signals(self):
        """Conectar señales específicas del controlador"""
        # Conectar botones de acción
        if hasattr(self, 'btnNuevoCliente'):
            self.btnNuevoCliente.clicked.connect(self.new_customer)
        
        if hasattr(self, 'btnGuardarCliente'):
            self.btnGuardarCliente.clicked.connect(self.save_customer)
        
        if hasattr(self, 'btnEditarCliente'):
            self.btnEditarCliente.clicked.connect(self.edit_customer)
        
        if hasattr(self, 'btnEliminarCliente'):
            self.btnEliminarCliente.clicked.connect(self.delete_customer)
        
        # Conectar campo de búsqueda
        if hasattr(self, 'lineEditBuscar'):
            self.lineEditBuscar.textChanged.connect(self.filter_customers)
        
        # Conectar eventos de tabla
        if hasattr(self, 'tblClientes'):
            self.tblClientes.itemSelectionChanged.connect(self.on_customer_selection_changed)
            self.tblClientes.itemDoubleClicked.connect(self.on_customer_double_click)
    
    def connect_model_signals(self):
        """Conectar señales del modelo"""
        self.customer_model.customer_created.connect(self.on_model_customer_created)
        self.customer_model.customer_updated.connect(self.on_model_customer_updated)
        self.customer_model.customer_deleted.connect(self.on_model_customer_deleted)
        self.customer_model.data_changed.connect(self.refresh_customer_display)
        self.customer_model.error_occurred.connect(self.show_model_error)
    
    def setup_customers_table(self):
        """Configurar tabla de clientes"""
        if not hasattr(self, 'tblClientes'):
            return
            
        headers = ["ID", "Nombre", "Email", "Teléfono", "Tipo", "Categoría", "Crédito", "Estado"]
        self.tblClientes.setColumnCount(len(headers))
        self.tblClientes.setHorizontalHeaderLabels(headers)
        
        # Configurar columnas
        header = self.tblClientes.horizontalHeader()
        header.setStretchLastSection(True)
        header.resizeSection(0, 50)   # ID
        header.resizeSection(1, 150)  # Nombre
        header.resizeSection(2, 150)  # Email
        header.resizeSection(3, 100)  # Teléfono
        header.resizeSection(4, 80)   # Tipo
        header.resizeSection(5, 100)  # Categoría
        header.resizeSection(6, 80)   # Crédito
        
        # Configurar selección
        self.tblClientes.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tblClientes.setAlternatingRowColors(True)
    
    def setup_customer_form(self):
        """Configurar formulario de cliente"""
        # Limpiar formulario
        self.clear_customer_form()
        
        # Configurar validadores si existen los campos
        if hasattr(self, 'lineEditEmail'):
            email_validator = QRegExpValidator(QRegExp(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"))
            self.lineEditEmail.setValidator(email_validator)
        
        if hasattr(self, 'lineEditTelefono'):
            phone_validator = QRegExpValidator(QRegExp(r"[0-9\-\+\(\)\s]+"))
            self.lineEditTelefono.setValidator(phone_validator)
    
    def setup_dashboard_metrics(self):
        """Configurar métricas del dashboard"""
        # Actualizar contadores y métricas
        self.update_dashboard_metrics()
    
    def load_initial_data(self):
        """Cargar datos iniciales"""
        self.load_customers()
        self.update_dashboard_metrics()
    
    def load_customers(self):
        """Cargar clientes usando el modelo"""
        if not hasattr(self, 'tblClientes'):
            return
        
        try:
            # Usar el modelo para cargar clientes
            if self.customer_model.load_customers():
                self.customers_list = self.customer_model.customers  # Ya son diccionarios
                self.update_customers_table()
            else:
                error_msg = self.customer_model.last_error or "Error desconocido"
                QMessageBox.critical(self, "Error", f"Error cargando clientes: {error_msg}")
        
        except Exception as e:
            logger.error(f"Error cargando clientes: {e}")
            QMessageBox.critical(self, "Error", f"Error cargando clientes: {e}")
    
    def update_customers_table(self):
        """Actualizar tabla de clientes con filtros aplicados"""
        if not hasattr(self, 'tblClientes'):
            return
        
        # Aplicar filtros
        filtered_customers = self.customers_list
        if self.filter_text:
            filtered_customers = [
                c for c in self.customers_list 
                if self.filter_text.lower() in c.get('nombre', '').lower() or
                   self.filter_text.lower() in c.get('email', '').lower() or
                   self.filter_text.lower() in c.get('telefono', '').lower()
            ]
        
        self.tblClientes.setRowCount(len(filtered_customers))
        
        for row, customer in enumerate(filtered_customers):
            self.tblClientes.setItem(row, 0, QTableWidgetItem(str(customer.get('id', ''))))
            self.tblClientes.setItem(row, 1, QTableWidgetItem(str(customer.get('nombre', ''))))
            self.tblClientes.setItem(row, 2, QTableWidgetItem(str(customer.get('email', ''))))
            self.tblClientes.setItem(row, 3, QTableWidgetItem(str(customer.get('telefono', ''))))
            self.tblClientes.setItem(row, 4, QTableWidgetItem(str(customer.get('tipo', 'Individual'))))
            self.tblClientes.setItem(row, 5, QTableWidgetItem(str(customer.get('categoria', 'Estándar'))))
            self.tblClientes.setItem(row, 6, QTableWidgetItem(f"${customer.get('limite_credito', 0):.2f}"))
            self.tblClientes.setItem(row, 7, QTableWidgetItem(str(customer.get('estado', 'Activo'))))
    
    def filter_customers(self, text):
        """Filtrar clientes por texto"""
        self.filter_text = text.strip()
        self.update_customers_table()
    
    def new_customer(self):
        """Crear nuevo cliente"""
        self.clear_customer_form()
        self.selected_customer = None
        
        # Enfocar primer campo del formulario
        if hasattr(self, 'lineEditNombre'):
            self.lineEditNombre.setFocus()
    
    def save_customer(self):
        """Guardar cliente actual"""
        try:
            # Recopilar datos del formulario
            customer_data = self.get_customer_form_data()
            
            # Validar datos
            if not self.validate_customer_data(customer_data):
                return
            
            if self.selected_customer:
                # Actualizar cliente existente
                customer_data['id'] = self.selected_customer['id']
                result = self.customer_manager.update_customer(customer_data)
                if result['success']:
                    QMessageBox.information(self, "Éxito", "Cliente actualizado exitosamente")
                    self.customer_updated.emit(customer_data)
                else:
                    QMessageBox.critical(self, "Error", f"Error actualizando cliente: {result['message']}")
                    return
            else:
                # Crear nuevo cliente
                result = self.customer_manager.create_customer(customer_data)
                if result['success']:
                    QMessageBox.information(self, "Éxito", "Cliente creado exitosamente")
                    customer_data['id'] = result['customer_id']
                    self.customer_added.emit(customer_data)
                else:
                    QMessageBox.critical(self, "Error", f"Error creando cliente: {result['message']}")
                    return
            
            # Recargar datos
            self.load_customers()
            self.clear_customer_form()
            self.update_dashboard_metrics()
        
        except Exception as e:
            logger.error(f"Error guardando cliente: {e}")
            QMessageBox.critical(self, "Error", f"Error guardando cliente: {e}")
    
    def edit_customer(self):
        """Editar cliente seleccionado"""
        if not self.selected_customer:
            QMessageBox.warning(self, "Selección", "Seleccione un cliente para editar")
            return
        
        self.load_customer_to_form(self.selected_customer)
    
    def delete_customer(self):
        """Eliminar cliente seleccionado"""
        if not self.selected_customer:
            QMessageBox.warning(self, "Selección", "Seleccione un cliente para eliminar")
            return
        
        reply = QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Está seguro que desea eliminar el cliente '{self.selected_customer['nombre']}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                result = self.customer_manager.delete_customer(self.selected_customer['id'])
                if result['success']:
                    QMessageBox.information(self, "Éxito", "Cliente eliminado exitosamente")
                    self.customer_deleted.emit(self.selected_customer['id'])
                    self.load_customers()
                    self.clear_customer_form()
                    self.selected_customer = None
                    self.update_dashboard_metrics()
                else:
                    QMessageBox.critical(self, "Error", f"Error eliminando cliente: {result['message']}")
            
            except Exception as e:
                logger.error(f"Error eliminando cliente: {e}")
                QMessageBox.critical(self, "Error", f"Error eliminando cliente: {e}")
    
    def get_customer_form_data(self) -> dict:
        """Obtener datos del formulario de cliente"""
        data = {}
        
        # Campos básicos
        if hasattr(self, 'lineEditNombre'):
            data['nombre'] = self.lineEditNombre.text().strip()
        if hasattr(self, 'lineEditEmail'):
            data['email'] = self.lineEditEmail.text().strip()
        if hasattr(self, 'lineEditTelefono'):
            data['telefono'] = self.lineEditTelefono.text().strip()
        if hasattr(self, 'textEditDireccion'):
            data['direccion'] = self.textEditDireccion.toPlainText().strip()
        if hasattr(self, 'comboBoxTipo'):
            data['tipo'] = self.comboBoxTipo.currentText()
        if hasattr(self, 'comboBoxCategoria'):
            data['categoria'] = self.comboBoxCategoria.currentText()
        if hasattr(self, 'spinBoxLimiteCredito'):
            data['limite_credito'] = self.spinBoxLimiteCredito.value()
        
        return data
    
    def validate_customer_data(self, data: dict) -> bool:
        """Validar datos del cliente"""
        if not data.get('nombre'):
            QMessageBox.warning(self, "Validación", "El nombre es obligatorio")
            return False
        
        if data.get('email') and '@' not in data['email']:
            QMessageBox.warning(self, "Validación", "Email inválido")
            return False
        
        return True
    
    def load_customer_to_form(self, customer: dict):
        """Cargar datos del cliente al formulario"""
        if hasattr(self, 'lineEditNombre'):
            self.lineEditNombre.setText(customer.get('nombre', ''))
        if hasattr(self, 'lineEditEmail'):
            self.lineEditEmail.setText(customer.get('email', ''))
        if hasattr(self, 'lineEditTelefono'):
            self.lineEditTelefono.setText(customer.get('telefono', ''))
        if hasattr(self, 'textEditDireccion'):
            self.textEditDireccion.setPlainText(customer.get('direccion', ''))
        if hasattr(self, 'comboBoxTipo'):
            tipo_text = customer.get('tipo', 'Individual')
            index = self.comboBoxTipo.findText(tipo_text)
            if index >= 0:
                self.comboBoxTipo.setCurrentIndex(index)
        if hasattr(self, 'comboBoxCategoria'):
            categoria_text = customer.get('categoria', 'Estándar')
            index = self.comboBoxCategoria.findText(categoria_text)
            if index >= 0:
                self.comboBoxCategoria.setCurrentIndex(index)
        if hasattr(self, 'spinBoxLimiteCredito'):
            self.spinBoxLimiteCredito.setValue(customer.get('limite_credito', 0))
    
    def clear_customer_form(self):
        """Limpiar formulario de cliente"""
        if hasattr(self, 'lineEditNombre'):
            self.lineEditNombre.clear()
        if hasattr(self, 'lineEditEmail'):
            self.lineEditEmail.clear()
        if hasattr(self, 'lineEditTelefono'):
            self.lineEditTelefono.clear()
        if hasattr(self, 'textEditDireccion'):
            self.textEditDireccion.clear()
        if hasattr(self, 'comboBoxTipo'):
            self.comboBoxTipo.setCurrentIndex(0)
        if hasattr(self, 'comboBoxCategoria'):
            self.comboBoxCategoria.setCurrentIndex(0)
        if hasattr(self, 'spinBoxLimiteCredito'):
            self.spinBoxLimiteCredito.setValue(0)
    
    def update_dashboard_metrics(self):
        """Actualizar métricas del dashboard"""
        if not self.customer_manager:
            return
        
        try:
            total_customers = len(self.customers_list)
            active_customers = len([c for c in self.customers_list if c.get('estado') == 'Activo'])
            
            # Actualizar labels de métricas
            if hasattr(self, 'lblTotalClientes'):
                self.lblTotalClientes.setText(str(total_customers))
            if hasattr(self, 'lblClientesActivos'):
                self.lblClientesActivos.setText(str(active_customers))
            
            # Métricas avanzadas si está disponible
            if self.advanced_customer_manager:
                try:
                    metrics = self.advanced_customer_manager.get_customer_metrics()
                    if hasattr(self, 'lblClientesVIP'):
                        self.lblClientesVIP.setText(str(metrics.get('vip_customers', 0)))
                    if hasattr(self, 'lblTicketPromedio'):
                        self.lblTicketPromedio.setText(f"${metrics.get('avg_ticket', 0):.2f}")
                except Exception as e:
                    logger.warning(f"Métricas avanzadas no disponibles: {e}")
        
        except Exception as e:
            logger.error(f"Error actualizando métricas: {e}")
    
    def on_customer_selection_changed(self):
        """Manejar cambio de selección en tabla"""
        if not hasattr(self, 'tblClientes'):
            return
            
        current_row = self.tblClientes.currentRow()
        if current_row >= 0:
            customer_id = int(self.tblClientes.item(current_row, 0).text())
            self.selected_customer = next(
                (c for c in self.customers_list if c.get('id') == customer_id), None
            )
            
            if self.selected_customer:
                self.customer_selected.emit(self.selected_customer)
        else:
            self.selected_customer = None
    
    def on_customer_double_click(self, item):
        """Manejar doble click en cliente"""
        self.edit_customer()
    
    # === MÉTODOS DE INTEGRACIÓN CON MODELO ===
    
    def refresh_customer_display(self):
        """Actualizar display cuando el modelo cambia"""
        self.customers_list = self.customer_model.customers  # Ya son diccionarios
        self.update_customers_table()
        self.update_dashboard_metrics()
    
    def on_model_customer_created(self, customer_data):
        """Manejar creación de cliente desde el modelo"""
        self.customer_added.emit(customer_data)
        QMessageBox.information(self, "Éxito", "Cliente creado exitosamente")
    
    def on_model_customer_updated(self, customer_data):
        """Manejar actualización de cliente desde el modelo"""
        self.customer_updated.emit(customer_data)
        QMessageBox.information(self, "Éxito", "Cliente actualizado exitosamente")
    
    def on_model_customer_deleted(self, customer_id):
        """Manejar eliminación de cliente desde el modelo"""
        self.customer_deleted.emit(customer_id)
        QMessageBox.information(self, "Éxito", "Cliente eliminado exitosamente")
    
    def show_model_error(self, error_message):
        """Mostrar errores del modelo"""
        QMessageBox.critical(self, "Error", error_message)