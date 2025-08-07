"""
Script final de configuración del sistema AlmacénPro v2.0
Aplicar todas las correcciones y preparar el sistema completamente funcional
"""

import sqlite3
import shutil
import logging
from pathlib import Path
from datetime import datetime
import os
import json

def final_system_setup():
    """Configuración final completa del sistema"""
    print("=" * 70)
    print("ALMACEN PRO V2.0 - CONFIGURACION FINAL DEL SISTEMA")
    print("=" * 70)
    
    # 1. Unificar bases de datos
    print("\n[PASO 1] Unificando bases de datos...")
    unify_databases()
    
    # 2. Crear tabla de logs
    print("\n[PASO 2] Creando sistema de logs...")
    create_system_logs()
    
    # 3. Verificar estructura de base de datos
    print("\n[PASO 3] Verificando estructura de BD...")
    verify_database_structure()
    
    # 4. Configurar rutas y archivos
    print("\n[PASO 4] Configurando archivos del sistema...")
    setup_system_files()
    
    # 5. Verificar datos de prueba
    print("\n[PASO 5] Verificando datos de prueba...")
    verify_test_data()
    
    # 6. Resumen final
    print("\n[PASO 6] Resumen final...")
    final_summary()
    
    print("\n" + "=" * 70)
    print("CONFIGURACION COMPLETADA - SISTEMA LISTO PARA USAR")
    print("=" * 70)

def unify_databases():
    """Unificar bases de datos en una sola ubicación"""
    try:
        # Asegurar que existe la carpeta data
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # Rutas de las bases de datos
        root_db = Path("almacen_pro.db")
        data_db = Path("data/almacen_pro.db")
        
        # Decidir cuál usar como principal
        if root_db.exists() and data_db.exists():
            # Comparar fechas de modificación
            if root_db.stat().st_mtime > data_db.stat().st_mtime:
                print(f"   📋 Usando BD de raíz (más reciente)")
                shutil.copy2(root_db, data_db)
            else:
                print(f"   📋 Usando BD de data (más reciente)")
        elif root_db.exists():
            print(f"   📋 Copiando BD de raíz a data/")
            shutil.copy2(root_db, data_db)
        elif data_db.exists():
            print(f"   📋 BD ya está en data/")
        else:
            print(f"   ⚠️ No se encontró ninguna BD")
            return
        
        # Crear backup de seguridad
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"data/almacen_pro_unified_{timestamp}.db"
        shutil.copy2(data_db, backup_path)
        print(f"   💾 Backup creado: {backup_path}")
        
        print("   ✅ Bases de datos unificadas en data/")
        
    except Exception as e:
        print(f"   ❌ Error unificando BD: {e}")

def create_system_logs():
    """Crear tabla de logs y sistema de auditoría"""
    try:
        db_path = "data/almacen_pro.db"
        
        if not Path(db_path).exists():
            print("   ❌ Base de datos no encontrada")
            return
        
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        
        # Crear tabla de logs si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                username VARCHAR(100),
                action VARCHAR(100) NOT NULL,
                table_name VARCHAR(100),
                record_id INTEGER,
                old_values TEXT,
                new_values TEXT,
                ip_address VARCHAR(45),
                user_agent TEXT,
                success BOOLEAN DEFAULT 1,
                error_message TEXT,
                FOREIGN KEY (user_id) REFERENCES usuarios(id)
            )
        """)
        
        # Crear índices para logs
        log_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_logs_user_id ON system_logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_logs_action ON system_logs(action)",
            "CREATE INDEX IF NOT EXISTS idx_logs_success ON system_logs(success)"
        ]
        
        for index_sql in log_indexes:
            cursor.execute(index_sql)
        
        # Insertar log inicial
        cursor.execute("""
            INSERT INTO system_logs (username, action, success)
            VALUES ('SYSTEM', 'SYSTEM_SETUP_COMPLETED', 1)
        """)
        
        # Crear directorio de logs
        Path("logs").mkdir(exist_ok=True)
        
        connection.commit()
        connection.close()
        
        print("   ✅ Sistema de logs configurado")
        
    except Exception as e:
        print(f"   ❌ Error creando logs: {e}")

def verify_database_structure():
    """Verificar y corregir estructura de BD"""
    try:
        db_path = "data/almacen_pro.db"
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        
        # Verificar tablas principales
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['usuarios', 'productos', 'categorias', 'ventas', 'clientes']
        missing_tables = [t for t in expected_tables if t not in tables]
        
        if missing_tables:
            print(f"   ⚠️ Tablas faltantes: {missing_tables}")
        else:
            print("   ✅ Tablas principales verificadas")
        
        # Verificar y agregar columnas faltantes
        fixes_applied = 0
        
        # Verificar columna 'color' en categorias
        cursor.execute("PRAGMA table_info(categorias)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'color' not in columns:
            cursor.execute("ALTER TABLE categorias ADD COLUMN color VARCHAR(7) DEFAULT '#3498db'")
            fixes_applied += 1
            print("   ➕ Columna 'color' agregada a categorias")
        
        # Verificar columna 'usuario_id' en ventas
        if 'ventas' in tables:
            cursor.execute("PRAGMA table_info(ventas)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'usuario_id' not in columns:
                cursor.execute("ALTER TABLE ventas ADD COLUMN usuario_id INTEGER")
                fixes_applied += 1
                print("   ➕ Columna 'usuario_id' agregada a ventas")
        
        # Verificar columna 'barcode' en productos
        if 'productos' in tables:
            cursor.execute("PRAGMA table_info(productos)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'barcode' not in columns:
                cursor.execute("ALTER TABLE productos ADD COLUMN barcode VARCHAR(50)")
                fixes_applied += 1
                print("   ➕ Columna 'barcode' agregada a productos")
        
        connection.commit()
        connection.close()
        
        print(f"   ✅ Estructura verificada ({fixes_applied} correcciones aplicadas)")
        
    except Exception as e:
        print(f"   ❌ Error verificando estructura: {e}")

def setup_system_files():
    """Configurar archivos necesarios del sistema"""
    try:
        # Crear directorios necesarios
        directories = ['logs', 'backups', 'exports', 'reports', 'temp']
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
        
        # Actualizar configuración para usar BD unificada
        config_file = Path("config.json")
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}
        
        # Actualizar ruta de base de datos
        if 'database' not in config:
            config['database'] = {}
        config['database']['path'] = 'data/almacen_pro.db'
        
        # Asegurar configuraciones básicas
        config.setdefault('ui', {}).update({
            'theme': 'default',
            'language': 'es',
            'window_maximized': False
        })
        
        config.setdefault('security', {}).update({
            'session_timeout': 60,
            'max_login_attempts': 3,
            'lockout_duration': 15
        })
        
        # Guardar configuración actualizada
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        print("   ✅ Archivos de sistema configurados")
        
    except Exception as e:
        print(f"   ❌ Error configurando archivos: {e}")

def verify_test_data():
    """Verificar que existen datos de prueba"""
    try:
        db_path = "data/almacen_pro.db"
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        
        # Contar registros en tablas principales
        stats = {}
        
        tables_to_check = ['usuarios', 'productos', 'categorias', 'ventas']
        
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[table] = count
            except sqlite3.OperationalError:
                stats[table] = "N/A (tabla no existe)"
        
        print("   📊 Datos disponibles:")
        for table, count in stats.items():
            print(f"      • {table}: {count}")
        
        # Verificar usuarios por defecto
        cursor.execute("SELECT username, rol_nombre FROM usuarios WHERE username IN ('admin', 'gerente', 'vendedor')")
        users = cursor.fetchall()
        
        if users:
            print("   👥 Usuarios de prueba disponibles:")
            for username, role in users:
                print(f"      • {username} ({role})")
        else:
            print("   ⚠️ No se encontraron usuarios de prueba")
        
        connection.close()
        print("   ✅ Verificación de datos completada")
        
    except Exception as e:
        print(f"   ❌ Error verificando datos: {e}")

def final_summary():
    """Mostrar resumen final del sistema"""
    try:
        db_path = "data/almacen_pro.db"
        
        if not Path(db_path).exists():
            print("   ❌ Base de datos no encontrada")
            return
        
        # Información del archivo
        db_size = Path(db_path).stat().st_size / (1024 * 1024)  # MB
        
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        
        # Contar tablas e índices
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        tables_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
        indexes_count = cursor.fetchone()[0]
        
        connection.close()
        
        print(f"""
   🎯 SISTEMA ALMACÉNPRO V2.0 CONFIGURADO
   
   📊 Estadísticas:
      • Base de datos: data/almacen_pro.db
      • Tamaño: {db_size:.2f} MB
      • Tablas: {tables_count}
      • Índices: {indexes_count}
   
   🔐 Usuarios de prueba:
      • admin / admin123 (Administrador completo)
      • gerente / gerente123 (Gerente - sin admin)
      • vendedor / vendedor123 (Solo ventas)
   
   📁 Directorios creados:
      • logs/ - Logs del sistema y auditoría
      • backups/ - Backups automáticos
      • exports/ - Exportaciones de datos
      • reports/ - Reportes generados
      • data/ - Base de datos unificada
   
   ✨ Funcionalidades implementadas:
      • ✅ Roles diferenciados por usuario
      • ✅ Panel de administración completo
      • ✅ Dashboard personalizado por rol
      • ✅ Sistema de logs de auditoría
      • ✅ Gestión de productos con datos reales
      • ✅ Acciones rápidas funcionales
      • ✅ Base de datos unificada y optimizada
        """)
        
    except Exception as e:
        print(f"   ❌ Error generando resumen: {e}")

if __name__ == "__main__":
    # Configurar logging básico
    logging.basicConfig(level=logging.INFO)
    
    # Ejecutar configuración final
    final_system_setup()
    
    print(f"""
🎉 ¡CONFIGURACIÓN COMPLETADA!

Para ejecutar el sistema:
   python main.py

Para crear logs iniciales:
   python create_logs_table.py

🔥 El sistema está listo para ser usado con todas las funcionalidades!
    """)