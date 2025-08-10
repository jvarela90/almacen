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
        self.metric_widgets = {}  # Para actualizar los widgets después
        
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
        
        # Panel izquierdo - Actividad reciente
        recent_activity = self.create_recent_activity_panel()
        details_layout.addWidget(recent_activity)
        
        # Panel derecho - Acciones rápidas
        quick_actions = self.create_quick_actions_panel()
        details_layout.addWidget(quick_actions)
        
        main_layout.addLayout(details_layout)
        main_layout.addStretch()
    
    def create_header(self) -> QWidget:
        """Crear header del dashboard"""
        header = QWidget()
        header.setObjectName("dashboard_header")
        layout = QHBoxLayout(header)
        
        # Título con saludo personalizado
        user_name = self.current_user.get('nombre_completo', 'Usuario')
        role_name = self.current_user.get('rol_nombre', 'N/A')
        
        title = QLabel(f"¡Bienvenido/a, {user_name}!")
        title.setObjectName("dashboard_title")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Información del usuario
        user_info = QLabel(f"👤 {role_name}")
        user_info.setObjectName("user_info_label")
        layout.addWidget(user_info)
        
        # Fecha y hora actual
        current_time = datetime.now().strftime("%d/%m/%Y - %H:%M")
        time_label = QLabel(f"🕐 {current_time}")
        time_label.setObjectName("time_label")
        layout.addWidget(time_label)
        
        # Aplicar estilos
        header.setStyleSheet("""
            #dashboard_header {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2c3e50);
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 10px;
            }
            #dashboard_title {
                color: white;
                font-size: 20px;
                font-weight: bold;
            }
            #user_info_label, #time_label {
                color: #ecf0f1;
                font-size: 12px;
                font-weight: bold;
                margin: 0 10px;
            }
        """)
        
        return header
    
    def create_metrics_panel(self) -> QWidget:
        """Panel principal con métricas según rol del usuario"""
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setSpacing(15)
        
        # Crear métricas según permisos del usuario
        metrics = []
        
        if self.user_has_permission('ventas'):
            ventas_value = f"${self.dashboard_data.get('ventas_hoy', 0):,.2f}"
            meta_value = f"{self.dashboard_data.get('meta_mes', 0):.1f}%"
            metrics.append(("💰 Ventas Hoy", ventas_value, "#27ae60", "ventas_hoy"))
            metrics.append(("📈 Meta del Mes", meta_value, "#f39c12", "meta_mes"))
        
        if self.user_has_permission('productos'):
            productos_value = str(int(self.dashboard_data.get('total_productos', 0)))
            stock_bajo_value = str(int(self.dashboard_data.get('stock_bajo', 0)))
            metrics.append(("📦 Total Productos", productos_value, "#3498db", "total_productos"))
            metrics.append(("⚠️ Stock Bajo", stock_bajo_value, "#e74c3c", "stock_bajo"))
        
        if self.user_has_permission('reportes'):
            clientes_value = str(int(self.dashboard_data.get('clientes_activos', 0)))
            utilidad_value = f"${self.dashboard_data.get('utilidad_mes', 0):,.2f}"
            metrics.append(("👥 Clientes Activos", clientes_value, "#9b59b6", "clientes_activos"))
            metrics.append(("💵 Utilidad Mes", utilidad_value, "#2ecc71", "utilidad_mes"))
        
        # Solo administradores ven métricas del sistema
        if self.user_has_permission('*'):
            metrics.append(("🖥️ Sistema", "OK", "#34495e", "estado_sistema"))
            metrics.append(("💾 Último Backup", "N/A", "#7f8c8d", "ultimo_backup"))
        
        # Si no hay métricas (usuario muy restringido), mostrar info básica
        if not metrics:
            metrics = [
                ("📊 Dashboard", "Disponible", "#3498db", "dashboard_basic"),
                ("👋 Sesión", "Activa", "#27ae60", "sesion_activa")
            ]
        
        # Organizar métricas en grid
        row, col = 0, 0
        max_cols = 4
        
        for title, value, color, key in metrics:
            card = self.create_metric_card(title, value, color, key)
            layout.addWidget(card, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        return widget
    
    def create_metric_card(self, title: str, value: str, color: str, key: str) -> QWidget:
        """Crear tarjeta de métrica"""
        card = QFrame()
        card.setObjectName(f"metric_card_{key}")
        card.setFrameStyle(QFrame.Box)
        card.setMinimumSize(200, 120)
        card.setMaximumSize(250, 140)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        
        # Título
        title_label = QLabel(title)
        title_label.setObjectName("metric_title")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Valor
        value_label = QLabel(value)
        value_label.setObjectName("metric_value")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        # Guardar referencia para actualizaciones posteriores
        self.metric_widgets[key] = value_label
        
        # Aplicar estilo específico
        card.setStyleSheet(f"""
            #metric_card_{key} {{
                border: 2px solid {color};
                border-radius: 12px;
                background-color: white;
                margin: 5px;
            }}
            #metric_card_{key}:hover {{
                background-color: {color}15;
                border-color: {color};
            }}
            #metric_title {{
                font-weight: bold;
                color: #2c3e50;
                font-size: 11px;
                margin-top: 10px;
            }}
            #metric_value {{
                font-size: 24px;
                font-weight: bold;
                color: {color};
                margin-bottom: 10px;
            }}
        """)
        
        # Hacer clickeable si tiene acción
        card.mousePressEvent = lambda event, k=key: self.on_metric_clicked(k)
        card.setCursor(Qt.PointingHandCursor)
        
        return card
    
    def create_recent_activity_panel(self) -> QWidget:
        """Panel de actividad reciente"""
        panel = QGroupBox("📋 Actividad Reciente")
        panel.setMaximumHeight(200)
        layout = QVBoxLayout(panel)
        
        # Lista de actividad
        activity_list = QListWidget()
        activity_list.setMaximumHeight(150)
        
        # Agregar elementos de ejemplo según permisos
        if self.user_has_permission('ventas'):
            activity_list.addItem("🛒 Venta #001 procesada - $125.50")
            activity_list.addItem("💳 Pago recibido - Cliente Juan Pérez")
        
        if self.user_has_permission('productos'):
            activity_list.addItem("📦 Stock actualizado - Producto ABC")
            activity_list.addItem("⚠️ Stock bajo detectado - Producto XYZ")
        
        if self.user_has_permission('*'):
            activity_list.addItem("💾 Backup automático completado")
            activity_list.addItem("👤 Nuevo usuario registrado")
        
        # Si no hay actividades, mostrar mensaje
        if activity_list.count() == 0:
            activity_list.addItem("ℹ️ No hay actividad reciente para mostrar")
        
        layout.addWidget(activity_list)
        
        return panel
    
    def create_quick_actions_panel(self) -> QWidget:
        """Panel de acciones rápidas"""
        panel = QGroupBox("⚡ Acciones Rápidas")
        panel.setMaximumHeight(200)
        layout = QVBoxLayout(panel)
        
        # Botones según permisos
        buttons_layout = QGridLayout()
        row, col = 0, 0
        
        if self.user_has_permission('ventas'):
            sale_btn = QPushButton("💰 Nueva Venta")
            sale_btn.setStyleSheet("QPushButton { background-color: #27ae60; color: white; padding: 8px; font-weight: bold; border-radius: 5px; }")
            sale_btn.clicked.connect(lambda: self.quick_action_clicked('nueva_venta'))
            buttons_layout.addWidget(sale_btn, row, col)
            col += 1
        
        if self.user_has_permission('productos'):
            product_btn = QPushButton("📦 Nuevo Producto")
            product_btn.setStyleSheet("QPushButton { background-color: #3498db; color: white; padding: 8px; font-weight: bold; border-radius: 5px; }")
            product_btn.clicked.connect(lambda: self.quick_action_clicked('nuevo_producto'))
            buttons_layout.addWidget(product_btn, row, col)
            col += 1
        
        if col >= 2:
            col = 0
            row += 1
        
        if self.user_has_permission('reportes'):
            report_btn = QPushButton("📊 Ver Reportes")
            report_btn.setStyleSheet("QPushButton { background-color: #9b59b6; color: white; padding: 8px; font-weight: bold; border-radius: 5px; }")
            report_btn.clicked.connect(lambda: self.quick_action_clicked('ver_reportes'))
            buttons_layout.addWidget(report_btn, row, col)
            col += 1
        
        if self.user_has_permission('*'):
            backup_btn = QPushButton("💾 Backup Ahora")
            backup_btn.setStyleSheet("QPushButton { background-color: #e67e22; color: white; padding: 8px; font-weight: bold; border-radius: 5px; }")
            backup_btn.clicked.connect(lambda: self.quick_action_clicked('backup'))
            buttons_layout.addWidget(backup_btn, row, col)
        
        layout.addLayout(buttons_layout)
        layout.addStretch()
        
        return panel
    
    def user_has_permission(self, permission: str) -> bool:
        """Verificar permisos del usuario actual"""
        user_permissions = self.current_user.get('permisos', [])
        if isinstance(user_permissions, str):
            user_permissions = user_permissions.split(',') if user_permissions else []
        user_permissions = [p.strip() for p in user_permissions if p.strip()]
        return permission in user_permissions or '*' in user_permissions
    
    def load_dashboard_data(self):
        """Cargar datos del dashboard"""
        try:
            self.dashboard_data = {}
            
            # Datos de ventas
            if 'sales' in self.managers and self.user_has_permission('ventas'):
                try:
                    today_sales = self.managers['sales'].get_sales_by_date(date.today())
                    ventas_hoy = sum(float(sale.get('total', 0)) for sale in today_sales or [])
                    self.dashboard_data['ventas_hoy'] = ventas_hoy
                    
                    # Meta del mes (ejemplo: comparar con mes anterior)
                    current_month_start = date.today().replace(day=1)
                    monthly_sales = self.managers['sales'].get_sales_by_date_range(current_month_start, date.today())
                    monthly_total = sum(float(sale.get('total', 0)) for sale in monthly_sales or [])
                    # Meta arbitraria del 20% más que el mes pasado
                    meta_mes = monthly_total * 1.2 
                    progress = (monthly_total / meta_mes * 100) if meta_mes > 0 else 0
                    self.dashboard_data['meta_mes'] = progress
                except Exception as e:
                    logger.warning(f"Error cargando datos de ventas: {e}")
                    self.dashboard_data['ventas_hoy'] = 0
                    self.dashboard_data['meta_mes'] = 0
            
            # Datos de productos
            if 'product' in self.managers and self.user_has_permission('productos'):
                try:
                    all_products = self.managers['product'].search_products('') or []
                    self.dashboard_data['total_productos'] = len(all_products)
                    
                    # Productos con stock bajo
                    low_stock_products = [p for p in all_products 
                                        if float(p.get('stock_actual', 0)) <= float(p.get('stock_minimo', 0))]
                    self.dashboard_data['stock_bajo'] = len(low_stock_products)
                except Exception as e:
                    logger.warning(f"Error cargando datos de productos: {e}")
                    self.dashboard_data['total_productos'] = 0
                    self.dashboard_data['stock_bajo'] = 0
            
            # Datos de clientes
            if 'customer' in self.managers and self.user_has_permission('reportes'):
                try:
                    all_customers = self.managers['customer'].get_all_customers() or []
                    self.dashboard_data['clientes_activos'] = len(all_customers)
                    
                    # Utilidad del mes (diferencia entre ventas y costos)
                    if 'sales' in self.managers:
                        current_month_start = date.today().replace(day=1)
                        monthly_sales = self.managers['sales'].get_sales_by_date_range(current_month_start, date.today())
                        utilidad = sum(float(sale.get('total', 0)) * 0.3 for sale in monthly_sales or [])  # Asumiendo 30% de margen
                        self.dashboard_data['utilidad_mes'] = utilidad
                    else:
                        self.dashboard_data['utilidad_mes'] = 0
                except Exception as e:
                    logger.warning(f"Error cargando datos de clientes: {e}")
                    self.dashboard_data['clientes_activos'] = 0
                    self.dashboard_data['utilidad_mes'] = 0
            
            # Valores por defecto para datos faltantes
            default_values = {
                'ventas_hoy': 0,
                'meta_mes': 0, 
                'total_productos': 0,
                'stock_bajo': 0,
                'clientes_activos': 0,
                'utilidad_mes': 0
            }
            
            for key, default_value in default_values.items():
                if key not in self.dashboard_data:
                    self.dashboard_data[key] = default_value
                    
            logger.info("Datos del dashboard cargados")
            
        except Exception as e:
            logger.error(f"Error cargando datos del dashboard: {e}")
    
    def refresh_data(self):
        """Actualizar datos del dashboard"""
        self.load_dashboard_data()
        self.update_metric_widgets()
    
    def update_metric_widgets(self):
        """Actualizar los widgets de métricas con los datos actuales"""
        try:
            for key, widget in self.metric_widgets.items():
                if key in self.dashboard_data:
                    value = self.dashboard_data[key]
                    
                    # Formatear valor según el tipo de métrica
                    if key in ['ventas_hoy', 'utilidad_mes']:
                        formatted_value = f"${value:,.2f}"
                    elif key == 'meta_mes':
                        formatted_value = f"{value:.1f}%"
                    elif key in ['total_productos', 'stock_bajo', 'clientes_activos']:
                        formatted_value = str(int(value))
                    else:
                        formatted_value = str(value)
                    
                    widget.setText(formatted_value)
                    
        except Exception as e:
            logger.error(f"Error actualizando widgets de métricas: {e}")
    
    def on_metric_clicked(self, key: str):
        """Manejar click en métrica"""
        # Emitir señal o navegar según la métrica
        logger.info(f"Métrica clickeada: {key}")
        # TODO: Implementar navegación específica
    
    def quick_action_clicked(self, action: str):
        """Manejar acciones rápidas"""
        logger.info(f"Acción rápida: {action}")
        
        try:
            # Encontrar la ventana principal recorriendo hacia arriba en la jerarquía
            main_window = None
            widget = self.parent()
            
            while widget and main_window is None:
                if hasattr(widget, 'switch_to_tab'):
                    main_window = widget
                    break
                widget = widget.parent()
            
            if main_window:
                if action == 'nueva_venta':
                    main_window.switch_to_tab('sales')
                elif action == 'nuevo_producto':
                    main_window.switch_to_tab('stock')
                elif action == 'ver_reportes':
                    main_window.switch_to_tab('reports')
                elif action == 'backup':
                    if hasattr(main_window, 'show_backup_dialog'):
                        main_window.show_backup_dialog()
                    else:
                        logger.info("Función de backup no disponible")
            else:
                logger.warning("No se pudo encontrar la ventana principal para la acción")
                
        except Exception as e:
            logger.error(f"Error ejecutando acción rápida {action}: {e}")