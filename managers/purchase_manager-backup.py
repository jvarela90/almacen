"""
Gestor de Compras para AlmacénPro
Manejo completo de órdenes de compra, recepción de mercadería y gestión de proveedores
"""

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

class PurchaseManager:
    """Gestor principal para compras y órdenes de compra"""
    
    def __init__(self, db_manager, product_manager):
        self.db = db_manager
        self.product_manager = product_manager
        self.logger = logging.getLogger(__name__)
    
    def create_purchase_order(self, purchase_data: Dict, items: List[Dict], 
                             user_id: int) -> Tuple[bool, str, int]:
        """Crear nueva orden de compra"""
        try:
            # Validaciones básicas
            if not items:
                return False, "La orden debe tener al menos un producto", 0
            
            if not purchase_data.get('proveedor_id'):
                return False, "Debe seleccionar un proveedor", 0
            
            # Iniciar transacción
            self.db.begin_transaction()
            
            try:
                # Calcular totales
                subtotal = sum(item['cantidad'] * item['precio_unitario'] for item in items)
                descuento_total = purchase_data.get('descuento_importe', 0)
                impuestos_total = purchase_data.get('impuestos_importe', 0)
                total = subtotal - descuento_total + impuestos_total
                
                # Crear orden de compra
                purchase_id = self.db.execute_insert("""
                    INSERT INTO compras (
                        numero_orden, proveedor_id, usuario_id, fecha_compra,
                        fecha_factura, fecha_vencimiento, subtotal, descuento_importe,
                        impuestos_importe, total, estado, tipo_comprobante,
                        observaciones
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.generate_order_number(),
                    purchase_data['proveedor_id'],
                    user_id,
                    purchase_data.get('fecha_compra', datetime.now()),
                    purchase_data.get('fecha_factura'),
                    purchase_data.get('fecha_vencimiento'),
                    subtotal,
                    descuento_total,
                    impuestos_total,
                    total,
                    'ORDENADA',
                    purchase_data.get('tipo_comprobante', 'FACTURA'),
                    purchase_data.get('observaciones')
                ))
                
                if not purchase_id:
                    raise Exception("Error creando orden de compra")
                
                # Insertar detalles de la orden
                for item in items:
                    # Validar producto
                    product = self.product_manager.get_product_by_id(item['producto_id'])
                    if not product:
                        raise Exception(f"Producto ID {item['producto_id']} no encontrado")
                    
                    # Calcular subtotal del item
                    item_subtotal = item['cantidad'] * item['precio_unitario']
                    item_descuento = item.get('descuento_importe', 0)
                    item_iva = item.get('iva_importe', 0)
                    
                    detail_id = self.db.execute_insert("""
                        INSERT INTO detalle_compras (
                            compra_id, producto_id, cantidad, precio_unitario,
                            descuento_porcentaje, descuento_importe, subtotal,
                            iva_porcentaje, iva_importe, lote, fecha_vencimiento
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        purchase_id,
                        item['producto_id'],
                        item['cantidad'],
                        item['precio_unitario'],
                        item.get('descuento_porcentaje', 0),
                        item_descuento,
                        item_subtotal - item_descuento + item_iva,
                        item.get('iva_porcentaje', 21),
                        item_iva,
                        item.get('lote'),
                        item.get('fecha_vencimiento')
                    ))
                    
                    if not detail_id:
                        raise Exception(f"Error insertando detalle para producto {item['producto_id']}")
                
                # Confirmar transacción
                self.db.commit_transaction()
                
                self.logger.info(f"Orden de compra creada: ID {purchase_id}, Total: ${total}")
                return True, f"Orden de compra #{purchase_id} creada exitosamente", purchase_id
                
            except Exception as e:
                self.db.rollback_transaction()
                raise e
                
        except Exception as e:
            self.logger.error(f"Error creando orden de compra: {e}")
            return False, f"Error creando orden de compra: {str(e)}", 0
    
    def receive_merchandise(self, purchase_id: int, received_items: List[Dict], 
                           user_id: int) -> Tuple[bool, str]:
        """Procesar recepción de mercadería"""
        try:
            # Verificar que la orden existe
            purchase = self.get_purchase_by_id(purchase_id)
            if not purchase:
                return False, "Orden de compra no encontrada"
            
            if purchase['estado'] == 'CANCELADA':
                return False, "No se puede recibir mercadería de una orden cancelada"
            
            # Validar items recibidos
            if not received_items:
                return False, "Debe especificar los productos recibidos"
            
            # Iniciar transacción
            self.db.begin_transaction()
            
            try:
                errors = []
                total_received = 0
                
                for received_item in received_items:
                    producto_id = received_item.get('producto_id')
                    cantidad_recibida = float(received_item.get('cantidad_recibida', 0))
                    precio_unitario = received_item.get('precio_unitario')
                    lote = received_item.get('lote')
                    fecha_vencimiento = received_item.get('fecha_vencimiento')
                    
                    if cantidad_recibida <= 0:
                        continue
                    
                    try:
                        # Obtener detalle original de la orden
                        original_detail = self.db.execute_single("""
                            SELECT * FROM detalle_compras 
                            WHERE compra_id = ? AND producto_id = ?
                        """, (purchase_id, producto_id))
                        
                        if not original_detail:
                            errors.append(f"Producto ID {producto_id} no está en la orden original")
                            continue
                        
                        # Calcular cantidad total recibida
                        nueva_cantidad_recibida = original_detail['cantidad_recibida'] + cantidad_recibida
                        
                        # Validar que no se reciba más de lo ordenado
                        if nueva_cantidad_recibida > original_detail['cantidad']:
                            errors.append(f"Producto ID {producto_id}: cantidad recibida excede la ordenada")
                            continue
                        
                        # Actualizar detalle de compra
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
                        UPDATE compras SET estado = ?, fecha_recepcion = CURRENT_TIMESTAMP WHERE id = ?
                    """, (new_status, purchase_id))
                
                # Confirmar transacción
                self.db.commit_transaction()
                
                if errors:
                    error_msg = "; ".join(errors)
                    self.logger.warning(f"Errores en recepción: {error_msg}")
                    return False, f"Recepción parcial con errores: {error_msg}"
                
                self.logger.info(f"Mercadería recibida: Orden {purchase_id}, {total_received} unidades")
                return True, f"Mercadería recibida exitosamente. Estado: {new_status}"
                
            except Exception as e:
                self.db.rollback_transaction()
                raise e
                
        except Exception as e:
            self.logger.error(f"Error recibiendo mercadería: {e}")
            return False, f"Error recibiendo mercadería: {str(e)}"
    
    def get_purchase_by_id(self, purchase_id: int) -> Optional[Dict]:
        """Obtener orden de compra por ID"""
        try:
            # Obtener información principal
            purchase = self.db.execute_single("""
                SELECT c.*, p.nombre as proveedor_nombre, p.telefono as proveedor_telefono,
                       p.email as proveedor_email, u.nombre_completo as usuario_nombre
                FROM compras c
                LEFT JOIN proveedores p ON c.proveedor_id = p.id
                LEFT JOIN usuarios u ON c.usuario_id = u.id
                WHERE c.id = ?
            """, (purchase_id,))
            
            if not purchase:
                return None
            
            # Obtener detalles de la orden
            items = self.db.execute_query("""
                SELECT dc.*, pr.nombre as producto_nombre, pr.codigo_barras,
                       pr.unidad_medida, pr.stock_actual
                FROM detalle_compras dc
                LEFT JOIN productos pr ON dc.producto_id = pr.id
                WHERE dc.compra_id = ?
                ORDER BY pr.nombre
            """, (purchase_id,))
            
            purchase = dict(purchase)
            purchase['items'] = [dict(item) for item in items]
            
            return purchase
            
        except Exception as e:
            self.logger.error(f"Error obteniendo orden de compra: {e}")
            return None
    
    def get_purchases(self, status: str = None, provider_id: int = None,
                     date_from: date = None, date_to: date = None,
                     limit: int = 100) -> List[Dict]:
        """Obtener lista de órdenes de compra con filtros"""
        try:
            query = """
                SELECT c.*, p.nombre as proveedor_nombre, u.nombre_completo as usuario_nombre,
                       COUNT(dc.id) as total_items,
                       SUM(dc.cantidad) as total_productos,
                       SUM(dc.cantidad_recibida) as total_recibidos
                FROM compras c
                LEFT JOIN proveedores p ON c.proveedor_id = p.id
                LEFT JOIN usuarios u ON c.usuario_id = u.id
                LEFT JOIN detalle_compras dc ON c.id = dc.compra_id
                WHERE 1=1
            """
            params = []
            
            if status:
                query += " AND c.estado = ?"
                params.append(status)
            
            if provider_id:
                query += " AND c.proveedor_id = ?"
                params.append(provider_id)
            
            if date_from:
                query += " AND DATE(c.fecha_compra) >= ?"
                params.append(date_from)
            
            if date_to:
                query += " AND DATE(c.fecha_compra) <= ?"
                params.append(date_to)
            
            query += """
                GROUP BY c.id
                ORDER BY c.fecha_compra DESC
                LIMIT ?
            """
            params.append(limit)
            
            return self.db.execute_query(query, params)
            
        except Exception as e:
            self.logger.error(f"Error obteniendo órdenes de compra: {e}")
            return []
    
    def update_purchase_status(self, purchase_id: int, new_status: str, 
                              user_id: int, notes: str = None) -> Tuple[bool, str]:
        """Actualizar estado de orden de compra"""
        try:
            valid_statuses = ['ORDENADA', 'CONFIRMADA', 'PARCIAL', 'RECIBIDA', 'CANCELADA']
            if new_status not in valid_statuses:
                return False, f"Estado inválido. Estados válidos: {', '.join(valid_statuses)}"
            
            # Verificar que existe la orden
            purchase = self.get_purchase_by_id(purchase_id)
            if not purchase:
                return False, "Orden de compra no encontrada"
            
            if purchase['estado'] == new_status:
                return False, f"La orden ya está en estado {new_status}"
            
            # Validaciones específicas por estado
            if new_status == 'CANCELADA' and purchase['estado'] in ['PARCIAL', 'RECIBIDA']:
                return False, "No se puede cancelar una orden que ya tiene mercadería recibida"
            
            # Actualizar estado
            success = self.db.execute_update("""
                UPDATE compras 
                SET estado = ?, actualizado_en = CURRENT_TIMESTAMP,
                    observaciones = COALESCE(observaciones || '\n', '') || ?
                WHERE id = ?
            """, (
                new_status,
                f"Estado cambiado a {new_status} por usuario {user_id}" + (f": {notes}" if notes else ""),
                purchase_id
            ))
            
            if success:
                self.logger.info(f"Estado de compra actualizado: ID {purchase_id} -> {new_status}")
                return True, f"Estado actualizado a {new_status}"
            else:
                return False, "Error actualizando estado"
                
        except Exception as e:
            self.logger.error(f"Error actualizando estado de compra: {e}")
            return False, f"Error actualizando estado: {str(e)}"
    
    def cancel_purchase(self, purchase_id: int, user_id: int, reason: str = None) -> Tuple[bool, str]:
        """Cancelar orden de compra"""
        try:
            purchase = self.get_purchase_by_id(purchase_id)
            if not purchase:
                return False, "Orden de compra no encontrada"
            
            if purchase['estado'] == 'CANCELADA':
                return False, "La orden ya está cancelada"
            
            if purchase['estado'] in ['PARCIAL', 'RECIBIDA']:
                return False, "No se puede cancelar una orden con mercadería recibida"
            
            # Cancelar orden
            notes = f"Orden cancelada por usuario {user_id}"
            if reason:
                notes += f". Motivo: {reason}"
            
            return self.update_purchase_status(purchase_id, 'CANCELADA', user_id, notes)
            
        except Exception as e:
            self.logger.error(f"Error cancelando orden de compra: {e}")
            return False, f"Error cancelando orden: {str(e)}"
    
    def get_pending_orders(self) -> List[Dict]:
        """Obtener órdenes pendientes de recibir"""
        try:
            return self.get_purchases(status='ORDENADA') + self.get_purchases(status='CONFIRMADA')
        except Exception as e:
            self.logger.error(f"Error obteniendo órdenes pendientes: {e}")
            return []
    
    def get_partial_orders(self) -> List[Dict]:
        """Obtener órdenes parcialmente recibidas"""
        try:
            return self.get_purchases(status='PARCIAL')
        except Exception as e:
            self.logger.error(f"Error obteniendo órdenes parciales: {e}")
            return []
    
    def get_purchase_statistics(self, date_from: date = None, date_to: date = None) -> Dict:
        """Obtener estadísticas de compras"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_ordenes,
                    SUM(CASE WHEN estado = 'ORDENADA' THEN 1 ELSE 0 END) as ordenes_pendientes,
                    SUM(CASE WHEN estado = 'PARCIAL' THEN 1 ELSE 0 END) as ordenes_parciales,
                    SUM(CASE WHEN estado = 'RECIBIDA' THEN 1 ELSE 0 END) as ordenes_completas,
                    SUM(CASE WHEN estado = 'CANCELADA' THEN 1 ELSE 0 END) as ordenes_canceladas,
                    SUM(total) as monto_total,
                    AVG(total) as monto_promedio,
                    COUNT(DISTINCT proveedor_id) as proveedores_activos
                FROM compras
                WHERE 1=1
            """
            params = []
            
            if date_from:
                query += " AND DATE(fecha_compra) >= ?"
                params.append(date_from)
            
            if date_to:
                query += " AND DATE(fecha_compra) <= ?"
                params.append(date_to)
            
            result = self.db.execute_single(query, params)
            
            if result:
                return {
                    'total_ordenes': result['total_ordenes'] or 0,
                    'ordenes_pendientes': result['ordenes_pendientes'] or 0,
                    'ordenes_parciales': result['ordenes_parciales'] or 0,
                    'ordenes_completas': result['ordenes_completas'] or 0,
                    'ordenes_canceladas': result['ordenes_canceladas'] or 0,
                    'monto_total': float(result['monto_total'] or 0),
                    'monto_promedio': float(result['monto_promedio'] or 0),
                    'proveedores_activos': result['proveedores_activos'] or 0
                }
            else:
                return {
                    'total_ordenes': 0,
                    'ordenes_pendientes': 0,
                    'ordenes_parciales': 0,
                    'ordenes_completas': 0,
                    'ordenes_canceladas': 0,
                    'monto_total': 0.0,
                    'monto_promedio': 0.0,
                    'proveedores_activos': 0
                }
                
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas de compras: {e}")
            return {}
    
    def get_top_suppliers(self, limit: int = 10, date_from: date = None, 
                         date_to: date = None) -> List[Dict]:
        """Obtener top proveedores por volumen de compras"""
        try:
            query = """
                SELECT p.id, p.nombre, p.telefono, p.email,
                       COUNT(c.id) as total_ordenes,
                       SUM(c.total) as monto_total,
                       AVG(c.total) as monto_promedio,
                       MAX(c.fecha_compra) as ultima_compra
                FROM proveedores p
                LEFT JOIN compras c ON p.id = c.proveedor_id AND c.estado != 'CANCELADA'
                WHERE 1=1
            """
            params = []
            
            if date_from:
                query += " AND DATE(c.fecha_compra) >= ?"
                params.append(date_from)
            
            if date_to:
                query += " AND DATE(c.fecha_compra) <= ?"
                params.append(date_to)
            
            query += """
                GROUP BY p.id, p.nombre, p.telefono, p.email
                HAVING COUNT(c.id) > 0
                ORDER BY monto_total DESC
                LIMIT ?
            """
            params.append(limit)
            
            return self.db.execute_query(query, params)
            
        except Exception as e:
            self.logger.error(f"Error obteniendo top proveedores: {e}")
            return []
    
    def generate_order_number(self) -> str:
        """Generar número de orden único"""
        try:
            # Obtener el siguiente número secuencial para hoy
            today = datetime.now().strftime('%Y%m%d')
            
            result = self.db.execute_single("""
                SELECT COALESCE(MAX(CAST(SUBSTR(numero_orden, -4) AS INTEGER)), 0) + 1 as next_num
                FROM compras 
                WHERE numero_orden LIKE ?
            """, (f"ORD{today}%",))
            
            if result and result['next_num']:
                next_num = result['next_num']
            else:
                next_num = 1
            
            return f"ORD{today}{next_num:04d}"
            
        except Exception as e:
            self.logger.error(f"Error generando número de orden: {e}")
            return f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def duplicate_purchase_order(self, purchase_id: int, user_id: int) -> Tuple[bool, str, int]:
        """Duplicar orden de compra existente"""
        try:
            # Obtener orden original
            original_purchase = self.get_purchase_by_id(purchase_id)
            if not original_purchase:
                return False, "Orden original no encontrada", 0
            
            # Preparar datos para nueva orden
            new_purchase_data = {
                'proveedor_id': original_purchase['proveedor_id'],
                'tipo_comprobante': original_purchase['tipo_comprobante'],
                'observaciones': f"Duplicada de orden #{purchase_id}"
            }
            
            # Preparar items
            new_items = []
            for item in original_purchase['items']:
                new_items.append({
                    'producto_id': item['producto_id'],
                    'cantidad': item['cantidad'],
                    'precio_unitario': item['precio_unitario'],
                    'descuento_porcentaje': item['descuento_porcentaje'],
                    'descuento_importe': item['descuento_importe'],
                    'iva_porcentaje': item['iva_porcentaje'],
                    'iva_importe': item['iva_importe']
                })
            
            # Crear nueva orden
            return self.create_purchase_order(new_purchase_data, new_items, user_id)
            
        except Exception as e:
            self.logger.error(f"Error duplicando orden de compra: {e}")
            return False, f"Error duplicando orden: {str(e)}", 0
    
    def delete_purchase_order(self, purchase_id: int, user_id: int) -> Tuple[bool, str]:
        """Eliminar orden de compra (solo si no tiene movimientos)"""
        try:
            purchase = self.get_purchase_by_id(purchase_id)
            if not purchase:
                return False, "Orden de compra no encontrada"
            
            # Solo permitir eliminar órdenes sin mercadería recibida
            total_received = sum(item['cantidad_recibida'] for item in purchase['items'])
            if total_received > 0:
                return False, "No se puede eliminar una orden con mercadería recibida"
            
            # Iniciar transacción
            self.db.begin_transaction()
            
            try:
                # Eliminar detalles
                self.db.execute_update("DELETE FROM detalle_compras WHERE compra_id = ?", (purchase_id,))
                
                # Eliminar compra principal
                success = self.db.execute_update("DELETE FROM compras WHERE id = ?", (purchase_id,))
                
                if not success:
                    raise Exception("Error eliminando orden de compra")
                
                # Confirmar transacción
                self.db.commit_transaction()
                
                self.logger.info(f"Orden de compra eliminada: ID {purchase_id}")
                return True, "Orden de compra eliminada exitosamente"
                
            except Exception as e:
                self.db.rollback_transaction()
                raise e
                
        except Exception as e:
            self.logger.error(f"Error eliminando orden de compra: {e}")
            return False, f"Error eliminando orden: {str(e)}"