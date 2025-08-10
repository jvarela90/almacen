"""
Widget de Gestión de Clientes Empresarial - AlmacénPro v2.0
Interface completa de CRM con análisis avanzado
"""

import logging
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from datetime import datetime, date
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class CustomersWidget(QWidget):
    """Widget principal para gestión empresarial de clientes"""
    
    def __init__(self, managers: Dict, parent=None):
        super().__init__(parent)
        
        self.managers = managers
        self.customer_manager = managers.get('customer_manager')
        self.current_customer = None
        self.customers_data = []
        
        self.init_ui()
        self.setup_connections()
        self.load_customers()
        self.load_dashboard()
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        layout = QVBoxLayout(self)
        
        # Header con título y acciones rápidas
        header_layout = self.create_header()
        layout.addLayout(header_layout)
        
        # Contenido principal con tabs
        self.tab_widget = QTabWidget()
        
        # Tab 1: Lista de clientes
        customers_tab = self.create_customers_tab()
        self.tab_widget.addTab(customers_tab, "📋 Lista de Clientes")
        
        # Tab 2: Dashboard CRM
        dashboard_tab = self.create_dashboard_tab()
        self.tab_widget.addTab(dashboard_tab, "📊 Dashboard CRM")
        
        # Tab 3: Análisis y Reportes
        analytics_tab = self.create_analytics_tab()
        self.tab_widget.addTab(analytics_tab, "📈 Análisis")
        
        # Tab 4: Cuenta Corriente
        accounts_tab = self.create_accounts_tab()
        self.tab_widget.addTab(accounts_tab, "💰 Cuenta Corriente")
        
        layout.addWidget(self.tab_widget)
        
        # Status bar
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)
    
    def create_header(self) -> QHBoxLayout:
        """Crear header con título y botones de acción"""
        layout = QHBoxLayout()
        
        # Título
        title_label = QLabel("🏢 Gestión de Clientes CRM")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50; margin: 10px;")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Búsqueda rápida
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar clientes...")
        self.search_input.setMaximumWidth(300)
        self.search_input.textChanged.connect(self.search_customers)
        layout.addWidget(self.search_input)
        
        # Botones de acción
        self.new_customer_btn = QPushButton("➕ Nuevo Cliente")
        self.new_customer_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover { background-color: #229954; }
        """)
        layout.addWidget(self.new_customer_btn)
        
        self.refresh_btn = QPushButton("🔄 Actualizar")
        self.refresh_btn.clicked.connect(self.refresh_data)
        layout.addWidget(self.refresh_btn)
        
        return layout
    
    def create_customers_tab(self) -> QWidget:
        """Crear tab de lista de clientes"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Toolbar con filtros
        toolbar_layout = QHBoxLayout()
        
        # Filtro por categoría
        toolbar_layout.addWidget(QLabel("Categoría:"))
        self.category_combo = QComboBox()
        self.category_combo.addItem("Todas las categorías", "")\n        if self.customer_manager:
            for category in self.customer_manager.CUSTOMER_CATEGORIES:
                self.category_combo.addItem(category, category)
        self.category_combo.currentTextChanged.connect(self.filter_customers)
        toolbar_layout.addWidget(self.category_combo)
        
        # Filtro por actividad
        toolbar_layout.addWidget(QLabel("Estado:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Todos", "Activos", "Con Deuda", "Inactivos"])
        self.status_combo.currentTextChanged.connect(self.filter_customers)
        toolbar_layout.addWidget(self.status_combo)
        
        toolbar_layout.addStretch()
        
        # Botón de exportar
        export_btn = QPushButton("📤 Exportar")
        toolbar_layout.addWidget(export_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Tabla de clientes
        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(8)
        self.customers_table.setHorizontalHeaderLabels([
            "ID", "Nombre", "Email", "Teléfono", "Categoría", 
            "Límite Crédito", "Saldo", "Última Compra"
        ])
        
        # Configurar tabla
        header = self.customers_table.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(8):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        self.customers_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.customers_table.setAlternatingRowColors(True)
        self.customers_table.doubleClicked.connect(self.open_customer_details)
        self.customers_table.itemSelectionChanged.connect(self.on_customer_selected)
        
        layout.addWidget(self.customers_table)
        
        # Botones de acción para cliente seleccionado
        actions_layout = QHBoxLayout()
        
        self.view_details_btn = QPushButton("👁 Ver Detalles")
        self.view_details_btn.setEnabled(False)
        self.view_details_btn.clicked.connect(self.open_customer_details)
        actions_layout.addWidget(self.view_details_btn)
        
        self.edit_customer_btn = QPushButton("✏ Editar")
        self.edit_customer_btn.setEnabled(False)
        actions_layout.addWidget(self.edit_customer_btn)
        
        self.add_note_btn = QPushButton("📝 Añadir Nota")
        self.add_note_btn.setEnabled(False)
        self.add_note_btn.clicked.connect(self.add_customer_note)
        actions_layout.addWidget(self.add_note_btn)
        
        self.process_payment_btn = QPushButton("💳 Procesar Pago")
        self.process_payment_btn.setEnabled(False)
        self.process_payment_btn.clicked.connect(self.process_payment)
        actions_layout.addWidget(self.process_payment_btn)
        
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)
        
        return tab
    
    def create_dashboard_tab(self) -> QWidget:
        """Crear tab de dashboard CRM"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # KPIs principales
        kpis_layout = QHBoxLayout()
        
        # Crear cards de KPIs
        self.total_customers_card = self.create_kpi_card("Total Clientes", "0", "#3498db")
        self.active_customers_card = self.create_kpi_card("Activos", "0", "#27ae60")
        self.debt_customers_card = self.create_kpi_card("Con Deuda", "0", "#e74c3c")
        self.total_debt_card = self.create_kpi_card("Deuda Total", "$0", "#f39c12")
        
        kpis_layout.addWidget(self.total_customers_card)
        kpis_layout.addWidget(self.active_customers_card)
        kpis_layout.addWidget(self.debt_customers_card)
        kpis_layout.addWidget(self.total_debt_card)
        
        layout.addLayout(kpis_layout)
        
        # Contenido del dashboard
        content_layout = QHBoxLayout()
        
        # Columna izquierda: Distribución por categorías
        left_column = QVBoxLayout()
        
        categories_group = QGroupBox("📊 Distribución por Categorías")
        categories_layout = QVBoxLayout(categories_group)
        
        self.categories_list = QListWidget()
        categories_layout.addWidget(self.categories_list)
        
        left_column.addWidget(categories_group)
        
        # Top deudores
        debtors_group = QGroupBox("💰 Top Deudores")
        debtors_layout = QVBoxLayout(debtors_group)
        
        self.debtors_list = QListWidget()
        debtors_layout.addWidget(self.debtors_list)
        
        left_column.addWidget(debtors_group)
        
        content_layout.addLayout(left_column)
        
        # Columna derecha: Clientes recientes y actividad
        right_column = QVBoxLayout()
        
        recent_group = QGroupBox("🆕 Clientes Recientes")
        recent_layout = QVBoxLayout(recent_group)
        
        self.recent_customers_list = QListWidget()
        recent_layout.addWidget(self.recent_customers_list)
        
        right_column.addWidget(recent_group)
        
        # Acciones rápidas
        actions_group = QGroupBox("⚡ Acciones Rápidas")
        actions_layout = QVBoxLayout(actions_group)
        
        categorize_btn = QPushButton("🏷 Categorizar Clientes Automáticamente")
        categorize_btn.clicked.connect(self.auto_categorize_customers)
        actions_layout.addWidget(categorize_btn)
        
        inactive_btn = QPushButton("😴 Ver Clientes Inactivos")
        inactive_btn.clicked.connect(self.show_inactive_customers)
        actions_layout.addWidget(inactive_btn)
        
        export_report_btn = QPushButton("📋 Generar Reporte CRM")
        actions_layout.addWidget(export_report_btn)
        
        right_column.addWidget(actions_group)
        
        content_layout.addLayout(right_column)
        
        layout.addLayout(content_layout)
        
        return tab
    
    def create_analytics_tab(self) -> QWidget:
        """Crear tab de análisis y reportes"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Controles de análisis
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Período de análisis:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Último mes", "Últimos 3 meses", "Últimos 6 meses", "Último año"])
        controls_layout.addWidget(self.period_combo)
        
        analyze_btn = QPushButton("🔍 Analizar")
        analyze_btn.clicked.connect(self.analyze_customers)
        controls_layout.addWidget(analyze_btn)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Tabla de top clientes
        top_customers_group = QGroupBox("🌟 Top Clientes por Valor")
        top_layout = QVBoxLayout(top_customers_group)
        
        self.top_customers_table = QTableWidget()
        self.top_customers_table.setColumnCount(7)
        self.top_customers_table.setHorizontalHeaderLabels([
            "Cliente", "Email", "Compras", "Monto Total", 
            "Ticket Promedio", "Última Compra", "Clasificación"
        ])
        
        header = self.top_customers_table.horizontalHeader()
        header.setStretchLastSection(True)
        
        top_layout.addWidget(self.top_customers_table)
        
        layout.addWidget(top_customers_group)
        
        return tab
    
    def create_accounts_tab(self) -> QWidget:
        """Crear tab de gestión de cuenta corriente"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Filtros y controles
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Mostrar:"))
        self.accounts_filter = QComboBox()
        self.accounts_filter.addItems(["Todos", "Solo con deuda", "Solo con crédito"])
        self.accounts_filter.currentTextChanged.connect(self.filter_accounts)
        controls_layout.addWidget(self.accounts_filter)
        
        controls_layout.addStretch()
        
        process_payments_btn = QPushButton("💳 Procesar Pagos Masivos")
        controls_layout.addWidget(process_payments_btn)
        
        layout.addLayout(controls_layout)
        
        # Tabla de cuentas corrientes
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(6)
        self.accounts_table.setHorizontalHeaderLabels([
            "Cliente", "Límite Crédito", "Saldo Actual", 
            "Crédito Disponible", "Días de Deuda", "Estado"
        ])
        
        header = self.accounts_table.horizontalHeader()
        header.setStretchLastSection(True)
        
        self.accounts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.accounts_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.accounts_table)
        
        return tab
    
    def create_kpi_card(self, title: str, value: str, color: str) -> QFrame:
        """Crear card de KPI"""
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {color};
                border-radius: 8px;
                background-color: white;
                margin: 5px;
            }}
        """)
        card.setFixedHeight(100)
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; color: #7f8c8d;")
        title_label.setAlignment(Qt.AlignCenter)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setObjectName(f"{title.lower().replace(' ', '_')}_value")
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        return card
    
    def setup_connections(self):
        """Configurar conexiones de señales"""
        self.new_customer_btn.clicked.connect(self.create_new_customer)
    
    def load_customers(self):
        """Cargar lista de clientes"""
        if not self.customer_manager:
            return
        
        try:
            self.customers_data = self.customer_manager.get_all_customers()
            self.populate_customers_table(self.customers_data)
            self.update_status(f"Clientes cargados: {len(self.customers_data)}")
            
        except Exception as e:
            logger.error(f"Error cargando clientes: {e}")
            self.show_error("Error", f"No se pudieron cargar los clientes: {str(e)}")
    
    def populate_customers_table(self, customers: List[Dict]):
        """Poblar tabla de clientes"""
        self.customers_table.setRowCount(len(customers))
        
        for row, customer in enumerate(customers):
            self.customers_table.setItem(row, 0, QTableWidgetItem(str(customer.get('id', ''))))
            self.customers_table.setItem(row, 1, QTableWidgetItem(
                f"{customer.get('nombre', '')} {customer.get('apellido', '')}"
            ))
            self.customers_table.setItem(row, 2, QTableWidgetItem(customer.get('email', '')))
            self.customers_table.setItem(row, 3, QTableWidgetItem(customer.get('telefono', '')))
            self.customers_table.setItem(row, 4, QTableWidgetItem(customer.get('categoria_cliente', '')))
            
            # Formatear montos
            limite = float(customer.get('limite_credito', 0))
            saldo = float(customer.get('saldo_cuenta_corriente', 0))
            
            self.customers_table.setItem(row, 5, QTableWidgetItem(f"${limite:.2f}"))
            
            # Colorear saldo según deuda
            saldo_item = QTableWidgetItem(f"${saldo:.2f}")
            if saldo > 0:
                saldo_item.setBackground(QColor("#ffebee"))  # Rojo claro para deuda
            self.customers_table.setItem(row, 6, saldo_item)
            
            # Última compra (placeholder)
            self.customers_table.setItem(row, 7, QTableWidgetItem("N/A"))
    
    def load_dashboard(self):
        """Cargar datos del dashboard"""
        if not self.customer_manager:
            return
        
        try:
            dashboard_data = self.customer_manager.get_customers_dashboard_data()
            
            # Actualizar KPIs
            general = dashboard_data.get('general', {})
            self.update_kpi_card('total_customers', str(general.get('total_clientes', 0)))
            self.update_kpi_card('activos', str(general.get('clientes_activos', 0)))
            self.update_kpi_card('con_deuda', str(general.get('clientes_con_deuda', 0)))
            self.update_kpi_card('deuda_total', f"${general.get('deuda_total', 0):.2f}")
            
            # Cargar distribución por categorías
            categories = dashboard_data.get('categories', [])
            self.categories_list.clear()
            for category in categories:
                self.categories_list.addItem(
                    f"{category['categoria_cliente']}: {category['count']} clientes"
                )
            
            # Cargar clientes recientes
            recent = dashboard_data.get('recent', [])
            self.recent_customers_list.clear()
            for customer in recent:
                self.recent_customers_list.addItem(
                    f"{customer['nombre']} {customer['apellido']} ({customer['categoria_cliente']})"
                )
            
            # Cargar top deudores
            debtors = dashboard_data.get('top_debtors', [])
            self.debtors_list.clear()
            for debtor in debtors:
                self.debtors_list.addItem(
                    f"{debtor['nombre']} {debtor['apellido']}: ${debtor['saldo_cuenta_corriente']:.2f}"
                )
            
        except Exception as e:
            logger.error(f"Error cargando dashboard: {e}")
    
    def update_kpi_card(self, card_type: str, value: str):
        """Actualizar valor de card KPI"""
        card = self.findChild(QLabel, f"{card_type}_value")
        if card:
            card.setText(value)
    
    def search_customers(self):
        """Buscar clientes"""
        search_term = self.search_input.text().strip()
        
        if not self.customer_manager:
            return
        
        try:
            if search_term:
                filtered_customers = self.customer_manager.search_customers(search_term)
            else:
                filtered_customers = self.customers_data
                
            self.populate_customers_table(filtered_customers)
            
        except Exception as e:
            logger.error(f"Error buscando clientes: {e}")
    
    def filter_customers(self):
        """Filtrar clientes por categoría y estado"""
        # Implementar filtros
        self.load_customers()
    
    def on_customer_selected(self):
        """Manejar selección de cliente"""
        selected_rows = self.customers_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        
        self.view_details_btn.setEnabled(has_selection)
        self.edit_customer_btn.setEnabled(has_selection)
        self.add_note_btn.setEnabled(has_selection)
        
        if has_selection:
            row = selected_rows[0].row()
            customer_id = int(self.customers_table.item(row, 0).text())
            customer = next((c for c in self.customers_data if c['id'] == customer_id), None)
            
            if customer:
                # Habilitar botón de pago solo si tiene deuda
                has_debt = float(customer.get('saldo_cuenta_corriente', 0)) > 0
                self.process_payment_btn.setEnabled(has_debt)
                
                self.current_customer = customer
    
    def open_customer_details(self):
        """Abrir detalles del cliente"""
        if not self.current_customer or not self.customer_manager:
            return
        
        customer_id = self.current_customer['id']
        
        try:
            # Obtener estadísticas completas
            stats = self.customer_manager.get_customer_statistics(customer_id)
            
            # Crear diálogo de detalles
            dialog = CustomerDetailsDialog(stats, self)
            dialog.exec_()
            
        except Exception as e:
            logger.error(f"Error abriendo detalles del cliente: {e}")
            self.show_error("Error", f"No se pudieron cargar los detalles: {str(e)}")
    
    def add_customer_note(self):
        """Añadir nota al cliente"""
        if not self.current_customer or not self.customer_manager:
            return
        
        note, ok = QInputDialog.getMultiLineText(
            self, "Añadir Nota", 
            f"Nota para {self.current_customer['nombre']} {self.current_customer['apellido']}:"
        )
        
        if ok and note.strip():
            try:
                success = self.customer_manager.add_customer_note(
                    customer_id=self.current_customer['id'],
                    note=note.strip(),
                    user_id=1  # TODO: Obtener del contexto de usuario
                )
                
                if success:
                    QMessageBox.information(self, "Éxito", "Nota añadida correctamente")
                else:
                    self.show_error("Error", "No se pudo añadir la nota")
                    
            except Exception as e:
                logger.error(f"Error añadiendo nota: {e}")
                self.show_error("Error", f"Error añadiendo nota: {str(e)}")
    
    def process_payment(self):
        """Procesar pago de cuenta corriente"""
        if not self.current_customer or not self.customer_manager:
            return
        
        current_debt = float(self.current_customer.get('saldo_cuenta_corriente', 0))
        if current_debt <= 0:
            QMessageBox.information(self, "Info", "Este cliente no tiene deuda pendiente")
            return
        
        # Diálogo para capturar datos del pago
        dialog = PaymentDialog(self.current_customer, current_debt, self)
        if dialog.exec_() == QDialog.Accepted:
            payment_data = dialog.get_payment_data()
            
            try:
                success, message = self.customer_manager.process_account_payment(
                    customer_id=self.current_customer['id'],
                    amount=payment_data['amount'],
                    payment_method=payment_data['method'],
                    reference=payment_data['reference'],
                    user_id=1,  # TODO: Obtener del contexto
                    notes=payment_data['notes']
                )
                
                if success:
                    QMessageBox.information(self, "Éxito", message)
                    self.refresh_data()
                else:
                    self.show_error("Error", message)
                    
            except Exception as e:
                logger.error(f"Error procesando pago: {e}")
                self.show_error("Error", f"Error procesando pago: {str(e)}")
    
    def create_new_customer(self):
        """Crear nuevo cliente"""
        # TODO: Implementar diálogo de creación de cliente
        QMessageBox.information(self, "Info", "Funcionalidad en desarrollo")
    
    def auto_categorize_customers(self):
        """Categorizar clientes automáticamente"""
        if not self.customer_manager:
            return
        
        reply = QMessageBox.question(
            self, "Confirmar", 
            "¿Desea categorizar automáticamente todos los clientes basado en su actividad?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                updated_count = 0
                for customer in self.customers_data:
                    if self.customer_manager.update_customer_category_auto(customer['id']):
                        updated_count += 1
                
                QMessageBox.information(
                    self, "Completado", 
                    f"Se actualizaron {updated_count} categorías de clientes"
                )
                self.refresh_data()
                
            except Exception as e:
                logger.error(f"Error en categorización automática: {e}")
                self.show_error("Error", f"Error en categorización: {str(e)}")
    
    def show_inactive_customers(self):
        """Mostrar clientes inactivos"""
        if not self.customer_manager:
            return
        
        try:
            inactive = self.customer_manager.get_inactive_customers(90)
            
            dialog = InactiveCustomersDialog(inactive, self)
            dialog.exec_()
            
        except Exception as e:
            logger.error(f"Error obteniendo clientes inactivos: {e}")
            self.show_error("Error", f"Error: {str(e)}")
    
    def analyze_customers(self):
        """Analizar top clientes"""
        if not self.customer_manager:
            return
        
        # Mapear período seleccionado a días
        period_map = {
            "Último mes": 30,
            "Últimos 3 meses": 90,
            "Últimos 6 meses": 180,
            "Último año": 365
        }
        
        period_text = self.period_combo.currentText()
        days = period_map.get(period_text, 365)
        
        try:
            top_customers = self.customer_manager.get_top_customers(limit=20, period_days=days)
            
            # Poblar tabla de top clientes
            self.top_customers_table.setRowCount(len(top_customers))
            
            for row, customer in enumerate(top_customers):
                classification = customer.get('classification', {})
                
                self.top_customers_table.setItem(row, 0, QTableWidgetItem(
                    f"{customer['nombre']} {customer['apellido']}"
                ))
                self.top_customers_table.setItem(row, 1, QTableWidgetItem(customer.get('email', '')))
                self.top_customers_table.setItem(row, 2, QTableWidgetItem(str(customer['total_compras'])))
                self.top_customers_table.setItem(row, 3, QTableWidgetItem(f"${customer['monto_total']:.2f}"))
                self.top_customers_table.setItem(row, 4, QTableWidgetItem(f"${customer['ticket_promedio']:.2f}"))
                self.top_customers_table.setItem(row, 5, QTableWidgetItem(customer.get('ultima_compra', 'N/A')))
                self.top_customers_table.setItem(row, 6, QTableWidgetItem(
                    f"{classification.get('valor', 'N/A')} / {classification.get('actividad', 'N/A')}"
                ))
            
        except Exception as e:
            logger.error(f"Error analizando clientes: {e}")
            self.show_error("Error", f"Error en análisis: {str(e)}")
    
    def filter_accounts(self):
        """Filtrar cuentas corrientes"""
        # Implementar filtro de cuentas
        pass
    
    def refresh_data(self):
        """Actualizar todos los datos"""
        self.load_customers()
        self.load_dashboard()
        self.update_status("Datos actualizados")
    
    def update_status(self, message: str):
        """Actualizar mensaje de estado"""
        self.status_bar.showMessage(message, 5000)
    
    def show_error(self, title: str, message: str):
        """Mostrar mensaje de error"""
        QMessageBox.critical(self, title, message)


class CustomerDetailsDialog(QDialog):
    """Diálogo para mostrar detalles completos del cliente"""
    
    def __init__(self, customer_stats: Dict, parent=None):
        super().__init__(parent)
        
        self.customer_stats = customer_stats
        self.setWindowTitle("Detalles del Cliente")
        self.setModal(True)
        self.resize(800, 600)
        
        self.init_ui()
    
    def init_ui(self):
        """Inicializar interfaz"""
        layout = QVBoxLayout(self)
        
        customer_info = self.customer_stats.get('customer_info', {})
        
        # Header con información básica
        header_layout = QHBoxLayout()
        
        name_label = QLabel(f"{customer_info.get('nombre', '')} {customer_info.get('apellido', '')}")
        name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(name_label)
        
        header_layout.addStretch()
        
        category_label = QLabel(customer_info.get('categoria_cliente', ''))
        category_label.setStyleSheet("background-color: #3498db; color: white; padding: 4px 8px; border-radius: 4px;")
        header_layout.addWidget(category_label)
        
        layout.addLayout(header_layout)
        
        # Tabs con detalles
        tabs = QTabWidget()
        
        # Tab información general
        general_tab = QWidget()
        general_layout = QFormLayout(general_tab)
        
        general_layout.addRow("Email:", QLabel(customer_info.get('email', 'N/A')))
        general_layout.addRow("Teléfono:", QLabel(customer_info.get('telefono', 'N/A')))
        general_layout.addRow("Dirección:", QLabel(customer_info.get('direccion', 'N/A')))
        general_layout.addRow("Límite Crédito:", QLabel(f"${float(customer_info.get('limite_credito', 0)):.2f}"))
        general_layout.addRow("Saldo Actual:", QLabel(f"${float(customer_info.get('saldo_cuenta_corriente', 0)):.2f}"))
        
        tabs.addTab(general_tab, "General")
        
        # Tab estadísticas de ventas
        sales_tab = QWidget()
        sales_layout = QFormLayout(sales_tab)
        
        sales = self.customer_stats.get('sales', {})
        sales_layout.addRow("Total Compras:", QLabel(str(sales.get('total_compras', 0))))
        sales_layout.addRow("Monto Total:", QLabel(f"${sales.get('monto_total', 0):.2f}"))
        sales_layout.addRow("Ticket Promedio:", QLabel(f"${sales.get('ticket_promedio', 0):.2f}"))
        sales_layout.addRow("Primera Compra:", QLabel(sales.get('primera_compra', 'N/A')))
        sales_layout.addRow("Última Compra:", QLabel(sales.get('ultima_compra', 'N/A')))
        
        tabs.addTab(sales_tab, "Ventas")
        
        # Tab clasificación
        class_tab = QWidget()
        class_layout = QFormLayout(class_tab)
        
        classification = self.customer_stats.get('classification', {})
        class_layout.addRow("Valor:", QLabel(classification.get('valor', 'N/A')))
        class_layout.addRow("Actividad:", QLabel(classification.get('actividad', 'N/A')))
        class_layout.addRow("Score:", QLabel(f"{classification.get('score', 0)}/100"))
        class_layout.addRow("Recomendación:", QLabel(classification.get('recomendacion', 'N/A')))
        
        tabs.addTab(class_tab, "Clasificación")
        
        layout.addWidget(tabs)
        
        # Botón cerrar
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class PaymentDialog(QDialog):
    """Diálogo para procesar pagos de cuenta corriente"""
    
    def __init__(self, customer: Dict, current_debt: float, parent=None):
        super().__init__(parent)
        
        self.customer = customer
        self.current_debt = current_debt
        
        self.setWindowTitle("Procesar Pago")
        self.setModal(True)
        self.resize(400, 300)
        
        self.init_ui()
    
    def init_ui(self):
        """Inicializar interfaz"""
        layout = QVBoxLayout(self)
        
        # Información del cliente
        info_label = QLabel(f"Cliente: {self.customer['nombre']} {self.customer['apellido']}")
        info_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(info_label)
        
        debt_label = QLabel(f"Deuda actual: ${self.current_debt:.2f}")
        debt_label.setStyleSheet("color: #e74c3c; font-size: 14px;")
        layout.addWidget(debt_label)
        
        layout.addWidget(QLabel())  # Separador
        
        # Formulario de pago
        form_layout = QFormLayout()
        
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0.01, self.current_debt)
        self.amount_input.setValue(self.current_debt)
        self.amount_input.setPrefix("$")
        self.amount_input.setDecimals(2)
        form_layout.addRow("Monto:", self.amount_input)
        
        self.method_combo = QComboBox()
        self.method_combo.addItems(["EFECTIVO", "TARJETA_DEBITO", "TARJETA_CREDITO", "TRANSFERENCIA", "CHEQUE"])
        form_layout.addRow("Método:", self.method_combo)
        
        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText("Número de referencia...")
        form_layout.addRow("Referencia:", self.reference_input)
        
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setPlaceholderText("Observaciones...")
        form_layout.addRow("Notas:", self.notes_input)
        
        layout.addLayout(form_layout)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        process_btn = QPushButton("Procesar Pago")
        process_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        process_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(process_btn)
        
        layout.addLayout(buttons_layout)
    
    def get_payment_data(self) -> Dict:
        """Obtener datos del pago"""
        return {
            'amount': self.amount_input.value(),
            'method': self.method_combo.currentText(),
            'reference': self.reference_input.text().strip(),
            'notes': self.notes_input.toPlainText().strip()
        }


class InactiveCustomersDialog(QDialog):
    """Diálogo para mostrar clientes inactivos"""
    
    def __init__(self, inactive_customers: List[Dict], parent=None):
        super().__init__(parent)
        
        self.inactive_customers = inactive_customers
        self.setWindowTitle("Clientes Inactivos - Campaña de Reactivación")
        self.setModal(True)
        self.resize(700, 500)
        
        self.init_ui()
    
    def init_ui(self):
        """Inicializar interfaz"""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel(f"Clientes Inactivos Detectados: {len(self.inactive_customers)}")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header_label)
        
        # Tabla de clientes inactivos
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Cliente", "Email", "Teléfono", "Última Compra", 
            "Monto Histórico", "Prioridad"
        ])
        
        table.setRowCount(len(self.inactive_customers))
        
        for row, customer in enumerate(self.inactive_customers):
            table.setItem(row, 0, QTableWidgetItem(
                f"{customer['nombre']} {customer['apellido']}"
            ))
            table.setItem(row, 1, QTableWidgetItem(customer.get('email', '')))
            table.setItem(row, 2, QTableWidgetItem(customer.get('telefono', '')))
            table.setItem(row, 3, QTableWidgetItem(customer.get('ultima_compra', 'N/A')))
            table.setItem(row, 4, QTableWidgetItem(f"${customer.get('monto_total_historico', 0):.2f}"))
            
            priority_item = QTableWidgetItem(customer.get('priority', 'BAJA'))
            if customer.get('priority') == 'ALTA':
                priority_item.setBackground(QColor("#ffcdd2"))
            elif customer.get('priority') == 'MEDIA':
                priority_item.setBackground(QColor("#fff3e0"))
            table.setItem(row, 5, priority_item)
        
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        
        layout.addWidget(table)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        export_btn = QPushButton("📤 Exportar Lista")
        buttons_layout.addWidget(export_btn)
        
        buttons_layout.addStretch()
        
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)