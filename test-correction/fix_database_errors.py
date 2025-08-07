"""
Script para corregir errores identificados en los logs de la base de datos
"""

import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def fix_database_errors():
    """Corregir errores de base de datos identificados en los logs"""
    db_path = "almacen_pro.db"
    
    try:
        # Conectar a la base de datos
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        
        print("🔧 Iniciando corrección de errores de base de datos...")
        
        # 1. Verificar y agregar columna 'color' a tabla categorias
        print("📝 Verificando tabla categorias...")
        cursor.execute("PRAGMA table_info(categorias)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'color' not in columns:
            print("   ➕ Agregando columna 'color' a tabla categorias")
            cursor.execute("ALTER TABLE categorias ADD COLUMN color VARCHAR(7) DEFAULT '#3498db'")
        else:
            print("   ✅ Columna 'color' ya existe")
        
        # 2. Verificar y agregar columna 'usuario_id' a tabla ventas
        print("📝 Verificando tabla ventas...")
        cursor.execute("PRAGMA table_info(ventas)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'usuario_id' not in columns:
            print("   ➕ Agregando columna 'usuario_id' a tabla ventas")
            cursor.execute("ALTER TABLE ventas ADD COLUMN usuario_id INTEGER")
        else:
            print("   ✅ Columna 'usuario_id' ya existe")
        
        # 3. Verificar y agregar columna 'total' a tabla detalle_ventas
        print("📝 Verificando tabla detalle_ventas...")
        try:
            cursor.execute("PRAGMA table_info(detalle_ventas)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'total' not in columns:
                print("   ➕ Agregando columna 'total' a tabla detalle_ventas")
                cursor.execute("ALTER TABLE detalle_ventas ADD COLUMN total DECIMAL(10,2) DEFAULT 0")
            else:
                print("   ✅ Columna 'total' ya existe")
        except sqlite3.OperationalError:
            print("   ⚠️ Tabla detalle_ventas no existe")
        
        # 4. Verificar y agregar columna 'numero_documento' a tabla usuarios (si existe)
        print("📝 Verificando tabla usuarios...")
        try:
            cursor.execute("PRAGMA table_info(usuarios)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'numero_documento' not in columns:
                print("   ➕ Agregando columna 'numero_documento' a tabla usuarios")
                cursor.execute("ALTER TABLE usuarios ADD COLUMN numero_documento VARCHAR(20)")
            else:
                print("   ✅ Columna 'numero_documento' ya existe")
        except sqlite3.OperationalError:
            print("   ⚠️ Tabla usuarios no existe")
        
        # 5. Crear índices corregidos que no fallen
        print("📝 Creando índices corregidos...")
        
        safe_indexes = [
            # Índices básicos que deberían funcionar
            "CREATE INDEX IF NOT EXISTS idx_productos_nombre ON productos(nombre)",
            "CREATE INDEX IF NOT EXISTS idx_productos_activo ON productos(activo)",
            "CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha_venta)",
            "CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username)",
            "CREATE INDEX IF NOT EXISTS idx_usuarios_activo ON usuarios(activo)"
        ]
        
        for index_sql in safe_indexes:
            try:
                cursor.execute(index_sql)
                print(f"   ✅ Índice creado: {index_sql.split('idx_')[1].split(' ')[0]}")
            except sqlite3.OperationalError as e:
                print(f"   ⚠️ Error en índice: {e}")
        
        # 6. Insertar datos por defecto corregidos
        print("📝 Insertando datos por defecto...")
        
        # Categoría por defecto con color
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO categorias (id, nombre, descripcion, color)
                VALUES (1, 'General', 'Categoría general para productos', '#3498db')
            """)
            print("   ✅ Categoría por defecto insertada")
        except sqlite3.OperationalError as e:
            print(f"   ⚠️ Error insertando categoría: {e}")
        
        # Confirmar cambios
        connection.commit()
        print("✅ Correcciones aplicadas exitosamente")
        
        # Mostrar información de tablas
        print("\n📊 Información de tablas principales:")
        
        tables_to_check = ['usuarios', 'productos', 'categorias', 'ventas']
        for table in tables_to_check:
            try:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                print(f"   {table}: {len(columns)} columnas")
                
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   {table}: {count} registros")
            except sqlite3.OperationalError:
                print(f"   {table}: ⚠️ No existe")
        
        connection.close()
        
    except Exception as e:
        print(f"❌ Error durante la corrección: {e}")
        logger.error(f"Error corrigiendo base de datos: {e}")

if __name__ == "__main__":
    # Configurar logging básico
    logging.basicConfig(level=logging.INFO)
    fix_database_errors()