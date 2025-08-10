"""
Diálogo de Procesamiento de Pagos - AlmacénPro v2.0
Gestión completa de pagos con múltiples métodos y validaciones
"""

import logging
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class PaymentDialog(QDialog):
    """Diálogo principal para procesamiento de pagos"""
    
    payment_processed = pyqtSignal(dict)  # Señal emitida al procesar pago
    
    def __init__(self, total_amount: float, customer_data: Optional[Dict] = None, 
                 existing_payments: Optional[List[Dict]] = None, parent=None):
        super().__init__(parent)
        
        self.total_amount = float(total_amount)
        self.customer_data = customer_data or {}
        self.existing_payments = existing_payments or []
        
        # Calcular montos
        self.paid_amount = sum(payment.get('importe', 0) for payment in self.existing_payments)
        self.remaining_amount = self.total_amount - self.paid_amount
        
        # Lista de métodos de pago disponibles
        self.payment_methods = [
            ('EFECTIVO', '💵 Efectivo'),
            ('TARJETA_DEBITO', '💳 Tarjeta de Débito'),
            ('TARJETA_CREDITO', '💳 Tarjeta de Crédito'),
            ('TRANSFERENCIA', '🏦 Transferencia Bancaria'),
            ('CHEQUE', '📝 Cheque'),
            ('CUENTA_CORRIENTE', '📊 Cuenta Corriente'),
            ('MERCADO_PAGO', '💰 Mercado Pago'),
            ('BILLETERA_VIRTUAL', '📱 Billetera Virtual')
        ]
        
        # Lista de pagos actuales
        self.current_payments = []
        
        self.setWindowTitle("Procesamiento de Pagos")
        self.setModal(True)
        self.resize(700, 600)
        
        self.init_ui()
        self.update_amounts_display()
        
        # Si hay un monto restante, pre-llenar efectivo
        if self.remaining_amount > 0:
            self.add_cash_payment()
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        layout = QVBoxLayout(self)
        
        # Header con información de la venta
        header_layout = self.create_header()
        layout.addLayout(header_layout)
        
        # Información del cliente (si existe)
        if self.customer_data:
            customer_info = self.create_customer_info()
            layout.addWidget(customer_info)
        
        # Panel de montos
        amounts_panel = self.create_amounts_panel()
        layout.addWidget(amounts_panel)
        
        # Lista de métodos de pago
        payments_panel = self.create_payments_panel()
        layout.addWidget(payments_panel)
        
        # Botones de acción
        buttons_layout = self.create_buttons()
        layout.addLayout(buttons_layout)
    
    def create_header(self) -> QHBoxLayout:
        """Crear header del diálogo"""
        layout = QHBoxLayout()
        
        # Icono y título
        icon_label = QLabel("💳")
        icon_label.setStyleSheet("font-size: 24px;")
        layout.addWidget(icon_label)
        
        title_label = QLabel("Procesamiento de Pagos")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Información de fecha/hora
        datetime_label = QLabel(datetime.now().strftime("%d/%m/%Y %H:%M"))
        datetime_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        layout.addWidget(datetime_label)
        
        return layout
    
    def create_customer_info(self) -> QGroupBox:
        """Crear panel de información del cliente"""
        group = QGroupBox("🧑‍💼 Información del Cliente")
        layout = QGridLayout(group)
        
        customer_name = f"{self.customer_data.get('nombre', '')} {self.customer_data.get('apellido', '')}"
        layout.addWidget(QLabel("Cliente:"), 0, 0)
        layout.addWidget(QLabel(customer_name), 0, 1)
        
        if self.customer_data.get('email'):
            layout.addWidget(QLabel("Email:"), 1, 0)
            layout.addWidget(QLabel(self.customer_data['email']), 1, 1)
        
        # Información de cuenta corriente
        if self.customer_data.get('limite_credito', 0) > 0:
            limite = float(self.customer_data['limite_credito'])
            saldo = float(self.customer_data.get('saldo_cuenta_corriente', 0))
            disponible = limite - saldo
            
            layout.addWidget(QLabel("Límite de Crédito:"), 0, 2)
            layout.addWidget(QLabel(f"${limite:.2f}"), 0, 3)
            
            layout.addWidget(QLabel("Crédito Disponible:"), 1, 2)
            disponible_label = QLabel(f"${disponible:.2f}")
            if disponible < self.remaining_amount:
                disponible_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            else:
                disponible_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            layout.addWidget(disponible_label, 1, 3)
        
        return group
    
    def create_amounts_panel(self) -> QGroupBox:
        """Crear panel de montos"""
        group = QGroupBox("💰 Resumen de Montos")
        layout = QGridLayout(group)
        
        # Total de la venta
        layout.addWidget(QLabel("Total de la Venta:"), 0, 0)
        self.total_label = QLabel(f"${self.total_amount:.2f}")
        self.total_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(self.total_label, 0, 1)
        
        # Ya pagado
        layout.addWidget(QLabel("Ya Pagado:"), 1, 0)
        self.paid_label = QLabel(f"${self.paid_amount:.2f}")
        self.paid_label.setStyleSheet("font-size: 14px; color: #27ae60;")
        layout.addWidget(self.paid_label, 1, 1)
        
        # Restante por pagar
        layout.addWidget(QLabel("Restante:"), 2, 0)
        self.remaining_label = QLabel(f"${self.remaining_amount:.2f}")
        self.remaining_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c;")
        layout.addWidget(self.remaining_label, 2, 1)
        
        # Cambio (si aplica)
        layout.addWidget(QLabel("Cambio:"), 3, 0)
        self.change_label = QLabel("$0.00")
        self.change_label.setStyleSheet("font-size: 14px; color: #f39c12;")
        layout.addWidget(self.change_label, 3, 1)
        
        return group
    
    def create_payments_panel(self) -> QWidget:
        """Crear panel de métodos de pago"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Header del panel
        header_layout = QHBoxLayout()
        
        payments_label = QLabel("💳 Métodos de Pago")
        payments_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(payments_label)
        
        header_layout.addStretch()
        
        # Botones para agregar métodos de pago
        add_payment_btn = QPushButton("➕ Agregar Pago")
        add_payment_btn.clicked.connect(self.add_payment_method)
        header_layout.addWidget(add_payment_btn)
        
        layout.addLayout(header_layout)
        
        # Área de scroll para los pagos
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(300)
        
        self.payments_container = QWidget()
        self.payments_layout = QVBoxLayout(self.payments_container)
        self.payments_layout.setSpacing(5)
        
        scroll_area.setWidget(self.payments_container)
        layout.addWidget(scroll_area)
        
        return widget
    
    def create_buttons(self) -> QHBoxLayout:
        """Crear botones de acción"""
        layout = QHBoxLayout()
        
        # Botones de acciones rápidas
        quick_actions_label = QLabel("⚡ Acciones Rápidas:")
        layout.addWidget(quick_actions_label)
        
        exact_change_btn = QPushButton("💵 Efectivo Exacto")
        exact_change_btn.clicked.connect(self.set_exact_cash)
        layout.addWidget(exact_change_btn)
        
        card_payment_btn = QPushButton("💳 Pago con Tarjeta")
        card_payment_btn.clicked.connect(self.set_card_payment)
        layout.addWidget(card_payment_btn)
        
        layout.addStretch()
        
        # Botones principales
        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        self.process_btn = QPushButton("✅ Procesar Pago")
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.process_btn.clicked.connect(self.process_payment)
        layout.addWidget(self.process_btn)
        
        return layout
    
    def add_payment_method(self):
        """Agregar un método de pago"""
        if self.remaining_amount <= 0:
            QMessageBox.information(self, "Info", "El pago ya está completo")
            return
        
        # Diálogo para seleccionar método de pago
        method, ok = QInputDialog.getItem(
            self, "Seleccionar Método", "Método de pago:",
            [display for _, display in self.payment_methods],
            0, False
        )
        
        if ok and method:
            # Encontrar el código del método
            method_code = None
            for code, display in self.payment_methods:
                if display == method:
                    method_code = code
                    break
            
            if method_code:
                self.add_payment_widget(method_code)
    
    def add_cash_payment(self):
        """Agregar pago en efectivo automáticamente"""
        self.add_payment_widget('EFECTIVO')
    
    def set_exact_cash(self):
        """Configurar pago exacto en efectivo"""
        self.clear_payments()
        self.add_payment_widget('EFECTIVO', self.remaining_amount)
    
    def set_card_payment(self):
        """Configurar pago con tarjeta"""
        self.clear_payments()
        self.add_payment_widget('TARJETA_DEBITO', self.remaining_amount)
    
    def add_payment_widget(self, method_code: str, amount: Optional[float] = None):
        """Agregar widget de método de pago"""
        payment_widget = PaymentMethodWidget(
            method_code, 
            self.payment_methods,
            amount or min(self.remaining_amount, 0),
            self.customer_data
        )
        payment_widget.amount_changed.connect(self.update_amounts_display)
        payment_widget.remove_requested.connect(self.remove_payment_widget)
        
        self.current_payments.append(payment_widget)
        self.payments_layout.addWidget(payment_widget)
        
        self.update_amounts_display()
    
    def remove_payment_widget(self, widget):
        """Remover widget de método de pago"""
        if widget in self.current_payments:
            self.current_payments.remove(widget)
            self.payments_layout.removeWidget(widget)
            widget.deleteLater()
            self.update_amounts_display()
    
    def clear_payments(self):
        """Limpiar todos los métodos de pago"""
        for widget in self.current_payments[:]:
            self.remove_payment_widget(widget)
    
    def update_amounts_display(self):
        """Actualizar visualización de montos"""
        # Calcular nuevo total pagado
        current_payment_total = sum(widget.get_amount() for widget in self.current_payments)
        new_total_paid = self.paid_amount + current_payment_total
        
        # Calcular restante y cambio
        remaining = self.total_amount - new_total_paid
        change = max(0, -remaining)
        
        # Actualizar labels
        self.paid_label.setText(f"${new_total_paid:.2f}")
        
        if remaining > 0:
            self.remaining_label.setText(f"${remaining:.2f}")
            self.remaining_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c;")
        else:
            self.remaining_label.setText("$0.00")
            self.remaining_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60;")
        
        self.change_label.setText(f"${change:.2f}")
        if change > 0:
            self.change_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f39c12;")
        else:
            self.change_label.setStyleSheet("font-size: 14px; color: #f39c12;")
        
        # Habilitar/deshabilitar botón de procesar
        payments_valid = all(widget.is_valid() for widget in self.current_payments)
        payment_complete = remaining <= 0
        
        self.process_btn.setEnabled(payments_valid and payment_complete and len(self.current_payments) > 0)
    
    def process_payment(self):
        """Procesar el pago"""
        try:
            # Validar todos los pagos
            for widget in self.current_payments:
                if not widget.is_valid():
                    QMessageBox.warning(self, "Error", "Hay errores en los métodos de pago")
                    return
            
            # Recopilar datos de pago
            payment_data = []
            for widget in self.current_payments:
                payment_info = widget.get_payment_data()
                if payment_info['importe'] > 0:  # Solo pagos con monto
                    payment_data.append(payment_info)
            
            if not payment_data:
                QMessageBox.warning(self, "Error", "No hay métodos de pago válidos")
                return
            
            # Calcular totales finales
            total_payment = sum(p['importe'] for p in payment_data)
            change = max(0, total_payment - self.remaining_amount)
            
            # Confirmar pago si hay cambio
            if change > 0:
                reply = QMessageBox.question(
                    self, "Confirmar Pago",
                    f"El pago es de ${total_payment:.2f} para un total de ${self.remaining_amount:.2f}\n"
                    f"Cambio a devolver: ${change:.2f}\n\n¿Confirmar transacción?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply != QMessageBox.Yes:
                    return
            
            # Emitir señal con datos del pago
            payment_result = {
                'payments': payment_data,
                'total_paid': total_payment,
                'change': change,
                'payment_complete': True
            }
            
            self.payment_processed.emit(payment_result)
            
            # Mostrar confirmación
            if change > 0:
                QMessageBox.information(
                    self, "Pago Procesado",
                    f"Pago procesado exitosamente\n\nCambio: ${change:.2f}"
                )
            else:
                QMessageBox.information(self, "Pago Procesado", "Pago procesado exitosamente")
            
            self.accept()
            
        except Exception as e:
            logger.error(f"Error procesando pago: {e}")
            QMessageBox.critical(self, "Error", f"Error procesando pago: {str(e)}")
    
    def get_payment_data(self) -> List[Dict]:
        """Obtener datos de todos los pagos"""
        return [widget.get_payment_data() for widget in self.current_payments if widget.is_valid()]


class PaymentMethodWidget(QFrame):
    """Widget para un método de pago individual"""
    
    amount_changed = pyqtSignal()
    remove_requested = pyqtSignal(object)  # self
    
    def __init__(self, method_code: str, available_methods: List[Tuple], 
                 default_amount: float = 0, customer_data: Optional[Dict] = None):
        super().__init__()
        
        self.method_code = method_code
        self.available_methods = available_methods
        self.customer_data = customer_data or {}
        
        # Encontrar nombre del método
        self.method_name = next(
            (display for code, display in available_methods if code == method_code),
            method_code
        )
        
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding: 8px;
                margin: 2px;
            }
        """)
        
        self.init_ui()
        
        # Configurar monto por defecto
        if default_amount > 0:
            self.amount_input.setValue(default_amount)
    
    def init_ui(self):
        """Inicializar interfaz del widget"""
        layout = QHBoxLayout(self)
        
        # Método de pago
        method_label = QLabel(self.method_name)
        method_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        method_label.setMinimumWidth(150)
        layout.addWidget(method_label)
        
        # Monto
        layout.addWidget(QLabel("$"))
        
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0.0, 999999.99)
        self.amount_input.setDecimals(2)
        self.amount_input.setSingleStep(0.01)
        self.amount_input.setMinimumWidth(100)
        self.amount_input.valueChanged.connect(self.on_amount_changed)
        layout.addWidget(self.amount_input)
        
        # Campos específicos según método
        self.setup_method_fields(layout)
        
        # Botón remover
        remove_btn = QPushButton("🗑")
        remove_btn.setMaximumWidth(30)
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))
        remove_btn.setStyleSheet("QPushButton { color: #e74c3c; }")
        layout.addWidget(remove_btn)
    
    def setup_method_fields(self, layout):
        """Configurar campos específicos según el método de pago"""
        self.reference_input = None
        self.auth_code_input = None
        
        if self.method_code in ['TARJETA_DEBITO', 'TARJETA_CREDITO']:
            # Código de autorización
            layout.addWidget(QLabel("Auth:"))
            self.auth_code_input = QLineEdit()
            self.auth_code_input.setPlaceholderText("Código autorización")
            self.auth_code_input.setMaximumWidth(120)
            layout.addWidget(self.auth_code_input)
            
            # Últimos 4 dígitos
            layout.addWidget(QLabel("****"))
            self.reference_input = QLineEdit()
            self.reference_input.setPlaceholderText("1234")
            self.reference_input.setMaxLength(4)
            self.reference_input.setMaximumWidth(60)
            layout.addWidget(self.reference_input)
            
        elif self.method_code == 'TRANSFERENCIA':
            # Número de referencia
            layout.addWidget(QLabel("Ref:"))
            self.reference_input = QLineEdit()
            self.reference_input.setPlaceholderText("Número de referencia")
            self.reference_input.setMaximumWidth(150)
            layout.addWidget(self.reference_input)
            
        elif self.method_code == 'CHEQUE':
            # Número de cheque
            layout.addWidget(QLabel("Nº:"))
            self.reference_input = QLineEdit()
            self.reference_input.setPlaceholderText("Número de cheque")
            self.reference_input.setMaximumWidth(120)
            layout.addWidget(self.reference_input)
            
        elif self.method_code == 'CUENTA_CORRIENTE':
            # Verificar límite de crédito
            if self.customer_data:
                limite = float(self.customer_data.get('limite_credito', 0))
                saldo = float(self.customer_data.get('saldo_cuenta_corriente', 0))
                disponible = limite - saldo
                
                credit_label = QLabel(f"Disponible: ${disponible:.2f}")
                if disponible <= 0:
                    credit_label.setStyleSheet("color: #e74c3c; font-size: 11px;")
                else:
                    credit_label.setStyleSheet("color: #27ae60; font-size: 11px;")
                layout.addWidget(credit_label)
    
    def on_amount_changed(self):
        """Manejar cambio en el monto"""
        self.amount_changed.emit()
    
    def get_amount(self) -> float:
        """Obtener monto del pago"""
        return self.amount_input.value()
    
    def is_valid(self) -> bool:
        """Verificar si el pago es válido"""
        if self.get_amount() <= 0:
            return False
        
        # Validaciones específicas por método
        if self.method_code in ['TARJETA_DEBITO', 'TARJETA_CREDITO']:
            # Requiere código de autorización
            if self.auth_code_input and not self.auth_code_input.text().strip():
                return False
        
        elif self.method_code == 'CUENTA_CORRIENTE':
            # Verificar límite de crédito
            if self.customer_data:
                limite = float(self.customer_data.get('limite_credito', 0))
                saldo = float(self.customer_data.get('saldo_cuenta_corriente', 0))
                disponible = limite - saldo
                
                if self.get_amount() > disponible:
                    return False
        
        return True
    
    def get_payment_data(self) -> Dict:
        """Obtener datos completos del pago"""
        data = {
            'metodo_pago': self.method_code,
            'importe': self.get_amount(),
            'fecha_pago': datetime.now(),
            'observaciones': f"Pago {self.method_name}"
        }
        
        # Agregar referencia según método
        if self.reference_input and self.reference_input.text().strip():
            if self.method_code in ['TARJETA_DEBITO', 'TARJETA_CREDITO']:
                auth_code = self.auth_code_input.text().strip() if self.auth_code_input else ""
                data['referencia'] = f"Auth: {auth_code} - ****{self.reference_input.text().strip()}"
            else:
                data['referencia'] = self.reference_input.text().strip()
        
        return data


class QuickPaymentDialog(QDialog):
    """Diálogo simplificado para pagos rápidos"""
    
    def __init__(self, amount: float, parent=None):
        super().__init__(parent)
        
        self.amount = amount
        self.payment_data = None
        
        self.setWindowTitle("Pago Rápido")
        self.setModal(True)
        self.resize(400, 250)
        
        self.init_ui()
    
    def init_ui(self):
        """Inicializar interfaz simplificada"""
        layout = QVBoxLayout(self)
        
        # Monto
        amount_label = QLabel(f"Total a pagar: ${self.amount:.2f}")
        amount_label.setStyleSheet("font-size: 18px; font-weight: bold; text-align: center;")
        amount_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(amount_label)
        
        layout.addWidget(QLabel())  # Separador
        
        # Botones de método rápido
        cash_btn = QPushButton("💵 Efectivo")
        cash_btn.setStyleSheet("padding: 15px; font-size: 16px;")
        cash_btn.clicked.connect(self.pay_cash)
        layout.addWidget(cash_btn)
        
        card_btn = QPushButton("💳 Tarjeta")
        card_btn.setStyleSheet("padding: 15px; font-size: 16px;")
        card_btn.clicked.connect(self.pay_card)
        layout.addWidget(card_btn)
        
        # Botón para pago completo
        full_btn = QPushButton("⚙️ Pago Completo")
        full_btn.clicked.connect(self.open_full_dialog)
        layout.addWidget(full_btn)
        
        # Cancelar
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
    
    def pay_cash(self):
        """Pago rápido en efectivo"""
        self.payment_data = [{
            'metodo_pago': 'EFECTIVO',
            'importe': self.amount,
            'fecha_pago': datetime.now(),
            'referencia': 'Pago rápido efectivo',
            'observaciones': 'Pago en efectivo'
        }]
        self.accept()
    
    def pay_card(self):
        """Pago rápido con tarjeta"""
        self.payment_data = [{
            'metodo_pago': 'TARJETA_DEBITO',
            'importe': self.amount,
            'fecha_pago': datetime.now(),
            'referencia': 'Pago rápido tarjeta',
            'observaciones': 'Pago con tarjeta'
        }]
        self.accept()
    
    def open_full_dialog(self):
        """Abrir diálogo completo"""
        self.done(2)  # Código especial para abrir diálogo completo
    
    def get_payment_data(self) -> Optional[List[Dict]]:
        """Obtener datos del pago"""
        return self.payment_data