"""
Sistema de Impresión de Tickets - AlmacénPro v2.0
Utilidades para generar e imprimir tickets de venta y comprobantes
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional
from decimal import Decimal

# Importar formatters
from .formatters import NumberFormatter, DateFormatter, TextFormatter

logger = logging.getLogger(__name__)

class TicketPrinter:
    """Generador de tickets de venta"""
    
    def __init__(self, company_name: str = "AlmacénPro", 
                 company_address: str = "", 
                 company_phone: str = "",
                 company_cuit: str = ""):
        self.company_name = company_name
        self.company_address = company_address
        self.company_phone = company_phone
        self.company_cuit = company_cuit
        
        # Configuración del ticket
        self.ticket_width = 42  # Caracteres de ancho del ticket
        self.line_separator = "=" * self.ticket_width
        self.dotted_line = "-" * self.ticket_width
    
    def generate_sale_ticket(self, sale_data: Dict) -> str:
        """Generar ticket de venta"""
        try:
            ticket_lines = []
            
            # Header de la empresa
            ticket_lines.extend(self._generate_header())
            ticket_lines.append("")
            
            # Información de la venta
            ticket_lines.extend(self._generate_sale_info(sale_data))
            ticket_lines.append("")
            
            # Detalle de productos
            ticket_lines.extend(self._generate_product_details(sale_data.get('items', [])))
            ticket_lines.append("")
            
            # Totales
            ticket_lines.extend(self._generate_totals(sale_data))
            ticket_lines.append("")
            
            # Información de pago
            if 'payments' in sale_data:
                ticket_lines.extend(self._generate_payment_info(sale_data['payments']))
                ticket_lines.append("")
            
            # Footer
            ticket_lines.extend(self._generate_footer())
            
            return "\n".join(ticket_lines)
            
        except Exception as e:
            logger.error(f"Error generando ticket: {e}")
            return f"Error generando ticket: {str(e)}"
    
    def _generate_header(self) -> List[str]:
        """Generar header del ticket"""
        lines = []
        
        # Nombre de la empresa centrado
        lines.append(self._center_text(self.company_name, bold=True))
        
        if self.company_address:
            lines.append(self._center_text(self.company_address))
        
        if self.company_phone:
            lines.append(self._center_text(f"Tel: {self.company_phone}"))
        
        if self.company_cuit:
            lines.append(self._center_text(f"CUIT: {TextFormatter.format_cuit(self.company_cuit)}"))
        
        lines.append(self.line_separator)
        
        return lines
    
    def _generate_sale_info(self, sale_data: Dict) -> List[str]:
        """Generar información de la venta"""
        lines = []
        
        # Fecha y hora
        fecha_venta = sale_data.get('fecha_venta', datetime.now())
        lines.append(f"Fecha: {DateFormatter.format_datetime(fecha_venta)}")
        
        # Número de ticket/factura
        numero = sale_data.get('numero_factura') or sale_data.get('id', '')
        if numero:
            lines.append(f"Ticket N°: {numero}")
        
        # Cliente
        cliente = sale_data.get('cliente_nombre', 'Consumidor Final')
        lines.append(f"Cliente: {cliente}")
        
        # Vendedor
        vendedor = sale_data.get('vendedor_nombre', '')
        if vendedor:
            lines.append(f"Vendedor: {vendedor}")
        
        lines.append(self.dotted_line)
        
        return lines
    
    def _generate_product_details(self, items: List[Dict]) -> List[str]:
        """Generar detalle de productos"""
        lines = []
        
        if not items:
            lines.append("No hay items en la venta")
            return lines
        
        # Header de productos
        lines.append("DETALLE DE PRODUCTOS")
        lines.append(self.dotted_line)
        
        for item in items:
            producto = item.get('producto_nombre', 'Producto')
            cantidad = float(item.get('cantidad', 0))
            precio_unit = float(item.get('precio_unitario', 0))
            subtotal = float(item.get('subtotal', cantidad * precio_unit))
            
            # Línea del producto (puede ocupar múltiples líneas)
            producto_line = TextFormatter.truncate(producto, self.ticket_width - 2)
            lines.append(producto_line)
            
            # Línea de cantidad, precio y subtotal
            qty_text = f"{cantidad:,.2f}".rstrip('0').rstrip('.')
            if '.' not in f"{cantidad:,.2f}":
                qty_text = f"{cantidad:,.0f}"
            
            precio_text = f"${precio_unit:,.2f}"
            subtotal_text = f"${subtotal:,.2f}"
            
            detail_line = f"{qty_text} x {precio_text}"
            spaces_needed = self.ticket_width - len(detail_line) - len(subtotal_text)
            detail_line += " " * max(1, spaces_needed) + subtotal_text
            
            lines.append(detail_line)
            lines.append("")  # Línea en blanco entre productos
        
        return lines
    
    def _generate_totals(self, sale_data: Dict) -> List[str]:
        """Generar sección de totales"""
        lines = []
        lines.append(self.dotted_line)
        
        # Subtotal
        subtotal = float(sale_data.get('subtotal', 0))
        if subtotal > 0:
            lines.append(self._format_total_line("SUBTOTAL:", subtotal))
        
        # Descuentos
        descuento = float(sale_data.get('descuento', 0))
        if descuento > 0:
            lines.append(self._format_total_line("DESCUENTO:", -descuento))
        
        # Impuestos
        impuestos = float(sale_data.get('impuestos', 0))
        if impuestos > 0:
            lines.append(self._format_total_line("IMPUESTOS:", impuestos))
        
        lines.append(self.dotted_line)
        
        # Total final
        total = float(sale_data.get('total', subtotal + impuestos - descuento))
        lines.append(self._format_total_line("TOTAL:", total, bold=True))
        
        lines.append(self.line_separator)
        
        return lines
    
    def _generate_payment_info(self, payments: List[Dict]) -> List[str]:
        """Generar información de pagos"""
        lines = []
        lines.append("FORMA DE PAGO")
        lines.append(self.dotted_line)
        
        for payment in payments:
            metodo = payment.get('metodo_pago', '').replace('_', ' ').title()
            importe = float(payment.get('importe', 0))
            
            # Mapear códigos de método a nombres legibles
            method_names = {
                'EFECTIVO': 'Efectivo',
                'TARJETA DEBITO': 'Tarjeta Débito', 
                'TARJETA CREDITO': 'Tarjeta Crédito',
                'TRANSFERENCIA': 'Transferencia',
                'CHEQUE': 'Cheque',
                'CUENTA CORRIENTE': 'Cuenta Corriente',
                'MERCADO PAGO': 'Mercado Pago',
                'BILLETERA VIRTUAL': 'Billetera Virtual'
            }
            
            metodo_display = method_names.get(metodo.upper(), metodo)
            lines.append(self._format_total_line(f"{metodo_display}:", importe))
            
            # Referencia si existe
            referencia = payment.get('referencia', '')
            if referencia:
                ref_line = f"  Ref: {TextFormatter.truncate(referencia, self.ticket_width - 8)}"
                lines.append(ref_line)
        
        return lines
    
    def _generate_footer(self) -> List[str]:
        """Generar footer del ticket"""
        lines = []
        lines.append(self.line_separator)
        lines.append(self._center_text("¡GRACIAS POR SU COMPRA!"))
        lines.append(self._center_text("Conserve este comprobante"))
        lines.append("")
        lines.append(self._center_text(f"Impreso: {DateFormatter.format_datetime(datetime.now())}"))
        lines.append(self._center_text("Sistema AlmacénPro v2.0"))
        
        return lines
    
    def _center_text(self, text: str, bold: bool = False) -> str:
        """Centrar texto en el ancho del ticket"""
        if bold:
            # Simular negrita duplicando caracteres importantes
            text = f"** {text} **"
        
        padding = (self.ticket_width - len(text)) // 2
        return " " * max(0, padding) + text
    
    def _format_total_line(self, label: str, amount: float, bold: bool = False) -> str:
        """Formatear línea de total"""
        amount_text = NumberFormatter.format_currency(amount)
        
        if bold:
            label = f"** {label}"
            amount_text = f"{amount_text} **"
        
        spaces_needed = self.ticket_width - len(label) - len(amount_text)
        return label + " " * max(1, spaces_needed) + amount_text
    
    def print_ticket(self, ticket_content: str, printer_name: Optional[str] = None) -> bool:
        """Imprimir ticket en impresora"""
        try:
            # Para sistemas Windows
            if os.name == 'nt':
                return self._print_windows(ticket_content, printer_name)
            else:
                return self._print_unix(ticket_content, printer_name)
                
        except Exception as e:
            logger.error(f"Error imprimiendo ticket: {e}")
            return False
    
    def _print_windows(self, content: str, printer_name: Optional[str] = None) -> bool:
        """Imprimir en Windows"""
        try:
            import tempfile
            import subprocess
            
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(content)
                temp_file = f.name
            
            # Comando para imprimir
            if printer_name:
                cmd = f'type "{temp_file}" | print /D:"{printer_name}"'
            else:
                cmd = f'type "{temp_file}" | print'
            
            # Ejecutar comando
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            # Limpiar archivo temporal
            os.unlink(temp_file)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error imprimiendo en Windows: {e}")
            return False
    
    def _print_unix(self, content: str, printer_name: Optional[str] = None) -> bool:
        """Imprimir en sistemas Unix/Linux"""
        try:
            import subprocess
            
            if printer_name:
                cmd = ['lp', '-d', printer_name]
            else:
                cmd = ['lp']
            
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, text=True)
            process.communicate(input=content)
            
            return process.returncode == 0
            
        except Exception as e:
            logger.error(f"Error imprimiendo en Unix: {e}")
            return False
    
    def save_ticket_to_file(self, ticket_content: str, filename: Optional[str] = None) -> str:
        """Guardar ticket en archivo"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"ticket_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(ticket_content)
            
            logger.info(f"Ticket guardado en: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error guardando ticket: {e}")
            return ""
    
    def preview_ticket(self, sale_data: Dict) -> str:
        """Generar preview del ticket para mostrar en pantalla"""
        return self.generate_sale_ticket(sale_data)


class ReceiptPrinter(TicketPrinter):
    """Impresora especializada para recibos y comprobantes"""
    
    def generate_payment_receipt(self, payment_data: Dict) -> str:
        """Generar recibo de pago"""
        try:
            lines = []
            
            # Header
            lines.extend(self._generate_header())
            lines.append("")
            lines.append(self._center_text("RECIBO DE PAGO"))
            lines.append(self.line_separator)
            
            # Información del pago
            fecha = payment_data.get('fecha_pago', datetime.now())
            lines.append(f"Fecha: {DateFormatter.format_datetime(fecha)}")
            
            recibo_num = payment_data.get('numero_recibo', '')
            if recibo_num:
                lines.append(f"Recibo N°: {recibo_num}")
            
            cliente = payment_data.get('cliente_nombre', '')
            if cliente:
                lines.append(f"Cliente: {cliente}")
            
            lines.append(self.dotted_line)
            
            # Detalle del pago
            concepto = payment_data.get('concepto', 'Pago a cuenta')
            lines.append(f"Concepto: {concepto}")
            
            metodo = payment_data.get('metodo_pago', '').replace('_', ' ').title()
            lines.append(f"Método: {metodo}")
            
            importe = float(payment_data.get('importe', 0))
            lines.append(self._format_total_line("IMPORTE:", importe, bold=True))
            
            # Referencia
            referencia = payment_data.get('referencia', '')
            if referencia:
                lines.append("")
                lines.append(f"Referencia: {referencia}")
            
            lines.append("")
            lines.extend(self._generate_footer())
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Error generando recibo: {e}")
            return f"Error generando recibo: {str(e)}"


# Funciones de conveniencia
def print_sale_ticket(sale_data: Dict, company_info: Optional[Dict] = None, 
                     printer_name: Optional[str] = None) -> bool:
    """Función de conveniencia para imprimir ticket de venta"""
    printer = TicketPrinter(**(company_info or {}))
    ticket_content = printer.generate_sale_ticket(sale_data)
    return printer.print_ticket(ticket_content, printer_name)

def save_sale_ticket(sale_data: Dict, filename: Optional[str] = None,
                    company_info: Optional[Dict] = None) -> str:
    """Función de conveniencia para guardar ticket de venta"""
    printer = TicketPrinter(**(company_info or {}))
    ticket_content = printer.generate_sale_ticket(sale_data)
    return printer.save_ticket_to_file(ticket_content, filename)

def preview_sale_ticket(sale_data: Dict, company_info: Optional[Dict] = None) -> str:
    """Función de conveniencia para preview de ticket"""
    printer = TicketPrinter(**(company_info or {}))
    return printer.preview_ticket(sale_data)