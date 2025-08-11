"""Agregar columna creado_en a detalle_ventas

Revision ID: 002
Revises: 001
Create Date: 2025-01-11 12:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Agregar columna creado_en a la tabla detalle_ventas"""
    
    # SQLite requires special handling for ALTER TABLE operations
    with op.batch_alter_table('detalle_ventas', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('creado_en', 
                     sa.TIMESTAMP(), 
                     server_default=sa.text('CURRENT_TIMESTAMP'),
                     nullable=False)
        )
        
        # Agregar también columna actualizado_en para consistencia
        batch_op.add_column(
            sa.Column('actualizado_en', 
                     sa.TIMESTAMP(), 
                     server_default=sa.text('CURRENT_TIMESTAMP'),
                     nullable=False)
        )
    
    # Actualizar registros existentes con la fecha actual
    # Esto es importante porque server_default solo afecta nuevos registros
    connection = op.get_bind()
    connection.execute(
        sa.text("""
        UPDATE detalle_ventas 
        SET creado_en = CURRENT_TIMESTAMP,
            actualizado_en = CURRENT_TIMESTAMP
        WHERE creado_en IS NULL
        """)
    )


def downgrade() -> None:
    """Eliminar columnas creado_en y actualizado_en de detalle_ventas"""
    
    with op.batch_alter_table('detalle_ventas', schema=None) as batch_op:
        batch_op.drop_column('actualizado_en')
        batch_op.drop_column('creado_en')