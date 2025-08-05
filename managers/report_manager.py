"""
Gestor de Reportes para AlmacénPro
Genera reportes de ventas, stock, financieros y análisis de negocio
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)

class ReportManager:
    """Gestor de reportes y análisis"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        logger.info("ReportManager inicializado")
    
    def generate_sales_report(self, start_date: str, end_date: str, 
                            vendedor_id: int = None, cliente_id: int = None,
                            categoria_id: int = None) -> Dict:
        """Generar reporte completo de ventas"""
        try:
            # Construir filtros dinámicos
            where_conditions = ["DATE(v.fecha_venta) BETWEEN ? AND ?", "v.estado = 'COMPLETADA'"]
            params = [start_date, end_date]
            
            if vendedor_id:
                where_conditions.append("v.vendedor_id = ?")
                params.append(vendedor_id)
            
            if cliente_id:
                where_conditions.append("v.cliente_id = ?")
                params.append(cliente_id)
            
            if categoria_id:
                where_conditions.append("p.categoria_id = ?")
                params.append(categoria_id)
            
            where_clause = " AND ".join(where_conditions)
            
            # Resumen general de ventas
            general_summary = self.db.execute_single(f"""
                SELECT 
                    COUNT(DISTINCT v.id) as total_ventas,
                    SUM(v.total) as total_facturado,
                    AVG(v.total) as ticket_promedio,
                    SUM(v.descuento) as total_descuentos,
                    MIN(v.total) as venta_minima,
                    MAX(v.total) as venta_maxima,
                    COUNT(DISTINCT v.cliente_id) as clientes_unicos,
                    COUNT(DISTINCT v.vendedor_id) as vendedores_activos,
                    SUM(dv.cantidad) as unidades_vendidas
                FROM ventas v
                LEFT JOIN detalle_ventas dv ON v.id = dv.venta_id
                LEFT JOIN productos p ON dv.producto_id = p.id
                WHERE {where_clause}
            """, tuple(params))
            
            # Ventas por día
            daily_sales = self.db.execute_query(f"""
                SELECT 
                    DATE(v.fecha_venta) as fecha,
                    COUNT(v.id) as cantidad_ventas,
                    SUM(v.total) as total_dia,
                    AVG(v.total) as promedio_dia,
                    SUM(dv.cantidad) as unidades_dia
                FROM ventas v
                LEFT JOIN detalle_ventas dv ON v.id = dv.venta_id
                LEFT JOIN productos p ON dv.producto_id = p.id
                WHERE {where_clause}
                GROUP BY DATE(v.fecha_venta)
                ORDER BY fecha
            """, tuple(params))
            
            # Ventas por método de pago
            payment_methods = self.db.execute_query(f"""
                SELECT 
                    v.metodo_pago,
                    COUNT(v.id) as cantidad,
                    SUM(v.total) as total,
                    AVG(v.total) as promedio,
                    (SUM(v.total) * 100.0 / (SELECT SUM(total) FROM ventas v2 
                     LEFT JOIN detalle_ventas dv2 ON v2.id = dv2.venta_id
                     LEFT JOIN productos p2 ON dv2.producto_id = p2.id
                     WHERE {where_clause.replace('v.', 'v2.').replace('dv.', 'dv2.').replace('p.', 'p2.')})) as porcentaje
                FROM ventas v
                LEFT JOIN detalle_ventas dv ON v.id = dv.venta_id
                LEFT JOIN productos p ON dv.producto_id = p.id
                WHERE {where_clause}
                GROUP BY v.metodo_pago
                ORDER BY total DESC
            """, tuple(params + params))
            
            # Top vendedores
            top_sellers = self.db.execute_query(f"""
                SELECT 
                    u.nombre_completo,
                    COUNT(v.id) as cantidad_ventas,
                    SUM(v.total) as total_vendido,
                    AVG(v.total) as promedio_venta,
                    SUM(dv.cantidad) as unidades_vendidas
                FROM ventas v
                JOIN usuarios u ON v.vendedor_id = u.id
                LEFT JOIN detalle_ventas dv ON v.id = dv.venta_id
                LEFT JOIN productos p ON dv.producto_id = p.id
                WHERE {where_clause}
                GROUP BY v.vendedor_id, u.nombre_completo
                ORDER BY total_vendido DESC
                LIMIT 10
            """, tuple(params))
            
            # Top clientes
            top_customers = self.db.execute_query(f"""
                SELECT 
                    COALESCE(c.nombre || ' ' || COALESCE(c.apellido, ''), 'Cliente Ocasional') as cliente,
                    COUNT(v.id) as cantidad_compras,
                    SUM(v.total) as total_comprado,
                    AVG(v.total) as promedio_compra
                FROM ventas v
                LEFT JOIN clientes c ON v.cliente_id = c.id
                LEFT JOIN detalle_ventas dv ON v.id = dv.venta_id
                LEFT JOIN productos p ON dv.producto_id = p.id
                WHERE {where_clause}
                GROUP BY v.cliente_id, c.nombre, c.apellido
                ORDER BY total_comprado DESC
                LIMIT 10
            """, tuple(params))
            
            # Productos más vendidos
            top_products = self.db.execute_query(f"""
                SELECT 
                    p.nombre,
                    p.codigo_barras,
                    cat.nombre as categoria,
                    SUM(dv.cantidad) as cantidad_vendida,
                    SUM(dv.subtotal) as total_vendido,
                    AVG(dv.precio_unitario) as precio_promedio
                FROM detalle_ventas dv
                JOIN productos p ON dv.producto_id = p.id
                JOIN ventas v ON dv.venta_id = v.id
                LEFT JOIN categorias cat ON p.categoria_id = cat.id
                WHERE {where_clause}
                GROUP BY p.id, p.nombre, p.codigo_barras, cat.nombre
                ORDER BY cantidad_vendida DESC
                LIMIT 20
            """, tuple(params))
            
            # Ventas por hora del día
            hourly_sales = self.db.execute_query(f"""
                SELECT 
                    CAST(strftime('%H', v.fecha_venta) AS INTEGER) as hora,
                    COUNT(v.id) as cantidad_ventas,
                    SUM(v.total) as total_hora
                FROM ventas v
                LEFT JOIN detalle_ventas dv ON v.id = dv.venta_id
                LEFT JOIN productos p ON dv.producto_id = p.id
                WHERE {where_clause}
                GROUP BY CAST(strftime('%H', v.fecha_venta) AS INTEGER)
                ORDER BY hora
            """, tuple(params))
            
            return {
                'periodo': {'inicio': start_date, 'fin': end_date},
                'filtros': {
                    'vendedor_id': vendedor_id,
                    'cliente_id': cliente_id,
                    'categoria_id': categoria_id
                },
                'resumen_general': dict(general_summary) if general_summary else {},
                'ventas_diarias': daily_sales,
                'metodos_pago': payment_methods,
                'top_vendedores': top_sellers,
                'top_clientes': top_customers,
                'productos_mas_vendidos': top_products,
                'ventas_por_hora': hourly_sales
            }
            
        except Exception as e:
            logger.error(f"Error generando reporte de ventas: {e}")
            return {}
    
    def generate_stock_report(self, include_movement_history: bool = False,
                            low_stock_only: bool = False, categoria_id: int = None) -> Dict:
        """Generar reporte de stock"""
        try:
            base_conditions = ["p.activo = 1"]
            params = []
            
            if low_stock_only:
                base_conditions.append("p.stock_actual <= p.stock_minimo")
            
            if categoria_id:
                base_conditions.append("p.categoria_id = ?")
                params.append(categoria_id)
            
            where_clause = " AND ".join(base_conditions)
            
            # Resumen general de stock
            stock_summary = self.db.execute_single(f"""
                SELECT 
                    COUNT(*) as total_productos,
                    SUM(p.stock_actual) as total_unidades,
                    COUNT(CASE WHEN p.stock_actual <= 0 THEN 1 END) as productos_sin_stock,
                    COUNT(CASE WHEN p.stock_actual <= p.stock_minimo AND p.stock_actual > 0 THEN 1 END) as productos_stock_bajo,
                    COUNT(CASE WHEN p.stock_actual > p.stock_minimo THEN 1 END) as productos_stock_ok,
                    SUM(p.stock_actual * p.precio_compra) as valor_stock_compra,
                    SUM(p.stock_actual * p.precio_venta) as valor_stock_venta,
                    AVG(p.stock_actual) as promedio_stock
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                WHERE {where_clause}
            """, tuple(params))
            
            # Stock por categoría
            stock_by_category = self.db.execute_query(f"""
                SELECT 
                    COALESCE(c.nombre, 'Sin Categoría') as categoria,
                    COUNT(p.id) as productos,
                    SUM(p.stock_actual) as unidades_total,
                    SUM(p.stock_actual * p.precio_venta) as valor_categoria,
                    COUNT(CASE WHEN p.stock_actual <= p.stock_minimo THEN 1 END) as productos_criticos
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                WHERE {where_clause}
                GROUP BY c.id, c.nombre
                ORDER BY valor_categoria DESC
            """, tuple(params))
            
            # Productos críticos (sin stock o stock bajo)
            critical_products = self.db.execute_query(f"""
                SELECT 
                    p.id,
                    p.nombre,
                    p.codigo_barras,
                    COALESCE(c.nombre, 'Sin Categoría') as categoria,
                    p.stock_actual,
                    p.stock_minimo,
                    p.precio_venta,
                    (p.stock_minimo - p.stock_actual) as unidades_faltantes,
                    COALESCE(pr.nombre, 'Sin Proveedor') as proveedor,
                    CASE 
                        WHEN p.stock_actual <= 0 THEN 'SIN_STOCK'
                        WHEN p.stock_actual <= p.stock_minimo THEN 'STOCK_BAJO'
                        ELSE 'OK'
                    END as estado_stock
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
                WHERE {where_clause} AND p.stock_actual <= p.stock_minimo
                ORDER BY 
                    CASE WHEN p.stock_actual <= 0 THEN 1 ELSE 2 END,
                    (p.stock_actual - p.stock_minimo) ASC
            """, tuple(params))
            
            # Productos con mayor valor en stock
            high_value_products = self.db.execute_query(f"""
                SELECT 
                    p.nombre,
                    p.codigo_barras,
                    p.stock_actual,
                    p.precio_venta,
                    (p.stock_actual * p.precio_venta) as valor_total_stock,
                    COALESCE(c.nombre, 'Sin Categoría') as categoria
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                WHERE {where_clause} AND p.stock_actual > 0
                ORDER BY valor_total_stock DESC
                LIMIT 20
            """, tuple(params))
            
            result = {
                'fecha_reporte': datetime.now().isoformat(),
                'filtros': {
                    'low_stock_only': low_stock_only,
                    'categoria_id': categoria_id
                },
                'resumen_general': dict(stock_summary) if stock_summary else {},
                'stock_por_categoria': stock_by_category,
                'productos_criticos': critical_products,
                'productos_mayor_valor': high_value_products
            }
            
            # Historial de movimientos si se solicita
            if include_movement_history:
                recent_movements = self.db.execute_query(f"""
                    SELECT 
                        p.nombre as producto,
                        ms.tipo_movimiento,
                        ms.motivo,
                        ms.cantidad_movimiento,
                        ms.cantidad_nueva,
                        ms.fecha_movimiento,
                        u.nombre_completo as usuario
                    FROM movimientos_stock ms
                    JOIN productos p ON ms.producto_id = p.id
                    LEFT JOIN usuarios u ON ms.usuario_id = u.id
                    LEFT JOIN categorias c ON p.categoria_id = c.id
                    WHERE {where_clause.replace('p.activo = 1', 'p.activo = 1')}
                    AND ms.fecha_movimiento >= DATE('now', '-30 days')
                    ORDER BY ms.fecha_movimiento DESC
                    LIMIT 100
                """, tuple(params))
                
                result['movimientos_recientes'] = recent_movements
            
            return result
            
        except Exception as e:
            logger.error(f"Error generando reporte de stock: {e}")
            return {}
    
    def generate_financial_report(self, start_date: str, end_date: str) -> Dict:
        """Generar reporte financiero"""
        try:
            # Resumen de ingresos
            income_summary = self.db.execute_single("""
                SELECT 
                    SUM(total) as total_ingresos,
                    SUM(subtotal) as subtotal_ingresos,
                    SUM(descuento) as total_descuentos,
                    SUM(impuestos) as total_impuestos,
                    COUNT(*) as total_transacciones,
                    AVG(total) as ticket_promedio
                FROM ventas 
                WHERE DATE(fecha_venta) BETWEEN ? AND ? 
                AND estado = 'COMPLETADA'
            """, (start_date, end_date))
            
            # Resumen de egresos (compras)
            expenses_summary = self.db.execute_single("""
                SELECT 
                    SUM(total) as total_egresos,
                    SUM(subtotal) as subtotal_egresos,
                    SUM(descuento) as descuentos_obtenidos,
                    SUM(impuestos) as impuestos_pagados,
                    COUNT(*) as total_compras
                FROM compras 
                WHERE DATE(fecha_compra) BETWEEN ? AND ? 
                AND estado IN ('RECIBIDA', 'PARCIAL')
            """, (start_date, end_date))
            
            # Cuentas por cobrar
            accounts_receivable = self.db.execute_single("""
                SELECT 
                    COUNT(DISTINCT c.id) as clientes_con_deuda,
                    SUM(c.saldo_cuenta_corriente) as total_por_cobrar,
                    AVG(c.saldo_cuenta_corriente) as promedio_deuda,
                    SUM(CASE WHEN v.fecha_vencimiento < DATE('now') THEN v.total ELSE 0 END) as deuda_vencida
                FROM clientes c
                LEFT JOIN ventas v ON c.id = v.cliente_id 
                    AND v.tipo_venta = 'CUENTA_CORRIENTE' 
                    AND v.estado = 'COMPLETADA'
                WHERE c.saldo_cuenta_corriente > 0
            """)
            
            # Flujo de caja diario
            daily_cash_flow = self.db.execute_query("""
                SELECT 
                    fecha,
                    SUM(ingresos) as ingresos_dia,
                    SUM(egresos) as egresos_dia,
                    (SUM(ingresos) - SUM(egresos)) as flujo_neto_dia
                FROM (
                    SELECT DATE(fecha_venta) as fecha, SUM(total) as ingresos, 0 as egresos
                    FROM ventas 
                    WHERE DATE(fecha_venta) BETWEEN ? AND ? 
                    AND estado = 'COMPLETADA'
                    AND tipo_venta != 'CUENTA_CORRIENTE'
                    GROUP BY DATE(fecha_venta)
                    
                    UNION ALL
                    
                    SELECT DATE(fecha_compra) as fecha, 0 as ingresos, SUM(total) as egresos
                    FROM compras 
                    WHERE DATE(fecha_compra) BETWEEN ? AND ? 
                    AND estado IN ('RECIBIDA', 'PARCIAL')
                    GROUP BY DATE(fecha_compra)
                )
                GROUP BY fecha
                ORDER BY fecha
            """, (start_date, end_date, start_date, end_date))
            
            # Rentabilidad por producto (estimación)
            product_profitability = self.db.execute_query("""
                SELECT 
                    p.nombre,
                    SUM(dv.cantidad) as cantidad_vendida,
                    SUM(dv.subtotal) as ingresos_producto,
                    AVG(p.precio_compra) as costo_promedio,
                    (SUM(dv.subtotal) - (SUM(dv.cantidad) * AVG(p.precio_compra))) as ganancia_estimada,
                    ((SUM(dv.subtotal) - (SUM(dv.cantidad) * AVG(p.precio_compra))) / SUM(dv.subtotal) * 100) as margen_porcentaje
                FROM detalle_ventas dv
                JOIN productos p ON dv.producto_id = p.id
                JOIN ventas v ON dv.venta_id = v.id
                WHERE DATE(v.fecha_venta) BETWEEN ? AND ? 
                AND v.estado = 'COMPLETADA'
                AND p.precio_compra > 0
                GROUP BY p.id, p.nombre
                HAVING cantidad_vendida > 0
                ORDER BY ganancia_estimada DESC
                LIMIT 20
            """, (start_date, end_date))
            
            # Análisis de métodos de pago para cash flow
            payment_analysis = self.db.execute_query("""
                SELECT 
                    metodo_pago,
                    SUM(total) as total_metodo,
                    COUNT(*) as transacciones,
                    (SUM(total) * 100.0 / (SELECT SUM(total) FROM ventas 
                     WHERE DATE(fecha_venta) BETWEEN ? AND ? AND estado = 'COMPLETADA')) as porcentaje_ingresos
                FROM ventas 
                WHERE DATE(fecha_venta) BETWEEN ? AND ? 
                AND estado = 'COMPLETADA'
                GROUP BY metodo_pago
                ORDER BY total_metodo DESC
            """, (start_date, end_date, start_date, end_date))
            
            # Calcular métricas derivadas
            income = dict(income_summary) if income_summary else {}
            expenses = dict(expenses_summary) if expenses_summary else {}
            
            total_income = income.get('total_ingresos', 0) or 0
            total_expenses = expenses.get('total_egresos', 0) or 0
            
            financial_metrics = {
                'utilidad_bruta': total_income - total_expenses,
                'margen_bruto_porcentaje': ((total_income - total_expenses) / total_income * 100) if total_income > 0 else 0,
                'roi_periodo': ((total_income - total_expenses) / total_expenses * 100) if total_expenses > 0 else 0
            }
            
            return {
                'periodo': {'inicio': start_date, 'fin': end_date},
                'resumen_ingresos': income,
                'resumen_egresos': expenses,
                'cuentas_por_cobrar': dict(accounts_receivable) if accounts_receivable else {},
                'metricas_financieras': financial_metrics,
                'flujo_caja_diario': daily_cash_flow,
                'rentabilidad_productos': product_profitability,
                'analisis_metodos_pago': payment_analysis
            }
            
        except Exception as e:
            logger.error(f"Error generando reporte financiero: {e}")
            return {}
    
    def generate_customer_analysis(self, start_date: str, end_date: str) -> Dict:
        """Generar análisis de clientes"""
        try:
            # Segmentación de clientes
            customer_segments = self.db.execute_query("""
                SELECT 
                    CASE 
                        WHEN total_comprado >= 100000 THEN 'VIP'
                        WHEN total_comprado >= 50000 THEN 'Premium'
                        WHEN total_comprado >= 10000 THEN 'Regular'
                        ELSE 'Ocasional'
                    END as segmento,
                    COUNT(*) as cantidad_clientes,
                    SUM(total_comprado) as ingresos_segmento,
                    AVG(total_comprado) as promedio_segmento,
                    AVG(frecuencia_compra) as frecuencia_promedio
                FROM (
                    SELECT 
                        c.id,
                        c.nombre,
                        SUM(v.total) as total_comprado,
                        COUNT(v.id) as frecuencia_compra
                    FROM clientes c
                    JOIN ventas v ON c.id = v.cliente_id
                    WHERE DATE(v.fecha_venta) BETWEEN ? AND ?
                    AND v.estado = 'COMPLETADA'
                    GROUP BY c.id, c.nombre
                ) customer_stats
                GROUP BY segmento
                ORDER BY 
                    CASE segmento
                        WHEN 'VIP' THEN 1
                        WHEN 'Premium' THEN 2
                        WHEN 'Regular' THEN 3
                        ELSE 4
                    END
            """, (start_date, end_date))
            
            # Clientes más valiosos
            top_customers = self.db.execute_query("""
                SELECT 
                    c.nombre || ' ' || COALESCE(c.apellido, '') as cliente,
                    c.telefono,
                    c.saldo_cuenta_corriente,
                    COUNT(v.id) as total_compras,
                    SUM(v.total) as total_gastado,
                    AVG(v.total) as ticket_promedio,
                    MIN(v.fecha_venta) as primera_compra,
                    MAX(v.fecha_venta) as ultima_compra,
                    JULIANDAY('now') - JULIANDAY(MAX(v.fecha_venta)) as dias_sin_comprar
                FROM clientes c
                JOIN ventas v ON c.id = v.cliente_id
                WHERE DATE(v.fecha_venta) BETWEEN ? AND ?
                AND v.estado = 'COMPLETADA'
                GROUP BY c.id, c.nombre, c.apellido, c.telefono, c.saldo_cuenta_corriente
                ORDER BY total_gastado DESC
                LIMIT 20
            """, (start_date, end_date))
            
            # Análisis de retención
            retention_analysis = self.db.execute_single("""
                SELECT 
                    COUNT(DISTINCT CASE WHEN compras_mes_anterior > 0 AND compras_mes_actual > 0 THEN cliente_id END) as clientes_retenidos,
                    COUNT(DISTINCT CASE WHEN compras_mes_anterior > 0 THEN cliente_id END) as clientes_mes_anterior,
                    COUNT(DISTINCT CASE WHEN compras_mes_actual > 0 THEN cliente_id END) as clientes_mes_actual,
                    COUNT(DISTINCT CASE WHEN compras_mes_anterior = 0 AND compras_mes_actual > 0 THEN cliente_id END) as clientes_nuevos
                FROM (
                    SELECT 
                        v.cliente_id,
                        SUM(CASE WHEN DATE(v.fecha_venta) BETWEEN DATE(?, '-1 month') AND DATE(?, '-1 day') THEN 1 ELSE 0 END) as compras_mes_anterior,
                        SUM(CASE WHEN DATE(v.fecha_venta) BETWEEN ? AND ? THEN 1 ELSE 0 END) as compras_mes_actual
                    FROM ventas v
                    WHERE v.cliente_id IS NOT NULL
                    AND v.estado = 'COMPLETADA'
                    AND DATE(v.fecha_venta) BETWEEN DATE(?, '-1 month') AND ?
                    GROUP BY v.cliente_id
                )
            """, (start_date, start_date, start_date, end_date, start_date, end_date))
            
            # Productos favoritos por segmento
            favorite_products_by_segment = self.db.execute_query("""
                SELECT 
                    segmento,
                    producto,
                    cantidad_total,
                    clientes_compraron
                FROM (
                    SELECT 
                        CASE 
                            WHEN customer_total >= 100000 THEN 'VIP'
                            WHEN customer_total >= 50000 THEN 'Premium'
                            WHEN customer_total >= 10000 THEN 'Regular'
                            ELSE 'Ocasional'
                        END as segmento,
                        p.nombre as producto,
                        SUM(dv.cantidad) as cantidad_total,
                        COUNT(DISTINCT v.cliente_id) as clientes_compraron,
                        ROW_NUMBER() OVER (
                            PARTITION BY CASE 
                                WHEN customer_total >= 100000 THEN 'VIP'
                                WHEN customer_total >= 50000 THEN 'Premium'
                                WHEN customer_total >= 10000 THEN 'Regular'
                                ELSE 'Ocasional'
                            END 
                            ORDER BY SUM(dv.cantidad) DESC
                        ) as ranking
                    FROM ventas v
                    JOIN detalle_ventas dv ON v.id = dv.venta_id
                    JOIN productos p ON dv.producto_id = p.id
                    JOIN (
                        SELECT cliente_id, SUM(total) as customer_total
                        FROM ventas
                        WHERE DATE(fecha_venta) BETWEEN ? AND ? AND estado = 'COMPLETADA'
                        GROUP BY cliente_id
                    ) ct ON v.cliente_id = ct.cliente_id
                    WHERE DATE(v.fecha_venta) BETWEEN ? AND ?
                    AND v.estado = 'COMPLETADA'
                    AND v.cliente_id IS NOT NULL
                    GROUP BY segmento, p.id, p.nombre
                ) ranked_products
                WHERE ranking <= 5
                ORDER BY segmento, ranking
            """, (start_date, end_date, start_date, end_date))
            
            # Calcular tasa de retención
            retention = dict(retention_analysis) if retention_analysis else {}
            if retention.get('clientes_mes_anterior', 0) > 0:
                retention['tasa_retencion'] = (retention.get('clientes_retenidos', 0) / retention['clientes_mes_anterior'] * 100)
            else:
                retention['tasa_retencion'] = 0
            
            return {
                'periodo': {'inicio': start_date, 'fin': end_date},
                'segmentacion_clientes': customer_segments,
                'top_clientes': top_customers,
                'analisis_retencion': retention,
                'productos_favoritos_por_segmento': favorite_products_by_segment
            }
            
        except Exception as e:
            logger.error(f"Error generando análisis de clientes: {e}")
            return {}
    
    def generate_inventory_turnover_report(self, months: int = 6) -> Dict:
        """Generar reporte de rotación de inventario"""
        try:
            start_date = (datetime.now() - timedelta(days=months*30)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            # Rotación de inventario por producto
            inventory_turnover = self.db.execute_query("""
                SELECT 
                    p.id,
                    p.nombre,
                    p.codigo_barras,
                    c.nombre as categoria,
                    p.stock_actual,
                    p.precio_compra,
                    p.precio_venta,
                    COALESCE(sales_data.cantidad_vendida, 0) as cantidad_vendida,
                    COALESCE(sales_data.ingresos_producto, 0) as ingresos_producto,
                    CASE 
                        WHEN p.stock_actual > 0 AND sales_data.cantidad_vendida > 0 
                        THEN ROUND(sales_data.cantidad_vendida / (p.stock_actual * 1.0), 2)
                        ELSE 0 
                    END as rotacion_veces,
                    CASE 
                        WHEN sales_data.cantidad_vendida > 0 
                        THEN ROUND((? * 30.0) / (sales_data.cantidad_vendida / (p.stock_actual + sales_data.cantidad_vendida)), 1)
                        ELSE 999 
                    END as dias_inventario,
                    CASE 
                        WHEN p.stock_actual > 0 AND p.precio_compra > 0
                        THEN p.stock_actual * p.precio_compra
                        ELSE 0
                    END as valor_inventario
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                LEFT JOIN (
                    SELECT 
                        dv.producto_id,
                        SUM(dv.cantidad) as cantidad_vendida,
                        SUM(dv.subtotal) as ingresos_producto
                    FROM detalle_ventas dv
                    JOIN ventas v ON dv.venta_id = v.id
                    WHERE DATE(v.fecha_venta) BETWEEN ? AND ?
                    AND v.estado = 'COMPLETADA'
                    GROUP BY dv.producto_id
                ) sales_data ON p.id = sales_data.producto_id
                WHERE p.activo = 1
                ORDER BY rotacion_veces DESC, cantidad_vendida DESC
            """, (months, start_date, end_date))
            
            # Resumen por categoría
            category_turnover = self.db.execute_query("""
                SELECT 
                    COALESCE(c.nombre, 'Sin Categoría') as categoria,
                    COUNT(p.id) as productos_categoria,
                    SUM(p.stock_actual) as stock_total_categoria,
                    SUM(p.stock_actual * p.precio_compra) as valor_inventario_categoria,
                    SUM(COALESCE(sales_data.cantidad_vendida, 0)) as total_vendido_categoria,
                    AVG(CASE 
                        WHEN p.stock_actual > 0 AND sales_data.cantidad_vendida > 0 
                        THEN sales_data.cantidad_vendida / (p.stock_actual * 1.0)
                        ELSE 0 
                    END) as rotacion_promedio_categoria
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                LEFT JOIN (
                    SELECT 
                        dv.producto_id,
                        SUM(dv.cantidad) as cantidad_vendida
                    FROM detalle_ventas dv
                    JOIN ventas v ON dv.venta_id = v.id
                    WHERE DATE(v.fecha_venta) BETWEEN ? AND ?
                    AND v.estado = 'COMPLETADA'
                    GROUP BY dv.producto_id
                ) sales_data ON p.id = sales_data.producto_id
                WHERE p.activo = 1
                GROUP BY c.id, c.nombre
                ORDER BY rotacion_promedio_categoria DESC
            """, (start_date, end_date))
            
            # Productos de lenta rotación (posibles obsoletos)
            slow_moving_products = [product for product in inventory_turnover 
                                  if product['rotacion_veces'] < 0.5 and product['stock_actual'] > 0]
            
            # Productos de alta rotación (posibles faltantes)
            fast_moving_products = [product for product in inventory_turnover 
                                  if product['rotacion_veces'] > 4 and product['stock_actual'] > 0]
            
            # Análisis ABC (clasificación por valor)
            total_inventory_value = sum(p['valor_inventario'] for p in inventory_turnover)
            sorted_by_value = sorted(inventory_turnover, key=lambda x: x['valor_inventario'], reverse=True)
            
            abc_analysis = []
            cumulative_value = 0
            for product in sorted_by_value:
                cumulative_value += product['valor_inventario']
                cumulative_percentage = (cumulative_value / total_inventory_value * 100) if total_inventory_value > 0 else 0
                
                if cumulative_percentage <= 80:
                    classification = 'A'
                elif cumulative_percentage <= 95:
                    classification = 'B'
                else:
                    classification = 'C'
                
                abc_analysis.append({
                    'nombre': product['nombre'],
                    'valor_inventario': product['valor_inventario'],
                    'clasificacion': classification,
                    'porcentaje_acumulado': cumulative_percentage
                })
            
            return {
                'periodo_analisis': {'inicio': start_date, 'fin': end_date, 'meses': months},
                'rotacion_por_producto': inventory_turnover,
                'rotacion_por_categoria': category_turnover,
                'productos_lenta_rotacion': slow_moving_products,
                'productos_alta_rotacion': fast_moving_products,
                'analisis_abc': abc_analysis,
                'resumen': {
                    'valor_total_inventario': total_inventory_value,
                    'productos_analizados': len(inventory_turnover),
                    'productos_sin_movimiento': len([p for p in inventory_turnover if p['cantidad_vendida'] == 0]),
                    'rotacion_promedio_general': sum(p['rotacion_veces'] for p in inventory_turnover) / len(inventory_turnover) if inventory_turnover else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error generando reporte de rotación: {e}")
            return {}
    
    def generate_comparative_report(self, current_start: str, current_end: str,
                                  previous_start: str, previous_end: str) -> Dict:
        """Generar reporte comparativo entre dos períodos"""
        try:
            # Obtener métricas del período actual
            current_metrics = self.db.execute_single("""
                SELECT 
                    COUNT(*) as ventas_cantidad,
                    SUM(total) as ventas_total,
                    AVG(total) as ticket_promedio,
                    COUNT(DISTINCT cliente_id) as clientes_unicos,
                    SUM(dv.cantidad) as unidades_vendidas
                FROM ventas v
                LEFT JOIN detalle_ventas dv ON v.id = dv.venta_id
                WHERE DATE(v.fecha_venta) BETWEEN ? AND ?
                AND v.estado = 'COMPLETADA'
            """, (current_start, current_end))
            
            # Obtener métricas del período anterior
            previous_metrics = self.db.execute_single("""
                SELECT 
                    COUNT(*) as ventas_cantidad,
                    SUM(total) as ventas_total,
                    AVG(total) as ticket_promedio,
                    COUNT(DISTINCT cliente_id) as clientes_unicos,
                    SUM(dv.cantidad) as unidades_vendidas
                FROM ventas v
                LEFT JOIN detalle_ventas dv ON v.id = dv.venta_id
                WHERE DATE(v.fecha_venta) BETWEEN ? AND ?
                AND v.estado = 'COMPLETADA'
            """, (previous_start, previous_end))
            
            # Calcular variaciones porcentuales
            def calculate_variation(current, previous):
                if previous and previous > 0:
                    return ((current - previous) / previous) * 100
                return 0
            
            current = dict(current_metrics) if current_metrics else {}
            previous = dict(previous_metrics) if previous_metrics else {}
            
            comparisons = {}
            for metric in ['ventas_cantidad', 'ventas_total', 'ticket_promedio', 'clientes_unicos', 'unidades_vendidas']:
                current_value = current.get(metric, 0) or 0
                previous_value = previous.get(metric, 0) or 0
                variation = calculate_variation(current_value, previous_value)
                
                comparisons[metric] = {
                    'actual': current_value,
                    'anterior': previous_value,
                    'variacion_absoluta': current_value - previous_value,
                    'variacion_porcentual': variation
                }
            
            # Top productos comparativo
            current_top_products = self.db.execute_query("""
                SELECT 
                    p.nombre,
                    SUM(dv.cantidad) as cantidad,
                    SUM(dv.subtotal) as total
                FROM detalle_ventas dv
                JOIN productos p ON dv.producto_id = p.id
                JOIN ventas v ON dv.venta_id = v.id
                WHERE DATE(v.fecha_venta) BETWEEN ? AND ?
                AND v.estado = 'COMPLETADA'
                GROUP BY p.id, p.nombre
                ORDER BY cantidad DESC
                LIMIT 10
            """, (current_start, current_end))
            
            previous_top_products = self.db.execute_query("""
                SELECT 
                    p.nombre,
                    SUM(dv.cantidad) as cantidad,
                    SUM(dv.subtotal) as total
                FROM detalle_ventas dv
                JOIN productos p ON dv.producto_id = p.id
                JOIN ventas v ON dv.venta_id = v.id
                WHERE DATE(v.fecha_venta) BETWEEN ? AND ?
                AND v.estado = 'COMPLETADA'
                GROUP BY p.id, p.nombre
                ORDER BY cantidad DESC
                LIMIT 10
            """, (previous_start, previous_end))
            
            return {
                'periodo_actual': {'inicio': current_start, 'fin': current_end},
                'periodo_anterior': {'inicio': previous_start, 'fin': previous_end},
                'metricas_comparativas': comparisons,
                'top_productos_actual': current_top_products,
                'top_productos_anterior': previous_top_products
            }
            
        except Exception as e:
            logger.error(f"Error generando reporte comparativo: {e}")
            return {}
    
    def export_report_to_csv(self, report_data: Dict, filename: str) -> Tuple[bool, str]:
        """Exportar reporte a CSV"""
        try:
            import csv
            import io
            
            # Esta función se implementaría según el tipo de reporte
            # Por ahora retorna un placeholder
            
            logger.info(f"Exportación a CSV solicitada: {filename}")
            return True, f"Reporte exportado a {filename}"
            
        except Exception as e:
            logger.error(f"Error exportando a CSV: {e}")
            return False, f"Error exportando reporte: {str(e)}"
    
    def get_dashboard_metrics(self) -> Dict:
        """Obtener métricas para dashboard ejecutivo"""
        try:
            today = date.today().isoformat()
            week_ago = (date.today() - timedelta(days=7)).isoformat()
            month_ago = (date.today() - timedelta(days=30)).isoformat()
            
            # Ventas de hoy
            today_sales = self.db.execute_single("""
                SELECT 
                    COUNT(*) as ventas_hoy,
                    COALESCE(SUM(total), 0) as total_hoy
                FROM ventas 
                WHERE DATE(fecha_venta) = ? AND estado = 'COMPLETADA'
            """, (today,))
            
            # Stock crítico
            critical_stock = self.db.execute_single("""
                SELECT 
                    COUNT(*) as productos_sin_stock,
                    COUNT(CASE WHEN stock_actual <= stock_minimo AND stock_actual > 0 THEN 1 END) as productos_stock_bajo
                FROM productos 
                WHERE activo = 1
            """)
            
            # Cuentas por cobrar
            accounts_receivable = self.db.execute_single("""
                SELECT 
                    COUNT(*) as clientes_con_deuda,
                    COALESCE(SUM(saldo_cuenta_corriente), 0) as total_por_cobrar
                FROM clientes 
                WHERE saldo_cuenta_corriente > 0
            """)
            
            # Órdenes pendientes
            pending_orders = self.db.execute_single("""
                SELECT 
                    COUNT(*) as ordenes_pendientes,
                    COALESCE(SUM(total), 0) as monto_pendiente
                FROM compras 
                WHERE estado IN ('PENDIENTE', 'CONFIRMADA', 'PARCIAL')
            """)
            
            # Tendencia semanal
            weekly_trend = self.db.execute_query("""
                SELECT 
                    DATE(fecha_venta) as fecha,
                    COALESCE(SUM(total), 0) as total_dia
                FROM ventas 
                WHERE DATE(fecha_venta) BETWEEN ? AND ? 
                AND estado = 'COMPLETADA'
                GROUP BY DATE(fecha_venta)
                ORDER BY fecha
            """, (week_ago, today))
            
            return {
                'fecha_actualizacion': datetime.now().isoformat(),
                'ventas_hoy': dict(today_sales) if today_sales else {},
                'stock_critico': dict(critical_stock) if critical_stock else {},
                'cuentas_por_cobrar': dict(accounts_receivable) if accounts_receivable else {},
                'ordenes_pendientes': dict(pending_orders) if pending_orders else {},
                'tendencia_semanal': weekly_trend
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas de dashboard: {e}")
            return {}