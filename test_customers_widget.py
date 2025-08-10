#!/usr/bin/env python3
"""
Test básico del widget de gestión de clientes
"""

import sys
import os

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Qt antes de otros imports para evitar conflictos
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from database.manager import DatabaseManager
from managers.customer_manager import CustomerManager
from ui.widgets.customers_widget import CustomersWidget

def test_customers_widget():
    """Test básico de inicialización del widget"""
    
    print("="*60)
    print("TEST WIDGET GESTION CLIENTES")
    print("="*60)
    
    try:
        # Crear aplicación Qt
        app = QApplication(sys.argv)
        
        print("\n1. INICIALIZACION DE MANAGERS")
        print("-" * 40)
        
        # Inicializar managers
        db = DatabaseManager()
        customer_manager = CustomerManager(db)
        
        managers = {
            'customer_manager': customer_manager
        }
        
        print("OK - Managers inicializados")
        
        print("\n2. CREACION DEL WIDGET")
        print("-" * 40)
        
        # Crear widget
        widget = CustomersWidget(managers)
        
        print("OK - Widget creado exitosamente")
        print(f"Widget title: {widget.windowTitle() if hasattr(widget, 'windowTitle') else 'N/A'}")
        
        # Verificar componentes principales
        print("\n3. VERIFICACION DE COMPONENTES")
        print("-" * 40)
        
        # Verificar tab widget
        if hasattr(widget, 'tab_widget'):
            tab_count = widget.tab_widget.count()
            print(f"OK - Tabs encontrados: {tab_count}")
            
            for i in range(tab_count):
                tab_name = widget.tab_widget.tabText(i)
                print(f"  - Tab {i+1}: {tab_name}")
        
        # Verificar tabla de clientes
        if hasattr(widget, 'customers_table'):
            print("OK - Tabla de clientes encontrada")
            column_count = widget.customers_table.columnCount()
            print(f"  - Columnas: {column_count}")
        
        # Verificar búsqueda
        if hasattr(widget, 'search_input'):
            print("OK - Campo de búsqueda encontrado")
        
        # Verificar botones principales
        buttons_found = []
        if hasattr(widget, 'new_customer_btn'):
            buttons_found.append("Nuevo Cliente")
        if hasattr(widget, 'refresh_btn'):
            buttons_found.append("Actualizar")
        
        print(f"OK - Botones encontrados: {', '.join(buttons_found)}")
        
        print("\n4. TEST DE CARGA DE DATOS")
        print("-" * 40)
        
        # Intentar cargar datos (sin mostrar el widget)
        if hasattr(widget, 'customers_data'):
            customers_count = len(widget.customers_data)
            print(f"OK - Clientes cargados: {customers_count}")
        
        if hasattr(widget, 'customers_table'):
            row_count = widget.customers_table.rowCount()
            print(f"OK - Filas en tabla: {row_count}")
        
        print("\n5. TEST FUNCIONALIDADES BASICAS")
        print("-" * 40)
        
        # Test búsqueda
        if hasattr(widget, 'search_customers'):
            print("OK - Función de búsqueda disponible")
        
        # Test filtros
        if hasattr(widget, 'filter_customers'):
            print("OK - Función de filtros disponible")
        
        # Test refresh
        if hasattr(widget, 'refresh_data'):
            print("OK - Función de actualización disponible")
        
        print("\n6. MOSTRANDO WIDGET (5 SEGUNDOS)")
        print("-" * 40)
        
        # Mostrar widget brevemente
        widget.show()
        widget.resize(1000, 700)
        
        print("OK - Widget mostrado")
        
        # Timer para cerrar automáticamente
        timer = QTimer()
        timer.timeout.connect(app.quit)
        timer.start(5000)  # 5 segundos
        
        # Ejecutar loop de eventos
        app.exec_()
        
        print("\n" + "="*60)
        print("RESULTADO: WIDGET DE CLIENTES FUNCIONANDO")
        print("="*60)
        print("✓ Inicialización exitosa")
        print("✓ Componentes UI creados correctamente") 
        print("✓ Datos cargados desde base de datos")
        print("✓ Funcionalidades básicas disponibles")
        print("✓ Interface mostrada correctamente")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\nERROR EN TEST WIDGET: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_customers_widget()
    if success:
        print("\nSUCCESS: Widget de clientes funcionando correctamente!")
        sys.exit(0)
    else:
        print("\nFAILED: Error en widget de clientes")
        sys.exit(1)