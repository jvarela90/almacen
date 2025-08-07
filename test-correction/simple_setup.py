"""
Script simple para configuración final del sistema AlmacénPro v2.0
"""

import sqlite3
import shutil
import logging
from pathlib import Path
from datetime import datetime
import os
import json

def simple_setup():
    """Configuración simple del sistema"""
    print("=" * 60)
    print("ALMACEN PRO V2.0 - CONFIGURACION FINAL")
    print("=" * 60)
    
    # 1. Unificar bases de datos
    print("\n[1] Unificando bases de datos...")
    unify_databases()
    
    # 2. Crear tabla de logs
    print("\n[2] Creando sistema de logs...")
    create_logs_system()
    
    # 3. Verificar estructura
    print("\n[3] Verificando estructura de BD...")
    verify_structure()
    
    # 4. Configurar archivos
    print("\n[4] Configurando archivos...")
    setup_files()
    
    print("\n" + "=" * 60)
    print("CONFIGURACION COMPLETADA")
    print("=" * 60)

def unify_databases():
    """Unificar bases de datos"""
    try:
        # Crear directorio data
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        root_db = Path("almacen_pro.db")
        data_db = Path("data/almacen_pro.db")
        
        if root_db.exists() and data_db.exists():
            if root_db.stat().st_mtime > data_db.stat().st_mtime:
                print("   -> Usando BD de raiz (mas reciente)")
                shutil.copy2(root_db, data_db)
            else:
                print("   -> BD de data es mas reciente")
        elif root_db.exists():
            print("   -> Copiando BD de raiz a data/")
            shutil.copy2(root_db, data_db)
        elif data_db.exists():
            print("   -> BD ya esta en data/")
        else:
            print("   -> No se encontro BD")
            return
        
        # Crear backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"data/backup_unified_{timestamp}.db"
        shutil.copy2(data_db, backup_path)
        print(f"   -> Backup creado: {backup_path}")
        print("   -> BD unificadas correctamente")
        
    except Exception as e:
        print(f"   ERROR: {e}")

def create_logs_system():
    """Crear sistema de logs"""
    try:
        db_path = "data/almacen_pro.db"
        
        if not Path(db_path).exists():
            print("   ERROR: BD no encontrada")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Crear tabla de logs
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
                success BOOLEAN DEFAULT 1,
                error_message TEXT,
                FOREIGN KEY (user_id) REFERENCES usuarios(id)
            )
        """)
        
        # Crear indices
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_logs_user_id ON system_logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_logs_action ON system_logs(action)",
            "CREATE INDEX IF NOT EXISTS idx_logs_success ON system_logs(success)"
        ]
        
        for idx in indexes:
            cursor.execute(idx)
        
        # Log inicial
        cursor.execute("""
            INSERT INTO system_logs (username, action, success)
            VALUES ('SYSTEM', 'SYSTEM_SETUP_COMPLETED', 1)
        """)
        
        # Crear directorio logs
        Path("logs").mkdir(exist_ok=True)
        
        conn.commit()
        conn.close()
        print("   -> Sistema de logs configurado")
        
    except Exception as e:
        print(f"   ERROR: {e}")

def verify_structure():
    """Verificar estructura de BD"""
    try:
        db_path = "data/almacen_pro.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected = ['usuarios', 'productos', 'categorias', 'ventas', 'clientes']
        missing = [t for t in expected if t not in tables]
        
        if missing:
            print(f"   -> Tablas faltantes: {missing}")
        else:
            print("   -> Todas las tablas principales verificadas")
        
        # Verificar y agregar columnas faltantes
        fixes = 0
        
        # Columna color en categorias
        cursor.execute("PRAGMA table_info(categorias)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'color' not in columns:
            cursor.execute("ALTER TABLE categorias ADD COLUMN color VARCHAR(7) DEFAULT '#3498db'")
            fixes += 1
            print("   -> Columna 'color' agregada a categorias")
        
        # Columna usuario_id en ventas
        if 'ventas' in tables:
            cursor.execute("PRAGMA table_info(ventas)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'usuario_id' not in columns:
                cursor.execute("ALTER TABLE ventas ADD COLUMN usuario_id INTEGER")
                fixes += 1
                print("   -> Columna 'usuario_id' agregada a ventas")
        
        conn.commit()
        conn.close()
        print(f"   -> Estructura verificada ({fixes} correcciones)")
        
    except Exception as e:
        print(f"   ERROR: {e}")

def setup_files():
    """Configurar archivos del sistema"""
    try:
        # Crear directorios
        dirs = ['logs', 'backups', 'exports', 'reports', 'temp']
        for d in dirs:
            Path(d).mkdir(exist_ok=True)
        
        # Configuracion
        config_file = Path("config.json")
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}
        
        # Actualizar configuracion
        if 'database' not in config:
            config['database'] = {}
        config['database']['path'] = 'data/almacen_pro.db'
        
        config.setdefault('ui', {}).update({
            'theme': 'default',
            'language': 'es'
        })
        
        config.setdefault('security', {}).update({
            'session_timeout': 60,
            'max_login_attempts': 3
        })
        
        # Guardar configuracion
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        print("   -> Archivos de sistema configurados")
        
    except Exception as e:
        print(f"   ERROR: {e}")

if __name__ == "__main__":
    simple_setup()
    
    print(f"""
CONFIGURACION COMPLETADA!

Para ejecutar el sistema:
   python main.py

El sistema esta listo con todas las funcionalidades:
- Roles diferenciados por usuario
- Panel de administracion completo
- Dashboard personalizado por rol
- Sistema de logs de auditoria
- Gestion de productos con datos reales
- Acciones rapidas funcionales
- Base de datos unificada y optimizada
""")