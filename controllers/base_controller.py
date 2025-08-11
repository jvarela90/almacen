"""
Controlador Base - AlmacénPro v2.0 MVC
Clase base para todos los controladores con funcionalidad común
"""

import os
import logging
from PyQt5.QtWidgets import QWidget, QMessageBox, QApplication, QShortcut
from PyQt5.QtCore import QObject, pyqtSlot, QTimer, QThread
from PyQt5.QtGui import QKeySequence
from PyQt5 import uic
from typing import Dict, Any, Optional, List
import traceback

logger = logging.getLogger(__name__)

class BaseController(QWidget):
    """Clase base para controladores MVC"""
    
    def __init__(self, managers: Dict, current_user: Dict, parent=None):
        super().__init__(parent)
        
        # Referencias comunes
        self.managers = managers
        self.current_user = current_user
        self.parent_window = parent
        
        # Estado del controlador
        self.is_initialized = False
        self.ui_loaded = False
        
        # Timer para operaciones diferidas
        self.defer_timer = QTimer()
        self.defer_timer.setSingleShot(True)
        self.defer_timer.timeout.connect(self._execute_deferred_operations)
        
        # Setup común
        self.setup_logging()
        
        # Lista de operaciones diferidas
        self._deferred_operations = []
    
    def setup_logging(self):
        """Configurar logging específico del controlador"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def get_ui_file_path(self) -> str:
        """Retornar ruta al archivo .ui correspondiente"""
        pass
    
    def load_ui(self):
        """Cargar interfaz desde archivo .ui"""
        try:
            ui_path = self.get_ui_file_path()
            
            if not os.path.exists(ui_path):
                raise FileNotFoundError(f"Archivo UI no encontrado: {ui_path}")
            
            # Cargar el archivo .ui
            uic.loadUi(ui_path, self)
            self.ui_loaded = True
            
            self.logger.info(f"UI cargada exitosamente: {os.path.basename(ui_path)}")
            
        except Exception as e:
            self.logger.error(f"Error cargando UI: {e}")
            self.show_error("Error de Inicialización", f"No se pudo cargar la interfaz: {str(e)}")
            raise
    
    def initialize(self):
        """Método de inicialización completo"""
        try:
            # Mostrar estado de carga
            QApplication.setOverrideCursor(Qt.WaitCursor)
            
            # Cargar UI
            self.load_ui()
            
            # Setup específico del controlador
            self.setup_ui()
            self.connect_signals()
            self.setup_shortcuts()
            self.apply_styles()
            
            # Cargar datos iniciales (diferido para no bloquear UI)
            self.defer_operation(self.load_initial_data)
            
            self.is_initialized = True
            self.logger.info(f"Controlador {self.__class__.__name__} inicializado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error en inicialización: {e}")
            self.logger.error(traceback.format_exc())
            raise
        finally:
            QApplication.restoreOverrideCursor()
    
    def setup_ui(self):
        """Configurar elementos específicos de la UI"""
        pass
    
    def connect_signals(self):
        """Conectar señales específicas del controlador"""
        pass
    
    def setup_shortcuts(self):
        """Configurar atajos de teclado (puede ser sobrescrito)"""
        # Atajos comunes
        from PyQt5.QtWidgets import QShortcut
        
        # Ctrl+S - Guardar
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.on_save_shortcut)
        
        # F5 - Actualizar
        refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        refresh_shortcut.activated.connect(self.on_refresh_shortcut)
        
        # Escape - Cancelar/Cerrar
        escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        escape_shortcut.activated.connect(self.on_escape_shortcut)
    
    def apply_styles(self):
        """Aplicar estilos CSS (puede ser sobrescrito)"""
        from utils.style_manager import StyleManager
        try:
            StyleManager.apply_default_styles(self)
        except ImportError:
            # Si no existe StyleManager, aplicar estilos básicos
            self.apply_basic_styles()
    
    def apply_basic_styles(self):
        """Aplicar estilos básicos si no hay StyleManager"""
        basic_style = """
        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 5px;
            margin: 5px;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 10px 0 10px;
        }
        
        QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
            min-width: 80px;
        }
        
        QPushButton:hover {
            background-color: #2980b9;
        }
        
        QPushButton:pressed {
            background-color: #21618c;
        }
        
        QPushButton:disabled {
            background-color: #bdc3c7;
            color: #7f8c8d;
        }
        
        QTableWidget {
            border: 1px solid #ddd;
            border-radius: 4px;
            gridline-color: #f0f0f0;
            alternate-background-color: #f8f9fa;
        }
        
        QTableWidget::item {
            padding: 8px;
            border-bottom: 1px solid #eee;
        }
        
        QTableWidget::item:selected {
            background-color: #3498db;
            color: white;
        }
        
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            border: 2px solid #ddd;
            border-radius: 4px;
            padding: 8px;
            font-size: 14px;
        }
        
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
            border-color: #3498db;
        }
        
        QLabel {
            color: #2c3e50;
        }
        """
        
        self.setStyleSheet(basic_style)
    
    def load_initial_data(self):
        """Cargar datos iniciales (puede ser sobrescrito)"""
        pass
    
    # === MÉTODOS DE UTILIDAD COMUNES ===
    
    def show_info(self, title: str, message: str):
        """Mostrar mensaje informativo"""
        QMessageBox.information(self, title, message)
    
    def show_warning(self, title: str, message: str):
        """Mostrar mensaje de advertencia"""
        QMessageBox.warning(self, title, message)
    
    def show_error(self, title: str, message: str):
        """Mostrar mensaje de error"""
        QMessageBox.critical(self, title, message)
    
    def show_question(self, title: str, message: str) -> bool:
        """Mostrar pregunta de confirmación"""
        reply = QMessageBox.question(self, title, message, 
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        return reply == QMessageBox.Yes
    
    def validate_required_fields(self, fields: Dict[str, Any]) -> bool:
        """Validar campos requeridos"""
        missing_fields = []
        
        for field_name, field_value in fields.items():
            if not field_value or (isinstance(field_value, str) and not field_value.strip()):
                missing_fields.append(field_name)
        
        if missing_fields:
            fields_text = ", ".join(missing_fields)
            self.show_warning("Campos Requeridos", 
                            f"Por favor complete los siguientes campos: {fields_text}")
            return False
        
        return True
    
    def safe_float_conversion(self, value: str, default: float = 0.0) -> float:
        """Conversión segura a float"""
        try:
            if isinstance(value, (int, float)):
                return float(value)
            return float(str(value).replace('$', '').replace(',', ''))
        except (ValueError, AttributeError):
            return default
    
    def safe_int_conversion(self, value: str, default: int = 0) -> int:
        """Conversión segura a int"""
        try:
            if isinstance(value, int):
                return value
            return int(float(str(value)))
        except (ValueError, AttributeError):
            return default
    
    def format_currency(self, amount: float) -> str:
        """Formatear monto como moneda"""
        return f"${amount:,.2f}"
    
    def format_date(self, date_obj, format_str: str = "%d/%m/%Y") -> str:
        """Formatear fecha"""
        try:
            if hasattr(date_obj, 'strftime'):
                return date_obj.strftime(format_str)
            return str(date_obj)
        except (AttributeError, ValueError):
            return str(date_obj)
    
    # === OPERACIONES DIFERIDAS ===
    
    def defer_operation(self, operation, delay_ms: int = 100):
        """Diferir operación para no bloquear UI"""
        self._deferred_operations.append(operation)
        if not self.defer_timer.isActive():
            self.defer_timer.start(delay_ms)
    
    def _execute_deferred_operations(self):
        """Ejecutar operaciones diferidas"""
        operations = self._deferred_operations.copy()
        self._deferred_operations.clear()
        
        for operation in operations:
            try:
                if callable(operation):
                    operation()
            except Exception as e:
                self.logger.error(f"Error en operación diferida: {e}")
    
    # === MANEJO DE TABLAS ===
    
    def setup_table_widget(self, table, headers: List[str], column_widths: Optional[List[int]] = None):
        """Configurar widget de tabla"""
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        
        # Configurar comportamiento
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(table.SelectRows)
        table.setEditTriggers(table.NoEditTriggers)
        table.setSortingEnabled(True)
        
        # Configurar anchos de columna
        header = table.horizontalHeader()
        if column_widths:
            for i, width in enumerate(column_widths):
                if width == -1:  # Stretch
                    header.setSectionResizeMode(i, header.Stretch)
                elif width == 0:  # ResizeToContents
                    header.setSectionResizeMode(i, header.ResizeToContents)
                else:  # Fixed width
                    table.setColumnWidth(i, width)
        else:
            # Por defecto, última columna se estira
            header.setStretchLastSection(True)
    
    def populate_table(self, table, data: List[Dict[str, Any]], columns: List[str]):
        """Poblar tabla con datos"""
        table.setRowCount(len(data))
        
        for row, item in enumerate(data):
            for col, column_key in enumerate(columns):
                value = item.get(column_key, "")
                
                # Formatear valores especiales
                if isinstance(value, float) and column_key.lower() in ['precio', 'costo', 'total', 'subtotal']:
                    value = self.format_currency(value)
                elif hasattr(value, 'strftime'):  # datetime
                    value = self.format_date(value)
                
                from PyQt5.QtWidgets import QTableWidgetItem
                table.setItem(row, col, QTableWidgetItem(str(value)))
        
        # Ajustar columnas
        table.resizeColumnsToContents()
    
    def get_selected_table_data(self, table) -> Optional[Dict[str, Any]]:
        """Obtener datos de fila seleccionada en tabla"""
        current_row = table.currentRow()
        if current_row < 0:
            return None
        
        data = {}
        headers = [table.horizontalHeaderItem(col).text() 
                  for col in range(table.columnCount())]
        
        for col, header in enumerate(headers):
            item = table.item(current_row, col)
            data[header.lower().replace(' ', '_')] = item.text() if item else ""
        
        return data
    
    # === SLOTS COMUNES ===
    
    @pyqtSlot()
    def on_save_shortcut(self):
        """Slot para atajo Ctrl+S"""
        # Implementar en clases hijas si es necesario
        pass
    
    @pyqtSlot()
    def on_refresh_shortcut(self):
        """Slot para atajo F5"""
        self.load_initial_data()
    
    @pyqtSlot()
    def on_escape_shortcut(self):
        """Slot para atajo Escape"""
        # Por defecto, cerrar si es un diálogo
        if hasattr(self, 'reject'):
            self.reject()
    
    # === MANEJO DE ESTADO ===
    
    def save_state(self) -> Dict[str, Any]:
        """Guardar estado actual del controlador (para sobrescribir)"""
        return {
            'window_geometry': self.geometry(),
            'is_maximized': self.isMaximized()
        }
    
    def restore_state(self, state: Dict[str, Any]):
        """Restaurar estado del controlador (para sobrescribir)"""
        if 'window_geometry' in state:
            self.setGeometry(state['window_geometry'])
        if state.get('is_maximized', False):
            self.showMaximized()
    
    def reset_form(self):
        """Resetear formulario a estado inicial (para sobrescribir)"""
        pass
    
    # === CLEANUP ===
    
    def cleanup(self):
        """Limpiar recursos antes de cerrar (para sobrescribir)"""
        self.logger.info(f"Limpiando controlador {self.__class__.__name__}")
        
        # Detener timers
        if self.defer_timer.isActive():
            self.defer_timer.stop()
    
    def closeEvent(self, event):
        """Manejar evento de cierre"""
        try:
            self.cleanup()
            event.accept()
        except Exception as e:
            self.logger.error(f"Error en cleanup: {e}")
            event.accept()
    
    # === MÉTODOS DE VALIDACIÓN ===
    
    def validate_email(self, email: str) -> bool:
        """Validar formato de email"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_phone(self, phone: str) -> bool:
        """Validar formato de teléfono"""
        import re
        # Permite varios formatos de teléfono
        pattern = r'^[\+]?[1-9][\d]{0,15}$'
        clean_phone = re.sub(r'[^\d\+]', '', phone)
        return len(clean_phone) >= 7 and re.match(pattern, clean_phone) is not None
    
    def validate_required_text(self, text: str, min_length: int = 1) -> bool:
        """Validar texto requerido"""
        return isinstance(text, str) and len(text.strip()) >= min_length
    
    def validate_positive_number(self, value: Any) -> bool:
        """Validar número positivo"""
        try:
            num = float(value)
            return num >= 0
        except (ValueError, TypeError):
            return False
    
    def validate_positive_integer(self, value: Any) -> bool:
        """Validar entero positivo"""
        try:
            num = int(value)
            return num >= 0
        except (ValueError, TypeError):
            return False