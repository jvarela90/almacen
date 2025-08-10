"""
Gestor de Comunicaciones - AlmacénPro v2.0
Sistema completo de comunicación multicanal integrado
"""

import logging
import smtplib
import json
import requests
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dataclasses import dataclass
from enum import Enum
import threading
import queue
import time

logger = logging.getLogger(__name__)

class MessagePriority(Enum):
    """Prioridades de mensajes"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

class MessageStatus(Enum):
    """Estados de mensajes"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    CANCELLED = "cancelled"

class CommunicationChannel(Enum):
    """Canales de comunicación"""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    INTERNAL = "internal"
    PUSH = "push"
    SLACK = "slack"

@dataclass
class Message:
    """Estructura de mensaje"""
    id: Optional[str]
    channel: CommunicationChannel
    recipient: str
    subject: str
    content: str
    template_id: Optional[str]
    template_vars: Dict[str, Any]
    priority: MessagePriority
    scheduled_at: Optional[datetime]
    created_at: datetime
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    status: MessageStatus
    error_message: Optional[str]
    metadata: Dict[str, Any]
    sender_id: Optional[str]
    customer_id: Optional[int]
    campaign_id: Optional[str]

@dataclass
class Template:
    """Plantilla de mensaje"""
    id: str
    name: str
    channel: CommunicationChannel
    subject_template: str
    content_template: str
    variables: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    category: str

@dataclass
class Campaign:
    """Campaña de comunicación"""
    id: str
    name: str
    description: str
    channel: CommunicationChannel
    template_id: str
    target_segments: List[str]
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    status: str
    total_recipients: int
    sent_count: int
    delivered_count: int
    failed_count: int
    metadata: Dict[str, Any]

class EmailProvider:
    """Proveedor de email"""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, 
                 password: str, use_tls: bool = True):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
    
    def send_email(self, message: Message, attachments: List[str] = None) -> bool:
        """Enviar email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = message.recipient
            msg['Subject'] = message.subject
            
            # Agregar contenido
            msg.attach(MIMEText(message.content, 'html'))
            
            # Agregar adjuntos
            if attachments:
                for file_path in attachments:
                    try:
                        with open(file_path, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {file_path.split("/")[-1]}'
                            )
                            msg.attach(part)
                    except Exception as e:
                        logger.warning(f"Error adjuntando archivo {file_path}: {e}")
            
            # Conectar y enviar
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.use_tls:
                server.starttls()
            
            server.login(self.username, self.password)
            text = msg.as_string()
            server.sendmail(self.username, message.recipient, text)
            server.quit()
            
            logger.info(f"Email enviado exitosamente a {message.recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email a {message.recipient}: {e}")
            return False

class WhatsAppProvider:
    """Proveedor de WhatsApp Business API"""
    
    def __init__(self, api_url: str, access_token: str, phone_number_id: str):
        self.api_url = api_url
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    def send_message(self, message: Message) -> bool:
        """Enviar mensaje de WhatsApp"""
        try:
            # Limpiar número de teléfono
            phone = self.clean_phone_number(message.recipient)
            
            data = {
                "messaging_product": "whatsapp",
                "to": phone,
                "type": "text",
                "text": {
                    "body": message.content
                }
            }
            
            url = f"{self.api_url}/{self.phone_number_id}/messages"
            response = requests.post(url, headers=self.headers, json=data)
            
            if response.status_code == 200:
                logger.info(f"WhatsApp enviado exitosamente a {phone}")
                return True
            else:
                logger.error(f"Error enviando WhatsApp: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error enviando WhatsApp a {message.recipient}: {e}")
            return False
    
    def send_template_message(self, message: Message, template_name: str, 
                            template_params: List[str] = None) -> bool:
        """Enviar mensaje con template de WhatsApp"""
        try:
            phone = self.clean_phone_number(message.recipient)
            
            data = {
                "messaging_product": "whatsapp",
                "to": phone,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": "es"
                    }
                }
            }
            
            if template_params:
                data["template"]["components"] = [{
                    "type": "body",
                    "parameters": [{"type": "text", "text": param} for param in template_params]
                }]
            
            url = f"{self.api_url}/{self.phone_number_id}/messages"
            response = requests.post(url, headers=self.headers, json=data)
            
            if response.status_code == 200:
                logger.info(f"WhatsApp template enviado a {phone}")
                return True
            else:
                logger.error(f"Error enviando template WhatsApp: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error enviando template WhatsApp: {e}")
            return False
    
    def clean_phone_number(self, phone: str) -> str:
        """Limpiar y formatear número de teléfono"""
        # Remover caracteres no numéricos
        clean = ''.join(filter(str.isdigit, phone))
        
        # Agregar código de país si no lo tiene (Argentina)
        if len(clean) == 10 and clean.startswith('11'):
            clean = '549' + clean
        elif len(clean) == 10:
            clean = '54' + clean
        elif not clean.startswith('54'):
            clean = '54' + clean
        
        return clean

class SMSProvider:
    """Proveedor de SMS"""
    
    def __init__(self, api_url: str, api_key: str, sender_id: str):
        self.api_url = api_url
        self.api_key = api_key
        self.sender_id = sender_id
    
    def send_sms(self, message: Message) -> bool:
        """Enviar SMS"""
        try:
            # Implementación básica - adaptable según proveedor
            data = {
                'api_key': self.api_key,
                'to': message.recipient,
                'from': self.sender_id,
                'message': message.content[:160]  # Límite SMS
            }
            
            response = requests.post(self.api_url, data=data)
            
            if response.status_code == 200:
                logger.info(f"SMS enviado exitosamente a {message.recipient}")
                return True
            else:
                logger.error(f"Error enviando SMS: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error enviando SMS a {message.recipient}: {e}")
            return False

class TemplateEngine:
    """Motor de plantillas"""
    
    def __init__(self):
        self.templates = {}
    
    def render_template(self, template: Template, variables: Dict[str, Any]) -> Tuple[str, str]:
        """Renderizar plantilla con variables"""
        try:
            subject = template.subject_template
            content = template.content_template
            
            # Reemplazar variables
            for var_name, var_value in variables.items():
                placeholder = "{{" + var_name + "}}"
                subject = subject.replace(placeholder, str(var_value))
                content = content.replace(placeholder, str(var_value))
            
            return subject, content
            
        except Exception as e:
            logger.error(f"Error renderizando template {template.id}: {e}")
            return template.subject_template, template.content_template
    
    def validate_template(self, template: Template) -> List[str]:
        """Validar plantilla"""
        errors = []
        
        # Verificar variables requeridas
        import re
        
        subject_vars = set(re.findall(r'\{\{(\w+)\}\}', template.subject_template))
        content_vars = set(re.findall(r'\{\{(\w+)\}\}', template.content_template))
        all_vars = subject_vars.union(content_vars)
        
        # Verificar que todas las variables estén declaradas
        declared_vars = set(template.variables)
        missing_vars = all_vars - declared_vars
        
        if missing_vars:
            errors.append(f"Variables no declaradas: {missing_vars}")
        
        # Verificaciones específicas por canal
        if template.channel == CommunicationChannel.EMAIL:
            if not template.subject_template:
                errors.append("Email requiere asunto")
        
        elif template.channel == CommunicationChannel.SMS:
            if len(template.content_template) > 160:
                errors.append("SMS no puede exceder 160 caracteres")
        
        return errors

class MessageQueue:
    """Cola de mensajes"""
    
    def __init__(self, max_size: int = 1000):
        self.queue = queue.PriorityQueue(maxsize=max_size)
        self.processing = False
        self.thread = None
    
    def add_message(self, message: Message):
        """Agregar mensaje a la cola"""
        try:
            # Usar prioridad como clave de ordenamiento
            priority_value = message.priority.value
            timestamp = message.created_at.timestamp()
            
            # Item: (prioridad, timestamp, mensaje)
            self.queue.put((priority_value, timestamp, message))
            
        except queue.Full:
            logger.error("Cola de mensajes llena")
    
    def start_processing(self, communication_manager):
        """Iniciar procesamiento de la cola"""
        if not self.processing:
            self.processing = True
            self.thread = threading.Thread(
                target=self._process_messages, 
                args=(communication_manager,)
            )
            self.thread.start()
    
    def stop_processing(self):
        """Detener procesamiento"""
        self.processing = False
        if self.thread:
            self.thread.join()
    
    def _process_messages(self, communication_manager):
        """Procesar mensajes en la cola"""
        while self.processing:
            try:
                # Obtener mensaje con timeout
                priority, timestamp, message = self.queue.get(timeout=1.0)
                
                # Procesar mensaje
                communication_manager._send_message_internal(message)
                
                # Marcar como procesado
                self.queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error procesando mensaje en cola: {e}")

class CommunicationManager:
    """Gestor principal de comunicaciones"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.template_engine = TemplateEngine()
        self.message_queue = MessageQueue()
        
        # Proveedores
        self.email_provider = None
        self.whatsapp_provider = None
        self.sms_provider = None
        
        # Cache de plantillas
        self.templates_cache = {}
        self.last_cache_update = None
        
        # Configuración
        self.config = self.load_configuration()
        
        # Inicializar proveedores
        self._initialize_providers()
        
        # Crear tablas si no existen
        self.create_communication_tables()
        
        # Iniciar procesamiento de cola
        self.message_queue.start_processing(self)
    
    def load_configuration(self) -> Dict[str, Any]:
        """Cargar configuración de comunicaciones"""
        default_config = {
            'email': {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'use_tls': True,
                'enabled': False
            },
            'whatsapp': {
                'api_url': 'https://graph.facebook.com/v18.0',
                'access_token': '',
                'phone_number_id': '',
                'enabled': False
            },
            'sms': {
                'api_url': '',
                'api_key': '',
                'sender_id': 'AlmacenPro',
                'enabled': False
            },
            'general': {
                'retry_attempts': 3,
                'retry_delay': 300,  # 5 minutos
                'batch_size': 100,
                'rate_limit': 60,  # mensajes por minuto
                'auto_notifications': True
            }
        }
        
        try:
            # En implementación real, cargar desde archivo o DB
            return default_config
        except:
            return default_config
    
    def _initialize_providers(self):
        """Inicializar proveedores de comunicación"""
        try:
            # Email
            if self.config['email']['enabled']:
                self.email_provider = EmailProvider(
                    smtp_server=self.config['email']['smtp_server'],
                    smtp_port=self.config['email']['smtp_port'],
                    username=self.config['email']['username'],
                    password=self.config['email']['password'],
                    use_tls=self.config['email']['use_tls']
                )
            
            # WhatsApp
            if self.config['whatsapp']['enabled']:
                self.whatsapp_provider = WhatsAppProvider(
                    api_url=self.config['whatsapp']['api_url'],
                    access_token=self.config['whatsapp']['access_token'],
                    phone_number_id=self.config['whatsapp']['phone_number_id']
                )
            
            # SMS
            if self.config['sms']['enabled']:
                self.sms_provider = SMSProvider(
                    api_url=self.config['sms']['api_url'],
                    api_key=self.config['sms']['api_key'],
                    sender_id=self.config['sms']['sender_id']
                )
                
        except Exception as e:
            logger.error(f"Error inicializando proveedores: {e}")
    
    def create_communication_tables(self):
        """Crear tablas de comunicación"""
        try:
            # Tabla de mensajes
            messages_table = """
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                channel TEXT NOT NULL,
                recipient TEXT NOT NULL,
                subject TEXT,
                content TEXT NOT NULL,
                template_id TEXT,
                template_vars TEXT,
                priority INTEGER NOT NULL,
                scheduled_at TEXT,
                created_at TEXT NOT NULL,
                sent_at TEXT,
                delivered_at TEXT,
                read_at TEXT,
                status TEXT NOT NULL,
                error_message TEXT,
                metadata TEXT,
                sender_id TEXT,
                customer_id INTEGER,
                campaign_id TEXT,
                FOREIGN KEY (customer_id) REFERENCES clientes (id)
            );
            """
            
            # Tabla de plantillas
            templates_table = """
            CREATE TABLE IF NOT EXISTS message_templates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                channel TEXT NOT NULL,
                subject_template TEXT,
                content_template TEXT NOT NULL,
                variables TEXT,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                category TEXT
            );
            """
            
            # Tabla de campañas
            campaigns_table = """
            CREATE TABLE IF NOT EXISTS campaigns (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                channel TEXT NOT NULL,
                template_id TEXT NOT NULL,
                target_segments TEXT,
                scheduled_at TEXT,
                started_at TEXT,
                completed_at TEXT,
                status TEXT NOT NULL,
                total_recipients INTEGER,
                sent_count INTEGER DEFAULT 0,
                delivered_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                metadata TEXT,
                FOREIGN KEY (template_id) REFERENCES message_templates (id)
            );
            """
            
            # Tabla de eventos de comunicación
            communication_events_table = """
            CREATE TABLE IF NOT EXISTS communication_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (message_id) REFERENCES messages (id)
            );
            """
            
            # Tabla de configuración
            communication_config_table = """
            CREATE TABLE IF NOT EXISTS communication_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
            
            self.db_manager.execute_query(messages_table)
            self.db_manager.execute_query(templates_table)
            self.db_manager.execute_query(campaigns_table)
            self.db_manager.execute_query(communication_events_table)
            self.db_manager.execute_query(communication_config_table)
            
            # Insertar plantillas por defecto
            self._create_default_templates()
            
            return True
            
        except Exception as e:
            logger.error(f"Error creando tablas de comunicación: {e}")
            return False
    
    def _create_default_templates(self):
        """Crear plantillas por defecto"""
        default_templates = [
            # Email de bienvenida
            {
                'id': 'email_welcome',
                'name': 'Bienvenida Email',
                'channel': 'email',
                'subject_template': '¡Bienvenido a {{company_name}}, {{customer_name}}!',
                'content_template': '''
                <html>
                <body>
                    <h2>¡Bienvenido {{customer_name}}!</h2>
                    <p>Nos complace tenerte como cliente de {{company_name}}.</p>
                    <p>Tu número de cliente es: <strong>{{customer_id}}</strong></p>
                    <p>Si tienes alguna consulta, no dudes en contactarnos.</p>
                    <p>¡Gracias por elegirnos!</p>
                </body>
                </html>
                ''',
                'variables': ['company_name', 'customer_name', 'customer_id'],
                'category': 'onboarding'
            },
            
            # WhatsApp recordatorio de pago
            {
                'id': 'whatsapp_payment_reminder',
                'name': 'Recordatorio de Pago WhatsApp',
                'channel': 'whatsapp',
                'subject_template': '',
                'content_template': '''Hola {{customer_name}},
Te recordamos que tienes un saldo pendiente de ${{amount}} en tu cuenta.
Puedes realizar el pago a través de nuestros canales habilitados.
¡Gracias por tu atención!
{{company_name}}''',
                'variables': ['customer_name', 'amount', 'company_name'],
                'category': 'payment'
            },
            
            # Email de compra realizada
            {
                'id': 'email_purchase_confirmation',
                'name': 'Confirmación de Compra',
                'channel': 'email',
                'subject_template': 'Confirmación de compra - Pedido #{{order_number}}',
                'content_template': '''
                <html>
                <body>
                    <h2>¡Gracias por tu compra {{customer_name}}!</h2>
                    <p>Hemos recibido tu pedido correctamente:</p>
                    <ul>
                        <li><strong>Número de pedido:</strong> {{order_number}}</li>
                        <li><strong>Fecha:</strong> {{order_date}}</li>
                        <li><strong>Total:</strong> ${{total_amount}}</li>
                    </ul>
                    <p>Te notificaremos cuando tu pedido esté listo.</p>
                </body>
                </html>
                ''',
                'variables': ['customer_name', 'order_number', 'order_date', 'total_amount'],
                'category': 'sales'
            },
            
            # SMS de código de verificación
            {
                'id': 'sms_verification',
                'name': 'Código de Verificación SMS',
                'channel': 'sms',
                'subject_template': '',
                'content_template': 'Tu código de verificación es: {{verification_code}}. Válido por {{expiry_minutes}} minutos.',
                'variables': ['verification_code', 'expiry_minutes'],
                'category': 'security'
            }
        ]
        
        for template_data in default_templates:
            existing = self.get_template(template_data['id'])
            if not existing:
                self.create_template(template_data)
    
    def send_message(self, channel: CommunicationChannel, recipient: str, 
                    subject: str, content: str, priority: MessagePriority = MessagePriority.NORMAL,
                    template_id: str = None, template_vars: Dict[str, Any] = None,
                    scheduled_at: datetime = None, customer_id: int = None,
                    sender_id: str = None, campaign_id: str = None,
                    metadata: Dict[str, Any] = None) -> str:
        """Enviar mensaje"""
        try:
            # Generar ID único
            message_id = self._generate_message_id()
            
            # Crear mensaje
            message = Message(
                id=message_id,
                channel=channel,
                recipient=recipient,
                subject=subject,
                content=content,
                template_id=template_id,
                template_vars=template_vars or {},
                priority=priority,
                scheduled_at=scheduled_at,
                created_at=datetime.now(),
                sent_at=None,
                delivered_at=None,
                read_at=None,
                status=MessageStatus.PENDING,
                error_message=None,
                metadata=metadata or {},
                sender_id=sender_id,
                customer_id=customer_id,
                campaign_id=campaign_id
            )
            
            # Guardar en base de datos
            self._save_message(message)
            
            # Si tiene template, renderizar
            if template_id and template_vars:
                template = self.get_template(template_id)
                if template:
                    rendered_subject, rendered_content = self.template_engine.render_template(
                        template, template_vars
                    )
                    message.subject = rendered_subject
                    message.content = rendered_content
            
            # Enviar inmediatamente o programar
            if scheduled_at and scheduled_at > datetime.now():
                logger.info(f"Mensaje {message_id} programado para {scheduled_at}")
            else:
                # Agregar a cola de envío
                self.message_queue.add_message(message)
            
            return message_id
            
        except Exception as e:
            logger.error(f"Error enviando mensaje: {e}")
            return None
    
    def _send_message_internal(self, message: Message) -> bool:
        """Envío interno de mensaje"""
        try:
            success = False
            
            if message.channel == CommunicationChannel.EMAIL and self.email_provider:
                success = self.email_provider.send_email(message)
            
            elif message.channel == CommunicationChannel.WHATSAPP and self.whatsapp_provider:
                success = self.whatsapp_provider.send_message(message)
            
            elif message.channel == CommunicationChannel.SMS and self.sms_provider:
                success = self.sms_provider.send_sms(message)
            
            elif message.channel == CommunicationChannel.INTERNAL:
                success = self._send_internal_notification(message)
            
            # Actualizar estado
            if success:
                message.status = MessageStatus.SENT
                message.sent_at = datetime.now()
            else:
                message.status = MessageStatus.FAILED
                message.error_message = "Error en el envío"
            
            self._update_message_status(message)
            self._log_communication_event(message.id, 'send_attempt', {
                'success': success,
                'channel': message.channel.value
            })
            
            return success
            
        except Exception as e:
            logger.error(f"Error en envío interno: {e}")
            message.status = MessageStatus.FAILED
            message.error_message = str(e)
            self._update_message_status(message)
            return False
    
    def _send_internal_notification(self, message: Message) -> bool:
        """Enviar notificación interna"""
        try:
            # Implementación básica - se puede expandir
            notification_data = {
                'recipient': message.recipient,
                'subject': message.subject,
                'content': message.content,
                'timestamp': datetime.now().isoformat(),
                'priority': message.priority.name
            }
            
            # En implementación real, integrar con sistema de notificaciones
            logger.info(f"Notificación interna enviada: {message.subject}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando notificación interna: {e}")
            return False
    
    def send_bulk_messages(self, messages_data: List[Dict[str, Any]], 
                          campaign_id: str = None) -> Dict[str, Any]:
        """Envío masivo de mensajes"""
        try:
            results = {
                'total': len(messages_data),
                'queued': 0,
                'failed': 0,
                'message_ids': []
            }
            
            for msg_data in messages_data:
                try:
                    message_id = self.send_message(
                        channel=CommunicationChannel(msg_data.get('channel')),
                        recipient=msg_data.get('recipient'),
                        subject=msg_data.get('subject', ''),
                        content=msg_data.get('content'),
                        priority=MessagePriority(msg_data.get('priority', MessagePriority.NORMAL.value)),
                        template_id=msg_data.get('template_id'),
                        template_vars=msg_data.get('template_vars'),
                        customer_id=msg_data.get('customer_id'),
                        campaign_id=campaign_id
                    )
                    
                    if message_id:
                        results['queued'] += 1
                        results['message_ids'].append(message_id)
                    else:
                        results['failed'] += 1
                        
                except Exception as e:
                    logger.error(f"Error en mensaje masivo: {e}")
                    results['failed'] += 1
            
            return results
            
        except Exception as e:
            logger.error(f"Error en envío masivo: {e}")
            return {'error': str(e)}
    
    def create_template(self, template_data: Dict[str, Any]) -> str:
        """Crear plantilla"""
        try:
            template = Template(
                id=template_data.get('id') or self._generate_template_id(),
                name=template_data['name'],
                channel=CommunicationChannel(template_data['channel']),
                subject_template=template_data.get('subject_template', ''),
                content_template=template_data['content_template'],
                variables=template_data.get('variables', []),
                is_active=template_data.get('is_active', True),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                category=template_data.get('category', 'general')
            )
            
            # Validar plantilla
            errors = self.template_engine.validate_template(template)
            if errors:
                raise ValueError(f"Template inválido: {errors}")
            
            # Guardar en base de datos
            query = """
            INSERT OR REPLACE INTO message_templates 
            (id, name, channel, subject_template, content_template, 
             variables, is_active, created_at, updated_at, category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                template.id, template.name, template.channel.value,
                template.subject_template, template.content_template,
                json.dumps(template.variables), template.is_active,
                template.created_at.isoformat(), template.updated_at.isoformat(),
                template.category
            )
            
            self.db_manager.execute_query(query, params)
            
            # Limpiar cache
            self.templates_cache.clear()
            
            logger.info(f"Template {template.id} creado exitosamente")
            return template.id
            
        except Exception as e:
            logger.error(f"Error creando template: {e}")
            return None
    
    def get_template(self, template_id: str) -> Optional[Template]:
        """Obtener plantilla"""
        try:
            # Verificar cache
            if template_id in self.templates_cache:
                return self.templates_cache[template_id]
            
            query = "SELECT * FROM message_templates WHERE id = ? AND is_active = 1"
            result = self.db_manager.execute_query(query, (template_id,))
            
            if result:
                row = result[0]
                template = Template(
                    id=row['id'],
                    name=row['name'],
                    channel=CommunicationChannel(row['channel']),
                    subject_template=row['subject_template'],
                    content_template=row['content_template'],
                    variables=json.loads(row['variables']) if row['variables'] else [],
                    is_active=bool(row['is_active']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']),
                    category=row['category']
                )
                
                # Guardar en cache
                self.templates_cache[template_id] = template
                return template
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo template {template_id}: {e}")
            return None
    
    def get_templates(self, channel: CommunicationChannel = None, 
                     category: str = None, active_only: bool = True) -> List[Template]:
        """Obtener lista de plantillas"""
        try:
            query = "SELECT * FROM message_templates WHERE 1=1"
            params = []
            
            if active_only:
                query += " AND is_active = 1"
            
            if channel:
                query += " AND channel = ?"
                params.append(channel.value)
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            query += " ORDER BY name"
            
            results = self.db_manager.execute_query(query, params)
            templates = []
            
            for row in results:
                template = Template(
                    id=row['id'],
                    name=row['name'],
                    channel=CommunicationChannel(row['channel']),
                    subject_template=row['subject_template'],
                    content_template=row['content_template'],
                    variables=json.loads(row['variables']) if row['variables'] else [],
                    is_active=bool(row['is_active']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']),
                    category=row['category']
                )
                templates.append(template)
            
            return templates
            
        except Exception as e:
            logger.error(f"Error obteniendo templates: {e}")
            return []
    
    def create_campaign(self, name: str, description: str, channel: CommunicationChannel,
                       template_id: str, target_segments: List[str],
                       scheduled_at: datetime = None) -> str:
        """Crear campaña"""
        try:
            campaign_id = self._generate_campaign_id()
            
            # Obtener destinatarios según segmentos
            recipients = self._get_campaign_recipients(target_segments)
            
            campaign = Campaign(
                id=campaign_id,
                name=name,
                description=description,
                channel=channel,
                template_id=template_id,
                target_segments=target_segments,
                scheduled_at=scheduled_at,
                started_at=None,
                completed_at=None,
                status='created',
                total_recipients=len(recipients),
                sent_count=0,
                delivered_count=0,
                failed_count=0,
                metadata={}
            )
            
            # Guardar campaña
            query = """
            INSERT INTO campaigns 
            (id, name, description, channel, template_id, target_segments,
             scheduled_at, status, total_recipients, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                campaign.id, campaign.name, campaign.description,
                campaign.channel.value, campaign.template_id,
                json.dumps(campaign.target_segments),
                campaign.scheduled_at.isoformat() if campaign.scheduled_at else None,
                campaign.status, campaign.total_recipients,
                json.dumps(campaign.metadata)
            )
            
            self.db_manager.execute_query(query, params)
            
            logger.info(f"Campaña {campaign_id} creada con {len(recipients)} destinatarios")
            return campaign_id
            
        except Exception as e:
            logger.error(f"Error creando campaña: {e}")
            return None
    
    def launch_campaign(self, campaign_id: str) -> bool:
        """Lanzar campaña"""
        try:
            # Obtener campaña
            campaign = self._get_campaign(campaign_id)
            if not campaign:
                return False
            
            # Obtener template
            template = self.get_template(campaign.template_id)
            if not template:
                logger.error(f"Template {campaign.template_id} no encontrado")
                return False
            
            # Obtener destinatarios
            recipients = self._get_campaign_recipients(campaign.target_segments)
            
            # Preparar mensajes
            messages_data = []
            for recipient in recipients:
                # Obtener variables específicas del destinatario
                template_vars = self._get_recipient_variables(recipient, template.variables)
                
                messages_data.append({
                    'channel': campaign.channel.value,
                    'recipient': recipient['contact'],
                    'subject': template.subject_template,
                    'content': template.content_template,
                    'template_id': template.id,
                    'template_vars': template_vars,
                    'customer_id': recipient.get('customer_id'),
                    'priority': MessagePriority.NORMAL.value
                })
            
            # Enviar mensajes masivos
            results = self.send_bulk_messages(messages_data, campaign_id)
            
            # Actualizar campaña
            self._update_campaign(campaign_id, {
                'status': 'launched',
                'started_at': datetime.now(),
                'sent_count': results.get('queued', 0),
                'failed_count': results.get('failed', 0)
            })
            
            logger.info(f"Campaña {campaign_id} lanzada: {results}")
            return True
            
        except Exception as e:
            logger.error(f"Error lanzando campaña {campaign_id}: {e}")
            return False
    
    def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """Obtener estado de mensaje"""
        try:
            query = "SELECT * FROM messages WHERE id = ?"
            result = self.db_manager.execute_query(query, (message_id,))
            
            if result:
                row = result[0]
                return {
                    'id': row['id'],
                    'status': row['status'],
                    'channel': row['channel'],
                    'recipient': row['recipient'],
                    'created_at': row['created_at'],
                    'sent_at': row['sent_at'],
                    'delivered_at': row['delivered_at'],
                    'read_at': row['read_at'],
                    'error_message': row['error_message']
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo estado del mensaje: {e}")
            return None
    
    def get_communication_history(self, customer_id: int = None, 
                                 channel: CommunicationChannel = None,
                                 limit: int = 100) -> List[Dict[str, Any]]:
        """Obtener historial de comunicaciones"""
        try:
            query = "SELECT * FROM messages WHERE 1=1"
            params = []
            
            if customer_id:
                query += " AND customer_id = ?"
                params.append(customer_id)
            
            if channel:
                query += " AND channel = ?"
                params.append(channel.value)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            results = self.db_manager.execute_query(query, params)
            return [dict(row) for row in results] if results else []
            
        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")
            return []
    
    def get_communication_stats(self, days: int = 30) -> Dict[str, Any]:
        """Obtener estadísticas de comunicación"""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Total mensajes
            query = "SELECT COUNT(*) as total FROM messages WHERE created_at >= ?"
            total_result = self.db_manager.execute_query(query, (start_date,))
            total = total_result[0]['total'] if total_result else 0
            
            # Por canal
            query = """
            SELECT channel, COUNT(*) as count 
            FROM messages 
            WHERE created_at >= ? 
            GROUP BY channel
            """
            channel_results = self.db_manager.execute_query(query, (start_date,))
            by_channel = {row['channel']: row['count'] for row in channel_results} if channel_results else {}
            
            # Por estado
            query = """
            SELECT status, COUNT(*) as count 
            FROM messages 
            WHERE created_at >= ? 
            GROUP BY status
            """
            status_results = self.db_manager.execute_query(query, (start_date,))
            by_status = {row['status']: row['count'] for row in status_results} if status_results else {}
            
            # Tasa de éxito
            sent = by_status.get('sent', 0)
            failed = by_status.get('failed', 0)
            success_rate = (sent / (sent + failed) * 100) if (sent + failed) > 0 else 0
            
            return {
                'period_days': days,
                'total_messages': total,
                'by_channel': by_channel,
                'by_status': by_status,
                'success_rate': round(success_rate, 2),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    # Métodos automáticos de notificación
    def notify_new_customer(self, customer_id: int):
        """Notificar nuevo cliente"""
        try:
            if not self.config['general']['auto_notifications']:
                return
            
            # Obtener datos del cliente
            customer = self._get_customer_data(customer_id)
            if not customer:
                return
            
            # Enviar email de bienvenida
            if customer.get('email') and self.email_provider:
                template_vars = {
                    'customer_name': customer['nombre'],
                    'customer_id': str(customer['id']),
                    'company_name': 'AlmacénPro'
                }
                
                self.send_message(
                    channel=CommunicationChannel.EMAIL,
                    recipient=customer['email'],
                    subject='',
                    content='',
                    template_id='email_welcome',
                    template_vars=template_vars,
                    customer_id=customer_id,
                    priority=MessagePriority.NORMAL
                )
            
        except Exception as e:
            logger.error(f"Error notificando nuevo cliente: {e}")
    
    def notify_purchase_confirmation(self, sale_id: int, customer_id: int):
        """Notificar confirmación de compra"""
        try:
            if not self.config['general']['auto_notifications']:
                return
            
            # Obtener datos de la venta y cliente
            customer = self._get_customer_data(customer_id)
            sale = self._get_sale_data(sale_id)
            
            if not customer or not sale:
                return
            
            template_vars = {
                'customer_name': customer['nombre'],
                'order_number': f"{sale_id:06d}",
                'order_date': sale['fecha_venta'],
                'total_amount': f"{sale['total']:,.2f}"
            }
            
            # Email
            if customer.get('email') and self.email_provider:
                self.send_message(
                    channel=CommunicationChannel.EMAIL,
                    recipient=customer['email'],
                    subject='',
                    content='',
                    template_id='email_purchase_confirmation',
                    template_vars=template_vars,
                    customer_id=customer_id,
                    priority=MessagePriority.HIGH
                )
            
            # WhatsApp
            if customer.get('telefono') and self.whatsapp_provider:
                whatsapp_content = f"""¡Gracias por tu compra {customer['nombre']}!
                
Pedido: #{sale_id:06d}
Total: ${sale['total']:,.2f}
Fecha: {sale['fecha_venta']}

Te notificaremos cuando esté listo."""
                
                self.send_message(
                    channel=CommunicationChannel.WHATSAPP,
                    recipient=customer['telefono'],
                    subject='',
                    content=whatsapp_content,
                    customer_id=customer_id,
                    priority=MessagePriority.HIGH
                )
            
        except Exception as e:
            logger.error(f"Error notificando compra: {e}")
    
    def notify_payment_reminder(self, customer_id: int, amount: float):
        """Notificar recordatorio de pago"""
        try:
            customer = self._get_customer_data(customer_id)
            if not customer:
                return
            
            template_vars = {
                'customer_name': customer['nombre'],
                'amount': f"{amount:,.2f}",
                'company_name': 'AlmacénPro'
            }
            
            # WhatsApp preferido para recordatorios
            if customer.get('telefono') and self.whatsapp_provider:
                self.send_message(
                    channel=CommunicationChannel.WHATSAPP,
                    recipient=customer['telefono'],
                    subject='',
                    content='',
                    template_id='whatsapp_payment_reminder',
                    template_vars=template_vars,
                    customer_id=customer_id,
                    priority=MessagePriority.HIGH
                )
            
        except Exception as e:
            logger.error(f"Error notificando recordatorio de pago: {e}")
    
    # Métodos auxiliares privados
    def _generate_message_id(self) -> str:
        """Generar ID único para mensaje"""
        return f"msg_{int(datetime.now().timestamp() * 1000)}_{hash(str(datetime.now()))}"[:32]
    
    def _generate_template_id(self) -> str:
        """Generar ID único para template"""
        return f"tpl_{int(datetime.now().timestamp() * 1000)}"
    
    def _generate_campaign_id(self) -> str:
        """Generar ID único para campaña"""
        return f"cmp_{int(datetime.now().timestamp() * 1000)}"
    
    def _save_message(self, message: Message):
        """Guardar mensaje en base de datos"""
        query = """
        INSERT INTO messages 
        (id, channel, recipient, subject, content, template_id, template_vars,
         priority, scheduled_at, created_at, status, metadata, sender_id, 
         customer_id, campaign_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            message.id, message.channel.value, message.recipient,
            message.subject, message.content, message.template_id,
            json.dumps(message.template_vars) if message.template_vars else None,
            message.priority.value,
            message.scheduled_at.isoformat() if message.scheduled_at else None,
            message.created_at.isoformat(), message.status.value,
            json.dumps(message.metadata) if message.metadata else None,
            message.sender_id, message.customer_id, message.campaign_id
        )
        
        self.db_manager.execute_query(query, params)
    
    def _update_message_status(self, message: Message):
        """Actualizar estado del mensaje"""
        query = """
        UPDATE messages 
        SET status = ?, sent_at = ?, delivered_at = ?, read_at = ?, error_message = ?
        WHERE id = ?
        """
        
        params = (
            message.status.value,
            message.sent_at.isoformat() if message.sent_at else None,
            message.delivered_at.isoformat() if message.delivered_at else None,
            message.read_at.isoformat() if message.read_at else None,
            message.error_message,
            message.id
        )
        
        self.db_manager.execute_query(query, params)
    
    def _log_communication_event(self, message_id: str, event_type: str, event_data: Dict[str, Any]):
        """Registrar evento de comunicación"""
        query = """
        INSERT INTO communication_events (message_id, event_type, event_data, timestamp)
        VALUES (?, ?, ?, ?)
        """
        
        params = (
            message_id, event_type, json.dumps(event_data), datetime.now().isoformat()
        )
        
        self.db_manager.execute_query(query, params)
    
    def _get_customer_data(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """Obtener datos del cliente"""
        try:
            query = "SELECT * FROM clientes WHERE id = ?"
            result = self.db_manager.execute_query(query, (customer_id,))
            return dict(result[0]) if result else None
        except:
            return None
    
    def _get_sale_data(self, sale_id: int) -> Optional[Dict[str, Any]]:
        """Obtener datos de la venta"""
        try:
            query = "SELECT * FROM ventas WHERE id = ?"
            result = self.db_manager.execute_query(query, (sale_id,))
            return dict(result[0]) if result else None
        except:
            return None
    
    def _get_campaign_recipients(self, target_segments: List[str]) -> List[Dict[str, Any]]:
        """Obtener destinatarios de campaña según segmentos"""
        try:
            recipients = []
            
            # Implementación básica - expandir según necesidades
            if 'all_customers' in target_segments:
                query = "SELECT id, nombre, email, telefono FROM clientes WHERE activo = 1"
                results = self.db_manager.execute_query(query)
                
                for row in results:
                    if row['email']:
                        recipients.append({
                            'customer_id': row['id'],
                            'name': row['nombre'],
                            'contact': row['email'],
                            'type': 'email'
                        })
                    if row['telefono']:
                        recipients.append({
                            'customer_id': row['id'],
                            'name': row['nombre'],
                            'contact': row['telefono'],
                            'type': 'phone'
                        })
            
            return recipients
            
        except Exception as e:
            logger.error(f"Error obteniendo destinatarios de campaña: {e}")
            return []
    
    def _get_recipient_variables(self, recipient: Dict[str, Any], 
                               required_vars: List[str]) -> Dict[str, Any]:
        """Obtener variables para destinatario específico"""
        try:
            variables = {}
            
            # Variables básicas
            variables['customer_name'] = recipient.get('name', 'Cliente')
            variables['customer_id'] = str(recipient.get('customer_id', ''))
            variables['company_name'] = 'AlmacénPro'
            
            # Agregar variables específicas según necesidad
            for var in required_vars:
                if var not in variables:
                    variables[var] = ''  # Valor por defecto
            
            return variables
            
        except Exception as e:
            logger.error(f"Error obteniendo variables del destinatario: {e}")
            return {}
    
    def _get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Obtener campaña"""
        try:
            query = "SELECT * FROM campaigns WHERE id = ?"
            result = self.db_manager.execute_query(query, (campaign_id,))
            
            if result:
                row = result[0]
                return Campaign(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    channel=CommunicationChannel(row['channel']),
                    template_id=row['template_id'],
                    target_segments=json.loads(row['target_segments']) if row['target_segments'] else [],
                    scheduled_at=datetime.fromisoformat(row['scheduled_at']) if row['scheduled_at'] else None,
                    started_at=datetime.fromisoformat(row['started_at']) if row['started_at'] else None,
                    completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
                    status=row['status'],
                    total_recipients=row['total_recipients'],
                    sent_count=row['sent_count'],
                    delivered_count=row['delivered_count'],
                    failed_count=row['failed_count'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo campaña: {e}")
            return None
    
    def _update_campaign(self, campaign_id: str, updates: Dict[str, Any]):
        """Actualizar campaña"""
        try:
            set_clauses = []
            params = []
            
            for key, value in updates.items():
                set_clauses.append(f"{key} = ?")
                if isinstance(value, datetime):
                    params.append(value.isoformat())
                else:
                    params.append(value)
            
            params.append(campaign_id)
            
            query = f"UPDATE campaigns SET {', '.join(set_clauses)} WHERE id = ?"
            self.db_manager.execute_query(query, params)
            
        except Exception as e:
            logger.error(f"Error actualizando campaña: {e}")
    
    def cleanup(self):
        """Limpiar recursos"""
        try:
            self.message_queue.stop_processing()
            logger.info("Communication Manager limpiado correctamente")
        except Exception as e:
            logger.error(f"Error limpiando Communication Manager: {e}")
    
    def __del__(self):
        """Destructor"""
        self.cleanup()