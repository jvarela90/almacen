"""
Formateadores de texto y números - AlmacénPro v2.0
Utilidades para formatear datos para presentación en UI y reportes
"""

import re
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Optional, Union

class NumberFormatter:
    """Formateador de números y moneda"""
    
    @staticmethod
    def format_currency(amount: Union[float, Decimal, int], 
                       currency_symbol: str = "$", 
                       decimal_places: int = 2) -> str:
        """Formatear monto como moneda"""
        try:
            if amount is None:
                return f"{currency_symbol}0.00"
            
            amount = float(amount)
            return f"{currency_symbol}{amount:,.{decimal_places}f}"
        except (ValueError, TypeError):
            return f"{currency_symbol}0.00"
    
    @staticmethod
    def format_percentage(value: Union[float, Decimal, int], 
                         decimal_places: int = 2) -> str:
        """Formatear como porcentaje"""
        try:
            if value is None:
                return "0.00%"
            
            value = float(value)
            return f"{value:.{decimal_places}f}%"
        except (ValueError, TypeError):
            return "0.00%"
    
    @staticmethod
    def format_number(value: Union[float, Decimal, int], 
                     decimal_places: int = 2, 
                     thousands_separator: bool = True) -> str:
        """Formatear número con separadores de miles"""
        try:
            if value is None:
                return "0.00"
            
            value = float(value)
            if thousands_separator:
                return f"{value:,.{decimal_places}f}"
            else:
                return f"{value:.{decimal_places}f}"
        except (ValueError, TypeError):
            return "0.00"
    
    @staticmethod
    def format_integer(value: Union[int, float, str]) -> str:
        """Formatear como entero con separadores de miles"""
        try:
            if value is None:
                return "0"
            
            value = int(float(value))
            return f"{value:,}"
        except (ValueError, TypeError):
            return "0"
    
    @staticmethod
    def parse_currency(currency_str: str) -> float:
        """Parsear string de moneda a float"""
        try:
            # Remover símbolos de moneda y espacios
            cleaned = re.sub(r'[^\d.,\-]', '', currency_str)
            # Reemplazar comas por puntos si es el último separador
            if ',' in cleaned and '.' in cleaned:
                # Si tiene ambos, asumir que coma es miles y punto decimal
                cleaned = cleaned.replace(',', '')
            elif ',' in cleaned:
                # Si solo tiene coma, podría ser decimal
                parts = cleaned.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    cleaned = cleaned.replace(',', '.')
                else:
                    cleaned = cleaned.replace(',', '')
            
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0


class DateFormatter:
    """Formateador de fechas"""
    
    @staticmethod
    def format_date(date_obj: Union[date, datetime, str], 
                   format_str: str = "%d/%m/%Y") -> str:
        """Formatear fecha"""
        try:
            if date_obj is None:
                return ""
            
            if isinstance(date_obj, str):
                # Intentar parsear diferentes formatos
                for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%d-%m-%Y"]:
                    try:
                        date_obj = datetime.strptime(date_obj, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return date_obj  # No se pudo parsear, devolver como string
            
            if isinstance(date_obj, datetime):
                return date_obj.strftime(format_str)
            elif isinstance(date_obj, date):
                return date_obj.strftime(format_str)
            
            return str(date_obj)
        except (ValueError, TypeError):
            return ""
    
    @staticmethod
    def format_datetime(datetime_obj: Union[datetime, str], 
                       format_str: str = "%d/%m/%Y %H:%M") -> str:
        """Formatear fecha y hora"""
        try:
            if datetime_obj is None:
                return ""
            
            if isinstance(datetime_obj, str):
                # Intentar parsear
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%d/%m/%Y %H:%M"]:
                    try:
                        datetime_obj = datetime.strptime(datetime_obj, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return datetime_obj  # No se pudo parsear
            
            if isinstance(datetime_obj, datetime):
                return datetime_obj.strftime(format_str)
            
            return str(datetime_obj)
        except (ValueError, TypeError):
            return ""
    
    @staticmethod
    def format_time_ago(date_obj: Union[date, datetime, str]) -> str:
        """Formatear como 'hace X tiempo'"""
        try:
            if date_obj is None:
                return ""
            
            if isinstance(date_obj, str):
                # Intentar parsear
                for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S"]:
                    try:
                        date_obj = datetime.strptime(date_obj, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return date_obj
            
            if isinstance(date_obj, date) and not isinstance(date_obj, datetime):
                date_obj = datetime.combine(date_obj, datetime.min.time())
            
            now = datetime.now()
            diff = now - date_obj
            
            if diff.days > 365:
                years = diff.days // 365
                return f"hace {years} año{'s' if years != 1 else ''}"
            elif diff.days > 30:
                months = diff.days // 30
                return f"hace {months} mes{'es' if months != 1 else ''}"
            elif diff.days > 0:
                return f"hace {diff.days} día{'s' if diff.days != 1 else ''}"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"hace {hours} hora{'s' if hours != 1 else ''}"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"hace {minutes} minuto{'s' if minutes != 1 else ''}"
            else:
                return "hace un momento"
                
        except (ValueError, TypeError):
            return ""


class TextFormatter:
    """Formateador de texto"""
    
    @staticmethod
    def truncate(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncar texto con sufijo"""
        if not text:
            return ""
        
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def capitalize_words(text: str) -> str:
        """Capitalizar cada palabra"""
        if not text:
            return ""
        
        return " ".join(word.capitalize() for word in text.split())
    
    @staticmethod
    def format_phone(phone: str) -> str:
        """Formatear número de teléfono argentino"""
        if not phone:
            return ""
        
        # Remover caracteres no numéricos
        digits = re.sub(r'\D', '', phone)
        
        # Formatear según longitud
        if len(digits) == 10:  # Teléfono fijo: (011) 1234-5678
            return f"({digits[:3]}) {digits[3:7]}-{digits[7:]}"
        elif len(digits) == 11:  # Celular: (011) 15-1234-5678
            return f"({digits[:3]}) {digits[3:5]}-{digits[5:9]}-{digits[9:]}"
        else:
            return phone  # Devolver original si no coincide con formato esperado
    
    @staticmethod
    def format_cuit(cuit: str) -> str:
        """Formatear CUIT/DNI"""
        if not cuit:
            return ""
        
        digits = re.sub(r'\D', '', cuit)
        
        if len(digits) == 11:  # CUIT: 12-34567890-1
            return f"{digits[:2]}-{digits[2:10]}-{digits[10]}"
        elif len(digits) == 8:  # DNI: 12.345.678
            return f"{digits[:2]}.{digits[2:5]}.{digits[5:]}"
        else:
            return cuit
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Limpiar texto removiendo caracteres especiales"""
        if not text:
            return ""
        
        # Remover múltiples espacios y trim
        cleaned = re.sub(r'\s+', ' ', text.strip())
        return cleaned
    
    @staticmethod
    def format_address(address: str, max_length: int = 50) -> str:
        """Formatear dirección"""
        if not address:
            return ""
        
        cleaned = TextFormatter.clean_text(address)
        return TextFormatter.truncate(cleaned, max_length)


class StatusFormatter:
    """Formateador para estados y categorías"""
    
    STATUS_COLORS = {
        'ACTIVO': '#27ae60',
        'INACTIVO': '#e74c3c', 
        'PENDIENTE': '#f39c12',
        'COMPLETADO': '#27ae60',
        'CANCELADO': '#e74c3c',
        'EN_PROCESO': '#3498db',
        'VENCIDO': '#e74c3c',
        'PAGADO': '#27ae60',
        'DEBE': '#e74c3c',
        'HABER': '#27ae60'
    }
    
    STATUS_LABELS = {
        'ACTIVO': '✅ Activo',
        'INACTIVO': '❌ Inactivo',
        'PENDIENTE': '⏳ Pendiente', 
        'COMPLETADO': '✅ Completado',
        'CANCELADO': '❌ Cancelado',
        'EN_PROCESO': '🔄 En Proceso',
        'VENCIDO': '⚠️ Vencido',
        'PAGADO': '💚 Pagado',
        'DEBE': '🔴 Debe',
        'HABER': '🟢 Haber'
    }
    
    @staticmethod
    def format_status(status: str) -> str:
        """Formatear estado con emoji"""
        if not status:
            return ""
        
        return StatusFormatter.STATUS_LABELS.get(status.upper(), status)
    
    @staticmethod
    def get_status_color(status: str) -> str:
        """Obtener color para estado"""
        if not status:
            return "#7f8c8d"
        
        return StatusFormatter.STATUS_COLORS.get(status.upper(), "#7f8c8d")


class ReportFormatter:
    """Formateador para reportes"""
    
    @staticmethod
    def format_header(title: str, company_name: str = "AlmacénPro", 
                     date_generated: Optional[datetime] = None) -> str:
        """Formatear header de reporte"""
        if date_generated is None:
            date_generated = datetime.now()
        
        return f"""
{company_name}
{title}
Generado: {DateFormatter.format_datetime(date_generated)}
{'-' * 60}
"""
    
    @staticmethod
    def format_table_row(*values, widths: Optional[list] = None) -> str:
        """Formatear fila de tabla para reporte texto"""
        if widths is None:
            widths = [15] * len(values)
        
        formatted_values = []
        for i, value in enumerate(values):
            width = widths[i] if i < len(widths) else 15
            str_value = str(value) if value is not None else ""
            formatted_values.append(str_value.ljust(width)[:width])
        
        return " | ".join(formatted_values)
    
    @staticmethod
    def format_summary(data: dict, title: str = "Resumen") -> str:
        """Formatear resumen con datos clave"""
        lines = [f"\n{title}", "=" * len(title)]
        
        for key, value in data.items():
            formatted_key = key.replace('_', ' ').title()
            if isinstance(value, (int, float)):
                if 'monto' in key.lower() or 'total' in key.lower() or 'precio' in key.lower():
                    formatted_value = NumberFormatter.format_currency(value)
                else:
                    formatted_value = NumberFormatter.format_number(value)
            else:
                formatted_value = str(value)
            
            lines.append(f"{formatted_key}: {formatted_value}")
        
        return "\n".join(lines)


class ValidationFormatter:
    """Formateador para validaciones y mensajes"""
    
    @staticmethod
    def format_validation_error(field_name: str, error_message: str) -> str:
        """Formatear mensaje de error de validación"""
        return f"❌ {field_name}: {error_message}"
    
    @staticmethod
    def format_success_message(message: str) -> str:
        """Formatear mensaje de éxito"""
        return f"✅ {message}"
    
    @staticmethod
    def format_warning_message(message: str) -> str:
        """Formatear mensaje de advertencia"""
        return f"⚠️ {message}"
    
    @staticmethod
    def format_info_message(message: str) -> str:
        """Formatear mensaje informativo"""
        return f"ℹ️ {message}"


# Funciones de conveniencia
def currency(amount: Union[float, Decimal, int], symbol: str = "$") -> str:
    """Función de conveniencia para formatear moneda"""
    return NumberFormatter.format_currency(amount, symbol)

def percent(value: Union[float, Decimal, int]) -> str:
    """Función de conveniencia para formatear porcentaje"""
    return NumberFormatter.format_percentage(value)

def number(value: Union[float, Decimal, int], decimals: int = 2) -> str:
    """Función de conveniencia para formatear número"""
    return NumberFormatter.format_number(value, decimals)

def date_format(date_obj: Union[date, datetime, str]) -> str:
    """Función de conveniencia para formatear fecha"""
    return DateFormatter.format_date(date_obj)

def datetime_format(datetime_obj: Union[datetime, str]) -> str:
    """Función de conveniencia para formatear fecha y hora"""
    return DateFormatter.format_datetime(datetime_obj)

def truncate(text: str, length: int) -> str:
    """Función de conveniencia para truncar texto"""
    return TextFormatter.truncate(text, length)

def phone(phone_number: str) -> str:
    """Función de conveniencia para formatear teléfono"""
    return TextFormatter.format_phone(phone_number)

def cuit(cuit_number: str) -> str:
    """Función de conveniencia para formatear CUIT"""
    return TextFormatter.format_cuit(cuit_number)

def status(status_value: str) -> str:
    """Función de conveniencia para formatear estado"""
    return StatusFormatter.format_status(status_value)


# Constantes útiles
CURRENCY_SYMBOLS = {
    'ARS': '$',
    'USD': 'US$',
    'EUR': '€',
    'BRL': 'R$'
}

DATE_FORMATS = {
    'SHORT': "%d/%m/%Y",
    'LONG': "%d de %B de %Y",
    'DATETIME': "%d/%m/%Y %H:%M",
    'DATETIME_FULL': "%d/%m/%Y %H:%M:%S",
    'ISO': "%Y-%m-%d",
    'ISO_DATETIME': "%Y-%m-%d %H:%M:%S"
}