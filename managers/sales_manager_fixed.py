"""
SalesManager corregido - AlmacénPro v2.0
Versión que funciona con la estructura real de la base de datos
"""

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
import uuid

logger = logging.getLogger(__name__)

class SalesManager:
    """Gestor principal para ventas y facturación - Versión Corregida"""
    
    def __init__(self, db_manager, product_manager, financial_manager=None):
        self.db = db_manager
        self.product_manager = product_manager
        self.financial_manager = financial_manager
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
        """Crear nueva venta - Versión corregida"""
        try:
            # Validaciones básicas
            if not items:
                return False, "La venta debe tener al menos un producto", 0
            
            if not payments:
                return False, "La venta debe tener al menos un método de pago", 0
            
            # Verificar stock disponible (sin actualizar para evitar triggers)
            for item in items:
                product = self.product_manager.get_product_by_id(item['producto_id'])
                if not product:
                    return False, f"Producto ID {item['producto_id']} no encontrado", 0
                
                current_stock = float(product.get('stock_actual', 0))
                if current_stock < item['cantidad']:
                    return False, f"Stock insuficiente para {product['nombre']}. Disponible: {current_stock}", 0
            
            # Calcular totales
            subtotal = sum(item['cantidad'] * item['precio_unitario'] for item in items)
            descuento_total = sum(item.get('descuento_importe', 0) for item in items)
            impuestos_total = sum(item.get('impuesto_importe', 0) for item in items)
            total = subtotal - descuento_total + impuestos_total
            
            # Validar que los pagos cubran el total
            total_pagos = sum(payment['importe'] for payment in payments)
            if abs(total_pagos - total) > 0.01:  # Tolerancia para redondeo
                return False, f"Los pagos ({total_pagos}) no coinciden con el total ({total})", 0
            
            # Iniciar transacción
            self.db.begin_transaction()
            
            try:
                # Crear venta
                sale_id = self.db.execute_insert("""
                    INSERT INTO ventas (
                        numero_factura, cliente_id, vendedor_id, usuario_id,
                        fecha_venta, subtotal, descuento, impuestos, total, 
                        estado, notas, caja_id, tipo_venta, metodo_pago
                    ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.generate_invoice_number(),
                    sale_data.get('cliente_id'),
                    user_id,  # vendedor_id = usuario_id
                    user_id,
                    subtotal,
                    descuento_total,
                    impuestos_total,
                    total,
                    'COMPLETADA',  # Directamente completada
                    sale_data.get('observaciones', ''),
                    sale_data.get('caja_id', 1),
                    sale_data.get('tipo_comprobante', 'TICKET'),
                    payments[0]['metodo_pago'] if payments else 'EFECTIVO'
                ))
                
                if not sale_id:
                    raise Exception("Error creando venta")
                
                # Insertar detalles de la venta
                for item in items:
                    item_subtotal = item['cantidad'] * item['precio_unitario']
                    
                    detail_id = self.db.execute_insert("""
                        INSERT INTO detalle_ventas (
                            venta_id, producto_id, cantidad, precio_unitario,
                            descuento_porcentaje, subtotal
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        sale_id,
                        item['producto_id'],
                        item['cantidad'],
                        item['precio_unitario'],
                        item.get('descuento_porcentaje', 0),
                        item_subtotal
                    ))
                    
                    if not detail_id:
                        raise Exception(f"Error insertando detalle para producto {item['producto_id']}")
                    
                    # Actualizar stock manualmente (evitando triggers)
                    try:
                        self.update_stock_direct(item['producto_id'], item['cantidad'])
                    except Exception as e:
                        self.logger.warning(f"No se pudo actualizar stock para producto {item['producto_id']}: {e}")
                        # Continúar sin actualizar stock por ahora
                
                # Insertar pagos
                for payment in payments:
                    payment_id = self.db.execute_insert("""
                        INSERT INTO pagos_venta (
                            venta_id, metodo_pago, importe, referencia,
                            fecha_pago, observaciones
                        ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                    """, (
                        sale_id,
                        payment['metodo_pago'],
                        payment['importe'],
                        payment.get('referencia'),
                        payment.get('observaciones')
                    ))
                    
                    if not payment_id:
                        raise Exception(f"Error registrando pago {payment['metodo_pago']}")
                    
                    # Registrar movimiento de caja si es efectivo y hay sesión activa
                    if payment['metodo_pago'] == 'EFECTIVO' and self.financial_manager and sale_data.get('caja_id'):
                        try:
                            session = self.financial_manager.get_current_session(sale_data['caja_id'])
                            if session:
                                self.financial_manager.record_sale_payment(
                                    session['id'], sale_id, payment['importe'], payment['metodo_pago']
                                )
                        except Exception as e:
                            self.logger.warning(f"No se pudo registrar en caja: {e}")
                
                # Actualizar cuenta corriente si es cliente con crédito
                if sale_data.get('cliente_id') and any(p['metodo_pago'] == 'CUENTA_CORRIENTE' for p in payments):
                    credit_amount = sum(p['importe'] for p in payments if p['metodo_pago'] == 'CUENTA_CORRIENTE')
                    if credit_amount > 0:
                        self.update_customer_account(sale_data['cliente_id'], credit_amount, 'DEBE', sale_id, user_id)
                
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
    
    def update_stock_direct(self, product_id: int, quantity_sold: float):
        """Actualizar stock directamente sin triggers problemáticos"""
        try:
            # Obtener stock actual
            result = self.db.execute_single("SELECT stock_actual FROM productos WHERE id = ?", (product_id,))
            if not result:
                raise Exception("Producto no encontrado")
            
            current_stock = float(result['stock_actual'])
            new_stock = current_stock - quantity_sold
            
            # Actualización simple sin triggers
            self.db.execute_update("UPDATE productos SET stock_actual = ? WHERE id = ?", (new_stock, product_id))
            
            # Registrar movimiento si existe la tabla
            try:
                self.db.execute_insert("""
                    INSERT INTO movimientos_stock (
                        producto_id, tipo_movimiento, motivo, cantidad_anterior,
                        cantidad_movimiento, cantidad_nueva, fecha_movimiento, usuario_id
                    ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                """, (
                    product_id, 'SALIDA', 'VENTA', current_stock, 
                    -quantity_sold, new_stock, 1
                ))
            except:
                # Si no existe la tabla de movimientos, continuar
                pass
                
        except Exception as e:
            self.logger.error(f"Error actualizando stock directo: {e}")
            raise e
    
    def get_sale_by_id(self, sale_id: int) -> Optional[Dict]:
        """Obtener venta por ID"""
        try:
            sale = self.db.execute_single("SELECT * FROM ventas WHERE id = ?", (sale_id,))
            if not sale:
                return None
            
            sale_dict = dict(sale)
            
            # Obtener items
            items = self.db.execute_query("""
                SELECT dv.*, p.nombre as producto_nombre
                FROM detalle_ventas dv
                INNER JOIN productos p ON dv.producto_id = p.id
                WHERE dv.venta_id = ?
            """, (sale_id,))
            sale_dict['items'] = [dict(item) for item in items] if items else []
            
            # Obtener pagos
            payments = self.db.execute_query("SELECT * FROM pagos_venta WHERE venta_id = ?", (sale_id,))
            sale_dict['payments'] = [dict(payment) for payment in payments] if payments else []
            
            return sale_dict
            
        except Exception as e:
            self.logger.error(f"Error obteniendo venta {sale_id}: {e}")
            return None
    
    def get_sales_by_date(self, target_date: date) -> List[Dict]:
        """Obtener ventas por fecha específica"""
        try:
            query = """
                SELECT v.*, c.nombre as cliente_nombre, c.apellido as cliente_apellido,
                       u.nombre_completo as usuario_nombre
                FROM ventas v
                LEFT JOIN clientes c ON v.cliente_id = c.id
                LEFT JOIN usuarios u ON v.usuario_id = u.id
                WHERE DATE(v.fecha_venta) = ? 
                ORDER BY v.fecha_venta DESC
            """
            
            sales = self.db.execute_query(query, (target_date,))
            return [dict(sale) for sale in sales] if sales else []
            
        except Exception as e:
            self.logger.error(f"Error obteniendo ventas por fecha {target_date}: {e}")
            return []
    
    def get_sales_by_date_range(self, date_from: date, date_to: date) -> List[Dict]:
        """Obtener ventas en un rango de fechas"""
        try:
            query = """
                SELECT v.*, c.nombre as cliente_nombre, c.apellido as cliente_apellido,
                       u.nombre_completo as usuario_nombre
                FROM ventas v
                LEFT JOIN clientes c ON v.cliente_id = c.id
                LEFT JOIN usuarios u ON v.usuario_id = u.id
                WHERE DATE(v.fecha_venta) BETWEEN ? AND ?
                ORDER BY v.fecha_venta DESC
            """
            
            sales = self.db.execute_query(query, (date_from, date_to))
            return [dict(sale) for sale in sales] if sales else []
            
        except Exception as e:
            self.logger.error(f"Error obteniendo ventas por rango {date_from} - {date_to}: {e}")
            return []
    
    def get_daily_summary(self, target_date: date = None, user_id: int = None) -> Dict:
        """Obtener resumen de ventas del día"""
        try:
            if target_date is None:
                target_date = date.today()
            
            query = """
                SELECT 
                    COUNT(*) as total_ventas,
                    COALESCE(SUM(total), 0) as monto_total,
                    COALESCE(SUM(subtotal), 0) as subtotal_total,
                    COALESCE(SUM(impuestos), 0) as impuestos_total,
                    COALESCE(SUM(descuento), 0) as descuentos_total,
                    COALESCE(AVG(total), 0) as ticket_promedio,
                    COALESCE(MIN(total), 0) as ticket_minimo,
                    COALESCE(MAX(total), 0) as ticket_maximo
                FROM ventas 
                WHERE DATE(fecha_venta) = ? AND estado = 'COMPLETADA'
            """
            
            params = [target_date]
            if user_id:
                query += " AND usuario_id = ?"
                params.append(user_id)
            
            result = self.db.execute_single(query, params)
            
            return {
                'fecha': target_date.isoformat(),
                'total_ventas': result['total_ventas'] if result else 0,
                'monto_total': float(result['monto_total'] or 0) if result else 0.0,
                'subtotal_total': float(result['subtotal_total'] or 0) if result else 0.0,
                'impuestos_total': float(result['impuestos_total'] or 0) if result else 0.0,
                'descuentos_total': float(result['descuentos_total'] or 0) if result else 0.0,
                'ticket_promedio': float(result['ticket_promedio'] or 0) if result else 0.0,
                'ticket_minimo': float(result['ticket_minimo'] or 0) if result else 0.0,
                'ticket_maximo': float(result['ticket_maximo'] or 0) if result else 0.0
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo resumen diario: {e}")
            return {'fecha': target_date.isoformat(), 'error': str(e)}
    
    def generate_invoice_number(self) -> str:
        """Generar número de factura único"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"FCT-{timestamp}"
    
    def update_customer_account(self, customer_id: int, amount: float, 
                               movement_type: str, sale_id: int, user_id: int,
                               notes: str = None):
        """Actualizar cuenta corriente del cliente"""
        try:
            # Obtener saldo actual del cliente
            customer = self.db.execute_single("SELECT saldo_cuenta_corriente FROM clientes WHERE id = ?", (customer_id,))
            if not customer:
                raise Exception("Cliente no encontrado")
            
            saldo_anterior = float(customer['saldo_cuenta_corriente'])
            
            if movement_type == 'DEBE':
                saldo_nuevo = saldo_anterior + amount
            else:  # HABER
                saldo_nuevo = saldo_anterior - amount
            
            # Actualizar saldo del cliente
            self.db.execute_update(
                "UPDATE clientes SET saldo_cuenta_corriente = ? WHERE id = ?",
                (saldo_nuevo, customer_id)
            )
            
            # Registrar movimiento
            concepto = f"Venta #{sale_id}" if sale_id else "Pago de cuenta"
            
            self.db.execute_insert("""
                INSERT INTO cuenta_corriente (
                    cliente_id, tipo_movimiento, concepto, importe,
                    saldo_anterior, saldo_nuevo, venta_id, fecha_movimiento,
                    usuario_id, notas
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
            """, (
                customer_id, movement_type, concepto, amount,
                saldo_anterior, saldo_nuevo, sale_id, user_id,
                notes or ''
            ))
            
            self.logger.info(f"Cuenta corriente actualizada: Cliente {customer_id}, {movement_type} ${amount}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error actualizando cuenta corriente: {e}")
            return False