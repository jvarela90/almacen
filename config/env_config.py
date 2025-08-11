"""
Configuración basada en variables de entorno - AlmacénPro v2.0
Manejo seguro de configuración usando python-dotenv
"""

import os
from pathlib import Path
from typing import Optional, Union, List, Dict, Any
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class EnvironmentConfig:
    """Configuración centralizada basada en variables de entorno"""
    
    # ========================================================================
    # HELPERS PARA CONVERSIÓN DE TIPOS
    # ========================================================================
    
    @staticmethod
    def get_bool(key: str, default: bool = False) -> bool:
        """Convertir variable de entorno a boolean"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on', 'enabled')
    
    @staticmethod
    def get_int(key: str, default: int = 0) -> int:
        """Convertir variable de entorno a int"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default
    
    @staticmethod
    def get_float(key: str, default: float = 0.0) -> float:
        """Convertir variable de entorno a float"""
        try:
            return float(os.getenv(key, str(default)))
        except ValueError:
            return default
    
    @staticmethod
    def get_list(key: str, default: List[str] = None, separator: str = ',') -> List[str]:
        """Convertir variable de entorno a lista"""
        if default is None:
            default = []
        value = os.getenv(key, '')
        if not value:
            return default
        return [item.strip() for item in value.split(separator)]
    
    # ========================================================================
    # BASE DE DATOS
    # ========================================================================
    
    DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'sqlite')
    SQLITE_PATH = os.getenv('SQLITE_PATH', 'data/almacen_pro.db')
    
    # PostgreSQL
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = get_int.__func__('POSTGRES_PORT', 5432)
    POSTGRES_DATABASE = os.getenv('POSTGRES_DATABASE', 'almacen_pro')
    POSTGRES_USERNAME = os.getenv('POSTGRES_USERNAME', '')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
    
    # ========================================================================
    # SEGURIDAD
    # ========================================================================
    
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-in-production')
    SESSION_TIMEOUT_MINUTES = get_int.__func__('SESSION_TIMEOUT_MINUTES', 480)
    PASSWORD_MIN_LENGTH = get_int.__func__('PASSWORD_MIN_LENGTH', 6)
    MAX_LOGIN_ATTEMPTS = get_int.__func__('MAX_LOGIN_ATTEMPTS', 3)
    LOCK_AFTER_ATTEMPTS = get_int.__func__('LOCK_AFTER_ATTEMPTS', 5)
    
    # ========================================================================
    # EMPRESA
    # ========================================================================
    
    COMPANY_NAME = os.getenv('COMPANY_NAME', 'Mi Almacén')
    COMPANY_ADDRESS = os.getenv('COMPANY_ADDRESS', '')
    COMPANY_PHONE = os.getenv('COMPANY_PHONE', '')
    COMPANY_EMAIL = os.getenv('COMPANY_EMAIL', '')
    COMPANY_CUIT = os.getenv('COMPANY_CUIT', '')
    COMPANY_LOGO_PATH = os.getenv('COMPANY_LOGO_PATH', '')
    
    # ========================================================================
    # BACKUPS
    # ========================================================================
    
    BACKUP_ENABLED = get_bool.__func__('BACKUP_ENABLED', True)
    AUTO_BACKUP = get_bool.__func__('AUTO_BACKUP', True)
    BACKUP_INTERVAL_HOURS = get_int.__func__('BACKUP_INTERVAL_HOURS', 24)
    BACKUP_PATH = os.getenv('BACKUP_PATH', 'backups')
    MAX_BACKUPS = get_int.__func__('MAX_BACKUPS', 30)
    COMPRESS_BACKUPS = get_bool.__func__('COMPRESS_BACKUPS', True)
    
    # Cloud Backup
    CLOUD_BACKUP_ENABLED = get_bool.__func__('CLOUD_BACKUP_ENABLED', False)
    CLOUD_BACKUP_PROVIDER = os.getenv('CLOUD_BACKUP_PROVIDER', 'google_drive')
    CLOUD_BACKUP_CREDENTIALS_FILE = os.getenv('CLOUD_BACKUP_CREDENTIALS_FILE', '')
    CLOUD_BACKUP_REMOTE_FOLDER = os.getenv('CLOUD_BACKUP_REMOTE_FOLDER', 'AlmacenPro_Backups')
    
    # ========================================================================
    # HARDWARE
    # ========================================================================
    
    BARCODE_SCANNER_ENABLED = get_bool.__func__('BARCODE_SCANNER_ENABLED', True)
    BARCODE_SCANNER_PORT = os.getenv('BARCODE_SCANNER_PORT', 'auto')
    BARCODE_SCANNER_PREFIX = os.getenv('BARCODE_SCANNER_PREFIX', '')
    BARCODE_SCANNER_SUFFIX = os.getenv('BARCODE_SCANNER_SUFFIX', '')
    
    CASH_DRAWER_ENABLED = get_bool.__func__('CASH_DRAWER_ENABLED', False)
    CASH_DRAWER_PORT = os.getenv('CASH_DRAWER_PORT', 'COM1')
    CASH_DRAWER_OPEN_COMMAND = os.getenv('CASH_DRAWER_OPEN_COMMAND', '')
    
    SCALE_ENABLED = get_bool.__func__('SCALE_ENABLED', False)
    SCALE_PORT = os.getenv('SCALE_PORT', 'COM2')
    SCALE_BRAND = os.getenv('SCALE_BRAND', 'toledo')
    SCALE_MODEL = os.getenv('SCALE_MODEL', '')
    
    # ========================================================================
    # IMPRESIÓN
    # ========================================================================
    
    PRINTER_NAME = os.getenv('PRINTER_NAME', '')
    PAPER_WIDTH = get_int.__func__('PAPER_WIDTH', 80)
    AUTO_PRINT = get_bool.__func__('AUTO_PRINT', False)
    COPY_COUNT = get_int.__func__('COPY_COUNT', 1)
    FOOTER_MESSAGE = os.getenv('FOOTER_MESSAGE', '¡Gracias por su compra!')
    INCLUDE_LOGO = get_bool.__func__('INCLUDE_LOGO', False)
    
    # ========================================================================
    # INTERFAZ
    # ========================================================================
    
    UI_THEME = os.getenv('UI_THEME', 'default')
    UI_LANGUAGE = os.getenv('UI_LANGUAGE', 'es')
    UI_FONT_SIZE = get_int.__func__('UI_FONT_SIZE', 9)
    WINDOW_MAXIMIZED = get_bool.__func__('WINDOW_MAXIMIZED', True)
    
    # ========================================================================
    # NOTIFICACIONES
    # ========================================================================
    
    NOTIFICATIONS_ENABLED = get_bool.__func__('NOTIFICATIONS_ENABLED', True)
    LOW_STOCK_ALERTS = get_bool.__func__('LOW_STOCK_ALERTS', True)
    DAILY_SALES_SUMMARY = get_bool.__func__('DAILY_SALES_SUMMARY', True)
    BACKUP_NOTIFICATIONS = get_bool.__func__('BACKUP_NOTIFICATIONS', True)
    SYSTEM_NOTIFICATIONS = get_bool.__func__('SYSTEM_NOTIFICATIONS', True)
    
    # ========================================================================
    # SYNC
    # ========================================================================
    
    SYNC_ENABLED = get_bool.__func__('SYNC_ENABLED', False)
    SYNC_SERVER_URL = os.getenv('SYNC_SERVER_URL', '')
    SYNC_API_KEY = os.getenv('SYNC_API_KEY', '')
    SYNC_INTERVAL_MINUTES = get_int.__func__('SYNC_INTERVAL_MINUTES', 30)
    OFFLINE_MODE = get_bool.__func__('OFFLINE_MODE', True)
    
    # ========================================================================
    # REPORTES
    # ========================================================================
    
    DEFAULT_EXPORT_FORMAT = os.getenv('DEFAULT_EXPORT_FORMAT', 'pdf')
    INCLUDE_CHARTS = get_bool.__func__('INCLUDE_CHARTS', True)
    AUTO_SAVE_PATH = os.getenv('AUTO_SAVE_PATH', 'exports')
    
    # ========================================================================
    # DESARROLLO
    # ========================================================================
    
    DEBUG = get_bool.__func__('DEBUG', False)
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    ENABLE_SQL_LOGGING = get_bool.__func__('ENABLE_SQL_LOGGING', False)
    
    # ========================================================================
    # MÉTODOS DE CONFIGURACIÓN
    # ========================================================================
    
    @classmethod
    def get_database_config(cls) -> Dict[str, Any]:
        """Obtener configuración de base de datos"""
        if cls.DATABASE_TYPE == 'postgresql':
            return {
                'type': 'postgresql',
                'host': cls.POSTGRES_HOST,
                'port': cls.POSTGRES_PORT,
                'database': cls.POSTGRES_DATABASE,
                'username': cls.POSTGRES_USERNAME,
                'password': cls.POSTGRES_PASSWORD,
            }
        else:
            return {
                'type': 'sqlite',
                'path': cls.SQLITE_PATH,
            }
    
    @classmethod
    def get_company_config(cls) -> Dict[str, str]:
        """Obtener configuración de empresa"""
        return {
            'name': cls.COMPANY_NAME,
            'address': cls.COMPANY_ADDRESS,
            'phone': cls.COMPANY_PHONE,
            'email': cls.COMPANY_EMAIL,
            'cuit': cls.COMPANY_CUIT,
            'logo_path': cls.COMPANY_LOGO_PATH,
        }
    
    @classmethod
    def get_backup_config(cls) -> Dict[str, Any]:
        """Obtener configuración de backups"""
        return {
            'enabled': cls.BACKUP_ENABLED,
            'auto_backup': cls.AUTO_BACKUP,
            'backup_interval_hours': cls.BACKUP_INTERVAL_HOURS,
            'backup_path': cls.BACKUP_PATH,
            'max_backups': cls.MAX_BACKUPS,
            'compress_backups': cls.COMPRESS_BACKUPS,
            'cloud_backup': {
                'enabled': cls.CLOUD_BACKUP_ENABLED,
                'provider': cls.CLOUD_BACKUP_PROVIDER,
                'credentials_file': cls.CLOUD_BACKUP_CREDENTIALS_FILE,
                'remote_folder': cls.CLOUD_BACKUP_REMOTE_FOLDER,
            }
        }
    
    @classmethod
    def get_hardware_config(cls) -> Dict[str, Any]:
        """Obtener configuración de hardware"""
        return {
            'barcode_scanner': {
                'enabled': cls.BARCODE_SCANNER_ENABLED,
                'port': cls.BARCODE_SCANNER_PORT,
                'prefix': cls.BARCODE_SCANNER_PREFIX,
                'suffix': cls.BARCODE_SCANNER_SUFFIX,
            },
            'cash_drawer': {
                'enabled': cls.CASH_DRAWER_ENABLED,
                'port': cls.CASH_DRAWER_PORT,
                'open_command': cls.CASH_DRAWER_OPEN_COMMAND,
            },
            'scale': {
                'enabled': cls.SCALE_ENABLED,
                'port': cls.SCALE_PORT,
                'brand': cls.SCALE_BRAND,
                'model': cls.SCALE_MODEL,
            },
        }
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """Validar configuración y retornar lista de errores"""
        errors = []
        
        # Validar SECRET_KEY en producción
        if not cls.DEBUG and cls.SECRET_KEY == 'change-this-in-production':
            errors.append("SECRET_KEY debe ser cambiado en producción")
        
        # Validar configuración de base de datos
        if cls.DATABASE_TYPE == 'postgresql':
            if not cls.POSTGRES_USERNAME:
                errors.append("POSTGRES_USERNAME es requerido para PostgreSQL")
            if not cls.POSTGRES_PASSWORD:
                errors.append("POSTGRES_PASSWORD es requerido para PostgreSQL")
        
        # Validar paths
        if cls.SQLITE_PATH and not os.path.isdir(os.path.dirname(cls.SQLITE_PATH)):
            try:
                Path(os.path.dirname(cls.SQLITE_PATH)).mkdir(parents=True, exist_ok=True)
            except Exception:
                errors.append(f"No se puede crear directorio para {cls.SQLITE_PATH}")
        
        return errors
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convertir toda la configuración a diccionario (para compatibilidad)"""
        return {
            'database': cls.get_database_config(),
            'company': cls.get_company_config(),
            'backup': cls.get_backup_config(),
            'hardware': cls.get_hardware_config(),
            'ui': {
                'theme': cls.UI_THEME,
                'language': cls.UI_LANGUAGE,
                'font_size': cls.UI_FONT_SIZE,
                'window_maximized': cls.WINDOW_MAXIMIZED,
            },
            'security': {
                'session_timeout_minutes': cls.SESSION_TIMEOUT_MINUTES,
                'password_min_length': cls.PASSWORD_MIN_LENGTH,
                'max_login_attempts': cls.MAX_LOGIN_ATTEMPTS,
                'lock_after_attempts': cls.LOCK_AFTER_ATTEMPTS,
            },
            'notifications': {
                'enabled': cls.NOTIFICATIONS_ENABLED,
                'low_stock_alerts': cls.LOW_STOCK_ALERTS,
                'daily_sales_summary': cls.DAILY_SALES_SUMMARY,
                'backup_notifications': cls.BACKUP_NOTIFICATIONS,
                'system_notifications': cls.SYSTEM_NOTIFICATIONS,
            },
            'tickets': {
                'printer_name': cls.PRINTER_NAME,
                'paper_width': cls.PAPER_WIDTH,
                'auto_print': cls.AUTO_PRINT,
                'copy_count': cls.COPY_COUNT,
                'footer_message': cls.FOOTER_MESSAGE,
                'include_logo': cls.INCLUDE_LOGO,
            },
            'reports': {
                'default_export_format': cls.DEFAULT_EXPORT_FORMAT,
                'include_charts': cls.INCLUDE_CHARTS,
                'auto_save_path': cls.AUTO_SAVE_PATH,
            },
            'sync': {
                'enabled': cls.SYNC_ENABLED,
                'server_url': cls.SYNC_SERVER_URL,
                'api_key': cls.SYNC_API_KEY,
                'sync_interval_minutes': cls.SYNC_INTERVAL_MINUTES,
                'offline_mode': cls.OFFLINE_MODE,
            }
        }

# Instancia global de configuración
env_config = EnvironmentConfig()