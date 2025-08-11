"""
Modelos de Datos - AlmacénPro v2.0 MVC
Contiene todos los modelos de datos y entidades del dominio
"""

from .base_model import BaseModel
from .entities import *

__all__ = [
    'BaseModel',
    'Product',
    'Customer', 
    'Sale',
    'SaleItem',
    'User',
    'Category',
    'Provider'
]