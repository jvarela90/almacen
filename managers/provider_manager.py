"""
Gestor de Proveedores para AlmacénPro
Manejo completo de proveedores, contactos y relaciones comerciales
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
import re

logger = logging.getLogger(__name__)

class ProviderManager:
    """Gestor principal para proveedores y relaciones comerciales"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
        
        # Tipos de condición ante IVA válidos
        self.VALID_IVA_CONDITIONS = [
            'RESPONSABLE_INSCRIPTO',
            'RESPONSABLE_NO_INSCRIPTO',
            'EXENTO',
            'MONOTRIBUTISTA',
            'CONSUMIDOR_FINAL',
            'NO_RESPONSABLE',
            'SUJETO_NO_CATEGORIZADO'
        ]
    
    def create_provider(self, provider_data: Dict, user_id: int = None) -> Tuple[bool, str, int]:
        """Crear nuevo proveedor"""
        try:
            # Validaciones básicas
            if not provider_data.get('nombre'):
                return False, "El nombre del proveedor es obligatorio", 0
            
            # Generar código si no se proporciona
            if not provider_data.get('codigo'):
                provider_data['codigo'] = self._generate_provider_code()
            
            # Validar código único
            if self._provider_code_exists(provider_data['codigo']):
                return False, f"Ya existe un proveedor con el código {provider_data['codigo']}", 0
            
            # Validar email si se proporciona
            if provider_data.get('email') and not self._validate_email(provider_data['email']):
                return False, "El formato del email no es válido", 0
            
            # Validar CUIT/CUIL si se proporciona
            if provider_data.get('cuit_cuil') and not self._validate_cuit_cuil(provider_data['cuit_cuil']):
                return False, "El formato del CUIT/CUIL no es válido", 0
            
            # Validar condición IVA
            iva_condition = provider_data.get('condicion_iva', 'RESPONSABLE_INSCRIPTO')
            if iva_condition not in self.VALID_IVA_CONDITIONS:
                return False, "Condición de IVA no válida", 0
            
            # Insertar proveedor
            provider_id = self.db.execute_insert("""
                INSERT INTO proveedores (
                    codigo, nombre, razon_social, cuit_cuil, telefono, email,
                    direccion, ciudad, provincia, codigo_postal,
                    contacto_nombre, contacto_telefono, contacto_email,
                    condicion_iva, dias_pago, limite_credito, observaciones
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                provider_data['codigo'],
                provider_data['nombre'],
                provider_data.get('razon_social'),
                provider_data.get('cuit_cuil'),
                provider_data.get('telefono'),
                provider_data.get('email'),
                provider_data.get('direccion'),
                provider_data.get('ciudad'),
                provider_data.get('provincia'),
                provider_data.get('codigo_postal'),
                provider_data.get('contacto_nombre'),
                provider_data.get('contacto_telefono'),
                provider_data.get('contacto_email'),
                iva_condition,
                provider_data.get('dias_pago', 30),
                provider_data.get('limite_credito', 0),
                provider_data.get('observaciones')
            ))
            
            if provider_id:
                self.logger.info(f"Proveedor creado exitosamente: {provider_data['nombre']} (ID: {provider_id})")
                return True, f"Proveedor creado exitosamente", provider_id
            else:
                return False, "Error al crear el proveedor", 0
                
        except Exception as e:
            self.logger.error(f"Error creando proveedor: {e}")
            return False, f"Error creando proveedor: {str(e)}", 0
    
    def update_provider(self, provider_id: int, provider_data: Dict, user_id: int = None) -> Tuple[bool, str]:
        """Actualizar proveedor existente"""
        try:
            # Verificar que el proveedor existe
            existing_provider = self.get_provider_by_id(provider_id)
            if not existing_provider:
                return False, "Proveedor no encontrado"
            
            # Validaciones básicas
            if provider_data.get('nombre') and not provider_data['nombre'].strip():
                return False, "El nombre del proveedor no puede estar vacío"
            
            # Validar código único (si se está cambiando)
            if provider_data.get('codigo') and provider_data['codigo'] != existing_provider['codigo']:
                if self._provider_code_exists(provider_data['codigo']):
                    return False, f"Ya existe un proveedor con el código {provider_data['codigo']}"
            
            # Validar email si se proporciona
            if provider_data.get('email') and not self._validate_email(provider_data['email']):
                return False, "El formato del email no es válido"
            
            # Validar CUIT/CUIL si se proporciona
            if provider_data.get('cuit_cuil') and not self._validate_cuit_cuil(provider_data['cuit_cuil']):
                return False, "El formato del CUIT/CUIL no es válido"
            
            # Validar condición IVA
            if provider_data.get('condicion_iva') and provider_data['condicion_iva'] not in self.VALID_IVA_CONDITIONS:
                return False, "Condición de IVA no válida"
            
            # Construir query de actualización dinámicamente
            update_fields = []
            update_values = []
            
            allowed_fields = [
                'codigo', 'nombre', 'razon_social', 'cuit_cuil', 'telefono', 'email',
                'direccion', 'ciudad', 'provincia', 'codigo_postal',
                'contacto_nombre', 'contacto_telefono', 'contacto_email',
                'condicion_iva', 'dias_pago', 'limite_credito', 'observaciones', 'activo'
            ]
            
            for field, value in provider_data.items():
                if field in allowed_fields and value is not None:
                    update_fields.append(f"{field} = ?")
                    update_values.append(value)
            
            if not update_fields:
                return False, "No hay campos válidos para actualizar"
            
            # Agregar timestamp de actualización
            update_fields.append("actualizado_en = CURRENT_TIMESTAMP")
            update_values.append(provider_id)
            
            query = f"UPDATE proveedores SET {', '.join(update_fields)} WHERE id = ?"
            
            success = self.db.execute_update(query, update_values)
            
            if success:
                self.logger.info(f"Proveedor actualizado: ID {provider_id}")
                return True, "Proveedor actualizado exitosamente"
            else:
                return False, "Error al actualizar el proveedor"
                
        except Exception as e:
            self.logger.error(f"Error actualizando proveedor: {e}")
            return False, f"Error actualizando proveedor: {str(e)}"
    
    def get_provider_by_id(self, provider_id: int) -> Optional[Dict]:
        """Obtener proveedor por ID"""
        try:
            return self.db.execute_single("""
                SELECT * FROM proveedores WHERE id = ?
            """, (provider_id,))
            
        except Exception as e:
            self.logger.error(f"Error obteniendo proveedor por ID: {e}")
            return None
    
    def get_provider_by_code(self, codigo: str) -> Optional[Dict]:
        """Obtener proveedor por código"""
        try:
            return self.db.execute_single("""
                SELECT * FROM proveedores WHERE codigo = ? AND activo = 1
            """, (codigo,))
            
        except Exception as e:
            self.logger.error(f"Error obteniendo proveedor por código: {e}")
            return None
    
    def search_providers(self, search_term: str, include_inactive: bool = False) -> List[Dict]:
        """Buscar proveedores por nombre, código o razón social"""
        try:
            if not search_term.strip():
                return []
            
            search_pattern = f"%{search_term.strip()}%"
            
            query = """
                SELECT p.*, 
                       COUNT(pr.id) as total_productos,
                       COUNT(c.id) as total_compras,
                       COALESCE(SUM(c.total), 0) as monto_total_compras
                FROM proveedores p
                LEFT JOIN productos pr ON p.id = pr.proveedor_id AND pr.activo = 1
                LEFT JOIN compras c ON p.id = c.proveedor_id
                WHERE (p.nombre LIKE ? OR p.codigo LIKE ? OR p.razon_social LIKE ?)
            """
            
            params = [search_pattern, search_pattern, search_pattern]
            
            if not include_inactive:
                query += " AND p.activo = 1"
            
            query += """
                GROUP BY p.id
                ORDER BY p.nombre
                LIMIT 100
            """
            
            return self.db.execute_query(query, params)
            
        except Exception as e:
            self.logger.error(f"Error buscando proveedores: {e}")
            return []
    
    def get_all_providers(self, include_inactive: bool = False, page: int = 1, page_size: int = 100) -> List[Dict]:
        """Obtener todos los proveedores con paginación"""
        try:
            query = """
                SELECT p.*,
                       COUNT(pr.id) as total_productos,
                       COUNT(c.id) as total_compras,
                       COALESCE(SUM(c.total), 0) as monto_total_compras,
                       MAX(c.fecha_compra) as ultima_compra
                FROM proveedores p
                LEFT JOIN productos pr ON p.id = pr.proveedor_id AND pr.activo = 1
                LEFT JOIN compras c ON p.id = c.proveedor_id
            """
            
            params = []
            
            if not include_inactive:
                query += " WHERE p.activo = 1"
            
            query += """
                GROUP BY p.id
                ORDER BY p.nombre
                LIMIT ? OFFSET ?
            """
            
            params.extend([page_size, (page - 1) * page_size])
            
            return self.db.execute_query(query, params)
            
        except Exception as e:
            self.logger.error(f"Error obteniendo proveedores: {e}")
            return []
    
    def get_provider_statistics(self, provider_id: int) -> Dict:
        """Obtener estadísticas detalladas de un proveedor"""
        try:
            # Estadísticas básicas
            stats = self.db.execute_single("""
                SELECT 
                    COUNT(DISTINCT pr.id) as total_productos,
                    COUNT(DISTINCT c.id) as total_compras,
                    COALESCE(SUM(c.total), 0) as monto_total_compras,
                    COALESCE(AVG(c.total), 0) as promedio_compra,
                    MIN(c.fecha_compra) as primera_compra,
                    MAX(c.fecha_compra) as ultima_compra,
                    COUNT(CASE WHEN c.estado = 'COMPLETADA' THEN 1 END) as compras_completadas,
                    COUNT(CASE WHEN c.estado = 'PENDIENTE' THEN 1 END) as compras_pendientes
                FROM proveedores p
                LEFT JOIN productos pr ON p.id = pr.proveedor_id AND pr.activo = 1
                LEFT JOIN compras c ON p.id = c.proveedor_id
                WHERE p.id = ?
                GROUP BY p.id
            """, (provider_id,))
            
            if not stats:
                return {
                    'total_productos': 0,
                    'total_compras': 0,
                    'monto_total_compras': 0.0,
                    'promedio_compra': 0.0,
                    'primera_compra': None,
                    'ultima_compra': None,
                    'compras_completadas': 0,
                    'compras_pendientes': 0
                }
            
            # Productos más comprados
            top_products = self.db.execute_query("""
                SELECT pr.nombre, pr.codigo_barras,
                       SUM(dc.cantidad) as cantidad_total,
                       SUM(dc.subtotal) as monto_total,
                       COUNT(DISTINCT c.id) as veces_comprado
                FROM productos pr
                INNER JOIN detalle_compras dc ON pr.id = dc.producto_id
                INNER JOIN compras c ON dc.compra_id = c.id
                WHERE c.proveedor_id = ? AND c.estado = 'COMPLETADA'
                GROUP BY pr.id, pr.nombre, pr.codigo_barras
                ORDER BY cantidad_total DESC
                LIMIT 10
            """, (provider_id,))
            
            # Compras por mes (últimos 12 meses)
            monthly_purchases = self.db.execute_query("""
                SELECT 
                    strftime('%Y-%m', fecha_compra) as mes,
                    COUNT(*) as total_compras,
                    SUM(total) as monto_total
                FROM compras
                WHERE proveedor_id = ? 
                AND fecha_compra >= date('now', '-12 months')
                AND estado = 'COMPLETADA'
                GROUP BY strftime('%Y-%m', fecha_compra)
                ORDER BY mes DESC
            """, (provider_id,))
            
            # Combinar resultados
            result = dict(stats)
            result['top_products'] = [dict(row) for row in top_products]
            result['monthly_purchases'] = [dict(row) for row in monthly_purchases]
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas del proveedor: {e}")
            return {}
    
    def get_providers_with_pending_orders(self) -> List[Dict]:
        """Obtener proveedores con órdenes de compra pendientes"""
        try:
            return self.db.execute_query("""
                SELECT p.*, 
                       COUNT(c.id) as ordenes_pendientes,
                       SUM(c.total) as monto_pendiente
                FROM proveedores p
                INNER JOIN compras c ON p.id = c.proveedor_id
                WHERE c.estado IN ('ORDENADA', 'CONFIRMADA', 'PARCIAL')
                AND p.activo = 1
                GROUP BY p.id, p.nombre
                ORDER BY ordenes_pendientes DESC, monto_pendiente DESC
            """)
            
        except Exception as e:
            self.logger.error(f"Error obteniendo proveedores con órdenes pendientes: {e}")
            return []
    
    def get_top_providers_by_volume(self, limit: int = 10, period_months: int = 12) -> List[Dict]:
        """Obtener top proveedores por volumen de compras"""
        try:
            return self.db.execute_query("""
                SELECT p.*,
                       COUNT(c.id) as total_compras,
                       SUM(c.total) as monto_total,
                       AVG(c.total) as promedio_compra,
                       MAX(c.fecha_compra) as ultima_compra
                FROM proveedores p
                INNER JOIN compras c ON p.id = c.proveedor_id
                WHERE c.fecha_compra >= date('now', '-{} months')
                AND c.estado = 'COMPLETADA'
                AND p.activo = 1
                GROUP BY p.id
                ORDER BY monto_total DESC
                LIMIT ?
            """.format(period_months), (limit,))
            
        except Exception as e:
            self.logger.error(f"Error obteniendo top proveedores: {e}")
            return []
    
    def deactivate_provider(self, provider_id: int, user_id: int = None) -> Tuple[bool, str]:
        """Desactivar proveedor"""
        try:
            # Verificar que el proveedor existe
            provider = self.get_provider_by_id(provider_id)
            if not provider:
                return False, "Proveedor no encontrado"
            
            if not provider['activo']:
                return False, "El proveedor ya está inactivo"
            
            # Verificar si tiene productos activos
            active_products = self.db.execute_single("""
                SELECT COUNT(*) as count FROM productos 
                WHERE proveedor_id = ? AND activo = 1
            """, (provider_id,))
            
            if active_products and active_products['count'] > 0:
                return False, f"No se puede desactivar: tiene {active_products['count']} productos activos"
            
            # Verificar si tiene órdenes pendientes
            pending_orders = self.db.execute_single("""
                SELECT COUNT(*) as count FROM compras 
                WHERE proveedor_id = ? AND estado IN ('ORDENADA', 'CONFIRMADA', 'PARCIAL')
            """, (provider_id,))
            
            if pending_orders and pending_orders['count'] > 0:
                return False, f"No se puede desactivar: tiene {pending_orders['count']} órdenes pendientes"
            
            # Desactivar proveedor
            success = self.db.execute_update("""
                UPDATE proveedores 
                SET activo = 0, actualizado_en = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (provider_id,))
            
            if success:
                self.logger.info(f"Proveedor desactivado: {provider['nombre']} (ID: {provider_id})")
                return True, "Proveedor desactivado exitosamente"
            else:
                return False, "Error al desactivar el proveedor"
                
        except Exception as e:
            self.logger.error(f"Error desactivando proveedor: {e}")
            return False, f"Error desactivando proveedor: {str(e)}"
    
    def reactivate_provider(self, provider_id: int, user_id: int = None) -> Tuple[bool, str]:
        """Reactivar proveedor"""
        try:
            # Verificar que el proveedor existe
            provider = self.get_provider_by_id(provider_id)
            if not provider:
                return False, "Proveedor no encontrado"
            
            if provider['activo']:
                return False, "El proveedor ya está activo"
            
            # Reactivar proveedor
            success = self.db.execute_update("""
                UPDATE proveedores 
                SET activo = 1, actualizado_en = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (provider_id,))
            
            if success:
                self.logger.info(f"Proveedor reactivado: {provider['nombre']} (ID: {provider_id})")
                return True, "Proveedor reactivado exitosamente"
            else:
                return False, "Error al reactivar el proveedor"
                
        except Exception as e:
            self.logger.error(f"Error reactivando proveedor: {e}")
            return False, f"Error reactivando proveedor: {str(e)}"
    
    def delete_provider(self, provider_id: int, user_id: int = None) -> Tuple[bool, str]:
        """Eliminar proveedor (solo si no tiene relaciones)"""
        try:
            # Verificar que el proveedor existe
            provider = self.get_provider_by_id(provider_id)
            if not provider:
                return False, "Proveedor no encontrado"
            
            # Verificar relaciones existentes
            has_products = self.db.execute_single("""
                SELECT COUNT(*) as count FROM productos WHERE proveedor_id = ?
            """, (provider_id,))
            
            if has_products and has_products['count'] > 0:
                return False, f"No se puede eliminar: tiene {has_products['count']} productos asociados"
            
            has_purchases = self.db.execute_single("""
                SELECT COUNT(*) as count FROM compras WHERE proveedor_id = ?
            """, (provider_id,))
            
            if has_purchases and has_purchases['count'] > 0:
                return False, f"No se puede eliminar: tiene {has_purchases['count']} compras asociadas"
            
            # Eliminar proveedor
            success = self.db.execute_update("DELETE FROM proveedores WHERE id = ?", (provider_id,))
            
            if success:
                self.logger.info(f"Proveedor eliminado: {provider['nombre']} (ID: {provider_id})")
                return True, "Proveedor eliminado exitosamente"
            else:
                return False, "Error al eliminar el proveedor"
                
        except Exception as e:
            self.logger.error(f"Error eliminando proveedor: {e}")
            return False, f"Error eliminando proveedor: {str(e)}"
    
    def _generate_provider_code(self) -> str:
        """Generar código único para proveedor"""
        try:
            # Obtener siguiente número secuencial
            result = self.db.execute_single("""
                SELECT COALESCE(MAX(CAST(SUBSTR(codigo, 5) AS INTEGER)), 0) + 1 as next_num
                FROM proveedores 
                WHERE codigo LIKE 'PROV%'
            """)
            
            if result:
                next_num = result['next_num']
            else:
                next_num = 1
            
            return f"PROV{next_num:04d}"
            
        except Exception as e:
            self.logger.error(f"Error generando código de proveedor: {e}")
            # Fallback usando timestamp
            import time
            return f"PROV{int(time.time())}"
    
    def _provider_code_exists(self, codigo: str) -> bool:
        """Verificar si existe un proveedor con el código dado"""
        try:
            result = self.db.execute_single("""
                SELECT id FROM proveedores WHERE codigo = ?
            """, (codigo,))
            return result is not None
        except Exception:
            return False
    
    def _validate_email(self, email: str) -> bool:
        """Validar formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email.strip()) is not None
    
    def _validate_cuit_cuil(self, cuit_cuil: str) -> bool:
        """Validar formato de CUIT/CUIL"""
        # Limpiar guiones y espacios
        cuit_cuil = re.sub(r'[-\s]', '', cuit_cuil.strip())
        
        # Debe tener exactamente 11 dígitos
        if not re.match(r'^\d{11}$', cuit_cuil):
            return False
        
        # Algoritmo de validación de CUIT/CUIL
        try:
            # Multiplicadores
            multiplicadores = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
            
            # Calcular suma
            suma = sum(int(cuit_cuil[i]) * multiplicadores[i] for i in range(10))
            
            # Calcular dígito verificador
            resto = suma % 11
            if resto < 2:
                digito_verificador = resto
            else:
                digito_verificador = 11 - resto
            
            # Comparar con el dígito verificador proporcionado
            return int(cuit_cuil[10]) == digito_verificador
            
        except Exception as e:
            self.logger.error(f"Error validando CUIT/CUIL: {e}")
            return False
    
    def get_provider_contacts(self, provider_id: int) -> List[Dict]:
        """Obtener contactos de un proveedor (implementación futura)"""
        # Para futuras versiones - sistema de múltiples contactos por proveedor
        try:
            provider = self.get_provider_by_id(provider_id)
            if not provider:
                return []
            
            # Por ahora retornar el contacto principal
            contacts = []
            if provider.get('contacto_nombre'):
                contacts.append({
                    'nombre': provider['contacto_nombre'],
                    'telefono': provider.get('contacto_telefono'),
                    'email': provider.get('contacto_email'),
                    'tipo': 'Principal'
                })
            
            return contacts
            
        except Exception as e:
            self.logger.error(f"Error obteniendo contactos del proveedor: {e}")
            return []
    
    def export_providers_data(self, provider_ids: List[int] = None) -> List[Dict]:
        """Exportar datos de proveedores para backup o transferencia"""
        try:
            if provider_ids:
                placeholders = ','.join(['?' for _ in provider_ids])
                query = f"SELECT * FROM proveedores WHERE id IN ({placeholders})"
                params = provider_ids
            else:
                query = "SELECT * FROM proveedores ORDER BY nombre"
                params = []
            
            return self.db.execute_query(query, params)
            
        except Exception as e:
            self.logger.error(f"Error exportando datos de proveedores: {e}")
            return []
    
    def import_providers_data(self, providers_data: List[Dict], overwrite: bool = False) -> Tuple[int, int, List[str]]:
        """
        Importar datos de proveedores desde backup
        
        Returns:
            tuple: (importados, actualizados, errores)
        """
        imported = 0
        updated = 0
        errors = []
        
        try:
            for provider_data in providers_data:
                try:
                    # Verificar si existe por código
                    existing = self.get_provider_by_code(provider_data.get('codigo', ''))
                    
                    if existing:
                        if overwrite:
                            # Actualizar existente
                            success, message = self.update_provider(existing['id'], provider_data)
                            if success:
                                updated += 1
                            else:
                                errors.append(f"Error actualizando {provider_data.get('nombre', 'N/A')}: {message}")
                        else:
                            errors.append(f"Proveedor ya existe: {provider_data.get('nombre', 'N/A')}")
                    else:
                        # Crear nuevo
                        success, message, provider_id = self.create_provider(provider_data)
                        if success:
                            imported += 1
                        else:
                            errors.append(f"Error creando {provider_data.get('nombre', 'N/A')}: {message}")
                            
                except Exception as e:
                    errors.append(f"Error procesando proveedor: {str(e)}")
            
            self.logger.info(f"Importación completada: {imported} importados, {updated} actualizados, {len(errors)} errores")
            return imported, updated, errors
            
        except Exception as e:
            self.logger.error(f"Error en importación de proveedores: {e}")
            return imported, updated, errors + [str(e)]