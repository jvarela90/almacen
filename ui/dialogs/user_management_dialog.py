"""
Diálogo de Gestión de Usuarios Avanzada - AlmacénPro v2.0
Sistema completo de administración de usuarios con seguridad empresarial
"""

import logging
import re
import bcrypt
from datetime import datetime, timedelta
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from typing import Dict, List, Optional, Tuple

# Importar utilidades propias
from utils.formatters import DateFormatter, StatusFormatter, ValidationFormatter
from utils.validators import UserValidator, PasswordValidator

logger = logging.getLogger(__name__)

class UserManagementDialog(QDialog):
    """Diálogo principal para gestión avanzada de usuarios"""
    
    user_created = pyqtSignal(dict)
    user_updated = pyqtSignal(dict)
    user_deleted = pyqtSignal(int)
    
    def __init__(self, user_manager, current_user, user_data=None, parent=None):
        super().__init__(parent)
        
        self.user_manager = user_manager
        self.current_user = current_user
        self.user_data = user_data
        self.editing_mode = user_data is not None
        
        # Validadores
        self.user_validator = UserValidator()
        self.password_validator = PasswordValidator()
        
        self.setWindowTitle("Editar Usuario" if self.editing_mode else "Crear Nuevo Usuario")
        self.setModal(True)
        self.resize(800, 700)
        
        self.init_ui()
        self.load_data()
        
        if self.editing_mode:
            self.populate_fields()
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = self.create_header()
        layout.addLayout(header_layout)
        
        # Tabs para organizar información
        self.tab_widget = QTabWidget()
        
        # Tab 1: Información básica
        basic_tab = self.create_basic_info_tab()
        self.tab_widget.addTab(basic_tab, "👤 Información Básica")
        
        # Tab 2: Seguridad y permisos
        security_tab = self.create_security_tab()
        self.tab_widget.addTab(security_tab, "🔐 Seguridad y Roles")
        
        # Tab 3: Configuraciones
        settings_tab = self.create_settings_tab()
        self.tab_widget.addTab(settings_tab, "⚙️ Configuraciones")
        
        # Tab 4: Actividad (solo en modo edición)
        if self.editing_mode:
            activity_tab = self.create_activity_tab()
            self.tab_widget.addTab(activity_tab, "📊 Actividad")
        
        layout.addWidget(self.tab_widget)
        
        # Botones de acción
        buttons_layout = self.create_buttons()
        layout.addLayout(buttons_layout)
    
    def create_header(self) -> QHBoxLayout:
        """Crear header del diálogo"""
        layout = QHBoxLayout()
        
        # Icono y título
        icon_label = QLabel("👤")
        icon_label.setStyleSheet("font-size: 24px;")
        layout.addWidget(icon_label)
        
        title_text = "Editar Usuario" if self.editing_mode else "Crear Nuevo Usuario"
        title_label = QLabel(title_text)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Estado del usuario (solo en edición)
        if self.editing_mode and self.user_data:
            status = "Activo" if self.user_data.get('activo', True) else "Inactivo"
            status_label = QLabel(f"Estado: {status}")
            status_color = "#27ae60" if self.user_data.get('activo', True) else "#e74c3c"
            status_label.setStyleSheet(f"color: {status_color}; font-weight: bold;")
            layout.addWidget(status_label)
        
        return layout
    
    def create_basic_info_tab(self) -> QWidget:
        """Crear tab de información básica"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Información personal
        personal_group = QGroupBox("👨‍💼 Información Personal")
        personal_layout = QGridLayout(personal_group)
        
        # Nombre de usuario
        personal_layout.addWidget(QLabel("* Usuario:"), 0, 0)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nombre de usuario único")
        self.username_input.textChanged.connect(self.validate_username)
        personal_layout.addWidget(self.username_input, 0, 1)
        
        self.username_status = QLabel()
        personal_layout.addWidget(self.username_status, 0, 2)
        
        # Nombre completo
        personal_layout.addWidget(QLabel("* Nombre completo:"), 1, 0)
        self.full_name_input = QLineEdit()
        self.full_name_input.setPlaceholderText("Nombre y apellido completo")
        personal_layout.addWidget(self.full_name_input, 1, 1, 1, 2)
        
        # Email
        personal_layout.addWidget(QLabel("* Email:"), 2, 0)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("correo@empresa.com")
        self.email_input.textChanged.connect(self.validate_email)
        personal_layout.addWidget(self.email_input, 2, 1)
        
        self.email_status = QLabel()
        personal_layout.addWidget(self.email_status, 2, 2)
        
        # Teléfono
        personal_layout.addWidget(QLabel("Teléfono:"), 3, 0)
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("(011) 1234-5678")
        personal_layout.addWidget(self.phone_input, 3, 1, 1, 2)
        
        # DNI
        personal_layout.addWidget(QLabel("DNI:"), 4, 0)
        self.dni_input = QLineEdit()
        self.dni_input.setPlaceholderText("12.345.678")
        personal_layout.addWidget(self.dni_input, 4, 1, 1, 2)
        
        layout.addWidget(personal_group)
        
        # Información laboral
        work_group = QGroupBox("🏢 Información Laboral")
        work_layout = QGridLayout(work_group)
        
        # Puesto
        work_layout.addWidget(QLabel("Puesto:"), 0, 0)
        self.position_input = QLineEdit()
        self.position_input.setPlaceholderText("Cargo o función")
        work_layout.addWidget(self.position_input, 0, 1)
        
        # Departamento
        work_layout.addWidget(QLabel("Departamento:"), 0, 2)
        self.department_input = QComboBox()
        self.department_input.addItems([
            "Administración", "Ventas", "Depósito", "Gerencia", 
            "Sistemas", "RRHH", "Contabilidad", "Otro"
        ])
        self.department_input.setEditable(True)
        work_layout.addWidget(self.department_input, 0, 3)
        
        # Fecha de ingreso
        work_layout.addWidget(QLabel("Fecha de ingreso:"), 1, 0)
        self.hire_date_input = QDateEdit()
        self.hire_date_input.setCalendarPopup(True)
        self.hire_date_input.setDate(QDate.currentDate())
        work_layout.addWidget(self.hire_date_input, 1, 1)
        
        # Supervisor
        work_layout.addWidget(QLabel("Supervisor:"), 1, 2)
        self.supervisor_combo = QComboBox()
        work_layout.addWidget(self.supervisor_combo, 1, 3)
        
        layout.addWidget(work_group)
        
        # Notas adicionales
        notes_group = QGroupBox("📝 Notas Adicionales")
        notes_layout = QVBoxLayout(notes_group)
        
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Información adicional sobre el usuario...")
        self.notes_input.setMaximumHeight(100)
        notes_layout.addWidget(self.notes_input)
        
        layout.addWidget(notes_group)
        
        layout.addStretch()
        return tab
    
    def create_security_tab(self) -> QWidget:
        """Crear tab de seguridad y permisos"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Configuración de contraseña
        password_group = QGroupBox("🔒 Configuración de Contraseña")
        password_layout = QGridLayout(password_group)
        
        if not self.editing_mode:
            # Nueva contraseña
            password_layout.addWidget(QLabel("* Nueva contraseña:"), 0, 0)
            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.Password)
            self.password_input.textChanged.connect(self.validate_password)
            password_layout.addWidget(self.password_input, 0, 1)
            
            # Confirmar contraseña
            password_layout.addWidget(QLabel("* Confirmar contraseña:"), 1, 0)
            self.confirm_password_input = QLineEdit()
            self.confirm_password_input.setEchoMode(QLineEdit.Password)
            self.confirm_password_input.textChanged.connect(self.validate_password_match)
            password_layout.addWidget(self.confirm_password_input, 1, 1)
            
            # Mostrar contraseña
            self.show_password_cb = QCheckBox("Mostrar contraseñas")
            self.show_password_cb.toggled.connect(self.toggle_password_visibility)
            password_layout.addWidget(self.show_password_cb, 2, 0, 1, 2)
        else:
            # Cambiar contraseña (opcional)
            self.change_password_cb = QCheckBox("Cambiar contraseña")
            self.change_password_cb.toggled.connect(self.toggle_password_change)
            password_layout.addWidget(self.change_password_cb, 0, 0, 1, 2)
            
            # Campos de contraseña (inicialmente ocultos)
            self.password_widget = QWidget()
            pwd_layout = QGridLayout(self.password_widget)
            
            pwd_layout.addWidget(QLabel("Nueva contraseña:"), 0, 0)
            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.Password)
            self.password_input.textChanged.connect(self.validate_password)
            pwd_layout.addWidget(self.password_input, 0, 1)
            
            pwd_layout.addWidget(QLabel("Confirmar contraseña:"), 1, 0)
            self.confirm_password_input = QLineEdit()
            self.confirm_password_input.setEchoMode(QLineEdit.Password)
            self.confirm_password_input.textChanged.connect(self.validate_password_match)
            pwd_layout.addWidget(self.confirm_password_input, 1, 1)
            
            self.password_widget.setVisible(False)
            password_layout.addWidget(self.password_widget, 1, 0, 1, 2)
        
        # Indicadores de fortaleza de contraseña
        self.password_strength = QProgressBar()
        self.password_strength.setRange(0, 100)
        password_layout.addWidget(QLabel("Fortaleza:"), 3, 0)
        password_layout.addWidget(self.password_strength, 3, 1)
        
        self.password_feedback = QLabel()
        self.password_feedback.setWordWrap(True)
        password_layout.addWidget(self.password_feedback, 4, 0, 1, 2)
        
        layout.addWidget(password_group)
        
        # Roles y permisos
        roles_group = QGroupBox("👥 Roles y Permisos")
        roles_layout = QVBoxLayout(roles_group)
        
        # Rol principal
        role_selection_layout = QHBoxLayout()
        role_selection_layout.addWidget(QLabel("* Rol principal:"))
        
        self.role_combo = QComboBox()
        self.role_combo.currentTextChanged.connect(self.on_role_changed)
        role_selection_layout.addWidget(self.role_combo)
        
        role_selection_layout.addStretch()
        roles_layout.addLayout(role_selection_layout)
        
        # Descripción del rol
        self.role_description = QLabel()
        self.role_description.setStyleSheet("color: #7f8c8d; font-style: italic; margin: 5px;")
        self.role_description.setWordWrap(True)
        roles_layout.addWidget(self.role_description)
        
        # Permisos específicos
        permissions_label = QLabel("Permisos específicos:")
        permissions_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        roles_layout.addWidget(permissions_label)
        
        # Contenedor de permisos con scroll
        permissions_scroll = QScrollArea()
        permissions_scroll.setMaximumHeight(200)
        permissions_scroll.setWidgetResizable(True)
        
        self.permissions_widget = QWidget()
        self.permissions_layout = QVBoxLayout(self.permissions_widget)
        self.permission_checkboxes = {}
        
        permissions_scroll.setWidget(self.permissions_widget)
        roles_layout.addWidget(permissions_scroll)
        
        layout.addWidget(roles_group)
        
        layout.addStretch()
        return tab
    
    def create_settings_tab(self) -> QWidget:
        """Crear tab de configuraciones"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Configuraciones de cuenta
        account_group = QGroupBox("⚙️ Configuraciones de Cuenta")
        account_layout = QGridLayout(account_group)
        
        # Estado de la cuenta
        account_layout.addWidget(QLabel("Estado de la cuenta:"), 0, 0)
        self.account_active_cb = QCheckBox("Cuenta activa")
        self.account_active_cb.setChecked(True)
        account_layout.addWidget(self.account_active_cb, 0, 1)
        
        # Forzar cambio de contraseña
        account_layout.addWidget(QLabel("Seguridad:"), 1, 0)
        self.force_password_change_cb = QCheckBox("Forzar cambio de contraseña en próximo login")
        account_layout.addWidget(self.force_password_change_cb, 1, 1)
        
        # Sesiones múltiples
        account_layout.addWidget(QLabel("Sesiones:"), 2, 0)
        self.allow_multiple_sessions_cb = QCheckBox("Permitir sesiones múltiples")
        self.allow_multiple_sessions_cb.setChecked(True)
        account_layout.addWidget(self.allow_multiple_sessions_cb, 2, 1)
        
        # Notificaciones
        account_layout.addWidget(QLabel("Notificaciones:"), 3, 0)
        self.email_notifications_cb = QCheckBox("Recibir notificaciones por email")
        self.email_notifications_cb.setChecked(True)
        account_layout.addWidget(self.email_notifications_cb, 3, 1)
        
        layout.addWidget(account_group)
        
        # Configuraciones de interfaz
        ui_group = QGroupBox("🖥️ Configuraciones de Interfaz")
        ui_layout = QGridLayout(ui_group)
        
        # Tema
        ui_layout.addWidget(QLabel("Tema:"), 0, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Claro", "Oscuro", "Sistema"])
        ui_layout.addWidget(self.theme_combo, 0, 1)
        
        # Idioma
        ui_layout.addWidget(QLabel("Idioma:"), 0, 2)
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Español", "English"])
        ui_layout.addWidget(self.language_combo, 0, 3)
        
        # Tamaño de fuente
        ui_layout.addWidget(QLabel("Tamaño de fuente:"), 1, 0)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 16)
        self.font_size_spin.setValue(9)
        ui_layout.addWidget(self.font_size_spin, 1, 1)
        
        # Dashboard por defecto
        ui_layout.addWidget(QLabel("Dashboard inicial:"), 1, 2)
        self.default_dashboard_combo = QComboBox()
        self.default_dashboard_combo.addItems(["Dashboard", "Ventas", "Stock", "Clientes", "Reportes"])
        ui_layout.addWidget(self.default_dashboard_combo, 1, 3)
        
        layout.addWidget(ui_group)
        
        # Horarios de trabajo
        schedule_group = QGroupBox("🕒 Horarios de Trabajo")
        schedule_layout = QGridLayout(schedule_group)
        
        self.schedule_checkboxes = {}
        days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        
        for i, day in enumerate(days):
            row = i // 2
            col = (i % 2) * 3
            
            cb = QCheckBox(day)
            cb.setChecked(i < 6)  # Lun-Sab por defecto
            schedule_layout.addWidget(cb, row, col)
            
            start_time = QTimeEdit()
            start_time.setTime(QTime(8, 0))
            schedule_layout.addWidget(start_time, row, col + 1)
            
            end_time = QTimeEdit()
            end_time.setTime(QTime(18, 0))
            schedule_layout.addWidget(end_time, row, col + 2)
            
            self.schedule_checkboxes[day] = (cb, start_time, end_time)
        
        layout.addWidget(schedule_group)
        
        layout.addStretch()
        return tab
    
    def create_activity_tab(self) -> QWidget:
        """Crear tab de actividad (solo en modo edición)"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Información de la cuenta
        account_info_group = QGroupBox("📊 Información de la Cuenta")
        account_info_layout = QGridLayout(account_info_group)
        
        # Datos básicos
        if self.user_data:
            created_date = self.user_data.get('fecha_creacion', 'N/A')
            last_login = self.user_data.get('ultimo_acceso', 'Nunca')
            login_count = self.user_data.get('total_accesos', 0)
            
            account_info_layout.addWidget(QLabel("Fecha de creación:"), 0, 0)
            account_info_layout.addWidget(QLabel(DateFormatter.format_datetime(created_date)), 0, 1)
            
            account_info_layout.addWidget(QLabel("Último acceso:"), 0, 2)
            account_info_layout.addWidget(QLabel(DateFormatter.format_datetime(last_login)), 0, 3)
            
            account_info_layout.addWidget(QLabel("Total accesos:"), 1, 0)
            account_info_layout.addWidget(QLabel(str(login_count)), 1, 1)
            
            # Días desde último acceso
            if last_login != 'Nunca':
                try:
                    last_login_date = datetime.fromisoformat(str(last_login))
                    days_ago = (datetime.now() - last_login_date).days
                    account_info_layout.addWidget(QLabel("Días desde último acceso:"), 1, 2)
                    account_info_layout.addWidget(QLabel(str(days_ago)), 1, 3)
                except:
                    pass
        
        layout.addWidget(account_info_group)
        
        # Actividad reciente
        activity_group = QGroupBox("📋 Actividad Reciente")
        activity_layout = QVBoxLayout(activity_group)
        
        # Tabla de actividad
        self.activity_table = QTableWidget(0, 4)
        self.activity_table.setHorizontalHeaderLabels(["Fecha", "Acción", "Módulo", "Detalles"])
        self.activity_table.horizontalHeader().setStretchLastSection(True)
        self.activity_table.setAlternatingRowColors(True)
        self.activity_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        activity_layout.addWidget(self.activity_table)
        
        # Botones de actividad
        activity_buttons_layout = QHBoxLayout()
        
        refresh_activity_btn = QPushButton("🔄 Actualizar")
        refresh_activity_btn.clicked.connect(self.refresh_activity)
        activity_buttons_layout.addWidget(refresh_activity_btn)
        
        export_activity_btn = QPushButton("📤 Exportar Actividad")
        export_activity_btn.clicked.connect(self.export_activity)
        activity_buttons_layout.addWidget(export_activity_btn)
        
        activity_buttons_layout.addStretch()
        
        clear_sessions_btn = QPushButton("🚪 Cerrar Todas las Sesiones")
        clear_sessions_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        clear_sessions_btn.clicked.connect(self.clear_all_sessions)
        activity_buttons_layout.addWidget(clear_sessions_btn)
        
        activity_layout.addLayout(activity_buttons_layout)
        
        layout.addWidget(activity_group)
        
        return tab
    
    def create_buttons(self) -> QHBoxLayout:
        """Crear botones de acción"""
        layout = QHBoxLayout()
        
        # Botón de ayuda
        help_btn = QPushButton("❓ Ayuda")
        help_btn.clicked.connect(self.show_help)
        layout.addWidget(help_btn)
        
        # Botón de prueba de email (solo si hay email)
        if self.editing_mode:
            test_email_btn = QPushButton("📧 Enviar Email de Prueba")
            test_email_btn.clicked.connect(self.send_test_email)
            layout.addWidget(test_email_btn)
        
        layout.addStretch()
        
        # Botones principales
        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        if self.editing_mode:
            # Botón eliminar (solo administradores)
            if self.current_user.get('rol_nombre') == 'ADMINISTRADOR':
                delete_btn = QPushButton("🗑️ Eliminar Usuario")
                delete_btn.setStyleSheet("background-color: #e74c3c; color: white;")
                delete_btn.clicked.connect(self.delete_user)
                layout.addWidget(delete_btn)
        
        save_btn = QPushButton("💾 Guardar Usuario")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        save_btn.clicked.connect(self.save_user)
        layout.addWidget(save_btn)
        
        return layout
    
    def load_data(self):
        """Cargar datos necesarios"""
        try:
            # Cargar roles disponibles
            roles = self.user_manager.get_available_roles()
            for role in roles:
                self.role_combo.addItem(role['nombre'], role)
            
            # Cargar usuarios para supervisor
            users = self.user_manager.get_all_users()
            self.supervisor_combo.addItem("Sin supervisor", None)
            for user in users:
                if not self.editing_mode or user['id'] != self.user_data.get('id'):
                    display_name = f"{user['nombre_completo']} ({user['username']})"
                    self.supervisor_combo.addItem(display_name, user['id'])
            
            # Cargar permisos disponibles
            self.load_available_permissions()
            
        except Exception as e:
            logger.error(f"Error cargando datos: {e}")
    
    def load_available_permissions(self):
        """Cargar permisos disponibles"""
        try:
            # Permisos básicos del sistema
            permissions = [
                ("ventas", "💰 Gestión de Ventas", "Crear, modificar y consultar ventas"),
                ("productos", "📦 Gestión de Productos", "Administrar catálogo de productos"),
                ("clientes", "👥 Gestión de Clientes", "Administrar información de clientes"),
                ("proveedores", "🏭 Gestión de Proveedores", "Administrar proveedores y compras"),
                ("reportes", "📊 Reportes y Analytics", "Generar y consultar reportes"),
                ("usuarios", "👤 Gestión de Usuarios", "Administrar usuarios del sistema"),
                ("configuracion", "⚙️ Configuración del Sistema", "Modificar configuraciones generales"),
                ("backup", "💾 Sistema de Backup", "Gestionar backups del sistema"),
                ("auditoria", "🔍 Auditoría", "Consultar logs y auditoría del sistema"),
                ("dashboard_admin", "📊 Dashboard Administrativo", "Vista completa de métricas"),
                ("impresion", "🖨️ Impresión Avanzada", "Configurar impresoras y tickets"),
                ("exportacion", "📤 Exportación de Datos", "Exportar datos a Excel/PDF"),
            ]
            
            # Limpiar permisos existentes
            for i in reversed(range(self.permissions_layout.count())):
                self.permissions_layout.itemAt(i).widget().setParent(None)
            
            self.permission_checkboxes.clear()
            
            # Crear checkboxes para cada permiso
            for perm_code, perm_name, perm_desc in permissions:
                perm_widget = QWidget()
                perm_layout = QVBoxLayout(perm_widget)
                perm_layout.setContentsMargins(5, 5, 5, 5)
                
                # Checkbox con nombre
                checkbox = QCheckBox(perm_name)
                checkbox.setStyleSheet("font-weight: bold;")
                perm_layout.addWidget(checkbox)
                
                # Descripción
                desc_label = QLabel(perm_desc)
                desc_label.setStyleSheet("color: #7f8c8d; font-size: 11px; margin-left: 20px;")
                desc_label.setWordWrap(True)
                perm_layout.addWidget(desc_label)
                
                self.permissions_layout.addWidget(perm_widget)
                self.permission_checkboxes[perm_code] = checkbox
            
        except Exception as e:
            logger.error(f"Error cargando permisos: {e}")
    
    def populate_fields(self):
        """Poblar campos con datos existentes"""
        if not self.user_data:
            return
        
        try:
            # Información básica
            self.username_input.setText(self.user_data.get('username', ''))
            self.full_name_input.setText(self.user_data.get('nombre_completo', ''))
            self.email_input.setText(self.user_data.get('email', ''))
            self.phone_input.setText(self.user_data.get('telefono', ''))
            self.dni_input.setText(self.user_data.get('dni', ''))
            self.position_input.setText(self.user_data.get('puesto', ''))
            
            # Configuraciones
            self.account_active_cb.setChecked(self.user_data.get('activo', True))
            
            # Rol
            rol_nombre = self.user_data.get('rol_nombre', '')
            for i in range(self.role_combo.count()):
                if self.role_combo.itemText(i) == rol_nombre:
                    self.role_combo.setCurrentIndex(i)
                    break
            
            # Permisos
            user_permissions = self.user_data.get('permisos', [])
            if isinstance(user_permissions, str):
                user_permissions = user_permissions.split(',')
            
            for perm_code, checkbox in self.permission_checkboxes.items():
                checkbox.setChecked(perm_code in user_permissions)
                
        except Exception as e:
            logger.error(f"Error poblando campos: {e}")
    
    def validate_username(self):
        """Validar nombre de usuario"""
        username = self.username_input.text().strip()
        
        if not username:
            self.username_status.setText("")
            return
        
        try:
            is_valid, message = self.user_validator.validate_username(username)
            
            # Verificar si ya existe (solo si no estamos editando el mismo usuario)
            if is_valid and not self.editing_mode:
                existing_user = self.user_manager.get_user_by_username(username)
                if existing_user:
                    is_valid = False
                    message = "Nombre de usuario ya existe"
            
            if is_valid:
                self.username_status.setText("✅")
                self.username_status.setStyleSheet("color: #27ae60;")
            else:
                self.username_status.setText("❌")
                self.username_status.setStyleSheet("color: #e74c3c;")
                self.username_status.setToolTip(message)
                
        except Exception as e:
            logger.error(f"Error validando username: {e}")
    
    def validate_email(self):
        """Validar email"""
        email = self.email_input.text().strip()
        
        if not email:
            self.email_status.setText("")
            return
        
        try:
            is_valid, message = self.user_validator.validate_email(email)
            
            if is_valid:
                self.email_status.setText("✅")
                self.email_status.setStyleSheet("color: #27ae60;")
            else:
                self.email_status.setText("❌")
                self.email_status.setStyleSheet("color: #e74c3c;")
                self.email_status.setToolTip(message)
                
        except Exception as e:
            logger.error(f"Error validando email: {e}")
    
    def validate_password(self):
        """Validar fortaleza de contraseña"""
        password = self.password_input.text()
        
        if not password:
            self.password_strength.setValue(0)
            self.password_feedback.setText("")
            return
        
        try:
            strength, feedback = self.password_validator.validate_password_strength(password)
            
            self.password_strength.setValue(strength)
            
            # Color basado en fortaleza
            if strength < 30:
                color = "#e74c3c"  # Rojo
            elif strength < 60:
                color = "#f39c12"  # Naranja
            elif strength < 80:
                color = "#f1c40f"  # Amarillo
            else:
                color = "#27ae60"  # Verde
            
            self.password_strength.setStyleSheet(f"""
                QProgressBar::chunk {{
                    background-color: {color};
                }}
            """)
            
            self.password_feedback.setText(feedback)
            self.password_feedback.setStyleSheet(f"color: {color};")
            
        except Exception as e:
            logger.error(f"Error validando contraseña: {e}")
    
    def validate_password_match(self):
        """Validar que las contraseñas coincidan"""
        if hasattr(self, 'password_input') and hasattr(self, 'confirm_password_input'):
            password = self.password_input.text()
            confirm = self.confirm_password_input.text()
            
            if password and confirm and password != confirm:
                self.confirm_password_input.setStyleSheet("border: 2px solid #e74c3c;")
            else:
                self.confirm_password_input.setStyleSheet("")
    
    def toggle_password_visibility(self, visible):
        """Alternar visibilidad de contraseñas"""
        echo_mode = QLineEdit.Normal if visible else QLineEdit.Password
        self.password_input.setEchoMode(echo_mode)
        self.confirm_password_input.setEchoMode(echo_mode)
    
    def toggle_password_change(self, enabled):
        """Alternar cambio de contraseña"""
        if hasattr(self, 'password_widget'):
            self.password_widget.setVisible(enabled)
            if not enabled:
                self.password_input.clear()
                self.confirm_password_input.clear()
    
    def on_role_changed(self):
        """Manejar cambio de rol"""
        current_role = self.role_combo.currentData()
        if current_role:
            description = current_role.get('descripcion', '')
            self.role_description.setText(description)
            
            # Auto-seleccionar permisos según el rol
            role_permissions = current_role.get('permisos_default', [])
            for perm_code, checkbox in self.permission_checkboxes.items():
                checkbox.setChecked(perm_code in role_permissions)
    
    def refresh_activity(self):
        """Actualizar actividad del usuario"""
        if not self.editing_mode or not self.user_data:
            return
        
        try:
            # Obtener actividad del usuario
            user_id = self.user_data['id']
            activity = self.user_manager.get_user_activity(user_id, limit=50)
            
            # Poblar tabla
            self.activity_table.setRowCount(len(activity))
            
            for row, record in enumerate(activity):
                fecha = DateFormatter.format_datetime(record.get('fecha', ''))
                accion = record.get('accion', '')
                modulo = record.get('modulo', '')
                detalles = record.get('detalles', '')
                
                self.activity_table.setItem(row, 0, QTableWidgetItem(fecha))
                self.activity_table.setItem(row, 1, QTableWidgetItem(accion))
                self.activity_table.setItem(row, 2, QTableWidgetItem(modulo))
                self.activity_table.setItem(row, 3, QTableWidgetItem(detalles))
            
            self.activity_table.resizeColumnsToContents()
            
        except Exception as e:
            logger.error(f"Error actualizando actividad: {e}")
            QMessageBox.warning(self, "Error", f"Error actualizando actividad: {str(e)}")
    
    def export_activity(self):
        """Exportar actividad del usuario"""
        try:
            from utils.exporters import export_data
            
            if not self.editing_mode or not self.user_data:
                return
            
            user_id = self.user_data['id']
            activity = self.user_manager.get_user_activity(user_id, limit=1000)
            
            if not activity:
                QMessageBox.information(self, "Info", "No hay actividad para exportar")
                return
            
            username = self.user_data.get('username', 'usuario')
            filename = f"actividad_{username}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            
            success = export_data(activity, filename, "csv", f"Actividad del usuario {username}")
            
            if success:
                QMessageBox.information(self, "Éxito", f"Actividad exportada: {filename}")
            else:
                QMessageBox.warning(self, "Error", "Error exportando actividad")
                
        except Exception as e:
            logger.error(f"Error exportando actividad: {e}")
            QMessageBox.warning(self, "Error", f"Error: {str(e)}")
    
    def clear_all_sessions(self):
        """Cerrar todas las sesiones del usuario"""
        if not self.editing_mode or not self.user_data:
            return
        
        reply = QMessageBox.question(
            self, "Confirmar Acción",
            "¿Está seguro que desea cerrar todas las sesiones activas de este usuario?\n\n"
            "El usuario deberá volver a iniciar sesión en todos sus dispositivos.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                user_id = self.user_data['id']
                success = self.user_manager.clear_user_sessions(user_id)
                
                if success:
                    QMessageBox.information(self, "Éxito", "Todas las sesiones han sido cerradas")
                else:
                    QMessageBox.warning(self, "Error", "Error cerrando sesiones")
                    
            except Exception as e:
                logger.error(f"Error cerrando sesiones: {e}")
                QMessageBox.warning(self, "Error", f"Error: {str(e)}")
    
    def send_test_email(self):
        """Enviar email de prueba"""
        try:
            email = self.email_input.text().strip()
            if not email:
                QMessageBox.warning(self, "Error", "Debe ingresar un email válido")
                return
            
            # Simular envío de email
            QMessageBox.information(
                self, "Email Enviado", 
                f"Se ha enviado un email de prueba a: {email}\n\n"
                "Nota: Esta es una funcionalidad simulada."
            )
            
        except Exception as e:
            logger.error(f"Error enviando email: {e}")
            QMessageBox.warning(self, "Error", f"Error: {str(e)}")
    
    def delete_user(self):
        """Eliminar usuario"""
        if not self.editing_mode or not self.user_data:
            return
        
        username = self.user_data.get('username', '')
        
        reply = QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Está seguro que desea eliminar el usuario '{username}'?\n\n"
            "Esta acción NO SE PUEDE DESHACER.\n"
            "Se eliminará toda la información asociada al usuario.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                user_id = self.user_data['id']
                success = self.user_manager.delete_user(user_id)
                
                if success:
                    QMessageBox.information(self, "Usuario Eliminado", f"El usuario '{username}' ha sido eliminado exitosamente")
                    self.user_deleted.emit(user_id)
                    self.accept()
                else:
                    QMessageBox.warning(self, "Error", "Error eliminando usuario")
                    
            except Exception as e:
                logger.error(f"Error eliminando usuario: {e}")
                QMessageBox.warning(self, "Error", f"Error eliminando usuario: {str(e)}")
    
    def save_user(self):
        """Guardar usuario"""
        try:
            # Validar datos obligatorios
            if not self.validate_required_fields():
                return
            
            # Recopilar datos del usuario
            user_data = self.collect_user_data()
            
            if self.editing_mode:
                # Actualizar usuario existente
                user_data['id'] = self.user_data['id']
                success = self.user_manager.update_user(user_data)
                
                if success:
                    QMessageBox.information(self, "Usuario Actualizado", "Usuario actualizado exitosamente")
                    self.user_updated.emit(user_data)
                    self.accept()
                else:
                    QMessageBox.warning(self, "Error", "Error actualizando usuario")
            else:
                # Crear nuevo usuario
                user_id = self.user_manager.create_user(user_data)
                
                if user_id:
                    user_data['id'] = user_id
                    QMessageBox.information(self, "Usuario Creado", "Usuario creado exitosamente")
                    self.user_created.emit(user_data)
                    self.accept()
                else:
                    QMessageBox.warning(self, "Error", "Error creando usuario")
                    
        except Exception as e:
            logger.error(f"Error guardando usuario: {e}")
            QMessageBox.critical(self, "Error", f"Error guardando usuario: {str(e)}")
    
    def validate_required_fields(self) -> bool:
        """Validar campos obligatorios"""
        username = self.username_input.text().strip()
        full_name = self.full_name_input.text().strip()
        email = self.email_input.text().strip()
        
        if not username:
            QMessageBox.warning(self, "Error", "El nombre de usuario es obligatorio")
            self.username_input.setFocus()
            return False
        
        if not full_name:
            QMessageBox.warning(self, "Error", "El nombre completo es obligatorio")
            self.full_name_input.setFocus()
            return False
        
        if not email:
            QMessageBox.warning(self, "Error", "El email es obligatorio")
            self.email_input.setFocus()
            return False
        
        # Validar contraseña para nuevos usuarios
        if not self.editing_mode:
            password = self.password_input.text()
            confirm_password = self.confirm_password_input.text()
            
            if not password:
                QMessageBox.warning(self, "Error", "La contraseña es obligatoria")
                self.password_input.setFocus()
                return False
            
            if password != confirm_password:
                QMessageBox.warning(self, "Error", "Las contraseñas no coinciden")
                self.confirm_password_input.setFocus()
                return False
        
        # Validar cambio de contraseña en edición
        if self.editing_mode and hasattr(self, 'change_password_cb') and self.change_password_cb.isChecked():
            password = self.password_input.text()
            confirm_password = self.confirm_password_input.text()
            
            if not password:
                QMessageBox.warning(self, "Error", "Debe ingresar la nueva contraseña")
                self.password_input.setFocus()
                return False
            
            if password != confirm_password:
                QMessageBox.warning(self, "Error", "Las contraseñas no coinciden")
                self.confirm_password_input.setFocus()
                return False
        
        # Validar rol
        if self.role_combo.currentIndex() == -1:
            QMessageBox.warning(self, "Error", "Debe seleccionar un rol")
            self.tab_widget.setCurrentIndex(1)  # Tab de seguridad
            self.role_combo.setFocus()
            return False
        
        return True
    
    def collect_user_data(self) -> dict:
        """Recopilar datos del usuario del formulario"""
        # Información básica
        user_data = {
            'username': self.username_input.text().strip(),
            'nombre_completo': self.full_name_input.text().strip(),
            'email': self.email_input.text().strip(),
            'telefono': self.phone_input.text().strip(),
            'dni': self.dni_input.text().strip(),
            'puesto': self.position_input.text().strip(),
            'departamento': self.department_input.currentText(),
            'fecha_ingreso': self.hire_date_input.date().toString('yyyy-MM-dd'),
            'supervisor_id': self.supervisor_combo.currentData(),
            'notas': self.notes_input.toPlainText().strip(),
        }
        
        # Contraseña (solo si es necesario)
        if not self.editing_mode:
            password = self.password_input.text()
            user_data['password'] = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        elif self.editing_mode and hasattr(self, 'change_password_cb') and self.change_password_cb.isChecked():
            password = self.password_input.text()
            user_data['password'] = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Rol y permisos
        selected_role = self.role_combo.currentData()
        user_data['rol_id'] = selected_role['id'] if selected_role else None
        user_data['rol_nombre'] = selected_role['nombre'] if selected_role else None
        
        # Permisos específicos
        permissions = []
        for perm_code, checkbox in self.permission_checkboxes.items():
            if checkbox.isChecked():
                permissions.append(perm_code)
        user_data['permisos'] = ','.join(permissions)
        
        # Configuraciones
        user_data['activo'] = self.account_active_cb.isChecked()
        user_data['forzar_cambio_password'] = self.force_password_change_cb.isChecked()
        user_data['permitir_sesiones_multiples'] = self.allow_multiple_sessions_cb.isChecked()
        user_data['notificaciones_email'] = self.email_notifications_cb.isChecked()
        
        # Configuraciones de UI
        user_data['tema'] = self.theme_combo.currentText()
        user_data['idioma'] = self.language_combo.currentText()
        user_data['tamano_fuente'] = self.font_size_spin.value()
        user_data['dashboard_default'] = self.default_dashboard_combo.currentText()
        
        # Horarios de trabajo
        schedule = {}
        for day, (cb, start_time, end_time) in self.schedule_checkboxes.items():
            if cb.isChecked():
                schedule[day] = {
                    'start': start_time.time().toString('HH:mm'),
                    'end': end_time.time().toString('HH:mm')
                }
        user_data['horarios_trabajo'] = schedule
        
        # Timestamps
        if not self.editing_mode:
            user_data['fecha_creacion'] = datetime.now().isoformat()
        user_data['fecha_modificacion'] = datetime.now().isoformat()
        
        return user_data
    
    def show_help(self):
        """Mostrar ayuda"""
        help_text = """
        <h3>Gestión de Usuarios - Ayuda</h3>
        
        <b>Información Básica:</b>
        <ul>
        <li>Todos los campos marcados con * son obligatorios</li>
        <li>El nombre de usuario debe ser único en el sistema</li>
        <li>Use un email válido para recibir notificaciones</li>
        </ul>
        
        <b>Seguridad:</b>
        <ul>
        <li>Las contraseñas deben tener al menos 8 caracteres</li>
        <li>Se recomienda usar mayúsculas, minúsculas, números y símbolos</li>
        <li>Los permisos se basan en el rol seleccionado</li>
        </ul>
        
        <b>Configuraciones:</b>
        <ul>
        <li>Configure horarios de trabajo para control de acceso</li>
        <li>Active notificaciones por email según necesidad</li>
        <li>El tema y idioma afectan la interfaz del usuario</li>
        </ul>
        
        <b>Actividad:</b>
        <ul>
        <li>Solo visible al editar usuarios existentes</li>
        <li>Muestra historial de accesos y acciones</li>
        <li>Permite cerrar sesiones activas remotamente</li>
        </ul>
        """
        
        QMessageBox.information(self, "Ayuda - Gestión de Usuarios", help_text)


class UserListDialog(QDialog):
    """Diálogo para mostrar lista de usuarios con filtros"""
    
    def __init__(self, user_manager, current_user, parent=None):
        super().__init__(parent)
        
        self.user_manager = user_manager
        self.current_user = current_user
        self.users_data = []
        
        self.setWindowTitle("Gestión de Usuarios")
        self.setModal(True)
        self.resize(1000, 600)
        
        self.init_ui()
        self.load_users()
    
    def init_ui(self):
        """Inicializar interfaz"""
        layout = QVBoxLayout(self)
        
        # Header con filtros
        header_layout = self.create_header()
        layout.addLayout(header_layout)
        
        # Tabla de usuarios
        self.users_table = QTableWidget(0, 8)
        self.users_table.setHorizontalHeaderLabels([
            "Usuario", "Nombre Completo", "Email", "Rol", 
            "Estado", "Último Acceso", "Creación", "Acciones"
        ])
        self.users_table.horizontalHeader().setStretchLastSection(True)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        layout.addWidget(self.users_table)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        export_btn = QPushButton("📤 Exportar Lista")
        export_btn.clicked.connect(self.export_users)
        buttons_layout.addWidget(export_btn)
        
        buttons_layout.addStretch()
        
        new_user_btn = QPushButton("➕ Nuevo Usuario")
        new_user_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 8px;")
        new_user_btn.clicked.connect(self.create_new_user)
        buttons_layout.addWidget(new_user_btn)
        
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.close)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def create_header(self) -> QHBoxLayout:
        """Crear header con filtros"""
        layout = QHBoxLayout()
        
        # Título
        title = QLabel("👥 Gestión de Usuarios")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Filtros
        layout.addWidget(QLabel("Filtrar por:"))
        
        self.role_filter = QComboBox()
        self.role_filter.addItem("Todos los roles")
        self.role_filter.currentTextChanged.connect(self.filter_users)
        layout.addWidget(self.role_filter)
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Todos", "Activos", "Inactivos"])
        self.status_filter.currentTextChanged.connect(self.filter_users)
        layout.addWidget(self.status_filter)
        
        # Búsqueda
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar usuario...")
        self.search_input.textChanged.connect(self.filter_users)
        layout.addWidget(self.search_input)
        
        refresh_btn = QPushButton("🔄")
        refresh_btn.clicked.connect(self.load_users)
        layout.addWidget(refresh_btn)
        
        return layout
    
    def load_users(self):
        """Cargar usuarios"""
        try:
            self.users_data = self.user_manager.get_all_users()
            
            # Cargar roles para filtro
            roles = self.user_manager.get_available_roles()
            current_roles = [self.role_filter.itemText(i) for i in range(self.role_filter.count())]
            
            for role in roles:
                if role['nombre'] not in current_roles:
                    self.role_filter.addItem(role['nombre'])
            
            self.populate_table(self.users_data)
            
        except Exception as e:
            logger.error(f"Error cargando usuarios: {e}")
            QMessageBox.warning(self, "Error", f"Error cargando usuarios: {str(e)}")
    
    def populate_table(self, users):
        """Poblar tabla con usuarios"""
        self.users_table.setRowCount(len(users))
        
        for row, user in enumerate(users):
            # Usuario
            self.users_table.setItem(row, 0, QTableWidgetItem(user.get('username', '')))
            
            # Nombre completo
            self.users_table.setItem(row, 1, QTableWidgetItem(user.get('nombre_completo', '')))
            
            # Email
            self.users_table.setItem(row, 2, QTableWidgetItem(user.get('email', '')))
            
            # Rol
            self.users_table.setItem(row, 3, QTableWidgetItem(user.get('rol_nombre', '')))
            
            # Estado
            status = "✅ Activo" if user.get('activo', True) else "❌ Inactivo"
            status_item = QTableWidgetItem(status)
            if not user.get('activo', True):
                status_item.setForeground(QColor("#e74c3c"))
            self.users_table.setItem(row, 4, status_item)
            
            # Último acceso
            last_login = user.get('ultimo_acceso', 'Nunca')
            if last_login != 'Nunca':
                last_login = DateFormatter.format_datetime(last_login)
            self.users_table.setItem(row, 5, QTableWidgetItem(last_login))
            
            # Fecha de creación
            created = DateFormatter.format_date(user.get('fecha_creacion', ''))
            self.users_table.setItem(row, 6, QTableWidgetItem(created))
            
            # Botones de acción
            actions_widget = self.create_action_buttons(user)
            self.users_table.setCellWidget(row, 7, actions_widget)
        
        self.users_table.resizeColumnsToContents()
    
    def create_action_buttons(self, user) -> QWidget:
        """Crear botones de acción para usuario"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # Botón editar
        edit_btn = QPushButton("✏️")
        edit_btn.setToolTip("Editar usuario")
        edit_btn.setFixedSize(25, 25)
        edit_btn.clicked.connect(lambda: self.edit_user(user))
        layout.addWidget(edit_btn)
        
        # Botón activar/desactivar
        if user.get('activo', True):
            status_btn = QPushButton("⏸️")
            status_btn.setToolTip("Desactivar usuario")
        else:
            status_btn = QPushButton("▶️")
            status_btn.setToolTip("Activar usuario")
        
        status_btn.setFixedSize(25, 25)
        status_btn.clicked.connect(lambda: self.toggle_user_status(user))
        layout.addWidget(status_btn)
        
        layout.addStretch()
        return widget
    
    def filter_users(self):
        """Filtrar usuarios según criterios"""
        try:
            search_text = self.search_input.text().lower()
            role_filter = self.role_filter.currentText()
            status_filter = self.status_filter.currentText()
            
            filtered_users = []
            
            for user in self.users_data:
                # Filtro por texto
                if search_text:
                    searchable_text = f"{user.get('username', '')} {user.get('nombre_completo', '')} {user.get('email', '')}".lower()
                    if search_text not in searchable_text:
                        continue
                
                # Filtro por rol
                if role_filter != "Todos los roles":
                    if user.get('rol_nombre', '') != role_filter:
                        continue
                
                # Filtro por estado
                if status_filter == "Activos" and not user.get('activo', True):
                    continue
                elif status_filter == "Inactivos" and user.get('activo', True):
                    continue
                
                filtered_users.append(user)
            
            self.populate_table(filtered_users)
            
        except Exception as e:
            logger.error(f"Error filtrando usuarios: {e}")
    
    def create_new_user(self):
        """Crear nuevo usuario"""
        dialog = UserManagementDialog(self.user_manager, self.current_user, parent=self)
        dialog.user_created.connect(self.on_user_created)
        dialog.exec_()
    
    def edit_user(self, user):
        """Editar usuario"""
        dialog = UserManagementDialog(self.user_manager, self.current_user, user, parent=self)
        dialog.user_updated.connect(self.on_user_updated)
        dialog.user_deleted.connect(self.on_user_deleted)
        dialog.exec_()
    
    def toggle_user_status(self, user):
        """Alternar estado del usuario"""
        try:
            new_status = not user.get('activo', True)
            action = "activar" if new_status else "desactivar"
            username = user.get('username', '')
            
            reply = QMessageBox.question(
                self, "Confirmar Acción",
                f"¿Está seguro que desea {action} el usuario '{username}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                success = self.user_manager.update_user_status(user['id'], new_status)
                
                if success:
                    user['activo'] = new_status
                    self.populate_table(self.users_data)
                    QMessageBox.information(self, "Éxito", f"Usuario {action}do exitosamente")
                else:
                    QMessageBox.warning(self, "Error", f"Error al {action} usuario")
                    
        except Exception as e:
            logger.error(f"Error cambiando estado de usuario: {e}")
            QMessageBox.warning(self, "Error", f"Error: {str(e)}")
    
    def on_user_created(self, user_data):
        """Callback cuando se crea un usuario"""
        self.load_users()
    
    def on_user_updated(self, user_data):
        """Callback cuando se actualiza un usuario"""
        self.load_users()
    
    def on_user_deleted(self, user_id):
        """Callback cuando se elimina un usuario"""
        self.load_users()
    
    def export_users(self):
        """Exportar lista de usuarios"""
        try:
            from utils.exporters import export_data
            
            if not self.users_data:
                QMessageBox.information(self, "Info", "No hay usuarios para exportar")
                return
            
            # Preparar datos para exportación
            export_data_list = []
            for user in self.users_data:
                export_data_list.append({
                    'Usuario': user.get('username', ''),
                    'Nombre Completo': user.get('nombre_completo', ''),
                    'Email': user.get('email', ''),
                    'Teléfono': user.get('telefono', ''),
                    'Rol': user.get('rol_nombre', ''),
                    'Estado': 'Activo' if user.get('activo', True) else 'Inactivo',
                    'Último Acceso': DateFormatter.format_datetime(user.get('ultimo_acceso', 'Nunca')),
                    'Fecha Creación': DateFormatter.format_date(user.get('fecha_creacion', '')),
                    'Departamento': user.get('departamento', ''),
                    'Puesto': user.get('puesto', '')
                })
            
            filename = f"usuarios_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            success = export_data(export_data_list, filename, "csv", "Lista de Usuarios del Sistema")
            
            if success:
                QMessageBox.information(self, "Éxito", f"Lista de usuarios exportada: {filename}")
            else:
                QMessageBox.warning(self, "Error", "Error exportando lista de usuarios")
                
        except Exception as e:
            logger.error(f"Error exportando usuarios: {e}")
            QMessageBox.warning(self, "Error", f"Error: {str(e)}")