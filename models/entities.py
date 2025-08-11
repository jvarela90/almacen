"""
Entidades del Dominio - AlmacénPro v2.0 MVC
Definición de todas las entidades de negocio
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
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