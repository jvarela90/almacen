"""
Modelo de Ventas - AlmacénPro v2.0 MVC
Modelo que gestiona el estado y lógica de datos para ventas
"""

from PyQt5.QtCore import pyqtSignal
from typing import List, Dict, Optional
from decimal import Decimal
from datetime import datetime
import json
import logging

from .base_model import BaseModel
from .entities import Sale, SaleItem, Product, Customer

logger = logging.getLogger(__name__)

class SalesModel(BaseModel):
    """Modelo de datos para el sistema de ventas"""
    
    # Señales específicas para ventas
    cart_updated = pyqtSignal()
    customer_changed = pyqtSignal(dict)
    totals_changed = pyqtSignal()
    item_added = pyqtSignal(dict)
    item_removed = pyqtSignal(int)
    
    def __init__(self, sales_manager=None, product_manager=None, customer_manager=None, parent=None):
        super().__init__(parent)
        self.sales_manager = sales_manager
        self.product_manager = product_manager
        self.customer_manager = customer_manager
        
        # Estado del carrito
        self._cart_items = []
        self._current_customer = None
        self._current_sale = Sale()
        
        # Configuración de impuestos y descuentos
        self._tax_rate = 0.16  # 16% IVA
        self._discount_rate = 0.0
        
        # Totales calculados
        self._subtotal = Decimal('0.00')
        self._tax_amount = Decimal('0.00')
        self._discount_amount = Decimal('0.00')
        self._total = Decimal('0.00')
        
        # Configuración del modelo
        self.auto_calculate_totals = True
    
    # === PROPIEDADES ===
    
    @property
    def cart_items(self) -> List[Dict]:
        """Obtener items del carrito"""
        return self._cart_items.copy()
    
    @property
    def current_customer(self) -> Optional[Customer]:
        """Obtener cliente actual"""
        return self._current_customer
    
    @property
    def current_sale(self) -> Sale:
        """Obtener venta actual"""
        return self._current_sale
    
    @property
    def tax_rate(self) -> float:
        """Obtener tasa de impuestos"""
        return self._tax_rate
    
    @property
    def discount_rate(self) -> float:
        """Obtener tasa de descuento"""
        return self._discount_rate
    
    def get_subtotal(self) -> float:
        """Obtener subtotal"""
        return float(self._subtotal)
    
    def get_tax_amount(self) -> float:
        """Obtener monto de impuestos"""
        return float(self._tax_amount)
    
    def get_discount_amount(self) -> float:
        """Obtener monto de descuento"""
        return float(self._discount_amount)
    
    def get_total(self) -> float:
        """Obtener total final"""
        return float(self._total)
    
    # === MÉTODOS PÚBLICOS ===
    
    def add_item_to_cart(self, item_data: Dict) -> bool:
        """Agregar item al carrito"""
        try:
            # Validar datos del item
            if not self._validate_cart_item(item_data):
                self._set_error("Datos del item inválidos")
                return False
            
            # Verificar si el producto ya está en el carrito
            existing_index = self._find_item_in_cart(item_data.get('code'))
            
            if existing_index is not None:
                # Actualizar cantidad del item existente
                existing_item = self._cart_items[existing_index]
                new_quantity = existing_item['quantity'] + item_data['quantity']
                existing_item['quantity'] = new_quantity
                existing_item['subtotal'] = existing_item['price'] * new_quantity
                
                self.logger.debug(f"Cantidad actualizada: {item_data['name']} x{new_quantity}")
            else:
                # Agregar nuevo item
                cart_item = {
                    'code': item_data['code'],
                    'name': item_data['name'],
                    'price': Decimal(str(item_data['price'])),
                    'quantity': item_data['quantity'],
                    'subtotal': Decimal(str(item_data['price'])) * item_data['quantity'],
                    'product_id': item_data.get('product_id'),
                    'category': item_data.get('category', ''),
                    'description': item_data.get('description', '')
                }
                self._cart_items.append(cart_item)
                
                self.logger.debug(f"Nuevo item agregado: {item_data['name']} x{item_data['quantity']}")
            
            # Recalcular totales y emitir señales
            self._calculate_totals()
            self.cart_updated.emit()
            self.item_added.emit(item_data)
            self.data_changed.emit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error agregando item al carrito: {e}")
            self._set_error(f"Error agregando producto: {str(e)}")
            return False
    
    def remove_item_from_cart(self, index: int) -> bool:
        """Eliminar item del carrito por índice"""
        try:
            if 0 <= index < len(self._cart_items):
                removed_item = self._cart_items.pop(index)
                
                # Recalcular totales
                self._calculate_totals()
                
                # Emitir señales
                self.cart_updated.emit()
                self.item_removed.emit(index)
                self.data_changed.emit()
                
                self.logger.debug(f"Item eliminado del carrito: {removed_item['name']}")
                return True
            
            self._set_error("Índice de item inválido")
            return False
            
        except Exception as e:
            self.logger.error(f"Error eliminando item del carrito: {e}")
            self._set_error(f"Error eliminando producto: {str(e)}")
            return False
    
    def update_item_quantity(self, index: int, new_quantity: int) -> bool:
        """Actualizar cantidad de un item"""
        try:
            if 0 <= index < len(self._cart_items) and new_quantity > 0:
                item = self._cart_items[index]
                old_quantity = item['quantity']
                
                item['quantity'] = new_quantity
                item['subtotal'] = item['price'] * new_quantity
                
                # Recalcular totales
                self._calculate_totals()
                
                # Emitir señales
                self.cart_updated.emit()
                self.data_changed.emit()
                
                self.logger.debug(f"Cantidad actualizada: {item['name']} {old_quantity} -> {new_quantity}")
                return True
            
            self._set_error("Índice inválido o cantidad menor a 1")
            return False
            
        except Exception as e:
            self.logger.error(f"Error actualizando cantidad: {e}")
            self._set_error(f"Error actualizando cantidad: {str(e)}")
            return False
    
    def clear_cart(self):
        """Limpiar carrito completo"""
        self._cart_items.clear()
        self._calculate_totals()
        
        # Emitir señales
        self.cart_updated.emit()
        self.data_changed.emit()
        
        self.logger.debug("Carrito limpiado")
    
    def set_customer(self, customer: Optional[Customer]):
        """Establecer cliente actual"""
        self._current_customer = customer
        
        # Actualizar venta actual
        if customer:
            self._current_sale.cliente_id = customer.id
            self._current_sale.cliente_nombre = customer.nombre
            
            # Aplicar descuento del cliente si tiene
            if customer.descuento_porcentual > 0:
                self.set_discount_rate(customer.descuento_porcentual / 100.0)
        else:
            self._current_sale.cliente_id = None
            self._current_sale.cliente_nombre = "Cliente General"
            self.set_discount_rate(0.0)
        
        # Emitir señal
        if customer:
            self.customer_changed.emit(customer.to_dict())
        
        self.logger.debug(f"Cliente establecido: {customer.nombre if customer else 'Cliente General'}")
    
    def set_discount_rate(self, discount_rate: float):
        """Establecer tasa de descuento"""
        self._discount_rate = max(0.0, min(1.0, discount_rate))  # Entre 0 y 100%
        self._calculate_totals()
        
        # Emitir señal
        self.data_changed.emit()
        self.logger.debug(f"Tasa de descuento establecida: {self._discount_rate:.1%}")
    
    def apply_discount_amount(self, discount_amount: float):
        """Aplicar descuento por monto fijo"""
        if discount_amount >= 0 and discount_amount <= float(self._subtotal):
            self._discount_amount = Decimal(str(discount_amount))
            self._discount_rate = 0.0  # Resetear tasa porcentual
            self._calculate_totals()
            
            # Emitir señal
            self.data_changed.emit()
            self.logger.debug(f"Descuento fijo aplicado: ${discount_amount}")
            return True
        
        self._set_error("Monto de descuento inválido")
        return False
    
    def set_tax_rate(self, tax_rate: float):
        """Establecer tasa de impuestos"""
        self._tax_rate = max(0.0, min(1.0, tax_rate))
        self._calculate_totals()
        
        # Emitir señal
        self.data_changed.emit()
        self.logger.debug(f"Tasa de impuestos establecida: {self._tax_rate:.1%}")
    
    # === MÉTODOS DE CONSULTA ===
    
    def has_items(self) -> bool:
        """Verificar si el carrito tiene items"""
        return len(self._cart_items) > 0
    
    def get_cart_items(self) -> List[Dict]:
        """Obtener copia de los items del carrito"""
        return [item.copy() for item in self._cart_items]
    
    def get_item_count(self) -> int:
        """Obtener número total de items en el carrito"""
        return sum(item['quantity'] for item in self._cart_items)
    
    def get_unique_products_count(self) -> int:
        """Obtener número de productos únicos en el carrito"""
        return len(self._cart_items)
    
    def find_item_by_code(self, product_code: str) -> Optional[Dict]:
        """Buscar item en carrito por código de producto"""
        for item in self._cart_items:
            if item.get('code') == product_code:
                return item.copy()
        return None
    
    def get_sale_summary(self) -> Dict:
        """Obtener resumen de la venta"""
        return {
            'customer': self._current_customer.to_dict() if self._current_customer else None,
            'items_count': self.get_item_count(),
            'unique_products': self.get_unique_products_count(),
            'subtotal': self.get_subtotal(),
            'discount_amount': self.get_discount_amount(),
            'tax_amount': self.get_tax_amount(),
            'total': self.get_total(),
            'items': self.get_cart_items()
        }
    
    # === MÉTODOS DE PERSISTENCIA ===
    
    def save_cart(self, name: str) -> bool:
        """Guardar carrito actual"""
        try:
            cart_data = {
                'name': name,
                'timestamp': datetime.now().isoformat(),
                'customer': self._current_customer.to_dict() if self._current_customer else None,
                'items': self.get_cart_items(),
                'discount_rate': self._discount_rate,
                'tax_rate': self._tax_rate,
                'totals': {
                    'subtotal': self.get_subtotal(),
                    'discount': self.get_discount_amount(),
                    'tax': self.get_tax_amount(),
                    'total': self.get_total()
                }
            }
            
            # Aquí implementarías la lógica de guardado
            # Por ahora, solo simular guardado exitoso
            
            self.logger.info(f"Carrito guardado: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error guardando carrito: {e}")
            self._set_error(f"Error guardando carrito: {str(e)}")
            return False
    
    def load_cart(self, cart_data: Dict) -> bool:
        """Cargar carrito desde datos"""
        try:
            self._cart_items.clear()
            
            # Cargar items
            items = cart_data.get('items', [])
            for item_data in items:
                self._cart_items.append({
                    'code': item_data.get('code', ''),
                    'name': item_data.get('name', ''),
                    'price': Decimal(str(item_data.get('price', 0))),
                    'quantity': item_data.get('quantity', 1),
                    'subtotal': Decimal(str(item_data.get('subtotal', 0))),
                    'product_id': item_data.get('product_id'),
                    'category': item_data.get('category', ''),
                    'description': item_data.get('description', '')
                })
            
            # Cargar configuración
            self._discount_rate = cart_data.get('discount_rate', 0.0)
            self._tax_rate = cart_data.get('tax_rate', 0.16)
            
            # Cargar cliente si existe
            customer_data = cart_data.get('customer')
            if customer_data:
                self._current_customer = Customer.from_dict(customer_data)
                self.customer_changed.emit(customer_data)
            
            # Recalcular totales
            self._calculate_totals()
            
            # Emitir señales
            self.cart_updated.emit()
            self.data_changed.emit()
            
            self.logger.info("Carrito cargado exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cargando carrito: {e}")
            self._set_error(f"Error cargando carrito: {str(e)}")
            return False
    
    def auto_save_cart(self):
        """Auto-guardar carrito"""
        if self.has_items():
            auto_save_name = f"auto_save_{datetime.now().strftime('%Y%m%d_%H%M')}"
            self.save_cart(auto_save_name)
    
    def prepare_sale_data(self) -> Dict:
        """Preparar datos para procesar la venta"""
        return {
            'customer_id': self._current_customer.id if self._current_customer else None,
            'customer_name': self._current_customer.nombre if self._current_customer else "Cliente General",
            'items': self.get_cart_items(),
            'subtotal': self.get_subtotal(),
            'discount_amount': self.get_discount_amount(),
            'tax_amount': self.get_tax_amount(),
            'total': self.get_total(),
            'tax_rate': self._tax_rate,
            'discount_rate': self._discount_rate,
            'timestamp': datetime.now()
        }
    
    # === MÉTODOS PROTEGIDOS ===
    
    def _calculate_totals(self):
        """Calcular totales basado en items del carrito"""
        try:
            # Calcular subtotal
            self._subtotal = sum(Decimal(str(item['subtotal'])) for item in self._cart_items)
            
            # Calcular descuento
            if self._discount_rate > 0:
                self._discount_amount = self._subtotal * Decimal(str(self._discount_rate))
            # Si hay descuento fijo, mantenerlo
            
            # Calcular impuestos sobre (subtotal - descuento)
            taxable_amount = self._subtotal - self._discount_amount
            self._tax_amount = taxable_amount * Decimal(str(self._tax_rate))
            
            # Calcular total
            self._total = self._subtotal - self._discount_amount + self._tax_amount
            
            # Asegurar que no haya valores negativos
            self._total = max(self._total, Decimal('0.00'))
            
            # Emitir señal de cambio en totales
            if self.auto_calculate_totals:
                self.totals_changed.emit()
            
        except Exception as e:
            self.logger.error(f"Error calculando totales: {e}")
            self._set_error(f"Error en cálculo de totales: {str(e)}")
    
    def _validate_cart_item(self, item_data: Dict) -> bool:
        """Validar datos de item antes de agregar al carrito"""
        required_fields = ['code', 'name', 'price', 'quantity']
        
        for field in required_fields:
            if field not in item_data:
                self.logger.warning(f"Campo requerido faltante en item: {field}")
                return False
        
        # Validar tipos y valores
        try:
            price = float(item_data['price'])
            quantity = int(item_data['quantity'])
            
            if price < 0:
                self.logger.warning("Precio no puede ser negativo")
                return False
                
            if quantity <= 0:
                self.logger.warning("Cantidad debe ser mayor a 0")
                return False
                
        except (ValueError, TypeError):
            self.logger.warning("Error de tipo en precio o cantidad")
            return False
        
        return True
    
    def _find_item_in_cart(self, product_code: str) -> Optional[int]:
        """Encontrar índice de item en carrito por código de producto"""
        for index, item in enumerate(self._cart_items):
            if item['code'] == product_code:
                return index
        return None
    
    def _get_default_values(self) -> Dict:
        """Obtener valores por defecto del modelo"""
        return {
            'cart_items': [],
            'current_customer': None,
            'tax_rate': 0.16,
            'discount_rate': 0.0
        }
    
    def reset_to_defaults(self):
        """Resetear modelo a valores por defecto"""
        self.clear_cart()
        self._current_customer = None
        self._tax_rate = 0.16
        self._discount_rate = 0.0
        self._discount_amount = Decimal('0.00')
        
        self._calculate_totals()
        
        # Emitir señales
        self.customer_changed.emit({})
        self.cart_updated.emit()
        self.data_changed.emit()
        
        self.logger.debug("Modelo de ventas reseteado a defaults")