"""
Modelo de Productos - AlmacénPro v2.0 MVC
Modelo especializado para gestión de productos
"""

import logging
from typing import Dict, Any, List, Optional
from PyQt5.QtCore import pyqtSignal

from models.base_model import BaseModel
from models.entities import Product, Category

logger = logging.getLogger(__name__)

class ProductModel(BaseModel):
    """Modelo de datos para productos"""
    
    # Señales específicas de productos
    product_created = pyqtSignal(dict)
    product_updated = pyqtSignal(dict)
    product_deleted = pyqtSignal(int)
    stock_changed = pyqtSignal(int, int)  # product_id, new_stock
    low_stock_alert = pyqtSignal(dict)
    
    def __init__(self, product_manager=None, parent=None):
        super().__init__(parent)
        self.product_manager = product_manager
        
        # Estado del modelo
        self._products = []
        self._categories = []
        self._current_product = None
        self._search_filters = {}
        
        # Configuración específica
        self.auto_check_stock = True
        self.low_stock_threshold = 5
        
        self.logger = logging.getLogger(f"{__name__}.ProductModel")
    
    # === PROPIEDADES ===
    
    @property
    def products(self) -> List[Product]:
        """Lista de productos"""
        return self._products.copy()
    
    @property
    def categories(self) -> List[Category]:
        """Lista de categorías"""
        return self._categories.copy()
    
    @property
    def current_product(self) -> Optional[Product]:
        """Producto actual seleccionado"""
        return self._current_product
    
    @property
    def total_products(self) -> int:
        """Total de productos"""
        return len(self._products)
    
    @property
    def low_stock_products(self) -> List[Product]:
        """Productos con stock bajo"""
        return [p for p in self._products if p.necesita_reposicion]
    
    @property
    def total_stock_value(self) -> float:
        """Valor total del stock"""
        return sum(p.valor_stock for p in self._products)
    
    # === MÉTODOS PÚBLICOS ===
    
    def load_products(self) -> bool:
        """Cargar productos desde el manager"""
        if not self.product_manager:
            self._set_error("Manager de productos no disponible")
            return False
        
        try:
            self.start_loading()
            
            # Cargar productos
            products_data = self.product_manager.get_all_products()
            self._products = [Product.from_dict(p) for p in products_data]
            
            # Cargar categorías
            categories_data = self.product_manager.get_all_categories()
            self._categories = [Category.from_dict(c) for c in categories_data]
            
            # Verificar stock bajo si está habilitado
            if self.auto_check_stock:
                self._check_low_stock()
            
            self.data_changed.emit()
            self.logger.info(f"Cargados {len(self._products)} productos y {len(self._categories)} categorías")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cargando productos: {e}")
            self._set_error(f"Error cargando productos: {str(e)}")
            return False
        finally:
            self.finish_loading()
    
    def create_product(self, product_data: Dict[str, Any]) -> bool:
        """Crear nuevo producto"""
        if not self.product_manager:
            return False
        
        try:
            # Validar datos
            if not self._validate_product_data(product_data):
                return False
            
            # Crear producto
            result = self.product_manager.create_product(product_data)
            
            if result.get('success'):
                # Crear entidad
                product_data['id'] = result.get('product_id')
                new_product = Product.from_dict(product_data)
                self._products.append(new_product)
                
                self.product_created.emit(product_data)
                self.data_changed.emit()
                
                self.logger.info(f"Producto creado: {new_product}")
                return True
            else:
                self._set_error(result.get('message', 'Error creando producto'))
                return False
                
        except Exception as e:
            self.logger.error(f"Error creando producto: {e}")
            self._set_error(f"Error creando producto: {str(e)}")
            return False
    
    def update_product(self, product_id: int, product_data: Dict[str, Any]) -> bool:
        """Actualizar producto existente"""
        if not self.product_manager:
            return False
        
        try:
            # Validar datos
            if not self._validate_product_data(product_data):
                return False
            
            # Actualizar producto
            product_data['id'] = product_id
            result = self.product_manager.update_product(product_data)
            
            if result.get('success'):
                # Actualizar en la lista local
                for i, product in enumerate(self._products):
                    if product.id == product_id:
                        self._products[i] = Product.from_dict(product_data)
                        break
                
                self.product_updated.emit(product_data)
                self.data_changed.emit()
                
                self.logger.info(f"Producto actualizado: {product_id}")
                return True
            else:
                self._set_error(result.get('message', 'Error actualizando producto'))
                return False
                
        except Exception as e:
            self.logger.error(f"Error actualizando producto: {e}")
            self._set_error(f"Error actualizando producto: {str(e)}")
            return False
    
    def delete_product(self, product_id: int) -> bool:
        """Eliminar producto"""
        if not self.product_manager:
            return False
        
        try:
            result = self.product_manager.delete_product(product_id)
            
            if result.get('success'):
                # Eliminar de la lista local
                self._products = [p for p in self._products if p.id != product_id]
                
                self.product_deleted.emit(product_id)
                self.data_changed.emit()
                
                self.logger.info(f"Producto eliminado: {product_id}")
                return True
            else:
                self._set_error(result.get('message', 'Error eliminando producto'))
                return False
                
        except Exception as e:
            self.logger.error(f"Error eliminando producto: {e}")
            self._set_error(f"Error eliminando producto: {str(e)}")
            return False
    
    def search_products(self, search_text: str, filters: Dict[str, Any] = None) -> List[Product]:
        """Buscar productos por texto y filtros"""
        if not search_text and not filters:
            return self._products
        
        results = self._products
        
        # Filtrar por texto
        if search_text:
            search_text = search_text.lower()
            results = [
                p for p in results
                if search_text in p.nombre.lower() or
                   search_text in p.codigo.lower() or
                   search_text in p.descripcion.lower()
            ]
        
        # Aplicar filtros adicionales
        if filters:
            if filters.get('categoria_id'):
                results = [p for p in results if p.categoria_id == filters['categoria_id']]
            
            if filters.get('activo') is not None:
                results = [p for p in results if p.activo == filters['activo']]
            
            if filters.get('stock_bajo'):
                results = [p for p in results if p.necesita_reposicion]
        
        return results
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Obtener producto por ID"""
        return next((p for p in self._products if p.id == product_id), None)
    
    def get_product_by_code(self, code: str) -> Optional[Product]:
        """Obtener producto por código"""
        return next((p for p in self._products if p.codigo == code), None)
    
    def set_current_product(self, product_id: int):
        """Establecer producto actual"""
        self._current_product = self.get_product_by_id(product_id)
        self.data_changed.emit()
    
    def update_stock(self, product_id: int, new_stock: int) -> bool:
        """Actualizar stock de producto"""
        product = self.get_product_by_id(product_id)
        if not product:
            return False
        
        try:
            # Actualizar en base de datos
            if self.product_manager:
                result = self.product_manager.update_product_stock(product_id, new_stock)
                if not result.get('success'):
                    self._set_error(result.get('message', 'Error actualizando stock'))
                    return False
            
            # Actualizar localmente
            old_stock = product.stock_actual
            product.stock_actual = new_stock
            
            self.stock_changed.emit(product_id, new_stock)
            
            # Verificar stock bajo
            if product.necesita_reposicion:
                self.low_stock_alert.emit(product.to_dict())
            
            self.data_changed.emit()
            
            self.logger.info(f"Stock actualizado para {product.nombre}: {old_stock} -> {new_stock}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error actualizando stock: {e}")
            self._set_error(f"Error actualizando stock: {str(e)}")
            return False
    
    def get_products_by_category(self, category_id: int) -> List[Product]:
        """Obtener productos por categoría"""
        return [p for p in self._products if p.categoria_id == category_id]
    
    def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """Obtener categoría por ID"""
        return next((c for c in self._categories if c.id == category_id), None)
    
    # === MÉTODOS PROTEGIDOS ===
    
    def _validate_product_data(self, data: Dict[str, Any]) -> bool:
        """Validar datos de producto"""
        self._validation_errors.clear()
        
        # Validaciones requeridas
        if not data.get('nombre', '').strip():
            self._add_validation_error("El nombre del producto es obligatorio")
        
        if not data.get('codigo', '').strip():
            self._add_validation_error("El código del producto es obligatorio")
        
        # Validaciones de formato
        try:
            precio = float(data.get('precio', 0))
            if precio < 0:
                self._add_validation_error("El precio no puede ser negativo")
        except (ValueError, TypeError):
            self._add_validation_error("Precio inválido")
        
        try:
            costo = float(data.get('costo', 0))
            if costo < 0:
                self._add_validation_error("El costo no puede ser negativo")
        except (ValueError, TypeError):
            self._add_validation_error("Costo inválido")
        
        try:
            stock = int(data.get('stock_actual', 0))
            if stock < 0:
                self._add_validation_error("El stock no puede ser negativo")
        except (ValueError, TypeError):
            self._add_validation_error("Stock inválido")
        
        # Verificar código único (si es creación)
        if not data.get('id'):
            if any(p.codigo == data.get('codigo') for p in self._products):
                self._add_validation_error("El código ya existe")
        
        return len(self._validation_errors) == 0
    
    def _check_low_stock(self):
        """Verificar productos con stock bajo"""
        for product in self._products:
            if product.necesita_reposicion:
                self.low_stock_alert.emit(product.to_dict())
    
    def _get_default_values(self) -> Dict[str, Any]:
        """Valores por defecto para producto"""
        return {
            'codigo': '',
            'nombre': '',
            'descripcion': '',
            'precio': 0.0,
            'costo': 0.0,
            'stock_actual': 0,
            'stock_minimo': 5,
            'stock_maximo': 100,
            'categoria_id': None,
            'unidad_medida': 'UNIDAD',
            'activo': True,
            'gravable': True
        }