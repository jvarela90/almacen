# Guía de Migraciones Alembic - AlmacénPro v2.0 (Actualizada)

## 🎯 Resumen Ejecutivo

Sistema de migraciones estructuradas con **Alembic** para gestionar cambios en la base de datos SQLite de forma controlada, versionada y reversible.

## 🏗️ Estructura Implementada

```
database/
├── migrate.py                      # Script principal de gestión
├── migrations/
│   ├── env.py                     # Configuración entorno Alembic
│   ├── script.py.mako             # Plantilla para nuevas migraciones
│   └── versions/                  # Migraciones versionadas
│       ├── 001_initial_schema.py         # Esquema inicial completo
│       ├── 002_add_detalle_ventas_created_at.py  # Ejemplo columna timestamp
│       └── 003_add_audit_columns_detalle_ventas.py  # Columnas auditoría
├── alembic.ini                    # Configuración principal Alembic
└── manager.py                     # DatabaseManager existente
```

## 🚀 Comandos Principales

### Gestión de Migraciones

```bash
# Ver estado actual
python database/migrate.py current

# Ver historial de migraciones
python database/migrate.py history

# Aplicar todas las migraciones pendientes
python database/migrate.py upgrade

# Aplicar hasta una revisión específica
python database/migrate.py upgrade 002

# Revertir a revisión anterior  
python database/migrate.py downgrade 001

# Crear nueva migración
python database/migrate.py create "Descripción del cambio"

# Ver migraciones pendientes
python database/migrate.py pending
```

### Migraciones Automáticas (Experimental)

```bash
# Generar migración automáticamente desde cambios en modelos
python database/migrate.py create "Auto-detectar cambios" --auto
```

## 📝 Migraciones Implementadas

### 1. **001_initial_schema.py** - Esquema Base
- **Descripción**: Schema inicial completo del sistema
- **Tablas**: usuarios, roles, clientes, productos, ventas, detalle_ventas
- **Características**:
  - Estructura normalizada completa
  - Índices optimizados
  - Foreign key constraints
  - Datos iniciales (roles, usuario admin)

### 2. **002_add_detalle_ventas_created_at.py** - Timestamps Básicos
- **Descripción**: Agregar columnas de timestamp a detalle_ventas
- **Cambios**:
  - `creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
  - `actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
- **Características**:
  - Compatible con SQLite usando batch operations
  - Actualiza registros existentes automáticamente

### 3. **003_add_audit_columns_detalle_ventas.py** - Auditoría Completa  
- **Descripción**: Sistema completo de auditoría para detalle_ventas
- **Cambios**:
  - `creado_en TIMESTAMP` (fecha creación)
  - `actualizado_en TIMESTAMP` (fecha actualización) 
  - `creado_por INTEGER` (usuario creador)
  - `actualizado_por INTEGER` (usuario actualizador)
  - Trigger automático para actualizar timestamps
- **Características**:
  - Verificación de existencia de columnas
  - Trigger SQL para auto-actualización
  - Rollback completo en downgrade

## 🛠️ Crear Nueva Migración - Ejemplo Práctico

### Ejemplo: Agregar Categorías de Productos

```bash
# 1. Crear archivo de migración
python database/migrate.py create "Add product categories table"
```

Esto genera: `004_add_product_categories_table.py`

```python
"""Add product categories table

Revision ID: 004
Revises: 003
Create Date: 2025-01-11 13:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '004'
down_revision = '003'

def upgrade() -> None:
    """Crear tabla categorias_productos"""
    
    # Crear tabla con batch operations para SQLite
    op.create_table('categorias_productos',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('nombre', sa.String(100), nullable=False),
        sa.Column('descripcion', sa.Text()),
        sa.Column('categoria_padre_id', sa.Integer()),
        sa.Column('activo', sa.Boolean(), default=True),
        sa.Column('orden_visualizacion', sa.Integer(), default=0),
        sa.Column('creado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('actualizado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['categoria_padre_id'], ['categorias_productos.id'])
    )
    
    # Crear índices
    op.create_index('idx_categorias_nombre', 'categorias_productos', ['nombre'])
    op.create_index('idx_categorias_activo', 'categorias_productos', ['activo'])
    
    # Insertar datos iniciales
    connection = op.get_bind()
    connection.execute(sa.text("""
        INSERT INTO categorias_productos (nombre, descripcion, orden_visualizacion) 
        VALUES 
        ('General', 'Categoría general para productos', 1),
        ('Alimentación', 'Productos alimenticios', 2),
        ('Bebidas', 'Bebidas y líquidos', 3),
        ('Limpieza', 'Productos de limpieza', 4)
    """))

def downgrade() -> None:
    """Eliminar tabla categorias_productos"""
    op.drop_index('idx_categorias_activo')
    op.drop_index('idx_categorias_nombre') 
    op.drop_table('categorias_productos')
```

### Aplicar la Migración

```bash
# Aplicar nueva migración
python database/migrate.py upgrade

# Verificar aplicación
python database/migrate.py current
```

## 🔍 Mejores Prácticas

### 1. **Nomenclatura de Archivos**
- `001_initial_schema.py` - Esquema inicial
- `002_add_table_name.py` - Agregar tabla
- `003_modify_column_table.py` - Modificar columna  
- `004_remove_deprecated_fields.py` - Eliminar campos

### 2. **Estructura de Migración**
```python
"""Descripción clara del cambio

Revision ID: 00X
Revises: 00Y  
Create Date: YYYY-MM-DD HH:MM:SS
"""

def upgrade() -> None:
    """Descripción de lo que hace la migración"""
    
    # 1. Verificar estado actual si es necesario
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # 2. Hacer cambios usando batch operations para SQLite
    with op.batch_alter_table('tabla_name') as batch_op:
        batch_op.add_column(sa.Column('nueva_columna', sa.String(100)))
    
    # 3. Crear índices si es necesario
    op.create_index('idx_tabla_columna', 'tabla_name', ['nueva_columna'])
    
    # 4. Migrar datos existentes si es necesario
    connection.execute(sa.text("UPDATE tabla_name SET nueva_columna = 'default'"))

def downgrade() -> None:
    """Revertir todos los cambios de upgrade()"""
    # Orden inverso de operaciones
```

### 3. **Batch Operations para SQLite**
```python
# ✅ CORRECTO - Usar batch operations
with op.batch_alter_table('productos', schema=None) as batch_op:
    batch_op.add_column(sa.Column('nueva_columna', sa.String(100)))
    batch_op.drop_column('columna_vieja')

# ❌ INCORRECTO - No funciona con SQLite
op.add_column('productos', sa.Column('nueva_columna', sa.String(100)))
```

### 4. **Verificación de Existencia**
```python
def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Verificar si tabla existe
    if 'mi_tabla' not in inspector.get_table_names():
        op.create_table('mi_tabla', ...)
    
    # Verificar si columna existe
    existing_columns = [col['name'] for col in inspector.get_columns('mi_tabla')]
    if 'nueva_columna' not in existing_columns:
        with op.batch_alter_table('mi_tabla') as batch_op:
            batch_op.add_column(sa.Column('nueva_columna', sa.String(100)))
```

## 🔄 Flujo de Trabajo Recomendado

### Desarrollo Local
```bash
# 1. Hacer cambios en el esquema/modelo
# 2. Crear migración
python database/migrate.py create "Descripción del cambio"

# 3. Editar archivo de migración generado
# 4. Probar migración
python database/migrate.py upgrade

# 5. Probar rollback
python database/migrate.py downgrade -1
python database/migrate.py upgrade

# 6. Confirmar estado
python database/migrate.py current
```

### Producción
```bash
# 1. Backup antes de migrar
cp data/almacen_pro.db data/almacen_pro_backup_$(date +%Y%m%d_%H%M%S).db

# 2. Ver cambios pendientes
python database/migrate.py pending

# 3. Aplicar migraciones
python database/migrate.py upgrade

# 4. Verificar resultado
python database/migrate.py current
python database/migrate.py history
```

## 🔧 Integración con CI/CD

El workflow de GitHub Actions ya incluye tests de migración:

```yaml
- name: Run database migrations test
  run: |
    python database/migrate.py upgrade
    python database/migrate.py current
```

## 🚨 Solución de Problemas

### Error: "No such table: alembic_version"
```bash
# Inicializar tabla de versiones
python database/migrate.py upgrade
```

### Error: "UNIQUE constraint failed"
```bash
# Verificar datos duplicados antes de crear constrains unique
python database/migrate.py downgrade -1
# Limpiar datos duplicados manualmente
python database/migrate.py upgrade
```

### Error: "Cannot add NOT NULL column"
```python
# ✅ SOLUCIÓN - Usar default value
batch_op.add_column(
    sa.Column('nueva_columna', sa.String(100), 
             nullable=False, server_default='default_value')
)

# O hacer en dos pasos
batch_op.add_column(
    sa.Column('nueva_columna', sa.String(100), nullable=True)
)
# Actualizar valores
connection.execute(sa.text("UPDATE tabla SET nueva_columna = 'valor'"))
# Cambiar a NOT NULL
batch_op.alter_column('nueva_columna', nullable=False)
```

## 📊 Estado Actual del Sistema

### Migraciones Aplicadas: ✅ 3/3
1. ✅ **001_initial_schema** - Esquema base completo
2. ✅ **002_add_detalle_ventas_created_at** - Timestamps básicos  
3. ✅ **003_add_audit_columns_detalle_ventas** - Auditoría completa

### Próximas Migraciones Sugeridas:
- **004** - Categorías de productos mejoradas
- **005** - Sistema de permisos granulares
- **006** - Tablas de auditoría centralizadas
- **007** - Índices de performance optimizados

## 🎯 Comandos de Referencia Rápida

```bash
# Estados y información
python database/migrate.py current      # Revisión actual
python database/migrate.py history      # Historial completo
python database/migrate.py pending      # Pendientes

# Aplicar cambios
python database/migrate.py upgrade      # Todas las pendientes
python database/migrate.py upgrade 003  # Hasta revisión específica

# Revertir cambios  
python database/migrate.py downgrade 002 # A revisión específica
python database/migrate.py downgrade -1  # Una revisión atrás

# Crear migraciones
python database/migrate.py create "Mensaje" # Manual
python database/migrate.py create "Auto" --auto # Automática
```

---

**🎉 Sistema de Migraciones Alembic Completamente Configurado y Documentado**