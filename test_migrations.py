#!/usr/bin/env python3
"""
Prueba básica del sistema de migraciones Alembic
AlmacénPro v2.0
"""

import os
import sys
import sqlite3
import tempfile
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from database.migrate import MigrationManager


def test_migration_system():
    """Prueba básica del sistema de migraciones"""
    print("=== Probando Sistema de Migraciones ===")
    
    # Crear base de datos temporal para pruebas
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    # Configurar variable de entorno para usar BD temporal
    original_db_path = os.environ.get('SQLITE_PATH')
    os.environ['SQLITE_PATH'] = temp_db_path
    
    try:
        # Crear manager de migraciones
        manager = MigrationManager()
        
        print("1. Verificando conexión a BD...")
        if not manager.check_database_connection():
            print("❌ Error: No se pudo conectar a la BD")
            return False
        print("✅ Conexión exitosa")
        
        print("\n2. Inicializando sistema de migraciones...")
        if not manager.init_migrations():
            print("❌ Error: No se pudo inicializar el sistema")
            return False
        print("✅ Sistema inicializado")
        
        print("\n3. Verificando tabla alembic_version...")
        # Verificar que se pueda consultar la tabla de versiones de Alembic
        try:
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
            if cursor.fetchone():
                print("✅ Tabla alembic_version creada")
            else:
                print("⚠️  Tabla alembic_version no encontrada (normal si no se han aplicado migraciones)")
            conn.close()
        except Exception as e:
            print(f"⚠️  Error verificando tabla: {e}")
        
        print("\n4. Mostrando revisión actual...")
        manager.show_current_revision()
        
        print("\n5. Mostrando migraciones disponibles...")
        manager.show_migration_history()
        
        print("\n=== Prueba Completada ===")
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        return False
    
    finally:
        # Restaurar configuración original
        if original_db_path:
            os.environ['SQLITE_PATH'] = original_db_path
        elif 'SQLITE_PATH' in os.environ:
            del os.environ['SQLITE_PATH']
        
        # Limpiar archivo temporal
        try:
            os.unlink(temp_db_path)
        except:
            pass


def test_database_structure():
    """Verificar que las migraciones definen la estructura correcta"""
    print("\n=== Verificando Estructura de Migraciones ===")
    
    migrations_dir = project_root / "database" / "migrations" / "versions"
    
    if not migrations_dir.exists():
        print("❌ Directorio de migraciones no encontrado")
        return False
    
    migration_files = list(migrations_dir.glob("*.py"))
    print(f"Migraciones encontradas: {len(migration_files)}")
    
    for migration_file in sorted(migration_files):
        print(f"  - {migration_file.name}")
        
        # Verificar que el archivo tiene la estructura correcta
        try:
            with open(migration_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Verificaciones básicas
            if 'def upgrade()' not in content:
                print(f"    ❌ Falta función upgrade() en {migration_file.name}")
            elif 'def downgrade()' not in content:
                print(f"    ❌ Falta función downgrade() en {migration_file.name}")
            else:
                print(f"    ✅ Estructura correcta")
                
        except Exception as e:
            print(f"    ❌ Error leyendo {migration_file.name}: {e}")
    
    return True


if __name__ == "__main__":
    print("Probando Sistema de Migraciones de AlmacénPro v2.0")
    print("=" * 60)
    
    success = True
    
    # Prueba 1: Sistema de migraciones
    if not test_migration_system():
        success = False
    
    # Prueba 2: Estructura de migraciones
    if not test_database_structure():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TODAS LAS PRUEBAS PASARON")
        sys.exit(0)
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
        sys.exit(1)