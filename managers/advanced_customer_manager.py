"""
CRM Empresarial Completo - AlmacénPro v2.0
Sistema avanzado de gestión de relaciones con clientes
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from enum import Enum
import json
import statistics

logger = logging.getLogger(__name__)

class CustomerSegment(Enum):
    """Segmentos de clientes"""
    VIP = "vip"
    PREMIUM = "premium"
    REGULAR = "regular"
    NUEVOS = "nuevos"
    INACTIVOS = "inactivos"
    PROBLEMATICOS = "problematicos"

class CustomerLifecycleStage(Enum):
    """Etapas del ciclo de vida del cliente"""
    PROSPECTO = "prospecto"
    NUEVO = "nuevo"
    ACTIVO = "activo"
    EN_RIESGO = "en_riesgo"
    PERDIDO = "perdido"
    REACTIVADO = "reactivado"

class CampaignType(Enum):
    """Tipos de campañas de marketing"""
    EMAIL_MARKETING = "email_marketing"
    SMS_MARKETING = "sms_marketing"
    PROMOCION_ESPECIAL = "promocion_especial"
    PROGRAMA_FIDELIDAD = "programa_fidelidad"
    REACTIVACION = "reactivacion"
    BIENVENIDA = "bienvenida"

class AdvancedCustomerManager:
    """Manager avanzado para CRM empresarial"""
    
    def __init__(self, database_manager):
        self.db = database_manager
        self.logger = logging.getLogger(__name__)
        
        # Configuración del CRM
        self.vip_threshold = 50000  # Umbral para cliente VIP
        self.premium_threshold = 20000  # Umbral para cliente Premium
        self.inactive_days = 90  # Días para considerar cliente inactivo
        self.at_risk_days = 60  # Días para considerar cliente en riesgo
        
        # Inicializar tablas CRM
        self._initialize_crm_tables()
        
    def _initialize_crm_tables(self):
        """Inicializar tablas específicas del CRM"""
        try:
            # Tabla de segmentación de clientes
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS customer_segments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    segment_type TEXT NOT NULL,
                    assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    score DECIMAL(10,2),
                    criteria_met TEXT,
                    active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (customer_id) REFERENCES clientes(id),
                    UNIQUE(customer_id, segment_type, assigned_date)
                )
            """)
            
            # Tabla de ciclo de vida del cliente
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS customer_lifecycle (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    stage TEXT NOT NULL,
                    stage_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    previous_stage TEXT,
                    clv_score DECIMAL(15,2),
                    predicted_next_stage TEXT,
                    stage_duration_days INTEGER,
                    notes TEXT,
                    FOREIGN KEY (customer_id) REFERENCES clientes(id)
                )
            """)
            
            # Tabla de sistema de fidelización
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS loyalty_program (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    total_points INTEGER DEFAULT 0,
                    current_tier TEXT DEFAULT 'BRONCE',
                    tier_since TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    lifetime_points INTEGER DEFAULT 0,
                    points_redeemed INTEGER DEFAULT 0,
                    last_activity TIMESTAMP,
                    active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (customer_id) REFERENCES clientes(id),
                    UNIQUE(customer_id)
                )
            """)
            
            # Tabla de transacciones de puntos
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS loyalty_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    transaction_type TEXT NOT NULL, -- 'EARN' o 'REDEEM'
                    points INTEGER NOT NULL,
                    reference_id INTEGER, -- ID de venta o producto canjeado
                    reference_type TEXT, -- 'SALE' o 'REDEMPTION'
                    description TEXT,
                    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES clientes(id)
                )
            """)
            
            # Tabla de campañas de marketing
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS marketing_campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_name TEXT NOT NULL,
                    campaign_type TEXT NOT NULL,
                    description TEXT,
                    start_date TIMESTAMP,
                    end_date TIMESTAMP,
                    target_segment TEXT,
                    budget DECIMAL(10,2),
                    status TEXT DEFAULT 'DRAFT', -- DRAFT, ACTIVE, COMPLETED, PAUSED
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metrics TEXT -- JSON con métricas de la campaña
                )
            """)
            
            # Tabla de participación en campañas
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS campaign_participants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER NOT NULL,
                    customer_id INTEGER NOT NULL,
                    enrolled_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'ENROLLED', -- ENROLLED, ENGAGED, CONVERTED, UNSUBSCRIBED
                    engagement_score DECIMAL(5,2),
                    conversion_value DECIMAL(10,2),
                    last_interaction TIMESTAMP,
                    FOREIGN KEY (campaign_id) REFERENCES marketing_campaigns(id),
                    FOREIGN KEY (customer_id) REFERENCES clientes(id),
                    UNIQUE(campaign_id, customer_id)
                )
            """)
            
            # Tabla de reclamos y soporte
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS customer_support (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    ticket_number TEXT UNIQUE NOT NULL,
                    subject TEXT NOT NULL,
                    description TEXT,
                    category TEXT, -- RECLAMO, CONSULTA, SOPORTE, DEVOLUCION
                    priority TEXT DEFAULT 'MEDIUM', -- LOW, MEDIUM, HIGH, CRITICAL
                    status TEXT DEFAULT 'OPEN', -- OPEN, IN_PROGRESS, RESOLVED, CLOSED
                    assigned_to INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    satisfaction_score INTEGER, -- 1-5
                    resolution_notes TEXT,
                    FOREIGN KEY (customer_id) REFERENCES clientes(id),
                    FOREIGN KEY (assigned_to) REFERENCES usuarios(id)
                )
            """)
            
            # Tabla de encuestas de satisfacción
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS satisfaction_surveys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    survey_type TEXT NOT NULL, -- POST_SALE, PERIODIC, SUPPORT
                    reference_id INTEGER, -- ID de venta o ticket
                    overall_score INTEGER, -- 1-10
                    product_quality_score INTEGER, -- 1-5
                    service_score INTEGER, -- 1-5
                    delivery_score INTEGER, -- 1-5
                    value_score INTEGER, -- 1-5
                    recommendation_score INTEGER, -- NPS: 0-10
                    comments TEXT,
                    survey_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES clientes(id)
                )
            """)
            
            # Tabla de predicción de comportamiento
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS customer_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    prediction_type TEXT NOT NULL, -- CHURN, CLV, NEXT_PURCHASE, SEGMENT
                    prediction_value DECIMAL(15,2),
                    confidence_score DECIMAL(5,2),
                    model_version TEXT,
                    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    factors TEXT, -- JSON con factores que influyen en la predicción
                    valid_until TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES clientes(id)
                )
            """)
            
            # Índices para optimizar consultas
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_customer_segments_customer ON customer_segments(customer_id)",
                "CREATE INDEX IF NOT EXISTS idx_customer_segments_type ON customer_segments(segment_type)",
                "CREATE INDEX IF NOT EXISTS idx_customer_lifecycle_customer ON customer_lifecycle(customer_id)",
                "CREATE INDEX IF NOT EXISTS idx_customer_lifecycle_stage ON customer_lifecycle(stage)",
                "CREATE INDEX IF NOT EXISTS idx_loyalty_program_customer ON loyalty_program(customer_id)",
                "CREATE INDEX IF NOT EXISTS idx_loyalty_transactions_customer ON loyalty_transactions(customer_id)",
                "CREATE INDEX IF NOT EXISTS idx_campaign_participants_campaign ON campaign_participants(campaign_id)",
                "CREATE INDEX IF NOT EXISTS idx_campaign_participants_customer ON campaign_participants(customer_id)",
                "CREATE INDEX IF NOT EXISTS idx_support_customer ON customer_support(customer_id)",
                "CREATE INDEX IF NOT EXISTS idx_support_status ON customer_support(status)",
                "CREATE INDEX IF NOT EXISTS idx_surveys_customer ON satisfaction_surveys(customer_id)",
                "CREATE INDEX IF NOT EXISTS idx_predictions_customer ON customer_predictions(customer_id)"
            ]
            
            for index_sql in indexes:
                self.db.execute_query(index_sql)
                
            self.logger.info("Tablas CRM inicializadas correctamente")
            
        except Exception as e:
            self.logger.error(f"Error inicializando tablas CRM: {e}")
    
    def perform_customer_segmentation(self) -> Dict:
        """Realizar segmentación automática de clientes"""
        try:
            self.logger.info("Iniciando segmentación automática de clientes")
            
            # Obtener todos los clientes con sus métricas
            customers_query = """
                SELECT 
                    c.id,
                    c.nombre,
                    c.email,
                    c.created_at,
                    COALESCE(SUM(v.total), 0) as total_compras,
                    COUNT(v.id) as cantidad_ventas,
                    MAX(v.fecha_venta) as ultima_compra,
                    MIN(v.fecha_venta) as primera_compra,
                    COALESCE(AVG(v.total), 0) as promedio_compra,
                    COALESCE(AVG(ss.overall_score), 0) as satisfaccion_promedio
                FROM clientes c
                LEFT JOIN ventas v ON c.id = v.customer_id
                LEFT JOIN satisfaction_surveys ss ON c.id = ss.customer_id
                WHERE c.activo = 1
                GROUP BY c.id, c.nombre, c.email, c.created_at
            """
            
            customers = self.db.execute_query(customers_query)
            if not customers:
                return {"error": "No se encontraron clientes"}
            
            segmentation_results = {
                "total_customers": len(customers),
                "segments": {
                    "VIP": [],
                    "PREMIUM": [],
                    "REGULAR": [],
                    "NUEVOS": [],
                    "INACTIVOS": [],
                    "PROBLEMATICOS": []
                },
                "segment_counts": {},
                "criteria": {}
            }
            
            current_date = datetime.now()
            
            for customer_data in customers:
                customer = dict(customer_data)
                customer_id = customer['id']
                total_compras = float(customer['total_compras'] or 0)
                cantidad_ventas = customer['cantidad_ventas'] or 0
                ultima_compra = customer['ultima_compra']
                satisfaccion = float(customer['satisfaccion_promedio'] or 5.0)
                
                # Calcular días desde última compra
                days_since_last_purchase = float('inf')
                if ultima_compra:
                    if isinstance(ultima_compra, str):
                        ultima_compra = datetime.fromisoformat(ultima_compra.replace('Z', '+00:00'))
                    days_since_last_purchase = (current_date - ultima_compra).days
                
                # Calcular días como cliente
                created_at = customer['created_at']
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                days_as_customer = (current_date - created_at).days
                
                # Lógica de segmentación
                segment = None
                criteria_met = []
                score = 0
                
                # Cliente problemático (baja satisfacción y reclamos)
                if satisfaccion < 3.0:
                    segment = CustomerSegment.PROBLEMATICOS.value
                    criteria_met.append("Satisfacción baja")
                    score = satisfaccion * 20  # 0-60 puntos
                
                # Cliente inactivo (más de X días sin compras)
                elif days_since_last_purchase > self.inactive_days:
                    segment = CustomerSegment.INACTIVOS.value
                    criteria_met.append(f"Sin compras por {days_since_last_purchase} días")
                    score = max(0, 50 - (days_since_last_purchase - self.inactive_days) * 0.5)
                
                # Cliente nuevo (menos de 30 días y pocas compras)
                elif days_as_customer <= 30 or cantidad_ventas <= 2:
                    segment = CustomerSegment.NUEVOS.value
                    criteria_met.append("Cliente reciente")
                    score = min(100, days_as_customer * 2 + cantidad_ventas * 10)
                
                # Cliente VIP (alto valor y frecuencia)
                elif total_compras >= self.vip_threshold and cantidad_ventas >= 10:
                    segment = CustomerSegment.VIP.value
                    criteria_met.append(f"Compras por ${total_compras:,.2f}")
                    criteria_met.append(f"{cantidad_ventas} transacciones")
                    score = min(100, 70 + (total_compras / self.vip_threshold) * 20 + satisfaccion * 2)
                
                # Cliente Premium (valor medio-alto)
                elif total_compras >= self.premium_threshold and cantidad_ventas >= 5:
                    segment = CustomerSegment.PREMIUM.value
                    criteria_met.append(f"Compras por ${total_compras:,.2f}")
                    score = min(100, 50 + (total_compras / self.premium_threshold) * 25 + satisfaccion * 2)
                
                # Cliente Regular
                else:
                    segment = CustomerSegment.REGULAR.value
                    criteria_met.append("Cliente estándar")
                    score = 40 + min(30, cantidad_ventas * 3) + satisfaccion * 4
                
                # Guardar segmentación en base de datos
                self.save_customer_segment(customer_id, segment, score, criteria_met)
                
                # Agregar a resultados
                customer_info = {
                    "id": customer_id,
                    "nombre": customer['nombre'],
                    "total_compras": total_compras,
                    "cantidad_ventas": cantidad_ventas,
                    "score": score,
                    "criteria": criteria_met
                }
                
                segmentation_results["segments"][segment.upper()].append(customer_info)
            
            # Calcular conteos por segmento
            for segment, customers in segmentation_results["segments"].items():
                segmentation_results["segment_counts"][segment] = len(customers)
            
            # Guardar criterios utilizados
            segmentation_results["criteria"] = {
                "VIP_threshold": self.vip_threshold,
                "Premium_threshold": self.premium_threshold,
                "inactive_days": self.inactive_days,
                "segmentation_date": current_date.isoformat()
            }
            
            self.logger.info(f"Segmentación completada: {segmentation_results['segment_counts']}")
            return segmentation_results
            
        except Exception as e:
            self.logger.error(f"Error en segmentación de clientes: {e}")
            return {"error": str(e)}
    
    def save_customer_segment(self, customer_id: int, segment: str, score: float, criteria: List[str]):
        """Guardar segmento de cliente en base de datos"""
        try:
            # Desactivar segmentaciones anteriores
            self.db.execute_query("""
                UPDATE customer_segments 
                SET active = FALSE 
                WHERE customer_id = ? AND active = TRUE
            """, (customer_id,))
            
            # Insertar nueva segmentación
            self.db.execute_query("""
                INSERT INTO customer_segments 
                (customer_id, segment_type, score, criteria_met, active)
                VALUES (?, ?, ?, ?, TRUE)
            """, (customer_id, segment, score, json.dumps(criteria)))
            
        except Exception as e:
            self.logger.error(f"Error guardando segmento: {e}")
    
    def calculate_customer_clv(self, customer_id: int, prediction_months: int = 12) -> Dict:
        """Calcular Customer Lifetime Value (CLV)"""
        try:
            # Obtener datos históricos del cliente
            customer_data_query = """
                SELECT 
                    c.id,
                    c.nombre,
                    c.created_at,
                    COUNT(v.id) as total_purchases,
                    COALESCE(SUM(v.total), 0) as total_spent,
                    COALESCE(AVG(v.total), 0) as avg_order_value,
                    MIN(v.fecha_venta) as first_purchase,
                    MAX(v.fecha_venta) as last_purchase
                FROM clientes c
                LEFT JOIN ventas v ON c.id = v.customer_id
                WHERE c.id = ?
                GROUP BY c.id
            """
            
            result = self.db.execute_query(customer_data_query, (customer_id,))
            if not result:
                return {"error": "Cliente no encontrado"}
            
            customer = dict(result[0])
            
            # Calcular métricas base
            total_purchases = customer['total_purchases'] or 0
            total_spent = float(customer['total_spent'] or 0)
            avg_order_value = float(customer['avg_order_value'] or 0)
            
            if total_purchases == 0:
                return {
                    "customer_id": customer_id,
                    "clv": 0,
                    "predicted_clv": 0,
                    "confidence": 0,
                    "metrics": {
                        "total_purchases": 0,
                        "total_spent": 0,
                        "avg_order_value": 0,
                        "purchase_frequency": 0
                    }
                }
            
            # Calcular frecuencia de compra
            first_purchase = customer['first_purchase']
            last_purchase = customer['last_purchase']
            
            if first_purchase and last_purchase:
                if isinstance(first_purchase, str):
                    first_purchase = datetime.fromisoformat(first_purchase.replace('Z', '+00:00'))
                if isinstance(last_purchase, str):
                    last_purchase = datetime.fromisoformat(last_purchase.replace('Z', '+00:00'))
                
                customer_lifespan_days = (last_purchase - first_purchase).days or 1
                purchase_frequency = total_purchases / (customer_lifespan_days / 30)  # Compras por mes
            else:
                customer_lifespan_days = 30
                purchase_frequency = total_purchases
            
            # Obtener datos de compras por mes para calcular tendencias
            monthly_purchases_query = """
                SELECT 
                    strftime('%Y-%m', fecha_venta) as month,
                    COUNT(*) as purchases,
                    SUM(total) as revenue
                FROM ventas
                WHERE customer_id = ?
                GROUP BY strftime('%Y-%m', fecha_venta)
                ORDER BY month DESC
                LIMIT 12
            """
            
            monthly_data = self.db.execute_query(monthly_purchases_query, (customer_id,))
            
            # Calcular tendencia de compras
            if len(monthly_data) >= 3:
                recent_months = [dict(row)['revenue'] for row in monthly_data[:3]]
                older_months = [dict(row)['revenue'] for row in monthly_data[3:6]] if len(monthly_data) >= 6 else [0]
                
                recent_avg = statistics.mean(recent_months) if recent_months else 0
                older_avg = statistics.mean(older_months) if older_months else recent_avg
                
                trend_factor = recent_avg / older_avg if older_avg > 0 else 1.0
                trend_factor = max(0.5, min(2.0, trend_factor))  # Limitar entre 0.5 y 2.0
            else:
                trend_factor = 1.0
            
            # Calcular CLV histórico
            historical_clv = total_spent
            
            # Predicción CLV
            monthly_value = avg_order_value * purchase_frequency * trend_factor
            predicted_clv = monthly_value * prediction_months
            
            # Calcular confianza basada en cantidad de datos
            confidence = min(95, 20 + (total_purchases * 5) + (len(monthly_data) * 10))
            
            # Obtener satisfacción promedio para ajustar predicción
            satisfaction_query = """
                SELECT AVG(overall_score) as avg_satisfaction
                FROM satisfaction_surveys
                WHERE customer_id = ?
            """
            
            satisfaction_result = self.db.execute_query(satisfaction_query, (customer_id,))
            avg_satisfaction = 5.0  # Default
            
            if satisfaction_result and satisfaction_result[0][0]:
                avg_satisfaction = float(satisfaction_result[0][0])
            
            # Ajustar predicción por satisfacción
            satisfaction_factor = avg_satisfaction / 5.0  # Normalizar a 0-2
            predicted_clv *= satisfaction_factor
            
            clv_data = {
                "customer_id": customer_id,
                "customer_name": customer['nombre'],
                "historical_clv": historical_clv,
                "predicted_clv": predicted_clv,
                "total_clv": historical_clv + predicted_clv,
                "confidence": confidence,
                "prediction_months": prediction_months,
                "metrics": {
                    "total_purchases": total_purchases,
                    "total_spent": total_spent,
                    "avg_order_value": avg_order_value,
                    "purchase_frequency": purchase_frequency,
                    "customer_lifespan_days": customer_lifespan_days,
                    "trend_factor": trend_factor,
                    "avg_satisfaction": avg_satisfaction
                },
                "calculation_date": datetime.now().isoformat()
            }
            
            # Guardar predicción en base de datos
            self.save_customer_prediction(customer_id, "CLV", predicted_clv, confidence, clv_data)
            
            return clv_data
            
        except Exception as e:
            self.logger.error(f"Error calculando CLV: {e}")
            return {"error": str(e)}
    
    def save_customer_prediction(self, customer_id: int, prediction_type: str, 
                               prediction_value: float, confidence: float, factors: Dict):
        """Guardar predicción de cliente"""
        try:
            # Calcular fecha de validez (30 días por defecto)
            valid_until = datetime.now() + timedelta(days=30)
            
            self.db.execute_query("""
                INSERT INTO customer_predictions 
                (customer_id, prediction_type, prediction_value, confidence_score, 
                 model_version, factors, valid_until)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                customer_id, prediction_type, prediction_value, confidence,
                "v1.0", json.dumps(factors, default=str), valid_until
            ))
            
        except Exception as e:
            self.logger.error(f"Error guardando predicción: {e}")
    
    def manage_loyalty_program(self, customer_id: int, action: str, points: int = 0, 
                              reference_id: int = None, reference_type: str = None) -> Dict:
        """Gestionar programa de fidelización"""
        try:
            # Verificar si el cliente ya está en el programa
            loyalty_query = """
                SELECT * FROM loyalty_program WHERE customer_id = ?
            """
            
            loyalty_result = self.db.execute_query(loyalty_query, (customer_id,))
            
            if not loyalty_result:
                # Inscribir cliente en programa de fidelización
                self.db.execute_query("""
                    INSERT INTO loyalty_program (customer_id, total_points, current_tier)
                    VALUES (?, 0, 'BRONCE')
                """, (customer_id,))
                
                current_loyalty = {
                    'customer_id': customer_id,
                    'total_points': 0,
                    'current_tier': 'BRONCE',
                    'lifetime_points': 0,
                    'points_redeemed': 0
                }
            else:
                current_loyalty = dict(loyalty_result[0])
            
            # Procesar acción
            if action == "EARN" and points > 0:
                # Sumar puntos
                new_total = current_loyalty['total_points'] + points
                new_lifetime = current_loyalty['lifetime_points'] + points
                
                # Actualizar puntos
                self.db.execute_query("""
                    UPDATE loyalty_program 
                    SET total_points = ?, lifetime_points = ?, last_activity = CURRENT_TIMESTAMP
                    WHERE customer_id = ?
                """, (new_total, new_lifetime, customer_id))
                
                # Registrar transacción
                self.db.execute_query("""
                    INSERT INTO loyalty_transactions 
                    (customer_id, transaction_type, points, reference_id, reference_type, description)
                    VALUES (?, 'EARN', ?, ?, ?, ?)
                """, (customer_id, points, reference_id, reference_type, f"Puntos ganados por {reference_type}"))
                
                # Verificar cambio de nivel
                new_tier = self.calculate_loyalty_tier(new_lifetime)
                if new_tier != current_loyalty['current_tier']:
                    self.db.execute_query("""
                        UPDATE loyalty_program 
                        SET current_tier = ?, tier_since = CURRENT_TIMESTAMP
                        WHERE customer_id = ?
                    """, (new_tier, customer_id))
                
                current_loyalty['total_points'] = new_total
                current_loyalty['current_tier'] = new_tier
                
            elif action == "REDEEM" and points > 0:
                # Verificar que tenga suficientes puntos
                if current_loyalty['total_points'] >= points:
                    new_total = current_loyalty['total_points'] - points
                    new_redeemed = current_loyalty['points_redeemed'] + points
                    
                    # Actualizar puntos
                    self.db.execute_query("""
                        UPDATE loyalty_program 
                        SET total_points = ?, points_redeemed = ?, last_activity = CURRENT_TIMESTAMP
                        WHERE customer_id = ?
                    """, (new_total, new_redeemed, customer_id))
                    
                    # Registrar transacción
                    self.db.execute_query("""
                        INSERT INTO loyalty_transactions 
                        (customer_id, transaction_type, points, reference_id, reference_type, description)
                        VALUES (?, 'REDEEM', ?, ?, ?, ?)
                    """, (customer_id, -points, reference_id, reference_type, f"Puntos canjeados por {reference_type}"))
                    
                    current_loyalty['total_points'] = new_total
                else:
                    return {"error": "Puntos insuficientes"}
            
            # Obtener información actualizada
            updated_loyalty = self.db.execute_query(loyalty_query, (customer_id,))
            if updated_loyalty:
                loyalty_info = dict(updated_loyalty[0])
                
                # Obtener historial reciente
                history_query = """
                    SELECT * FROM loyalty_transactions 
                    WHERE customer_id = ?
                    ORDER BY transaction_date DESC
                    LIMIT 10
                """
                
                history = self.db.execute_query(history_query, (customer_id,))
                loyalty_info['recent_transactions'] = [dict(t) for t in history] if history else []
                
                return {
                    "success": True,
                    "action": action,
                    "points_processed": points,
                    "loyalty_info": loyalty_info
                }
            
            return {"error": "Error actualizando programa de fidelización"}
            
        except Exception as e:
            self.logger.error(f"Error en programa de fidelización: {e}")
            return {"error": str(e)}
    
    def calculate_loyalty_tier(self, lifetime_points: int) -> str:
        """Calcular nivel de fidelización basado en puntos acumulados"""
        if lifetime_points >= 10000:
            return "DIAMANTE"
        elif lifetime_points >= 5000:
            return "ORO"
        elif lifetime_points >= 2000:
            return "PLATA"
        else:
            return "BRONCE"
    
    def create_marketing_campaign(self, campaign_data: Dict) -> Dict:
        """Crear campaña de marketing automatizada"""
        try:
            # Validar datos requeridos
            required_fields = ['campaign_name', 'campaign_type', 'target_segment']
            for field in required_fields:
                if field not in campaign_data:
                    return {"error": f"Campo requerido: {field}"}
            
            # Generar criterios de segmentación
            target_segment = campaign_data['target_segment']
            target_customers = self.get_customers_by_segment(target_segment)
            
            if not target_customers:
                return {"error": "No se encontraron clientes para el segmento objetivo"}
            
            # Crear campaña
            campaign_id = self.db.execute_query("""
                INSERT INTO marketing_campaigns 
                (campaign_name, campaign_type, description, start_date, end_date, 
                 target_segment, budget, status, metrics)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'DRAFT', ?)
            """, (
                campaign_data['campaign_name'],
                campaign_data['campaign_type'],
                campaign_data.get('description', ''),
                campaign_data.get('start_date'),
                campaign_data.get('end_date'),
                target_segment,
                campaign_data.get('budget', 0),
                json.dumps({"target_customers": len(target_customers)})
            ))
            
            if campaign_id:
                # Inscribir clientes objetivo
                enrolled_count = 0
                for customer in target_customers:
                    try:
                        self.db.execute_query("""
                            INSERT INTO campaign_participants 
                            (campaign_id, customer_id, status)
                            VALUES (?, ?, 'ENROLLED')
                        """, (campaign_id, customer['id']))
                        enrolled_count += 1
                    except:
                        continue  # Cliente ya inscrito o error
                
                return {
                    "success": True,
                    "campaign_id": campaign_id,
                    "target_customers": len(target_customers),
                    "enrolled_customers": enrolled_count,
                    "campaign_data": campaign_data
                }
            
            return {"error": "Error creando campaña"}
            
        except Exception as e:
            self.logger.error(f"Error creando campaña: {e}")
            return {"error": str(e)}
    
    def get_customers_by_segment(self, segment: str) -> List[Dict]:
        """Obtener clientes por segmento"""
        try:
            query = """
                SELECT c.*, cs.score, cs.criteria_met
                FROM clientes c
                JOIN customer_segments cs ON c.id = cs.customer_id
                WHERE cs.segment_type = ? AND cs.active = TRUE AND c.activo = 1
                ORDER BY cs.score DESC
            """
            
            result = self.db.execute_query(query, (segment.upper(),))
            return [dict(row) for row in result] if result else []
            
        except Exception as e:
            self.logger.error(f"Error obteniendo clientes por segmento: {e}")
            return []
    
    def predict_customer_churn(self, customer_id: int = None) -> Dict:
        """Predecir riesgo de abandono de clientes"""
        try:
            # Si se especifica un cliente, analizar solo ese
            if customer_id:
                customers_query = """
                    SELECT id FROM clientes WHERE id = ? AND activo = 1
                """
                customers_result = self.db.execute_query(customers_query, (customer_id,))
                customer_ids = [customer_id] if customers_result else []
            else:
                # Analizar todos los clientes activos
                customers_query = """
                    SELECT id FROM clientes WHERE activo = 1
                """
                customers_result = self.db.execute_query(customers_query)
                customer_ids = [row[0] for row in customers_result] if customers_result else []
            
            churn_predictions = []
            
            for cid in customer_ids:
                # Obtener métricas del cliente
                metrics_query = """
                    SELECT 
                        c.id,
                        c.nombre,
                        COUNT(v.id) as total_purchases,
                        COALESCE(MAX(v.fecha_venta), c.created_at) as last_activity,
                        COALESCE(AVG(v.total), 0) as avg_order_value,
                        COALESCE(SUM(v.total), 0) as total_spent,
                        COALESCE(AVG(ss.overall_score), 5.0) as avg_satisfaction,
                        COUNT(cs_support.id) as support_tickets
                    FROM clientes c
                    LEFT JOIN ventas v ON c.id = v.customer_id
                    LEFT JOIN satisfaction_surveys ss ON c.id = ss.customer_id
                    LEFT JOIN customer_support cs_support ON c.id = cs_support.customer_id
                    WHERE c.id = ?
                    GROUP BY c.id
                """
                
                metrics_result = self.db.execute_query(metrics_query, (cid,))
                if not metrics_result:
                    continue
                
                metrics = dict(metrics_result[0])
                
                # Calcular factores de riesgo
                current_date = datetime.now()
                last_activity = metrics['last_activity']
                
                if isinstance(last_activity, str):
                    last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                
                days_inactive = (current_date - last_activity).days
                
                # Modelo simple de predicción de churn
                risk_score = 0
                risk_factors = []
                
                # Factor 1: Inactividad (40% del score)
                if days_inactive > 90:
                    risk_score += 40
                    risk_factors.append(f"Inactivo por {days_inactive} días")
                elif days_inactive > 60:
                    risk_score += 25
                    risk_factors.append(f"Poca actividad ({days_inactive} días)")
                elif days_inactive > 30:
                    risk_score += 10
                    risk_factors.append(f"Actividad reducida ({days_inactive} días)")
                
                # Factor 2: Satisfacción (25% del score)
                avg_satisfaction = float(metrics['avg_satisfaction'])
                if avg_satisfaction < 3:
                    risk_score += 25
                    risk_factors.append(f"Baja satisfacción ({avg_satisfaction:.1f}/10)")
                elif avg_satisfaction < 4:
                    risk_score += 15
                    risk_factors.append(f"Satisfacción moderada ({avg_satisfaction:.1f}/10)")
                
                # Factor 3: Valor del cliente (20% del score)
                total_spent = float(metrics['total_spent'])
                if total_spent < 1000:  # Cliente de bajo valor
                    risk_score += 20
                    risk_factors.append("Cliente de bajo valor")
                elif total_spent < 5000:
                    risk_score += 10
                    risk_factors.append("Valor medio-bajo")
                
                # Factor 4: Tickets de soporte (15% del score)
                support_tickets = metrics['support_tickets']
                if support_tickets > 5:
                    risk_score += 15
                    risk_factors.append(f"Múltiples tickets de soporte ({support_tickets})")
                elif support_tickets > 2:
                    risk_score += 8
                    risk_factors.append(f"Algunos tickets de soporte ({support_tickets})")
                
                # Determinar nivel de riesgo
                if risk_score >= 70:
                    risk_level = "ALTO"
                elif risk_score >= 40:
                    risk_level = "MEDIO"
                elif risk_score >= 20:
                    risk_level = "BAJO"
                else:
                    risk_level = "MUY BAJO"
                
                # Calcular confianza de la predicción
                confidence = min(95, 50 + (metrics['total_purchases'] * 5))
                
                churn_prediction = {
                    "customer_id": cid,
                    "customer_name": metrics['nombre'],
                    "risk_score": risk_score,
                    "risk_level": risk_level,
                    "confidence": confidence,
                    "risk_factors": risk_factors,
                    "days_inactive": days_inactive,
                    "metrics": {
                        "total_purchases": metrics['total_purchases'],
                        "total_spent": total_spent,
                        "avg_satisfaction": avg_satisfaction,
                        "support_tickets": support_tickets
                    },
                    "recommendations": self.generate_churn_recommendations(risk_level, risk_factors)
                }
                
                churn_predictions.append(churn_prediction)
                
                # Guardar predicción
                self.save_customer_prediction(cid, "CHURN", risk_score, confidence, churn_prediction)
            
            # Ordenar por riesgo descendente
            churn_predictions.sort(key=lambda x: x['risk_score'], reverse=True)
            
            return {
                "success": True,
                "total_customers_analyzed": len(churn_predictions),
                "high_risk_customers": len([p for p in churn_predictions if p['risk_level'] == 'ALTO']),
                "medium_risk_customers": len([p for p in churn_predictions if p['risk_level'] == 'MEDIO']),
                "predictions": churn_predictions[:20] if not customer_id else churn_predictions  # Top 20 o específico
            }
            
        except Exception as e:
            self.logger.error(f"Error prediciendo churn: {e}")
            return {"error": str(e)}
    
    def generate_churn_recommendations(self, risk_level: str, risk_factors: List[str]) -> List[str]:
        """Generar recomendaciones para prevenir churn"""
        recommendations = []
        
        if risk_level == "ALTO":
            recommendations.extend([
                "Contacto inmediato del gerente de cuentas",
                "Oferta especial personalizada (descuento 15-20%)",
                "Encuesta de satisfacción urgente",
                "Asignación de account manager dedicado"
            ])
        elif risk_level == "MEDIO":
            recommendations.extend([
                "Campaña de reactivación por email",
                "Descuento del 10% en próxima compra",
                "Encuesta de satisfacción",
                "Invitación a programa de fidelización"
            ])
        else:
            recommendations.extend([
                "Mantener en programa de fidelización",
                "Newsletter personalizado",
                "Ofertas estacionales"
            ])
        
        # Recomendaciones específicas por factores
        for factor in risk_factors:
            if "satisfacción" in factor.lower():
                recommendations.append("Seguimiento de servicio al cliente")
            if "tickets" in factor.lower():
                recommendations.append("Revisión de historial de soporte")
            if "inactivo" in factor.lower():
                recommendations.append("Campaña de reactivación urgente")
        
        return list(set(recommendations))  # Eliminar duplicados
    
    def create_support_ticket(self, ticket_data: Dict) -> Dict:
        """Crear ticket de soporte al cliente"""
        try:
            # Generar número de ticket único
            ticket_number = f"TK{datetime.now().strftime('%Y%m%d')}{self.generate_ticket_sequence():03d}"
            
            # Insertar ticket
            ticket_id = self.db.execute_query("""
                INSERT INTO customer_support 
                (customer_id, ticket_number, subject, description, category, priority, assigned_to)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                ticket_data['customer_id'],
                ticket_number,
                ticket_data['subject'],
                ticket_data.get('description', ''),
                ticket_data.get('category', 'CONSULTA'),
                ticket_data.get('priority', 'MEDIUM'),
                ticket_data.get('assigned_to')
            ))
            
            if ticket_id:
                return {
                    "success": True,
                    "ticket_id": ticket_id,
                    "ticket_number": ticket_number,
                    "estimated_resolution": self.estimate_resolution_time(ticket_data.get('priority', 'MEDIUM'))
                }
            
            return {"error": "Error creando ticket"}
            
        except Exception as e:
            self.logger.error(f"Error creando ticket: {e}")
            return {"error": str(e)}
    
    def generate_ticket_sequence(self) -> int:
        """Generar secuencia para número de ticket"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            count_query = """
                SELECT COUNT(*) FROM customer_support 
                WHERE DATE(created_at) = ?
            """
            result = self.db.execute_query(count_query, (today,))
            return (result[0][0] if result else 0) + 1
        except:
            return 1
    
    def estimate_resolution_time(self, priority: str) -> str:
        """Estimar tiempo de resolución según prioridad"""
        time_estimates = {
            "CRITICAL": "2-4 horas",
            "HIGH": "4-8 horas", 
            "MEDIUM": "1-2 días",
            "LOW": "3-5 días"
        }
        return time_estimates.get(priority, "1-2 días")
    
    def conduct_satisfaction_survey(self, customer_id: int, survey_data: Dict) -> Dict:
        """Realizar encuesta de satisfacción"""
        try:
            survey_id = self.db.execute_query("""
                INSERT INTO satisfaction_surveys 
                (customer_id, survey_type, reference_id, overall_score, 
                 product_quality_score, service_score, delivery_score, 
                 value_score, recommendation_score, comments)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer_id,
                survey_data.get('survey_type', 'PERIODIC'),
                survey_data.get('reference_id'),
                survey_data.get('overall_score'),
                survey_data.get('product_quality_score'),
                survey_data.get('service_score'),
                survey_data.get('delivery_score'),
                survey_data.get('value_score'),
                survey_data.get('recommendation_score'),
                survey_data.get('comments', '')
            ))
            
            if survey_id:
                # Analizar resultado y generar alertas si es necesario
                overall_score = survey_data.get('overall_score', 5)
                if overall_score <= 3:
                    # Crear ticket automático por baja satisfacción
                    self.create_support_ticket({
                        'customer_id': customer_id,
                        'subject': 'Baja satisfacción detectada',
                        'description': f'Cliente reportó satisfacción de {overall_score}/10. Requiere seguimiento.',
                        'category': 'RECLAMO',
                        'priority': 'HIGH'
                    })
                
                return {
                    "success": True,
                    "survey_id": survey_id,
                    "nps_score": self.calculate_nps_category(survey_data.get('recommendation_score', 5)),
                    "action_required": overall_score <= 3
                }
            
            return {"error": "Error guardando encuesta"}
            
        except Exception as e:
            self.logger.error(f"Error en encuesta de satisfacción: {e}")
            return {"error": str(e)}
    
    def calculate_nps_category(self, recommendation_score: int) -> str:
        """Calcular categoría NPS"""
        if recommendation_score >= 9:
            return "PROMOTOR"
        elif recommendation_score >= 7:
            return "PASIVO"
        else:
            return "DETRACTOR"
    
    def get_customer_360_view(self, customer_id: int) -> Dict:
        """Vista 360 completa del cliente"""
        try:
            # Información básica
            customer_query = """
                SELECT * FROM clientes WHERE id = ?
            """
            customer_result = self.db.execute_query(customer_query, (customer_id,))
            if not customer_result:
                return {"error": "Cliente no encontrado"}
            
            customer_info = dict(customer_result[0])
            
            # Segmentación actual
            segment_query = """
                SELECT segment_type, score, criteria_met, assigned_date 
                FROM customer_segments 
                WHERE customer_id = ? AND active = TRUE
                ORDER BY assigned_date DESC LIMIT 1
            """
            segment_result = self.db.execute_query(segment_query, (customer_id,))
            segment_info = dict(segment_result[0]) if segment_result else {"segment_type": "NO_SEGMENTADO"}
            
            # CLV
            clv_info = self.calculate_customer_clv(customer_id)
            
            # Programa de fidelización
            loyalty_query = """
                SELECT * FROM loyalty_program WHERE customer_id = ?
            """
            loyalty_result = self.db.execute_query(loyalty_query, (customer_id,))
            loyalty_info = dict(loyalty_result[0]) if loyalty_result else {"total_points": 0, "current_tier": "NO_INSCRITO"}
            
            # Predicción de churn
            churn_prediction = self.predict_customer_churn(customer_id)
            churn_info = churn_prediction.get('predictions', [{}])[0] if churn_prediction.get('predictions') else {}
            
            # Historial de ventas (últimas 10)
            sales_query = """
                SELECT fecha_venta, total, metodo_pago, estado
                FROM ventas
                WHERE customer_id = ?
                ORDER BY fecha_venta DESC
                LIMIT 10
            """
            sales_result = self.db.execute_query(sales_query, (customer_id,))
            sales_history = [dict(sale) for sale in sales_result] if sales_result else []
            
            # Tickets de soporte
            support_query = """
                SELECT ticket_number, subject, category, priority, status, created_at, satisfaction_score
                FROM customer_support
                WHERE customer_id = ?
                ORDER BY created_at DESC
                LIMIT 5
            """
            support_result = self.db.execute_query(support_query, (customer_id,))
            support_tickets = [dict(ticket) for ticket in support_result] if support_result else []
            
            # Encuestas de satisfacción
            survey_query = """
                SELECT overall_score, recommendation_score, survey_type, survey_date, comments
                FROM satisfaction_surveys
                WHERE customer_id = ?
                ORDER BY survey_date DESC
                LIMIT 5
            """
            survey_result = self.db.execute_query(survey_query, (customer_id,))
            satisfaction_surveys = [dict(survey) for survey in survey_result] if survey_result else []
            
            # Participación en campañas
            campaign_query = """
                SELECT mc.campaign_name, mc.campaign_type, cp.status, cp.enrolled_date, cp.engagement_score
                FROM campaign_participants cp
                JOIN marketing_campaigns mc ON cp.campaign_id = mc.id
                WHERE cp.customer_id = ?
                ORDER BY cp.enrolled_date DESC
                LIMIT 5
            """
            campaign_result = self.db.execute_query(campaign_query, (customer_id,))
            campaign_participation = [dict(camp) for camp in campaign_result] if campaign_result else []
            
            return {
                "customer_info": customer_info,
                "segmentation": segment_info,
                "clv": clv_info,
                "loyalty": loyalty_info,
                "churn_risk": churn_info,
                "sales_history": sales_history,
                "support_tickets": support_tickets,
                "satisfaction_surveys": satisfaction_surveys,
                "campaign_participation": campaign_participation,
                "summary_metrics": {
                    "total_sales": len(sales_history),
                    "total_support_tickets": len(support_tickets),
                    "avg_satisfaction": statistics.mean([s['overall_score'] for s in satisfaction_surveys if s['overall_score']]) if satisfaction_surveys else 0,
                    "active_campaigns": len([c for c in campaign_participation if c['status'] == 'ENROLLED'])
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo vista 360: {e}")
            return {"error": str(e)}
    
    def get_crm_dashboard_data(self) -> Dict:
        """Obtener datos para dashboard CRM"""
        try:
            current_date = datetime.now()
            
            # Métricas principales
            metrics = {}
            
            # Total de clientes
            total_customers_query = "SELECT COUNT(*) FROM clientes WHERE activo = 1"
            total_customers = self.db.execute_query(total_customers_query)[0][0]
            metrics['total_customers'] = total_customers
            
            # Clientes nuevos este mes
            month_start = current_date.replace(day=1)
            new_customers_query = """
                SELECT COUNT(*) FROM clientes 
                WHERE activo = 1 AND DATE(created_at) >= ?
            """
            new_customers = self.db.execute_query(new_customers_query, (month_start.date(),))[0][0]
            metrics['new_customers_this_month'] = new_customers
            
            # Distribución por segmentos
            segments_query = """
                SELECT segment_type, COUNT(*) as count
                FROM customer_segments
                WHERE active = TRUE
                GROUP BY segment_type
            """
            segments_result = self.db.execute_query(segments_query)
            metrics['segments_distribution'] = {row[0]: row[1] for row in segments_result} if segments_result else {}
            
            # Tickets de soporte abiertos
            open_tickets_query = """
                SELECT COUNT(*) FROM customer_support 
                WHERE status IN ('OPEN', 'IN_PROGRESS')
            """
            open_tickets = self.db.execute_query(open_tickets_query)[0][0]
            metrics['open_support_tickets'] = open_tickets
            
            # Satisfacción promedio
            avg_satisfaction_query = """
                SELECT AVG(overall_score) FROM satisfaction_surveys
                WHERE DATE(survey_date) >= ?
            """
            thirty_days_ago = current_date - timedelta(days=30)
            avg_satisfaction_result = self.db.execute_query(avg_satisfaction_query, (thirty_days_ago.date(),))
            avg_satisfaction = avg_satisfaction_result[0][0] if avg_satisfaction_result[0][0] else 0
            metrics['avg_satisfaction'] = round(avg_satisfaction, 1)
            
            # Campañas activas
            active_campaigns_query = """
                SELECT COUNT(*) FROM marketing_campaigns 
                WHERE status = 'ACTIVE'
            """
            active_campaigns = self.db.execute_query(active_campaigns_query)[0][0]
            metrics['active_campaigns'] = active_campaigns
            
            # Top clientes por CLV
            top_clv_query = """
                SELECT c.id, c.nombre, cp.prediction_value as clv
                FROM customer_predictions cp
                JOIN clientes c ON cp.customer_id = c.id
                WHERE cp.prediction_type = 'CLV' 
                AND cp.prediction_date >= ?
                ORDER BY cp.prediction_value DESC
                LIMIT 10
            """
            week_ago = current_date - timedelta(days=7)
            top_clv_result = self.db.execute_query(top_clv_query, (week_ago,))
            metrics['top_clv_customers'] = [dict(row) for row in top_clv_result] if top_clv_result else []
            
            # Clientes en riesgo de churn
            high_risk_query = """
                SELECT c.id, c.nombre, cp.prediction_value as risk_score
                FROM customer_predictions cp
                JOIN clientes c ON cp.customer_id = c.id
                WHERE cp.prediction_type = 'CHURN' 
                AND cp.prediction_value >= 70
                AND cp.prediction_date >= ?
                ORDER BY cp.prediction_value DESC
                LIMIT 10
            """
            high_risk_result = self.db.execute_query(high_risk_query, (week_ago,))
            metrics['high_risk_customers'] = [dict(row) for row in high_risk_result] if high_risk_result else []
            
            return {
                "success": True,
                "metrics": metrics,
                "last_updated": current_date.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo datos de dashboard CRM: {e}")
            return {"error": str(e)}