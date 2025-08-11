"""
Login Controller - AlmacénPro v2.0 MVC
Controller para diálogo de autenticación usando .ui file
"""

import logging
from PyQt5.QtWidgets import QDialog, QTimer, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5 import uic
from controllers.base_controller import BaseController

logger = logging.getLogger(__name__)

class LoginController(BaseController):
    """Controller para el diálogo de login usando archivo .ui"""
    
    # Señal emitida cuando el login es exitoso
    login_successful = pyqtSignal(dict)  # user_data
    
    def __init__(self, user_manager, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.authenticated_user = None
        self.failed_attempts = 0
        self.max_attempts = 3
        
        # Setup UI
        self.setup_ui()
        self.setup_validators()
        self.setup_lockout_timer()
        
    def get_ui_file_path(self) -> str:
        """Retorna la ruta del archivo .ui"""
        return "views/dialogs/login_dialog.ui"
    
    def setup_ui(self):
        """Configuración específica de la UI después de cargar el archivo .ui"""
        super().setup_ui()
        
        # Configurar window properties
        self.setWindowTitle("AlmacénPro - Iniciar Sesión")
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.setModal(True)
        
        # Configurar valores por defecto para desarrollo
        if hasattr(self, 'txtUsername') and hasattr(self, 'txtPassword'):
            # Valores por defecto para facilitar desarrollo
            self.txtUsername.setText("admin")
            self.txtPassword.setText("")
            
            # Focus en password si username ya está lleno
            if self.txtUsername.text():
                self.txtPassword.setFocus()
            else:
                self.txtUsername.setFocus()
    
    def connect_signals(self):
        """Conectar señales específicas del login"""
        super().connect_signals()
        
        # Conectar botones
        if hasattr(self, 'btnLogin'):
            self.btnLogin.clicked.connect(self.attempt_login)
        if hasattr(self, 'btnCancel'):
            self.btnCancel.clicked.connect(self.reject)
            
        # Conectar Enter en campos de texto
        if hasattr(self, 'txtUsername'):
            self.txtUsername.returnPressed.connect(self.move_to_password)
        if hasattr(self, 'txtPassword'):
            self.txtPassword.returnPressed.connect(self.attempt_login)
            
        # Conectar cambios en campos para resetear errores
        if hasattr(self, 'txtUsername'):
            self.txtUsername.textChanged.connect(self.clear_error_styling)
        if hasattr(self, 'txtPassword'):
            self.txtPassword.textChanged.connect(self.clear_error_styling)
    
    def setup_validators(self):
        """Configurar validadores para los campos"""
        # Los validadores se pueden configurar en el .ui file
        # o aquí si se necesita lógica específica
        pass
    
    def setup_lockout_timer(self):
        """Configurar timer para bloqueo temporal"""
        self.lockout_timer = QTimer()
        self.lockout_timer.timeout.connect(self.unlock_login)
    
    def move_to_password(self):
        """Mover foco al campo de contraseña"""
        if hasattr(self, 'txtPassword'):
            self.txtPassword.setFocus()
    
    def attempt_login(self):
        """Intentar autenticación"""
        try:
            username = self.txtUsername.text().strip() if hasattr(self, 'txtUsername') else ""
            password = self.txtPassword.text() if hasattr(self, 'txtPassword') else ""
            
            # Validar campos obligatorios
            if not username:
                self.show_error("Por favor, ingrese su usuario")
                self.txtUsername.setFocus()
                return
                
            if not password:
                self.show_error("Por favor, ingrese su contraseña")
                self.txtPassword.setFocus()
                return
            
            # Deshabilitar botón durante la autenticación
            if hasattr(self, 'btnLogin'):
                self.btnLogin.setEnabled(False)
                self.btnLogin.setText("Validando...")
            
            # Intentar autenticación
            result = self.user_manager.authenticate_user(username, password)
            
            if result and result.get('success', False):
                # Login exitoso
                self.authenticated_user = result.get('user')
                logger.info(f"Login exitoso para usuario: {username}")
                
                # Emitir señal de login exitoso
                self.login_successful.emit(self.authenticated_user)
                
                # Cerrar diálogo con éxito
                self.accept()
                
            else:
                # Login fallido
                self.failed_attempts += 1
                error_message = result.get('message', 'Usuario o contraseña incorrectos')
                
                logger.warning(f"Login fallido para usuario: {username}. Intento {self.failed_attempts}/{self.max_attempts}")
                
                if self.failed_attempts >= self.max_attempts:
                    self.lockout_login()
                else:
                    self.show_error(f"{error_message}\nIntentos restantes: {self.max_attempts - self.failed_attempts}")
                
                # Limpiar contraseña
                if hasattr(self, 'txtPassword'):
                    self.txtPassword.clear()
                    self.txtPassword.setFocus()
                
                # Estilo de error en campos
                self.apply_error_styling()
        
        except Exception as e:
            logger.error(f"Error en attempt_login: {e}")
            self.show_error("Error interno del sistema. Contacte al administrador.")
        
        finally:
            # Rehabilitar botón
            if hasattr(self, 'btnLogin'):
                self.btnLogin.setEnabled(True)
                self.btnLogin.setText("Iniciar Sesión")
    
    def lockout_login(self):
        """Bloquear login temporalmente por múltiples intentos fallidos"""
        lockout_time = 30  # 30 segundos
        self.show_error(f"Demasiados intentos fallidos. Bloqueado por {lockout_time} segundos.")
        
        # Deshabilitar campos y botón
        if hasattr(self, 'txtUsername'):
            self.txtUsername.setEnabled(False)
        if hasattr(self, 'txtPassword'):
            self.txtPassword.setEnabled(False)
        if hasattr(self, 'btnLogin'):
            self.btnLogin.setEnabled(False)
            self.btnLogin.setText("Bloqueado")
        
        # Iniciar timer de desbloqueo
        self.lockout_timer.start(lockout_time * 1000)
    
    def unlock_login(self):
        """Desbloquear login después del tiempo de espera"""
        self.lockout_timer.stop()
        self.failed_attempts = 0
        
        # Rehabilitar campos y botón
        if hasattr(self, 'txtUsername'):
            self.txtUsername.setEnabled(True)
        if hasattr(self, 'txtPassword'):
            self.txtPassword.setEnabled(True)
        if hasattr(self, 'btnLogin'):
            self.btnLogin.setEnabled(True)
            self.btnLogin.setText("Iniciar Sesión")
        
        # Limpiar mensajes de error
        self.clear_error_styling()
        
        # Focus en username
        if hasattr(self, 'txtUsername'):
            self.txtUsername.setFocus()
    
    def show_error(self, message: str):
        """Mostrar mensaje de error"""
        if hasattr(self, 'lblError'):
            self.lblError.setText(message)
            self.lblError.setVisible(True)
        else:
            # Fallback a MessageBox si no hay label de error en el .ui
            QMessageBox.warning(self, "Error de Autenticación", message)
    
    def clear_error_styling(self):
        """Limpiar estilos de error y mensajes"""
        if hasattr(self, 'lblError'):
            self.lblError.clear()
            self.lblError.setVisible(False)
        
        # Restaurar estilos normales de los campos
        if hasattr(self, 'txtUsername'):
            self.txtUsername.setStyleSheet("")
        if hasattr(self, 'txtPassword'):
            self.txtPassword.setStyleSheet("")
    
    def apply_error_styling(self):
        """Aplicar estilos de error a los campos"""
        error_style = """
            QLineEdit {
                border: 2px solid #e74c3c;
                border-radius: 4px;
                padding: 8px;
                background-color: #fdf2f2;
            }
        """
        
        if hasattr(self, 'txtUsername'):
            self.txtUsername.setStyleSheet(error_style)
        if hasattr(self, 'txtPassword'):
            self.txtPassword.setStyleSheet(error_style)
    
    def get_authenticated_user(self):
        """Obtener usuario autenticado después del login exitoso"""
        return self.authenticated_user
    
    def reset_form(self):
        """Resetear formulario para nuevo intento"""
        if hasattr(self, 'txtUsername'):
            self.txtUsername.clear()
        if hasattr(self, 'txtPassword'):
            self.txtPassword.clear()
        
        self.clear_error_styling()
        self.failed_attempts = 0
        self.authenticated_user = None
        
        if hasattr(self, 'txtUsername'):
            self.txtUsername.setFocus()


# Función helper para facilitar el uso
def show_login_dialog(user_manager, parent=None):
    """
    Función helper para mostrar el diálogo de login
    
    Returns:
        tuple: (success: bool, user_data: dict or None)
    """
    try:
        dialog = LoginController(user_manager, parent)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            return True, dialog.get_authenticated_user()
        else:
            return False, None
            
    except Exception as e:
        logger.error(f"Error mostrando diálogo de login: {e}")
        return False, None