"""
Controlador de Clientes - AlmacénPro v2.0 MVC
Controlador que gestiona la interfaz de clientes usando Qt Designer
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from .base_controller import BaseController
from models.customer_model import CustomerModel
from models.entities import Customer

logger = logging.getLogger(__name__)

class CustomersController(BaseController):
    """Controlador principal para gestionar clientes"""
    
    # Señales de comunicación con otros componentes
    customer_created = pyqtSignal(dict)
    customer_updated = pyqtSignal(dict)
    customer_deleted = pyqtSignal(int)
    customer_selected_for_sale = pyqtSignal(dict)
    
    def __init__(self, managers: Dict, current_user: Dict, parent=None):
        # Managers específicos
        self.customer_manager = managers.get('customer')
        
        # Modelo de datos
        self.customer_model = CustomerModel()
        
        # Estado del controlador
        self.current_customer = None
        self.is_loading = False
        
        # Inicializar controlador base
        super().__init__(managers, current_user, parent)
    
    def get_ui_file_path(self) -> str:
        """Retornar ruta al archivo .ui correspondiente"""
        return os.path.join(os.path.dirname(__file__), '..', 'views', 'forms', 'customers_widget.ui')
    
    def setup_ui(self):
        """Configurar elementos específicos de la UI"""
        # Configurar tabla de clientes
        self.setup_customers_table()
        
        # Configurar filtros
        self.setup_filters()
        
        # Estado inicial
        self.reset_customer_details()
        
        # Aplicar estilos específicos del módulo
        from utils.style_manager import StyleManager
        StyleManager.apply_module_styles(self, 'customer')
    
    def setup_customers_table(self):
        """Configurar tabla de clientes"""
        headers = ['Código', 'Nombre', 'Email', 'Teléfono', 'Segmento', 'Estado', 'Total Compras', 'Última Compra']
        column_widths = [80, -1, 180, 120, 80, 80, 120, 120]  # -1 = stretch
        
        self.setup_table_widget(self.tblClientes, headers, column_widths)
        
        # Configurar ordenamiento
        self.tblClientes.setSortingEnabled(True)
        self.tblClientes.sortByColumn(1, Qt.AscendingOrder)  # Ordenar por nombre
        
        # Configurar selección
        self.tblClientes.setSelectionMode(QAbstractItemView.SingleSelection)
    
    def setup_filters(self):
        """Configurar elementos de filtrado"""
        # Configurar comboboxes
        segmentos = ['Todos', 'REGULAR', 'VIP', 'PREMIUM']
        self.cmbSegmento.addItems(segmentos)
        
        estados = ['Todos', 'ACTIVO', 'INACTIVO', 'POTENCIAL', 'PERDIDO']
        self.cmbEstado.addItems(estados)
        
        # Configurar campo de búsqueda
        self.lineEditBuscar.setMaxLength(100)
        self.lineEditBuscar.setClearButtonEnabled(True)
    
    def connect_signals(self):
        """Conectar señales específicas del controlador"""
        # Filtros
        self.lineEditBuscar.textChanged.connect(self.on_search_changed)
        self.cmbSegmento.currentTextChanged.connect(self.on_segment_filter_changed)
        self.cmbEstado.currentTextChanged.connect(self.on_status_filter_changed)
        self.btnLimpiarFiltros.clicked.connect(self.on_clear_filters)
        
        # Tabla de clientes
        self.tblClientes.itemSelectionChanged.connect(self.on_customer_selected)
        self.tblClientes.itemDoubleClicked.connect(self.on_edit_customer)
        
        # Botones principales
        self.btnNuevoCliente.clicked.connect(self.on_new_customer)
        self.btnEditarCliente.clicked.connect(self.on_edit_customer)
        self.btnEliminarCliente.clicked.connect(self.on_delete_customer)
        
        # Botones de acciones específicas
        self.btnHistorialCompras.clicked.connect(self.on_view_purchase_history)
        self.btnAnalisisPredictivo.clicked.connect(self.on_view_predictive_analysis)
        
        # Importar/Exportar
        self.btnExportarClientes.clicked.connect(self.on_export_customers)
        self.btnImportarClientes.clicked.connect(self.on_import_customers)
        
        # Señales del modelo
        self.customer_model.customers_loaded.connect(self.on_customers_loaded)
        self.customer_model.customer_selected.connect(self.on_customer_details_changed)
        self.customer_model.filters_changed.connect(self.on_filters_applied)
        self.customer_model.error_occurred.connect(self.on_model_error)
        self.customer_model.loading_started.connect(self.on_loading_started)
        self.customer_model.loading_finished.connect(self.on_loading_finished)
    
    def setup_shortcuts(self):
        """Configurar atajos de teclado específicos"""
        super().setup_shortcuts()  # Atajos base
        
        # Atajos específicos de clientes
        QShortcut(QKeySequence("Ctrl+N"), self, self.on_new_customer)
        QShortcut(QKeySequence("F2"), self, self.on_edit_customer)
        QShortcut(QKeySequence("Delete"), self, self.on_delete_customer)
        QShortcut(QKeySequence("Ctrl+F"), self, self.lineEditBuscar.setFocus)
        QShortcut(QKeySequence("Escape"), self, self.on_clear_search)
    
    def load_initial_data(self):
        """Cargar datos iniciales"""
        try:
            if self.customer_manager:
                customers_data = self.customer_manager.get_all_customers()
                self.customer_model.load_customers(customers_data)
                self.logger.info("Datos de clientes cargados exitosamente")
            else:
                self.logger.warning("Customer manager no disponible")
                self.show_warning("Advertencia", "Gestor de clientes no disponible")
                
        except Exception as e:
            self.logger.error(f"Error cargando datos de clientes: {e}")
            self.show_error("Error", f"Error cargando clientes: {str(e)}")
    
    # === SLOTS DE INTERFAZ ===
    
    @pyqtSlot(str)
    def on_search_changed(self, text: str):
        """Manejar cambio en búsqueda"""
        self.customer_model.set_search_filter(text)
    
    @pyqtSlot(str)
    def on_segment_filter_changed(self, segment: str):
        """Manejar cambio en filtro de segmento"""
        self.customer_model.set_segment_filter(segment)
    
    @pyqtSlot(str)
    def on_status_filter_changed(self, status: str):
        """Manejar cambio en filtro de estado"""
        self.customer_model.set_status_filter(status)
    
    @pyqtSlot()
    def on_clear_filters(self):
        """Limpiar todos los filtros"""
        # Limpiar controles de UI
        self.lineEditBuscar.clear()
        self.cmbSegmento.setCurrentText('Todos')
        self.cmbEstado.setCurrentText('Todos')
        
        # Limpiar modelo
        self.customer_model.clear_filters()
    
    @pyqtSlot()
    def on_clear_search(self):
        """Limpiar solo el campo de búsqueda"""
        self.lineEditBuscar.clear()
        self.lineEditBuscar.setFocus()
    
    @pyqtSlot()
    def on_customer_selected(self):
        """Manejar selección de cliente en tabla"""
        try:
            current_row = self.tblClientes.currentRow()
            if current_row >= 0:
                # Obtener ID del cliente desde la tabla (primera columna oculta o buscar por código)
                customer_code = self.tblClientes.item(current_row, 0).text()
                
                # Buscar cliente por código
                filtered_customers = self.customer_model.filtered_customers
                for customer in filtered_customers:
                    if customer.get('codigo') == customer_code:
                        self.customer_model.select_customer(customer.get('id'))
                        break
            else:
                self.customer_model.select_customer(None)
                
        except Exception as e:
            self.logger.error(f"Error seleccionando cliente: {e}")
    
    @pyqtSlot()
    def on_new_customer(self):
        """Crear nuevo cliente"""
        try:
            self.open_customer_dialog()
            
        except Exception as e:
            self.logger.error(f"Error creando nuevo cliente: {e}")
            self.show_error("Error", f"Error creando cliente: {str(e)}")
    
    @pyqtSlot()
    def on_edit_customer(self):
        """Editar cliente seleccionado"""
        try:
            if not self.current_customer:
                self.show_warning("Advertencia", "Por favor, seleccione un cliente.")
                return
            
            self.open_customer_dialog(self.current_customer)
            
        except Exception as e:
            self.logger.error(f"Error editando cliente: {e}")
            self.show_error("Error", f"Error editando cliente: {str(e)}")
    
    def open_customer_dialog(self, customer_data: Optional[Dict] = None):
        """Abrir diálogo de cliente"""
        try:
            # Intentar usar diálogo específico si existe
            from ui.dialogs.customer_dialog import CustomerDialog
            
            dialog = CustomerDialog(self.customer_manager, customer_data, self)
            if dialog.exec_() == QDialog.Accepted:
                result_data = dialog.get_customer_data()
                
                if customer_data:  # Editando
                    if self.customer_manager.update_customer(customer_data['id'], result_data):
                        # Actualizar modelo
                        self.customer_model.update_customer(customer_data['id'], result_data)
                        self.customer_updated.emit(result_data)
                        self.show_info("Éxito", "Cliente actualizado exitosamente.")
                    else:
                        self.show_error("Error", "No se pudo actualizar el cliente.")
                else:  # Creando
                    new_customer_id = self.customer_manager.create_customer(result_data)
                    if new_customer_id:
                        result_data['id'] = new_customer_id
                        # Actualizar modelo
                        self.customer_model.add_customer(result_data)
                        self.customer_created.emit(result_data)
                        self.show_info("Éxito", "Cliente creado exitosamente.")
                    else:
                        self.show_error("Error", "No se pudo crear el cliente.")
        
        except ImportError:
            # Si no existe el diálogo específico, crear uno simple
            self.open_simple_customer_dialog(customer_data)
        except Exception as e:
            self.logger.error(f"Error en diálogo de cliente: {e}")
            self.show_error("Error", f"Error en diálogo: {str(e)}")
    
    def open_simple_customer_dialog(self, customer_data: Optional[Dict] = None):
        """Crear diálogo simple de cliente"""
        try:
            # Crear diálogo básico
            dialog = QDialog(self)
            dialog.setWindowTitle("Nuevo Cliente" if not customer_data else "Editar Cliente")
            dialog.setModal(True)
            dialog.resize(400, 350)
            
            layout = QVBoxLayout(dialog)
            
            # Formulario
            form_layout = QFormLayout()
            
            # Campos básicos
            edit_nombre = QLineEdit()
            edit_codigo = QLineEdit()
            edit_email = QLineEdit()
            edit_telefono = QLineEdit()
            
            combo_segmento = QComboBox()
            combo_segmento.addItems(['REGULAR', 'VIP', 'PREMIUM'])
            
            combo_estado = QComboBox()
            combo_estado.addItems(['ACTIVO', 'INACTIVO', 'POTENCIAL'])
            
            # Agregar campos al formulario
            form_layout.addRow("Nombre:", edit_nombre)
            form_layout.addRow("Código:", edit_codigo)
            form_layout.addRow("Email:", edit_email)
            form_layout.addRow("Teléfono:", edit_telefono)
            form_layout.addRow("Segmento:", combo_segmento)
            form_layout.addRow("Estado:", combo_estado)
            
            # Si es edición, llenar datos
            if customer_data:
                edit_nombre.setText(customer_data.get('nombre', ''))
                edit_codigo.setText(customer_data.get('codigo', ''))
                edit_email.setText(customer_data.get('email', ''))
                edit_telefono.setText(customer_data.get('telefono', ''))
                combo_segmento.setCurrentText(customer_data.get('segmento', 'REGULAR'))
                combo_estado.setCurrentText(customer_data.get('estado', 'ACTIVO'))
            
            layout.addLayout(form_layout)
            
            # Botones
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            # Validar y procesar
            if dialog.exec_() == QDialog.Accepted:
                # Validar campos requeridos
                if not edit_nombre.text().strip() or not edit_codigo.text().strip():
                    self.show_warning("Campos Requeridos", "Nombre y código son obligatorios.")
                    return
                
                # Preparar datos
                result_data = {
                    'nombre': edit_nombre.text().strip(),
                    'codigo': edit_codigo.text().strip(),
                    'email': edit_email.text().strip(),
                    'telefono': edit_telefono.text().strip(),
                    'segmento': combo_segmento.currentText(),
                    'estado': combo_estado.currentText(),
                    'activo': True,
                    'direccion': '',
                    'ciudad': '',
                    'documento': '',
                    'tipo_documento': 'DNI',
                    'limite_credito': 0.0,
                    'saldo_actual': 0.0,
                    'descuento_porcentual': 0.0
                }
                
                # Procesar según modo
                if customer_data:  # Editando
                    result_data['id'] = customer_data['id']
                    if self.customer_manager.update_customer(customer_data['id'], result_data):
                        self.customer_model.update_customer(customer_data['id'], result_data)
                        self.customer_updated.emit(result_data)
                        self.show_info("Éxito", "Cliente actualizado exitosamente.")
                        self.load_initial_data()  # Recargar datos
                    else:
                        self.show_error("Error", "No se pudo actualizar el cliente.")
                else:  # Creando
                    new_customer_id = self.customer_manager.create_customer(result_data)
                    if new_customer_id:
                        result_data['id'] = new_customer_id
                        self.customer_model.add_customer(result_data)
                        self.customer_created.emit(result_data)
                        self.show_info("Éxito", "Cliente creado exitosamente.")
                        self.load_initial_data()  # Recargar datos
                    else:
                        self.show_error("Error", "No se pudo crear el cliente.")
            
        except Exception as e:
            self.logger.error(f"Error en diálogo simple: {e}")
            self.show_error("Error", f"Error en diálogo: {str(e)}")
    
    @pyqtSlot()
    def on_delete_customer(self):
        """Eliminar cliente seleccionado"""
        try:
            if not self.current_customer:
                self.show_warning("Advertencia", "Por favor, seleccione un cliente.")
                return
            
            customer_name = self.current_customer.get('nombre', 'cliente')
            
            # Confirmar eliminación
            reply = self.show_question("Confirmar Eliminación", 
                                     f"¿Está seguro que desea eliminar el cliente '{customer_name}'?\n\n"
                                     "Esta acción no se puede deshacer.")
            
            if reply:
                customer_id = self.current_customer['id']
                if self.customer_manager.delete_customer(customer_id):
                    self.customer_model.remove_customer(customer_id)
                    self.customer_deleted.emit(customer_id)
                    self.show_info("Éxito", "Cliente eliminado exitosamente.")
                    self.load_initial_data()  # Recargar datos
                else:
                    self.show_error("Error", "No se pudo eliminar el cliente.")
            
        except Exception as e:
            self.logger.error(f"Error eliminando cliente: {e}")
            self.show_error("Error", f"Error eliminando cliente: {str(e)}")
    
    @pyqtSlot()
    def on_view_purchase_history(self):
        """Ver historial de compras del cliente"""
        try:
            if not self.current_customer:
                self.show_warning("Advertencia", "Por favor, seleccione un cliente.")
                return
            
            # Por ahora mostrar mensaje de funcionalidad en desarrollo
            customer_name = self.current_customer.get('nombre', 'cliente')
            self.show_info("Historial de Compras", 
                         f"Mostrando historial de compras de {customer_name}.\n\n"
                         "Funcionalidad en desarrollo.")
            
        except Exception as e:
            self.logger.error(f"Error viendo historial: {e}")
            self.show_error("Error", f"Error viendo historial: {str(e)}")
    
    @pyqtSlot()
    def on_view_predictive_analysis(self):
        """Ver análisis predictivo del cliente"""
        try:
            if not self.current_customer:
                self.show_warning("Advertencia", "Por favor, seleccione un cliente.")
                return
            
            # Intentar abrir widget de análisis predictivo
            customer_name = self.current_customer.get('nombre', 'cliente')
            self.show_info("Análisis Predictivo", 
                         f"Mostrando análisis predictivo de {customer_name}.\n\n"
                         "Funcionalidad en desarrollo.")
            
        except Exception as e:
            self.logger.error(f"Error en análisis predictivo: {e}")
            self.show_error("Error", f"Error en análisis predictivo: {str(e)}")
    
    @pyqtSlot()
    def on_export_customers(self):
        """Exportar lista de clientes"""
        try:
            # Obtener archivo de destino
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar Clientes",
                f"clientes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv);;Excel Files (*.xlsx)"
            )
            
            if file_path:
                # Exportar datos filtrados
                customers_data = self.customer_model.export_filtered_customers()
                
                if file_path.endswith('.csv'):
                    self.export_to_csv(customers_data, file_path)
                elif file_path.endswith('.xlsx'):
                    self.export_to_excel(customers_data, file_path)
                
                self.show_info("Exportación Exitosa", f"Clientes exportados a:\n{file_path}")
            
        except Exception as e:
            self.logger.error(f"Error exportando clientes: {e}")
            self.show_error("Error", f"Error exportando: {str(e)}")
    
    def export_to_csv(self, data: List[Dict], file_path: str):
        """Exportar a CSV"""
        import csv
        
        if not data:
            self.show_warning("Advertencia", "No hay datos para exportar.")
            return
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['codigo', 'nombre', 'email', 'telefono', 'segmento', 'estado', 
                         'total_compras', 'numero_compras', 'ultima_compra']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for customer in data:
                writer.writerow({
                    field: customer.get(field, '') for field in fieldnames
                })
    
    def export_to_excel(self, data: List[Dict], file_path: str):
        """Exportar a Excel (requiere openpyxl)"""
        try:
            import openpyxl
            from openpyxl import Workbook
            
            wb = Workbook()
            ws = wb.active
            ws.title = "Clientes"
            
            # Headers
            headers = ['Código', 'Nombre', 'Email', 'Teléfono', 'Segmento', 'Estado', 
                      'Total Compras', 'Número Compras', 'Última Compra']
            ws.append(headers)
            
            # Data
            for customer in data:
                row = [
                    customer.get('codigo', ''),
                    customer.get('nombre', ''),
                    customer.get('email', ''),
                    customer.get('telefono', ''),
                    customer.get('segmento', ''),
                    customer.get('estado', ''),
                    customer.get('total_compras', 0),
                    customer.get('numero_compras', 0),
                    customer.get('ultima_compra', '')
                ]
                ws.append(row)
            
            wb.save(file_path)
            
        except ImportError:
            self.show_error("Error", "Se require openpyxl para exportar a Excel.\n"
                          "Instale con: pip install openpyxl")
        except Exception as e:
            raise e
    
    @pyqtSlot()
    def on_import_customers(self):
        """Importar clientes desde archivo"""
        try:
            # Por ahora mostrar mensaje de funcionalidad en desarrollo
            self.show_info("Importar Clientes", 
                         "Funcionalidad de importación en desarrollo.\n\n"
                         "Próximamente se podrán importar clientes desde CSV o Excel.")
            
        except Exception as e:
            self.logger.error(f"Error importando clientes: {e}")
            self.show_error("Error", f"Error importando: {str(e)}")
    
    # === SLOTS DE MODELO ===
    
    @pyqtSlot(list)
    def on_customers_loaded(self, customers: List[Dict]):
        """Manejar carga de clientes"""
        try:
            self.populate_customers_table(customers)
            self.update_statistics()
        except Exception as e:
            self.logger.error(f"Error manejando carga de clientes: {e}")
    
    @pyqtSlot(dict)
    def on_customer_details_changed(self, customer_data: Dict):
        """Manejar cambio en detalles de cliente"""
        if customer_data:
            self.current_customer = customer_data
            self.update_customer_details(customer_data)
            self.enable_customer_actions(True)
        else:
            self.current_customer = None
            self.reset_customer_details()
            self.enable_customer_actions(False)
    
    @pyqtSlot()
    def on_filters_applied(self):
        """Manejar aplicación de filtros"""
        try:
            filtered_customers = self.customer_model.filtered_customers
            self.populate_customers_table(filtered_customers)
            self.update_statistics()
        except Exception as e:
            self.logger.error(f"Error aplicando filtros: {e}")
    
    @pyqtSlot(str)
    def on_model_error(self, error_message: str):
        """Manejar errores del modelo"""
        self.logger.error(f"Error del modelo de clientes: {error_message}")
        # Mostrar error crítico solo si es necesario
    
    @pyqtSlot()
    def on_loading_started(self):
        """Manejar inicio de carga"""
        self.is_loading = True
        self.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)
    
    @pyqtSlot()
    def on_loading_finished(self):
        """Manejar fin de carga"""
        self.is_loading = False
        self.setEnabled(True)
        QApplication.restoreOverrideCursor()
    
    # === MÉTODOS DE APOYO ===
    
    def populate_customers_table(self, customers: List[Dict]):
        """Poblar tabla de clientes"""
        try:
            self.tblClientes.setRowCount(len(customers))
            
            for row, customer in enumerate(customers):
                # Código
                self.tblClientes.setItem(row, 0, QTableWidgetItem(customer.get('codigo', '')))
                
                # Nombre
                name_item = QTableWidgetItem(customer.get('nombre', ''))
                # Resaltar clientes VIP
                if customer.get('segmento', '').upper() == 'VIP':
                    name_item.setBackground(QColor(255, 215, 0, 50))  # Dorado claro
                self.tblClientes.setItem(row, 1, name_item)
                
                # Email
                self.tblClientes.setItem(row, 2, QTableWidgetItem(customer.get('email', '')))
                
                # Teléfono
                self.tblClientes.setItem(row, 3, QTableWidgetItem(customer.get('telefono', '')))
                
                # Segmento
                segment_item = QTableWidgetItem(customer.get('segmento', 'REGULAR'))
                # Colorear según segmento
                if customer.get('segmento', '').upper() == 'VIP':
                    segment_item.setForeground(QColor(255, 140, 0))  # Naranja
                elif customer.get('segmento', '').upper() == 'PREMIUM':
                    segment_item.setForeground(QColor(128, 0, 128))  # Púrpura
                self.tblClientes.setItem(row, 4, segment_item)
                
                # Estado
                status_item = QTableWidgetItem(customer.get('estado', 'ACTIVO'))
                # Colorear según estado
                if customer.get('estado', '').upper() == 'ACTIVO':
                    status_item.setForeground(QColor(0, 128, 0))  # Verde
                elif customer.get('estado', '').upper() == 'INACTIVO':
                    status_item.setForeground(QColor(128, 128, 128))  # Gris
                elif customer.get('estado', '').upper() == 'PERDIDO':
                    status_item.setForeground(QColor(255, 0, 0))  # Rojo
                self.tblClientes.setItem(row, 5, status_item)
                
                # Total compras
                total_compras = self.safe_float_conversion(customer.get('total_compras', 0))
                self.tblClientes.setItem(row, 6, QTableWidgetItem(self.format_currency(total_compras)))
                
                # Última compra
                ultima_compra = customer.get('ultima_compra', '')
                if ultima_compra:
                    try:
                        if isinstance(ultima_compra, str):
                            date_obj = datetime.strptime(ultima_compra, '%Y-%m-%d %H:%M:%S')
                            ultima_compra = date_obj.strftime('%d/%m/%Y')
                    except:
                        pass
                self.tblClientes.setItem(row, 7, QTableWidgetItem(str(ultima_compra)))
            
            # Ajustar columnas
            self.tblClientes.resizeColumnsToContents()
            
        except Exception as e:
            self.logger.error(f"Error poblando tabla de clientes: {e}")
    
    def update_customer_details(self, customer_data: Dict):
        """Actualizar panel de detalles del cliente"""
        try:
            # Información básica
            self.lblDetalleNombreValor.setText(customer_data.get('nombre', '-'))
            self.lblDetalleCodigoValor.setText(customer_data.get('codigo', '-'))
            self.lblDetalleEmailValor.setText(customer_data.get('email', '-'))
            self.lblDetalleTelefonoValor.setText(customer_data.get('telefono', '-'))
            
            # Estadísticas
            self.lblDetalleSegmentoValor.setText(customer_data.get('segmento', '-'))
            self.lblDetalleEstadoValor.setText(customer_data.get('estado', '-'))
            
            # Formato moneda para totales
            total_compras = self.safe_float_conversion(customer_data.get('total_compras', 0))
            self.lblDetalleTotalComprasValor.setText(self.format_currency(total_compras))
            
            num_compras = self.safe_int_conversion(customer_data.get('numero_compras', 0))
            self.lblDetalleNumComprasValor.setText(str(num_compras))
            
            # Última compra
            ultima_compra = customer_data.get('ultima_compra', '')
            if ultima_compra:
                try:
                    if isinstance(ultima_compra, str):
                        date_obj = datetime.strptime(ultima_compra, '%Y-%m-%d %H:%M:%S')
                        ultima_compra = date_obj.strftime('%d/%m/%Y')
                except:
                    pass
            self.lblDetalleUltimaCompraValor.setText(str(ultima_compra) if ultima_compra else '-')
            
        except Exception as e:
            self.logger.error(f"Error actualizando detalles de cliente: {e}")
    
    def reset_customer_details(self):
        """Resetear panel de detalles"""
        # Información básica
        self.lblDetalleNombreValor.setText('-')
        self.lblDetalleCodigoValor.setText('-')
        self.lblDetalleEmailValor.setText('-')
        self.lblDetalleTelefonoValor.setText('-')
        
        # Estadísticas
        self.lblDetalleSegmentoValor.setText('-')
        self.lblDetalleEstadoValor.setText('-')
        self.lblDetalleTotalComprasValor.setText('$0.00')
        self.lblDetalleNumComprasValor.setText('0')
        self.lblDetalleUltimaCompraValor.setText('-')
    
    def enable_customer_actions(self, enable: bool):
        """Habilitar/deshabilitar acciones de cliente"""
        self.btnEditarCliente.setEnabled(enable)
        self.btnEliminarCliente.setEnabled(enable)
        self.btnHistorialCompras.setEnabled(enable)
        self.btnAnalisisPredictivo.setEnabled(enable)
    
    def update_statistics(self):
        """Actualizar estadísticas mostradas"""
        try:
            filtered_count = self.customer_model.get_filtered_count()
            total_count = self.customer_model.get_total_count()
            
            if filtered_count == total_count:
                self.lblTotalClientes.setText(f"Total: {total_count} clientes")
            else:
                self.lblTotalClientes.setText(f"Mostrando: {filtered_count} de {total_count} clientes")
            
        except Exception as e:
            self.logger.error(f"Error actualizando estadísticas: {e}")
    
    # === OVERRIDES ===
    
    @pyqtSlot()
    def on_save_shortcut(self):
        """Override del shortcut Ctrl+S - Exportar"""
        self.on_export_customers()
    
    def save_state(self) -> Dict[str, Any]:
        """Guardar estado del controlador"""
        state = super().save_state()
        state.update({
            'search_text': self.lineEditBuscar.text(),
            'segment_filter': self.cmbSegmento.currentText(),
            'status_filter': self.cmbEstado.currentText(),
            'selected_customer_id': self.current_customer.get('id') if self.current_customer else None
        })
        return state
    
    def restore_state(self, state: Dict[str, Any]):
        """Restaurar estado del controlador"""
        super().restore_state(state)
        
        if 'search_text' in state:
            self.lineEditBuscar.setText(state['search_text'])
        
        if 'segment_filter' in state:
            self.cmbSegmento.setCurrentText(state['segment_filter'])
        
        if 'status_filter' in state:
            self.cmbEstado.setCurrentText(state['status_filter'])