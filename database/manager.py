"""
Gestor de Base de Datos para AlmacénPro
Sistema completo de gestión de base de datos con SQLite
Incluye creación de tablas, índices, triggers y validaciones
"""

import sqlite3
import logging
import os
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gestor principal de base de datos con soporte completo SQLite"""
    
    def __init__(self, db_path: str = None):
        # Import here to avoid circular imports
        from config.settings import settings
        
        if db_path is None:
            db_path = settings.get_database_path()
        
        self.db_path = Path(db_path)
        self.connection = None
        self.cursor = None
        self.thread_lock = threading.Lock()
        
        # Configuraciones de conexión
        self.connection_config = {
            'check_same_thread': False,
            'timeout': 30.0,
            'isolation_level': None  # Autocommit mode
        }
        
        self.logger = logging.getLogger(__name__)
        
        # Inicializar base de datos
        self.setup_database()
    
    def setup_database(self):
        """Configurar y crear base de datos completa"""
        try:
            # Crear directorio si no existe
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Conectar a la base de datos
            self.connect()
            
            # Configurar SQLite
            self._configure_sqlite()
            
            # Crear todas las tablas
            self._create_all_tables()
            
            # Crear índices
            self._create_indexes()
            
            # Crear triggers
            self._create_triggers()
            
            # Insertar datos por defecto
            self._insert_default_data()
            
            # Optimizar base de datos
            self._optimize_database()
            
            self.logger.info("Base de datos configurada exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error configurando base de datos: {e}")
            raise e
    
    def connect(self):
        """Establecer conexión con la base de datos"""
        try:
            self.connection = sqlite3.connect(str(self.db_path), **self.connection_config)
            self.connection.row_factory = sqlite3.Row  # Acceso por nombre de columna
            self.cursor = self.connection.cursor()
            
        except Exception as e:
            self.logger.error(f"Error conectando a base de datos: {e}")
            raise e
    
    def close_connection(self):
        """Cerrar conexión de base de datos"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
                
            self.logger.info("Conexión de base de datos cerrada")
            
        except Exception as e:
            self.logger.error(f"Error cerrando conexión: {e}")
    
    def _configure_sqlite(self):
        """Configurar SQLite para rendimiento y integridad optimizados"""
        configurations = [
            "PRAGMA foreign_keys = ON",
            "PRAGMA journal_mode = WAL",
            "PRAGMA synchronous = NORMAL",
            "PRAGMA cache_size = 10000",
            "PRAGMA temp_store = MEMORY",
            "PRAGMA mmap_size = 268435456",  # 256MB
            "PRAGMA optimize"
        ]
        
        for config in configurations:
            self.cursor.execute(config)
        
        self.connection.commit()
    
    def _create_all_tables(self):
        """Crear todas las tablas del sistema"""
        tables = {
            # Usuarios y roles
            'roles': '''
                CREATE TABLE IF NOT EXISTS roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre VARCHAR(50) UNIQUE NOT NULL,
                    descripcion TEXT,
                    permisos TEXT,
                    activo BOOLEAN DEFAULT 1,
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    creado_por INTEGER,
                    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    actualizado_por INTEGER,
                    FOREIGN KEY (creado_por) REFERENCES usuarios(id)
                )
            ''',
            
            'usuarios': '''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    email VARCHAR(100) UNIQUE,
                    nombre_completo VARCHAR(100) NOT NULL,
                    telefono VARCHAR(20),
                    rol_id INTEGER,
                    activo BOOLEAN DEFAULT 1,
                    ultimo_acceso TIMESTAMP,
                    intentos_fallidos INTEGER DEFAULT 0,
                    bloqueado_hasta TIMESTAMP,
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    creado_por INTEGER,
                    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    actualizado_por INTEGER,
                    FOREIGN KEY (rol_id) REFERENCES roles(id),
                    FOREIGN KEY (creado_por) REFERENCES usuarios(id),
                    FOREIGN KEY (actualizado_por) REFERENCES usuarios(id)
                )
            ''',
            
            # Categorías y proveedores
            'categorias': '''
                CREATE TABLE IF NOT EXISTS categorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre VARCHAR(100) UNIQUE NOT NULL,
                    descripcion TEXT,
                    color VARCHAR(7) DEFAULT '#3498db',
                    icono VARCHAR(50),
                    activo BOOLEAN DEFAULT 1,
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            
            'proveedores': '''
                CREATE TABLE IF NOT EXISTS proveedores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo VARCHAR(20) UNIQUE,
                    nombre VARCHAR(100) NOT NULL,
                    razon_social VARCHAR(150),
                    cuit_cuil VARCHAR(15),
                    telefono VARCHAR(20),
                    email VARCHAR(100),
                    direccion TEXT,
                    ciudad VARCHAR(100),
                    provincia VARCHAR(100),
                    codigo_postal VARCHAR(10),
                    contacto_nombre VARCHAR(100),
                    contacto_telefono VARCHAR(20),
                    contacto_email VARCHAR(100),
                    condicion_iva VARCHAR(50) DEFAULT 'RESPONSABLE_INSCRIPTO',
                    dias_pago INTEGER DEFAULT 30,
                    limite_credito DECIMAL(12,2) DEFAULT 0,
                    activo BOOLEAN DEFAULT 1,
                    observaciones TEXT,
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            
            # Productos  
            'productos': '''
                CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo_barras VARCHAR(50) UNIQUE,
                    codigo_interno VARCHAR(50) UNIQUE NOT NULL,
                    codigo_plu VARCHAR(20),
                    nombre VARCHAR(200) NOT NULL,
                    descripcion TEXT,
                    categoria_id INTEGER,
                    proveedor_id INTEGER,
                    
                    -- Precios
                    precio_compra DECIMAL(10,2) DEFAULT 0,
                    precio_venta DECIMAL(10,2) NOT NULL,
                    precio_mayorista DECIMAL(10,2) DEFAULT 0,
                    margen_ganancia DECIMAL(5,2) DEFAULT 0,
                    
                    -- Stock
                    stock_actual DECIMAL(8,3) DEFAULT 0,
                    stock_minimo DECIMAL(8,3) DEFAULT 0,
                    stock_maximo DECIMAL(8,3) DEFAULT 0,
                    stock_reservado DECIMAL(8,3) DEFAULT 0,
                    
                    -- Características
                    unidad_medida VARCHAR(20) DEFAULT 'UNIDAD',
                    peso DECIMAL(8,3),
                    volumen DECIMAL(8,3),
                    es_pesable BOOLEAN DEFAULT 0,
                    es_produccion_propia BOOLEAN DEFAULT 0,
                    permite_venta_sin_stock BOOLEAN DEFAULT 0,
                    requiere_lote BOOLEAN DEFAULT 0,
                    
                    -- Impuestos
                    iva_porcentaje DECIMAL(5,2) DEFAULT 21,
                    impuestos_internos DECIMAL(5,2) DEFAULT 0,
                    
                    -- Ubicación y otros
                    ubicacion VARCHAR(100),
                    imagen_url VARCHAR(500),
                    observaciones TEXT,
                    
                    -- Trazabilidad
                    lote VARCHAR(50),
                    fecha_vencimiento DATE,
                    
                    -- Control
                    activo BOOLEAN DEFAULT 1,
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (categoria_id) REFERENCES categorias(id),
                    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
                )
            ''',
            
            # Clientes
            'clientes': '''
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo VARCHAR(20) UNIQUE,
                    tipo_documento VARCHAR(20) DEFAULT 'DNI',
                    numero_documento VARCHAR(20),
                    nombre VARCHAR(100) NOT NULL,
                    apellido VARCHAR(100),
                    razon_social VARCHAR(150),
                    cuit_cuil VARCHAR(15),
                    telefono VARCHAR(20),
                    email VARCHAR(100),
                    fecha_nacimiento DATE,
                    
                    -- Dirección
                    direccion TEXT,
                    ciudad VARCHAR(100),
                    provincia VARCHAR(100),
                    codigo_postal VARCHAR(10),
                    
                    -- Comercial
                    condicion_iva VARCHAR(50) DEFAULT 'CONSUMIDOR_FINAL',
                    precio_lista VARCHAR(20) DEFAULT 'VENTA',
                    limite_credito DECIMAL(12,2) DEFAULT 0,
                    descuento_porcentaje DECIMAL(5,2) DEFAULT 0,
                    
                    -- Control
                    activo BOOLEAN DEFAULT 1,
                    observaciones TEXT,
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            
            # Ventas
            'ventas': '''
                CREATE TABLE IF NOT EXISTS ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_factura VARCHAR(50) UNIQUE NOT NULL,
                    tipo_comprobante VARCHAR(20) DEFAULT 'TICKET',
                    punto_venta INTEGER DEFAULT 1,
                    
                    -- Partes involucradas
                    cliente_id INTEGER,
                    usuario_id INTEGER NOT NULL,
                    caja_id INTEGER,
                    
                    -- Fechas
                    fecha_venta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_vencimiento DATE,
                    
                    -- Importes
                    subtotal DECIMAL(12,2) NOT NULL,
                    descuento_porcentaje DECIMAL(5,2) DEFAULT 0,
                    descuento_importe DECIMAL(12,2) DEFAULT 0,
                    impuestos_importe DECIMAL(12,2) DEFAULT 0,
                    total DECIMAL(12,2) NOT NULL,
                    
                    -- Control
                    estado VARCHAR(20) DEFAULT 'ACTIVA',
                    observaciones TEXT,
                    completada_en TIMESTAMP,
                    cancelada_en TIMESTAMP,
                    devolucion_en TIMESTAMP,
                    
                    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                    FOREIGN KEY (caja_id) REFERENCES cajas(id)
                )
            ''',
            
            'detalle_ventas': '''
                CREATE TABLE IF NOT EXISTS detalle_ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venta_id INTEGER NOT NULL,
                    producto_id INTEGER NOT NULL,
                    
                    -- Cantidades y precios
                    cantidad DECIMAL(8,3) NOT NULL,
                    precio_unitario DECIMAL(10,2) NOT NULL,
                    costo_unitario DECIMAL(10,2) DEFAULT 0,
                    
                    -- Descuentos
                    descuento_porcentaje DECIMAL(5,2) DEFAULT 0,
                    descuento_importe DECIMAL(10,2) DEFAULT 0,
                    
                    -- Impuestos
                    impuesto_porcentaje DECIMAL(5,2) DEFAULT 21,
                    impuesto_importe DECIMAL(10,2) DEFAULT 0,
                    
                    -- Totales
                    subtotal DECIMAL(10,2) NOT NULL,
                    total DECIMAL(10,2) NOT NULL,
                    
                    -- Trazabilidad
                    lote VARCHAR(50),
                    fecha_vencimiento DATE,
                    
                    FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE,
                    FOREIGN KEY (producto_id) REFERENCES productos(id)
                )
            ''',
            
            'pagos_venta': '''
                CREATE TABLE IF NOT EXISTS pagos_venta (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venta_id INTEGER NOT NULL,
                    metodo_pago VARCHAR(50) NOT NULL,
                    importe DECIMAL(12,2) NOT NULL,
                    referencia VARCHAR(100),
                    fecha_pago TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    observaciones TEXT,
                    FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE
                )
            ''',
            
            # Compras
            'compras': '''
                CREATE TABLE IF NOT EXISTS compras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_orden VARCHAR(50) UNIQUE NOT NULL,
                    numero_factura VARCHAR(50),
                    proveedor_id INTEGER NOT NULL,
                    usuario_id INTEGER NOT NULL,
                    
                    -- Fechas
                    fecha_compra TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_factura DATE,
                    fecha_vencimiento DATE,
                    fecha_recepcion TIMESTAMP,
                    
                    -- Importes
                    subtotal DECIMAL(12,2) NOT NULL,
                    descuento_importe DECIMAL(12,2) DEFAULT 0,
                    impuestos_importe DECIMAL(12,2) DEFAULT 0,
                    total DECIMAL(12,2) NOT NULL,
                    
                    -- Control
                    estado VARCHAR(20) DEFAULT 'ORDENADA',
                    tipo_comprobante VARCHAR(20) DEFAULT 'FACTURA',
                    observaciones TEXT,
                    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            ''',
            
            'detalle_compras': '''
                CREATE TABLE IF NOT EXISTS detalle_compras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    compra_id INTEGER NOT NULL,
                    producto_id INTEGER NOT NULL,
                    
                    -- Cantidades
                    cantidad DECIMAL(8,3) NOT NULL,
                    cantidad_recibida DECIMAL(8,3) DEFAULT 0,
                    
                    -- Precios
                    precio_unitario DECIMAL(10,2) NOT NULL,
                    descuento_porcentaje DECIMAL(5,2) DEFAULT 0,
                    descuento_importe DECIMAL(10,2) DEFAULT 0,
                    
                    -- Impuestos
                    iva_porcentaje DECIMAL(5,2) DEFAULT 21,
                    iva_importe DECIMAL(10,2) DEFAULT 0,
                    
                    -- Total
                    subtotal DECIMAL(10,2) NOT NULL,
                    
                    -- Trazabilidad
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
                    tipo_movimiento VARCHAR(20) NOT NULL,
                    motivo VARCHAR(50) NOT NULL,
                    
                    -- Cantidades
                    cantidad_anterior DECIMAL(8,3) NOT NULL,
                    cantidad_movimiento DECIMAL(8,3) NOT NULL,
                    cantidad_nueva DECIMAL(8,3) NOT NULL,
                    
                    -- Precio y referencia
                    precio_unitario DECIMAL(10,2),
                    usuario_id INTEGER NOT NULL,
                    referencia_id INTEGER,
                    referencia_tipo VARCHAR(20),
                    
                    -- Control
                    fecha_movimiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    observaciones TEXT,
                    lote VARCHAR(50),
                    
                    FOREIGN KEY (producto_id) REFERENCES productos(id),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            ''',
            
            # Cuenta corriente
            'cuenta_corriente': '''
                CREATE TABLE IF NOT EXISTS cuenta_corriente (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER NOT NULL,
                    tipo_movimiento VARCHAR(20) NOT NULL,
                    concepto VARCHAR(100) NOT NULL,
                    importe DECIMAL(12,2) NOT NULL,
                    saldo_anterior DECIMAL(12,2) NOT NULL,
                    saldo_nuevo DECIMAL(12,2) NOT NULL,
                    venta_id INTEGER,
                    fecha_movimiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_vencimiento DATE,
                    usuario_id INTEGER NOT NULL,
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
                    cajon_monedero BOOLEAN DEFAULT 0,
                    activo BOOLEAN DEFAULT 1,
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            
            'sesiones_caja': '''
                CREATE TABLE IF NOT EXISTS sesiones_caja (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    caja_id INTEGER NOT NULL,
                    usuario_id INTEGER NOT NULL,
                    fecha_apertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_cierre TIMESTAMP,
                    monto_apertura DECIMAL(12,2) DEFAULT 0,
                    monto_cierre DECIMAL(12,2) DEFAULT 0,
                    monto_ventas DECIMAL(12,2) DEFAULT 0,
                    monto_esperado DECIMAL(12,2) DEFAULT 0,
                    diferencia DECIMAL(12,2) DEFAULT 0,
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
                    tipo_movimiento VARCHAR(20) NOT NULL,
                    concepto VARCHAR(100) NOT NULL,
                    importe DECIMAL(12,2) NOT NULL,
                    saldo_anterior DECIMAL(12,2) NOT NULL,
                    saldo_nuevo DECIMAL(12,2) NOT NULL,
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
            
            # Devoluciones
            'devoluciones': '''
                CREATE TABLE IF NOT EXISTS devoluciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venta_id INTEGER NOT NULL,
                    producto_id INTEGER NOT NULL,
                    cantidad_devuelta DECIMAL(8,3) NOT NULL,
                    precio_unitario DECIMAL(10,2) NOT NULL,
                    motivo TEXT,
                    usuario_id INTEGER NOT NULL,
                    fecha_devolucion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (venta_id) REFERENCES ventas(id),
                    FOREIGN KEY (producto_id) REFERENCES productos(id),
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
            
            # Log de auditoría
            'auditoria': '''
                CREATE TABLE IF NOT EXISTS auditoria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tabla VARCHAR(50) NOT NULL,
                    operacion VARCHAR(20) NOT NULL,
                    registro_id INTEGER,
                    datos_anteriores TEXT,
                    datos_nuevos TEXT,
                    usuario_id INTEGER,
                    fecha_operacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            '''
        }
        
        # Crear todas las tablas
        for table_name, table_sql in tables.items():
            try:
                self.cursor.execute(table_sql)
                self.logger.debug(f"Tabla creada/verificada: {table_name}")
            except Exception as e:
                self.logger.error(f"Error creando tabla {table_name}: {e}")
                raise e
        
        self.connection.commit()
        self.logger.info("Todas las tablas creadas exitosamente")
    
    def _create_indexes(self):
        """Crear índices para optimización de consultas"""
        indexes = [
            # Índices de productos
            "CREATE INDEX IF NOT EXISTS idx_productos_codigo_barras ON productos(codigo_barras)",
            "CREATE INDEX IF NOT EXISTS idx_productos_codigo_interno ON productos(codigo_interno)",
            "CREATE INDEX IF NOT EXISTS idx_productos_nombre ON productos(nombre)",
            "CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos(categoria_id)",
            "CREATE INDEX IF NOT EXISTS idx_productos_proveedor ON productos(proveedor_id)",
            "CREATE INDEX IF NOT EXISTS idx_productos_activo ON productos(activo)",
            
            # Índices de ventas
            "CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha_venta)",
            "CREATE INDEX IF NOT EXISTS idx_ventas_cliente ON ventas(cliente_id)",
            "CREATE INDEX IF NOT EXISTS idx_ventas_usuario ON ventas(usuario_id)",
            "CREATE INDEX IF NOT EXISTS idx_ventas_estado ON ventas(estado)",
            "CREATE INDEX IF NOT EXISTS idx_ventas_numero ON ventas(numero_factura)",
            
            # Índices de detalle ventas
            "CREATE INDEX IF NOT EXISTS idx_detalle_ventas_venta ON detalle_ventas(venta_id)",
            "CREATE INDEX IF NOT EXISTS idx_detalle_ventas_producto ON detalle_ventas(producto_id)",
            
            # Índices de compras
            "CREATE INDEX IF NOT EXISTS idx_compras_fecha ON compras(fecha_compra)",
            "CREATE INDEX IF NOT EXISTS idx_compras_proveedor ON compras(proveedor_id)",
            "CREATE INDEX IF NOT EXISTS idx_compras_estado ON compras(estado)",
            
            # Índices de movimientos stock
            "CREATE INDEX IF NOT EXISTS idx_movimientos_producto ON movimientos_stock(producto_id)",
            "CREATE INDEX IF NOT EXISTS idx_movimientos_fecha ON movimientos_stock(fecha_movimiento)",
            "CREATE INDEX IF NOT EXISTS idx_movimientos_tipo ON movimientos_stock(tipo_movimiento)",
            "CREATE INDEX IF NOT EXISTS idx_movimientos_referencia ON movimientos_stock(referencia_id, referencia_tipo)",
            
            # Índices de usuarios
            "CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username)",
            "CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email)",
            "CREATE INDEX IF NOT EXISTS idx_usuarios_activo ON usuarios(activo)",
            
            # Índices de clientes - verificar si la columna existe antes de crear el índice
            "CREATE INDEX IF NOT EXISTS idx_clientes_nombre ON clientes(nombre, apellido)",
            "CREATE INDEX IF NOT EXISTS idx_clientes_activo ON clientes(activo)",
            
            # Índices de cuenta corriente
            "CREATE INDEX IF NOT EXISTS idx_cuenta_corriente_cliente ON cuenta_corriente(cliente_id)",
            "CREATE INDEX IF NOT EXISTS idx_cuenta_corriente_fecha ON cuenta_corriente(fecha_movimiento)",
            
            # Índices de auditoría
            "CREATE INDEX IF NOT EXISTS idx_auditoria_tabla ON auditoria(tabla)",
            "CREATE INDEX IF NOT EXISTS idx_auditoria_fecha ON auditoria(fecha_operacion)",
            "CREATE INDEX IF NOT EXISTS idx_auditoria_usuario ON auditoria(usuario_id)"
        ]
        
        for index_sql in indexes:
            try:
                self.cursor.execute(index_sql)
            except Exception as e:
                self.logger.warning(f"Error creando índice: {e}")
        
        self.connection.commit()
        self.logger.info("Índices creados exitosamente")
    
    def _create_triggers(self):
        """Crear triggers para auditoría y validaciones"""
        triggers = [
            # Trigger para actualizar stock automáticamente
            '''
            CREATE TRIGGER IF NOT EXISTS trg_actualizar_timestamp_productos
            AFTER UPDATE ON productos
            FOR EACH ROW
            BEGIN
                UPDATE productos SET actualizado_en = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            ''',
            
            # Trigger para validar stock negativo
            '''
            CREATE TRIGGER IF NOT EXISTS trg_validar_stock_negativo
            BEFORE UPDATE OF stock_actual ON productos
            FOR EACH ROW
            WHEN NEW.stock_actual < 0 AND NEW.permite_venta_sin_stock = 0
            BEGIN
                SELECT RAISE(ABORT, 'Stock no puede ser negativo para este producto');
            END
            ''',
            
            # Trigger para auditoría de cambios críticos
            '''
            CREATE TRIGGER IF NOT EXISTS trg_auditoria_productos
            AFTER UPDATE ON productos
            FOR EACH ROW
            WHEN OLD.precio_venta != NEW.precio_venta OR OLD.stock_actual != NEW.stock_actual
            BEGIN
                INSERT INTO auditoria (tabla, operacion, registro_id, datos_anteriores, datos_nuevos, fecha_operacion)
                VALUES ('productos', 'UPDATE', NEW.id, 
                       json_object('precio_venta', OLD.precio_venta, 'stock_actual', OLD.stock_actual),
                       json_object('precio_venta', NEW.precio_venta, 'stock_actual', NEW.stock_actual),
                       CURRENT_TIMESTAMP);
            END
            '''
        ]
        
        for trigger_sql in triggers:
            try:
                self.cursor.execute(trigger_sql)
            except Exception as e:
                self.logger.warning(f"Error creando trigger: {e}")
        
        self.connection.commit()
        self.logger.info("Triggers creados exitosamente")
    
    def _insert_default_data(self):
        """Insertar datos por defecto necesarios"""
        try:
            # Categoría por defecto
            self.cursor.execute("""
                INSERT OR IGNORE INTO categorias (id, nombre, descripcion, color)
                VALUES (1, 'General', 'Categoría general para productos sin clasificar', '#3498db')
            """)
            
            # Caja por defecto
            self.cursor.execute("""
                INSERT OR IGNORE INTO cajas (id, nombre, descripcion)
                VALUES (1, 'Caja Principal', 'Caja principal del sistema')
            """)
            
            # Configuraciones por defecto
            default_configs = [
                ('sistema.nombre_empresa', 'Mi Empresa', 'Nombre de la empresa'),
                ('sistema.version', '2.0.0', 'Versión del sistema'),
                ('ventas.iva_defecto', '21', 'IVA por defecto para productos'),
                ('ventas.punto_venta', '1', 'Punto de venta por defecto'),
                ('backup.automatico', '1', 'Backup automático habilitado'),
                ('backup.intervalo_horas', '24', 'Intervalo de backup en horas')
            ]
            
            for config in default_configs:
                self.cursor.execute("""
                    INSERT OR IGNORE INTO configuraciones (clave, valor, descripcion)
                    VALUES (?, ?, ?)
                """, config)
            
            self.connection.commit()
            self.logger.info("Datos por defecto insertados")
            
        except Exception as e:
            self.logger.error(f"Error insertando datos por defecto: {e}")
    
    def _optimize_database(self):
        """Optimizar base de datos"""
        try:
            optimization_commands = [
                "ANALYZE",
                "PRAGMA optimize",
                "VACUUM"
            ]
            
            for command in optimization_commands:
                self.cursor.execute(command)
            
            self.logger.info("Base de datos optimizada")
            
        except Exception as e:
            self.logger.warning(f"Error optimizando base de datos: {e}")
    
    # Métodos de transacción
    def begin_transaction(self):
        """Iniciar transacción"""
        with self.thread_lock:
            self.cursor.execute("BEGIN TRANSACTION")
    
    def commit_transaction(self):
        """Confirmar transacción"""
        with self.thread_lock:
            self.connection.commit()
    
    def rollback_transaction(self):
        """Revertir transacción"""
        with self.thread_lock:
            self.connection.rollback()
    
    # Métodos de consulta
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Ejecutar consulta SELECT"""
        try:
            with self.thread_lock:
                self.cursor.execute(query, params)
                return [dict(row) for row in self.cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error ejecutando consulta: {e}")
            raise e
    
    def execute_single(self, query: str, params: tuple = ()) -> Optional[Dict]:
        """Ejecutar consulta que retorna un solo registro"""
        try:
            with self.thread_lock:
                self.cursor.execute(query, params)
                row = self.cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"Error ejecutando consulta single: {e}")
            raise e
    
    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """Ejecutar INSERT y retornar ID insertado"""
        try:
            with self.thread_lock:
                self.cursor.execute(query, params)
                self.connection.commit()
                return self.cursor.lastrowid
        except Exception as e:
            self.logger.error(f"Error ejecutando insert: {e}")
            raise e
    
    def execute_update(self, query: str, params: tuple = ()) -> bool:
        """Ejecutar UPDATE/DELETE"""
        try:
            with self.thread_lock:
                self.cursor.execute(query, params)
                self.connection.commit()
                return self.cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Error ejecutando update: {e}")
            raise e
    
    def get_database_info(self) -> Dict:
        """Obtener información de la base de datos"""
        try:
            info = {
                'path': str(self.db_path),
                'size_mb': round(self.db_path.stat().st_size / (1024 * 1024), 2),
                'tables': [],
                'total_records': 0
            }
            
            # Obtener lista de tablas
            tables = self.execute_query("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            
            for table in tables:
                table_name = table['name']
                count_result = self.execute_single(f"SELECT COUNT(*) as count FROM {table_name}")
                record_count = count_result['count'] if count_result else 0
                
                info['tables'].append({
                    'name': table_name,
                    'records': record_count
                })
                info['total_records'] += record_count
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error obteniendo información de base de datos: {e}")
            return {'error': str(e)}
    
    def backup_database(self, backup_path: str) -> bool:
        """Crear backup de la base de datos"""
        try:
            backup_path = Path(backup_path)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Crear conexión de backup
            backup_conn = sqlite3.connect(str(backup_path))
            
            # Realizar backup
            self.connection.backup(backup_conn)
            backup_conn.close()
            
            self.logger.info(f"Backup creado: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creando backup: {e}")
            return False