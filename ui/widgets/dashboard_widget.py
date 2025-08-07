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
            metrics.append(("💰 Ventas Hoy", "$0.00", "#27ae60", "ventas_hoy"))
            metrics.append(("📈 Meta del Mes", "0%", "#f39c12", "meta_mes"))
        
        if self.user_has_permission('productos'):
            metrics.append(("📦 Total Productos", "0", "#3498db", "total_productos"))
            metrics.append(("⚠️ Stock Bajo", "0", "#e74c3c", "stock_bajo"))
        
        if self.user_has_permission('reportes'):
            metrics.append(("👥 Clientes Activos", "0", "#9b59b6", "clientes_activos"))
            metrics.append(("💵 Utilidad Mes", "$0.00", "#2ecc71", "utilidad_mes"))
        
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
            # Aquí se cargarían los datos reales de la base de datos
            # Por ahora, datos de ejemplo
            self.dashboard_data = {
                'ventas_hoy': 0,
                'total_productos': 0,
                'stock_bajo': 0,
                'clientes_activos': 0,
                'meta_mes': 0,
                'utilidad_mes': 0
            }
            
            # TODO: Implementar carga real de datos
            logger.info("Datos del dashboard cargados")
            
        except Exception as e:
            logger.error(f"Error cargando datos del dashboard: {e}")
    
    def refresh_data(self):
        """Actualizar datos del dashboard"""
        self.load_dashboard_data()
        # TODO: Actualizar widgets con nuevos datos
    
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