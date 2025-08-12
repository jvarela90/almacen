"""
Entidades del Dominio - AlmacénPro v2.0 MVC
Definición de todas las entidades de negocio
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from dataclasses import dataclass, asdict, field
from decimal import Decimal
import json

@dataclass
class Product:
    """Entidad Producto"""
    id: Optional[int] = None
    codigo: str = ""
    nombre: str = ""
    descripcion: str = ""
    precio: float = 0.0
    costo: float = 0.0
    stock_actual: int = 0
    stock_minimo: int = 0
    stock_maximo: int = 0
    categoria_id: Optional[int] = None
    categoria_nombre: str = ""
    proveedor_id: Optional[int] = None
    unidad_medida: str = "UNIDAD"
    codigo_barras: str = ""
    imagen: str = ""
    activo: bool = True
    gravable: bool = True
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Product':
        """Crear desde diccionario"""
        return cls(**data)
    
    @property
    def margen_ganancia(self) -> float:
        """Calcular margen de ganancia"""
        if self.costo > 0:
            return ((self.precio - self.costo) / self.costo) * 100
        return 0.0
    
    @property
    def valor_stock(self) -> float:
        """Calcular valor del stock actual"""
        return self.stock_actual * self.costo
    
    @property
    def necesita_reposicion(self) -> bool:
        """Verificar si necesita reposición"""
        return self.stock_actual <= self.stock_minimo
    
    def __str__(self) -> str:
        return f"{self.codigo} - {self.nombre}"

@dataclass
class Customer:
    """Entidad Cliente"""
    id: Optional[int] = None
    codigo: str = ""
    nombre: str = ""
    email: str = ""
    telefono: str = ""
    direccion: str = ""
    ciudad: str = ""
    documento: str = ""
    tipo_documento: str = "DNI"
    tipo_cliente: str = "MINORISTA"  # MINORISTA, MAYORISTA, DISTRIBUIDOR
    limite_credito: float = 0.0
    saldo_actual: float = 0.0
    descuento_porcentual: float = 0.0
    activo: bool = True
    fecha_nacimiento: Optional[datetime] = None
    ultima_compra: Optional[datetime] = None
    total_compras: float = 0.0
    numero_compras: int = 0
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None
    
    # Campos CRM avanzado
    origen: str = "DIRECTO"  # DIRECTO, REFERIDO, MARKETING, WEB
    segmento: str = "REGULAR"  # REGULAR, VIP, PREMIUM
    estado: str = "ACTIVO"  # ACTIVO, INACTIVO, POTENCIAL, PERDIDO
    observaciones: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Customer':
        """Crear desde diccionario"""
        return cls(**data)
    
    @property
    def credito_disponible(self) -> float:
        """Calcular crédito disponible"""
        return max(0, self.limite_credito - self.saldo_actual)
    
    @property
    def promedio_compra(self) -> float:
        """Calcular promedio de compra"""
        if self.numero_compras > 0:
            return self.total_compras / self.numero_compras
        return 0.0
    
    @property
    def dias_desde_ultima_compra(self) -> int:
        """Días desde última compra"""
        if self.ultima_compra:
            delta = datetime.now() - self.ultima_compra
            return delta.days
        return 999
    
    def __str__(self) -> str:
        return f"{self.codigo} - {self.nombre}"

@dataclass
class Sale:
    """Entidad Venta"""
    id: Optional[int] = None
    numero: str = ""
    cliente_id: Optional[int] = None
    cliente_nombre: str = ""
    usuario_id: int = 0
    usuario_nombre: str = ""
    fecha_venta: Optional[datetime] = None
    subtotal: float = 0.0
    descuento: float = 0.0
    impuestos: float = 0.0
    total: float = 0.0
    estado: str = "PENDIENTE"  # PENDIENTE, COMPLETADA, CANCELADA, DEVUELTA
    tipo_venta: str = "CONTADO"  # CONTADO, CREDITO
    metodo_pago: str = "EFECTIVO"
    observaciones: str = ""
    facturada: bool = False
    numero_factura: str = ""
    items: List['SaleItem'] = None
    
    def __post_init__(self):
        if self.items is None:
            self.items = []
        if self.fecha_venta is None:
            self.fecha_venta = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        data = asdict(self)
        data['items'] = [item.to_dict() for item in self.items]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Sale':
        """Crear desde diccionario"""
        items_data = data.pop('items', [])
        sale = cls(**data)
        sale.items = [SaleItem.from_dict(item) for item in items_data]
        return sale
    
    @property
    def total_items(self) -> int:
        """Total de items en la venta"""
        return sum(item.cantidad for item in self.items)
    
    @property
    def total_productos(self) -> int:
        """Total de productos diferentes"""
        return len(self.items)
    
    def add_item(self, item: 'SaleItem'):
        """Agregar item a la venta"""
        # Verificar si ya existe el producto
        for existing_item in self.items:
            if existing_item.producto_id == item.producto_id:
                existing_item.cantidad += item.cantidad
                existing_item.subtotal = existing_item.precio_unitario * existing_item.cantidad
                self._recalculate_totals()
                return
        
        # Agregar nuevo item
        self.items.append(item)
        self._recalculate_totals()
    
    def remove_item(self, producto_id: int):
        """Eliminar item de la venta"""
        self.items = [item for item in self.items if item.producto_id != producto_id]
        self._recalculate_totals()
    
    def _recalculate_totals(self):
        """Recalcular totales"""
        self.subtotal = sum(item.subtotal for item in self.items)
        self.total = self.subtotal - self.descuento + self.impuestos
    
    def __str__(self) -> str:
        return f"Venta #{self.numero} - ${self.total:,.2f}"

@dataclass
class SaleItem:
    """Entidad Item de Venta"""
    id: Optional[int] = None
    venta_id: Optional[int] = None
    producto_id: int = 0
    producto_codigo: str = ""
    producto_nombre: str = ""
    cantidad: int = 1
    precio_unitario: float = 0.0
    descuento_porcentaje: float = 0.0
    descuento_monto: float = 0.0
    subtotal: float = 0.0
    
    def __post_init__(self):
        if self.subtotal == 0.0:
            self.calculate_subtotal()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SaleItem':
        """Crear desde diccionario"""
        return cls(**data)
    
    def calculate_subtotal(self):
        """Calcular subtotal del item"""
        base = self.precio_unitario * self.cantidad
        discount = base * (self.descuento_porcentaje / 100) if self.descuento_porcentaje > 0 else self.descuento_monto
        self.subtotal = base - discount
    
    def apply_discount_percentage(self, percentage: float):
        """Aplicar descuento porcentual"""
        self.descuento_porcentaje = percentage
        self.descuento_monto = 0.0
        self.calculate_subtotal()
    
    def apply_discount_amount(self, amount: float):
        """Aplicar descuento por monto fijo"""
        self.descuento_monto = amount
        self.descuento_porcentaje = 0.0
        self.calculate_subtotal()
    
    def __str__(self) -> str:
        return f"{self.producto_nombre} x{self.cantidad} = ${self.subtotal:,.2f}"

@dataclass
class User:
    """Entidad Usuario"""
    id: Optional[int] = None
    username: str = ""
    password_hash: str = ""
    email: str = ""
    nombre_completo: str = ""
    telefono: str = ""
    rol_id: Optional[int] = None
    rol_nombre: str = ""
    activo: bool = True
    ultimo_acceso: Optional[datetime] = None
    intentos_fallidos: int = 0
    bloqueado_hasta: Optional[datetime] = None
    configuracion: str = "{}"  # JSON con configuraciones personales
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario (sin password_hash)"""
        data = asdict(self)
        data.pop('password_hash', None)  # No exponer hash de contraseña
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Crear desde diccionario"""
        return cls(**data)
    
    @property
    def is_blocked(self) -> bool:
        """Verificar si el usuario está bloqueado"""
        if self.bloqueado_hasta:
            return datetime.now() < self.bloqueado_hasta
        return False
    
    @property
    def config_dict(self) -> Dict[str, Any]:
        """Obtener configuración como diccionario"""
        try:
            return json.loads(self.configuracion) if self.configuracion else {}
        except json.JSONDecodeError:
            return {}
    
    def set_config(self, config: Dict[str, Any]):
        """Establecer configuración"""
        self.configuracion = json.dumps(config, default=str, ensure_ascii=False)
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Obtener valor de configuración"""
        return self.config_dict.get(key, default)
    
    def __str__(self) -> str:
        return f"{self.username} - {self.nombre_completo}"

@dataclass
class Category:
    """Entidad Categoría"""
    id: Optional[int] = None
    nombre: str = ""
    descripcion: str = ""
    categoria_padre_id: Optional[int] = None
    activo: bool = True
    orden: int = 0
    imagen: str = ""
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Category':
        """Crear desde diccionario"""
        return cls(**data)
    
    def __str__(self) -> str:
        return self.nombre

@dataclass
class Provider:
    """Entidad Proveedor"""
    id: Optional[int] = None
    codigo: str = ""
    nombre: str = ""
    contacto: str = ""
    email: str = ""
    telefono: str = ""
    direccion: str = ""
    ciudad: str = ""
    documento: str = ""
    tipo_documento: str = "RUT"
    activo: bool = True
    observaciones: str = ""
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Provider':
        """Crear desde diccionario"""
        return cls(**data)
    
    def __str__(self) -> str:
        return f"{self.codigo} - {self.nombre}"

@dataclass
class Purchase:
    """Entidad Compra"""
    id: Optional[int] = None
    numero: str = ""
    proveedor_id: Optional[int] = None
    proveedor_nombre: str = ""
    usuario_id: int = 0
    usuario_nombre: str = ""
    fecha_compra: Optional[datetime] = None
    fecha_entrega: Optional[datetime] = None
    subtotal: float = 0.0
    descuento: float = 0.0
    impuestos: float = 0.0
    total: float = 0.0
    estado: str = "PENDIENTE"  # PENDIENTE, RECIBIDA, CANCELADA
    tipo_compra: str = "CONTADO"  # CONTADO, CREDITO
    observaciones: str = ""
    numero_factura: str = ""
    items: List['PurchaseItem'] = None
    
    def __post_init__(self):
        if self.items is None:
            self.items = []
        if self.fecha_compra is None:
            self.fecha_compra = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        data = asdict(self)
        data['items'] = [item.to_dict() for item in self.items]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Purchase':
        """Crear desde diccionario"""
        items_data = data.pop('items', [])
        purchase = cls(**data)
        purchase.items = [PurchaseItem.from_dict(item) for item in items_data]
        return purchase
    
    @property
    def total_items(self) -> int:
        """Total de items en la compra"""
        return sum(item.cantidad for item in self.items)
    
    def add_item(self, item: 'PurchaseItem'):
        """Agregar item a la compra"""
        for existing_item in self.items:
            if existing_item.producto_id == item.producto_id:
                existing_item.cantidad += item.cantidad
                existing_item.subtotal = existing_item.precio_unitario * existing_item.cantidad
                self._recalculate_totals()
                return
        
        self.items.append(item)
        self._recalculate_totals()
    
    def _recalculate_totals(self):
        """Recalcular totales"""
        self.subtotal = sum(item.subtotal for item in self.items)
        self.total = self.subtotal - self.descuento + self.impuestos
    
    def __str__(self) -> str:
        return f"Compra #{self.numero} - ${self.total:,.2f}"

@dataclass
class PurchaseItem:
    """Entidad Item de Compra"""
    id: Optional[int] = None
    compra_id: Optional[int] = None
    producto_id: int = 0
    producto_codigo: str = ""
    producto_nombre: str = ""
    cantidad: int = 1
    precio_unitario: float = 0.0
    descuento_porcentaje: float = 0.0
    descuento_monto: float = 0.0
    subtotal: float = 0.0
    
    def __post_init__(self):
        if self.subtotal == 0.0:
            self.calculate_subtotal()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PurchaseItem':
        """Crear desde diccionario"""
        return cls(**data)
    
    def calculate_subtotal(self):
        """Calcular subtotal del item"""
        base = self.precio_unitario * self.cantidad
        discount = base * (self.descuento_porcentaje / 100) if self.descuento_porcentaje > 0 else self.descuento_monto
        self.subtotal = base - discount
    
    def __str__(self) -> str:
        return f"{self.producto_nombre} x{self.cantidad} = ${self.subtotal:,.2f}"

@dataclass
class InventoryMovement:
    """Entidad Movimiento de Inventario"""
    id: Optional[int] = None
    producto_id: int = 0
    producto_nombre: str = ""
    tipo_movimiento: str = "ENTRADA"  # ENTRADA, SALIDA, AJUSTE
    cantidad: int = 0
    cantidad_anterior: int = 0
    cantidad_nueva: int = 0
    precio_costo: float = 0.0
    motivo: str = ""
    referencia_id: Optional[int] = None  # ID de venta, compra, etc.
    referencia_tipo: str = ""  # venta, compra, ajuste
    usuario_id: int = 0
    usuario_nombre: str = ""
    fecha_movimiento: Optional[datetime] = None
    observaciones: str = ""
    
    def __post_init__(self):
        if self.fecha_movimiento is None:
            self.fecha_movimiento = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InventoryMovement':
        """Crear desde diccionario"""
        return cls(**data)
    
    @property
    def valor_movimiento(self) -> float:
        """Calcular valor del movimiento"""
        return abs(self.cantidad) * self.precio_costo
    
    def __str__(self) -> str:
        return f"{self.tipo_movimiento} - {self.producto_nombre} ({self.cantidad})"

@dataclass
class FinancialTransaction:
    """Entidad Transacción Financiera"""
    id: Optional[int] = None
    tipo: str = "INGRESO"  # INGRESO, EGRESO
    concepto: str = ""
    monto: float = 0.0
    metodo_pago: str = "EFECTIVO"
    referencia_id: Optional[int] = None
    referencia_tipo: str = ""  # venta, compra, gasto
    usuario_id: int = 0
    usuario_nombre: str = ""
    fecha_transaccion: Optional[datetime] = None
    caja_id: Optional[int] = None
    estado: str = "ACTIVA"  # ACTIVA, ANULADA
    observaciones: str = ""
    
    def __post_init__(self):
        if self.fecha_transaccion is None:
            self.fecha_transaccion = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FinancialTransaction':
        """Crear desde diccionario"""
        return cls(**data)
    
    @property
    def monto_con_signo(self) -> float:
        """Monto con signo según tipo"""
        return self.monto if self.tipo == "INGRESO" else -self.monto
    
    def __str__(self) -> str:
        return f"{self.tipo} - {self.concepto}: ${self.monto:,.2f}"

@dataclass
class Role:
    """Entidad Rol de Usuario"""
    id: Optional[int] = None
    nombre: str = ""
    descripcion: str = ""
    permisos: str = "{}"  # JSON con permisos específicos
    activo: bool = True
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Role':
        """Crear desde diccionario"""
        return cls(**data)
    
    @property
    def permisos_dict(self) -> Dict[str, Any]:
        """Obtener permisos como diccionario"""
        try:
            return json.loads(self.permisos) if self.permisos else {}
        except json.JSONDecodeError:
            return {}
    
    def set_permisos(self, permisos: Dict[str, Any]):
        """Establecer permisos"""
        self.permisos = json.dumps(permisos, default=str, ensure_ascii=False)
    
    def has_permission(self, permission: str) -> bool:
        """Verificar si tiene un permiso específico"""
        return self.permisos_dict.get(permission, False)
    
    def __str__(self) -> str:
        return self.nombre

@dataclass
class Report:
    """Entidad Reporte"""
    id: Optional[int] = None
    nombre: str = ""
    tipo: str = "VENTAS"  # VENTAS, COMPRAS, INVENTARIO, FINANCIERO
    parametros: str = "{}"  # JSON con parámetros del reporte
    fecha_desde: Optional[datetime] = None
    fecha_hasta: Optional[datetime] = None
    usuario_id: int = 0
    usuario_nombre: str = ""
    fecha_generacion: Optional[datetime] = None
    archivo_path: str = ""
    formato: str = "PDF"  # PDF, EXCEL, CSV
    estado: str = "GENERADO"  # GENERANDO, GENERADO, ERROR
    
    def __post_init__(self):
        if self.fecha_generacion is None:
            self.fecha_generacion = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Report':
        """Crear desde diccionario"""
        return cls(**data)
    
    @property
    def parametros_dict(self) -> Dict[str, Any]:
        """Obtener parámetros como diccionario"""
        try:
            return json.loads(self.parametros) if self.parametros else {}
        except json.JSONDecodeError:
            return {}
    
    def set_parametros(self, parametros: Dict[str, Any]):
        """Establecer parámetros"""
        self.parametros = json.dumps(parametros, default=str, ensure_ascii=False)
    
    def __str__(self) -> str:
        return f"{self.nombre} ({self.tipo})"

@dataclass
class CashRegister:
    """Entidad Caja Registradora"""
    id: Optional[int] = None
    nombre: str = ""
    usuario_id: int = 0
    usuario_nombre: str = ""
    fecha_apertura: Optional[datetime] = None
    fecha_cierre: Optional[datetime] = None
    monto_inicial: float = 0.0
    monto_ventas: float = 0.0
    monto_egresos: float = 0.0
    monto_final: float = 0.0
    monto_esperado: float = 0.0
    diferencia: float = 0.0
    estado: str = "ABIERTA"  # ABIERTA, CERRADA
    observaciones: str = ""
    
    def __post_init__(self):
        if self.fecha_apertura is None:
            self.fecha_apertura = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CashRegister':
        """Crear desde diccionario"""
        return cls(**data)
    
    def calculate_final_amount(self):
        """Calcular monto final esperado"""
        self.monto_esperado = self.monto_inicial + self.monto_ventas - self.monto_egresos
        self.diferencia = self.monto_final - self.monto_esperado
    
    def close_register(self, monto_final: float):
        """Cerrar caja"""
        self.monto_final = monto_final
        self.fecha_cierre = datetime.now()
        self.estado = "CERRADA"
        self.calculate_final_amount()
    
    def __str__(self) -> str:
        return f"Caja {self.nombre} - {self.estado}"

# === FUNCIONES DE UTILIDAD ===

def entity_to_dict(entity) -> Dict[str, Any]:
    """Convertir cualquier entidad a diccionario"""
    if hasattr(entity, 'to_dict'):
        return entity.to_dict()
    elif hasattr(entity, '__dict__'):
        return {k: v for k, v in entity.__dict__.items() if not k.startswith('_')}
    else:
        return {}

def dict_to_entity(entity_class, data: Dict[str, Any]):
    """Convertir diccionario a entidad específica"""
    if hasattr(entity_class, 'from_dict'):
        return entity_class.from_dict(data)
    else:
        return entity_class(**data)

# === UTILIDADES DE VALIDACIÓN ===

def validate_entity(entity) -> List[str]:
    """Validar entidad y retornar lista de errores"""
    errors = []
    
    # Validaciones básicas comunes
    if hasattr(entity, 'nombre') and not entity.nombre.strip():
        errors.append("El nombre es obligatorio")
    
    if hasattr(entity, 'email') and entity.email and '@' not in entity.email:
        errors.append("Email inválido")
    
    if hasattr(entity, 'precio') and entity.precio < 0:
        errors.append("El precio no puede ser negativo")
    
    if hasattr(entity, 'stock_actual') and entity.stock_actual < 0:
        errors.append("El stock no puede ser negativo")
    
    return errors

# === MAPEO DE ENTIDADES ===

ENTITY_CLASSES = {
    'product': Product,
    'customer': Customer,
    'sale': Sale,
    'sale_item': SaleItem,
    'user': User,
    'category': Category,
    'provider': Provider,
    'purchase': Purchase,
    'purchase_item': PurchaseItem,
    'inventory_movement': InventoryMovement,
    'financial_transaction': FinancialTransaction,
    'role': Role,
    'report': Report,
    'cash_register': CashRegister
}

def get_entity_class(entity_type: str):
    """Obtener clase de entidad por tipo"""
    return ENTITY_CLASSES.get(entity_type.lower())

def create_entity(entity_type: str, data: Dict[str, Any]):
    """Crear entidad desde tipo y datos"""
    entity_class = get_entity_class(entity_type)
    if entity_class:
        return entity_class.from_dict(data)
    return None