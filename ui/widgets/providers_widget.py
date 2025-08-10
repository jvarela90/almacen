"""
Widget de Gestión de Proveedores Mejorada - AlmacénPro v2.0
Sistema completo de gestión de proveedores con dashboard y análisis
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from decimal import Decimal

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QDateEdit,
    QCheckBox, QGroupBox, QSplitter, QFrame, QProgressBar,
    QHeaderView, QMessageBox, QDialog, QDialogButtonBox,
    QCalendarWidget, QSlider, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QDate, QThread, pyqtSignal as Signal
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QIcon

from ...utils.formatters import NumberFormatter, DateFormatter, TextFormatter, StatusFormatter
from ...utils.exporters import ExcelExporter, PDFExporter, CSVExporter

logger = logging.getLogger(__name__)

class ProviderPerformanceDialog(QDialog):
    """Diálogo para evaluar performance de proveedores"""
    
    def __init__(self, provider_manager, provider_id=None, parent=None):
        super().__init__(parent)
        self.provider_manager = provider_manager
        self.provider_id = provider_id
        self.setWindowTitle("Evaluación de Performance - Proveedor")
        self.setModal(True)
        self.resize(800, 600)
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Información del proveedor
        info_group = QGroupBox("Información del Proveedor")
        info_layout = QGridLayout(info_group)
        
        self.provider_label = QLabel()
        self.provider_label.setFont(QFont("Arial", 12, QFont.Bold))
        info_layout.addWidget(QLabel("Proveedor:"), 0, 0)
        info_layout.addWidget(self.provider_label, 0, 1)
        
        # Métricas de performance
        metrics_group = QGroupBox("Métricas de Performance")
        metrics_layout = QGridLayout(metrics_group)
        
        # Calidad de entrega
        metrics_layout.addWidget(QLabel("Calidad de Entrega:"), 0, 0)
        self.delivery_quality = QSlider(Qt.Horizontal)
        self.delivery_quality.setRange(0, 100)
        self.delivery_quality.setValue(85)
        self.delivery_quality_label = QLabel("85%")
        self.delivery_quality.valueChanged.connect(
            lambda v: self.delivery_quality_label.setText(f"{v}%")
        )
        metrics_layout.addWidget(self.delivery_quality, 0, 1)
        metrics_layout.addWidget(self.delivery_quality_label, 0, 2)
        
        # Puntualidad
        metrics_layout.addWidget(QLabel("Puntualidad:"), 1, 0)
        self.punctuality = QSlider(Qt.Horizontal)
        self.punctuality.setRange(0, 100)
        self.punctuality.setValue(90)
        self.punctuality_label = QLabel("90%")
        self.punctuality.valueChanged.connect(
            lambda v: self.punctuality_label.setText(f"{v}%")
        )
        metrics_layout.addWidget(self.punctuality, 1, 1)
        metrics_layout.addWidget(self.punctuality_label, 1, 2)
        
        # Competitividad de precios
        metrics_layout.addWidget(QLabel("Competitividad Precios:"), 2, 0)
        self.price_competitiveness = QSlider(Qt.Horizontal)
        self.price_competitiveness.setRange(0, 100)
        self.price_competitiveness.setValue(75)
        self.price_competitiveness_label = QLabel("75%")
        self.price_competitiveness.valueChanged.connect(
            lambda v: self.price_competitiveness_label.setText(f"{v}%")
        )
        metrics_layout.addWidget(self.price_competitiveness, 2, 1)
        metrics_layout.addWidget(self.price_competitiveness_label, 2, 2)
        
        # Calidad del producto
        metrics_layout.addWidget(QLabel("Calidad Producto:"), 3, 0)
        self.product_quality = QSlider(Qt.Horizontal)
        self.product_quality.setRange(0, 100)
        self.product_quality.setValue(88)
        self.product_quality_label = QLabel("88%")
        self.product_quality.valueChanged.connect(
            lambda v: self.product_quality_label.setText(f"{v}%")
        )
        metrics_layout.addWidget(self.product_quality, 3, 1)
        metrics_layout.addWidget(self.product_quality_label, 3, 2)
        
        # Servicio al cliente
        metrics_layout.addWidget(QLabel("Servicio al Cliente:"), 4, 0)
        self.customer_service = QSlider(Qt.Horizontal)
        self.customer_service.setRange(0, 100)
        self.customer_service.setValue(82)
        self.customer_service_label = QLabel("82%")
        self.customer_service.valueChanged.connect(
            lambda v: self.customer_service_label.setText(f"{v}%")
        )
        metrics_layout.addWidget(self.customer_service, 4, 1)
        metrics_layout.addWidget(self.customer_service_label, 4, 2)
        
        # Score general calculado
        self.general_score_label = QLabel()
        self.general_score_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.general_score_label.setStyleSheet("color: #2196F3; padding: 10px;")
        metrics_layout.addWidget(QLabel("Score General:"), 5, 0)
        metrics_layout.addWidget(self.general_score_label, 5, 1, 1, 2)
        
        # Conectar cambios para actualizar score general
        for slider in [self.delivery_quality, self.punctuality, self.price_competitiveness, 
                      self.product_quality, self.customer_service]:
            slider.valueChanged.connect(self.update_general_score)
        
        # Comentarios
        comments_group = QGroupBox("Comentarios y Observaciones")
        comments_layout = QVBoxLayout(comments_group)
        
        self.comments = QTextEdit()
        self.comments.setPlaceholderText("Ingrese comentarios sobre el proveedor...")
        comments_layout.addWidget(self.comments)
        
        # Botones
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Layout principal
        layout.addWidget(info_group)
        layout.addWidget(metrics_group)
        layout.addWidget(comments_group)
        layout.addWidget(button_box)
        
        # Actualizar score inicial
        self.update_general_score()
    
    def update_general_score(self):
        """Actualizar score general basado en métricas"""
        scores = [
            self.delivery_quality.value(),
            self.punctuality.value(), 
            self.price_competitiveness.value(),
            self.product_quality.value(),
            self.customer_service.value()
        ]
        
        general_score = sum(scores) / len(scores)
        self.general_score_label.setText(f"{general_score:.1f}%")
        
        # Cambiar color según score
        if general_score >= 90:
            color = "#4CAF50"  # Verde
        elif general_score >= 80:
            color = "#FF9800"  # Naranja
        elif general_score >= 70:
            color = "#FFC107"  # Amarillo
        else:
            color = "#F44336"  # Rojo
            
        self.general_score_label.setStyleSheet(f"color: {color}; padding: 10px; font-weight: bold;")
    
    def load_data(self):
        """Cargar datos del proveedor"""
        if self.provider_id:
            try:
                provider = self.provider_manager.get_provider_by_id(self.provider_id)
                if provider:
                    self.provider_label.setText(provider.get('nombre', 'N/A'))
                    
                    # Cargar evaluación existente si existe
                    evaluation = self.provider_manager.get_provider_evaluation(self.provider_id)
                    if evaluation:
                        self.delivery_quality.setValue(evaluation.get('delivery_quality', 85))
                        self.punctuality.setValue(evaluation.get('punctuality', 90))
                        self.price_competitiveness.setValue(evaluation.get('price_competitiveness', 75))
                        self.product_quality.setValue(evaluation.get('product_quality', 88))
                        self.customer_service.setValue(evaluation.get('customer_service', 82))
                        self.comments.setText(evaluation.get('comments', ''))
                        
            except Exception as e:
                logger.error(f"Error cargando datos del proveedor: {e}")
    
    def get_evaluation_data(self):
        """Obtener datos de evaluación"""
        return {
            'provider_id': self.provider_id,
            'delivery_quality': self.delivery_quality.value(),
            'punctuality': self.punctuality.value(),
            'price_competitiveness': self.price_competitiveness.value(),
            'product_quality': self.product_quality.value(),
            'customer_service': self.customer_service.value(),
            'general_score': sum([
                self.delivery_quality.value(),
                self.punctuality.value(),
                self.price_competitiveness.value(),
                self.product_quality.value(),
                self.customer_service.value()
            ]) / 5,
            'comments': self.comments.toPlainText(),
            'evaluation_date': datetime.now()
        }

class ProvidersWidget(QWidget):
    """Widget mejorado de gestión de proveedores"""
    
    # Señales
    provider_selected = pyqtSignal(dict)
    provider_updated = pyqtSignal()
    
    def __init__(self, provider_manager, purchase_manager=None, parent=None):
        super().__init__(parent)
        self.provider_manager = provider_manager
        self.purchase_manager = purchase_manager
        self.current_provider_id = None
        
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
        
        title_label = QLabel("Gestión de Proveedores")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet("color: #2196F3; margin-bottom: 10px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Botones principales
        self.add_btn = QPushButton("Agregar Proveedor")
        self.add_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px 16px; border-radius: 4px; }")
        
        self.edit_btn = QPushButton("Editar")
        self.edit_btn.setEnabled(False)
        self.edit_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 8px 16px; border-radius: 4px; }")
        
        self.evaluate_btn = QPushButton("Evaluar Performance")
        self.evaluate_btn.setEnabled(False)
        self.evaluate_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; padding: 8px 16px; border-radius: 4px; }")
        
        self.export_btn = QPushButton("Exportar")
        self.export_btn.setStyleSheet("QPushButton { background-color: #9C27B0; color: white; padding: 8px 16px; border-radius: 4px; }")
        
        header_layout.addWidget(self.add_btn)
        header_layout.addWidget(self.edit_btn)
        header_layout.addWidget(self.evaluate_btn)
        header_layout.addWidget(self.export_btn)
        
        layout.addLayout(header_layout)
        
        # Crear tabs principales
        self.tab_widget = QTabWidget()
        
        # Tab 1: Dashboard
        self.dashboard_tab = self.create_dashboard_tab()
        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
        
        # Tab 2: Lista de Proveedores
        self.providers_tab = self.create_providers_tab()
        self.tab_widget.addTab(self.providers_tab, "Proveedores")
        
        # Tab 3: Análisis de Performance
        self.performance_tab = self.create_performance_tab()
        self.tab_widget.addTab(self.performance_tab, "Performance")
        
        # Tab 4: Condiciones Comerciales
        self.conditions_tab = self.create_conditions_tab()
        self.tab_widget.addTab(self.conditions_tab, "Condiciones")
        
        layout.addWidget(self.tab_widget)
    
    def create_dashboard_tab(self):
        """Crear tab de dashboard"""
        widget = QWidget()
        layout = QGridLayout(widget)
        
        # Métricas principales
        metrics_frame = QFrame()
        metrics_frame.setFrameStyle(QFrame.StyledPanel)
        metrics_layout = QGridLayout(metrics_frame)
        
        # Total de proveedores
        self.total_providers_label = QLabel("0")
        self.total_providers_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.total_providers_label.setStyleSheet("color: #2196F3;")
        self.total_providers_label.setAlignment(Qt.AlignCenter)
        
        total_label = QLabel("Proveedores Totales")
        total_label.setAlignment(Qt.AlignCenter)
        
        metrics_layout.addWidget(self.total_providers_label, 0, 0)
        metrics_layout.addWidget(total_label, 1, 0)
        
        # Proveedores activos
        self.active_providers_label = QLabel("0")
        self.active_providers_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.active_providers_label.setStyleSheet("color: #4CAF50;")
        self.active_providers_label.setAlignment(Qt.AlignCenter)
        
        active_label = QLabel("Activos")
        active_label.setAlignment(Qt.AlignCenter)
        
        metrics_layout.addWidget(self.active_providers_label, 0, 1)
        metrics_layout.addWidget(active_label, 1, 1)
        
        # Compras este mes
        self.monthly_purchases_label = QLabel("$0")
        self.monthly_purchases_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.monthly_purchases_label.setStyleSheet("color: #FF9800;")
        self.monthly_purchases_label.setAlignment(Qt.AlignCenter)
        
        monthly_label = QLabel("Compras del Mes")
        monthly_label.setAlignment(Qt.AlignCenter)
        
        metrics_layout.addWidget(self.monthly_purchases_label, 0, 2)
        metrics_layout.addWidget(monthly_label, 1, 2)
        
        # Score promedio
        self.avg_score_label = QLabel("0%")
        self.avg_score_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.avg_score_label.setStyleSheet("color: #9C27B0;")
        self.avg_score_label.setAlignment(Qt.AlignCenter)
        
        score_label = QLabel("Score Promedio")
        score_label.setAlignment(Qt.AlignCenter)
        
        metrics_layout.addWidget(self.avg_score_label, 0, 3)
        metrics_layout.addWidget(score_label, 1, 3)
        
        layout.addWidget(metrics_frame, 0, 0, 1, 2)
        
        # Top proveedores por compras
        top_providers_group = QGroupBox("Top Proveedores por Compras")
        top_providers_layout = QVBoxLayout(top_providers_group)
        
        self.top_providers_table = QTableWidget()
        self.top_providers_table.setColumnCount(4)
        self.top_providers_table.setHorizontalHeaderLabels([
            "Proveedor", "Compras", "Monto Total", "Score"
        ])
        self.top_providers_table.horizontalHeader().setStretchLastSection(True)
        self.top_providers_table.setAlternatingRowColors(True)
        self.top_providers_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        top_providers_layout.addWidget(self.top_providers_table)
        layout.addWidget(top_providers_group, 1, 0)
        
        # Alertas y vencimientos
        alerts_group = QGroupBox("Alertas y Vencimientos")
        alerts_layout = QVBoxLayout(alerts_group)
        
        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(3)
        self.alerts_table.setHorizontalHeaderLabels([
            "Tipo", "Proveedor", "Vencimiento"
        ])
        self.alerts_table.horizontalHeader().setStretchLastSection(True)
        self.alerts_table.setAlternatingRowColors(True)
        
        alerts_layout.addWidget(self.alerts_table)
        layout.addWidget(alerts_group, 1, 1)
        
        return widget
    
    def create_providers_tab(self):
        """Crear tab de lista de proveedores"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filtros
        filters_layout = QHBoxLayout()
        
        self.search_line = QLineEdit()
        self.search_line.setPlaceholderText("Buscar proveedor...")
        filters_layout.addWidget(self.search_line)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Todos", "Activos", "Inactivos"])
        filters_layout.addWidget(self.status_combo)
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("Todas las Categorías")
        filters_layout.addWidget(self.category_combo)
        
        layout.addLayout(filters_layout)
        
        # Tabla de proveedores
        self.providers_table = QTableWidget()
        self.providers_table.setColumnCount(8)
        self.providers_table.setHorizontalHeaderLabels([
            "ID", "Nombre", "Categoría", "Email", "Teléfono", 
            "Estado", "Última Compra", "Score"
        ])
        
        # Configurar tabla
        header = self.providers_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.resizeSection(0, 60)  # ID
        header.resizeSection(1, 200) # Nombre
        header.resizeSection(2, 120) # Categoría
        header.resizeSection(3, 180) # Email
        header.resizeSection(4, 120) # Teléfono
        header.resizeSection(5, 80)  # Estado
        header.resizeSection(6, 100) # Última compra
        
        self.providers_table.setAlternatingRowColors(True)
        self.providers_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.providers_table.setSortingEnabled(True)
        
        layout.addWidget(self.providers_table)
        
        return widget
    
    def create_performance_tab(self):
        """Crear tab de análisis de performance"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Controles de filtro
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Período:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems([
            "Últimos 30 días", "Últimos 3 meses", 
            "Últimos 6 meses", "Último año"
        ])
        controls_layout.addWidget(self.period_combo)
        
        controls_layout.addStretch()
        
        self.refresh_performance_btn = QPushButton("Actualizar")
        controls_layout.addWidget(self.refresh_performance_btn)
        
        layout.addLayout(controls_layout)
        
        # Tabla de performance
        self.performance_table = QTableWidget()
        self.performance_table.setColumnCount(8)
        self.performance_table.setHorizontalHeaderLabels([
            "Proveedor", "Entregas", "Puntualidad", "Precio", 
            "Calidad", "Servicio", "Score General", "Última Eval."
        ])
        
        header = self.performance_table.horizontalHeader()
        header.setStretchLastSection(True)
        self.performance_table.setAlternatingRowColors(True)
        self.performance_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.performance_table.setSortingEnabled(True)
        
        layout.addWidget(self.performance_table)
        
        return widget
    
    def create_conditions_tab(self):
        """Crear tab de condiciones comerciales"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Selector de proveedor
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Proveedor:"))
        
        self.conditions_provider_combo = QComboBox()
        selector_layout.addWidget(self.conditions_provider_combo)
        
        selector_layout.addStretch()
        
        self.save_conditions_btn = QPushButton("Guardar Condiciones")
        self.save_conditions_btn.setEnabled(False)
        selector_layout.addWidget(self.save_conditions_btn)
        
        layout.addLayout(selector_layout)
        
        # Formulario de condiciones
        conditions_scroll = QScrollArea()
        conditions_widget = QWidget()
        conditions_layout = QGridLayout(conditions_widget)
        
        # Condiciones de pago
        payment_group = QGroupBox("Condiciones de Pago")
        payment_layout = QGridLayout(payment_group)
        
        payment_layout.addWidget(QLabel("Días de Pago:"), 0, 0)
        self.payment_days = QSpinBox()
        self.payment_days.setRange(0, 365)
        self.payment_days.setValue(30)
        payment_layout.addWidget(self.payment_days, 0, 1)
        
        payment_layout.addWidget(QLabel("Descuento Pronto Pago:"), 1, 0)
        self.early_payment_discount = QDoubleSpinBox()
        self.early_payment_discount.setRange(0, 100)
        self.early_payment_discount.setSuffix("%")
        payment_layout.addWidget(self.early_payment_discount, 1, 1)
        
        payment_layout.addWidget(QLabel("Moneda:"), 2, 0)
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["ARS", "USD", "EUR"])
        payment_layout.addWidget(self.currency_combo, 2, 1)
        
        conditions_layout.addWidget(payment_group, 0, 0)
        
        # Condiciones de entrega
        delivery_group = QGroupBox("Condiciones de Entrega")
        delivery_layout = QGridLayout(delivery_group)
        
        delivery_layout.addWidget(QLabel("Tiempo de Entrega:"), 0, 0)
        self.delivery_time = QSpinBox()
        self.delivery_time.setRange(1, 365)
        self.delivery_time.setValue(7)
        self.delivery_time.setSuffix(" días")
        delivery_layout.addWidget(self.delivery_time, 0, 1)
        
        delivery_layout.addWidget(QLabel("Pedido Mínimo:"), 1, 0)
        self.minimum_order = QDoubleSpinBox()
        self.minimum_order.setRange(0, 999999)
        self.minimum_order.setPrefix("$")
        delivery_layout.addWidget(self.minimum_order, 1, 1)
        
        delivery_layout.addWidget(QLabel("Costo de Envío:"), 2, 0)
        self.shipping_cost = QDoubleSpinBox()
        self.shipping_cost.setRange(0, 999999)
        self.shipping_cost.setPrefix("$")
        delivery_layout.addWidget(self.shipping_cost, 2, 1)
        
        conditions_layout.addWidget(delivery_group, 0, 1)
        
        # Términos especiales
        terms_group = QGroupBox("Términos Especiales")
        terms_layout = QVBoxLayout(terms_group)
        
        self.special_terms = QTextEdit()
        self.special_terms.setMaximumHeight(150)
        self.special_terms.setPlaceholderText("Términos y condiciones especiales...")
        terms_layout.addWidget(self.special_terms)
        
        conditions_layout.addWidget(terms_group, 1, 0, 1, 2)
        
        # Contratos vigentes
        contracts_group = QGroupBox("Contratos Vigentes")
        contracts_layout = QVBoxLayout(contracts_group)
        
        self.contracts_table = QTableWidget()
        self.contracts_table.setColumnCount(5)
        self.contracts_table.setHorizontalHeaderLabels([
            "Tipo", "Fecha Inicio", "Fecha Vencimiento", "Estado", "Acciones"
        ])
        self.contracts_table.setMaximumHeight(200)
        contracts_layout.addWidget(self.contracts_table)
        
        conditions_layout.addWidget(contracts_group, 2, 0, 1, 2)
        
        conditions_scroll.setWidget(conditions_widget)
        conditions_scroll.setWidgetResizable(True)
        layout.addWidget(conditions_scroll)
        
        return widget
    
    def setup_connections(self):
        """Configurar conexiones de señales"""
        # Botones principales
        self.add_btn.clicked.connect(self.add_provider)
        self.edit_btn.clicked.connect(self.edit_provider)
        self.evaluate_btn.clicked.connect(self.evaluate_provider)
        self.export_btn.clicked.connect(self.export_data)
        
        # Tabla de proveedores
        self.providers_table.selectionModel().selectionChanged.connect(
            self.on_provider_selection_changed
        )
        
        # Filtros
        self.search_line.textChanged.connect(self.filter_providers)
        self.status_combo.currentTextChanged.connect(self.filter_providers)
        self.category_combo.currentTextChanged.connect(self.filter_providers)
        
        # Performance
        self.refresh_performance_btn.clicked.connect(self.load_performance_data)
        self.period_combo.currentTextChanged.connect(self.load_performance_data)
        
        # Condiciones
        self.conditions_provider_combo.currentTextChanged.connect(self.load_provider_conditions)
        self.save_conditions_btn.clicked.connect(self.save_provider_conditions)
    
    def setup_timer(self):
        """Configurar timer para actualizaciones automáticas"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_data)
        self.update_timer.start(60000)  # Actualizar cada minuto
    
    def load_data(self):
        """Cargar todos los datos"""
        self.load_dashboard_data()
        self.load_providers_data()
        self.load_performance_data()
        self.load_categories()
        self.load_providers_combo()
    
    def load_dashboard_data(self):
        """Cargar datos del dashboard"""
        try:
            # Métricas principales
            total_providers = self.provider_manager.get_providers_count()
            active_providers = self.provider_manager.get_active_providers_count()
            
            self.total_providers_label.setText(str(total_providers))
            self.active_providers_label.setText(str(active_providers))
            
            # Compras del mes
            if self.purchase_manager:
                monthly_amount = self.purchase_manager.get_monthly_purchase_amount()
                self.monthly_purchases_label.setText(
                    NumberFormatter.format_currency(monthly_amount)
                )
            
            # Score promedio
            avg_score = self.provider_manager.get_average_provider_score()
            self.avg_score_label.setText(f"{avg_score:.1f}%")
            
            # Top proveedores
            self.load_top_providers()
            
            # Alertas
            self.load_alerts()
            
        except Exception as e:
            logger.error(f"Error cargando dashboard: {e}")
    
    def load_top_providers(self):
        """Cargar top proveedores"""
        try:
            top_providers = self.provider_manager.get_top_providers_by_purchases(limit=10)
            
            self.top_providers_table.setRowCount(len(top_providers))
            
            for row, provider in enumerate(top_providers):
                self.top_providers_table.setItem(row, 0, QTableWidgetItem(provider.get('nombre', '')))
                self.top_providers_table.setItem(row, 1, QTableWidgetItem(str(provider.get('total_purchases', 0))))
                
                amount = float(provider.get('total_amount', 0))
                self.top_providers_table.setItem(row, 2, QTableWidgetItem(
                    NumberFormatter.format_currency(amount)
                ))
                
                score = provider.get('score', 0)
                score_item = QTableWidgetItem(f"{score:.1f}%")
                if score >= 90:
                    score_item.setBackground(QColor("#4CAF50"))
                elif score >= 80:
                    score_item.setBackground(QColor("#FF9800"))
                elif score >= 70:
                    score_item.setBackground(QColor("#FFC107"))
                else:
                    score_item.setBackground(QColor("#F44336"))
                
                self.top_providers_table.setItem(row, 3, score_item)
                
        except Exception as e:
            logger.error(f"Error cargando top proveedores: {e}")
    
    def load_alerts(self):
        """Cargar alertas y vencimientos"""
        try:
            alerts = self.provider_manager.get_contract_alerts()
            
            self.alerts_table.setRowCount(len(alerts))
            
            for row, alert in enumerate(alerts):
                self.alerts_table.setItem(row, 0, QTableWidgetItem(alert.get('tipo', '')))
                self.alerts_table.setItem(row, 1, QTableWidgetItem(alert.get('proveedor', '')))
                
                vencimiento = alert.get('fecha_vencimiento')
                if vencimiento:
                    fecha_text = DateFormatter.format_date(vencimiento)
                    self.alerts_table.setItem(row, 2, QTableWidgetItem(fecha_text))
                
        except Exception as e:
            logger.error(f"Error cargando alertas: {e}")
    
    def load_providers_data(self):
        """Cargar datos de proveedores"""
        try:
            providers = self.provider_manager.get_all_providers()
            
            self.providers_table.setRowCount(len(providers))
            
            for row, provider in enumerate(providers):
                self.providers_table.setItem(row, 0, QTableWidgetItem(str(provider.get('id', ''))))
                self.providers_table.setItem(row, 1, QTableWidgetItem(provider.get('nombre', '')))
                self.providers_table.setItem(row, 2, QTableWidgetItem(provider.get('categoria', '')))
                self.providers_table.setItem(row, 3, QTableWidgetItem(provider.get('email', '')))
                self.providers_table.setItem(row, 4, QTableWidgetItem(provider.get('telefono', '')))
                
                # Estado
                estado = provider.get('activo', True)
                estado_item = QTableWidgetItem("Activo" if estado else "Inactivo")
                estado_item.setBackground(QColor("#4CAF50" if estado else "#F44336"))
                self.providers_table.setItem(row, 5, estado_item)
                
                # Última compra
                ultima_compra = provider.get('ultima_compra')
                if ultima_compra:
                    fecha_text = DateFormatter.format_date(ultima_compra)
                    self.providers_table.setItem(row, 6, QTableWidgetItem(fecha_text))
                
                # Score
                score = provider.get('score', 0)
                score_item = QTableWidgetItem(f"{score:.1f}%")
                if score >= 90:
                    score_item.setBackground(QColor("#4CAF50"))
                elif score >= 80:
                    score_item.setBackground(QColor("#FF9800"))
                elif score >= 70:
                    score_item.setBackground(QColor("#FFC107"))
                else:
                    score_item.setBackground(QColor("#F44336"))
                
                self.providers_table.setItem(row, 7, score_item)
                
        except Exception as e:
            logger.error(f"Error cargando proveedores: {e}")
    
    def load_performance_data(self):
        """Cargar datos de performance"""
        try:
            # Obtener período seleccionado
            period_text = self.period_combo.currentText()
            days = {
                "Últimos 30 días": 30,
                "Últimos 3 meses": 90,
                "Últimos 6 meses": 180,
                "Último año": 365
            }.get(period_text, 30)
            
            performance_data = self.provider_manager.get_providers_performance(days)
            
            self.performance_table.setRowCount(len(performance_data))
            
            for row, data in enumerate(performance_data):
                self.performance_table.setItem(row, 0, QTableWidgetItem(data.get('nombre', '')))
                self.performance_table.setItem(row, 1, QTableWidgetItem(f"{data.get('delivery_quality', 0):.1f}%"))
                self.performance_table.setItem(row, 2, QTableWidgetItem(f"{data.get('punctuality', 0):.1f}%"))
                self.performance_table.setItem(row, 3, QTableWidgetItem(f"{data.get('price_competitiveness', 0):.1f}%"))
                self.performance_table.setItem(row, 4, QTableWidgetItem(f"{data.get('product_quality', 0):.1f}%"))
                self.performance_table.setItem(row, 5, QTableWidgetItem(f"{data.get('customer_service', 0):.1f}%"))
                
                general_score = data.get('general_score', 0)
                score_item = QTableWidgetItem(f"{general_score:.1f}%")
                if general_score >= 90:
                    score_item.setBackground(QColor("#4CAF50"))
                elif general_score >= 80:
                    score_item.setBackground(QColor("#FF9800"))
                elif general_score >= 70:
                    score_item.setBackground(QColor("#FFC107"))
                else:
                    score_item.setBackground(QColor("#F44336"))
                
                self.performance_table.setItem(row, 6, score_item)
                
                eval_date = data.get('last_evaluation_date')
                if eval_date:
                    fecha_text = DateFormatter.format_date(eval_date)
                    self.performance_table.setItem(row, 7, QTableWidgetItem(fecha_text))
                
        except Exception as e:
            logger.error(f"Error cargando performance: {e}")
    
    def load_categories(self):
        """Cargar categorías para filtro"""
        try:
            categories = self.provider_manager.get_provider_categories()
            
            self.category_combo.clear()
            self.category_combo.addItem("Todas las Categorías")
            self.category_combo.addItems(categories)
            
        except Exception as e:
            logger.error(f"Error cargando categorías: {e}")
    
    def load_providers_combo(self):
        """Cargar proveedores en combo de condiciones"""
        try:
            providers = self.provider_manager.get_all_providers()
            
            self.conditions_provider_combo.clear()
            self.conditions_provider_combo.addItem("Seleccionar proveedor...")
            
            for provider in providers:
                self.conditions_provider_combo.addItem(
                    provider.get('nombre', ''),
                    provider.get('id')
                )
                
        except Exception as e:
            logger.error(f"Error cargando combo proveedores: {e}")
    
    def load_provider_conditions(self):
        """Cargar condiciones del proveedor seleccionado"""
        try:
            provider_id = self.conditions_provider_combo.currentData()
            if not provider_id:
                self.save_conditions_btn.setEnabled(False)
                return
                
            self.save_conditions_btn.setEnabled(True)
            
            conditions = self.provider_manager.get_provider_conditions(provider_id)
            if conditions:
                self.payment_days.setValue(conditions.get('payment_days', 30))
                self.early_payment_discount.setValue(conditions.get('early_payment_discount', 0))
                self.currency_combo.setCurrentText(conditions.get('currency', 'ARS'))
                self.delivery_time.setValue(conditions.get('delivery_time', 7))
                self.minimum_order.setValue(conditions.get('minimum_order', 0))
                self.shipping_cost.setValue(conditions.get('shipping_cost', 0))
                self.special_terms.setText(conditions.get('special_terms', ''))
            
            # Cargar contratos
            self.load_provider_contracts(provider_id)
            
        except Exception as e:
            logger.error(f"Error cargando condiciones: {e}")
    
    def load_provider_contracts(self, provider_id):
        """Cargar contratos del proveedor"""
        try:
            contracts = self.provider_manager.get_provider_contracts(provider_id)
            
            self.contracts_table.setRowCount(len(contracts))
            
            for row, contract in enumerate(contracts):
                self.contracts_table.setItem(row, 0, QTableWidgetItem(contract.get('tipo', '')))
                
                fecha_inicio = contract.get('fecha_inicio')
                if fecha_inicio:
                    self.contracts_table.setItem(row, 1, 
                        QTableWidgetItem(DateFormatter.format_date(fecha_inicio))
                    )
                
                fecha_vencimiento = contract.get('fecha_vencimiento') 
                if fecha_vencimiento:
                    self.contracts_table.setItem(row, 2,
                        QTableWidgetItem(DateFormatter.format_date(fecha_vencimiento))
                    )
                
                estado = contract.get('estado', '')
                estado_item = QTableWidgetItem(estado)
                if estado == 'Vigente':
                    estado_item.setBackground(QColor("#4CAF50"))
                elif estado == 'Por vencer':
                    estado_item.setBackground(QColor("#FF9800"))
                else:
                    estado_item.setBackground(QColor("#F44336"))
                
                self.contracts_table.setItem(row, 3, estado_item)
                
        except Exception as e:
            logger.error(f"Error cargando contratos: {e}")
    
    def on_provider_selection_changed(self):
        """Manejar cambio de selección de proveedor"""
        selected_rows = self.providers_table.selectionModel().selectedRows()
        
        if selected_rows:
            row = selected_rows[0].row()
            provider_id = self.providers_table.item(row, 0).text()
            self.current_provider_id = int(provider_id) if provider_id else None
            
            # Habilitar botones
            self.edit_btn.setEnabled(True)
            self.evaluate_btn.setEnabled(True)
            
            # Emitir señal
            provider_data = self.get_provider_data_from_row(row)
            self.provider_selected.emit(provider_data)
        else:
            self.current_provider_id = None
            self.edit_btn.setEnabled(False)
            self.evaluate_btn.setEnabled(False)
    
    def get_provider_data_from_row(self, row):
        """Obtener datos del proveedor desde la fila de tabla"""
        return {
            'id': int(self.providers_table.item(row, 0).text()),
            'nombre': self.providers_table.item(row, 1).text(),
            'categoria': self.providers_table.item(row, 2).text(),
            'email': self.providers_table.item(row, 3).text(),
            'telefono': self.providers_table.item(row, 4).text(),
        }
    
    def filter_providers(self):
        """Filtrar proveedores según criterios"""
        search_text = self.search_line.text().lower()
        status_filter = self.status_combo.currentText()
        category_filter = self.category_combo.currentText()
        
        for row in range(self.providers_table.rowCount()):
            show_row = True
            
            # Filtro por búsqueda
            if search_text:
                nombre = self.providers_table.item(row, 1).text().lower()
                if search_text not in nombre:
                    show_row = False
            
            # Filtro por estado
            if status_filter != "Todos":
                estado = self.providers_table.item(row, 5).text()
                if status_filter == "Activos" and estado != "Activo":
                    show_row = False
                elif status_filter == "Inactivos" and estado != "Inactivo":
                    show_row = False
            
            # Filtro por categoría
            if category_filter != "Todas las Categorías":
                categoria = self.providers_table.item(row, 2).text()
                if categoria != category_filter:
                    show_row = False
            
            self.providers_table.setRowHidden(row, not show_row)
    
    def add_provider(self):
        """Agregar nuevo proveedor"""
        try:
            # Aquí se abriría un diálogo de crear proveedor
            # Por ahora, mostrar mensaje
            QMessageBox.information(self, "Información", 
                "Funcionalidad de agregar proveedor disponible próximamente.")
        except Exception as e:
            logger.error(f"Error agregando proveedor: {e}")
            QMessageBox.critical(self, "Error", f"Error agregando proveedor: {str(e)}")
    
    def edit_provider(self):
        """Editar proveedor seleccionado"""
        try:
            if not self.current_provider_id:
                QMessageBox.warning(self, "Advertencia", "Seleccione un proveedor para editar.")
                return
            
            # Aquí se abriría un diálogo de editar proveedor
            QMessageBox.information(self, "Información", 
                f"Funcionalidad de editar proveedor {self.current_provider_id} disponible próximamente.")
        except Exception as e:
            logger.error(f"Error editando proveedor: {e}")
            QMessageBox.critical(self, "Error", f"Error editando proveedor: {str(e)}")
    
    def evaluate_provider(self):
        """Evaluar performance del proveedor"""
        try:
            if not self.current_provider_id:
                QMessageBox.warning(self, "Advertencia", "Seleccione un proveedor para evaluar.")
                return
            
            dialog = ProviderPerformanceDialog(self.provider_manager, self.current_provider_id, self)
            if dialog.exec_() == QDialog.Accepted:
                evaluation_data = dialog.get_evaluation_data()
                
                # Guardar evaluación
                success = self.provider_manager.save_provider_evaluation(evaluation_data)
                if success:
                    QMessageBox.information(self, "Éxito", "Evaluación guardada correctamente.")
                    self.refresh_data()
                else:
                    QMessageBox.warning(self, "Advertencia", "Error guardando evaluación.")
                    
        except Exception as e:
            logger.error(f"Error evaluando proveedor: {e}")
            QMessageBox.critical(self, "Error", f"Error evaluando proveedor: {str(e)}")
    
    def save_provider_conditions(self):
        """Guardar condiciones comerciales"""
        try:
            provider_id = self.conditions_provider_combo.currentData()
            if not provider_id:
                return
            
            conditions_data = {
                'provider_id': provider_id,
                'payment_days': self.payment_days.value(),
                'early_payment_discount': self.early_payment_discount.value(),
                'currency': self.currency_combo.currentText(),
                'delivery_time': self.delivery_time.value(),
                'minimum_order': self.minimum_order.value(),
                'shipping_cost': self.shipping_cost.value(),
                'special_terms': self.special_terms.toPlainText(),
                'updated_date': datetime.now()
            }
            
            success = self.provider_manager.save_provider_conditions(conditions_data)
            if success:
                QMessageBox.information(self, "Éxito", "Condiciones guardadas correctamente.")
            else:
                QMessageBox.warning(self, "Advertencia", "Error guardando condiciones.")
                
        except Exception as e:
            logger.error(f"Error guardando condiciones: {e}")
            QMessageBox.critical(self, "Error", f"Error guardando condiciones: {str(e)}")
    
    def export_data(self):
        """Exportar datos de proveedores"""
        try:
            # Crear menú de opciones de exportación
            from PyQt5.QtWidgets import QMenu
            from PyQt5.QtCore import QPoint
            
            menu = QMenu(self)
            menu.addAction("Exportar a Excel", lambda: self._export_to_format('excel'))
            menu.addAction("Exportar a PDF", lambda: self._export_to_format('pdf'))
            menu.addAction("Exportar a CSV", lambda: self._export_to_format('csv'))
            
            # Mostrar menú en la posición del botón
            button_pos = self.export_btn.mapToGlobal(QPoint(0, self.export_btn.height()))
            menu.exec_(button_pos)
            
        except Exception as e:
            logger.error(f"Error exportando: {e}")
            QMessageBox.critical(self, "Error", f"Error exportando: {str(e)}")
    
    def _export_to_format(self, format_type):
        """Exportar a formato específico"""
        try:
            # Obtener datos actuales de la tabla
            data = []
            headers = []
            
            # Obtener headers
            for col in range(self.providers_table.columnCount()):
                headers.append(self.providers_table.horizontalHeaderItem(col).text())
            
            # Obtener datos
            for row in range(self.providers_table.rowCount()):
                if not self.providers_table.isRowHidden(row):
                    row_data = []
                    for col in range(self.providers_table.columnCount()):
                        item = self.providers_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    data.append(row_data)
            
            filename = f"proveedores_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if format_type == 'excel':
                exporter = ExcelExporter()
                success = exporter.export_table_data(data, headers, f"{filename}.xlsx", "Proveedores")
            elif format_type == 'pdf':
                exporter = PDFExporter()
                success = exporter.export_table_data(data, headers, f"{filename}.pdf", "Proveedores")
            else:  # CSV
                exporter = CSVExporter()
                success = exporter.export_table_data(data, headers, f"{filename}.csv")
            
            if success:
                QMessageBox.information(self, "Éxito", f"Datos exportados correctamente a {filename}")
            else:
                QMessageBox.warning(self, "Advertencia", "Error exportando datos")
                
        except Exception as e:
            logger.error(f"Error en exportación {format_type}: {e}")
            QMessageBox.critical(self, "Error", f"Error exportando a {format_type}: {str(e)}")
    
    def refresh_data(self):
        """Refrescar todos los datos"""
        self.load_data()
        self.provider_updated.emit()