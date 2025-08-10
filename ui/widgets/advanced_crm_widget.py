"""
Widget CRM Avanzado - AlmacénPro v2.0
Interfaz completa para gestión de relaciones con clientes
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QDateEdit,
    QCheckBox, QGroupBox, QSplitter, QFrame, QProgressBar,
    QHeaderView, QMessageBox, QDialog, QDialogButtonBox,
    QScrollArea, QTreeWidget, QTreeWidgetItem, QSlider
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QDate, QThread
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon

from ...managers.advanced_customer_manager import AdvancedCustomerManager, CustomerSegment
from ...utils.formatters import NumberFormatter, DateFormatter, TextFormatter, StatusFormatter
from ...utils.exporters import ExcelExporter, PDFExporter, CSVExporter

logger = logging.getLogger(__name__)

class CustomerSegmentationDialog(QDialog):
    """Diálogo para configurar segmentación de clientes"""
    
    def __init__(self, crm_manager, parent=None):
        super().__init__(parent)
        self.crm_manager = crm_manager
        self.setWindowTitle("Segmentación Automática de Clientes")
        self.setModal(True)
        self.resize(700, 500)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Configuración de criterios
        config_group = QGroupBox("Criterios de Segmentación")
        config_layout = QGridLayout(config_group)
        
        config_layout.addWidget(QLabel("Umbral Cliente VIP:"), 0, 0)
        self.vip_threshold = QDoubleSpinBox()
        self.vip_threshold.setRange(0, 1000000)
        self.vip_threshold.setValue(50000)
        self.vip_threshold.setPrefix("$")
        config_layout.addWidget(self.vip_threshold, 0, 1)
        
        config_layout.addWidget(QLabel("Umbral Cliente Premium:"), 1, 0)
        self.premium_threshold = QDoubleSpinBox()
        self.premium_threshold.setRange(0, 1000000)
        self.premium_threshold.setValue(20000)
        self.premium_threshold.setPrefix("$")
        config_layout.addWidget(self.premium_threshold, 1, 1)
        
        config_layout.addWidget(QLabel("Días para Cliente Inactivo:"), 2, 0)
        self.inactive_days = QSpinBox()
        self.inactive_days.setRange(30, 365)
        self.inactive_days.setValue(90)
        config_layout.addWidget(self.inactive_days, 2, 1)
        
        layout.addWidget(config_group)
        
        # Resultados de segmentación
        results_group = QGroupBox("Resultados de Segmentación")
        results_layout = QVBoxLayout(results_group)
        
        # Botón para ejecutar segmentación
        self.run_segmentation_btn = QPushButton("Ejecutar Segmentación")
        self.run_segmentation_btn.clicked.connect(self.run_segmentation)
        results_layout.addWidget(self.run_segmentation_btn)
        
        # Tabla de resultados
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels([
            "Segmento", "Cantidad", "Porcentaje", "Criterios"
        ])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        results_layout.addWidget(self.results_table)
        
        # Área de detalles
        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(150)
        self.details_text.setReadOnly(True)
        results_layout.addWidget(self.details_text)
        
        layout.addWidget(results_group)
        
        # Botones
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def run_segmentation(self):
        """Ejecutar segmentación automática"""
        try:
            # Actualizar configuración del CRM manager
            self.crm_manager.vip_threshold = self.vip_threshold.value()
            self.crm_manager.premium_threshold = self.premium_threshold.value()
            self.crm_manager.inactive_days = self.inactive_days.value()
            
            # Ejecutar segmentación
            results = self.crm_manager.perform_customer_segmentation()
            
            if "error" in results:
                QMessageBox.warning(self, "Error", f"Error en segmentación: {results['error']}")
                return
            
            # Mostrar resultados
            segments = results["segments"]
            total_customers = results["total_customers"]
            
            self.results_table.setRowCount(len(segments))
            
            for row, (segment, customers) in enumerate(segments.items()):
                count = len(customers)
                percentage = (count / total_customers * 100) if total_customers > 0 else 0
                
                self.results_table.setItem(row, 0, QTableWidgetItem(segment))
                self.results_table.setItem(row, 1, QTableWidgetItem(str(count)))
                self.results_table.setItem(row, 2, QTableWidgetItem(f"{percentage:.1f}%"))
                
                # Mostrar criterios principales
                if customers:
                    sample_criteria = customers[0].get("criteria", [])
                    criteria_text = ", ".join(sample_criteria[:2])  # Primeros 2 criterios
                    self.results_table.setItem(row, 3, QTableWidgetItem(criteria_text))
            
            # Mostrar detalles
            details = f"""
Segmentación completada exitosamente:
- Total de clientes analizados: {total_customers}
- Criterios utilizados:
  * Umbral VIP: ${self.vip_threshold.value():,.2f}
  * Umbral Premium: ${self.premium_threshold.value():,.2f}
  * Días inactividad: {self.inactive_days.value()}
            """
            self.details_text.setText(details)
            
            QMessageBox.information(self, "Éxito", "Segmentación completada exitosamente")
            
        except Exception as e:
            logger.error(f"Error ejecutando segmentación: {e}")
            QMessageBox.critical(self, "Error", f"Error ejecutando segmentación: {str(e)}")

class CustomerCLVDialog(QDialog):
    """Diálogo para calcular Customer Lifetime Value"""
    
    def __init__(self, crm_manager, customer_id=None, parent=None):
        super().__init__(parent)
        self.crm_manager = crm_manager
        self.customer_id = customer_id
        self.setWindowTitle("Customer Lifetime Value (CLV)")
        self.setModal(True)
        self.resize(600, 450)
        
        self.setup_ui()
        if customer_id:
            self.calculate_clv()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Selección de cliente
        customer_group = QGroupBox("Selección de Cliente")
        customer_layout = QHBoxLayout(customer_group)
        
        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True)
        customer_layout.addWidget(QLabel("Cliente:"))
        customer_layout.addWidget(self.customer_combo)
        
        self.calculate_btn = QPushButton("Calcular CLV")
        self.calculate_btn.clicked.connect(self.calculate_clv)
        customer_layout.addWidget(self.calculate_btn)
        
        layout.addWidget(customer_group)
        
        # Configuración de predicción
        config_group = QGroupBox("Configuración")
        config_layout = QGridLayout(config_group)
        
        config_layout.addWidget(QLabel("Período de predicción:"), 0, 0)
        self.prediction_months = QSpinBox()
        self.prediction_months.setRange(1, 60)
        self.prediction_months.setValue(12)
        self.prediction_months.setSuffix(" meses")
        config_layout.addWidget(self.prediction_months, 0, 1)
        
        layout.addWidget(config_group)
        
        # Resultados
        results_group = QGroupBox("Resultados CLV")
        results_layout = QGridLayout(results_group)
        
        # CLV Histórico
        results_layout.addWidget(QLabel("CLV Histórico:"), 0, 0)
        self.historical_clv_label = QLabel("$0.00")
        self.historical_clv_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.historical_clv_label.setStyleSheet("color: #4CAF50;")
        results_layout.addWidget(self.historical_clv_label, 0, 1)
        
        # CLV Predicho
        results_layout.addWidget(QLabel("CLV Predicho:"), 1, 0)
        self.predicted_clv_label = QLabel("$0.00")
        self.predicted_clv_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.predicted_clv_label.setStyleSheet("color: #2196F3;")
        results_layout.addWidget(self.predicted_clv_label, 1, 1)
        
        # CLV Total
        results_layout.addWidget(QLabel("CLV Total:"), 2, 0)
        self.total_clv_label = QLabel("$0.00")
        self.total_clv_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.total_clv_label.setStyleSheet("color: #FF9800;")
        results_layout.addWidget(self.total_clv_label, 2, 1)
        
        # Confianza
        results_layout.addWidget(QLabel("Nivel de Confianza:"), 3, 0)
        self.confidence_label = QLabel("0%")
        self.confidence_label.setFont(QFont("Arial", 10))
        results_layout.addWidget(self.confidence_label, 3, 1)
        
        layout.addWidget(results_group)
        
        # Métricas detalladas
        metrics_group = QGroupBox("Métricas Detalladas")
        metrics_layout = QVBoxLayout(metrics_group)
        
        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(2)
        self.metrics_table.setHorizontalHeaderLabels(["Métrica", "Valor"])
        self.metrics_table.horizontalHeader().setStretchLastSection(True)
        self.metrics_table.setMaximumHeight(150)
        metrics_layout.addWidget(self.metrics_table)
        
        layout.addWidget(metrics_group)
        
        # Botones
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Cargar clientes
        self.load_customers()
    
    def load_customers(self):
        """Cargar lista de clientes"""
        try:
            # Simulación - en implementación real obtener de base de datos
            customers = [
                {"id": 1, "name": "Cliente Ejemplo 1"},
                {"id": 2, "name": "Cliente Ejemplo 2"}
            ]
            
            for customer in customers:
                self.customer_combo.addItem(customer["name"], customer["id"])
                
            if self.customer_id:
                for i in range(self.customer_combo.count()):
                    if self.customer_combo.itemData(i) == self.customer_id:
                        self.customer_combo.setCurrentIndex(i)
                        break
                        
        except Exception as e:
            logger.error(f"Error cargando clientes: {e}")
    
    def calculate_clv(self):
        """Calcular CLV del cliente seleccionado"""
        try:
            customer_id = self.customer_combo.currentData()
            if not customer_id:
                QMessageBox.warning(self, "Advertencia", "Seleccione un cliente")
                return
            
            prediction_months = self.prediction_months.value()
            clv_result = self.crm_manager.calculate_customer_clv(customer_id, prediction_months)
            
            if "error" in clv_result:
                QMessageBox.warning(self, "Error", f"Error calculando CLV: {clv_result['error']}")
                return
            
            # Mostrar resultados
            self.historical_clv_label.setText(
                NumberFormatter.format_currency(clv_result.get("historical_clv", 0))
            )
            self.predicted_clv_label.setText(
                NumberFormatter.format_currency(clv_result.get("predicted_clv", 0))
            )
            self.total_clv_label.setText(
                NumberFormatter.format_currency(clv_result.get("total_clv", 0))
            )
            self.confidence_label.setText(f"{clv_result.get('confidence', 0):.0f}%")
            
            # Mostrar métricas detalladas
            metrics = clv_result.get("metrics", {})
            self.metrics_table.setRowCount(len(metrics))
            
            metric_names = {
                "total_purchases": "Total de Compras",
                "total_spent": "Total Gastado",
                "avg_order_value": "Valor Promedio de Orden",
                "purchase_frequency": "Frecuencia de Compra",
                "customer_lifespan_days": "Días como Cliente",
                "trend_factor": "Factor de Tendencia",
                "avg_satisfaction": "Satisfacción Promedio"
            }
            
            for row, (key, value) in enumerate(metrics.items()):
                metric_name = metric_names.get(key, key)
                
                if isinstance(value, float):
                    if key in ["total_spent", "avg_order_value"]:
                        formatted_value = NumberFormatter.format_currency(value)
                    else:
                        formatted_value = f"{value:.2f}"
                else:
                    formatted_value = str(value)
                
                self.metrics_table.setItem(row, 0, QTableWidgetItem(metric_name))
                self.metrics_table.setItem(row, 1, QTableWidgetItem(formatted_value))
            
        except Exception as e:
            logger.error(f"Error calculando CLV: {e}")
            QMessageBox.critical(self, "Error", f"Error calculando CLV: {str(e)}")

class AdvancedCRMWidget(QWidget):
    """Widget principal del CRM avanzado"""
    
    # Señales
    customer_updated = pyqtSignal()
    campaign_created = pyqtSignal(dict)
    
    def __init__(self, database_manager, customer_manager=None, sales_manager=None, parent=None):
        super().__init__(parent)
        
        self.db_manager = database_manager
        self.customer_manager = customer_manager
        self.sales_manager = sales_manager
        
        # Inicializar CRM manager
        self.crm_manager = AdvancedCustomerManager(database_manager)
        
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
        
        title_label = QLabel("CRM Empresarial Avanzado")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setStyleSheet("color: #2196F3; margin-bottom: 10px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Botones principales
        self.segmentation_btn = QPushButton("Segmentación")
        self.segmentation_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; padding: 8px 16px; border-radius: 4px; }")
        
        self.clv_btn = QPushButton("Calcular CLV")
        self.clv_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px 16px; border-radius: 4px; }")
        
        self.churn_btn = QPushButton("Análisis Churn")
        self.churn_btn.setStyleSheet("QPushButton { background-color: #F44336; color: white; padding: 8px 16px; border-radius: 4px; }")
        
        self.campaign_btn = QPushButton("Nueva Campaña")
        self.campaign_btn.setStyleSheet("QPushButton { background-color: #9C27B0; color: white; padding: 8px 16px; border-radius: 4px; }")
        
        self.refresh_btn = QPushButton("Actualizar")
        self.refresh_btn.setStyleSheet("QPushButton { background-color: #607D8B; color: white; padding: 8px 16px; border-radius: 4px; }")
        
        header_layout.addWidget(self.segmentation_btn)
        header_layout.addWidget(self.clv_btn)
        header_layout.addWidget(self.churn_btn)
        header_layout.addWidget(self.campaign_btn)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Crear tabs principales
        self.tab_widget = QTabWidget()
        
        # Tab 1: Dashboard CRM
        self.dashboard_tab = self.create_dashboard_tab()
        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
        
        # Tab 2: Segmentación
        self.segmentation_tab = self.create_segmentation_tab()
        self.tab_widget.addTab(self.segmentation_tab, "Segmentación")
        
        # Tab 3: Fidelización
        self.loyalty_tab = self.create_loyalty_tab()
        self.tab_widget.addTab(self.loyalty_tab, "Fidelización")
        
        # Tab 4: Campañas
        self.campaigns_tab = self.create_campaigns_tab()
        self.tab_widget.addTab(self.campaigns_tab, "Campañas")
        
        # Tab 5: Soporte
        self.support_tab = self.create_support_tab()
        self.tab_widget.addTab(self.support_tab, "Soporte")
        
        # Tab 6: Analytics
        self.analytics_tab = self.create_analytics_tab()
        self.tab_widget.addTab(self.analytics_tab, "Analytics")
        
        layout.addWidget(self.tab_widget)
    
    def create_dashboard_tab(self):
        """Crear tab de dashboard CRM"""
        widget = QWidget()
        layout = QGridLayout(widget)
        
        # Métricas principales
        metrics_frame = QFrame()
        metrics_frame.setFrameStyle(QFrame.StyledPanel)
        metrics_layout = QGridLayout(metrics_frame)
        
        # Total clientes
        self.total_customers_label = QLabel("0")
        self.total_customers_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.total_customers_label.setStyleSheet("color: #2196F3;")
        self.total_customers_label.setAlignment(Qt.AlignCenter)
        
        total_label = QLabel("Total Clientes")
        total_label.setAlignment(Qt.AlignCenter)
        
        metrics_layout.addWidget(self.total_customers_label, 0, 0)
        metrics_layout.addWidget(total_label, 1, 0)
        
        # Clientes nuevos
        self.new_customers_label = QLabel("0")
        self.new_customers_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.new_customers_label.setStyleSheet("color: #4CAF50;")
        self.new_customers_label.setAlignment(Qt.AlignCenter)
        
        new_label = QLabel("Nuevos este Mes")
        new_label.setAlignment(Qt.AlignCenter)
        
        metrics_layout.addWidget(self.new_customers_label, 0, 1)
        metrics_layout.addWidget(new_label, 1, 1)
        
        # Tickets abiertos
        self.open_tickets_label = QLabel("0")
        self.open_tickets_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.open_tickets_label.setStyleSheet("color: #FF9800;")
        self.open_tickets_label.setAlignment(Qt.AlignCenter)
        
        tickets_label = QLabel("Tickets Abiertos")
        tickets_label.setAlignment(Qt.AlignCenter)
        
        metrics_layout.addWidget(self.open_tickets_label, 0, 2)
        metrics_layout.addWidget(tickets_label, 1, 2)
        
        # Satisfacción promedio
        self.avg_satisfaction_label = QLabel("0.0")
        self.avg_satisfaction_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.avg_satisfaction_label.setStyleSheet("color: #9C27B0;")
        self.avg_satisfaction_label.setAlignment(Qt.AlignCenter)
        
        satisfaction_label = QLabel("Satisfacción Promedio")
        satisfaction_label.setAlignment(Qt.AlignCenter)
        
        metrics_layout.addWidget(self.avg_satisfaction_label, 0, 3)
        metrics_layout.addWidget(satisfaction_label, 1, 3)
        
        layout.addWidget(metrics_frame, 0, 0, 1, 2)
        
        # Distribución por segmentos
        segments_group = QGroupBox("Distribución por Segmentos")
        segments_layout = QVBoxLayout(segments_group)
        
        self.segments_table = QTableWidget()
        self.segments_table.setColumnCount(3)
        self.segments_table.setHorizontalHeaderLabels(["Segmento", "Cantidad", "Porcentaje"])
        self.segments_table.horizontalHeader().setStretchLastSection(True)
        self.segments_table.setMaximumHeight(200)
        segments_layout.addWidget(self.segments_table)
        
        layout.addWidget(segments_group, 1, 0)
        
        # Top clientes por CLV
        clv_group = QGroupBox("Top Clientes por CLV")
        clv_layout = QVBoxLayout(clv_group)
        
        self.top_clv_table = QTableWidget()
        self.top_clv_table.setColumnCount(3)
        self.top_clv_table.setHorizontalHeaderLabels(["Cliente", "CLV", "Segmento"])
        self.top_clv_table.horizontalHeader().setStretchLastSection(True)
        self.top_clv_table.setMaximumHeight(200)
        clv_layout.addWidget(self.top_clv_table)
        
        layout.addWidget(clv_group, 1, 1)
        
        return widget
    
    def create_segmentation_tab(self):
        """Crear tab de segmentación"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Controles de segmentación
        controls_layout = QHBoxLayout()
        
        self.auto_segment_btn = QPushButton("Segmentación Automática")
        self.auto_segment_btn.clicked.connect(self.open_segmentation_dialog)
        controls_layout.addWidget(self.auto_segment_btn)
        
        controls_layout.addWidget(QLabel("Filtrar por:"))
        self.segment_filter_combo = QComboBox()
        self.segment_filter_combo.addItems([
            "Todos", "VIP", "Premium", "Regular", "Nuevos", "Inactivos", "Problemáticos"
        ])
        controls_layout.addWidget(self.segment_filter_combo)
        
        controls_layout.addStretch()
        
        self.export_segments_btn = QPushButton("Exportar")
        controls_layout.addWidget(self.export_segments_btn)
        
        layout.addLayout(controls_layout)
        
        # Tabla de clientes segmentados
        self.segmented_customers_table = QTableWidget()
        self.segmented_customers_table.setColumnCount(7)
        self.segmented_customers_table.setHorizontalHeaderLabels([
            "Cliente", "Segmento", "Score", "Compras", "Total Gastado", "Última Compra", "Acciones"
        ])
        
        header = self.segmented_customers_table.horizontalHeader()
        header.setStretchLastSection(True)
        self.segmented_customers_table.setAlternatingRowColors(True)
        self.segmented_customers_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.segmented_customers_table)
        
        return widget
    
    def create_loyalty_tab(self):
        """Crear tab de programa de fidelización"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Configuración del programa
        config_group = QGroupBox("Configuración del Programa")
        config_layout = QGridLayout(config_group)
        
        config_layout.addWidget(QLabel("Puntos por $1 gastado:"), 0, 0)
        self.points_per_dollar = QSpinBox()
        self.points_per_dollar.setRange(1, 100)
        self.points_per_dollar.setValue(1)
        config_layout.addWidget(self.points_per_dollar, 0, 1)
        
        config_layout.addWidget(QLabel("Puntos para Bronze:"), 1, 0)
        self.bronze_points = QSpinBox()
        self.bronze_points.setRange(0, 10000)
        self.bronze_points.setValue(0)
        config_layout.addWidget(self.bronze_points, 1, 1)
        
        config_layout.addWidget(QLabel("Puntos para Plata:"), 1, 2)
        self.silver_points = QSpinBox()
        self.silver_points.setRange(0, 10000)
        self.silver_points.setValue(2000)
        config_layout.addWidget(self.silver_points, 1, 3)
        
        config_layout.addWidget(QLabel("Puntos para Oro:"), 2, 0)
        self.gold_points = QSpinBox()
        self.gold_points.setRange(0, 20000)
        self.gold_points.setValue(5000)
        config_layout.addWidget(self.gold_points, 2, 1)
        
        config_layout.addWidget(QLabel("Puntos para Diamante:"), 2, 2)
        self.diamond_points = QSpinBox()
        self.diamond_points.setRange(0, 50000)
        self.diamond_points.setValue(10000)
        config_layout.addWidget(self.diamond_points, 2, 3)
        
        layout.addWidget(config_group)
        
        # Estadísticas del programa
        stats_layout = QHBoxLayout()
        
        # Distribución por niveles
        levels_group = QGroupBox("Distribución por Niveles")
        levels_layout = QVBoxLayout(levels_group)
        
        self.loyalty_levels_table = QTableWidget()
        self.loyalty_levels_table.setColumnCount(3)
        self.loyalty_levels_table.setHorizontalHeaderLabels(["Nivel", "Clientes", "Porcentaje"])
        self.loyalty_levels_table.setMaximumHeight(150)
        levels_layout.addWidget(self.loyalty_levels_table)
        
        stats_layout.addWidget(levels_group)
        
        # Actividad reciente
        activity_group = QGroupBox("Actividad Reciente")
        activity_layout = QVBoxLayout(activity_group)
        
        self.loyalty_activity_table = QTableWidget()
        self.loyalty_activity_table.setColumnCount(4)
        self.loyalty_activity_table.setHorizontalHeaderLabels([
            "Cliente", "Tipo", "Puntos", "Fecha"
        ])
        self.loyalty_activity_table.setMaximumHeight(150)
        activity_layout.addWidget(self.loyalty_activity_table)
        
        stats_layout.addWidget(activity_group)
        
        layout.addLayout(stats_layout)
        
        # Gestión manual de puntos
        manual_group = QGroupBox("Gestión Manual de Puntos")
        manual_layout = QHBoxLayout(manual_group)
        
        manual_layout.addWidget(QLabel("Cliente:"))
        self.loyalty_customer_combo = QComboBox()
        self.loyalty_customer_combo.setEditable(True)
        manual_layout.addWidget(self.loyalty_customer_combo)
        
        manual_layout.addWidget(QLabel("Puntos:"))
        self.points_amount = QSpinBox()
        self.points_amount.setRange(-99999, 99999)
        manual_layout.addWidget(self.points_amount)
        
        self.add_points_btn = QPushButton("Agregar")
        self.redeem_points_btn = QPushButton("Canjear")
        manual_layout.addWidget(self.add_points_btn)
        manual_layout.addWidget(self.redeem_points_btn)
        
        layout.addWidget(manual_group)
        
        return widget
    
    def create_campaigns_tab(self):
        """Crear tab de campañas de marketing"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Controles de campañas
        controls_layout = QHBoxLayout()
        
        self.new_campaign_btn = QPushButton("Nueva Campaña")
        self.new_campaign_btn.clicked.connect(self.create_new_campaign)
        controls_layout.addWidget(self.new_campaign_btn)
        
        controls_layout.addWidget(QLabel("Estado:"))
        self.campaign_status_filter = QComboBox()
        self.campaign_status_filter.addItems(["Todas", "Activas", "Completadas", "Borrador"])
        controls_layout.addWidget(self.campaign_status_filter)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Lista de campañas
        self.campaigns_table = QTableWidget()
        self.campaigns_table.setColumnCount(7)
        self.campaigns_table.setHorizontalHeaderLabels([
            "Campaña", "Tipo", "Segmento", "Participantes", "Estado", "Fechas", "Acciones"
        ])
        
        header = self.campaigns_table.horizontalHeader()
        header.setStretchLastSection(True)
        self.campaigns_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.campaigns_table)
        
        return widget
    
    def create_support_tab(self):
        """Crear tab de soporte al cliente"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Métricas de soporte
        support_metrics = QHBoxLayout()
        
        # Tickets abiertos
        open_frame = QFrame()
        open_frame.setFrameStyle(QFrame.StyledPanel)
        open_layout = QVBoxLayout(open_frame)
        
        self.support_open_label = QLabel("0")
        self.support_open_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.support_open_label.setAlignment(Qt.AlignCenter)
        self.support_open_label.setStyleSheet("color: #F44336;")
        open_layout.addWidget(self.support_open_label)
        
        open_layout.addWidget(QLabel("Tickets Abiertos", alignment=Qt.AlignCenter))
        support_metrics.addWidget(open_frame)
        
        # Tickets resueltos hoy
        resolved_frame = QFrame()
        resolved_frame.setFrameStyle(QFrame.StyledPanel)
        resolved_layout = QVBoxLayout(resolved_frame)
        
        self.support_resolved_label = QLabel("0")
        self.support_resolved_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.support_resolved_label.setAlignment(Qt.AlignCenter)
        self.support_resolved_label.setStyleSheet("color: #4CAF50;")
        resolved_layout.addWidget(self.support_resolved_label)
        
        resolved_layout.addWidget(QLabel("Resueltos Hoy", alignment=Qt.AlignCenter))
        support_metrics.addWidget(resolved_frame)
        
        # Tiempo promedio de resolución
        avg_time_frame = QFrame()
        avg_time_frame.setFrameStyle(QFrame.StyledPanel)
        avg_time_layout = QVBoxLayout(avg_time_frame)
        
        self.support_avg_time_label = QLabel("0h")
        self.support_avg_time_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.support_avg_time_label.setAlignment(Qt.AlignCenter)
        self.support_avg_time_label.setStyleSheet("color: #FF9800;")
        avg_time_layout.addWidget(self.support_avg_time_label)
        
        avg_time_layout.addWidget(QLabel("Tiempo Promedio", alignment=Qt.AlignCenter))
        support_metrics.addWidget(avg_time_frame)
        
        layout.addLayout(support_metrics)
        
        # Tabla de tickets
        tickets_controls = QHBoxLayout()
        
        self.new_ticket_btn = QPushButton("Nuevo Ticket")
        tickets_controls.addWidget(self.new_ticket_btn)
        
        tickets_controls.addWidget(QLabel("Filtrar:"))
        self.ticket_filter_combo = QComboBox()
        self.ticket_filter_combo.addItems([
            "Todos", "Abiertos", "En Progreso", "Resueltos", "Cerrados"
        ])
        tickets_controls.addWidget(self.ticket_filter_combo)
        
        tickets_controls.addStretch()
        
        layout.addLayout(tickets_controls)
        
        self.support_tickets_table = QTableWidget()
        self.support_tickets_table.setColumnCount(7)
        self.support_tickets_table.setHorizontalHeaderLabels([
            "Ticket #", "Cliente", "Asunto", "Prioridad", "Estado", "Creado", "Acciones"
        ])
        
        header = self.support_tickets_table.horizontalHeader()
        header.setStretchLastSection(True)
        self.support_tickets_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.support_tickets_table)
        
        return widget
    
    def create_analytics_tab(self):
        """Crear tab de analytics y reportes"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Controles de analytics
        analytics_controls = QHBoxLayout()
        
        analytics_controls.addWidget(QLabel("Análisis:"))
        self.analytics_type_combo = QComboBox()
        self.analytics_type_combo.addItems([
            "Churn Prediction", "Customer Journey", "RFM Analysis", "Cohort Analysis"
        ])
        analytics_controls.addWidget(self.analytics_type_combo)
        
        analytics_controls.addWidget(QLabel("Período:"))
        self.analytics_period_combo = QComboBox()
        self.analytics_period_combo.addItems([
            "Último mes", "Últimos 3 meses", "Últimos 6 meses", "Último año"
        ])
        analytics_controls.addWidget(self.analytics_period_combo)
        
        self.run_analysis_btn = QPushButton("Ejecutar Análisis")
        self.run_analysis_btn.clicked.connect(self.run_analytics)
        analytics_controls.addWidget(self.run_analysis_btn)
        
        analytics_controls.addStretch()
        
        layout.addLayout(analytics_controls)
        
        # Área de resultados
        results_splitter = QSplitter(Qt.Horizontal)
        
        # Panel izquierdo: Resultados tabulares
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        self.analytics_table = QTableWidget()
        self.analytics_table.setAlternatingRowColors(True)
        left_layout.addWidget(self.analytics_table)
        
        results_splitter.addWidget(left_widget)
        
        # Panel derecho: Insights y recomendaciones
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        insights_group = QGroupBox("Insights y Recomendaciones")
        insights_layout = QVBoxLayout(insights_group)
        
        self.insights_text = QTextEdit()
        self.insights_text.setReadOnly(True)
        insights_layout.addWidget(self.insights_text)
        
        right_layout.addWidget(insights_group)
        results_splitter.addWidget(right_widget)
        
        # Configurar proporciones
        results_splitter.setSizes([600, 400])
        
        layout.addWidget(results_splitter)
        
        return widget
    
    def setup_connections(self):
        """Configurar conexiones de señales"""
        # Botones principales
        self.segmentation_btn.clicked.connect(self.open_segmentation_dialog)
        self.clv_btn.clicked.connect(self.open_clv_dialog)
        self.churn_btn.clicked.connect(self.analyze_churn)
        self.campaign_btn.clicked.connect(self.create_new_campaign)
        self.refresh_btn.clicked.connect(self.refresh_data)
        
        # Filtros
        self.segment_filter_combo.currentTextChanged.connect(self.filter_segmented_customers)
        self.campaign_status_filter.currentTextChanged.connect(self.filter_campaigns)
        self.ticket_filter_combo.currentTextChanged.connect(self.filter_support_tickets)
        
        # Fidelización
        self.add_points_btn.clicked.connect(self.add_loyalty_points)
        self.redeem_points_btn.clicked.connect(self.redeem_loyalty_points)
        
        # Soporte
        self.new_ticket_btn.clicked.connect(self.create_support_ticket)
    
    def setup_timer(self):
        """Configurar timer para actualizaciones automáticas"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_data)
        self.update_timer.start(300000)  # Actualizar cada 5 minutos
    
    def load_data(self):
        """Cargar todos los datos"""
        self.load_dashboard_data()
        self.load_segmentation_data()
        self.load_loyalty_data()
        self.load_campaigns_data()
        self.load_support_data()
    
    def load_dashboard_data(self):
        """Cargar datos del dashboard"""
        try:
            dashboard_data = self.crm_manager.get_crm_dashboard_data()
            
            if "error" in dashboard_data:
                logger.error(f"Error cargando dashboard: {dashboard_data['error']}")
                return
            
            metrics = dashboard_data.get("metrics", {})
            
            # Actualizar métricas principales
            self.total_customers_label.setText(str(metrics.get("total_customers", 0)))
            self.new_customers_label.setText(str(metrics.get("new_customers_this_month", 0)))
            self.open_tickets_label.setText(str(metrics.get("open_support_tickets", 0)))
            self.avg_satisfaction_label.setText(f"{metrics.get('avg_satisfaction', 0):.1f}")
            
            # Distribución por segmentos
            segments_dist = metrics.get("segments_distribution", {})
            self.segments_table.setRowCount(len(segments_dist))
            
            total_segmented = sum(segments_dist.values()) if segments_dist else 1
            
            for row, (segment, count) in enumerate(segments_dist.items()):
                percentage = (count / total_segmented * 100) if total_segmented > 0 else 0
                
                self.segments_table.setItem(row, 0, QTableWidgetItem(segment))
                self.segments_table.setItem(row, 1, QTableWidgetItem(str(count)))
                self.segments_table.setItem(row, 2, QTableWidgetItem(f"{percentage:.1f}%"))
            
            # Top clientes por CLV
            top_clv = metrics.get("top_clv_customers", [])
            self.top_clv_table.setRowCount(len(top_clv))
            
            for row, customer in enumerate(top_clv):
                self.top_clv_table.setItem(row, 0, QTableWidgetItem(customer.get("nombre", "")))
                clv_value = NumberFormatter.format_currency(customer.get("clv", 0))
                self.top_clv_table.setItem(row, 1, QTableWidgetItem(clv_value))
                self.top_clv_table.setItem(row, 2, QTableWidgetItem("VIP"))  # Placeholder
            
        except Exception as e:
            logger.error(f"Error cargando datos de dashboard: {e}")
    
    def load_segmentation_data(self):
        """Cargar datos de segmentación"""
        # Implementar carga de datos de segmentación
        pass
    
    def load_loyalty_data(self):
        """Cargar datos de programa de fidelización"""
        # Implementar carga de datos de fidelización
        pass
    
    def load_campaigns_data(self):
        """Cargar datos de campañas"""
        # Implementar carga de datos de campañas
        pass
    
    def load_support_data(self):
        """Cargar datos de soporte"""
        # Implementar carga de datos de soporte
        pass
    
    def open_segmentation_dialog(self):
        """Abrir diálogo de segmentación"""
        dialog = CustomerSegmentationDialog(self.crm_manager, self)
        dialog.exec_()
        self.refresh_data()
    
    def open_clv_dialog(self):
        """Abrir diálogo de CLV"""
        dialog = CustomerCLVDialog(self.crm_manager, parent=self)
        dialog.exec_()
    
    def analyze_churn(self):
        """Analizar riesgo de churn"""
        try:
            results = self.crm_manager.predict_customer_churn()
            
            if "error" in results:
                QMessageBox.warning(self, "Error", f"Error en análisis: {results['error']}")
                return
            
            # Mostrar resultados en analytics tab
            self.tab_widget.setCurrentIndex(5)  # Analytics tab
            
            predictions = results.get("predictions", [])
            self.analytics_table.setRowCount(len(predictions))
            self.analytics_table.setColumnCount(5)
            self.analytics_table.setHorizontalHeaderLabels([
                "Cliente", "Nivel de Riesgo", "Score", "Días Inactivo", "Recomendaciones"
            ])
            
            for row, prediction in enumerate(predictions):
                self.analytics_table.setItem(row, 0, QTableWidgetItem(prediction.get("customer_name", "")))
                self.analytics_table.setItem(row, 1, QTableWidgetItem(prediction.get("risk_level", "")))
                self.analytics_table.setItem(row, 2, QTableWidgetItem(str(prediction.get("risk_score", 0))))
                self.analytics_table.setItem(row, 3, QTableWidgetItem(str(prediction.get("days_inactive", 0))))
                
                recommendations = prediction.get("recommendations", [])
                rec_text = ", ".join(recommendations[:3])  # Primeras 3 recomendaciones
                self.analytics_table.setItem(row, 4, QTableWidgetItem(rec_text))
            
            # Mostrar insights
            high_risk = results.get("high_risk_customers", 0)
            medium_risk = results.get("medium_risk_customers", 0)
            total_analyzed = results.get("total_customers_analyzed", 0)
            
            insights = f"""
ANÁLISIS DE RIESGO DE CHURN

Resumen:
• Total de clientes analizados: {total_analyzed}
• Clientes de alto riesgo: {high_risk} ({high_risk/total_analyzed*100:.1f}%)
• Clientes de riesgo medio: {medium_risk} ({medium_risk/total_analyzed*100:.1f}%)

Recomendaciones:
1. Contactar inmediatamente a clientes de alto riesgo
2. Implementar campañas de retención personalizadas
3. Mejorar seguimiento de satisfacción del cliente
4. Revisar procesos de atención al cliente

Próximos pasos:
• Crear campañas automáticas de reactivación
• Asignar account managers a clientes VIP en riesgo
• Implementar alertas tempranas de churn
            """
            
            self.insights_text.setText(insights)
            
        except Exception as e:
            logger.error(f"Error analizando churn: {e}")
            QMessageBox.critical(self, "Error", f"Error analizando churn: {str(e)}")
    
    def create_new_campaign(self):
        """Crear nueva campaña de marketing"""
        QMessageBox.information(self, "Información", 
            "Funcionalidad de creación de campañas disponible próximamente.")
    
    def filter_segmented_customers(self):
        """Filtrar clientes segmentados"""
        pass
    
    def filter_campaigns(self):
        """Filtrar campañas"""
        pass
    
    def filter_support_tickets(self):
        """Filtrar tickets de soporte"""
        pass
    
    def add_loyalty_points(self):
        """Agregar puntos de fidelización"""
        QMessageBox.information(self, "Información", 
            "Funcionalidad de gestión de puntos disponible próximamente.")
    
    def redeem_loyalty_points(self):
        """Canjear puntos de fidelización"""
        QMessageBox.information(self, "Información", 
            "Funcionalidad de canje de puntos disponible próximamente.")
    
    def create_support_ticket(self):
        """Crear ticket de soporte"""
        QMessageBox.information(self, "Información", 
            "Funcionalidad de tickets disponible próximamente.")
    
    def run_analytics(self):
        """Ejecutar análisis personalizado"""
        analysis_type = self.analytics_type_combo.currentText()
        
        if analysis_type == "Churn Prediction":
            self.analyze_churn()
        else:
            QMessageBox.information(self, "Información", 
                f"Análisis '{analysis_type}' disponible próximamente.")
    
    def refresh_data(self):
        """Refrescar todos los datos"""
        self.load_data()
        self.customer_updated.emit()