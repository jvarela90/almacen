"""
Widget de Análisis Predictivo - AlmacénPro v2.0
Interfaz gráfica para análisis predictivo y machine learning de clientes
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                           QTableWidget, QTableWidgetItem, QPushButton, 
                           QLabel, QComboBox, QSpinBox, QTextEdit, QFrame,
                           QProgressBar, QGroupBox, QGridLayout, QScrollArea,
                           QSplitter, QCheckBox, QDateEdit, QLineEdit, QSlider)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QDate
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QPen
from PyQt5.QtChart import QChart, QChartView, QBarSet, QBarSeries, QLineSeries, QPieSeries
from PyQt5.QtChart import QValueAxis, QBarCategoryAxis, QDateTimeAxis
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class PredictiveAnalyticsThread(QThread):
    """Hilo para ejecutar análisis predictivo en background"""
    
    analysis_completed = pyqtSignal(dict)
    progress_updated = pyqtSignal(int)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, predictive_manager, customer_id=None, analysis_type='full'):
        super().__init__()
        self.predictive_manager = predictive_manager
        self.customer_id = customer_id
        self.analysis_type = analysis_type
        self.is_running = True
    
    def run(self):
        """Ejecutar análisis predictivo"""
        try:
            if self.analysis_type == 'full':
                self.progress_updated.emit(10)
                
                if self.customer_id:
                    # Análisis de cliente específico
                    result = self.predictive_manager.analyze_customer_behavior(self.customer_id)
                    self.progress_updated.emit(100)
                    self.analysis_completed.emit(result)
                else:
                    # Análisis de segmentos
                    result = self.predictive_manager.get_segment_analysis()
                    self.progress_updated.emit(100)
                    self.analysis_completed.emit(result)
            
        except Exception as e:
            logger.error(f"Error en análisis predictivo: {e}")
            self.error_occurred.emit(str(e))
    
    def stop(self):
        """Detener el hilo"""
        self.is_running = False

class CustomerPredictionCard(QFrame):
    """Tarjeta para mostrar predicciones de un cliente"""
    
    def __init__(self, prediction_data):
        super().__init__()
        self.prediction_data = prediction_data
        self.init_ui()
    
    def init_ui(self):
        """Inicializar interfaz de la tarjeta"""
        self.setFrameStyle(QFrame.StyledPanel)
        self.setLineWidth(1)
        self.setMaximumHeight(200)
        
        layout = QVBoxLayout(self)
        
        # Header con nombre del cliente
        header_layout = QHBoxLayout()
        
        name_label = QLabel(f"Cliente ID: {self.prediction_data.get('customer_id', 'N/A')}")
        name_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(name_label)
        
        # Score de confianza
        confidence = self.prediction_data.get('confidence_score', 0)
        confidence_label = QLabel(f"Confianza: {confidence:.0%}")
        confidence_label.setStyleSheet(self._get_confidence_style(confidence))
        header_layout.addWidget(confidence_label)
        
        layout.addLayout(header_layout)
        
        # Información de churn
        churn_data = self.prediction_data.get('churn_prediction', {})
        if churn_data and 'churn_probability' in churn_data:
            churn_layout = QHBoxLayout()
            
            churn_label = QLabel(f"Riesgo de Abandono: {churn_data['churn_probability']:.0%}")
            churn_label.setStyleSheet(self._get_risk_style(churn_data['risk_level']))
            churn_layout.addWidget(churn_label)
            
            layout.addLayout(churn_layout)
        
        # Segmento
        segment_data = self.prediction_data.get('segment', {})
        if segment_data and 'segment_name' in segment_data:
            segment_label = QLabel(f"Segmento: {segment_data['segment_name']}")
            segment_label.setFont(QFont("Arial", 9))
            layout.addWidget(segment_label)
        
        # Próxima compra
        next_purchase = self.prediction_data.get('next_purchase_prediction', {})
        if next_purchase and 'predicted_date' in next_purchase:
            next_label = QLabel(f"Próxima compra: {next_purchase['predicted_date']}")
            next_label.setFont(QFont("Arial", 9))
            layout.addWidget(next_label)
        
        # CLV
        clv_data = self.prediction_data.get('clv_prediction', {})
        if clv_data and 'predicted_clv' in clv_data:
            clv_label = QLabel(f"CLV Predicho: ${clv_data['predicted_clv']:,.0f}")
            clv_label.setFont(QFont("Arial", 9, QFont.Bold))
            clv_label.setStyleSheet("color: green;")
            layout.addWidget(clv_label)
    
    def _get_confidence_style(self, confidence):
        """Obtener estilo según nivel de confianza"""
        if confidence >= 0.8:
            return "color: green; font-weight: bold;"
        elif confidence >= 0.6:
            return "color: orange; font-weight: bold;"
        else:
            return "color: red; font-weight: bold;"
    
    def _get_risk_style(self, risk_level):
        """Obtener estilo según nivel de riesgo"""
        if risk_level == 'high':
            return "color: red; font-weight: bold;"
        elif risk_level == 'medium':
            return "color: orange; font-weight: bold;"
        else:
            return "color: green; font-weight: bold;"

class SegmentAnalysisChart(QChartView):
    """Gráfico de análisis de segmentos"""
    
    def __init__(self):
        super().__init__()
        self.chart = QChart()
        self.setChart(self.chart)
        self.setRenderHint(QPainter.Antialiasing)
    
    def update_data(self, segment_data):
        """Actualizar datos del gráfico"""
        try:
            self.chart.removeAllSeries()
            
            # Crear serie de pie para distribución de segmentos
            pie_series = QPieSeries()
            
            for segment, data in segment_data.items():
                if segment != 'total_customers_analyzed':
                    name = data.get('name', segment)
                    percentage = data.get('percentage', 0)
                    pie_series.append(f"{name}\n{percentage}%", percentage)
            
            # Personalizar slices
            for slice in pie_series.slices():
                slice.setLabelVisible(True)
                slice.setPen(QPen(QColor('white'), 2))
            
            self.chart.addSeries(pie_series)
            self.chart.setTitle("Distribución de Segmentos de Clientes")
            self.chart.legend().setAlignment(Qt.AlignBottom)
            
        except Exception as e:
            logger.error(f"Error actualizando gráfico de segmentos: {e}")

class PredictiveAnalyticsWidget(QWidget):
    """Widget principal para análisis predictivo"""
    
    def __init__(self, db_manager, customer_manager):
        super().__init__()
        self.db_manager = db_manager
        self.customer_manager = customer_manager
        
        # Importar manager predictivo
        try:
            from managers.predictive_analysis_manager import PredictiveAnalysisManager
            self.predictive_manager = PredictiveAnalysisManager(db_manager)
            self.predictive_manager.create_prediction_tables()
        except ImportError as e:
            logger.error(f"Error importando PredictiveAnalysisManager: {e}")
            self.predictive_manager = None
        
        self.analysis_thread = None
        self.current_analysis = None
        
        self.init_ui()
        self.setup_connections()
        
        # Timer para actualizaciones automáticas
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.auto_refresh)
        self.update_timer.start(300000)  # 5 minutos
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header con controles
        header_layout = QHBoxLayout()
        
        # Título
        title_label = QLabel("📊 Análisis Predictivo de Clientes")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Controles
        self.customer_combo = QComboBox()
        self.customer_combo.setMinimumWidth(200)
        self.customer_combo.addItem("-- Todos los Clientes --", None)
        header_layout.addWidget(QLabel("Cliente:"))
        header_layout.addWidget(self.customer_combo)
        
        self.analyze_btn = QPushButton("🔍 Analizar")
        self.analyze_btn.setMinimumHeight(35)
        header_layout.addWidget(self.analyze_btn)
        
        self.export_btn = QPushButton("📊 Exportar")
        self.export_btn.setMinimumHeight(35)
        header_layout.addWidget(self.export_btn)
        
        layout.addLayout(header_layout)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Tabs principales
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Tab 1: Análisis Individual
        self.setup_individual_analysis_tab()
        
        # Tab 2: Análisis de Segmentos
        self.setup_segment_analysis_tab()
        
        # Tab 3: Predicciones en Tiempo Real
        self.setup_realtime_predictions_tab()
        
        # Tab 4: Configuración de Modelos
        self.setup_model_config_tab()
        
        # Cargar datos iniciales
        self.load_customers()
    
    def setup_individual_analysis_tab(self):
        """Configurar tab de análisis individual"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Splitter principal
        splitter = QSplitter(Qt.Horizontal)
        
        # Panel izquierdo - Información del cliente
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Información básica
        info_group = QGroupBox("Información del Cliente")
        info_layout = QGridLayout(info_group)
        
        self.customer_name_label = QLabel("Seleccione un cliente")
        self.customer_name_label.setFont(QFont("Arial", 12, QFont.Bold))
        info_layout.addWidget(self.customer_name_label, 0, 0, 1, 2)
        
        self.total_purchases_label = QLabel("Compras: N/A")
        info_layout.addWidget(self.total_purchases_label, 1, 0)
        
        self.total_spent_label = QLabel("Total Gastado: N/A")
        info_layout.addWidget(self.total_spent_label, 1, 1)
        
        self.last_purchase_label = QLabel("Última Compra: N/A")
        info_layout.addWidget(self.last_purchase_label, 2, 0)
        
        self.customer_since_label = QLabel("Cliente Desde: N/A")
        info_layout.addWidget(self.customer_since_label, 2, 1)
        
        left_layout.addWidget(info_group)
        
        # Predicciones principales
        predictions_group = QGroupBox("Predicciones Principales")
        predictions_layout = QVBoxLayout(predictions_group)
        
        # Riesgo de Churn
        self.churn_risk_frame = QFrame()
        self.churn_risk_frame.setFrameStyle(QFrame.StyledPanel)
        churn_layout = QVBoxLayout(self.churn_risk_frame)
        
        self.churn_title = QLabel("🚨 Riesgo de Abandono")
        self.churn_title.setFont(QFont("Arial", 11, QFont.Bold))
        churn_layout.addWidget(self.churn_title)
        
        self.churn_probability = QLabel("Probabilidad: N/A")
        churn_layout.addWidget(self.churn_probability)
        
        self.churn_factors = QTextEdit()
        self.churn_factors.setMaximumHeight(80)
        self.churn_factors.setPlaceholderText("Factores de riesgo...")
        churn_layout.addWidget(self.churn_factors)
        
        predictions_layout.addWidget(self.churn_risk_frame)
        
        # Próxima compra
        self.next_purchase_frame = QFrame()
        self.next_purchase_frame.setFrameStyle(QFrame.StyledPanel)
        next_purchase_layout = QVBoxLayout(self.next_purchase_frame)
        
        self.next_purchase_title = QLabel("🛒 Próxima Compra")
        self.next_purchase_title.setFont(QFont("Arial", 11, QFont.Bold))
        next_purchase_layout.addWidget(self.next_purchase_title)
        
        self.next_purchase_date = QLabel("Fecha Estimada: N/A")
        next_purchase_layout.addWidget(self.next_purchase_date)
        
        self.next_purchase_probability = QLabel("Probabilidad: N/A")
        next_purchase_layout.addWidget(self.next_purchase_probability)
        
        predictions_layout.addWidget(self.next_purchase_frame)
        
        # CLV
        self.clv_frame = QFrame()
        self.clv_frame.setFrameStyle(QFrame.StyledPanel)
        clv_layout = QVBoxLayout(self.clv_frame)
        
        self.clv_title = QLabel("💰 Valor de Vida (CLV)")
        self.clv_title.setFont(QFont("Arial", 11, QFont.Bold))
        clv_layout.addWidget(self.clv_title)
        
        self.clv_current = QLabel("CLV Actual: N/A")
        clv_layout.addWidget(self.clv_current)
        
        self.clv_predicted = QLabel("CLV Predicho: N/A")
        clv_layout.addWidget(self.clv_predicted)
        
        predictions_layout.addWidget(self.clv_frame)
        
        left_layout.addWidget(predictions_group)
        left_layout.addStretch()
        
        splitter.addWidget(left_panel)
        
        # Panel derecho - Patrones y recomendaciones
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Patrones detectados
        patterns_group = QGroupBox("Patrones de Compra Detectados")
        patterns_layout = QVBoxLayout(patterns_group)
        
        self.patterns_table = QTableWidget()
        self.patterns_table.setColumnCount(4)
        self.patterns_table.setHorizontalHeaderLabels(["Tipo", "Descripción", "Confianza", "Detalles"])
        self.patterns_table.setMaximumHeight(200)
        patterns_layout.addWidget(self.patterns_table)
        
        right_layout.addWidget(patterns_group)
        
        # Recomendaciones de productos
        recommendations_group = QGroupBox("Recomendaciones de Productos")
        recommendations_layout = QVBoxLayout(recommendations_group)
        
        self.recommendations_table = QTableWidget()
        self.recommendations_table.setColumnCount(4)
        self.recommendations_table.setHorizontalHeaderLabels(["Producto", "Categoría", "Score", "Razón"])
        self.recommendations_table.setMaximumHeight(200)
        recommendations_layout.addWidget(self.recommendations_table)
        
        right_layout.addWidget(recommendations_group)
        
        # Tendencias
        trends_group = QGroupBox("Análisis de Tendencias")
        trends_layout = QVBoxLayout(trends_group)
        
        self.trends_text = QTextEdit()
        self.trends_text.setMaximumHeight(150)
        self.trends_text.setPlaceholderText("Análisis de tendencias aparecerá aquí...")
        trends_layout.addWidget(self.trends_text)
        
        right_layout.addWidget(trends_group)
        
        splitter.addWidget(right_panel)
        
        # Configurar proporciones del splitter
        splitter.setSizes([300, 500])
        
        layout.addWidget(splitter)
        self.tab_widget.addTab(tab, "Análisis Individual")
    
    def setup_segment_analysis_tab(self):
        """Configurar tab de análisis de segmentos"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Controles del segmento
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Análisis de Segmentos:"))
        
        self.refresh_segments_btn = QPushButton("🔄 Actualizar Segmentos")
        controls_layout.addWidget(self.refresh_segments_btn)
        
        self.segment_export_btn = QPushButton("📊 Exportar Análisis")
        controls_layout.addWidget(self.segment_export_btn)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Splitter para gráfico y tabla
        splitter = QSplitter(Qt.Vertical)
        
        # Gráfico de segmentos
        self.segment_chart = SegmentAnalysisChart()
        self.segment_chart.setMinimumHeight(300)
        splitter.addWidget(self.segment_chart)
        
        # Tabla de estadísticas de segmentos
        self.segments_table = QTableWidget()
        self.segments_table.setColumnCount(7)
        self.segments_table.setHorizontalHeaderLabels([
            "Segmento", "Clientes", "% Total", "Ingresos", "CLV Promedio", 
            "Frecuencia", "% Ingresos"
        ])
        self.segments_table.setMinimumHeight(200)
        splitter.addWidget(self.segments_table)
        
        # Configurar proporciones
        splitter.setSizes([400, 200])
        
        layout.addWidget(splitter)
        
        # Recomendaciones por segmento
        recommendations_group = QGroupBox("Recomendaciones por Segmento")
        recommendations_layout = QVBoxLayout(recommendations_group)
        
        self.segment_recommendations_table = QTableWidget()
        self.segment_recommendations_table.setColumnCount(4)
        self.segment_recommendations_table.setHorizontalHeaderLabels([
            "Segmento", "Prioridad", "Acción", "Descripción"
        ])
        self.segment_recommendations_table.setMaximumHeight(150)
        recommendations_layout.addWidget(self.segment_recommendations_table)
        
        layout.addWidget(recommendations_group)
        
        self.tab_widget.addTab(tab, "Análisis de Segmentos")
    
    def setup_realtime_predictions_tab(self):
        """Configurar tab de predicciones en tiempo real"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Controles
        controls_layout = QHBoxLayout()
        
        self.auto_update_checkbox = QCheckBox("Actualización Automática")
        self.auto_update_checkbox.setChecked(True)
        controls_layout.addWidget(self.auto_update_checkbox)
        
        controls_layout.addWidget(QLabel("Intervalo (min):"))
        
        self.update_interval_spin = QSpinBox()
        self.update_interval_spin.setRange(1, 60)
        self.update_interval_spin.setValue(5)
        controls_layout.addWidget(self.update_interval_spin)
        
        self.manual_refresh_btn = QPushButton("🔄 Actualizar Ahora")
        controls_layout.addWidget(self.manual_refresh_btn)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Área de scroll para tarjetas de predicción
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.predictions_widget = QWidget()
        self.predictions_layout = QVBoxLayout(self.predictions_widget)
        self.predictions_layout.setAlignment(Qt.AlignTop)
        
        scroll_area.setWidget(self.predictions_widget)
        layout.addWidget(scroll_area)
        
        # Estado
        self.realtime_status_label = QLabel("Estado: Listo")
        self.realtime_status_label.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(self.realtime_status_label)
        
        self.tab_widget.addTab(tab, "Predicciones Tiempo Real")
    
    def setup_model_config_tab(self):
        """Configurar tab de configuración de modelos"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Configuración de parámetros
        config_group = QGroupBox("Configuración de Modelos Predictivos")
        config_layout = QGridLayout(config_group)
        
        # Umbral de confianza
        config_layout.addWidget(QLabel("Umbral de Confianza:"), 0, 0)
        self.confidence_threshold_slider = QSlider(Qt.Horizontal)
        self.confidence_threshold_slider.setRange(50, 95)
        self.confidence_threshold_slider.setValue(70)
        self.confidence_threshold_slider.setTickPosition(QSlider.TicksBelow)
        self.confidence_threshold_slider.setTickInterval(5)
        config_layout.addWidget(self.confidence_threshold_slider, 0, 1)
        
        self.confidence_value_label = QLabel("70%")
        config_layout.addWidget(self.confidence_value_label, 0, 2)
        
        # Mínimo de transacciones
        config_layout.addWidget(QLabel("Mínimo de Transacciones:"), 1, 0)
        self.min_transactions_spin = QSpinBox()
        self.min_transactions_spin.setRange(1, 20)
        self.min_transactions_spin.setValue(3)
        config_layout.addWidget(self.min_transactions_spin, 1, 1)
        
        # Período de análisis
        config_layout.addWidget(QLabel("Período de Análisis (días):"), 2, 0)
        self.analysis_period_spin = QSpinBox()
        self.analysis_period_spin.setRange(30, 730)
        self.analysis_period_spin.setValue(365)
        config_layout.addWidget(self.analysis_period_spin, 2, 1)
        
        # Factores de segmentación
        config_layout.addWidget(QLabel("Factores de Segmentación:"), 3, 0)
        
        segmentation_widget = QWidget()
        segmentation_layout = QVBoxLayout(segmentation_widget)
        
        self.high_value_threshold = QSpinBox()
        self.high_value_threshold.setRange(10000, 100000)
        self.high_value_threshold.setValue(50000)
        self.high_value_threshold.setSuffix(" $")
        segmentation_layout.addWidget(QLabel("Alto Valor (monto mínimo):"))
        segmentation_layout.addWidget(self.high_value_threshold)
        
        self.frequent_threshold = QSpinBox()
        self.frequent_threshold.setRange(5, 50)
        self.frequent_threshold.setValue(15)
        segmentation_layout.addWidget(QLabel("Cliente Frecuente (compras mínimas):"))
        segmentation_layout.addWidget(self.frequent_threshold)
        
        self.at_risk_days = QSpinBox()
        self.at_risk_days.setRange(30, 180)
        self.at_risk_days.setValue(60)
        segmentation_layout.addWidget(QLabel("En Riesgo (días sin comprar):"))
        segmentation_layout.addWidget(self.at_risk_days)
        
        config_layout.addWidget(segmentation_widget, 3, 1, 1, 2)
        
        layout.addWidget(config_group)
        
        # Botones de acción
        actions_layout = QHBoxLayout()
        
        self.save_config_btn = QPushButton("💾 Guardar Configuración")
        actions_layout.addWidget(self.save_config_btn)
        
        self.reset_config_btn = QPushButton("🔄 Restaurar Defaults")
        actions_layout.addWidget(self.reset_config_btn)
        
        self.test_model_btn = QPushButton("🧪 Probar Modelo")
        actions_layout.addWidget(self.test_model_btn)
        
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)
        
        # Log de resultados
        log_group = QGroupBox("Log de Configuración")
        log_layout = QVBoxLayout(log_group)
        
        self.config_log = QTextEdit()
        self.config_log.setMaximumHeight(200)
        self.config_log.setPlaceholderText("Los cambios de configuración aparecerán aquí...")
        log_layout.addWidget(self.config_log)
        
        layout.addWidget(log_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Configuración")
    
    def setup_connections(self):
        """Configurar conexiones de señales"""
        self.analyze_btn.clicked.connect(self.run_analysis)
        self.export_btn.clicked.connect(self.export_analysis)
        self.customer_combo.currentIndexChanged.connect(self.on_customer_selected)
        
        # Análisis de segmentos
        self.refresh_segments_btn.clicked.connect(self.refresh_segment_analysis)
        self.segment_export_btn.clicked.connect(self.export_segment_analysis)
        
        # Predicciones tiempo real
        self.manual_refresh_btn.clicked.connect(self.refresh_realtime_predictions)
        self.auto_update_checkbox.toggled.connect(self.toggle_auto_update)
        self.update_interval_spin.valueChanged.connect(self.update_refresh_interval)
        
        # Configuración
        self.confidence_threshold_slider.valueChanged.connect(self.update_confidence_label)
        self.save_config_btn.clicked.connect(self.save_configuration)
        self.reset_config_btn.clicked.connect(self.reset_configuration)
        self.test_model_btn.clicked.connect(self.test_model)
    
    def load_customers(self):
        """Cargar lista de clientes"""
        try:
            query = """
            SELECT c.id, c.nombre, COUNT(v.id) as purchases
            FROM clientes c
            LEFT JOIN ventas v ON c.id = v.cliente_id
            WHERE c.activo = 1
            GROUP BY c.id
            HAVING purchases > 0
            ORDER BY purchases DESC
            """
            
            customers = self.db_manager.execute_query(query)
            
            self.customer_combo.clear()
            self.customer_combo.addItem("-- Todos los Clientes --", None)
            
            for customer in customers:
                name = f"{customer['nombre']} ({customer['purchases']} compras)"
                self.customer_combo.addItem(name, customer['id'])
                
        except Exception as e:
            logger.error(f"Error cargando clientes: {e}")
    
    def on_customer_selected(self):
        """Manejar selección de cliente"""
        customer_id = self.customer_combo.currentData()
        if customer_id:
            self.load_customer_info(customer_id)
    
    def load_customer_info(self, customer_id):
        """Cargar información básica del cliente"""
        try:
            if not self.predictive_manager:
                return
            
            # Obtener datos básicos
            customer_data = self.predictive_manager._get_customer_data(customer_id)
            if customer_data:
                self.customer_name_label.setText(f"Cliente: {customer_data.get('nombre', 'N/A')}")
                self.total_purchases_label.setText(f"Compras: {customer_data.get('total_purchases', 0)}")
                self.total_spent_label.setText(f"Total: ${customer_data.get('total_spent', 0):,.0f}")
                
                last_purchase = customer_data.get('last_purchase')
                if last_purchase:
                    date_str = datetime.strptime(last_purchase, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
                    self.last_purchase_label.setText(f"Última: {date_str}")
                
                first_purchase = customer_data.get('first_purchase')
                if first_purchase:
                    date_str = datetime.strptime(first_purchase, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
                    self.customer_since_label.setText(f"Desde: {date_str}")
        
        except Exception as e:
            logger.error(f"Error cargando info del cliente: {e}")
    
    def run_analysis(self):
        """Ejecutar análisis predictivo"""
        if not self.predictive_manager:
            self.show_message("Error: Sistema de análisis predictivo no disponible")
            return
        
        customer_id = self.customer_combo.currentData()
        
        # Mostrar progreso
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.setText("Analizando...")
        
        # Crear y ejecutar hilo de análisis
        self.analysis_thread = PredictiveAnalyticsThread(
            self.predictive_manager, customer_id, 'full'
        )
        self.analysis_thread.analysis_completed.connect(self.on_analysis_completed)
        self.analysis_thread.progress_updated.connect(self.progress_bar.setValue)
        self.analysis_thread.error_occurred.connect(self.on_analysis_error)
        self.analysis_thread.start()
    
    def on_analysis_completed(self, result):
        """Manejar finalización del análisis"""
        self.progress_bar.setVisible(False)
        self.analyze_btn.setEnabled(True)
        self.analyze_btn.setText("🔍 Analizar")
        self.current_analysis = result
        
        customer_id = self.customer_combo.currentData()
        
        if customer_id:
            # Análisis individual
            self.display_individual_analysis(result)
        else:
            # Análisis de segmentos
            self.display_segment_analysis(result)
    
    def on_analysis_error(self, error_msg):
        """Manejar error en análisis"""
        self.progress_bar.setVisible(False)
        self.analyze_btn.setEnabled(True)
        self.analyze_btn.setText("🔍 Analizar")
        self.show_message(f"Error en análisis: {error_msg}")
    
    def display_individual_analysis(self, analysis):
        """Mostrar resultados de análisis individual"""
        try:
            if 'error' in analysis:
                self.show_message(f"Error: {analysis['error']}")
                return
            
            # Actualizar predicción de churn
            churn_data = analysis.get('churn_prediction', {})
            if churn_data:
                probability = churn_data.get('churn_probability', 0)
                risk_level = churn_data.get('risk_level', 'unknown')
                
                self.churn_probability.setText(f"Probabilidad: {probability:.0%}")
                self.churn_probability.setStyleSheet(self._get_risk_color(risk_level))
                
                factors = churn_data.get('factors', {})
                factors_text = "\n".join([f"• {factor.replace('_', ' ').title()}: {score:.1%}" 
                                        for factor, score in factors.items()])
                self.churn_factors.setPlainText(factors_text)
            
            # Próxima compra
            next_purchase = analysis.get('next_purchase_prediction', {})
            if next_purchase and 'predicted_date' in next_purchase:
                date = next_purchase['predicted_date']
                probability = next_purchase.get('probability', 0)
                
                self.next_purchase_date.setText(f"Fecha: {date}")
                self.next_purchase_probability.setText(f"Probabilidad: {probability:.0%}")
            
            # CLV
            clv_data = analysis.get('clv_prediction', {})
            if clv_data:
                current_clv = clv_data.get('current_clv', 0)
                predicted_clv = clv_data.get('predicted_clv', 0)
                
                self.clv_current.setText(f"Actual: ${current_clv:,.0f}")
                self.clv_predicted.setText(f"Predicho: ${predicted_clv:,.0f}")
                
                if predicted_clv > current_clv:
                    self.clv_predicted.setStyleSheet("color: green; font-weight: bold;")
                else:
                    self.clv_predicted.setStyleSheet("color: orange; font-weight: bold;")
            
            # Patrones
            patterns = analysis.get('purchase_patterns', [])
            self.populate_patterns_table(patterns)
            
            # Recomendaciones
            recommendations = analysis.get('product_recommendations', [])
            self.populate_recommendations_table(recommendations)
            
            # Tendencias
            trends = analysis.get('trends', {})
            self.display_trends_analysis(trends)
            
        except Exception as e:
            logger.error(f"Error mostrando análisis individual: {e}")
    
    def display_segment_analysis(self, analysis):
        """Mostrar resultados de análisis de segmentos"""
        try:
            if 'error' in analysis:
                self.show_message(f"Error: {analysis['error']}")
                return
            
            segments = analysis.get('segments', {})
            
            # Actualizar gráfico
            self.segment_chart.update_data(segments)
            
            # Actualizar tabla
            self.populate_segments_table(segments)
            
            # Recomendaciones por segmento
            recommendations = analysis.get('recommendations', [])
            self.populate_segment_recommendations_table(recommendations)
            
        except Exception as e:
            logger.error(f"Error mostrando análisis de segmentos: {e}")
    
    def populate_patterns_table(self, patterns):
        """Poblar tabla de patrones"""
        try:
            self.patterns_table.setRowCount(len(patterns))
            
            for row, pattern in enumerate(patterns):
                self.patterns_table.setItem(row, 0, QTableWidgetItem(
                    pattern.get('pattern_type', '').replace('_', ' ').title()
                ))
                self.patterns_table.setItem(row, 1, QTableWidgetItem(
                    pattern.get('description', '')
                ))
                self.patterns_table.setItem(row, 2, QTableWidgetItem(
                    pattern.get('confidence', 'medium').title()
                ))
                
                # Detalles específicos según tipo
                details = ""
                if pattern.get('pattern_type') == 'frequency':
                    details = f"Cada {pattern.get('avg_days_between_purchases', 0):.0f} días"
                elif pattern.get('pattern_type') == 'seasonal':
                    peak_month = pattern.get('peak_month_name', '')
                    details = f"Pico en {peak_month}"
                elif pattern.get('pattern_type') == 'spending_behavior':
                    trend = pattern.get('trend', '')
                    details = f"Tendencia: {trend}"
                
                self.patterns_table.setItem(row, 3, QTableWidgetItem(details))
            
            self.patterns_table.resizeColumnsToContents()
            
        except Exception as e:
            logger.error(f"Error poblando tabla de patrones: {e}")
    
    def populate_recommendations_table(self, recommendations):
        """Poblar tabla de recomendaciones"""
        try:
            self.recommendations_table.setRowCount(len(recommendations))
            
            for row, rec in enumerate(recommendations):
                self.recommendations_table.setItem(row, 0, QTableWidgetItem(
                    rec.get('product_name', '')
                ))
                self.recommendations_table.setItem(row, 1, QTableWidgetItem(
                    rec.get('category', '')
                ))
                self.recommendations_table.setItem(row, 2, QTableWidgetItem(
                    f"{rec.get('score', 0):.2f}"
                ))
                self.recommendations_table.setItem(row, 3, QTableWidgetItem(
                    rec.get('reason', '')
                ))
            
            self.recommendations_table.resizeColumnsToContents()
            
        except Exception as e:
            logger.error(f"Error poblando tabla de recomendaciones: {e}")
    
    def populate_segments_table(self, segments):
        """Poblar tabla de segmentos"""
        try:
            self.segments_table.setRowCount(len(segments))
            
            row = 0
            for segment_id, data in segments.items():
                if segment_id == 'total_customers_analyzed':
                    continue
                
                self.segments_table.setItem(row, 0, QTableWidgetItem(
                    data.get('name', segment_id)
                ))
                self.segments_table.setItem(row, 1, QTableWidgetItem(
                    str(data.get('customer_count', 0))
                ))
                self.segments_table.setItem(row, 2, QTableWidgetItem(
                    f"{data.get('percentage', 0):.1f}%"
                ))
                self.segments_table.setItem(row, 3, QTableWidgetItem(
                    f"${data.get('total_revenue', 0):,.0f}"
                ))
                self.segments_table.setItem(row, 4, QTableWidgetItem(
                    f"${data.get('avg_clv', 0):,.0f}"
                ))
                self.segments_table.setItem(row, 5, QTableWidgetItem(
                    f"{data.get('avg_frequency', 0):.1f}"
                ))
                self.segments_table.setItem(row, 6, QTableWidgetItem(
                    f"{data.get('revenue_percentage', 0):.1f}%"
                ))
                
                row += 1
            
            self.segments_table.resizeColumnsToContents()
            
        except Exception as e:
            logger.error(f"Error poblando tabla de segmentos: {e}")
    
    def populate_segment_recommendations_table(self, recommendations):
        """Poblar tabla de recomendaciones por segmento"""
        try:
            self.segment_recommendations_table.setRowCount(len(recommendations))
            
            for row, rec in enumerate(recommendations):
                self.segment_recommendations_table.setItem(row, 0, QTableWidgetItem(
                    rec.get('segment', '')
                ))
                
                priority = rec.get('priority', 'medium')
                priority_item = QTableWidgetItem(priority.title())
                if priority == 'urgent':
                    priority_item.setBackground(QColor('#ffcccc'))
                elif priority == 'high':
                    priority_item.setBackground(QColor('#fff2cc'))
                
                self.segment_recommendations_table.setItem(row, 1, priority_item)
                
                self.segment_recommendations_table.setItem(row, 2, QTableWidgetItem(
                    rec.get('action', '')
                ))
                self.segment_recommendations_table.setItem(row, 3, QTableWidgetItem(
                    rec.get('description', '')
                ))
            
            self.segment_recommendations_table.resizeColumnsToContents()
            
        except Exception as e:
            logger.error(f"Error poblando recomendaciones por segmento: {e}")
    
    def display_trends_analysis(self, trends):
        """Mostrar análisis de tendencias"""
        try:
            if not trends or 'insufficient_data' in trends:
                self.trends_text.setPlainText("Datos insuficientes para análisis de tendencias")
                return
            
            text = f"ANÁLISIS DE TENDENCIAS\n\n"
            
            # Tendencia general
            overall = trends.get('overall_trend', 'unknown')
            text += f"Tendencia General: {overall.upper()}\n\n"
            
            # Tendencias específicas
            freq_trend = trends.get('frequency_trend', {})
            if freq_trend:
                direction = freq_trend.get('direction', 'stable')
                strength = freq_trend.get('strength', 0)
                text += f"Frecuencia de Compras: {direction} (fuerza: {strength:.2f})\n"
            
            spend_trend = trends.get('spending_trend', {})
            if spend_trend:
                direction = spend_trend.get('direction', 'stable')
                strength = spend_trend.get('strength', 0)
                text += f"Gastos: {direction} (fuerza: {strength:.2f})\n"
            
            avg_trend = trends.get('average_order_trend', {})
            if avg_trend:
                direction = avg_trend.get('direction', 'stable')
                strength = avg_trend.get('strength', 0)
                text += f"Ticket Promedio: {direction} (fuerza: {strength:.2f})\n"
            
            # Datos mensuales
            monthly_data = trends.get('monthly_data', [])
            if monthly_data:
                text += f"\nDATOS MENSUALES ({len(monthly_data)} meses):\n"
                for month_data in monthly_data[-6:]:  # Últimos 6 meses
                    month = month_data.get('month', '')
                    purchases = month_data.get('purchases', 0)
                    total = month_data.get('total_spent', 0)
                    text += f"{month}: {purchases} compras, ${total:,.0f}\n"
            
            self.trends_text.setPlainText(text)
            
        except Exception as e:
            logger.error(f"Error mostrando análisis de tendencias: {e}")
    
    def refresh_segment_analysis(self):
        """Actualizar análisis de segmentos"""
        if not self.predictive_manager:
            return
        
        # Cambiar temporalmente el combo a "todos" para análisis de segmentos
        current_index = self.customer_combo.currentIndex()
        self.customer_combo.setCurrentIndex(0)  # Todos los clientes
        
        self.run_analysis()
        
        # Restaurar selección si había una específica
        if current_index > 0:
            self.customer_combo.setCurrentIndex(current_index)
    
    def refresh_realtime_predictions(self):
        """Actualizar predicciones en tiempo real"""
        try:
            self.realtime_status_label.setText("Estado: Actualizando...")
            self.realtime_status_label.setStyleSheet("color: orange; font-weight: bold;")
            
            # Limpiar predicciones anteriores
            for i in reversed(range(self.predictions_layout.count())):
                child = self.predictions_layout.itemAt(i).widget()
                if child:
                    child.setParent(None)
            
            if not self.predictive_manager:
                return
            
            # Obtener top 10 clientes para análisis rápido
            query = """
            SELECT c.id, c.nombre, COUNT(v.id) as purchases,
                   julianday('now') - julianday(MAX(v.fecha_venta)) as days_since_last
            FROM clientes c
            JOIN ventas v ON c.id = v.cliente_id
            WHERE c.activo = 1 AND v.fecha_venta >= date('now', '-1 year')
            GROUP BY c.id
            ORDER BY days_since_last ASC, purchases DESC
            LIMIT 10
            """
            
            customers = self.db_manager.execute_query(query)
            
            for customer in customers:
                # Análisis básico rápido
                prediction_data = {
                    'customer_id': customer['id'],
                    'customer_name': customer['nombre']
                }
                
                # Predicción simple de churn basada en días sin comprar
                days_since = customer.get('days_since_last', 0)
                if days_since > 90:
                    churn_prob = min(0.9, days_since / 180)
                    risk = 'high' if churn_prob > 0.7 else 'medium'
                else:
                    churn_prob = days_since / 180
                    risk = 'low'
                
                prediction_data['churn_prediction'] = {
                    'churn_probability': churn_prob,
                    'risk_level': risk
                }
                
                # Crear y agregar tarjeta
                card = CustomerPredictionCard(prediction_data)
                self.predictions_layout.addWidget(card)
            
            self.realtime_status_label.setText("Estado: Actualizado")
            self.realtime_status_label.setStyleSheet("color: green; font-weight: bold;")
            
        except Exception as e:
            logger.error(f"Error en predicciones tiempo real: {e}")
            self.realtime_status_label.setText("Estado: Error")
            self.realtime_status_label.setStyleSheet("color: red; font-weight: bold;")
    
    def toggle_auto_update(self, enabled):
        """Activar/desactivar actualización automática"""
        if enabled:
            interval = self.update_interval_spin.value() * 60000  # a milisegundos
            self.update_timer.start(interval)
        else:
            self.update_timer.stop()
    
    def update_refresh_interval(self):
        """Actualizar intervalo de refresco"""
        if self.auto_update_checkbox.isChecked():
            interval = self.update_interval_spin.value() * 60000
            self.update_timer.start(interval)
    
    def update_confidence_label(self):
        """Actualizar etiqueta de confianza"""
        value = self.confidence_threshold_slider.value()
        self.confidence_value_label.setText(f"{value}%")
    
    def save_configuration(self):
        """Guardar configuración de modelos"""
        try:
            config = {
                'confidence_threshold': self.confidence_threshold_slider.value() / 100,
                'min_transactions': self.min_transactions_spin.value(),
                'analysis_period': self.analysis_period_spin.value(),
                'high_value_threshold': self.high_value_threshold.value(),
                'frequent_threshold': self.frequent_threshold.value(),
                'at_risk_days': self.at_risk_days.value()
            }
            
            # En implementación real, guardar en base de datos o archivo
            log_msg = f"Configuración guardada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            log_msg += f"- Umbral confianza: {config['confidence_threshold']:.0%}\n"
            log_msg += f"- Mín. transacciones: {config['min_transactions']}\n"
            log_msg += f"- Período análisis: {config['analysis_period']} días\n"
            
            self.config_log.append(log_msg)
            
        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")
    
    def reset_configuration(self):
        """Restaurar configuración por defecto"""
        self.confidence_threshold_slider.setValue(70)
        self.min_transactions_spin.setValue(3)
        self.analysis_period_spin.setValue(365)
        self.high_value_threshold.setValue(50000)
        self.frequent_threshold.setValue(15)
        self.at_risk_days.setValue(60)
        
        self.config_log.append(f"Configuración restaurada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    def test_model(self):
        """Probar modelo predictivo"""
        try:
            if not self.predictive_manager:
                self.show_message("Sistema predictivo no disponible")
                return
            
            # Obtener cliente aleatorio para prueba
            query = "SELECT id FROM clientes WHERE id IN (SELECT cliente_id FROM ventas GROUP BY cliente_id HAVING COUNT(*) >= 3) ORDER BY RANDOM() LIMIT 1"
            result = self.db_manager.execute_query(query)
            
            if result:
                customer_id = result[0]['id']
                
                # Ejecutar análisis de prueba
                test_result = self.predictive_manager.analyze_customer_behavior(customer_id)
                
                log_msg = f"Prueba de modelo: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                log_msg += f"Cliente de prueba: {customer_id}\n"
                
                if 'error' in test_result:
                    log_msg += f"Error: {test_result['error']}\n"
                else:
                    confidence = test_result.get('confidence_score', 0)
                    log_msg += f"Confianza del análisis: {confidence:.0%}\n"
                    
                    churn = test_result.get('churn_prediction', {})
                    if churn:
                        log_msg += f"Predicción churn: {churn.get('churn_probability', 0):.0%}\n"
                    
                    clv = test_result.get('clv_prediction', {})
                    if clv:
                        log_msg += f"CLV predicho: ${clv.get('predicted_clv', 0):,.0f}\n"
                
                log_msg += "Prueba completada exitosamente.\n"
                self.config_log.append(log_msg)
            
        except Exception as e:
            error_msg = f"Error en prueba: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{str(e)}\n"
            self.config_log.append(error_msg)
            logger.error(f"Error probando modelo: {e}")
    
    def export_analysis(self):
        """Exportar análisis actual"""
        if not self.current_analysis:
            self.show_message("No hay análisis disponible para exportar")
            return
        
        try:
            # En implementación real, usar QFileDialog para elegir ubicación
            filename = f"analisis_predictivo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.current_analysis, f, indent=2, ensure_ascii=False, default=str)
            
            self.show_message(f"Análisis exportado a {filename}")
            
        except Exception as e:
            logger.error(f"Error exportando análisis: {e}")
            self.show_message(f"Error al exportar: {e}")
    
    def export_segment_analysis(self):
        """Exportar análisis de segmentos"""
        try:
            if not self.current_analysis:
                self.show_message("No hay análisis de segmentos disponible")
                return
            
            filename = f"segmentos_clientes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.current_analysis, f, indent=2, ensure_ascii=False, default=str)
            
            self.show_message(f"Análisis de segmentos exportado a {filename}")
            
        except Exception as e:
            logger.error(f"Error exportando segmentos: {e}")
    
    def auto_refresh(self):
        """Auto-actualización de datos"""
        if self.tab_widget.currentIndex() == 2:  # Tab de tiempo real
            self.refresh_realtime_predictions()
    
    def _get_risk_color(self, risk_level):
        """Obtener color según nivel de riesgo"""
        colors = {
            'high': "color: red; font-weight: bold;",
            'medium': "color: orange; font-weight: bold;",
            'low': "color: green; font-weight: bold;"
        }
        return colors.get(risk_level, "color: gray;")
    
    def show_message(self, message):
        """Mostrar mensaje al usuario"""
        # En implementación real, usar QMessageBox
        print(f"PredictiveAnalytics: {message}")
        
        # Agregar a log si estamos en tab de configuración
        if self.tab_widget.currentIndex() == 3:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.config_log.append(f"[{timestamp}] {message}")
    
    def closeEvent(self, event):
        """Limpiar recursos al cerrar"""
        if self.analysis_thread and self.analysis_thread.isRunning():
            self.analysis_thread.stop()
            self.analysis_thread.wait()
        
        self.update_timer.stop()
        event.accept()