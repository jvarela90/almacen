"""
Diálogo de Login para AlmacénPro
Sistema de autenticación con validación de usuarios, roles y seguridad
"""

import logging
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

logger = logging.getLogger(__name__)

class LoginDialog(QDialog):
    """Diálogo de autenticación de usuarios"""
    
    def __init__(self, user_manager, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.authenticated_user = None
        self.failed_attempts = 0
        self.max_attempts = 3
        
        self.init_ui()
        self.setup_styles()
        self.setup_validators()
        
        # Timer para bloqueo temporal
        self.lockout_timer = QTimer()
        self.lockout_timer.timeout.connect(self.unlock_login)
        
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        self.setWindowTitle("AlmacénPro - Iniciar Sesión")
        self.setFixedSize(800, 600)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Logo y título
        header_widget = self.create_header()
        main_layout.addWidget(header_widget)
        
        # Formulario de login
        form_widget = self.create_login_form()
        main_layout.addWidget(form_widget)
        
        # Mensajes de estado
        self.status_label = QLabel()
        self.status_label.setObjectName("status_label")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        main_layout.addWidget(self.status_label)
        
        # Botones
        buttons_widget = self.create_buttons()
        main_layout.addWidget(buttons_widget)
        
        # Información adicional
        footer_widget = self.create_footer()
        main_layout.addWidget(footer_widget)
        
        # Configurar orden de tabulación
        self.setTabOrder(self.username_input, self.password_input)
        self.setTabOrder(self.password_input, self.show_password_cb)
        self.setTabOrder(self.show_password_cb, self.remember_me_cb)
        self.setTabOrder(self.remember_me_cb, self.login_btn)
        self.setTabOrder(self.login_btn, self.cancel_btn)
        
        # Foco inicial
        self.username_input.setFocus()
        
        # Cargar último usuario si está guardado
        self.load_saved_credentials()
    
    def create_header(self) -> QWidget:
        """Crear header con logo y título"""
        header = QWidget()
        header.setObjectName("login_header")
        layout = QVBoxLayout(header)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)
        
        # Logo placeholder (se puede reemplazar con imagen real)
        logo_label = QLabel("🏪")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setObjectName("logo_label")
        layout.addWidget(logo_label)
        
        # Título principal
        title_label = QLabel("AlmacénPro v2.0")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("title_label")
        layout.addWidget(title_label)
        
        # Subtítulo
        subtitle_label = QLabel("Sistema ERP/POS Completo")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setObjectName("subtitle_label")
        layout.addWidget(subtitle_label)
        
        return header
    
    def create_login_form(self) -> QWidget:
        """Crear formulario de login"""
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(20)
        
        # Campo de usuario
        username_layout = QVBoxLayout()
        username_label = QLabel("Usuario:")
        username_label.setObjectName("field_label")
        username_layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setObjectName("username_input")
        self.username_input.setPlaceholderText("Ingrese su nombre de usuario")
        self.username_input.setMaxLength(50)
        self.username_input.setFixedHeight(40)
        username_layout.addWidget(self.username_input)
        
        form_layout.addLayout(username_layout)
        
        # Campo de contraseña
        password_layout = QVBoxLayout()
        password_label = QLabel("Contraseña:")
        password_label.setObjectName("field_label")
        password_layout.addWidget(password_label)
        
        # Container para password y botón de mostrar
        password_container = QHBoxLayout()
        
        self.password_input = QLineEdit()
        self.password_input.setObjectName("password_input")
        self.password_input.setPlaceholderText("Ingrese su contraseña")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMaxLength(100)
        self.password_input.setFixedHeight(40)
        password_container.addWidget(self.password_input)
        
        # Botón para mostrar/ocultar contraseña
        self.toggle_password_btn = QPushButton("👁")
        self.toggle_password_btn.setObjectName("toggle_password_btn")
        self.toggle_password_btn.setFixedSize(30, 30)
        self.toggle_password_btn.setCheckable(True)
        self.toggle_password_btn.setToolTip("Mostrar/Ocultar contraseña")
        self.toggle_password_btn.clicked.connect(self.toggle_password_visibility)
        password_container.addWidget(self.toggle_password_btn)
        
        password_layout.addLayout(password_container)
        form_layout.addLayout(password_layout)
        
        # Opciones adicionales
        options_layout = QVBoxLayout()
        
        # Mostrar contraseña (checkbox alternativo)
        self.show_password_cb = QCheckBox("Mostrar contraseña")
        self.show_password_cb.setObjectName("show_password_cb")
        self.show_password_cb.toggled.connect(self.on_show_password_toggled)
        options_layout.addWidget(self.show_password_cb)
        
        # Recordar usuario
        self.remember_me_cb = QCheckBox("Recordar usuario")
        self.remember_me_cb.setObjectName("remember_me_cb")
        self.remember_me_cb.setToolTip("Recordar el nombre de usuario para el próximo inicio de sesión")
        options_layout.addWidget(self.remember_me_cb)
        
        form_layout.addLayout(options_layout)
        
        # Conectar eventos
        self.username_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self.attempt_login)
        self.username_input.textChanged.connect(self.clear_status)
        self.password_input.textChanged.connect(self.clear_status)
        
        return form_widget
    
    def create_buttons(self) -> QWidget:
        """Crear botones de acción"""
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setSpacing(15)
        
        # Botón cancelar
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setObjectName("cancel_btn")
        self.cancel_btn.setFixedHeight(45)
        self.cancel_btn.setFixedWidth(120)
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        buttons_layout.addStretch()
        
        # Botón login
        self.login_btn = QPushButton("Iniciar Sesión")
        self.login_btn.setObjectName("login_btn")
        self.login_btn.setFixedHeight(45)
        self.login_btn.setFixedWidth(140)
        self.login_btn.setDefault(True)
        self.login_btn.clicked.connect(self.attempt_login)
        buttons_layout.addWidget(self.login_btn)
        
        return buttons_widget
    
    def create_footer(self) -> QWidget:
        """Crear información adicional en el footer"""
        footer = QWidget()
        footer.setObjectName("login_footer")
        layout = QVBoxLayout(footer)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(5)
        
        # Información del sistema
        system_info = QLabel("Sistema de gestión empresarial")
        system_info.setObjectName("system_info")
        system_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(system_info)
        
        # Usuario por defecto (solo en desarrollo)
        default_user_info = QLabel("Usuario por defecto: admin / admin123")
        default_user_info.setObjectName("default_user_info")
        default_user_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(default_user_info)
        
        return footer
    
    def setup_styles(self):
        """Configurar estilos CSS del diálogo"""
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f8f9fa, stop:1 #e9ecef);
            }
            
            #login_header {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #2E86AB, stop:1 #A23B72);
                border-radius: 15px;
                padding: 25px;
                margin-bottom: 20px;
            }
            
            #logo_label {
                font-size: 48px;
                color: white;
                margin-bottom: 5px;
            }
            
            #title_label {
                color: white;
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            #subtitle_label {
                color: #e8f4f8;
                font-size: 12px;
                font-style: italic;
            }
            
            #field_label {
                color: #2c3e50;
                font-weight: bold;
                font-size: 12px;
                margin-bottom: 5px;
            }
            
            #username_input, #password_input {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 12px 15px;
                font-size: 14px;
                background-color: white;
                color: #2c3e50;
            }
            
            #username_input:focus, #password_input:focus {
                border-color: #3498db;
                outline: none;
            }
            
            #username_input:hover, #password_input:hover {
                border-color: #85c1e9;
            }
            
            #toggle_password_btn {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background-color: white;
                font-size: 12px;
            }
            
            #toggle_password_btn:hover {
                background-color: #ecf0f1;
                border-color: #85c1e9;
            }
            
            #toggle_password_btn:pressed {
                background-color: #3498db;
                color: white;
            }
            
            QCheckBox {
                color: #2c3e50;
                font-size: 11px;
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border-color: #3498db;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }
            
            #login_btn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #3498db, stop:1 #2980b9);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 30px;
                font-weight: bold;
                font-size: 14px;
                min-width: 120px;
            }
            
            #login_btn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #5dade2, stop:1 #3498db);
            }
            
            #login_btn:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #2980b9, stop:1 #21618c);
            }
            
            #login_btn:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
            
            #cancel_btn {
                background-color: transparent;
                color: #7f8c8d;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 12px 30px;
                font-weight: bold;
                font-size: 14px;
                min-width: 120px;
            }
            
            #cancel_btn:hover {
                background-color: #ecf0f1;
                border-color: #95a5a6;
                color: #2c3e50;
            }
            
            #status_label {
                font-size: 12px;
                padding: 8px;
                border-radius: 6px;
                margin: 5px 0;
            }
            
            #login_footer {
                margin-top: 15px;
                padding-top: 15px;
                border-top: 1px solid #ecf0f1;
            }
            
            #system_info {
                color: #7f8c8d;
                font-size: 11px;
                font-style: italic;
            }
            
            #default_user_info {
                color: #e67e22;
                font-size: 10px;
                font-weight: bold;
                margin-top: 5px;
            }
        """)
    
    def setup_validators(self):
        """Configurar validadores de entrada"""
        # Validador para username (solo letras, números y algunos caracteres especiales)
        username_regex = QRegExp("[a-zA-Z0-9_.-]+")
        username_validator = QRegExpValidator(username_regex)
        self.username_input.setValidator(username_validator)
    
    def toggle_password_visibility(self):
        """Alternar visibilidad de la contraseña"""
        if self.toggle_password_btn.isChecked():
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.toggle_password_btn.setText("🙈")
            self.show_password_cb.setChecked(True)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.toggle_password_btn.setText("👁")
            self.show_password_cb.setChecked(False)
    
    def on_show_password_toggled(self, checked: bool):
        """Manejar cambio en checkbox de mostrar contraseña"""
        if checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.toggle_password_btn.setChecked(True)
            self.toggle_password_btn.setText("🙈")
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.toggle_password_btn.setChecked(False)
            self.toggle_password_btn.setText("👁")
    
    def clear_status(self):
        """Limpiar mensaje de estado"""
        self.status_label.clear()
        self.status_label.setStyleSheet("")
    
    def show_status(self, message: str, status_type: str = "info"):
        """Mostrar mensaje de estado"""
        self.status_label.setText(message)
        
        if status_type == "error":
            self.status_label.setStyleSheet("""
                background-color: #fadbd8;
                color: #c0392b;
                border: 1px solid #f1948a;
            """)
        elif status_type == "warning":
            self.status_label.setStyleSheet("""
                background-color: #fef9e7;
                color: #b7950b;
                border: 1px solid #f4d03f;
            """)
        elif status_type == "success":
            self.status_label.setStyleSheet("""
                background-color: #d5f4e6;
                color: #27ae60;
                border: 1px solid #82e0aa;
            """)
        else:  # info
            self.status_label.setStyleSheet("""
                background-color: #ebf3fd;
                color: #2471a3;
                border: 1px solid #85c1e9;
            """)
    
    def attempt_login(self):
        """Intentar iniciar sesión"""
        if self.login_btn.isEnabled() == False:
            return
        
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        # Validaciones básicas
        if not username:
            self.show_status("Por favor ingrese su nombre de usuario", "error")
            self.username_input.setFocus()
            return
        
        if not password:
            self.show_status("Por favor ingrese su contraseña", "error")
            self.password_input.setFocus()
            return
        
        # Deshabilitar botón temporalmente
        self.login_btn.setEnabled(False)
        self.show_status("Verificando credenciales...", "info")
        
        # Procesar en el próximo ciclo del event loop para mostrar el mensaje
        QTimer.singleShot(100, lambda: self._process_login(username, password))
    
    def _process_login(self, username: str, password: str):
        """Procesar login en segundo plano"""
        try:
            # Intentar autenticación
            success, message, user_data = self.user_manager.authenticate_user(username, password)
            
            if success:
                self.authenticated_user = user_data
                self.failed_attempts = 0
                
                # Guardar credenciales si está marcado
                if self.remember_me_cb.isChecked():
                    self.save_credentials(username)
                
                self.show_status("Acceso autorizado. Iniciando sistema...", "success")
                
                # Pequelña pausa para mostrar mensaje de éxito
                QTimer.singleShot(1000, self.accept)
                
            else:
                self.failed_attempts += 1
                self.show_status(message, "error")
                
                # Limpiar contraseña
                self.password_input.clear()
                self.password_input.setFocus()
                
                # Verificar intentos fallidos
                if self.failed_attempts >= self.max_attempts:
                    self.lock_login_temporarily()
                else:
                    remaining = self.max_attempts - self.failed_attempts
                    self.show_status(f"{message}. Intentos restantes: {remaining}", "error")
                
                # Reactivar botón
                self.login_btn.setEnabled(True)
                
        except Exception as e:
            logger.error(f"Error durante autenticación: {e}")
            self.show_status("Error interno del sistema. Contacte al administrador.", "error")
            self.login_btn.setEnabled(True)
    
    def lock_login_temporarily(self):
        """Bloquear login temporalmente"""
        lockout_seconds = 30
        self.show_status(f"Demasiados intentos fallidos. Bloqueado por {lockout_seconds} segundos.", "error")
        
        # Deshabilitar campos
        self.username_input.setEnabled(False)
        self.password_input.setEnabled(False)
        self.login_btn.setEnabled(False)
        
        # Iniciar countdown
        self.lockout_remaining = lockout_seconds
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_lockout_countdown)
        self.countdown_timer.start(1000)
        
        # Timer principal para desbloquear
        self.lockout_timer.start(lockout_seconds * 1000)
    
    def update_lockout_countdown(self):
        """Actualizar countdown de bloqueo"""
        self.lockout_remaining -= 1
        if self.lockout_remaining > 0:
            self.show_status(f"Sistema bloqueado. Tiempo restante: {self.lockout_remaining} segundos.", "warning")
        else:
            self.countdown_timer.stop()
    
    def unlock_login(self):
        """Desbloquear login después del timeout"""
        self.lockout_timer.stop()
        if hasattr(self, 'countdown_timer'):
            self.countdown_timer.stop()
        
        # Reactivar campos
        self.username_input.setEnabled(True)
        self.password_input.setEnabled(True)
        self.login_btn.setEnabled(True)
        
        # Resetear intentos
        self.failed_attempts = 0
        
        # Limpiar status
        self.clear_status()
        self.show_status("Sistema desbloqueado. Puede intentar nuevamente.", "info")
        
        # Foco en username
        self.username_input.setFocus()
    
    def load_saved_credentials(self):
        """Cargar credenciales guardadas"""
        try:
            from PyQt5.QtCore import QSettings
            settings = QSettings("AlmacenPro", "LoginCredentials")
            
            saved_username = settings.value("username", "")
            remember_user = settings.value("remember_user", False, type=bool)
            
            if saved_username and remember_user:
                self.username_input.setText(saved_username)
                self.remember_me_cb.setChecked(True)
                self.password_input.setFocus()
            
        except Exception as e:
            logger.warning(f"Error cargando credenciales guardadas: {e}")
    
    def save_credentials(self, username: str):
        """Guardar credenciales para recordar"""
        try:
            from PyQt5.QtCore import QSettings
            settings = QSettings("AlmacenPro", "LoginCredentials")
            
            settings.setValue("username", username)
            settings.setValue("remember_user", True)
            
        except Exception as e:
            logger.warning(f"Error guardando credenciales: {e}")
    
    def clear_saved_credentials(self):
        """Limpiar credenciales guardadas"""
        try:
            from PyQt5.QtCore import QSettings
            settings = QSettings("AlmacenPro", "LoginCredentials")
            settings.clear()
            
        except Exception as e:
            logger.warning(f"Error limpiando credenciales: {e}")
    
    def get_authenticated_user(self) -> dict:
        """Obtener datos del usuario autenticado"""
        return self.authenticated_user
    
    def keyPressEvent(self, event):
        """Manejar eventos de teclado"""
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if not self.login_btn.isEnabled():
                return
                
            if self.username_input.hasFocus() and not self.username_input.text().strip():
                return
            elif self.password_input.hasFocus() or self.login_btn.hasFocus():
                self.attempt_login()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Manejar cierre del diálogo"""
        # Detener timers si están activos
        if hasattr(self, 'lockout_timer'):
            self.lockout_timer.stop()
        if hasattr(self, 'countdown_timer'):
            self.countdown_timer.stop()
        
        # Si no hay usuario autenticado y se cierra, es cancelación
        if not self.authenticated_user:
            self.reject()
        
        event.accept()
    
    def reject(self):
        """Rechazar diálogo (cancelar)"""
        # Limpiar credenciales si no se debe recordar
        if not self.remember_me_cb.isChecked():
            self.clear_saved_credentials()
        
        super().reject()
    
    def accept(self):
        """Aceptar diálogo (login exitoso)"""
        if self.authenticated_user:
            super().accept()
        else:
            # No se puede aceptar sin autenticación válida
            self.show_status("Error: No hay usuario autenticado", "error")


class LoginSplashScreen(QSplashScreen):
    """Splash screen personalizado para mostrar durante la carga"""
    
    def __init__(self):
        # Crear pixmap personalizado
        pixmap = QPixmap(400, 300)
        pixmap.fill(Qt.white)
        
        super().__init__(pixmap)
        
        # Configurar estilo
        self.setStyleSheet("""
            QSplashScreen {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #2E86AB, stop:1 #A23B72);
                border: 3px solid #2E86AB;
                border-radius: 15px;
            }
        """)
        
        # Mostrar información de carga
        self.showMessage(
            "AlmacénPro v2.0\n\nIniciando sistema...",
            Qt.AlignCenter | Qt.AlignBottom,
            Qt.white
        )
    
    def update_message(self, message: str):
        """Actualizar mensaje del splash"""
        self.showMessage(
            f"AlmacénPro v2.0\n\n{message}",
            Qt.AlignCenter | Qt.AlignBottom,
            Qt.white
        )
        QApplication.processEvents()


# Función de utilidad para mostrar diálogo de login
def show_login_dialog(user_manager, parent=None) -> tuple:
    """
    Mostrar diálogo de login y retornar resultado
    
    Returns:
        tuple: (success: bool, user_data: dict or None)
    """
    try:
        dialog = LoginDialog(user_manager, parent)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            return True, dialog.get_authenticated_user()
        else:
            return False, None
            
    except Exception as e:
        logger.error(f"Error mostrando diálogo de login: {e}")
        return False, None