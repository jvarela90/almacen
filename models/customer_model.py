"""
Modelo de Clientes - AlmacénPro v2.0 MVC
Modelo que gestiona el estado y lógica de datos para clientes
"""

from PyQt5.QtCore import pyqtSignal
from typing import List, Dict, Optional
from datetime import datetime
import logging

from .base_model import BaseModel
from .entities import Customer

logger = logging.getLogger(__name__)

class CustomerModel(BaseModel):
    """Modelo de datos para el sistema de clientes"""
    
    # Señales específicas para clientes
    customer_selected = pyqtSignal(dict)
    customer_updated = pyqtSignal(dict)
    customer_deleted = pyqtSignal(int)
    customers_loaded = pyqtSignal(list)
    filters_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Estado del modelo
        self._customers = []
        self._filtered_customers = []
        self._selected_customer = None
        
        # Filtros activos
        self._filters = {
            'search_text': '',
            'segment': 'Todos',
            'status': 'Todos',
            'active_only': False
        }
        
        # Estadísticas
        self._statistics = {
            'total_customers': 0,
            'active_customers': 0,
            'vip_customers': 0,
            'total_sales_amount': 0.0
        }
    
    # === PROPIEDADES ===
    
    @property
    def customers(self) -> List[Dict]:
        """Obtener lista completa de clientes"""
        return self._customers.copy()
    
    @property
    def filtered_customers(self) -> List[Dict]:
        """Obtener lista filtrada de clientes"""
        return self._filtered_customers.copy()
    
    @property
    def selected_customer(self) -> Optional[Customer]:
        """Obtener cliente seleccionado"""
        return self._selected_customer
    
    @property
    def filters(self) -> Dict:
        """Obtener filtros activos"""
        return self._filters.copy()
    
    @property
    def statistics(self) -> Dict:
        """Obtener estadísticas"""
        return self._statistics.copy()
    
    # === MÉTODOS PÚBLICOS ===
    
    def load_customers(self, customers_data: List[Dict]):
        """Cargar lista de clientes"""
        try:
            self.start_loading()
            
            self._customers = customers_data.copy()
            self._update_statistics()
            self._apply_filters()
            
            # Emitir señales
            self.customers_loaded.emit(self._customers)
            self.data_changed.emit()
            
            self.logger.info(f"Clientes cargados: {len(self._customers)}")
            
        except Exception as e:
            self.logger.error(f"Error cargando clientes: {e}")
            self._set_error(f"Error cargando clientes: {str(e)}")
        finally:
            self.finish_loading()
    
    def add_customer(self, customer_data: Dict) -> bool:
        """Agregar nuevo cliente"""
        try:
            if not self._validate_customer_data(customer_data):
                return False
            
            # Agregar a la lista
            self._customers.append(customer_data)
            
            # Actualizar estadísticas y filtros
            self._update_statistics()
            self._apply_filters()
            
            # Emitir señales
            self.data_changed.emit()
            
            self.logger.info(f"Cliente agregado: {customer_data.get('nombre', 'Sin nombre')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error agregando cliente: {e}")
            self._set_error(f"Error agregando cliente: {str(e)}")
            return False
    
    def update_customer(self, customer_id: int, customer_data: Dict) -> bool:
        """Actualizar cliente existente"""
        try:
            if not self._validate_customer_data(customer_data):
                return False
            
            # Buscar y actualizar cliente
            for i, customer in enumerate(self._customers):
                if customer.get('id') == customer_id:
                    self._customers[i] = customer_data.copy()
                    
                    # Si es el cliente seleccionado, actualizarlo también
                    if self._selected_customer and self._selected_customer.id == customer_id:
                        self._selected_customer = Customer.from_dict(customer_data)
                        self.customer_selected.emit(customer_data)
                    
                    # Actualizar estadísticas y filtros
                    self._update_statistics()
                    self._apply_filters()
                    
                    # Emitir señales
                    self.customer_updated.emit(customer_data)
                    self.data_changed.emit()
                    
                    self.logger.info(f"Cliente actualizado: {customer_data.get('nombre', 'Sin nombre')}")
                    return True
            
            self._set_error("Cliente no encontrado")
            return False
            
        except Exception as e:
            self.logger.error(f"Error actualizando cliente: {e}")
            self._set_error(f"Error actualizando cliente: {str(e)}")
            return False
    
    def remove_customer(self, customer_id: int) -> bool:
        """Eliminar cliente"""
        try:
            # Buscar y eliminar cliente
            for i, customer in enumerate(self._customers):
                if customer.get('id') == customer_id:
                    removed_customer = self._customers.pop(i)
                    
                    # Si era el cliente seleccionado, deseleccionar
                    if self._selected_customer and self._selected_customer.id == customer_id:
                        self._selected_customer = None
                        self.customer_selected.emit({})
                    
                    # Actualizar estadísticas y filtros
                    self._update_statistics()
                    self._apply_filters()
                    
                    # Emitir señales
                    self.customer_deleted.emit(customer_id)
                    self.data_changed.emit()
                    
                    self.logger.info(f"Cliente eliminado: {removed_customer.get('nombre', 'Sin nombre')}")
                    return True
            
            self._set_error("Cliente no encontrado")
            return False
            
        except Exception as e:
            self.logger.error(f"Error eliminando cliente: {e}")
            self._set_error(f"Error eliminando cliente: {str(e)}")
            return False
    
    def select_customer(self, customer_id: int):
        """Seleccionar cliente"""
        try:
            # Buscar cliente
            for customer in self._customers:
                if customer.get('id') == customer_id:
                    self._selected_customer = Customer.from_dict(customer)
                    
                    # Emitir señal
                    self.customer_selected.emit(customer)
                    
                    self.logger.debug(f"Cliente seleccionado: {customer.get('nombre', 'Sin nombre')}")
                    return
            
            # Si no se encuentra, deseleccionar
            self._selected_customer = None
            self.customer_selected.emit({})
            
        except Exception as e:
            self.logger.error(f"Error seleccionando cliente: {e}")
            self._set_error(f"Error seleccionando cliente: {str(e)}")
    
    def set_search_filter(self, search_text: str):
        """Establecer filtro de búsqueda"""
        self._filters['search_text'] = search_text.strip().lower()
        self._apply_filters()
        self.filters_changed.emit()
    
    def set_segment_filter(self, segment: str):
        """Establecer filtro de segmento"""
        self._filters['segment'] = segment
        self._apply_filters()
        self.filters_changed.emit()
    
    def set_status_filter(self, status: str):
        """Establecer filtro de estado"""
        self._filters['status'] = status
        self._apply_filters()
        self.filters_changed.emit()
    
    def set_active_only_filter(self, active_only: bool):
        """Establecer filtro solo activos"""
        self._filters['active_only'] = active_only
        self._apply_filters()
        self.filters_changed.emit()
    
    def clear_filters(self):
        """Limpiar todos los filtros"""
        self._filters = {
            'search_text': '',
            'segment': 'Todos',
            'status': 'Todos',
            'active_only': False
        }
        self._apply_filters()
        self.filters_changed.emit()
    
    # === MÉTODOS DE CONSULTA ===
    
    def get_customer_by_id(self, customer_id: int) -> Optional[Dict]:
        """Obtener cliente por ID"""
        for customer in self._customers:
            if customer.get('id') == customer_id:
                return customer.copy()
        return None
    
    def get_customer_by_code(self, customer_code: str) -> Optional[Dict]:
        """Obtener cliente por código"""
        for customer in self._customers:
            if customer.get('codigo', '').lower() == customer_code.lower():
                return customer.copy()
        return None
    
    def search_customers(self, search_term: str) -> List[Dict]:
        """Buscar clientes por término"""
        search_term = search_term.strip().lower()
        if not search_term:
            return self._customers.copy()
        
        results = []
        for customer in self._customers:
            # Buscar en nombre, código, email, teléfono
            if (search_term in customer.get('nombre', '').lower() or
                search_term in customer.get('codigo', '').lower() or
                search_term in customer.get('email', '').lower() or
                search_term in customer.get('telefono', '').lower()):
                
                results.append(customer)
        
        return results
    
    def get_customers_by_segment(self, segment: str) -> List[Dict]:
        """Obtener clientes por segmento"""
        if segment == 'Todos':
            return self._customers.copy()
        
        return [c for c in self._customers if c.get('segmento', '').upper() == segment.upper()]
    
    def get_customers_by_status(self, status: str) -> List[Dict]:
        """Obtener clientes por estado"""
        if status == 'Todos':
            return self._customers.copy()
        
        return [c for c in self._customers if c.get('estado', '').upper() == status.upper()]
    
    def get_customer_statistics(self, customer_id: int) -> Optional[Dict]:
        """Obtener estadísticas de un cliente"""
        customer = self.get_customer_by_id(customer_id)
        if not customer:
            return None
        
        return {
            'total_compras': customer.get('total_compras', 0.0),
            'numero_compras': customer.get('numero_compras', 0),
            'promedio_compra': customer.get('total_compras', 0) / max(customer.get('numero_compras', 1), 1),
            'ultima_compra': customer.get('ultima_compra'),
            'dias_desde_ultima_compra': self._calculate_days_since_last_purchase(customer.get('ultima_compra')),
            'limite_credito': customer.get('limite_credito', 0.0),
            'saldo_actual': customer.get('saldo_actual', 0.0),
            'credito_disponible': customer.get('limite_credito', 0) - customer.get('saldo_actual', 0)
        }
    
    def get_filtered_count(self) -> int:
        """Obtener cantidad de clientes filtrados"""
        return len(self._filtered_customers)
    
    def get_total_count(self) -> int:
        """Obtener cantidad total de clientes"""
        return len(self._customers)
    
    # === MÉTODOS DE EXPORTACIÓN ===
    
    def export_to_dict(self) -> Dict:
        """Exportar datos a diccionario"""
        return {
            'customers': self._customers,
            'filters': self._filters,
            'statistics': self._statistics,
            'selected_customer': self._selected_customer.to_dict() if self._selected_customer else None
        }
    
    def export_filtered_customers(self) -> List[Dict]:
        """Exportar clientes filtrados"""
        return self._filtered_customers.copy()
    
    # === MÉTODOS PROTEGIDOS ===
    
    def _validate_customer_data(self, customer_data: Dict) -> bool:
        """Validar datos del cliente"""
        self._validation_errors.clear()
        
        # Campos requeridos
        required_fields = ['nombre', 'codigo']
        for field in required_fields:
            if not customer_data.get(field, '').strip():
                self._add_validation_error(f"Campo {field} es requerido")
        
        # Validar email si se proporciona
        email = customer_data.get('email', '').strip()
        if email and not self._validate_email_format(email):
            self._add_validation_error("Formato de email inválido")
        
        # Validar teléfono si se proporciona
        telefono = customer_data.get('telefono', '').strip()
        if telefono and not self._validate_phone_format(telefono):
            self._add_validation_error("Formato de teléfono inválido")
        
        # Validar valores numéricos
        try:
            limite_credito = float(customer_data.get('limite_credito', 0))
            if limite_credito < 0:
                self._add_validation_error("Límite de crédito no puede ser negativo")
        except (ValueError, TypeError):
            self._add_validation_error("Límite de crédito debe ser un número válido")
        
        try:
            saldo_actual = float(customer_data.get('saldo_actual', 0))
            if saldo_actual < 0:
                self._add_validation_error("Saldo actual no puede ser negativo")
        except (ValueError, TypeError):
            self._add_validation_error("Saldo actual debe ser un número válido")
        
        # Validar unicidad de código (excluyendo el mismo cliente en caso de edición)
        customer_id = customer_data.get('id')
        codigo = customer_data.get('codigo', '').strip().upper()
        for customer in self._customers:
            if (customer.get('codigo', '').upper() == codigo and 
                customer.get('id') != customer_id):
                self._add_validation_error(f"Ya existe un cliente con el código {codigo}")
                break
        
        return len(self._validation_errors) == 0
    
    def _validate_email_format(self, email: str) -> bool:
        """Validar formato de email"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_phone_format(self, phone: str) -> bool:
        """Validar formato de teléfono"""
        import re
        # Permitir varios formatos de teléfono
        clean_phone = re.sub(r'[^\d\+]', '', phone)
        return len(clean_phone) >= 7 and len(clean_phone) <= 15
    
    def _apply_filters(self):
        """Aplicar filtros activos"""
        try:
            self._filtered_customers = self._customers.copy()
            
            # Filtro de búsqueda
            search_text = self._filters['search_text']
            if search_text:
                self._filtered_customers = [
                    c for c in self._filtered_customers
                    if (search_text in c.get('nombre', '').lower() or
                        search_text in c.get('codigo', '').lower() or
                        search_text in c.get('email', '').lower() or
                        search_text in c.get('telefono', '').lower())
                ]
            
            # Filtro de segmento
            segment = self._filters['segment']
            if segment != 'Todos':
                self._filtered_customers = [
                    c for c in self._filtered_customers
                    if c.get('segmento', '').upper() == segment.upper()
                ]
            
            # Filtro de estado
            status = self._filters['status']
            if status != 'Todos':
                self._filtered_customers = [
                    c for c in self._filtered_customers
                    if c.get('estado', '').upper() == status.upper()
                ]
            
            # Filtro solo activos
            if self._filters['active_only']:
                self._filtered_customers = [
                    c for c in self._filtered_customers
                    if c.get('activo', True)
                ]
            
            self.logger.debug(f"Filtros aplicados: {len(self._filtered_customers)} de {len(self._customers)} clientes")
            
        except Exception as e:
            self.logger.error(f"Error aplicando filtros: {e}")
            self._filtered_customers = self._customers.copy()
    
    def _update_statistics(self):
        """Actualizar estadísticas"""
        try:
            total_customers = len(self._customers)
            active_customers = len([c for c in self._customers if c.get('activo', True)])
            vip_customers = len([c for c in self._customers if c.get('segmento', '').upper() == 'VIP'])
            
            total_sales_amount = sum(
                self._safe_convert_to_float(c.get('total_compras', 0))
                for c in self._customers
            )
            
            self._statistics = {
                'total_customers': total_customers,
                'active_customers': active_customers,
                'vip_customers': vip_customers,
                'total_sales_amount': total_sales_amount,
                'average_purchases_per_customer': total_sales_amount / max(total_customers, 1)
            }
            
        except Exception as e:
            self.logger.error(f"Error actualizando estadísticas: {e}")
    
    def _calculate_days_since_last_purchase(self, last_purchase_date) -> int:
        """Calcular días desde última compra"""
        try:
            if not last_purchase_date:
                return 999  # Valor alto para "nunca"
            
            if isinstance(last_purchase_date, str):
                last_date = datetime.strptime(last_purchase_date, '%Y-%m-%d %H:%M:%S')
            elif isinstance(last_purchase_date, datetime):
                last_date = last_purchase_date
            else:
                return 999
            
            delta = datetime.now() - last_date
            return delta.days
            
        except Exception:
            return 999
    
    def _get_default_values(self) -> Dict:
        """Obtener valores por defecto del modelo"""
        return {
            'customers': [],
            'selected_customer': None,
            'filters': {
                'search_text': '',
                'segment': 'Todos',
                'status': 'Todos',
                'active_only': False
            }
        }
    
    def reset_to_defaults(self):
        """Resetear modelo a valores por defecto"""
        defaults = self._get_default_values()
        
        self._customers.clear()
        self._filtered_customers.clear()
        self._selected_customer = None
        self._filters = defaults['filters'].copy()
        
        self._update_statistics()
        
        # Emitir señales
        self.customer_selected.emit({})
        self.customers_loaded.emit([])
        self.filters_changed.emit()
        self.data_changed.emit()
        
        self.logger.debug("Modelo de clientes reseteado a defaults")