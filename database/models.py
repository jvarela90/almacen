"""
Modelos de datos para AlmacénPro v2.0
Definición de estructuras de datos y validaciones
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum
import json

class UserRole(Enum):
    """Roles de usuario del sistema"""
    ADMINISTRADOR = "ADMINISTRADOR"
    GERENTE = "GERENTE"
    VENDEDOR = "VENDEDOR"
    DEPOSITO = "DEPOSITO"
    COLABORADOR = "COLABORADOR"

class TransactionStatus(Enum):
    """Estados de transacciones"""
    PENDING = "PENDIENTE"
    COMPLETED = "COMPLETADO"
    CANCELLED = "CANCELADO"
    REFUNDED = "DEVUELTO"

class ProductType(Enum):
    """Tipos de producto"""
    PHYSICAL = "FISICO"
    SERVICE = "SERVICIO"
    DIGITAL = "DIGITAL"
    COMBO = "COMBO"

@dataclass
class User:
    """Modelo de usuario del sistema"""
    id: Optional[int] = None
    username: str = ""
    email: Optional[str] = None
    password_hash: str = ""
    nombre_completo: str = ""
    telefono: Optional[str] = None
    rol_id: Optional[int] = None
    rol_nombre: Optional[str] = None
    numero_documento: Optional[str] = None
    activo: bool = True
    ultimo_acceso: Optional[datetime] = None
    intentos_fallidos: int = 0
    bloqueado_hasta: Optional[datetime] = None
    permisos: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'nombre_completo': self.nombre_completo,
            'telefono': self.telefono,
            'rol_id': self.rol_id,
            'rol_nombre': self.rol_nombre,
            'numero_documento': self.numero_documento,
            'activo': self.activo,
            'ultimo_acceso': self.ultimo_acceso.isoformat() if self.ultimo_acceso else None,
            'intentos_fallidos': self.intentos_fallidos,
            'permisos': self.permisos,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Crear desde diccionario"""
        user = cls()
        for key, value in data.items():
            if hasattr(user, key):
                if key in ['ultimo_acceso', 'created_at', 'updated_at'] and value:
                    setattr(user, key, datetime.fromisoformat(value) if isinstance(value, str) else value)
                else:
                    setattr(user, key, value)
        return user

@dataclass
class Product:
    """Modelo de producto"""
    id: Optional[int] = None
    codigo_interno: Optional[str] = None
    codigo_barras: Optional[str] = None
    barcode: Optional[str] = None  # Alias para codigo_barras
    nombre: str = ""
    descripcion: Optional[str] = None
    categoria_id: Optional[int] = None
    categoria_nombre: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    
    # Precios
    precio_compra: Decimal = field(default_factory=lambda: Decimal('0.00'))
    precio_venta: Decimal = field(default_factory=lambda: Decimal('0.00'))
    precio_mayorista: Optional[Decimal] = None
    margen_ganancia: Optional[Decimal] = None
    
    # Stock
    stock_actual: Decimal = field(default_factory=lambda: Decimal('0'))
    stock_minimo: Decimal = field(default_factory=lambda: Decimal('0'))
    stock_maximo: Optional[Decimal] = None
    unidad_medida: str = "UN"
    
    # Información adicional
    producto_tipo: ProductType = ProductType.PHYSICAL
    peso: Optional[Decimal] = None
    dimensiones: Optional[str] = None
    ubicacion_deposito: Optional[str] = None
    
    # Control de calidad
    vencimiento: Optional[date] = None
    lote: Optional[str] = None
    requiere_serie: bool = False
    
    # Impuestos
    aplica_iva: bool = True
    porcentaje_iva: Decimal = field(default_factory=lambda: Decimal('21.00'))
    
    # Estado
    activo: bool = True
    es_favorito: bool = False
    
    # Proveedores
    proveedor_id: Optional[int] = None
    proveedor_nombre: Optional[str] = None
    
    # Auditoría
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    
    def __post_init__(self):
        """Validaciones post-inicialización"""
        if self.barcode and not self.codigo_barras:
            self.codigo_barras = self.barcode
        elif self.codigo_barras and not self.barcode:
            self.barcode = self.codigo_barras
    
    @property
    def stock_bajo(self) -> bool:
        """Verificar si el stock está bajo"""
        return self.stock_actual <= self.stock_minimo
    
    @property
    def utilidad_unitaria(self) -> Decimal:
        """Calcular utilidad por unidad"""
        return self.precio_venta - self.precio_compra
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'codigo_interno': self.codigo_interno,
            'codigo_barras': self.codigo_barras,
            'barcode': self.barcode,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'categoria_id': self.categoria_id,
            'categoria_nombre': self.categoria_nombre,
            'marca': self.marca,
            'modelo': self.modelo,
            'precio_compra': float(self.precio_compra),
            'precio_venta': float(self.precio_venta),
            'precio_mayorista': float(self.precio_mayorista) if self.precio_mayorista else None,
            'stock_actual': float(self.stock_actual),
            'stock_minimo': float(self.stock_minimo),
            'stock_maximo': float(self.stock_maximo) if self.stock_maximo else None,
            'unidad_medida': self.unidad_medida,
            'producto_tipo': self.producto_tipo.value,
            'activo': self.activo,
            'stock_bajo': self.stock_bajo,
            'utilidad_unitaria': float(self.utilidad_unitaria),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

@dataclass
class Customer:
    """Modelo de cliente"""
    id: Optional[int] = None
    nombre: str = ""
    apellido: Optional[str] = None
    nombre_completo: Optional[str] = None
    documento_tipo: str = "DNI"
    documento_numero: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    codigo_postal: Optional[str] = None
    
    # Comercial
    tipo_cliente: str = "MINORISTA"  # MINORISTA, MAYORISTA, DISTRIBUIDOR
    descuento_porcentaje: Decimal = field(default_factory=lambda: Decimal('0.00'))
    limite_credito: Decimal = field(default_factory=lambda: Decimal('0.00'))
    saldo_actual: Decimal = field(default_factory=lambda: Decimal('0.00'))
    
    # Estado
    activo: bool = True
    es_vip: bool = False
    
    # Auditoría
    fecha_registro: Optional[date] = None
    ultima_compra: Optional[date] = None
    total_compras: Decimal = field(default_factory=lambda: Decimal('0.00'))
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Completar campos automáticamente"""
        if not self.nombre_completo and self.nombre:
            if self.apellido:
                self.nombre_completo = f"{self.nombre} {self.apellido}"
            else:
                self.nombre_completo = self.nombre
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'nombre_completo': self.nombre_completo,
            'documento_tipo': self.documento_tipo,
            'documento_numero': self.documento_numero,
            'telefono': self.telefono,
            'email': self.email,
            'direccion': self.direccion,
            'ciudad': self.ciudad,
            'tipo_cliente': self.tipo_cliente,
            'descuento_porcentaje': float(self.descuento_porcentaje),
            'limite_credito': float(self.limite_credito),
            'saldo_actual': float(self.saldo_actual),
            'activo': self.activo,
            'es_vip': self.es_vip,
            'total_compras': float(self.total_compras),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

@dataclass
class Sale:
    """Modelo de venta"""
    id: Optional[int] = None
    numero_factura: Optional[str] = None
    fecha_venta: Optional[datetime] = None
    cliente_id: Optional[int] = None
    cliente_nombre: Optional[str] = None
    usuario_id: Optional[int] = None
    usuario_nombre: Optional[str] = None
    
    # Totales
    subtotal: Decimal = field(default_factory=lambda: Decimal('0.00'))
    descuento: Decimal = field(default_factory=lambda: Decimal('0.00'))
    impuestos: Decimal = field(default_factory=lambda: Decimal('0.00'))
    total: Decimal = field(default_factory=lambda: Decimal('0.00'))
    
    # Pago
    metodo_pago: str = "EFECTIVO"
    monto_pagado: Decimal = field(default_factory=lambda: Decimal('0.00'))
    cambio: Decimal = field(default_factory=lambda: Decimal('0.00'))
    
    # Estado
    estado: TransactionStatus = TransactionStatus.COMPLETED
    observaciones: Optional[str] = None
    
    # Items
    items: List['SaleItem'] = field(default_factory=list)
    
    # Auditoría
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def add_item(self, producto_id: int, cantidad: Decimal, precio_unitario: Decimal, 
                 nombre_producto: str = "", descuento_item: Decimal = Decimal('0')):
        """Agregar item a la venta"""
        item = SaleItem(
            producto_id=producto_id,
            nombre_producto=nombre_producto,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            descuento=descuento_item
        )
        self.items.append(item)
        self._recalculate_totals()
    
    def _recalculate_totals(self):
        """Recalcular totales de la venta"""
        self.subtotal = sum(item.total for item in self.items)
        self.total = self.subtotal - self.descuento + self.impuestos
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'numero_factura': self.numero_factura,
            'fecha_venta': self.fecha_venta.isoformat() if self.fecha_venta else None,
            'cliente_id': self.cliente_id,
            'cliente_nombre': self.cliente_nombre,
            'usuario_id': self.usuario_id,
            'usuario_nombre': self.usuario_nombre,
            'subtotal': float(self.subtotal),
            'descuento': float(self.descuento),
            'impuestos': float(self.impuestos),
            'total': float(self.total),
            'metodo_pago': self.metodo_pago,
            'estado': self.estado.value,
            'observaciones': self.observaciones,
            'items': [item.to_dict() for item in self.items],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

@dataclass
class SaleItem:
    """Item de venta"""
    id: Optional[int] = None
    venta_id: Optional[int] = None
    producto_id: int = 0
    nombre_producto: str = ""
    cantidad: Decimal = field(default_factory=lambda: Decimal('1'))
    precio_unitario: Decimal = field(default_factory=lambda: Decimal('0.00'))
    descuento: Decimal = field(default_factory=lambda: Decimal('0.00'))
    
    @property
    def subtotal(self) -> Decimal:
        """Subtotal del item"""
        return self.cantidad * self.precio_unitario
    
    @property
    def total(self) -> Decimal:
        """Total del item con descuento"""
        return self.subtotal - self.descuento
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'venta_id': self.venta_id,
            'producto_id': self.producto_id,
            'nombre_producto': self.nombre_producto,
            'cantidad': float(self.cantidad),
            'precio_unitario': float(self.precio_unitario),
            'descuento': float(self.descuento),
            'subtotal': float(self.subtotal),
            'total': float(self.total)
        }

@dataclass
class Category:
    """Modelo de categoría"""
    id: Optional[int] = None
    nombre: str = ""
    descripcion: Optional[str] = None
    color: str = "#3498db"
    parent_id: Optional[int] = None
    activo: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'color': self.color,
            'parent_id': self.parent_id,
            'activo': self.activo
        }

@dataclass
class Provider:
    """Modelo de proveedor"""
    id: Optional[int] = None
    nombre: str = ""
    razon_social: Optional[str] = None
    cuit: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    contacto_nombre: Optional[str] = None
    activo: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'razon_social': self.razon_social,
            'cuit': self.cuit,
            'telefono': self.telefono,
            'email': self.email,
            'direccion': self.direccion,
            'contacto_nombre': self.contacto_nombre,
            'activo': self.activo
        }

@dataclass
class SystemLog:
    """Modelo de log del sistema"""
    id: Optional[int] = None
    timestamp: Optional[datetime] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    action: str = ""
    table_name: Optional[str] = None
    record_id: Optional[int] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'user_id': self.user_id,
            'username': self.username,
            'action': self.action,
            'table_name': self.table_name,
            'record_id': self.record_id,
            'old_values': json.dumps(self.old_values) if self.old_values else None,
            'new_values': json.dumps(self.new_values) if self.new_values else None,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'success': self.success,
            'error_message': self.error_message
        }

# Funciones de utilidad para conversión de datos
def row_to_user(row) -> User:
    """Convertir fila de base de datos a User"""
    if not row:
        return None
    
    return User(
        id=row.get('id'),
        username=row.get('username', ''),
        email=row.get('email'),
        nombre_completo=row.get('nombre_completo', ''),
        telefono=row.get('telefono'),
        rol_id=row.get('rol_id'),
        rol_nombre=row.get('rol_nombre'),
        numero_documento=row.get('numero_documento'),
        activo=bool(row.get('activo', True)),
        ultimo_acceso=row.get('ultimo_acceso'),
        intentos_fallidos=row.get('intentos_fallidos', 0),
        permisos=row.get('permisos', []) if isinstance(row.get('permisos', []), list) else row.get('permisos', '').split(',') if row.get('permisos') else []
    )

def row_to_product(row) -> Product:
    """Convertir fila de base de datos a Product"""
    if not row:
        return None
    
    return Product(
        id=row.get('id'),
        codigo_interno=row.get('codigo_interno'),
        codigo_barras=row.get('codigo_barras') or row.get('barcode'),
        barcode=row.get('barcode') or row.get('codigo_barras'),
        nombre=row.get('nombre', ''),
        descripcion=row.get('descripcion'),
        categoria_id=row.get('categoria_id'),
        categoria_nombre=row.get('categoria_nombre'),
        marca=row.get('marca'),
        precio_compra=Decimal(str(row.get('precio_compra', 0))),
        precio_venta=Decimal(str(row.get('precio_venta', 0))),
        stock_actual=Decimal(str(row.get('stock_actual', 0))),
        stock_minimo=Decimal(str(row.get('stock_minimo', 0))),
        activo=bool(row.get('activo', True)),
        created_at=row.get('created_at')
    )

def row_to_customer(row) -> Customer:
    """Convertir fila de base de datos a Customer"""
    if not row:
        return None
    
    return Customer(
        id=row.get('id'),
        nombre=row.get('nombre', ''),
        apellido=row.get('apellido'),
        nombre_completo=row.get('nombre_completo'),
        documento_tipo=row.get('documento_tipo', 'DNI'),
        documento_numero=row.get('documento_numero'),
        telefono=row.get('telefono'),
        email=row.get('email'),
        direccion=row.get('direccion'),
        activo=bool(row.get('activo', True)),
        created_at=row.get('created_at')
    )