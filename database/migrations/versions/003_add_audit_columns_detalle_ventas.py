"""Add audit columns to detalle_ventas table

Revision ID: 003
Revises: 002
Create Date: 2025-01-11 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add audit columns to detalle_ventas table"""
    
    # Check if table exists first
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    if 'detalle_ventas' not in inspector.get_table_names():
        # Create the table if it doesn't exist
        op.create_table('detalle_ventas',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('venta_id', sa.Integer(), nullable=False),
            sa.Column('producto_id', sa.Integer(), nullable=False),
            sa.Column('cantidad', sa.DECIMAL(8, 3), nullable=False),
            sa.Column('precio_unitario', sa.DECIMAL(10, 2), nullable=False),
            sa.Column('costo_unitario', sa.DECIMAL(10, 2), default=0),
            sa.Column('descuento_porcentaje', sa.DECIMAL(5, 2), default=0),
            sa.Column('descuento_importe', sa.DECIMAL(10, 2), default=0),
            sa.Column('impuesto_porcentaje', sa.DECIMAL(5, 2), default=21),
            sa.Column('impuesto_importe', sa.DECIMAL(10, 2), default=0),
            sa.Column('subtotal_linea', sa.DECIMAL(10, 2), nullable=False),
            sa.ForeignKeyConstraint(['venta_id'], ['ventas.id']),
            sa.ForeignKeyConstraint(['producto_id'], ['productos.id'])
        )
        print("Created detalle_ventas table")
    
    # Get existing columns
    existing_columns = [col['name'] for col in inspector.get_columns('detalle_ventas')]
    
    # Add audit columns using batch operations for SQLite compatibility
    with op.batch_alter_table('detalle_ventas', schema=None) as batch_op:
        
        # Add created_at column if it doesn't exist
        if 'creado_en' not in existing_columns:
            batch_op.add_column(
                sa.Column('creado_en', 
                         sa.TIMESTAMP(), 
                         server_default=sa.text('CURRENT_TIMESTAMP'),
                         nullable=False,
                         comment='Fecha y hora de creación del registro')
            )
            print("Added 'creado_en' column to detalle_ventas")
        
        # Add updated_at column if it doesn't exist
        if 'actualizado_en' not in existing_columns:
            batch_op.add_column(
                sa.Column('actualizado_en', 
                         sa.TIMESTAMP(), 
                         server_default=sa.text('CURRENT_TIMESTAMP'),
                         nullable=False,
                         comment='Fecha y hora de última actualización')
            )
            print("Added 'actualizado_en' column to detalle_ventas")
            
        # Add created_by column if it doesn't exist
        if 'creado_por' not in existing_columns:
            batch_op.add_column(
                sa.Column('creado_por', 
                         sa.Integer(), 
                         nullable=True,
                         comment='ID del usuario que creó el registro')
            )
            print("Added 'creado_por' column to detalle_ventas")
            
        # Add updated_by column if it doesn't exist  
        if 'actualizado_por' not in existing_columns:
            batch_op.add_column(
                sa.Column('actualizado_por', 
                         sa.Integer(), 
                         nullable=True,
                         comment='ID del usuario que actualizó el registro')
            )
            print("Added 'actualizado_por' column to detalle_ventas")
    
    # Update existing records with current timestamp for audit columns
    connection = op.get_bind()
    
    # Only update if the columns were actually added
    update_sql_parts = []
    
    if 'creado_en' not in existing_columns:
        update_sql_parts.append("creado_en = CURRENT_TIMESTAMP")
    if 'actualizado_en' not in existing_columns:
        update_sql_parts.append("actualizado_en = CURRENT_TIMESTAMP")
        
    if update_sql_parts:
        update_sql = f"""
        UPDATE detalle_ventas 
        SET {', '.join(update_sql_parts)}
        WHERE id IN (SELECT id FROM detalle_ventas LIMIT 100)
        """
        connection.execute(sa.text(update_sql))
        print("Updated existing records with audit timestamps")
    
    # Create trigger for auto-updating actualizado_en
    trigger_sql = """
    CREATE TRIGGER IF NOT EXISTS update_detalle_ventas_timestamp 
    AFTER UPDATE ON detalle_ventas
    FOR EACH ROW 
    BEGIN
        UPDATE detalle_ventas 
        SET actualizado_en = CURRENT_TIMESTAMP 
        WHERE id = NEW.id;
    END;
    """
    
    connection.execute(sa.text(trigger_sql))
    print("Created trigger for auto-updating timestamps")


def downgrade() -> None:
    """Remove audit columns from detalle_ventas table"""
    
    # Drop trigger first
    connection = op.get_bind()
    connection.execute(sa.text("DROP TRIGGER IF EXISTS update_detalle_ventas_timestamp"))
    print("Dropped trigger update_detalle_ventas_timestamp")
    
    # Remove audit columns using batch operations
    with op.batch_alter_table('detalle_ventas', schema=None) as batch_op:
        
        # Check which columns exist before dropping
        inspector = sa.inspect(connection)
        existing_columns = [col['name'] for col in inspector.get_columns('detalle_ventas')]
        
        if 'actualizado_por' in existing_columns:
            batch_op.drop_column('actualizado_por')
            print("Dropped 'actualizado_por' column")
            
        if 'creado_por' in existing_columns:
            batch_op.drop_column('creado_por')
            print("Dropped 'creado_por' column")
            
        if 'actualizado_en' in existing_columns:
            batch_op.drop_column('actualizado_en')
            print("Dropped 'actualizado_en' column")
            
        if 'creado_en' in existing_columns:
            batch_op.drop_column('creado_en')
            print("Dropped 'creado_en' column")
    
    print("Downgrade completed - removed all audit columns from detalle_ventas")