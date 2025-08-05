"""
Dashboard Widget para AlmacénPro
Panel ejecutivo con métricas, estadísticas y información del sistema en tiempo real
"""

import logging
from datetime import datetime, date, timedelta
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

logger = logging.getLogger(__name__)

class DashboardWidget(QWidget):
    """Widget principal del dashboard ejecutivo"""
    
    def __init__(self, managers: dict, current_user: dict, parent=None):
        super().__init__(parent)
        
        self.managers = managers
        self.current_user = current_user
        
        # Datos del dashboard
        self.dashboard_data = {}
        
        self.init_ui()
        self.load_dashboard_data()
        
        # Timer para actualización automática
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(300000)  # 5 minutos
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header del dashboard
        header_widget = self.create_header()
        main_layout.addWidget(header_widget)
        
        # Panel de métricas principales
        metrics_widget = self.create_metrics_panel()
        main_layout.addWidget(metrics_widget)
        
        # Panel inferior con detalles
        details_layout = QHBoxLayout()
        
        # Panel izquierdo: Ventas recientes y productos top
        left_panel = self.create_left_panel()
        details_layout.addWidget(left_panel, 2)
        
        # Panel derecho: Alertas y estadísticas
        right_panel = self.create_right_panel()
        details_layout.addWidget(right_panel, 1)
        
        main_layout.addLayout(details_layout)
        
        # Aplicar estilos
        self.setup_styles()
    
    def create_header(self) -> QWidget:
        """Crear header del dashboard"""
        header = QWidget()
        header.setObjectName("dashboard_header")
        layout = QHBoxLayout(header)
        
        # Título y fecha
        title_layout = QVBoxLayout()
        
        title = QLabel("📊 Dashboard Ejecutivo")
        title.setObjectName("dashboard_title")
        title_layout.addWidget(title)
        
        current_date = datetime.now().strftime("%A, %d de %B de %Y")
        date_label = QLabel(current_date)
        date_label.setObjectName("dashboard_date")
        title_layout.addWidget(date_label)
        
        layout.addLayout(title_layout)
        
        layout.addStretch()
        
        # Botón de actualizar
        refresh_btn = QPushButton("🔄 Actualizar")
        refresh_btn.setObjectName("refresh_button")
        refresh_btn.clicked.connect(self.refresh_data)
        layout.addWidget(refresh_btn)
        
        return header
    
    def create_metrics_panel(self) -> QWidget:
        """Crear panel de métricas principales"""
        panel = QWidget()
        panel.setObjectName("metrics_panel")
        layout = QGridLayout(panel)
        layout.setSpacing(15)
        
        # Métricas principales
        metrics = [
            ("ventas_hoy", "💰 Ventas Hoy", "#27ae60", "Total de ventas del día actual"),
            ("productos_vendidos", "📦 Productos Vendidos", "#3498db", "Cantidad de productos vendidos hoy"),
            ("stock_bajo", "⚠️ Stock Bajo", "#e74c3c", "Productos con stock por debajo del mínimo"),
            ("clientes_activos", "👥 Clientes del Mes", "#9b59b6", "Clientes que compraron este mes")
        ]
        
        row, col = 0, 0
        for metric_key, title, color, tooltip in metrics:
            metric_card = self.create_metric_card(metric_key, title, color, tooltip)
            layout.addWidget(metric_card, row, col)
            
            col += 1
            if col >= 4:
                col = 0
                row += 1
        
        return panel
    
    def create_metric_card(self, key: str, title: str, color: str, tooltip: str) -> QWidget:
        """Crear tarjeta de métrica individual"""
        card = QFrame()
        card.setObjectName("metric_card")
        card.setToolTip(tooltip)
        card.setFrameStyle(QFrame.StyledPanel)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Título
        title_label = QLabel(title)
        title_label.setObjectName("metric_title")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Valor principal
        value_label = QLabel("...")
        value_label.setObjectName(f"metric_value_{key}")
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: bold;")
        layout.addWidget(value_label)
        
        # Texto adicional
        detail_label = QLabel("")
        detail_label.setObjectName(f"metric_detail_{key}")
        detail_label.setAlignment(Qt.AlignCenter)
        detail_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        layout.addWidget(detail_label)
        
        # Guardar referencia para actualizar
        setattr(self, f"metric_{key}_value", value_label)
        setattr(self, f"metric_{key}_detail", detail_label)
        
        return card
    
    def create_left_panel(self) -> QWidget:
        """Crear panel izquierdo con tablas"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # Ventas recientes
        recent_sales_group = QGroupBox("💳 Ventas Recientes")
        recent_sales_layout = QVBoxLayout(recent_sales_group)
        
        self.recent_sales_table = QTableWidget()
        self.recent_sales_table.setColumnCount(4)
        self.recent_sales_table.setHorizontalHeaderLabels(["Fecha", "Cliente", "Total", "Estado"])
        self.recent_sales_table.horizontalHeader().setStretchLastSection(True)
        self.recent_sales_table.setMaximumHeight(200)
        self.recent_sales_table.setAlternatingRowColors(True)
        self.recent_sales_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        recent_sales_layout.addWidget(self.recent_sales_table)
        layout.addWidget(recent_sales_group)
        
        # Productos más vendidos
        top_products_group = QGroupBox("🔥 Productos Más Vendidos")
        top_products_layout = QVBoxLayout(top_products_group)
        
        self.top_products_table = QTableWidget()
        self.top_products_table.setColumnCount(3)
        self.top_products_table.setHorizontalHeaderLabels(["Producto", "Cantidad", "Ingresos"])
        self.top_products_table.horizontalHeader().setStretchLastSection(True)
        self.top_products_table.setMaximumHeight(200)
        self.top_products_table.setAlternatingRowColors(True)
        
        top_products_layout.addWidget(self.top_products_table)
        layout.addWidget(top_products_group)
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Crear panel derecho con alertas y estadísticas"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # Alertas del sistema
        alerts_group = QGroupBox("🚨 Alertas del Sistema")
        alerts_layout = QVBoxLayout(alerts_group)
        
        self.alerts_list = QListWidget()
        self.alerts_list.setMaximumHeight(150)
        
        alerts_layout.addWidget(self.alerts_list)
        layout.addWidget(alerts_group)
        
        # Gráfico de ventas de la semana (placeholder)
        chart_group = QGroupBox("📈 Ventas de la Semana")
        chart_layout = QVBoxLayout(chart_group)
        
        # Por ahora un placeholder, se puede implementar con matplotlib o QChart
        chart_placeholder = QLabel("Gráfico de ventas\n(En desarrollo)")
        chart_placeholder.setAlignment(Qt.AlignCenter)
        chart_placeholder.setMinimumHeight(150)
        chart_placeholder.setStyleSheet("border: 2px dashed #bdc3c7; color: #7f8c8d;")
        
        chart_layout.addWidget(chart_placeholder)
        layout.addWidget(chart_group)
        
        # Información del sistema
        system_group = QGroupBox("💻 Sistema")
        system_layout = QVBoxLayout(system_group)
        
        self.system_info_label = QLabel()
        self.system_info_label.setWordWrap(True)
        self.system_info_label.setStyleSheet("font-size: 11px; color: #2c3e50;")
        
        system_layout.addWidget(self.system_info_label)
        layout.addWidget(system_group)
        
        layout.addStretch()
        
        return panel
    
    def setup_styles(self):
        """Configurar estilos CSS del dashboard"""
        self.setStyleSheet("""
            #dashboard_header {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #3498db, stop:1 #2980b9);
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 10px;
            }
            
            #dashboard_title {
                color: white;
                font-size: 24px;
                font-weight: bold;
            }
            
            #dashboard_date {
                color: #ecf0f1;
                font-size: 14px;
            }
            
            #refresh_button {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
            
            #refresh_button:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            
            #metrics_panel {
                background-color: transparent;
            }
            
            #metric_card {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                min-height: 120px;
            }
            
            #metric_card:hover {
                border-color: #3498db;
                box-shadow: 0 4px 8px rgba(52, 152, 219, 0.2);
            }
            
            #metric_title {
                font-size: 13px;
                font-weight: bold;
                color: #2c3e50;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #2c3e50;
            }
            
            QTableWidget {
                gridline-color: #ecf0f1;
                background-color: white;
                alternate-background-color: #f8f9fa;
                selection-background-color: #3498db;
                selection-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
                font-size: 11px;
            }
            
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
            }
            
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
    
    def load_dashboard_data(self):
        """Cargar datos iniciales del dashboard"""
        try:
            today = date.today()
            
            # Obtener estadísticas de ventas
            sales_stats = self.managers['sales'].get_sales_statistics(
                date_from=today,
                date_to=today
            )
            
            # Obtener productos con stock bajo
            low_stock_products = self.managers['product'].get_products_with_low_stock()
            
            # Obtener estadísticas de productos
            stock_stats = self.managers['product'].calculate_stock_value()
            
            # Obtener ventas recientes
            recent_sales = self.managers['sales'].get_sales(limit=10)
            
            # Obtener productos más vendidos
            top_products = self.managers['sales'].get_top_products(limit=10)
            
            # Almacenar datos
            self.dashboard_data = {
                'sales_stats': sales_stats,
                'low_stock_products': low_stock_products,
                'stock_stats': stock_stats,
                'recent_sales': recent_sales,
                'top_products': top_products
            }
            
            # Actualizar UI
            self.update_metrics()
            self.update_tables()
            self.update_alerts()
            self.update_system_info()
            
        except Exception as e:
            logger.error(f"Error cargando datos del dashboard: {e}")
            self.show_error_message(f"Error cargando datos: {e}")
    
    def update_metrics(self):
        """Actualizar métricas principales"""
        try:
            sales_stats = self.dashboard_data.get('sales_stats', {})
            stock_stats = self.dashboard_data.get('stock_stats', {})
            low_stock_products = self.dashboard_data.get('low_stock_products', [])
            
            # Ventas hoy
            ventas_hoy = sales_stats.get('monto_total', 0)
            self.metric_ventas_hoy_value.setText(f"${ventas_hoy:,.2f}")
            
            if ventas_hoy > 0:
                avg_ticket = sales_stats.get('monto_promedio', 0)
                self.metric_ventas_hoy_detail.setText(f"Ticket promedio: ${avg_ticket:.2f}")
            else:
                self.metric_ventas_hoy_detail.setText("Sin ventas hoy")
            
            # Productos vendidos
            total_ventas = sales_stats.get('ventas_completadas', 0)
            self.metric_productos_vendidos_value.setText(str(total_ventas))
            
            if total_ventas > 0:
                self.metric_productos_vendidos_detail.setText(f"{total_ventas} transacciones")
            else:
                self.metric_productos_vendidos_detail.setText("Sin productos vendidos")
            
            # Stock bajo
            stock_bajo_count = len(low_stock_products)
            self.metric_stock_bajo_value.setText(str(stock_bajo_count))
            
            if stock_bajo_count > 0:
                self.metric_stock_bajo_detail.setText("Requiere atención")
            else:
                self.metric_stock_bajo_detail.setText("Stock en niveles normales")
            
            # Clientes activos (placeholder)
            clientes_unicos = sales_stats.get('clientes_unicos', 0)
            self.metric_clientes_activos_value.setText(str(clientes_unicos))
            self.metric_clientes_activos_detail.setText(f"Este mes")
            
        except Exception as e:
            logger.error(f"Error actualizando métricas: {e}")
    
    def update_tables(self):
        """Actualizar tablas de datos"""
        try:
            # Actualizar tabla de ventas recientes
            recent_sales = self.dashboard_data.get('recent_sales', [])
            self.recent_sales_table.setRowCount(len(recent_sales[:10]))
            
            for row, sale in enumerate(recent_sales[:10]):
                fecha = QTableWidgetItem(sale.get('fecha_venta', '')[:16])
                cliente = QTableWidgetItem(sale.get('cliente_nombre', 'Cliente General'))
                total = QTableWidgetItem(f"${sale.get('total', 0):,.2f}")
                estado = QTableWidgetItem(sale.get('estado', 'COMPLETADA'))
                
                # Colorear estado
                if sale.get('estado') == 'COMPLETADA':
                    estado.setBackground(QColor("#d5edda"))
                elif sale.get('estado') == 'CANCELADA':
                    estado.setBackground(QColor("#f8d7da"))
                
                self.recent_sales_table.setItem(row, 0, fecha)
                self.recent_sales_table.setItem(row, 1, cliente)
                self.recent_sales_table.setItem(row, 2, total)
                self.recent_sales_table.setItem(row, 3, estado)
            
            # Actualizar tabla de productos más vendidos
            top_products = self.dashboard_data.get('top_products', [])
            self.top_products_table.setRowCount(len(top_products[:10]))
            
            for row, product in enumerate(top_products[:10]):
                nombre = QTableWidgetItem(product.get('nombre', ''))
                cantidad = QTableWidgetItem(str(int(product.get('cantidad_vendida', 0))))
                ingresos = QTableWidgetItem(f"${product.get('monto_total', 0):,.2f}")
                
                self.top_products_table.setItem(row, 0, nombre)
                self.top_products_table.setItem(row, 1, cantidad)
                self.top_products_table.setItem(row, 2, ingresos)
                
        except Exception as e:
            logger.error(f"Error actualizando tablas: {e}")
    
    def update_alerts(self):
        """Actualizar lista de alertas"""
        try:
            self.alerts_list.clear()
            
            # Alertas por stock bajo
            low_stock_products = self.dashboard_data.get('low_stock_products', [])
            if low_stock_products:
                if len(low_stock_products) <= 3:
                    for product in low_stock_products[:3]:
                        alert_text = f"⚠️ Stock bajo: {product['nombre']} ({product['stock_actual']} unidades)"
                        item = QListWidgetItem(alert_text)
                        item.setData(Qt.UserRole, 'stock_bajo')
                        self.alerts_list.addItem(item)
                else:
                    alert_text = f"⚠️ {len(low_stock_products)} productos con stock bajo"
                    item = QListWidgetItem(alert_text)
                    item.setData(Qt.UserRole, 'stock_bajo')
                    self.alerts_list.addItem(item)
            
            # Alerta por productos próximos a vencer
            try:
                expiring_products = self.managers['product'].get_products_expiring_soon(7)
                if expiring_products:
                    alert_text = f"📅 {len(expiring_products)} productos vencen en 7 días"
                    item = QListWidgetItem(alert_text)
                    item.setData(Qt.UserRole, 'expiring')
                    self.alerts_list.addItem(item)
            except:
                pass  # No todos los productos tienen fecha de vencimiento
            
            # Si no hay alertas, mostrar mensaje positivo
            if self.alerts_list.count() == 0:
                item = QListWidgetItem("✅ Sin alertas críticas")
                item.setForeground(QColor("#27ae60"))
                self.alerts_list.addItem(item)
                
        except Exception as e:
            logger.error(f"Error actualizando alertas: {e}")
    
    def update_system_info(self):
        """Actualizar información del sistema"""
        try:
            db_info = self.managers['db'].get_database_info()
            
            system_text = f"""
            <b>Base de Datos:</b><br>
            • {db_info.get('total_records', 0):,} registros totales<br>
            • Tamaño: {db_info.get('size_mb', 0):.1f} MB<br><br>
            
            <b>Usuario Actual:</b><br>
            • {self.current_user['nombre_completo']}<br>
            • Rol: {self.current_user['rol_nombre']}<br><br>
            
            <b>Sesión:</b><br>
            • Iniciada: {datetime.now().strftime('%H:%M')}<br>
            • Última actualización: {datetime.now().strftime('%H:%M:%S')}
            """
            
            self.system_info_label.setText(system_text.strip())
            
        except Exception as e:
            logger.error(f"Error actualizando info del sistema: {e}")
            self.system_info_label.setText("Error cargando información del sistema")
    
    def refresh_data(self):
        """Actualizar todos los datos del dashboard"""
        try:
            # Mostrar indicador de carga
            self.setEnabled(False)
            QApplication.processEvents()
            
            # Recargar datos
            self.load_dashboard_data()
            
            # Restaurar interfaz
            self.setEnabled(True)
            
        except Exception as e:
            logger.error(f"Error refrescando dashboard: {e}")
            self.show_error_message(f"Error actualizando dashboard: {e}")
            self.setEnabled(True)
    
    def show_error_message(self, message: str):
        """Mostrar mensaje de error en el dashboard"""
        # Se podría mostrar un banner de error o notificación
        pass
    
    def closeEvent(self, event):
        """Limpiar recursos al cerrar"""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        event.accept()