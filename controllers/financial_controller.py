"""
Controlador Financiero - AlmacénPro v2.0 MVC
Gestión completa de operaciones financieras y caja
"""

import logging
from datetime import datetime, date
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from controllers.base_controller import BaseController
from models.financial_model import FinancialModel

logger = logging.getLogger(__name__)

class FinancialController(BaseController):
    """Controlador MVC para operaciones financieras"""
    
    # Señales personalizadas
    cash_register_opened = pyqtSignal(dict)
    cash_register_closed = pyqtSignal(dict)
    transaction_recorded = pyqtSignal(dict)
    balance_updated = pyqtSignal(float)
    
    def __init__(self, managers, current_user, parent=None):
        super().__init__(managers, current_user, parent)
        
        # Manager financiero
        self.financial_manager = managers.get('financial')
        
        # Modelo de datos
        self.financial_model = FinancialModel(
            financial_manager=self.financial_manager,
            parent=self
        )
        
        # Estado del controlador
        self.current_filters = {}
        
        # Configurar UI y conectar señales
        self.load_ui()
        self.setup_ui()
        self.connect_signals()
        self.connect_model_signals()
        
        # Cargar datos iniciales
        self.load_initial_data()
    
    def get_ui_file_path(self) -> str:
        """Retorna la ruta al archivo .ui"""
        return "views/widgets/financial_widget.ui"
    
    def setup_ui(self):
        """Configurar elementos específicos de la UI"""
        # Configurar tabla de transacciones
        if hasattr(self, 'tblTransacciones'):
            self.setup_transactions_table()
        
        # Configurar sección de caja
        self.setup_cash_register_section()
        
        # Configurar métricas financieras
        self.update_financial_metrics()
        
        # Configurar estado inicial de botones
        self.update_cash_register_buttons()
    
    def connect_signals(self):
        """Conectar señales específicas del controlador"""
        # Botones de caja
        if hasattr(self, 'btnAbrirCaja'):
            self.btnAbrirCaja.clicked.connect(self.open_cash_register)
        
        if hasattr(self, 'btnCerrarCaja'):
            self.btnCerrarCaja.clicked.connect(self.close_cash_register)
        
        # Botones de transacciones
        if hasattr(self, 'btnNuevaTransaccion'):
            self.btnNuevaTransaccion.clicked.connect(self.create_transaction)
        
        if hasattr(self, 'btnIngresoRapido'):
            self.btnIngresoRapido.clicked.connect(self.quick_income)
        
        if hasattr(self, 'btnEgresoRapido'):
            self.btnEgresoRapido.clicked.connect(self.quick_expense)
        
        # Botones de reportes
        if hasattr(self, 'btnReporteDaily'):
            self.btnReporteDaily.clicked.connect(self.generate_daily_report)
        
        if hasattr(self, 'btnReporteMonthly'):
            self.btnReporteMonthly.clicked.connect(self.generate_monthly_report)
        
        # Filtros
        if hasattr(self, 'dateEditDesde'):
            self.dateEditDesde.dateChanged.connect(self.apply_filters)
        
        if hasattr(self, 'dateEditHasta'):
            self.dateEditHasta.dateChanged.connect(self.apply_filters)
        
        if hasattr(self, 'cmbTipoTransaccion'):
            self.cmbTipoTransaccion.currentTextChanged.connect(self.apply_filters)
    
    def connect_model_signals(self):
        """Conectar señales del modelo"""
        self.financial_model.transaction_created.connect(self.on_transaction_created)
        self.financial_model.cash_register_opened.connect(self.on_cash_register_opened)
        self.financial_model.cash_register_closed.connect(self.on_cash_register_closed)
        self.financial_model.balance_updated.connect(self.on_balance_updated)
        self.financial_model.data_changed.connect(self.refresh_displays)
        self.financial_model.error_occurred.connect(self.show_error)
    
    def setup_transactions_table(self):
        """Configurar tabla de transacciones"""
        if not hasattr(self, 'tblTransacciones'):
            return
        
        headers = ["Fecha", "Tipo", "Concepto", "Monto", "Método", "Usuario", "Estado"]
        self.tblTransacciones.setColumnCount(len(headers))
        self.tblTransacciones.setHorizontalHeaderLabels(headers)
        
        # Configurar columnas
        header = self.tblTransacciones.horizontalHeader()
        header.setStretchLastSection(True)
        header.resizeSection(0, 120)  # Fecha
        header.resizeSection(1, 80)   # Tipo
        header.resizeSection(2, 200)  # Concepto
        header.resizeSection(3, 100)  # Monto
        header.resizeSection(4, 100)  # Método
        header.resizeSection(5, 100)  # Usuario
        
        # Configurar selección
        self.tblTransacciones.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tblTransacciones.setAlternatingRowColors(True)
        self.tblTransacciones.setSortingEnabled(True)
    
    def setup_cash_register_section(self):
        """Configurar sección de caja registradora"""
        # Configurar filtros de tipo
        if hasattr(self, 'cmbTipoTransaccion'):
            self.cmbTipoTransaccion.addItems(["Todas", "INGRESO", "EGRESO"])
        
        # Configurar fechas por defecto
        if hasattr(self, 'dateEditDesde'):
            self.dateEditDesde.setDate(QDate.currentDate())
        
        if hasattr(self, 'dateEditHasta'):
            self.dateEditHasta.setDate(QDate.currentDate())
    
    def load_initial_data(self):
        """Cargar datos iniciales"""
        self.refresh_data()
    
    def refresh_data(self):
        """Actualizar todos los datos"""
        try:
            # Cargar transacciones con filtros actuales
            self.financial_model.load_transactions(self.current_filters)
            
            # Actualizar displays
            self.refresh_displays()
            
        except Exception as e:
            logger.error(f"Error actualizando datos financieros: {e}")
            self.show_error(f"Error actualizando datos: {e}")
    
    def refresh_displays(self):
        """Actualizar todas las tablas y métricas"""
        self.update_transactions_table()
        self.update_financial_metrics()
        self.update_cash_register_display()
        self.update_cash_register_buttons()
    
    def update_transactions_table(self):
        """Actualizar tabla de transacciones"""
        if not hasattr(self, 'tblTransacciones'):
            return
        
        transactions = self.financial_model.transactions
        self.tblTransacciones.setRowCount(len(transactions))
        
        for row, transaction in enumerate(transactions):
            self.tblTransacciones.setItem(row, 0, QTableWidgetItem(
                transaction.fecha_transaccion.strftime("%d/%m/%Y %H:%M") if transaction.fecha_transaccion else ""
            ))
            
            # Tipo con color
            tipo_item = QTableWidgetItem(transaction.tipo)
            if transaction.tipo == "INGRESO":
                tipo_item.setBackground(QColor("#e8f5e8"))
            else:
                tipo_item.setBackground(QColor("#ffebee"))
            self.tblTransacciones.setItem(row, 1, tipo_item)
            
            self.tblTransacciones.setItem(row, 2, QTableWidgetItem(transaction.concepto))
            self.tblTransacciones.setItem(row, 3, QTableWidgetItem(f"${transaction.monto:,.2f}"))
            self.tblTransacciones.setItem(row, 4, QTableWidgetItem(transaction.metodo_pago))
            self.tblTransacciones.setItem(row, 5, QTableWidgetItem(transaction.usuario_nombre))
            self.tblTransacciones.setItem(row, 6, QTableWidgetItem(transaction.estado))
    
    def update_financial_metrics(self):
        """Actualizar métricas financieras"""
        try:
            # Balance diario
            daily_balance = self.financial_model.daily_balance
            if hasattr(self, 'lblBalanceDiario'):
                self.lblBalanceDiario.setText(f"${daily_balance:,.2f}")
                # Color según balance
                if daily_balance >= 0:
                    self.lblBalanceDiario.setStyleSheet("color: green; font-weight: bold;")
                else:
                    self.lblBalanceDiario.setStyleSheet("color: red; font-weight: bold;")
            
            # Balance mensual
            monthly_balance = self.financial_model.monthly_balance
            if hasattr(self, 'lblBalanceMensual'):
                self.lblBalanceMensual.setText(f"${monthly_balance:,.2f}")
            
            # Transacciones del día
            today = date.today()
            daily_transactions = self.financial_model.get_daily_transactions(today)
            
            daily_ingresos = sum(t.monto for t in daily_transactions if t.tipo == "INGRESO")
            daily_egresos = sum(t.monto for t in daily_transactions if t.tipo == "EGRESO")
            
            if hasattr(self, 'lblIngresosDiarios'):
                self.lblIngresosDiarios.setText(f"${daily_ingresos:,.2f}")
            
            if hasattr(self, 'lblEgresosDiarios'):
                self.lblEgresosDiarios.setText(f"${daily_egresos:,.2f}")
            
            if hasattr(self, 'lblTransaccionesDiarias'):
                self.lblTransaccionesDiarias.setText(str(len(daily_transactions)))
        
        except Exception as e:
            logger.error(f"Error actualizando métricas financieras: {e}")
    
    def update_cash_register_display(self):
        """Actualizar display de caja registradora"""
        cash_register = self.financial_model.current_cash_register
        
        if cash_register and self.financial_model.is_cash_register_open:
            # Mostrar información de caja abierta
            if hasattr(self, 'lblEstadoCaja'):
                self.lblEstadoCaja.setText("CAJA ABIERTA")
                self.lblEstadoCaja.setStyleSheet("color: green; font-weight: bold;")
            
            if hasattr(self, 'lblMontoInicial'):
                self.lblMontoInicial.setText(f"${cash_register.monto_inicial:,.2f}")
            
            if hasattr(self, 'lblVentasAcumuladas'):
                self.lblVentasAcumuladas.setText(f"${cash_register.monto_ventas:,.2f}")
            
            if hasattr(self, 'lblEgresosAcumulados'):
                self.lblEgresosAcumulados.setText(f"${cash_register.monto_egresos:,.2f}")
            
            # Calcular monto esperado
            monto_esperado = cash_register.monto_inicial + cash_register.monto_ventas - cash_register.monto_egresos
            if hasattr(self, 'lblMontoEsperado'):
                self.lblMontoEsperado.setText(f"${monto_esperado:,.2f}")
        else:
            # Mostrar caja cerrada
            if hasattr(self, 'lblEstadoCaja'):
                self.lblEstadoCaja.setText("CAJA CERRADA")
                self.lblEstadoCaja.setStyleSheet("color: red; font-weight: bold;")
            
            # Limpiar valores
            for label in ['lblMontoInicial', 'lblVentasAcumuladas', 'lblEgresosAcumulados', 'lblMontoEsperado']:
                if hasattr(self, label):
                    getattr(self, label).setText("$0.00")
    
    def update_cash_register_buttons(self):
        """Actualizar estado de botones de caja"""
        is_open = self.financial_model.is_cash_register_open
        
        if hasattr(self, 'btnAbrirCaja'):
            self.btnAbrirCaja.setEnabled(not is_open)
        
        if hasattr(self, 'btnCerrarCaja'):
            self.btnCerrarCaja.setEnabled(is_open)
    
    def open_cash_register(self):
        """Abrir caja registradora"""
        try:
            initial_amount, ok = QInputDialog.getDouble(
                self, "Abrir Caja",
                "Monto inicial en caja:",
                0.0, 0.0, 999999.99, 2
            )
            
            if ok:
                if self.financial_model.open_cash_register(
                    initial_amount, 
                    self.current_user['id'], 
                    self.current_user['username']
                ):
                    QMessageBox.information(self, "Éxito", "Caja abierta exitosamente")
                    self.cash_register_opened.emit({'monto_inicial': initial_amount})
                else:
                    error_msg = self.financial_model.last_error or "Error desconocido"
                    QMessageBox.critical(self, "Error", f"Error abriendo caja: {error_msg}")
        
        except Exception as e:
            logger.error(f"Error abriendo caja: {e}")
            QMessageBox.critical(self, "Error", f"Error abriendo caja: {e}")
    
    def close_cash_register(self):
        """Cerrar caja registradora"""
        try:
            cash_register = self.financial_model.current_cash_register
            if not cash_register:
                return
            
            monto_esperado = cash_register.monto_inicial + cash_register.monto_ventas - cash_register.monto_egresos
            
            final_amount, ok = QInputDialog.getDouble(
                self, "Cerrar Caja",
                f"Monto esperado: ${monto_esperado:,.2f}\\nMonto real en caja:",
                monto_esperado, 0.0, 999999.99, 2
            )
            
            if ok:
                if self.financial_model.close_cash_register(final_amount):
                    diferencia = final_amount - monto_esperado
                    if abs(diferencia) > 0.01:
                        QMessageBox.warning(
                            self, "Diferencia Detectada",
                            f"Diferencia en caja: ${diferencia:,.2f}"
                        )
                    
                    QMessageBox.information(self, "Éxito", "Caja cerrada exitosamente")
                    self.cash_register_closed.emit({'monto_final': final_amount})
                else:
                    error_msg = self.financial_model.last_error or "Error desconocido"
                    QMessageBox.critical(self, "Error", f"Error cerrando caja: {error_msg}")
        
        except Exception as e:
            logger.error(f"Error cerrando caja: {e}")
            QMessageBox.critical(self, "Error", f"Error cerrando caja: {e}")
    
    def create_transaction(self):
        """Crear nueva transacción"""
        from ui.dialogs.transaction_dialog import TransactionDialog
        
        try:
            dialog = TransactionDialog(
                current_user=self.current_user,
                parent=self
            )
            
            if dialog.exec_() == QDialog.Accepted:
                transaction_data = dialog.get_transaction_data()
                
                if self.financial_model.record_transaction(transaction_data):
                    QMessageBox.information(self, "Éxito", "Transacción registrada exitosamente")
                    self.transaction_recorded.emit(transaction_data)
                else:
                    errors = self.financial_model.validation_errors
                    error_msg = "\\n".join(errors) if errors else "Error desconocido"
                    QMessageBox.critical(self, "Error", f"Error registrando transacción:\\n{error_msg}")
        
        except Exception as e:
            logger.error(f"Error creando transacción: {e}")
            QMessageBox.critical(self, "Error", f"Error creando transacción: {e}")
    
    def quick_income(self):
        """Ingreso rápido"""
        self._quick_transaction("INGRESO")
    
    def quick_expense(self):
        """Egreso rápido"""
        self._quick_transaction("EGRESO")
    
    def _quick_transaction(self, tipo):
        """Crear transacción rápida"""
        try:
            # Obtener monto
            monto, ok = QInputDialog.getDouble(
                self, f"{tipo.title()} Rápido",
                "Monto:",
                0.0, 0.01, 999999.99, 2
            )
            
            if not ok:
                return
            
            # Obtener concepto
            concepto, ok = QInputDialog.getText(
                self, f"{tipo.title()} Rápido",
                "Concepto:",
                text=f"{tipo.title()} rápido"
            )
            
            if ok and concepto.strip():
                transaction_data = {
                    'tipo': tipo,
                    'concepto': concepto.strip(),
                    'monto': monto,
                    'metodo_pago': 'EFECTIVO',
                    'usuario_id': self.current_user['id'],
                    'usuario_nombre': self.current_user['username'],
                    'fecha_transaccion': datetime.now()
                }
                
                if self.financial_model.record_transaction(transaction_data):
                    QMessageBox.information(self, "Éxito", f"{tipo.title()} registrado exitosamente")
                    self.transaction_recorded.emit(transaction_data)
                else:
                    errors = self.financial_model.validation_errors
                    error_msg = "\\n".join(errors) if errors else "Error desconocido"
                    QMessageBox.critical(self, "Error", f"Error registrando {tipo.lower()}:\\n{error_msg}")
        
        except Exception as e:
            logger.error(f"Error en {tipo.lower()} rápido: {e}")
            QMessageBox.critical(self, "Error", f"Error en {tipo.lower()} rápido: {e}")
    
    def apply_filters(self):
        """Aplicar filtros de búsqueda"""
        try:
            filters = {}
            
            # Filtro por tipo
            if hasattr(self, 'cmbTipoTransaccion'):
                tipo = self.cmbTipoTransaccion.currentText()
                if tipo and tipo != "Todas":
                    filters['tipo'] = tipo
            
            # Filtro por fechas
            if hasattr(self, 'dateEditDesde') and hasattr(self, 'dateEditHasta'):
                fecha_desde = self.dateEditDesde.date().toPyDate()
                fecha_hasta = self.dateEditHasta.date().toPyDate()
                filters['fecha_desde'] = fecha_desde
                filters['fecha_hasta'] = fecha_hasta
            
            self.current_filters = filters
            self.refresh_data()
        
        except Exception as e:
            logger.error(f"Error aplicando filtros: {e}")
    
    def generate_daily_report(self):
        """Generar reporte diario"""
        try:
            today = date.today()
            balance_data = self.financial_model.calculate_balance_by_period(today, today)
            
            report_text = f"""
REPORTE FINANCIERO DIARIO
Fecha: {today.strftime('%d/%m/%Y')}

RESUMEN:
- Ingresos: ${balance_data['ingresos']:,.2f}
- Egresos: ${balance_data['egresos']:,.2f}
- Balance: ${balance_data['balance']:,.2f}
- Transacciones: {balance_data['transacciones']}

ESTADO DE CAJA:
"""
            if self.financial_model.current_cash_register:
                cash_register = self.financial_model.current_cash_register
                report_text += f"""- Estado: {cash_register.estado}
- Monto inicial: ${cash_register.monto_inicial:,.2f}
- Ventas: ${cash_register.monto_ventas:,.2f}
- Egresos: ${cash_register.monto_egresos:,.2f}
"""
            else:
                report_text += "- Estado: CERRADA"
            
            # Mostrar reporte en diálogo
            dialog = QDialog(self)
            dialog.setWindowTitle("Reporte Diario")
            dialog.resize(400, 300)
            
            layout = QVBoxLayout(dialog)
            text_edit = QTextEdit()
            text_edit.setPlainText(report_text)
            text_edit.setReadOnly(True)
            layout.addWidget(text_edit)
            
            buttons = QDialogButtonBox(QDialogButtonBox.Ok)
            buttons.accepted.connect(dialog.accept)
            layout.addWidget(buttons)
            
            dialog.exec_()
        
        except Exception as e:
            logger.error(f"Error generando reporte diario: {e}")
            QMessageBox.critical(self, "Error", f"Error generando reporte: {e}")
    
    def generate_monthly_report(self):
        """Generar reporte mensual"""
        # Similar al reporte diario pero para el mes actual
        pass
    
    def on_transaction_created(self, transaction_data):
        """Manejar creación de transacción"""
        self.update_financial_metrics()
    
    def on_cash_register_opened(self, cash_register_data):
        """Manejar apertura de caja"""
        self.update_cash_register_display()
        self.update_cash_register_buttons()
    
    def on_cash_register_closed(self, cash_register_data):
        """Manejar cierre de caja"""
        self.update_cash_register_display()
        self.update_cash_register_buttons()
    
    def on_balance_updated(self, new_balance):
        """Manejar actualización de balance"""
        self.balance_updated.emit(new_balance)
    
    def show_error(self, error_message):
        """Mostrar mensaje de error"""
        QMessageBox.critical(self, "Error", error_message)