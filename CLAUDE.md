# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AlmacénPro v2.0 is a comprehensive ERP/POS system for warehouse and retail management, built with Python 3.8+ and PyQt5. It features a modular architecture with specialized managers for different business domains and includes collaborative management capabilities for multi-partner businesses.

## Quick Start Commands

### Running the Application
```bash
# Main application entry point
python main.py
```

### Development Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Development tools (optional)
pip install pytest black flake8

# Run tests (if available)
pytest

# Code formatting
black .

# Code linting
flake8 --max-line-length=100 --exclude=venv
```

### Database Operations
The system automatically handles database setup and migrations. Database file: `almacen_pro.db`

## Architecture Overview

### Core Modules Structure

**Database Layer** (`database/`)
- `manager.py` - Central database manager with SQLite operations
- `models.py` - Database table definitions and schemas

**Business Logic** (`managers/`)
- `user_manager.py` - User authentication and role management
- `product_manager.py` - Product catalog and inventory
- `sales_manager.py` - Sales processing and transactions
- `purchase_manager.py` - Purchase orders and supplier management
- `provider_manager.py` - Supplier relationship management
- `report_manager.py` - Analytics and reporting

**User Interface** (`ui/`)
- `main_window.py` - Main application window with tab navigation
- `dialogs/` - Modal dialogs for specific operations
- `widgets/` - Reusable UI components for different modules

**Utilities** (`utils/`)
- `backup_manager.py` - Automated backup system with compression
- `notifications.py` - System-wide notification management
- `helpers.py` - Common utility functions

**Configuration** (`config/`)
- `settings.py` - Centralized configuration management
- `config.json` - Runtime configuration file

### Application Flow

1. **Initialization**: `main.py` creates `AlmacenProApp` class
2. **Component Loading**: `InitializationThread` loads all managers asynchronously
3. **Authentication**: `LoginDialog` authenticates users via `UserManager`
4. **Main Interface**: `MainWindow` provides tabbed interface with role-based access
5. **Business Operations**: Each tab connects to appropriate manager for business logic

### Key Design Patterns

- **Manager Pattern**: Business logic separated into specialized managers
- **Observer Pattern**: PyQt signals/slots for component communication
- **Factory Pattern**: Dynamic creation of UI widgets based on user roles
- **Command Pattern**: Database operations wrapped in transaction methods

## Database Architecture

The system uses a normalized SQLite database with 50+ tables covering:
- User management and authentication
- Product catalog with variants and attributes
- Inventory control with location tracking
- Sales and purchase transaction processing
- Customer relationship management (CRM)
- Financial tracking and reporting
- Automated backup and audit trails

Key database features:
- Foreign key constraints enabled
- Automatic indexing for performance
- Transaction-based operations
- Built-in backup and restore functionality

## Configuration Management

Configuration is handled through:
- `config.json` - Runtime settings (created automatically on first run)
- `config/settings.py` - Default configuration values and validation
- Environment variables for deployment settings

## Backup System

The application includes a sophisticated backup system:
- Automatic scheduled backups (configurable interval)
- Compressed backup files (80-90% size reduction)
- Backup verification and integrity checking
- GUI-based restore functionality
- Configurable retention policies

## Development Guidelines

### Code Organization
- Follow modular architecture - keep managers focused on single responsibility
- UI components should be in appropriate widget/dialog directories
- Database operations should go through `DatabaseManager`
- Use logging extensively for debugging and monitoring

### Adding New Features
1. Create or extend appropriate manager in `managers/`
2. Add database changes via `DatabaseManager.create_tables()`
3. Create UI components in `ui/widgets/` or `ui/dialogs/`
4. Update `MainWindow` to include new functionality
5. Add configuration options to `settings.py` if needed

### Database Changes
- All database operations should use the `DatabaseManager` class
- Use parameterized queries to prevent SQL injection
- Wrap operations in transactions for data consistency
- Add proper error handling and logging

### UI Development
- Follow existing PyQt5 patterns and styling
- Use signals/slots for component communication
- Implement proper validation in dialogs
- Maintain consistent styling using global CSS

## Testing

The codebase supports testing with pytest:
- Unit tests for managers and utilities
- UI tests using pytest-qt
- Database integration tests

## User Roles and Permissions

The system supports role-based access control:
- **Admin**: Full system access, user management, configuration
- **Manager**: Operations management, reporting, some configuration
- **Employee**: Daily operations, limited reporting
- **Collaborator**: Partner-specific access for multi-partner businesses

## Logging

Comprehensive logging system:
- Main log: `logs/almacen_pro_YYYYMMDD.log`
- Critical errors: `logs/critical_errors.log`
- Backup operations logged separately

## Dependencies

Key dependencies (see `requirements.txt` for complete list):
- PyQt5 5.15.4+ for GUI
- sqlite3 (built-in) for database
- reportlab for PDF generation
- Pillow for image processing
- cryptography for security
- python-barcode for barcode generation

## Deployment Notes

- Minimum Python 3.8
- Cross-platform (Windows, macOS, Linux)
- Self-contained SQLite database
- Configurable through `config.json`
- Backup system stores files in `backups/` directory