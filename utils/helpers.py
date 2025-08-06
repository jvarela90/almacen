"""
Funciones de Utilidad para AlmacénPro
Colección de funciones helper y utilidades para todo el sistema
"""

import os
import re
import hashlib
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
import uuid
import subprocess
import sys

logger = logging.getLogger(__name__)

# ============================================================================
# VALIDACIONES
# ============================================================================

def validate_email(email: str) -> bool:
    """Validar formato de email"""
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email.strip()) is not None

def validate_phone(phone: str) -> bool:
    """Validar formato de teléfono"""
    if not phone or not isinstance(phone, str):
        return False
    
    # Limpiar teléfono
    clean_phone = re.sub(r'[^\d+]', '', phone.strip())
    
    # Patrones válidos
    patterns = [
        r'^\+?[1-9]\d{1,14}$',  # Formato internacional
        r'^\d{7,15}$',          # Formato nacional
        r'^\+54\d{10}$',        # Argentina específico
    ]
    
    return any(re.match(pattern, clean_phone) for pattern in patterns)

def validate_cuit_cuil(cuit_cuil: str) -> bool:
    """Validar CUIT/CUIL argentino"""
    if not cuit_cuil or not isinstance(cuit_cuil, str):
        return False
    
    # Limpiar guiones y espacios
    cuit_cuil = re.sub(r'[-\s]', '', cuit_cuil.strip())
    
    # Debe tener exactamente 11 dígitos
    if not re.match(r'^\d{11}$', cuit_cuil):
        return False
    
    # Algoritmo de validación de CUIT/CUIL
    try:
        multiplicadores = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        suma = sum(int(cuit_cuil[i]) * multiplicadores[i] for i in range(10))
        
        resto = suma % 11
        if resto < 2:
            digito_verificador = resto
        else:
            digito_verificador = 11 - resto
        
        return int(cuit_cuil[10]) == digito_verificador
        
    except Exception as e:
        logger.error(f"Error validando CUIT/CUIL: {e}")
        return False

def validate_barcode(barcode: str) -> bool:
    """Validar código de barras"""
    if not barcode or not isinstance(barcode, str):
        return False
    
    # Limpiar código
    clean_barcode = barcode.strip()
    
    # Patrones válidos para diferentes tipos de códigos
    patterns = [
        r'^\d{8}$',   # EAN-8
        r'^\d{12}$',  # UPC-A
        r'^\d{13}$',  # EAN-13
        r'^\d{14}$',  # ITF-14
    ]
    
    return any(re.match(pattern, clean_barcode) for pattern in patterns)

def validate_price(price: Union[str, float, Decimal]) -> bool:
    """Validar precio"""
    try:
        if isinstance(price, str):
            # Limpiar string de precio
            clean_price = re.sub(r'[^\d.,]', '', price.strip())
            clean_price = clean_price.replace(',', '.')
            price = float(clean_price)
        
        return isinstance(price, (int, float, Decimal)) and price >= 0
        
    except (ValueError, TypeError):
        return False

def validate_quantity(quantity: Union[str, float, Decimal]) -> bool:
    """Validar cantidad"""
    try:
        if isinstance(quantity, str):
            clean_quantity = quantity.strip().replace(',', '.')
            quantity = float(clean_quantity)
        
        return isinstance(quantity, (int, float, Decimal)) and quantity >= 0
        
    except (ValueError, TypeError):
        return False

# ============================================================================
# FORMATEO Y CONVERSIONES
# ============================================================================

def format_currency(amount: Union[float, Decimal, int], currency_symbol: str = "$") -> str:
    """Formatear cantidad como moneda"""
    try:
        if isinstance(amount, str):
            amount = float(amount)
        
        # Redondear a 2 decimales
        amount = round(float(amount), 2)
        
        # Formatear con separadores de miles
        formatted = f"{amount:,.2f}"
        
        return f"{currency_symbol}{formatted}"
        
    except (ValueError, TypeError):
        return f"{currency_symbol}0.00"

def format_percentage(value: Union[float, Decimal, int], decimals: int = 1) -> str:
    """Formatear como porcentaje"""
    try:
        if isinstance(value, str):
            value = float(value)
        
        formatted = f"{float(value):.{decimals}f}"
        return f"{formatted}%"
        
    except (ValueError, TypeError):
        return "0.0%"

def format_quantity(quantity: Union[float, Decimal, int], decimals: int = 2) -> str:
    """Formatear cantidad"""
    try:
        if isinstance(quantity, str):
            quantity = float(quantity)
        
        # Si es número entero, no mostrar decimales
        if float(quantity).is_integer():
            return str(int(quantity))
        else:
            return f"{float(quantity):.{decimals}f}"
            
    except (ValueError, TypeError):
        return "0"

def format_date(date_obj: Union[datetime, date, str], format_str: str = "%d/%m/%Y") -> str:
    """Formatear fecha"""
    try:
        if isinstance(date_obj, str):
            # Intentar parsear diferentes formatos
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"]:
                try:
                    date_obj = datetime.strptime(date_obj, fmt)
                    break
                except ValueError:
                    continue
        
        if isinstance(date_obj, datetime):
            return date_obj.strftime(format_str)
        elif isinstance(date_obj, date):
            return date_obj.strftime(format_str)
        else:
            return "Fecha inválida"
            
    except Exception as e:
        logger.error(f"Error formateando fecha: {e}")
        return "Fecha inválida"

def format_datetime(datetime_obj: Union[datetime, str], format_str: str = "%d/%m/%Y %H:%M") -> str:
    """Formatear fecha y hora"""
    try:
        if isinstance(datetime_obj, str):
            # Intentar parsear ISO format
            if 'T' in datetime_obj:
                datetime_obj = datetime.fromisoformat(datetime_obj.replace('Z', '+00:00'))
            else:
                datetime_obj = datetime.fromisoformat(datetime_obj)
        
        if isinstance(datetime_obj, datetime):
            return datetime_obj.strftime(format_str)
        else:
            return "Fecha inválida"
            
    except Exception as e:
        logger.error(f"Error formateando datetime: {e}")
        return "Fecha inválida"

def parse_currency(currency_str: str) -> float:
    """Parsear string de moneda a float"""
    try:
        # Remover símbolos de moneda y espacios
        clean_str = re.sub(r'[^\d.,+-]', '', currency_str.strip())
        
        # Manejar separadores decimales
        if ',' in clean_str and '.' in clean_str:
            # Determinar cuál es el separador decimal
            if clean_str.rfind(',') > clean_str.rfind('.'):
                # Coma es decimal
                clean_str = clean_str.replace('.', '').replace(',', '.')
            else:
                # Punto es decimal
                clean_str = clean_str.replace(',', '')
        elif ',' in clean_str:
            # Solo coma - podría ser decimal o miles
            if len(clean_str.split(',')[-1]) == 2:
                # Probablemente decimal
                clean_str = clean_str.replace(',', '.')
            else:
                # Probablemente miles
                clean_str = clean_str.replace(',', '')
        
        return float(clean_str)
        
    except (ValueError, TypeError):
        return 0.0

# ============================================================================
# CÁLCULOS FINANCIEROS
# ============================================================================

def calculate_tax(base_amount: float, tax_rate: float) -> float:
    """Calcular impuesto"""
    try:
        return float(base_amount) * (float(tax_rate) / 100)
    except (ValueError, TypeError):
        return 0.0

def calculate_discount(base_amount: float, discount_rate: float) -> float:
    """Calcular descuento"""
    try:
        return float(base_amount) * (float(discount_rate) / 100)
    except (ValueError, TypeError):
        return 0.0

def calculate_markup(cost: float, markup_percentage: float) -> float:
    """Calcular precio con margen"""
    try:
        cost = float(cost)
        markup = float(markup_percentage)
        return cost * (1 + markup / 100)
    except (ValueError, TypeError):
        return 0.0

def calculate_margin_percentage(cost: float, selling_price: float) -> float:
    """Calcular porcentaje de margen"""
    try:
        cost = float(cost)
        selling_price = float(selling_price)
        
        if selling_price == 0:
            return 0.0
        
        return ((selling_price - cost) / selling_price) * 100
        
    except (ValueError, TypeError, ZeroDivisionError):
        return 0.0

def round_currency(amount: Union[float, Decimal]) -> Decimal:
    """Redondear cantidad de moneda"""
    try:
        return Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except (ValueError, TypeError):
        return Decimal('0.00')

# ============================================================================
# GENERACIÓN DE CÓDIGOS
# ============================================================================

def generate_uuid() -> str:
    """Generar UUID único"""
    return str(uuid.uuid4())

def generate_short_id(length: int = 8) -> str:
    """Generar ID corto alfanumérico"""
    import random
    import string
    
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def generate_barcode(prefix: str = "200") -> str:
    """Generar código de barras interno"""
    import random
    
    # Generar 9 dígitos después del prefijo
    suffix = ''.join([str(random.randint(0, 9)) for _ in range(9)])
    barcode = prefix + suffix
    
    # Calcular dígito verificador para EAN-13
    check_digit = calculate_ean13_check_digit(barcode)
    
    return barcode + str(check_digit)

def calculate_ean13_check_digit(barcode: str) -> int:
    """Calcular dígito verificador EAN-13"""
    try:
        # Solo usar los primeros 12 dígitos
        barcode = barcode[:12]
        
        odd_sum = sum(int(barcode[i]) for i in range(0, 12, 2))
        even_sum = sum(int(barcode[i]) for i in range(1, 12, 2))
        
        total = odd_sum + (even_sum * 3)
        check_digit = (10 - (total % 10)) % 10
        
        return check_digit
        
    except (ValueError, IndexError):
        return 0

def generate_invoice_number(prefix: str = "", sequence: int = 1) -> str:
    """Generar número de factura"""
    today = datetime.now().strftime("%Y%m%d")
    return f"{prefix}{today}{sequence:04d}"

# ============================================================================
# ARCHIVOS Y SISTEMA
# ============================================================================

def ensure_directory(directory_path: Union[str, Path]) -> Path:
    """Asegurar que un directorio existe"""
    path = Path(directory_path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_file_size_human(file_path: Union[str, Path]) -> str:
    """Obtener tamaño de archivo en formato humano"""
    try:
        size = Path(file_path).stat().st_size
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        
        return f"{size:.1f} PB"
        
    except (OSError, ValueError):
        return "Desconocido"

def calculate_file_hash(file_path: Union[str, Path], algorithm: str = 'md5') -> str:
    """Calcular hash de archivo"""
    try:
        hash_obj = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
        
    except Exception as e:
        logger.error(f"Error calculando hash: {e}")
        return ""

def open_file_explorer(path: Union[str, Path]):
    """Abrir explorador de archivos en la ruta especificada"""
    try:
        path = Path(path)
        
        if sys.platform == "win32":
            subprocess.Popen(f'explorer "{path}"')
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
            
    except Exception as e:
        logger.error(f"Error abriendo explorador: {e}")

def is_file_locked(file_path: Union[str, Path]) -> bool:
    """Verificar si un archivo está bloqueado"""
    try:
        with open(file_path, 'a'):
            return False
    except IOError:
        return True

# ============================================================================
# STRINGS Y TEXTO
# ============================================================================

def clean_string(text: str, max_length: int = None) -> str:
    """Limpiar y normalizar string"""
    if not text or not isinstance(text, str):
        return ""
    
    # Limpiar espacios en blanco
    cleaned = ' '.join(text.strip().split())
    
    # Truncar si es necesario
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length-3] + "..."
    
    return cleaned

def normalize_string(text: str) -> str:
    """Normalizar string para búsquedas"""
    if not text or not isinstance(text, str):
        return ""
    
    import unicodedata
    
    # Normalizar unicode y remover acentos
    normalized = unicodedata.normalize('NFKD', text)
    ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
    
    # Convertir a minúsculas y limpiar
    return clean_string(ascii_text.lower())

def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncar string con sufijo"""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def pluralize(word: str, count: int, plural_form: str = None) -> str:
    """Pluralizar palabra según cantidad"""
    if count == 1:
        return word
    
    if plural_form:
        return plural_form
    
    # Reglas básicas de pluralización en español
    if word.endswith(('a', 'e', 'i', 'o', 'u')):
        return word + 's'
    else:
        return word + 'es'

# ============================================================================
# FECHAS Y TIEMPO
# ============================================================================

def get_date_range(period: str) -> Tuple[date, date]:
    """Obtener rango de fechas para períodos comunes"""
    today = date.today()
    
    if period == "today":
        return today, today
    elif period == "yesterday":
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday
    elif period == "this_week":
        days_since_monday = today.weekday()
        start_week = today - timedelta(days=days_since_monday)
        return start_week, today
    elif period == "last_week":
        days_since_monday = today.weekday()
        start_this_week = today - timedelta(days=days_since_monday)
        end_last_week = start_this_week - timedelta(days=1)
        start_last_week = end_last_week - timedelta(days=6)
        return start_last_week, end_last_week
    elif period == "this_month":
        start_month = today.replace(day=1)
        return start_month, today
    elif period == "last_month":
        first_this_month = today.replace(day=1)
        last_day_prev_month = first_this_month - timedelta(days=1)
        first_prev_month = last_day_prev_month.replace(day=1)
        return first_prev_month, last_day_prev_month
    elif period == "this_year":
        start_year = today.replace(month=1, day=1)
        return start_year, today
    elif period == "last_30_days":
        start_date = today - timedelta(days=30)
        return start_date, today
    elif period == "last_90_days":
        start_date = today - timedelta(days=90)
        return start_date, today
    else:
        return today, today

def business_days_between(start_date: date, end_date: date) -> int:
    """Calcular días hábiles entre dos fechas"""
    current_date = start_date
    business_days = 0
    
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Lunes a Viernes
            business_days += 1
        current_date += timedelta(days=1)
    
    return business_days

def is_business_day(check_date: date) -> bool:
    """Verificar si una fecha es día hábil"""
    return check_date.weekday() < 5

# ============================================================================
# LOGGING Y DEBUG
# ============================================================================

def setup_file_logging(log_file: str, level: str = "INFO") -> logging.Logger:
    """Configurar logging a archivo"""
    logger = logging.getLogger(__name__)
    
    # Crear handler de archivo
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(getattr(logging, level.upper()))
    
    # Formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    return logger

def log_execution_time(func):
    """Decorador para medir tiempo de ejecución"""
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        logger.debug(f"{func.__name__} ejecutado en {execution_time:.4f} segundos")
        
        return result
    
    return wrapper

# ============================================================================
# CONFIGURACIÓN Y ENTORNO
# ============================================================================

def get_app_data_dir(app_name: str = "AlmacenPro") -> Path:
    """Obtener directorio de datos de aplicación"""
    if sys.platform == "win32":
        base_dir = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
    elif sys.platform == "darwin":
        base_dir = Path.home() / 'Library' / 'Application Support'
    else:
        base_dir = Path.home() / '.local' / 'share'
    
    app_dir = base_dir / app_name
    app_dir.mkdir(parents=True, exist_ok=True)
    
    return app_dir

def get_system_info() -> Dict[str, Any]:
    """Obtener información del sistema"""
    import platform
    
    return {
        'platform': platform.system(),
        'platform_release': platform.release(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'hostname': platform.node()
    }

# ============================================================================
# UTILIDADES DE DATOS
# ============================================================================

def safe_divide(dividend: float, divisor: float, default: float = 0.0) -> float:
    """División segura que evita división por cero"""
    try:
        if divisor == 0:
            return default
        return dividend / divisor
    except (TypeError, ValueError):
        return default

def safe_percentage(value: float, total: float) -> float:
    """Calcular porcentaje de forma segura"""
    return safe_divide(value * 100, total, 0.0)

def clamp(value: Union[int, float], min_value: Union[int, float], max_value: Union[int, float]) -> Union[int, float]:
    """Limitar valor entre mínimo y máximo"""
    return max(min_value, min(max_value, value))

def chunks(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Dividir lista en chunks del tamaño especificado"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

# ============================================================================
# FUNCIONES DE CONVENIENCIA
# ============================================================================

def yes_no_to_bool(value: str) -> bool:
    """Convertir string sí/no a booleano"""
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        value = value.lower().strip()
        return value in ('sí', 'si', 'yes', 'y', '1', 'true', 'verdadero')
    
    return bool(value)

def bool_to_yes_no(value: bool, language: str = 'es') -> str:
    """Convertir booleano a string sí/no"""
    if language == 'es':
        return 'Sí' if value else 'No'
    else:
        return 'Yes' if value else 'No'

def get_default_if_empty(value: Any, default: Any) -> Any:
    """Retornar valor por defecto si el valor está vacío"""
    if value is None or value == "" or (isinstance(value, (list, dict, tuple)) and len(value) == 0):
        return default
    return value