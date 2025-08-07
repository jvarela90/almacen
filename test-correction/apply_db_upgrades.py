"""
Script para aplicar las mejoras de base de datos del archivo upgrade-db.py
de forma gradual y controlada
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class DatabaseUpgrader:
    """Clase para aplicar upgrades de base de datos de forma segura"""
    
    def __init__(self, db_path="almacen_pro.db"):
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """Conectar a la base de datos"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
        
        # Habilitar foreign keys
        self.cursor.execute("PRAGMA foreign_keys = ON")
    
    def disconnect(self):
        """Desconectar de la base de datos"""
        if self.connection:
            self.connection.close()
    
    def create_backup(self):
        """Crear backup antes de aplicar cambios"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"almacen_pro_backup_{timestamp}.db"
        
        try:
            # Copiar base de datos
            import shutil
            shutil.copy2(self.db_path, backup_path)
            print(f"✅ Backup creado: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"❌ Error creando backup: {e}")
            return None
    
    def apply_essential_upgrades(self):
        """Aplicar upgrades esenciales identificados en los logs"""
        print("🔧 Aplicando upgrades esenciales...")
        
        upgrades = [
            {
                'name': 'Agregar columna color a categorias',
                'check': "SELECT sql FROM sqlite_master WHERE name='categorias'",
                'condition': lambda result: 'color' not in result[0].lower() if result else False,
                'sql': "ALTER TABLE categorias ADD COLUMN color VARCHAR(7) DEFAULT '#3498db'"
            },
            {
                'name': 'Agregar columna usuario_id a ventas',
                'check': "PRAGMA table_info(ventas)",
                'condition': lambda result: 'usuario_id' not in [row[1] for row in result],
                'sql': "ALTER TABLE ventas ADD COLUMN usuario_id INTEGER REFERENCES usuarios(id)"
            },
            {
                'name': 'Crear tabla system_config para configuraciones',
                'check': "SELECT name FROM sqlite_master WHERE type='table' AND name='system_config'",
                'condition': lambda result: len(result) == 0,
                'sql': """
                    CREATE TABLE IF NOT EXISTS system_config (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        config_key VARCHAR(100) UNIQUE NOT NULL,
                        config_value TEXT,
                        data_type VARCHAR(20) DEFAULT 'STRING',
                        category VARCHAR(50) DEFAULT 'GENERAL',
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
            },
            {
                'name': 'Crear tabla user_sessions',
                'check': "SELECT name FROM sqlite_master WHERE type='table' AND name='user_sessions'",
                'condition': lambda result: len(result) == 0,
                'sql': """
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        session_token VARCHAR(255) UNIQUE NOT NULL,
                        ip_address VARCHAR(45),
                        user_agent TEXT,
                        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP,
                        active BOOLEAN DEFAULT 1,
                        FOREIGN KEY (user_id) REFERENCES usuarios(id)
                    )
                """
            },
            {
                'name': 'Mejorar tabla productos con campos adicionales',
                'check': "PRAGMA table_info(productos)",
                'condition': lambda result: 'barcode' not in [row[1] for row in result],
                'sql': "ALTER TABLE productos ADD COLUMN barcode VARCHAR(50)"
            },
            {
                'name': 'Agregar campos de auditoría a productos',
                'check': "PRAGMA table_info(productos)",
                'condition': lambda result: 'created_at' not in [row[1] for row in result],
                'sql': "ALTER TABLE productos ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            }
        ]
        
        success_count = 0
        
        for upgrade in upgrades:
            try:
                print(f"   🔍 Verificando: {upgrade['name']}")
                
                # Ejecutar check
                self.cursor.execute(upgrade['check'])
                result = self.cursor.fetchall()
                
                # Verificar condición
                if upgrade['condition'](result):
                    print(f"   ➕ Aplicando: {upgrade['name']}")
                    self.cursor.execute(upgrade['sql'])
                    success_count += 1
                    print(f"   ✅ Completado")
                else:
                    print(f"   ⏭️ Ya existe")
                    
            except Exception as e:
                print(f"   ❌ Error en {upgrade['name']}: {e}")
        
        self.connection.commit()
        print(f"✅ {success_count} upgrades aplicados exitosamente")
    
    def create_improved_indexes(self):
        """Crear índices mejorados basados en upgrade-db.py"""
        print("📑 Creando índices mejorados...")
        
        indexes = [
            # Índices para productos
            "CREATE INDEX IF NOT EXISTS idx_productos_barcode ON productos(barcode)",
            "CREATE INDEX IF NOT EXISTS idx_productos_nombre_activo ON productos(nombre, activo)",
            "CREATE INDEX IF NOT EXISTS idx_productos_categoria_activo ON productos(categoria_id, activo)",
            
            # Índices para usuarios
            "CREATE INDEX IF NOT EXISTS idx_usuarios_username_activo ON usuarios(username, activo)",
            "CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email)",
            "CREATE INDEX IF NOT EXISTS idx_usuarios_rol ON usuarios(rol_id)",
            
            # Índices para ventas (con usuario_id si existe)
            "CREATE INDEX IF NOT EXISTS idx_ventas_fecha_usuario ON ventas(fecha_venta, usuario_id)",
            "CREATE INDEX IF NOT EXISTS idx_ventas_estado_fecha ON ventas(estado, fecha_venta)",
            
            # Índices para sesiones
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_user_active ON user_sessions(user_id, active)",
            
            # Índices para configuraciones
            "CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(config_key)",
            "CREATE INDEX IF NOT EXISTS idx_system_config_category ON system_config(category)"
        ]
        
        success_count = 0
        for index_sql in indexes:
            try:
                self.cursor.execute(index_sql)
                index_name = index_sql.split('idx_')[1].split(' ')[0]
                print(f"   ✅ Índice creado: {index_name}")
                success_count += 1
            except Exception as e:
                print(f"   ⚠️ Error en índice: {e}")
        
        self.connection.commit()
        print(f"✅ {success_count} índices creados")
    
    def insert_improved_default_data(self):
        """Insertar datos por defecto mejorados"""
        print("📝 Insertando datos por defecto mejorados...")
        
        # Configuraciones del sistema
        configs = [
            ('app.name', 'AlmacénPro', 'STRING', 'SYSTEM', 'Nombre de la aplicación'),
            ('app.version', '2.0.0', 'STRING', 'SYSTEM', 'Versión de la aplicación'),
            ('company.name', 'Mi Empresa', 'STRING', 'COMPANY', 'Nombre de la empresa'),
            ('pos.default_tax_rate', '21.00', 'DECIMAL', 'POS', 'Tasa de impuesto por defecto'),
            ('inventory.low_stock_threshold', '10', 'INTEGER', 'INVENTORY', 'Umbral de stock bajo'),
            ('backup.auto_enabled', '1', 'BOOLEAN', 'BACKUP', 'Backup automático habilitado'),
            ('backup.interval_hours', '24', 'INTEGER', 'BACKUP', 'Intervalo de backup en horas'),
            ('security.session_timeout', '480', 'INTEGER', 'SECURITY', 'Timeout de sesión en minutos')
        ]
        
        try:
            for config in configs:
                self.cursor.execute("""
                    INSERT OR IGNORE INTO system_config 
                    (config_key, config_value, data_type, category, description)
                    VALUES (?, ?, ?, ?, ?)
                """, config)
            
            self.connection.commit()
            print(f"   ✅ {len(configs)} configuraciones insertadas")
            
        except Exception as e:
            print(f"   ❌ Error insertando configuraciones: {e}")
    
    def run_full_upgrade(self):
        """Ejecutar upgrade completo"""
        try:
            print("🚀 Iniciando upgrade completo de base de datos...")
            print(f"📁 Base de datos: {self.db_path}")
            
            # Crear backup
            backup_path = self.create_backup()
            if not backup_path:
                print("❌ No se pudo crear backup. Abortando.")
                return False
            
            # Conectar
            self.connect()
            
            # Aplicar upgrades
            self.apply_essential_upgrades()
            self.create_improved_indexes()
            self.insert_improved_default_data()
            
            # Análisis final
            print("\n📊 Análisis final de base de datos:")
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in self.cursor.fetchall()]
            print(f"   📋 Tablas: {len(tables)}")
            
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row[0] for row in self.cursor.fetchall()]
            print(f"   📑 Índices: {len(indexes)}")
            
            print("✅ Upgrade completado exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error durante upgrade: {e}")
            logger.error(f"Error en upgrade de base de datos: {e}")
            return False
        finally:
            self.disconnect()

def main():
    """Función principal"""
    print("=" * 60)
    print("🔧 AlmacénPro - Upgrade de Base de Datos")
    print("=" * 60)
    
    upgrader = DatabaseUpgrader()
    success = upgrader.run_full_upgrade()
    
    if success:
        print("\n✅ ¡Upgrade completado! Puedes ejecutar la aplicación ahora.")
    else:
        print("\n❌ Upgrade falló. Revisa los logs para más detalles.")

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    main()