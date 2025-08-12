"""
Modelo Financiero - AlmacénPro v2.0 MVC
Modelo especializado para gestión financiera y caja
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from PyQt5.QtCore import pyqtSignal

from models.base_model import BaseModel
from models.entities import FinancialTransaction, CashRegister

logger = logging.getLogger(__name__)

class FinancialModel(BaseModel):
    """Modelo de datos para operaciones financieras"""
    
    # Señales específicas financieras
    transaction_created = pyqtSignal(dict)
    cash_register_opened = pyqtSignal(dict)
    cash_register_closed = pyqtSignal(dict)
    balance_updated = pyqtSignal(float)
    
    def __init__(self, financial_manager=None, parent=None):
        super().__init__(parent)
        self.financial_manager = financial_manager
        
        # Estado del modelo
        self._transactions = []
        self._current_cash_register = None
        self._daily_balance = 0.0
        self._monthly_balance = 0.0
        
        self.logger = logging.getLogger(f"{__name__}.FinancialModel")
    
    # === PROPIEDADES ===
    
    @property
    def transactions(self) -> List[FinancialTransaction]:
        """Lista de transacciones"""
        return self._transactions.copy()
    
    @property
    def current_cash_register(self) -> Optional[CashRegister]:
        """Caja actual"""
        return self._current_cash_register
    
    @property
    def daily_balance(self) -> float:
        """Balance diario"""
        return self._daily_balance
    
    @property
    def monthly_balance(self) -> float:
        """Balance mensual"""
        return self._monthly_balance
    
    @property
    def is_cash_register_open(self) -> bool:
        """Verificar si hay caja abierta"""
        return self._current_cash_register is not None and self._current_cash_register.estado == "ABIERTA"
    
    # === MÉTODOS PÚBLICOS ===
    
    def load_transactions(self, filters: Dict[str, Any] = None) -> bool:
        """Cargar transacciones"""
        if not self.financial_manager:
            self._set_error("Manager financiero no disponible")
            return False
        
        try:
            self.start_loading()
            
            # Cargar transacciones
            transactions_data = self.financial_manager.get_transactions(filters or {})
            self._transactions = [FinancialTransaction.from_dict(t) for t in transactions_data]
            
            # Calcular balances
            self._calculate_balances()
            
            self.data_changed.emit()
            self.logger.info(f"Cargadas {len(self._transactions)} transacciones")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cargando transacciones: {e}")
            self._set_error(f"Error cargando transacciones: {str(e)}")
            return False
        finally:
            self.finish_loading()
    
    def open_cash_register(self, initial_amount: float, user_id: int, user_name: str) -> bool:
        """Abrir caja registradora"""
        if self.is_cash_register_open:
            self._set_error("Ya hay una caja abierta")
            return False
        
        try:
            cash_register_data = {
                'usuario_id': user_id,
                'usuario_nombre': user_name,
                'monto_inicial': initial_amount,
                'fecha_apertura': datetime.now(),
                'estado': 'ABIERTA'
            }
            
            if self.financial_manager:
                result = self.financial_manager.open_cash_register(cash_register_data)
                if result.get('success'):
                    cash_register_data['id'] = result.get('cash_register_id')
            
            self._current_cash_register = CashRegister.from_dict(cash_register_data)
            
            self.cash_register_opened.emit(cash_register_data)
            self.data_changed.emit()
            
            self.logger.info(f"Caja abierta con monto inicial: ${initial_amount}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error abriendo caja: {e}")
            self._set_error(f"Error abriendo caja: {str(e)}")
            return False
    
    def close_cash_register(self, final_amount: float) -> bool:
        """Cerrar caja registradora"""
        if not self.is_cash_register_open:
            self._set_error("No hay caja abierta")
            return False
        
        try:
            self._current_cash_register.close_register(final_amount)
            
            if self.financial_manager:
                result = self.financial_manager.close_cash_register(
                    self._current_cash_register.id,
                    self._current_cash_register.to_dict()
                )
                if not result.get('success'):
                    self._set_error(result.get('message', 'Error cerrando caja'))
                    return False
            
            cash_register_data = self._current_cash_register.to_dict()
            self.cash_register_closed.emit(cash_register_data)
            
            # Limpiar caja actual
            self._current_cash_register = None
            
            self.data_changed.emit()
            self.logger.info("Caja cerrada exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cerrando caja: {e}")
            self._set_error(f"Error cerrando caja: {str(e)}")
            return False
    
    def record_transaction(self, transaction_data: Dict[str, Any]) -> bool:
        """Registrar transacción financiera"""
        try:
            # Validar datos
            if not self._validate_transaction_data(transaction_data):
                return False
            
            # Crear transacción
            transaction = FinancialTransaction.from_dict(transaction_data)
            
            if self.financial_manager:
                result = self.financial_manager.create_transaction(transaction_data)
                if result.get('success'):
                    transaction_data['id'] = result.get('transaction_id')
                else:
                    self._set_error(result.get('message', 'Error registrando transacción'))
                    return False
            
            # Agregar a lista local
            self._transactions.append(transaction)
            
            # Actualizar caja si está abierta
            if self.is_cash_register_open:
                if transaction.tipo == "INGRESO":
                    self._current_cash_register.monto_ventas += transaction.monto
                else:
                    self._current_cash_register.monto_egresos += transaction.monto
            
            # Recalcular balances
            self._calculate_balances()
            
            self.transaction_created.emit(transaction_data)
            self.data_changed.emit()
            
            self.logger.info(f"Transacción registrada: {transaction}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registrando transacción: {e}")
            self._set_error(f"Error registrando transacción: {str(e)}")
            return False
    
    def get_daily_transactions(self, target_date: date = None) -> List[FinancialTransaction]:
        """Obtener transacciones del día"""
        if target_date is None:
            target_date = date.today()
        
        return [
            t for t in self._transactions
            if t.fecha_transaccion and t.fecha_transaccion.date() == target_date
        ]
    
    def get_monthly_transactions(self, year: int = None, month: int = None) -> List[FinancialTransaction]:
        """Obtener transacciones del mes"""
        if year is None or month is None:
            now = datetime.now()
            year = year or now.year
            month = month or now.month
        
        return [
            t for t in self._transactions
            if t.fecha_transaccion and 
               t.fecha_transaccion.year == year and 
               t.fecha_transaccion.month == month
        ]
    
    def calculate_balance_by_period(self, start_date: date, end_date: date) -> Dict[str, float]:
        """Calcular balance por período"""
        period_transactions = [
            t for t in self._transactions
            if t.fecha_transaccion and 
               start_date <= t.fecha_transaccion.date() <= end_date
        ]
        
        ingresos = sum(t.monto for t in period_transactions if t.tipo == "INGRESO")
        egresos = sum(t.monto for t in period_transactions if t.tipo == "EGRESO")
        balance = ingresos - egresos
        
        return {
            'ingresos': ingresos,
            'egresos': egresos,
            'balance': balance,
            'transacciones': len(period_transactions)
        }
    
    # === MÉTODOS PROTEGIDOS ===
    
    def _validate_transaction_data(self, data: Dict[str, Any]) -> bool:
        """Validar datos de transacción"""
        self._validation_errors.clear()
        
        if not data.get('concepto', '').strip():
            self._add_validation_error("El concepto es obligatorio")
        
        try:
            monto = float(data.get('monto', 0))
            if monto <= 0:
                self._add_validation_error("El monto debe ser mayor a cero")
        except (ValueError, TypeError):
            self._add_validation_error("Monto inválido")
        
        if data.get('tipo') not in ['INGRESO', 'EGRESO']:
            self._add_validation_error("Tipo de transacción inválido")
        
        return len(self._validation_errors) == 0
    
    def _calculate_balances(self):
        """Calcular balances diario y mensual"""
        today = date.today()
        
        # Balance diario
        daily_transactions = self.get_daily_transactions(today)
        daily_ingresos = sum(t.monto for t in daily_transactions if t.tipo == "INGRESO")
        daily_egresos = sum(t.monto for t in daily_transactions if t.tipo == "EGRESO")
        self._daily_balance = daily_ingresos - daily_egresos
        
        # Balance mensual
        monthly_transactions = self.get_monthly_transactions(today.year, today.month)
        monthly_ingresos = sum(t.monto for t in monthly_transactions if t.tipo == "INGRESO")
        monthly_egresos = sum(t.monto for t in monthly_transactions if t.tipo == "EGRESO")
        self._monthly_balance = monthly_ingresos - monthly_egresos
        
        self.balance_updated.emit(self._daily_balance)
    
    def _get_default_values(self) -> Dict[str, Any]:
        """Valores por defecto para transacción"""
        return {
            'tipo': 'INGRESO',
            'concepto': '',
            'monto': 0.0,
            'metodo_pago': 'EFECTIVO',
            'usuario_id': 1,
            'estado': 'ACTIVA'
        }