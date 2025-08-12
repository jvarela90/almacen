# Guía de Desarrollo - AlmacénPro v2.0

## 🎯 Resumen Ejecutivo

Guía completa de desarrollo para AlmacénPro v2.0, incluyendo arquitectura MVC, convenciones de código, guías de migración a Qt Designer, pre-commit hooks y mejores prácticas.

---

## 🏗️ Arquitectura del Proyecto

### **Patrón MVC Implementado**
```
almacen/
├── controllers/           # 🎮 Lógica de control y coordinación
│   ├── base_controller.py    # Controlador base común
│   ├── login_controller.py   # Autenticación MVC
│   └── *_controller.py       # Controladores especializados
│
├── models/               # 📊 Lógica de datos y estado  
│   ├── entities.py          # Entidades de negocio (dataclasses)
│   └── *_model.py           # Modelos especializados
│
├── views/                # 🎨 Interfaces de usuario
│   ├── dialogs/             # Diálogos modales (.ui)
│   └── widgets/             # Widgets principales (.ui)
│
├── managers/             # 🧠 Lógica de negocio
│   └── *_manager.py         # Managers especializados
│
├── utils/               # 🛠️ Utilidades comunes
│   ├── validators.py        # Validadores de datos
│   └── style_manager.py     # Gestión de estilos CSS
│
└── database/            # 🗄️ Base de datos y migraciones
    ├── manager.py           # DatabaseManager principal
    └── migrations/          # Migraciones Alembic
```

---

## 🎨 Migración a Qt Designer

### **Convenciones de Naming para Widgets**
| Tipo Widget | Prefijo | Ejemplo |
|-------------|---------|---------|
| LineEdit | `lineEdit` | `lineEditUsername`, `lineEditPrice` |
| ComboBox | `cmb` | `cmbCategory`, `cmbStatus` |
| Table | `tbl` | `tblProducts`, `tblSales` |
| Button | `btn` | `btnSave`, `btnDelete` |
| Label | `lbl` | `lblTotal`, `lblError` |
| CheckBox | `chk` | `chkActive`, `chkRememberUser` |

### **Carga Dinámica de UI**
```python
# Patrón estándar para carga de .ui
class LoginController(QDialog):
    def __init__(self, user_manager, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.load_ui()
        
    def load_ui(self):
        ui_path = Path("views/dialogs/login_dialog.ui")
        uic.loadUi(str(ui_path), self)
```

### **Validación de Widgets**
```python
# Verificación defensiva de widgets
def attempt_login(self):
    username = self.lineEditUsername.text().strip() if hasattr(self, 'lineEditUsername') else ""
    password = self.lineEditPassword.text() if hasattr(self, 'lineEditPassword') else ""
```

---

## 🔧 Pre-Commit Hooks

### **Configuración Automática**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        language_version: python3.8
        args: [--line-length=100]

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile=black, --line-length=100]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=100, --exclude=venv]
```

### **Instalación y Uso**
```bash
# Instalar pre-commit
pip install pre-commit

# Instalar hooks en el repo
pre-commit install

# Ejecutar en todos los archivos
pre-commit run --all-files

# Bypass para casos especiales
git commit -m "mensaje" --no-verify
```

---

## 📝 Convenciones de Código

### **Python Code Style**
```python
# Clases: PascalCase
class ProductManager:
    pass

# Funciones y variables: snake_case
def calculate_total_price():
    total_amount = 0.0
    return total_amount

# Constantes: UPPER_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3
DEFAULT_DATABASE_PATH = "data/almacen_pro.db"
```

### **Docstrings y Comentarios**
```python
def authenticate_user(self, username: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    """
    Autenticar usuario con username y password
    
    Args:
        username: Nombre de usuario
        password: Contraseña sin encriptar
        
    Returns:
        Tuple con: (éxito, mensaje, datos_usuario)
        
    Raises:
        DatabaseError: Si hay problemas de conexión
    """
    pass
```

### **Type Hints**
```python
from typing import Dict, List, Optional, Tuple, Any

def get_products_by_category(self, category_id: int) -> List[Dict[str, Any]]:
    """Retorna productos de una categoría específica"""
    pass
```

---

## 🧪 Testing y Validación

### **Tests Unitarios**
```python
import unittest
from managers.user_manager import UserManager

class TestUserManager(unittest.TestCase):
    def setUp(self):
        self.user_manager = UserManager(mock_db)
    
    def test_authenticate_valid_user(self):
        success, message, user_data = self.user_manager.authenticate_user("admin", "admin123")
        self.assertTrue(success)
        self.assertIsNotNone(user_data)
```

### **Validación de Sistema**
```python
# Script de validación completa
python test_sistema_completo.py

# Tests específicos por módulo
python -m pytest tests/test_user_manager.py -v
```

---

## 🛡️ Validación de Datos

### **Validadores Implementados**
```python
from utils.validators import (
    EmailValidator, PhoneValidator, 
    DocumentValidator, PriceValidator
)

# Uso en controladores
email_validator = EmailValidator()
if not email_validator.validate(email_input):
    self.show_error("Email inválido")
```

### **Validaciones por Tipo**
- **Email**: RFC compliant con regex
- **Teléfono**: Formato argentino +54 9 xxxx
- **Documentos**: DNI/CUIT con dígito verificador
- **Precios**: Números positivos con decimales
- **Códigos**: SKU y códigos de barras

---

## 🎨 Sistema de Estilos

### **StyleManager Centralizado**
```python
from utils.style_manager import StyleManager

# Aplicar tema global
StyleManager.apply_theme(self.app, "default")

# Estilos por módulo
StyleManager.apply_module_styles(self, 'sales')

# Estilos de error dinámicos
StyleManager.apply_error_style(self.lineEditUsername)
```

### **CSS Modular**
```python
# Estilos básicos para formularios
FORM_STYLE = """
QLineEdit {
    padding: 8px;
    border: 2px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
}
QLineEdit:focus {
    border-color: #3498db;
}
"""
```

---

## 🔄 Manejo de Señales PyQt

### **Patrón de Señales MVC**
```python
class SalesModel(QObject):
    # Definir señales
    data_changed = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def add_product_to_cart(self, product):
        # Lógica de negocio
        self.cart.append(product)
        # Emitir señal
        self.data_changed.emit()

class SalesController(BaseController):
    def setup_signals(self):
        # Conectar señales del modelo
        self.model.data_changed.connect(self.update_ui)
        self.model.error_occurred.connect(self.show_error)
```

---

## 📊 Logging y Debugging

### **Configuración de Logging**
```python
import logging

# Configuración estándar
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/almacen_pro.log'),
        logging.StreamHandler()
    ]
)

# Uso en clases
class ProductManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def some_method(self):
        self.logger.info("Operación iniciada")
```

### **Debugging con PyQt**
```python
# Variables de entorno para debugging
QT_LOGGING_RULES="*.debug=true"
export QT_LOGGING_RULES

# Debug de layouts
from PyQt5.QtCore import QLoggingCategory
QLoggingCategory.setFilterRules("*.debug=true")
```

---

## 🚀 Deployment y Build

### **Preparación para Producción**
```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar pre-commit hooks
pre-commit run --all-files

# Ejecutar tests
python -m pytest tests/ -v

# Build con PyInstaller (opcional)
pyinstaller --onedir --windowed main.py
```

### **Environment Management**
```bash
# Desarrollo
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Variables de entorno
cp .env.example .env
# Editar .env con configuración local
```

---

## 📚 Documentación del Código

### **Generación de Docs**
```bash
# Sphinx documentation (futuro)
pip install sphinx sphinx-rtd-theme

# Generar documentación API
sphinx-apidoc -o docs/source .
sphinx-build -b html docs/source docs/build
```

### **Comentarios en Código**
- Documentar **por qué** se hace algo, no **qué** se hace
- Explicar lógica de negocio compleja
- Documentar APIs públicas
- Evitar comentarios obvios

---

## 🔧 Troubleshooting

### **Problemas Comunes**

#### **ImportError: No module named 'PyQt5'**
```bash
pip install PyQt5==5.15.10
```

#### **Widget no encontrado en .ui**
- Verificar nombres exactos en Qt Designer
- Usar `hasattr()` para verificación defensiva
- Logs detallados para debugging

#### **Base de datos bloqueada**
```python
# Verificar conexiones abiertas
# Usar context managers para auto-close
with DatabaseManager() as db:
    db.execute_query(sql)
```

---

## 🎯 Mejores Prácticas

### **Desarrollo**
1. **Separar responsabilidades** siguiendo MVC estricto
2. **Usar Type Hints** para mejor IDE support
3. **Validar inputs** siempre en controladores
4. **Manejar errores** gracefully con try/except
5. **Logging detallado** para operaciones críticas

### **UI/UX**
1. **Diseñar en Qt Designer** para consistencia
2. **Carga dinámica** con `uic.loadUi()`
3. **Validación en tiempo real** en formularios
4. **Feedback visual** de estados y errores
5. **Shortcuts de teclado** para eficiencia

### **Base de Datos**
1. **Usar transacciones** para operaciones críticas
2. **Validar datos** antes de inserción
3. **Índices estratégicos** para performance
4. **Backups automáticos** regulares
5. **Migraciones versionadas** con Alembic

---

*Actualizado: 11 de agosto de 2025*  
*Versión: 2.0*