"""
Gestor de Productos para AlmacénPro
Manejo completo de productos, stock y movimientos de inventario
"""

import logging
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

class ProductManager:
    """Gestor principal para productos y gestión de stock"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
        
    def search_products(self, search_term: str, limit: int = 50) -> List[Dict]:
        """Buscar productos por código de barras, nombre o código interno"""
        try:
            search_term = search_term.strip() if search_term else ""
            
            if not search_term:
                # Si no hay término de búsqueda, devolver todos los productos activos
                query = """
                    SELECT p.*, c.nombre as categoria_nombre, pr.nombre as proveedor_nombre
                    FROM productos p
                    LEFT JOIN categorias c ON p.categoria_id = c.id
                    LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
                    WHERE p.activo = 1
                    ORDER BY p.nombre
                    LIMIT ?
                """
                results = self.db.execute_query(query, (limit,))
                if results:
                    return [dict(row) for row in results]
                return []
            else:
                # Búsqueda con término específico
                query = """
                    SELECT p.*, c.nombre as categoria_nombre, pr.nombre as proveedor_nombre
                    FROM productos p
                    LEFT JOIN categorias c ON p.categoria_id = c.id
                    LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
                    WHERE (p.codigo_barras LIKE ? OR p.nombre LIKE ? 
                           OR p.codigo_interno LIKE ?)
                    AND p.activo = 1
                    ORDER BY 
                        CASE 
                            WHEN p.codigo_barras = ? THEN 1
                            WHEN p.codigo_barras LIKE ? THEN 2
                            WHEN p.nombre LIKE ? THEN 3
                            ELSE 4
                        END,
                        p.nombre
                    LIMIT ?
                """
                
                search_pattern = f"%{search_term}%"
                exact_pattern = search_term
                starts_pattern = f"{search_term}%"
                
                params = (
                    search_pattern, search_pattern, search_pattern,  # WHERE clause
                    exact_pattern, starts_pattern, starts_pattern,   # ORDER BY clause
                    limit
                )
                results = self.db.execute_query(query, params)
                if results:
                    return [dict(row) for row in results]
                return []
            
        except Exception as e:
            self.logger.error(f"Error buscando productos: {e}")
            return []
    
    def get_product_by_barcode(self, barcode: str) -> Optional[Dict]:
        """Obtener producto por código de barras"""
        try:
            return self.db.execute_single("""
                SELECT p.*, c.nombre as categoria_nombre, pr.nombre as proveedor_nombre
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
                WHERE p.codigo_barras = ? AND p.activo = 1
            """, (barcode,))
            
        except Exception as e:
            self.logger.error(f"Error obteniendo producto por código: {e}")
            return None
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """Obtener producto por ID"""
        try:
            return self.db.execute_single("""
                SELECT p.*, c.nombre as categoria_nombre, pr.nombre as proveedor_nombre
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
                WHERE p.id = ?
            """, (product_id,))
            
        except Exception as e:
            self.logger.error(f"Error obteniendo producto por ID: {e}")
            return None
    
    def create_product(self, product_data: Dict) -> int:
        """Crear nuevo producto - Compatible con GUI y esquema real"""
        try:
            # Mapear campos de GUI a esquema real para compatibilidad
            nombre = product_data.get('name') or product_data.get('nombre')
            codigo_barras = product_data.get('barcode') or product_data.get('codigo_barras')
            codigo_interno = product_data.get('sku') or product_data.get('codigo_interno')
            precio_venta = product_data.get('sale_price') or product_data.get('precio_venta')
            precio_compra = product_data.get('cost_price') or product_data.get('precio_compra', 0)
            stock_actual = product_data.get('stock') or product_data.get('stock_actual', 0)
            stock_minimo = product_data.get('minimum_stock') or product_data.get('stock_minimo', 0)
            
            # Validaciones básicas
            if not nombre:
                raise ValueError("El nombre del producto es obligatorio")
            
            if not precio_venta or precio_venta <= 0:
                raise ValueError("El precio de venta debe ser mayor a cero")
            
            # Verificar código de barras único (si se proporciona)
            if product_data.get('codigo_barras'):
                existing = self.db.execute_single("""
                    SELECT id FROM productos WHERE codigo_barras = ?
                """, (product_data['codigo_barras'],))
                
                if existing:
                    return False, "Ya existe un producto con ese código de barras", 0
            
            # Generar código interno si no se proporciona
            if not product_data.get('codigo_interno'):
                product_data['codigo_interno'] = self.generate_internal_code()
            
            # Insertar producto
            product_id = self.db.execute_insert("""
                INSERT INTO productos (
                    codigo_barras, codigo_interno, nombre, descripcion, categoria_id,
                    precio_compra, precio_venta, precio_mayorista, margen_ganancia,
                    stock_actual, stock_minimo, stock_maximo, unidad_medida,
                    proveedor_id, ubicacion, imagen_url, iva_porcentaje,
                    es_produccion_propia, peso, vencimiento, lote,
                    permite_venta_sin_stock, es_pesable, codigo_plu
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product_data.get('codigo_barras'),
                product_data.get('codigo_interno'),
                product_data['nombre'],
                product_data.get('descripcion'),
                product_data.get('categoria_id'),
                product_data.get('precio_compra', 0),
                product_data['precio_venta'],
                product_data.get('precio_mayorista', 0),
                product_data.get('margen_ganancia', 0),
                product_data.get('stock_actual', 0),
                product_data.get('stock_minimo', 0),
                product_data.get('stock_maximo', 0),
                product_data.get('unidad_medida', 'UNIDAD'),
                product_data.get('proveedor_id'),
                product_data.get('ubicacion'),
                product_data.get('imagen_url'),
                product_data.get('iva_porcentaje', 21),
                product_data.get('es_produccion_propia', False),
                product_data.get('peso'),
                product_data.get('vencimiento'),
                product_data.get('lote'),
                product_data.get('permite_venta_sin_stock', False),
                product_data.get('es_pesable', False),
                product_data.get('codigo_plu')
            ))
            
            if product_id:
                self.logger.info(f"Producto creado exitosamente: ID {product_id}")
                return True, f"Producto creado exitosamente", product_id
            else:
                return False, "Error al crear el producto", 0
                
        except Exception as e:
            self.logger.error(f"Error creando producto: {e}")
            return False, f"Error creando producto: {str(e)}", 0
    
    def update_product(self, product_id: int, product_data: Dict) -> Tuple[bool, str]:
        """Actualizar producto existente"""
        try:
            # Verificar que el producto existe
            existing_product = self.get_product_by_id(product_id)
            if not existing_product:
                return False, "Producto no encontrado"
            
            # Validaciones básicas
            if product_data.get('nombre') and not product_data['nombre'].strip():
                return False, "El nombre del producto no puede estar vacío"
            
            if product_data.get('precio_venta') and product_data['precio_venta'] <= 0:
                return False, "El precio de venta debe ser mayor a cero"
            
            # Verificar código de barras único (si se está cambiando)
            if product_data.get('codigo_barras'):
                existing = self.db.execute_single("""
                    SELECT id FROM productos WHERE codigo_barras = ? AND id != ?
                """, (product_data['codigo_barras'], product_id))
                
                if existing:
                    return False, "Ya existe otro producto con ese código de barras"
            
            # Construir query de actualización dinámicamente
            update_fields = []
            update_values = []
            
            allowed_fields = [
                'codigo_barras', 'codigo_interno', 'nombre', 'descripcion', 'categoria_id',
                'precio_compra', 'precio_venta', 'precio_mayorista', 'margen_ganancia',
                'stock_minimo', 'stock_maximo', 'unidad_medida', 'proveedor_id',
                'ubicacion', 'imagen_url', 'iva_porcentaje', 'es_produccion_propia',
                'peso', 'vencimiento', 'lote', 'activo'
            ]
            
            for field, value in product_data.items():
                if field in allowed_fields:
                    update_fields.append(f"{field} = ?")
                    update_values.append(value)
            
            if not update_fields:
                return False, "No hay campos válidos para actualizar"
            
            # Agregar timestamp de actualización
            update_fields.append("actualizado_en = CURRENT_TIMESTAMP")
            update_values.append(product_id)
            
            query = f"UPDATE productos SET {', '.join(update_fields)} WHERE id = ?"
            
            success = self.db.execute_update(query, update_values)
            
            if success:
                self.logger.info(f"Producto actualizado: ID {product_id}")
                return True, "Producto actualizado exitosamente"
            else:
                return False, "Error al actualizar el producto"
                
        except Exception as e:
            self.logger.error(f"Error actualizando producto: {e}")
            return False, f"Error actualizando producto: {str(e)}"
    
    def update_stock(self, product_id: int, new_quantity: float, movement_type: str, 
                    reason: str, user_id: int, unit_price: float = None, 
                    reference_id: int = None, reference_type: str = None,
                    notes: str = None) -> Tuple[bool, str]:
        """Actualizar stock y registrar movimiento"""
        try:
            # Obtener producto actual
            product = self.get_product_by_id(product_id)
            if not product:
                return False, "Producto no encontrado"
            
            current_stock = float(product['stock_actual'])
            
            # Calcular nuevo stock según tipo de movimiento
            if movement_type == 'ENTRADA':
                final_stock = current_stock + new_quantity
                movement_quantity = new_quantity
            elif movement_type == 'SALIDA':
                if current_stock < new_quantity:
                    return False, f"Stock insuficiente. Disponible: {current_stock}"
                final_stock = current_stock - new_quantity
                movement_quantity = -new_quantity
            elif movement_type == 'AJUSTE':
                final_stock = new_quantity
                movement_quantity = new_quantity - current_stock
            else:
                return False, "Tipo de movimiento inválido"
            
            # Iniciar transacción
            self.db.begin_transaction()
            
            try:
                # Para evitar problemas con triggers, usar método simple
                # que solo actualiza sin validaciones complejas
                success = self.db.execute_update(
                    "UPDATE productos SET stock_actual = ? WHERE id = ?", 
                    (final_stock, product_id)
                )
                
                if not success:
                    raise Exception("Error actualizando stock del producto")
                
                # Registrar movimiento
                movement_id = self.db.execute_insert("""
                    INSERT INTO movimientos_stock (
                        producto_id, tipo_movimiento, motivo, cantidad_anterior,
                        cantidad_movimiento, cantidad_nueva, precio_unitario,
                        usuario_id, referencia_id, referencia_tipo, observaciones
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    product_id, movement_type, reason, current_stock,
                    movement_quantity, final_stock, unit_price,
                    user_id, reference_id, reference_type, notes
                ))
                
                if not movement_id:
                    raise Exception("Error registrando movimiento de stock")
                
                # Confirmar transacción
                self.db.commit_transaction()
                
                self.logger.info(f"Stock actualizado: Producto {product_id}, "
                               f"Stock anterior: {current_stock}, "
                               f"Movimiento: {movement_quantity}, "
                               f"Stock nuevo: {final_stock}")
                
                return True, f"Stock actualizado. Nuevo stock: {final_stock}"
                
            except Exception as e:
                self.db.rollback_transaction()
                raise e
                
        except Exception as e:
            self.logger.error(f"Error actualizando stock: {e}")
            return False, f"Error actualizando stock: {str(e)}"
    
    def get_stock_movements(self, product_id: int = None, 
                           date_from: date = None, date_to: date = None,
                           limit: int = 100) -> List[Dict]:
        """Obtener historial de movimientos de stock"""
        try:
            query = """
                SELECT ms.*, p.nombre as producto_nombre, p.codigo_barras,
                       u.nombre_completo as usuario_nombre
                FROM movimientos_stock ms
                LEFT JOIN productos p ON ms.producto_id = p.id
                LEFT JOIN usuarios u ON ms.usuario_id = u.id
                WHERE 1=1
            """
            params = []
            
            if product_id:
                query += " AND ms.producto_id = ?"
                params.append(product_id)
            
            if date_from:
                query += " AND DATE(ms.fecha_movimiento) >= ?"
                params.append(date_from)
            
            if date_to:
                query += " AND DATE(ms.fecha_movimiento) <= ?"
                params.append(date_to)
            
            query += " ORDER BY ms.fecha_movimiento DESC LIMIT ?"
            params.append(limit)
            
            return self.db.execute_query(query, params)
            
        except Exception as e:
            self.logger.error(f"Error obteniendo movimientos de stock: {e}")
            return []
    
    def get_products_with_low_stock(self) -> List[Dict]:
        """Obtener productos con stock bajo (menor al mínimo)"""
        try:
            return self.db.execute_query("""
                SELECT p.*, c.nombre as categoria_nombre, pr.nombre as proveedor_nombre
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
                WHERE p.stock_actual <= p.stock_minimo 
                AND p.stock_minimo > 0
                AND p.activo = 1
                ORDER BY (p.stock_actual - p.stock_minimo) ASC
            """)
            
        except Exception as e:
            self.logger.error(f"Error obteniendo productos con stock bajo: {e}")
            return []
    
    def get_products_by_category(self, category_id: int) -> List[Dict]:
        """Obtener productos de una categoría específica"""
        try:
            return self.db.execute_query("""
                SELECT p.*, c.nombre as categoria_nombre, pr.nombre as proveedor_nombre
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
                WHERE p.categoria_id = ? AND p.activo = 1
                ORDER BY p.nombre
            """, (category_id,))
            
        except Exception as e:
            self.logger.error(f"Error obteniendo productos por categoría: {e}")
            return []
    
    def get_all_products(self, include_inactive: bool = False, 
                        page: int = 1, page_size: int = 100) -> List[Dict]:
        """Obtener todos los productos con paginación"""
        try:
            query = """
                SELECT p.*, c.nombre as categoria_nombre, pr.nombre as proveedor_nombre
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
            """
            params = []
            
            if not include_inactive:
                query += " WHERE p.activo = 1"
            
            query += " ORDER BY p.nombre LIMIT ? OFFSET ?"
            params.extend([page_size, (page - 1) * page_size])
            
            return self.db.execute_query(query, params)
            
        except Exception as e:
            self.logger.error(f"Error obteniendo todos los productos: {e}")
            return []
    
    def delete_product(self, product_id: int, user_id: int) -> Tuple[bool, str]:
        """Eliminar producto (marcar como inactivo)"""
        try:
            # Verificar que el producto existe
            product = self.get_product_by_id(product_id)
            if not product:
                return False, "Producto no encontrado"
            
            # Verificar si tiene movimientos recientes
            recent_movements = self.db.execute_query("""
                SELECT COUNT(*) as count FROM movimientos_stock 
                WHERE producto_id = ? AND fecha_movimiento >= datetime('now', '-30 days')
            """, (product_id,))
            
            if recent_movements and recent_movements[0]['count'] > 0:
                # Solo marcar como inactivo si tiene movimientos recientes
                success = self.db.execute_update("""
                    UPDATE productos 
                    SET activo = 0, actualizado_en = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (product_id,))
                
                if success:
                    self.logger.info(f"Producto marcado como inactivo: ID {product_id}")
                    return True, "Producto marcado como inactivo"
                else:
                    return False, "Error al desactivar el producto"
            else:
                # Eliminar físicamente si no tiene movimientos recientes
                success = self.db.execute_update("DELETE FROM productos WHERE id = ?", (product_id,))
                
                if success:
                    self.logger.info(f"Producto eliminado: ID {product_id}")
                    return True, "Producto eliminado exitosamente"
                else:
                    return False, "Error al eliminar el producto"
                    
        except Exception as e:
            self.logger.error(f"Error eliminando producto: {e}")
            return False, f"Error eliminando producto: {str(e)}"
    
    def generate_internal_code(self) -> str:
        """Generar código interno único"""
        try:
            # Obtener siguiente número secuencial
            result = self.db.execute_single("""
                SELECT COALESCE(MAX(CAST(SUBSTR(codigo_interno, 4) AS INTEGER)), 0) + 1 as next_num
                FROM productos 
                WHERE codigo_interno LIKE 'PRD%'
            """)
            
            if result:
                next_num = result['next_num']
            else:
                next_num = 1
            
            return f"PRD{next_num:06d}"
            
        except Exception as e:
            self.logger.error(f"Error generando código interno: {e}")
            return f"PRD{uuid.uuid4().hex[:6].upper()}"
    
    def update_prices_by_percentage(self, category_id: int = None, 
                                   provider_id: int = None,
                                   percentage: float = 0,
                                   price_type: str = 'venta',
                                   user_id: int = None) -> Tuple[bool, str, int]:
        """Actualizar precios masivamente por porcentaje"""
        try:
            if percentage == 0:
                return False, "El porcentaje debe ser diferente de cero", 0
            
            # Construir query dinámicamente
            query = "UPDATE productos SET "
            params = []
            
            if price_type == 'venta':
                query += "precio_venta = precio_venta * (1 + ? / 100)"
            elif price_type == 'compra':
                query += "precio_compra = precio_compra * (1 + ? / 100)"
            elif price_type == 'mayorista':
                query += "precio_mayorista = precio_mayorista * (1 + ? / 100)"
            else:
                return False, "Tipo de precio inválido", 0
            
            params.append(percentage)
            query += ", actualizado_en = CURRENT_TIMESTAMP WHERE activo = 1"
            
            if category_id:
                query += " AND categoria_id = ?"
                params.append(category_id)
            
            if provider_id:
                query += " AND proveedor_id = ?"
                params.append(provider_id)
            
            affected_rows = self.db.execute_update(query, params)
            
            if affected_rows > 0:
                self.logger.info(f"Precios actualizados: {affected_rows} productos, "
                               f"Porcentaje: {percentage}%, Tipo: {price_type}")
                return True, f"Precios actualizados en {affected_rows} productos", affected_rows
            else:
                return False, "No se encontraron productos para actualizar", 0
                
        except Exception as e:
            self.logger.error(f"Error actualizando precios masivamente: {e}")
            return False, f"Error actualizando precios: {str(e)}", 0
    
    def calculate_stock_value(self, category_id: int = None) -> Dict:
        """Calcular valor total del stock"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_productos,
                    SUM(stock_actual) as total_unidades,
                    SUM(stock_actual * precio_compra) as valor_compra,
                    SUM(stock_actual * precio_venta) as valor_venta,
                    SUM(stock_actual * (precio_venta - precio_compra)) as ganancia_potencial
                FROM productos 
                WHERE activo = 1
            """
            params = []
            
            if category_id:
                query += " AND categoria_id = ?"
                params.append(category_id)
            
            result = self.db.execute_single(query, params)
            
            if result:
                return {
                    'total_productos': result['total_productos'] or 0,
                    'total_unidades': float(result['total_unidades'] or 0),
                    'valor_compra': float(result['valor_compra'] or 0),
                    'valor_venta': float(result['valor_venta'] or 0),
                    'ganancia_potencial': float(result['ganancia_potencial'] or 0)
                }
            else:
                return {
                    'total_productos': 0,
                    'total_unidades': 0.0,
                    'valor_compra': 0.0,
                    'valor_venta': 0.0,
                    'ganancia_potencial': 0.0
                }
                
        except Exception as e:
            self.logger.error(f"Error calculando valor de stock: {e}")
            return {
                'total_productos': 0,
                'total_unidades': 0.0,
                'valor_compra': 0.0,
                'valor_venta': 0.0,
                'ganancia_potencial': 0.0
            }
    
    def get_products_expiring_soon(self, days: int = 30) -> List[Dict]:
        """Obtener productos que vencen pronto"""
        try:
            return self.db.execute_query("""
                SELECT p.*, c.nombre as categoria_nombre
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                WHERE p.vencimiento IS NOT NULL 
                AND p.vencimiento <= DATE('now', '+{} days')
                AND p.stock_actual > 0
                AND p.activo = 1
                ORDER BY p.vencimiento ASC
            """.format(days))
            
        except Exception as e:
            self.logger.error(f"Error obteniendo productos por vencer: {e}")
            return []