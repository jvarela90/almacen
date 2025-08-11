#!/usr/bin/env python3
"""
Prueba básica del sistema de migraciones Alembic
AlmacénPro v2.0
"""

import os
import sys
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def simple_test():
    """Prueba simple del sistema de migraciones"""
    print("=== Probando Sistema de Migraciones ===")
    
    try:
        from database.migrate import MigrationManager
        
        # Crear manager de migraciones
        manager = MigrationManager()
        
        print("1. Verificando conexion a BD...")
        if not manager.check_database_connection():
            print("[ERROR] No se pudo conectar a la BD")
            return False
        print("[OK] Conexion exitosa")
        
        print("\n2. Verificando archivos de migracion...")
        migrations_dir = project_root / "database" / "migrations" / "versions"
        migration_files = list(migrations_dir.glob("*.py"))
        print(f"Migraciones encontradas: {len(migration_files)}")
        
        for migration_file in sorted(migration_files):
            print(f"  - {migration_file.name}")
        
        print("\n[OK] Sistema de migraciones configurado correctamente")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error en prueba: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Probando Sistema de Migraciones de AlmacenPro v2.0")
    print("=" * 60)
    
    if simple_test():
        print("\n[OK] PRUEBA PASADA")
        
        print("\nComandos disponibles:")
        print("python database/migrate.py --help")
        print("python database/migrate.py current")
        print("python database/migrate.py history")
        print("python database/migrate.py upgrade")
        
        sys.exit(0)
    else:
        print("\n[ERROR] PRUEBA FALLIDA")
        sys.exit(1)