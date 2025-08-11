#!/usr/bin/env python3
"""
Test de Validación - Migración MVC AlmacénPro v2.0
Valida la estructura y componentes de la arquitectura MVC migrada
"""

import os
import sys
import importlib.util
import traceback
from pathlib import Path

def test_file_structure():
    """Verificar estructura de directorios MVC"""
    print("VERIFICANDO ESTRUCTURA MVC...")
    
    required_dirs = [
        'models',
        'views/forms', 
        'controllers',
        'utils',
        'database/scripts'
    ]
    
    all_good = True
    for dir_path in required_dirs:
        full_path = Path(dir_path)
        if full_path.exists():
            print(f"[OK] {dir_path}")
        else:
            print(f"[FALTA] {dir_path} - NO ENCONTRADO")
            all_good = False
    
    return all_good

def test_model_files():
    """Verificar archivos de modelos"""
    print("\nVERIFICANDO MODELOS...")
    
    model_files = [
        'models/base_model.py',
        'models/entities.py', 
        'models/sales_model.py',
        'models/customer_model.py'
    ]
    
    all_good = True
    for file_path in model_files:
        if Path(file_path).exists():
            print(f"[OK] {file_path}")
        else:
            print(f"[FALTA] {file_path} - NO ENCONTRADO")
            all_good = False
    
    return all_good

def test_view_files():
    """Verificar archivos .ui"""
    print("\n🎨 VERIFICANDO VISTAS (.ui files)...")
    
    ui_files = [
        'views/forms/sales_widget.ui',
        'views/forms/customers_widget.ui'
    ]
    
    all_good = True
    for file_path in ui_files:
        if Path(file_path).exists():
            # Verificar que es un archivo XML válido de Qt Designer
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '<?xml version="1.0" encoding="UTF-8"?>' in content and '<ui version="4.0">' in content:
                        print(f"✅ {file_path} - Archivo Qt Designer válido")
                    else:
                        print(f"⚠️  {file_path} - No parece ser archivo Qt Designer válido")
            except Exception as e:
                print(f"❌ {file_path} - Error leyendo: {e}")
                all_good = False
        else:
            print(f"❌ {file_path} - NO ENCONTRADO")
            all_good = False
    
    return all_good

def test_controller_files():
    """Verificar controladores"""
    print("\n🎮 VERIFICANDO CONTROLADORES...")
    
    controller_files = [
        'controllers/base_controller.py',
        'controllers/main_controller.py',
        'controllers/sales_controller.py',
        'controllers/customers_controller.py'
    ]
    
    all_good = True
    for file_path in controller_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - NO ENCONTRADO")
            all_good = False
    
    return all_good

def test_imports():
    """Verificar que los imports funcionen (sin PyQt5)"""
    print("\n🔗 VERIFICANDO IMPORTS (sin PyQt5)...")
    
    # Crear mock de PyQt5 para testing
    class MockPyQt5:
        class QtWidgets:
            class QWidget: pass
            class QApplication: pass
        class QtCore:
            class QObject: pass
            pyqtSignal = lambda *args: None
        class QtGui: pass
    
    # Mockear PyQt5
    sys.modules['PyQt5'] = MockPyQt5()
    sys.modules['PyQt5.QtWidgets'] = MockPyQt5.QtWidgets()
    sys.modules['PyQt5.QtCore'] = MockPyQt5.QtCore()
    sys.modules['PyQt5.QtGui'] = MockPyQt5.QtGui()
    
    test_imports = [
        ('models.base_model', 'BaseModel'),
        ('models.entities', 'Product'),
        ('utils.style_manager', 'StyleManager')
    ]
    
    all_good = True
    for module_name, class_name in test_imports:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, class_name):
                print(f"✅ {module_name}.{class_name}")
            else:
                print(f"⚠️  {module_name} - {class_name} no encontrado")
        except Exception as e:
            print(f"❌ {module_name} - Error: {e}")
            all_good = False
    
    return all_good

def test_database_integration():
    """Verificar integración con base de datos"""
    print("\n🗄️  VERIFICANDO INTEGRACIÓN BASE DE DATOS...")
    
    db_files = [
        'database/scripts/schema_export.sql',
        'database/scripts/dbeaver_connection.py'
    ]
    
    all_good = True
    for file_path in db_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - NO ENCONTRADO")
            all_good = False
    
    # Verificar que existe la base de datos
    db_path = Path('almacen_pro.db')
    if db_path.exists():
        print(f"✅ Base de datos: {db_path}")
        print(f"   Tamaño: {db_path.stat().st_size / 1024:.1f} KB")
    else:
        print(f"⚠️  Base de datos no encontrada: {db_path}")
    
    return all_good

def test_naming_conventions():
    """Verificar convenciones de nombres en archivos .ui"""
    print("\n📝 VERIFICANDO CONVENCIONES DE NOMBRES...")
    
    ui_files = [
        'views/forms/sales_widget.ui',
        'views/forms/customers_widget.ui'
    ]
    
    # Patrones esperados para widgets
    expected_patterns = {
        'sales_widget.ui': [
            'lineEditProductSearch',
            'tblProductos', 
            'tblCarrito',
            'btnAddProduct',
            'btnRemoveProduct'
        ],
        'customers_widget.ui': [
            'tblClientes',
            'lineEditBuscar',
            'cmbSegmento',
            'btnNuevoCliente'
        ]
    }
    
    all_good = True
    for file_path in ui_files:
        if Path(file_path).exists():
            filename = Path(file_path).name
            if filename in expected_patterns:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    patterns_found = 0
                    for pattern in expected_patterns[filename]:
                        if f'name="{pattern}"' in content:
                            patterns_found += 1
                        
                    if patterns_found >= len(expected_patterns[filename]) * 0.5:  # Al menos 50%
                        print(f"✅ {file_path} - Convenciones OK ({patterns_found}/{len(expected_patterns[filename])})")
                    else:
                        print(f"⚠️  {file_path} - Convenciones parciales ({patterns_found}/{len(expected_patterns[filename])})")
                        
                except Exception as e:
                    print(f"❌ {file_path} - Error verificando: {e}")
                    all_good = False
    
    return all_good

def test_mvc_integration():
    """Verificar integración MVC"""
    print("\n🔄 VERIFICANDO INTEGRACIÓN MVC...")
    
    integration_tests = [
        ("main_mvc.py existe", Path('main_mvc.py').exists()),
        ("main.py original existe", Path('main.py').exists()),
        ("Guía de migración existe", Path('GUIA_MIGRACION_MVC_QT_DESIGNER.md').exists())
    ]
    
    all_good = True
    for test_name, test_result in integration_tests:
        if test_result:
            print(f"✅ {test_name}")
        else:
            print(f"❌ {test_name}")
            all_good = False
    
    return all_good

def main():
    """Ejecutar todas las pruebas de validación"""
    print("=" * 60)
    print("VALIDACION MIGRACION MVC - AlmacenPro v2.0")
    print("=" * 60)
    
    tests = [
        ("Estructura de directorios", test_file_structure),
        ("Archivos de modelos", test_model_files), 
        ("Archivos de vistas", test_view_files),
        ("Archivos de controladores", test_controller_files),
        ("Imports y dependencias", test_imports),
        ("Integración base de datos", test_database_integration),
        ("Convenciones de nombres", test_naming_conventions),
        ("Integración MVC", test_mvc_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ ERROR en {test_name}: {e}")
            traceback.print_exc()
            results.append((test_name, False))
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE VALIDACIÓN")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{status} - {test_name}")
    
    print(f"\n🎯 RESULTADO FINAL: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡MIGRACIÓN MVC COMPLETADA EXITOSAMENTE!")
        print("\n📋 PRÓXIMOS PASOS:")
        print("   1. Instalar PyQt5: pip install PyQt5")
        print("   2. Ejecutar: python main_mvc.py")
        print("   3. Configurar DBeaver con almacen_pro.db")
        return True
    else:
        print(f"⚠️  Migración parcialmente completa ({passed}/{total})")
        print("   Revisar elementos faltantes arriba")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)