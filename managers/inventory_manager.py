"""
Gestor de Inventario Avanzado - AlmacénPro v2.0
Gestión completa de inventario multi-almacén con trazabilidad
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from database.models import Product
from utils.audit_logger import get_audit_logger

logger = logging.getLogger(__name__)

class InventoryManager:
    """Gestor avanzado de inventario y almacenes"""
    
    def __init__(self, db_manager, current_user: Dict = None):
        self.db = db_manager
        self.current_user = current_user
        self.audit_logger = get_audit_logger(db_manager, current_user)
        logger.info("InventoryManager inicializado")
    
    # ==================== GESTIÓN DE ALMACENES ====================
    
    def get_warehouses(self) -> List[Dict]:
        """Obtener lista de almacenes"""
        try:
            query = """
                SELECT w.*, 
                       COUNT(DISTINCT sl.product_id) as product_count,
                       SUM(sl.quantity) as total_items
                FROM warehouses w
                LEFT JOIN stock_by_location sl ON w.id = sl.warehouse_id
                WHERE w.active = 1
                GROUP BY w.id
                ORDER BY w.name
            """
            return self.db.execute_query(query) or []
        except Exception as e:
            logger.error(f"Error obteniendo almacenes: {e}")
            return []
    
    def create_warehouse(self, data: Dict) -> Optional[int]:
        """Crear nuevo almacén"""
        try:
            query = """
                INSERT INTO warehouses (name, code, address, phone, manager_id, active, created_at)
                VALUES (?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            """
            values = (
                data['name'],
                data.get('code', ''),
                data.get('address', ''),
                data.get('phone', ''),
                data.get('manager_id', self.current_user.get('id') if self.current_user else None)
            )
            
            warehouse_id = self.db.execute_query(query, values, return_id=True)
            
            if warehouse_id:
                self.audit_logger.log_create('warehouses', warehouse_id, data)
                logger.info(f"Almacén creado: {warehouse_id}")
            
            return warehouse_id
            
        except Exception as e:
            logger.error(f"Error creando almacén: {e}")
            return None
    
    def get_warehouse_zones(self, warehouse_id: int) -> List[Dict]:
        """Obtener zonas de un almacén"""
        try:
            query = """
                SELECT wz.*,
                       COUNT(DISTINCT sl.product_id) as product_count
                FROM warehouse_zones wz
                LEFT JOIN stock_by_location sl ON wz.id = sl.zone_id
                WHERE wz.warehouse_id = ? AND wz.active = 1
                GROUP BY wz.id
                ORDER BY wz.code
            """
            return self.db.execute_query(query, (warehouse_id,)) or []
        except Exception as e:
            logger.error(f"Error obteniendo zonas del almacén {warehouse_id}: {e}")
            return []
    
    # ==================== CONTROL DE STOCK ====================
    
    def get_stock_by_product(self, product_id: int) -> List[Dict]:
        """Obtener stock de un producto por ubicación"""
        try:
            query = """
                SELECT sl.*, w.name as warehouse_name, w.code as warehouse_code,
                       wz.name as zone_name, wz.code as zone_code
                FROM stock_by_location sl
                LEFT JOIN warehouses w ON sl.warehouse_id = w.id
                LEFT JOIN warehouse_zones wz ON sl.zone_id = wz.id
                WHERE sl.product_id = ? AND sl.quantity > 0
                ORDER BY w.name, wz.code
            """
            return self.db.execute_query(query, (product_id,)) or []
        except Exception as e:
            logger.error(f"Error obteniendo stock del producto {product_id}: {e}")
            return []
    
    def get_total_stock(self, product_id: int, warehouse_id: Optional[int] = None) -> float:
        """Obtener stock total de un producto"""
        try:
            if warehouse_id:
                query = """
                    SELECT COALESCE(SUM(quantity), 0) as total_stock
                    FROM stock_by_location 
                    WHERE product_id = ? AND warehouse_id = ?
                """
                values = (product_id, warehouse_id)
            else:
                query = """
                    SELECT COALESCE(SUM(quantity), 0) as total_stock
                    FROM stock_by_location 
                    WHERE product_id = ?
                """
                values = (product_id,)
            
            result = self.db.execute_single(query, values)
            return float(result['total_stock']) if result else 0.0
            
        except Exception as e:
            logger.error(f"Error obteniendo stock total: {e}")
            return 0.0
    
    def get_low_stock_products(self, warehouse_id: Optional[int] = None) -> List[Dict]:
        """Obtener productos con stock bajo"""
        try:
            base_query = """
                SELECT p.*, c.name as category_name,
                       COALESCE(SUM(sl.quantity), 0) as current_stock,
                       p.minimum_stock,
                       CASE 
                           WHEN COALESCE(SUM(sl.quantity), 0) <= 0 THEN 'SIN_STOCK'
                           WHEN COALESCE(SUM(sl.quantity), 0) <= p.minimum_stock THEN 'STOCK_BAJO'
                           ELSE 'STOCK_OK'
                       END as stock_status
                FROM products p
                LEFT JOIN product_categories c ON p.category_id = c.id
                LEFT JOIN stock_by_location sl ON p.id = sl.product_id
            """
            
            if warehouse_id:
                base_query += " AND sl.warehouse_id = ?"
                values = (warehouse_id,)
            else:
                values = ()
            
            base_query += """
                WHERE p.active = 1
                GROUP BY p.id
                HAVING stock_status IN ('SIN_STOCK', 'STOCK_BAJO')
                ORDER BY stock_status DESC, current_stock ASC
            """
            
            return self.db.execute_query(base_query, values) or []
            
        except Exception as e:
            logger.error(f"Error obteniendo productos con stock bajo: {e}")
            return []
    
    # ==================== MOVIMIENTOS DE STOCK ====================
    
    def create_stock_movement(self, movement_data: Dict) -> Optional[int]:
        """Crear movimiento de stock"""
        try:
            # Validar datos requeridos
            required_fields = ['product_id', 'warehouse_id', 'movement_type', 'quantity', 'reason']
            for field in required_fields:
                if field not in movement_data:
                    raise ValueError(f"Campo requerido faltante: {field}")
            
            # Insertar movimiento
            movement_query = """
                INSERT INTO stock_movements (
                    product_id, warehouse_id, zone_id, movement_type, quantity, 
                    unit_cost, total_cost, reason, reference_type, reference_id,
                    user_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            
            movement_values = (
                movement_data['product_id'],
                movement_data['warehouse_id'],
                movement_data.get('zone_id'),
                movement_data['movement_type'],
                movement_data['quantity'],
                movement_data.get('unit_cost', 0.0),
                movement_data.get('total_cost', 0.0),
                movement_data['reason'],
                movement_data.get('reference_type'),
                movement_data.get('reference_id'),
                self.current_user.get('id') if self.current_user else None
            )
            
            movement_id = self.db.execute_query(movement_query, movement_values, return_id=True)
            
            if movement_id:
                # Actualizar stock en ubicación
                self._update_location_stock(
                    movement_data['product_id'],
                    movement_data['warehouse_id'],
                    movement_data.get('zone_id'),
                    movement_data['quantity'],
                    movement_data['movement_type']
                )
                
                # Log de auditoría
                self.audit_logger.log_stock_movement(
                    movement_data['product_id'],
                    f"Producto ID: {movement_data['product_id']}",
                    movement_data['movement_type'],
                    movement_data['quantity'],
                    movement_data['reason']
                )
                
                logger.info(f"Movimiento de stock creado: {movement_id}")
            
            return movement_id
            
        except Exception as e:
            logger.error(f"Error creando movimiento de stock: {e}")
            return None
    
    def _update_location_stock(self, product_id: int, warehouse_id: int, zone_id: Optional[int], 
                              quantity: float, movement_type: str):
        """Actualizar stock en ubicación específica"""
        try:
            # Verificar si existe registro de stock para esta ubicación
            check_query = """
                SELECT id, quantity FROM stock_by_location 
                WHERE product_id = ? AND warehouse_id = ? AND zone_id IS ?
            """
            current_stock = self.db.execute_single(check_query, (product_id, warehouse_id, zone_id))
            
            # Calcular nueva cantidad
            if movement_type in ['IN', 'TRANSFER_IN', 'ADJUSTMENT_UP']:
                quantity_change = quantity
            elif movement_type in ['OUT', 'TRANSFER_OUT', 'ADJUSTMENT_DOWN', 'SALE']:
                quantity_change = -quantity
            else:
                quantity_change = 0
            
            if current_stock:
                # Actualizar stock existente
                new_quantity = current_stock['quantity'] + quantity_change
                update_query = """
                    UPDATE stock_by_location 
                    SET quantity = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """
                self.db.execute_query(update_query, (new_quantity, current_stock['id']))
            else:
                # Crear nuevo registro de stock
                if quantity_change > 0:  # Solo crear si la cantidad final es positiva
                    insert_query = """
                        INSERT INTO stock_by_location (
                            product_id, warehouse_id, zone_id, quantity, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """
                    self.db.execute_query(insert_query, (product_id, warehouse_id, zone_id, quantity_change))
                    
        except Exception as e:
            logger.error(f"Error actualizando stock en ubicación: {e}")
            raise
    
    def get_stock_movements(self, product_id: Optional[int] = None, 
                           warehouse_id: Optional[int] = None,
                           days: int = 30) -> List[Dict]:
        """Obtener movimientos de stock recientes"""
        try:
            base_query = """
                SELECT sm.*, p.name as product_name, p.sku,
                       w.name as warehouse_name, wz.name as zone_name,
                       u.username as user_name
                FROM stock_movements sm
                LEFT JOIN products p ON sm.product_id = p.id
                LEFT JOIN warehouses w ON sm.warehouse_id = w.id
                LEFT JOIN warehouse_zones wz ON sm.zone_id = wz.id
                LEFT JOIN users u ON sm.user_id = u.id
                WHERE sm.created_at >= datetime('now', '-{} days')
            """.format(days)
            
            conditions = []
            values = []
            
            if product_id:
                conditions.append("sm.product_id = ?")
                values.append(product_id)
            
            if warehouse_id:
                conditions.append("sm.warehouse_id = ?")
                values.append(warehouse_id)
            
            if conditions:
                base_query += " AND " + " AND ".join(conditions)
            
            base_query += " ORDER BY sm.created_at DESC"
            
            return self.db.execute_query(base_query, tuple(values)) or []
            
        except Exception as e:
            logger.error(f"Error obteniendo movimientos de stock: {e}")
            return []
    
    # ==================== TRANSFERENCIAS ENTRE ALMACENES ====================
    
    def create_transfer(self, transfer_data: Dict) -> Optional[int]:
        """Crear transferencia entre almacenes"""
        try:
            # Crear registro de transferencia
            transfer_query = """
                INSERT INTO stock_transfers (
                    from_warehouse_id, to_warehouse_id, status, notes,
                    created_by, created_at
                ) VALUES (?, ?, 'PENDING', ?, ?, CURRENT_TIMESTAMP)
            """
            
            transfer_values = (
                transfer_data['from_warehouse_id'],
                transfer_data['to_warehouse_id'],
                transfer_data.get('notes', ''),
                self.current_user.get('id') if self.current_user else None
            )
            
            transfer_id = self.db.execute_query(transfer_query, transfer_values, return_id=True)
            
            if transfer_id:
                # Procesar items de la transferencia
                for item in transfer_data['items']:
                    self._create_transfer_item(transfer_id, item)
                
                logger.info(f"Transferencia creada: {transfer_id}")
            
            return transfer_id
            
        except Exception as e:
            logger.error(f"Error creando transferencia: {e}")
            return None
    
    def _create_transfer_item(self, transfer_id: int, item_data: Dict):
        """Crear item de transferencia"""
        try:
            query = """
                INSERT INTO stock_transfer_items (
                    transfer_id, product_id, quantity_requested, 
                    quantity_sent, quantity_received, notes
                ) VALUES (?, ?, ?, 0, 0, ?)
            """
            
            values = (
                transfer_id,
                item_data['product_id'],
                item_data['quantity'],
                item_data.get('notes', '')
            )
            
            self.db.execute_query(query, values)
            
        except Exception as e:
            logger.error(f"Error creando item de transferencia: {e}")
            raise
    
    # ==================== CONTEOS FÍSICOS ====================
    
    def create_physical_count(self, count_data: Dict) -> Optional[int]:
        """Crear conteo físico de inventario"""
        try:
            count_query = """
                INSERT INTO inventory_counts (
                    warehouse_id, zone_id, count_type, status, notes,
                    scheduled_date, created_by, created_at
                ) VALUES (?, ?, ?, 'PLANNED', ?, ?, ?, CURRENT_TIMESTAMP)
            """
            
            count_values = (
                count_data['warehouse_id'],
                count_data.get('zone_id'),
                count_data.get('count_type', 'FULL'),
                count_data.get('notes', ''),
                count_data.get('scheduled_date'),
                self.current_user.get('id') if self.current_user else None
            )
            
            count_id = self.db.execute_query(count_query, count_values, return_id=True)
            
            if count_id:
                logger.info(f"Conteo físico creado: {count_id}")
            
            return count_id
            
        except Exception as e:
            logger.error(f"Error creando conteo físico: {e}")
            return None
    
    # ==================== REPORTES Y ANÁLISIS ====================
    
    def get_inventory_valuation(self, warehouse_id: Optional[int] = None) -> Dict:
        """Obtener valorización del inventario"""
        try:
            base_query = """
                SELECT 
                    COUNT(DISTINCT p.id) as total_products,
                    SUM(sl.quantity) as total_units,
                    SUM(sl.quantity * p.cost_price) as total_cost_value,
                    SUM(sl.quantity * p.sale_price) as total_sale_value,
                    AVG(p.margin_percentage) as avg_margin
                FROM stock_by_location sl
                JOIN products p ON sl.product_id = p.id
                WHERE sl.quantity > 0 AND p.active = 1
            """
            
            values = []
            if warehouse_id:
                base_query += " AND sl.warehouse_id = ?"
                values.append(warehouse_id)
            
            result = self.db.execute_single(base_query, tuple(values))
            
            return {
                'total_products': result['total_products'] or 0,
                'total_units': result['total_units'] or 0,
                'total_cost_value': result['total_cost_value'] or 0.0,
                'total_sale_value': result['total_sale_value'] or 0.0,
                'avg_margin': result['avg_margin'] or 0.0,
                'potential_profit': (result['total_sale_value'] or 0.0) - (result['total_cost_value'] or 0.0)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo valorización del inventario: {e}")
            return {}
    
    def get_abc_analysis(self, warehouse_id: Optional[int] = None, days: int = 90) -> List[Dict]:
        """Análisis ABC de productos por valor de ventas"""
        try:
            query = """
                SELECT p.id, p.name, p.sku,
                       SUM(rd.quantity) as units_sold,
                       SUM(rd.subtotal) as sales_value,
                       COALESCE(sl.total_stock, 0) as current_stock
                FROM receipt_details rd
                JOIN products p ON rd.product_id = p.id
                JOIN receipts r ON rd.receipt_id = r.id
                LEFT JOIN (
                    SELECT product_id, SUM(quantity) as total_stock
                    FROM stock_by_location
                    {} 
                    GROUP BY product_id
                ) sl ON p.id = sl.product_id
                WHERE r.date >= date('now', '-{} days')
                GROUP BY p.id
                ORDER BY sales_value DESC
            """.format(
                f"WHERE warehouse_id = {warehouse_id}" if warehouse_id else "",
                days
            )
            
            results = self.db.execute_query(query) or []
            
            # Calcular clasificación ABC
            if results:
                total_value = sum(item['sales_value'] for item in results)
                cumulative_value = 0
                
                for item in results:
                    cumulative_value += item['sales_value']
                    cumulative_percentage = (cumulative_value / total_value) * 100
                    
                    if cumulative_percentage <= 80:
                        item['abc_class'] = 'A'
                    elif cumulative_percentage <= 95:
                        item['abc_class'] = 'B'
                    else:
                        item['abc_class'] = 'C'
            
            return results
            
        except Exception as e:
            logger.error(f"Error en análisis ABC: {e}")
            return []
    
    # ==================== UTILIDADES ====================
    
    def validate_stock_operation(self, product_id: int, warehouse_id: int, 
                                quantity: float, operation: str) -> Dict:
        """Validar operación de stock"""
        try:
            validation = {
                'valid': True,
                'warnings': [],
                'errors': []
            }
            
            # Validar cantidad
            if quantity <= 0:
                validation['errors'].append("La cantidad debe ser mayor a cero")
            
            # Para operaciones de salida, validar stock disponible
            if operation in ['OUT', 'TRANSFER_OUT', 'SALE', 'ADJUSTMENT_DOWN']:
                current_stock = self.get_total_stock(product_id, warehouse_id)
                if current_stock < quantity:
                    validation['errors'].append(f"Stock insuficiente. Disponible: {current_stock}")
            
            # Validar existencia del producto
            product = self.db.execute_single("SELECT * FROM products WHERE id = ? AND active = 1", (product_id,))
            if not product:
                validation['errors'].append("Producto no encontrado o inactivo")
            
            validation['valid'] = len(validation['errors']) == 0
            return validation
            
        except Exception as e:
            logger.error(f"Error validando operación de stock: {e}")
            return {'valid': False, 'errors': [str(e)], 'warnings': []}