"""
Pytest configuration and fixtures for AlmacénPro v2.0 tests
"""

import os
import sys
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

# PyQt5 setup for testing
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PyQt5.QtWidgets import QApplication
from database.manager import DatabaseManager


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for the entire test session"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    if app:
        app.quit()


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
        temp_db_path = temp_file.name
    
    # Set environment variable for temporary database
    original_path = os.environ.get('SQLITE_PATH')
    os.environ['SQLITE_PATH'] = temp_db_path
    
    yield temp_db_path
    
    # Cleanup
    if original_path:
        os.environ['SQLITE_PATH'] = original_path
    elif 'SQLITE_PATH' in os.environ:
        del os.environ['SQLITE_PATH']
    
    try:
        os.unlink(temp_db_path)
        # Also remove WAL and SHM files if they exist
        for ext in ['-wal', '-shm']:
            wal_file = temp_db_path + ext
            if os.path.exists(wal_file):
                os.unlink(wal_file)
    except OSError:
        pass


@pytest.fixture
def db_manager(temp_db):
    """Create DatabaseManager instance with temporary database"""
    manager = DatabaseManager(temp_db)
    yield manager
    manager.close_connection()


@pytest.fixture
def mock_managers():
    """Create mock managers for testing controllers"""
    managers = {
        'user': MagicMock(),
        'product': MagicMock(),
        'sales': MagicMock(),
        'customer': MagicMock(),
        'financial': MagicMock(),
        'inventory': MagicMock(),
        'report': MagicMock()
    }
    
    # Configure common mock behaviors
    managers['user'].get_current_user.return_value = {
        'id': 1,
        'username': 'test_user',
        'nombre_completo': 'Usuario Test',
        'rol_nombre': 'ADMINISTRADOR'
    }
    
    managers['product'].get_all_products.return_value = []
    managers['sales'].create_sale.return_value = {'id': 1, 'numero_venta': 'TEST-001'}
    managers['customer'].get_all_customers.return_value = []
    
    return managers


@pytest.fixture
def current_user():
    """Mock current user for testing"""
    return {
        'id': 1,
        'username': 'test_user',
        'nombre_completo': 'Usuario Test',
        'email': 'test@test.com',
        'rol_id': 1,
        'rol_nombre': 'ADMINISTRADOR',
        'activo': True
    }


@pytest.fixture
def sample_product():
    """Sample product data for testing"""
    return {
        'id': 1,
        'codigo_barras': '1234567890123',
        'nombre': 'Producto Test',
        'descripcion': 'Descripción del producto test',
        'precio_venta': 100.0,
        'stock_actual': 50,
        'activo': True
    }


@pytest.fixture
def sample_customer():
    """Sample customer data for testing"""
    return {
        'id': 1,
        'nombre': 'Cliente',
        'apellido': 'Test',
        'email': 'cliente@test.com',
        'telefono': '123456789',
        'documento': '12345678',
        'activo': True
    }


@pytest.fixture
def sample_sale():
    """Sample sale data for testing"""
    return {
        'id': 1,
        'numero_venta': 'TEST-001',
        'cliente_id': 1,
        'vendedor_id': 1,
        'subtotal': 100.0,
        'impuesto_total': 21.0,
        'total_venta': 121.0,
        'tipo_pago': 'EFECTIVO',
        'estado': 'COMPLETADO'
    }


@pytest.fixture(autouse=True)
def clean_environment():
    """Clean up environment variables after each test"""
    yield
    
    # Clean up any test databases that might have been created
    test_files = [
        'test_almacen_pro.db',
        'integration_test_almacen_pro.db',
        'migration_test.db'
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            try:
                os.unlink(test_file)
                # Clean up WAL and SHM files
                for ext in ['-wal', '-shm']:
                    wal_file = test_file + ext
                    if os.path.exists(wal_file):
                        os.unlink(wal_file)
            except OSError:
                pass


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "ui: marks tests as UI tests")
    config.addinivalue_line("markers", "database: marks tests that require database")


def pytest_collection_modifyitems(config, items):
    """Add markers to tests based on their location"""
    for item in items:
        # Add markers based on test file path
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "ui" in str(item.fspath):
            item.add_marker(pytest.mark.ui)
        
        # Add database marker if test uses database fixtures
        if any(fixture in item.fixturenames for fixture in ['db_manager', 'temp_db']):
            item.add_marker(pytest.mark.database)