"""
Gestor de Ventas para AlmacénPro
Maneja ventas, tickets, facturación y cuenta corriente
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from datetime import datetime, date

logger = logging.getLogger(__name__)

class SalesManager:
    """Gestor de ventas y facturación"""
    
    def __init__(self, db_manager, product_manager):
        self.db = db_manager
        self.product_manager = product_manager
        logger.info("SalesManager inicializado")
    
    def create_sale(self, sale_data: Dict) -> Tuple[bool, str, int]:
        """Crear nueva venta"""
        try:
            # Validaciones básicas
            if not sale_data.get('items') or len(sale_data['items']) == 0:
                return False, "La venta debe tener al menos un producto", 0
            
            if not sale_data.get('vendedor_id'):
                return False, "Debe especificar el vendedor", 0
            
            # Validar stock de todos los productos antes de procesar
            for item in sale_data['items']:
                product = self.product_manager.get_product_by_id(item['producto_id'])
                if not product:
                    return False, f"Producto ID {item['producto_id']} no encontrado", 0
                
                if not product.get('permite_venta_sin_stock', False):
                    if product['stock_actual'] < item['cantidad']:
                        return False, f"Stock insuficiente para {product['nombre']}. Stock: {product['stock_actual']}", 0
            
            # Calcular totales
            subtotal = sum(
                Decimal(str(item['cantidad'])) * Decimal(str(item['precio_unitario']))
                for item in sale_data['items']
            )
            
            descuento_total = Decimal(str(sale_data.get('descuento', 0)))
            recargo_total = Decimal(str(sale_data.get('recargo', 0)))
            
            # Calcular impuestos (IVA)
            base_imponible = subtotal - descuento_total + recargo_total
            impuestos = base_imponible * Decimal('0.21')  # IVA 21% por defecto
            
            total = base_imponible + impuestos
            
            # Generar número de ticket único
            numero_ticket = self.generate_ticket_number(sale_data.get('caja_id', 1))
            
            # Crear venta principal
            sale_id = self.db.execute_insert("""
                INSERT INTO ventas (
                    numero_ticket, numero_factura, cliente_id, vendedor_id, caja_id,
                    tipo_venta, tipo_comprobante, subtotal, descuento, recargo,
                    impuestos, total, metodo_pago, estado, fecha_vencimiento,
                    observaciones
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                numero_ticket,
                sale_data.get('numero_factura'),
                sale_data.get('cliente_id'),
                sale_data['vendedor_id'],
                sale_data.get('caja_id', 1),
                sale_data.get('tipo_venta', 'CONTADO'),
                sale_data.get('tipo_comprobante', 'TICKET'),
                float(subtotal),
                float(descuento_total),
                float(recargo_total),
                float(impuestos),
                float(total),
                sale_data.get('metodo_pago', 'EFECTIVO'),
                'COMPLETADA',
                sale_data.get('fecha_vencimiento'),
                sale_data.get('observaciones')
            ))
            
            # Crear detalles de venta y actualizar stock
            for item in sale_data['items']:
                # Calcular subtotal del item con descuentos
                item_subtotal = (
                    Decimal(str(item['cantidad'])) * 
                    Decimal(str(item['precio_unitario']))
                )
                
                item_discount = item_subtotal * (Decimal(str(item.get('descuento_porcentaje', 0))) / 100)
                item_final = item_subtotal - item_discount
                
                # Calcular IVA del item
                iva_porcentaje = Decimal(str(item.get('iva_porcentaje', 21)))
                iva_importe = item_final * (iva_porcentaje / 100)
                
                # Insertar detalle
                self.db.execute_insert("""
                    INSERT INTO detalle_ventas (
                        venta_id, producto_id, cantidad, precio_unitario,
                        descuento_porcentaje, descuento_importe, subtotal,
                        iva_porcentaje, iva_importe
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sale_id,
                    item['producto_id'],
                    item['cantidad'],
                    item['precio_unitario'],
                    item.get('descuento_porcentaje', 0),
                    float(item_discount),
                    float(item_final),
                    float(iva_porcentaje),
                    float(iva_importe)
                ))
                
                # Actualizar stock
                success, message = self.product_manager.update_stock(
                    product_id=item['producto_id'],
                    new_quantity=item['cantidad'],
                    movement_type='SALIDA',
                    reason='VENTA',
                    user_id=sale_data['vendedor_id'],
                    unit_price=item['precio_unitario'],
                    reference_id=sale_id,
                    reference_type='VENTA',
                    notes=f"Venta {numero_ticket}"
                )
                
                if not success:
                    # Si hay error en stock, revertir transacción
                    self.db.connection.rollback()
                    return False, f"Error actualizando stock: {message}", 0
            
            # Si es cuenta corriente, registrar movimiento
            if sale_data.get('tipo_venta') == 'CUENTA_CORRIENTE' and sale_data.get('cliente_id'):
                success, message = self.register_account_movement(
                    cliente_id=sale_data['cliente_id'],
                    movement_type='DEBE',
                    concept=f'Venta {numero_ticket}',
                    amount=float(total),
                    sale_id=sale_id,
                    user_id=sale_data['vendedor_id']
                )
                
                if not success:
                    logger.warning(f"Error registrando cuenta corriente: {message}")
            
            # Registrar movimiento de caja si hay sesión activa
            self.register_cash_movement(
                sale_id=sale_id,
                amount=float(total),
                payment_method=sale_data.get('metodo_pago', 'EFECTIVO'),
                user_id=sale_data['vendedor_id']
            )
            
            logger.info(f"Venta creada: {numero_ticket} por ${total}")
            return True, f"Venta {numero_ticket} creada exitosamente", sale_id
            
        except Exception as e:
            logger.error(f"Error creando venta: {e}")
            return False, f"Error creando venta: {str(e)}", 0
    
    def get_sale_by_id(self, sale_id: int) -> Optional[Dict]:
        """Obtener venta por ID con detalles"""
        try:
            # Obtener venta principal
            sale = self.db.execute_single("""
                SELECT v.*, 
                       c.nombre as cliente_nombre, c.apellido as cliente_apellido,
                       u.nombre_completo as vendedor_nombre,
                       cj.nombre as caja_nombre
                FROM ventas v
                LEFT JOIN clientes c ON v.cliente_id = c.id
                LEFT JOIN usuarios u ON v.vendedor_id = u.id
                LEFT JOIN cajas cj ON v.caja_id = cj.id
                WHERE v.id = ?
            """, (sale_id,))
            
            if not sale:
                return None
            
            # Obtener detalles
            details = self.db.execute_query("""
                SELECT dv.*, p.nombre as producto_nombre, p.codigo_barras
                FROM detalle_ventas dv
                JOIN productos p ON dv.producto_id = p.id
                WHERE dv.venta_id = ?
                ORDER BY dv.id
            """, (sale_id,))
            
            sale_dict = dict(sale)
            sale_dict['items'] = details
            
            return sale_dict
            
        except Exception as e:
            logger.error(f"Error obteniendo venta: {e}")
            return None
    
    def get_sales_by_date_range(self, start_date: str, end_date: str, 
                               vendedor_id: int = None, cliente_id: int = None) -> List[Dict]:
        """Obtener ventas por rango de fechas"""
        try:
            query = """
                SELECT v.*, 
                       c.nombre as cliente_nombre, c.apellido as cliente_apellido,
                       u.nombre_completo as vendedor_nombre
                FROM ventas v
                LEFT JOIN clientes c ON v.cliente_id = c.id
                LEFT JOIN usuarios u ON v.vendedor_id = u.id
                WHERE DATE(v.fecha_venta) BETWEEN ? AND ?
            """
            
            params = [start_date, end_date]
            
            if vendedor_id:
                query += " AND v.vendedor_id = ?"
                params.append(vendedor_id)
            
            if cliente_id:
                query += " AND v.cliente_id = ?"
                params.append(cliente_id)
            
            query += " ORDER BY v.fecha_venta DESC"
            
            return self.db.execute_query(query, tuple(params))
            
        except Exception as e:
            logger.error(f"Error obteniendo ventas por fecha: {e}")
            return []
    
    def get_daily_sales_summary(self, target_date: str = None) -> Dict:
        """Obtener resumen de ventas del día"""
        try:
            if not target_date:
                target_date = date.today().isoformat()
            
            summary = self.db.execute_single("""
                SELECT 
                    COUNT(*) as total_ventas,
                    SUM(total) as total_facturado,
                    AVG(total) as ticket_promedio,
                    SUM(descuento) as total_descuentos,
                    MIN(total) as venta_minima,
                    MAX(total) as venta_maxima
                FROM ventas 
                WHERE DATE(fecha_venta) = ? AND estado = 'COMPLETADA'
            """, (target_date,))
            
            # Ventas por método de pago
            payment_methods = self.db.execute_query("""
                SELECT 
                    metodo_pago,
                    COUNT(*) as cantidad,
                    SUM(total) as total
                FROM ventas 
                WHERE DATE(fecha_venta) = ? AND estado = 'COMPLETADA'
                GROUP BY metodo_pago
                ORDER BY total DESC
            """, (target_date,))
            
            # Productos más vendidos del día
            top_products = self.db.execute_query("""
                SELECT 
                    p.nombre,
                    SUM(dv.cantidad) as cantidad_vendida,
                    SUM(dv.subtotal) as total_vendido
                FROM detalle_ventas dv
                JOIN productos p ON dv.producto_id = p.id
                JOIN ventas v ON dv.venta_id = v.id
                WHERE DATE(v.fecha_venta) = ? AND v.estado = 'COMPLETADA'
                GROUP BY p.id, p.nombre
                ORDER BY cantidad_vendida DESC
                LIMIT 10
            """, (target_date,))
            
            return {
                'fecha': target_date,
                'resumen': dict(summary) if summary else {},
                'por_metodo_pago': payment_methods,
                'productos_mas_vendidos': top_products
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen diario: {e}")
            return {}
    
    def cancel_sale(self, sale_id: int, user_id: int, reason: str) -> Tuple[bool, str]:
        """Cancelar venta y revertir stock"""
        try:
            # Obtener venta con detalles
            sale = self.get_sale_by_id(sale_id)
            if not sale:
                return False, "Venta no encontrada"
            
            if sale['estado'] != 'COMPLETADA':
                return False, "Solo se pueden cancelar ventas completadas"
            
            # Revertir stock de todos los productos
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
                    notes=f"Cancelación venta {sale['numero_ticket']}: {reason}"
                )
                
                if not success:
                    return False, f"Error revirtiendo stock: {message}"
            
            # Actualizar estado de la venta
            self.db.execute_update("""
                UPDATE ventas 
                SET estado = 'CANCELADA', observaciones = ? 
                WHERE id = ?
            """, (f"CANCELADA: {reason}", sale_id))
            
            # Si era cuenta corriente, revertir movimiento
            if sale['tipo_venta'] == 'CUENTA_CORRIENTE' and sale['cliente_id']:
                self.register_account_movement(
                    cliente_id=sale['cliente_id'],
                    movement_type='HABER',
                    concept=f'Cancelación venta {sale["numero_ticket"]}',
                    amount=sale['total'],
                    sale_id=sale_id,
                    user_id=user_id
                )
            
            logger.info(f"Venta cancelada: {sale['numero_ticket']}")
            return True, f"Venta {sale['numero_ticket']} cancelada exitosamente"
            
        except Exception as e:
            logger.error(f"Error cancelando venta: {e}")
            return False, f"Error cancelando venta: {str(e)}"
    
    def register_account_movement(self, cliente_id: int, movement_type: str,
                                concept: str, amount: float, sale_id: int = None,
                                user_id: int = None, due_date: str = None) -> Tuple[bool, str]:
        """Registrar movimiento en cuenta corriente"""
        try:
            # Obtener saldo actual del cliente
            client_data = self.db.execute_single("""
                SELECT saldo_cuenta_corriente FROM clientes WHERE id = ?
            """, (cliente_id,))
            
            if not client_data:
                return False, "Cliente no encontrado"
            
            previous_balance = float(client_data['saldo_cuenta_corriente'] or 0)
            
            # Calcular nuevo saldo
            if movement_type == 'DEBE':
                new_balance = previous_balance + amount
            else:  # HABER
                new_balance = previous_balance - amount
            
            # Registrar movimiento
            self.db.execute_insert("""
                INSERT INTO cuenta_corriente (
                    cliente_id, tipo_movimiento, concepto, importe,
                    saldo_anterior, saldo_nuevo, venta_id, fecha_vencimiento,
                    usuario_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cliente_id, movement_type, concept, amount,
                previous_balance, new_balance, sale_id, due_date, user_id
            ))
            
            # Actualizar saldo del cliente
            self.db.execute_update("""
                UPDATE clientes SET saldo_cuenta_corriente = ? WHERE id = ?
            """, (new_balance, cliente_id))
            
            logger.info(f"Movimiento cuenta corriente: Cliente {cliente_id}, {movement_type} ${amount}")
            return True, "Movimiento registrado exitosamente"
            
        except Exception as e:
            logger.error(f"Error registrando cuenta corriente: {e}")
            return False, f"Error registrando cuenta corriente: {str(e)}"
    
    def register_cash_movement(self, sale_id: int, amount: float, 
                             payment_method: str, user_id: int):
        """Registrar movimiento de caja"""
        try:
            # Obtener sesión de caja activa del usuario
            active_session = self.db.execute_single("""
                SELECT id, monto_apertura + COALESCE(
                    (SELECT SUM(importe) FROM movimientos_caja WHERE sesion_caja_id = sesiones_caja.id), 0
                ) as saldo_actual
                FROM sesiones_caja 
                WHERE usuario_id = ? AND estado = 'ABIERTA'
                ORDER BY fecha_apertura DESC
                LIMIT 1
            """, (user_id,))
            
            if not active_session:
                logger.warning(f"No hay sesión de caja activa para usuario {user_id}")
                return
            
            previous_balance = float(active_session['saldo_actual'])
            new_balance = previous_balance + amount
            
            # Registrar movimiento
            self.db.execute_insert("""
                INSERT INTO movimientos_caja (
                    sesion_caja_id, tipo_movimiento, concepto, importe,
                    saldo_anterior, saldo_nuevo, venta_id, metodo_pago, usuario_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                active_session['id'], 'VENTA', f'Venta ID {sale_id}', amount,
                previous_balance, new_balance, sale_id, payment_method, user_id
            ))
            
        except Exception as e:
            logger.error(f"Error registrando movimiento de caja: {e}")
    
    def generate_ticket_number(self, caja_id: int = 1) -> str:
        """Generar número de ticket único"""
        try:
            # Obtener último número del día para la caja
            today = date.today().isoformat()
            
            last_ticket = self.db.execute_single("""
                SELECT numero_ticket FROM ventas 
                WHERE caja_id = ? AND DATE(fecha_venta) = ?
                ORDER BY id DESC LIMIT 1
            """, (caja_id, today))
            
            if last_ticket and last_ticket['numero_ticket']:
                # Extraer número secuencial
                try:
                    last_num = int(last_ticket['numero_ticket'].split('-')[-1])
                    next_num = last_num + 1
                except:
                    next_num = 1
            else:
                next_num = 1
            
            # Formato: C01-YYYYMMDD-NNNNNN
            return f"C{caja_id:02d}-{datetime.now().strftime('%Y%m%d')}-{next_num:06d}"
            
        except Exception as e:
            logger.error(f"Error generando número de ticket: {e}")
            # Fallback a timestamp
            return f"T{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def get_account_balance(self, cliente_id: int) -> Dict:
        """Obtener balance de cuenta corriente de cliente"""
        try:
            # Saldo actual
            client_data = self.db.execute_single("""
                SELECT nombre, apellido, saldo_cuenta_corriente, limite_credito
                FROM clientes WHERE id = ?
            """, (cliente_id,))
            
            if not client_data:
                return {}
            
            # Últimos movimientos
            movements = self.db.execute_query("""
                SELECT * FROM cuenta_corriente 
                WHERE cliente_id = ? 
                ORDER BY fecha_movimiento DESC 
                LIMIT 20
            """, (cliente_id,))
            
            # Facturas vencidas
            overdue_sales = self.db.execute_query("""
                SELECT v.*, JULIANDAY('now') - JULIANDAY(v.fecha_vencimiento) as dias_vencido
                FROM ventas v
                WHERE v.cliente_id = ? 
                AND v.tipo_venta = 'CUENTA_CORRIENTE'
                AND v.estado = 'COMPLETADA'
                AND v.fecha_vencimiento < DATE('now')
                ORDER BY v.fecha_vencimiento
            """, (cliente_id,))
            
            return {
                'cliente': dict(client_data),
                'saldo_actual': float(client_data['saldo_cuenta_corriente'] or 0),
                'limite_credito': float(client_data['limite_credito'] or 0),
                'credito_disponible': float(client_data['limite_credito'] or 0) - float(client_data['saldo_cuenta_corriente'] or 0),
                'movimientos_recientes': movements,
                'facturas_vencidas': overdue_sales,
                'total_vencido': sum(float(sale['total']) for sale in overdue_sales)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo balance de cuenta: {e}")
            return {}
    
    def process_payment(self, cliente_id: int, amount: float, 
                       payment_method: str, user_id: int, notes: str = None) -> Tuple[bool, str]:
        """Procesar pago de cuenta corriente"""
        try:
            success, message = self.register_account_movement(
                cliente_id=cliente_id,
                movement_type='HABER',
                concept=f'Pago - {payment_method}',
                amount=amount,
                user_id=user_id
            )
            
            if success:
                logger.info(f"Pago procesado: Cliente {cliente_id}, ${amount}")
                return True, f"Pago de ${amount:.2f} procesado exitosamente"
            else:
                return False, message
                
        except Exception as e:
            logger.error(f"Error procesando pago: {e}")
            return False, f"Error procesando pago: {str(e)}"
    
    def get_sales_statistics(self, start_date: str, end_date: str) -> Dict:
        """Obtener estadísticas de ventas"""
        try:
            # Estadísticas generales
            general_stats = self.db.execute_single("""
                SELECT 
                    COUNT(*) as total_ventas,
                    SUM(total) as total_facturado,
                    AVG(total) as ticket_promedio,
                    SUM(descuento) as total_descuentos,
                    COUNT(DISTINCT cliente_id) as clientes_unicos,
                    COUNT(DISTINCT vendedor_id) as vendedores_activos
                FROM ventas 
                WHERE DATE(fecha_venta) BETWEEN ? AND ? 
                AND estado = 'COMPLETADA'
            """, (start_date, end_date))
            
            # Ventas por día
            daily_sales = self.db.execute_query("""
                SELECT 
                    DATE(fecha_venta) as fecha,
                    COUNT(*) as cantidad_ventas,
                    SUM(total) as total_dia
                FROM ventas 
                WHERE DATE(fecha_venta) BETWEEN ? AND ? 
                AND estado = 'COMPLETADA'
                GROUP BY DATE(fecha_venta)
                ORDER BY fecha
            """, (start_date, end_date))
            
            # Top vendedores
            top_sellers = self.db.execute_query("""
                SELECT 
                    u.nombre_completo,
                    COUNT(v.id) as cantidad_ventas,
                    SUM(v.total) as total_vendido
                FROM ventas v
                JOIN usuarios u ON v.vendedor_id = u.id
                WHERE DATE(v.fecha_venta) BETWEEN ? AND ? 
                AND v.estado = 'COMPLETADA'
                GROUP BY v.vendedor_id, u.nombre_completo
                ORDER BY total_vendido DESC
                LIMIT 10
            """, (start_date, end_date))
            
            # Métodos de pago
            payment_methods = self.db.execute_query("""
                SELECT 
                    metodo_pago,
                    COUNT(*) as cantidad,
                    SUM(total) as total,
                    AVG(total) as promedio
                FROM ventas 
                WHERE DATE(fecha_venta) BETWEEN ? AND ? 
                AND estado = 'COMPLETADA'
                GROUP BY metodo_pago
                ORDER BY total DESC
            """, (start_date, end_date))
            
            return {
                'periodo': {'inicio': start_date, 'fin': end_date},
                'resumen_general': dict(general_stats) if general_stats else {},
                'ventas_diarias': daily_sales,
                'top_vendedores': top_sellers,
                'metodos_pago': payment_methods
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de ventas: {e}")
            return {}
    
    def get_pending_accounts(self, include_overdue_only: bool = False) -> List[Dict]:
        """Obtener cuentas pendientes de pago"""
        try:
            query = """
                SELECT 
                    c.id, c.nombre, c.apellido, c.saldo_cuenta_corriente,
                    c.limite_credito, c.telefono,
                    COUNT(v.id) as facturas_pendientes,
                    MIN(v.fecha_vencimiento) as primer_vencimiento,
                    SUM(CASE WHEN v.fecha_vencimiento < DATE('now') THEN v.total ELSE 0 END) as monto_vencido
                FROM clientes c
                LEFT JOIN ventas v ON c.id = v.cliente_id 
                    AND v.tipo_venta = 'CUENTA_CORRIENTE' 
                    AND v.estado = 'COMPLETADA'
                WHERE c.saldo_cuenta_corriente > 0
            """
            
            if include_overdue_only:
                query += " AND v.fecha_vencimiento < DATE('now')"
            
            query += """
                GROUP BY c.id, c.nombre, c.apellido, c.saldo_cuenta_corriente, 
                         c.limite_credito, c.telefono
                ORDER BY c.saldo_cuenta_corriente DESC
            """
            
            return self.db.execute_query(query)
            
        except Exception as e:
            logger.error(f"Error obteniendo cuentas pendientes: {e}")
            return []