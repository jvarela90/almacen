#!/usr/bin/env python3
"""
Generador Automático de Archivos .ui - AlmacénPro v2.0
Genera archivos .ui faltantes basándose en los archivos Python existentes
"""

import os
from pathlib import Path

def generate_ui_template(widget_name: str, title: str, size_width: int = 800, size_height: int = 600) -> str:
    """Generar template básico de archivo .ui"""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>{widget_name}</class>
 <widget class="QWidget" name="{widget_name}">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>{size_width}</width>
    <height>{size_height}</height>
   </rect>
  </property>
  <property name="windowTitle">
   <string>{title}</string>
  </property>
  <layout class="QVBoxLayout" name="mainLayout">
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
   
   <!-- Header -->
   <item>
    <layout class="QHBoxLayout" name="headerLayout">
     <property name="spacing">
      <number>10</number>
     </property>
     <item>
      <widget class="QLabel" name="lblTitle">
       <property name="text">
        <string>{title}</string>
       </property>
       <property name="styleSheet">
        <string>font-size: 18px; font-weight: bold; color: #2c3e50;</string>
       </property>
      </widget>
     </item>
     <item>
      <spacer name="headerSpacer">
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
    </layout>
   </item>
   
   <!-- Main Content Area -->
   <item>
    <widget class="QFrame" name="frameMainContent">
     <property name="frameShape">
      <enum>QFrame::StyledPanel</enum>
     </property>
     <property name="frameShadow">
      <enum>QFrame::Raised</enum>
     </property>
     <property name="styleSheet">
      <string>
       QFrame#frameMainContent {{
        background-color: white;
        border: 1px solid #dee2e6;
        border-radius: 6px;
       }}
      </string>
     </property>
     <layout class="QVBoxLayout" name="contentLayout">
      <property name="spacing">
       <number>10</number>
      </property>
      <property name="leftMargin">
       <number>15</number>
      </property>
      <property name="topMargin">
       <number>15</number>
      </property>
      <property name="rightMargin">
       <number>15</number>
      </property>
      <property name="bottomMargin">
       <number>15</number>
      </property>
      
      <!-- Placeholder Content -->
      <item>
       <widget class="QLabel" name="lblPlaceholder">
        <property name="text">
         <string>🚧 Contenido de {title}
         
Interfaz en desarrollo.
Migrar funcionalidad desde archivo Python correspondiente.</string>
        </property>
        <property name="alignment">
         <set>Qt::AlignCenter</set>
        </property>
        <property name="styleSheet">
         <string>
          QLabel {{
           color: #7f8c8d;
           font-size: 14px;
           border: 2px dashed #bdc3c7;
           border-radius: 6px;
           background-color: #f8f9fa;
           padding: 40px;
          }}
         </string>
        </property>
       </widget>
      </item>
     </layout>
    </widget>
   </item>
  </layout>
 </widget>
 
 <resources/>
 <connections/>
</ui>'''

def generate_dialog_template(dialog_name: str, title: str, width: int = 500, height: int = 400) -> str:
    """Generar template básico para diálogos"""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>{dialog_name}</class>
 <widget class="QDialog" name="{dialog_name}">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>{width}</width>
    <height>{height}</height>
   </rect>
  </property>
  <property name="windowTitle">
   <string>{title}</string>
  </property>
  <property name="modal">
   <bool>true</bool>
  </property>
  <layout class="QVBoxLayout" name="mainLayout">
   <property name="spacing">
    <number>15</number>
   </property>
   <property name="leftMargin">
    <number>20</number>
   </property>
   <property name="topMargin">
    <number>20</number>
   </property>
   <property name="rightMargin">
    <number>20</number>
   </property>
   <property name="bottomMargin">
    <number>20</number>
   </property>
   
   <!-- Header -->
   <item>
    <layout class="QHBoxLayout" name="headerLayout">
     <item>
      <widget class="QLabel" name="lblIcon">
       <property name="text">
        <string>📋</string>
       </property>
       <property name="styleSheet">
        <string>font-size: 24px;</string>
       </property>
      </widget>
     </item>
     <item>
      <widget class="QLabel" name="lblTitle">
       <property name="text">
        <string>{title}</string>
       </property>
       <property name="styleSheet">
        <string>font-size: 18px; font-weight: bold; color: #2c3e50;</string>
       </property>
      </widget>
     </item>
     <item>
      <spacer name="headerSpacer">
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
    </layout>
   </item>
   
   <!-- Content -->
   <item>
    <widget class="QFrame" name="frameContent">
     <property name="frameShape">
      <enum>QFrame::StyledPanel</enum>
     </property>
     <property name="frameShadow">
      <enum>QFrame::Raised</enum>
     </property>
     <property name="styleSheet">
      <string>
       QFrame#frameContent {{
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 6px;
       }}
      </string>
     </property>
     <layout class="QVBoxLayout" name="contentLayout">
      <property name="spacing">
       <number>10</number>
      </property>
      <property name="leftMargin">
       <number>15</number>
      </property>
      <property name="topMargin">
       <number>15</number>
      </property>
      <property name="rightMargin">
       <number>15</number>
      </property>
      <property name="bottomMargin">
       <number>15</number>
      </property>
      
      <item>
       <widget class="QLabel" name="lblPlaceholder">
        <property name="text">
         <string>🚧 Contenido de {title}
         
Formulario en desarrollo.
Migrar desde archivo Python correspondiente.</string>
        </property>
        <property name="alignment">
         <set>Qt::AlignCenter</set>
        </property>
        <property name="styleSheet">
         <string>
          QLabel {{
           color: #7f8c8d;
           font-size: 14px;
           padding: 20px;
          }}
         </string>
        </property>
       </widget>
      </item>
     </layout>
    </widget>
   </item>
   
   <!-- Buttons -->
   <item>
    <layout class="QHBoxLayout" name="buttonLayout">
     <property name="spacing">
      <number>10</number>
     </property>
     <item>
      <spacer name="buttonSpacer">
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
      <widget class="QPushButton" name="btnCancel">
       <property name="text">
        <string>Cancelar</string>
       </property>
       <property name="minimumSize">
        <size>
         <width>100</width>
         <height>35</height>
        </size>
       </property>
      </widget>
     </item>
     <item>
      <widget class="QPushButton" name="btnAccept">
       <property name="text">
        <string>Aceptar</string>
       </property>
       <property name="default">
        <bool>true</bool>
       </property>
       <property name="minimumSize">
        <size>
         <width>100</width>
         <height>35</height>
        </size>
       </property>
      </widget>
     </item>
    </layout>
   </item>
  </layout>
 </widget>
 
 <tabstops>
  <tabstop>btnAccept</tabstop>
  <tabstop>btnCancel</tabstop>
 </tabstops>
 
 <resources/>
 <connections>
  <connection>
   <sender>btnCancel</sender>
   <signal>clicked()</signal>
   <receiver>{dialog_name}</receiver>
   <slot>reject()</slot>
   <hints>
    <hint type="sourcelabel">
     <x>350</x>
     <y>370</y>
    </hint>
    <hint type="destinationlabel">
     <x>250</x>
     <y>200</y>
    </hint>
   </hints>
  </connection>
 </connections>
</ui>'''

def main():
    """Función principal del generador"""
    print("=" * 60)
    print("GENERADOR AUTOMÁTICO DE ARCHIVOS .ui")
    print("AlmacénPro v2.0 - Migración MVC")
    print("=" * 60)
    
    # Asegurar que existen los directorios
    Path("views/dialogs").mkdir(parents=True, exist_ok=True)
    Path("views/widgets").mkdir(parents=True, exist_ok=True)
    
    # Definir archivos a generar
    dialogs_to_generate = [
        ("add_product_dialog.ui", "AddProductDialog", "Agregar Producto", 600, 500),
        ("add_provider_dialog.ui", "AddProviderDialog", "Agregar Proveedor", 500, 400),
        ("backup_dialog.ui", "BackupDialog", "Gestión de Respaldos", 550, 450),
        ("customer_selector_dialog.ui", "CustomerSelectorDialog", "Seleccionar Cliente", 600, 400),
        ("payment_debt_dialog.ui", "PaymentDebtDialog", "Gestionar Deudas", 500, 350),
        ("receive_purchase_dialog.ui", "ReceivePurchaseDialog", "Recibir Compra", 650, 500),
        ("report_dialog.ui", "ReportDialog", "Generar Reportes", 600, 450),
        ("sales_process_dialog.ui", "SalesProcessDialog", "Procesar Venta", 500, 400),
        ("user_management_dialog.ui", "UserManagementDialog", "Gestión de Usuarios", 700, 600)
    ]
    
    widgets_to_generate = [
        ("admin_widget.ui", "AdminWidget", "📊 Panel de Administración", 900, 650),
        ("advanced_crm_widget.ui", "AdvancedCrmWidget", "🎯 CRM Avanzado", 1000, 700),
        ("advanced_stock_widget.ui", "AdvancedStockWidget", "📦 Inventario Avanzado", 1000, 700),
        ("executive_dashboard_widget.ui", "ExecutiveDashboardWidget", "📈 Dashboard Ejecutivo", 1100, 800),
        ("predictive_analytics_widget.ui", "PredictiveAnalyticsWidget", "🤖 Análisis Predictivo", 1000, 700),
        ("providers_widget.ui", "ProvidersWidget", "🏪 Gestión de Proveedores", 900, 600),
        ("purchases_widget.ui", "PurchasesWidget", "🛒 Gestión de Compras", 1000, 700),
        ("reports_widget.ui", "ReportsWidget", "📊 Reportes y Análisis", 1000, 700)
    ]
    
    # Generar diálogos
    print("\nGenerando diálogos...")
    dialogs_created = 0
    for filename, class_name, title, width, height in dialogs_to_generate:
        file_path = Path(f"views/dialogs/{filename}")
        if not file_path.exists():
            ui_content = generate_dialog_template(class_name, title, width, height)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(ui_content)
            print(f"[CREADO] {file_path}")
            dialogs_created += 1
        else:
            print(f"[EXISTE] {file_path}")
    
    # Generar widgets
    print("\nGenerando widgets...")
    widgets_created = 0
    for filename, class_name, title, width, height in widgets_to_generate:
        file_path = Path(f"views/widgets/{filename}")
        if not file_path.exists():
            ui_content = generate_ui_template(class_name, title, width, height)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(ui_content)
            print(f"[CREADO] {file_path}")
            widgets_created += 1
        else:
            print(f"[EXISTE] {file_path}")
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE GENERACIÓN")
    print("=" * 60)
    print(f"Diálogos creados: {dialogs_created}")
    print(f"Widgets creados: {widgets_created}")
    print(f"Total archivos .ui generados: {dialogs_created + widgets_created}")
    
    # Listar todos los archivos .ui ahora disponibles
    print("\n📁 ARCHIVOS .ui DISPONIBLES:")
    
    dialogs_path = Path("views/dialogs")
    widgets_path = Path("views/widgets")
    
    if dialogs_path.exists():
        dialog_files = list(dialogs_path.glob("*.ui"))
        print(f"\n📂 Diálogos ({len(dialog_files)} archivos):")
        for file in sorted(dialog_files):
            size = file.stat().st_size
            print(f"   - {file.name} ({size:,} bytes)")
    
    if widgets_path.exists():
        widget_files = list(widgets_path.glob("*.ui"))
        print(f"\n📂 Widgets ({len(widget_files)} archivos):")
        for file in sorted(widget_files):
            size = file.stat().st_size
            print(f"   - {file.name} ({size:,} bytes)")
    
    # Archivos que ya existían
    existing_files = [
        "views/dialogs/login_dialog.ui",
        "views/dialogs/customer_dialog.ui", 
        "views/dialogs/payment_dialog.ui",
        "views/forms/sales_widget.ui",
        "views/forms/customers_widget.ui",
        "views/widgets/dashboard_widget.ui",
        "views/widgets/stock_widget.ui"
    ]
    
    print(f"\n📂 Archivos creados anteriormente ({len(existing_files)} archivos):")
    for file_path in existing_files:
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            print(f"   - {Path(file_path).name} ({size:,} bytes)")
    
    total_ui_files = dialogs_created + widgets_created + len(existing_files)
    print(f"\n🎯 TOTAL ARCHIVOS .ui EN PROYECTO: {total_ui_files}")
    
    print("\n✅ GENERACIÓN COMPLETADA!")
    print("\nPróximos pasos:")
    print("1. Revisar archivos .ui generados")
    print("2. Personalizar contenido según necesidades específicas")
    print("3. Crear controladores correspondientes")
    print("4. Integrar con sistema MVC existente")

if __name__ == "__main__":
    main()