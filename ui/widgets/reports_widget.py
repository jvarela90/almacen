"""
Widget de Reportes para AlmacénPro
Generación y visualización de reportes de ventas, stock, financieros y análisis
"""

import logging
from datetime import datetime, date, timedelta
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

logger = logging.getLogger(__name__)

class ReportsWidget(QWidget):
    """Widget principal para reportes y análisis"""
    
    def __init__(self, report_manager, sales_manager, product_manager, user_manager, parent=None):
        super().__init__(parent)
        self.report_manager = report_manager
        self.sales_manager = sales_manager
        self.product_manager = product_manager
        self.user_manager = user_manager
        
        self.init_ui()
        self.setup_default_dates()
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header_widget = self.create_header()
        main_layout.addWidget(header_widget)
        
        # Panel principal con tabs
        tabs_widget = self.create_tabs()
        main_layout.addWidget(tabs_widget)
        
        # Aplicar estilos
        self.setup_styles()
    
    def create_header(self) -> QWidget:
        """Crear header"""
        header = QWidget()
        header.setObjectName("header")
        layout = QHBoxLayout(header)
        
        # Título
        title_layout = QVBoxLayout()
        title = QLabel("📊 Centro de Reportes")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2E86AB;")
        title_layout.addWidget(title)
        
        subtitle = QLabel("Análisis completo del negocio con reportes detallados")
        subtitle.setStyleSheet("color: #666; font-size: 12px;")
        title_layout.addWidget(subtitle)
        
        layout.addLayout(title_layout)
        
        layout.addStretch()
        
        # Acciones rápidas
        quick_actions = QHBoxLayout()
        
        quick_sales_btn = QPushButton("📈 Ventas Rápido")
        quick_sales_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
        quick_sales_btn.clicked.connect(self.quick_sales_report)
        quick_actions.addWidget(quick_sales_btn)
        
        quick_stock_btn = QPushButton("📦 Stock Rápido")
        quick_stock_btn.setStyleSheet("background-color: #17a2b8; color: white; font-weight: bold;")
        quick_stock_btn.clicked.connect(self.quick_stock_report)
        quick_actions.addWidget(quick_stock_btn)
        
        export_all_btn = QPushButton("📤 Exportar Todo")
        export_all_btn.clicked.connect(self.export_all_reports)
        quick_actions.addWidget(export_all_btn)
        
        layout.addLayout(quick_actions)
        
        return header
    
    def create_tabs(self) -> QWidget:
        """Crear tabs de reportes"""
        tab_widget = QTabWidget()
        
        # Tab 1: Reportes de ventas
        sales_tab = self.create_sales_reports_tab()
        tab_widget.addTab(sales_tab, "📈 Ventas")
        
        # Tab 2: Reportes de stock
        stock_tab = self.create_stock_reports_tab()
        tab_widget.addTab(stock_tab, "📦 Stock")
        
        # Tab 3: Reportes financieros
        financial_tab = self.create_financial_reports_tab()
        tab_widget.addTab(financial_tab, "💰 Financieros")
        
        # Tab 4: Análisis de clientes
        customers_tab = self.create_customers_analysis_tab()
        tab_widget.addTab(customers_tab, "👥 Clientes")
        
        # Tab 5: Reportes personalizados
        custom_tab = self.create_custom_reports_tab()
        tab_widget.addTab(custom_tab, "🔧 Personalizados")
        
        return tab_widget
    
    def create_sales_reports_tab(self) -> QWidget:
        """Crear tab de reportes de ventas"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filtros comunes
        filters_group = QGroupBox("Filtros de Período")
        filters_layout = QGridLayout(filters_group)
        
        # Fechas
        filters_layout.addWidget(QLabel("Desde:"), 0, 0)
        self.sales_start_date = QDateEdit()
        self.sales_start_date.setCalendarPopup(True)
        self.sales_start_date.setDate(QDate.currentDate().addDays(-30))
        filters_layout.addWidget(self.sales_start_date, 0, 1)
        
        filters_layout.addWidget(QLabel("Hasta:"), 0, 2)
        self.sales_end_date = QDateEdit()
        self.sales_end_date.setCalendarPopup(True)
        self.sales_end_date.setDate(QDate.currentDate())
        filters_layout.addWidget(self.sales_end_date, 0, 3)
        
        # Vendedor
        filters_layout.addWidget(QLabel("Vendedor:"), 1, 0)
        self.sales_seller_combo = QComboBox()
        self.sales_seller_combo.addItem("Todos los vendedores", None)
        filters_layout.addWidget(self.sales_seller_combo, 1, 1)
        
        # Cliente
        filters_layout.addWidget(QLabel("Cliente:"), 1, 2)
        self.sales_customer_combo = QComboBox()
        self.sales_customer_combo.addItem("Todos los clientes", None)
        filters_layout.addWidget(self.sales_customer_combo, 1, 3)
        
        # Botones de período rápido
        quick_period_layout = QHBoxLayout()
        
        today_btn = QPushButton("Hoy")
        today_btn.clicked.connect(lambda: self.set_sales_period(0, 0))
        quick_period_layout.addWidget(today_btn)
        
        week_btn = QPushButton("Última Semana")
        week_btn.clicked.connect(lambda: self.set_sales_period(7, 0))
        quick_period_layout.addWidget(week_btn)
        
        month_btn = QPushButton("Último Mes")
        month_btn.clicked.connect(lambda: self.set_sales_period(30, 0))
        quick_period_layout.addWidget(month_btn)
        
        quarter_btn = QPushButton("Último Trimestre")
        quarter_btn.clicked.connect(lambda: self.set_sales_period(90, 0))
        quick_period_layout.addWidget(quarter_btn)
        
        quick_period_layout.addStretch()
        filters_layout.addLayout(quick_period_layout, 2, 0, 1, 4)
        
        layout.addWidget(filters_group)
        
        # Grid de reportes de ventas
        reports_grid = QGridLayout()
        
        # Reporte general de ventas
        general_sales_card = self.create_report_card(
            "📊 Reporte General de Ventas",
            "Resumen completo con totales, promedios y tendencias",
            "Generar Reporte",
            self.generate_general_sales_report
        )
        reports_grid.addWidget(general_sales_card, 0, 0)
        
        # Ventas por vendedor
        seller_sales_card = self.create_report_card(
            "👤 Ventas por Vendedor",
            "Análisis de desempeño individual de vendedores",
            "Ver Vendedores",
            self.generate_seller_sales_report
        )
        reports_grid.addWidget(seller_sales_card, 0, 1)
        
        # Productos más vendidos
        top_products_card = self.create_report_card(
            "🏆 Top Productos Vendidos",
            "Ranking de productos con mayor rotación",
            "Ver Ranking",
            self.generate_top_products_report
        )
        reports_grid.addWidget(top_products_card, 1, 0)
        
        # Ventas por método de pago
        payment_methods_card = self.create_report_card(
            "💳 Ventas por Método de Pago",
            "Distribución de ventas según forma de pago",
            "Analizar Pagos",
            self.generate_payment_methods_report
        )
        reports_grid.addWidget(payment_methods_card, 1, 1)
        
        # Ventas por hora
        hourly_sales_card = self.create_report_card(
            "🕐 Ventas por Hora",
            "Análisis de horarios pico de ventas",
            "Ver Horarios",
            self.generate_hourly_sales_report
        )
        reports_grid.addWidget(hourly_sales_card, 2, 0)
        
        # Comparativo de períodos
        comparative_card = self.create_report_card(
            "⚖️ Comparativo de Períodos",
            "Comparación con períodos anteriores",
            "Comparar",
            self.generate_comparative_report
        )
        reports_grid.addWidget(comparative_card, 2, 1)
        
        layout.addLayout(reports_grid)
        
        return widget
    
    def create_stock_reports_tab(self) -> QWidget:
        """Crear tab de reportes de stock"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filtros de stock
        stock_filters_group = QGroupBox("Filtros de Stock")
        stock_filters_layout = QGridLayout(stock_filters_group)
        
        # Categoría
        stock_filters_layout.addWidget(QLabel("Categoría:"), 0, 0)
        self.stock_category_combo = QComboBox()
        self.stock_category_combo.addItem("Todas las categorías", None)
        stock_filters_layout.addWidget(self.stock_category_combo, 0, 1)
        
        # Proveedor
        stock_filters_layout.addWidget(QLabel("Proveedor:"), 0, 2)
        self.stock_provider_combo = QComboBox()
        self.stock_provider_combo.addItem("Todos los proveedores", None)
        stock_filters_layout.addWidget(self.stock_provider_combo, 0, 3)
        
        # Estado de stock
        stock_filters_layout.addWidget(QLabel("Estado:"), 1, 0)
        self.stock_status_combo = QComboBox()
        self.stock_status_combo.addItems([
            "Todos", "Stock OK", "Stock Bajo", "Sin Stock", "Sobrestock"
        ])
        stock_filters_layout.addWidget(self.stock_status_combo, 1, 1)
        
        # Incluir movimientos
        self.include_movements_cb = QCheckBox("Incluir historial de movimientos")
        stock_filters_layout.addWidget(self.include_movements_cb, 1, 2, 1, 2)
        
        layout.addWidget(stock_filters_group)
        
        # Grid de reportes de stock
        stock_reports_grid = QGridLayout()
        
        # Inventario completo
        inventory_card = self.create_report_card(
            "📋 Inventario Completo",
            "Lista detallada de todos los productos y stock",
            "Generar Inventario",
            self.generate_inventory_report
        )
        stock_reports_grid.addWidget(inventory_card, 0, 0)
        
        # Stock bajo y alertas
        low_stock_card = self.create_report_card(
            "⚠️ Alertas de Stock",
            "Productos con stock bajo o sin stock",
            "Ver Alertas",
            self.generate_low_stock_report
        )
        stock_reports_grid.addWidget(low_stock_card, 0, 1)
        
        # Valorización de stock
        valuation_card = self.create_report_card(
            "💎 Valorización de Stock",
            "Valor actual del inventario por costo y venta",
            "Calcular Valor",
            self.generate_stock_valuation_report
        )
        stock_reports_grid.addWidget(valuation_card, 1, 0)
        
        # Rotación de inventario
        turnover_card = self.create_report_card(
            "🔄 Rotación de Inventario",
            "Análisis de rotación y productos de lento movimiento",
            "Analizar Rotación",
            self.generate_inventory_turnover_report
        )
        stock_reports_grid.addWidget(turnover_card, 1, 1)
        
        # Movimientos de stock
        movements_card = self.create_report_card(
            "📈 Movimientos de Stock",
            "Historial detallado de entradas y salidas",
            "Ver Movimientos",
            self.generate_stock_movements_report
        )
        stock_reports_grid.addWidget(movements_card, 2, 0)
        
        # Análisis ABC
        abc_card = self.create_report_card(
            "🔤 Análisis ABC",
            "Clasificación de productos por valor e importancia",
            "Clasificar ABC",
            self.generate_abc_analysis_report
        )
        stock_reports_grid.addWidget(abc_card, 2, 1)
        
        layout.addLayout(stock_reports_grid)
        
        return widget
    
    def create_financial_reports_tab(self) -> QWidget:
        """Crear tab de reportes financieros"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filtros financieros
        financial_filters_group = QGroupBox("Período Financiero")
        financial_filters_layout = QGridLayout(financial_filters_group)
        
        # Fechas
        financial_filters_layout.addWidget(QLabel("Desde:"), 0, 0)
        self.financial_start_date = QDateEdit()
        self.financial_start_date.setCalendarPopup(True)
        self.financial_start_date.setDate(QDate.currentDate().addDays(-30))
        financial_filters_layout.addWidget(self.financial_start_date, 0, 1)
        
        financial_filters_layout.addWidget(QLabel("Hasta:"), 0, 2)
        self.financial_end_date = QDateEdit()
        self.financial_end_date.setCalendarPopup(True)
        self.financial_end_date.setDate(QDate.currentDate())
        financial_filters_layout.addWidget(self.financial_end_date, 0, 3)
        
        # Opciones
        self.include_taxes_cb = QCheckBox("Incluir análisis de impuestos")
        self.include_taxes_cb.setChecked(True)
        financial_filters_layout.addWidget(self.include_taxes_cb, 1, 0, 1, 2)
        
        self.include_projections_cb = QCheckBox("Incluir proyecciones")
        financial_filters_layout.addWidget(self.include_projections_cb, 1, 2, 1, 2)
        
        layout.addWidget(financial_filters_group)
        
        # Grid de reportes financieros
        financial_reports_grid = QGridLayout()
        
        # Estado financiero
        financial_status_card = self.create_report_card(
            "💰 Estado Financiero",
            "Resumen completo de ingresos, egresos y rentabilidad",
            "Ver Estado",
            self.generate_financial_status_report
        )
        financial_reports_grid.addWidget(financial_status_card, 0, 0)
        
        # Flujo de caja
        cash_flow_card = self.create_report_card(
            "💸 Flujo de Caja",
            "Análisis detallado del movimiento de efectivo",
            "Ver Flujo",
            self.generate_cash_flow_report
        )
        financial_reports_grid.addWidget(cash_flow_card, 0, 1)
        
        # Cuentas por cobrar
        accounts_receivable_card = self.create_report_card(
            "📋 Cuentas por Cobrar",
            "Estado de deudas de clientes y cuenta corriente",
            "Ver Cuentas",
            self.generate_accounts_receivable_report
        )
        financial_reports_grid.addWidget(accounts_receivable_card, 1, 0)
        
        # Rentabilidad por producto
        profitability_card = self.create_report_card(
            "📊 Rentabilidad por Producto",
            "Análisis de margen y rentabilidad individual",
            "Analizar Rentabilidad",
            self.generate_profitability_report
        )
        financial_reports_grid.addWidget(profitability_card, 1, 1)
        
        # Costos operativos
        costs_card = self.create_report_card(
            "📉 Análisis de Costos",
            "Desglose detallado de costos operativos",
            "Ver Costos",
            self.generate_costs_analysis_report
        )
        financial_reports_grid.addWidget(costs_card, 2, 0)
        
        # Proyecciones
        projections_card = self.create_report_card(
            "🔮 Proyecciones Financieras",
            "Estimaciones y tendencias futuras",
            "Ver Proyecciones",
            self.generate_financial_projections_report
        )
        financial_reports_grid.addWidget(projections_card, 2, 1)
        
        layout.addLayout(financial_reports_grid)
        
        return widget
    
    def create_customers_analysis_tab(self) -> QWidget:
        """Crear tab de análisis de clientes"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filtros de clientes
        customers_filters_group = QGroupBox("Filtros de Análisis")
        customers_filters_layout = QGridLayout(customers_filters_group)
        
        # Período
        customers_filters_layout.addWidget(QLabel("Desde:"), 0, 0)
        self.customers_start_date = QDateEdit()
        self.customers_start_date.setCalendarPopup(True)
        self.customers_start_date.setDate(QDate.currentDate().addDays(-90))
        customers_filters_layout.addWidget(self.customers_start_date, 0, 1)
        
        customers_filters_layout.addWidget(QLabel("Hasta:"), 0, 2)
        self.customers_end_date = QDateEdit()
        self.customers_end_date.setCalendarPopup(True)
        self.customers_end_date.setDate(QDate.currentDate())
        customers_filters_layout.addWidget(self.customers_end_date, 0, 3)
        
        # Tipo de cliente
        customers_filters_layout.addWidget(QLabel("Tipo:"), 1, 0)
        self.customer_type_combo = QComboBox()
        self.customer_type_combo.addItems([
            "Todos", "Minoristas", "Mayoristas", "Cuenta Corriente", "Ocasionales"
        ])
        customers_filters_layout.addWidget(self.customer_type_combo, 1, 1)
        
        # Monto mínimo
        customers_filters_layout.addWidget(QLabel("Compra Mínima:"), 1, 2)
        self.min_purchase_input = QDoubleSpinBox()
        self.min_purchase_input.setMinimum(0)
        self.min_purchase_input.setMaximum(999999)
        self.min_purchase_input.setPrefix("$ ")
        customers_filters_layout.addWidget(self.min_purchase_input, 1, 3)
        
        layout.addWidget(customers_filters_group)
        
        # Grid de análisis de clientes
        customers_reports_grid = QGridLayout()
        
        # Top clientes
        top_customers_card = self.create_report_card(
            "🏆 Top Clientes",
            "Clientes más valiosos por volumen de compras",
            "Ver Top Clientes",
            self.generate_top_customers_report
        )
        customers_reports_grid.addWidget(top_customers_card, 0, 0)
        
        # Segmentación de clientes
        segmentation_card = self.create_report_card(
            "📊 Segmentación de Clientes",
            "Clasificación por comportamiento de compra",
            "Segmentar",
            self.generate_customer_segmentation_report
        )
        customers_reports_grid.addWidget(segmentation_card, 0, 1)
        
        # Análisis de retención
        retention_card = self.create_report_card(
            "🔄 Análisis de Retención",
            "Tasa de retención y clientes perdidos",
            "Analizar Retención",
            self.generate_customer_retention_report
        )
        customers_reports_grid.addWidget(retention_card, 1, 0)
        
        # Productos favoritos por cliente
        preferences_card = self.create_report_card(
            "❤️ Preferencias de Productos",
            "Productos más comprados por segmento",
            "Ver Preferencias",
            self.generate_customer_preferences_report
        )
        customers_reports_grid.addWidget(preferences_card, 1, 1)
        
        # Análisis de frecuencia
        frequency_card = self.create_report_card(
            "📅 Frecuencia de Compra",
            "Patrones de frecuencia y estacionalidad",
            "Analizar Frecuencia",
            self.generate_purchase_frequency_report
        )
        customers_reports_grid.addWidget(frequency_card, 2, 0)
        
        # Clientes inactivos
        inactive_card = self.create_report_card(
            "😴 Clientes Inactivos",
            "Identificar clientes que no compran",
            "Ver Inactivos",
            self.generate_inactive_customers_report
        )
        customers_reports_grid.addWidget(inactive_card, 2, 1)
        
        layout.addLayout(customers_reports_grid)
        
        return widget
    
    def create_custom_reports_tab(self) -> QWidget:
        """Crear tab de reportes personalizados"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Constructor de consultas
        query_builder_group = QGroupBox("Constructor de Reportes Personalizados")
        query_builder_layout = QVBoxLayout(query_builder_group)
        
        # Selector de datos
        data_selector_layout = QGridLayout()
        
        data_selector_layout.addWidget(QLabel("Tabla Principal:"), 0, 0)
        self.main_table_combo = QComboBox()
        self.main_table_combo.addItems([
            "Ventas", "Productos", "Clientes", "Proveedores", "Compras", "Movimientos Stock"
        ])
        data_selector_layout.addWidget(self.main_table_combo, 0, 1)
        
        data_selector_layout.addWidget(QLabel("Campos:"), 0, 2)
        self.fields_combo = QComboBox()
        self.fields_combo.setEditable(True)
        data_selector_layout.addWidget(self.fields_combo, 0, 3)
        
        data_selector_layout.addWidget(QLabel("Agrupado por:"), 1, 0)
        self.group_by_combo = QComboBox()
        self.group_by_combo.addItems([
            "Sin agrupar", "Fecha", "Producto", "Cliente", "Vendedor", "Categoría"
        ])
        data_selector_layout.addWidget(self.group_by_combo, 1, 1)
        
        data_selector_layout.addWidget(QLabel("Ordenado por:"), 1, 2)
        self.order_by_combo = QComboBox()
        self.order_by_combo.addItems([
            "Fecha DESC", "Fecha ASC", "Total DESC", "Total ASC", "Nombre ASC"
        ])
        data_selector_layout.addWidget(self.order_by_combo, 1, 3)
        
        query_builder_layout.addLayout(data_selector_layout)
        
        # Filtros personalizados
        custom_filters_layout = QHBoxLayout()
        
        custom_filters_layout.addWidget(QLabel("Filtros:"))
        self.custom_filter_input = QLineEdit()
        self.custom_filter_input.setPlaceholderText("Ej: fecha >= '2024-01-01' AND total > 100")
        custom_filters_layout.addWidget(self.custom_filter_input)
        
        query_builder_layout.addLayout(custom_filters_layout)
        
        # Vista previa de consulta
        self.query_preview = QTextEdit()
        self.query_preview.setMaximumHeight(100)
        self.query_preview.setPlaceholderText("Vista previa de la consulta SQL...")
        self.query_preview.setReadOnly(True)
        query_builder_layout.addWidget(self.query_preview)
        
        # Botones
        custom_buttons_layout = QHBoxLayout()
        
        preview_query_btn = QPushButton("👁️ Vista Previa")
        preview_query_btn.clicked.connect(self.preview_custom_query)
        custom_buttons_layout.addWidget(preview_query_btn)
        
        generate_custom_btn = QPushButton("▶️ Ejecutar Reporte")
        generate_custom_btn.setStyleSheet("background-color: #007bff; color: white; font-weight: bold;")
        generate_custom_btn.clicked.connect(self.generate_custom_report)
        custom_buttons_layout.addWidget(generate_custom_btn)
        
        save_template_btn = QPushButton("💾 Guardar Plantilla")
        save_template_btn.clicked.connect(self.save_report_template)
        custom_buttons_layout.addWidget(save_template_btn)
        
        custom_buttons_layout.addStretch()
        query_builder_layout.addLayout(custom_buttons_layout)
        
        layout.addWidget(query_builder_group)
        
        # Plantillas guardadas
        templates_group = QGroupBox("Plantillas Guardadas")
        templates_layout = QVBoxLayout(templates_group)
        
        self.templates_list = QListWidget()
        self.templates_list.addItems([
            "📊 Ventas por Vendedor - Últimos 30 días",
            "📦 Stock Crítico por Categoría", 
            "💰 Rentabilidad Mensual",
            "👥 Top 20 Clientes del Trimestre",
            "🔄 Rotación de Inventario Anual"
        ])
        self.templates_list.itemDoubleClicked.connect(self.load_template)
        templates_layout.addWidget(self.templates_list)
        
        templates_buttons_layout = QHBoxLayout()
        
        load_template_btn = QPushButton("📥 Cargar Plantilla")
        load_template_btn.clicked.connect(self.load_selected_template)
        templates_buttons_layout.addWidget(load_template_btn)
        
        edit_template_btn = QPushButton("✏️ Editar")
        edit_template_btn.clicked.connect(self.edit_template)
        templates_buttons_layout.addWidget(edit_template_btn)
        
        delete_template_btn = QPushButton("🗑️ Eliminar")
        delete_template_btn.setStyleSheet("background-color: #dc3545; color: white;")
        delete_template_btn.clicked.connect(self.delete_template)
        templates_buttons_layout.addWidget(delete_template_btn)
        
        templates_buttons_layout.addStretch()
        templates_layout.addLayout(templates_buttons_layout)
        
        layout.addWidget(templates_group)
        
        return widget
    
    def create_report_card(self, title: str, description: str, 
                          button_text: str, callback) -> QWidget:
        """Crear tarjeta de reporte"""
        card = QWidget()
        card.setFixedSize(300, 120)
        card.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                margin: 5px;
            }
            QWidget:hover {
                border-color: #2E86AB;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Título
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2E86AB;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Descripción
        desc_label = QLabel(description)
        desc_label.setStyleSheet("font-size: 11px; color: #666;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        layout.addStretch()
        
        # Botón
        button = QPushButton(button_text)
        button.setStyleSheet("""
            QPushButton {
                background-color: #2E86AB;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1e5f7a;
            }
        """)
        button.clicked.connect(callback)
        layout.addWidget(button)
        
        return card
    
    def setup_styles(self):
        """Configurar estilos CSS"""
        self.setStyleSheet("""
            QWidget#header {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 10px;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2E86AB;
            }
            
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit {
                padding: 6px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
            
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, 
            QDoubleSpinBox:focus, QDateEdit:focus, QTextEdit:focus {
                border-color: #2E86AB;
                outline: none;
            }
            
            QPushButton {
                padding: 8px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                background-color: #f8f9fa;
            }
            
            QPushButton:hover {
                background-color: #e9ecef;
            }
            
            QListWidget {
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
            
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f8f9fa;
            }
            
            QListWidget::item:hover {
                background-color: #e9ecef;
            }
            
            QListWidget::item:selected {
                background-color: #2E86AB;
                color: white;
            }
            
            QTabWidget::pane {
                border: 1px solid #ced4da;
                background-color: white;
                border-radius: 4px;
            }
            
            QTabBar::tab {
                background-color: #e9ecef;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
        """)
    
    def setup_default_dates(self):
        """Configurar fechas por defecto"""
        # Configurar todas las fechas por defecto
        current_date = QDate.currentDate()
        month_ago = current_date.addDays(-30)
        
        # Sincronizar todas las fechas de inicio
        self.sales_start_date.setDate(month_ago)
        self.financial_start_date.setDate(month_ago)
        
        # Fechas de fin al día actual
        self.sales_end_date.setDate(current_date)
        self.financial_end_date.setDate(current_date)
    
    def set_sales_period(self, days_back: int, days_forward: int = 0):
        """Establecer período para reportes de ventas"""
        end_date = QDate.currentDate().addDays(days_forward)
        start_date = end_date.addDays(-days_back) if days_back > 0 else end_date
        
        self.sales_start_date.setDate(start_date)
        self.sales_end_date.setDate(end_date)
    
    # ===========================================
    # MÉTODOS DE GENERACIÓN DE REPORTES
    # ===========================================
    
    def show_report_result(self, title: str, data: dict, format_type: str = "table"):
        """Mostrar resultado de reporte en ventana modal"""
        dialog = ReportResultDialog(title, data, format_type, self)
        dialog.exec_()
    
    # Reportes de Ventas
    def quick_sales_report(self):
        """Generar reporte rápido de ventas del día"""
        try:
            today = date.today().isoformat()
            summary = self.sales_manager.get_daily_sales_summary(today)
            self.show_report_result("📈 Resumen de Ventas del Día", summary)
        except Exception as e:
            self.show_error("Error generando reporte rápido de ventas", str(e))
    
    def generate_general_sales_report(self):
        """Generar reporte general de ventas"""
        try:
            start_date = self.sales_start_date.date().toString('yyyy-MM-dd')
            end_date = self.sales_end_date.date().toString('yyyy-MM-dd')
            
            report_data = self.report_manager.generate_sales_report(start_date, end_date)
            self.show_report_result("📊 Reporte General de Ventas", report_data)
        except Exception as e:
            self.show_error("Error generando reporte de ventas", str(e))
    
    def generate_seller_sales_report(self):
        """Generar reporte de ventas por vendedor"""
        QMessageBox.information(self, "Reporte", "Reporte de ventas por vendedor - En desarrollo")
    
    def generate_top_products_report(self):
        """Generar reporte de productos más vendidos"""
        QMessageBox.information(self, "Reporte", "Top productos vendidos - En desarrollo")
    
    def generate_payment_methods_report(self):
        """Generar reporte de métodos de pago"""
        QMessageBox.information(self, "Reporte", "Métodos de pago - En desarrollo")
    
    def generate_hourly_sales_report(self):
        """Generar reporte de ventas por hora"""
        QMessageBox.information(self, "Reporte", "Ventas por hora - En desarrollo")
    
    def generate_comparative_report(self):
        """Generar reporte comparativo"""
        QMessageBox.information(self, "Reporte", "Reporte comparativo - En desarrollo")
    
    # Reportes de Stock
    def quick_stock_report(self):
        """Generar reporte rápido de stock"""
        try:
            stats = self.product_manager.get_product_stats()
            self.show_report_result("📦 Resumen Rápido de Stock", stats)
        except Exception as e:
            self.show_error("Error generando reporte rápido de stock", str(e))
    
    def generate_inventory_report(self):
        """Generar reporte de inventario"""
        try:
            report_data = self.report_manager.generate_stock_report(
                include_movement_history=self.include_movements_cb.isChecked()
            )
            self.show_report_result("📋 Reporte de Inventario", report_data)
        except Exception as e:
            self.show_error("Error generando reporte de inventario", str(e))
    
    def generate_low_stock_report(self):
        """Generar reporte de stock bajo"""
        QMessageBox.information(self, "Reporte", "Reporte de stock bajo - En desarrollo")
    
    def generate_stock_valuation_report(self):
        """Generar reporte de valorización"""
        QMessageBox.information(self, "Reporte", "Valorización de stock - En desarrollo")
    
    def generate_inventory_turnover_report(self):
        """Generar reporte de rotación"""
        try:
            report_data = self.report_manager.generate_inventory_turnover_report()
            self.show_report_result("🔄 Reporte de Rotación de Inventario", report_data)
        except Exception as e:
            self.show_error("Error generando reporte de rotación", str(e))
    
    def generate_stock_movements_report(self):
        """Generar reporte de movimientos"""
        QMessageBox.information(self, "Reporte", "Movimientos de stock - En desarrollo")
    
    def generate_abc_analysis_report(self):
        """Generar análisis ABC"""
        QMessageBox.information(self, "Reporte", "Análisis ABC - En desarrollo")
    
    # Reportes Financieros
    def generate_financial_status_report(self):
        """Generar reporte de estado financiero"""
        try:
            start_date = self.financial_start_date.date().toString('yyyy-MM-dd')
            end_date = self.financial_end_date.date().toString('yyyy-MM-dd')
            
            report_data = self.report_manager.generate_financial_report(start_date, end_date)
            self.show_report_result("💰 Estado Financiero", report_data)
        except Exception as e:
            self.show_error("Error generando reporte financiero", str(e))
    
    def generate_cash_flow_report(self):
        """Generar reporte de flujo de caja"""
        QMessageBox.information(self, "Reporte", "Flujo de caja - En desarrollo")
    
    def generate_accounts_receivable_report(self):
        """Generar reporte de cuentas por cobrar"""
        QMessageBox.information(self, "Reporte", "Cuentas por cobrar - En desarrollo")
    
    def generate_profitability_report(self):
        """Generar reporte de rentabilidad"""
        QMessageBox.information(self, "Reporte", "Rentabilidad - En desarrollo")
    
    def generate_costs_analysis_report(self):
        """Generar análisis de costos"""
        QMessageBox.information(self, "Reporte", "Análisis de costos - En desarrollo")
    
    def generate_financial_projections_report(self):
        """Generar proyecciones financieras"""
        QMessageBox.information(self, "Reporte", "Proyecciones financieras - En desarrollo")
    
    # Análisis de Clientes
    def generate_top_customers_report(self):
        """Generar reporte de top clientes"""
        QMessageBox.information(self, "Reporte", "Top clientes - En desarrollo")
    
    def generate_customer_segmentation_report(self):
        """Generar segmentación de clientes"""
        try:
            start_date = self.customers_start_date.date().toString('yyyy-MM-dd')
            end_date = self.customers_end_date.date().toString('yyyy-MM-dd')
            
            report_data = self.report_manager.generate_customer_analysis(start_date, end_date)
            self.show_report_result("📊 Análisis de Clientes", report_data)
        except Exception as e:
            self.show_error("Error generando análisis de clientes", str(e))
    
    def generate_customer_retention_report(self):
        """Generar análisis de retención"""
        QMessageBox.information(self, "Reporte", "Retención de clientes - En desarrollo")
    
    def generate_customer_preferences_report(self):
        """Generar preferencias de clientes"""
        QMessageBox.information(self, "Reporte", "Preferencias de clientes - En desarrollo")
    
    def generate_purchase_frequency_report(self):
        """Generar análisis de frecuencia"""
        QMessageBox.information(self, "Reporte", "Frecuencia de compra - En desarrollo")
    
    def generate_inactive_customers_report(self):
        """Generar reporte de clientes inactivos"""
        QMessageBox.information(self, "Reporte", "Clientes inactivos - En desarrollo")
    
    # Reportes Personalizados
    def preview_custom_query(self):
        """Vista previa de consulta personalizada"""
        # Construir consulta SQL básica
        table = self.main_table_combo.currentText().lower()
        fields = self.fields_combo.currentText() or "*"
        group_by = self.group_by_combo.currentText()
        order_by = self.order_by_combo.currentText()
        filters = self.custom_filter_input.text()
        
        query = f"SELECT {fields} FROM {table}"
        
        if filters:
            query += f" WHERE {filters}"
        
        if group_by != "Sin agrupar":
            query += f" GROUP BY {group_by.lower()}"
        
        if order_by != "Sin ordenar":
            query += f" ORDER BY {order_by.lower()}"
        
        self.query_preview.setText(query)
    
    def generate_custom_report(self):
        """Generar reporte personalizado"""
        QMessageBox.information(self, "Reporte", "Reporte personalizado - En desarrollo")
    
    def save_report_template(self):
        """Guardar plantilla de reporte"""
        QMessageBox.information(self, "Plantilla", "Guardar plantilla - En desarrollo")
    
    def load_template(self, item):
        """Cargar plantilla seleccionada"""
        template_name = item.text()
        QMessageBox.information(self, "Plantilla", f"Cargar: {template_name}")
    
    def load_selected_template(self):
        """Cargar plantilla seleccionada"""
        current_item = self.templates_list.currentItem()
        if current_item:
            self.load_template(current_item)
    
    def edit_template(self):
        """Editar plantilla"""
        QMessageBox.information(self, "Plantilla", "Editar plantilla - En desarrollo")
    
    def delete_template(self):
        """Eliminar plantilla"""
        current_item = self.templates_list.currentItem()
        if current_item:
            reply = QMessageBox.question(self, "Eliminar Plantilla", 
                f"¿Eliminar la plantilla '{current_item.text()}'?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                row = self.templates_list.row(current_item)
                self.templates_list.takeItem(row)
    
    def export_all_reports(self):
        """Exportar todos los reportes"""
        QMessageBox.information(self, "Exportar", "Exportar todos los reportes - En desarrollo")
    
    def show_error(self, title: str, message: str):
        """Mostrar error"""
        QMessageBox.critical(self, title, message)


class ReportResultDialog(QDialog):
    """Diálogo para mostrar resultados de reportes"""
    
    def __init__(self, title: str, data: dict, format_type: str = "table", parent=None):
        super().__init__(parent)
        self.title = title
        self.data = data
        self.format_type = format_type
        self.init_ui()
    
    def init_ui(self):
        """Inicializar interfaz"""
        self.setWindowTitle(self.title)
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel(self.title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2E86AB;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Botones de exportación
        export_pdf_btn = QPushButton("📄 PDF")
        export_pdf_btn.clicked.connect(self.export_pdf)
        header_layout.addWidget(export_pdf_btn)
        
        export_excel_btn = QPushButton("📊 Excel")
        export_excel_btn.clicked.connect(self.export_excel)
        header_layout.addWidget(export_excel_btn)
        
        print_btn = QPushButton("🖨️ Imprimir")
        print_btn.clicked.connect(self.print_report)
        header_layout.addWidget(print_btn)
        
        layout.addLayout(header_layout)
        
        # Contenido del reporte
        self.content_area = QScrollArea()
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        
        self.display_report_data()
        
        self.content_area.setWidget(self.content_widget)
        self.content_area.setWidgetResizable(True)
        layout.addWidget(self.content_area)
        
        # Botón cerrar
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def display_report_data(self):
        """Mostrar datos del reporte"""
        try:
            if isinstance(self.data, dict):
                for key, value in self.data.items():
                    if isinstance(value, dict):
                        # Mostrar como tabla si tiene estructura tabular
                        self.add_section_title(key.replace('_', ' ').title())
                        self.add_dict_table(value)
                    elif isinstance(value, list):
                        # Mostrar como lista
                        self.add_section_title(key.replace('_', ' ').title())
                        self.add_list_table(value)
                    else:
                        # Mostrar como texto simple
                        self.add_simple_value(key.replace('_', ' ').title(), str(value))
            else:
                # Mostrar como texto plano
                content_label = QLabel(str(self.data))
                content_label.setWordWrap(True)
                self.content_layout.addWidget(content_label)
                
        except Exception as e:
            error_label = QLabel(f"Error mostrando datos: {str(e)}")
            error_label.setStyleSheet("color: red;")
            self.content_layout.addWidget(error_label)
    
    def add_section_title(self, title: str):
        """Agregar título de sección"""
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #2E86AB; 
            padding: 10px 0 5px 0;
            border-bottom: 1px solid #e9ecef;
        """)
        self.content_layout.addWidget(title_label)
    
    def add_dict_table(self, data_dict: dict):
        """Agregar tabla desde diccionario"""
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Campo", "Valor"])
        table.setRowCount(len(data_dict))
        
        for i, (key, value) in enumerate(data_dict.items()):
            table.setItem(i, 0, QTableWidgetItem(str(key).replace('_', ' ').title()))
            table.setItem(i, 1, QTableWidgetItem(str(value)))
        
        table.resizeColumnsToContents()
        table.setMaximumHeight(min(300, (len(data_dict) + 1) * 30))
        self.content_layout.addWidget(table)
    
    def add_list_table(self, data_list: list):
        """Agregar tabla desde lista"""
        if not data_list:
            no_data_label = QLabel("No hay datos disponibles")
            no_data_label.setStyleSheet("color: #666; font-style: italic;")
            self.content_layout.addWidget(no_data_label)
            return
        
        # Asumir que es una lista de diccionarios
        if isinstance(data_list[0], dict):
            headers = list(data_list[0].keys())
            
            table = QTableWidget()
            table.setColumnCount(len(headers))
            table.setHorizontalHeaderLabels([h.replace('_', ' ').title() for h in headers])
            table.setRowCount(len(data_list))
            
            for i, row_data in enumerate(data_list):
                for j, header in enumerate(headers):
                    value = str(row_data.get(header, ''))
                    table.setItem(i, j, QTableWidgetItem(value))
            
            table.resizeColumnsToContents()
            table.setMaximumHeight(min(400, (len(data_list) + 1) * 30))
            self.content_layout.addWidget(table)
        else:
            # Lista simple
            for item in data_list[:20]:  # Limitar a 20 items
                item_label = QLabel(f"• {str(item)}")
                self.content_layout.addWidget(item_label)
    
    def add_simple_value(self, key: str, value: str):
        """Agregar valor simple"""
        layout = QHBoxLayout()
        
        key_label = QLabel(f"{key}:")
        key_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(key_label)
        
        value_label = QLabel(value)
        layout.addWidget(value_label)
        
        layout.addStretch()
        
        widget = QWidget()
        widget.setLayout(layout)
        self.content_layout.addWidget(widget)
    
    def export_pdf(self):
        """Exportar a PDF"""
        QMessageBox.information(self, "Exportar", "Exportar a PDF - En desarrollo")
    
    def export_excel(self):
        """Exportar a Excel"""
        QMessageBox.information(self, "Exportar", "Exportar a Excel - En desarrollo")
    
    def print_report(self):
        """Imprimir reporte"""
        QMessageBox.information(self, "Imprimir", "Imprimir reporte - En desarrollo")