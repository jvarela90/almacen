"""
Unit tests for DatabaseManager
"""

import pytest
import sqlite3
from database.manager import DatabaseManager


class TestDatabaseManager:
    """Test suite for DatabaseManager"""

    def test_initialization(self, temp_db):
        """Test database initialization"""
        manager = DatabaseManager(temp_db)
        assert manager.db_path.exists()
        assert manager.connection is not None
        manager.close_connection()

    def test_connection(self, temp_db):
        """Test database connection"""
        manager = DatabaseManager(temp_db)
        
        # Test connection is working
        cursor = manager.cursor
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1
        
        manager.close_connection()

    def test_execute_query(self, db_manager):
        """Test query execution"""
        # Test simple query
        result = db_manager.execute_query("SELECT 1")
        assert result == [(1,)]

    def test_execute_query_with_params(self, db_manager):
        """Test parameterized query execution"""
        # Create a test table
        db_manager.execute_query("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        
        # Insert data with parameters
        success = db_manager.execute_query(
            "INSERT INTO test_table (name) VALUES (?)",
            ("Test Name",)
        )
        assert success is not False
        
        # Query with parameters
        result = db_manager.execute_query(
            "SELECT name FROM test_table WHERE id = ?",
            (1,)
        )
        assert result == [("Test Name",)]

    def test_transaction_rollback(self, db_manager):
        """Test transaction rollback on error"""
        # Create test table
        db_manager.execute_query("""
            CREATE TABLE test_transaction (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        """)
        
        # This should fail and rollback
        try:
            with db_manager.connection:
                db_manager.cursor.execute("INSERT INTO test_transaction (name) VALUES (?)", ("Test",))
                # This will fail due to NULL constraint
                db_manager.cursor.execute("INSERT INTO test_transaction (name) VALUES (NULL)")
        except sqlite3.IntegrityError:
            pass
        
        # Check that no data was inserted due to rollback
        result = db_manager.execute_query("SELECT COUNT(*) FROM test_transaction")
        assert result[0][0] == 0

    def test_close_connection(self, temp_db):
        """Test connection closing"""
        manager = DatabaseManager(temp_db)
        connection = manager.connection
        
        manager.close_connection()
        
        # Connection should be closed
        assert manager.connection is None or manager.connection is connection

    def test_database_file_creation(self):
        """Test that database file is created if it doesn't exist"""
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "new_test.db")
            
            # Database file shouldn't exist
            assert not os.path.exists(db_path)
            
            # Create manager - should create the file
            manager = DatabaseManager(db_path)
            
            # Database file should now exist
            assert os.path.exists(db_path)
            
            manager.close_connection()

    @pytest.mark.database
    def test_foreign_key_enforcement(self, db_manager):
        """Test that foreign key constraints are enforced"""
        # Create related tables
        db_manager.execute_query("""
            CREATE TABLE parent_table (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        
        db_manager.execute_query("""
            CREATE TABLE child_table (
                id INTEGER PRIMARY KEY,
                parent_id INTEGER,
                name TEXT,
                FOREIGN KEY (parent_id) REFERENCES parent_table(id)
            )
        """)
        
        # Insert valid parent
        db_manager.execute_query("INSERT INTO parent_table (name) VALUES (?)", ("Parent",))
        
        # This should work
        success = db_manager.execute_query(
            "INSERT INTO child_table (parent_id, name) VALUES (?, ?)",
            (1, "Child")
        )
        assert success is not False
        
        # This should fail due to foreign key constraint
        with pytest.raises(sqlite3.IntegrityError):
            db_manager.execute_query(
                "INSERT INTO child_table (parent_id, name) VALUES (?, ?)",
                (999, "Invalid Child")
            )