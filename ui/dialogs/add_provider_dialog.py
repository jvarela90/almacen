"""
Diálogo para agregar/editar proveedores en AlmacénPro
Permite gestionar información completa de proveedores
"""

import logging
import re
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

logger = logging.getLogger(__name__)

class AddProviderDialog(QDialog):
    """Diálogo para agregar o editar proveedores"""
    
    def __init__(self, provider_manager, provider_data=None, parent=None):
        super().__init__(parent)
        self.provider_manager = provider_manager
        self.provider_data = provider_data
        self.editing_mode = provider_data is not None
        
        self.init_ui()
        if self.editing_mode:
            self.populate_fields()
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        title = "Editar Proveedor" if self.editing_mode else "Agregar Nuevo Proveedor"
        self.setWindowTitle(title)
        self.setFixedSize(550, 600)
        
        # Layout principal con scroll
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Header
        self.create_header(scroll_layout)
        
        # Tabs para organizar información
        tab_widget = QTabWidget()
        
        # Tab 1: Información básica
        basic_tab = self.create_basic_info_tab()
        tab_widget.addTab(basic_tab, "📝 Información Básica")
        
        # Tab 2: Contacto
        contact_tab = self.create_contact_tab()
        tab_widget.addTab(contact_tab, "📞 Contacto")
        
        # Tab 3: Condiciones comerciales
        commercial_tab = self.create_commercial_tab()
        tab_widget.addTab(commercial_tab, "💼 Condiciones Comerciales")
        
        scroll_layout.addWidget(tab_widget)
        
        # Botones
        self.create_buttons(scroll_layout)
        
        # Configurar scroll area
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
        
        # Aplicar estilos
        self.setup_styles()
    
    def create_header(self, layout):
        """Crear header del diálogo"""
        header_widget = QWidget()
        header_widget.setObjectName("header")
        header_layout = QHBoxLayout(header_widget)
        
        # Icono
        icon_label = QLabel("👥")
        icon_label.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(icon_label)
        
        # Título y descripción
        text_layout = QVBoxLayout()
        
        title = "Editar Proveedor" if self.editing_mode else "Agregar Nuevo Proveedor"
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2E86AB;")
        text_layout.addWidget(title_label)
        
        desc = "Modifique los datos del proveedor" if self.editing_mode else "Complete la información del nuevo proveedor"
        desc_label = QLabel(desc)
        desc_label.setStyleSheet("color: #666; font-size: 12px;")
        text_layout.addWidget(desc_label)
        
        header_layout.addLayout(text_layout)
        header_layout.addStretch()
        
        # Rating visual (solo en modo edición)
        if self.editing_mode:
            rating_layout = QVBoxLayout()
            rating_label = QLabel("Calificación:")
            rating_label.setStyleSheet("font-size: 12px; color: #666;")
            rating_layout.addWidget(rating_label)
            
            self.rating_display = QLabel("⭐⭐⭐⭐⭐")
            self.rating_display.setStyleSheet("font-size: 16px;")
            rating_layout.addWidget(self.rating_display)
            
            header_layout.addLayout(rating_layout)
        
        layout.addWidget(header_widget)
    
    def create_basic_info_tab(self) -> QWidget:
        """Crear tab de información básica"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Grupo: Identificación
        id_group = QGroupBox("Identificación del Proveedor")
        id_layout = QFormLayout(id_group)
        
        # Nombre de la empresa
        self.company_name_input = QLineEdit()
        self.company_name_input.setPlaceholderText("Nombre de la empresa o proveedor *")
        self.company_name_input.setMaxLength(200)
        id_layout.addRow("Nombre de la Empresa *:", self.company_name_input)
        
        # CUIT/DNI
        self.cuit_input = QLineEdit()
        self.cuit_input.setPlaceholderText("XX-XXXXXXXX-X")
        self.cuit_input.setMaxLength(20)
        self.cuit_input.textChanged.connect(self.format_cuit)
        
        cuit_layout = QHBoxLayout()
        cuit_layout.addWidget(self.cuit_input)
        
        validate_cuit_btn = QPushButton("✓")
        validate_cuit_btn.setFixedWidth(30)
        validate_cuit_btn.setToolTip("Validar CUIT")
        validate_cuit_btn.clicked.connect(self.validate_cuit)
        cuit_layout.addWidget(validate_cuit_btn)
        
        cuit_widget = QWidget()
        cuit_widget.setLayout(cuit_layout)
        id_layout.addRow("CUIT/DNI:", cuit_widget)
        
        layout.addWidget(id_group)
        
        # Grupo: Dirección
        address_group = QGroupBox("Dirección")
        address_layout = QFormLayout(address_group)
        
        # Dirección
        self.address_input = QTextEdit()
        self.address_input.setPlaceholderText("Dirección completa del proveedor")
        self.address_input.setMaximumHeight(60)
        address_layout.addRow("Dirección:", self.address_input)
        
        # Ciudad
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("Ciudad")
        self.city_input.setMaxLength(100)
        address_layout.addRow("Ciudad:", self.city_input)
        
        # Provincia
        self.province_combo = QComboBox()
        self.province_combo.setEditable(True)
        self.load_provinces()
        address_layout.addRow("Provincia:", self.province_combo)
        
        # Código postal
        self.postal_code_input = QLineEdit()
        self.postal_code_input.setPlaceholderText("1234")
        self.postal_code_input.setMaxLength(10)
        address_layout.addRow("Código Postal:", self.postal_code_input)
        
        layout.addWidget(address_group)
        
        return widget
    
    def create_contact_tab(self) -> QWidget:
        """Crear tab de información de contacto"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Grupo: Información de contacto
        contact_group = QGroupBox("Información de Contacto")
        contact_layout = QFormLayout(contact_group)
        
        # Teléfono principal
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("(011) 1234-5678")
        self.phone_input.setMaxLength(50)
        contact_layout.addRow("Teléfono Principal:", self.phone_input)
        
        # Teléfono alternativo
        self.alt_phone_input = QLineEdit()
        self.alt_phone_input.setPlaceholderText("Teléfono alternativo")
        self.alt_phone_input.setMaxLength(50)
        contact_layout.addRow("Teléfono Alternativo:", self.alt_phone_input)
        
        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email@empresa.com")
        self.email_input.setMaxLength(100)
        self.email_input.textChanged.connect(self.validate_email_format)
        contact_layout.addRow("Email:", self.email_input)
        
        # Sitio web
        self.website_input = QLineEdit()
        self.website_input.setPlaceholderText("https://www.empresa.com")
        self.website_input.setMaxLength(200)
        contact_layout.addRow("Sitio Web:", self.website_input)
        
        layout.addWidget(contact_group)
        
        # Grupo: Persona de contacto
        person_group = QGroupBox("Persona de Contacto")
        person_layout = QFormLayout(person_group)
        
        # Nombre del contacto
        self.contact_name_input = QLineEdit()
        self.contact_name_input.setPlaceholderText("Nombre del contacto principal")
        self.contact_name_input.setMaxLength(100)
        person_layout.addRow("Nombre del Contacto:", self.contact_name_input)
        
        # Cargo
        self.contact_position_input = QLineEdit()
        self.contact_position_input.setPlaceholderText("Gerente de Ventas, Representante, etc.")
        self.contact_position_input.setMaxLength(100)
        person_layout.addRow("Cargo:", self.contact_position_input)
        
        layout.addWidget(person_group)
        
        # Grupo: Notas adicionales
        notes_group = QGroupBox("Notas Adicionales")
        notes_layout = QVBoxLayout(notes_group)
        
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Notas adicionales sobre el proveedor...")
        self.notes_input.setMaximumHeight(100)
        notes_layout.addWidget(self.notes_input)
        
        layout.addWidget(notes_group)
        
        return widget
    
    def create_commercial_tab(self) -> QWidget:
        """Crear tab de condiciones comerciales"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Grupo: Condiciones de pago
        payment_group = QGroupBox("Condiciones de Pago")
        payment_layout = QFormLayout(payment_group)
        
        # Condiciones de pago
        self.payment_terms_input = QTextEdit()
        self.payment_terms_input.setPlaceholderText("Ej: 30 días, Contado, Transferencia bancaria, etc.")
        self.payment_terms_input.setMaximumHeight(60)
        payment_layout.addRow("Condiciones de Pago:", self.payment_terms_input)
        
        # Descuento por pronto pago
        self.discount_input = QDoubleSpinBox()
        self.discount_input.setMinimum(0.00)
        self.discount_input.setMaximum(100.00)
        self.discount_input.setDecimals(2)
        self.discount_input.setSuffix(" %")
        payment_layout.addRow("Descuento (%):", self.discount_input)
        
        # Límite de crédito
        self.credit_limit_input = QDoubleSpinBox()
        self.credit_limit_input.setMinimum(0.00)
        self.credit_limit_input.setMaximum(9999999.99)
        self.credit_limit_input.setDecimals(2)
        self.credit_limit_input.setPrefix("$ ")
        payment_layout.addRow("Límite de Crédito:", self.credit_limit_input)
        
        layout.addWidget(payment_group)
        
        # Grupo: Evaluación
        evaluation_group = QGroupBox("Evaluación del Proveedor")
        evaluation_layout = QFormLayout(evaluation_group)
        
        # Calificación
        self.rating_input = QSpinBox()
        self.rating_input.setMinimum(1)
        self.rating_input.setMaximum(5)
        self.rating_input.setValue(5)
        self.rating_input.setSuffix(" ⭐")
        self.rating_input.valueChanged.connect(self.update_rating_display)
        evaluation_layout.addRow("Calificación (1-5):", self.rating_input)
        
        # Crear botones de rating visual
        rating_buttons_layout = QHBoxLayout()
        self.rating_buttons = []
        for i in range(1, 6):
            btn = QPushButton("⭐")
            btn.setFixedSize(30, 30)
            btn.setProperty("rating", i)
            btn.clicked.connect(lambda checked, rating=i: self.set_rating(rating))
            self.rating_buttons.append(btn)
            rating_buttons_layout.addWidget(btn)
        
        rating_buttons_widget = QWidget()
        rating_buttons_widget.setLayout(rating_buttons_layout)
        evaluation_layout.addRow("Rating Visual:", rating_buttons_widget)
        
        layout.addWidget(evaluation_group)
        
        # Grupo: Estado
        status_group = QGroupBox("Estado del Proveedor")
        status_layout = QVBoxLayout(status_group)
        
        self.active_checkbox = QCheckBox("Proveedor activo")
        self.active_checkbox.setChecked(True)
        status_layout.addWidget(self.active_checkbox)
        
        layout.addWidget(status_group)
        
        # Actualizar rating visual inicial
        self.update_rating_buttons()
        
        return widget
    
    def create_buttons(self, layout):
        """Crear botones de acción"""
        button_layout = QHBoxLayout()
        
        # Botón cancelar
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setFixedHeight(35)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # Botón para ver productos del proveedor (solo en modo edición)
        if self.editing_mode:
            view_products_btn = QPushButton("Ver Productos")
            view_products_btn.setFixedHeight(35)
            view_products_btn.clicked.connect(self.view_provider_products)
            button_layout.addWidget(view_products_btn)
        
        button_layout.addStretch()
        
        # Botón guardar
        save_text = "Guardar Cambios" if self.editing_mode else "Agregar Proveedor"
        self.save_btn = QPushButton(save_text)
        self.save_btn.setFixedHeight(35)
        self.save_btn.setObjectName("primary_btn")
        self.save_btn.clicked.connect(self.save_provider)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def setup_styles(self):
        """Configurar estilos CSS"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            
            QWidget#header {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 10px;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2E86AB;
            }
            
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                padding: 8px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
            
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, 
            QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #2E86AB;
                outline: none;
            }
            
            QLineEdit.error {
                border-color: #dc3545;
                background-color: #f8d7da;
            }
            
            QPushButton {
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            
            QPushButton#primary_btn {
                background-color: #2E86AB;
                color: white;
            }
            
            QPushButton#primary_btn:hover {
                background-color: #1e5f7a;
            }
            
            QPushButton:hover {
                background-color: #e9ecef;
            }
            
            QTabWidget::pane {
                border: 1px solid #ced4da;
                background-color: white;
                border-radius: 4px;
            }
            
            QTabBar::tab {
                background-color: #e9ecef;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
        """)
    
    def load_provinces(self):
        """Cargar lista de provincias argentinas"""
        provinces = [
            "Buenos Aires", "Catamarca", "Chaco", "Chubut", "Córdoba",
            "Corrientes", "Entre Ríos", "Formosa", "Jujuy", "La Pampa",
            "La Rioja", "Mendoza", "Misiones", "Neuquén", "Río Negro",
            "Salta", "San Juan", "San Luis", "Santa Cruz", "Santa Fe",
            "Santiago del Estero", "Tierra del Fuego", "Tucumán"
        ]
        
        for province in provinces:
            self.province_combo.addItem(province)
    
    def format_cuit(self, text):
        """Formatear CUIT mientras se escribe"""
        # Eliminar caracteres no numéricos
        numbers_only = re.sub(r'[^0-9]', '', text)
        
        # Formatear como XX-XXXXXXXX-X
        if len(numbers_only) >= 11:
            formatted = f"{numbers_only[:2]}-{numbers_only[2:10]}-{numbers_only[10]}"
            self.cuit_input.blockSignals(True)
            self.cuit_input.setText(formatted)
            self.cuit_input.blockSignals(False)
    
    def validate_cuit(self):
        """Validar CUIT (algoritmo básico)"""
        cuit = re.sub(r'[^0-9]', '', self.cuit_input.text())
        
        if len(cuit) != 11:
            QMessageBox.warning(self, "CUIT Inválido", "El CUIT debe tener 11 dígitos")
            return False
        
        # Algoritmo de validación CUIT (simplificado)
        try:
            multipliers = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
            total = sum(int(cuit[i]) * multipliers[i] for i in range(10))
            
            remainder = total % 11
            if remainder < 2:
                check_digit = remainder
            else:
                check_digit = 11 - remainder
            
            if check_digit == int(cuit[10]):
                QMessageBox.information(self, "CUIT Válido", "✅ El CUIT es válido")
                return True
            else:
                QMessageBox.warning(self, "CUIT Inválido", "❌ El dígito verificador es incorrecto")
                return False
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error validando CUIT: {str(e)}")
            return False
    
    def validate_email_format(self, email):
        """Validar formato de email en tiempo real"""
        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            self.email_input.setProperty("class", "error")
            self.email_input.setStyleSheet("border-color: #dc3545; background-color: #f8d7da;")
        else:
            self.email_input.setProperty("class", "")
            self.email_input.setStyleSheet("")
    
    def set_rating(self, rating):
        """Establecer calificación desde botones visuales"""
        self.rating_input.setValue(rating)
        self.update_rating_buttons()
    
    def update_rating_display(self):
        """Actualizar display de rating"""
        if hasattr(self, 'rating_display'):
            rating = self.rating_input.value()
            stars = "⭐" * rating + "☆" * (5 - rating)
            self.rating_display.setText(stars)
        
        self.update_rating_buttons()
    
    def update_rating_buttons(self):
        """Actualizar botones de rating visual"""
        rating = self.rating_input.value()
        for i, btn in enumerate(self.rating_buttons, 1):
            if i <= rating:
                btn.setStyleSheet("background-color: #ffc107; color: white;")
            else:
                btn.setStyleSheet("background-color: #e9ecef;")
    
    def populate_fields(self):
        """Llenar campos con datos del proveedor (modo edición)"""
        if not self.provider_data:
            return
        
        try:
            # Tab 1: Información básica
            self.company_name_input.setText(self.provider_data.get('nombre', ''))
            self.cuit_input.setText(self.provider_data.get('cuit_dni', ''))
            self.address_input.setPlainText(self.provider_data.get('direccion', ''))
            self.city_input.setText(self.provider_data.get('ciudad', ''))
            self.postal_code_input.setText(self.provider_data.get('codigo_postal', ''))
            
            # Provincia
            province = self.provider_data.get('provincia', '')
            if province:
                index = self.province_combo.findText(province)
                if index >= 0:
                    self.province_combo.setCurrentIndex(index)
                else:
                    self.province_combo.setCurrentText(province)
            
            # Tab 2: Contacto
            self.phone_input.setText(self.provider_data.get('telefono', ''))
            self.alt_phone_input.setText(self.provider_data.get('telefono_alternativo', ''))
            self.email_input.setText(self.provider_data.get('email', ''))
            self.website_input.setText(self.provider_data.get('sitio_web', ''))
            self.contact_name_input.setText(self.provider_data.get('contacto_principal', ''))
            self.contact_position_input.setText(self.provider_data.get('cargo_contacto', ''))
            self.notes_input.setPlainText(self.provider_data.get('notas', ''))
            
            # Tab 3: Condiciones comerciales
            self.payment_terms_input.setPlainText(self.provider_data.get('condiciones_pago', ''))
            self.discount_input.setValue(float(self.provider_data.get('descuento_porcentaje', 0)))
            self.credit_limit_input.setValue(float(self.provider_data.get('limite_credito', 0)))
            self.rating_input.setValue(int(self.provider_data.get('calificacion', 5)))
            self.active_checkbox.setChecked(self.provider_data.get('activo', True))
            
            # Actualizar displays
            self.update_rating_display()
            
        except Exception as e:
            logger.error(f"Error poblando campos: {e}")
            QMessageBox.warning(self, "Advertencia", f"Error cargando datos del proveedor: {str(e)}")
    
    def validate_form(self) -> tuple[bool, str]:
        """Validar formulario"""
        # Validaciones obligatorias
        if not self.company_name_input.text().strip():
            return False, "El nombre de la empresa es obligatorio"
        
        # Validar email si se proporciona
        email = self.email_input.text().strip()
        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return False, "El formato del email no es válido"
        
        # Validar CUIT único si se proporciona
        cuit = self.cuit_input.text().strip()
        if cuit:
            try:
                existing = self.provider_manager.db.execute_single("""
                    SELECT id FROM proveedores WHERE cuit_dni = ? AND activo = 1
                """, (cuit,))
                
                if existing and (not self.editing_mode or existing['id'] != self.provider_data['id']):
                    return False, "Ya existe un proveedor con ese CUIT/DNI"
            except:
                pass
        
        return True, ""
    
    def save_provider(self):
        """Guardar proveedor"""
        # Validar formulario
        valid, message = self.validate_form()
        if not valid:
            QMessageBox.warning(self, "Error de Validación", message)
            return
        
        try:
            # Recopilar datos del formulario
            provider_data = {
                'nombre': self.company_name_input.text().strip(),
                'cuit_dni': self.cuit_input.text().strip() or None,
                'direccion': self.address_input.toPlainText().strip() or None,
                'ciudad': self.city_input.text().strip() or None,
                'provincia': self.province_combo.currentText().strip() or None,
                'codigo_postal': self.postal_code_input.text().strip() or None,
                'telefono': self.phone_input.text().strip() or None,
                'telefono_alternativo': self.alt_phone_input.text().strip() or None,
                'email': self.email_input.text().strip() or None,
                'sitio_web': self.website_input.text().strip() or None,
                'contacto_principal': self.contact_name_input.text().strip() or None,
                'cargo_contacto': self.contact_position_input.text().strip() or None,
                'condiciones_pago': self.payment_terms_input.toPlainText().strip() or None,
                'descuento_porcentaje': self.discount_input.value(),
                'limite_credito': self.credit_limit_input.value(),
                'calificacion': self.rating_input.value(),
                'notas': self.notes_input.toPlainText().strip() or None,
                'activo': self.active_checkbox.isChecked()
            }
            
            # Guardar proveedor
            if self.editing_mode:
                success, message = self.provider_manager.update_provider(
                    self.provider_data['id'], provider_data
                )
            else:
                success, message, provider_id = self.provider_manager.create_provider(provider_data)
            
            if success:
                QMessageBox.information(self, "Éxito", message)
                self.accept()
            else:
                QMessageBox.critical(self, "Error", message)
                
        except Exception as e:
            logger.error(f"Error guardando proveedor: {e}")
            QMessageBox.critical(self, "Error", f"Error guardando proveedor: {str(e)}")
    
    def view_provider_products(self):
        """Ver productos del proveedor"""
        if not self.editing_mode:
            return
        
        try:
            products = self.provider_manager.get_provider_products(self.provider_data['id'])
            
            if not products:
                QMessageBox.information(self, "Sin Productos", "Este proveedor no tiene productos asignados")
                return
            
            # Crear diálogo simple para mostrar productos
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Productos de {self.provider_data['nombre']}")
            dialog.setFixedSize(600, 400)
            
            layout = QVBoxLayout()
            
            # Tabla de productos
            table = QTableWidget()
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(["Código", "Producto", "Stock", "Precio"])
            table.setRowCount(len(products))
            
            for i, product in enumerate(products):
                table.setItem(i, 0, QTableWidgetItem(product.get('codigo_barras', '')))
                table.setItem(i, 1, QTableWidgetItem(product['nombre']))
                table.setItem(i, 2, QTableWidgetItem(str(product['stock_actual'])))
                table.setItem(i, 3, QTableWidgetItem(f"${product['precio_venta']:.2f}"))
            
            table.resizeColumnsToContents()
            layout.addWidget(table)
            
            # Botón cerrar
            close_btn = QPushButton("Cerrar")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            dialog.setLayout(layout)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error obteniendo productos: {str(e)}")


class QuickAddProviderDialog(QDialog):
    """Diálogo simplificado para agregar proveedores rápidamente"""
    
    def __init__(self, provider_manager, parent=None):
        super().__init__(parent)
        self.provider_manager = provider_manager
        self.init_ui()
    
    def init_ui(self):
        """Inicializar interfaz simplificada"""
        self.setWindowTitle("Agregar Proveedor Rápido")
        self.setFixedSize(400, 250)
        
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("Agregar Proveedor Rápido")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 15px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Formulario básico
        form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre de la empresa *")
        form_layout.addRow("Nombre *:", self.name_input)
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Teléfono de contacto")
        form_layout.addRow("Teléfono:", self.phone_input)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email@empresa.com")
        form_layout.addRow("Email:", self.email_input)
        
        layout.addLayout(form_layout)
        
        # Nota
        note = QLabel("Nota: Podrá editar más detalles después desde la gestión de proveedores")
        note.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
        note.setWordWrap(True)
        layout.addWidget(note)
        
        # Botones
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Agregar Proveedor")
        save_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
        save_btn.clicked.connect(self.save_quick_provider)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def save_quick_provider(self):
        """Guardar proveedor con información básica"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Error", "El nombre de la empresa es obligatorio")
            return
        
        try:
            provider_data = {
                'nombre': self.name_input.text().strip(),
                'telefono': self.phone_input.text().strip() or None,
                'email': self.email_input.text().strip() or None,
                'calificacion': 5
            }
            
            success, message, provider_id = self.provider_manager.create_provider(provider_data)
            
            if success:
                QMessageBox.information(self, "Éxito", message)
                self.accept()
            else:
                QMessageBox.critical(self, "Error", message)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error creando proveedor: {str(e)}")