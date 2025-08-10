"""
Gestor de Clientes Simplificado - AlmacénPro v2.0
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class CustomerManager:
    """Gestor simplificado de clientes"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        logger.info("CustomerManager inicializado")
    
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