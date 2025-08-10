"""
Gestor de Clientes y CRM - AlmacénPro v2.0
Sistema completo de gestión de clientes y relaciones comerciales
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from database.models import Customer
from utils.audit_logger import get_audit_logger

logger = logging.getLogger(__name__)

class CustomerManager:
    """Gestor completo de clientes y CRM"""
    
    def __init__(self, db_manager, current_user: Dict = None):
        self.db = db_manager
        self.current_user = current_user
        self.audit_logger = get_audit_logger(db_manager, current_user)
        logger.info("CustomerManager inicializado")
    
    # ==================== GESTIÓN DE CLIENTES ====================
    
    def get_all_customers(self, active_only: bool = True) -> List[Dict]:
        """Obtener todos los clientes"""
        try:
            query = """
                SELECT c.*, cc.name as category_name,
                       COUNT(DISTINCT r.id) as total_sales,
                       COALESCE(SUM(r.total), 0) as total_amount,
                       MAX(r.date) as last_purchase_date,
                       COALESCE(ca.balance, 0) as account_balance
                FROM clientes c
                LEFT JOIN customer_categories cc ON c.category_id = cc.id
                LEFT JOIN receipts r ON c.id = r.customer_id
                LEFT JOIN customer_accounts ca ON c.id = ca.customer_id
                WHERE c.active = ? OR ? = 0
                GROUP BY c.id
                ORDER BY c.business_name, c.name
            """
            return self.db.execute_query(query, (1 if active_only else 0, 1 if active_only else 0)) or []
        except Exception as e:
            logger.error(f"Error obteniendo clientes: {e}")
            return []
    
    def get_customer_by_id(self, customer_id: int) -> Optional[Dict]:
        """Obtener cliente por ID"""
        try:
            query = """
                SELECT c.*, cc.name as category_name,
                       COUNT(DISTINCT r.id) as total_sales,
                       COALESCE(SUM(r.total), 0) as total_amount,
                       MAX(r.date) as last_purchase_date,
                       COALESCE(ca.balance, 0) as account_balance
                FROM clientes c
                LEFT JOIN customer_categories cc ON c.category_id = cc.id
                LEFT JOIN receipts r ON c.id = r.customer_id
                LEFT JOIN customer_accounts ca ON c.id = ca.customer_id
                WHERE c.id = ?
                GROUP BY c.id
            """
            return self.db.execute_single(query, (customer_id,))
        except Exception as e:
            logger.error(f"Error obteniendo cliente {customer_id}: {e}")
            return None
    
    def search_customers(self, search_term: str) -> List[Dict]:
        """Buscar clientes por nombre, documento o teléfono"""
        try:
            query = """
                SELECT c.*, cc.name as category_name,
                       COALESCE(ca.balance, 0) as account_balance
                FROM clientes c
                LEFT JOIN customer_categories cc ON c.category_id = cc.id
                LEFT JOIN customer_accounts ca ON c.id = ca.customer_id
                WHERE c.active = 1 AND (
                    c.name LIKE ? OR 
                    c.business_name LIKE ? OR
                    c.document_number LIKE ? OR
                    c.phone LIKE ? OR
                    c.email LIKE ?
                )
                ORDER BY c.business_name, c.name
            """
            search_pattern = f"%{search_term}%"
            return self.db.execute_query(query, (search_pattern,) * 5) or []
        except Exception as e:
            logger.error(f"Error buscando clientes: {e}")
            return []
    
    def create_customer(self, customer_data: Dict) -> Optional[int]:
        """Crear nuevo cliente"""
        try:
            # Validar datos requeridos
            if not customer_data.get('name') and not customer_data.get('business_name'):
                raise ValueError("Debe proporcionar nombre o razón social")
            
            query = """
                INSERT INTO clientes (
                    name, business_name, document_type, document_number, 
                    phone, mobile, email, address, city, postal_code,
                    category_id, tax_condition, credit_limit, payment_terms,
                    discount_percentage, price_list_id, notes, active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            """
            
            values = (
                customer_data.get('name', ''),
                customer_data.get('business_name', ''),
                customer_data.get('document_type', 'DNI'),
                customer_data.get('document_number', ''),
                customer_data.get('phone', ''),
                customer_data.get('mobile', ''),
                customer_data.get('email', ''),
                customer_data.get('address', ''),
                customer_data.get('city', ''),
                customer_data.get('postal_code', ''),
                customer_data.get('category_id'),
                customer_data.get('tax_condition', 'CONSUMIDOR_FINAL'),
                customer_data.get('credit_limit', 0.0),
                customer_data.get('payment_terms', 0),
                customer_data.get('discount_percentage', 0.0),
                customer_data.get('price_list_id'),
                customer_data.get('notes', '')
            )
            
            customer_id = self.db.execute_query(query, values, return_id=True)
            
            if customer_id:
                # Crear cuenta corriente
                self._create_customer_account(customer_id)
                
                # Log de auditoría
                self.audit_logger.log_create('customers', customer_id, customer_data)
                logger.info(f"Cliente creado: {customer_id}")
            
            return customer_id
            
        except Exception as e:
            logger.error(f"Error creando cliente: {e}")
            return None
    
    def update_customer(self, customer_id: int, customer_data: Dict) -> bool:
        """Actualizar cliente existente"""
        try:
            # Obtener datos actuales para auditoría
            current_data = self.get_customer_by_id(customer_id)
            if not current_data:
                return False
            
            query = """
                UPDATE clientes SET
                    name = ?, business_name = ?, document_type = ?, document_number = ?,
                    phone = ?, mobile = ?, email = ?, address = ?, city = ?, postal_code = ?,
                    category_id = ?, tax_condition = ?, credit_limit = ?, payment_terms = ?,
                    discount_percentage = ?, price_list_id = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            
            values = (
                customer_data.get('name', ''),
                customer_data.get('business_name', ''),
                customer_data.get('document_type', 'DNI'),
                customer_data.get('document_number', ''),
                customer_data.get('phone', ''),
                customer_data.get('mobile', ''),
                customer_data.get('email', ''),
                customer_data.get('address', ''),
                customer_data.get('city', ''),
                customer_data.get('postal_code', ''),
                customer_data.get('category_id'),
                customer_data.get('tax_condition', 'CONSUMIDOR_FINAL'),
                customer_data.get('credit_limit', 0.0),
                customer_data.get('payment_terms', 0),
                customer_data.get('discount_percentage', 0.0),
                customer_data.get('price_list_id'),
                customer_data.get('notes', ''),
                customer_id
            )
            
            success = self.db.execute_query(query, values)
            
            if success:
                # Log de auditoría
                self.audit_logger.log_update('customers', customer_id, current_data, customer_data)
                logger.info(f"Cliente actualizado: {customer_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error actualizando cliente {customer_id}: {e}")
            return False
    
    def delete_customer(self, customer_id: int) -> bool:
        """Eliminar cliente (soft delete)"""
        try:
            current_data = self.get_customer_by_id(customer_id)
            if not current_data:
                return False
            
            # Verificar si tiene ventas
            sales_count = self.db.execute_single(
                "SELECT COUNT(*) as count FROM receipts WHERE customer_id = ?", 
                (customer_id,)
            )
            
            if sales_count and sales_count['count'] > 0:
                # Solo desactivar si tiene ventas
                query = "UPDATE clientes SET active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            else:
                # Eliminar físicamente si no tiene ventas
                query = "DELETE FROM clientes WHERE id = ?"
            
            success = self.db.execute_query(query, (customer_id,))
            
            if success:
                self.audit_logger.log_delete('customers', customer_id, current_data)
                logger.info(f"Cliente eliminado: {customer_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error eliminando cliente {customer_id}: {e}")
            return False
    
    # ==================== CATEGORÍAS DE CLIENTES ====================
    
    def get_customer_categories(self) -> List[Dict]:
        """Obtener categorías de clientes"""
        try:
            query = """
                SELECT cc.*, COUNT(c.id) as customer_count
                FROM customer_categories cc
                LEFT JOIN customers c ON cc.id = c.category_id AND c.active = 1
                WHERE cc.active = 1
                GROUP BY cc.id
                ORDER BY cc.name
            """
            return self.db.execute_query(query) or []
        except Exception as e:
            logger.error(f"Error obteniendo categorías de clientes: {e}")
            return []
    
    def create_customer_category(self, category_data: Dict) -> Optional[int]:
        """Crear categoría de cliente"""
        try:
            query = """
                INSERT INTO customer_categories (name, description, discount_percentage, active, created_at)
                VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
            """
            values = (
                category_data['name'],
                category_data.get('description', ''),
                category_data.get('discount_percentage', 0.0)
            )
            
            category_id = self.db.execute_query(query, values, return_id=True)
            
            if category_id:
                self.audit_logger.log_create('customer_categories', category_id, category_data)
                logger.info(f"Categoría de cliente creada: {category_id}")
            
            return category_id
            
        except Exception as e:
            logger.error(f"Error creando categoría de cliente: {e}")
            return None
    
    # ==================== CUENTAS CORRIENTES ====================
    
    def _create_customer_account(self, customer_id: int) -> bool:
        """Crear cuenta corriente para cliente"""
        try:
            query = """
                INSERT INTO customer_accounts (customer_id, balance, credit_limit, created_at)
                VALUES (?, 0.0, 0.0, CURRENT_TIMESTAMP)
            """
            return self.db.execute_query(query, (customer_id,))
        except Exception as e:
            logger.error(f"Error creando cuenta de cliente {customer_id}: {e}")
            return False
    
    def get_customer_account(self, customer_id: int) -> Optional[Dict]:
        """Obtener cuenta corriente del cliente"""
        try:
            query = """
                SELECT ca.*, c.name, c.business_name
                FROM customer_accounts ca
                JOIN customers c ON ca.customer_id = c.id
                WHERE ca.customer_id = ?
            """
            return self.db.execute_single(query, (customer_id,))
        except Exception as e:
            logger.error(f"Error obteniendo cuenta del cliente {customer_id}: {e}")
            return None
    
    def add_account_movement(self, customer_id: int, movement_data: Dict) -> Optional[int]:
        """Agregar movimiento a cuenta corriente"""
        try:
            # Obtener balance actual
            account = self.get_customer_account(customer_id)
            if not account:
                return None
            
            # Calcular nuevo balance
            amount = movement_data['amount']
            if movement_data['movement_type'] in ['PAYMENT', 'CREDIT']:
                new_balance = account['balance'] - amount
            elif movement_data['movement_type'] in ['SALE', 'CHARGE']:
                new_balance = account['balance'] + amount
            else:
                new_balance = account['balance']
            
            # Insertar movimiento
            movement_query = """
                INSERT INTO account_movements (
                    customer_id, movement_type, amount, balance_after, 
                    reference_type, reference_id, description, user_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            
            movement_values = (
                customer_id,
                movement_data['movement_type'],
                amount,
                new_balance,
                movement_data.get('reference_type'),
                movement_data.get('reference_id'),
                movement_data.get('description', ''),
                self.current_user.get('id') if self.current_user else None
            )
            
            movement_id = self.db.execute_query(movement_query, movement_values, return_id=True)
            
            if movement_id:
                # Actualizar balance en cuenta
                update_query = """
                    UPDATE customer_accounts 
                    SET balance = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE customer_id = ?
                """
                self.db.execute_query(update_query, (new_balance, customer_id))
                
                logger.info(f"Movimiento de cuenta agregado: {movement_id}")
            
            return movement_id
            
        except Exception as e:
            logger.error(f"Error agregando movimiento de cuenta: {e}")
            return None
    
    def get_account_movements(self, customer_id: int, days: int = 90) -> List[Dict]:
        """Obtener movimientos de cuenta corriente"""
        try:
            query = """
                SELECT am.*, u.username as user_name
                FROM account_movements am
                LEFT JOIN users u ON am.user_id = u.id
                WHERE am.customer_id = ? 
                  AND am.created_at >= date('now', '-{} days')
                ORDER BY am.created_at DESC
            """.format(days)
            
            return self.db.execute_query(query, (customer_id,)) or []
        except Exception as e:
            logger.error(f"Error obteniendo movimientos de cuenta: {e}")
            return []
    
    # ==================== HISTORIAL DE COMPRAS ====================
    
    def get_customer_purchase_history(self, customer_id: int, days: int = 365) -> List[Dict]:
        """Obtener historial de compras del cliente"""
        try:
            query = """
                SELECT r.*, u.username as seller_name,
                       COUNT(rd.id) as items_count,
                       SUM(rd.quantity) as total_items
                FROM receipts r
                LEFT JOIN users u ON r.user_id = u.id
                LEFT JOIN receipt_details rd ON r.id = rd.receipt_id
                WHERE r.customer_id = ? 
                  AND r.date >= date('now', '-{} days')
                GROUP BY r.id
                ORDER BY r.date DESC
            """.format(days)
            
            return self.db.execute_query(query, (customer_id,)) or []
        except Exception as e:
            logger.error(f"Error obteniendo historial de compras: {e}")
            return []
    
    def get_customer_favorite_products(self, customer_id: int, limit: int = 10) -> List[Dict]:
        """Obtener productos favoritos del cliente"""
        try:
            query = """
                SELECT p.*, SUM(rd.quantity) as total_quantity,
                       COUNT(DISTINCT r.id) as purchase_count,
                       SUM(rd.subtotal) as total_spent,
                       MAX(r.date) as last_purchase_date
                FROM receipt_details rd
                JOIN receipts r ON rd.receipt_id = r.id
                JOIN products p ON rd.product_id = p.id
                WHERE r.customer_id = ?
                GROUP BY p.id
                ORDER BY total_quantity DESC, purchase_count DESC
                LIMIT ?
            """
            
            return self.db.execute_query(query, (customer_id, limit)) or []
        except Exception as e:
            logger.error(f"Error obteniendo productos favoritos: {e}")
            return []
    
    # ==================== SISTEMA DE FIDELIZACIÓN ====================
    
    def get_customer_loyalty_points(self, customer_id: int) -> Dict:
        """Obtener puntos de fidelización del cliente"""
        try:
            query = """
                SELECT 
                    COALESCE(SUM(CASE WHEN movement_type = 'EARNED' THEN points ELSE 0 END), 0) as total_earned,
                    COALESCE(SUM(CASE WHEN movement_type = 'REDEEMED' THEN points ELSE 0 END), 0) as total_redeemed,
                    COALESCE(SUM(CASE WHEN movement_type = 'EARNED' THEN points ELSE -points END), 0) as current_balance
                FROM customer_loyalty_points
                WHERE customer_id = ?
            """
            
            result = self.db.execute_single(query, (customer_id,))
            
            return {
                'total_earned': result['total_earned'] if result else 0,
                'total_redeemed': result['total_redeemed'] if result else 0,
                'current_balance': result['current_balance'] if result else 0
            }
        except Exception as e:
            logger.error(f"Error obteniendo puntos de fidelización: {e}")
            return {'total_earned': 0, 'total_redeemed': 0, 'current_balance': 0}
    
    def add_loyalty_points(self, customer_id: int, points: int, movement_type: str, 
                          description: str, reference_id: Optional[int] = None) -> bool:
        """Agregar puntos de fidelización"""
        try:
            query = """
                INSERT INTO customer_loyalty_points (
                    customer_id, points, movement_type, description, 
                    reference_id, created_at
                ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            
            values = (customer_id, points, movement_type, description, reference_id)
            success = self.db.execute_query(query, values)
            
            if success:
                logger.info(f"Puntos de fidelización agregados: {customer_id} - {points} puntos")
            
            return success
            
        except Exception as e:
            logger.error(f"Error agregando puntos de fidelización: {e}")
            return False
    
    # ==================== REPORTES Y ANÁLISIS ====================
    
    def get_customer_statistics(self, customer_id: int) -> Dict:
        """Obtener estadísticas completas del cliente"""
        try:
            # Estadísticas básicas
            basic_stats = self.db.execute_single("""
                SELECT 
                    COUNT(DISTINCT r.id) as total_purchases,
                    COALESCE(SUM(r.total), 0) as total_spent,
                    COALESCE(AVG(r.total), 0) as avg_purchase,
                    MAX(r.date) as last_purchase_date,
                    MIN(r.date) as first_purchase_date,
                    COUNT(DISTINCT rd.product_id) as different_products
                FROM receipts r
                LEFT JOIN receipt_details rd ON r.id = rd.receipt_id
                WHERE r.customer_id = ?
            """, (customer_id,))
            
            # Estadísticas de cuenta corriente
            account_stats = self.db.execute_single("""
                SELECT 
                    balance,
                    credit_limit,
                    CASE WHEN credit_limit > 0 THEN (balance / credit_limit) * 100 ELSE 0 END as credit_usage_pct
                FROM customer_accounts
                WHERE customer_id = ?
            """, (customer_id,))
            
            # Combinar estadísticas
            stats = basic_stats.copy() if basic_stats else {}
            if account_stats:
                stats.update(account_stats)
            
            # Calcular días desde última compra
            if stats.get('last_purchase_date'):
                try:
                    last_date = datetime.strptime(stats['last_purchase_date'], '%Y-%m-%d')
                    days_since_last = (datetime.now() - last_date).days
                    stats['days_since_last_purchase'] = days_since_last
                except:
                    stats['days_since_last_purchase'] = None
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del cliente: {e}")
            return {}
    
    def get_top_customers(self, limit: int = 50, period_days: int = 365) -> List[Dict]:
        """Obtener mejores clientes por volumen de compras"""
        try:
            query = """
                SELECT c.*, 
                       COUNT(DISTINCT r.id) as total_purchases,
                       COALESCE(SUM(r.total), 0) as total_spent,
                       COALESCE(AVG(r.total), 0) as avg_purchase,
                       MAX(r.date) as last_purchase_date,
                       COALESCE(ca.balance, 0) as account_balance
                FROM clientes c
                LEFT JOIN receipts r ON c.id = r.customer_id 
                    AND r.date >= date('now', '-{} days')
                LEFT JOIN customer_accounts ca ON c.id = ca.customer_id
                WHERE c.active = 1
                GROUP BY c.id
                HAVING total_purchases > 0
                ORDER BY total_spent DESC, total_purchases DESC
                LIMIT ?
            """.format(period_days)
            
            return self.db.execute_query(query, (limit,)) or []
        except Exception as e:
            logger.error(f"Error obteniendo mejores clientes: {e}")
            return []
    
    def get_customers_with_debt(self) -> List[Dict]:
        """Obtener clientes con deuda pendiente"""
        try:
            query = """
                SELECT c.*, ca.balance, ca.credit_limit,
                       CASE WHEN ca.credit_limit > 0 THEN (ca.balance / ca.credit_limit) * 100 ELSE 0 END as credit_usage_pct,
                       MAX(r.date) as last_purchase_date
                FROM clientes c
                JOIN customer_accounts ca ON c.id = ca.customer_id
                LEFT JOIN receipts r ON c.id = r.customer_id
                WHERE c.active = 1 AND ca.balance > 0
                GROUP BY c.id
                ORDER BY ca.balance DESC
            """
            
            return self.db.execute_query(query) or []
        except Exception as e:
            logger.error(f"Error obteniendo clientes con deuda: {e}")
            return []
    
    # ==================== UTILIDADES ====================
    
    def validate_customer_data(self, customer_data: Dict, is_update: bool = False) -> Dict:
        """Validar datos del cliente"""
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Validar campos requeridos
            if not customer_data.get('name') and not customer_data.get('business_name'):
                validation['errors'].append("Debe proporcionar nombre o razón social")
            
            # Validar documento si se proporciona
            if customer_data.get('document_number'):
                # Verificar duplicados (excepto en actualización del mismo cliente)
                existing_query = "SELECT id FROM clientes WHERE document_number = ? AND active = 1"
                params = (customer_data['document_number'],)
                
                if is_update and customer_data.get('id'):
                    existing_query += " AND id != ?"
                    params += (customer_data['id'],)
                
                existing = self.db.execute_single(existing_query, params)
                if existing:
                    validation['errors'].append("Ya existe un cliente con este número de documento")
            
            # Validar email
            if customer_data.get('email'):
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, customer_data['email']):
                    validation['errors'].append("Formato de email inválido")
            
            # Validar límite de crédito
            if customer_data.get('credit_limit', 0) < 0:
                validation['errors'].append("El límite de crédito no puede ser negativo")
            
            validation['valid'] = len(validation['errors']) == 0
            return validation
            
        except Exception as e:
            logger.error(f"Error validando datos del cliente: {e}")
            return {
                'valid': False,
                'errors': [f"Error en validación: {str(e)}"],
                'warnings': []
            }