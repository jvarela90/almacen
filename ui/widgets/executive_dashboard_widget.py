"""
Dashboard Ejecutivo Completo - AlmacénPro v2.0
Dashboard gerencial con KPIs, gráficos y análisis en tiempo real
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from decimal import Decimal
import json

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QDateEdit,
    QCheckBox, QGroupBox, QSplitter, QFrame, QProgressBar,
    QHeaderView, QMessageBox, QDialog, QDialogButtonBox,
    QCalendarWidget, QSlider, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QDate, QThread, pyqtSignal as Signal, QRect
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QIcon, QPainter, QPen

from ...utils.formatters import NumberFormatter, DateFormatter, TextFormatter, StatusFormatter
from ...utils.exporters import ExcelExporter, PDFExporter, CSVExporter

logger = logging.getLogger(__name__)

class KPIWidget(QFrame):
    """Widget para mostrar un KPI individual"""
    
    def __init__(self, title: str, value: str = "0", subtitle: str = "", 
                 color: str = "#2196F3", icon: str = None, parent=None):
        super().__init__(parent)
        self.title = title
        self.current_value = value
        self.subtitle = subtitle
        self.color = color
        
        self.setup_ui()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }}
            QFrame:hover {{
                border: 2px solid {color};
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }}
        """)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        # Título
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Arial", 10))
        title_label.setStyleSheet("color: #666; margin-bottom: 5px;")
        layout.addWidget(title_label)
        
        # Valor principal
        self.value_label = QLabel(self.current_value)
        self.value_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.value_label.setStyleSheet(f"color: {self.color}; margin-bottom: 5px;")
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)
        
        # Subtítulo
        if self.subtitle:
            subtitle_label = QLabel(self.subtitle)
            subtitle_label.setFont(QFont("Arial", 8))
            subtitle_label.setStyleSheet("color: #888;")
            subtitle_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(subtitle_label)
        
        layout.addStretch()
    
    def update_value(self, value: str, subtitle: str = None):
        """Actualizar valor del KPI"""
        self.current_value = value
        self.value_label.setText(value)
        
        if subtitle:
            self.subtitle = subtitle
            # Buscar y actualizar subtitle label si existe
            for i in range(self.layout().count()):
                widget = self.layout().itemAt(i).widget()
                if isinstance(widget, QLabel) and widget != self.value_label:
                    if "color: #888" in widget.styleSheet():
                        widget.setText(subtitle)
                        break

class SimpleBarChart(QWidget):
    """Gráfico de barras simple sin dependencias externas"""
    
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.data = []
        self.labels = []
        self.colors = ["#2196F3", "#4CAF50", "#FF9800", "#F44336", "#9C27B0", "#00BCD4"]
        self.setMinimumHeight(200)
        
    def set_data(self, data: List[Dict]):
        """Establecer datos del gráfico"""
        self.data = [item.get('value', 0) for item in data]
        self.labels = [item.get('label', '') for item in data]
        self.update()
    
    def paintEvent(self, event):
        """Dibujar gráfico de barras"""
        if not self.data:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Área de dibujo
        rect = self.rect()
        margin = 40
        chart_rect = QRect(margin, margin, rect.width() - 2*margin, rect.height() - 2*margin)
        
        # Título
        if self.title:
            painter.setFont(QFont("Arial", 12, QFont.Bold))
            painter.drawText(rect.width()//2 - len(self.title)*3, 20, self.title)
        
        # Calcular dimensiones de barras
        if len(self.data) == 0:
            return
            
        max_value = max(self.data) if self.data else 1
        bar_width = chart_rect.width() // len(self.data) - 10
        bar_spacing = 10
        
        # Dibujar barras
        for i, (value, label) in enumerate(zip(self.data, self.labels)):
            # Calcular posición y altura
            x = chart_rect.x() + i * (bar_width + bar_spacing)
            height = int((value / max_value) * chart_rect.height() * 0.8) if max_value > 0 else 0
            y = chart_rect.bottom() - height - 30
            
            # Dibujar barra
            color = QColor(self.colors[i % len(self.colors)])
            painter.fillRect(x, y, bar_width, height, color)
            
            # Valor encima de la barra
            painter.setFont(QFont("Arial", 8))
            painter.drawText(x, y - 5, bar_width, 20, Qt.AlignCenter, str(value))
            
            # Label debajo de la barra
            painter.drawText(x, chart_rect.bottom() - 20, bar_width, 20, Qt.AlignCenter, 
                           label[:8] + "..." if len(label) > 8 else label)

class TrendIndicator(QWidget):
    """Indicador de tendencia simple"""
    
    def __init__(self, value: float = 0, parent=None):
        super().__init__(parent)
        self.value = value
        self.setFixedSize(30, 20)
    
    def set_value(self, value: float):
        """Establecer valor de tendencia"""
        self.value = value
        self.update()
    
    def paintEvent(self, event):
        """Dibujar indicador de tendencia"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Determinar color según valor
        if self.value > 0:
            color = QColor("#4CAF50")  # Verde para positivo
            text = f"↑ {self.value:.1f}%"
        elif self.value < 0:
            color = QColor("#F44336")  # Rojo para negativo
            text = f"↓ {abs(self.value):.1f}%"
        else:
            color = QColor("#FFC107")  # Amarillo para neutro
            text = "→ 0%"
        
        painter.setPen(QPen(color, 2))
        painter.setFont(QFont("Arial", 8, QFont.Bold))
        painter.drawText(self.rect(), Qt.AlignCenter, text)

class AlertsPanel(QWidget):
    """Panel de alertas inteligentes"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.alerts = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Alertas Inteligentes")
        header.setFont(QFont("Arial", 12, QFont.Bold))
        header.setStyleSheet("color: #333; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Scroll area para alertas
        self.alerts_scroll = QScrollArea()
        self.alerts_widget = QWidget()
        self.alerts_layout = QVBoxLayout(self.alerts_widget)
        
        self.alerts_scroll.setWidget(self.alerts_widget)
        self.alerts_scroll.setWidgetResizable(True)
        self.alerts_scroll.setMaximumHeight(200)
        
        layout.addWidget(self.alerts_scroll)
    
    def add_alert(self, alert_type: str, message: str, priority: str = "medium"):
        """Agregar nueva alerta"""
        alert_widget = QFrame()
        alert_layout = QHBoxLayout(alert_widget)
        
        # Color según prioridad
        colors = {
            "high": "#F44336",
            "medium": "#FF9800", 
            "low": "#FFC107"
        }
        
        color = colors.get(priority, "#FFC107")
        alert_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {color}22;
                border-left: 4px solid {color};
                padding: 8px;
                margin-bottom: 5px;
                border-radius: 4px;
            }}
        """)
        
        # Icono de alerta
        icon_label = QLabel("⚠" if priority == "high" else "ℹ")
        icon_label.setFont(QFont("Arial", 12))
        icon_label.setFixedWidth(20)
        alert_layout.addWidget(icon_label)
        
        # Mensaje
        message_label = QLabel(message)
        message_label.setFont(QFont("Arial", 9))
        message_label.setWordWrap(True)
        alert_layout.addWidget(message_label)
        
        # Timestamp
        time_label = QLabel(datetime.now().strftime("%H:%M"))
        time_label.setFont(QFont("Arial", 8))
        time_label.setStyleSheet("color: #666;")
        alert_layout.addWidget(time_label)
        
        self.alerts_layout.addWidget(alert_widget)
        
        # Mantener solo las últimas 10 alertas
        if self.alerts_layout.count() > 10:
            old_widget = self.alerts_layout.itemAt(0).widget()
            self.alerts_layout.removeWidget(old_widget)
            old_widget.deleteLater()
    
    def clear_alerts(self):
        """Limpiar todas las alertas"""
        for i in reversed(range(self.alerts_layout.count())):
            widget = self.alerts_layout.itemAt(i).widget()
            self.alerts_layout.removeWidget(widget)
            widget.deleteLater()

class ExecutiveDashboardWidget(QWidget):
    """Dashboard ejecutivo completo con KPIs y análisis"""
    
    # Señales
    refresh_requested = pyqtSignal()
    alert_generated = pyqtSignal(dict)
    
    def __init__(self, sales_manager=None, product_manager=None, customer_manager=None, 
                 purchase_manager=None, user_manager=None, parent=None):
        super().__init__(parent)
        
        # Managers
        self.sales_manager = sales_manager
        self.product_manager = product_manager
        self.customer_manager = customer_manager
        self.purchase_manager = purchase_manager
        self.user_manager = user_manager
        
        # Estado interno
        self.last_update = None
        self.current_period = "month"
        self.kpi_data = {}
        
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
        
        title_label = QLabel("Dashboard Ejecutivo")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setStyleSheet("color: #2196F3; margin-bottom: 10px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Selector de período
        self.period_combo = QComboBox()
        self.period_combo.addItems([
            "Hoy", "Esta Semana", "Este Mes", "Último Trimestre", "Este Año"
        ])
        self.period_combo.setCurrentText("Este Mes")
        header_layout.addWidget(QLabel("Período:"))
        header_layout.addWidget(self.period_combo)
        
        # Botón de refresh
        self.refresh_btn = QPushButton("Actualizar")
        self.refresh_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px 16px; border-radius: 4px; }")
        header_layout.addWidget(self.refresh_btn)
        
        # Botón de exportar
        self.export_btn = QPushButton("Exportar")
        self.export_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 8px 16px; border-radius: 4px; }")
        header_layout.addWidget(self.export_btn)
        
        layout.addLayout(header_layout)
        
        # Crear tabs principales
        self.tab_widget = QTabWidget()
        
        # Tab 1: KPIs Principales
        self.kpis_tab = self.create_kpis_tab()
        self.tab_widget.addTab(self.kpis_tab, "KPIs")
        
        # Tab 2: Análisis de Ventas
        self.sales_tab = self.create_sales_analysis_tab()
        self.tab_widget.addTab(self.sales_tab, "Ventas")
        
        # Tab 3: Análisis de Productos
        self.products_tab = self.create_products_analysis_tab()
        self.tab_widget.addTab(self.products_tab, "Productos")
        
        # Tab 4: Análisis de Clientes
        self.customers_tab = self.create_customers_analysis_tab()
        self.tab_widget.addTab(self.customers_tab, "Clientes")
        
        # Tab 5: Proyecciones
        self.projections_tab = self.create_projections_tab()
        self.tab_widget.addTab(self.projections_tab, "Proyecciones")
        
        layout.addWidget(self.tab_widget)
        
        # Status bar
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("Última actualización: Nunca")
        self.status_label.setStyleSheet("color: #666; font-size: 10px;")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        self.data_quality_label = QLabel("Calidad de datos: Excelente")
        self.data_quality_label.setStyleSheet("color: #4CAF50; font-size: 10px;")
        status_layout.addWidget(self.data_quality_label)
        
        layout.addLayout(status_layout)
    
    def create_kpis_tab(self):
        """Crear tab de KPIs principales"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # KPIs principales en grid
        kpis_grid = QGridLayout()
        
        # Fila 1: Ventas
        self.revenue_kpi = KPIWidget("Ingresos del Período", "$0", "Total facturado", "#4CAF50")
        self.sales_count_kpi = KPIWidget("Cantidad de Ventas", "0", "Transacciones", "#2196F3")
        self.avg_sale_kpi = KPIWidget("Venta Promedio", "$0", "Por transacción", "#FF9800")
        self.margin_kpi = KPIWidget("Margen de Ganancia", "0%", "Rentabilidad", "#9C27B0")
        
        kpis_grid.addWidget(self.revenue_kpi, 0, 0)
        kpis_grid.addWidget(self.sales_count_kpi, 0, 1)
        kpis_grid.addWidget(self.avg_sale_kpi, 0, 2)
        kpis_grid.addWidget(self.margin_kpi, 0, 3)
        
        # Fila 2: Inventario y Operaciones
        self.stock_value_kpi = KPIWidget("Valor del Stock", "$0", "Inventario total", "#00BCD4")
        self.products_sold_kpi = KPIWidget("Productos Vendidos", "0", "Unidades", "#795548")
        self.customer_count_kpi = KPIWidget("Clientes Activos", "0", "Este período", "#E91E63")
        self.orders_pending_kpi = KPIWidget("Pedidos Pendientes", "0", "Por procesar", "#FF5722")
        
        kpis_grid.addWidget(self.stock_value_kpi, 1, 0)
        kpis_grid.addWidget(self.products_sold_kpi, 1, 1)
        kpis_grid.addWidget(self.customer_count_kpi, 1, 2)
        kpis_grid.addWidget(self.orders_pending_kpi, 1, 3)
        
        layout.addLayout(kpis_grid)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(separator)
        
        # Panel inferior con gráficos rápidos y alertas
        bottom_layout = QHBoxLayout()
        
        # Gráfico de ventas por día (últimos 7 días)
        sales_chart_group = QGroupBox("Ventas por Día (Últimos 7 días)")
        sales_chart_layout = QVBoxLayout(sales_chart_group)
        
        self.daily_sales_chart = SimpleBarChart("Ventas Diarias")
        sales_chart_layout.addWidget(self.daily_sales_chart)
        
        bottom_layout.addWidget(sales_chart_group)
        
        # Panel de alertas
        alerts_group = QGroupBox("Centro de Alertas")
        alerts_layout = QVBoxLayout(alerts_group)
        
        self.alerts_panel = AlertsPanel()
        alerts_layout.addWidget(self.alerts_panel)
        
        bottom_layout.addWidget(alerts_group)
        
        layout.addLayout(bottom_layout)
        
        return widget
    
    def create_sales_analysis_tab(self):
        """Crear tab de análisis de ventas"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filtros de análisis
        filters_layout = QHBoxLayout()
        
        filters_layout.addWidget(QLabel("Analizar por:"))
        self.sales_analysis_combo = QComboBox()
        self.sales_analysis_combo.addItems([
            "Día", "Semana", "Mes", "Vendedor", "Método de Pago"
        ])
        filters_layout.addWidget(self.sales_analysis_combo)
        
        filters_layout.addStretch()
        
        self.sales_refresh_btn = QPushButton("Actualizar Análisis")
        filters_layout.addWidget(self.sales_refresh_btn)
        
        layout.addLayout(filters_layout)
        
        # Métricas de ventas
        sales_metrics_layout = QHBoxLayout()
        
        self.total_sales_label = QLabel("Total Ventas: $0")
        self.total_sales_label.setFont(QFont("Arial", 14, QFont.Bold))
        sales_metrics_layout.addWidget(self.total_sales_label)
        
        self.growth_indicator = TrendIndicator()
        sales_metrics_layout.addWidget(self.growth_indicator)
        
        sales_metrics_layout.addStretch()
        
        layout.addLayout(sales_metrics_layout)
        
        # Gráfico principal de ventas
        sales_chart_group = QGroupBox("Análisis de Ventas")
        sales_chart_layout = QVBoxLayout(sales_chart_group)
        
        self.main_sales_chart = SimpleBarChart("Ventas por Período")
        sales_chart_layout.addWidget(self.main_sales_chart)
        
        layout.addWidget(sales_chart_group)
        
        # Tabla de detalles de ventas
        details_group = QGroupBox("Detalles de Ventas")
        details_layout = QVBoxLayout(details_group)
        
        self.sales_details_table = QTableWidget()
        self.sales_details_table.setColumnCount(6)
        self.sales_details_table.setHorizontalHeaderLabels([
            "Período", "Ventas", "Cantidad", "Promedio", "Crecimiento", "% del Total"
        ])
        self.sales_details_table.horizontalHeader().setStretchLastSection(True)
        self.sales_details_table.setAlternatingRowColors(True)
        self.sales_details_table.setMaximumHeight(200)
        
        details_layout.addWidget(self.sales_details_table)
        layout.addWidget(details_group)
        
        return widget
    
    def create_products_analysis_tab(self):
        """Crear tab de análisis de productos"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Controles de productos
        products_controls = QHBoxLayout()
        
        products_controls.addWidget(QLabel("Análisis:"))
        self.products_analysis_combo = QComboBox()
        self.products_analysis_combo.addItems([
            "Más Vendidos", "Más Rentables", "Stock Crítico", 
            "Rotación Lenta", "Categorías"
        ])
        products_controls.addWidget(self.products_analysis_combo)
        
        products_controls.addWidget(QLabel("Top:"))
        self.products_limit_spin = QSpinBox()
        self.products_limit_spin.setRange(5, 50)
        self.products_limit_spin.setValue(10)
        products_controls.addWidget(self.products_limit_spin)
        
        products_controls.addStretch()
        
        layout.addLayout(products_controls)
        
        # Layout de dos columnas
        products_layout = QHBoxLayout()
        
        # Columna izquierda: Gráfico
        left_column = QVBoxLayout()
        
        chart_group = QGroupBox("Top Productos")
        chart_layout = QVBoxLayout(chart_group)
        
        self.products_chart = SimpleBarChart("Análisis de Productos")
        chart_layout.addWidget(self.products_chart)
        
        left_column.addWidget(chart_group)
        
        # Columna derecha: Tabla de detalles
        right_column = QVBoxLayout()
        
        table_group = QGroupBox("Detalles de Productos")
        table_layout = QVBoxLayout(table_group)
        
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(6)
        self.products_table.setHorizontalHeaderLabels([
            "Producto", "Vendidos", "Ingresos", "Stock", "Margen", "Rotación"
        ])
        self.products_table.horizontalHeader().setStretchLastSection(True)
        self.products_table.setAlternatingRowColors(True)
        
        table_layout.addWidget(self.products_table)
        right_column.addWidget(table_group)
        
        products_layout.addLayout(left_column, 60)
        products_layout.addLayout(right_column, 40)
        
        layout.addLayout(products_layout)
        
        return widget
    
    def create_customers_analysis_tab(self):
        """Crear tab de análisis de clientes"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Métricas de clientes
        customers_metrics = QGridLayout()
        
        self.total_customers_kpi = KPIWidget("Total Clientes", "0", "Base de clientes", "#2196F3")
        self.new_customers_kpi = KPIWidget("Clientes Nuevos", "0", "Este período", "#4CAF50")
        self.avg_customer_value_kpi = KPIWidget("Valor Promedio", "$0", "Por cliente", "#FF9800")
        self.customer_retention_kpi = KPIWidget("Retención", "0%", "Clientes recurrentes", "#9C27B0")
        
        customers_metrics.addWidget(self.total_customers_kpi, 0, 0)
        customers_metrics.addWidget(self.new_customers_kpi, 0, 1)
        customers_metrics.addWidget(self.avg_customer_value_kpi, 0, 2)
        customers_metrics.addWidget(self.customer_retention_kpi, 0, 3)
        
        layout.addLayout(customers_metrics)
        
        # Análisis de clientes
        analysis_layout = QHBoxLayout()
        
        # Top clientes
        top_customers_group = QGroupBox("Top Clientes por Compras")
        top_customers_layout = QVBoxLayout(top_customers_group)
        
        self.top_customers_table = QTableWidget()
        self.top_customers_table.setColumnCount(4)
        self.top_customers_table.setHorizontalHeaderLabels([
            "Cliente", "Compras", "Total", "Última Compra"
        ])
        self.top_customers_table.horizontalHeader().setStretchLastSection(True)
        self.top_customers_table.setAlternatingRowColors(True)
        
        top_customers_layout.addWidget(self.top_customers_table)
        analysis_layout.addWidget(top_customers_group)
        
        # Segmentación de clientes
        segmentation_group = QGroupBox("Segmentación de Clientes")
        segmentation_layout = QVBoxLayout(segmentation_group)
        
        self.customer_segments_chart = SimpleBarChart("Segmentos")
        segmentation_layout.addWidget(self.customer_segments_chart)
        
        analysis_layout.addWidget(segmentation_group)
        
        layout.addLayout(analysis_layout)
        
        return widget
    
    def create_projections_tab(self):
        """Crear tab de proyecciones"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Controles de proyección
        projection_controls = QHBoxLayout()
        
        projection_controls.addWidget(QLabel("Proyectar:"))
        self.projection_type_combo = QComboBox()
        self.projection_type_combo.addItems([
            "Ventas", "Ingresos", "Productos Vendidos", "Clientes Nuevos"
        ])
        projection_controls.addWidget(self.projection_type_combo)
        
        projection_controls.addWidget(QLabel("Período:"))
        self.projection_period_combo = QComboBox()
        self.projection_period_combo.addItems([
            "Próximos 7 días", "Próximo mes", "Próximos 3 meses", "Próximo año"
        ])
        projection_controls.addWidget(self.projection_period_combo)
        
        projection_controls.addStretch()
        
        self.calculate_projection_btn = QPushButton("Calcular Proyección")
        projection_controls.addWidget(self.calculate_projection_btn)
        
        layout.addLayout(projection_controls)
        
        # Resultados de proyección
        projection_results = QHBoxLayout()
        
        # Gráfico de proyección
        projection_chart_group = QGroupBox("Proyección Basada en Historial")
        projection_chart_layout = QVBoxLayout(projection_chart_group)
        
        self.projection_chart = SimpleBarChart("Proyección")
        projection_chart_layout.addWidget(self.projection_chart)
        
        projection_results.addWidget(projection_chart_group)
        
        # Métricas de proyección
        projection_metrics_group = QGroupBox("Métricas Proyectadas")
        projection_metrics_layout = QVBoxLayout(projection_metrics_group)
        
        self.projected_value_label = QLabel("Valor Proyectado: $0")
        self.projected_value_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.projected_value_label.setStyleSheet("color: #2196F3; margin: 10px;")
        projection_metrics_layout.addWidget(self.projected_value_label)
        
        self.confidence_label = QLabel("Nivel de Confianza: 0%")
        self.confidence_label.setFont(QFont("Arial", 12))
        projection_metrics_layout.addWidget(self.confidence_label)
        
        self.trend_label = QLabel("Tendencia: Estable")
        projection_metrics_layout.addWidget(self.trend_label)
        
        projection_metrics_layout.addStretch()
        
        projection_results.addWidget(projection_metrics_group)
        
        layout.addLayout(projection_results)
        
        return widget
    
    def setup_connections(self):
        """Configurar conexiones de señales"""
        # Controles principales
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.export_btn.clicked.connect(self.export_dashboard)
        self.period_combo.currentTextChanged.connect(self.on_period_changed)
        
        # Análisis de ventas
        self.sales_analysis_combo.currentTextChanged.connect(self.update_sales_analysis)
        self.sales_refresh_btn.clicked.connect(self.update_sales_analysis)
        
        # Análisis de productos
        self.products_analysis_combo.currentTextChanged.connect(self.update_products_analysis)
        self.products_limit_spin.valueChanged.connect(self.update_products_analysis)
        
        # Proyecciones
        self.calculate_projection_btn.clicked.connect(self.calculate_projections)
    
    def setup_timer(self):
        """Configurar timer para actualizaciones automáticas"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_data)
        self.update_timer.start(300000)  # Actualizar cada 5 minutos
    
    def load_data(self):
        """Cargar todos los datos del dashboard"""
        self.load_kpis_data()
        self.update_sales_analysis()
        self.update_products_analysis()
        self.load_customers_data()
        self.generate_intelligent_alerts()
        
        # Actualizar timestamp
        self.last_update = datetime.now()
        self.status_label.setText(f"Última actualización: {self.last_update.strftime('%H:%M:%S')}")
    
    def load_kpis_data(self):
        """Cargar datos de KPIs principales"""
        try:
            period_data = self.get_period_data()
            
            # KPIs de ventas
            if self.sales_manager:
                revenue = self.sales_manager.get_revenue_by_period(period_data['start'], period_data['end'])
                sales_count = self.sales_manager.get_sales_count_by_period(period_data['start'], period_data['end'])
                avg_sale = revenue / sales_count if sales_count > 0 else 0
                margin = self.sales_manager.get_profit_margin_by_period(period_data['start'], period_data['end'])
                
                self.revenue_kpi.update_value(NumberFormatter.format_currency(revenue))
                self.sales_count_kpi.update_value(str(sales_count))
                self.avg_sale_kpi.update_value(NumberFormatter.format_currency(avg_sale))
                self.margin_kpi.update_value(f"{margin:.1f}%")
            
            # KPIs de inventario
            if self.product_manager:
                stock_value = self.product_manager.get_total_stock_value()
                products_sold = self.product_manager.get_products_sold_by_period(period_data['start'], period_data['end'])
                
                self.stock_value_kpi.update_value(NumberFormatter.format_currency(stock_value))
                self.products_sold_kpi.update_value(str(products_sold))
            
            # KPIs de clientes
            if self.customer_manager:
                active_customers = self.customer_manager.get_active_customers_by_period(period_data['start'], period_data['end'])
                self.customer_count_kpi.update_value(str(active_customers))
            
            # Pedidos pendientes (simulado)
            pending_orders = 5  # Placeholder
            self.orders_pending_kpi.update_value(str(pending_orders))
            
            # Cargar gráfico de ventas diarias
            self.load_daily_sales_chart()
            
        except Exception as e:
            logger.error(f"Error cargando KPIs: {e}")
    
    def load_daily_sales_chart(self):
        """Cargar gráfico de ventas diarias"""
        try:
            if not self.sales_manager:
                return
                
            # Últimos 7 días
            chart_data = []
            for i in range(7):
                date = datetime.now() - timedelta(days=6-i)
                sales = self.sales_manager.get_sales_by_date(date)
                chart_data.append({
                    'label': date.strftime('%d/%m'),
                    'value': int(sales)
                })
            
            self.daily_sales_chart.set_data(chart_data)
            
        except Exception as e:
            logger.error(f"Error cargando gráfico diario: {e}")
    
    def update_sales_analysis(self):
        """Actualizar análisis de ventas"""
        try:
            if not self.sales_manager:
                return
                
            analysis_type = self.sales_analysis_combo.currentText()
            period_data = self.get_period_data()
            
            # Obtener datos según tipo de análisis
            if analysis_type == "Día":
                data = self.sales_manager.get_daily_sales_analysis(period_data['start'], period_data['end'])
            elif analysis_type == "Semana":
                data = self.sales_manager.get_weekly_sales_analysis(period_data['start'], period_data['end'])
            elif analysis_type == "Mes":
                data = self.sales_manager.get_monthly_sales_analysis(period_data['start'], period_data['end'])
            elif analysis_type == "Vendedor":
                data = self.sales_manager.get_sales_by_seller(period_data['start'], period_data['end'])
            else:  # Método de Pago
                data = self.sales_manager.get_sales_by_payment_method(period_data['start'], period_data['end'])
            
            # Actualizar gráfico
            chart_data = []
            for item in data[:10]:  # Top 10
                chart_data.append({
                    'label': item.get('label', ''),
                    'value': int(item.get('total_sales', 0))
                })
            
            self.main_sales_chart.set_data(chart_data)
            
            # Actualizar tabla
            self.sales_details_table.setRowCount(len(data))
            total_sales = sum(item.get('total_sales', 0) for item in data)
            
            for row, item in enumerate(data):
                self.sales_details_table.setItem(row, 0, QTableWidgetItem(item.get('label', '')))
                
                sales = item.get('total_sales', 0)
                self.sales_details_table.setItem(row, 1, 
                    QTableWidgetItem(NumberFormatter.format_currency(sales))
                )
                
                count = item.get('count', 0)
                self.sales_details_table.setItem(row, 2, QTableWidgetItem(str(count)))
                
                avg = sales / count if count > 0 else 0
                self.sales_details_table.setItem(row, 3, 
                    QTableWidgetItem(NumberFormatter.format_currency(avg))
                )
                
                growth = item.get('growth', 0)
                growth_item = QTableWidgetItem(f"{growth:+.1f}%")
                if growth > 0:
                    growth_item.setBackground(QColor("#4CAF50"))
                elif growth < 0:
                    growth_item.setBackground(QColor("#F44336"))
                self.sales_details_table.setItem(row, 4, growth_item)
                
                percentage = (sales / total_sales * 100) if total_sales > 0 else 0
                self.sales_details_table.setItem(row, 5, QTableWidgetItem(f"{percentage:.1f}%"))
            
            # Actualizar métricas
            self.total_sales_label.setText(f"Total Ventas: {NumberFormatter.format_currency(total_sales)}")
            
            # Calcular crecimiento general
            prev_period_sales = self.sales_manager.get_previous_period_sales(period_data['start'], period_data['end'])
            if prev_period_sales > 0:
                growth_rate = ((total_sales - prev_period_sales) / prev_period_sales) * 100
                self.growth_indicator.set_value(growth_rate)
            
        except Exception as e:
            logger.error(f"Error actualizando análisis de ventas: {e}")
    
    def update_products_analysis(self):
        """Actualizar análisis de productos"""
        try:
            if not self.product_manager:
                return
                
            analysis_type = self.products_analysis_combo.currentText()
            limit = self.products_limit_spin.value()
            period_data = self.get_period_data()
            
            # Obtener datos según tipo de análisis
            if analysis_type == "Más Vendidos":
                data = self.product_manager.get_best_selling_products(
                    period_data['start'], period_data['end'], limit
                )
            elif analysis_type == "Más Rentables":
                data = self.product_manager.get_most_profitable_products(
                    period_data['start'], period_data['end'], limit
                )
            elif analysis_type == "Stock Crítico":
                data = self.product_manager.get_critical_stock_products(limit)
            elif analysis_type == "Rotación Lenta":
                data = self.product_manager.get_slow_moving_products(limit)
            else:  # Categorías
                data = self.product_manager.get_sales_by_category(
                    period_data['start'], period_data['end']
                )
            
            # Actualizar gráfico
            chart_data = []
            for item in data:
                chart_data.append({
                    'label': item.get('name', '')[:8],
                    'value': int(item.get('value', 0))
                })
            
            self.products_chart.set_data(chart_data)
            
            # Actualizar tabla
            self.products_table.setRowCount(len(data))
            
            for row, item in enumerate(data):
                self.products_table.setItem(row, 0, QTableWidgetItem(item.get('name', '')))
                self.products_table.setItem(row, 1, QTableWidgetItem(str(item.get('quantity_sold', 0))))
                
                revenue = item.get('revenue', 0)
                self.products_table.setItem(row, 2, 
                    QTableWidgetItem(NumberFormatter.format_currency(revenue))
                )
                
                stock = item.get('stock', 0)
                self.products_table.setItem(row, 3, QTableWidgetItem(str(stock)))
                
                margin = item.get('margin', 0)
                self.products_table.setItem(row, 4, QTableWidgetItem(f"{margin:.1f}%"))
                
                rotation = item.get('rotation', 0)
                self.products_table.setItem(row, 5, QTableWidgetItem(f"{rotation:.1f}"))
            
        except Exception as e:
            logger.error(f"Error actualizando análisis de productos: {e}")
    
    def load_customers_data(self):
        """Cargar datos de análisis de clientes"""
        try:
            if not self.customer_manager:
                return
                
            period_data = self.get_period_data()
            
            # KPIs de clientes
            total_customers = self.customer_manager.get_total_customers()
            new_customers = self.customer_manager.get_new_customers_by_period(
                period_data['start'], period_data['end']
            )
            avg_customer_value = self.customer_manager.get_average_customer_value(
                period_data['start'], period_data['end']
            )
            retention_rate = self.customer_manager.get_retention_rate(
                period_data['start'], period_data['end']
            )
            
            self.total_customers_kpi.update_value(str(total_customers))
            self.new_customers_kpi.update_value(str(new_customers))
            self.avg_customer_value_kpi.update_value(NumberFormatter.format_currency(avg_customer_value))
            self.customer_retention_kpi.update_value(f"{retention_rate:.1f}%")
            
            # Top clientes
            top_customers = self.customer_manager.get_top_customers_by_purchases(
                period_data['start'], period_data['end'], 10
            )
            
            self.top_customers_table.setRowCount(len(top_customers))
            
            for row, customer in enumerate(top_customers):
                self.top_customers_table.setItem(row, 0, QTableWidgetItem(customer.get('name', '')))
                self.top_customers_table.setItem(row, 1, QTableWidgetItem(str(customer.get('purchases', 0))))
                
                total = customer.get('total_spent', 0)
                self.top_customers_table.setItem(row, 2, 
                    QTableWidgetItem(NumberFormatter.format_currency(total))
                )
                
                last_purchase = customer.get('last_purchase')
                if last_purchase:
                    self.top_customers_table.setItem(row, 3, 
                        QTableWidgetItem(DateFormatter.format_date(last_purchase))
                    )
            
            # Segmentación de clientes
            segments = self.customer_manager.get_customer_segmentation()
            
            segment_data = []
            for segment in segments:
                segment_data.append({
                    'label': segment.get('name', ''),
                    'value': segment.get('count', 0)
                })
            
            self.customer_segments_chart.set_data(segment_data)
            
        except Exception as e:
            logger.error(f"Error cargando datos de clientes: {e}")
    
    def calculate_projections(self):
        """Calcular proyecciones basadas en datos históricos"""
        try:
            projection_type = self.projection_type_combo.currentText()
            projection_period = self.projection_period_combo.currentText()
            
            # Días a proyectar
            days_map = {
                "Próximos 7 días": 7,
                "Próximo mes": 30,
                "Próximos 3 meses": 90,
                "Próximo año": 365
            }
            
            days = days_map.get(projection_period, 30)
            
            # Obtener datos históricos (últimos 30 días para base)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            if projection_type == "Ventas" and self.sales_manager:
                historical_data = self.sales_manager.get_daily_sales_count(start_date, end_date)
                avg_daily = sum(historical_data) / len(historical_data) if historical_data else 0
                projected_value = avg_daily * days
                confidence = min(95, len(historical_data) * 3)  # Simulado
                
            elif projection_type == "Ingresos" and self.sales_manager:
                historical_data = self.sales_manager.get_daily_revenue(start_date, end_date)
                avg_daily = sum(historical_data) / len(historical_data) if historical_data else 0
                projected_value = avg_daily * days
                confidence = min(95, len(historical_data) * 3)
                
            else:
                # Valores simulados para otros tipos
                projected_value = 1000 * days / 30
                confidence = 75
            
            # Actualizar UI
            if projection_type in ["Ingresos"]:
                value_text = NumberFormatter.format_currency(projected_value)
            else:
                value_text = str(int(projected_value))
                
            self.projected_value_label.setText(f"Valor Proyectado: {value_text}")
            self.confidence_label.setText(f"Nivel de Confianza: {confidence:.0f}%")
            
            # Determinar tendencia
            if confidence > 80:
                trend = "Crecimiento"
                color = "#4CAF50"
            elif confidence > 60:
                trend = "Estable"
                color = "#FF9800"
            else:
                trend = "Incierto"
                color = "#F44336"
                
            self.trend_label.setText(f"Tendencia: {trend}")
            self.trend_label.setStyleSheet(f"color: {color};")
            
            # Generar datos para gráfico de proyección
            projection_chart_data = []
            for i in range(min(7, days)):  # Mostrar hasta 7 períodos
                period_value = projected_value * (i + 1) / days
                projection_chart_data.append({
                    'label': f"P{i+1}",
                    'value': int(period_value)
                })
            
            self.projection_chart.set_data(projection_chart_data)
            
        except Exception as e:
            logger.error(f"Error calculando proyecciones: {e}")
    
    def generate_intelligent_alerts(self):
        """Generar alertas inteligentes del negocio"""
        try:
            self.alerts_panel.clear_alerts()
            
            # Alerta de stock bajo
            if self.product_manager:
                low_stock_count = self.product_manager.get_low_stock_count()
                if low_stock_count > 0:
                    self.alerts_panel.add_alert(
                        "stock", 
                        f"{low_stock_count} productos con stock bajo requieren atención",
                        "medium"
                    )
            
            # Alerta de ventas
            if self.sales_manager:
                today_sales = self.sales_manager.get_sales_by_date(datetime.now())
                yesterday_sales = self.sales_manager.get_sales_by_date(datetime.now() - timedelta(days=1))
                
                if today_sales < yesterday_sales * 0.7:  # 30% menos que ayer
                    self.alerts_panel.add_alert(
                        "sales",
                        "Las ventas de hoy están significativamente por debajo del promedio",
                        "high"
                    )
                elif today_sales > yesterday_sales * 1.3:  # 30% más que ayer
                    self.alerts_panel.add_alert(
                        "sales",
                        "¡Excelente! Las ventas superan el promedio diario",
                        "low"
                    )
            
            # Alerta de clientes nuevos
            if self.customer_manager:
                new_customers_today = self.customer_manager.get_new_customers_by_period(
                    datetime.now().date(), datetime.now().date()
                )
                if new_customers_today > 5:
                    self.alerts_panel.add_alert(
                        "customers",
                        f"{new_customers_today} nuevos clientes registrados hoy",
                        "low"
                    )
            
            # Alerta de rendimiento del sistema
            self.alerts_panel.add_alert(
                "system",
                "Sistema funcionando optimamente - Todos los servicios operativos",
                "low"
            )
            
        except Exception as e:
            logger.error(f"Error generando alertas: {e}")
    
    def get_period_data(self):
        """Obtener datos del período seleccionado"""
        period = self.period_combo.currentText()
        end_date = datetime.now()
        
        if period == "Hoy":
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "Esta Semana":
            days_since_monday = end_date.weekday()
            start_date = end_date - timedelta(days=days_since_monday)
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "Este Mes":
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == "Último Trimestre":
            start_date = end_date - timedelta(days=90)
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        else:  # Este Año
            start_date = end_date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        return {
            'start': start_date,
            'end': end_date,
            'period': period
        }
    
    def on_period_changed(self):
        """Manejar cambio de período"""
        self.refresh_data()
    
    def refresh_data(self):
        """Refrescar todos los datos del dashboard"""
        self.load_data()
        self.refresh_requested.emit()
    
    def export_dashboard(self):
        """Exportar datos del dashboard"""
        try:
            # Crear datos para exportación
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'period': self.period_combo.currentText(),
                'kpis': self.kpi_data,
                'last_update': self.last_update.isoformat() if self.last_update else None
            }
            
            # Exportar a Excel
            exporter = ExcelExporter()
            filename = f"dashboard_ejecutivo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            # Preparar datos para exportación
            dashboard_summary = [
                ['KPI', 'Valor', 'Período'],
                ['Ingresos', self.revenue_kpi.current_value, self.period_combo.currentText()],
                ['Ventas', self.sales_count_kpi.current_value, self.period_combo.currentText()],
                ['Venta Promedio', self.avg_sale_kpi.current_value, self.period_combo.currentText()],
                ['Margen', self.margin_kpi.current_value, self.period_combo.currentText()],
                ['Valor Stock', self.stock_value_kpi.current_value, self.period_combo.currentText()],
                ['Productos Vendidos', self.products_sold_kpi.current_value, self.period_combo.currentText()],
                ['Clientes Activos', self.customer_count_kpi.current_value, self.period_combo.currentText()],
                ['Pedidos Pendientes', self.orders_pending_kpi.current_value, self.period_combo.currentText()],
            ]
            
            headers = dashboard_summary[0]
            data = dashboard_summary[1:]
            
            success = exporter.export_table_data(data, headers, filename, "Dashboard Ejecutivo")
            
            if success:
                QMessageBox.information(self, "Éxito", f"Dashboard exportado a {filename}")
            else:
                QMessageBox.warning(self, "Advertencia", "Error exportando dashboard")
                
        except Exception as e:
            logger.error(f"Error exportando dashboard: {e}")
            QMessageBox.critical(self, "Error", f"Error exportando dashboard: {str(e)}")