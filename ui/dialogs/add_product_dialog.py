"""
Diálogo para agregar/editar productos en AlmacénPro
Permite gestionar toda la información de productos
"""

import logging
from decimal import Decimal
from datetime import datetime, date
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

logger = logging.getLogger(__name__)

class AddProductDialog(QDialog):
    """Diálogo para agregar o editar productos"""
    
    def __init__(self, product_manager, provider_manager, product_data=None, parent=None):
        super().__init__(parent)
        self.product_manager = product_manager
        self.provider_manager = provider_manager
        self.product_data = product_data
        self.editing_mode = product_data is not None
        
        self.init_ui()
        self.load_data()
        if self.editing_mode:
            self.populate_fields()
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        title = "Editar Producto" if self.editing_mode else "Agregar Nuevo Producto"
        self.setWindowTitle(title)
        self.setFixedSize(600, 700)
        
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
        
        # Tab 2: Precios y stock
        pricing_tab = self.create_pricing_tab()
        tab_widget.addTab(pricing_tab, "💰 Precios y Stock")
        
        # Tab 3: Detalles adicionales
        details_tab = self.create_details_tab()
        tab_widget.addTab(details_tab, "📋 Detalles Adicionales")
        
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
        icon_label = QLabel("📦")
        icon_label.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(icon_label)
        
        # Título y descripción
        text_layout = QVBoxLayout()
        
        title = "Editar Producto" if self.editing_mode else "Agregar Nuevo Producto"
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2E86AB;")
        text_layout.addWidget(title_label)
        
        desc = "Modifique la información del producto" if self.editing_mode else "Complete la información del nuevo producto"
        desc_label = QLabel(desc)
        desc_label.setStyleSheet("color: #666; font-size: 12px;")
        text_layout.addWidget(desc_label)
        
        header_layout.addLayout(text_layout)
        header_layout.addStretch()
        
        layout.addWidget(header_widget)
    
    def create_basic_info_tab(self) -> QWidget:
        """Crear tab de información básica"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Grupo: Identificación
        id_group = QGroupBox("Identificación del Producto")
        id_layout = QFormLayout(id_group)
        
        # Código de barras
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Escanee o ingrese código de barras")
        self.barcode_input.setMaxLength(50)
        barcode_layout = QHBoxLayout()
        barcode_layout.addWidget(self.barcode_input)
        
        scan_btn = QPushButton("📷 Escanear")
        scan_btn.setFixedWidth(80)
        scan_btn.clicked.connect(self.scan_barcode)
        barcode_layout.addWidget(scan_btn)
        
        barcode_widget = QWidget()
        barcode_widget.setLayout(barcode_layout)
        id_layout.addRow("Código de Barras:", barcode_widget)
        
        # Código interno
        self.internal_code_input = QLineEdit()
        self.internal_code_input.setPlaceholderText("Se genera automáticamente")
        self.internal_code_input.setMaxLength(50)
        id_layout.addRow("Código Interno:", self.internal_code_input)
        
        # Nombre del producto
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre del producto *")
        self.name_input.setMaxLength(200)
        id_layout.addRow("Nombre del Producto *:", self.name_input)
        
        # Descripción
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Descripción detallada del producto")
        self.description_input.setMaximumHeight(80)
        id_layout.addRow("Descripción:", self.description_input)
        
        layout.addWidget(id_group)
        
        # Grupo: Categorización
        cat_group = QGroupBox("Categorización")
        cat_layout = QFormLayout(cat_group)
        
        # Categoría
        self.category_combo = QComboBox()
        self.category_combo.setEditable(False)
        cat_layout.addRow("Categoría:", self.category_combo)
        
        # Proveedor
        self.provider_combo = QComboBox()
        self.provider_combo.setEditable(False)
        provider_layout = QHBoxLayout()
        provider_layout.addWidget(self.provider_combo)
        
        new_provider_btn = QPushButton("➕")
        new_provider_btn.setFixedWidth(30)
        new_provider_btn.setToolTip("Agregar nuevo proveedor")
        new_provider_btn.clicked.connect(self.add_new_provider)
        provider_layout.addWidget(new_provider_btn)
        
        provider_widget = QWidget()
        provider_widget.setLayout(provider_layout)
        cat_layout.addRow("Proveedor:", provider_widget)
        
        # Unidad de medida
        self.unit_combo = QComboBox()
        self.unit_combo.addItems([
            "UNIDAD", "KILOGRAMO", "GRAMO", "LITRO", "METRO", 
            "CAJA", "PACK", "DOCENA", "CENTENA"
        ])
        self.unit_combo.setEditable(True)
        cat_layout.addRow("Unidad de Medida:", self.unit_combo)
        
        layout.addWidget(cat_group)
        
        return widget
    
    def create_pricing_tab(self) -> QWidget:
        """Crear tab de precios y stock"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Grupo: Precios
        price_group = QGroupBox("Gestión de Precios")
        price_layout = QFormLayout(price_group)
        
        # Precio de compra
        self.purchase_price_input = QDoubleSpinBox()
        self.purchase_price_input.setMinimum(0.00)
        self.purchase_price_input.setMaximum(999999.99)
        self.purchase_price_input.setDecimals(2)
        self.purchase_price_input.setPrefix("$ ")
        price_layout.addRow("Precio de Compra:", self.purchase_price_input)
        
        # Precio de venta
        self.sale_price_input = QDoubleSpinBox()
        self.sale_price_input.setMinimum(0.01)
        self.sale_price_input.setMaximum(999999.99)
        self.sale_price_input.setDecimals(2)
        self.sale_price_input.setPrefix("$ ")
        self.sale_price_input.valueChanged.connect(self.calculate_margin)
        price_layout.addRow("Precio de Venta *:", self.sale_price_input)
        
        # Precio mayorista
        self.wholesale_price_input = QDoubleSpinBox()
        self.wholesale_price_input.setMinimum(0.00)
        self.wholesale_price_input.setMaximum(999999.99)
        self.wholesale_price_input.setDecimals(2)
        self.wholesale_price_input.setPrefix("$ ")
        price_layout.addRow("Precio Mayorista:", self.wholesale_price_input)
        
        # Margen de ganancia
        self.margin_input = QDoubleSpinBox()
        self.margin_input.setMinimum(-100.00)
        self.margin_input.setMaximum(1000.00)
        self.margin_input.setDecimals(2)
        self.margin_input.setSuffix(" %")
        self.margin_input.setReadOnly(True)
        self.margin_input.setStyleSheet("background-color: #f8f9fa;")
        price_layout.addRow("Margen de Ganancia:", self.margin_input)
        
        # IVA
        self.iva_input = QDoubleSpinBox()
        self.iva_input.setMinimum(0.00)
        self.iva_input.setMaximum(50.00)
        self.iva_input.setDecimals(2)
        self.iva_input.setSuffix(" %")
        self.iva_input.setValue(21.00)
        price_layout.addRow("IVA (%):", self.iva_input)
        
        layout.addWidget(price_group)
        
        # Grupo: Stock
        stock_group = QGroupBox("Control de Stock")
        stock_layout = QFormLayout(stock_group)
        
        # Stock actual
        self.current_stock_input = QSpinBox()
        self.current_stock_input.setMinimum(0)
        self.current_stock_input.setMaximum(999999)
        stock_layout.addRow("Stock Actual:", self.current_stock_input)
        
        # Stock mínimo
        self.min_stock_input = QSpinBox()
        self.min_stock_input.setMinimum(0)
        self.min_stock_input.setMaximum(999999)
        stock_layout.addRow("Stock Mínimo:", self.min_stock_input)
        
        # Stock máximo
        self.max_stock_input = QSpinBox()
        self.max_stock_input.setMinimum(0)
        self.max_stock_input.setMaximum(999999)
        stock_layout.addRow("Stock Máximo:", self.max_stock_input)
        
        # Ubicación
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Ej: Estante A, Fila 3, Góndola 2")
        self.location_input.setMaxLength(100)
        stock_layout.addRow("Ubicación:", self.location_input)
        
        layout.addWidget(stock_group)
        
        # Grupo: Opciones
        options_group = QGroupBox("Opciones de Venta")
        options_layout = QVBoxLayout(options_group)
        
        self.allow_negative_stock_cb = QCheckBox("Permitir venta sin stock")
        options_layout.addWidget(self.allow_negative_stock_cb)
        
        self.is_weighable_cb = QCheckBox("Producto pesable")
        options_layout.addWidget(self.is_weighable_cb)
        
        self.own_production_cb = QCheckBox("Producción propia")
        options_layout.addWidget(self.own_production_cb)
        
        layout.addWidget(options_group)
        
        return widget
    
    def create_details_tab(self) -> QWidget:
        """Crear tab de detalles adicionales"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Grupo: Información adicional
        info_group = QGroupBox("Información Adicional")
        info_layout = QFormLayout(info_group)
        
        # Peso
        self.weight_input = QDoubleSpinBox()
        self.weight_input.setMinimum(0.000)
        self.weight_input.setMaximum(999.999)
        self.weight_input.setDecimals(3)
        self.weight_input.setSuffix(" kg")
        info_layout.addRow("Peso:", self.weight_input)
        
        # Fecha de vencimiento
        self.expiry_date_input = QDateEdit()
        self.expiry_date_input.setDate(QDate.currentDate().addDays(365))
        self.expiry_date_input.setCalendarPopup(True)
        self.expiry_date_input.setSpecialValueText("Sin vencimiento")
        info_layout.addRow("Fecha de Vencimiento:", self.expiry_date_input)
        
        # Lote
        self.batch_input = QLineEdit()
        self.batch_input.setPlaceholderText("Número de lote")
        self.batch_input.setMaxLength(50)
        info_layout.addRow("Lote:", self.batch_input)
        
        # Código PLU (para productos pesables)
        self.plu_input = QLineEdit()
        self.plu_input.setPlaceholderText("Código PLU para balanza")
        self.plu_input.setMaxLength(10)
        self.plu_input.setEnabled(False)
        info_layout.addRow("Código PLU:", self.plu_input)
        
        # Conectar checkbox pesable con PLU
        self.is_weighable_cb.toggled.connect(self.plu_input.setEnabled)
        
        layout.addWidget(info_group)
        
        # Grupo: Imagen
        image_group = QGroupBox("Imagen del Producto")
        image_layout = QVBoxLayout(image_group)
        
        # Preview de imagen
        self.image_label = QLabel()
        self.image_label.setFixedSize(150, 150)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            border: 2px dashed #ccc;
            border-radius: 8px;
            background-color: #f8f9fa;
        """)
        self.image_label.setText("📷\nSin imagen")
        
        image_buttons_layout = QHBoxLayout()
        
        select_image_btn = QPushButton("Seleccionar Imagen")
        select_image_btn.clicked.connect(self.select_image)
        image_buttons_layout.addWidget(select_image_btn)
        
        remove_image_btn = QPushButton("Quitar Imagen")
        remove_image_btn.clicked.connect(self.remove_image)
        image_buttons_layout.addWidget(remove_image_btn)
        
        image_layout.addWidget(self.image_label, 0, Qt.AlignCenter)
        image_layout.addLayout(image_buttons_layout)
        
        layout.addWidget(image_group)
        
        layout.addStretch()
        
        return widget
    
    def create_buttons(self, layout):
        """Crear botones de acción"""
        button_layout = QHBoxLayout()
        
        # Botón cancelar
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setFixedHeight(35)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        button_layout.addStretch()
        
        # Botón guardar
        save_text = "Guardar Cambios" if self.editing_mode else "Agregar Producto"
        self.save_btn = QPushButton(save_text)
        self.save_btn.setFixedHeight(35)
        self.save_btn.setObjectName("primary_btn")
        self.save_btn.clicked.connect(self.save_product)
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
            
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
                padding: 8px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
            
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, 
            QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
                border-color: #2E86AB;
                outline: none;
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
    
    def load_data(self):
        """Cargar datos de categorías y proveedores"""
        # Cargar categorías
        try:
            categories = self.product_manager.get_categories()
            self.category_combo.addItem("Sin categoría", None)
            for category in categories:
                self.category_combo.addItem(category['nombre'], category['id'])
        except Exception as e:
            logger.error(f"Error cargando categorías: {e}")
        
        # Cargar proveedores
        try:
            providers = self.provider_manager.get_all_providers()
            self.provider_combo.addItem("Sin proveedor", None)
            for provider in providers:
                self.provider_combo.addItem(provider['nombre'], provider['id'])
        except Exception as e:
            logger.error(f"Error cargando proveedores: {e}")
    
    def populate_fields(self):
        """Llenar campos con datos del producto (modo edición)"""
        if not self.product_data:
            return
        
        try:
            # Tab 1: Información básica
            self.barcode_input.setText(self.product_data.get('codigo_barras', ''))
            self.internal_code_input.setText(self.product_data.get('codigo_interno', ''))
            self.name_input.setText(self.product_data.get('nombre', ''))
            self.description_input.setPlainText(self.product_data.get('descripcion', ''))
            
            # Seleccionar categoría
            category_id = self.product_data.get('categoria_id')
            if category_id:
                for i in range(self.category_combo.count()):
                    if self.category_combo.itemData(i) == category_id:
                        self.category_combo.setCurrentIndex(i)
                        break
            
            # Seleccionar proveedor
            provider_id = self.product_data.get('proveedor_id')
            if provider_id:
                for i in range(self.provider_combo.count()):
                    if self.provider_combo.itemData(i) == provider_id:
                        self.provider_combo.setCurrentIndex(i)
                        break
            
            # Unidad de medida
            unit = self.product_data.get('unidad_medida', 'UNIDAD')
            index = self.unit_combo.findText(unit)
            if index >= 0:
                self.unit_combo.setCurrentIndex(index)
            else:
                self.unit_combo.setCurrentText(unit)
            
            # Tab 2: Precios y stock
            self.purchase_price_input.setValue(float(self.product_data.get('precio_compra', 0)))
            self.sale_price_input.setValue(float(self.product_data.get('precio_venta', 0)))
            self.wholesale_price_input.setValue(float(self.product_data.get('precio_mayorista', 0)))
            self.iva_input.setValue(float(self.product_data.get('iva_porcentaje', 21)))
            
            self.current_stock_input.setValue(int(self.product_data.get('stock_actual', 0)))
            self.min_stock_input.setValue(int(self.product_data.get('stock_minimo', 0)))
            self.max_stock_input.setValue(int(self.product_data.get('stock_maximo', 0)))
            self.location_input.setText(self.product_data.get('ubicacion', ''))
            
            # Opciones
            self.allow_negative_stock_cb.setChecked(self.product_data.get('permite_venta_sin_stock', False))
            self.is_weighable_cb.setChecked(self.product_data.get('es_pesable', False))
            self.own_production_cb.setChecked(self.product_data.get('es_produccion_propia', False))
            
            # Tab 3: Detalles
            self.weight_input.setValue(float(self.product_data.get('peso', 0)))
            self.batch_input.setText(self.product_data.get('lote', ''))
            self.plu_input.setText(self.product_data.get('codigo_plu', ''))
            
            # Fecha de vencimiento
            if self.product_data.get('vencimiento'):
                try:
                    exp_date = datetime.strptime(self.product_data['vencimiento'], '%Y-%m-%d').date()
                    self.expiry_date_input.setDate(QDate(exp_date))
                except:
                    pass
            
            # Calcular margen
            self.calculate_margin()
            
        except Exception as e:
            logger.error(f"Error poblando campos: {e}")
            QMessageBox.warning(self, "Advertencia", f"Error cargando datos del producto: {str(e)}")
    
    def calculate_margin(self):
        """Calcular margen de ganancia"""
        try:
            purchase_price = self.purchase_price_input.value()
            sale_price = self.sale_price_input.value()
            
            if purchase_price > 0:
                margin = ((sale_price - purchase_price) / purchase_price) * 100
                self.margin_input.setValue(margin)
            else:
                self.margin_input.setValue(0)
        except:
            self.margin_input.setValue(0)
    
    def scan_barcode(self):
        """Simular escaneo de código de barras"""
        # En una implementación real, aquí se integraría con el scanner
        barcode, ok = QInputDialog.getText(
            self, "Escanear Código de Barras",
            "Escanee el código de barras o ingrese manualmente:"
        )
        
        if ok and barcode:
            self.barcode_input.setText(barcode)
    
    def add_new_provider(self):
        """Agregar nuevo proveedor"""
        # En implementación completa, abriría AddProviderDialog
        QMessageBox.information(self, "Función", "Diálogo de agregar proveedor - En desarrollo")
    
    def select_image(self):
        """Seleccionar imagen del producto"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Imagen del Producto",
            "", "Imágenes (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        
        if file_path:
            try:
                pixmap = QPixmap(file_path)
                scaled_pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_label.setPixmap(scaled_pixmap)
                self.image_path = file_path
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error cargando imagen: {str(e)}")
    
    def remove_image(self):
        """Quitar imagen del producto"""
        self.image_label.clear()
        self.image_label.setText("📷\nSin imagen")
        self.image_path = None
    
    def validate_form(self) -> Tuple[bool, str]:
        """Validar formulario"""
        # Validaciones obligatorias
        if not self.name_input.text().strip():
            return False, "El nombre del producto es obligatorio"
        
        if self.sale_price_input.value() <= 0:
            return False, "El precio de venta debe ser mayor a cero"
        
        # Validar código de barras único (si se proporciona)
        barcode = self.barcode_input.text().strip()
        if barcode:
            try:
                existing = self.product_manager.get_product_by_barcode(barcode)
                if existing and (not self.editing_mode or existing['id'] != self.product_data['id']):
                    return False, "Ya existe un producto con ese código de barras"
            except:
                pass
        
        return True, ""
    
    def save_product(self):
        """Guardar producto"""
        # Validar formulario
        valid, message = self.validate_form()
        if not valid:
            QMessageBox.warning(self, "Error de Validación", message)
            return
        
        try:
            # Recopilar datos del formulario
            product_data = {
                'codigo_barras': self.barcode_input.text().strip() or None,
                'codigo_interno': self.internal_code_input.text().strip() or None,
                'nombre': self.name_input.text().strip(),
                'descripcion': self.description_input.toPlainText().strip() or None,
                'categoria_id': self.category_combo.currentData(),
                'proveedor_id': self.provider_combo.currentData(),
                'unidad_medida': self.unit_combo.currentText(),
                'precio_compra': self.purchase_price_input.value(),
                'precio_venta': self.sale_price_input.value(),
                'precio_mayorista': self.wholesale_price_input.value(),
                'iva_porcentaje': self.iva_input.value(),
                'stock_actual': self.current_stock_input.value(),
                'stock_minimo': self.min_stock_input.value(),
                'stock_maximo': self.max_stock_input.value(),
                'ubicacion': self.location_input.text().strip() or None,
                'permite_venta_sin_stock': self.allow_negative_stock_cb.isChecked(),
                'es_pesable': self.is_weighable_cb.isChecked(),
                'es_produccion_propia': self.own_production_cb.isChecked(),
                'peso': self.weight_input.value() if self.weight_input.value() > 0 else None,
                'lote': self.batch_input.text().strip() or None,
                'codigo_plu': self.plu_input.text().strip() or None,
                'imagen_url': getattr(self, 'image_path', None)
            }
            
            # Fecha de vencimiento
            exp_date = self.expiry_date_input.date().toPyDate()
            if exp_date != QDate.currentDate().toPyDate():
                product_data['vencimiento'] = exp_date.isoformat()
            
            # Guardar producto
            if self.editing_mode:
                success, message = self.product_manager.update_product(
                    self.product_data['id'], product_data
                )
            else:
                success, message, product_id = self.product_manager.create_product(product_data)
            
            if success:
                QMessageBox.information(self, "Éxito", message)
                self.accept()
            else:
                QMessageBox.critical(self, "Error", message)
                
        except Exception as e:
            logger.error(f"Error guardando producto: {e}")
            QMessageBox.critical(self, "Error", f"Error guardando producto: {str(e)}")


class QuickAddProductDialog(QDialog):
    """Diálogo simplificado para agregar productos rápidamente"""
    
    def __init__(self, product_manager, parent=None):
        super().__init__(parent)
        self.product_manager = product_manager
        self.init_ui()
    
    def init_ui(self):
        """Inicializar interfaz simplificada"""
        self.setWindowTitle("Agregar Producto Rápido")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("Agregar Producto Rápido")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 15px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Formulario básico
        form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre del producto *")
        form_layout.addRow("Nombre *:", self.name_input)
        
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Código de barras")
        form_layout.addRow("Código de Barras:", self.barcode_input)
        
        self.price_input = QDoubleSpinBox()
        self.price_input.setMinimum(0.01)
        self.price_input.setMaximum(999999.99)
        self.price_input.setDecimals(2)
        self.price_input.setPrefix("$ ")
        form_layout.addRow("Precio de Venta *:", self.price_input)
        
        self.stock_input = QSpinBox()
        self.stock_input.setMinimum(0)
        self.stock_input.setMaximum(999999)
        form_layout.addRow("Stock Inicial:", self.stock_input)
        
        layout.addLayout(form_layout)
        
        # Nota
        note = QLabel("Nota: Podrá editar más detalles después desde la gestión de productos")
        note.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
        note.setWordWrap(True)
        layout.addWidget(note)
        
        # Botones
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Agregar Producto")
        save_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
        save_btn.clicked.connect(self.save_quick_product)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def save_quick_product(self):
        """Guardar producto con información básica"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Error", "El nombre del producto es obligatorio")
            return
        
        if self.price_input.value() <= 0:
            QMessageBox.warning(self, "Error", "El precio debe ser mayor a cero")
            return
        
        try:
            product_data = {
                'nombre': self.name_input.text().strip(),
                'codigo_barras': self.barcode_input.text().strip() or None,
                'precio_venta': self.price_input.value(),
                'stock_actual': self.stock_input.value(),
                'stock_minimo': 0,
                'iva_porcentaje': 21.0
            }
            
            success, message, product_id = self.product_manager.create_product(product_data)
            
            if success:
                QMessageBox.information(self, "Éxito", message)
                self.accept()
            else:
                QMessageBox.critical(self, "Error", message)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error creando producto: {str(e)}")