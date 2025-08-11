"""
Modelo Base - AlmacénPro v2.0 MVC
Clase base para todos los modelos con funcionalidad común
"""

from PyQt5.QtCore import QObject, pyqtSignal
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

class BaseModel(QObject):
    """Clase base para todos los modelos de datos"""
    
    # Señales comunes para todos los modelos
    data_changed = pyqtSignal()
    error_occurred = pyqtSignal(str)
    loading_started = pyqtSignal()
    loading_finished = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Estado del modelo
        self._data = {}
        self._is_loading = False
        self._last_error = None
        self._validation_errors = []
        
        # Configuración
        self.auto_save = True
        self.validate_on_change = True
        
        # Logger específico del modelo
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    # === PROPIEDADES ===
    
    @property
    def data(self) -> Dict[str, Any]:
        """Obtener datos del modelo"""
        return self._data.copy()
    
    @property
    def is_loading(self) -> bool:
        """Verificar si el modelo está cargando datos"""
        return self._is_loading
    
    @property
    def last_error(self) -> Optional[str]:
        """Obtener último error ocurrido"""
        return self._last_error
    
    @property
    def validation_errors(self) -> List[str]:
        """Obtener errores de validación"""
        return self._validation_errors.copy()
    
    @property
    def is_valid(self) -> bool:
        """Verificar si los datos son válidos"""
        return len(self._validation_errors) == 0
    
    # === MÉTODOS PÚBLICOS ===
    
    def set_data(self, data: Dict[str, Any], validate: bool = True):
        """Establecer datos del modelo"""
        try:
            if validate and not self._validate_data(data):
                self.error_occurred.emit("Datos inválidos")
                return False
            
            old_data = self._data.copy()
            self._data = data.copy()
            
            # Emitir señal de cambio
            self.data_changed.emit()
            
            # Auto-guardar si está habilitado
            if self.auto_save:
                self._auto_save(old_data)
            
            self.logger.debug("Datos del modelo actualizados")
            return True
            
        except Exception as e:
            self.logger.error(f"Error estableciendo datos: {e}")
            self.error_occurred.emit(str(e))
            return False
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """Obtener valor específico del modelo"""
        return self._data.get(key, default)
    
    def set_value(self, key: str, value: Any, validate: bool = True):
        """Establecer valor específico del modelo"""
        try:
            if validate and not self._validate_field(key, value):
                return False
            
            old_value = self._data.get(key)
            self._data[key] = value
            
            # Emitir señal de cambio
            self.data_changed.emit()
            
            self.logger.debug(f"Campo {key} actualizado: {old_value} -> {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error estableciendo valor {key}: {e}")
            self.error_occurred.emit(str(e))
            return False
    
    def clear(self):
        """Limpiar todos los datos del modelo"""
        self._data.clear()
        self._validation_errors.clear()
        self._last_error = None
        
        self.data_changed.emit()
        self.logger.debug("Modelo limpiado")
    
    def reset_to_defaults(self):
        """Resetear modelo a valores por defecto"""
        defaults = self._get_default_values()
        self.set_data(defaults)
    
    def validate(self) -> bool:
        """Validar datos actuales del modelo"""
        return self._validate_data(self._data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir modelo a diccionario"""
        return self._data.copy()
    
    def to_json(self) -> str:
        """Convertir modelo a JSON"""
        try:
            return json.dumps(self._data, default=str, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Error convirtiendo a JSON: {e}")
            return "{}"
    
    def from_json(self, json_str: str) -> bool:
        """Cargar modelo desde JSON"""
        try:
            data = json.loads(json_str)
            return self.set_data(data)
        except Exception as e:
            self.logger.error(f"Error cargando desde JSON: {e}")
            self.error_occurred.emit(f"Error en JSON: {str(e)}")
            return False
    
    # === MÉTODOS DE CARGA ===
    
    def start_loading(self):
        """Iniciar estado de carga"""
        self._is_loading = True
        self.loading_started.emit()
    
    def finish_loading(self):
        """Finalizar estado de carga"""
        self._is_loading = False
        self.loading_finished.emit()
    
    # === MÉTODOS PROTEGIDOS (PARA SOBRESCRIBIR) ===
    
    def _validate_data(self, data: Dict[str, Any]) -> bool:
        """Validar datos completos (implementar en clases hijas)"""
        self._validation_errors.clear()
        
        # Validación básica - sobrescribir en clases hijas
        for key, value in data.items():
            if not self._validate_field(key, value):
                return False
        
        return len(self._validation_errors) == 0
    
    def _validate_field(self, field_name: str, value: Any) -> bool:
        """Validar campo específico (implementar en clases hijas)"""
        # Validación básica por defecto
        return True
    
    def _get_default_values(self) -> Dict[str, Any]:
        """Obtener valores por defecto (implementar en clases hijas)"""
        return {}
    
    def _auto_save(self, old_data: Dict[str, Any]):
        """Auto-guardado (implementar en clases hijas si es necesario)"""
        pass
    
    # === MÉTODOS DE UTILIDAD ===
    
    def _add_validation_error(self, error: str):
        """Agregar error de validación"""
        if error not in self._validation_errors:
            self._validation_errors.append(error)
    
    def _set_error(self, error: str):
        """Establecer error y emitir señal"""
        self._last_error = error
        self.error_occurred.emit(error)
        self.logger.error(f"Error en modelo: {error}")
    
    def _safe_convert_to_float(self, value: Any, default: float = 0.0) -> float:
        """Conversión segura a float"""
        try:
            if isinstance(value, str):
                return float(value.replace('$', '').replace(',', ''))
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def _safe_convert_to_int(self, value: Any, default: int = 0) -> int:
        """Conversión segura a int"""
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def _format_currency(self, amount: float) -> str:
        """Formatear monto como moneda"""
        return f"${amount:,.2f}"
    
    def _format_datetime(self, dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Formatear fecha y hora"""
        try:
            if isinstance(dt, str):
                return dt
            return dt.strftime(format_str)
        except (AttributeError, ValueError):
            return str(dt)