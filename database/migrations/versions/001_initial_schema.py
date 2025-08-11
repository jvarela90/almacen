"""Esquema inicial de AlmacénPro v2.0

Revision ID: 001
Revises: 
Create Date: 2025-01-11 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Crear esquema inicial completo de AlmacénPro v2.0"""
    
    # ========================================================================
    # ROLES Y USUARIOS
    # ========================================================================
    
    op.create_table('roles',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('nombre', sa.String(50), nullable=False, unique=True),
        sa.Column('descripcion', sa.Text()),
        sa.Column('permisos', sa.Text()),
        sa.Column('activo', sa.Boolean(), default=True),
        sa.Column('creado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('creado_por', sa.Integer()),
        sa.Column('actualizado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('actualizado_por', sa.Integer()),
        sa.ForeignKeyConstraint(['creado_por'], ['usuarios.id'])
    )
    
    op.create_table('usuarios',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('username', sa.String(50), nullable=False, unique=True),
        sa.Column('email', sa.String(100), unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('nombre_completo', sa.String(100)),
        sa.Column('telefono', sa.String(20)),
        sa.Column('numero_documento', sa.String(20)),
        sa.Column('direccion', sa.Text()),
        sa.Column('rol_id', sa.Integer(), nullable=False),
        sa.Column('activo', sa.Boolean(), default=True),
        sa.Column('ultimo_acceso', sa.TIMESTAMP()),
        sa.Column('intentos_fallidos', sa.Integer(), default=0),
        sa.Column('bloqueado_hasta', sa.TIMESTAMP()),
        sa.Column('token_recuperacion', sa.String(255)),
        sa.Column('token_expira_en', sa.TIMESTAMP()),
        sa.Column('configuracion_personal', sa.Text()),
        sa.Column('creado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('creado_por', sa.Integer()),
        sa.Column('actualizado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('actualizado_por', sa.Integer()),
        sa.ForeignKeyConstraint(['rol_id'], ['roles.id']),
        sa.ForeignKeyConstraint(['creado_por'], ['usuarios.id'])
    )
    
    # ========================================================================
    # CLIENTES
    # ========================================================================
    
    op.create_table('clientes',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('nombre', sa.String(100), nullable=False),
        sa.Column('apellido', sa.String(100)),
        sa.Column('email', sa.String(100)),
        sa.Column('telefono', sa.String(20)),
        sa.Column('documento', sa.String(20)),
        sa.Column('tipo_documento', sa.String(10)),
        sa.Column('direccion', sa.Text()),
        sa.Column('ciudad', sa.String(50)),
        sa.Column('provincia', sa.String(50)),
        sa.Column('codigo_postal', sa.String(10)),
        sa.Column('limite_credito', sa.DECIMAL(10, 2), default=0),
        sa.Column('descuento_porcentaje', sa.DECIMAL(5, 2), default=0),
        sa.Column('categoria_id', sa.Integer()),
        sa.Column('vendedor_asignado_id', sa.Integer()),
        sa.Column('activo', sa.Boolean(), default=True),
        sa.Column('notas', sa.Text()),
        sa.Column('creado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('creado_por', sa.Integer()),
        sa.Column('actualizado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('actualizado_por', sa.Integer()),
        sa.ForeignKeyConstraint(['categoria_id'], ['categorias_clientes.id']),
        sa.ForeignKeyConstraint(['vendedor_asignado_id'], ['usuarios.id']),
        sa.ForeignKeyConstraint(['creado_por'], ['usuarios.id'])
    )
    
    # ========================================================================
    # PRODUCTOS
    # ========================================================================
    
    op.create_table('categorias',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('nombre', sa.String(100), nullable=False, unique=True),
        sa.Column('descripcion', sa.Text()),
        sa.Column('categoria_padre_id', sa.Integer()),
        sa.Column('nivel', sa.Integer(), default=0),
        sa.Column('activo', sa.Boolean(), default=True),
        sa.Column('creado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('creado_por', sa.Integer()),
        sa.ForeignKeyConstraint(['categoria_padre_id'], ['categorias.id']),
        sa.ForeignKeyConstraint(['creado_por'], ['usuarios.id'])
    )
    
    op.create_table('productos',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('codigo_barras', sa.String(50), unique=True),
        sa.Column('codigo_interno', sa.String(50)),
        sa.Column('nombre', sa.String(200), nullable=False),
        sa.Column('descripcion', sa.Text()),
        sa.Column('categoria_id', sa.Integer()),
        sa.Column('marca', sa.String(100)),
        sa.Column('modelo', sa.String(100)),
        sa.Column('unidad_medida', sa.String(20), default='unidad'),
        sa.Column('precio_compra', sa.DECIMAL(10, 2), default=0),
        sa.Column('precio_venta', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('precio_mayorista', sa.DECIMAL(10, 2)),
        sa.Column('stock_actual', sa.DECIMAL(8, 3), default=0),
        sa.Column('stock_minimo', sa.DECIMAL(8, 3), default=0),
        sa.Column('stock_maximo', sa.DECIMAL(8, 3), default=0),
        sa.Column('punto_reposicion', sa.DECIMAL(8, 3), default=0),
        sa.Column('ubicacion_fisica', sa.String(100)),
        sa.Column('peso', sa.DECIMAL(8, 3)),
        sa.Column('dimensiones', sa.String(100)),
        sa.Column('impuesto_porcentaje', sa.DECIMAL(5, 2), default=21),
        sa.Column('activo', sa.Boolean(), default=True),
        sa.Column('permite_venta_negativo', sa.Boolean(), default=False),
        sa.Column('controla_stock', sa.Boolean(), default=True),
        sa.Column('imagen_url', sa.String(500)),
        sa.Column('notas', sa.Text()),
        sa.Column('creado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('creado_por', sa.Integer()),
        sa.Column('actualizado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('actualizado_por', sa.Integer()),
        sa.ForeignKeyConstraint(['categoria_id'], ['categorias.id']),
        sa.ForeignKeyConstraint(['creado_por'], ['usuarios.id'])
    )
    
    # ========================================================================
    # VENTAS Y DETALLES
    # ========================================================================
    
    op.create_table('ventas',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('numero_venta', sa.String(20), nullable=False, unique=True),
        sa.Column('fecha_venta', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('cliente_id', sa.Integer()),
        sa.Column('vendedor_id', sa.Integer(), nullable=False),
        sa.Column('tipo_comprobante', sa.String(20), default='TICKET'),
        sa.Column('punto_venta', sa.Integer(), default=1),
        sa.Column('numero_comprobante', sa.String(20)),
        sa.Column('subtotal', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('descuento_total', sa.DECIMAL(10, 2), default=0),
        sa.Column('impuesto_total', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('total_venta', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('tipo_pago', sa.String(20), nullable=False),
        sa.Column('estado', sa.String(20), default='COMPLETADO'),
        sa.Column('observaciones', sa.Text()),
        sa.Column('anulada', sa.Boolean(), default=False),
        sa.Column('fecha_anulacion', sa.TIMESTAMP()),
        sa.Column('motivo_anulacion', sa.String(200)),
        sa.Column('impreso', sa.Boolean(), default=False),
        sa.Column('creado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('creado_por', sa.Integer()),
        sa.ForeignKeyConstraint(['cliente_id'], ['clientes.id']),
        sa.ForeignKeyConstraint(['vendedor_id'], ['usuarios.id']),
        sa.ForeignKeyConstraint(['creado_por'], ['usuarios.id'])
    )
    
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
    
    # ========================================================================
    # ÍNDICES PRINCIPALES
    # ========================================================================
    
    # Usuarios
    op.create_index('idx_usuarios_username', 'usuarios', ['username'])
    op.create_index('idx_usuarios_email', 'usuarios', ['email'])
    op.create_index('idx_usuarios_rol', 'usuarios', ['rol_id'])
    
    # Clientes
    op.create_index('idx_clientes_nombre', 'clientes', ['nombre'])
    op.create_index('idx_clientes_documento', 'clientes', ['documento'])
    op.create_index('idx_clientes_email', 'clientes', ['email'])
    
    # Productos
    op.create_index('idx_productos_codigo_barras', 'productos', ['codigo_barras'])
    op.create_index('idx_productos_codigo_interno', 'productos', ['codigo_interno'])
    op.create_index('idx_productos_nombre', 'productos', ['nombre'])
    op.create_index('idx_productos_categoria', 'productos', ['categoria_id'])
    
    # Ventas
    op.create_index('idx_ventas_fecha', 'ventas', ['fecha_venta'])
    op.create_index('idx_ventas_cliente', 'ventas', ['cliente_id'])
    op.create_index('idx_ventas_vendedor', 'ventas', ['vendedor_id'])
    op.create_index('idx_ventas_numero', 'ventas', ['numero_venta'])
    
    # Detalle ventas
    op.create_index('idx_detalle_ventas_venta', 'detalle_ventas', ['venta_id'])
    op.create_index('idx_detalle_ventas_producto', 'detalle_ventas', ['producto_id'])


def downgrade() -> None:
    """Eliminar esquema completo"""
    
    # Eliminar en orden inverso debido a foreign keys
    op.drop_table('detalle_ventas')
    op.drop_table('ventas')
    op.drop_table('productos')
    op.drop_table('categorias')
    op.drop_table('clientes')
    op.drop_table('usuarios')
    op.drop_table('roles')