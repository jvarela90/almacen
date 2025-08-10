"""
Widget de Control de Stock Avanzado - AlmacénPro v2.0
Sistema completo de gestión de inventario con trazabilidad y alertas
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from decimal import Decimal
from enum import Enum

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QDateEdit,
    QCheckBox, QGroupBox, QSplitter, QFrame, QProgressBar,
    QHeaderView, QMessageBox, QDialog, QDialogButtonBox,
    QCalendarWidget, QSlider, QScrollArea, QTreeWidget, QTreeWidgetItem
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QDate, QThread, pyqtSignal as Signal
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QIcon

from ...utils.formatters import NumberFormatter, DateFormatter, TextFormatter, StatusFormatter
from ...utils.exporters import ExcelExporter, PDFExporter, CSVExporter

logger = logging.getLogger(__name__)

class StockAdjustmentType(Enum):
    """Tipos de ajuste de stock"""
    AJUSTE_POSITIVO = "ajuste_positivo"
    AJUSTE_NEGATIVO = "ajuste_negativo"
    PERDIDA = "perdida"
    ROBO = "robo"
    VENCIMIENTO = "vencimiento"
    DANO = "dano"
    DEVOLUCION_CLIENTE = "devolucion_cliente"
    DEVOLUCION_PROVEEDOR = "devolucion_proveedor"
    TRANSFERENCIA_ENTRADA = "transferencia_entrada"
    TRANSFERENCIA_SALIDA = "transferencia_salida"
    INVENTARIO_INICIAL = "inventario_inicial"

class StockAdjustmentDialog(QDialog):
    """Diálogo para ajustes de stock con autorización"""
    
    def __init__(self, product_manager, user_manager, product_id=None, parent=None):
        super().__init__(parent)
        self.product_manager = product_manager
        self.user_manager = user_manager
        self.product_id = product_id
        self.setWindowTitle("Ajuste de Stock")
        self.setModal(True)
        self.resize(600, 500)
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Información del producto
        product_group = QGroupBox("Producto")
        product_layout = QGridLayout(product_group)
        
        self.product_combo = QComboBox()
        self.product_combo.setEditable(True)
        product_layout.addWidget(QLabel("Producto:"), 0, 0)
        product_layout.addWidget(self.product_combo, 0, 1, 1, 2)
        
        self.current_stock_label = QLabel("0")
        self.current_stock_label.setFont(QFont("Arial", 12, QFont.Bold))
        product_layout.addWidget(QLabel("Stock Actual:"), 1, 0)
        product_layout.addWidget(self.current_stock_label, 1, 1)
        
        self.location_combo = QComboBox()
        self.location_combo.addItems(["Almacén Principal", "Depósito 1", "Depósito 2", "Sucursal Centro", "Sucursal Norte"])
        product_layout.addWidget(QLabel("Ubicación:"), 2, 0)
        product_layout.addWidget(self.location_combo, 2, 1, 1, 2)
        
        layout.addWidget(product_group)
        
        # Tipo y cantidad de ajuste
        adjustment_group = QGroupBox("Ajuste")
        adjustment_layout = QGridLayout(adjustment_group)
        
        self.adjustment_type_combo = QComboBox()
        for adj_type in StockAdjustmentType:
            display_name = adj_type.value.replace('_', ' ').title()
            self.adjustment_type_combo.addItem(display_name, adj_type.value)
        
        adjustment_layout.addWidget(QLabel("Tipo:"), 0, 0)
        adjustment_layout.addWidget(self.adjustment_type_combo, 0, 1)
        
        self.adjustment_quantity = QDoubleSpinBox()
        self.adjustment_quantity.setRange(-999999, 999999)
        self.adjustment_quantity.setDecimals(2)
        self.adjustment_quantity.setSuffix(" unidades")
        adjustment_layout.addWidget(QLabel("Cantidad:"), 1, 0)
        adjustment_layout.addWidget(self.adjustment_quantity, 1, 1)
        
        # Nuevo stock calculado automáticamente
        self.new_stock_label = QLabel("0")
        self.new_stock_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.new_stock_label.setStyleSheet("color: #2196F3;")
        adjustment_layout.addWidget(QLabel("Nuevo Stock:"), 2, 0)
        adjustment_layout.addWidget(self.new_stock_label, 2, 1)
        
        layout.addWidget(adjustment_group)
        
        # Motivo y observaciones
        reason_group = QGroupBox("Justificación")
        reason_layout = QVBoxLayout(reason_group)
        
        self.reason_combo = QComboBox()
        self.reason_combo.setEditable(True)
        self.reason_combo.addItems([
            "Inventario físico - diferencia",
            "Producto dañado",
            "Producto vencido",
            "Robo/hurto",
            "Error de carga",
            "Devolución cliente",
            "Devolución proveedor",
            "Transferencia entre depósitos",
            "Ajuste por sistema",
            "Otro motivo"
        ])
        reason_layout.addWidget(QLabel("Motivo:"))
        reason_layout.addWidget(self.reason_combo)
        
        self.observations = QTextEdit()
        self.observations.setMaximumHeight(100)
        self.observations.setPlaceholderText("Observaciones adicionales...")
        reason_layout.addWidget(QLabel("Observaciones:"))
        reason_layout.addWidget(self.observations)
        
        layout.addWidget(reason_group)
        
        # Información de lote (opcional)
        batch_group = QGroupBox("Información de Lote (Opcional)")
        batch_layout = QGridLayout(batch_group)
        
        self.batch_number = QLineEdit()
        self.batch_number.setPlaceholderText("Número de lote...")
        batch_layout.addWidget(QLabel("Lote:"), 0, 0)
        batch_layout.addWidget(self.batch_number, 0, 1)
        
        self.expiry_date = QDateEdit()
        self.expiry_date.setCalendarPopup(True)
        self.expiry_date.setDate(QDate.currentDate().addDays(365))
        batch_layout.addWidget(QLabel("Vencimiento:"), 1, 0)
        batch_layout.addWidget(self.expiry_date, 1, 1)
        
        layout.addWidget(batch_group)
        
        # Autorización
        auth_group = QGroupBox("Autorización")
        auth_layout = QGridLayout(auth_group)
        
        self.auth_user_combo = QComboBox()
        auth_layout.addWidget(QLabel("Usuario Autoriza:"), 0, 0)
        auth_layout.addWidget(self.auth_user_combo, 0, 1)
        
        self.auth_password = QLineEdit()
        self.auth_password.setEchoMode(QLineEdit.Password)
        self.auth_password.setPlaceholderText("Contraseña de autorización")
        auth_layout.addWidget(QLabel("Contraseña:"), 1, 0)
        auth_layout.addWidget(self.auth_password, 1, 1)
        
        layout.addWidget(auth_group)
        
        # Botones
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Conexiones
        self.product_combo.currentTextChanged.connect(self.update_current_stock)
        self.adjustment_quantity.valueChanged.connect(self.calculate_new_stock)
        self.adjustment_type_combo.currentTextChanged.connect(self.update_adjustment_sign)
    
    def load_data(self):
        """Cargar datos iniciales"""
        try:
            # Cargar productos
            products = self.product_manager.get_all_products()
            for product in products:
                self.product_combo.addItem(
                    f"{product.get('codigo', '')} - {product.get('nombre', '')}",
                    product.get('id')
                )
            
            # Cargar usuarios autorizadores (supervisores y gerentes)
            authorized_users = self.user_manager.get_users_by_role(['GERENTE', 'ADMINISTRADOR'])
            for user in authorized_users:
                self.auth_user_combo.addItem(
                    f"{user.get('nombre', '')} ({user.get('rol', '')})",
                    user.get('id')
                )
            
            # Si hay producto preseleccionado
            if self.product_id:
                self.select_product_by_id(self.product_id)
                
        except Exception as e:
            logger.error(f"Error cargando datos: {e}")
    
    def select_product_by_id(self, product_id):
        """Seleccionar producto por ID"""
        for i in range(self.product_combo.count()):
            if self.product_combo.itemData(i) == product_id:
                self.product_combo.setCurrentIndex(i)
                break
    
    def update_current_stock(self):
        """Actualizar stock actual del producto seleccionado"""
        try:
            product_id = self.product_combo.currentData()
            if product_id:
                location = self.location_combo.currentText()
                current_stock = self.product_manager.get_product_stock(product_id, location)
                self.current_stock_label.setText(f"{current_stock:,.2f}")
                self.calculate_new_stock()
                
        except Exception as e:
            logger.error(f"Error actualizando stock: {e}")
    
    def update_adjustment_sign(self):
        """Actualizar signo del ajuste según el tipo"""
        adjustment_type = self.adjustment_type_combo.currentData()
        
        # Tipos que normalmente son negativos
        negative_types = [
            StockAdjustmentType.AJUSTE_NEGATIVO.value,
            StockAdjustmentType.PERDIDA.value,
            StockAdjustmentType.ROBO.value,
            StockAdjustmentType.VENCIMIENTO.value,
            StockAdjustmentType.DANO.value,
            StockAdjustmentType.TRANSFERENCIA_SALIDA.value
        ]
        
        current_value = abs(self.adjustment_quantity.value())
        if adjustment_type in negative_types:
            self.adjustment_quantity.setValue(-current_value)
        else:
            self.adjustment_quantity.setValue(current_value)
            
        self.calculate_new_stock()
    
    def calculate_new_stock(self):
        """Calcular nuevo stock después del ajuste"""
        try:
            current_stock = float(self.current_stock_label.text().replace(',', ''))
            adjustment = self.adjustment_quantity.value()
            new_stock = current_stock + adjustment
            
            self.new_stock_label.setText(f"{new_stock:,.2f}")
            
            # Cambiar color según si queda en negativo
            if new_stock < 0:
                self.new_stock_label.setStyleSheet("color: #F44336; font-weight: bold;")
            elif new_stock == 0:
                self.new_stock_label.setStyleSheet("color: #FF9800; font-weight: bold;")
            else:
                self.new_stock_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                
        except Exception as e:
            logger.error(f"Error calculando nuevo stock: {e}")
    
    def get_adjustment_data(self):
        """Obtener datos del ajuste"""
        return {
            'product_id': self.product_combo.currentData(),
            'product_name': self.product_combo.currentText(),
            'location': self.location_combo.currentText(),
            'adjustment_type': self.adjustment_type_combo.currentData(),
            'adjustment_type_display': self.adjustment_type_combo.currentText(),
            'quantity': self.adjustment_quantity.value(),
            'current_stock': float(self.current_stock_label.text().replace(',', '')),
            'new_stock': float(self.new_stock_label.text().replace(',', '')),
            'reason': self.reason_combo.currentText(),
            'observations': self.observations.toPlainText(),
            'batch_number': self.batch_number.text(),
            'expiry_date': self.expiry_date.date().toPyDate() if self.expiry_date.date() != QDate.currentDate() else None,
            'authorized_by': self.auth_user_combo.currentData(),
            'authorized_by_name': self.auth_user_combo.currentText(),
            'auth_password': self.auth_password.text(),
            'adjustment_date': datetime.now()
        }

class StockTransferDialog(QDialog):
    """Diálogo para transferencias de stock entre almacenes"""
    
    def __init__(self, product_manager, parent=None):
        super().__init__(parent)
        self.product_manager = product_manager
        self.setWindowTitle("Transferencia de Stock")
        self.setModal(True)
        self.resize(500, 400)
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Información de transferencia
        transfer_group = QGroupBox("Transferencia")
        transfer_layout = QGridLayout(transfer_group)
        
        # Origen
        self.origin_combo = QComboBox()
        self.origin_combo.addItems(["Almacén Principal", "Depósito 1", "Depósito 2", "Sucursal Centro", "Sucursal Norte"])
        transfer_layout.addWidget(QLabel("Origen:"), 0, 0)
        transfer_layout.addWidget(self.origin_combo, 0, 1)
        
        # Destino
        self.destination_combo = QComboBox()
        self.destination_combo.addItems(["Almacén Principal", "Depósito 1", "Depósito 2", "Sucursal Centro", "Sucursal Norte"])
        transfer_layout.addWidget(QLabel("Destino:"), 1, 0)
        transfer_layout.addWidget(self.destination_combo, 1, 1)
        
        layout.addWidget(transfer_group)
        
        # Productos a transferir
        products_group = QGroupBox("Productos")
        products_layout = QVBoxLayout(products_group)
        
        # Botones para agregar/quitar productos
        buttons_layout = QHBoxLayout()
        self.add_product_btn = QPushButton("Agregar Producto")
        self.remove_product_btn = QPushButton("Quitar Producto")
        self.remove_product_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.add_product_btn)
        buttons_layout.addWidget(self.remove_product_btn)
        buttons_layout.addStretch()
        
        products_layout.addLayout(buttons_layout)
        
        # Tabla de productos
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(5)
        self.products_table.setHorizontalHeaderLabels([
            "Producto", "Stock Origen", "Cantidad", "Lote", "Observaciones"
        ])
        self.products_table.horizontalHeader().setStretchLastSection(True)
        products_layout.addWidget(self.products_table)
        
        layout.addWidget(products_group)
        
        # Observaciones generales
        notes_group = QGroupBox("Observaciones")
        notes_layout = QVBoxLayout(notes_group)
        
        self.transfer_notes = QTextEdit()
        self.transfer_notes.setMaximumHeight(80)
        self.transfer_notes.setPlaceholderText("Observaciones sobre la transferencia...")
        notes_layout.addWidget(self.transfer_notes)
        
        layout.addWidget(notes_group)
        
        # Botones
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Conexiones
        self.add_product_btn.clicked.connect(self.add_product_row)
        self.remove_product_btn.clicked.connect(self.remove_product_row)
        self.products_table.selectionModel().selectionChanged.connect(self.update_remove_button)
    
    def load_data(self):
        """Cargar datos iniciales"""
        pass
    
    def add_product_row(self):
        """Agregar fila de producto"""
        row = self.products_table.rowCount()
        self.products_table.insertRow(row)
        
        # Combo de productos
        product_combo = QComboBox()
        products = self.product_manager.get_all_products()
        for product in products:
            product_combo.addItem(
                f"{product.get('codigo', '')} - {product.get('nombre', '')}",
                product.get('id')
            )
        self.products_table.setCellWidget(row, 0, product_combo)
        
        # Stock origen (label)
        stock_label = QLabel("0")
        self.products_table.setCellWidget(row, 1, stock_label)
        
        # Cantidad (spinbox)
        quantity_spin = QDoubleSpinBox()
        quantity_spin.setRange(0, 999999)
        quantity_spin.setDecimals(2)
        self.products_table.setCellWidget(row, 2, quantity_spin)
        
        # Lote
        batch_line = QLineEdit()
        batch_line.setPlaceholderText("Número de lote...")
        self.products_table.setCellWidget(row, 3, batch_line)
        
        # Observaciones
        obs_line = QLineEdit()
        obs_line.setPlaceholderText("Observaciones...")
        self.products_table.setCellWidget(row, 4, obs_line)
        
        # Conectar cambio de producto para actualizar stock
        product_combo.currentTextChanged.connect(
            lambda: self.update_origin_stock(row)
        )
        
        self.update_remove_button()
    
    def remove_product_row(self):
        """Quitar fila seleccionada"""
        current_row = self.products_table.currentRow()
        if current_row >= 0:
            self.products_table.removeRow(current_row)
        self.update_remove_button()
    
    def update_remove_button(self):
        """Actualizar estado del botón quitar"""
        self.remove_product_btn.setEnabled(
            self.products_table.rowCount() > 0 and 
            self.products_table.currentRow() >= 0
        )
    
    def update_origin_stock(self, row):
        """Actualizar stock de origen para el producto seleccionado"""
        try:
            product_combo = self.products_table.cellWidget(row, 0)
            stock_label = self.products_table.cellWidget(row, 1)
            
            if product_combo and stock_label:
                product_id = product_combo.currentData()
                if product_id:
                    origin = self.origin_combo.currentText()
                    stock = self.product_manager.get_product_stock(product_id, origin)
                    stock_label.setText(f"{stock:,.2f}")
                    
        except Exception as e:
            logger.error(f"Error actualizando stock origen: {e}")
    
    def get_transfer_data(self):
        """Obtener datos de transferencia"""
        products = []
        
        for row in range(self.products_table.rowCount()):
            product_combo = self.products_table.cellWidget(row, 0)
            stock_label = self.products_table.cellWidget(row, 1)
            quantity_spin = self.products_table.cellWidget(row, 2)
            batch_line = self.products_table.cellWidget(row, 3)
            obs_line = self.products_table.cellWidget(row, 4)
            
            if product_combo and quantity_spin.value() > 0:
                products.append({
                    'product_id': product_combo.currentData(),
                    'product_name': product_combo.currentText(),
                    'origin_stock': float(stock_label.text().replace(',', '')),
                    'quantity': quantity_spin.value(),
                    'batch_number': batch_line.text(),
                    'observations': obs_line.text()
                })
        
        return {
            'origin_location': self.origin_combo.currentText(),
            'destination_location': self.destination_combo.currentText(),
            'products': products,
            'notes': self.transfer_notes.toPlainText(),
            'transfer_date': datetime.now()
        }

class AdvancedStockWidget(QWidget):
    """Widget avanzado de control de stock"""
    
    # Señales
    stock_updated = pyqtSignal()
    alert_triggered = pyqtSignal(dict)
    
    def __init__(self, product_manager, user_manager=None, parent=None):
        super().__init__(parent)
        self.product_manager = product_manager
        self.user_manager = user_manager
        
        self.setup_ui()
        self.setup_connections()
        self.setup_timer()
        self.load_data()
    
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header con título y controles
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Control de Stock Avanzado")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet("color: #2196F3; margin-bottom: 10px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Botones principales
        self.adjust_stock_btn = QPushButton("Ajustar Stock")
        self.adjust_stock_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; padding: 8px 16px; border-radius: 4px; }")
        
        self.transfer_stock_btn = QPushButton("Transferir Stock")
        self.transfer_stock_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 8px 16px; border-radius: 4px; }")
        
        self.physical_inventory_btn = QPushButton("Inventario Físico")
        self.physical_inventory_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px 16px; border-radius: 4px; }")
        
        self.export_btn = QPushButton("Exportar")
        self.export_btn.setStyleSheet("QPushButton { background-color: #9C27B0; color: white; padding: 8px 16px; border-radius: 4px; }")
        
        header_layout.addWidget(self.adjust_stock_btn)
        header_layout.addWidget(self.transfer_stock_btn)
        header_layout.addWidget(self.physical_inventory_btn)
        header_layout.addWidget(self.export_btn)
        
        layout.addLayout(header_layout)
        
        # Crear tabs principales
        self.tab_widget = QTabWidget()
        
        # Tab 1: Dashboard de Stock
        self.dashboard_tab = self.create_dashboard_tab()
        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
        
        # Tab 2: Stock por Producto
        self.products_tab = self.create_products_tab()
        self.tab_widget.addTab(self.products_tab, "Por Producto")
        
        # Tab 3: Stock por Ubicación
        self.locations_tab = self.create_locations_tab()
        self.tab_widget.addTab(self.locations_tab, "Por Ubicación")
        
        # Tab 4: Movimientos
        self.movements_tab = self.create_movements_tab()
        self.tab_widget.addTab(self.movements_tab, "Movimientos")
        
        # Tab 5: Alertas
        self.alerts_tab = self.create_alerts_tab()
        self.tab_widget.addTab(self.alerts_tab, "Alertas")
        
        layout.addWidget(self.tab_widget)
    
    def create_dashboard_tab(self):
        """Crear tab de dashboard"""
        widget = QWidget()
        layout = QGridLayout(widget)
        
        # Métricas principales
        metrics_frame = QFrame()
        metrics_frame.setFrameStyle(QFrame.StyledPanel)
        metrics_layout = QGridLayout(metrics_frame)
        
        # Total de productos
        self.total_products_label = QLabel("0")
        self.total_products_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.total_products_label.setStyleSheet("color: #2196F3;")
        self.total_products_label.setAlignment(Qt.AlignCenter)
        
        products_label = QLabel("Total Productos")
        products_label.setAlignment(Qt.AlignCenter)
        
        metrics_layout.addWidget(self.total_products_label, 0, 0)
        metrics_layout.addWidget(products_label, 1, 0)
        
        # Valor total del stock
        self.stock_value_label = QLabel("$0")
        self.stock_value_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.stock_value_label.setStyleSheet("color: #4CAF50;")
        self.stock_value_label.setAlignment(Qt.AlignCenter)
        
        value_label = QLabel("Valor del Stock")
        value_label.setAlignment(Qt.AlignCenter)
        
        metrics_layout.addWidget(self.stock_value_label, 0, 1)
        metrics_layout.addWidget(value_label, 1, 1)
        
        # Productos con stock bajo
        self.low_stock_label = QLabel("0")
        self.low_stock_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.low_stock_label.setStyleSheet("color: #FF9800;")
        self.low_stock_label.setAlignment(Qt.AlignCenter)
        
        low_stock_label = QLabel("Stock Bajo")
        low_stock_label.setAlignment(Qt.AlignCenter)
        
        metrics_layout.addWidget(self.low_stock_label, 0, 2)
        metrics_layout.addWidget(low_stock_label, 1, 2)
        
        # Productos sin stock
        self.no_stock_label = QLabel("0")
        self.no_stock_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.no_stock_label.setStyleSheet("color: #F44336;")
        self.no_stock_label.setAlignment(Qt.AlignCenter)
        
        no_stock_label = QLabel("Sin Stock")
        no_stock_label.setAlignment(Qt.AlignCenter)
        
        metrics_layout.addWidget(self.no_stock_label, 0, 3)
        metrics_layout.addWidget(no_stock_label, 1, 3)
        
        layout.addWidget(metrics_frame, 0, 0, 1, 2)
        
        # Productos con stock crítico
        critical_group = QGroupBox("Stock Crítico")
        critical_layout = QVBoxLayout(critical_group)
        
        self.critical_stock_table = QTableWidget()
        self.critical_stock_table.setColumnCount(5)
        self.critical_stock_table.setHorizontalHeaderLabels([
            "Producto", "Stock Actual", "Stock Mínimo", "Ubicación", "Estado"
        ])
        self.critical_stock_table.horizontalHeader().setStretchLastSection(True)
        self.critical_stock_table.setAlternatingRowColors(True)
        self.critical_stock_table.setMaximumHeight(200)
        
        critical_layout.addWidget(self.critical_stock_table)
        layout.addWidget(critical_group, 1, 0)
        
        # Últimos movimientos
        movements_group = QGroupBox("Últimos Movimientos")
        movements_layout = QVBoxLayout(movements_group)
        
        self.recent_movements_table = QTableWidget()
        self.recent_movements_table.setColumnCount(5)
        self.recent_movements_table.setHorizontalHeaderLabels([
            "Fecha", "Producto", "Tipo", "Cantidad", "Usuario"
        ])
        self.recent_movements_table.horizontalHeader().setStretchLastSection(True)
        self.recent_movements_table.setAlternatingRowColors(True)
        self.recent_movements_table.setMaximumHeight(200)
        
        movements_layout.addWidget(self.recent_movements_table)
        layout.addWidget(movements_group, 1, 1)
        
        return widget
    
    def create_products_tab(self):
        """Crear tab de stock por producto"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filtros
        filters_layout = QHBoxLayout()
        
        self.search_line = QLineEdit()
        self.search_line.setPlaceholderText("Buscar producto...")
        filters_layout.addWidget(self.search_line)
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("Todas las Categorías")
        filters_layout.addWidget(self.category_combo)
        
        self.stock_status_combo = QComboBox()
        self.stock_status_combo.addItems([
            "Todos", "Con Stock", "Stock Bajo", "Sin Stock", "Stock Crítico"
        ])
        filters_layout.addWidget(self.stock_status_combo)
        
        layout.addLayout(filters_layout)
        
        # Tabla de productos con stock
        self.products_stock_table = QTableWidget()
        self.products_stock_table.setColumnCount(8)
        self.products_stock_table.setHorizontalHeaderLabels([
            "Código", "Producto", "Categoría", "Stock Actual", 
            "Stock Mínimo", "Valor Unitario", "Valor Total", "Estado"
        ])
        
        # Configurar tabla
        header = self.products_stock_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.resizeSection(0, 80)   # Código
        header.resizeSection(1, 200)  # Producto
        header.resizeSection(2, 120)  # Categoría
        header.resizeSection(3, 100)  # Stock actual
        header.resizeSection(4, 100)  # Stock mínimo
        header.resizeSection(5, 100)  # Valor unitario
        header.resizeSection(6, 100)  # Valor total
        
        self.products_stock_table.setAlternatingRowColors(True)
        self.products_stock_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.products_stock_table.setSortingEnabled(True)
        
        layout.addWidget(self.products_stock_table)
        
        return widget
    
    def create_locations_tab(self):
        """Crear tab de stock por ubicación"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Tree de ubicaciones
        self.locations_tree = QTreeWidget()
        self.locations_tree.setHeaderLabels(["Ubicación", "Productos", "Valor Total"])
        self.locations_tree.setMaximumWidth(300)
        layout.addWidget(self.locations_tree)
        
        # Detalle de ubicación seleccionada
        detail_layout = QVBoxLayout()
        
        # Header de detalle
        detail_header = QLabel("Seleccione una ubicación")
        detail_header.setFont(QFont("Arial", 14, QFont.Bold))
        detail_header.setAlignment(Qt.AlignCenter)
        detail_layout.addWidget(detail_header)
        
        # Tabla de productos en ubicación
        self.location_products_table = QTableWidget()
        self.location_products_table.setColumnCount(6)
        self.location_products_table.setHorizontalHeaderLabels([
            "Producto", "Cantidad", "Lote", "Vencimiento", "Valor Unit.", "Valor Total"
        ])
        self.location_products_table.horizontalHeader().setStretchLastSection(True)
        self.location_products_table.setAlternatingRowColors(True)
        
        detail_layout.addWidget(self.location_products_table)
        
        layout.addLayout(detail_layout)
        
        return widget
    
    def create_movements_tab(self):
        """Crear tab de movimientos de stock"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filtros de movimientos
        filters_layout = QHBoxLayout()
        
        self.movement_search = QLineEdit()
        self.movement_search.setPlaceholderText("Buscar en movimientos...")
        filters_layout.addWidget(self.movement_search)
        
        self.movement_type_combo = QComboBox()
        self.movement_type_combo.addItems([
            "Todos los Tipos", "Venta", "Compra", "Ajuste", "Transferencia", 
            "Devolución", "Inventario"
        ])
        filters_layout.addWidget(self.movement_type_combo)
        
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        filters_layout.addWidget(QLabel("Desde:"))
        filters_layout.addWidget(self.date_from)
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        filters_layout.addWidget(QLabel("Hasta:"))
        filters_layout.addWidget(self.date_to)
        
        layout.addLayout(filters_layout)
        
        # Tabla de movimientos
        self.movements_table = QTableWidget()
        self.movements_table.setColumnCount(8)
        self.movements_table.setHorizontalHeaderLabels([
            "Fecha", "Producto", "Tipo", "Cantidad", "Ubicación", 
            "Usuario", "Referencia", "Observaciones"
        ])
        
        header = self.movements_table.horizontalHeader()
        header.setStretchLastSection(True)
        self.movements_table.setAlternatingRowColors(True)
        self.movements_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.movements_table.setSortingEnabled(True)
        
        layout.addWidget(self.movements_table)
        
        return widget
    
    def create_alerts_tab(self):
        """Crear tab de alertas"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Configuración de alertas
        config_group = QGroupBox("Configuración de Alertas")
        config_layout = QGridLayout(config_group)
        
        self.enable_low_stock_alerts = QCheckBox("Alertas de stock bajo")
        self.enable_low_stock_alerts.setChecked(True)
        config_layout.addWidget(self.enable_low_stock_alerts, 0, 0)
        
        self.enable_expiry_alerts = QCheckBox("Alertas de vencimiento")
        self.enable_expiry_alerts.setChecked(True)
        config_layout.addWidget(self.enable_expiry_alerts, 0, 1)
        
        self.enable_overstock_alerts = QCheckBox("Alertas de sobrestock")
        config_layout.addWidget(self.enable_overstock_alerts, 1, 0)
        
        self.auto_reorder = QCheckBox("Reorden automático")
        config_layout.addWidget(self.auto_reorder, 1, 1)
        
        layout.addWidget(config_group)
        
        # Lista de alertas activas
        alerts_group = QGroupBox("Alertas Activas")
        alerts_layout = QVBoxLayout(alerts_group)
        
        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(6)
        self.alerts_table.setHorizontalHeaderLabels([
            "Prioridad", "Tipo", "Producto", "Descripción", "Fecha", "Estado"
        ])
        
        header = self.alerts_table.horizontalHeader()
        header.setStretchLastSection(True)
        self.alerts_table.setAlternatingRowColors(True)
        self.alerts_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        alerts_layout.addWidget(self.alerts_table)
        layout.addWidget(alerts_group)
        
        return widget
    
    def setup_connections(self):
        """Configurar conexiones de señales"""
        # Botones principales
        self.adjust_stock_btn.clicked.connect(self.adjust_stock)
        self.transfer_stock_btn.clicked.connect(self.transfer_stock)
        self.physical_inventory_btn.clicked.connect(self.physical_inventory)
        self.export_btn.clicked.connect(self.export_data)
        
        # Filtros
        self.search_line.textChanged.connect(self.filter_products)
        self.category_combo.currentTextChanged.connect(self.filter_products)
        self.stock_status_combo.currentTextChanged.connect(self.filter_products)
        
        # Movimientos
        self.movement_search.textChanged.connect(self.filter_movements)
        self.movement_type_combo.currentTextChanged.connect(self.filter_movements)
        self.date_from.dateChanged.connect(self.filter_movements)
        self.date_to.dateChanged.connect(self.filter_movements)
        
        # Ubicaciones
        self.locations_tree.itemSelectionChanged.connect(self.load_location_detail)
    
    def setup_timer(self):
        """Configurar timer para actualizaciones automáticas"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_data)
        self.update_timer.start(120000)  # Actualizar cada 2 minutos
    
    def load_data(self):
        """Cargar todos los datos"""
        self.load_dashboard_data()
        self.load_products_stock_data()
        self.load_locations_data()
        self.load_movements_data()
        self.load_alerts_data()
        self.load_categories()
    
    def load_dashboard_data(self):
        """Cargar datos del dashboard"""
        try:
            # Métricas principales
            total_products = self.product_manager.get_products_count()
            self.total_products_label.setText(str(total_products))
            
            stock_value = self.product_manager.get_total_stock_value()
            self.stock_value_label.setText(NumberFormatter.format_currency(stock_value))
            
            low_stock_count = self.product_manager.get_low_stock_count()
            self.low_stock_label.setText(str(low_stock_count))
            
            no_stock_count = self.product_manager.get_no_stock_count()
            self.no_stock_label.setText(str(no_stock_count))
            
            # Stock crítico
            self.load_critical_stock()
            
            # Movimientos recientes
            self.load_recent_movements()
            
        except Exception as e:
            logger.error(f"Error cargando dashboard: {e}")
    
    def load_critical_stock(self):
        """Cargar productos con stock crítico"""
        try:
            critical_products = self.product_manager.get_critical_stock_products()
            
            self.critical_stock_table.setRowCount(len(critical_products))
            
            for row, product in enumerate(critical_products):
                self.critical_stock_table.setItem(row, 0, QTableWidgetItem(product.get('nombre', '')))
                
                stock_actual = float(product.get('stock_actual', 0))
                stock_minimo = float(product.get('stock_minimo', 0))
                
                self.critical_stock_table.setItem(row, 1, QTableWidgetItem(f"{stock_actual:,.2f}"))
                self.critical_stock_table.setItem(row, 2, QTableWidgetItem(f"{stock_minimo:,.2f}"))
                self.critical_stock_table.setItem(row, 3, QTableWidgetItem(product.get('ubicacion', '')))
                
                # Estado con color
                if stock_actual <= 0:
                    estado = "Sin Stock"
                    color = "#F44336"
                elif stock_actual <= stock_minimo:
                    estado = "Stock Crítico"
                    color = "#FF9800"
                else:
                    estado = "Stock Bajo"
                    color = "#FFC107"
                
                estado_item = QTableWidgetItem(estado)
                estado_item.setBackground(QColor(color))
                self.critical_stock_table.setItem(row, 4, estado_item)
                
        except Exception as e:
            logger.error(f"Error cargando stock crítico: {e}")
    
    def load_recent_movements(self):
        """Cargar movimientos recientes"""
        try:
            recent_movements = self.product_manager.get_recent_stock_movements(limit=10)
            
            self.recent_movements_table.setRowCount(len(recent_movements))
            
            for row, movement in enumerate(recent_movements):
                fecha = movement.get('fecha')
                if fecha:
                    self.recent_movements_table.setItem(row, 0, 
                        QTableWidgetItem(DateFormatter.format_datetime(fecha))
                    )
                
                self.recent_movements_table.setItem(row, 1, 
                    QTableWidgetItem(movement.get('producto_nombre', ''))
                )
                self.recent_movements_table.setItem(row, 2, 
                    QTableWidgetItem(movement.get('tipo_movimiento', ''))
                )
                
                cantidad = movement.get('cantidad', 0)
                cantidad_text = f"{cantidad:+,.2f}"  # Con signo
                self.recent_movements_table.setItem(row, 3, QTableWidgetItem(cantidad_text))
                
                self.recent_movements_table.setItem(row, 4, 
                    QTableWidgetItem(movement.get('usuario_nombre', ''))
                )
                
        except Exception as e:
            logger.error(f"Error cargando movimientos recientes: {e}")
    
    def load_products_stock_data(self):
        """Cargar datos de stock por producto"""
        try:
            products_stock = self.product_manager.get_all_products_with_stock()
            
            self.products_stock_table.setRowCount(len(products_stock))
            
            for row, product in enumerate(products_stock):
                self.products_stock_table.setItem(row, 0, QTableWidgetItem(product.get('codigo', '')))
                self.products_stock_table.setItem(row, 1, QTableWidgetItem(product.get('nombre', '')))
                self.products_stock_table.setItem(row, 2, QTableWidgetItem(product.get('categoria', '')))
                
                stock_actual = float(product.get('stock_actual', 0))
                stock_minimo = float(product.get('stock_minimo', 0))
                precio_unitario = float(product.get('precio_unitario', 0))
                valor_total = stock_actual * precio_unitario
                
                self.products_stock_table.setItem(row, 3, QTableWidgetItem(f"{stock_actual:,.2f}"))
                self.products_stock_table.setItem(row, 4, QTableWidgetItem(f"{stock_minimo:,.2f}"))
                self.products_stock_table.setItem(row, 5, QTableWidgetItem(
                    NumberFormatter.format_currency(precio_unitario)
                ))
                self.products_stock_table.setItem(row, 6, QTableWidgetItem(
                    NumberFormatter.format_currency(valor_total)
                ))
                
                # Estado del stock
                estado_item = StatusFormatter.format_stock_status(stock_actual, stock_minimo)
                self.products_stock_table.setItem(row, 7, estado_item)
                
        except Exception as e:
            logger.error(f"Error cargando stock de productos: {e}")
    
    def load_locations_data(self):
        """Cargar datos de ubicaciones"""
        try:
            self.locations_tree.clear()
            
            locations = self.product_manager.get_stock_locations_summary()
            
            for location_data in locations:
                location_name = location_data.get('nombre', '')
                products_count = location_data.get('productos_count', 0)
                total_value = location_data.get('valor_total', 0)
                
                item = QTreeWidgetItem([
                    location_name, 
                    str(products_count), 
                    NumberFormatter.format_currency(total_value)
                ])
                item.setData(0, Qt.UserRole, location_data)
                
                self.locations_tree.addTopLevelItem(item)
                
        except Exception as e:
            logger.error(f"Error cargando ubicaciones: {e}")
    
    def load_location_detail(self):
        """Cargar detalle de ubicación seleccionada"""
        try:
            selected_items = self.locations_tree.selectedItems()
            if not selected_items:
                return
            
            item = selected_items[0]
            location_data = item.data(0, Qt.UserRole)
            location_name = location_data.get('nombre', '')
            
            # Cargar productos en la ubicación
            products = self.product_manager.get_products_in_location(location_name)
            
            self.location_products_table.setRowCount(len(products))
            
            for row, product in enumerate(products):
                self.location_products_table.setItem(row, 0, 
                    QTableWidgetItem(product.get('nombre', ''))
                )
                
                cantidad = float(product.get('cantidad', 0))
                self.location_products_table.setItem(row, 1, 
                    QTableWidgetItem(f"{cantidad:,.2f}")
                )
                
                self.location_products_table.setItem(row, 2, 
                    QTableWidgetItem(product.get('lote', ''))
                )
                
                vencimiento = product.get('fecha_vencimiento')
                if vencimiento:
                    self.location_products_table.setItem(row, 3, 
                        QTableWidgetItem(DateFormatter.format_date(vencimiento))
                    )
                
                precio_unit = float(product.get('precio_unitario', 0))
                valor_total = cantidad * precio_unit
                
                self.location_products_table.setItem(row, 4, 
                    QTableWidgetItem(NumberFormatter.format_currency(precio_unit))
                )
                self.location_products_table.setItem(row, 5, 
                    QTableWidgetItem(NumberFormatter.format_currency(valor_total))
                )
                
        except Exception as e:
            logger.error(f"Error cargando detalle de ubicación: {e}")
    
    def load_movements_data(self):
        """Cargar datos de movimientos"""
        try:
            date_from = self.date_from.date().toPyDate()
            date_to = self.date_to.date().toPyDate()
            
            movements = self.product_manager.get_stock_movements(date_from, date_to)
            
            self.movements_table.setRowCount(len(movements))
            
            for row, movement in enumerate(movements):
                fecha = movement.get('fecha')
                if fecha:
                    self.movements_table.setItem(row, 0, 
                        QTableWidgetItem(DateFormatter.format_datetime(fecha))
                    )
                
                self.movements_table.setItem(row, 1, 
                    QTableWidgetItem(movement.get('producto_nombre', ''))
                )
                self.movements_table.setItem(row, 2, 
                    QTableWidgetItem(movement.get('tipo_movimiento', ''))
                )
                
                cantidad = movement.get('cantidad', 0)
                cantidad_text = f"{cantidad:+,.2f}"
                self.movements_table.setItem(row, 3, QTableWidgetItem(cantidad_text))
                
                self.movements_table.setItem(row, 4, 
                    QTableWidgetItem(movement.get('ubicacion', ''))
                )
                self.movements_table.setItem(row, 5, 
                    QTableWidgetItem(movement.get('usuario_nombre', ''))
                )
                self.movements_table.setItem(row, 6, 
                    QTableWidgetItem(movement.get('referencia', ''))
                )
                self.movements_table.setItem(row, 7, 
                    QTableWidgetItem(movement.get('observaciones', ''))
                )
                
        except Exception as e:
            logger.error(f"Error cargando movimientos: {e}")
    
    def load_alerts_data(self):
        """Cargar datos de alertas"""
        try:
            alerts = self.product_manager.get_stock_alerts()
            
            self.alerts_table.setRowCount(len(alerts))
            
            for row, alert in enumerate(alerts):
                # Prioridad con color
                prioridad = alert.get('prioridad', 'Media')
                prioridad_item = QTableWidgetItem(prioridad)
                
                if prioridad == 'Alta':
                    prioridad_item.setBackground(QColor("#F44336"))
                elif prioridad == 'Media':
                    prioridad_item.setBackground(QColor("#FF9800"))
                else:
                    prioridad_item.setBackground(QColor("#FFC107"))
                
                self.alerts_table.setItem(row, 0, prioridad_item)
                
                self.alerts_table.setItem(row, 1, QTableWidgetItem(alert.get('tipo', '')))
                self.alerts_table.setItem(row, 2, QTableWidgetItem(alert.get('producto_nombre', '')))
                self.alerts_table.setItem(row, 3, QTableWidgetItem(alert.get('descripcion', '')))
                
                fecha = alert.get('fecha_creacion')
                if fecha:
                    self.alerts_table.setItem(row, 4, 
                        QTableWidgetItem(DateFormatter.format_datetime(fecha))
                    )
                
                estado = alert.get('estado', 'Activa')
                estado_item = QTableWidgetItem(estado)
                if estado == 'Activa':
                    estado_item.setBackground(QColor("#4CAF50"))
                else:
                    estado_item.setBackground(QColor("#9E9E9E"))
                
                self.alerts_table.setItem(row, 5, estado_item)
                
        except Exception as e:
            logger.error(f"Error cargando alertas: {e}")
    
    def load_categories(self):
        """Cargar categorías para filtro"""
        try:
            categories = self.product_manager.get_product_categories()
            
            self.category_combo.clear()
            self.category_combo.addItem("Todas las Categorías")
            self.category_combo.addItems(categories)
            
        except Exception as e:
            logger.error(f"Error cargando categorías: {e}")
    
    def filter_products(self):
        """Filtrar productos según criterios"""
        search_text = self.search_line.text().lower()
        category_filter = self.category_combo.currentText()
        status_filter = self.stock_status_combo.currentText()
        
        for row in range(self.products_stock_table.rowCount()):
            show_row = True
            
            # Filtro por búsqueda
            if search_text:
                nombre = self.products_stock_table.item(row, 1).text().lower()
                codigo = self.products_stock_table.item(row, 0).text().lower()
                if search_text not in nombre and search_text not in codigo:
                    show_row = False
            
            # Filtro por categoría
            if category_filter != "Todas las Categorías":
                categoria = self.products_stock_table.item(row, 2).text()
                if categoria != category_filter:
                    show_row = False
            
            # Filtro por estado de stock
            if status_filter != "Todos":
                estado = self.products_stock_table.item(row, 7).text()
                if status_filter == "Con Stock" and "Sin Stock" in estado:
                    show_row = False
                elif status_filter == "Stock Bajo" and "Stock Bajo" not in estado:
                    show_row = False
                elif status_filter == "Sin Stock" and "Sin Stock" not in estado:
                    show_row = False
                elif status_filter == "Stock Crítico" and "Crítico" not in estado:
                    show_row = False
            
            self.products_stock_table.setRowHidden(row, not show_row)
    
    def filter_movements(self):
        """Filtrar movimientos según criterios"""
        search_text = self.movement_search.text().lower()
        type_filter = self.movement_type_combo.currentText()
        
        for row in range(self.movements_table.rowCount()):
            show_row = True
            
            # Filtro por búsqueda
            if search_text:
                producto = self.movements_table.item(row, 1).text().lower()
                if search_text not in producto:
                    show_row = False
            
            # Filtro por tipo
            if type_filter != "Todos los Tipos":
                tipo = self.movements_table.item(row, 2).text()
                if type_filter not in tipo:
                    show_row = False
            
            self.movements_table.setRowHidden(row, not show_row)
    
    def adjust_stock(self):
        """Ajustar stock de productos"""
        try:
            if not self.user_manager:
                QMessageBox.warning(self, "Advertencia", 
                    "Sistema de usuarios no disponible para autorización.")
                return
            
            dialog = StockAdjustmentDialog(self.product_manager, self.user_manager, parent=self)
            if dialog.exec_() == QDialog.Accepted:
                adjustment_data = dialog.get_adjustment_data()
                
                # Validar autorización
                if not self.validate_authorization(adjustment_data):
                    QMessageBox.warning(self, "Advertencia", "Autorización inválida.")
                    return
                
                # Procesar ajuste
                success = self.product_manager.process_stock_adjustment(adjustment_data)
                if success:
                    QMessageBox.information(self, "Éxito", "Ajuste de stock procesado correctamente.")
                    self.refresh_data()
                    self.stock_updated.emit()
                else:
                    QMessageBox.warning(self, "Advertencia", "Error procesando ajuste de stock.")
                    
        except Exception as e:
            logger.error(f"Error en ajuste de stock: {e}")
            QMessageBox.critical(self, "Error", f"Error en ajuste de stock: {str(e)}")
    
    def transfer_stock(self):
        """Transferir stock entre ubicaciones"""
        try:
            dialog = StockTransferDialog(self.product_manager, parent=self)
            if dialog.exec_() == QDialog.Accepted:
                transfer_data = dialog.get_transfer_data()
                
                if not transfer_data['products']:
                    QMessageBox.warning(self, "Advertencia", "Debe agregar al menos un producto.")
                    return
                
                # Procesar transferencia
                success = self.product_manager.process_stock_transfer(transfer_data)
                if success:
                    QMessageBox.information(self, "Éxito", "Transferencia procesada correctamente.")
                    self.refresh_data()
                    self.stock_updated.emit()
                else:
                    QMessageBox.warning(self, "Advertencia", "Error procesando transferencia.")
                    
        except Exception as e:
            logger.error(f"Error en transferencia: {e}")
            QMessageBox.critical(self, "Error", f"Error en transferencia: {str(e)}")
    
    def physical_inventory(self):
        """Realizar inventario físico"""
        try:
            reply = QMessageBox.question(self, "Inventario Físico", 
                "¿Desea iniciar un inventario físico completo?\n\n"
                "Esto generará un reporte de diferencias entre el stock del sistema "
                "y el stock físico contado.",
                QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                QMessageBox.information(self, "Información", 
                    "Funcionalidad de inventario físico disponible próximamente.\n\n"
                    "Permitirá:\n"
                    "• Generar listas de conteo por ubicación\n"
                    "• Registrar conteos físicos\n"
                    "• Generar reportes de diferencias\n"
                    "• Ajustar stocks automáticamente")
                    
        except Exception as e:
            logger.error(f"Error en inventario físico: {e}")
            QMessageBox.critical(self, "Error", f"Error en inventario físico: {str(e)}")
    
    def validate_authorization(self, adjustment_data):
        """Validar autorización del ajuste"""
        try:
            auth_user_id = adjustment_data.get('authorized_by')
            auth_password = adjustment_data.get('auth_password')
            
            if not auth_user_id or not auth_password:
                return False
            
            return self.user_manager.validate_user_password(auth_user_id, auth_password)
            
        except Exception as e:
            logger.error(f"Error validando autorización: {e}")
            return False
    
    def export_data(self):
        """Exportar datos de stock"""
        try:
            from PyQt5.QtWidgets import QMenu
            from PyQt5.QtCore import QPoint
            
            menu = QMenu(self)
            menu.addAction("Exportar Stock por Producto", lambda: self._export_stock_data('products'))
            menu.addAction("Exportar Movimientos", lambda: self._export_stock_data('movements'))
            menu.addAction("Exportar Alertas", lambda: self._export_stock_data('alerts'))
            
            button_pos = self.export_btn.mapToGlobal(QPoint(0, self.export_btn.height()))
            menu.exec_(button_pos)
            
        except Exception as e:
            logger.error(f"Error exportando: {e}")
            QMessageBox.critical(self, "Error", f"Error exportando: {str(e)}")
    
    def _export_stock_data(self, data_type):
        """Exportar datos específicos"""
        try:
            if data_type == 'products':
                table = self.products_stock_table
                title = "Stock por Producto"
            elif data_type == 'movements':
                table = self.movements_table
                title = "Movimientos de Stock"
            else:  # alerts
                table = self.alerts_table
                title = "Alertas de Stock"
            
            # Obtener datos
            data = []
            headers = []
            
            for col in range(table.columnCount()):
                headers.append(table.horizontalHeaderItem(col).text())
            
            for row in range(table.rowCount()):
                if not table.isRowHidden(row):
                    row_data = []
                    for col in range(table.columnCount()):
                        item = table.item(row, col)
                        row_data.append(item.text() if item else "")
                    data.append(row_data)
            
            filename = f"stock_{data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            exporter = ExcelExporter()
            success = exporter.export_table_data(data, headers, filename, title)
            
            if success:
                QMessageBox.information(self, "Éxito", f"Datos exportados a {filename}")
            else:
                QMessageBox.warning(self, "Advertencia", "Error exportando datos")
                
        except Exception as e:
            logger.error(f"Error exportando {data_type}: {e}")
            QMessageBox.critical(self, "Error", f"Error exportando {data_type}: {str(e)}")
    
    def refresh_data(self):
        """Refrescar todos los datos"""
        self.load_data()
        self.stock_updated.emit()