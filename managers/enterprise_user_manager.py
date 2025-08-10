"""
Sistema de Usuarios Empresarial - AlmacénPro v2.0
Gestión avanzada de usuarios con 2FA, SSO y auditoría completa
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import hashlib
import secrets
import base64
from enum import Enum
import uuid

# Para 2FA
try:
    import pyotp
    import qrcode
    from io import BytesIO
    TOTP_AVAILABLE = True
except ImportError:
    TOTP_AVAILABLE = False
    logger.warning("PyOTP no disponible - 2FA deshabilitado")

logger = logging.getLogger(__name__)

class SessionStatus(Enum):
    """Estados de sesión"""
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    LOCKED = "locked"

class AuditAction(Enum):
    """Tipos de acciones para auditoría"""
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    PROFILE_UPDATE = "profile_update"
    PERMISSION_CHANGE = "permission_change"
    ROLE_CHANGE = "role_change"
    ACCOUNT_LOCK = "account_lock"
    ACCOUNT_UNLOCK = "account_unlock"
    TWO_FA_ENABLE = "2fa_enable"
    TWO_FA_DISABLE = "2fa_disable"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    DATA_ACCESS = "data_access"
    DATA_EXPORT = "data_export"
    SYSTEM_ADMIN = "system_admin"

class EnterpriseUserManager:
    """Manager empresarial de usuarios con funcionalidades avanzadas"""
    
    def __init__(self, database_manager):
        self.db = database_manager
        self.logger = logging.getLogger(__name__)
        
        # Configuraciones de seguridad
        self.max_login_attempts = 5
        self.lockout_duration_minutes = 30
        self.session_timeout_hours = 8
        self.password_min_length = 8
        self.password_require_complex = True
        self.force_2fa_for_admins = True
        
        # Configuración de auditoría
        self.audit_retention_days = 365
        self.detailed_audit = True
        
        # Inicializar tablas empresariales
        self._initialize_enterprise_tables()
    
    def _initialize_enterprise_tables(self):
        """Inicializar tablas específicas para funciones empresariales"""
        try:
            # Tabla extendida de usuarios con campos empresariales
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS users_enterprise (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    employee_id TEXT UNIQUE,
                    department TEXT,
                    job_title TEXT,
                    manager_id INTEGER,
                    hire_date DATE,
                    phone_mobile TEXT,
                    phone_extension TEXT,
                    office_location TEXT,
                    cost_center TEXT,
                    security_clearance TEXT,
                    two_factor_enabled BOOLEAN DEFAULT FALSE,
                    two_factor_secret TEXT,
                    backup_codes TEXT, -- JSON array
                    sso_provider TEXT,
                    sso_user_id TEXT,
                    password_policy_id INTEGER,
                    last_policy_acceptance TIMESTAMP,
                    emergency_contact_name TEXT,
                    emergency_contact_phone TEXT,
                    FOREIGN KEY (user_id) REFERENCES usuarios(id),
                    FOREIGN KEY (manager_id) REFERENCES usuarios(id)
                )
            """)
            
            # Tabla de sesiones empresariales
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS user_sessions_enterprise (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_id TEXT UNIQUE NOT NULL,
                    device_info TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    location_info TEXT, -- Geolocalización si está disponible
                    login_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    logout_timestamp TIMESTAMP,
                    status TEXT DEFAULT 'ACTIVE',
                    session_duration INTEGER, -- En minutos
                    terminated_by INTEGER, -- User ID que terminó la sesión
                    termination_reason TEXT,
                    FOREIGN KEY (user_id) REFERENCES usuarios(id)
                )
            """)
            
            # Tabla de intentos de login
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS login_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    user_id INTEGER,
                    ip_address TEXT,
                    user_agent TEXT,
                    attempt_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN,
                    failure_reason TEXT,
                    two_factor_used BOOLEAN DEFAULT FALSE,
                    device_fingerprint TEXT,
                    FOREIGN KEY (user_id) REFERENCES usuarios(id)
                )
            """)
            
            # Tabla de auditoría empresarial
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS audit_log_enterprise (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    session_id TEXT,
                    action_type TEXT NOT NULL,
                    action_category TEXT,
                    resource_type TEXT, -- Usuario, Cliente, Producto, etc.
                    resource_id TEXT,
                    old_values TEXT, -- JSON
                    new_values TEXT, -- JSON
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT,
                    risk_score INTEGER DEFAULT 0, -- 0-100
                    requires_review BOOLEAN DEFAULT FALSE,
                    reviewed_by INTEGER,
                    review_timestamp TIMESTAMP,
                    additional_metadata TEXT, -- JSON
                    FOREIGN KEY (user_id) REFERENCES usuarios(id),
                    FOREIGN KEY (reviewed_by) REFERENCES usuarios(id)
                )
            """)
            
            # Tabla de políticas de contraseñas
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS password_policies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    policy_name TEXT UNIQUE NOT NULL,
                    min_length INTEGER DEFAULT 8,
                    require_uppercase BOOLEAN DEFAULT TRUE,
                    require_lowercase BOOLEAN DEFAULT TRUE,
                    require_numbers BOOLEAN DEFAULT TRUE,
                    require_symbols BOOLEAN DEFAULT TRUE,
                    max_age_days INTEGER DEFAULT 90,
                    history_count INTEGER DEFAULT 5, -- No reutilizar últimas N contraseñas
                    max_failed_attempts INTEGER DEFAULT 5,
                    lockout_duration_minutes INTEGER DEFAULT 30,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (created_by) REFERENCES usuarios(id)
                )
            """)
            
            # Tabla de historial de contraseñas
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS password_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES usuarios(id)
                )
            """)
            
            # Tabla de delegaciones de permisos
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS permission_delegations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    delegator_id INTEGER NOT NULL,
                    delegate_id INTEGER NOT NULL,
                    permission_type TEXT NOT NULL,
                    resource_filter TEXT, -- JSON para filtros específicos
                    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_date TIMESTAMP,
                    active BOOLEAN DEFAULT TRUE,
                    created_by INTEGER,
                    notes TEXT,
                    FOREIGN KEY (delegator_id) REFERENCES usuarios(id),
                    FOREIGN KEY (delegate_id) REFERENCES usuarios(id),
                    FOREIGN KEY (created_by) REFERENCES usuarios(id)
                )
            """)
            
            # Tabla de tokens de acceso (para APIs y servicios externos)
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS access_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token_hash TEXT UNIQUE NOT NULL,
                    token_name TEXT,
                    scopes TEXT, -- JSON array de permisos
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    last_used_at TIMESTAMP,
                    usage_count INTEGER DEFAULT 0,
                    ip_whitelist TEXT, -- JSON array de IPs permitidas
                    active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (user_id) REFERENCES usuarios(id)
                )
            """)
            
            # Tabla de notificaciones de seguridad
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS security_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    notification_type TEXT NOT NULL,
                    severity TEXT DEFAULT 'INFO', -- INFO, WARNING, CRITICAL
                    title TEXT NOT NULL,
                    message TEXT,
                    metadata TEXT, -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    read_at TIMESTAMP,
                    dismissed_at TIMESTAMP,
                    action_taken TEXT,
                    FOREIGN KEY (user_id) REFERENCES usuarios(id)
                )
            """)
            
            # Índices para optimización
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_sessions_user_status ON user_sessions_enterprise(user_id, status)",
                "CREATE INDEX IF NOT EXISTS idx_sessions_timestamp ON user_sessions_enterprise(login_timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_login_attempts_username ON login_attempts(username, attempt_timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip_address, attempt_timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_audit_user_timestamp ON audit_log_enterprise(user_id, timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_audit_action_timestamp ON audit_log_enterprise(action_type, timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_password_history_user ON password_history(user_id, created_at)",
                "CREATE INDEX IF NOT EXISTS idx_delegations_delegate ON permission_delegations(delegate_id, active)",
                "CREATE INDEX IF NOT EXISTS idx_tokens_user_active ON access_tokens(user_id, active)",
                "CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON security_notifications(user_id, read_at)"
            ]
            
            for index_sql in indexes:
                self.db.execute_query(index_sql)
            
            # Crear política de contraseñas por defecto
            self._create_default_password_policy()
            
            self.logger.info("Tablas empresariales de usuarios inicializadas correctamente")
            
        except Exception as e:
            self.logger.error(f"Error inicializando tablas empresariales: {e}")
    
    def _create_default_password_policy(self):
        """Crear política de contraseñas por defecto"""
        try:
            # Verificar si ya existe
            existing = self.db.execute_query("""
                SELECT id FROM password_policies WHERE policy_name = 'DEFAULT'
            """)
            
            if not existing:
                self.db.execute_query("""
                    INSERT INTO password_policies 
                    (policy_name, min_length, require_uppercase, require_lowercase, 
                     require_numbers, require_symbols, max_age_days, history_count)
                    VALUES ('DEFAULT', 8, TRUE, TRUE, TRUE, FALSE, 90, 5)
                """)
                self.logger.info("Política de contraseñas por defecto creada")
                
        except Exception as e:
            self.logger.error(f"Error creando política por defecto: {e}")
    
    def enhanced_authenticate_user(self, username: str, password: str, 
                                 totp_code: str = None, device_info: Dict = None) -> Dict:
        """Autenticación empresarial con 2FA y auditoría completa"""
        try:
            ip_address = device_info.get('ip_address', '') if device_info else ''
            user_agent = device_info.get('user_agent', '') if device_info else ''
            
            # Registrar intento de login
            attempt_id = self._log_login_attempt(username, ip_address, user_agent, False)
            
            # Verificar bloqueos por IP
            if self._is_ip_blocked(ip_address):
                self._audit_action(None, None, AuditAction.LOGIN_FAILED, 
                                 "IP bloqueada por múltiples intentos fallidos", ip_address)
                return {
                    "success": False,
                    "error": "IP temporalmente bloqueada",
                    "lockout_remaining": self._get_ip_lockout_remaining(ip_address)
                }
            
            # Buscar usuario
            user_query = """
                SELECT u.*, ue.two_factor_enabled, ue.two_factor_secret, 
                       ue.employee_id, ue.department, ue.security_clearance
                FROM usuarios u
                LEFT JOIN users_enterprise ue ON u.id = ue.user_id
                WHERE u.username = ? AND u.activo = 1
            """
            
            user_result = self.db.execute_query(user_query, (username,))
            
            if not user_result:
                self._update_login_attempt(attempt_id, False, "Usuario no encontrado")
                self._audit_action(None, None, AuditAction.LOGIN_FAILED, 
                                 "Usuario no encontrado", ip_address)
                return {"success": False, "error": "Credenciales inválidas"}
            
            user = dict(user_result[0])
            user_id = user['id']
            
            # Verificar si la cuenta está bloqueada
            if self._is_user_locked(user_id):
                lockout_remaining = self._get_user_lockout_remaining(user_id)
                self._update_login_attempt(attempt_id, False, "Cuenta bloqueada")
                self._audit_action(user_id, None, AuditAction.LOGIN_FAILED, 
                                 "Cuenta bloqueada", ip_address)
                return {
                    "success": False,
                    "error": "Cuenta temporalmente bloqueada",
                    "lockout_remaining": lockout_remaining
                }
            
            # Verificar contraseña
            if not self._verify_password(password, user['password_hash']):
                self._increment_failed_attempts(user_id)
                self._update_login_attempt(attempt_id, False, "Contraseña incorrecta")
                self._audit_action(user_id, None, AuditAction.LOGIN_FAILED, 
                                 "Contraseña incorrecta", ip_address)
                return {"success": False, "error": "Credenciales inválidas"}
            
            # Verificar 2FA si está habilitado
            if user.get('two_factor_enabled') and TOTP_AVAILABLE:
                if not totp_code:
                    return {
                        "success": False,
                        "requires_2fa": True,
                        "error": "Código 2FA requerido"
                    }
                
                if not self._verify_totp_code(user['two_factor_secret'], totp_code):
                    self._increment_failed_attempts(user_id)
                    self._update_login_attempt(attempt_id, False, "Código 2FA inválido")
                    self._audit_action(user_id, None, AuditAction.LOGIN_FAILED, 
                                     "Código 2FA inválido", ip_address)
                    return {"success": False, "error": "Código 2FA inválido"}
            
            # Login exitoso
            self._reset_failed_attempts(user_id)
            self._update_login_attempt(attempt_id, True, None)
            
            # Crear sesión empresarial
            session_data = self._create_enterprise_session(user_id, device_info)
            
            # Auditoría de login exitoso
            self._audit_action(user_id, session_data['session_id'], AuditAction.LOGIN, 
                             "Login exitoso", ip_address, {"device_info": device_info})
            
            # Crear notificación de seguridad si es desde dispositivo nuevo
            if self._is_new_device(user_id, device_info):
                self._create_security_notification(
                    user_id, "NEW_DEVICE_LOGIN", "INFO",
                    "Nuevo dispositivo detectado",
                    f"Se detectó un login desde un nuevo dispositivo: {user_agent}",
                    {"ip_address": ip_address, "device_info": device_info}
                )
            
            return {
                "success": True,
                "user": {
                    "id": user['id'],
                    "username": user['username'],
                    "nombre": user['nombre'],
                    "email": user['email'],
                    "rol": user['rol'],
                    "employee_id": user.get('employee_id'),
                    "department": user.get('department'),
                    "security_clearance": user.get('security_clearance'),
                    "two_factor_enabled": bool(user.get('two_factor_enabled'))
                },
                "session": session_data,
                "permissions": self._get_user_permissions(user_id)
            }
            
        except Exception as e:
            self.logger.error(f"Error en autenticación empresarial: {e}")
            return {"success": False, "error": "Error interno del sistema"}
    
    def _create_enterprise_session(self, user_id: int, device_info: Dict = None) -> Dict:
        """Crear sesión empresarial"""
        try:
            session_id = str(uuid.uuid4())
            device_info = device_info or {}
            
            # Insertar sesión
            self.db.execute_query("""
                INSERT INTO user_sessions_enterprise 
                (user_id, session_id, device_info, ip_address, user_agent, location_info)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                session_id,
                json.dumps(device_info),
                device_info.get('ip_address', ''),
                device_info.get('user_agent', ''),
                device_info.get('location', '')
            ))
            
            return {
                "session_id": session_id,
                "expires_at": (datetime.now() + timedelta(hours=self.session_timeout_hours)).isoformat(),
                "timeout_hours": self.session_timeout_hours
            }
            
        except Exception as e:
            self.logger.error(f"Error creando sesión empresarial: {e}")
            return {}
    
    def setup_two_factor_auth(self, user_id: int) -> Dict:
        """Configurar autenticación de dos factores"""
        try:
            if not TOTP_AVAILABLE:
                return {"error": "2FA no disponible - PyOTP no instalado"}
            
            # Generar secreto
            secret = pyotp.random_base32()
            
            # Obtener información del usuario
            user_query = "SELECT username, email FROM usuarios WHERE id = ?"
            user_result = self.db.execute_query(user_query, (user_id,))
            
            if not user_result:
                return {"error": "Usuario no encontrado"}
            
            user = dict(user_result[0])
            
            # Crear TOTP
            totp = pyotp.TOTP(secret)
            
            # Generar QR code
            provisioning_uri = totp.provisioning_uri(
                user['email'],
                issuer_name="AlmacénPro v2.0"
            )
            
            # Crear QR image
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convertir a base64
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            # Generar códigos de respaldo
            backup_codes = [secrets.token_hex(4).upper() for _ in range(8)]
            
            # Guardar temporalmente (se activa cuando se verifica)
            temp_secret = f"TEMP_{secret}"
            
            self.db.execute_query("""
                INSERT OR REPLACE INTO users_enterprise 
                (user_id, two_factor_secret, backup_codes)
                VALUES (?, ?, ?)
            """, (user_id, temp_secret, json.dumps(backup_codes)))
            
            return {
                "success": True,
                "secret": secret,
                "qr_code": qr_code_base64,
                "backup_codes": backup_codes,
                "manual_entry_key": secret
            }
            
        except Exception as e:
            self.logger.error(f"Error configurando 2FA: {e}")
            return {"error": str(e)}
    
    def verify_and_enable_2fa(self, user_id: int, totp_code: str) -> Dict:
        """Verificar y activar 2FA"""
        try:
            if not TOTP_AVAILABLE:
                return {"error": "2FA no disponible"}
            
            # Obtener secreto temporal
            query = """
                SELECT two_factor_secret, backup_codes 
                FROM users_enterprise 
                WHERE user_id = ?
            """
            result = self.db.execute_query(query, (user_id,))
            
            if not result:
                return {"error": "Configuración 2FA no encontrada"}
            
            temp_secret = result[0][0]
            backup_codes = result[0][1]
            
            if not temp_secret.startswith("TEMP_"):
                return {"error": "2FA ya está activado"}
            
            # Extraer secreto real
            secret = temp_secret[5:]  # Remover "TEMP_"
            
            # Verificar código TOTP
            if not self._verify_totp_code(secret, totp_code):
                return {"error": "Código TOTP inválido"}
            
            # Activar 2FA
            self.db.execute_query("""
                UPDATE users_enterprise 
                SET two_factor_enabled = TRUE, two_factor_secret = ?
                WHERE user_id = ?
            """, (secret, user_id))
            
            # Auditoría
            self._audit_action(user_id, None, AuditAction.TWO_FA_ENABLE, 
                             "2FA activado exitosamente")
            
            # Notificación de seguridad
            self._create_security_notification(
                user_id, "TWO_FA_ENABLED", "INFO",
                "Autenticación de dos factores activada",
                "La autenticación de dos factores ha sido activada en su cuenta."
            )
            
            return {
                "success": True,
                "message": "2FA activado exitosamente",
                "backup_codes": json.loads(backup_codes) if backup_codes else []
            }
            
        except Exception as e:
            self.logger.error(f"Error activando 2FA: {e}")
            return {"error": str(e)}
    
    def disable_2fa(self, user_id: int, current_password: str, admin_override: bool = False) -> Dict:
        """Desactivar 2FA"""
        try:
            if not admin_override:
                # Verificar contraseña actual
                user_query = "SELECT password_hash FROM usuarios WHERE id = ?"
                user_result = self.db.execute_query(user_query, (user_id,))
                
                if not user_result or not self._verify_password(current_password, user_result[0][0]):
                    return {"error": "Contraseña incorrecta"}
            
            # Desactivar 2FA
            self.db.execute_query("""
                UPDATE users_enterprise 
                SET two_factor_enabled = FALSE, two_factor_secret = NULL, backup_codes = NULL
                WHERE user_id = ?
            """, (user_id,))
            
            # Auditoría
            action_detail = "2FA desactivado por administrador" if admin_override else "2FA desactivado por usuario"
            self._audit_action(user_id, None, AuditAction.TWO_FA_DISABLE, action_detail)
            
            # Notificación de seguridad
            self._create_security_notification(
                user_id, "TWO_FA_DISABLED", "WARNING",
                "Autenticación de dos factores desactivada",
                action_detail
            )
            
            return {"success": True, "message": "2FA desactivado exitosamente"}
            
        except Exception as e:
            self.logger.error(f"Error desactivando 2FA: {e}")
            return {"error": str(e)}
    
    def create_access_token(self, user_id: int, token_name: str, scopes: List[str], 
                           expires_days: int = 365, ip_whitelist: List[str] = None) -> Dict:
        """Crear token de acceso para APIs"""
        try:
            # Generar token
            token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            expires_at = datetime.now() + timedelta(days=expires_days)
            
            # Insertar token
            token_id = self.db.execute_query("""
                INSERT INTO access_tokens 
                (user_id, token_hash, token_name, scopes, expires_at, ip_whitelist)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                token_hash,
                token_name,
                json.dumps(scopes),
                expires_at,
                json.dumps(ip_whitelist) if ip_whitelist else None
            ))
            
            if token_id:
                # Auditoría
                self._audit_action(user_id, None, "TOKEN_CREATE", 
                                 f"Token de acceso creado: {token_name}",
                                 metadata={"scopes": scopes, "expires_days": expires_days})
                
                return {
                    "success": True,
                    "token_id": token_id,
                    "token": token,  # Solo se muestra una vez
                    "expires_at": expires_at.isoformat(),
                    "scopes": scopes
                }
            
            return {"error": "Error creando token"}
            
        except Exception as e:
            self.logger.error(f"Error creando token de acceso: {e}")
            return {"error": str(e)}
    
    def validate_access_token(self, token: str, required_scope: str = None, 
                            client_ip: str = None) -> Dict:
        """Validar token de acceso"""
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            # Buscar token
            query = """
                SELECT at.*, u.username, u.activo as user_active
                FROM access_tokens at
                JOIN usuarios u ON at.user_id = u.id
                WHERE at.token_hash = ? AND at.active = TRUE
            """
            
            result = self.db.execute_query(query, (token_hash,))
            
            if not result:
                return {"valid": False, "error": "Token inválido"}
            
            token_data = dict(result[0])
            
            # Verificar expiración
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            if datetime.now() > expires_at:
                return {"valid": False, "error": "Token expirado"}
            
            # Verificar usuario activo
            if not token_data['user_active']:
                return {"valid": False, "error": "Usuario inactivo"}
            
            # Verificar IP whitelist
            ip_whitelist = json.loads(token_data['ip_whitelist']) if token_data['ip_whitelist'] else None
            if ip_whitelist and client_ip and client_ip not in ip_whitelist:
                return {"valid": False, "error": "IP no autorizada"}
            
            # Verificar scope
            scopes = json.loads(token_data['scopes']) if token_data['scopes'] else []
            if required_scope and required_scope not in scopes:
                return {"valid": False, "error": "Scope insuficiente"}
            
            # Actualizar uso
            self.db.execute_query("""
                UPDATE access_tokens 
                SET last_used_at = CURRENT_TIMESTAMP, usage_count = usage_count + 1
                WHERE id = ?
            """, (token_data['id'],))
            
            return {
                "valid": True,
                "user_id": token_data['user_id'],
                "username": token_data['username'],
                "scopes": scopes,
                "token_name": token_data['token_name']
            }
            
        except Exception as e:
            self.logger.error(f"Error validando token: {e}")
            return {"valid": False, "error": "Error interno"}
    
    def delegate_permissions(self, delegator_id: int, delegate_id: int, 
                           permissions: List[str], end_date: datetime, 
                           resource_filter: Dict = None, notes: str = "") -> Dict:
        """Delegar permisos temporalmente"""
        try:
            # Verificar que el delegador tenga los permisos
            delegator_permissions = self._get_user_permissions(delegator_id)
            
            for permission in permissions:
                if permission not in delegator_permissions:
                    return {"error": f"No tiene permiso para delegar: {permission}"}
            
            # Crear delegación
            delegation_id = self.db.execute_query("""
                INSERT INTO permission_delegations 
                (delegator_id, delegate_id, permission_type, resource_filter, 
                 end_date, created_by, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                delegator_id,
                delegate_id,
                json.dumps(permissions),
                json.dumps(resource_filter) if resource_filter else None,
                end_date,
                delegator_id,
                notes
            ))
            
            if delegation_id:
                # Auditoría
                self._audit_action(delegator_id, None, "PERMISSION_DELEGATE",
                                 f"Permisos delegados a usuario {delegate_id}",
                                 metadata={
                                     "permissions": permissions,
                                     "delegate_id": delegate_id,
                                     "end_date": end_date.isoformat()
                                 })
                
                return {
                    "success": True,
                    "delegation_id": delegation_id,
                    "expires_at": end_date.isoformat()
                }
            
            return {"error": "Error creando delegación"}
            
        except Exception as e:
            self.logger.error(f"Error delegando permisos: {e}")
            return {"error": str(e)}
    
    def get_user_sessions(self, user_id: int, include_terminated: bool = False) -> List[Dict]:
        """Obtener sesiones del usuario"""
        try:
            status_filter = "" if include_terminated else "AND status = 'ACTIVE'"
            
            query = f"""
                SELECT session_id, device_info, ip_address, login_timestamp,
                       last_activity, status, session_duration
                FROM user_sessions_enterprise
                WHERE user_id = ? {status_filter}
                ORDER BY login_timestamp DESC
                LIMIT 50
            """
            
            result = self.db.execute_query(query, (user_id,))
            
            sessions = []
            for row in result:
                session_dict = dict(row)
                if session_dict['device_info']:
                    session_dict['device_info'] = json.loads(session_dict['device_info'])
                sessions.append(session_dict)
            
            return sessions
            
        except Exception as e:
            self.logger.error(f"Error obteniendo sesiones: {e}")
            return []
    
    def terminate_session(self, session_id: str, terminated_by: int, reason: str = "") -> Dict:
        """Terminar sesión específica"""
        try:
            # Actualizar sesión
            self.db.execute_query("""
                UPDATE user_sessions_enterprise 
                SET status = 'TERMINATED', logout_timestamp = CURRENT_TIMESTAMP,
                    terminated_by = ?, termination_reason = ?
                WHERE session_id = ? AND status = 'ACTIVE'
            """, (terminated_by, reason, session_id))
            
            # Auditoría
            self._audit_action(terminated_by, session_id, "SESSION_TERMINATE",
                             f"Sesión terminada: {reason}")
            
            return {"success": True, "message": "Sesión terminada"}
            
        except Exception as e:
            self.logger.error(f"Error terminando sesión: {e}")
            return {"error": str(e)}
    
    def get_audit_log(self, user_id: int = None, action_type: str = None, 
                     start_date: datetime = None, end_date: datetime = None, 
                     limit: int = 100) -> List[Dict]:
        """Obtener log de auditoría"""
        try:
            conditions = []
            params = []
            
            if user_id:
                conditions.append("user_id = ?")
                params.append(user_id)
            
            if action_type:
                conditions.append("action_type = ?")
                params.append(action_type)
            
            if start_date:
                conditions.append("timestamp >= ?")
                params.append(start_date)
            
            if end_date:
                conditions.append("timestamp <= ?")
                params.append(end_date)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            query = f"""
                SELECT ale.*, u.username
                FROM audit_log_enterprise ale
                LEFT JOIN usuarios u ON ale.user_id = u.id
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT ?
            """
            
            params.append(limit)
            result = self.db.execute_query(query, params)
            
            audit_entries = []
            for row in result:
                entry = dict(row)
                
                # Parsear JSON fields
                for field in ['old_values', 'new_values', 'additional_metadata']:
                    if entry[field]:
                        try:
                            entry[field] = json.loads(entry[field])
                        except:
                            pass
                
                audit_entries.append(entry)
            
            return audit_entries
            
        except Exception as e:
            self.logger.error(f"Error obteniendo audit log: {e}")
            return []
    
    def get_security_notifications(self, user_id: int, unread_only: bool = False) -> List[Dict]:
        """Obtener notificaciones de seguridad"""
        try:
            read_filter = "AND read_at IS NULL" if unread_only else ""
            
            query = f"""
                SELECT * FROM security_notifications
                WHERE user_id = ? {read_filter}
                ORDER BY created_at DESC
                LIMIT 50
            """
            
            result = self.db.execute_query(query, (user_id,))
            
            notifications = []
            for row in result:
                notification = dict(row)
                if notification['metadata']:
                    try:
                        notification['metadata'] = json.loads(notification['metadata'])
                    except:
                        pass
                notifications.append(notification)
            
            return notifications
            
        except Exception as e:
            self.logger.error(f"Error obteniendo notificaciones: {e}")
            return []
    
    # Métodos privados de utilidad
    
    def _log_login_attempt(self, username: str, ip_address: str, user_agent: str, 
                          success: bool) -> int:
        """Registrar intento de login"""
        try:
            return self.db.execute_query("""
                INSERT INTO login_attempts 
                (username, ip_address, user_agent, success)
                VALUES (?, ?, ?, ?)
            """, (username, ip_address, user_agent, success))
        except:
            return 0
    
    def _update_login_attempt(self, attempt_id: int, success: bool, failure_reason: str = None):
        """Actualizar intento de login"""
        try:
            self.db.execute_query("""
                UPDATE login_attempts 
                SET success = ?, failure_reason = ?
                WHERE id = ?
            """, (success, failure_reason, attempt_id))
        except:
            pass
    
    def _is_ip_blocked(self, ip_address: str) -> bool:
        """Verificar si IP está bloqueada"""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=self.lockout_duration_minutes)
            
            query = """
                SELECT COUNT(*) FROM login_attempts
                WHERE ip_address = ? AND success = FALSE 
                AND attempt_timestamp > ?
            """
            
            result = self.db.execute_query(query, (ip_address, cutoff_time))
            return result[0][0] >= self.max_login_attempts if result else False
            
        except:
            return False
    
    def _get_ip_lockout_remaining(self, ip_address: str) -> int:
        """Obtener minutos restantes de bloqueo IP"""
        try:
            query = """
                SELECT MAX(attempt_timestamp) FROM login_attempts
                WHERE ip_address = ? AND success = FALSE
            """
            
            result = self.db.execute_query(query, (ip_address,))
            if result and result[0][0]:
                last_attempt = datetime.fromisoformat(result[0][0])
                unblock_time = last_attempt + timedelta(minutes=self.lockout_duration_minutes)
                remaining = (unblock_time - datetime.now()).total_seconds() / 60
                return max(0, int(remaining))
            
            return 0
        except:
            return 0
    
    def _is_user_locked(self, user_id: int) -> bool:
        """Verificar si usuario está bloqueado"""
        # Implementación similar a _is_ip_blocked pero por user_id
        return False
    
    def _get_user_lockout_remaining(self, user_id: int) -> int:
        """Obtener minutos restantes de bloqueo de usuario"""
        return 0
    
    def _verify_password(self, password: str, hash: str) -> bool:
        """Verificar contraseña"""
        # Implementación usando bcrypt u otro hash seguro
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), hash.encode('utf-8'))
    
    def _verify_totp_code(self, secret: str, code: str) -> bool:
        """Verificar código TOTP"""
        try:
            if not TOTP_AVAILABLE:
                return False
            
            totp = pyotp.TOTP(secret)
            return totp.verify(code, valid_window=1)  # 30s window
            
        except:
            return False
    
    def _increment_failed_attempts(self, user_id: int):
        """Incrementar intentos fallidos"""
        pass
    
    def _reset_failed_attempts(self, user_id: int):
        """Resetear intentos fallidos"""
        pass
    
    def _get_user_permissions(self, user_id: int) -> List[str]:
        """Obtener permisos del usuario"""
        return []  # Placeholder
    
    def _is_new_device(self, user_id: int, device_info: Dict) -> bool:
        """Verificar si es un dispositivo nuevo"""
        return False  # Placeholder
    
    def _audit_action(self, user_id: int, session_id: str, action: AuditAction, 
                     details: str, ip_address: str = "", metadata: Dict = None):
        """Registrar acción en auditoría"""
        try:
            self.db.execute_query("""
                INSERT INTO audit_log_enterprise 
                (user_id, session_id, action_type, ip_address, additional_metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_id,
                session_id,
                action.value if isinstance(action, AuditAction) else action,
                ip_address,
                json.dumps(metadata) if metadata else None
            ))
        except Exception as e:
            self.logger.error(f"Error en auditoría: {e}")
    
    def _create_security_notification(self, user_id: int, notification_type: str, 
                                    severity: str, title: str, message: str, 
                                    metadata: Dict = None):
        """Crear notificación de seguridad"""
        try:
            self.db.execute_query("""
                INSERT INTO security_notifications 
                (user_id, notification_type, severity, title, message, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id, notification_type, severity, title, message,
                json.dumps(metadata) if metadata else None
            ))
        except Exception as e:
            self.logger.error(f"Error creando notificación: {e}")