"""
Gestor de Usuarios para AlmacénPro
Sistema completo de autenticación, autorización y gestión de usuarios
"""

import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import bcrypt

logger = logging.getLogger(__name__)

class UserManager:
    """Gestor principal para usuarios, roles y autenticación"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
        self.failed_attempts = {}  # Cache de intentos fallidos por usuario
        
        # Roles por defecto del sistema
        self.DEFAULT_ROLES = {
            'ADMINISTRADOR': {
                'descripcion': 'Acceso completo al sistema',
                'permisos': ['*']  # Todos los permisos
            },
            'GERENTE': {
                'descripcion': 'Gestión completa excepto configuración',
                'permisos': ['ventas', 'compras', 'productos', 'reportes', 'usuarios_consulta']
            },
            'VENDEDOR': {
                'descripcion': 'Operación de punto de venta',
                'permisos': ['ventas', 'productos_consulta', 'clientes_consulta']
            },
            'DEPOSITO': {
                'descripcion': 'Gestión de stock y recepción',
                'permisos': ['productos', 'compras_recepcion', 'stock']
            }
        }
        
        # Asegurar que existan los roles por defecto
        self._ensure_default_roles()
        
        # Asegurar que exista el usuario administrador
        self._ensure_admin_user()
    
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """Autenticar usuario con username y password"""
        try:
            # Verificar si el usuario no está bloqueado
            if self._is_user_locked(username):
                return False, "Usuario temporalmente bloqueado por múltiples intentos fallidos", None
            
            # Obtener usuario de la base de datos
            user = self.db.execute_single("""
                SELECT u.*, r.nombre as rol_nombre, r.permisos as rol_permisos
                FROM usuarios u
                LEFT JOIN roles r ON u.rol_id = r.id
                WHERE u.username = ? AND u.activo = 1
            """, (username,))
            
            if not user:
                self._record_failed_attempt(username)
                return False, "Usuario no encontrado o inactivo", None
            
            # Verificar contraseña
            if not self._verify_password(password, user['password_hash']):
                self._record_failed_attempt(username)
                return False, "Contraseña incorrecta", None
            
            # Limpiar intentos fallidos
            self._clear_failed_attempts(username)
            
            # Actualizar último acceso
            self.db.execute_update("""
                UPDATE usuarios SET ultimo_acceso = CURRENT_TIMESTAMP WHERE id = ?
            """, (user['id'],))
            
            # Preparar datos del usuario autenticado
            user_data = {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'nombre_completo': user['nombre_completo'],
                'rol_id': user['rol_id'],
                'rol_nombre': user['rol_nombre'],
                'permisos': self._parse_permissions(user['rol_permisos']),
                'ultimo_acceso': user['ultimo_acceso']
            }
            
            self.logger.info(f"Usuario autenticado exitosamente: {username}")
            return True, "Autenticación exitosa", user_data
            
        except Exception as e:
            self.logger.error(f"Error en autenticación: {e}")
            return False, f"Error de autenticación: {str(e)}", None
    
    def create_user(self, user_data: Dict, creator_user_id: int) -> Tuple[bool, str, int]:
        """Crear nuevo usuario"""
        try:
            # Validaciones básicas
            required_fields = ['username', 'password', 'nombre_completo']
            for field in required_fields:
                if not user_data.get(field):
                    return False, f"El campo {field} es obligatorio", 0
            
            # Validar unicidad del username
            existing_user = self.db.execute_single("""
                SELECT id FROM usuarios WHERE username = ?
            """, (user_data['username'],))
            
            if existing_user:
                return False, "Ya existe un usuario con ese nombre de usuario", 0
            
            # Validar email único (si se proporciona)
            if user_data.get('email'):
                existing_email = self.db.execute_single("""
                    SELECT id FROM usuarios WHERE email = ? AND id != ?
                """, (user_data['email'], 0))
                
                if existing_email:
                    return False, "Ya existe un usuario con ese email", 0
            
            # Validar rol
            if user_data.get('rol_id'):
                role = self.get_role_by_id(user_data['rol_id'])
                if not role:
                    return False, "Rol no válido", 0
            
            # Validar contraseña
            if not self._validate_password(user_data['password']):
                return False, "La contraseña no cumple con los requisitos mínimos", 0
            
            # Hash de la contraseña
            password_hash = self._hash_password(user_data['password'])
            
            # Crear usuario
            user_id = self.db.execute_insert("""
                INSERT INTO usuarios (
                    username, password_hash, email, nombre_completo, 
                    rol_id, activo, creado_por
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_data['username'],
                password_hash,
                user_data.get('email'),
                user_data['nombre_completo'],
                user_data.get('rol_id', self._get_default_role_id()),
                user_data.get('activo', True),
                creator_user_id
            ))
            
            if user_id:
                self.logger.info(f"Usuario creado: {user_data['username']} (ID: {user_id})")
                return True, f"Usuario creado exitosamente", user_id
            else:
                return False, "Error al crear el usuario", 0
                
        except Exception as e:
            self.logger.error(f"Error creando usuario: {e}")
            return False, f"Error creando usuario: {str(e)}", 0
    
    def update_user(self, user_id: int, user_data: Dict, updater_user_id: int) -> Tuple[bool, str]:
        """Actualizar usuario existente"""
        try:
            # Verificar que el usuario existe
            existing_user = self.get_user_by_id(user_id)
            if not existing_user:
                return False, "Usuario no encontrado"
            
            # Validar username único (si se está cambiando)
            if user_data.get('username') and user_data['username'] != existing_user['username']:
                existing_username = self.db.execute_single("""
                    SELECT id FROM usuarios WHERE username = ? AND id != ?
                """, (user_data['username'], user_id))
                
                if existing_username:
                    return False, "Ya existe un usuario con ese nombre de usuario"
            
            # Validar email único (si se está cambiando)
            if user_data.get('email') and user_data['email'] != existing_user.get('email'):
                existing_email = self.db.execute_single("""
                    SELECT id FROM usuarios WHERE email = ? AND id != ?
                """, (user_data['email'], user_id))
                
                if existing_email:
                    return False, "Ya existe un usuario con ese email"
            
            # Construir query de actualización dinámicamente
            update_fields = []
            update_values = []
            
            allowed_fields = ['username', 'email', 'nombre_completo', 'rol_id', 'activo']
            
            for field, value in user_data.items():
                if field in allowed_fields and value is not None:
                    update_fields.append(f"{field} = ?")
                    update_values.append(value)
            
            # Manejar cambio de contraseña por separado
            if user_data.get('password'):
                if not self._validate_password(user_data['password']):
                    return False, "La nueva contraseña no cumple con los requisitos mínimos"
                
                update_fields.append("password_hash = ?")
                update_values.append(self._hash_password(user_data['password']))
            
            if not update_fields:
                return False, "No hay campos válidos para actualizar"
            
            # Agregar campos de auditoría
            update_fields.extend(["actualizado_en = CURRENT_TIMESTAMP", "actualizado_por = ?"])
            update_values.extend([updater_user_id, user_id])
            
            query = f"UPDATE usuarios SET {', '.join(update_fields)} WHERE id = ?"
            
            success = self.db.execute_update(query, update_values)
            
            if success:
                self.logger.info(f"Usuario actualizado: ID {user_id}")
                return True, "Usuario actualizado exitosamente"
            else:
                return False, "Error al actualizar el usuario"
                
        except Exception as e:
            self.logger.error(f"Error actualizando usuario: {e}")
            return False, f"Error actualizando usuario: {str(e)}"
    
    def change_password(self, user_id: int, current_password: str, 
                       new_password: str) -> Tuple[bool, str]:
        """Cambiar contraseña de usuario"""
        try:
            # Obtener usuario actual
            user = self.get_user_by_id(user_id)
            if not user:
                return False, "Usuario no encontrado"
            
            # Verificar contraseña actual
            if not self._verify_password(current_password, user['password_hash']):
                return False, "Contraseña actual incorrecta"
            
            # Validar nueva contraseña
            if not self._validate_password(new_password):
                return False, "La nueva contraseña no cumple con los requisitos mínimos"
            
            # Actualizar contraseña
            password_hash = self._hash_password(new_password)
            success = self.db.execute_update("""
                UPDATE usuarios 
                SET password_hash = ?, actualizado_en = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (password_hash, user_id))
            
            if success:
                self.logger.info(f"Contraseña cambiada para usuario ID: {user_id}")
                return True, "Contraseña actualizada exitosamente"
            else:
                return False, "Error al actualizar la contraseña"
                
        except Exception as e:
            self.logger.error(f"Error cambiando contraseña: {e}")
            return False, f"Error cambiando contraseña: {str(e)}"
    
    def reset_password(self, user_id: int, new_password: str, 
                      admin_user_id: int) -> Tuple[bool, str]:
        """Resetear contraseña de usuario (solo administradores)"""
        try:
            # Verificar que el administrador tiene permisos
            admin_user = self.get_user_by_id(admin_user_id)
            if not admin_user or not self.user_has_permission(admin_user_id, 'usuarios_admin'):
                return False, "No tiene permisos para resetear contraseñas"
            
            # Verificar que el usuario objetivo existe
            target_user = self.get_user_by_id(user_id)
            if not target_user:
                return False, "Usuario no encontrado"
            
            # Validar nueva contraseña
            if not self._validate_password(new_password):
                return False, "La nueva contraseña no cumple con los requisitos mínimos"
            
            # Actualizar contraseña
            password_hash = self._hash_password(new_password)
            success = self.db.execute_update("""
                UPDATE usuarios 
                SET password_hash = ?, actualizado_en = CURRENT_TIMESTAMP,
                    actualizado_por = ?
                WHERE id = ?
            """, (password_hash, admin_user_id, user_id))
            
            if success:
                self.logger.info(f"Contraseña reseteada para usuario {target_user['username']} por {admin_user['username']}")
                return True, "Contraseña reseteada exitosamente"
            else:
                return False, "Error al resetear la contraseña"
                
        except Exception as e:
            self.logger.error(f"Error reseteando contraseña: {e}")
            return False, f"Error reseteando contraseña: {str(e)}"
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Obtener usuario por ID"""
        try:
            return self.db.execute_single("""
                SELECT u.*, r.nombre as rol_nombre, r.permisos as rol_permisos,
                       creator.username as creado_por_username,
                       updater.username as actualizado_por_username
                FROM usuarios u
                LEFT JOIN roles r ON u.rol_id = r.id
                LEFT JOIN usuarios creator ON u.creado_por = creator.id
                LEFT JOIN usuarios updater ON u.actualizado_por = updater.id
                WHERE u.id = ?
            """, (user_id,))
            
        except Exception as e:
            self.logger.error(f"Error obteniendo usuario por ID: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Obtener usuario por username"""
        try:
            return self.db.execute_single("""
                SELECT u.*, r.nombre as rol_nombre, r.permisos as rol_permisos
                FROM usuarios u
                LEFT JOIN roles r ON u.rol_id = r.id
                WHERE u.username = ?
            """, (username,))
            
        except Exception as e:
            self.logger.error(f"Error obteniendo usuario por username: {e}")
            return None
    
    def get_all_users(self, include_inactive: bool = False) -> List[Dict]:
        """Obtener todos los usuarios"""
        try:
            query = """
                SELECT u.*, r.nombre as rol_nombre
                FROM usuarios u
                LEFT JOIN roles r ON u.rol_id = r.id
            """
            params = []
            
            if not include_inactive:
                query += " WHERE u.activo = 1"
            
            query += " ORDER BY u.nombre_completo"
            
            return self.db.execute_query(query, params)
            
        except Exception as e:
            self.logger.error(f"Error obteniendo usuarios: {e}")
            return []
    
    def user_has_permission(self, user_id: int, permission: str) -> bool:
        """Verificar si un usuario tiene un permiso específico"""
        try:
            user = self.get_user_by_id(user_id)
            if not user or not user.get('activo'):
                return False
            
            user_permissions = self._parse_permissions(user.get('rol_permisos', ''))
            
            # Administrador tiene todos los permisos
            if '*' in user_permissions:
                return True
            
            return permission in user_permissions
            
        except Exception as e:
            self.logger.error(f"Error verificando permisos: {e}")
            return False
    
    def create_role(self, role_data: Dict, creator_user_id: int) -> Tuple[bool, str, int]:
        """Crear nuevo rol"""
        try:
            # Validaciones básicas
            if not role_data.get('nombre'):
                return False, "El nombre del rol es obligatorio", 0
            
            # Verificar unicidad del nombre
            existing_role = self.db.execute_single("""
                SELECT id FROM roles WHERE nombre = ?
            """, (role_data['nombre'],))
            
            if existing_role:
                return False, "Ya existe un rol con ese nombre", 0
            
            # Validar permisos
            permisos_str = ','.join(role_data.get('permisos', []))
            
            # Crear rol
            role_id = self.db.execute_insert("""
                INSERT INTO roles (nombre, descripcion, permisos, creado_por)
                VALUES (?, ?, ?, ?)
            """, (
                role_data['nombre'],
                role_data.get('descripcion', ''),
                permisos_str,
                creator_user_id
            ))
            
            if role_id:
                self.logger.info(f"Rol creado: {role_data['nombre']} (ID: {role_id})")
                return True, f"Rol creado exitosamente", role_id
            else:
                return False, "Error al crear el rol", 0
                
        except Exception as e:
            self.logger.error(f"Error creando rol: {e}")
            return False, f"Error creando rol: {str(e)}", 0
    
    def get_role_by_id(self, role_id: int) -> Optional[Dict]:
        """Obtener rol por ID"""
        try:
            role = self.db.execute_single("""
                SELECT * FROM roles WHERE id = ?
            """, (role_id,))
            
            if role:
                role = dict(role)
                role['permisos'] = self._parse_permissions(role.get('permisos', ''))
            
            return role
            
        except Exception as e:
            self.logger.error(f"Error obteniendo rol: {e}")
            return None
    
    def get_all_roles(self) -> List[Dict]:
        """Obtener todos los roles"""
        try:
            roles = self.db.execute_query("SELECT * FROM roles ORDER BY nombre")
            
            # Parsear permisos para cada rol
            for role in roles:
                role['permisos'] = self._parse_permissions(role.get('permisos', ''))
            
            return roles
            
        except Exception as e:
            self.logger.error(f"Error obteniendo roles: {e}")
            return []
    
    def deactivate_user(self, user_id: int, admin_user_id: int) -> Tuple[bool, str]:
        """Desactivar usuario"""
        try:
            success = self.db.execute_update("""
                UPDATE usuarios 
                SET activo = 0, actualizado_en = CURRENT_TIMESTAMP, actualizado_por = ?
                WHERE id = ?
            """, (admin_user_id, user_id))
            
            if success:
                self.logger.info(f"Usuario desactivado: ID {user_id}")
                return True, "Usuario desactivado exitosamente"
            else:
                return False, "Error al desactivar el usuario"
                
        except Exception as e:
            self.logger.error(f"Error desactivando usuario: {e}")
            return False, f"Error desactivando usuario: {str(e)}"
    
    def _hash_password(self, password: str) -> str:
        """Hash de contraseña usando bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verificar contraseña contra hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False
    
    def _validate_password(self, password: str) -> bool:
        """Validar que la contraseña cumple con los requisitos"""
        if len(password) < 6:  # Mínimo 6 caracteres por defecto
            return False
        return True
    
    def _parse_permissions(self, permissions_str: str) -> List[str]:
        """Parsear string de permisos a lista"""
        if not permissions_str:
            return []
        return [p.strip() for p in permissions_str.split(',') if p.strip()]
    
    def _record_failed_attempt(self, username: str):
        """Registrar intento fallido de login"""
        if username not in self.failed_attempts:
            self.failed_attempts[username] = []
        
        self.failed_attempts[username].append(datetime.now())
        
        # Limpiar intentos antiguos (más de 15 minutos)
        cutoff_time = datetime.now() - timedelta(minutes=15)
        self.failed_attempts[username] = [
            attempt for attempt in self.failed_attempts[username] 
            if attempt > cutoff_time
        ]
    
    def _is_user_locked(self, username: str) -> bool:
        """Verificar si el usuario está bloqueado por intentos fallidos"""
        if username not in self.failed_attempts:
            return False
        
        # Limpiar intentos antiguos
        cutoff_time = datetime.now() - timedelta(minutes=15)
        self.failed_attempts[username] = [
            attempt for attempt in self.failed_attempts[username] 
            if attempt > cutoff_time
        ]
        
        # Verificar si hay más de 5 intentos en los últimos 15 minutos
        return len(self.failed_attempts[username]) >= 5
    
    def _clear_failed_attempts(self, username: str):
        """Limpiar intentos fallidos para un usuario"""
        if username in self.failed_attempts:
            del self.failed_attempts[username]
    
    def _ensure_default_roles(self):
        """Asegurar que existen los roles por defecto"""
        try:
            for role_name, role_data in self.DEFAULT_ROLES.items():
                existing_role = self.db.execute_single("""
                    SELECT id FROM roles WHERE nombre = ?
                """, (role_name,))
                
                if not existing_role:
                    permisos_str = ','.join(role_data['permisos'])
                    self.db.execute_insert("""
                        INSERT INTO roles (nombre, descripcion, permisos)
                        VALUES (?, ?, ?)
                    """, (role_name, role_data['descripcion'], permisos_str))
                    self.logger.info(f"Rol por defecto creado: {role_name}")
                    
        except Exception as e:
            self.logger.error(f"Error creando roles por defecto: {e}")
    
    def _ensure_admin_user(self):
        """Asegurar que existe el usuario administrador"""
        try:
            admin_user = self.db.execute_single("""
                SELECT id FROM usuarios WHERE username = 'admin'
            """)
            
            if not admin_user:
                admin_role = self.db.execute_single("""
                    SELECT id FROM roles WHERE nombre = 'ADMINISTRADOR'
                """)
                
                admin_role_id = admin_role['id'] if admin_role else None
                
                password_hash = self._hash_password('admin123')  # Contraseña por defecto
                
                self.db.execute_insert("""
                    INSERT INTO usuarios (username, password_hash, nombre_completo, rol_id, activo)
                    VALUES (?, ?, ?, ?, ?)
                """, ('admin', password_hash, 'Administrador del Sistema', admin_role_id, True))
                
                self.logger.info("Usuario administrador por defecto creado (admin/admin123)")
                
        except Exception as e:
            self.logger.error(f"Error creando usuario administrador: {e}")
    
    def _get_default_role_id(self) -> Optional[int]:
        """Obtener ID del rol por defecto (VENDEDOR)"""
        try:
            role = self.db.execute_single("""
                SELECT id FROM roles WHERE nombre = 'VENDEDOR'
            """)
            return role['id'] if role else None
        except Exception:
            return None