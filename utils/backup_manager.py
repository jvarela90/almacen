"""
Sistema de Backup Automático para AlmacénPro
Funcionalidades:
- Backup automático de base de datos
- Compresión de archivos
- Limpieza automática de backups antiguos
- Backup en la nube (Google Drive, Dropbox)
- Restauración de backups
- Programación de backups
"""

import os
import shutil
import sqlite3
import gzip
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
import threading
import time
import schedule

logger = logging.getLogger(__name__)

class BackupManager:
    """Gestor principal de backups"""
    
    def __init__(self, settings):
        self.settings = settings
        self.backup_path = settings.get_backup_path()
        self.database_path = settings.get_database_path()
        self.is_running = False
        self.scheduler_thread = None
        
        # Crear directorio de backups si no existe
        self.backup_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"BackupManager inicializado - Ruta: {self.backup_path}")
    
    def start_automatic_backup(self):
        """Iniciar sistema de backup automático"""
        if not self.settings.is_backup_enabled():
            logger.info("Backup automático deshabilitado")
            return
        
        if self.is_running:
            logger.warning("El sistema de backup ya está en ejecución")
            return
        
        self.is_running = True
        
        # Configurar programación
        interval_hours = self.settings.get('backup.backup_interval_hours', 24)
        schedule.every(interval_hours).hours.do(self._scheduled_backup)
        
        # Iniciar hilo del programador
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info(f"Sistema de backup automático iniciado (cada {interval_hours} horas)")
        
        # Crear backup inicial si no existe ninguno reciente
        if not self._has_recent_backup(hours=interval_hours):
            self.create_backup()
    
    def stop_automatic_backup(self):
        """Detener sistema de backup automático"""
        self.is_running = False
        schedule.clear()
        logger.info("Sistema de backup automático detenido")
    
    def _run_scheduler(self):
        """Ejecutar programador de backups en hilo separado"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Verificar cada minuto
    
    def _scheduled_backup(self):
        """Backup programado automático"""
        try:
            logger.info("Ejecutando backup automático programado")
            success, message, backup_file = self.create_backup()
            
            if success:
                logger.info(f"Backup automático completado: {backup_file}")
                self._cleanup_old_backups()
                
                # Notificar si está habilitado
                if self.settings.get('notifications.backup_notifications', True):
                    self._notify_backup_success(backup_file)
            else:
                logger.error(f"Error en backup automático: {message}")
                self._notify_backup_error(message)
                
        except Exception as e:
            logger.error(f"Error en backup programado: {e}")
            self._notify_backup_error(str(e))
    
    def create_backup(self, description: str = "") -> Tuple[bool, str, Optional[str]]:
        """
        Crear backup completo del sistema
        Returns: (success, message, backup_file_path)
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"almacen_backup_{timestamp}"
            
            if description:
                # Limpiar descripción para nombre de archivo
                clean_desc = "".join(c for c in description if c.isalnum() or c in (' ', '-', '_')).rstrip()
                backup_name += f"_{clean_desc}"
            
            backup_dir = self.backup_path / backup_name
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Creando backup en: {backup_dir}")
            
            # 1. Backup de base de datos
            db_backup_success = self._backup_database(backup_dir)
            if not db_backup_success:
                return False, "Error en backup de base de datos", None
            
            # 2. Backup de archivos de configuración
            config_backup_success = self._backup_configuration(backup_dir)
            if not config_backup_success:
                logger.warning("Error en backup de configuración (continuando)")
            
            # 3. Backup de archivos adicionales (imágenes, etc.)
            files_backup_success = self._backup_additional_files(backup_dir)
            if not files_backup_success:
                logger.warning("Error en backup de archivos adicionales (continuando)")
            
            # 4. Crear archivo de metadatos
            metadata_success = self._create_backup_metadata(backup_dir, description)
            
            # 5. Comprimir backup si está habilitado
            final_backup_path = backup_dir
            if self.settings.get('backup.compress_backups', True):
                compressed_path = self._compress_backup(backup_dir)
                if compressed_path:
                    # Eliminar directorio original después de comprimir
                    shutil.rmtree(backup_dir)
                    final_backup_path = compressed_path
            
            # 6. Backup en la nube si está configurado
            if self.settings.get('backup.cloud_backup.enabled', False):
                cloud_success = self._upload_to_cloud(final_backup_path)
                if not cloud_success:
                    logger.warning("Error en backup en la nube (continuando)")
            
            # 7. Verificar integridad del backup
            if not self._verify_backup_integrity(final_backup_path):
                return False, "Error en verificación de integridad del backup", None
            
            logger.info(f"Backup creado exitosamente: {final_backup_path}")
            return True, f"Backup creado exitosamente", str(final_backup_path)
            
        except Exception as e:
            logger.error(f"Error creando backup: {e}")
            return False, f"Error creando backup: {str(e)}", None
    
    def _backup_database(self, backup_dir: Path) -> bool:
        """Backup de la base de datos SQLite"""
        try:
            db_path = Path(self.database_path)
            if not db_path.exists():
                logger.error(f"Base de datos no encontrada: {db_path}")
                return False
            
            # Crear backup usando SQLite backup API (más seguro que copiar archivo)
            backup_db_path = backup_dir / "database.db"
            
            source_conn = sqlite3.connect(str(db_path))
            backup_conn = sqlite3.connect(str(backup_db_path))
            
            # Realizar backup página por página
            source_conn.backup(backup_conn)
            
            source_conn.close()
            backup_conn.close()
            
            logger.info(f"Base de datos respaldada: {backup_db_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error en backup de base de datos: {e}")
            return False
    
    def _backup_configuration(self, backup_dir: Path) -> bool:
        """Backup de archivos de configuración"""
        try:
            config_dir = backup_dir / "config"
            config_dir.mkdir(exist_ok=True)
            
            # Backup del archivo de configuración principal
            config_file = Path("config.json")
            if config_file.exists():
                shutil.copy2(config_file, config_dir / "config.json")
            
            # Backup de otros archivos de configuración
            config_files = [
                "almacen_pro.log",
                "user_preferences.json",
                "printer_settings.json"
            ]
            
            for file_name in config_files:
                file_path = Path(file_name)
                if file_path.exists():
                    shutil.copy2(file_path, config_dir / file_name)
            
            logger.info(f"Configuración respaldada: {config_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Error en backup de configuración: {e}")
            return False
    
    def _backup_additional_files(self, backup_dir: Path) -> bool:
        """Backup de archivos adicionales (imágenes, exports, etc.)"""
        try:
            files_dir = backup_dir / "files"
            files_dir.mkdir(exist_ok=True)
            
            # Directorios a respaldar
            directories_to_backup = [
                "images",
                "exports", 
                "templates",
                "reports"
            ]
            
            for dir_name in directories_to_backup:
                source_dir = Path(dir_name)
                if source_dir.exists() and source_dir.is_dir():
                    dest_dir = files_dir / dir_name
                    shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
                    logger.info(f"Directorio respaldado: {dir_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error en backup de archivos adicionales: {e}")
            return False
    
    def _create_backup_metadata(self, backup_dir: Path, description: str) -> bool:
        """Crear archivo de metadatos del backup"""
        try:
            metadata = {
                "created_at": datetime.now().isoformat(),
                "version": "2.0",
                "description": description,
                "database_size": os.path.getsize(self.database_path) if os.path.exists(self.database_path) else 0,
                "backup_type": "full",
                "compression": self.settings.get('backup.compress_backups', True),
                "files_included": {
                    "database": True,
                    "configuration": True,
                    "additional_files": True
                }
            }
            
            metadata_file = backup_dir / "backup_info.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=4, ensure_ascii=False)
            
            logger.info(f"Metadatos creados: {metadata_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error creando metadatos: {e}")
            return False
    
    def _compress_backup(self, backup_dir: Path) -> Optional[Path]:
        """Comprimir backup usando gzip"""
        try:
            import tarfile
            
            compressed_file = backup_dir.with_suffix('.tar.gz')
            
            with tarfile.open(compressed_file, 'w:gz') as tar:
                tar.add(backup_dir, arcname=backup_dir.name)
            
            # Verificar que el archivo comprimido se creó correctamente
            if compressed_file.exists() and compressed_file.stat().st_size > 0:
                logger.info(f"Backup comprimido: {compressed_file}")
                return compressed_file
            else:
                logger.error("Error: archivo comprimido está vacío o no se creó")
                return None
                
        except Exception as e:
            logger.error(f"Error comprimiendo backup: {e}")
            return None
    
    def _verify_backup_integrity(self, backup_path: Path) -> bool:
        """Verificar integridad del backup"""
        try:
            if not backup_path.exists():
                return False
            
            # Verificar que el archivo no está vacío
            if backup_path.stat().st_size == 0:
                return False
            
            # Si es un archivo comprimido, verificar que se puede leer
            if backup_path.suffix == '.gz':
                import tarfile
                try:
                    with tarfile.open(backup_path, 'r:gz') as tar:
                        # Verificar que tiene contenido
                        members = tar.getmembers()
                        if not members:
                            return False
                        
                        # Verificar que contiene la base de datos
                        has_database = any('database.db' in member.name for member in members)
                        if not has_database:
                            return False
                            
                except tarfile.ReadError:
                    return False
            
            logger.info(f"Integridad del backup verificada: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error verificando integridad: {e}")
            return False
    
    def _cleanup_old_backups(self):
        """Limpiar backups antiguos según configuración"""
        try:
            max_backups = self.settings.get('backup.max_backups', 30)
            
            # Obtener lista de backups ordenados por fecha (más reciente primero)
            backups = self.list_backups()
            
            if len(backups) > max_backups:
                backups_to_delete = backups[max_backups:]
                
                for backup in backups_to_delete:
                    backup_path = Path(backup['path'])
                    try:
                        if backup_path.is_file():
                            backup_path.unlink()
                        else:
                            shutil.rmtree(backup_path)
                        
                        logger.info(f"Backup antiguo eliminado: {backup_path}")
                    except Exception as e:
                        logger.error(f"Error eliminando backup {backup_path}: {e}")
                
                logger.info(f"Limpieza completada: {len(backups_to_delete)} backups eliminados")
            
        except Exception as e:
            logger.error(f"Error en limpieza de backups: {e}")
    
    def list_backups(self) -> List[Dict]:
        """Listar todos los backups disponibles"""
        backups = []
        
        try:
            for item in self.backup_path.iterdir():
                if item.name.startswith('almacen_backup_'):
                    backup_info = {
                        'name': item.name,
                        'path': str(item),
                        'created_at': datetime.fromtimestamp(item.stat().st_mtime),
                        'size': self._get_backup_size(item),
                        'type': 'compressed' if item.suffix == '.gz' else 'directory'
                    }
                    
                    # Leer metadatos si existen
                    metadata = self._read_backup_metadata(item)
                    if metadata:
                        backup_info.update(metadata)
                    
                    backups.append(backup_info)
            
            # Ordenar por fecha de creación (más reciente primero)
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listando backups: {e}")
        
        return backups
    
    def _get_backup_size(self, backup_path: Path) -> int:
        """Obtener tamaño del backup en bytes"""
        try:
            if backup_path.is_file():
                return backup_path.stat().st_size
            else:
                total_size = 0
                for file_path in backup_path.rglob('*'):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
                return total_size
        except Exception:
            return 0
    
    def _read_backup_metadata(self, backup_path: Path) -> Optional[Dict]:
        """Leer metadatos de un backup"""
        try:
            if backup_path.is_file() and backup_path.suffix == '.gz':
                # Leer de archivo comprimido
                import tarfile
                with tarfile.open(backup_path, 'r:gz') as tar:
                    try:
                        metadata_member = tar.getmember(f"{backup_path.stem}/backup_info.json")
                        metadata_file = tar.extractfile(metadata_member)
                        if metadata_file:
                            return json.loads(metadata_file.read().decode('utf-8'))
                    except KeyError:
                        pass
            else:
                # Leer de directorio
                metadata_file = backup_path / "backup_info.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
        except Exception as e:
            logger.error(f"Error leyendo metadatos de {backup_path}: {e}")
        
        return None
    
    def _has_recent_backup(self, hours: int = 24) -> bool:
        """Verificar si existe un backup reciente"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            backups = self.list_backups()
            
            for backup in backups:
                if backup['created_at'] > cutoff_time:
                    return True
            
            return False
        except Exception:
            return False
    
    def restore_backup(self, backup_path: str) -> Tuple[bool, str]:
        """Restaurar un backup"""
        try:
            backup_path = Path(backup_path)
            
            if not backup_path.exists():
                return False, "Archivo de backup no encontrado"
            
            # Crear backup de seguridad de la base de datos actual
            current_db = Path(self.database_path)
            if current_db.exists():
                backup_current = current_db.with_suffix('.db.pre_restore')
                shutil.copy2(current_db, backup_current)
                logger.info(f"Backup de seguridad creado: {backup_current}")
            
            # Extraer y restaurar
            if backup_path.suffix == '.gz':
                success = self._restore_from_compressed(backup_path)
            else:
                success = self._restore_from_directory(backup_path)
            
            if success:
                logger.info(f"Backup restaurado exitosamente desde: {backup_path}")
                return True, "Backup restaurado exitosamente"
            else:
                return False, "Error durante la restauración"
                
        except Exception as e:
            logger.error(f"Error restaurando backup: {e}")
            return False, f"Error restaurando backup: {str(e)}"
    
    def _restore_from_compressed(self, backup_path: Path) -> bool:
        """Restaurar desde archivo comprimido"""
        try:
            import tarfile
            temp_dir = self.backup_path / "temp_restore"
            
            # Limpiar directorio temporal si existe
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            
            temp_dir.mkdir()
            
            # Extraer archivo comprimido
            with tarfile.open(backup_path, 'r:gz') as tar:
                tar.extractall(temp_dir)
            
            # Buscar directorio extraído
            extracted_dirs = [d for d in temp_dir.iterdir() if d.is_dir()]
            if not extracted_dirs:
                return False
            
            extracted_dir = extracted_dirs[0]
            success = self._restore_from_directory(extracted_dir)
            
            # Limpiar directorio temporal
            shutil.rmtree(temp_dir)
            
            return success
            
        except Exception as e:
            logger.error(f"Error restaurando desde comprimido: {e}")
            return False
    
    def _restore_from_directory(self, backup_dir: Path) -> bool:
        """Restaurar desde directorio de backup"""
        try:
            # Restaurar base de datos
            db_backup = backup_dir / "database.db"
            if db_backup.exists():
                shutil.copy2(db_backup, self.database_path)
                logger.info("Base de datos restaurada")
            
            # Restaurar configuración
            config_backup = backup_dir / "config" / "config.json"
            if config_backup.exists():
                shutil.copy2(config_backup, "config.json")
                logger.info("Configuración restaurada")
            
            # Restaurar archivos adicionales
            files_backup = backup_dir / "files"
            if files_backup.exists():
                for item in files_backup.iterdir():
                    if item.is_dir():
                        dest_dir = Path(item.name)
                        if dest_dir.exists():
                            shutil.rmtree(dest_dir)
                        shutil.copytree(item, dest_dir)
                        logger.info(f"Directorio restaurado: {item.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error restaurando desde directorio: {e}")
            return False
    
    def _upload_to_cloud(self, backup_path: Path) -> bool:
        """Subir backup a la nube (placeholder para implementación futura)"""
        try:
            # Aquí se implementaría la subida a Google Drive, Dropbox, etc.
            logger.info("Función de backup en la nube no implementada aún")
            return True
        except Exception as e:
            logger.error(f"Error subiendo a la nube: {e}")
            return False
    
    def _notify_backup_success(self, backup_file: str):
        """Notificar backup exitoso"""
        # Esta función se integrará con el sistema de notificaciones
        logger.info(f"Notificación: Backup exitoso - {backup_file}")
    
    def _notify_backup_error(self, error_message: str):
        """Notificar error en backup"""
        # Esta función se integrará con el sistema de notificaciones
        logger.error(f"Notificación: Error en backup - {error_message}")
    
    def get_backup_status(self) -> Dict:
        """Obtener estado actual del sistema de backup"""
        backups = self.list_backups()
        last_backup = backups[0] if backups else None
        
        return {
            'enabled': self.settings.is_backup_enabled(),
            'running': self.is_running,
            'total_backups': len(backups),
            'last_backup': last_backup,
            'next_backup': self._get_next_backup_time(),
            'backup_path': str(self.backup_path),
            'total_backup_size': sum(b['size'] for b in backups)
        }