"""
Gestor de Productos para AlmacénPro
Maneja productos, stock, categorías y movimientos de inventario
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from datetime import datetime

logger = logging.getLogger(__name__)

class ProductManager:
    """Gestor de productos y stock"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        logger.info("ProductManager inicializado")
    
    def get_all_products(self, active_only: bool = True, category_id: int = None) -> List[Dict]:
        """Obtener lista de todos los productos"""
        try:
            query = """
                SELECT p.*, c.nombre as categoria_nombre, pr.nombre as proveedor_nombre
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
            """
            
            conditions = []
            params = []
            
            if active_only:
                conditions.append("p.activo = 1")
            
            if category_id:
                conditions.append("p.categoria_id = ?")
                params.append(category_id)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY p.nombre"
            
            return self.db.execute_query(query, tuple(params) if params else None)
            
        except Exception as e:
            logger.error(f"Error obteniendo productos: {e}")
            return []
    
    def search_products(self, search_term: str, limit: int = 50) -> List[Dict]:
        """Buscar productos por código de barras, nombre o código interno"""
        try:
            # Limpiar término de búsqueda
            search_term = search_term.strip()
            if not search_term:
                return []
            
            query = """
                SELECT p.*, c.nombre as categoria_nombre, pr.nombre as proveedor_nombre
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
                WHERE (p.codigo_barras LIKE ? OR p.nombre LIKE ? OR p.codigo_interno LIKE ?)
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
            
            return self.db.execute_query(query, params)
            
        except Exception as e:
            logger.error(f"Error buscando productos: {e}")
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
            logger.error(f"Error obteniendo producto por código: {e}")
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
            logger.error(f"Error obteniendo producto por ID: {e}")
            return None
    
    def create_product(self, product_data: Dict) -> Tuple[bool, str, int]:
        """Crear nuevo producto"""
        try:
            # Validaciones básicas
            if not product_data.get('nombre'):
                return False, "El nombre del producto es obligatorio", 0
            
            if product_data.get('precio_venta', 0) <= 0:
                return False, "El precio de venta debe ser mayor a cero", 0
            
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
            
            # Registrar movimiento de stock inicial si hay stock
            if product_data.get('stock_actual', 0) > 0:
                self.register_stock_movement(
                    product_id=product_id,
                    movement_type='ENTRADA',
                    reason='STOCK_INICIAL',
                    quantity=product_data['stock_actual'],
                    unit_price=product_data.get('precio_compra', 0),
                    user_id=None,
                    notes="Stock inicial del producto"
                )
            
            logger.info(f"Producto creado: {product_data['nombre']} (ID: {product_id})")
            return True, f"Producto '{product_data['nombre']}' creado exitosamente", product_id
            
        except Exception as e:
            logger.error(f"Error creando producto: {e}")
            return False, f"Error creando producto: {str(e)}", 0
    
    def update_product(self, product_id: int, product_data: Dict) -> Tuple[bool, str]:
        """Actualizar producto existente"""
        try:
            # Verificar que el producto existe
            existing_product = self.get_product_by_id(product_id)
            if not existing_product:
                return False, "Producto no encontrado"
            
            # Validaciones
            if 'nombre' in product_data and not product_data['nombre']:
                return False, "El nombre del producto es obligatorio"
            
            if 'precio_venta' in product_data and product_data['precio_venta'] <= 0:
                return False, "El precio de venta debe ser mayor a cero"
            
            # Verificar código de barras único (si se está cambiando)
            if 'codigo_barras' in product_data and product_data['codigo_barras']:
                existing = self.db.execute_single("""
                    SELECT id FROM productos 
                    WHERE codigo_barras = ? AND id != ?
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
                'peso', 'vencimiento', 'lote', 'permite_venta_sin_stock', 'es_pesable',
                'codigo_plu', 'activo'
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
            
            rows_affected = self.db.execute_update(query, tuple(update_values))
            
            if rows_affected > 0:
                logger.info(f"Producto actualizado: ID {product_id}")
                return True, "Producto actualizado exitosamente"
            else:
                return False, "No se pudo actualizar el producto"
                
        except Exception as e:
            logger.error(f"Error actualizando producto: {e}")
            return False, f"Error actualizando producto: {str(e)}"
    
    def update_stock(self, product_id: int, new_quantity: float, 
                    movement_type: str, reason: str, user_id: int = None,
                    unit_price: float = None, reference_id: int = None,
                    reference_type: str = None, notes: str = None) -> Tuple[bool, str]:
        """Actualizar stock de producto y registrar movimiento"""
        try:
            # Obtener producto actual
            product = self.get_product_by_id(product_id)
            if not product:
                return False, "Producto no encontrado"
            
            current_stock = float(product['stock_actual'])
            
            # Calcular movimiento según tipo
            if movement_type == 'ENTRADA':
                final_stock = current_stock + new_quantity
                movement_quantity = new_quantity
            elif movement_type == 'SALIDA':
                final_stock = current_stock - new_quantity
                movement_quantity = -new_quantity
                
                # Verificar stock suficiente (si no permite venta sin stock)
                if not product.get('permite_venta_sin_stock', False) and final_stock < 0:
                    return False, f"Stock insuficiente. Stock actual: {current_stock}"
            else:  # AJUSTE
                final_stock = new_quantity
                movement_quantity = new_quantity - current_stock
            
            # Actualizar stock del producto
            self.db.execute_update("""
                UPDATE productos 
                SET stock_actual = ?, actualizado_en = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (final_stock, product_id))
            
            # Registrar movimiento
            self.register_stock_movement(
                product_id=product_id,
                movement_type=movement_type,
                reason=reason,
                previous_quantity=current_stock,
                movement_quantity=movement_quantity,
                new_quantity=final_stock,
                unit_price=unit_price,
                user_id=user_id,
                reference_id=reference_id,
                reference_type=reference_type,
                notes=notes
            )
            
            logger.info(f"Stock actualizado: Producto {product_id}, {current_stock} -> {final_stock}")
            return True, f"Stock actualizado: {current_stock} -> {final_stock}"
            
        except Exception as e:
            logger.error(f"Error actualizando stock: {e}")
            return False, f"Error actualizando stock: {str(e)}"
    
    def register_stock_movement(self, product_id: int, movement_type: str, reason: str,
                              quantity: float = None, previous_quantity: float = None,
                              movement_quantity: float = None, new_quantity: float = None,
                              unit_price: float = None, user_id: int = None,
                              reference_id: int = None, reference_type: str = None,
                              notes: str = None):
        """Registrar movimiento de stock"""
        try:
            # Si no se proporcionan las cantidades, usar quantity como movement_quantity
            if movement_quantity is None and quantity is not None:
                movement_quantity = quantity
            
            self.db.execute_insert("""
                INSERT INTO movimientos_stock (
                    producto_id, tipo_movimiento, motivo, cantidad_anterior,
                    cantidad_movimiento, cantidad_nueva, precio_unitario,
                    usuario_id, referencia_id, referencia_tipo, observaciones
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product_id, movement_type, reason, previous_quantity,
                movement_quantity, new_quantity, unit_price,
                user_id, reference_id, reference_type, notes
            ))
            
        except Exception as e:
            logger.error(f"Error registrando movimiento de stock: {e}")
    
    def get_stock_movements(self, product_id: int = None, days: int = 30) -> List[Dict]:
        """Obtener movimientos de stock"""
        try:
            query = """
                SELECT ms.*, p.nombre as producto_nombre, u.nombre_completo as usuario_nombre
                FROM movimientos_stock ms
                LEFT JOIN productos p ON ms.producto_id = p.id
                LEFT JOIN usuarios u ON ms.usuario_id = u.id
                WHERE ms.fecha_movimiento >= date('now', '-{} days')
            """.format(days)
            
            params = []
            if product_id:
                query += " AND ms.producto_id = ?"
                params.append(product_id)
            
            query += " ORDER BY ms.fecha_movimiento DESC LIMIT 1000"
            
            return self.db.execute_query(query, tuple(params) if params else None)
            
        except Exception as e:
            logger.error(f"Error obteniendo movimientos de stock: {e}")
            return []
    
    def get_low_stock_products(self, include_zero_stock: bool = True) -> List[Dict]:
        """Obtener productos con stock bajo o sin stock"""
        try:
            query = """
                SELECT p.*, c.nombre as categoria_nombre, pr.nombre as proveedor_nombre
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
                WHERE p.activo = 1 AND (
                    p.stock_actual <= p.stock_minimo
            """
            
            if not include_zero_stock:
                query += " AND p.stock_actual > 0"
            
            query += ") ORDER BY (p.stock_actual - p.stock_minimo) ASC, p.nombre"
            
            return self.db.execute_query(query)
            
        except Exception as e:
            logger.error(f"Error obteniendo productos con stock bajo: {e}")
            return []
    
    def get_products_by_category(self, category_id: int) -> List[Dict]:
        """Obtener productos por categoría"""
        try:
            return self.db.execute_query("""
                SELECT p.*, c.nombre as categoria_nombre
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                WHERE p.categoria_id = ? AND p.activo = 1
                ORDER BY p.nombre
            """, (category_id,))
            
        except Exception as e:
            logger.error(f"Error obteniendo productos por categoría: {e}")
            return []
    
    def generate_internal_code(self) -> str:
        """Generar código interno único"""
        try:
            # Obtener el último ID + 1
            result = self.db.execute_single("""
                SELECT MAX(id) as max_id FROM productos
            """)
            
            next_id = (result['max_id'] if result and result['max_id'] else 0) + 1
            return f"PROD{next_id:06d}"
            
        except Exception as e:
            logger.error(f"Error generando código interno: {e}")
            return f"PROD{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def calculate_stock_value(self, product_id: int = None) -> Dict:
        """Calcular valor del stock"""
        try:
            if product_id:
                # Valor de un producto específico
                query = """
                    SELECT 
                        SUM(stock_actual * precio_compra) as valor_compra,
                        SUM(stock_actual * precio_venta) as valor_venta,
                        SUM(stock_actual) as total_unidades
                    FROM productos 
                    WHERE id = ? AND activo = 1
                """
                params = (product_id,)
            else:
                # Valor total del stock
                query = """
                    SELECT 
                        SUM(stock_actual * precio_compra) as valor_compra,
                        SUM(stock_actual * precio_venta) as valor_venta,
                        SUM(stock_actual) as total_unidades,
                        COUNT(*) as total_productos
                    FROM productos 
                    WHERE activo = 1
                """
                params = None
            
            result = self.db.execute_single(query, params)
            
            return {
                'valor_compra': float(result.get('valor_compra', 0) or 0),
                'valor_venta': float(result.get('valor_venta', 0) or 0),
                'total_unidades': int(result.get('total_unidades', 0) or 0),
                'total_productos': int(result.get('total_productos', 0) or 0),
                'ganancia_potencial': float((result.get('valor_venta', 0) or 0) - (result.get('valor_compra', 0) or 0))
            }
            
        except Exception as e:
            logger.error(f"Error calculando valor de stock: {e}")
            return {
                'valor_compra': 0,
                'valor_venta': 0,
                'total_unidades': 0,
                'total_productos': 0,
                'ganancia_potencial': 0
            }
    
    def get_categories(self, active_only: bool = True) -> List[Dict]:
        """Obtener categorías de productos"""
        try:
            query = "SELECT * FROM categorias"
            
            if active_only:
                query += " WHERE activo = 1"
            
            query += " ORDER BY orden, nombre"
            
            return self.db.execute_query(query)
            
        except Exception as e:
            logger.error(f"Error obteniendo categorías: {e}")
            return []
    
    def create_category(self, name: str, description: str = None, 
                       parent_id: int = None, order: int = 0) -> Tuple[bool, str, int]:
        """Crear nueva categoría"""
        try:
            category_id = self.db.execute_insert("""
                INSERT INTO categorias (nombre, descripcion, categoria_padre_id, orden)
                VALUES (?, ?, ?, ?)
            """, (name, description, parent_id, order))
            
            logger.info(f"Categoría creada: {name} (ID: {category_id})")
            return True, f"Categoría '{name}' creada exitosamente", category_id
            
        except Exception as e:
            logger.error(f"Error creando categoría: {e}")
            return False, f"Error creando categoría: {str(e)}", 0
    
    def update_category(self, category_id: int, **kwargs) -> Tuple[bool, str]:
        """Actualizar categoría"""
        try:
            update_fields = []
            update_values = []
            
            allowed_fields = ['nombre', 'descripcion', 'categoria_padre_id', 'orden', 'activo']
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    update_fields.append(f"{field} = ?")
                    update_values.append(value)
            
            if not update_fields:
                return False, "No hay campos válidos para actualizar"
            
            update_fields.append("actualizado_en = CURRENT_TIMESTAMP")
            update_values.append(category_id)
            
            query = f"UPDATE categorias SET {', '.join(update_fields)} WHERE id = ?"
            
            rows_affected = self.db.execute_update(query, tuple(update_values))
            
            if rows_affected > 0:
                logger.info(f"Categoría actualizada: ID {category_id}")
                return True, "Categoría actualizada exitosamente"
            else:
                return False, "Categoría no encontrada"
                
        except Exception as e:
            logger.error(f"Error actualizando categoría: {e}")
            return False, f"Error actualizando categoría: {str(e)}"
    
    def delete_product(self, product_id: int, soft_delete: bool = True) -> Tuple[bool, str]:
        """Eliminar producto (lógico o físico)"""
        try:
            if soft_delete:
                # Eliminación lógica (marcar como inactivo)
                rows_affected = self.db.execute_update("""
                    UPDATE productos 
                    SET activo = 0, actualizado_en = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (product_id,))
                
                action = "desactivado"
            else:
                # Eliminación física (verificar que no tenga movimientos)
                movements = self.db.execute_single("""
                    SELECT COUNT(*) as count FROM movimientos_stock WHERE producto_id = ?
                """, (product_id,))
                
                if movements and movements['count'] > 0:
                    return False, "No se puede eliminar: el producto tiene movimientos de stock"
                
                rows_affected = self.db.execute_update("""
                    DELETE FROM productos WHERE id = ?
                """, (product_id,))
                
                action = "eliminado"
            
            if rows_affected > 0:
                logger.info(f"Producto {action}: ID {product_id}")
                return True, f"Producto {action} exitosamente"
            else:
                return False, "Producto no encontrado"
                
        except Exception as e:
            logger.error(f"Error eliminando producto: {e}")
            return False, f"Error eliminando producto: {str(e)}"
    
    def import_products_from_csv(self, csv_data: List[Dict], user_id: int = None) -> Tuple[bool, str, Dict]:
        """Importar productos desde datos CSV"""
        try:
            results = {
                'total': len(csv_data),
                'created': 0,
                'updated': 0,
                'errors': []
            }
            
            for i, row in enumerate(csv_data):
                try:
                    # Verificar si el producto ya existe por código de barras
                    existing_product = None
                    if row.get('codigo_barras'):
                        existing_product = self.get_product_by_barcode(row['codigo_barras'])
                    
                    if existing_product:
                        # Actualizar producto existente
                        success, message = self.update_product(existing_product['id'], row)
                        if success:
                            results['updated'] += 1
                        else:
                            results['errors'].append(f"Fila {i+1}: {message}")
                    else:
                        # Crear nuevo producto
                        success, message, product_id = self.create_product(row)
                        if success:
                            results['created'] += 1
                        else:
                            results['errors'].append(f"Fila {i+1}: {message}")
                            
                except Exception as e:
                    results['errors'].append(f"Fila {i+1}: Error procesando - {str(e)}")
            
            success_rate = (results['created'] + results['updated']) / results['total'] * 100
            
            logger.info(f"Importación completada: {results['created']} creados, {results['updated']} actualizados, {len(results['errors'])} errores")
            
            return True, f"Importación completada: {success_rate:.1f}% exitoso", results
            
        except Exception as e:
            logger.error(f"Error en importación de productos: {e}")
            return False, f"Error en importación: {str(e)}", {}
    
    def get_product_stats(self) -> Dict:
        """Obtener estadísticas de productos"""
        try:
            stats = {}
            
            # Contadores básicos
            basic_stats = self.db.execute_single("""
                SELECT 
                    COUNT(*) as total_productos,
                    COUNT(CASE WHEN activo = 1 THEN 1 END) as productos_activos,
                    COUNT(CASE WHEN stock_actual <= 0 THEN 1 END) as sin_stock,
                    COUNT(CASE WHEN stock_actual <= stock_minimo AND stock_actual > 0 THEN 1 END) as stock_bajo,
                    AVG(precio_venta) as precio_promedio,
                    SUM(stock_actual) as total_unidades_stock
                FROM productos
                WHERE activo = 1
            """)
            
            stats.update(basic_stats)
            
            # Productos por categoría
            category_stats = self.db.execute_query("""
                SELECT c.nombre, COUNT(p.id) as cantidad
                FROM categorias c
                LEFT JOIN productos p ON c.id = p.categoria_id AND p.activo = 1
                GROUP BY c.id, c.nombre
                ORDER BY cantidad DESC
            """)
            
            stats['por_categoria'] = category_stats
            
            # Valor del stock
            stock_value = self.calculate_stock_value()
            stats['valor_stock'] = stock_value
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de productos: {e}")
            return {}