"""
Gestor Financiero - AlmacénPro v2.0
Sistema completo de gestión financiera y contable
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from utils.audit_logger import get_audit_logger

logger = logging.getLogger(__name__)

class FinancialManager:
    """Gestor completo de finanzas y contabilidad"""
    
    def __init__(self, db_manager, current_user: Dict = None):
        self.db = db_manager
        self.current_user = current_user
        self.audit_logger = get_audit_logger(db_manager, current_user)
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
                WHERE cr.activo = ? OR ? = 0
                ORDER BY cr.nombre
            """
            return self.db.execute_query(query, (1 if active_only else 0, 1 if active_only else 0)) or []
        except Exception as e:
            logger.error(f"Error obteniendo cajas: {e}")
            return []
    
    def open_cash_session(self, cash_register_id: int, opening_balance: float, notes: str = "") -> Optional[int]:
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
            
            values = (
                cash_register_id,
                self.current_user.get('id') if self.current_user else None,
                opening_balance,
                notes
            )
            
            session_id = self.db.execute_insert(query, values)
            
            if session_id:
                # Registrar movimiento inicial
                self.add_cash_movement(
                    session_id,
                    opening_balance,
                    'OPENING',
                    'Apertura de caja',
                    'CASH_SESSION',
                    session_id
                )
                
                self.audit_logger.log_action('CASH_SESSION_OPENED', 'cash_sessions', session_id)
                logger.info(f"Sesión de caja abierta: {session_id}")
            
            return session_id
            
        except Exception as e:
            logger.error(f"Error abriendo sesión de caja: {e}")
            return None
    
    def close_cash_session(self, session_id: int, closing_balance: float, notes: str = "") -> bool:
        """Cerrar sesión de caja"""
        try:
            # Obtener sesión actual
            session = self.db.execute_single("""
                SELECT * FROM cash_sessions WHERE id = ? AND status = 'OPEN'
            """, (session_id,))
            
            if not session:
                raise ValueError("Sesión no encontrada o ya cerrada")
            
            # Calcular diferencia
            difference = closing_balance - session['current_balance']
            
            # Actualizar sesión
            update_query = """
                UPDATE cash_sessions SET
                    closing_balance = ?, 
                    difference = ?,
                    closed_at = CURRENT_TIMESTAMP,
                    status = 'CLOSED',
                    closing_notes = ?
                WHERE id = ?
            """
            
            success = self.db.execute_query(update_query, (closing_balance, difference, notes, session_id))
            
            if success and difference != 0:
                # Registrar diferencia si existe
                movement_type = 'SURPLUS' if difference > 0 else 'SHORTAGE'
                self.add_cash_movement(
                    session_id,
                    abs(difference),
                    movement_type,
                    f"Diferencia de cierre: {notes}",
                    'CASH_SESSION',
                    session_id
                )
            
            if success:
                self.audit_logger.log_action('CASH_SESSION_CLOSED', 'cash_sessions', session_id)
                logger.info(f"Sesión de caja cerrada: {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error cerrando sesión de caja: {e}")
            return False
    
    def add_cash_movement(self, session_id: int, amount: float, movement_type: str,
                         description: str, reference_type: str = None, 
                         reference_id: int = None) -> Optional[int]:
        """Agregar movimiento de caja"""
        try:
            # Obtener sesión actual
            session = self.db.execute_single("""
                SELECT current_balance FROM cash_sessions WHERE id = ? AND status = 'OPEN'
            """, (session_id,))
            
            if not session:
                raise ValueError("Sesión de caja no encontrada o cerrada")
            
            # Calcular nuevo balance
            if movement_type in ['SALE', 'PAYMENT_RECEIVED', 'OPENING', 'SURPLUS']:
                new_balance = session['current_balance'] + amount
            elif movement_type in ['EXPENSE', 'PAYMENT_MADE', 'WITHDRAWAL', 'SHORTAGE']:
                new_balance = session['current_balance'] - amount
            else:
                new_balance = session['current_balance']
            
            # Insertar movimiento
            movement_query = """
                INSERT INTO cash_movements (
                    session_id, amount, movement_type, description,
                    reference_type, reference_id, balance_after, user_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            
            movement_values = (
                session_id, amount, movement_type, description,
                reference_type, reference_id, new_balance,
                self.current_user.get('id') if self.current_user else None
            )
            
            movement_id = self.db.execute_query(movement_query, movement_values, return_id=True)
            
            if movement_id:
                # Actualizar balance de la sesión
                self.db.execute_query("""
                    UPDATE cash_sessions SET current_balance = ? WHERE id = ?
                """, (new_balance, session_id))
                
                logger.info(f"Movimiento de caja agregado: {movement_id}")
            
            return movement_id
            
        except Exception as e:
            logger.error(f"Error agregando movimiento de caja: {e}")
            return None
    
    def get_cash_movements(self, session_id: Optional[int] = None, 
                          days: int = 30) -> List[Dict]:
        """Obtener movimientos de caja"""
        try:
            base_query = """
                SELECT cm.*, cs.cash_register_id, cr.name as register_name,
                       u.username as user_name
                FROM cash_movements cm
                LEFT JOIN cash_sessions cs ON cm.session_id = cs.id
                LEFT JOIN cash_registers cr ON cs.cash_register_id = cr.id
                LEFT JOIN users u ON cm.user_id = u.id
                WHERE cm.created_at >= date('now', '-{} days')
            """.format(days)
            
            values = []
            if session_id:
                base_query += " AND cm.session_id = ?"
                values.append(session_id)
            
            base_query += " ORDER BY cm.created_at DESC"
            
            return self.db.execute_query(base_query, tuple(values)) or []
            
        except Exception as e:
            logger.error(f"Error obteniendo movimientos de caja: {e}")
            return []
    
    # ==================== GESTIÓN DE GASTOS ====================
    
    def get_expense_categories(self, active_only: bool = True) -> List[Dict]:
        """Obtener categorías de gastos"""
        try:
            query = """
                SELECT ec.*, COUNT(e.id) as expense_count,
                       COALESCE(SUM(e.amount), 0) as total_amount
                FROM expense_categories ec
                LEFT JOIN expenses e ON ec.id = e.category_id 
                    AND e.date >= date('now', '-30 days')
                WHERE ec.active = ? OR ? = 0
                GROUP BY ec.id
                ORDER BY ec.name
            """
            return self.db.execute_query(query, (1 if active_only else 0, 1 if active_only else 0)) or []
        except Exception as e:
            logger.error(f"Error obteniendo categorías de gastos: {e}")
            return []
    
    def create_expense(self, expense_data: Dict) -> Optional[int]:
        """Crear gasto"""
        try:
            query = """
                INSERT INTO expenses (
                    category_id, amount, description, supplier_id, 
                    payment_method, reference_number, date, user_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            
            values = (
                expense_data['category_id'],
                expense_data['amount'],
                expense_data.get('description', ''),
                expense_data.get('supplier_id'),
                expense_data.get('payment_method', 'CASH'),
                expense_data.get('reference_number', ''),
                expense_data.get('date', datetime.now().strftime('%Y-%m-%d')),
                self.current_user.get('id') if self.current_user else None
            )
            
            expense_id = self.db.execute_query(query, values, return_id=True)
            
            if expense_id:
                self.audit_logger.log_create('expenses', expense_id, expense_data)
                logger.info(f"Gasto creado: {expense_id}")
            
            return expense_id
            
        except Exception as e:
            logger.error(f"Error creando gasto: {e}")
            return None
    
    def get_expenses(self, category_id: Optional[int] = None, 
                    days: int = 30) -> List[Dict]:
        """Obtener gastos"""
        try:
            base_query = """
                SELECT e.*, ec.name as category_name, ec.code as category_code,
                       s.business_name as supplier_name, u.username as user_name
                FROM expenses e
                LEFT JOIN expense_categories ec ON e.category_id = ec.id
                LEFT JOIN suppliers s ON e.supplier_id = s.id
                LEFT JOIN users u ON e.user_id = u.id
                WHERE e.date >= date('now', '-{} days')
            """.format(days)
            
            values = []
            if category_id:
                base_query += " AND e.category_id = ?"
                values.append(category_id)
            
            base_query += " ORDER BY e.date DESC, e.created_at DESC"
            
            return self.db.execute_query(base_query, tuple(values)) or []
            
        except Exception as e:
            logger.error(f"Error obteniendo gastos: {e}")
            return []
    
    # ==================== CUENTAS BANCARIAS ====================
    
    def get_bank_accounts(self, active_only: bool = True) -> List[Dict]:
        """Obtener cuentas bancarias"""
        try:
            query = """
                SELECT ba.*, 
                       COUNT(bt.id) as transaction_count,
                       COALESCE(SUM(CASE WHEN bt.transaction_type = 'CREDIT' THEN bt.amount ELSE 0 END), 0) as total_credits,
                       COALESCE(SUM(CASE WHEN bt.transaction_type = 'DEBIT' THEN bt.amount ELSE 0 END), 0) as total_debits
                FROM bank_accounts ba
                LEFT JOIN bank_transactions bt ON ba.id = bt.account_id 
                    AND bt.date >= date('now', '-30 days')
                WHERE ba.active = ? OR ? = 0
                GROUP BY ba.id
                ORDER BY ba.bank_name, ba.account_number
            """
            return self.db.execute_query(query, (1 if active_only else 0, 1 if active_only else 0)) or []
        except Exception as e:
            logger.error(f"Error obteniendo cuentas bancarias: {e}")
            return []
    
    def create_bank_transaction(self, transaction_data: Dict) -> Optional[int]:
        """Crear transacción bancaria"""
        try:
            # Obtener balance actual de la cuenta
            current_balance = self.db.execute_single("""
                SELECT current_balance FROM bank_accounts WHERE id = ?
            """, (transaction_data['account_id'],))
            
            if not current_balance:
                raise ValueError("Cuenta bancaria no encontrada")
            
            # Calcular nuevo balance
            amount = transaction_data['amount']
            if transaction_data['transaction_type'] == 'CREDIT':
                new_balance = current_balance['current_balance'] + amount
            else:  # DEBIT
                new_balance = current_balance['current_balance'] - amount
            
            # Insertar transacción
            transaction_query = """
                INSERT INTO bank_transactions (
                    account_id, transaction_type, amount, description,
                    reference_number, date, balance_after, user_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            
            transaction_values = (
                transaction_data['account_id'],
                transaction_data['transaction_type'],
                amount,
                transaction_data.get('description', ''),
                transaction_data.get('reference_number', ''),
                transaction_data.get('date', datetime.now().strftime('%Y-%m-%d')),
                new_balance,
                self.current_user.get('id') if self.current_user else None
            )
            
            transaction_id = self.db.execute_query(transaction_query, transaction_values, return_id=True)
            
            if transaction_id:
                # Actualizar balance de la cuenta
                self.db.execute_query("""
                    UPDATE bank_accounts SET current_balance = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (new_balance, transaction_data['account_id']))
                
                self.audit_logger.log_create('bank_transactions', transaction_id, transaction_data)
                logger.info(f"Transacción bancaria creada: {transaction_id}")
            
            return transaction_id
            
        except Exception as e:
            logger.error(f"Error creando transacción bancaria: {e}")
            return None
    
    # ==================== REPORTES FINANCIEROS ====================
    
    def get_financial_summary(self, start_date: str, end_date: str) -> Dict:
        """Obtener resumen financiero por período"""
        try:
            # Ingresos por ventas
            sales_income = self.db.execute_single("""
                SELECT COALESCE(SUM(total), 0) as total_sales
                FROM receipts 
                WHERE date BETWEEN ? AND ? AND status != 'CANCELLED'
            """, (start_date, end_date))
            
            # Gastos
            expenses_total = self.db.execute_single("""
                SELECT COALESCE(SUM(amount), 0) as total_expenses
                FROM expenses 
                WHERE date BETWEEN ? AND ?
            """, (start_date, end_date))
            
            # Compras
            purchases_total = self.db.execute_single("""
                SELECT COALESCE(SUM(total_amount), 0) as total_purchases
                FROM purchase_orders 
                WHERE date BETWEEN ? AND ? AND status = 'COMPLETED'
            """, (start_date, end_date))
            
            # Movimientos de caja
            cash_movements = self.db.execute_single("""
                SELECT 
                    COALESCE(SUM(CASE WHEN movement_type IN ('SALE', 'PAYMENT_RECEIVED') THEN amount ELSE 0 END), 0) as cash_in,
                    COALESCE(SUM(CASE WHEN movement_type IN ('EXPENSE', 'PAYMENT_MADE', 'WITHDRAWAL') THEN amount ELSE 0 END), 0) as cash_out
                FROM cash_movements cm
                JOIN cash_sessions cs ON cm.session_id = cs.id
                WHERE DATE(cm.created_at) BETWEEN ? AND ?
            """, (start_date, end_date))
            
            # Cuentas por cobrar
            accounts_receivable = self.db.execute_single("""
                SELECT COALESCE(SUM(balance), 0) as total_receivable
                FROM customer_accounts
                WHERE balance > 0
            """)
            
            # Calcular totales
            total_income = sales_income['total_sales'] if sales_income else 0
            total_expenses = (expenses_total['total_expenses'] if expenses_total else 0) + \
                           (purchases_total['total_purchases'] if purchases_total else 0)
            
            net_profit = total_income - total_expenses
            
            return {
                'period': {'start': start_date, 'end': end_date},
                'income': {
                    'sales': sales_income['total_sales'] if sales_income else 0,
                    'total': total_income
                },
                'expenses': {
                    'operational': expenses_total['total_expenses'] if expenses_total else 0,
                    'purchases': purchases_total['total_purchases'] if purchases_total else 0,
                    'total': total_expenses
                },
                'cash_flow': {
                    'cash_in': cash_movements['cash_in'] if cash_movements else 0,
                    'cash_out': cash_movements['cash_out'] if cash_movements else 0,
                    'net_cash_flow': (cash_movements['cash_in'] if cash_movements else 0) - 
                                   (cash_movements['cash_out'] if cash_movements else 0)
                },
                'profitability': {
                    'gross_profit': total_income - (purchases_total['total_purchases'] if purchases_total else 0),
                    'net_profit': net_profit,
                    'profit_margin': (net_profit / total_income * 100) if total_income > 0 else 0
                },
                'accounts': {
                    'receivable': accounts_receivable['total_receivable'] if accounts_receivable else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen financiero: {e}")
            return {}
    
    def get_sales_by_payment_method(self, start_date: str, end_date: str) -> List[Dict]:
        """Obtener ventas por método de pago"""
        try:
            query = """
                SELECT pm.name as payment_method,
                       COUNT(sp.id) as transaction_count,
                       COALESCE(SUM(sp.amount), 0) as total_amount
                FROM sales_payments sp
                JOIN payment_methods pm ON sp.payment_method_id = pm.id
                JOIN receipts r ON sp.receipt_id = r.id
                WHERE r.date BETWEEN ? AND ? AND r.status != 'CANCELLED'
                GROUP BY pm.id, pm.name
                ORDER BY total_amount DESC
            """
            
            return self.db.execute_query(query, (start_date, end_date)) or []
        except Exception as e:
            logger.error(f"Error obteniendo ventas por método de pago: {e}")
            return []
    
    def get_expense_analysis(self, start_date: str, end_date: str) -> List[Dict]:
        """Obtener análisis de gastos por categoría"""
        try:
            query = """
                SELECT ec.name as category_name,
                       ec.code as category_code,
                       COUNT(e.id) as expense_count,
                       COALESCE(SUM(e.amount), 0) as total_amount,
                       COALESCE(AVG(e.amount), 0) as avg_amount
                FROM expense_categories ec
                LEFT JOIN expenses e ON ec.id = e.category_id
                    AND e.date BETWEEN ? AND ?
                WHERE ec.active = 1
                GROUP BY ec.id
                HAVING expense_count > 0
                ORDER BY total_amount DESC
            """
            
            return self.db.execute_query(query, (start_date, end_date)) or []
        except Exception as e:
            logger.error(f"Error obteniendo análisis de gastos: {e}")
            return []
    
    # ==================== PRESUPUESTOS ====================
    
    def get_budgets(self, year: int) -> List[Dict]:
        """Obtener presupuestos del año"""
        try:
            query = """
                SELECT b.*, 
                       COUNT(bi.id) as item_count,
                       COALESCE(SUM(bi.budgeted_amount), 0) as total_budgeted,
                       COALESCE(SUM(bi.actual_amount), 0) as total_actual
                FROM budgets b
                LEFT JOIN budget_items bi ON b.id = bi.budget_id
                WHERE b.year = ?
                GROUP BY b.id
                ORDER BY b.name
            """
            
            return self.db.execute_query(query, (year,)) or []
        except Exception as e:
            logger.error(f"Error obteniendo presupuestos: {e}")
            return []
    
    def update_budget_actual(self, budget_id: int) -> bool:
        """Actualizar montos reales del presupuesto"""
        try:
            # Actualizar gastos reales por categoría
            update_query = """
                UPDATE budget_items 
                SET actual_amount = (
                    SELECT COALESCE(SUM(e.amount), 0)
                    FROM expenses e
                    WHERE e.category_id = budget_items.category_id
                      AND strftime('%Y', e.date) = (SELECT CAST(year AS TEXT) FROM budgets WHERE id = budget_items.budget_id)
                )
                WHERE budget_id = ?
            """
            
            success = self.db.execute_query(update_query, (budget_id,))
            
            if success:
                logger.info(f"Presupuesto actualizado: {budget_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error actualizando presupuesto: {e}")
            return False
    
    # ==================== UTILIDADES ====================
    
    def get_cash_flow_projection(self, days: int = 30) -> Dict:
        """Proyección de flujo de caja"""
        try:
            # Ingresos proyectados (basado en promedio de ventas)
            avg_daily_sales = self.db.execute_single("""
                SELECT AVG(daily_sales) as avg_sales
                FROM (
                    SELECT DATE(date) as sale_date, SUM(total) as daily_sales
                    FROM receipts
                    WHERE date >= date('now', '-30 days') AND status != 'CANCELLED'
                    GROUP BY DATE(date)
                )
            """)
            
            # Gastos proyectados (basado en promedio)
            avg_daily_expenses = self.db.execute_single("""
                SELECT AVG(daily_expenses) as avg_expenses
                FROM (
                    SELECT DATE(date) as expense_date, SUM(amount) as daily_expenses
                    FROM expenses
                    WHERE date >= date('now', '-30 days')
                    GROUP BY DATE(date)
                )
            """)
            
            # Cuentas por cobrar próximas a vencer
            upcoming_receivables = self.db.execute_single("""
                SELECT COALESCE(SUM(balance), 0) as total_receivable
                FROM customer_accounts ca
                JOIN customers c ON ca.customer_id = c.id
                WHERE ca.balance > 0 AND c.payment_terms <= ?
            """, (days,))
            
            daily_sales = avg_daily_sales['avg_sales'] if avg_daily_sales else 0
            daily_expenses = avg_daily_expenses['avg_expenses'] if avg_daily_expenses else 0
            
            return {
                'projection_days': days,
                'projected_income': daily_sales * days,
                'projected_expenses': daily_expenses * days,
                'projected_net_flow': (daily_sales - daily_expenses) * days,
                'upcoming_receivables': upcoming_receivables['total_receivable'] if upcoming_receivables else 0,
                'daily_averages': {
                    'sales': daily_sales,
                    'expenses': daily_expenses,
                    'net': daily_sales - daily_expenses
                }
            }
            
        except Exception as e:
            logger.error(f"Error en proyección de flujo de caja: {e}")
            return {}
    
    def validate_financial_operation(self, operation_type: str, amount: float, 
                                   account_id: Optional[int] = None) -> Dict:
        """Validar operación financiera"""
        validation = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        try:
            # Validar cantidad
            if amount <= 0:
                validation['errors'].append("El monto debe ser mayor a cero")
            
            # Validar operaciones específicas
            if operation_type == 'CASH_WITHDRAWAL' and account_id:
                # Verificar fondos disponibles
                account = self.db.execute_single("""
                    SELECT current_balance FROM bank_accounts WHERE id = ?
                """, (account_id,))
                
                if account and account['current_balance'] < amount:
                    validation['errors'].append("Fondos insuficientes en la cuenta")
            
            # Validar límites diarios (ejemplo)
            if amount > 10000:  # Límite ejemplo
                validation['warnings'].append("Monto elevado, requiere autorización especial")
            
            validation['valid'] = len(validation['errors']) == 0
            return validation
            
        except Exception as e:
            logger.error(f"Error validando operación financiera: {e}")
            return {
                'valid': False,
                'errors': [f"Error en validación: {str(e)}"],
                'warnings': []
            }