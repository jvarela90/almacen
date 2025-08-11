#!/usr/bin/env python3
"""
Test de Validacion - Migracion MVC AlmacenPro v2.0
"""

import os
import sys
from pathlib import Path

def test_structure():
    """Verificar estructura MVC"""
    print("VERIFICANDO ESTRUCTURA MVC...")
    
    # Directorios requeridos
    dirs = ['models', 'views/forms', 'controllers', 'utils', 'database/scripts']
    
    # Archivos clave
    files = [
        'models/base_model.py',
        'models/entities.py', 
        'models/sales_model.py',
        'models/customer_model.py',
        'views/forms/sales_widget.ui',
        'views/forms/customers_widget.ui',
        'controllers/base_controller.py',
        'controllers/main_controller.py',
        'controllers/sales_controller.py',
        'controllers/customers_controller.py',
        'main_mvc.py',
        'database/scripts/schema_export.sql'
    ]
    
    all_good = True
    
    # Verificar directorios
    print("\nDIRECTORIOS:")
    for dir_path in dirs:
        if Path(dir_path).exists():
            print(f"[OK] {dir_path}")
        else:
            print(f"[FALTA] {dir_path}")
            all_good = False
    
    # Verificar archivos
    print("\nARCHIVOS CLAVE:")
    for file_path in files:
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            print(f"[OK] {file_path} ({size} bytes)")
        else:
            print(f"[FALTA] {file_path}")
            all_good = False
    
    # Verificar contenido de archivos .ui
    print("\nVERIFICANDO ARCHIVOS .UI:")
    ui_files = ['views/forms/sales_widget.ui', 'views/forms/customers_widget.ui']
    
    for ui_file in ui_files:
        if Path(ui_file).exists():
            try:
                with open(ui_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'ui version="4.0"' in content:
                        print(f"[OK] {ui_file} - Qt Designer valido")
                    else:
                        print(f"[ADVERTENCIA] {ui_file} - No parece Qt Designer")
            except Exception as e:
                print(f"[ERROR] {ui_file} - {e}")
                all_good = False
    
    # Verificar base de datos
    print("\nBASE DE DATOS:")
    if Path('almacen_pro.db').exists():
        size = Path('almacen_pro.db').stat().st_size
        print(f"[OK] almacen_pro.db ({size/1024:.1f} KB)")
    else:
        print("[ADVERTENCIA] almacen_pro.db no encontrada")
    
    return all_good

def main():
    print("=" * 50)
    print("VALIDACION MIGRACION MVC - AlmacenPro v2.0")
    print("=" * 50)
    
    try:
        result = test_structure()
        
        print("\n" + "=" * 50)
        print("RESUMEN:")
        if result:
            print("[EXITO] Migracion MVC completada correctamente")
            print("\nPROXIMOS PASOS:")
            print("1. Instalar PyQt5: pip install PyQt5")
            print("2. Ejecutar: python main_mvc.py") 
            print("3. Configurar DBeaver con almacen_pro.db")
        else:
            print("[ADVERTENCIA] Algunos elementos faltantes")
            print("Revisar elementos [FALTA] arriba")
        
        print("=" * 50)
        return result
        
    except Exception as e:
        print(f"ERROR en validacion: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)