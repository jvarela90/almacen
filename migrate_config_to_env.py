#!/usr/bin/env python3
"""
Script de migración de config.json a variables de entorno (.env)
AlmacénPro v2.0

Este script ayuda a migrar la configuración existente desde config.json 
hacia el nuevo sistema basado en variables de entorno.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

def load_config_json(file_path: str = 'config.json') -> Dict[str, Any]:
    """Cargar configuración desde config.json"""
    config_path = Path(file_path)
    
    if not config_path.exists():
        print(f"❌ Archivo {file_path} no encontrado")
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"✅ Cargado config.json ({config_path.stat().st_size} bytes)")
        return config
    except Exception as e:
        print(f"❌ Error cargando {file_path}: {e}")
        return {}

def convert_to_env_vars(config: Dict[str, Any]) -> List[str]:
    """Convertir configuración de config.json a variables de entorno"""
    env_vars = []
    
    # Header
    env_vars.extend([
        "# AlmacénPro v2.0 - Variables de Entorno (Migradas desde config.json)",
        "# Generado automáticamente - revise y ajuste según sea necesario",
        ""
    ])
    
    # Database configuration
    if 'database' in config:
        env_vars.extend([
            "# ============================================================================",
            "# BASE DE DATOS", 
            "# ============================================================================"
        ])
        
        db = config['database']
        env_vars.append(f"DATABASE_TYPE={db.get('type', 'sqlite')}")
        
        if 'sqlite_path' in db:
            env_vars.append(f"SQLITE_PATH={db['sqlite_path']}")
        elif 'path' in db:
            env_vars.append(f"SQLITE_PATH={db['path']}")
            
        if 'postgresql' in db:
            pg = db['postgresql']
            env_vars.extend([
                f"POSTGRES_HOST={pg.get('host', 'localhost')}",
                f"POSTGRES_PORT={pg.get('port', 5432)}",
                f"POSTGRES_DATABASE={pg.get('database', 'almacen_pro')}",
                f"POSTGRES_USERNAME={pg.get('username', '')}",
                f"POSTGRES_PASSWORD={pg.get('password', '')}"
            ])
        env_vars.append("")
    
    # Security configuration
    if 'security' in config:
        env_vars.extend([
            "# ============================================================================", 
            "# SEGURIDAD",
            "# ============================================================================"
        ])
        
        sec = config['security']
        env_vars.extend([
            "SECRET_KEY=change-this-in-production",  # No migrar la clave actual
            f"SESSION_TIMEOUT_MINUTES={sec.get('session_timeout_minutes', 480)}",
            f"PASSWORD_MIN_LENGTH={sec.get('password_min_length', 6)}",
            f"MAX_LOGIN_ATTEMPTS={sec.get('max_login_attempts', 3)}",
            f"LOCK_AFTER_ATTEMPTS={sec.get('lock_after_attempts', 5)}",
            f"AUDIT_LOG={str(sec.get('audit_log', True)).lower()}",
            ""
        ])
    
    # Company configuration
    if 'company' in config:
        env_vars.extend([
            "# ============================================================================",
            "# EMPRESA", 
            "# ============================================================================"
        ])
        
        comp = config['company']
        env_vars.extend([
            f"COMPANY_NAME={comp.get('name', 'Mi Almacén')}",
            f"COMPANY_ADDRESS={comp.get('address', '')}",
            f"COMPANY_PHONE={comp.get('phone', '')}",
            f"COMPANY_EMAIL={comp.get('email', '')}",
            f"COMPANY_CUIT={comp.get('cuit', '')}",
            f"COMPANY_LOGO_PATH={comp.get('logo_path', '')}",
            ""
        ])
    
    # Backup configuration
    if 'backup' in config:
        env_vars.extend([
            "# ============================================================================",
            "# BACKUP",
            "# ============================================================================"
        ])
        
        backup = config['backup']
        env_vars.extend([
            f"BACKUP_ENABLED={str(backup.get('enabled', True)).lower()}",
            f"AUTO_BACKUP={str(backup.get('auto_backup', True)).lower()}",
            f"BACKUP_INTERVAL_HOURS={backup.get('backup_interval_hours', 24)}",
            f"BACKUP_PATH={backup.get('backup_path', 'backups')}",
            f"MAX_BACKUPS={backup.get('max_backups', 30)}",
            f"COMPRESS_BACKUPS={str(backup.get('compress_backups', True)).lower()}"
        ])
        
        if 'cloud_backup' in backup:
            cloud = backup['cloud_backup']
            env_vars.extend([
                "",
                "# Cloud Backup",
                f"CLOUD_BACKUP_ENABLED={str(cloud.get('enabled', False)).lower()}",
                f"CLOUD_BACKUP_PROVIDER={cloud.get('provider', 'google_drive')}",
                f"CLOUD_BACKUP_CREDENTIALS_FILE={cloud.get('credentials_file', '')}",
                f"CLOUD_BACKUP_REMOTE_FOLDER={cloud.get('remote_folder', 'AlmacenPro_Backups')}"
            ])
        env_vars.append("")
    
    # Tickets configuration
    if 'tickets' in config:
        env_vars.extend([
            "# ============================================================================",
            "# IMPRESIÓN Y TICKETS",
            "# ============================================================================"
        ])
        
        tickets = config['tickets']
        env_vars.extend([
            f"PRINTER_NAME={tickets.get('printer_name', '')}",
            f"PAPER_WIDTH={tickets.get('paper_width', 80)}",
            f"AUTO_PRINT={str(tickets.get('auto_print', False)).lower()}",
            f"COPY_COUNT={tickets.get('copy_count', 1)}",
            f"FOOTER_MESSAGE={tickets.get('footer_message', '¡Gracias por su compra!')}",
            f"INCLUDE_LOGO={str(tickets.get('include_logo', False)).lower()}",
            ""
        ])
    
    # UI configuration
    if 'ui' in config:
        env_vars.extend([
            "# ============================================================================",
            "# INTERFAZ DE USUARIO",
            "# ============================================================================"
        ])
        
        ui = config['ui']
        env_vars.extend([
            f"UI_THEME={ui.get('theme', 'default')}",
            f"UI_LANGUAGE={ui.get('language', 'es')}",
            f"UI_FONT_SIZE={ui.get('font_size', 9)}",
            f"WINDOW_MAXIMIZED={str(ui.get('window_maximized', True)).lower()}"
        ])
        
        if 'last_window_size' in ui:
            size = ui['last_window_size']
            if isinstance(size, list) and len(size) >= 2:
                env_vars.extend([
                    f"LAST_WINDOW_WIDTH={size[0]}",
                    f"LAST_WINDOW_HEIGHT={size[1]}"
                ])
                
        if 'last_window_position' in ui:
            pos = ui['last_window_position'] 
            if isinstance(pos, list) and len(pos) >= 2:
                env_vars.extend([
                    f"LAST_WINDOW_X={pos[0]}",
                    f"LAST_WINDOW_Y={pos[1]}"
                ])
        env_vars.append("")
    
    # Notifications configuration
    if 'notifications' in config:
        env_vars.extend([
            "# ============================================================================",
            "# NOTIFICACIONES", 
            "# ============================================================================"
        ])
        
        notif = config['notifications']
        env_vars.extend([
            f"NOTIFICATIONS_ENABLED={str(notif.get('enabled', True)).lower()}",
            f"LOW_STOCK_ALERTS={str(notif.get('low_stock_alerts', True)).lower()}",
            f"DAILY_SALES_SUMMARY={str(notif.get('daily_sales_summary', True)).lower()}",
            f"BACKUP_NOTIFICATIONS={str(notif.get('backup_notifications', True)).lower()}",
            f"SYSTEM_NOTIFICATIONS={str(notif.get('system_notifications', True)).lower()}",
            ""
        ])
    
    # Hardware configuration
    if 'hardware' in config:
        env_vars.extend([
            "# ============================================================================",
            "# HARDWARE EXTERNO",
            "# ============================================================================"
        ])
        
        hw = config['hardware']
        
        if 'barcode_scanner' in hw:
            scanner = hw['barcode_scanner']
            env_vars.extend([
                f"BARCODE_SCANNER_ENABLED={str(scanner.get('enabled', True)).lower()}",
                f"BARCODE_SCANNER_PORT={scanner.get('port', 'auto')}",
                f"BARCODE_SCANNER_PREFIX={scanner.get('prefix', '')}",
                f"BARCODE_SCANNER_SUFFIX={scanner.get('suffix', '')}"
            ])
            
        if 'cash_drawer' in hw:
            drawer = hw['cash_drawer']
            env_vars.extend([
                "",
                f"CASH_DRAWER_ENABLED={str(drawer.get('enabled', False)).lower()}",
                f"CASH_DRAWER_PORT={drawer.get('port', 'COM1')}",
                f"CASH_DRAWER_OPEN_COMMAND={drawer.get('open_command', '')}"
            ])
            
        if 'scale' in hw:
            scale = hw['scale']
            env_vars.extend([
                "",
                f"SCALE_ENABLED={str(scale.get('enabled', False)).lower()}",
                f"SCALE_PORT={scale.get('port', 'COM2')}",
                f"SCALE_BRAND={scale.get('brand', 'toledo')}",
                f"SCALE_MODEL={scale.get('model', '')}"
            ])
        env_vars.append("")
    
    # Sync configuration
    if 'sync' in config:
        env_vars.extend([
            "# ============================================================================",
            "# SINCRONIZACIÓN",
            "# ============================================================================"
        ])
        
        sync = config['sync']
        env_vars.extend([
            f"SYNC_ENABLED={str(sync.get('enabled', False)).lower()}",
            f"SYNC_SERVER_URL={sync.get('server_url', '')}",
            f"SYNC_API_KEY={sync.get('api_key', '')}",
            f"SYNC_INTERVAL_MINUTES={sync.get('sync_interval_minutes', 30)}",
            f"OFFLINE_MODE={str(sync.get('offline_mode', True)).lower()}",
            ""
        ])
    
    # Reports configuration
    if 'reports' in config:
        env_vars.extend([
            "# ============================================================================",
            "# REPORTES",
            "# ============================================================================"
        ])
        
        reports = config['reports']
        env_vars.extend([
            f"DEFAULT_EXPORT_FORMAT={reports.get('default_export_format', 'pdf')}",
            f"INCLUDE_CHARTS={str(reports.get('include_charts', True)).lower()}",
            f"AUTO_SAVE_PATH={reports.get('auto_save_path', 'exports')}",
            ""
        ])
    
    # Development settings
    env_vars.extend([
        "# ============================================================================",
        "# DESARROLLO",
        "# ============================================================================",
        "DEBUG=false",
        "LOG_LEVEL=INFO", 
        "ENABLE_SQL_LOGGING=false"
    ])
    
    return env_vars

def save_env_file(env_vars: List[str], file_path: str = '.env') -> bool:
    """Guardar variables de entorno a archivo .env"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(env_vars))
        
        print(f"✅ Archivo {file_path} creado exitosamente")
        print(f"📄 {len(env_vars)} líneas escritas")
        return True
        
    except Exception as e:
        print(f"❌ Error escribiendo {file_path}: {e}")
        return False

def backup_existing_files():
    """Hacer backup de archivos existentes"""
    files_to_backup = ['.env', 'config.json']
    backups_made = []
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            backup_path = f"{file_path}.backup"
            try:
                # Si ya existe backup, agregar timestamp
                if os.path.exists(backup_path):
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_path = f"{file_path}.backup_{timestamp}"
                
                os.rename(file_path, backup_path)
                backups_made.append(backup_path)
                print(f"📋 Backup creado: {backup_path}")
            except Exception as e:
                print(f"⚠️ Error creando backup de {file_path}: {e}")
    
    return backups_made

def main():
    """Función principal del script de migración"""
    print("🚀 AlmacénPro v2.0 - Migración config.json → .env")
    print("=" * 60)
    
    # Verificar si .env ya existe
    if os.path.exists('.env'):
        response = input("⚠️ El archivo .env ya existe. ¿Sobrescribir? (s/N): ")
        if response.lower() not in ['s', 'si', 'y', 'yes']:
            print("❌ Operación cancelada")
            return
    
    # Cargar config.json
    config = load_config_json()
    if not config:
        print("❌ No se pudo cargar config.json. Creando .env con valores por defecto...")
        # Crear .env.example como base
        if os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
            print("✅ Copiado .env.example → .env")
        return
    
    print(f"📊 Secciones encontradas en config.json: {list(config.keys())}")
    
    # Crear backup de archivos existentes
    print("\n📋 Creando backups...")
    backup_existing_files()
    
    # Convertir configuración
    print("\n🔄 Convirtiendo configuración...")
    env_vars = convert_to_env_vars(config)
    
    # Guardar archivo .env
    print("\n💾 Guardando archivo .env...")
    if save_env_file(env_vars):
        print("\n✅ ¡Migración completada exitosamente!")
        print("\n📋 Próximos pasos:")
        print("1. Revisar y ajustar el archivo .env generado")
        print("2. Cambiar SECRET_KEY por un valor seguro")
        print("3. Configurar credenciales de base de datos si usa PostgreSQL")
        print("4. Probar la aplicación con la nueva configuración")
        print("5. Una vez validado, puede eliminar config.json")
        
        print(f"\n📁 Archivos generados:")
        print(f"   - .env (configuración principal)")
        if os.path.exists('config.json.backup'):
            print(f"   - config.json.backup (respaldo)")
            
    else:
        print("❌ Error en la migración")

if __name__ == "__main__":
    main()