"""
Diálogo de Configuración de Reportes - AlmacénPro v2.0
Configurador avanzado para generación de reportes y exportación
"""

import logging
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
import os

# Importar utilidades propias
try:
    from ...utils.exporters import FileExporter
    from ...utils.formatters import DateFormatter, NumberFormatter
except ImportError:
    # Fallback para imports relativos
    import sys
    sys.path.append('..')
    from utils.exporters import FileExporter
    from utils.formatters import DateFormatter, NumberFormatter

logger = logging.getLogger(__name__)

class ReportDialog(QDialog):
    """Diálogo principal para configuración de reportes"""
    
    report_generated = pyqtSignal(str, str)  # filename, format
    
    def __init__(self, managers: Dict, parent=None):
        super().__init__(parent)
        
        self.managers = managers
        self.file_exporter = FileExporter()
        self.current_data = []
        
        self.setWindowTitle("Generador de Reportes")
        self.setModal(True)
        self.resize(800, 600)
        
        # Tipos de reportes disponibles
        self.report_types = {
            'ventas': {
                'name': '📊 Reporte de Ventas',
                'description': 'Análisis detallado de ventas por período',
                'manager': 'sales_manager'
            },
            'clientes': {
                'name': '👥 Reporte de Clientes', 
                'description': 'Lista y análisis de clientes',
                'manager': 'customer_manager'
            },
            'productos': {
                'name': '📦 Catálogo de Productos',
                'description': 'Inventario y datos de productos',
                'manager': 'product_manager'
            },
            'inventario': {
                'name': '📋 Reporte de Inventario',
                'description': 'Estado actual del inventario',
                'manager': 'inventory_manager'
            },
            'financiero': {
                'name': '💰 Reporte Financiero',
                'description': 'Análisis financiero y flujo de caja',
                'manager': 'financial_manager'
            },
            'top_clientes': {
                'name': '🌟 Top Clientes',
                'description': 'Mejores clientes por período',
                'manager': 'customer_manager'
            },
            'productos_bajo_stock': {
                'name': '⚠️ Productos con Stock Bajo',
                'description': 'Productos que necesitan reposición',
                'manager': 'product_manager'
            }
        }
        
        self.init_ui()
        self.load_default_values()
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = self.create_header()
        layout.addLayout(header_layout)
        
        # Contenido principal con tabs
        self.tab_widget = QTabWidget()
        
        # Tab 1: Configuración básica
        config_tab = self.create_config_tab()
        self.tab_widget.addTab(config_tab, "⚙️ Configuración")
        
        # Tab 2: Filtros avanzados
        filters_tab = self.create_filters_tab()
        self.tab_widget.addTab(filters_tab, "🔍 Filtros")
        
        # Tab 3: Formato y exportación
        export_tab = self.create_export_tab()
        self.tab_widget.addTab(export_tab, "📤 Exportación")
        
        # Tab 4: Previsualización
        preview_tab = self.create_preview_tab()
        self.tab_widget.addTab(preview_tab, "👁️ Previsualización")
        
        layout.addWidget(self.tab_widget)
        
        # Botones de acción
        buttons_layout = self.create_buttons()
        layout.addLayout(buttons_layout)
    
    def create_header(self) -> QHBoxLayout:
        """Crear header del diálogo"""
        layout = QHBoxLayout()
        
        # Icono y título
        icon_label = QLabel("📊")
        icon_label.setStyleSheet("font-size: 24px;")
        layout.addWidget(icon_label)
        
        title_label = QLabel("Generador de Reportes")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Información de fecha
        date_label = QLabel(f"Fecha: {DateFormatter.format_date(datetime.now())}")
        date_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        layout.addWidget(date_label)
        
        return layout
    
    def create_config_tab(self) -> QWidget:
        """Crear tab de configuración básica"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Selección de tipo de reporte
        report_group = QGroupBox("📋 Tipo de Reporte")
        report_layout = QVBoxLayout(report_group)
        
        self.report_type_combo = QComboBox()
        for key, info in self.report_types.items():
            self.report_type_combo.addItem(info['name'], key)
        self.report_type_combo.currentTextChanged.connect(self.on_report_type_changed)
        
        self.report_description = QLabel()
        self.report_description.setStyleSheet("color: #7f8c8d; font-style: italic; margin: 5px;")
        self.report_description.setWordWrap(True)
        
        report_layout.addWidget(self.report_type_combo)
        report_layout.addWidget(self.report_description)
        
        layout.addWidget(report_group)
        
        # Configuración de período
        period_group = QGroupBox("📅 Período del Reporte")
        period_layout = QGridLayout(period_group)
        
        # Período predefinido
        period_layout.addWidget(QLabel("Período:"), 0, 0)
        self.period_combo = QComboBox()
        self.period_combo.addItems([
            "Hoy", "Ayer", "Últimos 7 días", "Últimos 30 días", 
            "Este mes", "Mes anterior", "Últimos 3 meses", 
            "Este año", "Año anterior", "Personalizado"
        ])
        self.period_combo.currentTextChanged.connect(self.on_period_changed)
        period_layout.addWidget(self.period_combo, 0, 1)
        
        # Fechas personalizadas
        period_layout.addWidget(QLabel("Desde:"), 1, 0)
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setEnabled(False)
        period_layout.addWidget(self.date_from, 1, 1)
        
        period_layout.addWidget(QLabel("Hasta:"), 2, 0)
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setEnabled(False)
        period_layout.addWidget(self.date_to, 2, 1)
        
        layout.addWidget(period_group)
        
        # Configuración adicional
        additional_group = QGroupBox("⚙️ Configuración Adicional")
        additional_layout = QFormLayout(additional_group)
        
        # Incluir inactivos
        self.include_inactive_cb = QCheckBox("Incluir elementos inactivos")
        additional_layout.addRow(self.include_inactive_cb)
        
        # Agrupar por
        self.group_by_combo = QComboBox()
        self.group_by_combo.addItems(["Sin agrupación", "Por día", "Por semana", "Por mes", "Por categoría"])
        additional_layout.addRow("Agrupar por:", self.group_by_combo)
        
        # Ordenar por
        self.sort_by_combo = QComboBox()
        self.sort_by_combo.addItems(["Fecha", "Nombre", "Cantidad", "Monto"])
        additional_layout.addRow("Ordenar por:", self.sort_by_combo)
        
        # Orden
        self.sort_order_combo = QComboBox()
        self.sort_order_combo.addItems(["Ascendente", "Descendente"])
        additional_layout.addRow("Orden:", self.sort_order_combo)
        
        layout.addWidget(additional_group)
        
        layout.addStretch()
        
        return tab
    
    def create_filters_tab(self) -> QWidget:
        """Crear tab de filtros avanzados"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Filtros por categorías
        category_group = QGroupBox("🏷️ Filtros por Categoría")
        category_layout = QVBoxLayout(category_group)
        
        # Categorías de productos
        self.product_categories = QListWidget()
        self.product_categories.setSelectionMode(QAbstractItemView.MultiSelection)
        self.product_categories.setMaximumHeight(100)
        category_layout.addWidget(QLabel("Categorías de productos:"))
        category_layout.addWidget(self.product_categories)
        
        # Categorías de clientes
        self.customer_categories = QListWidget()
        self.customer_categories.setSelectionMode(QAbstractItemView.MultiSelection) 
        self.customer_categories.setMaximumHeight(100)
        category_layout.addWidget(QLabel("Categorías de clientes:"))
        category_layout.addWidget(self.customer_categories)
        
        layout.addWidget(category_group)
        
        # Filtros por rangos
        range_group = QGroupBox("📊 Filtros por Rangos")
        range_layout = QFormLayout(range_group)
        
        # Rango de montos
        monto_layout = QHBoxLayout()
        self.monto_min = QDoubleSpinBox()
        self.monto_min.setRange(0, 999999)
        self.monto_min.setPrefix("$")
        monto_layout.addWidget(self.monto_min)
        
        monto_layout.addWidget(QLabel(" a "))
        
        self.monto_max = QDoubleSpinBox()
        self.monto_max.setRange(0, 999999)
        self.monto_max.setValue(999999)
        self.monto_max.setPrefix("$")
        monto_layout.addWidget(self.monto_max)
        
        range_layout.addRow("Rango de montos:", monto_layout)
        
        # Rango de cantidades
        qty_layout = QHBoxLayout()
        self.qty_min = QSpinBox()
        self.qty_min.setRange(0, 99999)
        qty_layout.addWidget(self.qty_min)
        
        qty_layout.addWidget(QLabel(" a "))
        
        self.qty_max = QSpinBox()
        self.qty_max.setRange(0, 99999)
        self.qty_max.setValue(99999)
        qty_layout.addWidget(self.qty_max)
        
        range_layout.addRow("Rango de cantidades:", qty_layout)
        
        layout.addWidget(range_group)
        
        # Filtros específicos
        specific_group = QGroupBox("🎯 Filtros Específicos")
        specific_layout = QFormLayout(specific_group)
        
        # Estados
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Todos", "Activos", "Completados", "Pendientes", "Cancelados"])
        specific_layout.addRow("Estado:", self.status_filter)
        
        # Usuarios/Vendedores
        self.user_filter = QComboBox()
        self.user_filter.addItem("Todos los usuarios", None)
        specific_layout.addRow("Usuario:", self.user_filter)
        
        # Solo con deuda (para clientes)
        self.debt_only_cb = QCheckBox("Solo clientes con deuda pendiente")
        specific_layout.addRow(self.debt_only_cb)
        
        # Stock bajo (para productos)
        self.low_stock_cb = QCheckBox("Solo productos con stock bajo")
        specific_layout.addRow(self.low_stock_cb)
        
        layout.addWidget(specific_group)
        
        layout.addStretch()
        
        return tab
    
    def create_export_tab(self) -> QWidget:
        """Crear tab de exportación"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Formato de archivo
        format_group = QGroupBox("📁 Formato de Archivo")
        format_layout = QVBoxLayout(format_group)
        
        # Radio buttons para formato
        self.format_excel = QRadioButton("📊 Excel (.xlsx)")
        self.format_excel.setChecked(True)
        format_layout.addWidget(self.format_excel)
        
        self.format_pdf = QRadioButton("📄 PDF (.pdf)")
        format_layout.addWidget(self.format_pdf)
        
        self.format_csv = QRadioButton("📋 CSV (.csv)")
        format_layout.addWidget(self.format_csv)
        
        # Verificar disponibilidad de formatos
        available_formats = self.file_exporter.get_available_formats()
        if 'excel' not in available_formats:
            self.format_excel.setEnabled(False)
            self.format_excel.setText("📊 Excel (.xlsx) - No disponible")
        
        if 'pdf' not in available_formats:
            self.format_pdf.setEnabled(False)
            self.format_pdf.setText("📄 PDF (.pdf) - No disponible")
        
        layout.addWidget(format_group)
        
        # Configuración de archivo
        file_group = QGroupBox("💾 Configuración de Archivo")
        file_layout = QFormLayout(file_group)
        
        # Nombre de archivo
        filename_layout = QHBoxLayout()
        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText("reporte_ventas_2024")
        filename_layout.addWidget(self.filename_input)
        
        browse_btn = QPushButton("📂 Examinar")
        browse_btn.clicked.connect(self.browse_file)
        filename_layout.addWidget(browse_btn)
        
        file_layout.addRow("Nombre de archivo:", filename_layout)
        
        # Directorio de destino
        dir_layout = QHBoxLayout()
        self.directory_input = QLineEdit()
        self.directory_input.setText(os.path.expanduser("~/Desktop"))
        dir_layout.addWidget(self.directory_input)
        
        browse_dir_btn = QPushButton("📁 Examinar")
        browse_dir_btn.clicked.connect(self.browse_directory)
        dir_layout.addWidget(browse_dir_btn)
        
        file_layout.addRow("Directorio:", dir_layout)
        
        layout.addWidget(file_group)
        
        # Opciones adicionales
        options_group = QGroupBox("⚙️ Opciones de Exportación")
        options_layout = QVBoxLayout(options_group)
        
        self.open_after_export = QCheckBox("Abrir archivo después de exportar")
        self.open_after_export.setChecked(True)
        options_layout.addWidget(self.open_after_export)
        
        self.include_summary = QCheckBox("Incluir resumen estadístico")
        self.include_summary.setChecked(True)
        options_layout.addWidget(self.include_summary)
        
        self.include_charts = QCheckBox("Incluir gráficos (solo PDF/Excel)")
        options_layout.addWidget(self.include_charts)
        
        layout.addWidget(options_group)
        
        layout.addStretch()
        
        return tab
    
    def create_preview_tab(self) -> QWidget:
        """Crear tab de previsualización"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Controles de previsualización
        controls_layout = QHBoxLayout()
        
        refresh_preview_btn = QPushButton("🔄 Actualizar Previsualización")
        refresh_preview_btn.clicked.connect(self.refresh_preview)
        controls_layout.addWidget(refresh_preview_btn)
        
        controls_layout.addStretch()
        
        self.preview_count_label = QLabel("Registros: 0")
        controls_layout.addWidget(self.preview_count_label)
        
        layout.addLayout(controls_layout)
        
        # Tabla de previsualización
        self.preview_table = QTableWidget()
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.preview_table)
        
        return tab
    
    def create_buttons(self) -> QHBoxLayout:
        """Crear botones de acción"""
        layout = QHBoxLayout()
        
        # Botón de ayuda
        help_btn = QPushButton("❓ Ayuda")
        help_btn.clicked.connect(self.show_help)
        layout.addWidget(help_btn)
        
        layout.addStretch()
        
        # Botones principales
        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        preview_btn = QPushButton("👁️ Previsualizar")
        preview_btn.clicked.connect(self.show_preview)
        layout.addWidget(preview_btn)
        
        self.generate_btn = QPushButton("📊 Generar Reporte")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.generate_btn.clicked.connect(self.generate_report)
        layout.addWidget(self.generate_btn)
        
        return layout
    
    def load_default_values(self):
        """Cargar valores por defecto"""
        # Cargar primera descripción de reporte
        self.on_report_type_changed()
        
        # Configurar fechas por defecto
        self.on_period_changed()
        
        # Cargar categorías disponibles
        self.load_categories()
        
        # Cargar usuarios disponibles
        self.load_users()
        
        # Generar nombre de archivo por defecto
        self.generate_default_filename()
    
    def on_report_type_changed(self):
        """Manejar cambio de tipo de reporte"""
        current_key = self.report_type_combo.currentData()
        if current_key and current_key in self.report_types:
            info = self.report_types[current_key]
            self.report_description.setText(info['description'])
            self.generate_default_filename()
    
    def on_period_changed(self):
        """Manejar cambio de período"""
        period = self.period_combo.currentText()
        today = date.today()
        
        if period == "Personalizado":
            self.date_from.setEnabled(True)
            self.date_to.setEnabled(True)
        else:
            self.date_from.setEnabled(False)
            self.date_to.setEnabled(False)
            
            # Configurar fechas según período
            if period == "Hoy":
                start_date = today
                end_date = today
            elif period == "Ayer":
                start_date = today - timedelta(days=1)
                end_date = today - timedelta(days=1)
            elif period == "Últimos 7 días":
                start_date = today - timedelta(days=7)
                end_date = today
            elif period == "Últimos 30 días":
                start_date = today - timedelta(days=30)
                end_date = today
            elif period == "Este mes":
                start_date = today.replace(day=1)
                end_date = today
            elif period == "Mes anterior":
                if today.month == 1:
                    start_date = date(today.year - 1, 12, 1)
                    end_date = date(today.year - 1, 12, 31)
                else:
                    start_date = date(today.year, today.month - 1, 1)
                    if today.month == 1:
                        end_date = date(today.year - 1, 12, 31)
                    else:
                        import calendar
                        last_day = calendar.monthrange(today.year, today.month - 1)[1]
                        end_date = date(today.year, today.month - 1, last_day)
            elif period == "Últimos 3 meses":
                start_date = today - timedelta(days=90)
                end_date = today
            elif period == "Este año":
                start_date = date(today.year, 1, 1)
                end_date = today
            elif period == "Año anterior":
                start_date = date(today.year - 1, 1, 1)
                end_date = date(today.year - 1, 12, 31)
            else:
                start_date = today
                end_date = today
            
            self.date_from.setDate(start_date)
            self.date_to.setDate(end_date)
    
    def load_categories(self):
        """Cargar categorías disponibles"""
        try:
            # Categorías de productos
            if 'product_manager' in self.managers:
                # TODO: Implementar obtención de categorías de productos
                self.product_categories.addItem("Todas las categorías")
            
            # Categorías de clientes
            if 'customer_manager' in self.managers:
                customer_manager = self.managers['customer_manager']
                if hasattr(customer_manager, 'CUSTOMER_CATEGORIES'):
                    for category in customer_manager.CUSTOMER_CATEGORIES:
                        self.customer_categories.addItem(category)
                
        except Exception as e:
            logger.error(f"Error cargando categorías: {e}")
    
    def load_users(self):
        """Cargar usuarios disponibles"""
        try:
            if 'user_manager' in self.managers:
                # TODO: Implementar obtención de usuarios
                self.user_filter.addItem("Usuario Admin", 1)
        except Exception as e:
            logger.error(f"Error cargando usuarios: {e}")
    
    def generate_default_filename(self):
        """Generar nombre de archivo por defecto"""
        report_type = self.report_type_combo.currentData() or "reporte"
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"{report_type}_{timestamp}"
        self.filename_input.setText(filename)
    
    def browse_file(self):
        """Examinar archivo de destino"""
        format_ext = ".xlsx"
        if self.format_pdf.isChecked():
            format_ext = ".pdf"
        elif self.format_csv.isChecked():
            format_ext = ".csv"
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Guardar Reporte Como",
            os.path.join(self.directory_input.text(), self.filename_input.text() + format_ext),
            f"Archivos (*{format_ext})"
        )
        
        if filename:
            directory = os.path.dirname(filename)
            name = os.path.splitext(os.path.basename(filename))[0]
            
            self.directory_input.setText(directory)
            self.filename_input.setText(name)
    
    def browse_directory(self):
        """Examinar directorio de destino"""
        directory = QFileDialog.getExistingDirectory(
            self, "Seleccionar Directorio",
            self.directory_input.text()
        )
        
        if directory:
            self.directory_input.setText(directory)
    
    def refresh_preview(self):
        """Actualizar previsualización"""
        try:
            # Obtener datos según configuración
            data = self.get_report_data()
            
            if not data:
                self.preview_table.setRowCount(0)
                self.preview_table.setColumnCount(0)
                self.preview_count_label.setText("Registros: 0")
                return
            
            # Configurar tabla
            headers = list(data[0].keys()) if data else []
            self.preview_table.setColumnCount(len(headers))
            self.preview_table.setHorizontalHeaderLabels(headers)
            
            # Mostrar máximo 100 registros en preview
            preview_data = data[:100]
            self.preview_table.setRowCount(len(preview_data))
            
            # Poblar tabla
            for row, record in enumerate(preview_data):
                for col, header in enumerate(headers):
                    value = record.get(header, "")
                    
                    # Formatear valor para mostrar
                    if isinstance(value, (int, float)):
                        if any(keyword in str(header).lower() for keyword in ['precio', 'monto', 'total', 'importe']):
                            display_value = NumberFormatter.format_currency(value)
                        else:
                            display_value = NumberFormatter.format_number(value)
                    elif isinstance(value, datetime):
                        display_value = DateFormatter.format_datetime(value)
                    else:
                        display_value = str(value) if value is not None else ""
                    
                    self.preview_table.setItem(row, col, QTableWidgetItem(display_value))
            
            # Actualizar contador
            total_count = len(data)
            shown_count = len(preview_data)
            
            if total_count > shown_count:
                self.preview_count_label.setText(f"Registros: {shown_count} de {total_count} (mostrando primeros 100)")
            else:
                self.preview_count_label.setText(f"Registros: {total_count}")
            
            # Ajustar columnas
            self.preview_table.resizeColumnsToContents()
            
        except Exception as e:
            logger.error(f"Error actualizando preview: {e}")
            QMessageBox.warning(self, "Error", f"Error actualizando previsualización: {str(e)}")
    
    def show_preview(self):
        """Mostrar tab de previsualización"""
        self.tab_widget.setCurrentIndex(3)  # Tab de preview
        self.refresh_preview()
    
    def get_report_data(self) -> List[Dict]:
        """Obtener datos del reporte según configuración"""
        try:
            report_type = self.report_type_combo.currentData()
            if not report_type:
                return []
            
            # Obtener manager correspondiente
            manager_name = self.report_types[report_type]['manager']
            manager = self.managers.get(manager_name)
            
            if not manager:
                logger.warning(f"Manager no disponible: {manager_name}")
                return []
            
            # Obtener fechas
            date_from = self.date_from.date().toPython()
            date_to = self.date_to.date().toPython()
            
            # Generar datos según tipo de reporte
            if report_type == 'ventas':
                return self.get_sales_data(manager, date_from, date_to)
            elif report_type == 'clientes':
                return self.get_customers_data(manager)
            elif report_type == 'productos':
                return self.get_products_data(manager)
            elif report_type == 'top_clientes':
                return self.get_top_customers_data(manager, date_from, date_to)
            elif report_type == 'productos_bajo_stock':
                return self.get_low_stock_data(manager)
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error obteniendo datos del reporte: {e}")
            return []
    
    def get_sales_data(self, manager, date_from, date_to) -> List[Dict]:
        """Obtener datos de ventas"""
        try:
            if hasattr(manager, 'get_sales_by_date_range'):
                return manager.get_sales_by_date_range(date_from, date_to)
            else:
                return []
        except Exception as e:
            logger.error(f"Error obteniendo datos de ventas: {e}")
            return []
    
    def get_customers_data(self, manager) -> List[Dict]:
        """Obtener datos de clientes"""
        try:
            if hasattr(manager, 'get_all_customers'):
                customers = manager.get_all_customers(active_only=not self.include_inactive_cb.isChecked())
                
                # Filtrar por deuda si está activado
                if self.debt_only_cb.isChecked():
                    customers = [c for c in customers if float(c.get('saldo_cuenta_corriente', 0)) > 0]
                
                return customers
            else:
                return []
        except Exception as e:
            logger.error(f"Error obteniendo datos de clientes: {e}")
            return []
    
    def get_products_data(self, manager) -> List[Dict]:
        """Obtener datos de productos"""
        try:
            if hasattr(manager, 'get_all_products'):
                return manager.get_all_products(include_inactive=self.include_inactive_cb.isChecked())
            else:
                return []
        except Exception as e:
            logger.error(f"Error obteniendo datos de productos: {e}")
            return []
    
    def get_top_customers_data(self, manager, date_from, date_to) -> List[Dict]:
        """Obtener datos de top clientes"""
        try:
            if hasattr(manager, 'get_top_customers'):
                days = (date_to - date_from).days
                return manager.get_top_customers(limit=50, period_days=days)
            else:
                return []
        except Exception as e:
            logger.error(f"Error obteniendo top clientes: {e}")
            return []
    
    def get_low_stock_data(self, manager) -> List[Dict]:
        """Obtener productos con stock bajo"""
        try:
            if hasattr(manager, 'get_products_with_low_stock'):
                return manager.get_products_with_low_stock()
            else:
                return []
        except Exception as e:
            logger.error(f"Error obteniendo productos con stock bajo: {e}")
            return []
    
    def generate_report(self):
        """Generar y exportar reporte"""
        try:
            # Validar configuración
            if not self.filename_input.text().strip():
                QMessageBox.warning(self, "Error", "Debe especificar un nombre de archivo")
                return
            
            if not self.directory_input.text().strip():
                QMessageBox.warning(self, "Error", "Debe especificar un directorio de destino")
                return
            
            # Determinar formato
            if self.format_excel.isChecked():
                format_type = "excel"
                extension = ".xlsx"
            elif self.format_pdf.isChecked():
                format_type = "pdf"
                extension = ".pdf"
            else:
                format_type = "csv"
                extension = ".csv"
            
            # Construir ruta completa
            filename = self.filename_input.text().strip()
            if not filename.endswith(extension):
                filename += extension
            
            full_path = os.path.join(self.directory_input.text(), filename)
            
            # Obtener datos
            data = self.get_report_data()
            
            if not data:
                QMessageBox.information(self, "Info", "No hay datos para exportar con los filtros seleccionados")
                return
            
            # Generar título del reporte
            report_type_info = self.report_types[self.report_type_combo.currentData()]
            title = f"{report_type_info['name']} - {DateFormatter.format_date(datetime.now())}"
            
            # Exportar
            success = self.file_exporter.export(
                data, full_path, format_type, title
            )
            
            if success:
                QMessageBox.information(
                    self, "Éxito", 
                    f"Reporte generado exitosamente:\n{full_path}\n\nRegistros exportados: {len(data)}"
                )
                
                # Abrir archivo si está configurado
                if self.open_after_export.isChecked():
                    try:
                        os.startfile(full_path)  # Windows
                    except:
                        try:
                            import subprocess
                            subprocess.call(['open', full_path])  # macOS
                        except:
                            pass  # Linux requiere diferentes comandos según el entorno
                
                # Emitir señal
                self.report_generated.emit(full_path, format_type)
                
                self.accept()
            else:
                QMessageBox.critical(
                    self, "Error", 
                    "Error generando el reporte. Verifique los permisos del archivo y el directorio."
                )
                
        except Exception as e:
            logger.error(f"Error generando reporte: {e}")
            QMessageBox.critical(self, "Error", f"Error generando reporte: {str(e)}")
    
    def show_help(self):
        """Mostrar ayuda"""
        help_text = """
        <h3>Generador de Reportes - Ayuda</h3>
        
        <b>Configuración:</b>
        <ul>
        <li>Seleccione el tipo de reporte deseado</li>
        <li>Configure el período de análisis</li>
        <li>Ajuste los filtros según sus necesidades</li>
        </ul>
        
        <b>Filtros:</b>
        <ul>
        <li>Use filtros para mostrar solo datos específicos</li>
        <li>Los rangos ayudan a filtrar por montos o cantidades</li>
        <li>Los filtros específicos varían según el tipo de reporte</li>
        </ul>
        
        <b>Exportación:</b>
        <ul>
        <li>Excel: Mejor para análisis detallado</li>
        <li>PDF: Ideal para presentaciones</li>
        <li>CSV: Compatible con cualquier sistema</li>
        </ul>
        
        <b>Previsualización:</b>
        <ul>
        <li>Use la previsualización para verificar los datos</li>
        <li>Muestra los primeros 100 registros</li>
        <li>Ajuste filtros si es necesario</li>
        </ul>
        """
        
        QMessageBox.information(self, "Ayuda - Generador de Reportes", help_text)