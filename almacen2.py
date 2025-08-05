"""
AlmacénPro - Sistema ERP/POS Completo
Sistema profesional de gestión para almacenes, kioscos, distribuidoras
Desarrollado en Python con PyQt5 y SQLite/PostgreSQL
"""

import sys
import os
import sqlite3
import json
import hashlib
import logging
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import threading
import time
from typing import Dict, List, Optional, Tuple, Any

# PyQt5 imports
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class DatabaseManager:
    """Gestor principal de base de datos con soporte SQLite y PostgreSQL"""
    
    def __init__(self, db_path="almacen_pro.db"):
        self.db_path = db_path
        self.connection = None
        self.setup_database()
    
    def setup_database(self):
        """Configurar y crear todas las tablas necesarias"""
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        
        # Crear todas las tablas
        self.create_tables()
        self.create_indexes()
        self.insert_default_data()
    
    def create_tables(self):
        """Crear estructura completa de base de datos"""
        tables = {
            # Usuarios y roles
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
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (rol_id) REFERENCES roles(id)
                )
            ''',
            
            'roles': '''
                CREATE TABLE IF NOT EXISTS roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre VARCHAR(50) UNIQUE NOT NULL,
                    descripcion TEXT,
                    permisos TEXT, -- JSON con permisos
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                    telefono VARCHAR(50),
                    email VARCHAR(100),
                    contacto_principal VARCHAR(100),
                    condiciones_pago TEXT,
                    descuento_porcentaje DECIMAL(5,2) DEFAULT 0,
                    activo BOOLEAN DEFAULT 1,
                    notas TEXT,
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                    telefono VARCHAR(50),
                    email VARCHAR(100),
                    fecha_nacimiento DATE,
                    limite_credito DECIMAL(10,2) DEFAULT 0,
                    saldo_cuenta_corriente DECIMAL(10,2) DEFAULT 0,
                    descuento_porcentaje DECIMAL(5,2) DEFAULT 0,
                    categoria_cliente VARCHAR(50) DEFAULT 'MINORISTA',
                    activo BOOLEAN DEFAULT 1,
                    notas TEXT,
                    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                    subtotal DECIMAL(10,2) NOT NULL,
                    descuento DECIMAL(10,2) DEFAULT 0,
                    impuestos DECIMAL(10,2) DEFAULT 0,
                    total DECIMAL(10,2) NOT NULL,
                    metodo_pago VARCHAR(50), -- EFECTIVO, TARJETA, TRANSFERENCIA, MULTIPLE
                    estado VARCHAR(20) DEFAULT 'COMPLETADA',
                    fecha_venta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notas TEXT,
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
                    subtotal DECIMAL(10,2) NOT NULL,
                    FOREIGN KEY (venta_id) REFERENCES ventas(id),
                    FOREIGN KEY (producto_id) REFERENCES productos(id)
                )
            ''',
            
            # Compras
            'compras': '''
                CREATE TABLE IF NOT EXISTS compras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_factura VARCHAR(50),
                    proveedor_id INTEGER NOT NULL,
                    usuario_id INTEGER NOT NULL,
                    subtotal DECIMAL(10,2) NOT NULL,
                    descuento DECIMAL(10,2) DEFAULT 0,
                    impuestos DECIMAL(10,2) DEFAULT 0,
                    total DECIMAL(10,2) NOT NULL,
                    fecha_compra TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_vencimiento DATE,
                    estado VARCHAR(20) DEFAULT 'PENDIENTE',
                    notas TEXT,
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
                    precio_unitario DECIMAL(10,2) NOT NULL,
                    subtotal DECIMAL(10,2) NOT NULL,
                    FOREIGN KEY (compra_id) REFERENCES compras(id),
                    FOREIGN KEY (producto_id) REFERENCES productos(id)
                )
            ''',
            
            # Movimientos de stock
            'movimientos_stock': '''
                CREATE TABLE IF NOT EXISTS movimientos_stock (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    producto_id INTEGER NOT NULL,
                    tipo_movimiento VARCHAR(20) NOT NULL, -- ENTRADA, SALIDA, AJUSTE
                    motivo VARCHAR(50), -- VENTA, COMPRA, DEVOLUCION, AJUSTE_INVENTARIO
                    cantidad_anterior DECIMAL(8,3),
                    cantidad_movimiento DECIMAL(8,3) NOT NULL,
                    cantidad_nueva DECIMAL(8,3),
                    precio_unitario DECIMAL(10,2),
                    usuario_id INTEGER,
                    referencia_id INTEGER, -- ID de venta/compra relacionada
                    referencia_tipo VARCHAR(20), -- VENTA, COMPRA
                    fecha_movimiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notas TEXT,
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
                    usuario_id INTEGER,
                    notas TEXT,
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
                    activo BOOLEAN DEFAULT 1,
                    ubicacion VARCHAR(100)
                )
            ''',
            
            'movimientos_caja': '''
                CREATE TABLE IF NOT EXISTS movimientos_caja (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    caja_id INTEGER NOT NULL,
                    tipo_movimiento VARCHAR(20) NOT NULL, -- APERTURA, VENTA, GASTO, CIERRE
                    concepto VARCHAR(100),
                    importe DECIMAL(10,2) NOT NULL,
                    saldo_anterior DECIMAL(10,2),
                    saldo_nuevo DECIMAL(10,2),
                    venta_id INTEGER,
                    usuario_id INTEGER NOT NULL,
                    fecha_movimiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (caja_id) REFERENCES cajas(id),
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
                    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                    fecha_operacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''
        }
        
        cursor = self.connection.cursor()
        for table_name, sql in tables.items():
            try:
                cursor.execute(sql)
                logging.info(f"Tabla {table_name} creada/verificada")
            except Exception as e:
                logging.error(f"Error creando tabla {table_name}: {e}")
        
        self.connection.commit()
    
    def create_indexes(self):
        """Crear índices para optimizar rendimiento"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_productos_codigo_barras ON productos(codigo_barras)",
            "CREATE INDEX IF NOT EXISTS idx_productos_nombre ON productos(nombre)",
            "CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha_venta)",
            "CREATE INDEX IF NOT EXISTS idx_ventas_cliente ON ventas(cliente_id)",
            "CREATE INDEX IF NOT EXISTS idx_movimientos_stock_producto ON movimientos_stock(producto_id)",
            "CREATE INDEX IF NOT EXISTS idx_cuenta_corriente_cliente ON cuenta_corriente(cliente_id)",
            "CREATE INDEX IF NOT EXISTS idx_sync_log_sincronizado ON sync_log(sincronizado)"
        ]
        
        cursor = self.connection.cursor()
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                logging.error(f"Error creando índice: {e}")
        
        self.connection.commit()
    
    def insert_default_data(self):
        """Insertar datos por defecto del sistema"""
        cursor = self.connection.cursor()
        
        # Roles por defecto
        roles_default = [
            ('ADMIN', 'Administrator', '{"all": true}'),
            ('GERENTE', 'Gerente', '{"ventas": true, "compras": true, "reportes": true, "stock": true}'),
            ('VENDEDOR', 'Vendedor', '{"ventas": true, "clientes": true}'),
            ('STOCK', 'Encargado de Stock', '{"stock": true, "productos": true, "compras": true}'),
            ('CAJA', 'Cajero', '{"ventas": true, "caja": true}')
        ]
        
        for nombre, descripcion, permisos in roles_default:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO roles (nombre, descripcion, permisos) 
                    VALUES (?, ?, ?)
                """, (nombre, descripcion, permisos))
            except:
                pass
        
        # Usuario administrador por defecto
        admin_password = hashlib.sha256("admin123".encode()).hexdigest()
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO usuarios (username, password_hash, nombre_completo, rol_id) 
                VALUES ('admin', ?, 'Administrador', 1)
            """, (admin_password,))
        except:
            pass
        
        # Categorías por defecto
        categorias_default = [
            ('GENERAL', 'Productos generales'),
            ('ALIMENTACION', 'Alimentos y bebidas'),
            ('LIMPIEZA', 'Productos de limpieza'),
            ('PERFUMERIA', 'Perfumería y cosmética'),
            ('PANADERIA', 'Panadería y repostería'),
            ('FIAMBRERIA', 'Fiambres y lácteos'),
            ('CARNICERIA', 'Carnes y embutidos')
        ]
        
        for nombre, descripcion in categorias_default:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO categorias (nombre, descripcion) 
                    VALUES (?, ?)
                """, (nombre, descripcion))
            except:
                pass
        
        # Caja por defecto
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO cajas (id, nombre, descripcion) 
                VALUES (1, 'Caja Principal', 'Caja principal del local')
            """)
        except:
            pass
        
        # Configuraciones por defecto
        config_default = [
            ('empresa_nombre', 'Mi Almacén', 'Nombre de la empresa'),
            ('empresa_direccion', '', 'Dirección de la empresa'),
            ('empresa_telefono', '', 'Teléfono de la empresa'),
            ('empresa_cuit', '', 'CUIT de la empresa'),
            ('ticket_pie_mensaje', 'Gracias por su compra', 'Mensaje al pie del ticket'),
            ('backup_automatico', 'true', 'Backup automático habilitado'),
            ('sync_servidor_url', '', 'URL del servidor de sincronización'),
            ('impresora_tickets', '', 'Impresora para tickets')
        ]
        
        for clave, valor, descripcion in config_default:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO configuraciones (clave, valor, descripcion) 
                    VALUES (?, ?, ?)
                """, (clave, valor, descripcion))
            except:
                pass
        
        self.connection.commit()

class UserManager:
    """Gestor de usuarios y autenticación"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.current_user = None
        self.current_permissions = {}
    
    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """Autenticar usuario"""
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            cursor = self.db.connection.cursor()
            
            cursor.execute("""
                SELECT u.*, r.nombre as rol_nombre, r.permisos 
                FROM usuarios u 
                LEFT JOIN roles r ON u.rol_id = r.id 
                WHERE u.username = ? AND u.password_hash = ? AND u.activo = 1
            """, (username, password_hash))
            
            user = cursor.fetchone()
            
            if user:
                self.current_user = dict(user)
                self.current_permissions = json.loads(user['permisos'] or '{}')
                
                # Actualizar último acceso
                cursor.execute("""
                    UPDATE usuarios SET ultimo_acceso = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (user['id'],))
                self.db.connection.commit()
                
                return True, f"Bienvenido {user['nombre_completo']}"
            else:
                return False, "Usuario o contraseña incorrectos"
                
        except Exception as e:
            logging.error(f"Error en login: {e}")
            return False, "Error de autenticación"
    
    def has_permission(self, permission: str) -> bool:
        """Verificar si el usuario tiene un permiso específico"""
        if not self.current_user:
            return False
        
        if self.current_permissions.get('all'):
            return True
        
        return self.current_permissions.get(permission, False)
    
    def logout(self):
        """Cerrar sesión"""
        self.current_user = None
        self.current_permissions = {}

class ProductManager:
    """Gestor de productos"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def buscar_producto(self, termino: str) -> List[Dict]:
        """Buscar productos por código de barras o nombre"""
        cursor = self.db.connection.cursor()
        
        cursor.execute("""
            SELECT p.*, c.nombre as categoria_nombre, pr.nombre as proveedor_nombre
            FROM productos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
            WHERE (p.codigo_barras LIKE ? OR p.nombre LIKE ? OR p.codigo_interno LIKE ?)
            AND p.activo = 1
            ORDER BY p.nombre
            LIMIT 50
        """, (f"%{termino}%", f"%{termino}%", f"%{termino}%"))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def obtener_producto_por_codigo(self, codigo_barras: str) -> Optional[Dict]:
        """Obtener producto por código de barras"""
        cursor = self.db.connection.cursor()
        
        cursor.execute("""
            SELECT p.*, c.nombre as categoria_nombre 
            FROM productos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            WHERE p.codigo_barras = ? AND p.activo = 1
        """, (codigo_barras,))
        
        result = cursor.fetchone()
        return dict(result) if result else None
    
    def actualizar_stock(self, producto_id: int, nueva_cantidad: int, 
                        tipo_movimiento: str, motivo: str, usuario_id: int,
                        precio_unitario: float = None, referencia_id: int = None):
        """Actualizar stock y registrar movimiento"""
        cursor = self.db.connection.cursor()
        
        # Obtener stock actual
        cursor.execute("SELECT stock_actual FROM productos WHERE id = ?", (producto_id,))
        stock_anterior = cursor.fetchone()[0]
        
        # Calcular movimiento
        if tipo_movimiento == 'ENTRADA':
            stock_nuevo = stock_anterior + nueva_cantidad
            cantidad_movimiento = nueva_cantidad
        elif tipo_movimiento == 'SALIDA':
            stock_nuevo = stock_anterior - nueva_cantidad
            cantidad_movimiento = -nueva_cantidad
        else:  # AJUSTE
            stock_nuevo = nueva_cantidad
            cantidad_movimiento = nueva_cantidad - stock_anterior
        
        # Actualizar stock del producto
        cursor.execute("""
            UPDATE productos 
            SET stock_actual = ?, actualizado_en = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (stock_nuevo, producto_id))
        
        # Registrar movimiento
        cursor.execute("""
            INSERT INTO movimientos_stock (
                producto_id, tipo_movimiento, motivo, cantidad_anterior,
                cantidad_movimiento, cantidad_nueva, precio_unitario,
                usuario_id, referencia_id, referencia_tipo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            producto_id, tipo_movimiento, motivo, stock_anterior,
            cantidad_movimiento, stock_nuevo, precio_unitario,
            usuario_id, referencia_id, 'VENTA' if motivo == 'VENTA' else 'COMPRA'
        ))
        
        self.db.connection.commit()

class PurchaseManager:
    """Gestor de compras"""
    
    def __init__(self, db_manager: DatabaseManager, product_manager: ProductManager):
        self.db = db_manager
        self.product_manager = product_manager
    
    def crear_compra(self, items: List[Dict], proveedor_id: int, 
                    numero_factura: str = None, usuario_id: int = None,
                    fecha_vencimiento: str = None) -> Tuple[bool, str, int]:
        """Crear nueva orden de compra"""
        try:
            cursor = self.db.connection.cursor()
            
            # Calcular totales
            subtotal = sum(item['cantidad'] * item['precio_unitario'] for item in items)
            descuento = sum(item.get('descuento', 0) for item in items)
            impuestos = subtotal * 0.21  # IVA 21%
            total = subtotal - descuento + impuestos
            
            # Crear compra
            cursor.execute("""
                INSERT INTO compras (
                    numero_factura, proveedor_id, usuario_id, subtotal, 
                    descuento, impuestos, total, fecha_vencimiento, estado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDIENTE')
            """, (numero_factura, proveedor_id, usuario_id, subtotal,
                  descuento, impuestos, total, fecha_vencimiento))
            
            compra_id = cursor.lastrowid
            
            # Crear detalles de compra
            for item in items:
                cursor.execute("""
                    INSERT INTO detalle_compras (
                        compra_id, producto_id, cantidad, precio_unitario, subtotal
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    compra_id, item['producto_id'], item['cantidad'],
                    item['precio_unitario'], item['cantidad'] * item['precio_unitario']
                ))
            
            self.db.connection.commit()
            return True, f"Orden de compra #{compra_id} creada exitosamente", compra_id
            
        except Exception as e:
            self.db.connection.rollback()
            logging.error(f"Error creando compra: {e}")
            return False, f"Error creando compra: {str(e)}", 0
    
    def recibir_compra(self, compra_id: int, items_recibidos: List[Dict], 
                      usuario_id: int) -> Tuple[bool, str]:
        """Procesar recepción de mercadería"""
        try:
            cursor = self.db.connection.cursor()
            
            # Actualizar estado de compra
            cursor.execute("""
                UPDATE compras SET estado = 'RECIBIDA' WHERE id = ?
            """, (compra_id,))
            
            # Actualizar stock para cada item recibido
            for item in items_recibidos:
                if item['cantidad_recibida'] > 0:
                    # Actualizar stock
                    self.product_manager.actualizar_stock(
                        item['producto_id'], item['cantidad_recibida'], 
                        'ENTRADA', 'COMPRA', usuario_id, 
                        item['precio_unitario'], compra_id
                    )
                    
                    # Actualizar precio de compra del producto
                    cursor.execute("""
                        UPDATE productos SET precio_compra = ?, actualizado_en = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    """, (item['precio_unitario'], item['producto_id']))
            
            self.db.connection.commit()
            return True, "Compra recibida y stock actualizado"
            
        except Exception as e:
            self.db.connection.rollback()
            logging.error(f"Error recibiendo compra: {e}")
            return False, f"Error recibiendo compra: {str(e)}"
    
    def obtener_compras(self, estado: str = None) -> List[Dict]:
        """Obtener lista de compras"""
        cursor = self.db.connection.cursor()
        
        query = """
            SELECT c.*, p.nombre as proveedor_nombre, u.nombre_completo as usuario_nombre
            FROM compras c
            LEFT JOIN proveedores p ON c.proveedor_id = p.id
            LEFT JOIN usuarios u ON c.usuario_id = u.id
        """
        
        params = []
        if estado:
            query += " WHERE c.estado = ?"
            params.append(estado)
            
        query += " ORDER BY c.fecha_compra DESC"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

class ProviderManager:
    """Gestor de proveedores"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def crear_proveedor(self, datos: Dict) -> Tuple[bool, str, int]:
        """Crear nuevo proveedor"""
        try:
            cursor = self.db.connection.cursor()
            
            cursor.execute("""
                INSERT INTO proveedores (
                    nombre, cuit_dni, direccion, telefono, email, 
                    contacto_principal, condiciones_pago, descuento_porcentaje, notas
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datos['nombre'], datos.get('cuit_dni'), datos.get('direccion'),
                datos.get('telefono'), datos.get('email'), datos.get('contacto_principal'),
                datos.get('condiciones_pago'), datos.get('descuento_porcentaje', 0),
                datos.get('notas')
            ))
            
            proveedor_id = cursor.lastrowid
            self.db.connection.commit()
            
            return True, f"Proveedor '{datos['nombre']}' creado exitosamente", proveedor_id
            
        except Exception as e:
            self.db.connection.rollback()
            logging.error(f"Error creando proveedor: {e}")
            return False, f"Error creando proveedor: {str(e)}", 0
    
    def obtener_proveedores(self, activos_solo: bool = True) -> List[Dict]:
        """Obtener lista de proveedores"""
        cursor = self.db.connection.cursor()
        
        query = "SELECT * FROM proveedores"
        if activos_solo:
            query += " WHERE activo = 1"
        query += " ORDER BY nombre"
        
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def buscar_proveedor(self, termino: str) -> List[Dict]:
        """Buscar proveedores por nombre o CUIT"""
        cursor = self.db.connection.cursor()
        
        cursor.execute("""
            SELECT * FROM proveedores 
            WHERE (nombre LIKE ? OR cuit_dni LIKE ?) AND activo = 1
            ORDER BY nombre
        """, (f"%{termino}%", f"%{termino}%"))
        
        return [dict(row) for row in cursor.fetchall()]

class ReportManager:
    """Gestor de reportes"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def reporte_ventas_periodo(self, fecha_desde: str, fecha_hasta: str) -> Dict:
        """Reporte de ventas por período"""
        cursor = self.db.connection.cursor()
        
        # Ventas totales
        cursor.execute("""
            SELECT 
                COUNT(*) as total_ventas,
                SUM(total) as total_facturado,
                AVG(total) as ticket_promedio,
                SUM(descuento) as total_descuentos
            FROM ventas 
            WHERE DATE(fecha_venta) BETWEEN ? AND ?
            AND estado = 'COMPLETADA'
        """, (fecha_desde, fecha_hasta))
        
        resumen = dict(cursor.fetchone())
        
        # Ventas por día
        cursor.execute("""
            SELECT 
                DATE(fecha_venta) as fecha,
                COUNT(*) as cantidad_ventas,
                SUM(total) as total_dia
            FROM ventas 
            WHERE DATE(fecha_venta) BETWEEN ? AND ?
            AND estado = 'COMPLETADA'
            GROUP BY DATE(fecha_venta)
            ORDER BY fecha
        """, (fecha_desde, fecha_hasta))
        
        ventas_diarias = [dict(row) for row in cursor.fetchall()]
        
        # Ventas por método de pago
        cursor.execute("""
            SELECT 
                metodo_pago,
                COUNT(*) as cantidad,
                SUM(total) as total
            FROM ventas 
            WHERE DATE(fecha_venta) BETWEEN ? AND ?
            AND estado = 'COMPLETADA'
            GROUP BY metodo_pago
        """, (fecha_desde, fecha_hasta))
        
        por_metodo_pago = [dict(row) for row in cursor.fetchall()]
        
        return {
            'resumen': resumen,
            'ventas_diarias': ventas_diarias,
            'por_metodo_pago': por_metodo_pago,
            'periodo': {'desde': fecha_desde, 'hasta': fecha_hasta}
        }
    
    def productos_mas_vendidos(self, fecha_desde: str, fecha_hasta: str, limite: int = 20) -> List[Dict]:
        """Productos más vendidos en un período"""
        cursor = self.db.connection.cursor()
        
        cursor.execute("""
            SELECT 
                p.nombre,
                p.codigo_barras,
                SUM(dv.cantidad) as cantidad_vendida,
                SUM(dv.subtotal) as total_vendido,
                AVG(dv.precio_unitario) as precio_promedio
            FROM detalle_ventas dv
            JOIN productos p ON dv.producto_id = p.id
            JOIN ventas v ON dv.venta_id = v.id
            WHERE DATE(v.fecha_venta) BETWEEN ? AND ?
            AND v.estado = 'COMPLETADA'
            GROUP BY p.id, p.nombre, p.codigo_barras
            ORDER BY cantidad_vendida DESC
            LIMIT ?
        """, (fecha_desde, fecha_hasta, limite))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def reporte_stock_bajo(self) -> List[Dict]:
        """Productos con stock bajo o sin stock"""
        cursor = self.db.connection.cursor()
        
        cursor.execute("""
            SELECT 
                p.nombre,
                p.codigo_barras,
                p.stock_actual,
                p.stock_minimo,
                c.nombre as categoria,
                pr.nombre as proveedor
            FROM productos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
            WHERE p.stock_actual <= p.stock_minimo 
            AND p.activo = 1
            ORDER BY (p.stock_actual - p.stock_minimo) ASC
        """)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def reporte_cuenta_corriente(self, cliente_id: int = None) -> List[Dict]:
        """Reporte de cuenta corriente"""
        cursor = self.db.connection.cursor()
        
        query = """
            SELECT 
                c.nombre || ' ' || COALESCE(c.apellido, '') as cliente,
                cc.tipo_movimiento,
                cc.concepto,
                cc.importe,
                cc.saldo_nuevo,
                cc.fecha_movimiento
            FROM cuenta_corriente cc
            JOIN clientes c ON cc.cliente_id = c.id
        """
        
        params = []
        if cliente_id:
            query += " WHERE cc.cliente_id = ?"
            params.append(cliente_id)
            
        query += " ORDER BY cc.fecha_movimiento DESC"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

class SalesManager:
    """Gestor de ventas"""
    
    def __init__(self, db_manager: DatabaseManager, product_manager: ProductManager):
        self.db = db_manager
        self.product_manager = product_manager
    
    def crear_venta(self, items: List[Dict], cliente_id: int = None, 
                   tipo_venta: str = 'CONTADO', metodo_pago: str = 'EFECTIVO',
                   vendedor_id: int = None, caja_id: int = 1) -> Tuple[bool, str, int]:
        """Crear nueva venta"""
        try:
            cursor = self.db.connection.cursor()
            
            # Calcular totales
            subtotal = sum(item['cantidad'] * item['precio_unitario'] for item in items)
            descuento = sum(item.get('descuento', 0) for item in items)
            impuestos = subtotal * 0.21  # IVA 21%
            total = subtotal - descuento + impuestos
            
            # Generar número de ticket
            numero_ticket = f"T{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Crear venta
            cursor.execute("""
                INSERT INTO ventas (
                    numero_ticket, cliente_id, vendedor_id, caja_id, tipo_venta,
                    subtotal, descuento, impuestos, total, metodo_pago, estado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'COMPLETADA')
            """, (numero_ticket, cliente_id, vendedor_id, caja_id, tipo_venta,
                  subtotal, descuento, impuestos, total, metodo_pago))
            
            venta_id = cursor.lastrowid
            
            # Crear detalles de venta y actualizar stock
            for item in items:
                cursor.execute("""
                    INSERT INTO detalle_ventas (
                        venta_id, producto_id, cantidad, precio_unitario,
                        descuento_porcentaje, subtotal
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    venta_id, item['producto_id'], item['cantidad'],
                    item['precio_unitario'], item.get('descuento_porcentaje', 0),
                    item['cantidad'] * item['precio_unitario']
                ))
                
                # Actualizar stock
                self.product_manager.actualizar_stock(
                    item['producto_id'], item['cantidad'], 'SALIDA', 'VENTA',
                    vendedor_id, item['precio_unitario'], venta_id
                )
            
            # Si es cuenta corriente, registrar movimiento
            if tipo_venta == 'CUENTA_CORRIENTE' and cliente_id:
                self.registrar_cuenta_corriente(
                    cliente_id, 'DEBE', f'Venta {numero_ticket}',
                    total, venta_id, vendedor_id
                )
            
            self.db.connection.commit()
            return True, f"Venta {numero_ticket} creada exitosamente", venta_id
            
        except Exception as e:
            self.db.connection.rollback()
            logging.error(f"Error creando venta: {e}")
            return False, f"Error creando venta: {str(e)}", 0
    
    def registrar_cuenta_corriente(self, cliente_id: int, tipo_movimiento: str,
                                  concepto: str, importe: float, venta_id: int = None,
                                  usuario_id: int = None):
        """Registrar movimiento en cuenta corriente"""
        cursor = self.db.connection.cursor()
        
        # Obtener saldo actual
        cursor.execute("""
            SELECT saldo_cuenta_corriente FROM clientes WHERE id = ?
        """, (cliente_id,))
        saldo_anterior = cursor.fetchone()[0] or 0
        
        # Calcular nuevo saldo
        if tipo_movimiento == 'DEBE':
            saldo_nuevo = saldo_anterior + importe
        else:  # HABER
            saldo_nuevo = saldo_anterior - importe
        
        # Registrar movimiento
        cursor.execute("""
            INSERT INTO cuenta_corriente (
                cliente_id, tipo_movimiento, concepto, importe,
                saldo_anterior, saldo_nuevo, venta_id, usuario_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (cliente_id, tipo_movimiento, concepto, importe,
              saldo_anterior, saldo_nuevo, venta_id, usuario_id))
        
        # Actualizar saldo del cliente
        cursor.execute("""
            UPDATE clientes SET saldo_cuenta_corriente = ? WHERE id = ?
        """, (saldo_nuevo, cliente_id))

class POSWindow(QMainWindow):
    """Ventana principal del sistema POS"""
    
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.user_manager = UserManager(self.db_manager)
        self.product_manager = ProductManager(self.db_manager)
        self.sales_manager = SalesManager(self.db_manager, self.product_manager)
        self.purchase_manager = PurchaseManager(self.db_manager, self.product_manager)
        self.provider_manager = ProviderManager(self.db_manager)
        self.report_manager = ReportManager(self.db_manager)
        
        self.cart_items = []
        self.purchase_items = []
        self.current_customer = None
        self.selected_provider = None
        
        # Mostrar login primero
        if self.show_login():
            self.init_ui()
        else:
            sys.exit()
    
    def show_login(self) -> bool:
        """Mostrar diálogo de login"""
        dialog = LoginDialog(self.user_manager)
        return dialog.exec_() == QDialog.Accepted
    
    def init_ui(self):
        """Inicializar interfaz principal"""
        self.setWindowTitle("AlmacénPro - Sistema de Gestión Completo")
        self.setGeometry(100, 100, 1400, 800)
        
        # Widget central con pestañas
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        layout = QVBoxLayout(central_widget)
        
        # Barra de estado del usuario
        self.create_user_status_bar()
        layout.addWidget(self.user_status_widget)
        
        # Pestañas principales
        self.tab_widget = QTabWidget()
        
        # Crear pestañas según permisos
        if self.user_manager.has_permission('ventas'):
            self.create_sales_tab()
        
        if self.user_manager.has_permission('stock'):
            self.create_stock_tab()
        
        if self.user_manager.has_permission('compras'):
            self.create_purchases_tab()
        
        if self.user_manager.has_permission('reportes'):
            self.create_reports_tab()
        
        if self.user_manager.has_permission('all'):
            self.create_admin_tab()
        
        layout.addWidget(self.tab_widget)
    
    def create_user_status_bar(self):
        """Crear barra de estado del usuario"""
        self.user_status_widget = QWidget()
        layout = QHBoxLayout(self.user_status_widget)
        
        user_info = QLabel(f"Usuario: {self.user_manager.current_user['nombre_completo']} | "
                          f"Rol: {self.user_manager.current_user['rol_nombre']}")
        user_info.setStyleSheet("font-weight: bold; color: #2E86AB;")
        
        logout_btn = QPushButton("Cerrar Sesión")
        logout_btn.clicked.connect(self.logout)
        
        layout.addWidget(user_info)
        layout.addStretch()
        layout.addWidget(logout_btn)
    
    def create_sales_tab(self):
        """Crear pestaña de ventas"""
        sales_widget = QWidget()
        layout = QHBoxLayout(sales_widget)
        
        # Panel izquierdo - Búsqueda y productos
        left_panel = QVBoxLayout()
        
        # Búsqueda de productos
        search_group = QGroupBox("Búsqueda de Productos")
        search_layout = QVBoxLayout(search_group)
        
        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText("Escanear código de barras o buscar producto...")
        self.product_search.returnPressed.connect(self.search_products)
        search_layout.addWidget(self.product_search)
        
        self.products_list = QListWidget()
        self.products_list.itemDoubleClicked.connect(self.add_product_to_cart)
        search_layout.addWidget(self.products_list)
        
        left_panel.addWidget(search_group)
        
        # Panel derecho - Carrito y total
        right_panel = QVBoxLayout()
        
        # Carrito de compras
        cart_group = QGroupBox("Carrito de Compras")
        cart_layout = QVBoxLayout(cart_group)
        
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(6)
        self.cart_table.setHorizontalHeaderLabels([
            "Producto", "Cantidad", "Precio Unit.", "Descuento", "Subtotal", "Acciones"
        ])
        cart_layout.addWidget(self.cart_table)
        
        # Totales
        totals_layout = QGridLayout()
        totals_layout.addWidget(QLabel("Subtotal:"), 0, 0)
        self.subtotal_label = QLabel("$0.00")
        totals_layout.addWidget(self.subtotal_label, 0, 1)
        
        totals_layout.addWidget(QLabel("Descuentos:"), 1, 0)
        self.discount_label = QLabel("$0.00")
        totals_layout.addWidget(self.discount_label, 1, 1)
        
        totals_layout.addWidget(QLabel("IVA (21%):"), 2, 0)
        self.tax_label = QLabel("$0.00")
        totals_layout.addWidget(self.tax_label, 2, 1)
        
        totals_layout.addWidget(QLabel("TOTAL:"), 3, 0)
        self.total_label = QLabel("$0.00")
        self.total_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2E86AB;")
        totals_layout.addWidget(self.total_label, 3, 1)
        
        cart_layout.addLayout(totals_layout)
        
        # Botones de acción
        buttons_layout = QHBoxLayout()
        
        clear_cart_btn = QPushButton("Limpiar Carrito")
        clear_cart_btn.clicked.connect(self.clear_cart)
        buttons_layout.addWidget(clear_cart_btn)
        
        process_sale_btn = QPushButton("Procesar Venta")
        process_sale_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        process_sale_btn.clicked.connect(self.process_sale)
        buttons_layout.addWidget(process_sale_btn)
        
        cart_layout.addLayout(buttons_layout)
        right_panel.addWidget(cart_group)
        
        # Agregar paneles al layout principal
        layout.addLayout(left_panel, 1)
        layout.addLayout(right_panel, 1)
        
        self.tab_widget.addTab(sales_widget, "🛒 Ventas")
        
        # Dar foco al campo de búsqueda
        self.product_search.setFocus()
    
    def create_stock_tab(self):
        """Crear pestaña de gestión de stock"""
        stock_widget = QWidget()
        layout = QVBoxLayout(stock_widget)
        
        # Barra de herramientas
        toolbar = QHBoxLayout()
        
        add_product_btn = QPushButton("Agregar Producto")
        add_product_btn.clicked.connect(self.show_add_product_dialog)
        toolbar.addWidget(add_product_btn)
        
        stock_alert_btn = QPushButton("Alertas de Stock")
        toolbar.addWidget(stock_alert_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Tabla de productos
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(8)
        self.stock_table.setHorizontalHeaderLabels([
            "Código", "Producto", "Categoría", "Stock Actual", 
            "Stock Mínimo", "Precio Venta", "Estado", "Acciones"
        ])
        layout.addWidget(self.stock_table)
        
        self.load_stock_data()
        self.tab_widget.addTab(stock_widget, "📦 Stock")
    
    def create_purchases_tab(self):
        """Crear pestaña de compras"""
        purchases_widget = QWidget()
        layout = QVBoxLayout(purchases_widget)
        
        # Pestañas secundarias para compras
        purchases_tab_widget = QTabWidget()
        
        # Pestaña Nueva Compra
        new_purchase_widget = QWidget()
        self.setup_new_purchase_tab(new_purchase_widget)
        purchases_tab_widget.addTab(new_purchase_widget, "Nueva Compra")
        
        # Pestaña Órdenes de Compra
        orders_widget = QWidget()
        self.setup_purchase_orders_tab(orders_widget)
        purchases_tab_widget.addTab(orders_widget, "Órdenes de Compra")
        
        # Pestaña Proveedores
        providers_widget = QWidget()
        self.setup_providers_tab(providers_widget)
        purchases_tab_widget.addTab(providers_widget, "Proveedores")
        
        layout.addWidget(purchases_tab_widget)
        self.tab_widget.addTab(purchases_widget, "🛍️ Compras")
    
    def setup_new_purchase_tab(self, widget):
        """Configurar pestaña de nueva compra"""
        layout = QHBoxLayout(widget)
        
        # Panel izquierdo - Selección de proveedor y productos
        left_panel = QVBoxLayout()
        
        # Selección de proveedor
        provider_group = QGroupBox("Proveedor")
        provider_layout = QVBoxLayout(provider_group)
        
        provider_search_layout = QHBoxLayout()
        self.provider_search = QLineEdit()
        self.provider_search.setPlaceholderText("Buscar proveedor...")
        self.provider_search.textChanged.connect(self.search_providers)
        provider_search_layout.addWidget(self.provider_search)
        
        new_provider_btn = QPushButton("Nuevo Proveedor")
        new_provider_btn.clicked.connect(self.show_add_provider_dialog)
        provider_search_layout.addWidget(new_provider_btn)
        
        provider_layout.addLayout(provider_search_layout)
        
        self.providers_list = QListWidget()
        self.providers_list.itemClicked.connect(self.select_provider)
        provider_layout.addWidget(self.providers_list)
        
        self.selected_provider_label = QLabel("Proveedor: No seleccionado")
        self.selected_provider_label.setStyleSheet("font-weight: bold; color: red;")
        provider_layout.addWidget(self.selected_provider_label)
        
        left_panel.addWidget(provider_group)
        
        # Búsqueda de productos para compra
        product_search_group = QGroupBox("Agregar Productos")
        product_search_layout = QVBoxLayout(product_search_group)
        
        self.purchase_product_search = QLineEdit()
        self.purchase_product_search.setPlaceholderText("Buscar producto para agregar a la compra...")
        self.purchase_product_search.textChanged.connect(self.search_products_for_purchase)
        product_search_layout.addWidget(self.purchase_product_search)
        
        self.purchase_products_list = QListWidget()
        self.purchase_products_list.itemDoubleClicked.connect(self.add_product_to_purchase)
        product_search_layout.addWidget(self.purchase_products_list)
        
        left_panel.addWidget(product_search_group)
        
        # Panel derecho - Orden de compra
        right_panel = QVBoxLayout()
        
        # Detalles de la orden
        order_details_group = QGroupBox("Detalles de la Orden")
        order_details_layout = QGridLayout(order_details_group)
        
        order_details_layout.addWidget(QLabel("N° Factura:"), 0, 0)
        self.invoice_number_input = QLineEdit()
        order_details_layout.addWidget(self.invoice_number_input, 0, 1)
        
        order_details_layout.addWidget(QLabel("Fecha Venc.:"), 1, 0)
        self.due_date_input = QDateEdit()
        self.due_date_input.setDate(QDate.currentDate().addDays(30))
        order_details_layout.addWidget(self.due_date_input, 1, 1)
        
        right_panel.addWidget(order_details_group)
        
        # Tabla de productos en la compra
        purchase_table_group = QGroupBox("Productos a Comprar")
        purchase_table_layout = QVBoxLayout(purchase_table_group)
        
        self.purchase_table = QTableWidget()
        self.purchase_table.setColumnCount(6)
        self.purchase_table.setHorizontalHeaderLabels([
            "Producto", "Cantidad", "Precio Unit.", "Descuento", "Subtotal", "Acciones"
        ])
        purchase_table_layout.addWidget(self.purchase_table)
        
        # Totales de compra
        purchase_totals_layout = QGridLayout()
        purchase_totals_layout.addWidget(QLabel("Subtotal:"), 0, 0)
        self.purchase_subtotal_label = QLabel("$0.00")
        purchase_totals_layout.addWidget(self.purchase_subtotal_label, 0, 1)
        
        purchase_totals_layout.addWidget(QLabel("Descuentos:"), 1, 0)
        self.purchase_discount_label = QLabel("$0.00")
        purchase_totals_layout.addWidget(self.purchase_discount_label, 1, 1)
        
        purchase_totals_layout.addWidget(QLabel("IVA (21%):"), 2, 0)
        self.purchase_tax_label = QLabel("$0.00")
        purchase_totals_layout.addWidget(self.purchase_tax_label, 2, 1)
        
        purchase_totals_layout.addWidget(QLabel("TOTAL:"), 3, 0)
        self.purchase_total_label = QLabel("$0.00")
        self.purchase_total_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2E86AB;")
        purchase_totals_layout.addWidget(self.purchase_total_label, 3, 1)
        
        purchase_table_layout.addLayout(purchase_totals_layout)
        
        # Botones de acción
        purchase_buttons_layout = QHBoxLayout()
        
        clear_purchase_btn = QPushButton("Limpiar")
        clear_purchase_btn.clicked.connect(self.clear_purchase)
        purchase_buttons_layout.addWidget(clear_purchase_btn)
        
        create_order_btn = QPushButton("Crear Orden de Compra")
        create_order_btn.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; padding: 10px;")
        create_order_btn.clicked.connect(self.create_purchase_order)
        purchase_buttons_layout.addWidget(create_order_btn)
        
        purchase_table_layout.addLayout(purchase_buttons_layout)
        right_panel.addWidget(purchase_table_group)
        
        # Agregar paneles al layout principal
        layout.addLayout(left_panel, 1)
        layout.addLayout(right_panel, 2)
        
        # Cargar proveedores al inicio
        self.load_providers()
    
    def setup_purchase_orders_tab(self, widget):
        """Configurar pestaña de órdenes de compra"""
        layout = QVBoxLayout(widget)
        
        # Filtros
        filters_layout = QHBoxLayout()
        
        filters_layout.addWidget(QLabel("Estado:"))
        self.order_status_filter = QComboBox()
        self.order_status_filter.addItems(['TODAS', 'PENDIENTE', 'RECIBIDA', 'CANCELADA'])
        self.order_status_filter.currentTextChanged.connect(self.filter_purchase_orders)
        filters_layout.addWidget(self.order_status_filter)
        
        filters_layout.addStretch()
        
        refresh_orders_btn = QPushButton("Actualizar")
        refresh_orders_btn.clicked.connect(self.load_purchase_orders)
        filters_layout.addWidget(refresh_orders_btn)
        
        layout.addLayout(filters_layout)
        
        # Tabla de órdenes de compra
        self.purchase_orders_table = QTableWidget()
        self.purchase_orders_table.setColumnCount(8)
        self.purchase_orders_table.setHorizontalHeaderLabels([
            "ID", "Fecha", "Proveedor", "N° Factura", "Total", "Estado", "Vencimiento", "Acciones"
        ])
        layout.addWidget(self.purchase_orders_table)
        
        self.load_purchase_orders()
    
    def setup_providers_tab(self, widget):
        """Configurar pestaña de proveedores"""
        layout = QVBoxLayout(widget)
        
        # Barra de herramientas
        toolbar_layout = QHBoxLayout()
        
        add_provider_btn = QPushButton("Agregar Proveedor")
        add_provider_btn.clicked.connect(self.show_add_provider_dialog)
        toolbar_layout.addWidget(add_provider_btn)
        
        provider_search_input = QLineEdit()
        provider_search_input.setPlaceholderText("Buscar proveedor...")
        provider_search_input.textChanged.connect(self.filter_providers_table)
        toolbar_layout.addWidget(provider_search_input)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # Tabla de proveedores
        self.providers_table = QTableWidget()
        self.providers_table.setColumnCount(7)
        self.providers_table.setHorizontalHeaderLabels([
            "Nombre", "CUIT/DNI", "Teléfono", "Email", "Contacto", "Descuento", "Acciones"
        ])
        layout.addWidget(self.providers_table)
        
        self.load_providers_table()
    
    def create_reports_tab(self):
        """Crear pestaña de reportes"""
        reports_widget = QWidget()
        layout = QVBoxLayout(reports_widget)
        
        # Pestañas de reportes
        reports_tab_widget = QTabWidget()
        
        # Reporte de Ventas
        sales_report_widget = QWidget()
        self.setup_sales_report_tab(sales_report_widget)
        reports_tab_widget.addTab(sales_report_widget, "Ventas")
        
        # Reporte de Stock
        stock_report_widget = QWidget()
        self.setup_stock_report_tab(stock_report_widget)
        reports_tab_widget.addTab(stock_report_widget, "Stock")
        
        # Reporte de Cuenta Corriente
        cc_report_widget = QWidget()
        self.setup_cc_report_tab(cc_report_widget)
        reports_tab_widget.addTab(cc_report_widget, "Cuenta Corriente")
        
        layout.addWidget(reports_tab_widget)
        self.tab_widget.addTab(reports_widget, "📊 Reportes")
    
    def setup_sales_report_tab(self, widget):
        """Configurar pestaña de reporte de ventas"""
        layout = QVBoxLayout(widget)
        
        # Filtros de fecha
        filters_group = QGroupBox("Filtros")
        filters_layout = QGridLayout(filters_group)
        
        filters_layout.addWidget(QLabel("Desde:"), 0, 0)
        self.sales_from_date = QDateEdit()
        self.sales_from_date.setDate(QDate.currentDate().addDays(-30))
        filters_layout.addWidget(self.sales_from_date, 0, 1)
        
        filters_layout.addWidget(QLabel("Hasta:"), 0, 2)
        self.sales_to_date = QDateEdit()
        self.sales_to_date.setDate(QDate.currentDate())
        filters_layout.addWidget(self.sales_to_date, 0, 3)
        
        generate_sales_report_btn = QPushButton("Generar Reporte")
        generate_sales_report_btn.clicked.connect(self.generate_sales_report)
        filters_layout.addWidget(generate_sales_report_btn, 0, 4)
        
        layout.addWidget(filters_group)
        
        # Área de resultados
        self.sales_report_text = QTextEdit()
        self.sales_report_text.setReadOnly(True)
        layout.addWidget(self.sales_report_text)
    
    def setup_stock_report_tab(self, widget):
        """Configurar pestaña de reporte de stock"""
        layout = QVBoxLayout(widget)
        
        # Botones de acción
        buttons_layout = QHBoxLayout()
        
        stock_bajo_btn = QPushButton("Stock Bajo/Sin Stock")
        stock_bajo_btn.clicked.connect(self.generate_low_stock_report)
        buttons_layout.addWidget(stock_bajo_btn)
        
        productos_vendidos_btn = QPushButton("Productos Más Vendidos")
        productos_vendidos_btn.clicked.connect(self.show_top_products_dialog)
        buttons_layout.addWidget(productos_vendidos_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        # Tabla de resultados
        self.stock_report_table = QTableWidget()
        layout.addWidget(self.stock_report_table)
    
    def setup_cc_report_tab(self, widget):
        """Configurar pestaña de reporte de cuenta corriente"""
        layout = QVBoxLayout(widget)
        
        # Selección de cliente
        client_layout = QHBoxLayout()
        
        client_layout.addWidget(QLabel("Cliente:"))
        self.cc_client_combo = QComboBox()
        self.load_clients_for_cc()
        client_layout.addWidget(self.cc_client_combo)
        
        generate_cc_report_btn = QPushButton("Generar Reporte")
        generate_cc_report_btn.clicked.connect(self.generate_cc_report)
        client_layout.addWidget(generate_cc_report_btn)
        
        client_layout.addStretch()
        layout.addLayout(client_layout)
        
        # Tabla de movimientos
        self.cc_report_table = QTableWidget()
        self.cc_report_table.setColumnCount(6)
        self.cc_report_table.setHorizontalHeaderLabels([
            "Fecha", "Tipo", "Concepto", "Importe", "Saldo", "Estado"
        ])
        layout.addWidget(self.cc_report_table)
    
    def create_admin_tab(self):
        """Crear pestaña de administración"""
        admin_widget = QWidget()
        layout = QVBoxLayout(admin_widget)
        
        layout.addWidget(QLabel("Módulo de Administración - En desarrollo"))
        self.tab_widget.addTab(admin_widget, "⚙️ Administración")
    
    def search_products(self):
        """Buscar productos"""
        search_term = self.product_search.text().strip()
        if not search_term:
            return
        
        products = self.product_manager.buscar_producto(search_term)
        
        self.products_list.clear()
        for product in products:
            item_text = f"{product['nombre']} - ${product['precio_venta']:.2f} (Stock: {product['stock_actual']})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, product)
            self.products_list.addItem(item)
        
        # Si es un código de barras exacto, agregar automáticamente
        if len(products) == 1 and search_term == products[0]['codigo_barras']:
            self.add_product_to_cart_by_data(products[0])
            self.product_search.clear()
    
    def add_product_to_cart(self, item):
        """Agregar producto al carrito desde la lista"""
        product_data = item.data(Qt.UserRole)
        self.add_product_to_cart_by_data(product_data)
    
    def add_product_to_cart_by_data(self, product_data):
        """Agregar producto al carrito por datos"""
        if product_data['stock_actual'] <= 0:
            QMessageBox.warning(self, "Sin Stock", "Este producto no tiene stock disponible")
            return
        
        # Verificar si ya está en el carrito
        for i, item in enumerate(self.cart_items):
            if item['producto_id'] == product_data['id']:
                # Incrementar cantidad
                self.cart_items[i]['cantidad'] += 1
                break
        else:
            # Agregar nuevo item
            self.cart_items.append({
                'producto_id': product_data['id'],
                'nombre': product_data['nombre'],
                'cantidad': 1,
                'precio_unitario': float(product_data['precio_venta']),
                'descuento': 0,
                'descuento_porcentaje': 0
            })
        
        self.update_cart_display()
    
    def update_cart_display(self):
        """Actualizar visualización del carrito"""
        self.cart_table.setRowCount(len(self.cart_items))
        
        subtotal = 0
        total_discount = 0
        
        for i, item in enumerate(self.cart_items):
            # Producto
            self.cart_table.setItem(i, 0, QTableWidgetItem(item['nombre']))
            
            # Cantidad
            quantity_spin = QSpinBox()
            quantity_spin.setMinimum(1)
            quantity_spin.setValue(item['cantidad'])
            quantity_spin.valueChanged.connect(lambda v, idx=i: self.update_item_quantity(idx, v))
            self.cart_table.setCellWidget(i, 1, quantity_spin)
            
            # Precio unitario
            self.cart_table.setItem(i, 2, QTableWidgetItem(f"${item['precio_unitario']:.2f}"))
            
            # Descuento
            discount_spin = QDoubleSpinBox()
            discount_spin.setMaximum(100)
            discount_spin.setValue(item['descuento_porcentaje'])
            discount_spin.valueChanged.connect(lambda v, idx=i: self.update_item_discount(idx, v))
            self.cart_table.setCellWidget(i, 3, discount_spin)
            
            # Subtotal del item
            item_subtotal = item['cantidad'] * item['precio_unitario']
            item_discount = item_subtotal * (item['descuento_porcentaje'] / 100)
            item_final = item_subtotal - item_discount
            
            self.cart_table.setItem(i, 4, QTableWidgetItem(f"${item_final:.2f}"))
            
            # Botón eliminar
            remove_btn = QPushButton("Eliminar")
            remove_btn.clicked.connect(lambda checked, idx=i: self.remove_cart_item(idx))
            self.cart_table.setCellWidget(i, 5, remove_btn)
            
            subtotal += item_subtotal
            total_discount += item_discount
        
        # Actualizar totales
        tax_amount = (subtotal - total_discount) * 0.21
        total = subtotal - total_discount + tax_amount
        
        self.subtotal_label.setText(f"${subtotal:.2f}")
        self.discount_label.setText(f"${total_discount:.2f}")
        self.tax_label.setText(f"${tax_amount:.2f}")
        self.total_label.setText(f"${total:.2f}")
    
    def update_item_quantity(self, index: int, quantity: int):
        """Actualizar cantidad de un item"""
        self.cart_items[index]['cantidad'] = quantity
        self.update_cart_display()
    
    def update_item_discount(self, index: int, discount: float):
        """Actualizar descuento de un item"""
        self.cart_items[index]['descuento_porcentaje'] = discount
        self.update_cart_display()
    
    def remove_cart_item(self, index: int):
        """Eliminar item del carrito"""
        del self.cart_items[index]
        self.update_cart_display()
    
    def clear_cart(self):
        """Limpiar carrito"""
        if self.cart_items:
            reply = QMessageBox.question(
                self, "Confirmar", "¿Desea limpiar el carrito?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.cart_items.clear()
                self.update_cart_display()
    
    def process_sale(self):
        """Procesar venta"""
        if not self.cart_items:
            QMessageBox.warning(self, "Carrito Vacío", "Agregue productos al carrito")
            return
        
        # Mostrar diálogo de procesamiento de venta
        dialog = SaleProcessDialog(self.cart_items, self.db_manager)
        if dialog.exec_() == QDialog.Accepted:
            # Procesar la venta
            success, message, venta_id = self.sales_manager.crear_venta(
                self.cart_items,
                cliente_id=dialog.selected_customer_id,
                tipo_venta=dialog.sale_type,
                metodo_pago=dialog.payment_method,
                vendedor_id=self.user_manager.current_user['id'],
                caja_id=1
            )
            
            if success:
                QMessageBox.information(self, "Venta Completada", message)
                
                # Preguntar si desea imprimir ticket
                reply = QMessageBox.question(
                    self, "Imprimir Ticket", "¿Desea imprimir el ticket?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    self.print_ticket(venta_id)
                
                # Limpiar carrito
                self.cart_items.clear()
                self.update_cart_display()
                self.product_search.setFocus()
            else:
                QMessageBox.critical(self, "Error", message)
    
    def print_ticket(self, venta_id: int):
        """Imprimir ticket de venta"""
        try:
            # Obtener datos de la venta
            cursor = self.db_manager.connection.cursor()
            cursor.execute("""
                SELECT v.*, c.nombre as cliente_nombre, u.nombre_completo as vendedor_nombre
                FROM ventas v
                LEFT JOIN clientes c ON v.cliente_id = c.id
                LEFT JOIN usuarios u ON v.vendedor_id = u.id
                WHERE v.id = ?
            """, (venta_id,))
            
            venta = dict(cursor.fetchone())
            
            # Obtener detalles
            cursor.execute("""
                SELECT dv.*, p.nombre as producto_nombre
                FROM detalle_ventas dv
                JOIN productos p ON dv.producto_id = p.id
                WHERE dv.venta_id = ?
            """, (venta_id,))
            
            detalles = [dict(row) for row in cursor.fetchall()]
            
            # Crear contenido del ticket
            ticket_content = self.generate_ticket_content(venta, detalles)
            
            # Mostrar diálogo de impresión
            dialog = QDialog(self)
            dialog.setWindowTitle("Vista Previa del Ticket")
            layout = QVBoxLayout(dialog)
            
            text_edit = QTextEdit()
            text_edit.setPlainText(ticket_content)
            text_edit.setFont(QFont("Courier", 10))
            layout.addWidget(text_edit)
            
            button_layout = QHBoxLayout()
            print_btn = QPushButton("Imprimir")
            print_btn.clicked.connect(lambda: self.do_print(ticket_content))
            cancel_btn = QPushButton("Cancelar")
            cancel_btn.clicked.connect(dialog.reject)
            
            button_layout.addWidget(print_btn)
            button_layout.addWidget(cancel_btn)
            layout.addLayout(button_layout)
            
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generando ticket: {str(e)}")
    
    def generate_ticket_content(self, venta: Dict, detalles: List[Dict]) -> str:
        """Generar contenido del ticket"""
        content = []
        content.append("=" * 40)
        content.append("         MI ALMACÉN")
        content.append("=" * 40)
        content.append(f"Ticket: {venta['numero_ticket']}")
        content.append(f"Fecha: {venta['fecha_venta']}")
        content.append(f"Vendedor: {venta['vendedor_nombre']}")
        if venta['cliente_nombre']:
            content.append(f"Cliente: {venta['cliente_nombre']}")
        content.append("-" * 40)
        
        for detalle in detalles:
            content.append(f"{detalle['producto_nombre'][:25]:<25}")
            content.append(f"  {detalle['cantidad']:.2f} x ${detalle['precio_unitario']:.2f} = ${detalle['subtotal']:.2f}")
        
        content.append("-" * 40)
        content.append(f"Subtotal: ${venta['subtotal']:.2f}")
        if venta['descuento'] > 0:
            content.append(f"Descuento: ${venta['descuento']:.2f}")
        content.append(f"IVA (21%): ${venta['impuestos']:.2f}")
        content.append(f"TOTAL: ${venta['total']:.2f}")
        content.append("-" * 40)
        content.append(f"Pago: {venta['metodo_pago']}")
        content.append("")
        content.append("    ¡Gracias por su compra!")
        content.append("=" * 40)
        
        return "\n".join(content)
    
    def do_print(self, content: str):
        """Realizar impresión"""
        printer = QPrinter()
        print_dialog = QPrintDialog(printer, self)
        
        if print_dialog.exec_() == QPrintDialog.Accepted:
            # Aquí implementarías la lógica de impresión real
            QMessageBox.information(self, "Impresión", "Ticket enviado a la impresora")
    
    def show_add_product_dialog(self):
        """Mostrar diálogo para agregar producto"""
        dialog = AddProductDialog(self.db_manager)
        if dialog.exec_() == QDialog.Accepted:
            self.load_stock_data()
    
    def load_stock_data(self):
        """Cargar datos de stock"""
        cursor = self.db_manager.connection.cursor()
        cursor.execute("""
            SELECT p.*, c.nombre as categoria_nombre
            FROM productos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            WHERE p.activo = 1
            ORDER BY p.nombre
        """)
        
        products = cursor.fetchall()
        self.stock_table.setRowCount(len(products))
        
        for i, product in enumerate(products):
            self.stock_table.setItem(i, 0, QTableWidgetItem(product['codigo_barras'] or ''))
            self.stock_table.setItem(i, 1, QTableWidgetItem(product['nombre']))
            self.stock_table.setItem(i, 2, QTableWidgetItem(product['categoria_nombre'] or ''))
            self.stock_table.setItem(i, 3, QTableWidgetItem(str(product['stock_actual'])))
            self.stock_table.setItem(i, 4, QTableWidgetItem(str(product['stock_minimo'])))
            self.stock_table.setItem(i, 5, QTableWidgetItem(f"${product['precio_venta']:.2f}"))
            
            # Estado según stock
            if product['stock_actual'] <= 0:
                status = "SIN STOCK"
                color = "red"
            elif product['stock_actual'] <= product['stock_minimo']:
                status = "STOCK BAJO"
                color = "orange"
            else:
                status = "OK"
                color = "green"
            
            status_item = QTableWidgetItem(status)
            status_item.setForeground(QColor(color))
            self.stock_table.setItem(i, 6, status_item)
            
            # Botones de acción
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            
            edit_btn = QPushButton("Editar")
            edit_btn.clicked.connect(lambda checked, pid=product['id']: self.edit_product(pid))
            actions_layout.addWidget(edit_btn)
            
            self.stock_table.setCellWidget(i, 7, actions_widget)
    
    def edit_product(self, product_id: int):
        """Editar producto"""
        # Implementar diálogo de edición
        QMessageBox.information(self, "Función", f"Editar producto ID: {product_id}")
    
    
    # ==================== MÉTODOS DE COMPRAS ====================
    
    def search_providers(self):
        """Buscar proveedores"""
        search_term = self.provider_search.text().strip()
        if len(search_term) < 2:
            self.load_providers()
            return
        
        providers = self.provider_manager.buscar_proveedor(search_term)
        self.update_providers_list(providers)
    
    def load_providers(self):
        """Cargar todos los proveedores"""
        providers = self.provider_manager.obtener_proveedores()
        self.update_providers_list(providers)
    
    def update_providers_list(self, providers):
        """Actualizar lista de proveedores"""
        self.providers_list.clear()
        for provider in providers:
            item_text = f"{provider['nombre']} - {provider['cuit_dni'] or 'Sin CUIT'}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, provider)
            self.providers_list.addItem(item)
    
    def select_provider(self, item):
        """Seleccionar proveedor para compra"""
        provider_data = item.data(Qt.UserRole)
        self.selected_provider = provider_data
        self.selected_provider_label.setText(f"Proveedor: {provider_data['nombre']}")
        self.selected_provider_label.setStyleSheet("font-weight: bold; color: green;")
    
    def search_products_for_purchase(self):
        """Buscar productos para agregar a compra"""
        search_term = self.purchase_product_search.text().strip()
        if len(search_term) < 2:
            self.purchase_products_list.clear()
            return
        
        products = self.product_manager.buscar_producto(search_term)
        
        self.purchase_products_list.clear()
        for product in products:
            item_text = f"{product['nombre']} - Stock: {product['stock_actual']}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, product)
            self.purchase_products_list.addItem(item)
    
    def add_product_to_purchase(self, item):
        """Agregar producto a la orden de compra"""
        if not hasattr(self, 'selected_provider'):
            QMessageBox.warning(self, "Error", "Seleccione un proveedor primero")
            return
        
        product_data = item.data(Qt.UserRole)
        
        # Verificar si ya está en la compra
        for i, item in enumerate(self.purchase_items):
            if item['producto_id'] == product_data['id']:
                self.purchase_items[i]['cantidad'] += 1
                break
        else:
            # Agregar nuevo item
            self.purchase_items.append({
                'producto_id': product_data['id'],
                'nombre': product_data['nombre'],
                'cantidad': 1,
                'precio_unitario': float(product_data.get('precio_compra', 0) or 0),
                'descuento': 0,
                'descuento_porcentaje': 0
            })
        
        self.update_purchase_display()
    
    def update_purchase_display(self):
        """Actualizar visualización de la orden de compra"""
        self.purchase_table.setRowCount(len(self.purchase_items))
        
        subtotal = 0
        total_discount = 0
        
        for i, item in enumerate(self.purchase_items):
            # Producto
            self.purchase_table.setItem(i, 0, QTableWidgetItem(item['nombre']))
            
            # Cantidad
            quantity_spin = QSpinBox()
            quantity_spin.setMinimum(1)
            quantity_spin.setMaximum(99999)
            quantity_spin.setValue(item['cantidad'])
            quantity_spin.valueChanged.connect(lambda v, idx=i: self.update_purchase_item_quantity(idx, v))
            self.purchase_table.setCellWidget(i, 1, quantity_spin)
            
            # Precio unitario
            price_spin = QDoubleSpinBox()
            price_spin.setMaximum(999999)
            price_spin.setValue(item['precio_unitario'])
            price_spin.valueChanged.connect(lambda v, idx=i: self.update_purchase_item_price(idx, v))
            self.purchase_table.setCellWidget(i, 2, price_spin)
            
            # Descuento
            discount_spin = QDoubleSpinBox()
            discount_spin.setMaximum(100)
            discount_spin.setValue(item['descuento_porcentaje'])
            discount_spin.valueChanged.connect(lambda v, idx=i: self.update_purchase_item_discount(idx, v))
            self.purchase_table.setCellWidget(i, 3, discount_spin)
            
            # Subtotal del item
            item_subtotal = item['cantidad'] * item['precio_unitario']
            item_discount = item_subtotal * (item['descuento_porcentaje'] / 100)
            item_final = item_subtotal - item_discount
            
            self.purchase_table.setItem(i, 4, QTableWidgetItem(f"${item_final:.2f}"))
            
            # Botón eliminar
            remove_btn = QPushButton("Eliminar")
            remove_btn.clicked.connect(lambda checked, idx=i: self.remove_purchase_item(idx))
            self.purchase_table.setCellWidget(i, 5, remove_btn)
            
            subtotal += item_subtotal
            total_discount += item_discount
        
        # Actualizar totales
        tax_amount = (subtotal - total_discount) * 0.21
        total = subtotal - total_discount + tax_amount
        
        self.purchase_subtotal_label.setText(f"${subtotal:.2f}")
        self.purchase_discount_label.setText(f"${total_discount:.2f}")
        self.purchase_tax_label.setText(f"${tax_amount:.2f}")
        self.purchase_total_label.setText(f"${total:.2f}")
    
    def update_purchase_item_quantity(self, index: int, quantity: int):
        """Actualizar cantidad de un item de compra"""
        self.purchase_items[index]['cantidad'] = quantity
        self.update_purchase_display()
    
    def update_purchase_item_price(self, index: int, price: float):
        """Actualizar precio de un item de compra"""
        self.purchase_items[index]['precio_unitario'] = price
        self.update_purchase_display()
    
    def update_purchase_item_discount(self, index: int, discount: float):
        """Actualizar descuento de un item de compra"""
        self.purchase_items[index]['descuento_porcentaje'] = discount
        self.update_purchase_display()
    
    def remove_purchase_item(self, index: int):
        """Eliminar item de la orden de compra"""
        del self.purchase_items[index]
        self.update_purchase_display()
    
    def clear_purchase(self):
        """Limpiar orden de compra"""
        if self.purchase_items:
            reply = QMessageBox.question(
                self, "Confirmar", "¿Desea limpiar la orden de compra?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.purchase_items.clear()
                self.update_purchase_display()
    
    def create_purchase_order(self):
        """Crear orden de compra"""
        if not hasattr(self, 'selected_provider'):
            QMessageBox.warning(self, "Error", "Seleccione un proveedor")
            return
        
        if not self.purchase_items:
            QMessageBox.warning(self, "Error", "Agregue productos a la orden")
            return
        
        success, message, order_id = self.purchase_manager.crear_compra(
            self.purchase_items,
            self.selected_provider['id'],
            self.invoice_number_input.text().strip() or None,
            self.user_manager.current_user['id'],
            self.due_date_input.date().toString('yyyy-MM-dd')
        )
        
        if success:
            QMessageBox.information(self, "Éxito", message)
            
            # Preguntar si desea marcar como recibida inmediatamente
            reply = QMessageBox.question(
                self, "Recibir Mercadería", 
                "¿Desea marcar esta compra como recibida y actualizar el stock?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.receive_purchase_immediately(order_id)
            
            # Limpiar formulario
            self.purchase_items.clear()
            self.update_purchase_display()
            self.invoice_number_input.clear()
            self.load_purchase_orders()
        else:
            QMessageBox.critical(self, "Error", message)
    
    def receive_purchase_immediately(self, order_id: int):
        """Recibir compra inmediatamente"""
        items_recibidos = []
        for item in self.purchase_items:
            items_recibidos.append({
                'producto_id': item['producto_id'],
                'cantidad_recibida': item['cantidad'],
                'precio_unitario': item['precio_unitario']
            })
        
        success, message = self.purchase_manager.recibir_compra(
            order_id, items_recibidos, self.user_manager.current_user['id']
        )
        
        if success:
            QMessageBox.information(self, "Éxito", "Stock actualizado correctamente")
        else:
            QMessageBox.critical(self, "Error", message)
    
    def load_purchase_orders(self):
        """Cargar órdenes de compra"""
        estado_filter = self.order_status_filter.currentText()
        estado = None if estado_filter == 'TODAS' else estado_filter
        
        orders = self.purchase_manager.obtener_compras(estado)
        
        self.purchase_orders_table.setRowCount(len(orders))
        
        for i, order in enumerate(orders):
            self.purchase_orders_table.setItem(i, 0, QTableWidgetItem(str(order['id'])))
            self.purchase_orders_table.setItem(i, 1, QTableWidgetItem(order['fecha_compra'][:10]))
            self.purchase_orders_table.setItem(i, 2, QTableWidgetItem(order['proveedor_nombre'] or ''))
            self.purchase_orders_table.setItem(i, 3, QTableWidgetItem(order['numero_factura'] or ''))
            self.purchase_orders_table.setItem(i, 4, QTableWidgetItem(f"${order['total']:.2f}"))
            
            # Estado con color
            status_item = QTableWidgetItem(order['estado'])
            if order['estado'] == 'PENDIENTE':
                status_item.setForeground(QColor('orange'))
            elif order['estado'] == 'RECIBIDA':
                status_item.setForeground(QColor('green'))
            else:
                status_item.setForeground(QColor('red'))
            self.purchase_orders_table.setItem(i, 5, status_item)
            
            self.purchase_orders_table.setItem(i, 6, QTableWidgetItem(order['fecha_vencimiento'] or ''))
            
            # Botones de acción
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            
            if order['estado'] == 'PENDIENTE':
                receive_btn = QPushButton("Recibir")
                receive_btn.clicked.connect(lambda checked, oid=order['id']: self.show_receive_dialog(oid))
                actions_layout.addWidget(receive_btn)
            
            view_btn = QPushButton("Ver")
            view_btn.clicked.connect(lambda checked, oid=order['id']: self.view_purchase_order(oid))
            actions_layout.addWidget(view_btn)
            
            self.purchase_orders_table.setCellWidget(i, 7, actions_widget)
    
    def filter_purchase_orders(self):
        """Filtrar órdenes de compra por estado"""
        self.load_purchase_orders()
    
    def show_receive_dialog(self, order_id: int):
        """Mostrar diálogo para recibir mercadería"""
        dialog = ReceivePurchaseDialog(order_id, self.db_manager, self.purchase_manager)
        if dialog.exec_() == QDialog.Accepted:
            self.load_purchase_orders()
    
    def view_purchase_order(self, order_id: int):
        """Ver detalles de orden de compra"""
        QMessageBox.information(self, "Función", f"Ver orden de compra #{order_id}")
    
    # ==================== MÉTODOS DE PROVEEDORES ====================
    
    def show_add_provider_dialog(self):
        """Mostrar diálogo para agregar proveedor"""
        dialog = AddProviderDialog(self.db_manager, self.provider_manager)
        if dialog.exec_() == QDialog.Accepted:
            self.load_providers()
            self.load_providers_table()
    
    def load_providers_table(self):
        """Cargar tabla de proveedores"""
        providers = self.provider_manager.obtener_proveedores()
        
        self.providers_table.setRowCount(len(providers))
        
        for i, provider in enumerate(providers):
            self.providers_table.setItem(i, 0, QTableWidgetItem(provider['nombre']))
            self.providers_table.setItem(i, 1, QTableWidgetItem(provider['cuit_dni'] or ''))
            self.providers_table.setItem(i, 2, QTableWidgetItem(provider['telefono'] or ''))
            self.providers_table.setItem(i, 3, QTableWidgetItem(provider['email'] or ''))
            self.providers_table.setItem(i, 4, QTableWidgetItem(provider['contacto_principal'] or ''))
            self.providers_table.setItem(i, 5, QTableWidgetItem(f"{provider['descuento_porcentaje']:.1f}%"))
            
            # Botones de acción
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            
            edit_btn = QPushButton("Editar")
            edit_btn.clicked.connect(lambda checked, pid=provider['id']: self.edit_provider(pid))
            actions_layout.addWidget(edit_btn)
            
            self.providers_table.setCellWidget(i, 6, actions_widget)
    
    def filter_providers_table(self, text):
        """Filtrar tabla de proveedores"""
        for i in range(self.providers_table.rowCount()):
            item = self.providers_table.item(i, 0)  # Nombre
            if item:
                match = text.lower() in item.text().lower()
                self.providers_table.setRowHidden(i, not match)
    
    def edit_provider(self, provider_id: int):
        """Editar proveedor"""
        QMessageBox.information(self, "Función", f"Editar proveedor ID: {provider_id}")
    
    # ==================== MÉTODOS DE REPORTES ====================
    
    def generate_sales_report(self):
        """Generar reporte de ventas"""
        fecha_desde = self.sales_from_date.date().toString('yyyy-MM-dd')
        fecha_hasta = self.sales_to_date.date().toString('yyyy-MM-dd')
        
        reporte = self.report_manager.reporte_ventas_periodo(fecha_desde, fecha_hasta)
        
        # Formatear reporte
        content = []
        content.append("=" * 50)
        content.append(f"REPORTE DE VENTAS")
        content.append(f"Período: {fecha_desde} al {fecha_hasta}")
        content.append("=" * 50)
        content.append("")
        
        resumen = reporte['resumen']
        content.append("RESUMEN GENERAL:")
        content.append(f"Total de ventas: {resumen['total_ventas'] or 0}")
        content.append(f"Total facturado: ${resumen['total_facturado'] or 0:.2f}")
        content.append(f"Ticket promedio: ${resumen['ticket_promedio'] or 0:.2f}")
        content.append(f"Total descuentos: ${resumen['total_descuentos'] or 0:.2f}")
        content.append("")
        
        content.append("VENTAS POR DÍA:")
        for venta_dia in reporte['ventas_diarias']:
            content.append(f"{venta_dia['fecha']}: {venta_dia['cantidad_ventas']} ventas - ${venta_dia['total_dia']:.2f}")
        content.append("")
        
        content.append("VENTAS POR MÉTODO DE PAGO:")
        for metodo in reporte['por_metodo_pago']:
            content.append(f"{metodo['metodo_pago']}: {metodo['cantidad']} ventas - ${metodo['total']:.2f}")
        
        self.sales_report_text.setPlainText("\n".join(content))
    
    def generate_low_stock_report(self):
        """Generar reporte de stock bajo"""
        productos = self.report_manager.reporte_stock_bajo()
        
        self.stock_report_table.setColumnCount(6)
        self.stock_report_table.setHorizontalHeaderLabels([
            "Producto", "Código", "Stock Actual", "Stock Mínimo", "Categoría", "Proveedor"
        ])
        self.stock_report_table.setRowCount(len(productos))
        
        for i, producto in enumerate(productos):
            self.stock_report_table.setItem(i, 0, QTableWidgetItem(producto['nombre']))
            self.stock_report_table.setItem(i, 1, QTableWidgetItem(producto['codigo_barras'] or ''))
            
            # Stock actual con color
            stock_item = QTableWidgetItem(str(producto['stock_actual']))
            if producto['stock_actual'] <= 0:
                stock_item.setForeground(QColor('red'))
            elif producto['stock_actual'] <= producto['stock_minimo']:
                stock_item.setForeground(QColor('orange'))
            self.stock_report_table.setItem(i, 2, stock_item)
            
            self.stock_report_table.setItem(i, 3, QTableWidgetItem(str(producto['stock_minimo'])))
            self.stock_report_table.setItem(i, 4, QTableWidgetItem(producto['categoria'] or ''))
            self.stock_report_table.setItem(i, 5, QTableWidgetItem(producto['proveedor'] or ''))
    
    def show_top_products_dialog(self):
        """Mostrar diálogo de productos más vendidos"""
        dialog = TopProductsDialog(self.report_manager)
        dialog.exec_()
    
    def load_clients_for_cc(self):
        """Cargar clientes para cuenta corriente"""
        cursor = self.db_manager.connection.cursor()
        cursor.execute("""
            SELECT id, nombre, apellido, saldo_cuenta_corriente 
            FROM clientes 
            WHERE activo = 1 AND saldo_cuenta_corriente != 0
            ORDER BY nombre
        """)
        clients = cursor.fetchall()
        
        self.cc_client_combo.addItem("Todos los clientes", None)
        for client in clients:
            display_name = f"{client['nombre']} {client['apellido'] or ''}".strip()
            display_name += f" (${client['saldo_cuenta_corriente']:.2f})"
            self.cc_client_combo.addItem(display_name, client['id'])
    
    def generate_cc_report(self):
        """Generar reporte de cuenta corriente"""
        client_id = self.cc_client_combo.currentData()
        
        movimientos = self.report_manager.reporte_cuenta_corriente(client_id)
        
        self.cc_report_table.setRowCount(len(movimientos))
        
        for i, mov in enumerate(movimientos):
            self.cc_report_table.setItem(i, 0, QTableWidgetItem(mov['fecha_movimiento'][:10]))
            
            # Tipo con color
            tipo_item = QTableWidgetItem(mov['tipo_movimiento'])
            if mov['tipo_movimiento'] == 'DEBE':
                tipo_item.setForeground(QColor('red'))
            else:
                tipo_item.setForeground(QColor('green'))
            self.cc_report_table.setItem(i, 1, tipo_item)
            
            self.cc_report_table.setItem(i, 2, QTableWidgetItem(mov['concepto']))
            self.cc_report_table.setItem(i, 3, QTableWidgetItem(f"${mov['importe']:.2f}"))
            self.cc_report_table.setItem(i, 4, QTableWidgetItem(f"${mov['saldo_nuevo']:.2f}"))
            self.cc_report_table.setItem(i, 5, QTableWidgetItem("Activo"))
    
    def logout(self):
        """Cerrar sesión"""
        reply = QMessageBox.question(
            self, "Cerrar Sesión", "¿Desea cerrar la sesión actual?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.user_manager.logout()
            self.close()
            # Mostrar login nuevamente
            app = QApplication.instance()
            if app:
                login_window = POSWindow()
                login_window.show()

class LoginDialog(QDialog):
    """Diálogo de login"""
    
    def __init__(self, user_manager: UserManager):
        super().__init__()
        self.user_manager = user_manager
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("AlmacénPro - Iniciar Sesión")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        # Logo/Título
        title = QLabel("AlmacénPro")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2E86AB; margin: 20px;")
        layout.addWidget(title)
        
        subtitle = QLabel("Sistema de Gestión Completo")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: gray; margin-bottom: 30px;")
        layout.addWidget(subtitle)
        
        # Campos de login
        form_layout = QFormLayout()
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Usuario")
        form_layout.addRow("Usuario:", self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.returnPressed.connect(self.login)
        form_layout.addRow("Contraseña:", self.password_input)
        
        layout.addLayout(form_layout)
        
        # Botones
        button_layout = QHBoxLayout()
        
        login_btn = QPushButton("Iniciar Sesión")
        login_btn.setStyleSheet("background-color: #2E86AB; color: white; padding: 10px; font-weight: bold;")
        login_btn.clicked.connect(self.login)
        button_layout.addWidget(login_btn)
        
        cancel_btn = QPushButton("Salir")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Valores por defecto para testing
        self.username_input.setText("admin")
        self.password_input.setText("admin123")
        self.username_input.setFocus()
    
    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Error", "Complete todos los campos")
            return
        
        success, message = self.user_manager.login(username, password)
        
        if success:
            self.accept()
        else:
            QMessageBox.critical(self, "Error de Autenticación", message)
            self.password_input.clear()
            self.password_input.setFocus()

class SaleProcessDialog(QDialog):
    """Diálogo para procesar venta"""
    
    def __init__(self, cart_items: List[Dict], db_manager: DatabaseManager):
        super().__init__()
        self.cart_items = cart_items
        self.db_manager = db_manager
        self.selected_customer_id = None
        self.sale_type = 'CONTADO'
        self.payment_method = 'EFECTIVO'
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Procesar Venta")
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout()
        
        # Resumen de venta
        summary_group = QGroupBox("Resumen de Venta")
        summary_layout = QVBoxLayout(summary_group)
        
        total = sum(item['cantidad'] * item['precio_unitario'] for item in self.cart_items)
        items_count = len(self.cart_items)
        
        summary_layout.addWidget(QLabel(f"Items: {items_count}"))
        summary_layout.addWidget(QLabel(f"Total: ${total:.2f}"))
        
        layout.addWidget(summary_group)
        
        # Tipo de venta
        sale_type_group = QGroupBox("Tipo de Venta")
        sale_type_layout = QVBoxLayout(sale_type_group)
        
        self.contado_radio = QRadioButton("Contado")
        self.contado_radio.setChecked(True)
        self.contado_radio.toggled.connect(lambda: self.set_sale_type('CONTADO'))
        sale_type_layout.addWidget(self.contado_radio)
        
        self.credito_radio = QRadioButton("Cuenta Corriente")
        self.credito_radio.toggled.connect(lambda: self.set_sale_type('CUENTA_CORRIENTE'))
        sale_type_layout.addWidget(self.credito_radio)
        
        layout.addWidget(sale_type_group)
        
        # Método de pago
        payment_group = QGroupBox("Método de Pago")
        payment_layout = QVBoxLayout(payment_group)
        
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(['EFECTIVO', 'TARJETA_DEBITO', 'TARJETA_CREDITO', 'TRANSFERENCIA'])
        self.payment_combo.currentTextChanged.connect(self.set_payment_method)
        payment_layout.addWidget(self.payment_combo)
        
        layout.addWidget(payment_group)
        
        # Cliente (solo si es cuenta corriente)
        self.customer_group = QGroupBox("Cliente")
        customer_layout = QHBoxLayout(self.customer_group)
        
        self.customer_combo = QComboBox()
        self.load_customers()
        customer_layout.addWidget(self.customer_combo)
        
        add_customer_btn = QPushButton("Nuevo Cliente")
        customer_layout.addWidget(add_customer_btn)
        
        self.customer_group.setEnabled(False)
        layout.addWidget(self.customer_group)
        
        # Botones
        button_layout = QHBoxLayout()
        
        process_btn = QPushButton("Procesar Venta")
        process_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        process_btn.clicked.connect(self.accept)
        button_layout.addWidget(process_btn)
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def set_sale_type(self, sale_type: str):
        self.sale_type = sale_type
        self.customer_group.setEnabled(sale_type == 'CUENTA_CORRIENTE')
    
    def set_payment_method(self, method: str):
        self.payment_method = method
    
    def load_customers(self):
        cursor = self.db_manager.connection.cursor()
        cursor.execute("SELECT id, nombre, apellido FROM clientes WHERE activo = 1 ORDER BY nombre")
        customers = cursor.fetchall()
        
        self.customer_combo.addItem("Seleccionar cliente...", None)
        for customer in customers:
            display_name = f"{customer['nombre']} {customer['apellido'] or ''}".strip()
            self.customer_combo.addItem(display_name, customer['id'])
    
    def accept(self):
        if self.sale_type == 'CUENTA_CORRIENTE':
            self.selected_customer_id = self.customer_combo.currentData()
            if not self.selected_customer_id:
                QMessageBox.warning(self, "Error", "Seleccione un cliente para venta a cuenta corriente")
                return
        
        super().accept()

class AddProductDialog(QDialog):
    """Diálogo para agregar producto"""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Agregar Producto")
        self.setFixedSize(600, 500)
        
        layout = QVBoxLayout()
        
        # Formulario de producto
        form_layout = QFormLayout()
        
        self.barcode_input = QLineEdit()
        form_layout.addRow("Código de Barras:", self.barcode_input)
        
        self.name_input = QLineEdit()
        form_layout.addRow("Nombre:", self.name_input)
        
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(60)
        form_layout.addRow("Descripción:", self.description_input)
        
        self.category_combo = QComboBox()
        self.load_categories()
        form_layout.addRow("Categoría:", self.category_combo)
        
        self.purchase_price_input = QDoubleSpinBox()
        self.purchase_price_input.setMaximum(999999)
        form_layout.addRow("Precio Compra:", self.purchase_price_input)
        
        self.sale_price_input = QDoubleSpinBox()
        self.sale_price_input.setMaximum(999999)
        form_layout.addRow("Precio Venta:", self.sale_price_input)
        
        self.stock_input = QSpinBox()
        self.stock_input.setMaximum(999999)
        form_layout.addRow("Stock Inicial:", self.stock_input)
        
        self.min_stock_input = QSpinBox()
        self.min_stock_input.setMaximum(999999)
        form_layout.addRow("Stock Mínimo:", self.min_stock_input)
        
        layout.addLayout(form_layout)
        
        # Botones
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Guardar")
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        save_btn.clicked.connect(self.save_product)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_categories(self):
        cursor = self.db_manager.connection.cursor()
        cursor.execute("SELECT id, nombre FROM categorias WHERE activo = 1 ORDER BY nombre")
        categories = cursor.fetchall()
        
        for category in categories:
            self.category_combo.addItem(category['nombre'], category['id'])
    
    def save_product(self):
        # Validaciones
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Error", "El nombre es obligatorio")
            return
        
        if self.sale_price_input.value() <= 0:
            QMessageBox.warning(self, "Error", "El precio de venta debe ser mayor a 0")
            return
        
        try:
            cursor = self.db_manager.connection.cursor()
            
            cursor.execute("""
                INSERT INTO productos (
                    codigo_barras, nombre, descripcion, categoria_id,
                    precio_compra, precio_venta, stock_actual, stock_minimo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.barcode_input.text().strip() or None,
                self.name_input.text().strip(),
                self.description_input.toPlainText().strip(),
                self.category_combo.currentData(),
                self.purchase_price_input.value(),
                self.sale_price_input.value(),
                self.stock_input.value(),
                self.min_stock_input.value()
            ))
            
            self.db_manager.connection.commit()
            QMessageBox.information(self, "Éxito", "Producto agregado correctamente")
            self.accept()
            
        except sqlite3.IntegrityError as e:
            if "codigo_barras" in str(e):
                QMessageBox.critical(self, "Error", "Ya existe un producto con ese código de barras")
            else:
                QMessageBox.critical(self, "Error", f"Error de integridad: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error guardando producto: {str(e)}")

def main():
    app = QApplication(sys.argv)
    
    # Configurar estilo
    app.setStyle('Fusion')
    
    # Configurar icono de la aplicación
    app.setWindowIcon(QIcon())  # Aquí puedes agregar un icono
    
    # Crear y mostrar ventana principal
    window = POSWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()