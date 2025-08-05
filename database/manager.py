"""
Gestor de Base de Datos para AlmacénPro
Maneja todas las operaciones de base de datos con SQLite y PostgreSQL
"""

import sqlite3
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gestor principal de base de datos con soporte SQLite y PostgreSQL"""
    
    def __init__(self, settings):
        self.settings = settings
        self.db_type = settings.get('database.type', 'sqlite')
        self.connection = None
        self._lock = threading.RLock()
        
        if self.db_type == 'sqlite':
            self.db_path = settings.get_database_path()
            logger.info(f"Usando SQLite: {self.db_path}")
        else:
            # Para futuro soporte de PostgreSQL
            logger.info("PostgreSQL no implementado aún, usando SQLite")
            self.db_type = 'sqlite'
            self.db_path = settings.get_database_path()
        
        self.setup_database()
    
    def setup_database(self):
        """Configurar y crear todas las tablas necesarias"""
        try:
            # Crear directorio de base de datos si no existe
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            # Establecer conexión
            self.connection = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                timeout=30.0
            )
            self.connection.row_factory = sqlite3.Row
            
            # Configurar SQLite para mejor rendimiento
            cursor = self.connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=10000")
            cursor.execute("PRAGMA temp_store=MEMORY")
            
            # Crear todas las tablas
            self.create_tables()
            self.create_indexes()
            self.insert_default_data()
            
            logger.info("Base de datos configurada correctamente")
            
        except Exception as e:
            logger.error(f"Error configurando base de datos: {e}")
            raise
    
    @contextmanager
    def get_cursor(self):
        """Context manager para obtener cursor con manejo automático de transacciones"""
        with self._lock:
            cursor = self.connection.cursor()
            try:
                yield cursor
                self.connection.commit()
            except Exception as e:
                self.connection.rollback()
                logger.error(f"Error en transacción de base de datos: {e}")
                raise
            finally:
                cursor.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Ejecutar consulta SELECT y retornar resultados"""
        with self.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_single(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Ejecutar consulta SELECT y retornar un solo resultado"""
        with self.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Ejecutar consulta INSERT/UPDATE/DELETE y retornar filas afectadas"""
        with self.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.rowcount
    
    def execute_insert(self, query: str, params: tuple = None) -> int:
        """Ejecutar INSERT y retornar ID del registro insertado"""
        with self.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.lastrowid
    
    def create_tables(self):
        """Crear estructura completa de base de datos"""
        tables = {
            # Usuarios y roles
            'roles': '''
                CREATE TABLE IF NOT EXISTS roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre VARCHAR(50) UNIQUE NOT NULL,
                    descripcion TEXT,
                    permisos TEXT, -- JSON con permisos
                    activo BOOLEAN DEFAULT 1,
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            
            'usuarios': '''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    email VARCHAR(100),
                    nombre_completo VARCHAR(100),
                    rol_id INTEGER,
                    activo BOOLEAN DEFAULT 1,
                    ultimo_acceso TIMESTAMP,
                    intentos_login INTEGER DEFAULT 0,
                    bloqueado_hasta TIMESTAMP,
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (rol_id) REFERENCES roles(id)
                )
            ''',
            
            # Productos y categorías
            'categorias': '''
                CREATE TABLE IF NOT EXISTS categorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre VARCHAR(100) NOT NULL,
                    descripcion TEXT,
                    categoria_padre_id INTEGER,
                    activo BOOLEAN DEFAULT 1,
                    orden INTEGER DEFAULT 0,
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (categoria_padre_id) REFERENCES categorias(id)
                )
            ''',
            
            'productos': '''
                CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo_barras VARCHAR(50) UNIQUE,
                    codigo_interno VARCHAR(50),
                    nombre VARCHAR(200) NOT NULL,
                    descripcion TEXT,
                    categoria_id INTEGER,
                    precio_compra DECIMAL(10,2),
                    precio_venta DECIMAL(10,2),
                    precio_mayorista DECIMAL(10,2),
                    margen_ganancia DECIMAL(5,2),
                    stock_actual INTEGER DEFAULT 0,
                    stock_minimo INTEGER DEFAULT 0,
                    stock_maximo INTEGER DEFAULT 0,
                    unidad_medida VARCHAR(20) DEFAULT 'UNIDAD',
                    proveedor_id INTEGER,
                    ubicacion VARCHAR(100),
                    imagen_url VARCHAR(255),
                    iva_porcentaje DECIMAL(5,2) DEFAULT 21,
                    activo BOOLEAN DEFAULT 1,
                    es_produccion_propia BOOLEAN DEFAULT 0,
                    peso DECIMAL(8,3),
                    vencimiento DATE,
                    lote VARCHAR(50),
                    permite_venta_sin_stock BOOLEAN DEFAULT 0,
                    es_pesable BOOLEAN DEFAULT 0,
                    codigo_plu VARCHAR(10),
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (categoria_id) REFERENCES categorias(id),
                    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
                )
            ''',
            
            # Proveedores
            'proveedores': '''
                CREATE TABLE IF NOT EXISTS proveedores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre VARCHAR(200) NOT NULL,
                    cuit_dni VARCHAR(20),
                    direccion TEXT,
                    ciudad VARCHAR(100),
                    provincia VARCHAR(100),
                    codigo_postal VARCHAR(10),
                    telefono VARCHAR(50),
                    telefono_alternativo VARCHAR(50),
                    email VARCHAR(100),
                    sitio_web VARCHAR(200),
                    contacto_principal VARCHAR(100),
                    cargo_contacto VARCHAR(100),
                    condiciones_pago TEXT,
                    descuento_porcentaje DECIMAL(5,2) DEFAULT 0,
                    limite_credito DECIMAL(10,2) DEFAULT 0,
                    activo BOOLEAN DEFAULT 1,
                    calificacion INTEGER DEFAULT 5,
                    notas TEXT,
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            
            # Clientes
            'clientes': '''
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre VARCHAR(200) NOT NULL,
                    apellido VARCHAR(200),
                    dni_cuit VARCHAR(20),
                    direccion TEXT,
                    ciudad VARCHAR(100),
                    provincia VARCHAR(100),
                    codigo_postal VARCHAR(10),
                    telefono VARCHAR(50),
                    telefono_alternativo VARCHAR(50),
                    email VARCHAR(100),
                    fecha_nacimiento DATE,
                    limite_credito DECIMAL(10,2) DEFAULT 0,
                    saldo_cuenta_corriente DECIMAL(10,2) DEFAULT 0,
                    descuento_porcentaje DECIMAL(5,2) DEFAULT 0,
                    categoria_cliente VARCHAR(50) DEFAULT 'MINORISTA',
                    activo BOOLEAN DEFAULT 1,
                    es_consumidor_final BOOLEAN DEFAULT 1,
                    notas TEXT,
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            
            # Ventas
            'ventas': '''
                CREATE TABLE IF NOT EXISTS ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_ticket VARCHAR(50) UNIQUE,
                    numero_factura VARCHAR(50),
                    cliente_id INTEGER,
                    vendedor_id INTEGER NOT NULL,
                    caja_id INTEGER,
                    tipo_venta VARCHAR(20) DEFAULT 'CONTADO', -- CONTADO, CREDITO, CUENTA_CORRIENTE
                    tipo_comprobante VARCHAR(20) DEFAULT 'TICKET', -- TICKET, FACTURA_A, FACTURA_B, etc.
                    subtotal DECIMAL(10,2) NOT NULL,
                    descuento DECIMAL(10,2) DEFAULT 0,
                    recargo DECIMAL(10,2) DEFAULT 0,
                    impuestos DECIMAL(10,2) DEFAULT 0,
                    total DECIMAL(10,2) NOT NULL,
                    metodo_pago VARCHAR(50), -- EFECTIVO, TARJETA, TRANSFERENCIA, MULTIPLE
                    estado VARCHAR(20) DEFAULT 'COMPLETADA',
                    fecha_venta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_vencimiento DATE,
                    observaciones TEXT,
                    cae VARCHAR(20),
                    fecha_vto_cae DATE,
                    punto_venta INTEGER DEFAULT 1,
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
                    FOREIGN KEY (vendedor_id) REFERENCES usuarios(id),
                    FOREIGN KEY (caja_id) REFERENCES cajas(id)
                )
            ''',
            
            'detalle_ventas': '''
                CREATE TABLE IF NOT EXISTS detalle_ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venta_id INTEGER NOT NULL,
                    producto_id INTEGER NOT NULL,
                    cantidad DECIMAL(8,3) NOT NULL,
                    precio_unitario DECIMAL(10,2) NOT NULL,
                    descuento_porcentaje DECIMAL(5,2) DEFAULT 0,
                    descuento_importe DECIMAL(10,2) DEFAULT 0,
                    subtotal DECIMAL(10,2) NOT NULL,
                    iva_porcentaje DECIMAL(5,2) DEFAULT 21,
                    iva_importe DECIMAL(10,2) DEFAULT 0,
                    FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE,
                    FOREIGN KEY (producto_id) REFERENCES productos(id)
                )
            ''',
            
            # Compras
            'compras': '''
                CREATE TABLE IF NOT EXISTS compras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_factura VARCHAR(50),
                    numero_remito VARCHAR(50),
                    proveedor_id INTEGER NOT NULL,
                    usuario_id INTEGER NOT NULL,
                    subtotal DECIMAL(10,2) NOT NULL,
                    descuento DECIMAL(10,2) DEFAULT 0,
                    recargo DECIMAL(10,2) DEFAULT 0,
                    impuestos DECIMAL(10,2) DEFAULT 0,
                    total DECIMAL(10,2) NOT NULL,
                    fecha_compra TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_factura DATE,
                    fecha_vencimiento DATE,
                    estado VARCHAR(20) DEFAULT 'PENDIENTE',
                    tipo_comprobante VARCHAR(20) DEFAULT 'FACTURA',
                    observaciones TEXT,
                    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            ''',
            
            'detalle_compras': '''
                CREATE TABLE IF NOT EXISTS detalle_compras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    compra_id INTEGER NOT NULL,
                    producto_id INTEGER NOT NULL,
                    cantidad DECIMAL(8,3) NOT NULL,
                    cantidad_recibida DECIMAL(8,3) DEFAULT 0,
                    precio_unitario DECIMAL(10,2) NOT NULL,
                    descuento_porcentaje DECIMAL(5,2) DEFAULT 0,
                    descuento_importe DECIMAL(10,2) DEFAULT 0,
                    subtotal DECIMAL(10,2) NOT NULL,
                    iva_porcentaje DECIMAL(5,2) DEFAULT 21,
                    iva_importe DECIMAL(10,2) DEFAULT 0,
                    lote VARCHAR(50),
                    fecha_vencimiento DATE,
                    FOREIGN KEY (compra_id) REFERENCES compras(id) ON DELETE CASCADE,
                    FOREIGN KEY (producto_id) REFERENCES productos(id)
                )
            ''',
            
            # Movimientos de stock
            'movimientos_stock': '''
                CREATE TABLE IF NOT EXISTS movimientos_stock (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    producto_id INTEGER NOT NULL,
                    tipo_movimiento VARCHAR(20) NOT NULL, -- ENTRADA, SALIDA, AJUSTE
                    motivo VARCHAR(50), -- VENTA, COMPRA, DEVOLUCION, AJUSTE_INVENTARIO, PRODUCCION
                    cantidad_anterior DECIMAL(8,3),
                    cantidad_movimiento DECIMAL(8,3) NOT NULL,
                    cantidad_nueva DECIMAL(8,3),
                    precio_unitario DECIMAL(10,2),
                    usuario_id INTEGER,
                    referencia_id INTEGER, -- ID de venta/compra relacionada
                    referencia_tipo VARCHAR(20), -- VENTA, COMPRA, AJUSTE
                    fecha_movimiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    observaciones TEXT,
                    lote VARCHAR(50),
                    FOREIGN KEY (producto_id) REFERENCES productos(id),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            ''',
            
            # Cuentas corrientes
            'cuenta_corriente': '''
                CREATE TABLE IF NOT EXISTS cuenta_corriente (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER NOT NULL,
                    tipo_movimiento VARCHAR(20) NOT NULL, -- DEBE, HABER
                    concepto VARCHAR(100),
                    importe DECIMAL(10,2) NOT NULL,
                    saldo_anterior DECIMAL(10,2),
                    saldo_nuevo DECIMAL(10,2),
                    venta_id INTEGER,
                    fecha_movimiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_vencimiento DATE,
                    usuario_id INTEGER,
                    observaciones TEXT,
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
                    FOREIGN KEY (venta_id) REFERENCES ventas(id),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            ''',
            
            # Cajas
            'cajas': '''
                CREATE TABLE IF NOT EXISTS cajas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre VARCHAR(100) NOT NULL,
                    descripcion TEXT,
                    ubicacion VARCHAR(100),
                    impresora_ticket VARCHAR(200),
                    cajón_monedero BOOLEAN DEFAULT 0,
                    activo BOOLEAN DEFAULT 1,
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            
            'sesiones_caja': '''
                CREATE TABLE IF NOT EXISTS sesiones_caja (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    caja_id INTEGER NOT NULL,
                    usuario_id INTEGER NOT NULL,
                    fecha_apertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_cierre TIMESTAMP,
                    monto_apertura DECIMAL(10,2) DEFAULT 0,
                    monto_cierre DECIMAL(10,2) DEFAULT 0,
                    monto_ventas DECIMAL(10,2) DEFAULT 0,
                    monto_esperado DECIMAL(10,2) DEFAULT 0,
                    diferencia DECIMAL(10,2) DEFAULT 0,
                    estado VARCHAR(20) DEFAULT 'ABIERTA',
                    observaciones TEXT,
                    FOREIGN KEY (caja_id) REFERENCES cajas(id),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            ''',
            
            'movimientos_caja': '''
                CREATE TABLE IF NOT EXISTS movimientos_caja (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sesion_caja_id INTEGER NOT NULL,
                    tipo_movimiento VARCHAR(20) NOT NULL, -- APERTURA, VENTA, GASTO, INGRESO, CIERRE
                    concepto VARCHAR(100),
                    importe DECIMAL(10,2) NOT NULL,
                    saldo_anterior DECIMAL(10,2),
                    saldo_nuevo DECIMAL(10,2),
                    venta_id INTEGER,
                    metodo_pago VARCHAR(50),
                    fecha_movimiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    usuario_id INTEGER NOT NULL,
                    observaciones TEXT,
                    FOREIGN KEY (sesion_caja_id) REFERENCES sesiones_caja(id),
                    FOREIGN KEY (venta_id) REFERENCES ventas(id),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            ''',
            
            # Configuraciones
            'configuraciones': '''
                CREATE TABLE IF NOT EXISTS configuraciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    clave VARCHAR(100) UNIQUE NOT NULL,
                    valor TEXT,
                    descripcion TEXT,
                    tipo VARCHAR(20) DEFAULT 'STRING',
                    categoria VARCHAR(50) DEFAULT 'GENERAL',
                    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    usuario_id INTEGER,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            ''',
            
            # Backups y sincronización
            'sync_log': '''
                CREATE TABLE IF NOT EXISTS sync_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tabla VARCHAR(50),
                    operacion VARCHAR(20), -- INSERT, UPDATE, DELETE
                    registro_id INTEGER,
                    datos_json TEXT,
                    sincronizado BOOLEAN DEFAULT 0,
                    fecha_operacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_sincronizacion TIMESTAMP,
                    servidor_destino VARCHAR(100),
                    error_mensaje TEXT
                )
            ''',
            
            # Notificaciones
            'notificaciones': '''
                CREATE TABLE IF NOT EXISTS notificaciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo VARCHAR(50) NOT NULL,
                    titulo VARCHAR(200) NOT NULL,
                    mensaje TEXT,
                    usuario_id INTEGER,
                    leida BOOLEAN DEFAULT 0,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_lectura TIMESTAMP,
                    fecha_expiracion TIMESTAMP,
                    prioridad VARCHAR(20) DEFAULT 'NORMAL', -- BAJA, NORMAL, ALTA, CRITICA
                    categoria VARCHAR(50) DEFAULT 'SISTEMA',
                    datos_extra TEXT, -- JSON con datos adicionales
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            ''',
            
            # Auditoría
            'auditoria': '''
                CREATE TABLE IF NOT EXISTS auditoria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tabla VARCHAR(50) NOT NULL,
                    operacion VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
                    registro_id INTEGER,
                    datos_anteriores TEXT, -- JSON
                    datos_nuevos TEXT, -- JSON
                    usuario_id INTEGER,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    fecha_operacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            '''
        }
        
        with self.get_cursor() as cursor:
            for table_name, sql in tables.items():
                try:
                    cursor.execute(sql)
                    logger.info(f"Tabla {table_name} creada/verificada")
                except Exception as e:
                    logger.error(f"Error creando tabla {table_name}: {e}")
                    raise
    
    def create_indexes(self):
        """Crear índices para optimizar rendimiento"""
        indexes = [
            # Índices para productos
            "CREATE INDEX IF NOT EXISTS idx_productos_codigo_barras ON productos(codigo_barras)",
            "CREATE INDEX IF NOT EXISTS idx_productos_nombre ON productos(nombre)",
            "CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos(categoria_id)",
            "CREATE INDEX IF NOT EXISTS idx_productos_activo ON productos(activo)",
            "CREATE INDEX IF NOT EXISTS idx_productos_stock ON productos(stock_actual)",
            
            # Índices para ventas
            "CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha_venta)",
            "CREATE INDEX IF NOT EXISTS idx_ventas_cliente ON ventas(cliente_id)",
            "CREATE INDEX IF NOT EXISTS idx_ventas_vendedor ON ventas(vendedor_id)",
            "CREATE INDEX IF NOT EXISTS idx_ventas_estado ON ventas(estado)",
            "CREATE INDEX IF NOT EXISTS idx_ventas_numero_ticket ON ventas(numero_ticket)",
            
            # Índices para detalle de ventas
            "CREATE INDEX IF NOT EXISTS idx_detalle_ventas_venta ON detalle_ventas(venta_id)",
            "CREATE INDEX IF NOT EXISTS idx_detalle_ventas_producto ON detalle_ventas(producto_id)",
            
            # Índices para compras
            "CREATE INDEX IF NOT EXISTS idx_compras_fecha ON compras(fecha_compra)",
            "CREATE INDEX IF NOT EXISTS idx_compras_proveedor ON compras(proveedor_id)",
            "CREATE INDEX IF NOT EXISTS idx_compras_estado ON compras(estado)",
            
            # Índices para movimientos de stock
            "CREATE INDEX IF NOT EXISTS idx_movimientos_stock_producto ON movimientos_stock(producto_id)",
            "CREATE INDEX IF NOT EXISTS idx_movimientos_stock_fecha ON movimientos_stock(fecha_movimiento)",
            "CREATE INDEX IF NOT EXISTS idx_movimientos_stock_tipo ON movimientos_stock(tipo_movimiento)",
            
            # Índices para cuenta corriente
            "CREATE INDEX IF NOT EXISTS idx_cuenta_corriente_cliente ON cuenta_corriente(cliente_id)",
            "CREATE INDEX IF NOT EXISTS idx_cuenta_corriente_fecha ON cuenta_corriente(fecha_movimiento)",
            
            # Índices para usuarios y seguridad
            "CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username)",
            "CREATE INDEX IF NOT EXISTS idx_usuarios_activo ON usuarios(activo)",
            "CREATE INDEX IF NOT EXISTS idx_usuarios_ultimo_acceso ON usuarios(ultimo_acceso)",
            
            # Índices para sincronización
            "CREATE INDEX IF NOT EXISTS idx_sync_log_sincronizado ON sync_log(sincronizado)",
            "CREATE INDEX IF NOT EXISTS idx_sync_log_fecha ON sync_log(fecha_operacion)",
            
            # Índices para notificaciones
            "CREATE INDEX IF NOT EXISTS idx_notificaciones_usuario ON notificaciones(usuario_id)",
            "CREATE INDEX IF NOT EXISTS idx_notificaciones_leida ON notificaciones(leida)",
            "CREATE INDEX IF NOT EXISTS idx_notificaciones_fecha ON notificaciones(fecha_creacion)",
            
            # Índices para auditoría
            "CREATE INDEX IF NOT EXISTS idx_auditoria_tabla ON auditoria(tabla)",
            "CREATE INDEX IF NOT EXISTS idx_auditoria_usuario ON auditoria(usuario_id)",
            "CREATE INDEX IF NOT EXISTS idx_auditoria_fecha ON auditoria(fecha_operacion)"
        ]
        
        with self.get_cursor() as cursor:
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                except Exception as e:
                    logger.error(f"Error creando índice: {e}")
    
    def insert_default_data(self):
        """Insertar datos por defecto del sistema"""
        with self.get_cursor() as cursor:
            
            # Roles por defecto
            roles_default = [
                ('ADMIN', 'Administrador', '{"all": true}'),
                ('GERENTE', 'Gerente', '{"ventas": true, "compras": true, "reportes": true, "stock": true, "configuracion": true}'),
                ('VENDEDOR', 'Vendedor', '{"ventas": true, "clientes": true}'),
                ('STOCK', 'Encargado de Stock', '{"stock": true, "productos": true, "compras": true}'),
                ('CAJA', 'Cajero', '{"ventas": true, "caja": true}'),
                ('CONSULTA', 'Solo Consulta', '{"reportes": true}')
            ]
            
            for nombre, descripcion, permisos in roles_default:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO roles (nombre, descripcion, permisos) 
                        VALUES (?, ?, ?)
                    """, (nombre, descripcion, permisos))
                except Exception as e:
                    logger.error(f"Error insertando rol {nombre}: {e}")
            
            # Usuario administrador por defecto
            import hashlib
            admin_password = hashlib.sha256("admin123".encode()).hexdigest()
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO usuarios (username, password_hash, nombre_completo, rol_id) 
                    VALUES ('admin', ?, 'Administrador del Sistema', 1)
                """, (admin_password,))
            except Exception as e:
                logger.error(f"Error creando usuario admin: {e}")
            
            # Categorías por defecto
            categorias_default = [
                ('GENERAL', 'Productos generales', None, 0),
                ('ALIMENTACION', 'Alimentos y bebidas', None, 1),
                ('LIMPIEZA', 'Productos de limpieza', None, 2),
                ('PERFUMERIA', 'Perfumería y cosmética', None, 3),
                ('PANADERIA', 'Panadería y repostería', 2, 4),
                ('FIAMBRERIA', 'Fiambres y lácteos', 2, 5),
                ('CARNICERIA', 'Carnes y embutidos', 2, 6),
                ('BEBIDAS', 'Bebidas y refrescos', 2, 7),
                ('GOLOSINAS', 'Golosinas y snacks', 2, 8),
                ('CIGARRILLOS', 'Cigarrillos y tabaco', None, 9),
                ('LIBRERIA', 'Librería y papelería', None, 10)
            ]
            
            for nombre, descripcion, padre_id, orden in categorias_default:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO categorias (nombre, descripcion, categoria_padre_id, orden) 
                        VALUES (?, ?, ?, ?)
                    """, (nombre, descripcion, padre_id, orden))
                except Exception as e:
                    logger.error(f"Error insertando categoría {nombre}: {e}")
            
            # Caja por defecto
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO cajas (id, nombre, descripcion, activo) 
                    VALUES (1, 'Caja Principal', 'Caja principal del local', 1)
                """)
            except Exception as e:
                logger.error(f"Error creando caja por defecto: {e}")
            
            # Configuraciones por defecto
            config_default = [
                ('empresa_nombre', 'Mi Almacén', 'Nombre de la empresa', 'STRING', 'EMPRESA'),
                ('empresa_direccion', '', 'Dirección de la empresa', 'STRING', 'EMPRESA'),
                ('empresa_telefono', '', 'Teléfono de la empresa', 'STRING', 'EMPRESA'),
                ('empresa_email', '', 'Email de la empresa', 'STRING', 'EMPRESA'),
                ('empresa_cuit', '', 'CUIT de la empresa', 'STRING', 'EMPRESA'),
                ('empresa_logo', '', 'Ruta del logo de la empresa', 'STRING', 'EMPRESA'),
                
                ('ticket_pie_mensaje', 'Gracias por su compra', 'Mensaje al pie del ticket', 'STRING', 'TICKETS'),
                ('ticket_incluir_logo', 'false', 'Incluir logo en ticket', 'BOOLEAN', 'TICKETS'),
                ('ticket_auto_imprimir', 'false', 'Imprimir automáticamente', 'BOOLEAN', 'TICKETS'),
                ('ticket_copias', '1', 'Número de copias', 'INTEGER', 'TICKETS'),
                
                ('impresora_tickets', '', 'Impresora para tickets', 'STRING', 'HARDWARE'),
                ('cajon_monedero_habilitado', 'false', 'Cajón monedero habilitado', 'BOOLEAN', 'HARDWARE'),
                ('scanner_habilitado', 'true', 'Scanner de códigos habilitado', 'BOOLEAN', 'HARDWARE'),
                
                ('backup_automatico', 'true', 'Backup automático habilitado', 'BOOLEAN', 'BACKUP'),
                ('backup_intervalo_horas', '24', 'Intervalo de backup en horas', 'INTEGER', 'BACKUP'),
                ('backup_max_archivos', '30', 'Máximo número de backups', 'INTEGER', 'BACKUP'),
                
                ('sync_habilitado', 'false', 'Sincronización habilitada', 'BOOLEAN', 'SYNC'),
                ('sync_servidor_url', '', 'URL del servidor de sincronización', 'STRING', 'SYNC'),
                ('sync_api_key', '', 'Clave API para sincronización', 'STRING', 'SYNC'),
                
                ('notificaciones_habilitadas', 'true', 'Notificaciones habilitadas', 'BOOLEAN', 'NOTIFICACIONES'),
                ('notificaciones_stock_bajo', 'true', 'Alertas de stock bajo', 'BOOLEAN', 'NOTIFICACIONES'),
                ('notificaciones_ventas_diarias', 'true', 'Resumen diario de ventas', 'BOOLEAN', 'NOTIFICACIONES'),
                
                ('tema_interfaz', 'light', 'Tema de la interfaz', 'STRING', 'UI'),
                ('idioma', 'es', 'Idioma de la interfaz', 'STRING', 'UI'),
                ('fuente_tamaño', '9', 'Tamaño de fuente', 'INTEGER', 'UI'),
                
                ('pos_modo_rapido', 'true', 'Modo rápido de ventas', 'BOOLEAN', 'POS'),
                ('pos_confirmar_eliminacion', 'true', 'Confirmar eliminación de items', 'BOOLEAN', 'POS'),
                ('pos_scanner_auto_agregar', 'true', 'Agregar automáticamente al escanear', 'BOOLEAN', 'POS')
            ]
            
            for clave, valor, descripcion, tipo, categoria in config_default:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO configuraciones (clave, valor, descripcion, tipo, categoria) 
                        VALUES (?, ?, ?, ?, ?)
                    """, (clave, valor, descripcion, tipo, categoria))
                except Exception as e:
                    logger.error(f"Error insertando configuración {clave}: {e}")
            
            logger.info("Datos por defecto insertados correctamente")
    
    def get_database_version(self) -> str:
        """Obtener versión de la base de datos"""
        try:
            result = self.execute_single("SELECT valor FROM configuraciones WHERE clave = 'db_version'")
            return result['valor'] if result else '1.0'
        except:
            return '1.0'
    
    def update_database_version(self, version: str):
        """Actualizar versión de la base de datos"""
        try:
            self.execute_update("""
                INSERT OR REPLACE INTO configuraciones (clave, valor, descripcion, categoria)
                VALUES ('db_version', ?, 'Versión de la base de datos', 'SISTEMA')
            """, (version,))
        except Exception as e:
            logger.error(f"Error actualizando versión de BD: {e}")
    
    def vacuum_database(self):
        """Optimizar base de datos (VACUUM)"""
        try:
            with self._lock:
                self.connection.execute("VACUUM")
                logger.info("Base de datos optimizada (VACUUM)")
        except Exception as e:
            logger.error(f"Error ejecutando VACUUM: {e}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de la base de datos"""
        try:
            stats = {}
            
            # Tamaño de la base de datos
            if hasattr(self, 'db_path'):
                db_file = Path(self.db_path)
                if db_file.exists():
                    stats['file_size_mb'] = db_file.stat().st_size / (1024 * 1024)
            
            # Contar registros en tablas principales
            tables = [
                'productos', 'ventas', 'compras', 'clientes', 
                'proveedores', 'movimientos_stock', 'usuarios'
            ]
            
            for table in tables:
                try:
                    result = self.execute_single(f"SELECT COUNT(*) as count FROM {table}")
                    stats[f'{table}_count'] = result['count'] if result else 0
                except:
                    stats[f'{table}_count'] = 0
            
            # Información de la base de datos
            with self.get_cursor() as cursor:
                cursor.execute("PRAGMA page_count")
                page_count = cursor.fetchone()[0]
                
                cursor.execute("PRAGMA page_size")
                page_size = cursor.fetchone()[0]
                
                stats['total_pages'] = page_count
                stats['page_size'] = page_size
                stats['estimated_size_mb'] = (page_count * page_size) / (1024 * 1024)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de BD: {e}")
            return {}
    
    def close(self):
        """Cerrar conexión a la base de datos"""
        if self.connection:
            try:
                self.connection.close()
                logger.info("Conexión a base de datos cerrada")
            except Exception as e:
                logger.error(f"Error cerrando conexión: {e}")
    
    def __del__(self):
        """Cerrar conexión al destruir el objeto"""
        self.close()