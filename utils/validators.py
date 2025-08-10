"""
Validadores de Datos - AlmacénPro v2.0
Conjunto completo de validadores para datos del sistema
"""

import re
import logging
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple, Union
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)

class ValidationResult:
    """Resultado de validación"""
    
    def __init__(self, valid: bool = True, errors: List[str] = None, 
                 warnings: List[str] = None, value: Any = None):
        self.valid = valid
        self.errors = errors or []
        self.warnings = warnings or []
        self.value = value
    
    def add_error(self, error: str):
        """Agregar error"""
        self.errors.append(error)
        self.valid = False
    
    def add_warning(self, warning: str):
        """Agregar advertencia"""
        self.warnings.append(warning)
    
    def __bool__(self):
        return self.valid

class BaseValidator:
    """Validador base"""
    
    def __init__(self, required: bool = False, allow_empty: bool = True):
        self.required = required
        self.allow_empty = allow_empty
    
    def validate(self, value: Any, field_name: str = "Campo") -> ValidationResult:
        """Validar valor"""
        result = ValidationResult()
        
        # Validar requerido
        if self.required and (value is None or (isinstance(value, str) and not value.strip())):
            result.add_error(f"{field_name} es requerido")
            return result
        
        # Validar vacío
        if not self.allow_empty and isinstance(value, str) and not value.strip():
            result.add_error(f"{field_name} no puede estar vacío")
            return result
        
        # Si es None o vacío y no es requerido, es válido
        if value is None or (isinstance(value, str) and not value.strip()):
            result.value = value
            return result
        
        # Validación específica del validador
        return self._validate_value(value, field_name, result)
    
    def _validate_value(self, value: Any, field_name: str, result: ValidationResult) -> ValidationResult:
        """Validación específica (implementar en subclases)"""
        result.value = value
        return result

# ==================== VALIDADORES DE TEXTO ====================

class StringValidator(BaseValidator):
    """Validador de cadenas de texto"""
    
    def __init__(self, min_length: int = 0, max_length: int = None, 
                 pattern: str = None, **kwargs):
        super().__init__(**kwargs)
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = re.compile(pattern) if pattern else None
    
    def _validate_value(self, value: Any, field_name: str, result: ValidationResult) -> ValidationResult:
        if not isinstance(value, str):
            result.add_error(f"{field_name} debe ser una cadena de texto")
            return result
        
        # Validar longitud mínima
        if len(value) < self.min_length:
            result.add_error(f"{field_name} debe tener al menos {self.min_length} caracteres")
        
        # Validar longitud máxima
        if self.max_length and len(value) > self.max_length:
            result.add_error(f"{field_name} no puede tener más de {self.max_length} caracteres")
        
        # Validar patrón
        if self.pattern and not self.pattern.match(value):
            result.add_error(f"{field_name} no tiene el formato correcto")
        
        result.value = value.strip()
        return result

class EmailValidator(BaseValidator):
    """Validador de email"""
    
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    def _validate_value(self, value: Any, field_name: str, result: ValidationResult) -> ValidationResult:
        if not isinstance(value, str):
            result.add_error(f"{field_name} debe ser una cadena de texto")
            return result
        
        email = value.strip().lower()
        
        if not self.EMAIL_PATTERN.match(email):
            result.add_error(f"{field_name} no es un email válido")
        
        result.value = email
        return result

class PhoneValidator(BaseValidator):
    """Validador de teléfonos"""
    
    PHONE_PATTERNS = [
        re.compile(r'^\(\d{2,4}\)\s?\d{4}-?\d{4}$'),  # (011) 4444-5555
        re.compile(r'^\d{2,4}-?\d{4}-?\d{4}$'),       # 011-4444-5555
        re.compile(r'^\d{8,15}$'),                     # 1144445555
        re.compile(r'^\+\d{1,3}\s?\d{8,12}$')         # +54 1144445555
    ]
    
    def _validate_value(self, value: Any, field_name: str, result: ValidationResult) -> ValidationResult:
        if not isinstance(value, str):
            result.add_error(f"{field_name} debe ser una cadena de texto")
            return result
        
        phone = value.strip()
        
        # Verificar si coincide con algún patrón
        if not any(pattern.match(phone) for pattern in self.PHONE_PATTERNS):
            result.add_error(f"{field_name} no es un número de teléfono válido")
        
        result.value = phone
        return result

# ==================== VALIDADORES NUMÉRICOS ====================

class NumericValidator(BaseValidator):
    """Validador numérico base"""
    
    def __init__(self, min_value: Union[int, float] = None, 
                 max_value: Union[int, float] = None, **kwargs):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value
    
    def _validate_range(self, value: Union[int, float], field_name: str, 
                       result: ValidationResult) -> ValidationResult:
        """Validar rango"""
        if self.min_value is not None and value < self.min_value:
            result.add_error(f"{field_name} debe ser mayor o igual a {self.min_value}")
        
        if self.max_value is not None and value > self.max_value:
            result.add_error(f"{field_name} debe ser menor o igual a {self.max_value}")
        
        return result

class IntegerValidator(NumericValidator):
    """Validador de enteros"""
    
    def _validate_value(self, value: Any, field_name: str, result: ValidationResult) -> ValidationResult:
        try:
            if isinstance(value, str):
                int_value = int(value.strip())
            elif isinstance(value, (int, float)):
                int_value = int(value)
            else:
                result.add_error(f"{field_name} debe ser un número entero")
                return result
            
            result.value = int_value
            return self._validate_range(int_value, field_name, result)
            
        except (ValueError, TypeError):
            result.add_error(f"{field_name} debe ser un número entero válido")
            return result

class DecimalValidator(NumericValidator):
    """Validador de decimales"""
    
    def __init__(self, decimal_places: int = 2, **kwargs):
        super().__init__(**kwargs)
        self.decimal_places = decimal_places
    
    def _validate_value(self, value: Any, field_name: str, result: ValidationResult) -> ValidationResult:
        try:
            if isinstance(value, str):
                decimal_value = Decimal(value.strip())
            elif isinstance(value, (int, float, Decimal)):
                decimal_value = Decimal(str(value))
            else:
                result.add_error(f"{field_name} debe ser un número decimal")
                return result
            
            # Validar decimales
            if self.decimal_places >= 0:
                quantized = decimal_value.quantize(Decimal(10) ** -self.decimal_places)
                if quantized != decimal_value:
                    result.add_warning(f"{field_name} redondeado a {self.decimal_places} decimales")
                    decimal_value = quantized
            
            result.value = float(decimal_value)
            return self._validate_range(float(decimal_value), field_name, result)
            
        except (ValueError, TypeError, InvalidOperation):
            result.add_error(f"{field_name} debe ser un número decimal válido")
            return result

# ==================== VALIDADORES DE FECHA ====================

class DateValidator(BaseValidator):
    """Validador de fechas"""
    
    def __init__(self, min_date: date = None, max_date: date = None, 
                 date_format: str = '%Y-%m-%d', **kwargs):
        super().__init__(**kwargs)
        self.min_date = min_date
        self.max_date = max_date
        self.date_format = date_format
    
    def _validate_value(self, value: Any, field_name: str, result: ValidationResult) -> ValidationResult:
        try:
            if isinstance(value, str):
                date_value = datetime.strptime(value.strip(), self.date_format).date()
            elif isinstance(value, datetime):
                date_value = value.date()
            elif isinstance(value, date):
                date_value = value
            else:
                result.add_error(f"{field_name} debe ser una fecha válida")
                return result
            
            # Validar rango
            if self.min_date and date_value < self.min_date:
                result.add_error(f"{field_name} no puede ser anterior a {self.min_date}")
            
            if self.max_date and date_value > self.max_date:
                result.add_error(f"{field_name} no puede ser posterior a {self.max_date}")
            
            result.value = date_value
            return result
            
        except ValueError:
            result.add_error(f"{field_name} debe ser una fecha en formato {self.date_format}")
            return result

# ==================== VALIDADORES ESPECÍFICOS ====================

class DocumentValidator(BaseValidator):
    """Validador de documentos argentinos"""
    
    DNI_PATTERN = re.compile(r'^\d{7,8}$')
    CUIT_PATTERN = re.compile(r'^\d{2}-?\d{8}-?\d{1}$')
    
    def __init__(self, document_type: str = 'DNI', **kwargs):
        super().__init__(**kwargs)
        self.document_type = document_type.upper()
    
    def _validate_value(self, value: Any, field_name: str, result: ValidationResult) -> ValidationResult:
        if not isinstance(value, str):
            result.add_error(f"{field_name} debe ser una cadena de texto")
            return result
        
        document = value.strip().replace('-', '').replace('.', '')
        
        if self.document_type == 'DNI':
            if not self.DNI_PATTERN.match(document):
                result.add_error(f"{field_name} debe ser un DNI válido (7-8 dígitos)")
        
        elif self.document_type == 'CUIT':
            # Remover separadores para validación
            clean_cuit = document.replace('-', '')
            if not re.match(r'^\d{11}$', clean_cuit):
                result.add_error(f"{field_name} debe ser un CUIT válido (XX-XXXXXXXX-X)")
            else:
                # Validar dígito verificador
                if not self._validate_cuit_checksum(clean_cuit):
                    result.add_error(f"{field_name} tiene un dígito verificador inválido")
        
        result.value = document
        return result
    
    def _validate_cuit_checksum(self, cuit: str) -> bool:
        """Validar dígito verificador de CUIT"""
        try:
            # Coeficientes para cálculo
            coefficients = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
            
            # Calcular suma
            total = sum(int(cuit[i]) * coefficients[i] for i in range(10))
            
            # Calcular dígito verificador
            remainder = total % 11
            check_digit = 11 - remainder if remainder != 0 else 0
            
            return check_digit == int(cuit[10])
            
        except (ValueError, IndexError):
            return False

class SKUValidator(BaseValidator):
    """Validador de códigos SKU"""
    
    def __init__(self, allow_spaces: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.allow_spaces = allow_spaces
    
    def _validate_value(self, value: Any, field_name: str, result: ValidationResult) -> ValidationResult:
        if not isinstance(value, str):
            result.add_error(f"{field_name} debe ser una cadena de texto")
            return result
        
        sku = value.strip()
        
        # Validar caracteres
        if not self.allow_spaces and ' ' in sku:
            result.add_error(f"{field_name} no puede contener espacios")
        
        # Validar longitud
        if len(sku) < 3:
            result.add_error(f"{field_name} debe tener al menos 3 caracteres")
        
        if len(sku) > 50:
            result.add_error(f"{field_name} no puede tener más de 50 caracteres")
        
        result.value = sku.upper()
        return result

class BarcodeValidator(BaseValidator):
    """Validador de códigos de barras"""
    
    def _validate_value(self, value: Any, field_name: str, result: ValidationResult) -> ValidationResult:
        if not isinstance(value, str):
            result.add_error(f"{field_name} debe ser una cadena de texto")
            return result
        
        barcode = value.strip()
        
        # Validar que solo contenga números
        if not barcode.isdigit():
            result.add_error(f"{field_name} debe contener solo números")
            return result
        
        # Validar longitudes estándar
        valid_lengths = [8, 12, 13, 14]  # EAN-8, UPC-A, EAN-13, EAN-14
        if len(barcode) not in valid_lengths:
            result.add_warning(f"{field_name} no tiene una longitud estándar ({', '.join(map(str, valid_lengths))} dígitos)")
        
        result.value = barcode
        return result

# ==================== VALIDADORES DE NEGOCIO ====================

class PriceValidator(DecimalValidator):
    """Validador de precios"""
    
    def __init__(self, **kwargs):
        kwargs.setdefault('min_value', 0)
        kwargs.setdefault('decimal_places', 2)
        super().__init__(**kwargs)

class QuantityValidator(DecimalValidator):
    """Validador de cantidades"""
    
    def __init__(self, **kwargs):
        kwargs.setdefault('min_value', 0)
        kwargs.setdefault('decimal_places', 3)
        super().__init__(**kwargs)

class PercentageValidator(DecimalValidator):
    """Validador de porcentajes"""
    
    def __init__(self, **kwargs):
        kwargs.setdefault('min_value', 0)
        kwargs.setdefault('max_value', 100)
        kwargs.setdefault('decimal_places', 2)
        super().__init__(**kwargs)

# ==================== VALIDADOR COMPUESTO ====================

class FormValidator:
    """Validador de formularios completos"""
    
    def __init__(self):
        self.validators: Dict[str, BaseValidator] = {}
    
    def add_field(self, field_name: str, validator: BaseValidator):
        """Agregar campo a validar"""
        self.validators[field_name] = validator
        return self
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """Validar todos los campos"""
        result = ValidationResult()
        validated_data = {}
        
        for field_name, validator in self.validators.items():
            field_value = data.get(field_name)
            field_result = validator.validate(field_value, field_name)
            
            if not field_result.valid:
                result.errors.extend(field_result.errors)
                result.valid = False
            
            result.warnings.extend(field_result.warnings)
            validated_data[field_name] = field_result.value
        
        result.value = validated_data
        return result

# ==================== VALIDADORES DE CONVENIENCIA ====================

def validate_product_data(product_data: Dict[str, Any]) -> ValidationResult:
    """Validar datos de producto"""
    validator = FormValidator()
    
    validator.add_field('name', StringValidator(min_length=2, max_length=100, required=True))
    validator.add_field('sku', SKUValidator(required=True))
    validator.add_field('barcode', BarcodeValidator(required=False))
    validator.add_field('cost_price', PriceValidator(required=True))
    validator.add_field('sale_price', PriceValidator(required=True))
    validator.add_field('stock', QuantityValidator(required=False))
    validator.add_field('minimum_stock', QuantityValidator(required=False))
    
    return validator.validate(product_data)

def validate_customer_data(customer_data: Dict[str, Any]) -> ValidationResult:
    """Validar datos de cliente"""
    validator = FormValidator()
    
    # Al menos nombre o razón social
    if not customer_data.get('name') and not customer_data.get('business_name'):
        result = ValidationResult(False)
        result.add_error("Debe proporcionar nombre o razón social")
        return result
    
    validator.add_field('name', StringValidator(max_length=100, required=False))
    validator.add_field('business_name', StringValidator(max_length=100, required=False))
    validator.add_field('email', EmailValidator(required=False))
    validator.add_field('phone', PhoneValidator(required=False))
    validator.add_field('mobile', PhoneValidator(required=False))
    validator.add_field('credit_limit', DecimalValidator(min_value=0, required=False))
    validator.add_field('discount_percentage', PercentageValidator(required=False))
    
    return validator.validate(customer_data)

def validate_sale_data(sale_data: Dict[str, Any]) -> ValidationResult:
    """Validar datos de venta"""
    validator = FormValidator()
    
    validator.add_field('total', PriceValidator(min_value=0.01, required=True))
    validator.add_field('date', DateValidator(required=True))
    validator.add_field('payment_method', StringValidator(required=True))
    
    # Validar items
    result = validator.validate(sale_data)
    
    if 'items' not in sale_data or not sale_data['items']:
        result.add_error("La venta debe tener al menos un item")
        result.valid = False
    
    return result

# ==================== UTILIDADES ====================

def clean_numeric_string(value: str) -> str:
    """Limpiar string numérico"""
    if not isinstance(value, str):
        return str(value)
    
    # Remover caracteres no numéricos excepto punto y coma
    cleaned = re.sub(r'[^\d.,-]', '', value)
    
    # Reemplazar coma por punto para decimales
    cleaned = cleaned.replace(',', '.')
    
    return cleaned

def format_document(document: str, document_type: str) -> str:
    """Formatear documento según tipo"""
    if not document:
        return document
    
    clean_doc = document.replace('-', '').replace('.', '').strip()
    
    if document_type.upper() == 'CUIT' and len(clean_doc) == 11:
        return f"{clean_doc[:2]}-{clean_doc[2:10]}-{clean_doc[10]}"
    
    return clean_doc

def is_valid_email(email: str) -> bool:
    """Verificar si es un email válido"""
    validator = EmailValidator()
    result = validator.validate(email, "Email")
    return result.valid

def is_valid_phone(phone: str) -> bool:
    """Verificar si es un teléfono válido"""
    validator = PhoneValidator()
    result = validator.validate(phone, "Teléfono")
    return result.valid