"""
Gestor de Proveedores para AlmacénPro
Maneja proveedores, contactos y relaciones comerciales
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date

logger = logging.getLogger(__name__)

class ProviderManager:
    """Gestor de proveedores"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        logger.info("ProviderManager inicializado")
    
    def create_provider(self, provider_data: Dict) -> Tuple[bool, str, int]:
        """Crear nuevo proveedor"""
        try:
            # Validaciones básicas
            if not provider_data.get('nombre') or not provider_data['nombre'].strip():
                return False, "El nombre del proveedor es obligatorio", 0
            
            # Verificar CUIT único (si se proporciona)
            if provider_data.get('cuit_dni'):
                existing = self.db.execute_single("""
                    SELECT id FROM proveedores WHERE cuit_dni = ? AND activo = 1
                """, (provider_data['cuit_dni'],))
                
                if existing:
                    return False, "Ya existe un proveedor con ese CUIT/DNI", 0
            
            # Validar email (si se proporciona)
            if provider_data.get('email') and '@' not in provider_data['email']:
                return False, "El formato del email no es válido", 0
            
            # Crear proveedor
            provider_id = self.db.execute_insert("""
                INSERT INTO proveedores (
                    nombre, cuit_dni, direccion, ciudad, provincia, codigo_postal,
                    telefono, telefono_alternativo, email, sitio_web,
                    contacto_principal, cargo_contacto, condiciones_pago,
                    descuento_porcentaje, limite_credito, calificacion, notas
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                provider_data['nombre'].strip(),
                provider_data.get('cuit_dni', '').strip() or None,
                provider_data.get('direccion', '').strip() or None,
                provider_data.get('ciudad', '').strip() or None,
                provider_data.get('provincia', '').strip() or None,
                provider_data.get('codigo_postal', '').strip() or None,
                provider_data.get('telefono', '').strip() or None,
                provider_data.get('telefono_alternativo', '').strip() or None,
                provider_data.get('email', '').strip() or None,
                provider_data.get('sitio_web', '').strip() or None,
                provider_data.get('contacto_principal', '').strip() or None,
                provider_data.get('cargo_contacto', '').strip() or None,
                provider_data.get('condiciones_pago', '').strip() or None,
                provider_data.get('descuento_porcentaje', 0),
                provider_data.get('limite_credito', 0),
                provider_data.get('calificacion', 5),
                provider_data.get('notas', '').strip() or None
            ))
            
            logger.info(f"Proveedor creado: {provider_data['nombre']} (ID: {provider_id})")
            return True, f"Proveedor '{provider_data['nombre']}' creado exitosamente", provider_id
            
        except Exception as e:
            logger.error(f"Error creando proveedor: {e}")
            return False, f"Error creando proveedor: {str(e)}", 0
    
    def get_provider_by_id(self, provider_id: int) -> Optional[Dict]:
        """Obtener proveedor por ID"""
        try:
            provider = self.db.execute_single("""
                SELECT * FROM proveedores WHERE id = ?
            """, (provider_id,))
            
            if provider:
                # Agregar estadísticas básicas
                stats = self.get_provider_statistics(provider_id)
                provider_dict = dict(provider)
                provider_dict['estadisticas'] = stats
                return provider_dict
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo proveedor: {e}")
            return None
    
    def get_all_providers(self, active_only: bool = True, 
                         include_stats: bool = False) -> List[Dict]:
        """Obtener lista de todos los proveedores"""
        try:
            query = "SELECT * FROM proveedores"
            
            if active_only:
                query += " WHERE activo = 1"
            
            query += " ORDER BY nombre"
            
            providers = self.db.execute_query(query)
            
            if include_stats:
                for provider in providers:
                    provider['estadisticas'] = self.get_provider_statistics(provider['id'])
            
            return providers
            
        except Exception as e:
            logger.error(f"Error obteniendo proveedores: {e}")
            return []
    
    def search_providers(self, search_term: str) -> List[Dict]:
        """Buscar proveedores por nombre, CUIT o contacto"""
        try:
            search_term = search_term.strip()
            if not search_term:
                return []
            
            providers = self.db.execute_query("""
                SELECT * FROM proveedores 
                WHERE (
                    nombre LIKE ? OR 
                    cuit_dni LIKE ? OR 
                    contacto_principal LIKE ? OR
                    email LIKE ?
                ) AND activo = 1
                ORDER BY 
                    CASE 
                        WHEN nombre LIKE ? THEN 1
                        WHEN cuit_dni LIKE ? THEN 2
                        ELSE 3
                    END,
                    nombre
                LIMIT 50
            """, (
                f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%",
                f"{search_term}%", f"{search_term}%"
            ))
            
            return providers
            
        except Exception as e:
            logger.error(f"Error buscando proveedores: {e}")
            return []
    
    def update_provider(self, provider_id: int, provider_data: Dict) -> Tuple[bool, str]:
        """Actualizar proveedor existente"""
        try:
            # Verificar que el proveedor existe
            existing_provider = self.get_provider_by_id(provider_id)
            if not existing_provider:
                return False, "Proveedor no encontrado"
            
            # Validaciones
            if 'nombre' in provider_data and not provider_data['nombre'].strip():
                return False, "El nombre del proveedor es obligatorio"
            
            # Verificar CUIT único (si se está cambiando)
            if 'cuit_dni' in provider_data and provider_data['cuit_dni']:
                existing = self.db.execute_single("""
                    SELECT id FROM proveedores 
                    WHERE cuit_dni = ? AND id != ? AND activo = 1
                """, (provider_data['cuit_dni'], provider_id))
                
                if existing:
                    return False, "Ya existe otro proveedor con ese CUIT/DNI"
            
            # Validar email
            if 'email' in provider_data and provider_data['email'] and '@' not in provider_data['email']:
                return False, "El formato del email no es válido"
            
            # Construir query de actualización dinámicamente
            update_fields = []
            update_values = []
            
            allowed_fields = [
                'nombre', 'cuit_dni', 'direccion', 'ciudad', 'provincia', 'codigo_postal',
                'telefono', 'telefono_alternativo', 'email', 'sitio_web',
                'contacto_principal', 'cargo_contacto', 'condiciones_pago',
                'descuento_porcentaje', 'limite_credito', 'calificacion', 'notas', 'activo'
            ]
            
            for field, value in provider_data.items():
                if field in allowed_fields:
                    update_fields.append(f"{field} = ?")
                    # Limpiar strings vacíos a NULL
                    if isinstance(value, str) and not value.strip():
                        update_values.append(None)
                    else:
                        update_values.append(value)
            
            if not update_fields:
                return False, "No hay campos válidos para actualizar"
            
            # Agregar timestamp de actualización
            update_fields.append("actualizado_en = CURRENT_TIMESTAMP")
            update_values.append(provider_id)
            
            query = f"UPDATE proveedores SET {', '.join(update_fields)} WHERE id = ?"
            
            rows_affected = self.db.execute_update(query, tuple(update_values))
            
            if rows_affected > 0:
                logger.info(f"Proveedor actualizado: ID {provider_id}")
                return True, "Proveedor actualizado exitosamente"
            else:
                return False, "No se pudo actualizar el proveedor"
                
        except Exception as e:
            logger.error(f"Error actualizando proveedor: {e}")
            return False, f"Error actualizando proveedor: {str(e)}"
    
    def deactivate_provider(self, provider_id: int, reason: str = None) -> Tuple[bool, str]:
        """Desactivar proveedor (eliminación lógica)"""
        try:
            # Verificar si tiene compras pendientes
            pending_purchases = self.db.execute_single("""
                SELECT COUNT(*) as count FROM compras 
                WHERE proveedor_id = ? AND estado IN ('PENDIENTE', 'CONFIRMADA', 'PARCIAL')
            """, (provider_id,))
            
            if pending_purchases and pending_purchases['count'] > 0:
                return False, f"No se puede desactivar: tiene {pending_purchases['count']} compras pendientes"
            
            # Verificar si tiene productos asignados
            assigned_products = self.db.execute_single("""
                SELECT COUNT(*) as count FROM productos 
                WHERE proveedor_id = ? AND activo = 1
            """, (provider_id,))
            
            if assigned_products and assigned_products['count'] > 0:
                # Advertir pero permitir la desactivación
                logger.warning(f"Proveedor {provider_id} tiene {assigned_products['count']} productos asignados")
            
            # Desactivar proveedor
            notes_update = f"DESACTIVADO: {reason}" if reason else "DESACTIVADO"
            
            rows_affected = self.db.execute_update("""
                UPDATE proveedores 
                SET activo = 0, 
                    notas = COALESCE(notas || '\n', '') || ?,
                    actualizado_en = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (notes_update, provider_id))
            
            if rows_affected > 0:
                logger.info(f"Proveedor desactivado: ID {provider_id}")
                return True, "Proveedor desactivado exitosamente"
            else:
                return False, "Proveedor no encontrado"
                
        except Exception as e:
            logger.error(f"Error desactivando proveedor: {e}")
            return False, f"Error desactivando proveedor: {str(e)}"
    
    def get_provider_statistics(self, provider_id: int) -> Dict:
        """Obtener estadísticas del proveedor"""
        try:
            # Estadísticas de compras
            purchase_stats = self.db.execute_single("""
                SELECT 
                    COUNT(*) as total_ordenes,
                    SUM(total) as total_comprado,
                    AVG(total) as promedio_orden,
                    MAX(fecha_compra) as ultima_compra,
                    MIN(fecha_compra) as primera_compra,
                    SUM(CASE WHEN estado = 'RECIBIDA' THEN 1 ELSE 0 END) as ordenes_completadas,
                    SUM(CASE WHEN estado IN ('PENDIENTE', 'CONFIRMADA', 'PARCIAL') THEN 1 ELSE 0 END) as ordenes_pendientes
                FROM compras 
                WHERE proveedor_id = ?
            """, (provider_id,))
            
            # Productos suministrados
            products_stats = self.db.execute_single("""
                SELECT 
                    COUNT(*) as productos_asignados,
                    COUNT(CASE WHEN activo = 1 THEN 1 END) as productos_activos
                FROM productos 
                WHERE proveedor_id = ?
            """, (provider_id,))
            
            # Últimas compras
            recent_purchases = self.db.execute_query("""
                SELECT fecha_compra, total, estado
                FROM compras 
                WHERE proveedor_id = ?
                ORDER BY fecha_compra DESC
                LIMIT 5
            """, (provider_id,))
            
            # Promedio de días entre compras
            avg_days_between = self.db.execute_single("""
                SELECT AVG(dias_entre_compras) as promedio_dias
                FROM (
                    SELECT JULIANDAY(fecha_compra) - LAG(JULIANDAY(fecha_compra)) 
                           OVER (ORDER BY fecha_compra) as dias_entre_compras
                    FROM compras 
                    WHERE proveedor_id = ? AND estado != 'CANCELADA'
                ) WHERE dias_entre_compras IS NOT NULL
            """, (provider_id,))
            
            return {
                'compras': dict(purchase_stats) if purchase_stats else {},
                'productos': dict(products_stats) if products_stats else {},
                'compras_recientes': recent_purchases,
                'promedio_dias_entre_compras': avg_days_between['promedio_dias'] if avg_days_between and avg_days_between['promedio_dias'] else None
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del proveedor: {e}")
            return {}
    
    def get_provider_products(self, provider_id: int, active_only: bool = True) -> List[Dict]:
        """Obtener productos del proveedor"""
        try:
            query = """
                SELECT p.*, c.nombre as categoria_nombre
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                WHERE p.proveedor_id = ?
            """
            
            params = [provider_id]
            
            if active_only:
                query += " AND p.activo = 1"
            
            query += " ORDER BY p.nombre"
            
            return self.db.execute_query(query, tuple(params))
            
        except Exception as e:
            logger.error(f"Error obteniendo productos del proveedor: {e}")
            return []
    
    def get_provider_purchases(self, provider_id: int, start_date: str = None, 
                             end_date: str = None, status: str = None) -> List[Dict]:
        """Obtener compras del proveedor"""
        try:
            query = """
                SELECT c.*, u.nombre_completo as usuario_nombre
                FROM compras c
                LEFT JOIN usuarios u ON c.usuario_id = u.id
                WHERE c.proveedor_id = ?
            """
            
            params = [provider_id]
            
            if start_date and end_date:
                query += " AND DATE(c.fecha_compra) BETWEEN ? AND ?"
                params.extend([start_date, end_date])
            
            if status:
                query += " AND c.estado = ?"
                params.append(status)
            
            query += " ORDER BY c.fecha_compra DESC"
            
            return self.db.execute_query(query, tuple(params))
            
        except Exception as e:
            logger.error(f"Error obteniendo compras del proveedor: {e}")
            return []
    
    def update_provider_rating(self, provider_id: int, rating: int, 
                             reason: str = None) -> Tuple[bool, str]:
        """Actualizar calificación del proveedor"""
        try:
            if rating < 1 or rating > 5:
                return False, "La calificación debe estar entre 1 y 5"
            
            notes_update = ""
            if reason:
                current_date = datetime.now().strftime("%Y-%m-%d")
                notes_update = f"\n[{current_date}] Calificación: {rating}/5 - {reason}"
            
            rows_affected = self.db.execute_update("""
                UPDATE proveedores 
                SET calificacion = ?,
                    notas = COALESCE(notas, '') || ?,
                    actualizado_en = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (rating, notes_update, provider_id))
            
            if rows_affected > 0:
                logger.info(f"Calificación actualizada: Proveedor {provider_id} -> {rating}/5")
                return True, f"Calificación actualizada a {rating}/5"
            else:
                return False, "Proveedor no encontrado"
                
        except Exception as e:
            logger.error(f"Error actualizando calificación: {e}")
            return False, f"Error actualizando calificación: {str(e)}"
    
    def get_providers_by_rating(self, min_rating: int = 1, max_rating: int = 5) -> List[Dict]:
        """Obtener proveedores por rango de calificación"""
        try:
            return self.db.execute_query("""
                SELECT p.*, 
                       COUNT(c.id) as total_compras,
                       SUM(c.total) as total_comprado
                FROM proveedores p
                LEFT JOIN compras c ON p.id = c.proveedor_id AND c.estado != 'CANCELADA'
                WHERE p.calificacion BETWEEN ? AND ? AND p.activo = 1
                GROUP BY p.id
                ORDER BY p.calificacion DESC, p.nombre
            """, (min_rating, max_rating))
            
        except Exception as e:
            logger.error(f"Error obteniendo proveedores por calificación: {e}")
            return []
    
    def get_provider_contact_info(self, provider_id: int) -> Dict:
        """Obtener información de contacto del proveedor"""
        try:
            provider = self.db.execute_single("""
                SELECT nombre, telefono, telefono_alternativo, email, 
                       contacto_principal, cargo_contacto, direccion,
                       ciudad, provincia, codigo_postal, sitio_web
                FROM proveedores 
                WHERE id = ? AND activo = 1
            """, (provider_id,))
            
            return dict(provider) if provider else {}
            
        except Exception as e:
            logger.error(f"Error obteniendo info de contacto: {e}")
            return {}
    
    def get_top_providers_by_volume(self, start_date: str, end_date: str, 
                                   limit: int = 10) -> List[Dict]:
        """Obtener principales proveedores por volumen de compras"""
        try:
            return self.db.execute_query("""
                SELECT 
                    p.id,
                    p.nombre,
                    p.telefono,
                    p.email,
                    p.calificacion,
                    COUNT(c.id) as total_ordenes,
                    SUM(c.total) as total_comprado,
                    AVG(c.total) as promedio_orden,
                    MAX(c.fecha_compra) as ultima_compra
                FROM proveedores p
                JOIN compras c ON p.id = c.proveedor_id
                WHERE DATE(c.fecha_compra) BETWEEN ? AND ?
                AND c.estado != 'CANCELADA'
                AND p.activo = 1
                GROUP BY p.id, p.nombre, p.telefono, p.email, p.calificacion
                ORDER BY total_comprado DESC
                LIMIT ?
            """, (start_date, end_date, limit))
            
        except Exception as e:
            logger.error(f"Error obteniendo top proveedores: {e}")
            return []
    
    def get_providers_with_pending_orders(self) -> List[Dict]:
        """Obtener proveedores con órdenes pendientes"""
        try:
            return self.db.execute_query("""
                SELECT 
                    p.id,
                    p.nombre,
                    p.telefono,
                    p.email,
                    COUNT(c.id) as ordenes_pendientes,
                    SUM(c.total) as monto_pendiente,
                    MIN(c.fecha_compra) as orden_mas_antigua,
                    AVG(JULIANDAY('now') - JULIANDAY(c.fecha_compra)) as dias_promedio_pendiente
                FROM proveedores p
                JOIN compras c ON p.id = c.proveedor_id
                WHERE c.estado IN ('PENDIENTE', 'CONFIRMADA', 'PARCIAL')
                AND p.activo = 1
                GROUP BY p.id, p.nombre, p.telefono, p.email
                ORDER BY dias_promedio_pendiente DESC
            """)
            
        except Exception as e:
            logger.error(f"Error obteniendo proveedores con órdenes pendientes: {e}")
            return []
    
    def suggest_alternative_providers(self, product_id: int) -> List[Dict]:
        """Sugerir proveedores alternativos para un producto"""
        try:
            # Obtener producto actual
            product = self.db.execute_single("""
                SELECT nombre, categoria_id, proveedor_id FROM productos WHERE id = ?
            """, (product_id,))
            
            if not product:
                return []
            
            # Buscar proveedores que suministren productos similares
            alternatives = self.db.execute_query("""
                SELECT DISTINCT
                    p.id,
                    p.nombre,
                    p.telefono,
                    p.email,
                    p.calificacion,
                    p.descuento_porcentaje,
                    COUNT(DISTINCT pr.id) as productos_similares,
                    AVG(pr.precio_compra) as precio_promedio,
                    MAX(c.fecha_compra) as ultima_compra
                FROM proveedores p
                JOIN productos pr ON p.id = pr.proveedor_id
                LEFT JOIN compras c ON p.id = c.proveedor_id AND c.estado != 'CANCELADA'
                WHERE pr.categoria_id = ?
                AND p.id != ?
                AND p.activo = 1
                AND pr.activo = 1
                GROUP BY p.id, p.nombre, p.telefono, p.email, p.calificacion, p.descuento_porcentaje
                ORDER BY p.calificacion DESC, productos_similares DESC
                LIMIT 5
            """, (product['categoria_id'], product['proveedor_id']))
            
            return alternatives
            
        except Exception as e:
            logger.error(f"Error sugiriendo proveedores alternativos: {e}")
            return []
    
    def get_provider_performance_report(self, provider_id: int, months: int = 12) -> Dict:
        """Generar reporte de desempeño del proveedor"""
        try:
            # Período de análisis
            start_date = datetime.now().replace(day=1)
            for _ in range(months - 1):
                if start_date.month == 1:
                    start_date = start_date.replace(year=start_date.year - 1, month=12)
                else:
                    start_date = start_date.replace(month=start_date.month - 1)
            
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = datetime.now().strftime('%Y-%m-%d')
            
            # Métricas de desempeño
            performance = self.db.execute_single("""
                SELECT 
                    COUNT(*) as total_ordenes,
                    SUM(total) as total_comprado,
                    AVG(total) as promedio_orden,
                    SUM(CASE WHEN estado = 'RECIBIDA' THEN 1 ELSE 0 END) as ordenes_completadas,
                    SUM(CASE WHEN estado = 'CANCELADA' THEN 1 ELSE 0 END) as ordenes_canceladas,
                    AVG(CASE 
                        WHEN estado = 'RECIBIDA' AND fecha_vencimiento IS NOT NULL 
                        THEN JULIANDAY(fecha_compra) - JULIANDAY(fecha_vencimiento)
                        ELSE NULL 
                    END) as promedio_dias_retraso
                FROM compras 
                WHERE proveedor_id = ? 
                AND DATE(fecha_compra) BETWEEN ? AND ?
            """, (provider_id, start_date_str, end_date_str))
            
            # Evolución mensual
            monthly_evolution = self.db.execute_query("""
                SELECT 
                    strftime('%Y-%m', fecha_compra) as mes,
                    COUNT(*) as ordenes,
                    SUM(total) as total_mes
                FROM compras 
                WHERE proveedor_id = ? 
                AND DATE(fecha_compra) BETWEEN ? AND ?
                AND estado != 'CANCELADA'
                GROUP BY strftime('%Y-%m', fecha_compra)
                ORDER BY mes
            """, (provider_id, start_date_str, end_date_str))
            
            # Productos más comprados
            top_products = self.db.execute_query("""
                SELECT 
                    p.nombre,
                    SUM(dc.cantidad) as cantidad_total,
                    SUM(dc.subtotal) as total_gastado,
                    AVG(dc.precio_unitario) as precio_promedio
                FROM detalle_compras dc
                JOIN productos p ON dc.producto_id = p.id
                JOIN compras c ON dc.compra_id = c.id
                WHERE c.proveedor_id = ?
                AND DATE(c.fecha_compra) BETWEEN ? AND ?
                AND c.estado != 'CANCELADA'
                GROUP BY p.id, p.nombre
                ORDER BY total_gastado DESC
                LIMIT 10
            """, (provider_id, start_date_str, end_date_str))
            
            # Calcular métricas derivadas
            performance_dict = dict(performance) if performance else {}
            
            if performance_dict.get('total_ordenes', 0) > 0:
                performance_dict['tasa_cumplimiento'] = (
                    performance_dict.get('ordenes_completadas', 0) / 
                    performance_dict['total_ordenes'] * 100
                )
                performance_dict['tasa_cancelacion'] = (
                    performance_dict.get('ordenes_canceladas', 0) / 
                    performance_dict['total_ordenes'] * 100
                )
            else:
                performance_dict['tasa_cumplimiento'] = 0
                performance_dict['tasa_cancelacion'] = 0
            
            return {
                'periodo_analisis': {
                    'inicio': start_date_str,
                    'fin': end_date_str,
                    'meses': months
                },
                'metricas_generales': performance_dict,
                'evolucion_mensual': monthly_evolution,
                'productos_mas_comprados': top_products
            }
            
        except Exception as e:
            logger.error(f"Error generando reporte de desempeño: {e}")
            return {}
    
    def import_providers_from_csv(self, csv_data: List[Dict]) -> Tuple[bool, str, Dict]:
        """Importar proveedores desde datos CSV"""
        try:
            results = {
                'total': len(csv_data),
                'created': 0,
                'updated': 0,
                'errors': []
            }
            
            for i, row in enumerate(csv_data):
                try:
                    # Verificar si el proveedor ya existe por CUIT o nombre
                    existing_provider = None
                    if row.get('cuit_dni'):
                        existing_provider = self.db.execute_single("""
                            SELECT id FROM proveedores WHERE cuit_dni = ?
                        """, (row['cuit_dni'],))
                    
                    if not existing_provider and row.get('nombre'):
                        existing_provider = self.db.execute_single("""
                            SELECT id FROM proveedores WHERE nombre = ?
                        """, (row['nombre'],))
                    
                    if existing_provider:
                        # Actualizar proveedor existente
                        success, message = self.update_provider(existing_provider['id'], row)
                        if success:
                            results['updated'] += 1
                        else:
                            results['errors'].append(f"Fila {i+1}: {message}")
                    else:
                        # Crear nuevo proveedor
                        success, message, provider_id = self.create_provider(row)
                        if success:
                            results['created'] += 1
                        else:
                            results['errors'].append(f"Fila {i+1}: {message}")
                            
                except Exception as e:
                    results['errors'].append(f"Fila {i+1}: Error procesando - {str(e)}")
            
            success_rate = (results['created'] + results['updated']) / results['total'] * 100
            
            logger.info(f"Importación de proveedores completada: {results['created']} creados, {results['updated']} actualizados, {len(results['errors'])} errores")
            
            return True, f"Importación completada: {success_rate:.1f}% exitoso", results
            
        except Exception as e:
            logger.error(f"Error en importación de proveedores: {e}")
            return False, f"Error en importación: {str(e)}", {}