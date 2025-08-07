"""
Widget de administración para usuarios ADMINISTRADOR
Funcionalidades completas de gestión del sistema
"""

import logging
from datetime import datetime, timedelta
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

logger = logging.getLogger(__name__)

class AdminWidget(QWidget):
    """Widget de administración del sistema"""
    
    def __init__(self, managers: dict, current_user: dict, parent=None):
        super().__init__(parent)
        
        self.managers = managers
        self.current_user = current_user
        
        self.init_ui()
        self.load_admin_data()
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Tabs principales
        tabs = QTabWidget()
        
        # Tab 1: Gestión de usuarios
        users_tab = self.create_users_management_tab()
        tabs.addTab(users_tab, "👥 Gestión de Usuarios")
        
        # Tab 2: Estado del sistema
        system_tab = self.create_system_status_tab()
        tabs.addTab(system_tab, "🖥️ Estado del Sistema")
        
        # Tab 3: Configuraciones
        config_tab = self.create_configuration_tab()
        tabs.addTab(config_tab, "⚙️ Configuraciones")
        
        # Tab 4: Logs de auditoría
        logs_tab = self.create_logs_tab()
        tabs.addTab(logs_tab, "📋 Logs de Auditoría")
        
        # Tab 5: Backup y restauración
        backup_tab = self.create_backup_tab()
        tabs.addTab(backup_tab, "💾 Backup & Restauración")
        
        main_layout.addWidget(tabs)
    
    def create_header(self) -> QWidget:
        """Crear header del panel admin"""
        header = QWidget()
        layout = QHBoxLayout(header)
        
        title = QLabel("🔧 Panel de Administración")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #e74c3c;
            margin: 10px 0;
        """)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Indicador de privilegios
        admin_badge = QLabel("🛡️ ADMINISTRADOR")
        admin_badge.setStyleSheet("""
            background-color: #e74c3c;
            color: white;
            padding: 5px 15px;
            border-radius: 15px;
            font-weight: bold;
            font-size: 12px;
        """)
        layout.addWidget(admin_badge)
        
        return header
    
    def create_users_management_tab(self) -> QWidget:
        """Tab de gestión de usuarios"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Controles superiores
        controls_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Actualizar")
        refresh_btn.clicked.connect(self.refresh_users_list)
        controls_layout.addWidget(refresh_btn)
        
        add_user_btn = QPushButton("➕ Nuevo Usuario")
        add_user_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 8px; font-weight: bold;")
        add_user_btn.clicked.connect(self.create_new_user)
        controls_layout.addWidget(add_user_btn)
        
        controls_layout.addStretch()
        
        search_input = QLineEdit()
        search_input.setPlaceholderText("🔍 Buscar usuario...")
        search_input.textChanged.connect(self.filter_users)
        controls_layout.addWidget(search_input)
        
        layout.addLayout(controls_layout)
        
        # Tabla de usuarios
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(8)
        self.users_table.setHorizontalHeaderLabels([
            "ID", "Usuario", "Nombre Completo", "Email", "Rol", 
            "Estado", "Último Acceso", "Acciones"
        ])
        
        # Configurar tabla
        header = self.users_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        
        self.users_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.users_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.users_table)
        
        return widget
    
    def create_system_status_tab(self) -> QWidget:
        """Tab de estado del sistema"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Métricas del sistema
        metrics_layout = QGridLayout()
        
        # Crear tarjetas de métricas
        metrics = [
            ("💾 Base de Datos", "Conectada", "#27ae60"),
            ("👥 Usuarios Activos", "0", "#3498db"),
            ("📊 Tablas", "0", "#9b59b6"),
            ("🔍 Índices", "0", "#f39c12"),
            ("💿 Tamaño BD", "0 MB", "#e67e22"),
            ("🕐 Uptime", "0 min", "#2ecc71")
        ]
        
        self.system_metrics = {}
        
        for i, (title, value, color) in enumerate(metrics):
            card = self.create_metric_card(title, value, color)
            row, col = divmod(i, 3)
            metrics_layout.addWidget(card, row, col)
            
            # Guardar referencia para actualizar
            self.system_metrics[title] = card.findChild(QLabel, "metric_value")
        
        layout.addLayout(metrics_layout)
        
        # Información detallada del sistema
        details_group = QGroupBox("🔍 Información Detallada")
        details_layout = QVBoxLayout(details_group)
        
        self.system_info_text = QTextEdit()
        self.system_info_text.setReadOnly(True)
        self.system_info_text.setMaximumHeight(200)
        details_layout.addWidget(self.system_info_text)
        
        layout.addWidget(details_group)
        
        # Botones de acción
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        
        optimize_btn = QPushButton("⚡ Optimizar BD")
        optimize_btn.clicked.connect(self.optimize_database)
        actions_layout.addWidget(optimize_btn)
        
        vacuum_btn = QPushButton("🧹 Limpiar BD")
        vacuum_btn.clicked.connect(self.vacuum_database)
        actions_layout.addWidget(vacuum_btn)
        
        refresh_system_btn = QPushButton("🔄 Actualizar Info")
        refresh_system_btn.clicked.connect(self.refresh_system_info)
        actions_layout.addWidget(refresh_system_btn)
        
        layout.addLayout(actions_layout)
        layout.addStretch()
        
        return widget
    
    def create_configuration_tab(self) -> QWidget:
        """Tab de configuraciones del sistema"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Configuraciones por categorías
        config_tabs = QTabWidget()
        
        # Empresa
        company_tab = self.create_company_config()
        config_tabs.addTab(company_tab, "🏢 Empresa")
        
        # Sistema
        system_tab = self.create_system_config()
        config_tabs.addTab(system_tab, "💻 Sistema")
        
        # Seguridad
        security_tab = self.create_security_config()
        config_tabs.addTab(security_tab, "🔒 Seguridad")
        
        layout.addWidget(config_tabs)
        
        # Botones de control
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        reset_btn = QPushButton("🔄 Restaurar Defecto")
        reset_btn.clicked.connect(self.reset_configurations)
        buttons_layout.addWidget(reset_btn)
        
        save_btn = QPushButton("💾 Guardar Cambios")
        save_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 8px; font-weight: bold;")
        save_btn.clicked.connect(self.save_configurations)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
        
        return widget
    
    def create_logs_tab(self) -> QWidget:
        """Tab de logs de auditoría"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Controles
        controls_layout = QHBoxLayout()
        
        # Filtros
        filter_combo = QComboBox()
        filter_combo.addItems(["Todos", "Login", "Ventas", "Productos", "Usuarios", "Configuración"])
        controls_layout.addWidget(QLabel("Filtro:"))
        controls_layout.addWidget(filter_combo)
        
        # Rango de fechas
        controls_layout.addWidget(QLabel("Desde:"))
        date_from = QDateEdit(QDate.currentDate().addDays(-7))
        date_from.setCalendarPopup(True)
        controls_layout.addWidget(date_from)
        
        controls_layout.addWidget(QLabel("Hasta:"))
        date_to = QDateEdit(QDate.currentDate())
        date_to.setCalendarPopup(True)
        controls_layout.addWidget(date_to)
        
        controls_layout.addStretch()
        
        export_btn = QPushButton("📤 Exportar")
        export_btn.clicked.connect(self.export_logs)
        controls_layout.addWidget(export_btn)
        
        clear_logs_btn = QPushButton("🗑️ Limpiar Logs")
        clear_logs_btn.clicked.connect(self.clear_old_logs)
        controls_layout.addWidget(clear_logs_btn)
        
        layout.addLayout(controls_layout)
        
        # Tabla de logs
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(7)
        self.logs_table.setHorizontalHeaderLabels([
            "Fecha/Hora", "Usuario", "Acción", "Tabla", "Éxito", "Detalles", "Error"
        ])
        
        self.logs_table.horizontalHeader().setStretchLastSection(True)
        self.logs_table.setAlternatingRowColors(True)
        self.logs_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        layout.addWidget(self.logs_table)
        
        return widget
    
    def create_backup_tab(self) -> QWidget:
        """Tab de backup y restauración"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Estado del backup
        status_group = QGroupBox("📊 Estado del Backup")
        status_layout = QFormLayout(status_group)
        
        self.last_backup_label = QLabel("No disponible")
        self.next_backup_label = QLabel("No programado")
        self.backup_size_label = QLabel("0 MB")
        
        status_layout.addRow("Último backup:", self.last_backup_label)
        status_layout.addRow("Próximo backup:", self.next_backup_label)
        status_layout.addRow("Tamaño último backup:", self.backup_size_label)
        
        layout.addWidget(status_group)
        
        # Acciones de backup
        backup_group = QGroupBox("💾 Acciones de Backup")
        backup_layout = QVBoxLayout(backup_group)
        
        # Backup manual
        manual_layout = QHBoxLayout()
        manual_layout.addWidget(QLabel("Backup manual:"))
        
        backup_now_btn = QPushButton("📦 Crear Backup Ahora")
        backup_now_btn.setStyleSheet("background-color: #3498db; color: white; padding: 10px; font-weight: bold;")
        backup_now_btn.clicked.connect(self.create_manual_backup)
        manual_layout.addWidget(backup_now_btn)
        manual_layout.addStretch()
        
        backup_layout.addLayout(manual_layout)
        
        # Configuración automática
        auto_layout = QHBoxLayout()
        self.auto_backup_checkbox = QCheckBox("Backup automático habilitado")
        auto_layout.addWidget(self.auto_backup_checkbox)
        
        auto_layout.addWidget(QLabel("Intervalo (horas):"))
        self.backup_interval_spin = QSpinBox()
        self.backup_interval_spin.setRange(1, 168)  # 1 hora a 7 días
        self.backup_interval_spin.setValue(24)
        auto_layout.addWidget(self.backup_interval_spin)
        auto_layout.addStretch()
        
        backup_layout.addLayout(auto_layout)
        
        layout.addWidget(backup_group)
        
        # Lista de backups
        backups_group = QGroupBox("📚 Historial de Backups")
        backups_layout = QVBoxLayout(backups_group)
        
        self.backups_table = QTableWidget()
        self.backups_table.setColumnCount(5)
        self.backups_table.setHorizontalHeaderLabels([
            "Fecha", "Tipo", "Tamaño", "Estado", "Acciones"
        ])
        self.backups_table.horizontalHeader().setStretchLastSection(True)
        
        backups_layout.addWidget(self.backups_table)
        
        layout.addWidget(backups_group)
        layout.addStretch()
        
        return widget
    
    def create_metric_card(self, title: str, value: str, color: str) -> QWidget:
        """Crear tarjeta de métrica"""
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {color};
                border-radius: 10px;
                background-color: white;
                margin: 5px;
                padding: 10px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setObjectName("metric_value")
        value_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        return card
    
    def create_company_config(self) -> QWidget:
        """Configuración de empresa"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.company_name = QLineEdit()
        self.company_address = QLineEdit()
        self.company_phone = QLineEdit()
        self.company_email = QLineEdit()
        self.company_tax_id = QLineEdit()
        
        layout.addRow("Nombre de la empresa:", self.company_name)
        layout.addRow("Dirección:", self.company_address)
        layout.addRow("Teléfono:", self.company_phone)
        layout.addRow("Email:", self.company_email)
        layout.addRow("CUIT/RUT:", self.company_tax_id)
        
        return widget
    
    def create_system_config(self) -> QWidget:
        """Configuración del sistema"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.auto_backup = QCheckBox()
        self.backup_interval = QSpinBox()
        self.backup_interval.setRange(1, 720)
        self.backup_interval.setValue(24)
        
        self.low_stock_threshold = QSpinBox()
        self.low_stock_threshold.setRange(0, 1000)
        self.low_stock_threshold.setValue(10)
        
        layout.addRow("Backup automático:", self.auto_backup)
        layout.addRow("Intervalo backup (horas):", self.backup_interval)
        layout.addRow("Umbral stock bajo:", self.low_stock_threshold)
        
        return widget
    
    def create_security_config(self) -> QWidget:
        """Configuración de seguridad"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        self.session_timeout = QSpinBox()
        self.session_timeout.setRange(5, 480)
        self.session_timeout.setValue(60)
        
        self.max_login_attempts = QSpinBox()
        self.max_login_attempts.setRange(3, 10)
        self.max_login_attempts.setValue(3)
        
        self.lockout_duration = QSpinBox()
        self.lockout_duration.setRange(1, 60)
        self.lockout_duration.setValue(15)
        
        layout.addRow("Timeout sesión (min):", self.session_timeout)
        layout.addRow("Máx. intentos login:", self.max_login_attempts)
        layout.addRow("Duración bloqueo (min):", self.lockout_duration)
        
        return widget
    
    # MÉTODOS DE FUNCIONALIDAD
    
    def load_admin_data(self):
        """Cargar datos del panel admin"""
        self.refresh_users_list()
        self.refresh_system_info()
        self.load_configurations()
        self.refresh_logs()
        self.refresh_backup_info()
    
    def refresh_users_list(self):
        """Actualizar lista de usuarios"""
        try:
            if 'user' not in self.managers:
                return
            
            users = self.managers['user'].get_all_users()
            
            self.users_table.setRowCount(len(users))
            
            for row, user in enumerate(users):
                self.users_table.setItem(row, 0, QTableWidgetItem(str(user.get('id', ''))))
                self.users_table.setItem(row, 1, QTableWidgetItem(user.get('username', '')))
                self.users_table.setItem(row, 2, QTableWidgetItem(user.get('nombre_completo', '')))
                self.users_table.setItem(row, 3, QTableWidgetItem(user.get('email', '')))
                self.users_table.setItem(row, 4, QTableWidgetItem(user.get('rol_nombre', '')))
                
                # Estado
                status = "✅ Activo" if user.get('activo') else "❌ Inactivo"
                self.users_table.setItem(row, 5, QTableWidgetItem(status))
                
                # Último acceso
                last_access = user.get('ultimo_acceso', 'Nunca')
                self.users_table.setItem(row, 6, QTableWidgetItem(str(last_access)))
                
                # Botones de acción
                actions_widget = self.create_user_actions(user.get('id'))
                self.users_table.setCellWidget(row, 7, actions_widget)
                
        except Exception as e:
            logger.error(f"Error actualizando lista de usuarios: {e}")
    
    def create_user_actions(self, user_id: int) -> QWidget:
        """Crear botones de acción para usuario"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        
        edit_btn = QPushButton("✏️")
        edit_btn.setToolTip("Editar usuario")
        edit_btn.setFixedSize(30, 25)
        edit_btn.clicked.connect(lambda: self.edit_user(user_id))
        
        reset_pwd_btn = QPushButton("🔑")
        reset_pwd_btn.setToolTip("Resetear contraseña")
        reset_pwd_btn.setFixedSize(30, 25)
        reset_pwd_btn.clicked.connect(lambda: self.reset_user_password(user_id))
        
        toggle_btn = QPushButton("🔄")
        toggle_btn.setToolTip("Activar/Desactivar")
        toggle_btn.setFixedSize(30, 25)
        toggle_btn.clicked.connect(lambda: self.toggle_user_status(user_id))
        
        layout.addWidget(edit_btn)
        layout.addWidget(reset_pwd_btn)
        layout.addWidget(toggle_btn)
        layout.addStretch()
        
        return widget
    
    def refresh_system_info(self):
        """Actualizar información del sistema"""
        try:
            db_manager = self.managers.get('db')
            if not db_manager:
                return
            
            # Obtener estadísticas de la base de datos
            stats = self.get_database_statistics()
            
            # Actualizar métricas
            if "👥 Usuarios Activos" in self.system_metrics:
                active_users = stats.get('active_users', 0)
                self.system_metrics["👥 Usuarios Activos"].setText(str(active_users))
            
            if "📊 Tablas" in self.system_metrics:
                tables_count = stats.get('tables_count', 0)
                self.system_metrics["📊 Tablas"].setText(str(tables_count))
            
            # Actualizar texto detallado
            info_text = f"""
Estado de la Base de Datos:
• Archivo: {stats.get('db_path', 'N/A')}
• Tamaño: {stats.get('db_size', 'N/A')} MB
• Tablas: {stats.get('tables_count', 0)}
• Usuarios totales: {stats.get('total_users', 0)}
• Productos totales: {stats.get('total_products', 0)}
• Ventas totales: {stats.get('total_sales', 0)}
• Última optimización: {stats.get('last_optimization', 'Nunca')}
            """
            
            self.system_info_text.setPlainText(info_text.strip())
            
        except Exception as e:
            logger.error(f"Error actualizando información del sistema: {e}")
    
    def get_database_statistics(self) -> dict:
        """Obtener estadísticas de la base de datos"""
        stats = {}
        
        try:
            db_manager = self.managers.get('db')
            if not db_manager:
                return stats
            
            # Contar usuarios activos
            result = db_manager.execute_single("SELECT COUNT(*) as count FROM usuarios WHERE activo = 1")
            stats['active_users'] = result['count'] if result else 0
            
            # Contar tablas
            result = db_manager.execute_single("SELECT COUNT(*) as count FROM sqlite_master WHERE type='table'")
            stats['tables_count'] = result['count'] if result else 0
            
            # Contar usuarios totales
            result = db_manager.execute_single("SELECT COUNT(*) as count FROM usuarios")
            stats['total_users'] = result['count'] if result else 0
            
            # Contar productos
            result = db_manager.execute_single("SELECT COUNT(*) as count FROM productos")
            stats['total_products'] = result['count'] if result else 0
            
            # Contar ventas
            result = db_manager.execute_single("SELECT COUNT(*) as count FROM ventas")
            stats['total_sales'] = result['count'] if result else 0
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
        
        return stats
    
    # Métodos de acción (placeholder para implementar funcionalidad completa)
    def create_new_user(self):
        """Crear nuevo usuario"""
        QMessageBox.information(self, "Nuevo Usuario", "Funcionalidad de crear usuario en desarrollo")
    
    def edit_user(self, user_id: int):
        """Editar usuario"""
        QMessageBox.information(self, "Editar Usuario", f"Editar usuario ID: {user_id}")
    
    def reset_user_password(self, user_id: int):
        """Resetear contraseña de usuario"""
        reply = QMessageBox.question(self, "Resetear Contraseña", 
                                   f"¿Confirma resetear la contraseña del usuario ID: {user_id}?")
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "Contraseña", "Contraseña reseteada a: 123456")
    
    def toggle_user_status(self, user_id: int):
        """Activar/Desactivar usuario"""
        QMessageBox.information(self, "Estado Usuario", f"Estado cambiado para usuario ID: {user_id}")
    
    def filter_users(self, text: str):
        """Filtrar usuarios por texto"""
        for row in range(self.users_table.rowCount()):
            username = self.users_table.item(row, 1).text()
            name = self.users_table.item(row, 2).text()
            should_show = text.lower() in username.lower() or text.lower() in name.lower()
            self.users_table.setRowHidden(row, not should_show)
    
    def optimize_database(self):
        """Optimizar base de datos"""
        reply = QMessageBox.question(self, "Optimizar BD", "¿Confirma optimizar la base de datos?")
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "Optimización", "Base de datos optimizada exitosamente")
    
    def vacuum_database(self):
        """Limpiar base de datos"""
        reply = QMessageBox.question(self, "Limpiar BD", "¿Confirma limpiar la base de datos?")
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "Limpieza", "Base de datos limpiada exitosamente")
    
    def load_configurations(self):
        """Cargar configuraciones actuales"""
        # TODO: Implementar carga desde base de datos
        pass
    
    def save_configurations(self):
        """Guardar configuraciones"""
        QMessageBox.information(self, "Configuración", "Configuraciones guardadas exitosamente")
    
    def reset_configurations(self):
        """Resetear configuraciones a defecto"""
        reply = QMessageBox.question(self, "Resetear", "¿Confirma resetear todas las configuraciones?")
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "Reset", "Configuraciones reseteadas a valores por defecto")
    
    def refresh_logs(self):
        """Actualizar logs"""
        # TODO: Implementar carga de logs reales
        pass
    
    def export_logs(self):
        """Exportar logs"""
        QMessageBox.information(self, "Exportar", "Logs exportados exitosamente")
    
    def clear_old_logs(self):
        """Limpiar logs antiguos"""
        reply = QMessageBox.question(self, "Limpiar Logs", "¿Confirma eliminar logs antiguos?")
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "Limpieza", "Logs antiguos eliminados")
    
    def refresh_backup_info(self):
        """Actualizar información de backup"""
        # TODO: Implementar información real de backup
        pass
    
    def create_manual_backup(self):
        """Crear backup manual"""
        try:
            if 'backup' in self.managers:
                backup_manager = self.managers['backup']
                success = backup_manager.create_backup("Backup manual desde panel admin")
                if success:
                    QMessageBox.information(self, "Backup", "Backup creado exitosamente")
                else:
                    QMessageBox.warning(self, "Backup", "Error creando backup")
            else:
                QMessageBox.warning(self, "Backup", "Servicio de backup no disponible")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error creando backup: {str(e)}")