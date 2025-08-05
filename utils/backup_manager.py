"""
Gestor de Backup para AlmacénPro
Sistema completo de backup automático con compresión, limpieza y restauración
"""

import os
import shutil
import zipfile
import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import hashlib

logger = logging.getLogger(__name__)

class BackupManager:
    """Gestor principal de backups del sistema"""
    
    def __init__(self, database_path: str):
        self.database_path = Path(database_path)
        self.backup_directory = Path("backups")
        self.config_file = Path("backup_config.json")
        
        # Configuración por defecto
        self.default_config = {
            "auto_backup_enabled": True,
            "backup_interval_hours": 24,
            "keep_backups_days": 30,
            "compress_backups": True,
            "include_images": True,
            "include_logs": False,
            "max_backup_size_mb": 500,
            "backup_location": str(self.backup_directory),
            "notification_on_success": True,
            "notification_on_error": True
        }
        
        self.config = self.load_config()
        self.backup_thread = None
        self.auto_backup_timer = None
        
        # Crear directorio de backups
        self.backup_directory.mkdir(exist_ok=True)
        
        # Iniciar backup automático si está habilitado
        if self.config.get("auto_backup_enabled", True):
            self.start_automatic_backup()
        
        self.logger = logging.getLogger(__name__)
    
    def load_config(self) -> Dict:
        """Cargar configuración de backup"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Combinar con configuración por defecto
                merged_config = self.default_config.copy()
                merged_config.update(config)
                return merged_config
            else:
                return self.default_config.copy()
                
        except Exception as e:
            self.logger.error(f"Error cargando configuración de backup: {e}")
            return self.default_config.copy()
    
    def save_config(self):
        """Guardar configuración de backup"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Error guardando configuración de backup: {e}")
    
    def create_manual_backup(self, description: str = None) -> Optional[Path]:
        """Crear backup manual"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_manual_{timestamp}"
            
            if description:
                backup_name += f"_{description}"
            
            return self._create_backup(backup_name, manual=True)
            
        except Exception as e:
            self.logger.error(f"Error creando backup manual: {e}")
            return None
    
    def create_automatic_backup(self) -> Optional[Path]:
        """Crear backup automático"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_auto_{timestamp}"
            
            return self._create_backup(backup_name, manual=False)
            
        except Exception as e:
            self.logger.error(f"Error creando backup automático: {e}")
            return None
    
    def _create_backup(self, backup_name: str, manual: bool = False) -> Optional[Path]:
        """Crear backup interno"""
        try:
            # Crear directorio temporal para el backup
            backup_temp_dir = self.backup_directory / f"temp_{backup_name}"
            backup_temp_dir.mkdir(exist_ok=True)
            
            # Metadatos del backup
            backup_metadata = {
                "backup_name": backup_name,
                "created_at": datetime.now().isoformat(),
                "type": "manual" if manual else "automatic",
                "database_size": self.database_path.stat().st_size if self.database_path.exists() else 0,
                "version": "2.0.0",
                "files_included": []
            }
            
            try:
                # 1. Copiar base de datos
                if self.database_path.exists():
                    db_backup_path = backup_temp_dir / "database.db"
                    shutil.copy2(self.database_path, db_backup_path)
                    backup_metadata["files_included"].append("database.db")
                    self.logger.info("Base de datos copiada al backup")
                
                # 2. Copiar configuraciones
                config_backup_dir = backup_temp_dir / "config"
                config_backup_dir.mkdir(exist_ok=True)
                
                config_files = ["config.json", "backup_config.json"]
                for config_file in config_files:
                    if Path(config_file).exists():
                        shutil.copy2(config_file, config_backup_dir / config_file)
                        backup_metadata["files_included"].append(f"config/{config_file}")
                
                # 3. Copiar imágenes (si está habilitado)
                if self.config.get("include_images", True):
                    images_dir = Path("images")
                    if images_dir.exists():
                        backup_images_dir = backup_temp_dir / "images"
                        shutil.copytree(images_dir, backup_images_dir, dirs_exist_ok=True)
                        backup_metadata["files_included"].append("images/")
                
                # 4. Copiar logs (si está habilitado)
                if self.config.get("include_logs", False):
                    logs_dir = Path("logs")
                    if logs_dir.exists():
                        backup_logs_dir = backup_temp_dir / "logs"
                        shutil.copytree(logs_dir, backup_logs_dir, dirs_exist_ok=True)
                        backup_metadata["files_included"].append("logs/")
                
                # 5. Crear archivo de metadatos
                metadata_file = backup_temp_dir / "backup_metadata.json"
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(backup_metadata, f, indent=4, ensure_ascii=False)
                
                # 6. Comprimir si está habilitado
                if self.config.get("compress_backups", True):
                    backup_file = self.backup_directory / f"{backup_name}.zip"
                    self._compress_backup(backup_temp_dir, backup_file)
                    final_backup_path = backup_file
                else:
                    final_backup_dir = self.backup_directory / backup_name
                    if final_backup_dir.exists():
                        shutil.rmtree(final_backup_dir)
                    shutil.move(backup_temp_dir, final_backup_dir)
                    final_backup_path = final_backup_dir
                
                # 7. Limpiar directorio temporal
                if backup_temp_dir.exists():
                    shutil.rmtree(backup_temp_dir)
                
                # 8. Verificar integridad del backup
                if self._verify_backup_integrity(final_backup_path):
                    # 9. Actualizar registro de backups
                    self._update_backup_registry(backup_name, final_backup_path, backup_metadata)
                    
                    # 10. Limpiar backups antiguos
                    self.cleanup_old_backups()
                    
                    self.logger.info(f"Backup creado exitosamente: {final_backup_path}")
                    return final_backup_path
                else:
                    self.logger.error("Backup creado pero falló la verificación de integridad")
                    return None
                
            except Exception as e:
                # Limpiar en caso de error
                if backup_temp_dir.exists():
                    shutil.rmtree(backup_temp_dir)
                raise e
                
        except Exception as e:
            self.logger.error(f"Error en proceso de backup: {e}")
            return None
    
    def _compress_backup(self, source_dir: Path, output_file: Path):
        """Comprimir directorio de backup"""
        try:
            with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zip_file:
                for file_path in source_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(source_dir)
                        zip_file.write(file_path, arcname)
                        
            self.logger.info(f"Backup comprimido: {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error comprimiendo backup: {e}")
            raise e
    
    def _verify_backup_integrity(self, backup_path: Path) -> bool:
        """Verificar integridad del backup"""
        try:
            if backup_path.suffix == '.zip':
                # Verificar archivo ZIP
                with zipfile.ZipFile(backup_path, 'r') as zip_file:
                    # Verificar que no esté corrupto
                    bad_file = zip_file.testzip()
                    if bad_file:
                        self.logger.error(f"Archivo corrupto en backup: {bad_file}")
                        return False
                    
                    # Verificar que contiene archivos esenciales
                    required_files = ['database.db', 'backup_metadata.json']
                    zip_contents = zip_file.namelist()
                    
                    for required_file in required_files:
                        if not any(required_file in name for name in zip_contents):
                            self.logger.error(f"Archivo requerido faltante en backup: {required_file}")
                            return False
            else:
                # Verificar directorio
                if not backup_path.is_dir():
                    return False
                
                required_files = ['database.db', 'backup_metadata.json']
                for required_file in required_files:
                    if not (backup_path / required_file).exists():
                        self.logger.error(f"Archivo requerido faltante en backup: {required_file}")
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error verificando integridad del backup: {e}")
            return False
    
    def _update_backup_registry(self, backup_name: str, backup_path: Path, metadata: Dict):
        """Actualizar registro de backups"""
        try:
            registry_file = self.backup_directory / "backup_registry.json"
            
            # Cargar registro existente
            if registry_file.exists():
                with open(registry_file, 'r', encoding='utf-8') as f:
                    registry = json.load(f)
            else:
                registry = {"backups": []}
            
            # Agregar nuevo backup
            backup_info = {
                "name": backup_name,
                "path": str(backup_path),
                "size_bytes": backup_path.stat().st_size,
                "created_at": metadata["created_at"],
                "type": metadata["type"],
                "files_included": metadata["files_included"],
                "verified": True
            }
            
            registry["backups"].append(backup_info)
            
            # Guardar registro actualizado
            with open(registry_file, 'w', encoding='utf-8') as f:
                json.dump(registry, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Error actualizando registro de backups: {e}")
    
    def get_backup_list(self) -> List[Dict]:
        """Obtener lista de backups disponibles"""
        try:
            registry_file = self.backup_directory / "backup_registry.json"
            
            if registry_file.exists():
                with open(registry_file, 'r', encoding='utf-8') as f:
                    registry = json.load(f)
                return registry.get("backups", [])
            else:
                # Escanear directorio de backups para crear registro
                backups = []
                for backup_path in self.backup_directory.iterdir():
                    if backup_path.is_file() and backup_path.suffix == '.zip':
                        backups.append({
                            "name": backup_path.stem,
                            "path": str(backup_path),
                            "size_bytes": backup_path.stat().st_size,
                            "created_at": datetime.fromtimestamp(backup_path.stat().st_ctime).isoformat(),
                            "type": "manual" if "manual" in backup_path.name else "automatic",
                            "verified": None
                        })
                    elif backup_path.is_dir() and backup_path.name != "temp":
                        backups.append({
                            "name": backup_path.name,
                            "path": str(backup_path),
                            "size_bytes": sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file()),
                            "created_at": datetime.fromtimestamp(backup_path.stat().st_ctime).isoformat(),
                            "type": "manual" if "manual" in backup_path.name else "automatic",
                            "verified": None
                        })
                
                return sorted(backups, key=lambda x: x["created_at"], reverse=True)
                
        except Exception as e:
            self.logger.error(f"Error obteniendo lista de backups: {e}")
            return []
    
    def restore_backup(self, backup_path: str) -> bool:
        """Restaurar backup"""
        try:
            backup_path = Path(backup_path)
            
            if not backup_path.exists():
                self.logger.error(f"Backup no encontrado: {backup_path}")
                return False
            
            # Crear backup actual antes de restaurar
            current_backup = self.create_manual_backup("pre_restore")
            if not current_backup:
                self.logger.warning("No se pudo crear backup de seguridad antes de restaurar")
            
            if backup_path.suffix == '.zip':
                return self._restore_from_zip(backup_path)
            else:
                return self._restore_from_directory(backup_path)
                
        except Exception as e:
            self.logger.error(f"Error restaurando backup: {e}")
            return False
    
    def _restore_from_zip(self, backup_path: Path) -> bool:
        """Restaurar desde archivo comprimido"""
        try:
            # Crear directorio temporal
            temp_dir = self.backup_directory / f"temp_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            temp_dir.mkdir(exist_ok=True)
            
            # Extraer backup
            with zipfile.ZipFile(backup_path, 'r') as zip_file:
                zip_file.extractall(temp_dir)
            
            # Buscar directorio extraído
            extracted_dirs = [d for d in temp_dir.iterdir() if d.is_dir()]
            if not extracted_dirs:
                # Los archivos están en la raíz del temp_dir
                extracted_dir = temp_dir
            else:
                extracted_dir = extracted_dirs[0]
            
            success = self._restore_from_directory(extracted_dir)
            
            # Limpiar directorio temporal
            shutil.rmtree(temp_dir)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error restaurando desde comprimido: {e}")
            return False
    
    def _restore_from_directory(self, backup_dir: Path) -> bool:
        """Restaurar desde directorio de backup"""
        try:
            # Verificar integridad antes de restaurar
            if not self._verify_backup_integrity(backup_dir):
                self.logger.error("Backup corrupto, no se puede restaurar")
                return False
            
            # 1. Restaurar base de datos
            db_backup = backup_dir / "database.db"
            if db_backup.exists():
                # Hacer backup de la BD actual
                if self.database_path.exists():
                    backup_current_db = self.database_path.with_suffix('.db.backup')
                    shutil.copy2(self.database_path, backup_current_db)
                
                # Restaurar BD
                shutil.copy2(db_backup, self.database_path)
                self.logger.info("Base de datos restaurada")
            
            # 2. Restaurar configuraciones
            config_backup_dir = backup_dir / "config"
            if config_backup_dir.exists():
                for config_file in config_backup_dir.iterdir():
                    if config_file.is_file():
                        shutil.copy2(config_file, config_file.name)
                        self.logger.info(f"Configuración restaurada: {config_file.name}")
            
            # 3. Restaurar imágenes
            images_backup = backup_dir / "images"
            if images_backup.exists():
                images_dir = Path("images")
                if images_dir.exists():
                    shutil.rmtree(images_dir)
                shutil.copytree(images_backup, images_dir)
                self.logger.info("Imágenes restauradas")
            
            # 4. Restaurar logs (si existen)
            logs_backup = backup_dir / "logs"
            if logs_backup.exists():
                logs_dir = Path("logs")
                if logs_dir.exists():
                    shutil.rmtree(logs_dir)
                shutil.copytree(logs_backup, logs_dir)
                self.logger.info("Logs restaurados")
            
            self.logger.info(f"Backup restaurado exitosamente desde: {backup_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restaurando desde directorio: {e}")
            return False
    
    def delete_backup(self, backup_path: str) -> bool:
        """Eliminar backup"""
        try:
            backup_path = Path(backup_path)
            
            if not backup_path.exists():
                return False
            
            if backup_path.is_file():
                backup_path.unlink()
            else:
                shutil.rmtree(backup_path)
            
            # Actualizar registro
            self._remove_from_registry(str(backup_path))
            
            self.logger.info(f"Backup eliminado: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error eliminando backup: {e}")
            return False
    
    def _remove_from_registry(self, backup_path: str):
        """Remover backup del registro"""
        try:
            registry_file = self.backup_directory / "backup_registry.json"
            
            if not registry_file.exists():
                return
            
            with open(registry_file, 'r', encoding='utf-8') as f:
                registry = json.load(f)
            
            # Filtrar backup eliminado
            registry["backups"] = [
                backup for backup in registry["backups"]
                if backup["path"] != backup_path
            ]
            
            with open(registry_file, 'w', encoding='utf-8') as f:
                json.dump(registry, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Error removiendo backup del registro: {e}")
    
    def cleanup_old_backups(self):
        """Limpiar backups antiguos según configuración"""
        try:
            keep_days = self.config.get("keep_backups_days", 30)
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            
            backups = self.get_backup_list()
            deleted_count = 0
            
            for backup in backups:
                try:
                    backup_date = datetime.fromisoformat(backup["created_at"])
                    
                    # Solo eliminar backups automáticos antiguos
                    if backup_date < cutoff_date and backup["type"] == "automatic":
                        if self.delete_backup(backup["path"]):
                            deleted_count += 1
                            
                except Exception as e:
                    self.logger.warning(f"Error procesando backup para limpieza: {e}")
            
            if deleted_count > 0:
                self.logger.info(f"Limpieza completada: {deleted_count} backups antiguos eliminados")
                
        except Exception as e:
            self.logger.error(f"Error limpiando backups antiguos: {e}")
    
    def start_automatic_backup(self):
        """Iniciar backup automático"""
        try:
            if self.auto_backup_timer:
                self.stop_automatic_backup()
            
            interval_hours = self.config.get("backup_interval_hours", 24)
            interval_seconds = interval_hours * 3600
            
            self.auto_backup_timer = threading.Timer(interval_seconds, self._automatic_backup_callback)
            self.auto_backup_timer.daemon = True
            self.auto_backup_timer.start()
            
            self.logger.info(f"Backup automático iniciado (cada {interval_hours} horas)")
            
        except Exception as e:
            self.logger.error(f"Error iniciando backup automático: {e}")
    
    def stop_automatic_backup(self):
        """Detener backup automático"""
        if self.auto_backup_timer:
            self.auto_backup_timer.cancel()
            self.auto_backup_timer = None
            self.logger.info("Backup automático detenido")
    
    def _automatic_backup_callback(self):
        """Callback para backup automático"""
        try:
            self.logger.info("Iniciando backup automático")
            backup_path = self.create_automatic_backup()
            
            if backup_path:
                self.logger.info(f"Backup automático completado: {backup_path}")
            else:
                self.logger.error("Backup automático falló")
            
            # Programar próximo backup
            self.start_automatic_backup()
            
        except Exception as e:
            self.logger.error(f"Error en backup automático: {e}")
            # Intentar reprogramar
            self.start_automatic_backup()
    
    def get_backup_statistics(self) -> Dict:
        """Obtener estadísticas de backups"""
        try:
            backups = self.get_backup_list()
            
            total_backups = len(backups)
            manual_backups = len([b for b in backups if b["type"] == "manual"])
            automatic_backups = len([b for b in backups if b["type"] == "automatic"])
            total_size = sum(b["size_bytes"] for b in backups)
            
            # Último backup
            last_backup = None
            if backups:
                last_backup = max(backups, key=lambda x: x["created_at"])
            
            return {
                "total_backups": total_backups,
                "manual_backups": manual_backups,
                "automatic_backups": automatic_backups,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "last_backup": last_backup,
                "auto_backup_enabled": self.config.get("auto_backup_enabled", False),
                "backup_interval_hours": self.config.get("backup_interval_hours", 24)
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas de backup: {e}")
            return {}
    
    def update_config(self, new_config: Dict):
        """Actualizar configuración de backup"""
        try:
            self.config.update(new_config)
            self.save_config()
            
            # Reiniciar backup automático si cambió la configuración
            if "auto_backup_enabled" in new_config or "backup_interval_hours" in new_config:
                self.stop_automatic_backup()
                if self.config.get("auto_backup_enabled", True):
                    self.start_automatic_backup()
            
            self.logger.info("Configuración de backup actualizada")
            
        except Exception as e:
            self.logger.error(f"Error actualizando configuración de backup: {e}")