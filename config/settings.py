"""
Configuraciones globales para AlmacénPro v2.0
Manejo centralizado de configuraciones del sistema
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class Settings:
    """Gestor de configuraciones del sistema"""
    
    # Configuraciones por defecto
    DEFAULT_SETTINGS = {
        # Base de datos
        'database': {
            'path': 'almacen_pro.db',
            'backup_on_startup': True,
            'optimize_on_startup': True,
            'enable_foreign_keys': True
        },
        
        # Interfaz de usuario
        'ui': {
            'theme': 'default',
            'language': 'es',
            'window_size': {'width': 1200, 'height': 800},
            'window_maximized': False,
            'show_splash': True,
            'auto_save_layout': True,
            'grid_lines': True,
            'row_height': 25
        },
        
        # Ventas
        'sales': {
            'auto_print_ticket': False,
            'ask_customer_data': False,
            'allow_negative_stock': False,
            'default_payment_method': 'EFECTIVO',
            'tax_included': True,
            'default_tax_rate': 21.0,
            'round_totals': True,
            'ticket_copies': 1
        },
        
        # Productos
        'products': {
            'auto_generate_barcode': True,
            'barcode_prefix': '200',
            'require_category': False,
            'require_provider': False,
            'default_unit': 'UNIDAD',
            'track_lot_numbers': False,
            'track_expiration': False,
            'low_stock_warning': True,
            'low_stock_days': 30
        },
        
        # Reportes
        'reports': {
            'default_format': 'PDF',
            'include_logo': True,
            'company_name': 'Mi Empresa',
            'company_address': '',
            'company_phone': '',
            'company_email': '',
            'auto_open_reports': True
        },
        
        # Backup
        'backup': {
            'enabled': True,
            'auto_backup': True,
            'backup_interval': 24,  # horas
            'keep_backups': 30,     # días
            'compress_backups': True,
            'backup_location': 'backups',
            'include_images': True,
            'cloud_backup': False
        },
        
        # Seguridad
        'security': {
            'session_timeout': 480,  # minutos (8 horas)
            'password_min_length': 6,
            'require_strong_password': False,
            'max_login_attempts': 5,
            'lockout_duration': 15,  # minutos
            'log_user_actions': True
        },
        
        # Sistema
        'system': {
            'log_level': 'INFO',
            'log_file_size': 10,  # MB
            'log_files_keep': 5,
            'enable_notifications': True,
            'check_updates': True,
            'send_usage_stats': False
        },
        
        # Hardware
        'hardware': {
            'default_printer': '',
            'ticket_printer': '',
            'barcode_scanner': {
                'enabled': True,
                'auto_search': True,
                'play_sound': True,
                'prefix': '',
                'suffix': ''
            },
            'cash_drawer': {
                'enabled': False,
                'open_on_sale': True,
                'open_command': ''
            },
            'display_customer': {
                'enabled': False,
                'port': '',
                'show_total': True,
                'show_change': True
            }
        }
    }
    
    def __init__(self, config_file: str = 'config.json'):
        self.config_file = Path(config_file)
        self.settings = {}
        self.load_settings()
    
    def load_settings(self):
        """Cargar configuraciones desde archivo"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_settings = json.load(f)
                
                # Combinar con configuraciones por defecto
                self.settings = self._merge_settings(self.DEFAULT_SETTINGS.copy(), file_settings)
                logger.info("Configuraciones cargadas desde archivo")
            else:
                # Usar configuraciones por defecto
                self.settings = self.DEFAULT_SETTINGS.copy()
                self.save_settings()
                logger.info("Configuraciones por defecto creadas")
                
        except Exception as e:
            logger.error(f"Error cargando configuraciones: {e}")
            self.settings = self.DEFAULT_SETTINGS.copy()
    
    def save_settings(self):
        """Guardar configuraciones a archivo"""
        try:
            # Crear directorio si no existe
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Guardar con formato bonito
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            
            logger.info("Configuraciones guardadas")
            
        except Exception as e:
            logger.error(f"Error guardando configuraciones: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtener valor de configuración usando notación de punto"""
        try:
            keys = key.split('.')
            value = self.settings
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception as e:
            logger.error(f"Error obteniendo configuración '{key}': {e}")
            return default
    
    def set(self, key: str, value: Any, save: bool = True):
        """Establecer valor de configuración usando notación de punto"""
        try:
            keys = key.split('.')
            current = self.settings
            
            # Navegar hasta el penúltimo nivel
            for k in keys[:-1]:
                if k not in current or not isinstance(current[k], dict):
                    current[k] = {}
                current = current[k]
            
            # Establecer valor
            current[keys[-1]] = value
            
            if save:
                self.save_settings()
            
            logger.debug(f"Configuración establecida: {key} = {value}")
            
        except Exception as e:
            logger.error(f"Error estableciendo configuración '{key}': {e}")
    
    def get_database_config(self) -> Dict[str, Any]:
        """Obtener configuración de base de datos"""
        return self.get('database', {})
    
    def get_ui_config(self) -> Dict[str, Any]:
        """Obtener configuración de interfaz"""
        return self.get('ui', {})
    
    def get_sales_config(self) -> Dict[str, Any]:
        """Obtener configuración de ventas"""
        return self.get('sales', {})
    
    def get_backup_config(self) -> Dict[str, Any]:
        """Obtener configuración de backup"""
        return self.get('backup', {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """Obtener configuración de seguridad"""
        return self.get('security', {})
    
    def reset_to_defaults(self, section: str = None):
        """Resetear configuraciones a valores por defecto"""
        try:
            if section:
                if section in self.DEFAULT_SETTINGS:
                    self.settings[section] = self.DEFAULT_SETTINGS[section].copy()
                    logger.info(f"Sección '{section}' reseteada a valores por defecto")
                else:
                    logger.warning(f"Sección '{section}' no encontrada")
            else:
                self.settings = self.DEFAULT_SETTINGS.copy()
                logger.info("Todas las configuraciones reseteadas a valores por defecto")
            
            self.save_settings()
            
        except Exception as e:
            logger.error(f"Error reseteando configuraciones: {e}")
    
    def export_settings(self, export_file: str) -> bool:
        """Exportar configuraciones a archivo"""
        try:
            export_path = Path(export_file)
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'version': '2.0',
                'settings': self.settings
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=4, ensure_ascii=False)
            
            logger.info(f"Configuraciones exportadas a: {export_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando configuraciones: {e}")
            return False
    
    def import_settings(self, import_file: str, overwrite: bool = False) -> bool:
        """Importar configuraciones desde archivo"""
        try:
            import_path = Path(import_file)
            if not import_path.exists():
                logger.error(f"Archivo de importación no encontrado: {import_file}")
                return False
            
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if 'settings' not in import_data:
                logger.error("Archivo de importación inválido")
                return False
            
            imported_settings = import_data['settings']
            
            if overwrite:
                # Sobrescribir completamente
                self.settings = self._merge_settings(self.DEFAULT_SETTINGS.copy(), imported_settings)
            else:
                # Combinar con configuraciones existentes
                self.settings = self._merge_settings(self.settings, imported_settings)
            
            self.save_settings()
            logger.info(f"Configuraciones importadas desde: {import_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error importando configuraciones: {e}")
            return False
    
    def validate_settings(self) -> Dict[str, list]:
        """Validar configuraciones actuales"""
        errors = {}
        warnings = {}
        
        try:
            # Validar base de datos
            db_path = self.get('database.path')
            if not db_path:
                errors.setdefault('database', []).append("Ruta de base de datos requerida")
            
            # Validar backup
            if self.get('backup.enabled'):
                backup_location = self.get('backup.backup_location')
                if not backup_location:
                    errors.setdefault('backup', []).append("Ubicación de backup requerida")
                
                backup_interval = self.get('backup.backup_interval', 0)
                if backup_interval <= 0 or backup_interval > 168:  # 1 semana máximo
                    warnings.setdefault('backup', []).append("Intervalo de backup debería estar entre 1 y 168 horas")
            
            # Validar seguridad
            session_timeout = self.get('security.session_timeout', 0)
            if session_timeout <= 0:
                warnings.setdefault('security', []).append("Timeout de sesión debería ser mayor a 0")
            
            password_length = self.get('security.password_min_length', 0)
            if password_length < 4:
                warnings.setdefault('security', []).append("Longitud mínima de contraseña debería ser al menos 4")
            
            # Validar ventas
            tax_rate = self.get('sales.default_tax_rate', 0)
            if tax_rate < 0 or tax_rate > 100:
                errors.setdefault('sales', []).append("Tasa de impuesto debe estar entre 0 y 100")
            
            return {'errors': errors, 'warnings': warnings}
            
        except Exception as e:
            logger.error(f"Error validando configuraciones: {e}")
            return {'errors': {'general': [str(e)]}, 'warnings': {}}
    
    def _merge_settings(self, base: dict, overlay: dict) -> dict:
        """Combinar configuraciones recursivamente"""
        result = base.copy()
        
        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_settings(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get_company_info(self) -> Dict[str, str]:
        """Obtener información de la empresa"""
        return {
            'name': self.get('reports.company_name', 'Mi Empresa'),
            'address': self.get('reports.company_address', ''),
            'phone': self.get('reports.company_phone', ''),
            'email': self.get('reports.company_email', ''),
        }
    
    def update_company_info(self, name: str = None, address: str = None, 
                           phone: str = None, email: str = None):
        """Actualizar información de la empresa"""
        if name is not None:
            self.set('reports.company_name', name, False)
        if address is not None:
            self.set('reports.company_address', address, False)
        if phone is not None:
            self.set('reports.company_phone', phone, False)
        if email is not None:
            self.set('reports.company_email', email, False)
        
        self.save_settings()
    
    def is_first_run(self) -> bool:
        """Verificar si es la primera ejecución"""
        return not self.config_file.exists()
    
    def create_directories(self):
        """Crear directorios necesarios según configuración"""
        try:
            directories = [
                'logs',
                self.get('backup.backup_location', 'backups'),
                'temp',
                'reports',
                'images/products',
                'data'
            ]
            
            for directory in directories:
                Path(directory).mkdir(parents=True, exist_ok=True)
                
            logger.info("Directorios del sistema creados")
            
        except Exception as e:
            logger.error(f"Error creando directorios: {e}")

# Instancia global de configuraciones
settings = Settings()