"""
Sistema de Notificaciones para AlmacénPro
Gestión completa de notificaciones del sistema, alertas y comunicaciones
"""

import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    """Tipos de notificaciones"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SYSTEM = "system"
    BUSINESS = "business"

class NotificationPriority(Enum):
    """Prioridades de notificaciones"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Notification:
    """Clase para representar una notificación"""
    id: str
    title: str
    message: str
    notification_type: NotificationType
    priority: NotificationPriority
    timestamp: datetime
    read: bool = False
    persistent: bool = False
    action_callback: Optional[Callable] = None
    action_text: Optional[str] = None
    metadata: Optional[Dict] = None
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """Convertir a diccionario para serialización"""
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.notification_type.value,
            'priority': self.priority.value,
            'timestamp': self.timestamp.isoformat(),
            'read': self.read,
            'persistent': self.persistent,
            'action_text': self.action_text,
            'metadata': self.metadata,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Notification':
        """Crear notificación desde diccionario"""
        return cls(
            id=data['id'],
            title=data['title'],
            message=data['message'],
            notification_type=NotificationType(data['type']),
            priority=NotificationPriority(data['priority']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            read=data.get('read', False),
            persistent=data.get('persistent', False),
            action_text=data.get('action_text'),
            metadata=data.get('metadata'),
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None
        )

class NotificationManager:
    """Gestor principal del sistema de notificaciones"""
    
    def __init__(self):
        self.notifications: List[Notification] = []
        self.subscribers: List[Callable] = []
        self.logger = logging.getLogger(__name__)
        
        # Configuración
        self.max_notifications = 100
        self.notification_file = Path("data/notifications.json")
        self.notification_file.parent.mkdir(exist_ok=True)
        
        # Timer para limpieza automática
        self.cleanup_timer = threading.Timer(3600, self._cleanup_expired)  # 1 hour
        self.cleanup_timer.daemon = True
        self.cleanup_timer.start()
        
        # Cargar notificaciones persistentes
        self.load_notifications()
        
        # Configuración de notificaciones del sistema
        self.system_notifications_enabled = True
        self.business_notifications_enabled = True
        self.sound_enabled = True
        
        # Configuración por defecto de expiraciones
        self.default_expiry_hours = {
            NotificationPriority.LOW: 24,      # 1 día
            NotificationPriority.MEDIUM: 72,   # 3 días  
            NotificationPriority.HIGH: 168,    # 1 semana
            NotificationPriority.CRITICAL: 0   # No expiran
        }
    
    def add_notification(self, 
                        title: str,
                        message: str,
                        notification_type: NotificationType = NotificationType.INFO,
                        priority: NotificationPriority = NotificationPriority.MEDIUM,
                        persistent: bool = False,
                        action_callback: Optional[Callable] = None,
                        action_text: Optional[str] = None,
                        metadata: Optional[Dict] = None,
                        expires_in_hours: Optional[int] = None) -> str:
        """
        Agregar nueva notificación
        
        Returns:
            str: ID de la notificación creada
        """
        try:
            # Generar ID único
            notification_id = self._generate_notification_id()
            
            # Calcular fecha de expiración
            expires_at = None
            if expires_in_hours is not None:
                expires_at = datetime.now() + timedelta(hours=expires_in_hours)
            elif not persistent and priority != NotificationPriority.CRITICAL:
                default_hours = self.default_expiry_hours.get(priority, 24)
                if default_hours > 0:
                    expires_at = datetime.now() + timedelta(hours=default_hours)
            
            # Crear notificación
            notification = Notification(
                id=notification_id,
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority,
                timestamp=datetime.now(),
                persistent=persistent,
                action_callback=action_callback,
                action_text=action_text,
                metadata=metadata,
                expires_at=expires_at
            )
            
            # Agregar a la lista
            self.notifications.append(notification)
            
            # Mantener límite de notificaciones
            self._trim_notifications()
            
            # Guardar si es persistente
            if persistent:
                self.save_notifications()
            
            # Notificar a suscriptores
            self._notify_subscribers(notification)
            
            # Log
            self.logger.info(f"Notificación agregada: {title} ({notification_type.value})")
            
            return notification_id
            
        except Exception as e:
            self.logger.error(f"Error agregando notificación: {e}")
            return ""
    
    def add_info(self, title: str, message: str, **kwargs) -> str:
        """Agregar notificación informativa"""
        return self.add_notification(title, message, NotificationType.INFO, **kwargs)
    
    def add_success(self, title: str, message: str, **kwargs) -> str:
        """Agregar notificación de éxito"""
        return self.add_notification(title, message, NotificationType.SUCCESS, **kwargs)
    
    def add_warning(self, title: str, message: str, **kwargs) -> str:
        """Agregar notificación de advertencia"""
        return self.add_notification(title, message, NotificationType.WARNING, 
                                   priority=NotificationPriority.HIGH, **kwargs)
    
    def add_error(self, title: str, message: str, **kwargs) -> str:
        """Agregar notificación de error"""
        return self.add_notification(title, message, NotificationType.ERROR,
                                   priority=NotificationPriority.CRITICAL, **kwargs)
    
    def add_system_notification(self, title: str, message: str, **kwargs) -> str:
        """Agregar notificación del sistema"""
        if not self.system_notifications_enabled:
            return ""
        
        return self.add_notification(title, message, NotificationType.SYSTEM, **kwargs)
    
    def add_business_notification(self, title: str, message: str, **kwargs) -> str:
        """Agregar notificación de negocio"""
        if not self.business_notifications_enabled:
            return ""
        
        return self.add_notification(title, message, NotificationType.BUSINESS, **kwargs)
    
    def mark_as_read(self, notification_id: str) -> bool:
        """Marcar notificación como leída"""
        try:
            for notification in self.notifications:
                if notification.id == notification_id:
                    notification.read = True
                    
                    if notification.persistent:
                        self.save_notifications()
                    
                    self.logger.debug(f"Notificación marcada como leída: {notification_id}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error marcando notificación como leída: {e}")
            return False
    
    def mark_all_as_read(self) -> int:
        """Marcar todas las notificaciones como leídas"""
        try:
            count = 0
            for notification in self.notifications:
                if not notification.read:
                    notification.read = True
                    count += 1
            
            if count > 0:
                self.save_notifications()
                self.logger.info(f"{count} notificaciones marcadas como leídas")
            
            return count
            
        except Exception as e:
            self.logger.error(f"Error marcando todas como leídas: {e}")
            return 0
    
    def remove_notification(self, notification_id: str) -> bool:
        """Remover notificación específica"""
        try:
            for i, notification in enumerate(self.notifications):
                if notification.id == notification_id:
                    del self.notifications[i]
                    
                    if notification.persistent:
                        self.save_notifications()
                    
                    self.logger.debug(f"Notificación removida: {notification_id}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error removiendo notificación: {e}")
            return False
    
    def clear_read_notifications(self) -> int:
        """Limpiar notificaciones leídas"""
        try:
            initial_count = len(self.notifications)
            self.notifications = [n for n in self.notifications 
                                if not n.read or n.persistent]
            
            removed_count = initial_count - len(self.notifications)
            
            if removed_count > 0:
                self.save_notifications()
                self.logger.info(f"{removed_count} notificaciones leídas eliminadas")
            
            return removed_count
            
        except Exception as e:
            self.logger.error(f"Error limpiando notificaciones leídas: {e}")
            return 0
    
    def clear_all_notifications(self) -> int:
        """Limpiar todas las notificaciones"""
        try:
            # Mantener solo las críticas no leídas
            critical_unread = [n for n in self.notifications 
                             if n.priority == NotificationPriority.CRITICAL and not n.read]
            
            removed_count = len(self.notifications) - len(critical_unread)
            self.notifications = critical_unread
            
            if removed_count > 0:
                self.save_notifications()
                self.logger.info(f"{removed_count} notificaciones eliminadas")
            
            return removed_count
            
        except Exception as e:
            self.logger.error(f"Error limpiando todas las notificaciones: {e}")
            return 0
    
    def get_notifications(self, 
                         include_read: bool = True,
                         notification_type: Optional[NotificationType] = None,
                         priority: Optional[NotificationPriority] = None,
                         limit: Optional[int] = None) -> List[Notification]:
        """Obtener notificaciones con filtros"""
        try:
            filtered_notifications = self.notifications.copy()
            
            # Filtrar por estado de lectura
            if not include_read:
                filtered_notifications = [n for n in filtered_notifications if not n.read]
            
            # Filtrar por tipo
            if notification_type:
                filtered_notifications = [n for n in filtered_notifications 
                                        if n.notification_type == notification_type]
            
            # Filtrar por prioridad
            if priority:
                filtered_notifications = [n for n in filtered_notifications 
                                        if n.priority == priority]
            
            # Ordenar por timestamp (más recientes primero)
            filtered_notifications.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Aplicar límite
            if limit:
                filtered_notifications = filtered_notifications[:limit]
            
            return filtered_notifications
            
        except Exception as e:
            self.logger.error(f"Error obteniendo notificaciones: {e}")
            return []
    
    def get_unread_count(self) -> int:
        """Obtener cantidad de notificaciones no leídas"""
        return len([n for n in self.notifications if not n.read])
    
    def get_critical_count(self) -> int:
        """Obtener cantidad de notificaciones críticas no leídas"""
        return len([n for n in self.notifications 
                   if not n.read and n.priority == NotificationPriority.CRITICAL])
    
    def subscribe(self, callback: Callable[[Notification], None]):
        """Suscribirse a notificaciones nuevas"""
        if callback not in self.subscribers:
            self.subscribers.append(callback)
            self.logger.debug("Nuevo suscriptor agregado")
    
    def unsubscribe(self, callback: Callable[[Notification], None]):
        """Desuscribirse de notificaciones"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
            self.logger.debug("Suscriptor removido")
    
    def _notify_subscribers(self, notification: Notification):
        """Notificar a todos los suscriptores"""
        for callback in self.subscribers:
            try:
                callback(notification)
            except Exception as e:
                self.logger.error(f"Error notificando suscriptor: {e}")
    
    def _generate_notification_id(self) -> str:
        """Generar ID único para notificación"""
        import uuid
        return str(uuid.uuid4())
    
    def _trim_notifications(self):
        """Mantener límite de notificaciones"""
        if len(self.notifications) > self.max_notifications:
            # Ordenar por timestamp
            self.notifications.sort(key=lambda x: x.timestamp)
            
            # Mantener las más recientes, pero preservar las críticas no leídas
            critical_unread = [n for n in self.notifications 
                             if n.priority == NotificationPriority.CRITICAL and not n.read]
            
            other_notifications = [n for n in self.notifications 
                                 if not (n.priority == NotificationPriority.CRITICAL and not n.read)]
            
            # Mantener solo las más recientes de las no críticas
            keep_count = self.max_notifications - len(critical_unread)
            if keep_count > 0:
                other_notifications = other_notifications[-keep_count:]
            else:
                other_notifications = []
            
            self.notifications = critical_unread + other_notifications
    
    def _cleanup_expired(self):
        """Limpiar notificaciones expiradas"""
        try:
            now = datetime.now()
            initial_count = len(self.notifications)
            
            self.notifications = [n for n in self.notifications 
                                if n.expires_at is None or n.expires_at > now]
            
            removed_count = initial_count - len(self.notifications)
            
            if removed_count > 0:
                self.save_notifications()
                self.logger.info(f"{removed_count} notificaciones expiradas eliminadas")
            
            # Reprogramar limpieza
            self.cleanup_timer = threading.Timer(3600, self._cleanup_expired)
            self.cleanup_timer.daemon = True
            self.cleanup_timer.start()
            
        except Exception as e:
            self.logger.error(f"Error limpiando notificaciones expiradas: {e}")
    
    def save_notifications(self):
        """Guardar notificaciones persistentes"""
        try:
            persistent_notifications = [n for n in self.notifications if n.persistent]
            
            data = {
                'notifications': [n.to_dict() for n in persistent_notifications],
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.notification_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"{len(persistent_notifications)} notificaciones persistentes guardadas")
            
        except Exception as e:
            self.logger.error(f"Error guardando notificaciones: {e}")
    
    def load_notifications(self):
        """Cargar notificaciones persistentes"""
        try:
            if not self.notification_file.exists():
                return
            
            with open(self.notification_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for notification_data in data.get('notifications', []):
                try:
                    notification = Notification.from_dict(notification_data)
                    
                    # Verificar si no ha expirado
                    if notification.expires_at is None or notification.expires_at > datetime.now():
                        self.notifications.append(notification)
                        
                except Exception as e:
                    self.logger.warning(f"Error cargando notificación: {e}")
            
            self.logger.info(f"{len(self.notifications)} notificaciones persistentes cargadas")
            
        except Exception as e:
            self.logger.error(f"Error cargando notificaciones: {e}")
    
    def get_statistics(self) -> Dict:
        """Obtener estadísticas de notificaciones"""
        try:
            total = len(self.notifications)
            unread = self.get_unread_count()
            critical = self.get_critical_count()
            
            # Contar por tipo
            by_type = {}
            for notification_type in NotificationType:
                count = len([n for n in self.notifications if n.notification_type == notification_type])
                by_type[notification_type.value] = count
            
            # Contar por prioridad
            by_priority = {}
            for priority in NotificationPriority:
                count = len([n for n in self.notifications if n.priority == priority])
                by_priority[priority.name] = count
            
            return {
                'total': total,
                'unread': unread,
                'critical_unread': critical,
                'read_percentage': round((total - unread) / total * 100, 1) if total > 0 else 0,
                'by_type': by_type,
                'by_priority': by_priority
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def enable_system_notifications(self, enabled: bool = True):
        """Habilitar/deshabilitar notificaciones del sistema"""
        self.system_notifications_enabled = enabled
        self.logger.info(f"Notificaciones del sistema: {'habilitadas' if enabled else 'deshabilitadas'}")
    
    def enable_business_notifications(self, enabled: bool = True):
        """Habilitar/deshabilitar notificaciones de negocio"""
        self.business_notifications_enabled = enabled
        self.logger.info(f"Notificaciones de negocio: {'habilitadas' if enabled else 'deshabilitadas'}")
    
    def enable_sound(self, enabled: bool = True):
        """Habilitar/deshabilitar sonidos"""
        self.sound_enabled = enabled
        self.logger.info(f"Sonidos de notificación: {'habilitados' if enabled else 'deshabilitados'}")
    
    def create_stock_alert(self, product_name: str, current_stock: float, min_stock: float):
        """Crear alerta de stock bajo"""
        self.add_warning(
            "Stock Bajo",
            f"El producto '{product_name}' tiene stock bajo.\n"
            f"Stock actual: {current_stock}\n"
            f"Stock mínimo: {min_stock}",
            metadata={
                'type': 'stock_alert',
                'product_name': product_name,
                'current_stock': current_stock,
                'min_stock': min_stock
            }
        )
    
    def create_sale_notification(self, sale_id: int, amount: float, customer: str = None):
        """Crear notificación de venta"""
        customer_text = f" a {customer}" if customer else ""
        
        self.add_success(
            "Venta Completada",
            f"Venta #{sale_id} completada{customer_text}.\n"
            f"Monto: ${amount:.2f}",
            metadata={
                'type': 'sale_completed',
                'sale_id': sale_id,
                'amount': amount,
                'customer': customer
            }
        )
    
    def create_backup_notification(self, success: bool, backup_path: str = None, error: str = None):
        """Crear notificación de backup"""
        if success:
            self.add_success(
                "Backup Completado",
                f"Backup creado exitosamente.\n"
                f"Ubicación: {backup_path}",
                metadata={
                    'type': 'backup_completed',
                    'backup_path': backup_path
                }
            )
        else:
            self.add_error(
                "Error en Backup",
                f"Error creando backup del sistema.\n"
                f"Error: {error}",
                persistent=True,
                metadata={
                    'type': 'backup_error',
                    'error': error
                }
            )
    
    def create_system_startup_notification(self):
        """Crear notificación de inicio del sistema"""
        self.add_system_notification(
            "Sistema Iniciado",
            f"AlmacénPro iniciado exitosamente.\n"
            f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            metadata={'type': 'system_startup'}
        )
    
    def shutdown(self):
        """Cerrar gestor de notificaciones"""
        try:
            # Detener timer de limpieza
            if hasattr(self, 'cleanup_timer'):
                self.cleanup_timer.cancel()
            
            # Guardar notificaciones persistentes
            self.save_notifications()
            
            self.logger.info("Gestor de notificaciones cerrado")
            
        except Exception as e:
            self.logger.error(f"Error cerrando gestor de notificaciones: {e}")


# Instancia global del gestor de notificaciones
notification_manager = NotificationManager()

# Funciones de conveniencia
def notify_info(title: str, message: str, **kwargs) -> str:
    """Función de conveniencia para notificación informativa"""
    return notification_manager.add_info(title, message, **kwargs)

def notify_success(title: str, message: str, **kwargs) -> str:
    """Función de conveniencia para notificación de éxito"""
    return notification_manager.add_success(title, message, **kwargs)

def notify_warning(title: str, message: str, **kwargs) -> str:
    """Función de conveniencia para notificación de advertencia"""
    return notification_manager.add_warning(title, message, **kwargs)

def notify_error(title: str, message: str, **kwargs) -> str:
    """Función de conveniencia para notificación de error"""
    return notification_manager.add_error(title, message, **kwargs)

def get_notification_manager() -> NotificationManager:
    """Obtener instancia del gestor de notificaciones"""
    return notification_manager