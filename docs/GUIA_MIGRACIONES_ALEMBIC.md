# Guía de Migraciones con Alembic - AlmacénPro v2.0

## Introducción

Este documento explica cómo utilizar el sistema de migraciones de base de datos implementado con **Alembic** para AlmacénPro v2.0. El sistema permite versionar y aplicar cambios en la estructura de la base de datos de forma controlada y reversible.

## Características del Sistema

- ✅ **SQLite compatible**: Configurado específicamente para SQLite con soporte para ALTER TABLE
- ✅ **Migraciones versionadas**: Cada cambio tiene un identificador único
- ✅ **Reversible**: Posibilidad de revertir cambios (downgrade)
- ✅ **Autogeneración**: Detección automática de cambios en modelos
- ✅ **Configuración por entorno**: Usa variables de entorno para configuración
- ✅ **Script de gestión**: Wrapper simplificado para comandos Alembic

## Estructura de Archivos

```
F:/almacen/
├── alembic.ini                     # Configuración principal de Alembic
├── database/
│   ├── migrate.py                  # Script de gestión de migraciones
│   └── migrations/
│       ├── env.py                  # Configuración del entorno de migraciones
│       ├── script.py.mako          # Plantilla para nuevas migraciones
│       └── versions/               # Archivos de migración
│           ├── 001_initial_schema.py
│           └── 002_add_detalle_ventas_created_at.py
└── config/
    └── env_config.py               # Configuración por variables de entorno
```

## Configuración Inicial

### 1. Variables de Entorno

Cree el archivo `.env` basándose en `.env.example`:

```bash
# Base de datos
DATABASE_TYPE=sqlite
SQLITE_PATH=data/almacen_pro.db

# Desarrollo
DEBUG=false
LOG_LEVEL=INFO
ENABLE_SQL_LOGGING=false
```

### 2. Instalación de Dependencias

Las dependencias ya están incluidas en `requirements.txt`:

```bash
pip install alembic>=1.8.0,<2.0.0
pip install SQLAlchemy>=1.4.0,<2.0.0
```

### 3. Inicialización (Solo Primera Vez)

```bash
python database/migrate.py init
```

## Comandos Disponibles

### Script de Gestión (Recomendado)

El script `database/migrate.py` proporciona una interfaz simplificada:

```bash
# Ver ayuda
python database/migrate.py --help

# Inicializar sistema de migraciones
python database/migrate.py init

# Crear nueva migración manual
python database/migrate.py create "Agregar tabla productos_variantes"

# Crear migración automática (detecta cambios en modelos)
python database/migrate.py create "Auto-detectar cambios" --auto

# Aplicar todas las migraciones pendientes
python database/migrate.py upgrade

# Aplicar hasta una revisión específica
python database/migrate.py upgrade 002

# Revertir a una revisión anterior
python database/migrate.py downgrade 001

# Ver revisión actual
python database/migrate.py current

# Ver historial de migraciones
python database/migrate.py history

# Ver migraciones pendientes
python database/migrate.py pending
```

### Comandos Alembic Directos (Avanzado)

Si necesita usar Alembic directamente:

```bash
# Desde el directorio raíz del proyecto
alembic -c alembic.ini current
alembic -c alembic.ini upgrade head
alembic -c alembic.ini downgrade -1
alembic -c alembic.ini history --verbose
```

## Ejemplos de Uso

### 1. Aplicar Migraciones Iniciales

```bash
# Primera vez - aplicar esquema inicial
python database/migrate.py upgrade
```

### 2. Crear Nueva Migración Manual

```bash
# Crear migración para nueva tabla
python database/migrate.py create "Agregar tabla auditoria"
```

Esto crea un archivo en `database/migrations/versions/` que puede editar:

```python
def upgrade() -> None:
    """Aplicar migración"""
    op.create_table('auditoria',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tabla', sa.String(50), nullable=False),
        sa.Column('operacion', sa.String(10), nullable=False),
        sa.Column('usuario_id', sa.Integer()),
        sa.Column('fecha', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'])
    )

def downgrade() -> None:
    """Revertir migración"""
    op.drop_table('auditoria')
```

### 3. Migración Automática (Experimental)

```bash
# Detectar cambios automáticamente en modelos
python database/migrate.py create "Auto-detectar cambios" --auto
```

**Nota**: La autogeneración requiere que los modelos estén definidos con SQLAlchemy en `database/models.py` con una clase `Base`.

### 4. Ejemplo Práctico: Agregar Nueva Columna

```bash
# Crear migración
python database/migrate.py create "Agregar campo observaciones a productos"
```

Editar el archivo generado:

```python
def upgrade() -> None:
    """Agregar columna observaciones a productos"""
    with op.batch_alter_table('productos', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('observaciones', sa.Text(), nullable=True)
        )

def downgrade() -> None:
    """Eliminar columna observaciones de productos"""
    with op.batch_alter_table('productos', schema=None) as batch_op:
        batch_op.drop_column('observaciones')
```

Aplicar la migración:

```bash
python database/migrate.py upgrade
```

## Consideraciones Especiales para SQLite

### 1. Operaciones ALTER TABLE Limitadas

SQLite tiene limitaciones para modificar tablas. Alembic usa `batch_alter_table` para superar esto:

```python
# CORRECTO para SQLite
with op.batch_alter_table('productos', schema=None) as batch_op:
    batch_op.add_column(sa.Column('nueva_columna', sa.String(100)))
    batch_op.drop_column('columna_vieja')

# INCORRECTO para SQLite
op.add_column('productos', sa.Column('nueva_columna', sa.String(100)))
```

### 2. Foreign Keys

Asegurar que las foreign keys estén habilitadas:

```python
# En el archivo env.py ya está configurado
connection.execute("PRAGMA foreign_keys=ON")
```

### 3. Indices

Crear índices de forma compatible:

```python
def upgrade():
    # Crear tabla
    op.create_table('mi_tabla', ...)
    
    # Crear índice
    op.create_index('idx_mi_tabla_campo', 'mi_tabla', ['campo'])

def downgrade():
    op.drop_index('idx_mi_tabla_campo')
    op.drop_table('mi_tabla')
```

## Flujo de Trabajo Recomendado

### 1. Desarrollo

1. **Hacer cambios** en la estructura de BD (agregar tablas, columnas, etc.)
2. **Crear migración**: `python database/migrate.py create "Descripción del cambio"`
3. **Editar archivo** de migración generado
4. **Probar migración**: `python database/migrate.py upgrade`
5. **Probar reversión**: `python database/migrate.py downgrade -1` y luego `upgrade`

### 2. Testing

```bash
# Aplicar todas las migraciones en base de test
DATABASE_TYPE=sqlite SQLITE_PATH=test_almacen_pro.db python database/migrate.py upgrade

# Ejecutar tests
pytest

# Limpiar base de test si es necesario
rm test_almacen_pro.db
```

### 3. Producción

```bash
# Backup de seguridad antes de migrar
cp data/almacen_pro.db data/almacen_pro_backup_$(date +%Y%m%d_%H%M%S).db

# Ver qué migraciones se van a aplicar
python database/migrate.py pending

# Aplicar migraciones
python database/migrate.py upgrade

# Verificar resultado
python database/migrate.py current
```

## Solución de Problemas

### Error: "No such table: alembic_version"

```bash
# El sistema no está inicializado
python database/migrate.py init
python database/migrate.py upgrade
```

### Error: "PRAGMA foreign_keys=ON failed"

Verificar que la base de datos SQLite sea compatible con foreign keys y esté correctamente configurada.

### Error: "Cannot add a NOT NULL column without a default value"

```python
# En la migración, agregar default value o nullable=True
batch_op.add_column(
    sa.Column('nueva_columna', sa.String(100), 
             nullable=False, server_default='valor_default')
)

# O hacerlo en dos pasos
batch_op.add_column(
    sa.Column('nueva_columna', sa.String(100), nullable=True)
)
# Luego actualizar valores y cambiar a NOT NULL si es necesario
```

### Migración Corrupta

```bash
# Ver revisión actual
python database/migrate.py current

# Marcar una revisión específica como actual sin aplicarla
alembic -c alembic.ini stamp 001

# Luego aplicar desde ahí
python database/migrate.py upgrade
```

## Integración con el Proyecto

### 1. Actualizar DatabaseManager

El `DatabaseManager` actual puede convivir con Alembic. Para nuevas instalaciones, las migraciones pueden reemplazar `_create_all_tables()`.

### 2. CI/CD

Agregar a scripts de despliegue:

```bash
# En el script de despliegue
python database/migrate.py upgrade
```

### 3. Tests de Migración

```python
# tests/test_migrations.py
import pytest
from database.migrate import MigrationManager

def test_migrations_up_and_down():
    manager = MigrationManager()
    
    # Aplicar todas las migraciones
    assert manager.upgrade_database("head")
    
    # Revertir a inicial
    assert manager.downgrade_database("001")
    
    # Aplicar de nuevo
    assert manager.upgrade_database("head")
```

## Próximos Pasos

1. **Integrar con DatabaseManager**: Modificar para usar migraciones en lugar de `_create_all_tables()`
2. **Scripts de backup**: Automatizar backup antes de migraciones
3. **Validaciones**: Agregar validaciones de integridad después de migraciones
4. **Documentar cambios**: Política de documentación de cada migración

## Referencias

- [Documentación oficial de Alembic](https://alembic.sqlalchemy.org/)
- [SQLite ALTER TABLE limitations](https://www.sqlite.org/lang_altertable.html)
- [Alembic SQLite batch operations](https://alembic.sqlalchemy.org/en/latest/batch.html)