#!/usr/bin/env python3
"""
Generador Simplificado de Archivos .ui - AlmacenPro v2.0
"""

import os
from pathlib import Path

def create_basic_ui_template(class_name, title, width=800, height=600):
    """Crear template basico de .ui"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>{class_name}</class>
 <widget class="QWidget" name="{class_name}">
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
    <widget class="QFrame" name="frameContent">
     <property name="frameShape">
      <enum>QFrame::StyledPanel</enum>
     </property>
     <property name="frameShadow">
      <enum>QFrame::Raised</enum>
     </property>
     <layout class="QVBoxLayout" name="contentLayout">
      <item>
       <widget class="QLabel" name="lblPlaceholder">
        <property name="text">
         <string>Contenido de {title}

Interface migrada desde Python.
Completar implementacion.</string>
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
           padding: 20px;
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
</ui>"""

def create_dialog_template(class_name, title, width=500, height=400):
    """Crear template para dialogos"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>{class_name}</class>
 <widget class="QDialog" name="{class_name}">
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
    <widget class="QFrame" name="frameContent">
     <property name="frameShape">
      <enum>QFrame::StyledPanel</enum>
     </property>
     <layout class="QVBoxLayout" name="contentLayout">
      <item>
       <widget class="QLabel" name="lblPlaceholder">
        <property name="text">
         <string>Formulario de {title}

Migrar contenido desde archivo Python correspondiente.</string>
        </property>
        <property name="alignment">
         <set>Qt::AlignCenter</set>
        </property>
        <property name="styleSheet">
         <string>color: #7f8c8d; font-size: 14px; padding: 20px;</string>
        </property>
       </widget>
      </item>
     </layout>
    </widget>
   </item>
   
   <item>
    <layout class="QHBoxLayout" name="buttonLayout">
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
 
 <resources/>
 <connections>
  <connection>
   <sender>btnCancel</sender>
   <signal>clicked()</signal>
   <receiver>{class_name}</receiver>
   <slot>reject()</slot>
  </connection>
 </connections>
</ui>"""

def main():
    print("=" * 50)
    print("GENERADOR DE ARCHIVOS .UI")
    print("AlmacenPro v2.0 - Migracion MVC")  
    print("=" * 50)
    
    # Crear directorios
    Path("views/dialogs").mkdir(parents=True, exist_ok=True)
    Path("views/widgets").mkdir(parents=True, exist_ok=True)
    
    # Dialogos a generar
    dialogs = [
        ("add_product_dialog.ui", "AddProductDialog", "Agregar Producto", 600, 500),
        ("add_provider_dialog.ui", "AddProviderDialog", "Agregar Proveedor", 500, 400),
        ("backup_dialog.ui", "BackupDialog", "Gestion de Respaldos", 550, 450),
        ("customer_selector_dialog.ui", "CustomerSelectorDialog", "Seleccionar Cliente", 600, 400),
        ("payment_debt_dialog.ui", "PaymentDebtDialog", "Gestionar Deudas", 500, 350),
        ("receive_purchase_dialog.ui", "ReceivePurchaseDialog", "Recibir Compra", 650, 500),
        ("report_dialog.ui", "ReportDialog", "Generar Reportes", 600, 450),
        ("sales_process_dialog.ui", "SalesProcessDialog", "Procesar Venta", 500, 400),
        ("user_management_dialog.ui", "UserManagementDialog", "Gestion de Usuarios", 700, 600)
    ]
    
    # Widgets a generar
    widgets = [
        ("admin_widget.ui", "AdminWidget", "Panel de Administracion", 900, 650),
        ("advanced_crm_widget.ui", "AdvancedCrmWidget", "CRM Avanzado", 1000, 700),
        ("advanced_stock_widget.ui", "AdvancedStockWidget", "Inventario Avanzado", 1000, 700),
        ("executive_dashboard_widget.ui", "ExecutiveDashboardWidget", "Dashboard Ejecutivo", 1100, 800),
        ("predictive_analytics_widget.ui", "PredictiveAnalyticsWidget", "Analisis Predictivo", 1000, 700),
        ("providers_widget.ui", "ProvidersWidget", "Gestion de Proveedores", 900, 600),
        ("purchases_widget.ui", "PurchasesWidget", "Gestion de Compras", 1000, 700),
        ("reports_widget.ui", "ReportsWidget", "Reportes y Analisis", 1000, 700)
    ]
    
    # Generar dialogos
    print("\nGenerando dialogos...")
    dialogs_created = 0
    for filename, class_name, title, width, height in dialogs:
        file_path = Path(f"views/dialogs/{filename}")
        if not file_path.exists():
            content = create_dialog_template(class_name, title, width, height)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[CREADO] {file_path}")
            dialogs_created += 1
        else:
            print(f"[EXISTE] {file_path}")
    
    # Generar widgets
    print("\nGenerando widgets...")
    widgets_created = 0
    for filename, class_name, title, width, height in widgets:
        file_path = Path(f"views/widgets/{filename}")
        if not file_path.exists():
            content = create_basic_ui_template(class_name, title, width, height)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[CREADO] {file_path}")
            widgets_created += 1
        else:
            print(f"[EXISTE] {file_path}")
    
    # Resumen
    print("\n" + "=" * 50)
    print("RESUMEN")
    print("=" * 50)
    print(f"Dialogos creados: {dialogs_created}")
    print(f"Widgets creados: {widgets_created}")
    print(f"Total archivos .ui generados: {dialogs_created + widgets_created}")
    
    # Contar archivos totales
    total_dialogs = len(list(Path("views/dialogs").glob("*.ui")))
    total_widgets = len(list(Path("views/widgets").glob("*.ui")))
    total_forms = len(list(Path("views/forms").glob("*.ui"))) if Path("views/forms").exists() else 0
    
    print(f"\nArchivos .ui en el proyecto:")
    print(f"- Dialogos: {total_dialogs}")
    print(f"- Widgets: {total_widgets}")
    print(f"- Forms: {total_forms}")
    print(f"- TOTAL: {total_dialogs + total_widgets + total_forms}")
    
    print("\nGeneracion completada!")

if __name__ == "__main__":
    main()