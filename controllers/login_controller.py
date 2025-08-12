"""
Login Controller - AlmacénPro v2.0 MVC
Controller para diálogo de autenticación usando .ui file
"""

import logging
from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5 import uic
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class LoginController(QDialog):
    """Controller para el diálogo de login usando archivo .ui"""
    
    # Señal emitida cuando el login es exitoso
    login_successful = pyqtSignal(dict)  # user_data
    
    def __init__(self, user_manager, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.authenticated_user = None
        self.failed_attempts = 0
        self.max_attempts = 3
        
        # Cargar UI
        self.load_ui()
        
        # Setup específico
        self.setup_ui()
        self.connect_signals()
        self.setup_validators()
        self.setup_lockout_timer()
    
    def load_ui(self):
        """Cargar archivo .ui"""
        try:
            ui_path = Path("views/dialogs/login_dialog.ui")
            if ui_path.exists():
                uic.loadUi(str(ui_path), self)
                logger.info(f"UI cargada desde: {ui_path}")
            else:
                logger.error(f"Archivo UI no encontrado: {ui_path}")
                raise FileNotFoundError(f"Archivo UI no encontrado: {ui_path}")
        except Exception as e:
            logger.error(f"Error cargando UI: {e}")
            raise
    
    def setup_ui(self):
        """Configuración específica de la UI después de cargar el archivo .ui"""
        
        # Configurar window properties
        self.setWindowTitle("AlmacénPro - Iniciar Sesión")
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.setModal(True)
        
        # Configurar valores por defecto para desarrollo
        if hasattr(self, 'lineEditUsername') and hasattr(self, 'lineEditPassword'):
            # Valores por defecto para facilitar desarrollo
            self.lineEditUsername.setText("admin")
            self.lineEditPassword.setText("")
            
            # Focus en password si username ya está lleno
            if self.lineEditUsername.text():
                self.lineEditPassword.setFocus()
            else:
                self.lineEditUsername.setFocus()
    
    def connect_signals(self):
        """Conectar señales específicas del login"""
        
        # Conectar botones
        if hasattr(self, 'btnLogin'):
            self.btnLogin.clicked.connect(self.attempt_login)
        if hasattr(self, 'btnCancel'):
            self.btnCancel.clicked.connect(self.reject)
            
        # Conectar Enter en campos de texto
        if hasattr(self, 'lineEditUsername'):
            self.lineEditUsername.returnPressed.connect(self.move_to_password)
        if hasattr(self, 'lineEditPassword'):
            self.lineEditPassword.returnPressed.connect(self.attempt_login)
            
        # Conectar cambios en campos para resetear errores
        if hasattr(self, 'lineEditUsername'):
            self.lineEditUsername.textChanged.connect(self.clear_error_styling)
        if hasattr(self, 'lineEditPassword'):
            self.lineEditPassword.textChanged.connect(self.clear_error_styling)
    
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
        if hasattr(self, 'lineEditPassword'):
            self.lineEditPassword.setFocus()
    
    def attempt_login(self):
        """Intentar autenticación"""
        try:
            username = self.lineEditUsername.text().strip() if hasattr(self, 'lineEditUsername') else ""
            password = self.lineEditPassword.text() if hasattr(self, 'lineEditPassword') else ""
            
            # Validar campos obligatorios
            if not username:
                self.show_error("Por favor, ingrese su usuario")
                if hasattr(self, 'lineEditUsername'):
                    self.lineEditUsername.setFocus()
                return
                
            if not password:
                self.show_error("Por favor, ingrese su contraseña")
                if hasattr(self, 'lineEditPassword'):
                    self.lineEditPassword.setFocus()
                return
            
            # Deshabilitar botón durante la autenticación
            if hasattr(self, 'btnLogin'):
                self.btnLogin.setEnabled(False)
                self.btnLogin.setText("Validando...")
            
            # Intentar autenticación
            success, message, user_data = self.user_manager.authenticate_user(username, password)
            
            if success and user_data:
                # Login exitoso
                self.authenticated_user = user_data
                logger.info(f"Login exitoso para usuario: {username}")
                
                # Emitir señal de login exitoso
                self.login_successful.emit(self.authenticated_user)
                
                # Cerrar diálogo con éxito
                self.accept()
                
            else:
                # Login fallido
                self.failed_attempts += 1
                error_message = message or 'Usuario o contraseña incorrectos'
                
                logger.warning(f"Login fallido para usuario: {username}. Intento {self.failed_attempts}/{self.max_attempts}")
                
                if self.failed_attempts >= self.max_attempts:
                    self.lockout_login()
                else:
                    self.show_error(f"{error_message}\nIntentos restantes: {self.max_attempts - self.failed_attempts}")
                
                # Limpiar contraseña
                if hasattr(self, 'lineEditPassword'):
                    self.lineEditPassword.clear()
                    self.lineEditPassword.setFocus()
                
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
        if hasattr(self, 'lineEditUsername'):
            self.lineEditUsername.setEnabled(False)
        if hasattr(self, 'lineEditPassword'):
            self.lineEditPassword.setEnabled(False)
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
        if hasattr(self, 'lineEditUsername'):
            self.lineEditUsername.setEnabled(True)
        if hasattr(self, 'lineEditPassword'):
            self.lineEditPassword.setEnabled(True)
        if hasattr(self, 'btnLogin'):
            self.btnLogin.setEnabled(True)
            self.btnLogin.setText("Iniciar Sesión")
        
        # Limpiar mensajes de error
        self.clear_error_styling()
        
        # Focus en username
        if hasattr(self, 'lineEditUsername'):
            self.lineEditUsername.setFocus()
    
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
        if hasattr(self, 'lineEditUsername'):
            self.lineEditUsername.setStyleSheet("")
        if hasattr(self, 'lineEditPassword'):
            self.lineEditPassword.setStyleSheet("")
    
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
        
        if hasattr(self, 'lineEditUsername'):
            self.lineEditUsername.setStyleSheet(error_style)
        if hasattr(self, 'lineEditPassword'):
            self.lineEditPassword.setStyleSheet(error_style)
    
    def get_authenticated_user(self):
        """Obtener usuario autenticado después del login exitoso"""
        return self.authenticated_user
    
    def reset_form(self):
        """Resetear formulario para nuevo intento"""
        if hasattr(self, 'lineEditUsername'):
            self.lineEditUsername.clear()
        if hasattr(self, 'lineEditPassword'):
            self.lineEditPassword.clear()
        
        self.clear_error_styling()
        self.failed_attempts = 0
        self.authenticated_user = None
        
        if hasattr(self, 'lineEditUsername'):
            self.lineEditUsername.setFocus()


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