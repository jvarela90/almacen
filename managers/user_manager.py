"""
Gestor de Usuarios y Autenticación para AlmacénPro
Maneja login, permisos, roles y seguridad de usuarios
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class UserManager:
    """Gestor de usuarios y autenticación"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.current_user = None
        self.current_permissions = {}
        self.session_start_time = None
        self.failed_login_attempts = {}
        
        logger.info("UserManager inicializado")
    
    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """Autenticar usuario"""
        try:
            # Verificar si el usuario está bloqueado
            if self.is_user_blocked(username):
                return False, "Usuario temporalmente bloqueado por múltiples intentos fallidos"
            
            # Hash de la contraseña
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Buscar usuario
            user_data = self.db.execute_single("""
                SELECT u.*, r.nombre as rol_nombre, r.permisos 
                FROM usuarios u 
                LEFT JOIN roles r ON u.rol_id = r.id 
                WHERE u.username = ? AND u.password_hash = ? AND u.activo = 1
            """, (username, password_hash))
            
            if user_data:
                # Login exitoso
                self.current_user = user_data
                self.current_permissions = json.loads(user_data.get('permisos') or '{}')
                self.session_start_time = datetime.now()
                
                # Actualizar último acceso y resetear intentos
                self.db.execute_update("""
                    UPDATE usuarios 
                    SET ultimo_acceso = CURRENT_TIMESTAMP, intentos_login = 0, bloqueado_hasta = NULL
                    WHERE id = ?
                """, (user_data['id'],))
                
                # Resetear contador de intentos fallidos
                if username in self.failed_login_attempts:
                    del self.failed_login_attempts[username]
                
                # Registrar en auditoría
                self.log_user_action('LOGIN', f"Usuario {username} inició sesión")
                
                logger.info(f"Login exitoso: {username}")
                return True, f"Bienvenido {user_data['nombre_completo']}"
            else:
                # Login fallido
                self.register_failed_login(username)
                logger.warning(f"Login fallido: {username}")
                return False, "Usuario o contraseña incorrectos"
                
        except Exception as e:
            logger.error(f"Error en login: {e}")
            return False, "Error de autenticación"
    
    def logout(self):
        """Cerrar sesión"""
        if self.current_user:
            # Registrar cierre de sesión
            self.log_user_action('LOGOUT', f"Usuario {self.current_user['username']} cerró sesión")
            logger.info(f"Logout: {self.current_user['username']}")
        
        # Limpiar datos de sesión
        self.current_user = None
        self.current_permissions = {}
        self.session_start_time = None
    
    def is_user_blocked(self, username: str) -> bool:
        """Verificar si el usuario está bloqueado"""
        try:
            # Verificar bloqueo en base de datos
            user_data = self.db.execute_single("""
                SELECT bloqueado_hasta, intentos_login 
                FROM usuarios 
                WHERE username = ?
            """, (username,))
            
            if user_data and user_data['bloqueado_hasta']:
                blocked_until = datetime.fromisoformat(user_data['bloqueado_hasta'])
                if datetime.now() < blocked_until:
                    return True
            
            # Verificar bloqueo temporal en memoria
            if username in self.failed_login_attempts:
                attempts = self.failed_login_attempts[username]
                if attempts['count'] >= 5:  # Máximo 5 intentos
                    last_attempt = datetime.fromisoformat(attempts['last_attempt'])
                    if datetime.now() - last_attempt < timedelta(minutes=15):  # Bloqueo de 15 minutos
                        return True
                    else:
                        # El bloqueo temporal ha expirado
                        del self.failed_login_attempts[username]
            
            return False
            
        except Exception as e:
            logger.error(f"Error verificando bloqueo de usuario: {e}")
            return False
    
    def register_failed_login(self, username: str):
        """Registrar intento de login fallido"""
        try:
            # Actualizar contador en base de datos
            self.db.execute_update("""
                UPDATE usuarios 
                SET intentos_login = intentos_login + 1
                WHERE username = ?
            """, (username,))
            
            # Actualizar contador en memoria
            if username not in self.failed_login_attempts:
                self.failed_login_attempts[username] = {'count': 0, 'last_attempt': None}
            
            self.failed_login_attempts[username]['count'] += 1
            self.failed_login_attempts[username]['last_attempt'] = datetime.now().isoformat()
            
            # Si supera 5 intentos, bloquear por 1 hora en BD
            if self.failed_login_attempts[username]['count'] >= 5:
                blocked_until = datetime.now() + timedelta(hours=1)
                self.db.execute_update("""
                    UPDATE usuarios 
                    SET bloqueado_hasta = ?
                    WHERE username = ?
                """, (blocked_until.isoformat(), username))
                
                logger.warning(f"Usuario {username} bloqueado por múltiples intentos fallidos")
            
        except Exception as e:
            logger.error(f"Error registrando intento fallido: {e}")
    
    def has_permission(self, permission: str) -> bool:
        """Verificar si el usuario tiene un permiso específico"""
        if not self.current_user:
            return False
        
        # Administrador tiene todos los permisos
        if self.current_permissions.get('all'):
            return True
        
        # Verificar permiso específico
        return self.current_permissions.get(permission, False)
    
    def get_user_permissions(self) -> Dict:
        """Obtener todos los permisos del usuario actual"""
        return self.current_permissions.copy()
    
    def is_session_valid(self) -> bool:
        """Verificar si la sesión actual es válida"""
        if not self.current_user or not self.session_start_time:
            return False
        
        # Verificar timeout de sesión (por defecto 8 horas)
        session_timeout = timedelta(hours=8)
        if datetime.now() - self.session_start_time > session_timeout:
            logger.info("Sesión expirada por timeout")
            return False
        
        return True
    
    def extend_session(self):
        """Extender la sesión actual"""
        if self.current_user:
            self.session_start_time = datetime.now()
    
    def create_user(self, username: str, password: str, nombre_completo: str, 
                   email: str = None, rol_id: int = None) -> Tuple[bool, str, int]:
        """Crear nuevo usuario"""
        try:
            # Verificar que el usuario actual tenga permisos
            if not self.has_permission('all') and not self.has_permission('usuarios'):
                return False, "No tiene permisos para crear usuarios", 0
            
            # Verificar que el username no exista
            existing_user = self.db.execute_single("""
                SELECT id FROM usuarios WHERE username = ?
            """, (username,))
            
            if existing_user:
                return False, "El nombre de usuario ya existe", 0
            
            # Hash de la contraseña
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Crear usuario
            user_id = self.db.execute_insert("""
                INSERT INTO usuarios (username, password_hash, nombre_completo, email, rol_id)
                VALUES (?, ?, ?, ?, ?)
            """, (username, password_hash, nombre_completo, email, rol_id))
            
            # Registrar en auditoría
            self.log_user_action('CREATE_USER', f"Usuario {username} creado")
            
            logger.info(f"Usuario creado: {username}")
            return True, f"Usuario {username} creado exitosamente", user_id
            
        except Exception as e:
            logger.error(f"Error creando usuario: {e}")
            return False, f"Error creando usuario: {str(e)}", 0
    
    def update_user(self, user_id: int, **kwargs) -> Tuple[bool, str]:
        """Actualizar datos de usuario"""
        try:
            if not self.has_permission('all') and not self.has_permission('usuarios'):
                return False, "No tiene permisos para modificar usuarios"
            
            # Construir query dinámicamente
            update_fields = []
            update_values = []
            
            allowed_fields = ['nombre_completo', 'email', 'rol_id', 'activo']
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    update_fields.append(f"{field} = ?")
                    update_values.append(value)
            
            if not update_fields:
                return False, "No hay campos válidos para actualizar"
            
            # Agregar timestamp de actualización
            update_fields.append("actualizado_en = CURRENT_TIMESTAMP")
            update_values.append(user_id)
            
            query = f"UPDATE usuarios SET {', '.join(update_fields)} WHERE id = ?"
            
            rows_affected = self.db.execute_update(query, tuple(update_values))
            
            if rows_affected > 0:
                self.log_user_action('UPDATE_USER', f"Usuario ID {user_id} actualizado")
                logger.info(f"Usuario ID {user_id} actualizado")
                return True, "Usuario actualizado exitosamente"
            else:
                return False, "Usuario no encontrado"
                
        except Exception as e:
            logger.error(f"Error actualizando usuario: {e}")
            return False, f"Error actualizando usuario: {str(e)}"
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> Tuple[bool, str]:
        """Cambiar contraseña de usuario"""
        try:
            # Verificar que sea el propio usuario o un admin
            if (self.current_user['id'] != user_id and 
                not self.has_permission('all') and 
                not self.has_permission('usuarios')):
                return False, "No tiene permisos para cambiar esta contraseña"
            
            # Si no es admin, verificar contraseña actual
            if self.current_user['id'] == user_id:
                current_hash = hashlib.sha256(current_password.encode()).hexdigest()
                user_data = self.db.execute_single("""
                    SELECT id FROM usuarios WHERE id = ? AND password_hash = ?
                """, (user_id, current_hash))
                
                if not user_data:
                    return False, "Contraseña actual incorrecta"
            
            # Validar nueva contraseña
            if len(new_password) < 6:
                return False, "La nueva contraseña debe tener al menos 6 caracteres"
            
            # Actualizar contraseña
            new_hash = hashlib.sha256(new_password.encode()).hexdigest()
            rows_affected = self.db.execute_update("""
                UPDATE usuarios 
                SET password_hash = ?, actualizado_en = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_hash, user_id))
            
            if rows_affected > 0:
                self.log_user_action('CHANGE_PASSWORD', f"Contraseña cambiada para usuario ID {user_id}")
                logger.info(f"Contraseña cambiada para usuario ID {user_id}")
                return True, "Contraseña cambiada exitosamente"
            else:
                return False, "Usuario no encontrado"
                
        except Exception as e:
            logger.error(f"Error cambiando contraseña: {e}")
            return False, f"Error cambiando contraseña: {str(e)}"
    
    def get_all_users(self, include_inactive: bool = False) -> List[Dict]:
        """Obtener lista de todos los usuarios"""
        try:
            if not self.has_permission('all') and not self.has_permission('usuarios'):
                return []
            
            query = """
                SELECT u.*, r.nombre as rol_nombre
                FROM usuarios u
                LEFT JOIN roles r ON u.rol_id = r.id
            """
            
            if not include_inactive:
                query += " WHERE u.activo = 1"
            
            query += " ORDER BY u.nombre_completo"
            
            return self.db.execute_query(query)
            
        except Exception as e:
            logger.error(f"Error obteniendo usuarios: {e}")
            return []
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Obtener usuario por ID"""
        try:
            return self.db.execute_single("""
                SELECT u.*, r.nombre as rol_nombre, r.permisos
                FROM usuarios u
                LEFT JOIN roles r ON u.rol_id = r.id
                WHERE u.id = ?
            """, (user_id,))
            
        except Exception as e:
            logger.error(f"Error obteniendo usuario por ID: {e}")
            return None
    
    def get_all_roles(self) -> List[Dict]:
        """Obtener lista de todos los roles"""
        try:
            return self.db.execute_query("""
                SELECT * FROM roles WHERE activo = 1 ORDER BY nombre
            """)
            
        except Exception as e:
            logger.error(f"Error obteniendo roles: {e}")
            return []
    
    def create_role(self, nombre: str, descripcion: str, permisos: Dict) -> Tuple[bool, str, int]:
        """Crear nuevo rol"""
        try:
            if not self.has_permission('all'):
                return False, "No tiene permisos para crear roles", 0
            
            permisos_json = json.dumps(permisos)
            
            role_id = self.db.execute_insert("""
                INSERT INTO roles (nombre, descripcion, permisos)
                VALUES (?, ?, ?)
            """, (nombre, descripcion, permisos_json))
            
            self.log_user_action('CREATE_ROLE', f"Rol {nombre} creado")
            logger.info(f"Rol creado: {nombre}")
            
            return True, f"Rol {nombre} creado exitosamente", role_id
            
        except Exception as e:
            logger.error(f"Error creando rol: {e}")
            return False, f"Error creando rol: {str(e)}", 0
    
    def log_user_action(self, action: str, description: str, table: str = 'usuarios', record_id: int = None):
        """Registrar acción del usuario en auditoría"""
        try:
            if not self.current_user:
                return
            
            self.db.execute_insert("""
                INSERT INTO auditoria (tabla, operacion, registro_id, datos_nuevos, usuario_id, fecha_operacion)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (table, action, record_id, description, self.current_user['id']))
            
        except Exception as e:
            logger.error(f"Error registrando acción en auditoría: {e}")
    
    def get_user_activity_log(self, user_id: int = None, days: int = 30) -> List[Dict]:
        """Obtener log de actividad de usuario"""
        try:
            if not self.has_permission('all') and not self.has_permission('auditoria'):
                return []
            
            query = """
                SELECT a.*, u.username, u.nombre_completo
                FROM auditoria a
                LEFT JOIN usuarios u ON a.usuario_id = u.id
                WHERE a.fecha_operacion >= date('now', '-{} days')
            """.format(days)
            
            params = []
            if user_id:
                query += " AND a.usuario_id = ?"
                params.append(user_id)
            
            query += " ORDER BY a.fecha_operacion DESC LIMIT 1000"
            
            return self.db.execute_query(query, tuple(params) if params else None)
            
        except Exception as e:
            logger.error(f"Error obteniendo log de actividad: {e}")
            return []
    
    def cleanup_expired_sessions(self):
        """Limpiar sesiones expiradas y bloqueos antiguos"""
        try:
            # Limpiar bloqueos expirados
            self.db.execute_update("""
                UPDATE usuarios 
                SET bloqueado_hasta = NULL, intentos_login = 0
                WHERE bloqueado_hasta < datetime('now')
            """)
            
            # Limpiar intentos fallidos en memoria (más de 1 hora)
            current_time = datetime.now()
            expired_usernames = []
            
            for username, attempts in self.failed_login_attempts.items():
                last_attempt = datetime.fromisoformat(attempts['last_attempt'])
                if current_time - last_attempt > timedelta(hours=1):
                    expired_usernames.append(username)
            
            for username in expired_usernames:
                del self.failed_login_attempts[username]
            
            logger.info("Limpieza de sesiones expiradas completada")
            
        except Exception as e:
            logger.error(f"Error en limpieza de sesiones: {e}")
    
    def get_session_info(self) -> Dict:
        """Obtener información de la sesión actual"""
        if not self.current_user or not self.session_start_time:
            return {}
        
        session_duration = datetime.now() - self.session_start_time
        
        return {
            'user_id': self.current_user['id'],
            'username': self.current_user['username'],
            'nombre_completo': self.current_user['nombre_completo'],
            'rol': self.current_user.get('rol_nombre', 'Sin rol'),
            'session_start': self.session_start_time.isoformat(),
            'session_duration_minutes': int(session_duration.total_seconds() / 60),
            'permissions': self.current_permissions,
            'last_activity': datetime.now().isoformat()
        }