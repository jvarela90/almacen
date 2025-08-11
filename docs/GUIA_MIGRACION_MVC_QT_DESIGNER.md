# Guía Completa de Migración a MVC con Qt Designer y DBeaver

## Índice
1. [Análisis de Estructura Actual](#1-análisis-de-estructura-actual)
2. [Convenciones de Nombres para Widgets](#2-convenciones-de-nombres-para-widgets)
3. [Ejemplo Completo: Sales Widget](#3-ejemplo-completo-sales-widget)
4. [Arquitectura MVC Propuesta](#4-arquitectura-mvc-propuesta)
5. [Integración con DBeaver](#5-integración-con-dbeaver)
6. [Plan de Migración](#6-plan-de-migración)

---

## 1. Análisis de Estructura Actual

### Estructura Existente
```
almacen/
├── database/          # Modelos y gestor DB
├── managers/          # Lógica de negocio
├── ui/
│   ├── dialogs/       # Diálogos modales
│   ├── widgets/       # Widgets principales
│   └── main_window.py # Ventana principal
├── utils/             # Utilidades
└── config/            # Configuración
```

### Problemas Identificados
- **UI mezclada con lógica**: Los widgets contienen tanto interfaz como lógica de negocio
- **Código duplicado**: Estilos y comportamientos repetidos
- **Difícil mantenimiento**: Cambios de diseño requieren modificar código Python
- **Testing complejo**: Lógica acoplada a la UI

---

## 2. Convenciones de Nombres para Widgets

### Sistema de Nomenclatura Propuesto

#### Prefijos por Tipo de Widget
```python
# Botones
btnGuardar, btnCancelar, btnNuevo, btnEliminar, btnBuscar

# Campos de texto
lineEditNombre, lineEditPrecio, lineEditCodigo, lineEditEmail

# Campos de texto multilínea  
textEditDescripcion, textEditObservaciones, textEditComentarios

# Etiquetas
lblTitulo, lblTotal, lblSubtotal, lblEstado, lblFecha

# ComboBox
cmbCategoria, cmbEstado, cmbMetodoPago, cmbProveedor

# SpinBox y DoubleSpinBox
spinCantidad, spinStock, dspinPrecio, dspinDescuento

# CheckBox y RadioButton
chkActivo, chkVisible, rbEfectivo, rbTarjeta

# DateEdit y DateTimeEdit
dateInicio, dateFin, datetimeVenta, datetimeEntrega

# Tablas y Listas
tblProductos, tblVentas, tblClientes, lstCategorias

# Layouts y Contenedores
layoutPrincipal, frameHeader, groupDatos, scrollArea

# Progress y StatusBar
progressBar, statusBar, lblStatus

# Menús y Toolbars
menuArchivo, toolbarPrincipal, actionNuevo
```

#### Sufijos Descriptivos
```python
# Por función
btnGuardarCliente, btnEliminarProducto, btnBuscarVenta
lineEditNombreCliente, lineEditCodigoProducto

# Por contexto
tblProductosVenta, tblClientesActivos
cmbEstadoVenta, cmbCategoriaProducto

# Por posición/grupo
btnAceptarDialog, btnCancelarDialog
frameHeaderPrincipal, frameDatosCliente
```

### Convenciones de Señales y Slots
```python
# Señales personalizadas
cliente_seleccionado = pyqtSignal(dict)
venta_completada = pyqtSignal(int)
producto_agregado = pyqtSignal(dict)

# Slots estándar
def on_btnGuardar_clicked(self)
def on_lineEditBuscar_textChanged(self, text)
def on_tblProductos_itemSelectionChanged(self)
def on_cmbCategoria_currentTextChanged(self, text)
```

---

## 3. Ejemplo Completo: Sales Widget

### 3.1 Archivo .ui (sales_widget.ui)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>SalesWidget</class>
 <widget class="QWidget" name="SalesWidget">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>1200</width>
    <height>800</height>
   </rect>
  </property>
  <property name="windowTitle">
   <string>Punto de Venta</string>
  </property>
  <layout class="QHBoxLayout" name="layoutPrincipal">
   <property name="spacing">
    <number>10</number>
   </property>
   <property name="leftMargin">
    <number>10</number>
   </property>
   <property name="topMargin">
    <number>10</number>
   </property>
   <property name="rightMargin">
    <number>10</number>
   </property>
   <property name="bottomMargin">
    <number>10</number>
   </property>
   
   <!-- Panel Izquierdo: Scanner y Productos -->
   <item>
    <widget class="QWidget" name="framePanelIzquierdo">
     <layout class="QVBoxLayout" name="layoutPanelIzquierdo">
      
      <!-- Header -->
      <item>
       <widget class="QFrame" name="frameHeader">
        <property name="objectName">
         <string>sales_header</string>
        </property>
        <layout class="QHBoxLayout" name="layoutHeader">
         <item>
          <widget class="QLabel" name="lblTitulo">
           <property name="text">
            <string>🛒 Punto de Venta</string>
           </property>
           <property name="objectName">
            <string>sales_title</string>
           </property>
          </widget>
         </item>
         <item>
          <spacer name="spacerHeader">
           <property name="orientation">
            <enum>Qt::Horizontal</enum>
           </property>
           <property name="sizeHint" stdset="0">
            <size>
             <width>40</width>
             <height>20</height>
            </size>
           </property>
          </spacer>
         </item>
         <item>
          <widget class="QLabel" name="lblUsuario">
           <property name="objectName">
            <string>user_info</string>
           </property>
          </widget>
         </item>
        </layout>
       </widget>
      </item>
      
      <!-- Grupo Scanner -->
      <item>
       <widget class="QGroupBox" name="groupScanner">
        <property name="title">
         <string>Buscar Producto</string>
        </property>
        <layout class="QVBoxLayout" name="layoutScanner">
         <item>
          <layout class="QHBoxLayout" name="layoutBusqueda">
           <item>
            <widget class="QLineEdit" name="lineEditBuscarProducto">
             <property name="placeholderText">
              <string>Escanear código o buscar producto...</string>
             </property>
             <property name="objectName">
              <string>product_search</string>
             </property>
            </widget>
           </item>
           <item>
            <widget class="QPushButton" name="btnBuscar">
             <property name="text">
              <string>🔍</string>
             </property>
             <property name="toolTip">
              <string>Buscar producto</string>
             </property>
            </widget>
           </item>
           <item>
            <widget class="QPushButton" name="btnLimpiarBusqueda">
             <property name="text">
              <string>✖</string>
             </property>
             <property name="toolTip">
              <string>Limpiar búsqueda</string>
             </property>
            </widget>
           </item>
          </layout>
         </item>
        </layout>
       </widget>
      </item>
      
      <!-- Lista de Productos -->
      <item>
       <widget class="QGroupBox" name="groupProductos">
        <property name="title">
         <string>Productos Disponibles</string>
        </property>
        <layout class="QVBoxLayout" name="layoutProductos">
         <item>
          <widget class="QTableWidget" name="tblProductosDisponibles">
           <property name="alternatingRowColors">
            <bool>true</bool>
           </property>
           <property name="selectionBehavior">
            <enum>QAbstractItemView::SelectRows</enum>
           </property>
           <property name="sortingEnabled">
            <bool>true</bool>
           </property>
          </widget>
         </item>
         <item>
          <layout class="QHBoxLayout" name="layoutProductosAcciones">
           <item>
            <widget class="QPushButton" name="btnAgregarProducto">
             <property name="text">
              <string>➕ Agregar al Carrito</string>
             </property>
            </widget>
           </item>
           <item>
            <spacer name="spacerProductos">
             <property name="orientation">
              <enum>Qt::Horizontal</enum>
             </property>
            </spacer>
           </item>
           <item>
            <widget class="QSpinBox" name="spinCantidadAgregar">
             <property name="minimum">
              <number>1</number>
             </property>
             <property name="maximum">
              <number>999</number>
             </property>
             <property name="value">
              <number>1</number>
             </property>
            </widget>
           </item>
          </layout>
         </item>
        </layout>
       </widget>
      </item>
     </layout>
    </widget>
   </item>
   
   <!-- Panel Derecho: Carrito y Checkout -->
   <item>
    <widget class="QWidget" name="framePanelDerecho">
     <layout class="QVBoxLayout" name="layoutPanelDerecho">
      
      <!-- Cliente Seleccionado -->
      <item>
       <widget class="QGroupBox" name="groupCliente">
        <property name="title">
         <string>Cliente</string>
        </property>
        <layout class="QHBoxLayout" name="layoutCliente">
         <item>
          <widget class="QLabel" name="lblClienteNombre">
           <property name="text">
            <string>Cliente General</string>
           </property>
          </widget>
         </item>
         <item>
          <spacer name="spacerCliente">
           <property name="orientation">
            <enum>Qt::Horizontal</enum>
           </property>
          </spacer>
         </item>
         <item>
          <widget class="QPushButton" name="btnSeleccionarCliente">
           <property name="text">
            <string>👤 Seleccionar</string>
           </property>
          </widget>
         </item>
        </layout>
       </widget>
      </item>
      
      <!-- Carrito -->
      <item>
       <widget class="QGroupBox" name="groupCarrito">
        <property name="title">
         <string>Carrito de Compras</string>
        </property>
        <layout class="QVBoxLayout" name="layoutCarrito">
         <item>
          <widget class="QTableWidget" name="tblCarrito">
           <property name="alternatingRowColors">
            <bool>true</bool>
           </property>
           <property name="selectionBehavior">
            <enum>QAbstractItemView::SelectRows</enum>
           </property>
          </widget>
         </item>
         <item>
          <layout class="QHBoxLayout" name="layoutCarritoAcciones">
           <item>
            <widget class="QPushButton" name="btnEliminarDelCarrito">
             <property name="text">
              <string>🗑 Eliminar</string>
             </property>
            </widget>
           </item>
           <item>
            <widget class="QPushButton" name="btnLimpiarCarrito">
             <property name="text">
              <string>🧹 Limpiar Todo</string>
             </property>
            </widget>
           </item>
           <item>
            <spacer name="spacerCarritoAcciones">
             <property name="orientation">
              <enum>Qt::Horizontal</enum>
             </property>
            </spacer>
           </item>
          </layout>
         </item>
        </layout>
       </widget>
      </item>
      
      <!-- Totales -->
      <item>
       <widget class="QGroupBox" name="groupTotales">
        <property name="title">
         <string>Totales</string>
        </property>
        <layout class="QGridLayout" name="layoutTotales">
         <item row="0" column="0">
          <widget class="QLabel" name="lblSubtotalTexto">
           <property name="text">
            <string>Subtotal:</string>
           </property>
          </widget>
         </item>
         <item row="0" column="1">
          <widget class="QLabel" name="lblSubtotalValor">
           <property name="text">
            <string>$0.00</string>
           </property>
           <property name="alignment">
            <set>Qt::AlignRight|Qt::AlignTrailing|Qt::AlignVCenter</set>
           </property>
          </widget>
         </item>
         <item row="1" column="0">
          <widget class="QLabel" name="lblDescuentoTexto">
           <property name="text">
            <string>Descuento:</string>
           </property>
          </widget>
         </item>
         <item row="1" column="1">
          <widget class="QLabel" name="lblDescuentoValor">
           <property name="text">
            <string>$0.00</string>
           </property>
           <property name="alignment">
            <set>Qt::AlignRight|Qt::AlignTrailing|Qt::AlignVCenter</set>
           </property>
          </widget>
         </item>
         <item row="2" column="0">
          <widget class="QLabel" name="lblImpuestosTexto">
           <property name="text">
            <string>Impuestos:</string>
           </property>
          </widget>
         </item>
         <item row="2" column="1">
          <widget class="QLabel" name="lblImpuestosValor">
           <property name="text">
            <string>$0.00</string>
           </property>
           <property name="alignment">
            <set>Qt::AlignRight|Qt::AlignTrailing|Qt::AlignVCenter</set>
           </property>
          </widget>
         </item>
         <item row="3" column="0">
          <widget class="QLabel" name="lblTotalTexto">
           <property name="text">
            <string>TOTAL:</string>
           </property>
           <property name="styleSheet">
            <string>font-weight: bold; font-size: 14px;</string>
           </property>
          </widget>
         </item>
         <item row="3" column="1">
          <widget class="QLabel" name="lblTotalValor">
           <property name="text">
            <string>$0.00</string>
           </property>
           <property name="alignment">
            <set>Qt::AlignRight|Qt::AlignTrailing|Qt::AlignVCenter</set>
           </property>
           <property name="styleSheet">
            <string>font-weight: bold; font-size: 14px; color: #27ae60;</string>
           </property>
          </widget>
         </item>
        </layout>
       </widget>
      </item>
      
      <!-- Botones de Acción -->
      <item>
       <layout class="QVBoxLayout" name="layoutAccionesPrincipales">
        <item>
         <widget class="QPushButton" name="btnProcesarVenta">
          <property name="text">
           <string>💳 Procesar Venta</string>
          </property>
          <property name="styleSheet">
           <string>QPushButton { background-color: #27ae60; color: white; font-weight: bold; padding: 10px; }</string>
          </property>
         </widget>
        </item>
        <item>
         <layout class="QHBoxLayout" name="layoutAccionesSecundarias">
          <item>
           <widget class="QPushButton" name="btnGuardarCarrito">
            <property name="text">
             <string>💾 Guardar</string>
            </property>
           </widget>
          </item>
          <item>
           <widget class="QPushButton" name="btnCargarCarrito">
            <property name="text">
             <string>📁 Cargar</string>
            </property>
           </widget>
          </item>
          <item>
           <widget class="QPushButton" name="btnNuevaVenta">
            <property name="text">
             <string>🆕 Nueva Venta</string>
            </property>
           </widget>
          </item>
         </layout>
        </item>
       </layout>
      </item>
     </layout>
    </widget>
   </item>
  </layout>
 </widget>
 <resources/>
 <connections/>
</ui>
```

### 3.2 Controlador Adaptado (controllers/sales_controller.py)

```python
"""
Controlador de Ventas - AlmacénPro v2.0 MVC
Controlador que gestiona la interfaz de ventas usando Qt Designer
"""

import logging
import os
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional, Any
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import uic

# Importar modelos y managers
from models.sales_model import SalesModel
from managers.sales_manager import SalesManager
from managers.product_manager import ProductManager
from managers.customer_manager import CustomerManager
from models.entities import Product, Customer, SaleItem

logger = logging.getLogger(__name__)

class SalesController(QWidget):
    """Controlador principal para gestionar ventas (POS)"""
    
    # Señales de comunicación con otros componentes
    sale_completed = pyqtSignal(dict)
    product_added = pyqtSignal(dict)
    cart_updated = pyqtSignal()
    
    def __init__(self, managers: Dict, current_user: Dict, parent=None):
        super().__init__(parent)
        
        # Referencias a managers y modelo
        self.managers = managers
        self.current_user = current_user
        self.sales_manager = managers.get('sales')
        self.product_manager = managers.get('product')
        self.customer_manager = managers.get('customer')
        
        # Modelo de datos
        self.sales_model = SalesModel()
        
        # Estado del controlador
        self.current_customer = None
        self.cart_items = []
        
        # Cargar interfaz desde archivo .ui
        self.load_ui()
        
        # Configurar interfaz y conexiones
        self.setup_ui()
        self.connect_signals()
        self.setup_shortcuts()
        self.setup_auto_save()
        
        # Cargar datos iniciales
        self.load_initial_data()
    
    def load_ui(self):
        """Cargar interfaz desde archivo .ui"""
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'ui', 'forms', 'sales_widget.ui')
        
        if not os.path.exists(ui_path):
            raise FileNotFoundError(f"Archivo UI no encontrado: {ui_path}")
        
        # Cargar el archivo .ui
        uic.loadUi(ui_path, self)
        
        logger.info("Interfaz de ventas cargada exitosamente desde .ui")
    
    def setup_ui(self):
        """Configurar elementos de la interfaz"""
        # Configurar información del usuario
        self.lblUsuario.setText(f"Cajero: {self.current_user.get('nombre_completo', 'Usuario')}")
        
        # Configurar tablas
        self.setup_products_table()
        self.setup_cart_table()
        
        # Configurar validadores
        self.setup_validators()
        
        # Aplicar estilos
        self.apply_styles()
        
        # Estado inicial
        self.reset_form()
    
    def setup_products_table(self):
        """Configurar tabla de productos disponibles"""
        headers = ['Código', 'Nombre', 'Categoría', 'Precio', 'Stock', 'Descripción']
        self.tblProductosDisponibles.setColumnCount(len(headers))
        self.tblProductosDisponibles.setHorizontalHeaderLabels(headers)
        
        # Configurar columnas
        header = self.tblProductosDisponibles.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Código
        header.setSectionResizeMode(1, QHeaderView.Stretch)          # Nombre
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Categoría
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Precio
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # Stock
        
        # Configurar selección
        self.tblProductosDisponibles.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tblProductosDisponibles.setEditTriggers(QAbstractItemView.NoEditTriggers)
    
    def setup_cart_table(self):
        """Configurar tabla del carrito"""
        headers = ['Código', 'Producto', 'Cantidad', 'Precio Unit.', 'Subtotal', 'Acciones']
        self.tblCarrito.setColumnCount(len(headers))
        self.tblCarrito.setHorizontalHeaderLabels(headers)
        
        # Configurar columnas
        header = self.tblCarrito.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Código
        header.setSectionResizeMode(1, QHeaderView.Stretch)          # Producto
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Cantidad
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Precio Unit.
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # Subtotal
    
    def setup_validators(self):
        """Configurar validadores de entrada"""
        # Validador para cantidad
        quantity_validator = QIntValidator(1, 9999)
        self.spinCantidadAgregar.setValidator(quantity_validator)
    
    def connect_signals(self):
        """Conectar señales de la interfaz a los slots correspondientes"""
        # Búsqueda de productos
        self.lineEditBuscarProducto.textChanged.connect(self.on_search_products)
        self.lineEditBuscarProducto.returnPressed.connect(self.on_search_enter_pressed)
        self.btnBuscar.clicked.connect(self.on_search_clicked)
        self.btnLimpiarBusqueda.clicked.connect(self.on_clear_search)
        
        # Tabla de productos
        self.tblProductosDisponibles.itemSelectionChanged.connect(self.on_product_selected)
        self.tblProductosDisponibles.itemDoubleClicked.connect(self.on_add_product)
        
        # Carrito
        self.btnAgregarProducto.clicked.connect(self.on_add_product)
        self.btnEliminarDelCarrito.clicked.connect(self.on_remove_from_cart)
        self.btnLimpiarCarrito.clicked.connect(self.on_clear_cart)
        self.tblCarrito.itemSelectionChanged.connect(self.on_cart_item_selected)
        
        # Cliente
        self.btnSeleccionarCliente.clicked.connect(self.on_select_customer)
        
        # Acciones principales
        self.btnProcesarVenta.clicked.connect(self.on_process_sale)
        self.btnGuardarCarrito.clicked.connect(self.on_save_cart)
        self.btnCargarCarrito.clicked.connect(self.on_load_cart)
        self.btnNuevaVenta.clicked.connect(self.on_new_sale)
        
        # Señales del modelo
        self.sales_model.data_changed.connect(self.update_totals)
        self.sales_model.cart_updated.connect(self.refresh_cart_table)
    
    def setup_shortcuts(self):
        """Configurar atajos de teclado"""
        # F1 - Buscar producto
        QShortcut(QKeySequence("F1"), self, self.lineEditBuscarProducto.setFocus)
        
        # F2 - Agregar producto seleccionado
        QShortcut(QKeySequence("F2"), self, self.on_add_product)
        
        # F3 - Seleccionar cliente
        QShortcut(QKeySequence("F3"), self, self.on_select_customer)
        
        # F4 - Procesar venta
        QShortcut(QKeySequence("F4"), self, self.on_process_sale)
        
        # Ctrl+N - Nueva venta
        QShortcut(QKeySequence("Ctrl+N"), self, self.on_new_sale)
        
        # Ctrl+S - Guardar carrito
        QShortcut(QKeySequence("Ctrl+S"), self, self.on_save_cart)
        
        # Delete - Eliminar del carrito
        QShortcut(QKeySequence("Delete"), self, self.on_remove_from_cart)
        
        # Escape - Limpiar búsqueda
        QShortcut(QKeySequence("Escape"), self, self.on_clear_search)
    
    def setup_auto_save(self):
        """Configurar auto-guardado del carrito"""
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self.auto_save_cart)
        self.autosave_timer.start(30000)  # 30 segundos
    
    def apply_styles(self):
        """Aplicar estilos CSS a la interfaz"""
        style = """
        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 5px;
            margin: 5px;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 10px 0 10px;
        }
        
        QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #2980b9;
        }
        
        QPushButton:pressed {
            background-color: #21618c;
        }
        
        QTableWidget {
            border: 1px solid #ddd;
            border-radius: 4px;
            gridline-color: #f0f0f0;
        }
        
        QTableWidget::item {
            padding: 8px;
        }
        
        QTableWidget::item:selected {
            background-color: #3498db;
            color: white;
        }
        
        QLineEdit {
            border: 2px solid #ddd;
            border-radius: 4px;
            padding: 8px;
            font-size: 14px;
        }
        
        QLineEdit:focus {
            border-color: #3498db;
        }
        """
        
        self.setStyleSheet(style)
    
    # === SLOTS DE INTERFAZ ===
    
    @pyqtSlot(str)
    def on_search_products(self, text: str):
        """Buscar productos en tiempo real"""
        if len(text) >= 2:  # Buscar solo si hay al menos 2 caracteres
            self.search_products(text)
        elif not text:  # Si está vacío, mostrar todos
            self.load_all_products()
    
    @pyqtSlot()
    def on_search_enter_pressed(self):
        """Manejar Enter en búsqueda"""
        text = self.lineEditBuscarProducto.text().strip()
        if text:
            # Si hay productos en la tabla, agregar el primero
            if self.tblProductosDisponibles.rowCount() > 0:
                self.tblProductosDisponibles.selectRow(0)
                self.on_add_product()
    
    @pyqtSlot()
    def on_search_clicked(self):
        """Botón de búsqueda clickeado"""
        text = self.lineEditBuscarProducto.text().strip()
        if text:
            self.search_products(text)
    
    @pyqtSlot()
    def on_clear_search(self):
        """Limpiar búsqueda y mostrar todos los productos"""
        self.lineEditBuscarProducto.clear()
        self.load_all_products()
    
    @pyqtSlot()
    def on_product_selected(self):
        """Producto seleccionado en tabla"""
        selected_rows = self.tblProductosDisponibles.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        self.btnAgregarProducto.setEnabled(has_selection)
    
    @pyqtSlot()
    def on_add_product(self):
        """Agregar producto seleccionado al carrito"""
        try:
            current_row = self.tblProductosDisponibles.currentRow()
            if current_row < 0:
                QMessageBox.warning(self, "Advertencia", "Por favor, seleccione un producto.")
                return
            
            # Obtener datos del producto
            product_code = self.tblProductosDisponibles.item(current_row, 0).text()
            product_name = self.tblProductosDisponibles.item(current_row, 1).text()
            price_text = self.tblProductosDisponibles.item(current_row, 3).text().replace('$', '').replace(',', '')
            stock_text = self.tblProductosDisponibles.item(current_row, 4).text()
            
            # Validar datos
            try:
                price = float(price_text)
                stock = int(stock_text)
            except ValueError:
                QMessageBox.warning(self, "Error", "Error en los datos del producto.")
                return
            
            # Obtener cantidad a agregar
            quantity = self.spinCantidadAgregar.value()
            
            # Validar stock disponible
            if quantity > stock:
                QMessageBox.warning(self, "Stock Insuficiente", 
                                  f"Stock disponible: {stock}\\nCantidad solicitada: {quantity}")
                return
            
            # Crear item del carrito
            cart_item = {
                'code': product_code,
                'name': product_name,
                'price': price,
                'quantity': quantity,
                'subtotal': price * quantity
            }
            
            # Agregar al modelo
            self.sales_model.add_item_to_cart(cart_item)
            
            # Emitir señal
            self.product_added.emit(cart_item)
            
            # Limpiar búsqueda y resetear cantidad
            self.lineEditBuscarProducto.clear()
            self.spinCantidadAgregar.setValue(1)
            self.lineEditBuscarProducto.setFocus()
            
            logger.info(f"Producto agregado al carrito: {product_name} x{quantity}")
            
        except Exception as e:
            logger.error(f"Error agregando producto: {e}")
            QMessageBox.critical(self, "Error", f"Error agregando producto: {str(e)}")
    
    @pyqtSlot()
    def on_remove_from_cart(self):
        """Eliminar producto seleccionado del carrito"""
        try:
            current_row = self.tblCarrito.currentRow()
            if current_row < 0:
                QMessageBox.warning(self, "Advertencia", "Por favor, seleccione un item del carrito.")
                return
            
            # Confirmar eliminación
            product_name = self.tblCarrito.item(current_row, 1).text()
            reply = QMessageBox.question(self, "Confirmar", 
                                       f"¿Eliminar '{product_name}' del carrito?",
                                       QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # Eliminar del modelo
                self.sales_model.remove_item_from_cart(current_row)
                logger.info(f"Producto eliminado del carrito: {product_name}")
            
        except Exception as e:
            logger.error(f"Error eliminando producto del carrito: {e}")
            QMessageBox.critical(self, "Error", f"Error eliminando producto: {str(e)}")
    
    @pyqtSlot()
    def on_clear_cart(self):
        """Limpiar carrito completo"""
        if not self.sales_model.has_items():
            QMessageBox.information(self, "Información", "El carrito ya está vacío.")
            return
        
        reply = QMessageBox.question(self, "Confirmar", 
                                   "¿Está seguro que desea limpiar todo el carrito?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.sales_model.clear_cart()
            logger.info("Carrito limpiado")
    
    @pyqtSlot()
    def on_cart_item_selected(self):
        """Item del carrito seleccionado"""
        selected_rows = self.tblCarrito.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        self.btnEliminarDelCarrito.setEnabled(has_selection)
    
    @pyqtSlot()
    def on_select_customer(self):
        """Seleccionar cliente para la venta"""
        try:
            from ui.dialogs.customer_selector_dialog import CustomerSelectorDialog
            
            dialog = CustomerSelectorDialog(self.customer_manager, self)
            if dialog.exec_() == QDialog.Accepted:
                customer = dialog.get_selected_customer()
                if customer:
                    self.current_customer = customer
                    self.lblClienteNombre.setText(f"{customer.get('nombre', 'Cliente')}")
                    logger.info(f"Cliente seleccionado: {customer.get('nombre')}")
        
        except Exception as e:
            logger.error(f"Error seleccionando cliente: {e}")
            QMessageBox.critical(self, "Error", f"Error seleccionando cliente: {str(e)}")
    
    @pyqtSlot()
    def on_process_sale(self):
        """Procesar venta actual"""
        try:
            if not self.sales_model.has_items():
                QMessageBox.warning(self, "Carrito Vacío", "Agregue productos al carrito antes de procesar la venta.")
                return
            
            # Preparar datos de la venta
            sale_data = {
                'customer_id': self.current_customer.get('id') if self.current_customer else None,
                'items': self.sales_model.get_cart_items(),
                'subtotal': self.sales_model.get_subtotal(),
                'tax_amount': self.sales_model.get_tax_amount(),
                'discount_amount': self.sales_model.get_discount_amount(),
                'total_amount': self.sales_model.get_total(),
                'cashier_id': self.current_user.get('id'),
                'sale_date': datetime.now()
            }
            
            # Abrir diálogo de pago
            from ui.dialogs.payment_dialog import PaymentDialog
            
            payment_dialog = PaymentDialog(sale_data['total_amount'], self.current_customer, parent=self)
            if payment_dialog.exec_() == QDialog.Accepted:
                # Obtener información del pago
                payment_info = payment_dialog.get_payment_info()
                
                # Procesar venta en el manager
                sale_id = self.sales_manager.process_sale(sale_data, payment_info)
                
                if sale_id:
                    # Venta exitosa
                    QMessageBox.information(self, "Venta Procesada", 
                                          f"Venta #{sale_id} procesada exitosamente.")
                    
                    # Emitir señal
                    self.sale_completed.emit({'sale_id': sale_id, 'total': sale_data['total_amount']})
                    
                    # Preguntar si imprimir ticket
                    reply = QMessageBox.question(self, "Imprimir Ticket", 
                                               "¿Desea imprimir el ticket de venta?",
                                               QMessageBox.Yes | QMessageBox.No)
                    
                    if reply == QMessageBox.Yes:
                        self.print_ticket(sale_id)
                    
                    # Limpiar para nueva venta
                    self.on_new_sale()
                    
                else:
                    QMessageBox.critical(self, "Error", "Error procesando la venta. Intente nuevamente.")
        
        except Exception as e:
            logger.error(f"Error procesando venta: {e}")
            QMessageBox.critical(self, "Error", f"Error procesando venta: {str(e)}")
    
    @pyqtSlot()
    def on_save_cart(self):
        """Guardar carrito actual"""
        try:
            if not self.sales_model.has_items():
                QMessageBox.information(self, "Información", "El carrito está vacío.")
                return
            
            # Implementar guardado de carrito
            self.sales_model.save_cart(f"cart_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            QMessageBox.information(self, "Guardado", "Carrito guardado exitosamente.")
            
        except Exception as e:
            logger.error(f"Error guardando carrito: {e}")
            QMessageBox.critical(self, "Error", f"Error guardando carrito: {str(e)}")
    
    @pyqtSlot()
    def on_load_cart(self):
        """Cargar carrito guardado"""
        try:
            # Implementar carga de carrito
            # Por ahora, mostrar mensaje de funcionalidad pendiente
            QMessageBox.information(self, "Información", "Funcionalidad de carga de carrito en desarrollo.")
            
        except Exception as e:
            logger.error(f"Error cargando carrito: {e}")
            QMessageBox.critical(self, "Error", f"Error cargando carrito: {str(e)}")
    
    @pyqtSlot()
    def on_new_sale(self):
        """Iniciar nueva venta"""
        try:
            if self.sales_model.has_items():
                reply = QMessageBox.question(self, "Confirmar", 
                                           "¿Está seguro que desea iniciar una nueva venta?\\n"
                                           "Se perderán los datos del carrito actual.",
                                           QMessageBox.Yes | QMessageBox.No)
                
                if reply != QMessageBox.Yes:
                    return
            
            # Limpiar modelo y interfaz
            self.sales_model.clear_cart()
            self.current_customer = None
            self.reset_form()
            
            # Focus en búsqueda
            self.lineEditBuscarProducto.setFocus()
            
            logger.info("Nueva venta iniciada")
            
        except Exception as e:
            logger.error(f"Error iniciando nueva venta: {e}")
            QMessageBox.critical(self, "Error", f"Error iniciando nueva venta: {str(e)}")
    
    # === MÉTODOS DE APOYO ===
    
    def load_initial_data(self):
        """Cargar datos iniciales"""
        self.load_all_products()
    
    def load_all_products(self):
        """Cargar todos los productos disponibles"""
        try:
            products = self.product_manager.get_all_products()
            self.populate_products_table(products)
            
        except Exception as e:
            logger.error(f"Error cargando productos: {e}")
            QMessageBox.critical(self, "Error", f"Error cargando productos: {str(e)}")
    
    def search_products(self, search_term: str):
        """Buscar productos por término"""
        try:
            products = self.product_manager.search_products(search_term)
            self.populate_products_table(products)
            
        except Exception as e:
            logger.error(f"Error buscando productos: {e}")
            QMessageBox.critical(self, "Error", f"Error buscando productos: {str(e)}")
    
    def populate_products_table(self, products: List[Dict]):
        """Poblar tabla de productos"""
        self.tblProductosDisponibles.setRowCount(len(products))
        
        for row, product in enumerate(products):
            self.tblProductosDisponibles.setItem(row, 0, QTableWidgetItem(product.get('codigo', '')))
            self.tblProductosDisponibles.setItem(row, 1, QTableWidgetItem(product.get('nombre', '')))
            self.tblProductosDisponibles.setItem(row, 2, QTableWidgetItem(product.get('categoria', '')))
            self.tblProductosDisponibles.setItem(row, 3, QTableWidgetItem(f"${product.get('precio', 0):,.2f}"))
            self.tblProductosDisponibles.setItem(row, 4, QTableWidgetItem(str(product.get('stock', 0))))
            self.tblProductosDisponibles.setItem(row, 5, QTableWidgetItem(product.get('descripcion', '')))
        
        # Ajustar columnas
        self.tblProductosDisponibles.resizeColumnsToContents()
    
    @pyqtSlot()
    def refresh_cart_table(self):
        """Actualizar tabla del carrito"""
        cart_items = self.sales_model.get_cart_items()
        self.tblCarrito.setRowCount(len(cart_items))
        
        for row, item in enumerate(cart_items):
            self.tblCarrito.setItem(row, 0, QTableWidgetItem(item.get('code', '')))
            self.tblCarrito.setItem(row, 1, QTableWidgetItem(item.get('name', '')))
            self.tblCarrito.setItem(row, 2, QTableWidgetItem(str(item.get('quantity', 0))))
            self.tblCarrito.setItem(row, 3, QTableWidgetItem(f"${item.get('price', 0):,.2f}"))
            self.tblCarrito.setItem(row, 4, QTableWidgetItem(f"${item.get('subtotal', 0):,.2f}"))
            
            # Botón de eliminar
            btn_delete = QPushButton("🗑")
            btn_delete.setToolTip("Eliminar del carrito")
            btn_delete.clicked.connect(lambda checked, r=row: self.remove_cart_item(r))
            self.tblCarrito.setCellWidget(row, 5, btn_delete)
    
    @pyqtSlot()
    def update_totals(self):
        """Actualizar displays de totales"""
        subtotal = self.sales_model.get_subtotal()
        discount = self.sales_model.get_discount_amount()
        tax = self.sales_model.get_tax_amount()
        total = self.sales_model.get_total()
        
        self.lblSubtotalValor.setText(f"${subtotal:,.2f}")
        self.lblDescuentoValor.setText(f"${discount:,.2f}")
        self.lblImpuestosValor.setText(f"${tax:,.2f}")
        self.lblTotalValor.setText(f"${total:,.2f}")
        
        # Habilitar/deshabilitar botón de procesar venta
        self.btnProcesarVenta.setEnabled(total > 0)
    
    def reset_form(self):
        """Resetear formulario a estado inicial"""
        self.lblClienteNombre.setText("Cliente General")
        self.lineEditBuscarProducto.clear()
        self.spinCantidadAgregar.setValue(1)
        self.btnAgregarProducto.setEnabled(False)
        self.btnEliminarDelCarrito.setEnabled(False)
        self.update_totals()
    
    def remove_cart_item(self, row: int):
        """Eliminar item específico del carrito"""
        self.sales_model.remove_item_from_cart(row)
    
    def auto_save_cart(self):
        """Auto-guardar carrito cada cierto tiempo"""
        if self.sales_model.has_items():
            try:
                self.sales_model.auto_save_cart()
            except Exception as e:
                logger.warning(f"Error en auto-guardado: {e}")
    
    def print_ticket(self, sale_id: int):
        """Imprimir ticket de venta"""
        try:
            from utils.ticket_printer import TicketPrinter
            
            printer = TicketPrinter()
            sale_data = self.sales_manager.get_sale_details(sale_id)
            printer.print_sale_ticket(sale_data)
            
        except Exception as e:
            logger.error(f"Error imprimiendo ticket: {e}")
            QMessageBox.warning(self, "Error de Impresión", 
                              f"No se pudo imprimir el ticket: {str(e)}")
```

### 3.3 Modelo de Datos (models/sales_model.py)

```python
"""
Modelo de Ventas - AlmacénPro v2.0 MVC
Modelo que gestiona el estado y lógica de datos para ventas
"""

from PyQt5.QtCore import QObject, pyqtSignal
from typing import List, Dict, Optional
from decimal import Decimal
import json
import logging

logger = logging.getLogger(__name__)

class SalesModel(QObject):
    """Modelo de datos para el sistema de ventas"""
    
    # Señales para notificar cambios
    data_changed = pyqtSignal()
    cart_updated = pyqtSignal()
    customer_changed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        
        # Estado del carrito
        self._cart_items = []
        self._current_customer = None
        
        # Configuración de impuestos y descuentos
        self._tax_rate = 0.16  # 16% IVA
        self._discount_rate = 0.0
        
        # Totales calculados
        self._subtotal = Decimal('0.00')
        self._tax_amount = Decimal('0.00')
        self._discount_amount = Decimal('0.00')
        self._total = Decimal('0.00')
    
    # === PROPIEDADES ===
    
    @property
    def cart_items(self) -> List[Dict]:
        """Obtener items del carrito"""
        return self._cart_items.copy()
    
    @property
    def current_customer(self) -> Optional[Dict]:
        """Obtener cliente actual"""
        return self._current_customer
    
    @property
    def tax_rate(self) -> float:
        """Obtener tasa de impuestos"""
        return self._tax_rate
    
    @property
    def discount_rate(self) -> float:
        """Obtener tasa de descuento"""
        return self._discount_rate
    
    # === MÉTODOS PÚBLICOS ===
    
    def add_item_to_cart(self, item_data: Dict) -> bool:
        """Agregar item al carrito"""
        try:
            # Validar datos del item
            if not self._validate_cart_item(item_data):
                return False
            
            # Verificar si el producto ya está en el carrito
            existing_index = self._find_item_in_cart(item_data.get('code'))
            
            if existing_index is not None:
                # Actualizar cantidad del item existente
                existing_item = self._cart_items[existing_index]
                new_quantity = existing_item['quantity'] + item_data['quantity']
                existing_item['quantity'] = new_quantity
                existing_item['subtotal'] = existing_item['price'] * new_quantity
            else:
                # Agregar nuevo item
                cart_item = {
                    'code': item_data['code'],
                    'name': item_data['name'],
                    'price': Decimal(str(item_data['price'])),
                    'quantity': item_data['quantity'],
                    'subtotal': Decimal(str(item_data['price'])) * item_data['quantity']
                }
                self._cart_items.append(cart_item)
            
            # Recalcular totales
            self._calculate_totals()
            
            # Emitir señales
            self.cart_updated.emit()
            self.data_changed.emit()
            
            logger.debug(f"Item agregado al carrito: {item_data['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Error agregando item al carrito: {e}")
            return False
    
    def remove_item_from_cart(self, index: int) -> bool:
        """Eliminar item del carrito por índice"""
        try:
            if 0 <= index < len(self._cart_items):
                removed_item = self._cart_items.pop(index)
                
                # Recalcular totales
                self._calculate_totals()
                
                # Emitir señales
                self.cart_updated.emit()
                self.data_changed.emit()
                
                logger.debug(f"Item eliminado del carrito: {removed_item['name']}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error eliminando item del carrito: {e}")
            return False
    
    def update_item_quantity(self, index: int, new_quantity: int) -> bool:
        """Actualizar cantidad de un item"""
        try:
            if 0 <= index < len(self._cart_items) and new_quantity > 0:
                item = self._cart_items[index]
                item['quantity'] = new_quantity
                item['subtotal'] = item['price'] * new_quantity
                
                # Recalcular totales
                self._calculate_totals()
                
                # Emitir señales
                self.cart_updated.emit()
                self.data_changed.emit()
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error actualizando cantidad: {e}")
            return False
    
    def clear_cart(self):
        """Limpiar carrito completo"""
        self._cart_items.clear()
        self._calculate_totals()
        
        # Emitir señales
        self.cart_updated.emit()
        self.data_changed.emit()
        
        logger.debug("Carrito limpiado")
    
    def set_customer(self, customer_data: Optional[Dict]):
        """Establecer cliente actual"""
        self._current_customer = customer_data
        
        # Emitir señal
        if customer_data:
            self.customer_changed.emit(customer_data)
        
        logger.debug(f"Cliente establecido: {customer_data.get('name') if customer_data else 'None'}")
    
    def set_discount_rate(self, discount_rate: float):
        """Establecer tasa de descuento"""
        self._discount_rate = max(0.0, min(1.0, discount_rate))  # Entre 0 y 100%
        self._calculate_totals()
        
        # Emitir señal
        self.data_changed.emit()
    
    def apply_discount_amount(self, discount_amount: float):
        """Aplicar descuento por monto fijo"""
        if discount_amount >= 0 and discount_amount <= float(self._subtotal):
            self._discount_amount = Decimal(str(discount_amount))
            self._total = self._subtotal + self._tax_amount - self._discount_amount
            
            # Emitir señal
            self.data_changed.emit()
    
    # === MÉTODOS DE CONSULTA ===
    
    def has_items(self) -> bool:
        """Verificar si el carrito tiene items"""
        return len(self._cart_items) > 0
    
    def get_cart_items(self) -> List[Dict]:
        """Obtener copia de los items del carrito"""
        return [item.copy() for item in self._cart_items]
    
    def get_item_count(self) -> int:
        """Obtener número total de items en el carrito"""
        return sum(item['quantity'] for item in self._cart_items)
    
    def get_subtotal(self) -> float:
        """Obtener subtotal"""
        return float(self._subtotal)
    
    def get_tax_amount(self) -> float:
        """Obtener monto de impuestos"""
        return float(self._tax_amount)
    
    def get_discount_amount(self) -> float:
        """Obtener monto de descuento"""
        return float(self._discount_amount)
    
    def get_total(self) -> float:
        """Obtener total final"""
        return float(self._total)
    
    # === MÉTODOS DE PERSISTENCIA ===
    
    def save_cart(self, name: str) -> bool:
        """Guardar carrito actual"""
        try:
            cart_data = {
                'name': name,
                'items': self.get_cart_items(),
                'customer': self._current_customer,
                'discount_rate': self._discount_rate,
                'timestamp': str(datetime.now())
            }
            
            # Aquí implementarías la lógica de guardado
            # Por ejemplo, guardar en archivo JSON o base de datos
            
            return True
            
        except Exception as e:
            logger.error(f"Error guardando carrito: {e}")
            return False
    
    def load_cart(self, cart_data: Dict) -> bool:
        """Cargar carrito desde datos"""
        try:
            self._cart_items = cart_data.get('items', [])
            self._current_customer = cart_data.get('customer')
            self._discount_rate = cart_data.get('discount_rate', 0.0)
            
            # Recalcular totales
            self._calculate_totals()
            
            # Emitir señales
            self.cart_updated.emit()
            self.data_changed.emit()
            
            if self._current_customer:
                self.customer_changed.emit(self._current_customer)
            
            return True
            
        except Exception as e:
            logger.error(f"Error cargando carrito: {e}")
            return False
    
    def auto_save_cart(self):
        """Auto-guardar carrito"""
        if self.has_items():
            auto_save_name = f"auto_save_{datetime.now().strftime('%Y%m%d_%H%M')}"
            self.save_cart(auto_save_name)
    
    # === MÉTODOS PRIVADOS ===
    
    def _calculate_totals(self):
        """Calcular totales basado en items del carrito"""
        # Calcular subtotal
        self._subtotal = sum(item['subtotal'] for item in self._cart_items)
        
        # Calcular descuento
        if self._discount_rate > 0:
            self._discount_amount = self._subtotal * Decimal(str(self._discount_rate))
        else:
            # Mantener descuento fijo si se estableció manualmente
            pass
        
        # Calcular impuestos sobre (subtotal - descuento)
        taxable_amount = self._subtotal - self._discount_amount
        self._tax_amount = taxable_amount * Decimal(str(self._tax_rate))
        
        # Calcular total
        self._total = self._subtotal - self._discount_amount + self._tax_amount
        
        # Asegurar que no haya valores negativos
        self._total = max(self._total, Decimal('0.00'))
    
    def _validate_cart_item(self, item_data: Dict) -> bool:
        """Validar datos de item antes de agregar al carrito"""
        required_fields = ['code', 'name', 'price', 'quantity']
        
        for field in required_fields:
            if field not in item_data:
                logger.warning(f"Campo requerido faltante en item: {field}")
                return False
        
        # Validar tipos y valores
        try:
            price = float(item_data['price'])
            quantity = int(item_data['quantity'])
            
            if price < 0 or quantity <= 0:
                logger.warning("Precio o cantidad inválidos")
                return False
                
        except (ValueError, TypeError):
            logger.warning("Error de tipo en precio o cantidad")
            return False
        
        return True
    
    def _find_item_in_cart(self, product_code: str) -> Optional[int]:
        """Encontrar índice de item en carrito por código de producto"""
        for index, item in enumerate(self._cart_items):
            if item['code'] == product_code:
                return index
        return None
```

---

## 4. Arquitectura MVC Propuesta

### 4.1 Nueva Estructura de Directorios

```
almacen/
├── models/                    # MODELOS (M)
│   ├── __init__.py
│   ├── entities.py           # Entidades de dominio
│   ├── sales_model.py        # Modelo de ventas
│   ├── inventory_model.py    # Modelo de inventario
│   ├── customer_model.py     # Modelo de clientes
│   └── financial_model.py    # Modelo financiero
│
├── views/                    # VISTAS (V) - Solo archivos .ui
│   ├── forms/               # Formularios principales
│   │   ├── main_window.ui
│   │   ├── sales_widget.ui
│   │   ├── inventory_widget.ui
│   │   └── customer_widget.ui
│   ├── dialogs/             # Diálogos modales
│   │   ├── payment_dialog.ui
│   │   ├── product_dialog.ui
│   │   ├── customer_dialog.ui
│   │   └── report_dialog.ui
│   └── resources/           # Recursos (iconos, imágenes)
│       ├── icons/
│       └── images/
│
├── controllers/              # CONTROLADORES (C)
│   ├── __init__.py
│   ├── base_controller.py   # Controlador base
│   ├── main_controller.py   # Controlador principal
│   ├── sales_controller.py  # Controlador de ventas
│   ├── inventory_controller.py
│   ├── customer_controller.py
│   └── dialog_controllers/
│       ├── payment_controller.py
│       ├── product_controller.py
│       └── customer_controller.py
│
├── managers/                 # LÓGICA DE NEGOCIO
│   ├── (mantener estructura actual)
│   └── business_rules/      # Reglas de negocio específicas
│
├── database/                 # ACCESO A DATOS
│   ├── (mantener estructura actual)
│   └── repositories/        # Patrón Repository
│       ├── sales_repository.py
│       ├── product_repository.py
│       └── customer_repository.py
│
├── utils/                    # UTILIDADES
│   ├── (mantener estructura actual)
│   ├── ui_utils.py          # Utilidades para UI
│   └── style_manager.py     # Gestión de estilos
│
├── config/                   # CONFIGURACIÓN
│   └── (mantener estructura actual)
│
└── main.py                   # Punto de entrada
```

### 4.2 Flujo de Comunicación MVC

```python
# Ejemplo de flujo en venta de productos

# 1. USUARIO INTERACTÚA CON LA VISTA
# - Hace clic en "Agregar Producto"
# - El .ui emite señal btnAgregarProducto.clicked

# 2. CONTROLADOR MANEJA LA INTERACCIÓN  
# - sales_controller.on_add_product() recibe la señal
# - Obtiene datos de la vista
# - Valida entrada del usuario

# 3. CONTROLADOR ACTUALIZA EL MODELO
# - sales_model.add_item_to_cart(item_data)
# - El modelo actualiza su estado interno
# - Emite señal data_changed

# 4. VISTA SE ACTUALIZA AUTOMÁTICAMENTE
# - sales_controller.update_cart_display() se ejecuta
# - La vista refleja el nuevo estado del modelo
```

### 4.3 Controlador Base (controllers/base_controller.py)

```python
"""
Controlador Base - AlmacénPro v2.0 MVC
Clase base para todos los controladores con funcionalidad común
"""

import os
import logging
from abc import ABC, abstractmethod
from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5 import uic
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class BaseController(QWidget, ABC):
    """Clase base para controladores MVC"""
    
    def __init__(self, managers: Dict, current_user: Dict, parent=None):
        super().__init__(parent)
        
        # Referencias comunes
        self.managers = managers
        self.current_user = current_user
        self.parent_window = parent
        
        # Estado del controlador
        self.is_initialized = False
        self.ui_loaded = False
        
        # Setup común
        self.setup_logging()
    
    def setup_logging(self):
        """Configurar logging específico del controlador"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def get_ui_file_path(self) -> str:
        """Retornar ruta al archivo .ui correspondiente"""
        pass
    
    def load_ui(self):
        """Cargar interfaz desde archivo .ui"""
        try:
            ui_path = self.get_ui_file_path()
            
            if not os.path.exists(ui_path):
                raise FileNotFoundError(f"Archivo UI no encontrado: {ui_path}")
            
            uic.loadUi(ui_path, self)
            self.ui_loaded = True
            
            self.logger.info(f"UI cargada exitosamente: {os.path.basename(ui_path)}")
            
        except Exception as e:
            self.logger.error(f"Error cargando UI: {e}")
            self.show_error("Error de Inicialización", f"No se pudo cargar la interfaz: {str(e)}")
            raise
    
    def initialize(self):
        """Método de inicialización completo"""
        try:
            # Cargar UI
            self.load_ui()
            
            # Setup específico del controlador
            self.setup_ui()
            self.connect_signals()
            self.setup_shortcuts()
            self.apply_styles()
            
            # Cargar datos iniciales
            self.load_initial_data()
            
            self.is_initialized = True
            self.logger.info(f"Controlador {self.__class__.__name__} inicializado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error en inicialización: {e}")
            raise
    
    @abstractmethod
    def setup_ui(self):
        """Configurar elementos específicos de la UI"""
        pass
    
    @abstractmethod
    def connect_signals(self):
        """Conectar señales específicas del controlador"""
        pass
    
    def setup_shortcuts(self):
        """Configurar atajos de teclado (puede ser sobrescrito)"""
        pass
    
    def apply_styles(self):
        """Aplicar estilos CSS (puede ser sobrescrito)"""
        from utils.style_manager import StyleManager
        StyleManager.apply_default_styles(self)
    
    def load_initial_data(self):
        """Cargar datos iniciales (puede ser sobrescrito)"""
        pass
    
    # === MÉTODOS DE UTILIDAD COMUNES ===
    
    def show_info(self, title: str, message: str):
        """Mostrar mensaje informativo"""
        QMessageBox.information(self, title, message)
    
    def show_warning(self, title: str, message: str):
        """Mostrar mensaje de advertencia"""
        QMessageBox.warning(self, title, message)
    
    def show_error(self, title: str, message: str):
        """Mostrar mensaje de error"""
        QMessageBox.critical(self, title, message)
    
    def show_question(self, title: str, message: str) -> bool:
        """Mostrar pregunta de confirmación"""
        reply = QMessageBox.question(self, title, message, 
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        return reply == QMessageBox.Yes
    
    def validate_required_fields(self, fields: Dict[str, Any]) -> bool:
        """Validar campos requeridos"""
        missing_fields = []
        
        for field_name, field_value in fields.items():
            if not field_value or (isinstance(field_value, str) and not field_value.strip()):
                missing_fields.append(field_name)
        
        if missing_fields:
            fields_text = ", ".join(missing_fields)
            self.show_warning("Campos Requeridos", 
                            f"Por favor complete los siguientes campos: {fields_text}")
            return False
        
        return True
    
    def safe_float_conversion(self, value: str, default: float = 0.0) -> float:
        """Conversión segura a float"""
        try:
            return float(value.replace('$', '').replace(',', ''))
        except (ValueError, AttributeError):
            return default
    
    def safe_int_conversion(self, value: str, default: int = 0) -> int:
        """Conversión segura a int"""
        try:
            return int(value)
        except (ValueError, AttributeError):
            return default
    
    def format_currency(self, amount: float) -> str:
        """Formatear monto como moneda"""
        return f"${amount:,.2f}"
    
    def format_date(self, date_obj, format_str: str = "%d/%m/%Y") -> str:
        """Formatear fecha"""
        try:
            return date_obj.strftime(format_str)
        except AttributeError:
            return str(date_obj)
    
    # === MANEJO DE ESTADO ===
    
    def save_state(self) -> Dict[str, Any]:
        """Guardar estado actual del controlador (para sobrescribir)"""
        return {}
    
    def restore_state(self, state: Dict[str, Any]):
        """Restaurar estado del controlador (para sobrescribir)"""
        pass
    
    def reset_form(self):
        """Resetear formulario a estado inicial (para sobrescribir)"""
        pass
    
    # === CLEANUP ===
    
    def cleanup(self):
        """Limpiar recursos antes de cerrar (para sobrescribir)"""
        self.logger.info(f"Limpiando controlador {self.__class__.__name__}")
    
    def closeEvent(self, event):
        """Manejar evento de cierre"""
        try:
            self.cleanup()
            event.accept()
        except Exception as e:
            self.logger.error(f"Error en cleanup: {e}")
            event.accept()
```

---

## 5. Integración con DBeaver

### 5.1 Configuración Inicial

#### Paso 1: Instalación y Configuración
```bash
# 1. Descargar DBeaver Community desde: https://dbeaver.io/download/
# 2. Instalar siguiendo las instrucciones del sistema operativo
# 3. Ejecutar DBeaver
```

#### Paso 2: Conexión a la Base de Datos
1. **Crear Nueva Conexión**
   - Clic en "Nueva Conexión" o `Ctrl+Shift+N`
   - Seleccionar "SQLite"
   - Configurar parámetros:

```
Tipo: SQLite
Ruta de Base de Datos: F:\almacen\data\almacen_pro.db
Nombre de Conexión: AlmacénPro Local
Usuario: (vacío para SQLite)
Contraseña: (vacío para SQLite)
```

2. **Probar Conexión**
   - Clic en "Test Connection"
   - Si falla, verificar que el archivo .db existe
   - Confirmar permisos de lectura/escritura

#### Paso 3: Configuración de Proyecto
```
Workspace: F:\almacen\database\
Proyecto DBeaver: AlmacenPro_DB
Scripts SQL: F:\almacen\database\scripts\
```

### 5.2 Gestión del Schema de Base de Datos

#### Estructura Recomendada en DBeaver
```
AlmacénPro/
├── Scripts/
│   ├── 01_schema_creation.sql      # Creación de tablas
│   ├── 02_initial_data.sql         # Datos iniciales
│   ├── 03_indexes.sql              # Índices de rendimiento
│   ├── 04_triggers.sql             # Triggers de auditoría
│   ├── 05_views.sql                # Vistas útiles
│   └── migrations/                 # Scripts de migración
│       ├── 2024_01_add_predictive_tables.sql
│       └── 2024_02_add_crm_fields.sql
├── Diagrams/
│   └── almacen_er_diagram.erd      # Diagrama ER
├── Documentation/
│   ├── table_descriptions.md
│   └── business_rules.md
└── Backups/
    ├── daily/
    └── weekly/
```

#### Exportar Schema Actual
```sql
-- Script para documentar schema actual
.output F:\almacen\database\docs\current_schema.sql
.schema

-- Exportar datos de configuración crítica
.mode insert usuarios
SELECT * FROM usuarios;

.mode insert roles  
SELECT * FROM roles;

.mode insert configuraciones
SELECT * FROM configuraciones;
```

### 5.3 Diagrama Entity-Relationship

#### Crear Diagrama en DBeaver
1. **Nuevo Diagrama ER**
   - Clic derecho en conexión → "Create" → "ER Diagram"
   - Nombre: `AlmacenPro_ER_Diagram`

2. **Configurar Visualización**
```sql
-- Agregar todas las tablas principales
-- DBeaver detectará automáticamente las relaciones basadas en FOREIGN KEYs

-- Tablas principales a incluir:
- usuarios
- roles  
- clientes
- productos
- categorias
- proveedores
- ventas
- detalles_venta
- compras
- detalles_compra
- inventario
- movimientos_inventario
- pagos
- facturas
- configuraciones
- auditoria
```

3. **Personalizar Layout**
   - Agrupar tablas por dominio (Usuarios, Productos, Ventas, etc.)
   - Usar colores para diferenciar módulos
   - Agregar notas explicativas

### 5.4 Queries de Análisis y Mantenimiento

#### Dashboard SQL para DBeaver
```sql
-- F:\almacen\database\scripts\dashboard_queries.sql

-- ============================================================================
-- DASHBOARD DE MONITOREO - ALMACÉN PRO
-- ============================================================================

-- 1. RESUMEN GENERAL DEL SISTEMA
SELECT 
    'Usuarios Activos' as Metrica,
    COUNT(*) as Valor
FROM usuarios 
WHERE activo = 1
UNION ALL
SELECT 
    'Productos en Catálogo',
    COUNT(*) 
FROM productos
UNION ALL
SELECT 
    'Clientes Registrados',
    COUNT(*) 
FROM clientes
UNION ALL
SELECT 
    'Ventas Este Mes',
    COUNT(*) 
FROM ventas 
WHERE fecha_venta >= date('now', 'start of month');

-- 2. ANÁLISIS DE VENTAS DIARIAS
SELECT 
    DATE(fecha_venta) as Fecha,
    COUNT(*) as NumVentas,
    ROUND(SUM(total), 2) as TotalVentas,
    ROUND(AVG(total), 2) as PromedioVenta
FROM ventas 
WHERE fecha_venta >= date('now', '-30 days')
GROUP BY DATE(fecha_venta)
ORDER BY Fecha DESC;

-- 3. PRODUCTOS CON STOCK BAJO
SELECT 
    p.codigo,
    p.nombre,
    p.stock_actual,
    p.stock_minimo,
    (p.stock_minimo - p.stock_actual) as FaltanteStock,
    c.nombre as Categoria
FROM productos p
JOIN categorias c ON p.categoria_id = c.id
WHERE p.stock_actual <= p.stock_minimo
ORDER BY FaltanteStock DESC;

-- 4. CLIENTES MÁS ACTIVOS
SELECT 
    cl.nombre,
    cl.email,
    COUNT(v.id) as NumCompras,
    ROUND(SUM(v.total), 2) as TotalGastado,
    ROUND(AVG(v.total), 2) as PromedioCompra,
    MAX(v.fecha_venta) as UltimaCompra
FROM clientes cl
JOIN ventas v ON cl.id = v.cliente_id
WHERE v.fecha_venta >= date('now', '-90 days')
GROUP BY cl.id
ORDER BY TotalGastado DESC
LIMIT 10;

-- 5. INTEGRIDAD REFERENCIAL
SELECT 
    'Ventas sin Cliente' as Problema,
    COUNT(*) as Cantidad
FROM ventas v
LEFT JOIN clientes c ON v.cliente_id = c.id
WHERE v.cliente_id IS NOT NULL AND c.id IS NULL
UNION ALL
SELECT 
    'Productos sin Categoría',
    COUNT(*) 
FROM productos p
LEFT JOIN categorias c ON p.categoria_id = c.id
WHERE c.id IS NULL
UNION ALL
SELECT 
    'Detalles Venta Huérfanos',
    COUNT(*) 
FROM detalles_venta dv
LEFT JOIN ventas v ON dv.venta_id = v.id
WHERE v.id IS NULL;

-- 6. ANÁLISIS DE RENDIMIENTO
EXPLAIN QUERY PLAN 
SELECT v.*, cl.nombre as cliente_nombre
FROM ventas v
JOIN clientes cl ON v.cliente_id = cl.id
WHERE v.fecha_venta >= date('now', '-7 days');
```

#### Scripts de Mantenimiento
```sql
-- F:\almacen\database\scripts\maintenance.sql

-- VACUUM para optimizar base de datos
VACUUM;

-- Reindexar tablas principales
REINDEX ventas;
REINDEX productos;
REINDEX clientes;

-- Estadísticas de tablas
SELECT 
    name as Tabla,
    type as Tipo,
    sql
FROM sqlite_master 
WHERE type IN ('table', 'index')
ORDER BY name;

-- Análisis de tamaño de base de datos
SELECT 
    name as Tabla,
    COUNT(*) as NumRegistros
FROM (
    SELECT 'usuarios' as name FROM usuarios
    UNION ALL SELECT 'clientes' FROM clientes  
    UNION ALL SELECT 'productos' FROM productos
    UNION ALL SELECT 'ventas' FROM ventas
    UNION ALL SELECT 'detalles_venta' FROM detalles_venta
) 
GROUP BY name;
```

### 5.5 Sincronización con Código Python

#### Configuración de Auto-sync
```python
# utils/database_sync.py

"""
Sincronizador de Base de Datos - DBeaver Integration
Mantiene sincronizadas las definiciones entre DBeaver y el código Python
"""

import sqlite3
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class DatabaseSynchronizer:
    """Sincronizador entre DBeaver y aplicación Python"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.scripts_path = os.path.join(os.path.dirname(db_path), 'scripts')
        self.ensure_scripts_directory()
    
    def ensure_scripts_directory(self):
        """Crear directorio de scripts si no existe"""
        os.makedirs(self.scripts_path, exist_ok=True)
    
    def export_schema_to_dbeaver(self):
        """Exportar schema actual para uso en DBeaver"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Obtener todas las tablas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            # Crear script de schema
            schema_script = self._generate_schema_script(cursor, tables)
            
            # Guardar script
            script_path = os.path.join(self.scripts_path, 'current_schema.sql')
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(schema_script)
            
            conn.close()
            logger.info(f"Schema exportado a: {script_path}")
            
        except Exception as e:
            logger.error(f"Error exportando schema: {e}")
            raise
    
    def _generate_schema_script(self, cursor, tables) -> str:
        """Generar script SQL del schema"""
        script_parts = [
            f"-- Schema de AlmacénPro generado automáticamente",
            f"-- Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"-- Base de datos: {os.path.basename(self.db_path)}",
            "",
            "-- ============================================================================",
            "-- CREACIÓN DE TABLAS",
            "-- ============================================================================",
            ""
        ]
        
        for (table_name,) in tables:
            # Obtener DDL de la tabla
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';")
            ddl = cursor.fetchone()
            
            if ddl and ddl[0]:
                script_parts.extend([
                    f"-- Tabla: {table_name}",
                    ddl[0] + ";",
                    ""
                ])
        
        # Agregar índices
        script_parts.extend([
            "-- ============================================================================", 
            "-- ÍNDICES",
            "-- ============================================================================",
            ""
        ])
        
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL;")
        indexes = cursor.fetchall()
        
        for (index_sql,) in indexes:
            script_parts.append(index_sql + ";")
        
        return "\n".join(script_parts)
    
    def validate_schema_consistency(self) -> Dict[str, List[str]]:
        """Validar consistencia entre código Python y base de datos"""
        issues = {
            'missing_tables': [],
            'extra_columns': [],
            'missing_columns': [],
            'type_mismatches': []
        }
        
        try:
            # Obtener esquema de la base de datos
            db_schema = self._get_database_schema()
            
            # Obtener esquema esperado del código Python
            expected_schema = self._get_expected_schema()
            
            # Comparar esquemas
            for table_name, expected_columns in expected_schema.items():
                if table_name not in db_schema:
                    issues['missing_tables'].append(table_name)
                    continue
                
                db_columns = db_schema[table_name]
                
                # Verificar columnas
                for col_name, col_info in expected_columns.items():
                    if col_name not in db_columns:
                        issues['missing_columns'].append(f"{table_name}.{col_name}")
                
                for col_name, col_info in db_columns.items():
                    if col_name not in expected_columns:
                        issues['extra_columns'].append(f"{table_name}.{col_name}")
            
            return issues
            
        except Exception as e:
            logger.error(f"Error validando consistencia: {e}")
            return issues
    
    def _get_database_schema(self) -> Dict[str, Dict[str, str]]:
        """Obtener esquema actual de la base de datos"""
        schema = {}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Obtener todas las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for (table_name,) in tables:
            # Obtener información de columnas
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            schema[table_name] = {}
            for col_info in columns:
                col_name = col_info[1]
                col_type = col_info[2]
                schema[table_name][col_name] = col_type
        
        conn.close()
        return schema
    
    def _get_expected_schema(self) -> Dict[str, Dict[str, str]]:
        """Obtener esquema esperado desde el código Python"""
        # Esta función debería extraer el esquema desde database/manager.py
        # Por ahora, retorno un esquema básico como ejemplo
        
        return {
            'usuarios': {
                'id': 'INTEGER',
                'username': 'VARCHAR(50)',
                'password_hash': 'VARCHAR(255)',
                'email': 'VARCHAR(100)',
                'nombre_completo': 'VARCHAR(100)',
                'activo': 'BOOLEAN'
            },
            'productos': {
                'id': 'INTEGER',
                'codigo': 'VARCHAR(50)',
                'nombre': 'VARCHAR(200)',
                'precio': 'DECIMAL(10,2)',
                'stock_actual': 'INTEGER',
                'activo': 'BOOLEAN'
            }
            # ... más tablas
        }
    
    def generate_migration_script(self, changes: Dict[str, List[str]]) -> str:
        """Generar script de migración basado en cambios detectados"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        script_name = f"migration_{timestamp}.sql"
        
        script_parts = [
            f"-- Migración automática generada: {timestamp}",
            f"-- Cambios detectados en esquema",
            "",
            "BEGIN TRANSACTION;",
            ""
        ]
        
        # Agregar tablas faltantes
        for table in changes.get('missing_tables', []):
            script_parts.append(f"-- TODO: Crear tabla {table}")
            script_parts.append(f"-- CREATE TABLE {table} (...);")
            script_parts.append("")
        
        # Agregar columnas faltantes
        for column in changes.get('missing_columns', []):
            table, col = column.split('.')
            script_parts.append(f"-- TODO: Agregar columna {col} a tabla {table}")
            script_parts.append(f"-- ALTER TABLE {table} ADD COLUMN {col} TYPE DEFAULT_VALUE;")
            script_parts.append("")
        
        script_parts.extend([
            "COMMIT;",
            "",
            "-- Ejecutar análisis después de cambios",
            "ANALYZE;"
        ])
        
        # Guardar script
        script_path = os.path.join(self.scripts_path, 'migrations', script_name)
        os.makedirs(os.path.dirname(script_path), exist_ok=True)
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(script_parts))
        
        logger.info(f"Script de migración generado: {script_path}")
        return script_path
```

---

## 6. Plan de Migración

### Fase 1: Preparación (1-2 días)
1. **Instalar herramientas**
   - Qt Designer
   - DBeaver Community
   - Configurar entorno de desarrollo

2. **Crear estructura MVC**
   - Crear directorios: `models/`, `views/`, `controllers/`
   - Mover archivos existentes manteniendo funcionalidad
   - Crear `base_controller.py`

3. **Configurar DBeaver**
   - Conectar a base de datos actual
   - Crear diagrama ER
   - Exportar schema documentado

### Fase 2: Migración de Módulo Piloto (3-4 días)
1. **Seleccionar módulo simple** (ej: Configuraciones)
   - Convertir interfaz manual a .ui
   - Crear controlador correspondiente
   - Implementar modelo si es necesario
   - Probar funcionalidad completa

2. **Documentar proceso**
   - Crear checklist de migración
   - Documentar problemas encontrados
   - Refinar convenciones de nombres

### Fase 3: Migración de Módulos Principales (1-2 semanas)
1. **Migrar en orden de complejidad**:
   - Productos/Inventario
   - Clientes/CRM  
   - Ventas/POS
   - Reportes/Análisis

2. **Para cada módulo**:
   - Diseñar .ui en Qt Designer
   - Implementar controlador
   - Migrar lógica desde widgets existentes
   - Crear/actualizar modelo de datos
   - Testing funcional completo

### Fase 4: Integración y Optimización (3-5 días)
1. **Integrar todos los módulos**
   - Actualizar `main.py` y `main_window`
   - Verificar comunicación entre controladores
   - Testing de integración

2. **Optimizaciones**
   - Aplicar estilos CSS unificados
   - Optimizar carga de interfaces
   - Mejorar rendimiento

### Fase 5: Finalización (1-2 días)
1. **Documentación final**
   - Manual de mantenimiento
   - Guía para desarrolladores futuros
   - Documentación de base de datos

2. **Testing final y deployment**
   - Testing completo del sistema
   - Backup de versión anterior
   - Deploy de nueva versión

### Checklist de Migración por Módulo

#### Pre-migración
- [ ] Analizar widget/diálogo existente
- [ ] Identificar componentes UI y lógica
- [ ] Documentar señales y slots actuales
- [ ] Identificar dependencias

#### Diseño .ui
- [ ] Crear archivo .ui en Qt Designer  
- [ ] Aplicar convenciones de nombres
- [ ] Configurar layouts y propiedades
- [ ] Agregar tooltips y accesibilidad

#### Implementación Controlador
- [ ] Crear clase controlador heredando de BaseController
- [ ] Implementar métodos abstractos requeridos
- [ ] Migrar lógica de eventos desde widget original
- [ ] Conectar señales usando convenciones

#### Modelo de Datos (si aplica)
- [ ] Crear/actualizar modelo correspondiente
- [ ] Implementar señales de cambio de datos
- [ ] Migrar estado desde widget original

#### Testing
- [ ] Verificar carga de interfaz
- [ ] Testing de funcionalidad básica
- [ ] Testing de señales y eventos
- [ ] Verificar integración con otros módulos
- [ ] Testing de casos edge

#### Documentación
- [ ] Comentar código nuevo
- [ ] Actualizar diagramas si es necesario
- [ ] Documentar cambios en base de datos
- [ ] Actualizar manual de usuario si aplica

### Comandos Útiles

#### Generar archivo .py desde .ui (opcional, para referencia)
```bash
pyuic5 -x views/forms/sales_widget.ui -o temp_sales_widget_reference.py
```

#### Verificar recursos Qt
```bash
pyrcc5 views/resources/resources.qrc -o resources_rc.py
```

#### Backup antes de migración
```bash
# Crear backup completo antes de cada fase
cp -r almacen/ almacen_backup_$(date +%Y%m%d_%H%M%S)/
```

---

## Consideraciones Adicionales

### Ventajas de esta Migración
- **Diseño Visual**: Interfaces editables en Qt Designer
- **Separación Clara**: Lógica separada de presentación
- **Mantenibilidad**: Código más organizado y fácil de mantener
- **Escalabilidad**: Arquitectura preparada para crecimiento
- **Gestión DB**: DBeaver facilita administración de base de datos

### Posibles Desafíos
- **Tiempo de Migración**: Proceso puede tomar 2-3 semanas
- **Curva de Aprendizaje**: Equipo debe familiarizarse con MVC
- **Testing Extensivo**: Verificar que funcionalidad se mantiene
- **Compatibilidad**: Asegurar que .ui funciona en diferentes versiones Qt

### Recomendaciones Finales
1. **Migración Gradual**: No migrar todo a la vez
2. **Backup Frecuente**: Mantener versiones funcionales
3. **Testing Continuo**: Probar cada módulo migrado
4. **Documentación Activa**: Documentar mientras se migra
5. **Capacitación**: Entrenar equipo en nuevas herramientas

Esta guía proporciona una base sólida para la migración completa a una arquitectura MVC profesional con Qt Designer y DBeaver, manteniendo la funcionalidad existente mientras se mejora significativamente la mantenibilidad y escalabilidad del sistema.