"""
Diálogo de login para AlmacénPro
Sistema de autenticación con validación de usuarios y roles
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
        self.init_ui()
        self.setup_styles()
        
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        self.setWindowTitle("AlmacénPro - Iniciar Sesión")
        self.setFixedSize(400, 300)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(40, 30, 40, 30)
        
        # Logo y título
        self.create_header(main_layout)
        
        # Formulario de login
        self.create_login_form(main_layout)
        
        # Botones
        self.create_buttons(main_layout)
        
        # Información adicional
        self.create_footer(main_layout)
        
        self.setLayout(main_layout)
        
        # Configurar tab order
        self.setTabOrder(self.username_input, self.password_input)
        self.setTabOrder(self.password_input, self.login_btn)
        self.setTabOrder(self.login_btn, self.cancel_btn)
        
        # Foco inicial en username
        self.username_input.setFocus()
    
    def create_header(self, layout):
        """Crear header con logo y título"""
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignCenter)
        
        # Logo placeholder (se puede reemplazar con imagen real)
        logo_label = QLabel("🏪")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("font-size: 48px; margin-bottom: 10px;")
        header_layout.addWidget(logo_label)
        
        # Título
        title_label = QLabel("AlmacénPro v2.0")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            color: #2E86AB; 
            margin-bottom: 5px;
        """)
        header_layout.addWidget(title_label)
        
        # Subtítulo
        subtitle_label = QLabel("Sistema de Gestión Completo")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("font-size: 12px; color: #666; margin-bottom: 20px;")
        header_layout.addWidget(subtitle_label)
        
        layout.addLayout(header_layout)
    
    def create_login_form(self, layout):
        """Crear formulario de login"""
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Campo de usuario
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Ingrese su usuario")
        self.username_input.returnPressed.connect(self.password_input.setFocus)
        
        user_icon = QLabel("👤")
        user_icon.setFixedWidth(25)
        user_layout = QHBoxLayout()
        user_layout.addWidget(user_icon)
        user_layout.addWidget(self.username_input)
        user_layout.setContentsMargins(0, 0, 0, 0)
        user_widget = QWidget()
        user_widget.setLayout(user_layout)
        
        form_layout.addRow("Usuario:", user_widget)
        
        # Campo de contraseña
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Ingrese su contraseña")
        self.password_input.returnPressed.connect(self.attempt_login)
        
        pass_icon = QLabel("🔐")
        pass_icon.setFixedWidth(25)
        pass_layout = QHBoxLayout()
        pass_layout.addWidget(pass_icon)
        pass_layout.addWidget(self.password_input)
        pass_layout.setContentsMargins(0, 0, 0, 0)
        pass_widget = QWidget()
        pass_widget.setLayout(pass_layout)
        
        form_layout.addRow("Contraseña:", pass_widget)
        
        # Checkbox para mostrar contraseña
        self.show_password_cb = QCheckBox("Mostrar contraseña")
        self.show_password_cb.toggled.connect(self.toggle_password_visibility)
        form_layout.addRow("", self.show_password_cb)
        
        layout.addLayout(form_layout)
        
        # Mensaje de error
        self.error_label = QLabel()
        self.error_label.setStyleSheet("""
            color: #e74c3c; 
            font-weight: bold; 
            padding: 5px; 
            background-color: #fdf2f2; 
            border: 1px solid #fadadd; 
            border-radius: 4px;
        """)
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
    
    def create_buttons(self, layout):
        """Crear botones de acción"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Botón de cancelar
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setFixedHeight(35)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        # Espaciador
        button_layout.addStretch()
        
        # Botón de login
        self.login_btn = QPushButton("Iniciar Sesión")
        self.login_btn.setFixedHeight(35)
        self.login_btn.setDefault(True)
        self.login_btn.clicked.connect(self.attempt_login)
        button_layout.addWidget(self.login_btn)
        
        layout.addLayout(button_layout)
    
    def create_footer(self, layout):
        """Crear footer con información adicional"""
        footer_layout = QVBoxLayout()
        footer_layout.setAlignment(Qt.AlignCenter)
        footer_layout.setSpacing(5)
        
        # Información de usuario por defecto
        default_info = QLabel("Usuario por defecto: admin | Contraseña: admin123")
        default_info.setStyleSheet("font-size: 10px; color: #888; font-style: italic;")
        default_info.setAlignment(Qt.AlignCenter)
        footer_layout.addWidget(default_info)
        
        # Separador
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("margin: 10px 0;")
        footer_layout.addWidget(line)
        
        # Botón de configuración de conexión
        config_btn = QPushButton("⚙️ Configurar Conexión")
        config_btn.setFlat(True)
        config_btn.setStyleSheet("color: #2E86AB; text-decoration: underline;")
        config_btn.clicked.connect(self.show_connection_config)
        footer_layout.addWidget(config_btn)
        
        layout.addLayout(footer_layout)
    
    def setup_styles(self):
        """Configurar estilos CSS"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
                border-radius: 10px;
            }
            
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                font-size: 14px;
                background-color: white;
            }
            
            QLineEdit:focus {
                border-color: #2E86AB;
                outline: none;
            }
            
            QPushButton {
                padding: 8px 20px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            
            QPushButton#login_btn {
                background-color: #2E86AB;
                color: white;
            }
            
            QPushButton#login_btn:hover {
                background-color: #1e5f7a;
            }
            
            QPushButton#login_btn:pressed {
                background-color: #164a5e;
            }
            
            QPushButton#cancel_btn {
                background-color: #6c757d;
                color: white;
            }
            
            QPushButton#cancel_btn:hover {
                background-color: #5a6268;
            }
            
            QCheckBox {
                font-size: 12px;
                color: #495057;
            }
            
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            
            QCheckBox::indicator:unchecked {
                border: 2px solid #ced4da;
                border-radius: 3px;
                background-color: white;
            }
            
            QCheckBox::indicator:checked {
                border: 2px solid #2E86AB;
                border-radius: 3px;
                background-color: #2E86AB;
                image: url(check.png); /* Se puede agregar icono de check */
            }
            
            QFormLayout QLabel {
                font-weight: bold;
                color: #495057;
            }
        """)
        
        # Aplicar IDs para estilos específicos
        self.login_btn.setObjectName("login_btn")
        self.cancel_btn.setObjectName("cancel_btn")
    
    def toggle_password_visibility(self, checked):
        """Alternar visibilidad de contraseña"""
        if checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
    
    def attempt_login(self):
        """Intentar autenticación"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        # Validaciones básicas
        if not username:
            self.show_error("Por favor ingrese su nombre de usuario")
            self.username_input.setFocus()
            return
        
        if not password:
            self.show_error("Por favor ingrese su contraseña")
            self.password_input.setFocus()
            return
        
        # Deshabilitar botón mientras se autentica
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Autenticando...")
        
        # Procesar autenticación en el siguiente ciclo de eventos
        QTimer.singleShot(100, lambda: self.process_login(username, password))
    
    def process_login(self, username, password):
        """Procesar login en el gestor de usuarios"""
        try:
            success, message = self.user_manager.login(username, password)
            
            if success:
                logger.info(f"Login exitoso para usuario: {username}")
                self.accept()  # Cerrar diálogo con éxito
            else:
                self.show_error(message)
                logger.warning(f"Login fallido para usuario: {username}")
                
                # Limpiar contraseña en caso de error
                self.password_input.clear()
                self.password_input.setFocus()
                
        except Exception as e:
            logger.error(f"Error durante el login: {e}")
            self.show_error("Error interno durante la autenticación")
        
        finally:
            # Restaurar botón
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Iniciar Sesión")
    
    def show_error(self, message):
        """Mostrar mensaje de error"""
        self.error_label.setText(f"❌ {message}")
        self.error_label.show()
        
        # Ocultar error después de 5 segundos
        QTimer.singleShot(5000, self.error_label.hide)
        
        # Efecto visual de shake
        self.shake_dialog()
    
    def shake_dialog(self):
        """Efecto de shake para indicar error"""
        try:
            original_pos = self.pos()
            
            # Crear animación de shake
            self.animation = QPropertyAnimation(self, b"pos")
            self.animation.setDuration(500)
            self.animation.setLoopCount(3)
            
            # Definir keyframes
            self.animation.setKeyValueAt(0, original_pos)
            self.animation.setKeyValueAt(0.25, QPoint(original_pos.x() + 10, original_pos.y()))
            self.animation.setKeyValueAt(0.75, QPoint(original_pos.x() - 10, original_pos.y()))
            self.animation.setKeyValueAt(1, original_pos)
            
            self.animation.start()
            
        except Exception as e:
            logger.error(f"Error en animación shake: {e}")
    
    def show_connection_config(self):
        """Mostrar configuración de conexión a BD"""
        msg = QMessageBox.information(
            self, "Configuración de Conexión",
            "Configuración de conexión a base de datos:\n\n"
            "• Tipo: SQLite\n"
            "• Archivo: data/almacen_pro.db\n"
            "• Estado: Conectado ✅\n\n"
            "Para configuraciones avanzadas, contacte al administrador."
        )
    
    def keyPressEvent(self, event):
        """Manejar eventos de teclado"""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if self.username_input.hasFocus():
                self.password_input.setFocus()
            elif self.password_input.hasFocus():
                self.attempt_login()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Manejar cierre del diálogo"""
        # Si el usuario cierra la ventana, considerarlo como cancelación
        self.reject()
        event.accept()


class ChangePasswordDialog(QDialog):
    """Diálogo para cambiar contraseña"""
    
    def __init__(self, user_manager, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.init_ui()
    
    def init_ui(self):
        """Inicializar interfaz"""
        self.setWindowTitle("Cambiar Contraseña")
        self.setFixedSize(350, 250)
        
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("Cambiar Contraseña")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Formulario
        form_layout = QFormLayout()
        
        self.current_password = QLineEdit()
        self.current_password.setEchoMode(QLineEdit.Password)
        self.current_password.setPlaceholderText("Contraseña actual")
        form_layout.addRow("Contraseña Actual:", self.current_password)
        
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.Password)
        self.new_password.setPlaceholderText("Nueva contraseña")
        form_layout.addRow("Nueva Contraseña:", self.new_password)
        
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.Password)
        self.confirm_password.setPlaceholderText("Confirmar contraseña")
        form_layout.addRow("Confirmar:", self.confirm_password)
        
        layout.addLayout(form_layout)
        
        # Mensaje de error
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red; font-weight: bold;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # Botones
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Cambiar Contraseña")
        save_btn.setStyleSheet("background-color: #2E86AB; color: white; font-weight: bold;")
        save_btn.clicked.connect(self.change_password)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def change_password(self):
        """Cambiar contraseña"""
        current = self.current_password.text()
        new_pass = self.new_password.text()
        confirm = self.confirm_password.text()
        
        if not all([current, new_pass, confirm]):
            self.show_error("Todos los campos son obligatorios")
            return
        
        if new_pass != confirm:
            self.show_error("Las contraseñas nuevas no coinciden")
            return
        
        if len(new_pass) < 6:
            self.show_error("La nueva contraseña debe tener al menos 6 caracteres")
            return
        
        try:
            user_id = self.user_manager.current_user['id']
            success, message = self.user_manager.change_password(user_id, current, new_pass)
            
            if success:
                QMessageBox.information(self, "Éxito", "Contraseña cambiada exitosamente")
                self.accept()
            else:
                self.show_error(message)
                
        except Exception as e:
            self.show_error(f"Error cambiando contraseña: {str(e)}")
    
    def show_error(self, message):
        """Mostrar mensaje de error"""
        self.error_label.setText(message)
        self.error_label.show()