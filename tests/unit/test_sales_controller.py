"""
Unit tests for SalesController
"""

import pytest
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QWidget
from controllers.sales_controller import SalesController


class TestSalesController:
    """Test suite for SalesController"""

    @pytest.fixture
    def controller(self, qapp, mock_managers, current_user):
        """Create SalesController instance for testing"""
        with patch('controllers.sales_controller.uic.loadUi'):
            controller = SalesController(mock_managers, current_user)
            yield controller

    def test_initialization(self, controller, mock_managers, current_user):
        """Test controller initialization"""
        assert controller.managers == mock_managers
        assert controller.current_user == current_user
        assert controller.sales_manager == mock_managers['sales']
        assert controller.product_manager == mock_managers['product']
        assert controller.customer_manager == mock_managers['customer']

    def test_get_ui_file_path(self, controller):
        """Test UI file path resolution"""
        ui_path = controller.get_ui_file_path()
        assert ui_path.endswith('views/forms/sales_widget.ui')

    def test_setup_ui(self, controller, current_user):
        """Test UI setup"""
        # Mock UI elements
        controller.lblUsuario = MagicMock()
        controller.lblFechaHora = MagicMock()
        controller.cboClientes = MagicMock()
        controller.tablaProductos = MagicMock()
        controller.tablaCarrito = MagicMock()
        
        controller.setup_ui()
        
        # Verify user info is set
        expected_text = f"Cajero: {current_user.get('nombre_completo', 'Usuario')}"
        controller.lblUsuario.setText.assert_called_with(expected_text)

    def test_load_customers(self, controller):
        """Test customer loading"""
        # Mock UI elements
        controller.cboClientes = MagicMock()
        
        # Mock customer data
        mock_customers = [
            {'id': 1, 'nombre': 'Cliente 1', 'apellido': 'Apellido 1'},
            {'id': 2, 'nombre': 'Cliente 2', 'apellido': 'Apellido 2'}
        ]
        controller.customer_manager.get_all_customers.return_value = mock_customers
        
        controller.load_customers()
        
        # Verify customers were loaded
        controller.customer_manager.get_all_customers.assert_called_once()
        assert controller.cboClientes.addItem.call_count >= len(mock_customers)

    def test_search_products(self, controller):
        """Test product search functionality"""
        # Mock UI elements
        controller.txtBuscarProducto = MagicMock()
        controller.txtBuscarProducto.text.return_value = "test product"
        controller.tablaProductos = MagicMock()
        
        # Mock product data
        mock_products = [
            {'id': 1, 'nombre': 'Test Product', 'precio_venta': 100.0},
        ]
        controller.product_manager.search_products.return_value = mock_products
        
        controller.search_products()
        
        # Verify search was performed
        controller.product_manager.search_products.assert_called_once_with("test product")

    def test_add_product_to_cart(self, controller, sample_product):
        """Test adding product to cart"""
        # Mock UI elements
        controller.tablaCarrito = MagicMock()
        controller.update_totals = MagicMock()
        
        # Initialize cart
        controller.cart_items = []
        
        # Add product to cart
        controller.add_product_to_cart(sample_product, quantity=2)
        
        # Verify product was added
        assert len(controller.cart_items) == 1
        assert controller.cart_items[0]['producto_id'] == sample_product['id']
        assert controller.cart_items[0]['cantidad'] == 2

    def test_remove_product_from_cart(self, controller, sample_product):
        """Test removing product from cart"""
        # Setup cart with item
        controller.cart_items = [
            {
                'producto_id': sample_product['id'],
                'nombre': sample_product['nombre'],
                'cantidad': 2,
                'precio_unitario': sample_product['precio_venta']
            }
        ]
        controller.tablaCarrito = MagicMock()
        controller.update_totals = MagicMock()
        
        # Remove product
        controller.remove_product_from_cart(0)  # Remove by index
        
        # Verify product was removed
        assert len(controller.cart_items) == 0

    def test_calculate_totals(self, controller, sample_product):
        """Test totals calculation"""
        # Setup cart with items
        controller.cart_items = [
            {
                'cantidad': 2,
                'precio_unitario': 100.0,
                'descuento_importe': 0.0,
                'impuesto_porcentaje': 21.0
            },
            {
                'cantidad': 1,
                'precio_unitario': 50.0,
                'descuento_importe': 5.0,
                'impuesto_porcentaje': 21.0
            }
        ]
        
        subtotal, tax_total, discount_total, total = controller.calculate_totals()
        
        # Verify calculations
        assert subtotal == 245.0  # (2 * 100) + (1 * 50) - 5
        assert tax_total == 51.45  # 21% of 245
        assert discount_total == 5.0
        assert total == 296.45  # subtotal + tax

    @pytest.mark.parametrize("payment_type", ["EFECTIVO", "TARJETA", "TRANSFERENCIA"])
    def test_process_sale(self, controller, sample_customer, payment_type):
        """Test sale processing with different payment types"""
        # Setup mock UI elements
        controller.cboClientes = MagicMock()
        controller.cboClientes.currentData.return_value = sample_customer
        controller.cboFormaPago = MagicMock()
        controller.cboFormaPago.currentText.return_value = payment_type
        
        # Setup cart
        controller.cart_items = [
            {
                'producto_id': 1,
                'cantidad': 1,
                'precio_unitario': 100.0,
                'descuento_importe': 0.0,
                'impuesto_porcentaje': 21.0
            }
        ]
        
        # Mock sale creation
        mock_sale = {'id': 1, 'numero_venta': 'TEST-001'}
        controller.sales_manager.create_sale.return_value = mock_sale
        
        # Process sale
        result = controller.process_sale()
        
        # Verify sale was created
        assert result is True
        controller.sales_manager.create_sale.assert_called_once()

    def test_clear_cart(self, controller):
        """Test cart clearing"""
        # Setup cart with items
        controller.cart_items = [{'test': 'item'}]
        controller.tablaCarrito = MagicMock()
        controller.update_totals = MagicMock()
        
        # Clear cart
        controller.clear_cart()
        
        # Verify cart is empty
        assert len(controller.cart_items) == 0

    def test_error_handling(self, controller):
        """Test error handling in controller methods"""
        # Mock UI elements
        controller.customer_manager = MagicMock()
        controller.customer_manager.get_all_customers.side_effect = Exception("Database error")
        
        # This should not raise an exception
        try:
            controller.load_customers()
        except Exception:
            pytest.fail("Controller should handle exceptions gracefully")

    def test_signals_emission(self, controller, sample_product):
        """Test that signals are emitted correctly"""
        # Mock signal connections
        controller.sale_completed = MagicMock()
        controller.product_added = MagicMock()
        
        # Setup cart and process
        controller.cart_items = []
        controller.tablaCarrito = MagicMock()
        controller.update_totals = MagicMock()
        
        # Add product (should emit signal)
        controller.add_product_to_cart(sample_product)
        
        # Verify signal emission (would need to be tested with actual Qt signals)
        # This is a placeholder for signal testing