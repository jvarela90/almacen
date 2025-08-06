"""
Gestor de Reportes para AlmacénPro
Sistema completo de generación de reportes, estadísticas y análisis de datos
"""

import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json

logger = logging.getLogger(__name__)

class ReportManager:
    """Gestor principal para reportes y estadísticas del sistema"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
        
        # Directorio para reportes generados
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
        
        # Tipos de reportes disponibles
        self.REPORT_TYPES = {
            'SALES_DAILY': 'Reporte Diario de Ventas',
            'SALES_MONTHLY': 'Reporte Mensual de Ventas',
            'SALES_YEARLY': 'Reporte Anual de Ventas',
            'INVENTORY': 'Reporte de Inventario',
            'LOW_STOCK': 'Productos con Stock Bajo',
            'TOP_PRODUCTS': 'Productos Más Vendidos',
            'TOP_CUSTOMERS': 'Mejores Clientes',
            'PROVIDERS': 'Reporte de Proveedores',
            'FINANCIAL': 'Reporte Financiero',
            'MOVEMENTS': 'Movimientos de Stock'
        }
    
    def generate_daily_sales_report(self, target_date: date = None, user_id: int = None) -> Dict:
        """Generar reporte diario de ventas"""
        try:
            if not target_date:
                target_date = date.today()
            
            # Consulta principal de ventas del día
            sales_query = """
                SELECT 
                    COUNT(*) as total_ventas,
                    COUNT(CASE WHEN estado = 'COMPLETADA' THEN 1 END) as ventas_completadas,
                    COUNT(CASE WHEN estado = 'CANCELADA' THEN 1 END) as ventas_canceladas,
                    SUM(CASE WHEN estado = 'COMPLETADA' THEN total ELSE 0 END) as monto_total,
                    SUM(CASE WHEN estado = 'COMPLETADA' THEN subtotal ELSE 0 END) as subtotal_total,
                    SUM(CASE WHEN estado = 'COMPLETADA' THEN impuestos_importe ELSE 0 END) as impuestos_total,
                    SUM(CASE WHEN estado = 'COMPLETADA' THEN descuento_importe ELSE 0 END) as descuentos_total,
                    AVG(CASE WHEN estado = 'COMPLETADA' THEN total ELSE NULL END) as ticket_promedio,
                    MIN(CASE WHEN estado = 'COMPLETADA' THEN total ELSE NULL END) as ticket_minimo,
                    MAX(CASE WHEN estado = 'COMPLETADA' THEN total ELSE NULL END) as ticket_maximo
                FROM ventas
                WHERE DATE(fecha_venta) = ?
            """
            
            params = [target_date]
            if user_id:
                sales_query += " AND usuario_id = ?"
                params.append(user_id)
            
            sales_data = self.db.execute_single(sales_query, params)
            
            # Métodos de pago
            payment_methods = self.db.execute_query("""
                SELECT pv.metodo_pago, 
                       COUNT(*) as cantidad_transacciones,
                       SUM(pv.importe) as monto_total
                FROM pagos_venta pv
                INNER JOIN ventas v ON pv.venta_id = v.id
                WHERE DATE(v.fecha_venta) = ? AND v.estado = 'COMPLETADA'
                {} 
                GROUP BY pv.metodo_pago
                ORDER BY monto_total DESC
            """.format("AND v.usuario_id = ?" if user_id else ""), params)
            
            # Productos más vendidos del día
            top_products = self.db.execute_query("""
                SELECT p.nombre, p.codigo_barras,
                       SUM(dv.cantidad) as cantidad_vendida,
                       SUM(dv.total) as monto_total,
                       COUNT(DISTINCT v.id) as transacciones
                FROM productos p
                INNER JOIN detalle_ventas dv ON p.id = dv.producto_id
                INNER JOIN ventas v ON dv.venta_id = v.id
                WHERE DATE(v.fecha_venta) = ? AND v.estado = 'COMPLETADA'
                {}
                GROUP BY p.id, p.nombre, p.codigo_barras
                ORDER BY cantidad_vendida DESC
                LIMIT 10
            """.format("AND v.usuario_id = ?" if user_id else ""), params)
            
            # Ventas por hora
            hourly_sales = self.db.execute_query("""
                SELECT 
                    strftime('%H', fecha_venta) as hora,
                    COUNT(*) as cantidad_ventas,
                    SUM(total) as monto_total
                FROM ventas
                WHERE DATE(fecha_venta) = ? AND estado = 'COMPLETADA'
                {}
                GROUP BY strftime('%H', fecha_venta)
                ORDER BY hora
            """.format("AND usuario_id = ?" if user_id else ""), params)
            
            # Armar reporte
            report = {
                'tipo': 'SALES_DAILY',
                'fecha': target_date.isoformat(),
                'generado_en': datetime.now().isoformat(),
                'usuario_id': user_id,
                'resumen': {
                    'total_ventas': sales_data.get('total_ventas', 0),
                    'ventas_completadas': sales_data.get('ventas_completadas', 0),
                    'ventas_canceladas': sales_data.get('ventas_canceladas', 0),
                    'monto_total': float(sales_data.get('monto_total', 0) or 0),
                    'subtotal_total': float(sales_data.get('subtotal_total', 0) or 0),
                    'impuestos_total': float(sales_data.get('impuestos_total', 0) or 0),
                    'descuentos_total': float(sales_data.get('descuentos_total', 0) or 0),
                    'ticket_promedio': float(sales_data.get('ticket_promedio', 0) or 0),
                    'ticket_minimo': float(sales_data.get('ticket_minimo', 0) or 0),
                    'ticket_maximo': float(sales_data.get('ticket_maximo', 0) or 0)
                },
                'metodos_pago': [dict(row) for row in payment_methods],
                'productos_top': [dict(row) for row in top_products],
                'ventas_por_hora': [dict(row) for row in hourly_sales]
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generando reporte diario: {e}")
            return {'error': str(e)}
    
    def generate_monthly_sales_report(self, year: int, month: int, user_id: int = None) -> Dict:
        """Generar reporte mensual de ventas"""
        try:
            # Fechas del mes
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
            
            # Estadísticas generales del mes
            monthly_stats = self.db.execute_single("""
                SELECT 
                    COUNT(*) as total_ventas,
                    COUNT(CASE WHEN estado = 'COMPLETADA' THEN 1 END) as ventas_completadas,
                    SUM(CASE WHEN estado = 'COMPLETADA' THEN total ELSE 0 END) as monto_total,
                    AVG(CASE WHEN estado = 'COMPLETADA' THEN total ELSE NULL END) as ticket_promedio,
                    COUNT(DISTINCT cliente_id) as clientes_unicos,
                    COUNT(DISTINCT DATE(fecha_venta)) as dias_con_ventas
                FROM ventas
                WHERE DATE(fecha_venta) BETWEEN ? AND ?
                {}
            """.format("AND usuario_id = ?" if user_id else ""), 
            [start_date, end_date] + ([user_id] if user_id else []))
            
            # Ventas por día del mes
            daily_sales = self.db.execute_query("""
                SELECT 
                    DATE(fecha_venta) as fecha,
                    COUNT(*) as cantidad_ventas,
                    SUM(CASE WHEN estado = 'COMPLETADA' THEN total ELSE 0 END) as monto_total
                FROM ventas
                WHERE DATE(fecha_venta) BETWEEN ? AND ?
                {}
                GROUP BY DATE(fecha_venta)
                ORDER BY fecha
            """.format("AND usuario_id = ?" if user_id else ""), 
            [start_date, end_date] + ([user_id] if user_id else []))
            
            # Top productos del mes
            top_products_month = self.db.execute_query("""
                SELECT p.nombre, p.codigo_barras, c.nombre as categoria,
                       SUM(dv.cantidad) as cantidad_vendida,
                       SUM(dv.total) as monto_total,
                       COUNT(DISTINCT v.id) as transacciones
                FROM productos p
                INNER JOIN detalle_ventas dv ON p.id = dv.producto_id
                INNER JOIN ventas v ON dv.venta_id = v.id
                LEFT JOIN categorias c ON p.categoria_id = c.id
                WHERE DATE(v.fecha_venta) BETWEEN ? AND ? AND v.estado = 'COMPLETADA'
                {}
                GROUP BY p.id, p.nombre, p.codigo_barras, c.nombre
                ORDER BY monto_total DESC
                LIMIT 20
            """.format("AND v.usuario_id = ?" if user_id else ""), 
            [start_date, end_date] + ([user_id] if user_id else []))
            
            # Comparación con mes anterior
            prev_month_start = start_date - timedelta(days=start_date.day)
            prev_month_start = prev_month_start.replace(day=1)
            prev_month_end = start_date - timedelta(days=1)
            
            prev_month_stats = self.db.execute_single("""
                SELECT 
                    COUNT(CASE WHEN estado = 'COMPLETADA' THEN 1 END) as ventas_completadas,
                    SUM(CASE WHEN estado = 'COMPLETADA' THEN total ELSE 0 END) as monto_total
                FROM ventas
                WHERE DATE(fecha_venta) BETWEEN ? AND ?
                {}
            """.format("AND usuario_id = ?" if user_id else ""), 
            [prev_month_start, prev_month_end] + ([user_id] if user_id else []))
            
            # Calcular variaciones
            current_sales = monthly_stats.get('ventas_completadas', 0)
            current_amount = float(monthly_stats.get('monto_total', 0) or 0)
            prev_sales = prev_month_stats.get('ventas_completadas', 0) if prev_month_stats else 0
            prev_amount = float(prev_month_stats.get('monto_total', 0) or 0) if prev_month_stats else 0
            
            sales_growth = ((current_sales - prev_sales) / prev_sales * 100) if prev_sales > 0 else 0
            amount_growth = ((current_amount - prev_amount) / prev_amount * 100) if prev_amount > 0 else 0
            
            report = {
                'tipo': 'SALES_MONTHLY',
                'periodo': f"{year}-{month:02d}",
                'generado_en': datetime.now().isoformat(),
                'usuario_id': user_id,
                'resumen': {
                    **dict(monthly_stats),
                    'monto_total': current_amount,
                    'ticket_promedio': float(monthly_stats.get('ticket_promedio', 0) or 0),
                    'crecimiento_ventas_pct': round(sales_growth, 2),
                    'crecimiento_monto_pct': round(amount_growth, 2)
                },
                'ventas_diarias': [dict(row) for row in daily_sales],
                'productos_top': [dict(row) for row in top_products_month],
                'comparacion_mes_anterior': {
                    'ventas_anteriores': prev_sales,
                    'monto_anterior': prev_amount
                }
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generando reporte mensual: {e}")
            return {'error': str(e)}
    
    def generate_inventory_report(self, category_id: int = None, low_stock_only: bool = False) -> Dict:
        """Generar reporte de inventario"""
        try:
            base_query = """
                SELECT p.*, c.nombre as categoria_nombre, pr.nombre as proveedor_nombre,
                       (p.stock_actual * p.precio_compra) as valor_stock_compra,
                       (p.stock_actual * p.precio_venta) as valor_stock_venta,
                       CASE 
                           WHEN p.stock_minimo > 0 AND p.stock_actual <= p.stock_minimo THEN 'BAJO' 
                           WHEN p.stock_actual = 0 THEN 'SIN_STOCK'
                           ELSE 'NORMAL' 
                       END as estado_stock
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
                WHERE p.activo = 1
            """
            
            params = []
            
            if category_id:
                base_query += " AND p.categoria_id = ?"
                params.append(category_id)
            
            if low_stock_only:
                base_query += " AND (p.stock_actual <= p.stock_minimo OR p.stock_actual = 0)"
            
            base_query += " ORDER BY p.nombre"
            
            products = self.db.execute_query(base_query, params)
            
            # Estadísticas generales
            total_products = len(products)
            total_stock_value_cost = sum(float(p.get('valor_stock_compra', 0) or 0) for p in products)
            total_stock_value_sale = sum(float(p.get('valor_stock_venta', 0) or 0) for p in products)
            
            # Contadores por estado
            stock_counts = {
                'NORMAL': len([p for p in products if p['estado_stock'] == 'NORMAL']),
                'BAJO': len([p for p in products if p['estado_stock'] == 'BAJO']),
                'SIN_STOCK': len([p for p in products if p['estado_stock'] == 'SIN_STOCK'])
            }
            
            # Productos por categoría
            categories_stats = {}
            for product in products:
                cat_name = product.get('categoria_nombre', 'Sin Categoría')
                if cat_name not in categories_stats:
                    categories_stats[cat_name] = {
                        'productos': 0,
                        'valor_compra': 0,
                        'valor_venta': 0
                    }
                
                categories_stats[cat_name]['productos'] += 1
                categories_stats[cat_name]['valor_compra'] += float(product.get('valor_stock_compra', 0) or 0)
                categories_stats[cat_name]['valor_venta'] += float(product.get('valor_stock_venta', 0) or 0)
            
            report = {
                'tipo': 'INVENTORY',
                'generado_en': datetime.now().isoformat(),
                'filtros': {
                    'categoria_id': category_id,
                    'solo_stock_bajo': low_stock_only
                },
                'resumen': {
                    'total_productos': total_products,
                    'valor_total_compra': total_stock_value_cost,
                    'valor_total_venta': total_stock_value_sale,
                    'ganancia_potencial': total_stock_value_sale - total_stock_value_cost,
                    'productos_stock_normal': stock_counts['NORMAL'],
                    'productos_stock_bajo': stock_counts['BAJO'],
                    'productos_sin_stock': stock_counts['SIN_STOCK']
                },
                'por_categoria': categories_stats,
                'productos': [dict(p) for p in products]
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generando reporte de inventario: {e}")
            return {'error': str(e)}
    
    def generate_top_products_report(self, period_days: int = 30, limit: int = 50) -> Dict:
        """Generar reporte de productos más vendidos"""
        try:
            start_date = date.today() - timedelta(days=period_days)
            
            top_products = self.db.execute_query("""
                SELECT p.nombre, p.codigo_barras, c.nombre as categoria_nombre,
                       SUM(dv.cantidad) as cantidad_vendida,
                       SUM(dv.total) as monto_total,
                       COUNT(DISTINCT v.id) as transacciones,
                       AVG(dv.precio_unitario) as precio_promedio,
                       p.stock_actual,
                       p.stock_minimo,
                       (SUM(dv.total) - SUM(dv.cantidad * COALESCE(p.precio_compra, 0))) as ganancia_bruta
                FROM productos p
                INNER JOIN detalle_ventas dv ON p.id = dv.producto_id
                INNER JOIN ventas v ON dv.venta_id = v.id
                LEFT JOIN categorias c ON p.categoria_id = c.id
                WHERE DATE(v.fecha_venta) >= ? AND v.estado = 'COMPLETADA'
                GROUP BY p.id, p.nombre, p.codigo_barras, c.nombre, p.stock_actual, p.stock_minimo
                ORDER BY cantidad_vendida DESC
                LIMIT ?
            """, (start_date, limit))
            
            # Estadísticas del período
            period_stats = self.db.execute_single("""
                SELECT 
                    COUNT(DISTINCT p.id) as productos_vendidos,
                    SUM(dv.cantidad) as cantidad_total,
                    SUM(dv.total) as monto_total
                FROM productos p
                INNER JOIN detalle_ventas dv ON p.id = dv.producto_id
                INNER JOIN ventas v ON dv.venta_id = v.id
                WHERE DATE(v.fecha_venta) >= ? AND v.estado = 'COMPLETADA'
            """, (start_date,))
            
            report = {
                'tipo': 'TOP_PRODUCTS',
                'periodo_dias': period_days,
                'fecha_desde': start_date.isoformat(),
                'fecha_hasta': date.today().isoformat(),
                'generado_en': datetime.now().isoformat(),
                'resumen': dict(period_stats) if period_stats else {},
                'productos': [dict(row) for row in top_products]
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generando reporte de productos top: {e}")
            return {'error': str(e)}
    
    def generate_financial_report(self, start_date: date, end_date: date) -> Dict:
        """Generar reporte financiero"""
        try:
            # Ingresos por ventas
            sales_income = self.db.execute_single("""
                SELECT 
                    SUM(total) as ingresos_brutos,
                    SUM(subtotal) as ingresos_netos,
                    SUM(impuestos_importe) as impuestos_recaudados,
                    SUM(descuento_importe) as descuentos_otorgados,
                    COUNT(*) as cantidad_transacciones
                FROM ventas
                WHERE DATE(fecha_venta) BETWEEN ? AND ? AND estado = 'COMPLETADA'
            """, (start_date, end_date))
            
            # Costos por compras
            purchase_costs = self.db.execute_single("""
                SELECT 
                    SUM(total) as costos_compras,
                    COUNT(*) as cantidad_compras
                FROM compras
                WHERE DATE(fecha_compra) BETWEEN ? AND ? AND estado = 'COMPLETADA'
            """, (start_date, end_date))
            
            # Margen bruto estimado (basado en productos vendidos)
            gross_margin = self.db.execute_single("""
                SELECT 
                    SUM(dv.total) as ingresos_productos,
                    SUM(dv.cantidad * COALESCE(p.precio_compra, 0)) as costos_productos,
                    SUM(dv.total - (dv.cantidad * COALESCE(p.precio_compra, 0))) as margen_bruto
                FROM detalle_ventas dv
                INNER JOIN ventas v ON dv.venta_id = v.id
                INNER JOIN productos p ON dv.producto_id = p.id
                WHERE DATE(v.fecha_venta) BETWEEN ? AND ? AND v.estado = 'COMPLETADA'
            """, (start_date, end_date))
            
            # Métodos de pago
            payment_methods = self.db.execute_query("""
                SELECT pv.metodo_pago, 
                       SUM(pv.importe) as monto_total,
                       COUNT(*) as cantidad_transacciones
                FROM pagos_venta pv
                INNER JOIN ventas v ON pv.venta_id = v.id
                WHERE DATE(v.fecha_venta) BETWEEN ? AND ? AND v.estado = 'COMPLETADA'
                GROUP BY pv.metodo_pago
                ORDER BY monto_total DESC
            """, (start_date, end_date))
            
            # Calcular ratios
            ingresos_brutos = float(sales_income.get('ingresos_brutos', 0) or 0)
            costos_compras = float(purchase_costs.get('costos_compras', 0) or 0)
            margen_bruto_value = float(gross_margin.get('margen_bruto', 0) or 0)
            
            margen_bruto_pct = (margen_bruto_value / ingresos_brutos * 100) if ingresos_brutos > 0 else 0
            
            report = {
                'tipo': 'FINANCIAL',
                'periodo': {
                    'fecha_inicio': start_date.isoformat(),
                    'fecha_fin': end_date.isoformat(),
                    'dias': (end_date - start_date).days + 1
                },
                'generado_en': datetime.now().isoformat(),
                'ingresos': dict(sales_income) if sales_income else {},
                'costos': dict(purchase_costs) if purchase_costs else {},
                'margen': dict(gross_margin) if gross_margin else {},
                'ratios': {
                    'margen_bruto_porcentaje': round(margen_bruto_pct, 2),
                    'ingresos_por_dia': round(ingresos_brutos / ((end_date - start_date).days + 1), 2) if ingresos_brutos > 0 else 0
                },
                'metodos_pago': [dict(row) for row in payment_methods]
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generando reporte financiero: {e}")
            return {'error': str(e)}
    
    def generate_stock_movements_report(self, start_date: date, end_date: date, 
                                      product_id: int = None) -> Dict:
        """Generar reporte de movimientos de stock"""
        try:
            query = """
                SELECT ms.*, p.nombre as producto_nombre, p.codigo_barras,
                       u.nombre_completo as usuario_nombre
                FROM movimientos_stock ms
                INNER JOIN productos p ON ms.producto_id = p.id
                LEFT JOIN usuarios u ON ms.usuario_id = u.id
                WHERE DATE(ms.fecha_movimiento) BETWEEN ? AND ?
            """
            
            params = [start_date, end_date]
            
            if product_id:
                query += " AND ms.producto_id = ?"
                params.append(product_id)
            
            query += " ORDER BY ms.fecha_movimiento DESC"
            
            movements = self.db.execute_query(query, params)
            
            # Estadísticas por tipo de movimiento
            movement_stats = self.db.execute_query("""
                SELECT 
                    tipo_movimiento,
                    COUNT(*) as cantidad_movimientos,
                    SUM(ABS(cantidad_movimiento)) as cantidad_total
                FROM movimientos_stock
                WHERE DATE(fecha_movimiento) BETWEEN ? AND ?
                {}
                GROUP BY tipo_movimiento
            """.format("AND producto_id = ?" if product_id else ""), 
            params if not product_id else params)
            
            report = {
                'tipo': 'MOVEMENTS',
                'periodo': {
                    'fecha_inicio': start_date.isoformat(),
                    'fecha_fin': end_date.isoformat()
                },
                'producto_id': product_id,
                'generado_en': datetime.now().isoformat(),
                'resumen': [dict(row) for row in movement_stats],
                'movimientos': [dict(row) for row in movements]
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generando reporte de movimientos: {e}")
            return {'error': str(e)}
    
    def save_report_to_file(self, report: Dict, filename: str = None) -> str:
        """Guardar reporte en archivo JSON"""
        try:
            if not filename:
                report_type = report.get('tipo', 'UNKNOWN')
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{report_type}_{timestamp}.json"
            
            filepath = self.reports_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Reporte guardado: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error guardando reporte: {e}")
            raise e
    
    def get_report_summary(self, report_type: str = None, days: int = 30) -> Dict:
        """Obtener resumen rápido de reportes"""
        try:
            summary = {}
            
            # Resumen de ventas
            sales_summary = self.generate_daily_sales_report()
            if 'error' not in sales_summary:
                summary['ventas_hoy'] = sales_summary['resumen']
            
            # Productos con stock bajo
            low_stock = self.generate_inventory_report(low_stock_only=True)
            if 'error' not in low_stock:
                summary['stock_bajo'] = {
                    'productos_stock_bajo': low_stock['resumen']['productos_stock_bajo'],
                    'productos_sin_stock': low_stock['resumen']['productos_sin_stock']
                }
            
            # Top productos últimos días
            top_products = self.generate_top_products_report(period_days=days, limit=5)
            if 'error' not in top_products:
                summary['top_productos'] = top_products['productos'][:5]
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generando resumen de reportes: {e}")
            return {'error': str(e)}
    
    def get_available_reports(self) -> List[Dict]:
        """Obtener lista de tipos de reportes disponibles"""
        return [
            {'code': code, 'name': name} 
            for code, name in self.REPORT_TYPES.items()
        ]
    
    def cleanup_old_reports(self, days_to_keep: int = 30):
        """Limpiar reportes antiguos"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            deleted_count = 0
            
            for report_file in self.reports_dir.glob("*.json"):
                try:
                    file_time = datetime.fromtimestamp(report_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        report_file.unlink()
                        deleted_count += 1
                except Exception as e:
                    self.logger.warning(f"Error eliminando reporte {report_file}: {e}")
            
            if deleted_count > 0:
                self.logger.info(f"Limpieza de reportes completada: {deleted_count} archivos eliminados")
                
        except Exception as e:
            self.logger.error(f"Error limpiando reportes antiguos: {e}")