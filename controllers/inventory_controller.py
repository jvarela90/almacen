"""
Controlador de Inventario - AlmacénPro v2.0 MVC
Controlador que gestiona la interfaz de inventario usando Qt Designer
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from .base_controller import BaseController

logger = logging.getLogger(__name__)

class InventoryController(BaseController):
    """Controlador para gestión de inventario"""
    
    def __init__(self, managers: Dict, current_user: Dict, parent=None):
        super().__init__(managers, current_user, parent)
        
        self.product_manager = managers.get('product')
        self.inventory_manager = managers.get('inventory')
        
        self.initialize()
    
    def get_ui_file_path(self) -> str:
        """Retornar ruta al archivo .ui correspondiente"""
        return os.path.join('views', 'widgets', 'inventory_widget.ui')
    
    def setup_ui(self):
        """Configurar elementos específicos de la UI"""
        try:
            # Configurar tabla de productos
            if hasattr(self, 'tblProductos'):
                headers = ['ID', 'Código', 'Nombre', 'Categoría', 'Stock Actual', 'Stock Mínimo', 'Estado']
                column_widths = [60, 100, -1, 120, 80, 80, 80]  # -1 = stretch
                self.setup_table_widget(self.tblProductos, headers, column_widths)
            
            # Configurar filtros si existen
            if hasattr(self, 'cmbCategoria'):
                self.load_categories()
                
        except Exception as e:
            self.logger.error(f"Error configurando UI de inventario: {e}")
    
    def connect_signals(self):
        """Conectar señales específicas del controlador"""
        try:
            # Conectar botones
            if hasattr(self, 'btnActualizar'):
                self.btnActualizar.clicked.connect(self.load_initial_data)
            
            if hasattr(self, 'btnAjustarStock'):
                self.btnAjustarStock.clicked.connect(self.adjust_stock)
                
            if hasattr(self, 'btnExportar'):
                self.btnExportar.clicked.connect(self.export_inventory)
            
            # Conectar filtros
            if hasattr(self, 'cmbCategoria'):
                self.cmbCategoria.currentTextChanged.connect(self.filter_products)
                
            if hasattr(self, 'cmbEstado'):
                self.cmbEstado.currentTextChanged.connect(self.filter_products)
            
            # Conectar tabla
            if hasattr(self, 'tblProductos'):
                self.tblProductos.cellDoubleClicked.connect(self.edit_product_stock)
                
        except Exception as e:
            self.logger.error(f"Error conectando señales de inventario: {e}")
    
    def load_initial_data(self):
        """Cargar datos iniciales"""
        try:
            self.load_products()
            self.load_categories()
            self.update_summary()
            self.logger.info("Datos iniciales cargados para inventario")
            
        except Exception as e:
            self.logger.error(f"Error cargando datos iniciales de inventario: {e}")
    
    def load_products(self):
        """Cargar productos en la tabla"""
        try:
            if not self.product_manager or not hasattr(self, 'tblProductos'):
                return
            
            products = self.product_manager.get_all_products()
            
            data = []
            for product in products:
                # Determinar estado del stock
                stock_actual = product.get('stock_actual', 0)
                stock_minimo = product.get('stock_minimo', 0)
                
                if stock_actual <= 0:
                    estado = "Sin Stock"
                elif stock_actual <= stock_minimo:
                    estado = "Stock Bajo"
                else:
                    estado = "Normal"
                
                data.append({
                    'id': product.get('id'),
                    'codigo_interno': product.get('codigo_interno', ''),
                    'nombre': product.get('nombre', ''),
                    'categoria_nombre': product.get('categoria_nombre', 'Sin Categoría'),
                    'stock_actual': stock_actual,
                    'stock_minimo': stock_minimo,
                    'estado': estado
                })
            
            columns = ['id', 'codigo_interno', 'nombre', 'categoria_nombre', 'stock_actual', 'stock_minimo', 'estado']
            self.populate_table(self.tblProductos, data, columns)
            
            # Aplicar colores por estado
            self.apply_stock_colors()
            
        except Exception as e:
            self.logger.error(f"Error cargando productos: {e}")
    
    def load_categories(self):
        """Cargar categorías en combo"""
        try:
            if not self.product_manager or not hasattr(self, 'cmbCategoria'):
                return
                
            categories = self.product_manager.get_all_categories()
            
            self.cmbCategoria.clear()
            self.cmbCategoria.addItem("Todas las Categorías", None)
            
            for category in categories:
                self.cmbCategoria.addItem(category.get('nombre', ''), category.get('id'))
                
        except Exception as e:
            self.logger.error(f"Error cargando categorías: {e}")
    
    def apply_stock_colors(self):
        """Aplicar colores según estado del stock"""
        try:
            if not hasattr(self, 'tblProductos'):
                return
                
            for row in range(self.tblProductos.rowCount()):
                estado_item = self.tblProductos.item(row, 6)  # Columna Estado
                if not estado_item:
                    continue
                    
                estado = estado_item.text()
                
                if estado == "Sin Stock":
                    color = QColor(220, 53, 69)  # Rojo
                elif estado == "Stock Bajo":
                    color = QColor(255, 193, 7)  # Amarillo
                else:
                    color = QColor(40, 167, 69)  # Verde
                
                # Aplicar color a toda la fila
                for col in range(self.tblProductos.columnCount()):
                    item = self.tblProductos.item(row, col)
                    if item:
                        item.setBackground(color.lighter(180))
                        
        except Exception as e:
            self.logger.error(f"Error aplicando colores: {e}")
    
    def filter_products(self):
        """Filtrar productos según criterios seleccionados"""
        try:
            # Por ahora solo recargar - se puede implementar filtrado más sofisticado
            self.load_products()
            
        except Exception as e:
            self.logger.error(f"Error filtrando productos: {e}")
    
    def update_summary(self):
        """Actualizar resumen de inventario"""
        try:
            if not self.product_manager:
                return
                
            stats = self.inventory_manager.get_inventory_summary() if self.inventory_manager else {}
            
            # Actualizar labels si existen
            if hasattr(self, 'lblTotalProductos'):
                self.lblTotalProductos.setText(str(stats.get('total_productos', 0)))
                
            if hasattr(self, 'lblSinStock'):
                self.lblSinStock.setText(str(stats.get('productos_sin_stock', 0)))
                
            if hasattr(self, 'lblStockBajo'):
                self.lblStockBajo.setText(str(stats.get('productos_stock_bajo', 0)))
                
            if hasattr(self, 'lblValorInventario'):
                valor = stats.get('valor_total_inventario', 0)
                self.lblValorInventario.setText(self.format_currency(valor))
                
        except Exception as e:
            self.logger.error(f"Error actualizando resumen: {e}")
    
    def adjust_stock(self):
        """Ajustar stock de producto seleccionado"""
        try:
            selected_data = self.get_selected_table_data(self.tblProductos) if hasattr(self, 'tblProductos') else None
            if not selected_data:
                self.show_warning("Selección", "Seleccione un producto para ajustar stock")
                return
            
            product_id = selected_data.get('id')
            product_name = selected_data.get('nombre')
            current_stock = float(selected_data.get('stock_actual', 0))
            
            # Diálogo simple para ajuste de stock
            new_stock, ok = QInputDialog.getDouble(
                self, 
                "Ajustar Stock",
                f"Producto: {product_name}\nStock actual: {current_stock}\n\nNuevo stock:",
                current_stock, 0, 999999, 2
            )
            
            if ok and new_stock != current_stock:
                # Actualizar stock
                if self.inventory_manager:
                    success = self.inventory_manager.adjust_stock(
                        product_id, 
                        new_stock, 
                        "AJUSTE_MANUAL",
                        f"Ajuste manual por {self.current_user.get('username')}"
                    )
                    
                    if success:
                        self.show_info("Éxito", "Stock actualizado correctamente")
                        self.load_products()  # Recargar datos
                    else:
                        self.show_error("Error", "No se pudo actualizar el stock")
                        
        except Exception as e:
            self.logger.error(f"Error ajustando stock: {e}")
            self.show_error("Error", f"Error ajustando stock: {str(e)}")
    
    def edit_product_stock(self, row: int, column: int):
        """Editar stock desde doble click en tabla"""
        self.adjust_stock()
    
    def export_inventory(self):
        """Exportar inventario a CSV"""
        try:
            if not hasattr(self, 'tblProductos'):
                return
                
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar Inventario",
                f"inventario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV files (*.csv)"
            )
            
            if filename:
                # Obtener datos de la tabla
                table = self.tblProductos
                rows = table.rowCount()
                cols = table.columnCount()
                
                # Crear CSV
                with open(filename, 'w', encoding='utf-8', newline='') as f:
                    import csv
                    writer = csv.writer(f)
                    
                    # Headers
                    headers = []
                    for col in range(cols):
                        header_item = table.horizontalHeaderItem(col)
                        headers.append(header_item.text() if header_item else f"Col{col}")
                    writer.writerow(headers)
                    
                    # Data
                    for row in range(rows):
                        row_data = []
                        for col in range(cols):
                            item = table.item(row, col)
                            row_data.append(item.text() if item else "")
                        writer.writerow(row_data)
                
                self.show_info("Éxito", f"Inventario exportado a: {filename}")
                
        except Exception as e:
            self.logger.error(f"Error exportando inventario: {e}")
            self.show_error("Error", f"Error exportando: {str(e)}")