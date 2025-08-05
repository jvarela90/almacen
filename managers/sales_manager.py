"""
Gestor de Ventas para AlmacénPro
Sistema completo de punto de venta (POS) con facturación y gestión de clientes
"""

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
import uuid

logger = logging.getLogger(__name__)

class SalesManager:
    """Gestor principal para ventas y facturación"""
    
    def __init__(self, db_manager, product_manager):
        self.db = db_manager
        self.product_manager = product_manager
        self.logger = logging.getLogger(__name__)
        
        # Estados válidos de venta
        self.VALID_STATUSES = ['ACTIVA', 'COMPLETADA', 'CANCELADA', 'DEVUELTA']
        
        # Métodos de pago válidos
        self.PAYMENT_METHODS = [
            'EFECTIVO', 'TARJETA_DEBITO', 'TARJETA_CREDITO', 
            'TRANSFERENCIA', 'CHEQUE', 'CUENTA_CORRIENTE'
        ]
    
    def create_sale(self, sale_data: Dict, items: List[Dict], 
                   payments: List[Dict], user_id: int) -> Tuple[bool, str, int]:
        """Crear nueva venta"""
        try:
            # Validaciones básicas
            if not items:
                return False, "La venta debe tener al menos un producto", 0
            
            if not payments:
                return False, "La venta debe tener al menos un método de pago", 0
            
            # Validar stock de productos
            stock_errors = []
            for item in items:
                product = self.product_manager.get_product_by_id(item['producto_id'])
                if not product:
                    stock_errors.append(f"Producto ID {item['producto_id']} no encontrado")
                    continue
                
                if not product.get('permite_venta_sin_stock', False):
                    if product['stock_actual'] < item['cantidad']:
                        stock_errors.append(f"{product['nombre']}: stock insuficiente ({product['stock_actual']} disponible)")
            
            if stock_errors:
                return False, "; ".join(stock_errors), 0
            
            # Iniciar transacción
            self.db.begin_transaction()
            
            try:
                # Calcular totales
                subtotal = sum(item['cantidad'] * item['precio_unitario'] for item in items)
                descuento_total = sale_data.get('descuento_importe', 0)
                impuestos_total = sum(item.get('impuesto_importe', 0) for item in items)
                total = subtotal - descuento_total + impuestos_total
                
                # Validar que los pagos cubran el total
                total_pagos = sum(payment['importe'] for payment in payments)
                if abs(total_pagos - total) > 0.01:  # Tolerancia para redondeo
                    raise Exception(f"Los pagos ({total_pagos}) no coinciden con el total ({total})")
                
                # Crear venta
                sale_id = self.db.execute_insert("""
                    INSERT INTO ventas (
                        numero_factura, tipo_comprobante, cliente_id, usuario_id,
                        fecha_venta, subtotal, descuento_porcentaje, descuento_importe,
                        impuestos_importe, total, estado, observaciones, caja_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.generate_invoice_number(),
                    sale_data.get('tipo_comprobante', 'TICKET'),
                    sale_data.get('cliente_id'),
                    user_id,
                    sale_data.get('fecha_venta', datetime.now()),
                    subtotal,
                    sale_data.get('descuento_porcentaje', 0),
                    descuento_total,
                    impuestos_total,
                    total,
                    'ACTIVA',
                    sale_data.get('observaciones'),
                    sale_data.get('caja_id')
                ))
                
                if not sale_id:
                    raise Exception("Error creando venta")
                
                # Insertar detalles de la venta
                for item in items:
                    product = self.product_manager.get_product_by_id(item['producto_id'])
                    
                    # Calcular impuesto del item
                    item_subtotal = item['cantidad'] * item['precio_unitario']
                    item_descuento = item.get('descuento_importe', 0)
                    item_impuesto = item.get('impuesto_importe', 0)
                    item_total = item_subtotal - item_descuento + item_impuesto
                    
                    detail_id = self.db.execute_insert("""
                        INSERT INTO detalle_ventas (
                            venta_id, producto_id, cantidad, precio_unitario,
                            descuento_porcentaje, descuento_importe, subtotal,
                            impuesto_porcentaje, impuesto_importe, total,
                            costo_unitario, lote, fecha_vencimiento
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        sale_id,
                        item['producto_id'],
                        item['cantidad'],
                        item['precio_unitario'],
                        item.get('descuento_porcentaje', 0),
                        item_descuento,
                        item_subtotal,
                        item.get('impuesto_porcentaje', product.get('iva_porcentaje', 21)),
                        item_impuesto,
                        item_total,
                        product.get('precio_compra', 0),
                        item.get('lote'),
                        item.get('fecha_vencimiento')
                    ))
                    
                    if not detail_id:
                        raise Exception(f"Error insertando detalle para producto {item['producto_id']}")
                    
                    # Actualizar stock
                    success, message = self.product_manager.update_stock(
                        product_id=item['producto_id'],
                        new_quantity=item['cantidad'],
                        movement_type='SALIDA',
                        reason='VENTA',
                        user_id=user_id,
                        unit_price=item['precio_unitario'],
                        reference_id=sale_id,
                        reference_type='VENTA',
                        notes=f"Venta #{sale_id}"
                    )
                    
                    if not success:
                        raise Exception(f"Error actualizando stock: {message}")
                
                # Insertar pagos
                for payment in payments:
                    payment_id = self.db.execute_insert("""
                        INSERT INTO pagos_venta (
                            venta_id, metodo_pago, importe, referencia,
                            fecha_pago, observaciones
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        sale_id,
                        payment['metodo_pago'],
                        payment['importe'],
                        payment.get('referencia'),
                        payment.get('fecha_pago', datetime.now()),
                        payment.get('observaciones')
                    ))
                    
                    if not payment_id:
                        raise Exception(f"Error registrando pago {payment['metodo_pago']}")
                
                # Actualizar cuenta corriente si es cliente con crédito
                if sale_data.get('cliente_id') and any(p['metodo_pago'] == 'CUENTA_CORRIENTE' for p in payments):
                    credit_amount = sum(p['importe'] for p in payments if p['metodo_pago'] == 'CUENTA_CORRIENTE')
                    if credit_amount > 0:
                        self.update_customer_account(sale_data['cliente_id'], credit_amount, 'DEBE', sale_id, user_id)
                
                # Completar venta
                self.db.execute_update("""
                    UPDATE ventas SET estado = 'COMPLETADA', completada_en = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (sale_id,))
                
                # Confirmar transacción
                self.db.commit_transaction()
                
                self.logger.info(f"Venta creada exitosamente: ID {sale_id}, Total: ${total}")
                return True, f"Venta #{sale_id} completada exitosamente", sale_id
                
            except Exception as e:
                self.db.rollback_transaction()
                raise e
                
        except Exception as e:
            self.logger.error(f"Error creando venta: {e}")
            return False, f"Error creando venta: {str(e)}", 0
    
    def get_sale_by_id(self, sale_id: int) -> Optional[Dict]:
        """Obtener venta por ID"""
        try:
            # Obtener información principal
            sale = self.db.execute_single("""
                SELECT v.*, c.nombre as cliente_nombre, c.email as cliente_email,
                       c.telefono as cliente_telefono, u.nombre_completo as usuario_nombre,
                       cj.nombre as caja_nombre
                FROM ventas v
                LEFT JOIN clientes c ON v.cliente_id = c.id
                LEFT JOIN usuarios u ON v.usuario_id = u.id
                LEFT JOIN cajas cj ON v.caja_id = cj.id
                WHERE v.id = ?
            """, (sale_id,))
            
            if not sale:
                return None
            
            # Obtener detalles de la venta
            items = self.db.execute_query("""
                SELECT dv.*, p.nombre as producto_nombre, p.codigo_barras,
                       p.unidad_medida, c.nombre as categoria_nombre
                FROM detalle_ventas dv
                LEFT JOIN productos p ON dv.producto_id = p.id
                LEFT JOIN categorias c ON p.categoria_id = c.id
                WHERE dv.venta_id = ?
                ORDER BY p.nombre
            """, (sale_id,))
            
            # Obtener pagos
            payments = self.db.execute_query("""
                SELECT * FROM pagos_venta 
                WHERE venta_id = ?
                ORDER BY fecha_pago
            """, (sale_id,))
            
            sale = dict(sale)
            sale['items'] = [dict(item) for item in items]
            sale['payments'] = [dict(payment) for payment in payments]
            
            return sale
            
        except Exception as e:
            self.logger.error(f"Error obteniendo venta: {e}")
            return None
    
    def get_sales(self, status: str = None, customer_id: int = None,
                 user_id: int = None, date_from: date = None, date_to: date = None,
                 limit: int = 100) -> List[Dict]:
        """Obtener lista de ventas con filtros"""
        try:
            query = """
                SELECT v.*, c.nombre as cliente_nombre, u.nombre_completo as usuario_nombre,
                       COUNT(dv.id) as total_items,
                       SUM(dv.cantidad) as total_productos
                FROM ventas v
                LEFT JOIN clientes c ON v.cliente_id = c.id
                LEFT JOIN usuarios u ON v.usuario_id = u.id
                LEFT JOIN detalle_ventas dv ON v.id = dv.venta_id
                WHERE 1=1
            """
            params = []
            
            if status:
                query += " AND v.estado = ?"
                params.append(status)
            
            if customer_id:
                query += " AND v.cliente_id = ?"
                params.append(customer_id)
            
            if user_id:
                query += " AND v.usuario_id = ?"
                params.append(user_id)
            
            if date_from:
                query += " AND DATE(v.fecha_venta) >= ?"
                params.append(date_from)
            
            if date_to:
                query += " AND DATE(v.fecha_venta) <= ?"
                params.append(date_to)
            
            query += """
                GROUP BY v.id
                ORDER BY v.fecha_venta DESC
                LIMIT ?
            """
            params.append(limit)
            
            return self.db.execute_query(query, params)
            
        except Exception as e:
            self.logger.error(f"Error obteniendo ventas: {e}")
            return []
    
    def cancel_sale(self, sale_id: int, user_id: int, reason: str = None) -> Tuple[bool, str]:
        """Cancelar venta y restaurar stock"""
        try:
            # Verificar que la venta existe
            sale = self.get_sale_by_id(sale_id)
            if not sale:
                return False, "Venta no encontrada"
            
            if sale['estado'] == 'CANCELADA':
                return False, "La venta ya está cancelada"
            
            if sale['estado'] == 'DEVUELTA':
                return False, "No se puede cancelar una venta devuelta"
            
            # Iniciar transacción
            self.db.begin_transaction()
            
            try:
                # Restaurar stock de todos los productos
                for item in sale['items']:
                    success, message = self.product_manager.update_stock(
                        product_id=item['producto_id'],
                        new_quantity=item['cantidad'],
                        movement_type='ENTRADA',
                        reason='CANCELACION_VENTA',
                        user_id=user_id,
                        unit_price=item['precio_unitario'],
                        reference_id=sale_id,
                        reference_type='CANCELACION',
                        notes=f"Cancelación de venta #{sale_id}: {reason or 'Sin motivo especificado'}"
                    )
                    
                    if not success:
                        raise Exception(f"Error restaurando stock: {message}")
                
                # Actualizar estado de la venta
                notes = f"Cancelada por usuario {user_id}"
                if reason:
                    notes += f". Motivo: {reason}"
                
                self.db.execute_update("""
                    UPDATE ventas 
                    SET estado = 'CANCELADA', cancelada_en = CURRENT_TIMESTAMP,
                        observaciones = COALESCE(observaciones || '\n', '') || ?
                    WHERE id = ?
                """, (notes, sale_id))
                
                # Reversar cuenta corriente si fue a crédito
                if sale['cliente_id']:
                    credit_payments = [p for p in sale['payments'] if p['metodo_pago'] == 'CUENTA_CORRIENTE']
                    for payment in credit_payments:
                        self.update_customer_account(
                            sale['cliente_id'], payment['importe'], 'HABER', 
                            sale_id, user_id, f"Cancelación de venta #{sale_id}"
                        )
                
                # Confirmar transacción
                self.db.commit_transaction()
                
                self.logger.info(f"Venta cancelada: ID {sale_id}")
                return True, "Venta cancelada exitosamente"
                
            except Exception as e:
                self.db.rollback_transaction()
                raise e
                
        except Exception as e:
            self.logger.error(f"Error cancelando venta: {e}")
            return False, f"Error cancelando venta: {str(e)}"
    
    def process_return(self, sale_id: int, returned_items: List[Dict], 
                      user_id: int, reason: str = None) -> Tuple[bool, str]:
        """Procesar devolución parcial o total"""
        try:
            # Verificar que la venta existe
            sale = self.get_sale_by_id(sale_id)
            if not sale:
                return False, "Venta no encontrada"
            
            if sale['estado'] != 'COMPLETADA':
                return False, "Solo se pueden devolver ventas completadas"
            
            # Validar items a devolver
            if not returned_items:
                return False, "Debe especificar los productos a devolver"
            
            # Iniciar transacción
            self.db.begin_transaction()
            
            try:
                total_devuelto = 0
                
                for returned_item in returned_items:
                    producto_id = returned_item['producto_id']
                    cantidad_devuelta = returned_item['cantidad_devuelta']
                    
                    # Buscar el item original en la venta
                    original_item = None
                    for item in sale['items']:
                        if item['producto_id'] == producto_id:
                            original_item = item
                            break
                    
                    if not original_item:
                        raise Exception(f"Producto ID {producto_id} no está en la venta original")
                    
                    if cantidad_devuelta > original_item['cantidad']:
                        raise Exception(f"No se puede devolver más cantidad de la vendida")
                    
                    # Crear registro de devolución
                    return_id = self.db.execute_insert("""
                        INSERT INTO devoluciones (
                            venta_id, producto_id, cantidad_devuelta, precio_unitario,
                            motivo, usuario_id, fecha_devolucion
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        sale_id, producto_id, cantidad_devuelta,
                        original_item['precio_unitario'], reason, user_id, datetime.now()
                    ))
                    
                    if not return_id:
                        raise Exception(f"Error registrando devolución para producto {producto_id}")
                    
                    # Restaurar stock
                    success, message = self.product_manager.update_stock(
                        product_id=producto_id,
                        new_quantity=cantidad_devuelta,
                        movement_type='ENTRADA',
                        reason='DEVOLUCION',
                        user_id=user_id,
                        unit_price=original_item['precio_unitario'],
                        reference_id=sale_id,
                        reference_type='DEVOLUCION',
                        notes=f"Devolución de venta #{sale_id}: {reason or 'Sin motivo'}"
                    )
                    
                    if not success:
                        raise Exception(f"Error restaurando stock: {message}")
                    
                    total_devuelto += cantidad_devuelta * original_item['precio_unitario']
                
                # Actualizar estado de la venta
                notes = f"Devolución procesada por usuario {user_id}. Monto: ${total_devuelto}"
                if reason:
                    notes += f". Motivo: {reason}"
                
                # Verificar si es devolución total
                total_original = sum(item['cantidad'] for item in sale['items'])
                total_devuelto_cantidad = sum(item['cantidad_devuelta'] for item in returned_items)
                
                if total_devuelto_cantidad >= total_original:
                    new_status = 'DEVUELTA'
                else:
                    new_status = 'COMPLETADA'  # Mantener como completada para devoluciones parciales
                
                self.db.execute_update("""
                    UPDATE ventas 
                    SET estado = ?, devolucion_en = CURRENT_TIMESTAMP,
                        observaciones = COALESCE(observaciones || '\n', '') || ?
                    WHERE id = ?
                """, (new_status, notes, sale_id))
                
                # Confirmar transacción
                self.db.commit_transaction()
                
                self.logger.info(f"Devolución procesada: Venta {sale_id}, Monto: ${total_devuelto}")
                return True, f"Devolución procesada. Monto devuelto: ${total_devuelto}"
                
            except Exception as e:
                self.db.rollback_transaction()
                raise e
                
        except Exception as e:
            self.logger.error(f"Error procesando devolución: {e}")
            return False, f"Error procesando devolución: {str(e)}"
    
    def get_sales_statistics(self, date_from: date = None, date_to: date = None,
                           user_id: int = None) -> Dict:
        """Obtener estadísticas de ventas"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_ventas,
                    SUM(CASE WHEN estado = 'COMPLETADA' THEN 1 ELSE 0 END) as ventas_completadas,
                    SUM(CASE WHEN estado = 'CANCELADA' THEN 1 ELSE 0 END) as ventas_canceladas,
                    SUM(CASE WHEN estado = 'DEVUELTA' THEN 1 ELSE 0 END) as ventas_devueltas,
                    SUM(CASE WHEN estado = 'COMPLETADA' THEN total ELSE 0 END) as monto_total,
                    AVG(CASE WHEN estado = 'COMPLETADA' THEN total ELSE NULL END) as monto_promedio,
                    COUNT(DISTINCT cliente_id) as clientes_unicos,
                    SUM(CASE WHEN estado = 'COMPLETADA' THEN total - subtotal ELSE 0 END) as impuestos_total
                FROM ventas
                WHERE 1=1
            """
            params = []
            
            if date_from:
                query += " AND DATE(fecha_venta) >= ?"
                params.append(date_from)
            
            if date_to:
                query += " AND DATE(fecha_venta) <= ?"
                params.append(date_to)
            
            if user_id:
                query += " AND usuario_id = ?"
                params.append(user_id)
            
            result = self.db.execute_single(query, params)
            
            if result:
                return {
                    'total_ventas': result['total_ventas'] or 0,
                    'ventas_completadas': result['ventas_completadas'] or 0,
                    'ventas_canceladas': result['ventas_canceladas'] or 0,
                    'ventas_devueltas': result['ventas_devueltas'] or 0,
                    'monto_total': float(result['monto_total'] or 0),
                    'monto_promedio': float(result['monto_promedio'] or 0),
                    'clientes_unicos': result['clientes_unicos'] or 0,
                    'impuestos_total': float(result['impuestos_total'] or 0)
                }
            else:
                return self._empty_statistics()
                
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas de ventas: {e}")
            return self._empty_statistics()
    
    def get_top_products(self, limit: int = 10, date_from: date = None, 
                        date_to: date = None) -> List[Dict]:
        """Obtener productos más vendidos"""
        try:
            query = """
                SELECT p.id, p.nombre, p.codigo_barras, c.nombre as categoria_nombre,
                       SUM(dv.cantidad) as cantidad_vendida,
                       SUM(dv.total) as monto_total,
                       COUNT(DISTINCT v.id) as veces_vendido,
                       AVG(dv.precio_unitario) as precio_promedio
                FROM productos p
                INNER JOIN detalle_ventas dv ON p.id = dv.producto_id
                INNER JOIN ventas v ON dv.venta_id = v.id
                LEFT JOIN categorias c ON p.categoria_id = c.id
                WHERE v.estado = 'COMPLETADA'
            """
            params = []
            
            if date_from:
                query += " AND DATE(v.fecha_venta) >= ?"
                params.append(date_from)
            
            if date_to:
                query += " AND DATE(v.fecha_venta) <= ?"
                params.append(date_to)
            
            query += """
                GROUP BY p.id, p.nombre, p.codigo_barras, c.nombre
                ORDER BY cantidad_vendida DESC
                LIMIT ?
            """
            params.append(limit)
            
            return self.db.execute_query(query, params)
            
        except Exception as e:
            self.logger.error(f"Error obteniendo productos más vendidos: {e}")
            return []
    
    def generate_invoice_number(self) -> str:
        """Generar número de factura único"""
        try:
            # Obtener el siguiente número secuencial para hoy
            today = datetime.now().strftime('%Y%m%d')
            
            result = self.db.execute_single("""
                SELECT COALESCE(MAX(CAST(SUBSTR(numero_factura, -6) AS INTEGER)), 0) + 1 as next_num
                FROM ventas 
                WHERE numero_factura LIKE ?
            """, (f"{today}%",))
            
            if result and result['next_num']:
                next_num = result['next_num']
            else:
                next_num = 1
            
            return f"{today}{next_num:06d}"
            
        except Exception as e:
            self.logger.error(f"Error generando número de factura: {e}")
            return f"{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def update_customer_account(self, customer_id: int, amount: float, 
                               movement_type: str, sale_id: int, user_id: int,
                               notes: str = None):
        """Actualizar cuenta corriente del cliente"""
        try:
            # Obtener saldo actual
            current_balance = self.db.execute_single("""
                SELECT COALESCE(SUM(CASE 
                    WHEN tipo_movimiento = 'DEBE' THEN importe 
                    ELSE -importe 
                END), 0) as saldo
                FROM cuenta_corriente 
                WHERE cliente_id = ?
            """, (customer_id,))
            
            previous_balance = float(current_balance['saldo']) if current_balance else 0.0
            
            if movement_type == 'DEBE':
                new_balance = previous_balance + amount
            else:  # HABER
                new_balance = previous_balance - amount
            
            # Insertar movimiento
            self.db.execute_insert("""
                INSERT INTO cuenta_corriente (
                    cliente_id, tipo_movimiento, concepto, importe,
                    saldo_anterior, saldo_nuevo, venta_id, usuario_id,
                    observaciones
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer_id, movement_type,
                f"Venta #{sale_id}" if movement_type == 'DEBE' else f"Pago venta #{sale_id}",
                amount, previous_balance, new_balance, sale_id, user_id, notes
            ))
            
        except Exception as e:
            self.logger.error(f"Error actualizando cuenta corriente: {e}")
            raise e
    
    def get_daily_summary(self, target_date: date = None, user_id: int = None) -> Dict:
        """Obtener resumen diario de ventas"""
        try:
            if not target_date:
                target_date = date.today()
            
            query = """
                SELECT 
                    COUNT(*) as total_ventas,
                    SUM(total) as monto_total,
                    SUM(subtotal) as subtotal_total,
                    SUM(impuestos_importe) as impuestos_total,
                    SUM(descuento_importe) as descuentos_total,
                    AVG(total) as ticket_promedio,
                    MIN(total) as ticket_minimo,
                    MAX(total) as ticket_maximo
                FROM ventas
                WHERE DATE(fecha_venta) = ? AND estado = 'COMPLETADA'
            """
            params = [target_date]
            
            if user_id:
                query += " AND usuario_id = ?"
                params.append(user_id)
            
            result = self.db.execute_single(query, params)
            
            # Obtener métodos de pago del día
            payment_query = """
                SELECT pv.metodo_pago, SUM(pv.importe) as total_metodo
                FROM pagos_venta pv
                INNER JOIN ventas v ON pv.venta_id = v.id
                WHERE DATE(v.fecha_venta) = ? AND v.estado = 'COMPLETADA'
            """
            if user_id:
                payment_query += " AND v.usuario_id = ?"
            
            payment_query += " GROUP BY pv.metodo_pago ORDER BY total_metodo DESC"
            
            payments = self.db.execute_query(payment_query, params)
            
            return {
                'fecha': target_date.isoformat(),
                'total_ventas': result['total_ventas'] if result else 0,
                'monto_total': float(result['monto_total'] or 0) if result else 0.0,
                'subtotal_total': float(result['subtotal_total'] or 0) if result else 0.0,
                'impuestos_total': float(result['impuestos_total'] or 0) if result else 0.0,
                'descuentos_total': float(result['descuentos_total'] or 0) if result else 0.0,
                'ticket_promedio': float(result['ticket_promedio'] or 0) if result else 0.0,
                'ticket_minimo': float(result['ticket_minimo'] or 0) if result else 0.0,
                'ticket_maximo': float(result['ticket_maximo'] or 0) if result else 0.0,
                'metodos_pago': [dict(payment) for payment in payments] if payments else []
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo resumen diario: {e}")
            return {'fecha': target_date.isoformat(), 'error': str(e)}
    
    def _empty_statistics(self) -> Dict:
        """Retornar estadísticas vacías"""
        return {
            'total_ventas': 0,
            'ventas_completadas': 0,
            'ventas_canceladas': 0,
            'ventas_devueltas': 0,
            'monto_total': 0.0,
            'monto_promedio': 0.0,
            'clientes_unicos': 0,
            'impuestos_total': 0.0
        }