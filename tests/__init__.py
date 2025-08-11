"""
Test suite for AlmacénPro v2.0
Comprehensive testing framework for ERP/POS system
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

# Test configuration
TEST_DATABASE_PATH = "test_almacen_pro.db"
INTEGRATION_TEST_DATABASE_PATH = "integration_test_almacen_pro.db"

# Test environment setup
os.environ.setdefault("DATABASE_TYPE", "sqlite")
os.environ.setdefault("SQLITE_PATH", TEST_DATABASE_PATH)
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("LOG_LEVEL", "DEBUG")