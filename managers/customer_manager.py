"""
Gestor de Clientes Empresarial - AlmacénPro v2.0
CRM completo con análisis avanzado de clientes
"""

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import json

logger = logging.getLogger(__name__)

class CustomerManager:
    """Gestor empresarial de clientes con CRM avanzado"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
        
        # Categorías de clientes predefinidas
        self.CUSTOMER_CATEGORIES = [
            'VIP', 'MAYORISTA', 'MINORISTA', 'CORPORATIVO', 
            'DISTRIBUIDOR', 'OCASIONAL', 'GENERAL'
        ]
        
        # Configuración de análisis
        self.VIP_MINIMUM_PURCHASES = 10  # Compras mínimas para VIP
        self.VIP_MINIMUM_AMOUNT = 50000  # Monto mínimo para VIP
        
        logger.info("CustomerManager empresarial inicializado")
    
    def get_all_customers(self, active_only: bool = True) -> List[Dict]:
        """Obtener todos los clientes"""
        try:
            query = """
                SELECT * FROM clientes
                WHERE activo = 1
                ORDER BY nombre, apellido
            """
            results = self.db.execute_query(query)
            return [dict(row) for row in results] if results else []
        except Exception as e:
            logger.error(f"Error obteniendo clientes: {e}")
            return []
    
    def get_customer_by_id(self, customer_id: int) -> Optional[Dict]:
        """Obtener cliente por ID"""
        try:
            query = "SELECT * FROM clientes WHERE id = ?"
            result = self.db.execute_single(query, (customer_id,))
            return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error obteniendo cliente {customer_id}: {e}")
            return None
    
    def search_customers(self, search_term: str, limit: int = 50) -> List[Dict]:
        """Buscar clientes por nombre, apellido o documento"""
        try:
            if not search_term.strip():
                return self.get_all_customers()
            
            search_pattern = f"%{search_term.strip()}%"
            query = """
                SELECT * FROM clientes
                WHERE (nombre LIKE ? OR apellido LIKE ? OR dni_cuit LIKE ?)
                AND activo = 1
                ORDER BY nombre, apellido
                LIMIT ?
            """
            results = self.db.execute_query(query, (search_pattern, search_pattern, search_pattern, limit))
            return [dict(row) for row in results] if results else []
        except Exception as e:
            logger.error(f"Error buscando clientes: {e}")
            return []
    
    def create_customer(self, customer_data: Dict) -> Optional[int]:
        """Crear nuevo cliente"""
        try:
            query = """
                INSERT INTO clientes (
                    nombre, apellido, dni_cuit, direccion, telefono, email,
                    limite_credito, saldo_cuenta_corriente, descuento_porcentaje,
                    categoria_cliente, activo, creado_en
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            
            customer_id = self.db.execute_insert(query, (
                customer_data.get('nombre', ''),
                customer_data.get('apellido', ''),
                customer_data.get('documento_numero', customer_data.get('dni_cuit', '')),
                customer_data.get('direccion', ''),
                customer_data.get('telefono', ''),
                customer_data.get('email', ''),
                customer_data.get('limite_credito', 0),
                customer_data.get('saldo_cuenta_corriente', 0),
                customer_data.get('descuento_porcentaje', 0),
                customer_data.get('categoria_cliente', 'GENERAL'),
                True
            ))
            
            if customer_id:
                logger.info(f"Cliente creado exitosamente: ID {customer_id}")
                return customer_id
            return None
            
        except Exception as e:
            logger.error(f"Error creando cliente: {e}")
            return None
    
    def update_customer(self, customer_id: int, customer_data: Dict) -> bool:
        """Actualizar cliente existente"""
        try:
            query = """
                UPDATE clientes SET
                    nombre = ?, apellido = ?, dni_cuit = ?, direccion = ?,
                    telefono = ?, email = ?, limite_credito = ?,
                    descuento_porcentaje = ?, categoria_cliente = ?
                WHERE id = ?
            """
            
            rows_affected = self.db.execute_update(query, (
                customer_data.get('nombre', ''),
                customer_data.get('apellido', ''),
                customer_data.get('dni_cuit', ''),
                customer_data.get('direccion', ''),
                customer_data.get('telefono', ''),
                customer_data.get('email', ''),
                customer_data.get('limite_credito', 0),
                customer_data.get('descuento_porcentaje', 0),
                customer_data.get('categoria_cliente', 'GENERAL'),
                customer_id
            ))
            
            if rows_affected > 0:
                logger.info(f"Cliente {customer_id} actualizado exitosamente")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error actualizando cliente {customer_id}: {e}")
            return False
    
    def get_customers_with_debt(self) -> List[Dict]:
        """Obtener clientes que tienen deuda pendiente"""
        try:
            query = """
                SELECT * FROM clientes
                WHERE saldo_cuenta_corriente > 0 AND activo = 1
                ORDER BY saldo_cuenta_corriente DESC
            """
            results = self.db.execute_query(query)
            return [dict(row) for row in results] if results else []
        except Exception as e:
            logger.error(f"Error obteniendo clientes con deuda: {e}")
            return []
    
    def get_customer_account_movements(self, customer_id: int, limit: int = 10) -> List[Dict]:
        """Obtener movimientos de cuenta corriente de un cliente"""
        try:
            query = """
                SELECT * FROM cuenta_corriente
                WHERE cliente_id = ?
                ORDER BY fecha_movimiento DESC
                LIMIT ?
            """
            results = self.db.execute_query(query, (customer_id, limit))
            return [dict(row) for row in results] if results else []
        except Exception as e:
            logger.error(f"Error obteniendo movimientos del cliente {customer_id}: {e}")
            return []
    
    # ============================================================================
    # FUNCIONALIDADES EMPRESARIALES AVANZADAS
    # ============================================================================
    
    def get_customer_statistics(self, customer_id: int) -> Dict:
        """Obtener estadísticas completas de un cliente"""
        try:
            stats = {}
            
            # Datos básicos del cliente
            customer = self.get_customer_by_id(customer_id)
            if not customer:
                return {}
            
            stats['customer_info'] = customer
            
            # Estadísticas de ventas
            sales_stats = self.db.execute_single("""
                SELECT 
                    COUNT(*) as total_compras,
                    COALESCE(SUM(total), 0) as monto_total_comprado,
                    COALESCE(AVG(total), 0) as ticket_promedio,
                    COALESCE(MAX(total), 0) as compra_maxima,
                    MIN(fecha_venta) as primera_compra,
                    MAX(fecha_venta) as ultima_compra
                FROM ventas 
                WHERE cliente_id = ? AND estado = 'COMPLETADA'
            """, (customer_id,))
            
            if sales_stats:
                stats['sales'] = {
                    'total_compras': sales_stats['total_compras'],
                    'monto_total': float(sales_stats['monto_total_comprado'] or 0),
                    'ticket_promedio': float(sales_stats['ticket_promedio'] or 0),
                    'compra_maxima': float(sales_stats['compra_maxima'] or 0),
                    'primera_compra': sales_stats['primera_compra'],
                    'ultima_compra': sales_stats['ultima_compra']
                }
            
            # Productos más comprados
            top_products = self.db.execute_query("""
                SELECT 
                    p.nombre,
                    SUM(dv.cantidad) as cantidad_total,
                    SUM(dv.subtotal) as monto_total,
                    COUNT(DISTINCT v.id) as veces_comprado
                FROM detalle_ventas dv
                INNER JOIN ventas v ON dv.venta_id = v.id
                INNER JOIN productos p ON dv.producto_id = p.id
                WHERE v.cliente_id = ? AND v.estado = 'COMPLETADA'
                GROUP BY p.id, p.nombre
                ORDER BY cantidad_total DESC
                LIMIT 10
            """, (customer_id,))
            
            stats['top_products'] = [dict(row) for row in top_products] if top_products else []
            
            # Análisis temporal (compras por mes)
            monthly_purchases = self.db.execute_query("""
                SELECT 
                    strftime('%Y-%m', fecha_venta) as mes,
                    COUNT(*) as total_compras,
                    SUM(total) as monto_mes
                FROM ventas 
                WHERE cliente_id = ? AND estado = 'COMPLETADA'
                GROUP BY strftime('%Y-%m', fecha_venta)
                ORDER BY mes DESC
                LIMIT 12
            """, (customer_id,))
            
            stats['monthly_analysis'] = [dict(row) for row in monthly_purchases] if monthly_purchases else []
            
            # Estado de cuenta corriente
            if float(customer.get('saldo_cuenta_corriente', 0)) > 0:
                account_movements = self.get_customer_account_movements(customer_id, 5)
                stats['account_status'] = {
                    'saldo_actual': float(customer['saldo_cuenta_corriente']),
                    'limite_credito': float(customer['limite_credito']),
                    'credito_disponible': float(customer['limite_credito']) - float(customer['saldo_cuenta_corriente']),
                    'ultimos_movimientos': account_movements
                }
            
            # Clasificación del cliente
            stats['classification'] = self.classify_customer(customer_id, stats.get('sales', {}))
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas del cliente {customer_id}: {e}")
            return {}
    
    def classify_customer(self, customer_id: int, sales_data: Dict = None) -> Dict:
        """Clasificar cliente según su actividad y valor"""
        try:
            if not sales_data:
                stats = self.get_customer_statistics(customer_id)
                sales_data = stats.get('sales', {})
            
            total_compras = sales_data.get('total_compras', 0)
            monto_total = sales_data.get('monto_total', 0)
            ultima_compra = sales_data.get('ultima_compra')
            
            # Clasificación por valor
            if monto_total >= self.VIP_MINIMUM_AMOUNT and total_compras >= self.VIP_MINIMUM_PURCHASES:
                valor_categoria = 'VIP'
            elif monto_total >= 20000:
                valor_categoria = 'ALTO'
            elif monto_total >= 5000:
                valor_categoria = 'MEDIO'
            else:
                valor_categoria = 'BAJO'
            
            # Clasificación por actividad
            if ultima_compra:
                days_since_last = (datetime.now() - datetime.strptime(ultima_compra[:10], '%Y-%m-%d')).days
                if days_since_last <= 30:
                    actividad = 'ACTIVO'
                elif days_since_last <= 90:
                    actividad = 'REGULAR'
                elif days_since_last <= 180:
                    actividad = 'INACTIVO'
                else:
                    actividad = 'PERDIDO'
            else:
                actividad = 'NUEVO'
            
            # Score general (0-100)
            score = min(100, (total_compras * 2) + (monto_total / 1000))
            
            return {
                'valor': valor_categoria,
                'actividad': actividad,
                'score': int(score),
                'total_compras': total_compras,
                'monto_total': monto_total,
                'recomendacion': self.get_customer_recommendation(valor_categoria, actividad, score)
            }
            
        except Exception as e:
            self.logger.error(f"Error clasificando cliente {customer_id}: {e}")
            return {}
    
    def get_customer_recommendation(self, valor: str, actividad: str, score: int) -> str:
        """Obtener recomendación para el cliente"""
        if valor == 'VIP' and actividad == 'ACTIVO':
            return "Cliente VIP activo - Mantener beneficios especiales"
        elif valor == 'VIP' and actividad in ['REGULAR', 'INACTIVO']:
            return "Cliente VIP con baja actividad - Campaña de reactivación"
        elif valor == 'ALTO' and actividad == 'ACTIVO':
            return "Cliente de alto valor - Candidato para programa VIP"
        elif actividad == 'PERDIDO':
            return "Cliente perdido - Campaña de recuperación"
        elif actividad == 'NUEVO':
            return "Cliente nuevo - Programa de bienvenida"
        else:
            return "Cliente regular - Mantener seguimiento"
    
    def get_top_customers(self, limit: int = 20, period_days: int = 365) -> List[Dict]:
        """Obtener los mejores clientes por valor"""
        try:
            since_date = (datetime.now() - timedelta(days=period_days)).strftime('%Y-%m-%d')
            
            query = """
                SELECT 
                    c.id, c.nombre, c.apellido, c.email, c.categoria_cliente,
                    COUNT(v.id) as total_compras,
                    SUM(v.total) as monto_total,
                    AVG(v.total) as ticket_promedio,
                    MAX(v.fecha_venta) as ultima_compra
                FROM clientes c
                INNER JOIN ventas v ON c.id = v.cliente_id
                WHERE v.estado = 'COMPLETADA' 
                AND v.fecha_venta >= ?
                AND c.activo = 1
                GROUP BY c.id
                ORDER BY monto_total DESC
                LIMIT ?
            """
            
            results = self.db.execute_query(query, (since_date, limit))
            
            top_customers = []
            for row in results:
                customer = dict(row)
                customer['monto_total'] = float(customer['monto_total'])
                customer['ticket_promedio'] = float(customer['ticket_promedio'])
                
                # Añadir clasificación
                classification = self.classify_customer(customer['id'])
                customer['classification'] = classification
                
                top_customers.append(customer)
            
            return top_customers
            
        except Exception as e:
            self.logger.error(f"Error obteniendo top clientes: {e}")
            return []
    
    def get_customers_by_category(self, category: str) -> List[Dict]:
        """Obtener clientes por categoría"""
        try:
            query = """
                SELECT * FROM clientes
                WHERE categoria_cliente = ? AND activo = 1
                ORDER BY nombre, apellido
            """
            results = self.db.execute_query(query, (category,))
            return [dict(row) for row in results] if results else []
        except Exception as e:
            self.logger.error(f"Error obteniendo clientes por categoría {category}: {e}")
            return []
    
    def update_customer_category_auto(self, customer_id: int) -> bool:
        """Actualizar categoría de cliente automáticamente basado en su actividad"""
        try:
            classification = self.classify_customer(customer_id)
            
            # Determinar nueva categoría basada en clasificación
            valor = classification.get('valor', 'BAJO')
            total_compras = classification.get('total_compras', 0)
            
            if valor == 'VIP':
                new_category = 'VIP'
            elif total_compras >= 20:
                new_category = 'MAYORISTA'
            elif valor == 'ALTO':
                new_category = 'CORPORATIVO'
            elif total_compras >= 5:
                new_category = 'MINORISTA'
            else:
                new_category = 'GENERAL'
            
            # Actualizar si es diferente
            current_customer = self.get_customer_by_id(customer_id)
            if current_customer and current_customer['categoria_cliente'] != new_category:
                success = self.db.execute_update(
                    "UPDATE clientes SET categoria_cliente = ? WHERE id = ?",
                    (new_category, customer_id)
                )
                
                if success:
                    self.logger.info(f"Cliente {customer_id} reclasificado de {current_customer['categoria_cliente']} a {new_category}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error actualizando categoría automática del cliente {customer_id}: {e}")
            return False
    
    def get_inactive_customers(self, days_inactive: int = 90) -> List[Dict]:
        """Obtener clientes inactivos para campañas de reactivación"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_inactive)).strftime('%Y-%m-%d')
            
            query = """
                SELECT DISTINCT
                    c.id, c.nombre, c.apellido, c.email, c.telefono,
                    c.categoria_cliente, c.saldo_cuenta_corriente,
                    MAX(v.fecha_venta) as ultima_compra,
                    COUNT(v.id) as total_compras_historicas,
                    SUM(v.total) as monto_total_historico
                FROM clientes c
                LEFT JOIN ventas v ON c.id = v.cliente_id AND v.estado = 'COMPLETADA'
                WHERE c.activo = 1
                AND (
                    v.fecha_venta < ? OR v.fecha_venta IS NULL
                )
                GROUP BY c.id
                HAVING COUNT(v.id) > 0  -- Solo clientes que han comprado antes
                ORDER BY monto_total_historico DESC
            """
            
            results = self.db.execute_query(query, (cutoff_date,))
            
            inactive_customers = []
            for row in results:
                customer = dict(row)
                customer['monto_total_historico'] = float(customer['monto_total_historico'] or 0)
                customer['days_inactive'] = days_inactive
                
                # Calcular prioridad de reactivación
                total_historico = customer['monto_total_historico']
                if total_historico >= 50000:
                    customer['priority'] = 'ALTA'
                elif total_historico >= 10000:
                    customer['priority'] = 'MEDIA'
                else:
                    customer['priority'] = 'BAJA'
                
                inactive_customers.append(customer)
            
            return inactive_customers
            
        except Exception as e:
            self.logger.error(f"Error obteniendo clientes inactivos: {e}")
            return []
    
    def add_customer_note(self, customer_id: int, note: str, user_id: int) -> bool:
        """Añadir nota a un cliente"""
        try:
            current_customer = self.get_customer_by_id(customer_id)
            if not current_customer:
                return False
            
            # Obtener notas actuales
            current_notes = current_customer.get('notas', '') or ''
            
            # Añadir nueva nota con timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            new_note = f"[{timestamp}] {note}"
            
            if current_notes:
                updated_notes = f"{current_notes}\n{new_note}"
            else:
                updated_notes = new_note
            
            success = self.db.execute_update(
                "UPDATE clientes SET notas = ? WHERE id = ?",
                (updated_notes, customer_id)
            )
            
            if success:
                self.logger.info(f"Nota añadida al cliente {customer_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error añadiendo nota al cliente {customer_id}: {e}")
            return False
    
    def process_account_payment(self, customer_id: int, amount: float, 
                              payment_method: str, reference: str, 
                              user_id: int, notes: str = None) -> Tuple[bool, str]:
        """Procesar pago de cuenta corriente"""
        try:
            customer = self.get_customer_by_id(customer_id)
            if not customer:
                return False, "Cliente no encontrado"
            
            current_balance = float(customer.get('saldo_cuenta_corriente', 0))
            if amount > current_balance:
                return False, f"El pago (${amount:.2f}) es mayor al saldo adeudado (${current_balance:.2f})"
            
            new_balance = current_balance - amount
            
            # Iniciar transacción
            self.db.begin_transaction()
            
            try:
                # Actualizar saldo del cliente
                self.db.execute_update(
                    "UPDATE clientes SET saldo_cuenta_corriente = ? WHERE id = ?",
                    (new_balance, customer_id)
                )
                
                # Registrar movimiento en cuenta corriente
                self.db.execute_insert("""
                    INSERT INTO cuenta_corriente (
                        cliente_id, tipo_movimiento, concepto, importe,
                        saldo_anterior, saldo_nuevo, venta_id, fecha_movimiento,
                        usuario_id, notas
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
                """, (
                    customer_id, 'HABER', f"Pago {payment_method} - {reference}",
                    -amount, current_balance, new_balance, None, user_id, notes or ''
                ))
                
                self.db.commit_transaction()
                
                self.logger.info(f"Pago procesado para cliente {customer_id}: ${amount:.2f}")
                return True, f"Pago procesado correctamente. Nuevo saldo: ${new_balance:.2f}"
                
            except Exception as e:
                self.db.rollback_transaction()
                raise e
                
        except Exception as e:
            self.logger.error(f"Error procesando pago de cliente {customer_id}: {e}")
            return False, f"Error procesando pago: {str(e)}"
    
    def get_customers_dashboard_data(self) -> Dict:
        """Obtener datos para dashboard de clientes"""
        try:
            dashboard = {}
            
            # Estadísticas generales
            general_stats = self.db.execute_single("""
                SELECT 
                    COUNT(*) as total_clientes,
                    COUNT(CASE WHEN activo = 1 THEN 1 END) as clientes_activos,
                    COUNT(CASE WHEN saldo_cuenta_corriente > 0 THEN 1 END) as clientes_con_deuda,
                    SUM(CASE WHEN saldo_cuenta_corriente > 0 THEN saldo_cuenta_corriente ELSE 0 END) as deuda_total
                FROM clientes
            """)
            
            if general_stats:
                dashboard['general'] = {
                    'total_clientes': general_stats['total_clientes'],
                    'clientes_activos': general_stats['clientes_activos'],
                    'clientes_con_deuda': general_stats['clientes_con_deuda'],
                    'deuda_total': float(general_stats['deuda_total'] or 0)
                }
            
            # Distribución por categorías
            category_distribution = self.db.execute_query("""
                SELECT categoria_cliente, COUNT(*) as count
                FROM clientes 
                WHERE activo = 1
                GROUP BY categoria_cliente
                ORDER BY count DESC
            """)
            dashboard['categories'] = [dict(row) for row in category_distribution] if category_distribution else []
            
            # Clientes recientes (últimos 30 días)
            recent_customers = self.db.execute_query("""
                SELECT nombre, apellido, categoria_cliente, creado_en
                FROM clientes 
                WHERE creado_en >= datetime('now', '-30 days')
                AND activo = 1
                ORDER BY creado_en DESC
                LIMIT 10
            """)
            dashboard['recent'] = [dict(row) for row in recent_customers] if recent_customers else []
            
            # Top 5 clientes por deuda
            top_debtors = self.db.execute_query("""
                SELECT nombre, apellido, saldo_cuenta_corriente, limite_credito
                FROM clientes 
                WHERE saldo_cuenta_corriente > 0 AND activo = 1
                ORDER BY saldo_cuenta_corriente DESC
                LIMIT 5
            """)
            
            if top_debtors:
                dashboard['top_debtors'] = []
                for row in top_debtors:
                    debtor = dict(row)
                    debtor['saldo_cuenta_corriente'] = float(debtor['saldo_cuenta_corriente'])
                    debtor['limite_credito'] = float(debtor['limite_credito'])
                    dashboard['top_debtors'].append(debtor)
            
            return dashboard
            
        except Exception as e:
            self.logger.error(f"Error obteniendo datos de dashboard: {e}")
            return {}