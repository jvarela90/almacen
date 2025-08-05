"""
Configuraciones globales de AlmacénPro
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class AppSettings:
    """Gestor de configuraciones de la aplicación"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.settings = self._load_default_settings()
        self.load_from_file()
    
    def _load_default_settings(self) -> Dict[str, Any]:
        """Cargar configuraciones por defecto"""
        return {
            # Configuraciones de base de datos
            "database": {
                "type": "sqlite",
                "sqlite_path": "data/almacen_pro.db",
                "postgresql": {
                    "host": "localhost",
                    "port": 5432,
                    "database": "almacen_pro",
                    "username": "",
                    "password": ""
                }
            },
            
            # Configuraciones de backup
            "backup": {
                "enabled": True,
                "auto_backup": True,
                "backup_interval_hours": 24,
                "backup_path": "backups",
                "max_backups": 30,
                "compress_backups": True,
                "cloud_backup": {
                    "enabled": False,
                    "provider": "google_drive",  # google_drive, dropbox, onedrive
                    "credentials_file": "",
                    "remote_folder": "AlmacenPro_Backups"
                }
            },
            
            # Configuraciones de la empresa
            "company": {
                "name": "Mi Almacén",
                "address": "",
                "phone": "",
                "email": "",
                "cuit": "",
                "logo_path": ""
            },
            
            # Configuraciones de tickets
            "tickets": {
                "printer_name": "",
                "paper_width": 80,  # mm
                "auto_print": False,
                "copy_count": 1,
                "footer_message": "¡Gracias por su compra!",
                "include_logo": False
            },
            
            # Configuraciones de interfaz
            "ui": {
                "theme": "light",  # light, dark
                "language": "es",
                "font_size": 9,
                "window_maximized": True,
                "last_window_size": [1200, 800],
                "last_window_position": [100, 100]
            },
            
            # Configuraciones de notificaciones
            "notifications": {
                "enabled": True,
                "low_stock_alerts": True,
                "daily_sales_summary": True,
                "backup_notifications": True,
                "system_notifications": True
            },
            
            # Configuraciones de sincronización
            "sync": {
                "enabled": False,
                "server_url": "",
                "api_key": "",
                "sync_interval_minutes": 30,
                "offline_mode": True
            },
            
            # Configuraciones de hardware
            "hardware": {
                "barcode_scanner": {
                    "enabled": True,
                    "port": "auto",
                    "prefix": "",
                    "suffix": ""
                },
                "cash_drawer": {
                    "enabled": False,
                    "port": "COM1",
                    "open_command": ""
                },
                "scale": {
                    "enabled": False,
                    "port": "COM2",
                    "brand": "toledo",  # toledo, systel, other
                    "model": ""
                }
            },
            
            # Configuraciones de seguridad
            "security": {
                "session_timeout_minutes": 480,  # 8 horas
                "password_min_length": 6,
                "lock_after_attempts": 5,
                "audit_log": True
            },
            
            # Configuraciones de reportes
            "reports": {
                "default_export_format": "pdf",  # pdf, excel, csv
                "include_charts": True,
                "auto_save_path": "exports"
            }
        }
    
    def load_from_file(self) -> bool:
        """Cargar configuraciones desde archivo"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_settings = json.load(f)
                
                # Fusionar configuraciones (mantener estructura por defecto)
                self._merge_settings(self.settings, file_settings)
                logger.info(f"Configuraciones cargadas desde {self.config_file}")
                return True
            else:
                logger.info("Archivo de configuración no existe, usando valores por defecto")
                self.save_to_file()  # Crear archivo con valores por defecto
                return False
        except Exception as e:
            logger.error(f"Error cargando configuraciones: {e}")
            return False
    
    def save_to_file(self) -> bool:
        """Guardar configuraciones en archivo"""
        try:
            # Crear directorio si no existe
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            
            logger.info(f"Configuraciones guardadas en {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error guardando configuraciones: {e}")
            return False
    
    def _merge_settings(self, default: Dict, file_settings: Dict):
        """Fusionar configuraciones manteniendo estructura por defecto"""
        for key, value in file_settings.items():
            if key in default:
                if isinstance(value, dict) and isinstance(default[key], dict):
                    self._merge_settings(default[key], value)
                else:
                    default[key] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Obtener valor de configuración usando notación de punto
        Ejemplo: get('backup.enabled') o get('database.sqlite_path')
        """
        keys = key_path.split('.')
        value = self.settings
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> bool:
        """
        Establecer valor de configuración usando notación de punto
        Ejemplo: set('backup.enabled', True)
        """
        keys = key_path.split('.')
        settings = self.settings
        
        try:
            # Navegar hasta el penúltimo nivel
            for key in keys[:-1]:
                if key not in settings:
                    settings[key] = {}
                settings = settings[key]
            
            # Establecer el valor final
            settings[keys[-1]] = value
            return True
        except Exception as e:
            logger.error(f"Error estableciendo configuración {key_path}: {e}")
            return False
    
    def get_database_path(self) -> str:
        """Obtener ruta completa de la base de datos"""
        db_path = self.get('database.sqlite_path')
        if not os.path.isabs(db_path):
            # Ruta relativa, convertir a absoluta
            root_dir = Path(__file__).parent.parent
            db_path = root_dir / db_path
        return str(db_path)
    
    def get_backup_path(self) -> Path:
        """Obtener ruta completa de backups"""
        backup_path = self.get('backup.backup_path')
        if not os.path.isabs(backup_path):
            root_dir = Path(__file__).parent.parent
            backup_path = root_dir / backup_path
        
        backup_path = Path(backup_path)
        backup_path.mkdir(parents=True, exist_ok=True)
        return backup_path
    
    def is_backup_enabled(self) -> bool:
        """Verificar si el backup está habilitado"""
        return self.get('backup.enabled', False) and self.get('backup.auto_backup', False)
    
    def get_backup_interval_seconds(self) -> int:
        """Obtener intervalo de backup en segundos"""
        hours = self.get('backup.backup_interval_hours', 24)
        return hours * 3600
    
    def update_ui_settings(self, **kwargs):
        """Actualizar configuraciones de UI"""
        for key, value in kwargs.items():
            self.set(f'ui.{key}', value)
        self.save_to_file()
    
    def update_company_info(self, **kwargs):
        """Actualizar información de la empresa"""
        for key, value in kwargs.items():
            self.set(f'company.{key}', value)
        self.save_to_file()
    
    def update_backup_settings(self, **kwargs):
        """Actualizar configuraciones de backup"""
        for key, value in kwargs.items():
            self.set(f'backup.{key}', value)
        self.save_to_file()
    
    def export_settings(self, file_path: str) -> bool:
        """Exportar configuraciones a un archivo"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error exportando configuraciones: {e}")
            return False
    
    def import_settings(self, file_path: str) -> bool:
        """Importar configuraciones desde un archivo"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_settings = json.load(f)
            
            # Hacer backup de configuraciones actuales
            backup_file = self.config_file.with_suffix('.bak')
            self.export_settings(str(backup_file))
            
            # Fusionar configuraciones importadas
            self._merge_settings(self.settings, imported_settings)
            self.save_to_file()
            
            logger.info(f"Configuraciones importadas desde {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error importando configuraciones: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Restaurar configuraciones por defecto"""
        try:
            # Hacer backup de configuraciones actuales
            backup_file = self.config_file.with_suffix('.bak')
            self.export_settings(str(backup_file))
            
            # Restaurar valores por defecto
            self.settings = self._load_default_settings()
            self.save_to_file()
            
            logger.info("Configuraciones restauradas a valores por defecto")
            return True
        except Exception as e:
            logger.error(f"Error restaurando configuraciones: {e}")
            return False