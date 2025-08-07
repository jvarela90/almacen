"""
Sistema de logs de auditoría para AlmacénPro v2.0
Registro completo de acciones del usuario y cambios en el sistema
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import threading
from dataclasses import asdict

from database.models import SystemLog

class AuditLogger:
    """Logger de auditoría para el sistema"""
    
    def __init__(self, db_manager, current_user: Optional[Dict] = None):
        self.db_manager = db_manager
        self.current_user = current_user
        self.lock = threading.Lock()
        
        # Configurar logger dedicado para auditoría
        self.logger = logging.getLogger('audit')
        if not self.logger.handlers:
            # Handler para archivo de auditoría
            log_path = Path("logs/audit.log")
            log_path.parent.mkdir(exist_ok=True)
            
            handler = logging.FileHandler(str(log_path), encoding='utf-8')
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def set_current_user(self, user: Dict[str, Any]):
        """Establecer usuario actual para los logs"""
        self.current_user = user
    
    def log_action(self, action: str, table_name: str = None, record_id: int = None, 
                   old_values: Dict = None, new_values: Dict = None, 
                   success: bool = True, error_message: str = None,
                   additional_info: Dict = None):
        """Registrar acción del usuario"""
        try:
            with self.lock:
                # Crear log entry
                log_entry = SystemLog(
                    timestamp=datetime.now(),
                    user_id=self.current_user.get('id') if self.current_user else None,
                    username=self.current_user.get('username') if self.current_user else 'SYSTEM',
                    action=action,
                    table_name=table_name,
                    record_id=record_id,
                    old_values=old_values,
                    new_values=new_values,
                    success=success,
                    error_message=error_message
                )
                
                # Log a archivo
                log_message = self._format_log_message(log_entry, additional_info)
                if success:
                    self.logger.info(log_message)
                else:
                    self.logger.error(log_message)
                
                # Guardar en base de datos
                self._save_to_database(log_entry)
                
        except Exception as e:
            # Fallback logging si hay problemas
            logging.error(f"Error en audit logger: {e}")
    
    def log_login(self, username: str, success: bool, ip_address: str = None, 
                  user_agent: str = None, error_message: str = None):
        """Registrar intento de login"""
        self.log_action(
            action="LOGIN_ATTEMPT" if not success else "LOGIN_SUCCESS",
            success=success,
            error_message=error_message,
            additional_info={
                'attempted_username': username,
                'ip_address': ip_address,
                'user_agent': user_agent
            }
        )
    
    def log_logout(self, username: str):
        """Registrar logout"""
        self.log_action(
            action="LOGOUT",
            additional_info={'username': username}
        )
    
    def log_create(self, table_name: str, record_id: int, new_values: Dict):
        """Registrar creación de registro"""
        self.log_action(
            action="CREATE",
            table_name=table_name,
            record_id=record_id,
            new_values=new_values
        )
    
    def log_update(self, table_name: str, record_id: int, old_values: Dict, new_values: Dict):
        """Registrar actualización de registro"""
        # Solo incluir campos que cambiaron
        changes = {}
        for key, new_val in new_values.items():
            old_val = old_values.get(key)
            if old_val != new_val:
                changes[key] = {'old': old_val, 'new': new_val}
        
        if changes:
            self.log_action(
                action="UPDATE",
                table_name=table_name,
                record_id=record_id,
                old_values=old_values,
                new_values=new_values,
                additional_info={'changes': changes}
            )
    
    def log_delete(self, table_name: str, record_id: int, old_values: Dict):
        """Registrar eliminación de registro"""
        self.log_action(
            action="DELETE",
            table_name=table_name,
            record_id=record_id,
            old_values=old_values
        )
    
    def log_sale(self, sale_id: int, total: float, items_count: int, payment_method: str):
        """Registrar venta"""
        self.log_action(
            action="SALE_COMPLETED",
            table_name="ventas",
            record_id=sale_id,
            additional_info={
                'total': total,
                'items_count': items_count,
                'payment_method': payment_method
            }
        )
    
    def log_stock_movement(self, product_id: int, product_name: str, 
                          movement_type: str, quantity: float, reason: str):
        """Registrar movimiento de stock"""
        self.log_action(
            action="STOCK_MOVEMENT",
            table_name="productos",
            record_id=product_id,
            additional_info={
                'product_name': product_name,
                'movement_type': movement_type,  # IN, OUT, ADJUSTMENT
                'quantity': quantity,
                'reason': reason
            }
        )
    
    def log_backup(self, backup_type: str, success: bool, file_path: str = None, 
                   error_message: str = None):
        """Registrar operación de backup"""
        self.log_action(
            action="BACKUP",
            success=success,
            error_message=error_message,
            additional_info={
                'backup_type': backup_type,
                'file_path': file_path
            }
        )
    
    def log_configuration_change(self, config_key: str, old_value: Any, new_value: Any):
        """Registrar cambio de configuración"""
        self.log_action(
            action="CONFIG_CHANGE",
            table_name="system_config",
            old_values={'value': old_value},
            new_values={'value': new_value},
            additional_info={'config_key': config_key}
        )
    
    def log_report_generation(self, report_type: str, parameters: Dict, success: bool, 
                            error_message: str = None):
        """Registrar generación de reporte"""
        self.log_action(
            action="REPORT_GENERATED",
            success=success,
            error_message=error_message,
            additional_info={
                'report_type': report_type,
                'parameters': parameters
            }
        )
    
    def _format_log_message(self, log_entry: SystemLog, additional_info: Dict = None) -> str:
        """Formatear mensaje de log"""
        user_info = f"{log_entry.username}({log_entry.user_id})" if log_entry.username else "SYSTEM"
        
        message_parts = [
            f"USER={user_info}",
            f"ACTION={log_entry.action}"
        ]
        
        if log_entry.table_name:
            message_parts.append(f"TABLE={log_entry.table_name}")
        
        if log_entry.record_id:
            message_parts.append(f"RECORD_ID={log_entry.record_id}")
        
        if not log_entry.success and log_entry.error_message:
            message_parts.append(f"ERROR={log_entry.error_message}")
        
        if additional_info:
            for key, value in additional_info.items():
                if isinstance(value, dict):
                    message_parts.append(f"{key.upper()}={json.dumps(value)}")
                else:
                    message_parts.append(f"{key.upper()}={value}")
        
        return " | ".join(message_parts)
    
    def _save_to_database(self, log_entry: SystemLog):
        """Guardar log en base de datos"""
        try:
            if not self.db_manager:
                return
            
            sql = """
                INSERT INTO system_logs (
                    timestamp, user_id, username, action, table_name, record_id,
                    old_values, new_values, success, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            values = (
                log_entry.timestamp,
                log_entry.user_id,
                log_entry.username,
                log_entry.action,
                log_entry.table_name,
                log_entry.record_id,
                json.dumps(log_entry.old_values) if log_entry.old_values else None,
                json.dumps(log_entry.new_values) if log_entry.new_values else None,
                log_entry.success,
                log_entry.error_message
            )
            
            self.db_manager.execute_query(sql, values)
            
        except Exception as e:
            # No hacer logging recursivo si hay error guardando en DB
            pass
    
    def get_user_activity(self, user_id: int, days: int = 30) -> List[Dict]:
        """Obtener actividad reciente de un usuario"""
        try:
            sql = """
                SELECT * FROM system_logs 
                WHERE user_id = ? 
                AND timestamp >= datetime('now', '-{} days')
                ORDER BY timestamp DESC
                LIMIT 100
            """.format(days)
            
            rows = self.db_manager.execute_query(sql, (user_id,))
            return [dict(row) for row in rows] if rows else []
            
        except Exception as e:
            logging.error(f"Error obteniendo actividad de usuario: {e}")
            return []
    
    def get_system_activity(self, hours: int = 24) -> List[Dict]:
        """Obtener actividad reciente del sistema"""
        try:
            sql = """
                SELECT * FROM system_logs 
                WHERE timestamp >= datetime('now', '-{} hours')
                ORDER BY timestamp DESC
                LIMIT 200
            """.format(hours)
            
            rows = self.db_manager.execute_query(sql)
            return [dict(row) for row in rows] if rows else []
            
        except Exception as e:
            logging.error(f"Error obteniendo actividad del sistema: {e}")
            return []
    
    def get_failed_actions(self, hours: int = 24) -> List[Dict]:
        """Obtener acciones fallidas recientes"""
        try:
            sql = """
                SELECT * FROM system_logs 
                WHERE success = 0 
                AND timestamp >= datetime('now', '-{} hours')
                ORDER BY timestamp DESC
            """.format(hours)
            
            rows = self.db_manager.execute_query(sql)
            return [dict(row) for row in rows] if rows else []
            
        except Exception as e:
            logging.error(f"Error obteniendo acciones fallidas: {e}")
            return []

# Instancia global del logger de auditoría
_audit_logger = None

def get_audit_logger(db_manager=None, current_user=None):
    """Obtener instancia global del audit logger"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(db_manager, current_user)
    else:
        if current_user:
            _audit_logger.set_current_user(current_user)
    return _audit_logger

def init_audit_logger(db_manager, current_user=None):
    """Inicializar el audit logger global"""
    global _audit_logger
    _audit_logger = AuditLogger(db_manager, current_user)
    return _audit_logger