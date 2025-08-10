"""
Portal de Clientes Web - AlmacénPro v2.0
Aplicación web Flask para portal de clientes
"""

from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import check_password_hash
import logging
from datetime import datetime, timedelta
import json
import os
import sys

# Agregar path del proyecto principal
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from database.manager import DatabaseManager
from managers.customer_manager import CustomerManager
from managers.sales_manager import SalesManager
from utils.formatters import NumberFormatter, DateFormatter

logger = logging.getLogger(__name__)

class CustomerPortalUser(UserMixin):
    """Clase de usuario para Flask-Login"""
    
    def __init__(self, customer_id, email, nombre):
        self.id = customer_id
        self.email = email
        self.nombre = nombre
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
    
    def get_id(self):
        return str(self.id)

def create_customer_portal_app():
    """Factory function para crear la aplicación del portal"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'customer_portal_secret_key_change_in_production'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Configurar Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Por favor inicie sesión para acceder al portal.'
    login_manager.login_message_category = 'info'
    
    # Inicializar managers
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'almacen_pro.db')
        db_manager = DatabaseManager(db_path)
        customer_manager = CustomerManager(db_manager)
        sales_manager = SalesManager(db_manager, None)  # product_manager puede ser None para consultas
        
        app.db_manager = db_manager
        app.customer_manager = customer_manager
        app.sales_manager = sales_manager
        
    except Exception as e:
        logger.error(f"Error inicializando managers: {e}")
        app.db_manager = None
        app.customer_manager = None
        app.sales_manager = None
    
    @login_manager.user_loader
    def load_user(customer_id):
        """Cargar usuario para Flask-Login"""
        try:
            if not app.customer_manager:
                return None
                
            customer = app.customer_manager.get_customer_by_id(int(customer_id))
            if customer and customer.get('activo'):
                return CustomerPortalUser(customer['id'], customer['email'], customer['nombre'])
            return None
        except:
            return None
    
    # ==================== RUTAS ====================
    
    @app.route('/')
    def index():
        """Página principal del portal"""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('index.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Login de clientes"""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            remember_me = request.form.get('remember_me') == 'on'
            
            if not email or not password:
                flash('Email y contraseña son requeridos', 'error')
                return render_template('login.html')
            
            try:
                # Buscar cliente por email
                customer = app.customer_manager.get_customer_by_email(email)
                
                if customer and customer.get('activo') and customer.get('portal_password'):
                    # Verificar contraseña (en implementación real usar hash)
                    if check_password_hash(customer['portal_password'], password):
                        # Crear usuario y hacer login
                        user = CustomerPortalUser(customer['id'], customer['email'], customer['nombre'])
                        login_user(user, remember=remember_me)
                        
                        # Registrar acceso
                        app.customer_manager.log_portal_access(customer['id'], 'LOGIN', request.remote_addr)
                        
                        flash(f'Bienvenido, {customer["nombre"]}!', 'success')
                        
                        # Redirigir a página solicitada o dashboard
                        next_page = request.args.get('next')
                        return redirect(next_page) if next_page else redirect(url_for('dashboard'))
                    else:
                        flash('Credenciales inválidas', 'error')
                else:
                    flash('Credenciales inválidas', 'error')
                    
            except Exception as e:
                logger.error(f"Error en login: {e}")
                flash('Error interno del sistema', 'error')
        
        return render_template('login.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        """Logout de clientes"""
        try:
            # Registrar logout
            app.customer_manager.log_portal_access(current_user.id, 'LOGOUT', request.remote_addr)
        except:
            pass
        
        logout_user()
        flash('Sesión cerrada exitosamente', 'info')
        return redirect(url_for('index'))
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """Registro de nuevos clientes al portal"""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            nombre = request.form.get('nombre')
            telefono = request.form.get('telefono')
            
            # Validaciones
            if not all([email, password, confirm_password, nombre]):
                flash('Todos los campos son requeridos', 'error')
                return render_template('register.html')
            
            if password != confirm_password:
                flash('Las contraseñas no coinciden', 'error')
                return render_template('register.html')
            
            if len(password) < 6:
                flash('La contraseña debe tener al menos 6 caracteres', 'error')
                return render_template('register.html')
            
            try:
                # Verificar si el email ya existe
                existing = app.customer_manager.get_customer_by_email(email)
                if existing:
                    flash('El email ya está registrado', 'error')
                    return render_template('register.html')
                
                # Crear cliente
                customer_data = {
                    'nombre': nombre,
                    'email': email,
                    'telefono': telefono or '',
                    'activo': True,
                    'portal_enabled': True,
                    'portal_password': password  # En implementación real usar hash
                }
                
                customer_id = app.customer_manager.create_customer(customer_data)
                
                if customer_id:
                    flash('Registro exitoso. Ya puede iniciar sesión.', 'success')
                    return redirect(url_for('login'))
                else:
                    flash('Error en el registro', 'error')
                    
            except Exception as e:
                logger.error(f"Error en registro: {e}")
                flash('Error interno del sistema', 'error')
        
        return render_template('register.html')
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Dashboard principal del cliente"""
        try:
            # Obtener estadísticas del cliente
            stats = get_customer_stats(current_user.id)
            
            # Últimas compras
            recent_purchases = app.sales_manager.get_customer_sales(current_user.id, limit=5)
            
            # Estado de cuenta
            account_balance = app.customer_manager.get_customer_balance(current_user.id)
            
            return render_template('dashboard.html', 
                                 stats=stats,
                                 recent_purchases=recent_purchases,
                                 account_balance=account_balance)
                                 
        except Exception as e:
            logger.error(f"Error cargando dashboard: {e}")
            flash('Error cargando información', 'error')
            return render_template('dashboard.html', stats={}, recent_purchases=[], account_balance=0)
    
    @app.route('/purchases')
    @login_required
    def purchases():
        """Historial de compras"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = 20
            
            # Filtros
            date_from = request.args.get('date_from')
            date_to = request.args.get('date_to')
            
            # Obtener compras del cliente
            purchases = app.sales_manager.get_customer_sales(
                current_user.id,
                date_from=date_from,
                date_to=date_to,
                page=page,
                per_page=per_page
            )
            
            return render_template('purchases.html', 
                                 purchases=purchases,
                                 page=page,
                                 date_from=date_from,
                                 date_to=date_to)
                                 
        except Exception as e:
            logger.error(f"Error cargando compras: {e}")
            flash('Error cargando historial de compras', 'error')
            return render_template('purchases.html', purchases=[])
    
    @app.route('/purchase/<int:purchase_id>')
    @login_required
    def purchase_detail(purchase_id):
        """Detalle de una compra específica"""
        try:
            # Verificar que la compra pertenece al cliente
            purchase = app.sales_manager.get_sale_by_id(purchase_id)
            
            if not purchase or purchase.get('customer_id') != current_user.id:
                flash('Compra no encontrada', 'error')
                return redirect(url_for('purchases'))
            
            # Obtener items de la compra
            purchase_items = app.sales_manager.get_sale_items(purchase_id)
            
            return render_template('purchase_detail.html',
                                 purchase=purchase,
                                 purchase_items=purchase_items)
                                 
        except Exception as e:
            logger.error(f"Error cargando detalle de compra: {e}")
            flash('Error cargando detalle', 'error')
            return redirect(url_for('purchases'))
    
    @app.route('/account')
    @login_required
    def account():
        """Estado de cuenta corriente"""
        try:
            # Movimientos de cuenta corriente
            movements = app.customer_manager.get_account_movements(current_user.id)
            
            # Balance actual
            balance = app.customer_manager.get_customer_balance(current_user.id)
            
            return render_template('account.html',
                                 movements=movements,
                                 balance=balance)
                                 
        except Exception as e:
            logger.error(f"Error cargando cuenta corriente: {e}")
            flash('Error cargando estado de cuenta', 'error')
            return render_template('account.html', movements=[], balance=0)
    
    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        """Perfil del cliente"""
        if request.method == 'POST':
            try:
                # Obtener datos del formulario
                nombre = request.form.get('nombre')
                telefono = request.form.get('telefono')
                direccion = request.form.get('direccion')
                
                # Actualizar datos
                update_data = {
                    'nombre': nombre,
                    'telefono': telefono,
                    'direccion': direccion
                }
                
                success = app.customer_manager.update_customer(current_user.id, update_data)
                
                if success:
                    flash('Perfil actualizado exitosamente', 'success')
                else:
                    flash('Error actualizando perfil', 'error')
                    
            except Exception as e:
                logger.error(f"Error actualizando perfil: {e}")
                flash('Error interno del sistema', 'error')
        
        try:
            # Cargar datos actuales
            customer = app.customer_manager.get_customer_by_id(current_user.id)
            return render_template('profile.html', customer=customer)
            
        except Exception as e:
            logger.error(f"Error cargando perfil: {e}")
            flash('Error cargando perfil', 'error')
            return render_template('profile.html', customer={})
    
    @app.route('/change_password', methods=['GET', 'POST'])
    @login_required
    def change_password():
        """Cambio de contraseña"""
        if request.method == 'POST':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if not all([current_password, new_password, confirm_password]):
                flash('Todos los campos son requeridos', 'error')
                return render_template('change_password.html')
            
            if new_password != confirm_password:
                flash('Las contraseñas nuevas no coinciden', 'error')
                return render_template('change_password.html')
            
            if len(new_password) < 6:
                flash('La contraseña debe tener al menos 6 caracteres', 'error')
                return render_template('change_password.html')
            
            try:
                # Verificar contraseña actual
                customer = app.customer_manager.get_customer_by_id(current_user.id)
                
                if not check_password_hash(customer['portal_password'], current_password):
                    flash('Contraseña actual incorrecta', 'error')
                    return render_template('change_password.html')
                
                # Actualizar contraseña
                success = app.customer_manager.update_customer_password(current_user.id, new_password)
                
                if success:
                    flash('Contraseña actualizada exitosamente', 'success')
                    return redirect(url_for('profile'))
                else:
                    flash('Error actualizando contraseña', 'error')
                    
            except Exception as e:
                logger.error(f"Error cambiando contraseña: {e}")
                flash('Error interno del sistema', 'error')
        
        return render_template('change_password.html')
    
    @app.route('/support', methods=['GET', 'POST'])
    @login_required
    def support():
        """Sistema de tickets de soporte"""
        if request.method == 'POST':
            subject = request.form.get('subject')
            message = request.form.get('message')
            priority = request.form.get('priority', 'medium')
            
            if not all([subject, message]):
                flash('Asunto y mensaje son requeridos', 'error')
                return render_template('support.html')
            
            try:
                # Crear ticket
                ticket_data = {
                    'customer_id': current_user.id,
                    'subject': subject,
                    'message': message,
                    'priority': priority,
                    'status': 'open',
                    'channel': 'portal'
                }
                
                ticket_id = app.customer_manager.create_support_ticket(ticket_data)
                
                if ticket_id:
                    flash('Ticket creado exitosamente', 'success')
                    return redirect(url_for('support_tickets'))
                else:
                    flash('Error creando ticket', 'error')
                    
            except Exception as e:
                logger.error(f"Error creando ticket: {e}")
                flash('Error interno del sistema', 'error')
        
        return render_template('support.html')
    
    @app.route('/support/tickets')
    @login_required
    def support_tickets():
        """Lista de tickets del cliente"""
        try:
            tickets = app.customer_manager.get_customer_tickets(current_user.id)
            return render_template('support_tickets.html', tickets=tickets)
            
        except Exception as e:
            logger.error(f"Error cargando tickets: {e}")
            flash('Error cargando tickets', 'error')
            return render_template('support_tickets.html', tickets=[])
    
    @app.route('/support/ticket/<int:ticket_id>')
    @login_required
    def support_ticket_detail(ticket_id):
        """Detalle de ticket específico"""
        try:
            ticket = app.customer_manager.get_ticket_by_id(ticket_id)
            
            if not ticket or ticket.get('customer_id') != current_user.id:
                flash('Ticket no encontrado', 'error')
                return redirect(url_for('support_tickets'))
            
            # Obtener mensajes del ticket
            messages = app.customer_manager.get_ticket_messages(ticket_id)
            
            return render_template('support_ticket_detail.html',
                                 ticket=ticket,
                                 messages=messages)
                                 
        except Exception as e:
            logger.error(f"Error cargando ticket: {e}")
            flash('Error cargando ticket', 'error')
            return redirect(url_for('support_tickets'))
    
    @app.route('/download/invoice/<int:purchase_id>')
    @login_required
    def download_invoice(purchase_id):
        """Descargar comprobante de compra"""
        try:
            # Verificar que la compra pertenece al cliente
            purchase = app.sales_manager.get_sale_by_id(purchase_id)
            
            if not purchase or purchase.get('customer_id') != current_user.id:
                flash('Comprobante no encontrado', 'error')
                return redirect(url_for('purchases'))
            
            # Generar PDF del comprobante
            # En implementación real, generar PDF y enviarlo
            flash('Funcionalidad de descarga disponible próximamente', 'info')
            return redirect(url_for('purchase_detail', purchase_id=purchase_id))
            
        except Exception as e:
            logger.error(f"Error descargando comprobante: {e}")
            flash('Error descargando comprobante', 'error')
            return redirect(url_for('purchases'))
    
    # ==================== API ENDPOINTS ====================
    
    @app.route('/api/stats')
    @login_required
    def api_stats():
        """API: Estadísticas del cliente"""
        try:
            stats = get_customer_stats(current_user.id)
            return jsonify(stats)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/purchases')
    @login_required
    def api_purchases():
        """API: Lista de compras"""
        try:
            limit = request.args.get('limit', 10, type=int)
            purchases = app.sales_manager.get_customer_sales(current_user.id, limit=limit)
            
            # Formatear para JSON
            formatted_purchases = []
            for purchase in purchases:
                formatted_purchases.append({
                    'id': purchase['id'],
                    'fecha': DateFormatter.format_date(purchase['fecha_venta']),
                    'total': NumberFormatter.format_currency(purchase['total']),
                    'estado': purchase['estado']
                })
            
            return jsonify({'purchases': formatted_purchases})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # ==================== FUNCIONES AUXILIARES ====================
    
    def get_customer_stats(customer_id):
        """Obtener estadísticas del cliente"""
        try:
            stats = {}
            
            # Total de compras
            total_purchases = app.sales_manager.get_customer_purchase_count(customer_id)
            stats['total_purchases'] = total_purchases
            
            # Total gastado
            total_spent = app.sales_manager.get_customer_total_spent(customer_id)
            stats['total_spent'] = NumberFormatter.format_currency(total_spent)
            
            # Última compra
            last_purchase = app.sales_manager.get_customer_last_purchase(customer_id)
            if last_purchase:
                stats['last_purchase_date'] = DateFormatter.format_date(last_purchase['fecha_venta'])
                stats['last_purchase_amount'] = NumberFormatter.format_currency(last_purchase['total'])
            else:
                stats['last_purchase_date'] = 'Sin compras'
                stats['last_purchase_amount'] = '$0.00'
            
            # Estado de cuenta
            balance = app.customer_manager.get_customer_balance(customer_id)
            stats['account_balance'] = NumberFormatter.format_currency(balance)
            stats['balance_status'] = 'positive' if balance >= 0 else 'negative'
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    # ==================== FILTROS DE TEMPLATE ====================
    
    @app.template_filter('currency')
    def currency_filter(value):
        """Filtro para formatear moneda"""
        return NumberFormatter.format_currency(value)
    
    @app.template_filter('date')
    def date_filter(value):
        """Filtro para formatear fecha"""
        return DateFormatter.format_date(value)
    
    @app.template_filter('datetime')
    def datetime_filter(value):
        """Filtro para formatear fecha y hora"""
        return DateFormatter.format_datetime(value)
    
    # ==================== CONTEXT PROCESSORS ====================
    
    @app.context_processor
    def inject_globals():
        """Variables globales para templates"""
        return {
            'current_year': datetime.now().year,
            'company_name': 'AlmacénPro v2.0',
            'portal_version': '2.0'
        }
    
    return app

# ==================== PUNTO DE ENTRADA ====================

if __name__ == '__main__':
    app = create_customer_portal_app()
    
    # Configuración para desarrollo
    app.config['DEBUG'] = True
    
    print("🌐 Iniciando Portal de Clientes - AlmacénPro v2.0")
    print("📊 Portal disponible en: http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)