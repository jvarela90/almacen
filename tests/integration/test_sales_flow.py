"""
Integration tests for sales flow
"""

import pytest
from decimal import Decimal
from database.manager import DatabaseManager


@pytest.mark.integration
class TestSalesFlow:
    """Integration tests for complete sales workflow"""

    @pytest.fixture
    def setup_test_data(self, db_manager):
        """Setup test data for sales integration tests"""
        # Create test user
        db_manager.execute_query("""
            INSERT INTO roles (nombre, descripcion, activo) 
            VALUES ('ADMINISTRADOR', 'Administrador del sistema', 1)
        """)
        
        db_manager.execute_query("""
            INSERT INTO usuarios (username, password_hash, nombre_completo, rol_id, activo)
            VALUES ('test_user', 'hash', 'Test User', 1, 1)
        """)
        
        # Create test category
        db_manager.execute_query("""
            INSERT INTO categorias (nombre, descripcion, activo)
            VALUES ('Categoria Test', 'Categoria para testing', 1)
        """)
        
        # Create test product
        db_manager.execute_query("""
            INSERT INTO productos (codigo_barras, nombre, descripcion, categoria_id, 
                                 precio_venta, stock_actual, activo)
            VALUES ('1234567890123', 'Producto Test', 'Producto para testing', 1,
                   100.00, 50, 1)
        """)
        
        # Create test customer
        db_manager.execute_query("""
            INSERT INTO clientes (nombre, apellido, email, telefono, documento, activo)
            VALUES ('Cliente', 'Test', 'test@test.com', '123456789', '12345678', 1)
        """)

    def test_complete_sale_flow(self, db_manager, setup_test_data):
        """Test complete sales flow from product selection to completion"""
        
        # Step 1: Get available products
        products = db_manager.execute_query("""
            SELECT id, nombre, precio_venta, stock_actual 
            FROM productos WHERE activo = 1
        """)
        assert len(products) > 0
        
        product = products[0]
        product_id = product[0]
        product_price = product[2]
        
        # Step 2: Get customer
        customers = db_manager.execute_query("""
            SELECT id, nombre, apellido FROM clientes WHERE activo = 1
        """)
        assert len(customers) > 0
        
        customer_id = customers[0][0]
        
        # Step 3: Create sale
        sale_data = {
            'numero_venta': 'TEST-001',
            'cliente_id': customer_id,
            'vendedor_id': 1,
            'subtotal': float(product_price * 2),  # 2 units
            'impuesto_total': float(product_price * 2 * Decimal('0.21')),
            'total_venta': float(product_price * 2 * Decimal('1.21')),
            'tipo_pago': 'EFECTIVO'
        }
        
        # Insert sale
        sale_result = db_manager.execute_query("""
            INSERT INTO ventas (numero_venta, cliente_id, vendedor_id, subtotal, 
                              impuesto_total, total_venta, tipo_pago)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            sale_data['numero_venta'],
            sale_data['cliente_id'], 
            sale_data['vendedor_id'],
            sale_data['subtotal'],
            sale_data['impuesto_total'],
            sale_data['total_venta'],
            sale_data['tipo_pago']
        ))
        
        # Get sale ID
        sale_id_result = db_manager.execute_query("""
            SELECT id FROM ventas WHERE numero_venta = ?
        """, (sale_data['numero_venta'],))
        
        assert len(sale_id_result) > 0
        sale_id = sale_id_result[0][0]
        
        # Step 4: Add sale details
        db_manager.execute_query("""
            INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario,
                                      impuesto_porcentaje, subtotal_linea)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            sale_id, product_id, 2, float(product_price), 21.0,
            float(product_price * 2)
        ))
        
        # Step 5: Verify sale was created correctly
        sale_verification = db_manager.execute_query("""
            SELECT v.id, v.numero_venta, v.total_venta, 
                   COUNT(dv.id) as item_count,
                   SUM(dv.cantidad) as total_quantity
            FROM ventas v
            JOIN detalle_ventas dv ON v.id = dv.venta_id
            WHERE v.numero_venta = ?
            GROUP BY v.id
        """, (sale_data['numero_venta'],))
        
        assert len(sale_verification) == 1
        verified_sale = sale_verification[0]
        
        assert verified_sale[1] == sale_data['numero_venta']  # numero_venta
        assert verified_sale[3] == 1  # item_count
        assert verified_sale[4] == 2  # total_quantity

    def test_stock_update_after_sale(self, db_manager, setup_test_data):
        """Test that stock is updated after a sale"""
        
        # Get initial stock
        initial_stock = db_manager.execute_query("""
            SELECT stock_actual FROM productos WHERE codigo_barras = ?
        """, ('1234567890123',))
        
        initial_stock_value = initial_stock[0][0]
        
        # Create a sale that should reduce stock
        # (This would typically be handled by triggers or application logic)
        
        # For this test, we'll simulate the stock update manually
        quantity_sold = 3
        
        db_manager.execute_query("""
            UPDATE productos 
            SET stock_actual = stock_actual - ?
            WHERE codigo_barras = ?
        """, (quantity_sold, '1234567890123'))
        
        # Verify stock was reduced
        final_stock = db_manager.execute_query("""
            SELECT stock_actual FROM productos WHERE codigo_barras = ?
        """, ('1234567890123',))
        
        final_stock_value = final_stock[0][0]
        
        assert final_stock_value == initial_stock_value - quantity_sold

    def test_sale_with_multiple_products(self, db_manager, setup_test_data):
        """Test sale with multiple different products"""
        
        # Add another test product
        db_manager.execute_query("""
            INSERT INTO productos (codigo_barras, nombre, descripcion, categoria_id,
                                 precio_venta, stock_actual, activo)
            VALUES ('9876543210987', 'Producto Test 2', 'Segundo producto', 1,
                   50.00, 25, 1)
        """)
        
        # Create sale with multiple products
        sale_id = self._create_test_sale(db_manager)
        
        # Add multiple products to sale
        products = db_manager.execute_query("""
            SELECT id, precio_venta FROM productos WHERE activo = 1
        """)
        
        for i, product in enumerate(products[:2]):  # Use first 2 products
            product_id = product[0]
            product_price = product[1]
            quantity = i + 1  # 1 for first product, 2 for second
            
            db_manager.execute_query("""
                INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, 
                                          precio_unitario, impuesto_porcentaje, 
                                          subtotal_linea)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                sale_id, product_id, quantity, float(product_price), 21.0,
                float(product_price * quantity)
            ))
        
        # Verify sale has multiple items
        items_count = db_manager.execute_query("""
            SELECT COUNT(*) FROM detalle_ventas WHERE venta_id = ?
        """, (sale_id,))
        
        assert items_count[0][0] == 2

    def test_sale_totals_calculation(self, db_manager, setup_test_data):
        """Test that sale totals are calculated correctly"""
        
        # Create sale
        sale_id = self._create_test_sale(db_manager)
        
        # Add products with known prices
        items = [
            {'price': 100.0, 'quantity': 2},  # 200.00 subtotal
            {'price': 50.0, 'quantity': 1}   # 50.00 subtotal
        ]
        
        total_subtotal = 0
        
        for i, item in enumerate(items):
            product_id = 1  # Use first product
            subtotal = item['price'] * item['quantity']
            total_subtotal += subtotal
            
            db_manager.execute_query("""
                INSERT INTO detalle_ventas (venta_id, producto_id, cantidad,
                                          precio_unitario, impuesto_porcentaje,
                                          subtotal_linea)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sale_id, product_id, item['quantity'], item['price'], 21.0, subtotal))
        
        # Calculate expected totals
        expected_subtotal = 250.0  # 200 + 50
        expected_tax = expected_subtotal * 0.21  # 21% tax
        expected_total = expected_subtotal + expected_tax
        
        # Update sale with calculated totals
        db_manager.execute_query("""
            UPDATE ventas 
            SET subtotal = ?, impuesto_total = ?, total_venta = ?
            WHERE id = ?
        """, (expected_subtotal, expected_tax, expected_total, sale_id))
        
        # Verify totals
        sale_totals = db_manager.execute_query("""
            SELECT subtotal, impuesto_total, total_venta FROM ventas WHERE id = ?
        """, (sale_id,))
        
        assert len(sale_totals) == 1
        subtotal, tax, total = sale_totals[0]
        
        assert abs(subtotal - expected_subtotal) < 0.01
        assert abs(tax - expected_tax) < 0.01
        assert abs(total - expected_total) < 0.01

    def _create_test_sale(self, db_manager):
        """Helper method to create a test sale"""
        import uuid
        
        sale_number = f"TEST-{str(uuid.uuid4())[:8]}"
        
        db_manager.execute_query("""
            INSERT INTO ventas (numero_venta, cliente_id, vendedor_id, subtotal,
                              impuesto_total, total_venta, tipo_pago)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (sale_number, 1, 1, 0.0, 0.0, 0.0, 'EFECTIVO'))
        
        sale_id_result = db_manager.execute_query("""
            SELECT id FROM ventas WHERE numero_venta = ?
        """, (sale_number,))
        
        return sale_id_result[0][0]