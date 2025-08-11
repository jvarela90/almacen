"""
Controlador de Reportes - AlmacénPro v2.0 MVC
Controlador que gestiona la interfaz de reportes usando Qt Designer
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from .base_controller import BaseController

logger = logging.getLogger(__name__)

class ReportsController(BaseController):
    """Controlador para generación de reportes"""
    
    def __init__(self, managers: Dict, current_user: Dict, parent=None):
        super().__init__(managers, current_user, parent)
        
        self.report_manager = managers.get('report')
        self.sales_manager = managers.get('sales')
        self.product_manager = managers.get('product')
        self.customer_manager = managers.get('customer')
        
        self.initialize()
    
    def get_ui_file_path(self) -> str:
        """Retornar ruta al archivo .ui correspondiente"""
        return os.path.join('views', 'widgets', 'reports_widget.ui')
    
    def setup_ui(self):
        """Configurar elementos específicos de la UI"""
        try:
            # Configurar fechas por defecto
            if hasattr(self, 'dateDesde'):
                # Primer día del mes actual
                first_day = datetime.now().replace(day=1)
                self.dateDesde.setDate(first_day.date())
                
            if hasattr(self, 'dateHasta'):
                # Fecha actual
                self.dateHasta.setDate(datetime.now().date())
            
            # Configurar combo de reportes
            if hasattr(self, 'cmbTipoReporte'):
                self.load_report_types()
                
        except Exception as e:
            self.logger.error(f"Error configurando UI de reportes: {e}")
    
    def connect_signals(self):
        """Conectar señales específicas del controlador"""
        try:
            # Conectar botones
            if hasattr(self, 'btnGenerar'):
                self.btnGenerar.clicked.connect(self.generate_report)
            
            if hasattr(self, 'btnExportar'):
                self.btnExportar.clicked.connect(self.export_report)
                
            if hasattr(self, 'btnImprimir'):
                self.btnImprimir.clicked.connect(self.print_report)
            
            # Conectar combo de reportes
            if hasattr(self, 'cmbTipoReporte'):
                self.cmbTipoReporte.currentTextChanged.connect(self.on_report_type_changed)
                
        except Exception as e:
            self.logger.error(f"Error conectando señales de reportes: {e}")
    
    def load_initial_data(self):
        """Cargar datos iniciales"""
        try:
            self.load_report_types()
            self.clear_report_view()
            self.logger.info("Datos iniciales cargados para reportes")
            
        except Exception as e:
            self.logger.error(f"Error cargando datos iniciales de reportes: {e}")
    
    def load_report_types(self):
        """Cargar tipos de reportes disponibles"""
        try:
            if not hasattr(self, 'cmbTipoReporte'):
                return
                
            report_types = [
                "Seleccionar reporte...",
                "Ventas por Período",
                "Productos Más Vendidos",
                "Clientes Top",
                "Movimientos de Inventario",
                "Resumen Financiero",
                "Análisis de Márgenes",
                "Reporte de Stock",
                "Ventas por Vendedor",
                "Análisis ABC de Productos"
            ]
            
            self.cmbTipoReporte.clear()
            self.cmbTipoReporte.addItems(report_types)
                
        except Exception as e:
            self.logger.error(f"Error cargando tipos de reporte: {e}")
    
    def on_report_type_changed(self, report_type: str):
        """Manejar cambio de tipo de reporte"""
        try:
            # Limpiar vista de reporte
            self.clear_report_view()
            
            # Actualizar descripción si existe
            descriptions = {
                "Ventas por Período": "Resumen de ventas en el período seleccionado",
                "Productos Más Vendidos": "Top 10 productos por cantidad vendida",
                "Clientes Top": "Clientes con mayor volumen de compras",
                "Movimientos de Inventario": "Histórico de movimientos de stock",
                "Resumen Financiero": "Indicadores financieros del período",
                "Análisis de Márgenes": "Análisis de rentabilidad por producto",
                "Reporte de Stock": "Estado actual del inventario",
                "Ventas por Vendedor": "Desempeño de ventas por usuario",
                "Análisis ABC de Productos": "Clasificación ABC de productos por valor"
            }
            
            if hasattr(self, 'lblDescripcion'):
                desc = descriptions.get(report_type, "Seleccione un tipo de reporte")
                self.lblDescripcion.setText(desc)
                
        except Exception as e:
            self.logger.error(f"Error cambiando tipo de reporte: {e}")
    
    def generate_report(self):
        """Generar reporte seleccionado"""
        try:
            if not hasattr(self, 'cmbTipoReporte'):
                return
                
            report_type = self.cmbTipoReporte.currentText()
            
            if report_type == "Seleccionar reporte...":
                self.show_warning("Reporte", "Por favor seleccione un tipo de reporte")
                return
            
            # Obtener fechas
            date_desde = self.dateDesde.date().toPyDate() if hasattr(self, 'dateDesde') else datetime.now().date()
            date_hasta = self.dateHasta.date().toPyDate() if hasattr(self, 'dateHasta') else datetime.now().date()
            
            # Mostrar indicador de carga
            if hasattr(self, 'lblEstado'):
                self.lblEstado.setText("Generando reporte...")
            
            # Generar según tipo
            report_data = None
            
            if report_type == "Ventas por Período":
                report_data = self.generate_sales_report(date_desde, date_hasta)
            elif report_type == "Productos Más Vendidos":
                report_data = self.generate_top_products_report(date_desde, date_hasta)
            elif report_type == "Clientes Top":
                report_data = self.generate_top_customers_report(date_desde, date_hasta)
            elif report_type == "Reporte de Stock":
                report_data = self.generate_stock_report()
            else:
                self.show_info("Info", f"Reporte '{report_type}' en desarrollo")
                return
            
            # Mostrar resultados
            if report_data:
                self.display_report_results(report_data, report_type)
                if hasattr(self, 'lblEstado'):
                    self.lblEstado.setText(f"Reporte generado exitosamente - {len(report_data)} registros")
            else:
                self.show_info("Info", "No se encontraron datos para el reporte")
                if hasattr(self, 'lblEstado'):
                    self.lblEstado.setText("Sin datos")
                
        except Exception as e:
            self.logger.error(f"Error generando reporte: {e}")
            self.show_error("Error", f"Error generando reporte: {str(e)}")
            if hasattr(self, 'lblEstado'):
                self.lblEstado.setText("Error en generación")
    
    def generate_sales_report(self, date_desde, date_hasta):
        """Generar reporte de ventas"""
        try:
            if not self.sales_manager:
                return []
            
            # Por simplicidad, generar datos básicos
            # En implementación real, usar métodos del sales_manager
            return [
                {
                    'fecha': date_desde.strftime('%Y-%m-%d'),
                    'ventas': 10,
                    'total': 15000.00,
                    'promedio': 1500.00
                },
                {
                    'fecha': date_hasta.strftime('%Y-%m-%d'),
                    'ventas': 8,
                    'total': 12000.00,
                    'promedio': 1500.00
                }
            ]
            
        except Exception as e:
            self.logger.error(f"Error generando reporte de ventas: {e}")
            return []
    
    def generate_top_products_report(self, date_desde, date_hasta):
        """Generar reporte de productos más vendidos"""
        try:
            # Datos de ejemplo
            return [
                {'producto': 'Producto A', 'cantidad': 100, 'total': 5000.00},
                {'producto': 'Producto B', 'cantidad': 80, 'total': 4000.00},
                {'producto': 'Producto C', 'cantidad': 60, 'total': 3000.00}
            ]
            
        except Exception as e:
            self.logger.error(f"Error generando reporte de productos: {e}")
            return []
    
    def generate_top_customers_report(self, date_desde, date_hasta):
        """Generar reporte de clientes top"""
        try:
            # Datos de ejemplo
            return [
                {'cliente': 'Cliente VIP', 'compras': 15, 'total': 25000.00},
                {'cliente': 'Cliente Premium', 'compras': 12, 'total': 18000.00},
                {'cliente': 'Cliente Regular', 'compras': 8, 'total': 12000.00}
            ]
            
        except Exception as e:
            self.logger.error(f"Error generando reporte de clientes: {e}")
            return []
    
    def generate_stock_report(self):
        """Generar reporte de stock"""
        try:
            if not self.product_manager:
                return []
                
            products = self.product_manager.get_all_products()
            
            stock_data = []
            for product in products:
                stock_data.append({
                    'producto': product.get('nombre', ''),
                    'categoria': product.get('categoria_nombre', ''),
                    'stock_actual': product.get('stock_actual', 0),
                    'stock_minimo': product.get('stock_minimo', 0),
                    'estado': 'Bajo' if product.get('stock_actual', 0) <= product.get('stock_minimo', 0) else 'Normal'
                })
            
            return stock_data
            
        except Exception as e:
            self.logger.error(f"Error generando reporte de stock: {e}")
            return []
    
    def display_report_results(self, data: List[Dict], report_type: str):
        """Mostrar resultados del reporte en la tabla"""
        try:
            if not hasattr(self, 'tblResultados') or not data:
                return
            
            # Configurar tabla según tipo de reporte
            if report_type == "Ventas por Período":
                headers = ['Fecha', 'N° Ventas', 'Total', 'Promedio']
                columns = ['fecha', 'ventas', 'total', 'promedio']
            elif report_type == "Productos Más Vendidos":
                headers = ['Producto', 'Cantidad', 'Total']
                columns = ['producto', 'cantidad', 'total']
            elif report_type == "Clientes Top":
                headers = ['Cliente', 'Compras', 'Total']
                columns = ['cliente', 'compras', 'total']
            elif report_type == "Reporte de Stock":
                headers = ['Producto', 'Categoría', 'Stock Actual', 'Stock Mínimo', 'Estado']
                columns = ['producto', 'categoria', 'stock_actual', 'stock_minimo', 'estado']
            else:
                headers = ['Descripción', 'Valor']
                columns = list(data[0].keys()) if data else []
            
            # Configurar y poblar tabla
            self.setup_table_widget(self.tblResultados, headers)
            self.populate_table(self.tblResultados, data, columns)
            
        except Exception as e:
            self.logger.error(f"Error mostrando resultados: {e}")
    
    def clear_report_view(self):
        """Limpiar vista de reporte"""
        try:
            if hasattr(self, 'tblResultados'):
                self.tblResultados.setRowCount(0)
                
            if hasattr(self, 'lblEstado'):
                self.lblEstado.setText("Listo")
                
        except Exception as e:
            self.logger.error(f"Error limpiando vista: {e}")
    
    def export_report(self):
        """Exportar reporte actual"""
        try:
            if not hasattr(self, 'tblResultados') or self.tblResultados.rowCount() == 0:
                self.show_warning("Exportar", "No hay datos para exportar")
                return
                
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar Reporte",
                f"reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV files (*.csv)"
            )
            
            if filename:
                table = self.tblResultados
                rows = table.rowCount()
                cols = table.columnCount()
                
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
                
                self.show_info("Éxito", f"Reporte exportado a: {filename}")
                
        except Exception as e:
            self.logger.error(f"Error exportando reporte: {e}")
            self.show_error("Error", f"Error exportando: {str(e)}")
    
    def print_report(self):
        """Imprimir reporte actual"""
        try:
            self.show_info("Info", "Función de impresión en desarrollo")
            
        except Exception as e:
            self.logger.error(f"Error imprimiendo reporte: {e}")
            self.show_error("Error", f"Error imprimiendo: {str(e)}")