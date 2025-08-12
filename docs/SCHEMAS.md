# Esquema de base de datos ERP/POS

## Tablas principales
- **productos**: información de cada producto.
- **categorias**: clasificación de productos.
- **clientes**: datos de clientes.
- **proveedores**: datos de proveedores.
- **ventas**: registros de ventas realizadas.
- **detalle_ventas**: productos vendidos por venta.
- **compras**: registros de compras.
- **detalle_compras**: productos comprados por compra.
- **usuarios**: credenciales y roles.
- **roles**: permisos del sistema.

## Relaciones
- Un producto pertenece a una categoría.
- Una venta tiene múltiples productos (detalle_ventas).
- Una compra tiene múltiples productos (detalle_compras).
- Un usuario pertenece a un rol.

## Integridad y optimización
- Claves primarias y foráneas correctamente definidas.
- Índices en campos de búsqueda frecuente.
- Triggers para auditoría y control de stock.
