"""
Modelo de Inventario - AlmacénPro v2.0 MVC
Modelo especializado para gestión de inventario y movimientos
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from PyQt5.QtCore import pyqtSignal

from models.base_model import BaseModel
from models.entities import InventoryMovement, Product

logger = logging.getLogger(__name__)

class InventoryModel(BaseModel):
    """Modelo de datos para inventario"""
    
    # Señales específicas de inventario
    movement_created = pyqtSignal(dict)
    stock_updated = pyqtSignal(int, int)  # product_id, new_stock
    low_stock_alert = pyqtSignal(dict)
    movement_reversed = pyqtSignal(dict)
    
    def __init__(self, inventory_manager=None, product_manager=None, parent=None):
        super().__init__(parent)
        self.inventory_manager = inventory_manager
        self.product_manager = product_manager
        
        # Estado del modelo
        self._movements = []
        self._products_stock = {}  # Cache de stock por producto
        
        # Configuración
        self.low_stock_threshold = 5
        self.auto_check_stock = True
        
        self.logger = logging.getLogger(f"{__name__}.InventoryModel")
    
    # === PROPIEDADES ===
    
    @property
    def movements(self) -> List[InventoryMovement]:
        """Lista de movimientos"""
        return self._movements.copy()
    
    @property
    def products_stock(self) -> Dict[int, int]:
        """Stock actual por producto"""
        return self._products_stock.copy()
    
    @property
    def total_movements(self) -> int:
        """Total de movimientos"""
        return len(self._movements)
    
    @property
    def low_stock_products(self) -> List[int]:
        """IDs de productos con stock bajo"""
        return [
            product_id for product_id, stock in self._products_stock.items()
            if stock <= self.low_stock_threshold
        ]
    
    # === MÉTODOS PÚBLICOS ===
    
    def load_movements(self, filters: Dict[str, Any] = None) -> bool:
        """Cargar movimientos de inventario"""
        if not self.inventory_manager:
            self._set_error("Manager de inventario no disponible")
            return False
        
        try:
            self.start_loading()
            
            # Cargar movimientos
            movements_data = self.inventory_manager.get_movements(filters or {})
            self._movements = [InventoryMovement.from_dict(m) for m in movements_data]
            
            # Actualizar cache de stock
            self._update_stock_cache()
            
            self.data_changed.emit()
            self.logger.info(f"Cargados {len(self._movements)} movimientos")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cargando movimientos: {e}")
            self._set_error(f"Error cargando movimientos: {str(e)}")
            return False
        finally:
            self.finish_loading()
    
    def create_movement(self, movement_data: Dict[str, Any]) -> bool:
        """Crear nuevo movimiento de inventario"""
        try:
            # Validar datos
            if not self._validate_movement_data(movement_data):
                return False
            
            # Crear movimiento
            movement = InventoryMovement.from_dict(movement_data)
            
            # Procesar movimiento si hay manager
            if self.inventory_manager:
                result = self.inventory_manager.create_movement(movement_data)
                if result.get('success'):
                    movement_data['id'] = result.get('movement_id')
                else:
                    self._set_error(result.get('message', 'Error creando movimiento'))
                    return False
            
            # Agregar a lista local
            self._movements.append(movement)
            
            # Actualizar stock
            self._update_product_stock(movement.producto_id, movement.cantidad, movement.tipo_movimiento)
            
            self.movement_created.emit(movement_data)
            self.data_changed.emit()
            
            self.logger.info(f"Movimiento creado: {movement}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creando movimiento: {e}")
            self._set_error(f"Error creando movimiento: {str(e)}")
            return False
    
    def adjust_stock(self, product_id: int, new_stock: int, reason: str = "Ajuste manual") -> bool:
        """Ajustar stock de producto"""
        try:
            current_stock = self._products_stock.get(product_id, 0)
            difference = new_stock - current_stock
            
            if difference == 0:
                return True  # No hay cambio
            
            # Determinar tipo de movimiento
            tipo_movimiento = "ENTRADA" if difference > 0 else "SALIDA"
            cantidad = abs(difference)
            
            # Crear movimiento de ajuste
            movement_data = {
                'producto_id': product_id,
                'tipo_movimiento': tipo_movimiento,
                'cantidad': cantidad,
                'cantidad_anterior': current_stock,
                'cantidad_nueva': new_stock,
                'motivo': reason,
                'referencia_tipo': 'ajuste',
                'usuario_id': self.get_value('current_user_id', 1),
                'usuario_nombre': self.get_value('current_user_name', 'Sistema'),
                'fecha_movimiento': datetime.now()
            }
            
            return self.create_movement(movement_data)
            
        except Exception as e:
            self.logger.error(f"Error ajustando stock: {e}")
            self._set_error(f"Error ajustando stock: {str(e)}")
            return False
    
    def process_sale_movement(self, sale_items: List[Dict[str, Any]], sale_id: int) -> bool:
        """Procesar movimientos de salida por venta"""
        try:
            for item in sale_items:
                movement_data = {
                    'producto_id': item['producto_id'],
                    'tipo_movimiento': 'SALIDA',
                    'cantidad': item['cantidad'],
                    'precio_costo': item.get('precio_costo', 0),
                    'motivo': 'Venta',
                    'referencia_id': sale_id,
                    'referencia_tipo': 'venta',
                    'usuario_id': self.get_value('current_user_id', 1),
                    'usuario_nombre': self.get_value('current_user_name', 'Sistema')
                }
                
                if not self.create_movement(movement_data):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error procesando movimientos de venta: {e}")
            self._set_error(f"Error procesando movimientos de venta: {str(e)}")
            return False
    
    def process_purchase_movement(self, purchase_items: List[Dict[str, Any]], purchase_id: int) -> bool:
        """Procesar movimientos de entrada por compra"""
        try:
            for item in purchase_items:
                movement_data = {
                    'producto_id': item['producto_id'],
                    'tipo_movimiento': 'ENTRADA',
                    'cantidad': item['cantidad'],
                    'precio_costo': item.get('precio_unitario', 0),
                    'motivo': 'Compra',
                    'referencia_id': purchase_id,
                    'referencia_tipo': 'compra',
                    'usuario_id': self.get_value('current_user_id', 1),
                    'usuario_nombre': self.get_value('current_user_name', 'Sistema')
                }
                
                if not self.create_movement(movement_data):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error procesando movimientos de compra: {e}")
            self._set_error(f"Error procesando movimientos de compra: {str(e)}")
            return False
    
    def get_product_stock(self, product_id: int) -> int:
        """Obtener stock actual de producto"""
        return self._products_stock.get(product_id, 0)
    
    def get_movements_by_product(self, product_id: int) -> List[InventoryMovement]:
        """Obtener movimientos por producto"""
        return [m for m in self._movements if m.producto_id == product_id]
    
    def get_movements_by_date(self, start_date: date, end_date: date) -> List[InventoryMovement]:
        """Obtener movimientos por rango de fechas"""
        return [
            m for m in self._movements
            if m.fecha_movimiento and start_date <= m.fecha_movimiento.date() <= end_date
        ]
    
    def get_movements_by_type(self, movement_type: str) -> List[InventoryMovement]:
        """Obtener movimientos por tipo"""
        return [m for m in self._movements if m.tipo_movimiento == movement_type]
    
    def calculate_stock_value(self) -> Dict[str, float]:
        """Calcular valor total del stock"""
        total_value = 0.0
        product_values = {}
        
        for movement in self._movements:
            if movement.tipo_movimiento == "ENTRADA":
                value = movement.cantidad * movement.precio_costo
                total_value += value
                product_values[movement.producto_id] = product_values.get(movement.producto_id, 0) + value
        
        return {
            'total_value': total_value,
            'product_values': product_values
        }
    
    # === MÉTODOS PROTEGIDOS ===
    
    def _validate_movement_data(self, data: Dict[str, Any]) -> bool:
        """Validar datos de movimiento"""
        self._validation_errors.clear()
        
        # Validaciones requeridas
        if not data.get('producto_id'):
            self._add_validation_error("ID de producto es obligatorio")
        
        if data.get('tipo_movimiento') not in ['ENTRADA', 'SALIDA', 'AJUSTE']:
            self._add_validation_error("Tipo de movimiento inválido")
        
        try:
            cantidad = int(data.get('cantidad', 0))
            if cantidad <= 0:
                self._add_validation_error("La cantidad debe ser mayor a cero")
        except (ValueError, TypeError):
            self._add_validation_error("Cantidad inválida")
        
        # Verificar stock disponible para salidas
        if data.get('tipo_movimiento') == 'SALIDA':
            product_id = data.get('producto_id')
            cantidad = data.get('cantidad', 0)
            current_stock = self.get_product_stock(product_id)
            
            if cantidad > current_stock:
                self._add_validation_error(f"Stock insuficiente. Disponible: {current_stock}")
        
        return len(self._validation_errors) == 0
    
    def _update_product_stock(self, product_id: int, cantidad: int, tipo_movimiento: str):
        """Actualizar stock de producto en cache"""
        current_stock = self._products_stock.get(product_id, 0)
        
        if tipo_movimiento == "ENTRADA":
            new_stock = current_stock + cantidad
        elif tipo_movimiento == "SALIDA":
            new_stock = max(0, current_stock - cantidad)
        else:  # AJUSTE
            new_stock = cantidad
        
        self._products_stock[product_id] = new_stock
        
        # Emitir señal de actualización
        self.stock_updated.emit(product_id, new_stock)
        
        # Verificar stock bajo
        if self.auto_check_stock and new_stock <= self.low_stock_threshold:
            self.low_stock_alert.emit({
                'product_id': product_id,
                'current_stock': new_stock,
                'threshold': self.low_stock_threshold
            })
    
    def _update_stock_cache(self):
        """Actualizar cache de stock desde productos"""
        if self.product_manager:
            try:
                products = self.product_manager.get_all_products()
                self._products_stock = {p['id']: p.get('stock_actual', 0) for p in products}
            except Exception as e:
                self.logger.warning(f"No se pudo actualizar cache de stock: {e}")
    
    def _get_default_values(self) -> Dict[str, Any]:
        """Valores por defecto para movimiento"""
        return {
            'producto_id': 0,
            'tipo_movimiento': 'ENTRADA',
            'cantidad': 1,
            'precio_costo': 0.0,
            'motivo': '',
            'usuario_id': 1,
            'estado': 'ACTIVO'
        }