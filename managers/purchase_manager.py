"""
Gestor de Compras para AlmacénPro
Maneja órdenes de compra, recepción de mercadería y relaciones con proveedores
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from datetime import datetime, date

logger = logging.getLogger(__name__)

class PurchaseManager:
    """Gestor de compras y órdenes"""
    
    def __init__(self, db_manager, product_manager):
        self.db = db_manager
        self.product_manager = product_manager
        logger.info("PurchaseManager inicializado")
    
    def create_purchase_order(self, purchase_data: Dict) -> Tuple[bool, str, int]:
        """Crear nueva orden de compra"""
        try:
            # Validaciones básicas
            if not purchase_data.get('items') or len(purchase_data['items']) == 0:
                return False, "La orden debe tener al menos un producto", 0
            
            if not purchase_data.get('proveedor_id'):
                return False, "Debe especificar el proveedor", 0
            
            if not purchase_data.get('usuario_id'):
                return False, "Debe especificar el usuario", 0
            
            # Validar productos
            for item in purchase_data['items']:
                if not item.get('producto_id') or not item.get('cantidad') or not item.get('precio_unitario'):
                    return False, "Todos los productos deben tener ID, cantidad y precio", 0
                
                if item['cantidad'] <= 0 or item['precio_unitario'] <= 0:
                    return False, "La cantidad y precio deben ser mayores a cero", 0
            
            # Calcular totales
            subtotal = sum(
                Decimal(str(item['cantidad'])) * Decimal(str(item['precio_unitario']))
                for item in purchase_data['items']
            )
            
            descuento_total = Decimal(str(purchase_data.get('descuento', 0)))
            recargo_total = Decimal(str(purchase_data.get('recargo', 0)))
            
            # Calcular impuestos (IVA)
            base_imponible = subtotal - descuento_total + recargo_total
            impuestos = base_imponible * Decimal('0.21')  # IVA 21% por defecto
            
            total = base_imponible + impuestos
            
            # Crear orden de compra
            purchase_id = self.db.execute_insert("""
                INSERT INTO compras (
                    numero_factura, numero_remito, proveedor_id, usuario_id,
                    subtotal, descuento, recargo, impuestos, total,
                    fecha_factura, fecha_vencimiento, estado, tipo_comprobante,
                    observaciones
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                purchase_data.get('numero_factura'),
                purchase_data.get('numero_remito'),
                purchase_data['proveedor_id'],
                purchase_data['usuario_id'],
                float(subtotal),
                float(descuento_total),
                float(recargo_total),
                float(impuestos),
                float(total),
                purchase_data.get('fecha_factura'),
                purchase_data.get('fecha_vencimiento'),
                purchase_data.get('estado', 'PENDIENTE'),
                purchase_data.get('tipo_comprobante', 'FACTURA'),
                purchase_data.get('observaciones')
            ))
            
            # Crear detalles de compra
            for item in purchase_data['items']:
                item_subtotal = (
                    Decimal(str(item['cantidad'])) * 
                    Decimal(str(item['precio_unitario']))
                )
                
                item_discount = item_subtotal * (Decimal(str(item.get('descuento_porcentaje', 0))) / 100)
                item_final = item_subtotal - item_discount
                
                # Calcular IVA del item
                iva_porcentaje = Decimal(str(item.get('iva_porcentaje', 21)))
                iva_importe = item_final * (iva_porcentaje / 100)
                
                self.db.execute_insert("""
                    INSERT INTO detalle_compras (
                        compra_id, producto_id, cantidad, cantidad_recibida,
                        precio_unitario, descuento_porcentaje, descuento_importe,
                        subtotal, iva_porcentaje, iva_importe, lote, fecha_vencimiento
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    purchase_id,
                    item['producto_id'],
                    item['cantidad'],
                    0,  # cantidad_recibida inicial
                    item['precio_unitario'],
                    item.get('descuento_porcentaje', 0),
                    float(item_discount),
                    float(item_final),
                    float(iva_porcentaje),
                    float(iva_importe),
                    item.get('lote'),
                    item.get('fecha_vencimiento')
                ))
            
            logger.info(f"Orden de compra creada: ID {purchase_id} por ${total}")
            return True, f"Orden de compra #{purchase_id} creada exitosamente", purchase_id
            
        except Exception as e:
            logger.error(f"Error creando orden de compra: {e}")
            return False, f"Error creando orden: {str(e)}", 0
    
    def get_purchase_by_id(self, purchase_id: int) -> Optional[Dict]:
        """Obtener orden de compra por ID con detalles"""
        try:
            # Obtener compra principal
            purchase = self.db.execute_single("""
                SELECT c.*, 
                       p.nombre as proveedor_nombre, p.cuit_dni as proveedor_cuit,
                       u.nombre_completo as usuario_nombre
                FROM compras c
                LEFT JOIN proveedores p ON c.proveedor_id = p.id
                LEFT JOIN usuarios u ON c.usuario_id = u.id
                WHERE c.id = ?
            """, (purchase_id,))
            
            if not purchase:
                return None
            
            # Obtener detalles
            details = self.db.execute_query("""
                SELECT dc.*, p.nombre as producto_nombre, p.codigo_barras, p.unidad_medida
                FROM detalle_compras dc
                JOIN productos p ON dc.producto_id = p.id
                WHERE dc.compra_id = ?
                ORDER BY dc.id
            """, (purchase_id,))
            
            purchase_dict = dict(purchase)
            purchase_dict['items'] = details
            
            return purchase_dict
            
        except Exception as e:
            logger.error(f"Error obteniendo orden de compra: {e}")
            return None
    
    def get_purchases_by_status(self, status: str = None, proveedor_id: int = None) -> List[Dict]:
        """Obtener órdenes de compra por estado"""
        try:
            query = """
                SELECT c.*, 
                       p.nombre as proveedor_nombre,
                       u.nombre_completo as usuario_nombre
                FROM compras c
                LEFT JOIN proveedores p ON c.proveedor_id = p.id
                LEFT JOIN usuarios u ON c.usuario_id = u.id
            """
            
            conditions = []
            params = []
            
            if status:
                conditions.append("c.estado = ?")
                params.append(status)
            
            if proveedor_id:
                conditions.append("c.proveedor_id = ?")
                params.append(proveedor_id)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY c.fecha_compra DESC"
            
            return self.db.execute_query(query, tuple(params) if params else None)
            
        except Exception as e:
            logger.error(f"Error obteniendo órdenes por estado: {e}")
            return []
    
    def receive_merchandise(self, purchase_id: int, received_items: List[Dict], 
                          user_id: int) -> Tuple[bool, str]:
        """Recibir mercadería y actualizar stock"""
        try:
            # Verificar que la orden existe
            purchase = self.get_purchase_by_id(purchase_id)
            if not purchase:
                return False, "Orden de compra no encontrada"
            
            if purchase['estado'] == 'RECIBIDA':
                return False, "Esta orden ya fue recibida completamente"
            
            if purchase['estado'] == 'CANCELADA':
                return False, "No se puede recibir una orden cancelada"
            
            total_received = 0
            errors = []
            
            # Procesar cada item recibido
            for received_item in received_items:
                try:
                    producto_id = received_item['producto_id']
                    cantidad_recibida = received_item['cantidad_recibida']
                    precio_unitario = received_item.get('precio_unitario')
                    lote = received_item.get('lote')
                    fecha_vencimiento = received_item.get('fecha_vencimiento')
                    
                    if cantidad_recibida <= 0:
                        continue
                    
                    # Buscar el detalle original
                    original_detail = None
                    for item in purchase['items']:
                        if item['producto_id'] == producto_id:
                            original_detail = item
                            break
                    
                    if not original_detail:
                        errors.append(f"Producto ID {producto_id} no encontrado en la orden")
                        continue
                    
                    # Verificar que no se exceda la cantidad pedida
                    cantidad_ya_recibida = original_detail['cantidad_recibida']
                    cantidad_pendiente = original_detail['cantidad'] - cantidad_ya_recibida
                    
                    if cantidad_recibida > cantidad_pendiente:
                        errors.append(f"Cantidad excedida para producto {original_detail['producto_nombre']}")
                        continue
                    
                    # Actualizar cantidad recibida en detalle_compras
                    nueva_cantidad_recibida = cantidad_ya_recibida + cantidad_recibida
                    
                    self.db.execute_update("""
                        UPDATE detalle_compras 
                        SET cantidad_recibida = ?, lote = ?, fecha_vencimiento = ?
                        WHERE compra_id = ? AND producto_id = ?
                    """, (
                        nueva_cantidad_recibida, lote, fecha_vencimiento,
                        purchase_id, producto_id
                    ))
                    
                    # Actualizar stock del producto
                    success, message = self.product_manager.update_stock(
                        product_id=producto_id,
                        new_quantity=cantidad_recibida,
                        movement_type='ENTRADA',
                        reason='COMPRA',
                        user_id=user_id,
                        unit_price=precio_unitario or original_detail['precio_unitario'],
                        reference_id=purchase_id,
                        reference_type='COMPRA',
                        notes=f"Compra #{purchase_id} - Lote: {lote or 'N/A'}"
                    )
                    
                    if not success:
                        errors.append(f"Error actualizando stock: {message}")
                        continue
                    
                    # Actualizar precio de compra del producto si cambió
                    if precio_unitario and precio_unitario != original_detail['precio_unitario']:
                        self.db.execute_update("""
                            UPDATE productos 
                            SET precio_compra = ?, actualizado_en = CURRENT_TIMESTAMP 
                            WHERE id = ?
                        """, (precio_unitario, producto_id))
                    
                    total_received += cantidad_recibida
                    
                except Exception as e:
                    errors.append(f"Error procesando producto ID {received_item.get('producto_id', 'N/A')}: {str(e)}")
            
            # Verificar si la orden está completamente recibida
            all_items_received = True
            for item in purchase['items']:
                if item['cantidad_recibida'] < item['cantidad']:
                    all_items_received = False
                    break
            
            # Actualizar estado de la orden
            if all_items_received:
                new_status = 'RECIBIDA'
            elif total_received > 0:
                new_status = 'PARCIAL'
            else:
                new_status = purchase['estado']  # Mantener estado actual
            
            if new_status != purchase['estado']:
                self.db.execute_update("""
                    UPDATE compras SET estado = ? WHERE id = ?
                """, (new_status, purchase_id))
            
            if errors:
                error_msg = "; ".join(errors)
                logger.warning(f"Errores en recepción: {error_msg}")
                return False, f"Recepción parcial con errores: {error_msg}"
            
            logger.info(f"Mercadería recibida: Orden {purchase_id}, {total_received} unidades")
            return True, f"Mercadería recibida exitosamente. Total: {total_received} unidades"
            
        except Exception as e:
            logger.error(f"Error recibiendo mercadería: {e}")
            return False, f"Error recibiendo mercadería: {str(e)}"
    
    def update_purchase_status(self, purchase_id: int, new_status: str, 
                             user_id: int, notes: str = None) -> Tuple[bool, str]:
        """Actualizar estado de orden de compra"""
        try:
            valid_statuses = ['PENDIENTE', 'CONFIRMADA', 'PARCIAL', 'RECIBIDA', 'CANCELADA']
            
            if new_status not in valid_statuses:
                return False, f"Estado inválido. Estados válidos: {', '.join(valid_statuses)}"
            
            # Actualizar estado
            rows_affected = self.db.execute_update("""
                UPDATE compras 
                SET estado = ?, observaciones = COALESCE(observaciones || '\n', '') || ?
                WHERE id = ?
            """, (new_status, notes or f"Estado cambiado a {new_status}", purchase_id))
            
            if rows_affected > 0:
                logger.info(f"Estado de compra actualizado: ID {purchase_id} -> {new_status}")
                return True, f"Estado actualizado a {new_status}"
            else:
                return False, "Orden de compra no encontrada"
                
        except Exception as e:
            logger.error(f"Error actualizando estado de compra: {e}")
            return False, f"Error actualizando estado: {str(e)}"
    
    def cancel_purchase_order(self, purchase_id: int, user_id: int, reason: str) -> Tuple[bool, str]:
        """Cancelar orden de compra"""
        try:
            purchase = self.get_purchase_by_id(purchase_id)
            if not purchase:
                return False, "Orden de compra no encontrada"
            
            if purchase['estado'] == 'RECIBIDA':
                return False, "No se puede cancelar una orden ya recibida"
            
            if purchase['estado'] == 'CANCELADA':
                return False, "La orden ya está cancelada"
            
            # Si hay mercadería parcialmente recibida, revertir stock
            if purchase['estado'] == 'PARCIAL':
                for item in purchase['items']:
                    if item['cantidad_recibida'] > 0:
                        success, message = self.product_manager.update_stock(
                            product_id=item['producto_id'],
                            new_quantity=item['cantidad_recibida'],
                            movement_type='SALIDA',
                            reason='CANCELACION_COMPRA',
                            user_id=user_id,
                            unit_price=item['precio_unitario'],
                            reference_id=purchase_id,
                            reference_type='CANCELACION',
                            notes=f"Cancelación compra #{purchase_id}: {reason}"
                        )
                        
                        if not success:
                            logger.warning(f"Error revirtiendo stock al cancelar: {message}")
            
            # Actualizar estado a cancelada
            self.db.execute_update("""
                UPDATE compras 
                SET estado = 'CANCELADA', 
                    observaciones = COALESCE(observaciones || '\n', '') || ?
                WHERE id = ?
            """, (f"CANCELADA: {reason}", purchase_id))
            
            logger.info(f"Orden de compra cancelada: ID {purchase_id}")
            return True, f"Orden #{purchase_id} cancelada exitosamente"
            
        except Exception as e:
            logger.error(f"Error cancelando orden: {e}")
            return False, f"Error cancelando orden: {str(e)}"
    
    def get_pending_purchases(self, days_old: int = None) -> List[Dict]:
        """Obtener compras pendientes"""
        try:
            query = """
                SELECT c.*, 
                       p.nombre as proveedor_nombre, p.telefono as proveedor_telefono,
                       u.nombre_completo as usuario_nombre,
                       JULIANDAY('now') - JULIANDAY(c.fecha_compra) as dias_pendiente
                FROM compras c
                LEFT JOIN proveedores p ON c.proveedor_id = p.id
                LEFT JOIN usuarios u ON c.usuario_id = u.id
                WHERE c.estado IN ('PENDIENTE', 'CONFIRMADA', 'PARCIAL')
            """
            
            params = []
            if days_old:
                query += " AND JULIANDAY('now') - JULIANDAY(c.fecha_compra) >= ?"
                params.append(days_old)
            
            query += " ORDER BY c.fecha_compra ASC"
            
            return self.db.execute_query(query, tuple(params) if params else None)
            
        except Exception as e:
            logger.error(f"Error obteniendo compras pendientes: {e}")
            return []
    
    def get_overdue_purchases(self) -> List[Dict]:
        """Obtener compras vencidas"""
        try:
            return self.db.execute_query("""
                SELECT c.*, 
                       p.nombre as proveedor_nombre, p.telefono as proveedor_telefono,
                       JULIANDAY('now') - JULIANDAY(c.fecha_vencimiento) as dias_vencido
                FROM compras c
                LEFT JOIN proveedores p ON c.proveedor_id = p.id
                WHERE c.estado IN ('PENDIENTE', 'CONFIRMADA', 'PARCIAL')
                AND c.fecha_vencimiento < DATE('now')
                ORDER BY c.fecha_vencimiento ASC
            """)
            
        except Exception as e:
            logger.error(f"Error obteniendo compras vencidas: {e}")
            return []
    
    def get_purchase_statistics(self, start_date: str, end_date: str) -> Dict:
        """Obtener estadísticas de compras"""
        try:
            # Estadísticas generales
            general_stats = self.db.execute_single("""
                SELECT 
                    COUNT(*) as total_compras,
                    SUM(total) as total_comprado,
                    AVG(total) as compra_promedio,
                    COUNT(DISTINCT proveedor_id) as proveedores_activos,
                    SUM(CASE WHEN estado = 'RECIBIDA' THEN 1 ELSE 0 END) as compras_recibidas,
                    SUM(CASE WHEN estado = 'PENDIENTE' THEN 1 ELSE 0 END) as compras_pendientes
                FROM compras 
                WHERE DATE(fecha_compra) BETWEEN ? AND ?
            """, (start_date, end_date))
            
            # Compras por proveedor
            by_provider = self.db.execute_query("""
                SELECT 
                    p.nombre,
                    COUNT(c.id) as cantidad_ordenes,
                    SUM(c.total) as total_comprado,
                    AVG(c.total) as promedio_orden
                FROM compras c
                JOIN proveedores p ON c.proveedor_id = p.id
                WHERE DATE(c.fecha_compra) BETWEEN ? AND ?
                GROUP BY c.proveedor_id, p.nombre
                ORDER BY total_comprado DESC
                LIMIT 10
            """, (start_date, end_date))
            
            # Compras por estado
            by_status = self.db.execute_query("""
                SELECT 
                    estado,
                    COUNT(*) as cantidad,
                    SUM(total) as total
                FROM compras 
                WHERE DATE(fecha_compra) BETWEEN ? AND ?
                GROUP BY estado
                ORDER BY cantidad DESC
            """, (start_date, end_date))
            
            # Productos más comprados
            top_products = self.db.execute_query("""
                SELECT 
                    p.nombre,
                    SUM(dc.cantidad) as cantidad_comprada,
                    SUM(dc.subtotal) as total_gastado
                FROM detalle_compras dc
                JOIN productos p ON dc.producto_id = p.id
                JOIN compras c ON dc.compra_id = c.id
                WHERE DATE(c.fecha_compra) BETWEEN ? AND ?
                GROUP BY p.id, p.nombre
                ORDER BY cantidad_comprada DESC
                LIMIT 10
            """, (start_date, end_date))
            
            return {
                'periodo': {'inicio': start_date, 'fin': end_date},
                'resumen_general': dict(general_stats) if general_stats else {},
                'por_proveedor': by_provider,
                'por_estado': by_status,
                'productos_mas_comprados': top_products
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de compras: {e}")
            return {}
    
    def get_cost_analysis(self, product_id: int = None, start_date: str = None, 
                         end_date: str = None) -> Dict:
        """Análisis de costos de productos"""
        try:
            base_query = """
                SELECT 
                    p.nombre as producto,
                    p.codigo_barras,
                    AVG(dc.precio_unitario) as precio_promedio,
                    MIN(dc.precio_unitario) as precio_minimo,
                    MAX(dc.precio_unitario) as precio_maximo,
                    SUM(dc.cantidad) as cantidad_total_comprada,
                    SUM(dc.subtotal) as costo_total,
                    COUNT(DISTINCT c.proveedor_id) as proveedores_distintos
                FROM detalle_compras dc
                JOIN productos p ON dc.producto_id = p.id
                JOIN compras c ON dc.compra_id = c.id
                WHERE c.estado != 'CANCELADA'
            """
            
            params = []
            
            if product_id:
                base_query += " AND p.id = ?"
                params.append(product_id)
            
            if start_date and end_date:
                base_query += " AND DATE(c.fecha_compra) BETWEEN ? AND ?"
                params.extend([start_date, end_date])
            
            if product_id:
                # Análisis detallado para un producto específico
                base_query += " GROUP BY p.id, p.nombre, p.codigo_barras"
                
                result = self.db.execute_single(base_query, tuple(params))
                
                if result:
                    # Historial de precios
                    price_history = self.db.execute_query("""
                        SELECT 
                            c.fecha_compra,
                            dc.precio_unitario,
                            dc.cantidad,
                            pr.nombre as proveedor
                        FROM detalle_compras dc
                        JOIN compras c ON dc.compra_id = c.id
                        JOIN proveedores pr ON c.proveedor_id = pr.id
                        WHERE dc.producto_id = ? AND c.estado != 'CANCELADA'
                        ORDER BY c.fecha_compra DESC
                        LIMIT 20
                    """, (product_id,))
                    
                    return {
                        'producto': dict(result),
                        'historial_precios': price_history
                    }
            else:
                # Análisis general por producto
                base_query += " GROUP BY p.id, p.nombre, p.codigo_barras ORDER BY costo_total DESC LIMIT 50"
                
                products = self.db.execute_query(base_query, tuple(params))
                
                return {
                    'productos': products,
                    'total_productos': len(products)
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error en análisis de costos: {e}")
            return {}
    
    def suggest_reorder_products(self, days_without_purchase: int = 30) -> List[Dict]:
        """Sugerir productos para reordenar"""
        try:
            return self.db.execute_query("""
                SELECT 
                    p.id,
                    p.nombre,
                    p.codigo_barras,
                    p.stock_actual,
                    p.stock_minimo,
                    p.precio_compra,
                    pr.nombre as proveedor_principal,
                    pr.id as proveedor_id,
                    COALESCE(last_purchase.dias_sin_compra, 999) as dias_sin_compra,
                    COALESCE(avg_consumption.consumo_promedio_diario, 0) as consumo_promedio_diario,
                    COALESCE(suggested.cantidad_sugerida, p.stock_minimo * 2) as cantidad_sugerida
                FROM productos p
                LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
                LEFT JOIN (
                    SELECT 
                        dc.producto_id,
                        JULIANDAY('now') - JULIANDAY(MAX(c.fecha_compra)) as dias_sin_compra
                    FROM detalle_compras dc
                    JOIN compras c ON dc.compra_id = c.id
                    WHERE c.estado != 'CANCELADA'
                    GROUP BY dc.producto_id
                ) last_purchase ON p.id = last_purchase.producto_id
                LEFT JOIN (
                    SELECT 
                        dv.producto_id,
                        AVG(dv.cantidad) as consumo_promedio_diario
                    FROM detalle_ventas dv
                    JOIN ventas v ON dv.venta_id = v.id
                    WHERE DATE(v.fecha_venta) >= DATE('now', '-30 days')
                    AND v.estado = 'COMPLETADA'
                    GROUP BY dv.producto_id
                ) avg_consumption ON p.id = avg_consumption.producto_id
                LEFT JOIN (
                    SELECT 
                        producto_id,
                        AVG(cantidad) * 1.5 as cantidad_sugerida
                    FROM detalle_compras dc
                    JOIN compras c ON dc.compra_id = c.id
                    WHERE c.estado != 'CANCELADA'
                    AND DATE(c.fecha_compra) >= DATE('now', '-90 days')
                    GROUP BY producto_id
                ) suggested ON p.id = suggested.producto_id
                WHERE p.activo = 1
                AND (
                    p.stock_actual <= p.stock_minimo
                    OR COALESCE(last_purchase.dias_sin_compra, 999) >= ?
                )
                ORDER BY 
                    CASE WHEN p.stock_actual <= 0 THEN 1 ELSE 2 END,
                    p.stock_actual - p.stock_minimo ASC,
                    last_purchase.dias_sin_compra DESC
                LIMIT 100
            """, (days_without_purchase,))
            
        except Exception as e:
            logger.error(f"Error sugiriendo reorden: {e}")
            return []
    
    def create_purchase_from_suggestions(self, suggestions: List[Dict], 
                                       proveedor_id: int, user_id: int) -> Tuple[bool, str, int]:
        """Crear orden de compra desde sugerencias"""
        try:
            if not suggestions:
                return False, "No hay productos sugeridos", 0
            
            # Filtrar solo productos del proveedor seleccionado
            filtered_items = []
            for suggestion in suggestions:
                if suggestion.get('proveedor_id') == proveedor_id:
                    filtered_items.append({
                        'producto_id': suggestion['id'],
                        'cantidad': suggestion.get('cantidad_sugerida', suggestion.get('stock_minimo', 1)),
                        'precio_unitario': suggestion.get('precio_compra', 0)
                    })
            
            if not filtered_items:
                return False, "No hay productos del proveedor seleccionado", 0
            
            # Crear orden de compra
            purchase_data = {
                'proveedor_id': proveedor_id,
                'usuario_id': user_id,
                'items': filtered_items,
                'observaciones': 'Orden generada automáticamente por sugerencias de reorden'
            }
            
            return self.create_purchase_order(purchase_data)
            
        except Exception as e:
            logger.error(f"Error creando orden desde sugerencias: {e}")
            return False, f"Error creando orden: {str(e)}", 0