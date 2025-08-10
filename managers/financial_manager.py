"""
Gestor Financiero - AlmacénPro v2.0
Sistema completo de gestión financiera y contable
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal

logger = logging.getLogger(__name__)

class FinancialManager:
    """Gestor completo de finanzas y contabilidad"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        logger.info("FinancialManager inicializado")
    
    # ==================== GESTIÓN DE CAJAS ====================
    
    def get_cash_registers(self, active_only: bool = True) -> List[Dict]:
        """Obtener cajas registradoras"""
        try:
            query = """
                SELECT cr.*, 
                       cs.id as current_session_id,
                       cs.monto_apertura as opening_balance,
                       (cs.monto_apertura + cs.monto_ventas) as current_balance,
                       cs.fecha_apertura as opened_at,
                       u.username as operator_name
                FROM cajas cr
                LEFT JOIN sesiones_caja cs ON cr.id = cs.caja_id AND cs.estado = 'ABIERTA'
                LEFT JOIN usuarios u ON cs.usuario_id = u.id
                WHERE cr.activo = 1 OR ? = 0
                ORDER BY cr.nombre
            """
            return self.db.execute_query(query, (1 if not active_only else 0,)) or []
        except Exception as e:
            logger.error(f"Error obteniendo cajas: {e}")
            return []
    
    def open_cash_session(self, cash_register_id: int, opening_balance: float, user_id: int, notes: str = "") -> Optional[int]:
        """Abrir sesión de caja"""
        try:
            # Verificar que no hay sesión abierta
            existing_session = self.db.execute_single("""
                SELECT id FROM sesiones_caja 
                WHERE caja_id = ? AND estado = 'ABIERTA'
            """, (cash_register_id,))
            
            if existing_session:
                raise ValueError("Ya existe una sesión abierta para esta caja")
            
            query = """
                INSERT INTO sesiones_caja (
                    caja_id, usuario_id, monto_apertura, monto_ventas,
                    fecha_apertura, estado, observaciones
                ) VALUES (?, ?, ?, 0, CURRENT_TIMESTAMP, 'ABIERTA', ?)
            """
            
            session_id = self.db.execute_insert(query, (
                cash_register_id,
                user_id,
                opening_balance,
                notes
            ))
            
            if session_id:
                # Registrar movimiento inicial
                self.add_cash_movement(
                    session_id,
                    opening_balance,
                    'APERTURA',
                    'Apertura de caja',
                    'SESION_CAJA',
                    session_id
                )
                
                logger.info(f"Sesión de caja abierta: {session_id}")
            
            return session_id
            
        except Exception as e:
            logger.error(f"Error abriendo sesión de caja: {e}")
            return None
    
    def close_cash_session(self, session_id: int, closing_balance: float, user_id: int, notes: str = "") -> bool:
        """Cerrar sesión de caja"""
        try:
            # Obtener sesión actual
            session = self.db.execute_single("""
                SELECT * FROM sesiones_caja WHERE id = ? AND estado = 'ABIERTA'
            """, (session_id,))
            
            if not session:
                raise ValueError("Sesión no encontrada o ya cerrada")
            
            # Calcular balance esperado (apertura + ventas)
            expected_balance = float(session['monto_apertura']) + float(session['monto_ventas'])
            difference = closing_balance - expected_balance
            
            # Actualizar sesión
            update_query = """
                UPDATE sesiones_caja SET
                    monto_cierre = ?, 
                    diferencia = ?,
                    fecha_cierre = CURRENT_TIMESTAMP,
                    estado = 'CERRADA',
                    observaciones = COALESCE(observaciones || '\n', '') || ?
                WHERE id = ?
            """
            
            self.db.execute_update(update_query, (closing_balance, difference, notes, session_id))
            
            if difference != 0:
                # Registrar diferencia si existe
                movement_type = 'SOBRANTE' if difference > 0 else 'FALTANTE'
                movement_desc = f"Diferencia en cierre: {'+' if difference > 0 else ''}{difference}"
                self.add_cash_movement(
                    session_id,
                    abs(difference),
                    movement_type,
                    movement_desc,
                    'CIERRE_CAJA',
                    session_id
                )
            
            logger.info(f"Sesión de caja cerrada: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cerrando sesión de caja: {e}")
            return False
    
    def get_current_session(self, cash_register_id: int) -> Optional[Dict]:
        """Obtener sesión actual de una caja"""
        try:
            return self.db.execute_single("""
                SELECT sc.*, c.nombre as caja_nombre, u.username as usuario_nombre
                FROM sesiones_caja sc
                JOIN cajas c ON sc.caja_id = c.id
                JOIN usuarios u ON sc.usuario_id = u.id
                WHERE sc.caja_id = ? AND sc.estado = 'ABIERTA'
            """, (cash_register_id,))
        except Exception as e:
            logger.error(f"Error obteniendo sesión actual: {e}")
            return None
    
    def add_cash_movement(self, session_id: int, amount: float, movement_type: str,
                         description: str, reference_type: str = None, 
                         reference_id: int = None) -> Optional[int]:
        """Agregar movimiento de caja"""
        try:
            # Obtener sesión actual
            session = self.db.execute_single("""
                SELECT monto_apertura, monto_ventas FROM sesiones_caja 
                WHERE id = ? AND estado = 'ABIERTA'
            """, (session_id,))
            
            if not session:
                raise ValueError("Sesión de caja no encontrada o cerrada")
            
            # Calcular balance anterior
            previous_balance = float(session['monto_apertura']) + float(session['monto_ventas'])
            
            # Calcular nuevo balance según el tipo de movimiento
            if movement_type in ['VENTA', 'COBRO', 'APERTURA', 'SOBRANTE']:
                new_balance = previous_balance + amount
            elif movement_type in ['GASTO', 'PAGO', 'RETIRO', 'FALTANTE']:
                new_balance = previous_balance - amount
            else:
                new_balance = previous_balance
            
            # Insertar movimiento
            movement_id = self.db.execute_insert("""
                INSERT INTO movimientos_caja (
                    sesion_caja_id, tipo_movimiento, concepto, importe,
                    saldo_anterior, saldo_nuevo, venta_id, usuario_id,
                    fecha_movimiento, observaciones
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            """, (
                session_id, movement_type, description, amount,
                previous_balance, new_balance, 
                reference_id if reference_type == 'VENTA' else None,
                1,  # Usuario por defecto, debería pasarse como parámetro
                f"{reference_type}: {reference_id}" if reference_type and reference_id else None
            ))
            
            # Actualizar balance de la sesión si es una venta
            if movement_type == 'VENTA':
                self.db.execute_update("""
                    UPDATE sesiones_caja 
                    SET monto_ventas = monto_ventas + ?
                    WHERE id = ?
                """, (amount, session_id))
            
            return movement_id
            
        except Exception as e:
            logger.error(f"Error agregando movimiento de caja: {e}")
            return None
    
    def get_cash_movements(self, session_id: int) -> List[Dict]:
        """Obtener movimientos de una sesión de caja"""
        try:
            return self.db.execute_query("""
                SELECT * FROM movimientos_caja 
                WHERE sesion_caja_id = ?
                ORDER BY fecha_movimiento ASC
            """, (session_id,)) or []
        except Exception as e:
            logger.error(f"Error obteniendo movimientos de caja: {e}")
            return []
    
    # ==================== INTEGRACIÓN CON VENTAS ====================
    
    def record_sale_payment(self, session_id: int, sale_id: int, amount: float, payment_method: str) -> bool:
        """Registrar pago de venta en caja"""
        try:
            if payment_method == 'EFECTIVO':
                return self.add_cash_movement(
                    session_id,
                    amount,
                    'VENTA',
                    f'Venta #{sale_id} - {payment_method}',
                    'VENTA',
                    sale_id
                ) is not None
            return True  # Otros métodos de pago no afectan la caja
        except Exception as e:
            logger.error(f"Error registrando pago de venta: {e}")
            return False
    
    def get_session_summary(self, session_id: int) -> Dict:
        """Obtener resumen de sesión de caja"""
        try:
            session = self.db.execute_single("""
                SELECT sc.*, c.nombre as caja_nombre, u.username as usuario_nombre
                FROM sesiones_caja sc
                JOIN cajas c ON sc.caja_id = c.id
                JOIN usuarios u ON sc.usuario_id = u.id
                WHERE sc.id = ?
            """, (session_id,))
            
            if not session:
                return {}
            
            movements = self.get_cash_movements(session_id)
            
            # Calcular totales por tipo
            totals_by_type = {}
            for movement in movements:
                mov_type = movement['tipo_movimiento']
                if mov_type not in totals_by_type:
                    totals_by_type[mov_type] = 0
                totals_by_type[mov_type] += float(movement['importe'])
            
            session_dict = dict(session)
            session_dict['movements'] = movements
            session_dict['totals_by_type'] = totals_by_type
            session_dict['total_movements'] = len(movements)
            
            return session_dict
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen de sesión: {e}")
            return {}
    
    # ==================== REPORTES FINANCIEROS ====================
    
    def get_daily_cash_report(self, target_date: str = None, cash_register_id: int = None) -> Dict:
        """Generar reporte diario de caja"""
        try:
            if not target_date:
                target_date = datetime.now().strftime('%Y-%m-%d')
            
            query = """
                SELECT sc.*, c.nombre as caja_nombre, u.username as usuario_nombre,
                       COUNT(mc.id) as total_movimientos,
                       SUM(CASE WHEN mc.tipo_movimiento = 'VENTA' THEN mc.importe ELSE 0 END) as total_ventas_efectivo
                FROM sesiones_caja sc
                JOIN cajas c ON sc.caja_id = c.id
                JOIN usuarios u ON sc.usuario_id = u.id
                LEFT JOIN movimientos_caja mc ON sc.id = mc.sesion_caja_id
                WHERE DATE(sc.fecha_apertura) = ?
            """
            params = [target_date]
            
            if cash_register_id:
                query += " AND sc.caja_id = ?"
                params.append(cash_register_id)
            
            query += " GROUP BY sc.id ORDER BY sc.fecha_apertura"
            
            sessions = self.db.execute_query(query, params) or []
            
            return {
                'date': target_date,
                'sessions': [dict(session) for session in sessions],
                'total_sessions': len(sessions)
            }
            
        except Exception as e:
            logger.error(f"Error generando reporte diario: {e}")
            return {'error': str(e)}
    
    # ==================== UTILIDADES ====================
    
    def validate_cash_register(self, cash_register_id: int) -> bool:
        """Validar que la caja existe y está activa"""
        try:
            result = self.db.execute_single("""
                SELECT id FROM cajas WHERE id = ? AND activo = 1
            """, (cash_register_id,))
            return result is not None
        except Exception as e:
            logger.error(f"Error validando caja: {e}")
            return False