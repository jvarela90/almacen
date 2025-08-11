"""
Configuración unificada basada en variables de entorno - AlmacénPro v2.0
Reemplaza config.json con un sistema seguro y flexible usando python-dotenv
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Union, List, Dict, Any, Tuple
from dotenv import load_dotenv

# Configurar logging
logger = logging.getLogger(__name__)

class EnvSettings:
    """
    Configuración centralizada usando variables de entorno
    Diseñado para reemplazar completamente config.json
    """
    
    def __init__(self, env_file: str = '.env'):
        """
        Inicializar configuración desde variables de entorno
        
        Args:
            env_file: Archivo .env a cargar (default: '.env')
        """
        # Cargar variables de entorno desde archivo .env
        self.env_file = env_file
        self.project_root = Path(__file__).resolve().parents[1]
        env_path = self.project_root / env_file
        
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"Cargado archivo de configuración: {env_path}")
        else:
            logger.warning(f"Archivo .env no encontrado: {env_path}")
            
        # Validar configuración crítica
        self._validate_critical_config()
    
    # ========================================================================
    # HELPERS PARA CONVERSIÓN DE TIPOS
    # ========================================================================
    
    @staticmethod
    def get_bool(key: str, default: bool = False) -> bool:
        """Convertir variable de entorno a boolean"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on', 'enabled', 'si')
    
    @staticmethod
    def get_int(key: str, default: int = 0) -> int:
        """Convertir variable de entorno a int con validación"""
        try:
            value = os.getenv(key, str(default))
            return int(value)
        except (ValueError, TypeError) as e:
            logger.warning(f"Error convirtiendo {key}='{value}' a int: {e}. Usando default: {default}")
            return default
    
    @staticmethod
    def get_float(key: str, default: float = 0.0) -> float:
        """Convertir variable de entorno a float con validación"""
        try:
            value = os.getenv(key, str(default))
            return float(value)
        except (ValueError, TypeError) as e:
            logger.warning(f"Error convirtiendo {key}='{value}' a float: {e}. Usando default: {default}")
            return default
    
    @staticmethod
    def get_list(key: str, default: List[str] = None, separator: str = ',') -> List[str]:
        """Convertir variable de entorno a lista"""
        if default is None:
            default = []
        value = os.getenv(key, '')
        if not value.strip():
            return default
        return [item.strip() for item in value.split(separator) if item.strip()]
    
    @staticmethod
    def get_path(key: str, default: str = '') -> Path:
        """Convertir variable de entorno a Path"""
        value = os.getenv(key, default)
        return Path(value) if value else Path(default)
    
    # ========================================================================
    # CONFIGURACIÓN DE BASE DE DATOS
    # ========================================================================
    
    @property
    def database_type(self) -> str:
        return os.getenv('DATABASE_TYPE', 'sqlite').lower()
    
    @property
    def sqlite_path(self) -> str:
        return os.getenv('SQLITE_PATH', 'data/almacen_pro.db')
    
    @property
    def postgres_config(self) -> Dict[str, Any]:
        return {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': self.get_int('POSTGRES_PORT', 5432),
            'database': os.getenv('POSTGRES_DATABASE', 'almacen_pro'),
            'username': os.getenv('POSTGRES_USERNAME', ''),
            'password': os.getenv('POSTGRES_PASSWORD', '')
        }
    
    def get_database_config(self) -> Dict[str, Any]:
        """Obtener configuración de base de datos completa"""
        if self.database_type == 'postgresql':
            return {
                'type': 'postgresql',
                **self.postgres_config,
                'path': None
            }
        else:
            return {
                'type': 'sqlite',
                'path': self.sqlite_path,
                'host': None,
                'port': None
            }
    
    # ========================================================================
    # CONFIGURACIÓN DE SEGURIDAD
    # ========================================================================
    
    @property
    def secret_key(self) -> str:
        return os.getenv('SECRET_KEY', 'change-this-in-production')
    
    @property
    def session_timeout_minutes(self) -> int:
        return self.get_int('SESSION_TIMEOUT_MINUTES', 480)
    
    @property
    def password_min_length(self) -> int:
        return self.get_int('PASSWORD_MIN_LENGTH', 6)
    
    @property
    def max_login_attempts(self) -> int:
        return self.get_int('MAX_LOGIN_ATTEMPTS', 3)
    
    @property
    def lock_after_attempts(self) -> int:
        return self.get_int('LOCK_AFTER_ATTEMPTS', 5)
    
    @property
    def audit_log_enabled(self) -> bool:
        return self.get_bool('AUDIT_LOG', True)
    
    def get_security_config(self) -> Dict[str, Any]:
        """Obtener configuración de seguridad completa"""
        return {
            'secret_key': self.secret_key,
            'session_timeout_minutes': self.session_timeout_minutes,
            'password_min_length': self.password_min_length,
            'max_login_attempts': self.max_login_attempts,
            'lock_after_attempts': self.lock_after_attempts,
            'audit_log': self.audit_log_enabled
        }
    
    # ========================================================================
    # CONFIGURACIÓN DE EMPRESA
    # ========================================================================
    
    @property
    def company_config(self) -> Dict[str, Any]:
        return {
            'name': os.getenv('COMPANY_NAME', 'Mi Almacén'),
            'address': os.getenv('COMPANY_ADDRESS', ''),
            'phone': os.getenv('COMPANY_PHONE', ''),
            'email': os.getenv('COMPANY_EMAIL', ''),
            'cuit': os.getenv('COMPANY_CUIT', ''),
            'logo_path': os.getenv('COMPANY_LOGO_PATH', '')
        }
    
    # ========================================================================
    # CONFIGURACIÓN DE BACKUP
    # ========================================================================
    
    @property
    def backup_config(self) -> Dict[str, Any]:
        return {
            'enabled': self.get_bool('BACKUP_ENABLED', True),
            'auto_backup': self.get_bool('AUTO_BACKUP', True),
            'backup_interval_hours': self.get_int('BACKUP_INTERVAL_HOURS', 24),
            'backup_path': os.getenv('BACKUP_PATH', 'backups'),
            'max_backups': self.get_int('MAX_BACKUPS', 30),
            'compress_backups': self.get_bool('COMPRESS_BACKUPS', True),
            'cloud_backup': {
                'enabled': self.get_bool('CLOUD_BACKUP_ENABLED', False),
                'provider': os.getenv('CLOUD_BACKUP_PROVIDER', 'google_drive'),
                'credentials_file': os.getenv('CLOUD_BACKUP_CREDENTIALS_FILE', ''),
                'remote_folder': os.getenv('CLOUD_BACKUP_REMOTE_FOLDER', 'AlmacenPro_Backups')
            }
        }
    
    # ========================================================================
    # CONFIGURACIÓN DE IMPRESIÓN/TICKETS  
    # ========================================================================
    
    @property
    def tickets_config(self) -> Dict[str, Any]:
        return {
            'printer_name': os.getenv('PRINTER_NAME', ''),
            'paper_width': self.get_int('PAPER_WIDTH', 80),
            'auto_print': self.get_bool('AUTO_PRINT', False),
            'copy_count': self.get_int('COPY_COUNT', 1),
            'footer_message': os.getenv('FOOTER_MESSAGE', '¡Gracias por su compra!'),
            'include_logo': self.get_bool('INCLUDE_LOGO', False)
        }
    
    # ========================================================================
    # CONFIGURACIÓN DE INTERFAZ
    # ========================================================================
    
    @property
    def ui_config(self) -> Dict[str, Any]:
        return {
            'theme': os.getenv('UI_THEME', 'default'),
            'language': os.getenv('UI_LANGUAGE', 'es'),
            'font_size': self.get_int('UI_FONT_SIZE', 9),
            'window_maximized': self.get_bool('WINDOW_MAXIMIZED', True),
            'last_window_size': [
                self.get_int('LAST_WINDOW_WIDTH', 1200),
                self.get_int('LAST_WINDOW_HEIGHT', 800)
            ],
            'last_window_position': [
                self.get_int('LAST_WINDOW_X', 100),
                self.get_int('LAST_WINDOW_Y', 100)
            ]
        }
    
    # ========================================================================
    # CONFIGURACIÓN DE NOTIFICACIONES
    # ========================================================================
    
    @property 
    def notifications_config(self) -> Dict[str, Any]:
        return {
            'enabled': self.get_bool('NOTIFICATIONS_ENABLED', True),
            'low_stock_alerts': self.get_bool('LOW_STOCK_ALERTS', True),
            'daily_sales_summary': self.get_bool('DAILY_SALES_SUMMARY', True),
            'backup_notifications': self.get_bool('BACKUP_NOTIFICATIONS', True),
            'system_notifications': self.get_bool('SYSTEM_NOTIFICATIONS', True)
        }
    
    # ========================================================================
    # CONFIGURACIÓN DE HARDWARE
    # ========================================================================
    
    @property
    def hardware_config(self) -> Dict[str, Any]:
        return {
            'barcode_scanner': {
                'enabled': self.get_bool('BARCODE_SCANNER_ENABLED', True),
                'port': os.getenv('BARCODE_SCANNER_PORT', 'auto'),
                'prefix': os.getenv('BARCODE_SCANNER_PREFIX', ''),
                'suffix': os.getenv('BARCODE_SCANNER_SUFFIX', '')
            },
            'cash_drawer': {
                'enabled': self.get_bool('CASH_DRAWER_ENABLED', False),
                'port': os.getenv('CASH_DRAWER_PORT', 'COM1'),
                'open_command': os.getenv('CASH_DRAWER_OPEN_COMMAND', '')
            },
            'scale': {
                'enabled': self.get_bool('SCALE_ENABLED', False),
                'port': os.getenv('SCALE_PORT', 'COM2'),
                'brand': os.getenv('SCALE_BRAND', 'toledo'),
                'model': os.getenv('SCALE_MODEL', '')
            }
        }
    
    # ========================================================================
    # CONFIGURACIÓN DE SINCRONIZACIÓN
    # ========================================================================
    
    @property
    def sync_config(self) -> Dict[str, Any]:
        return {
            'enabled': self.get_bool('SYNC_ENABLED', False),
            'server_url': os.getenv('SYNC_SERVER_URL', ''),
            'api_key': os.getenv('SYNC_API_KEY', ''),
            'sync_interval_minutes': self.get_int('SYNC_INTERVAL_MINUTES', 30),
            'offline_mode': self.get_bool('OFFLINE_MODE', True)
        }
    
    # ========================================================================
    # CONFIGURACIÓN DE REPORTES
    # ========================================================================
    
    @property
    def reports_config(self) -> Dict[str, Any]:
        return {
            'default_export_format': os.getenv('DEFAULT_EXPORT_FORMAT', 'pdf'),
            'include_charts': self.get_bool('INCLUDE_CHARTS', True),
            'auto_save_path': os.getenv('AUTO_SAVE_PATH', 'exports')
        }
    
    # ========================================================================
    # CONFIGURACIÓN DE DESARROLLO
    # ========================================================================
    
    @property
    def debug_mode(self) -> bool:
        return self.get_bool('DEBUG', False)
    
    @property
    def log_level(self) -> str:
        return os.getenv('LOG_LEVEL', 'INFO').upper()
    
    @property
    def sql_logging_enabled(self) -> bool:
        return self.get_bool('ENABLE_SQL_LOGGING', False)
    
    # ========================================================================
    # MÉTODOS PÚBLICOS PRINCIPALES
    # ========================================================================
    
    def to_config_dict(self) -> Dict[str, Any]:
        """
        Convertir toda la configuración a un diccionario compatible con config.json
        Útil para migración gradual y compatibilidad hacia atrás
        """
        return {
            'database': self.get_database_config(),
            'security': self.get_security_config(),
            'company': self.company_config,
            'backup': self.backup_config,
            'tickets': self.tickets_config,
            'ui': self.ui_config,
            'notifications': self.notifications_config,
            'hardware': self.hardware_config,
            'sync': self.sync_config,
            'reports': self.reports_config,
            'development': {
                'debug': self.debug_mode,
                'log_level': self.log_level,
                'sql_logging': self.sql_logging_enabled
            }
        }
    
    def save_to_json(self, file_path: str = 'config_generated.json') -> bool:
        """
        Guardar configuración actual a archivo JSON para backup/debug
        """
        try:
            config_dict = self.to_config_dict()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=4, ensure_ascii=False)
            logger.info(f"Configuración guardada en: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error guardando configuración a JSON: {e}")
            return False
    
    def _validate_critical_config(self) -> List[str]:
        """Validar configuración crítica y retornar lista de errores"""
        errors = []
        
        # Validar SECRET_KEY en producción
        if not self.debug_mode and self.secret_key == 'change-this-in-production':
            errors.append("SECRET_KEY debe ser cambiado en producción")
        
        # Validar configuración de base de datos
        if self.database_type == 'postgresql':
            if not self.postgres_config['username']:
                errors.append("POSTGRES_USERNAME es requerido para PostgreSQL")
            if not self.postgres_config['password']:
                errors.append("POSTGRES_PASSWORD es requerido para PostgreSQL")
        
        # Validar paths críticos
        if self.database_type == 'sqlite':
            db_path = Path(self.sqlite_path)
            try:
                db_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"No se puede crear directorio para BD: {e}")
        
        # Validar configuración de empresa para producción
        if not self.debug_mode:
            if not self.company_config['name'].strip():
                logger.warning("COMPANY_NAME no configurado")
        
        if errors:
            logger.error(f"Errores de configuración encontrados: {errors}")
            
        return errors
    
    def get_database_path(self) -> str:
        """Obtener ruta de base de datos para compatibilidad"""
        return self.sqlite_path
    
    def is_development(self) -> bool:
        """Verificar si está en modo desarrollo"""
        return self.debug_mode
    
    def get_log_config(self) -> Dict[str, Any]:
        """Configuración de logging"""
        return {
            'level': self.log_level,
            'sql_logging': self.sql_logging_enabled,
            'debug': self.debug_mode
        }


# ============================================================================
# INSTANCIA GLOBAL PARA IMPORTACIÓN FÁCIL
# ============================================================================

# Instancia global para fácil acceso desde cualquier parte del código
settings = EnvSettings()

# Función helper para compatibilidad con código existente
def get_config() -> Dict[str, Any]:
    """Obtener configuración completa como diccionario (compatibilidad)"""
    return settings.to_config_dict()

# Validar configuración al importar
validation_errors = settings._validate_critical_config()
if validation_errors:
    logger.warning(f"Configuración tiene {len(validation_errors)} advertencias")
else:
    logger.info("Configuración validada correctamente")