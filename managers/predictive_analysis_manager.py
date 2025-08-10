"""
Gestor de Análisis Predictivo - AlmacénPro v2.0
Sistema avanzado de análisis predictivo y machine learning para clientes
"""

import logging
import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import sqlite3
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

@dataclass
class CustomerPrediction:
    """Estructura para predicciones de cliente"""
    customer_id: int
    prediction_type: str
    probability: float
    confidence: str
    factors: List[str]
    recommendation: str
    created_at: datetime

@dataclass
class SegmentProfile:
    """Perfil de segmento de clientes"""
    segment_id: str
    name: str
    description: str
    size: int
    avg_purchase: float
    avg_frequency: float
    retention_rate: float
    characteristics: Dict[str, Any]

@dataclass
class PurchasePattern:
    """Patrón de compra detectado"""
    pattern_id: str
    customer_id: int
    pattern_type: str
    frequency: str
    seasonal: bool
    products: List[str]
    probability: float
    next_purchase_date: Optional[datetime]

class PredictiveAnalysisManager:
    """Gestor de análisis predictivo de clientes"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.min_transactions = 3  # Mínimo para análisis
        self.confidence_threshold = 0.7
        
        # Configurar segmentos predefinidos
        self.segment_definitions = {
            'high_value': {'min_total': 50000, 'min_frequency': 10},
            'frequent': {'min_frequency': 15, 'max_days_since': 30},
            'seasonal': {'seasonal_variance': 0.3},
            'at_risk': {'days_since_last': 60, 'declining_trend': True},
            'new': {'registration_days': 90, 'transaction_count': 1},
            'dormant': {'days_since_last': 180}
        }

    def analyze_customer_behavior(self, customer_id: int) -> Dict[str, Any]:
        """Análisis completo de comportamiento de cliente"""
        try:
            # Obtener datos históricos
            customer_data = self._get_customer_data(customer_id)
            if not customer_data:
                return {'error': 'Cliente no encontrado o sin datos suficientes'}
            
            # Análisis de patrones
            purchase_patterns = self._analyze_purchase_patterns(customer_id)
            
            # Análisis de tendencias
            trends = self._analyze_trends(customer_id)
            
            # Predicción de churn
            churn_prediction = self._predict_churn(customer_id)
            
            # Segmentación automática
            segment = self._classify_customer_segment(customer_id)
            
            # Predicción de próxima compra
            next_purchase = self._predict_next_purchase(customer_id)
            
            # Recomendaciones de productos
            product_recommendations = self._recommend_products(customer_id)
            
            # Valor de vida del cliente (CLV)
            clv_prediction = self._calculate_clv_prediction(customer_id)
            
            return {
                'customer_id': customer_id,
                'analysis_date': datetime.now().isoformat(),
                'purchase_patterns': purchase_patterns,
                'trends': trends,
                'churn_prediction': churn_prediction,
                'segment': segment,
                'next_purchase_prediction': next_purchase,
                'product_recommendations': product_recommendations,
                'clv_prediction': clv_prediction,
                'confidence_score': self._calculate_overall_confidence(customer_id)
            }
            
        except Exception as e:
            logger.error(f"Error analizando comportamiento del cliente {customer_id}: {e}")
            return {'error': str(e)}

    def _get_customer_data(self, customer_id: int) -> Dict[str, Any]:
        """Obtener datos completos del cliente"""
        try:
            query = """
            SELECT c.*, 
                   COUNT(v.id) as total_purchases,
                   COALESCE(SUM(v.total), 0) as total_spent,
                   COALESCE(AVG(v.total), 0) as avg_purchase,
                   MAX(v.fecha_venta) as last_purchase,
                   MIN(v.fecha_venta) as first_purchase,
                   julianday('now') - julianday(MAX(v.fecha_venta)) as days_since_last,
                   julianday(MAX(v.fecha_venta)) - julianday(MIN(v.fecha_venta)) as customer_lifespan
            FROM clientes c
            LEFT JOIN ventas v ON c.id = v.cliente_id
            WHERE c.id = ?
            GROUP BY c.id
            """
            
            result = self.db_manager.execute_query(query, (customer_id,))
            if result:
                return dict(result[0])
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo datos del cliente {customer_id}: {e}")
            return None

    def _analyze_purchase_patterns(self, customer_id: int) -> List[Dict[str, Any]]:
        """Análisis de patrones de compra"""
        try:
            # Obtener historial de compras
            query = """
            SELECT v.fecha_venta, v.total, dv.producto_id, dv.cantidad, p.nombre, p.categoria
            FROM ventas v
            JOIN detalle_venta dv ON v.id = dv.venta_id
            JOIN productos p ON dv.producto_id = p.id
            WHERE v.cliente_id = ?
            ORDER BY v.fecha_venta
            """
            
            purchases = self.db_manager.execute_query(query, (customer_id,))
            if not purchases or len(purchases) < self.min_transactions:
                return []
            
            patterns = []
            
            # Patrón de frecuencia
            frequency_pattern = self._analyze_frequency_pattern(purchases)
            if frequency_pattern:
                patterns.append(frequency_pattern)
            
            # Patrón estacional
            seasonal_pattern = self._analyze_seasonal_pattern(purchases)
            if seasonal_pattern:
                patterns.append(seasonal_pattern)
            
            # Patrón de productos
            product_pattern = self._analyze_product_pattern(purchases)
            if product_pattern:
                patterns.append(product_pattern)
            
            # Patrón de montos
            amount_pattern = self._analyze_amount_pattern(purchases)
            if amount_pattern:
                patterns.append(amount_pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analizando patrones de compra: {e}")
            return []

    def _analyze_frequency_pattern(self, purchases: List) -> Optional[Dict[str, Any]]:
        """Análisis de patrón de frecuencia"""
        try:
            if len(purchases) < 2:
                return None
            
            # Calcular intervalos entre compras
            dates = [datetime.strptime(p['fecha_venta'], '%Y-%m-%d %H:%M:%S') for p in purchases]
            intervals = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
            
            if not intervals:
                return None
            
            avg_interval = sum(intervals) / len(intervals)
            std_deviation = (sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)) ** 0.5
            
            # Determinar tipo de frecuencia
            if avg_interval <= 7:
                frequency_type = 'weekly'
            elif avg_interval <= 30:
                frequency_type = 'monthly'
            elif avg_interval <= 90:
                frequency_type = 'quarterly'
            else:
                frequency_type = 'irregular'
            
            regularity = 1.0 - min(std_deviation / avg_interval, 1.0) if avg_interval > 0 else 0
            
            return {
                'pattern_type': 'frequency',
                'frequency_type': frequency_type,
                'avg_days_between_purchases': round(avg_interval, 1),
                'regularity_score': round(regularity, 2),
                'confidence': 'high' if regularity > 0.7 else 'medium' if regularity > 0.4 else 'low',
                'description': f'Cliente compra cada {avg_interval:.0f} días en promedio'
            }
            
        except Exception as e:
            logger.error(f"Error analizando patrón de frecuencia: {e}")
            return None

    def _analyze_seasonal_pattern(self, purchases: List) -> Optional[Dict[str, Any]]:
        """Análisis de patrón estacional"""
        try:
            if len(purchases) < 6:  # Necesario para detectar patrones estacionales
                return None
            
            # Agrupar compras por mes
            monthly_purchases = defaultdict(list)
            for purchase in purchases:
                date = datetime.strptime(purchase['fecha_venta'], '%Y-%m-%d %H:%M:%S')
                month = date.month
                monthly_purchases[month].append(purchase['total'])
            
            # Calcular promedios mensuales
            monthly_averages = {month: sum(totals) / len(totals) 
                              for month, totals in monthly_purchases.items()}
            
            if len(monthly_averages) < 3:
                return None
            
            # Detectar variación estacional
            avg_total = sum(monthly_averages.values()) / len(monthly_averages)
            variance = sum((v - avg_total) ** 2 for v in monthly_averages.values()) / len(monthly_averages)
            coefficient_of_variation = (variance ** 0.5) / avg_total if avg_total > 0 else 0
            
            is_seasonal = coefficient_of_variation > 0.3
            
            if not is_seasonal:
                return None
            
            # Encontrar meses pico y valle
            peak_month = max(monthly_averages.keys(), key=lambda k: monthly_averages[k])
            low_month = min(monthly_averages.keys(), key=lambda k: monthly_averages[k])
            
            month_names = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                          'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
            
            return {
                'pattern_type': 'seasonal',
                'is_seasonal': True,
                'seasonality_strength': round(coefficient_of_variation, 2),
                'peak_month': peak_month,
                'peak_month_name': month_names[peak_month - 1],
                'low_month': low_month,
                'low_month_name': month_names[low_month - 1],
                'monthly_averages': monthly_averages,
                'confidence': 'high' if coefficient_of_variation > 0.5 else 'medium',
                'description': f'Cliente muestra patrón estacional con pico en {month_names[peak_month - 1]}'
            }
            
        except Exception as e:
            logger.error(f"Error analizando patrón estacional: {e}")
            return None

    def _analyze_product_pattern(self, purchases: List) -> Optional[Dict[str, Any]]:
        """Análisis de patrón de productos"""
        try:
            # Contar productos y categorías
            product_counts = Counter()
            category_counts = Counter()
            
            for purchase in purchases:
                product_counts[purchase['nombre']] += purchase['cantidad']
                category_counts[purchase['categoria']] += purchase['cantidad']
            
            if not product_counts:
                return None
            
            # Top productos y categorías
            top_products = dict(product_counts.most_common(5))
            top_categories = dict(category_counts.most_common(3))
            
            # Calcular diversidad (índice de Shannon)
            total_items = sum(product_counts.values())
            diversity = -sum((count/total_items) * math.log(count/total_items) 
                           for count in product_counts.values() if count > 0)
            
            # Detectar lealtad a productos
            loyalty_score = product_counts.most_common(1)[0][1] / total_items
            
            return {
                'pattern_type': 'product_preference',
                'top_products': top_products,
                'top_categories': top_categories,
                'product_diversity': round(diversity, 2),
                'loyalty_score': round(loyalty_score, 2),
                'total_unique_products': len(product_counts),
                'confidence': 'high' if loyalty_score > 0.5 else 'medium',
                'description': f'Cliente prefiere {list(top_categories.keys())[0]} con {loyalty_score:.0%} de lealtad'
            }
            
        except Exception as e:
            logger.error(f"Error analizando patrón de productos: {e}")
            return None

    def _analyze_amount_pattern(self, purchases: List) -> Optional[Dict[str, Any]]:
        """Análisis de patrón de montos"""
        try:
            amounts = [purchase['total'] for purchase in purchases]
            if len(amounts) < 2:
                return None
            
            avg_amount = sum(amounts) / len(amounts)
            std_dev = (sum((x - avg_amount) ** 2 for x in amounts) / len(amounts)) ** 0.5
            
            # Detectar tendencia
            mid_point = len(amounts) // 2
            first_half_avg = sum(amounts[:mid_point]) / mid_point if mid_point > 0 else 0
            second_half_avg = sum(amounts[mid_point:]) / (len(amounts) - mid_point)
            
            trend_change = (second_half_avg - first_half_avg) / first_half_avg if first_half_avg > 0 else 0
            
            if trend_change > 0.2:
                trend = 'increasing'
            elif trend_change < -0.2:
                trend = 'decreasing'
            else:
                trend = 'stable'
            
            # Detectar consistencia
            consistency = 1.0 - min(std_dev / avg_amount, 1.0) if avg_amount > 0 else 0
            
            return {
                'pattern_type': 'spending_behavior',
                'avg_amount': round(avg_amount, 2),
                'std_deviation': round(std_dev, 2),
                'consistency_score': round(consistency, 2),
                'trend': trend,
                'trend_change_percent': round(trend_change * 100, 1),
                'min_amount': min(amounts),
                'max_amount': max(amounts),
                'confidence': 'high' if consistency > 0.6 else 'medium',
                'description': f'Gasto promedio ${avg_amount:.0f} con tendencia {trend}'
            }
            
        except Exception as e:
            logger.error(f"Error analizando patrón de montos: {e}")
            return None

    def _analyze_trends(self, customer_id: int) -> Dict[str, Any]:
        """Análisis de tendencias del cliente"""
        try:
            # Obtener ventas de los últimos 12 meses
            query = """
            SELECT strftime('%Y-%m', fecha_venta) as month,
                   COUNT(*) as purchase_count,
                   SUM(total) as total_spent,
                   AVG(total) as avg_purchase
            FROM ventas
            WHERE cliente_id = ? AND fecha_venta >= date('now', '-12 months')
            GROUP BY strftime('%Y-%m', fecha_venta)
            ORDER BY month
            """
            
            monthly_data = self.db_manager.execute_query(query, (customer_id,))
            if not monthly_data or len(monthly_data) < 3:
                return {'insufficient_data': True}
            
            # Analizar tendencias
            months = [row['month'] for row in monthly_data]
            purchase_counts = [row['purchase_count'] for row in monthly_data]
            total_amounts = [row['total_spent'] for row in monthly_data]
            avg_amounts = [row['avg_purchase'] for row in monthly_data]
            
            trends = {
                'data_points': len(monthly_data),
                'frequency_trend': self._calculate_trend(purchase_counts),
                'spending_trend': self._calculate_trend(total_amounts),
                'average_order_trend': self._calculate_trend(avg_amounts),
                'monthly_data': [
                    {
                        'month': month,
                        'purchases': count,
                        'total_spent': total,
                        'avg_purchase': avg
                    }
                    for month, count, total, avg in zip(months, purchase_counts, total_amounts, avg_amounts)
                ]
            }
            
            # Determinar tendencia general
            positive_trends = sum(1 for trend in [trends['frequency_trend']['direction'], 
                                                trends['spending_trend']['direction']] 
                                if trend == 'increasing')
            
            if positive_trends >= 2:
                trends['overall_trend'] = 'positive'
            elif positive_trends == 0:
                trends['overall_trend'] = 'negative'
            else:
                trends['overall_trend'] = 'mixed'
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analizando tendencias: {e}")
            return {'error': str(e)}

    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """Calcular tendencia de una serie de valores"""
        if len(values) < 2:
            return {'direction': 'insufficient_data', 'strength': 0}
        
        # Regresión lineal simple
        n = len(values)
        x = list(range(n))
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(xi * yi for xi, yi in zip(x, values))
        sum_x2 = sum(xi * xi for xi in x)
        
        # Calcular pendiente
        if n * sum_x2 - sum_x * sum_x == 0:
            slope = 0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Determinar dirección y fuerza
        avg_value = sum_y / n
        relative_slope = slope / avg_value if avg_value != 0 else 0
        
        if abs(relative_slope) < 0.05:
            direction = 'stable'
            strength = abs(relative_slope) * 20
        elif relative_slope > 0:
            direction = 'increasing'
            strength = min(relative_slope * 10, 1.0)
        else:
            direction = 'decreasing'
            strength = min(abs(relative_slope) * 10, 1.0)
        
        return {
            'direction': direction,
            'strength': round(strength, 2),
            'slope': round(slope, 4),
            'relative_change': round(relative_slope * 100, 1)
        }

    def _predict_churn(self, customer_id: int) -> Dict[str, Any]:
        """Predicción de abandono (churn) del cliente"""
        try:
            customer_data = self._get_customer_data(customer_id)
            if not customer_data:
                return {'error': 'No hay datos suficientes'}
            
            # Factores de churn
            factors = {}
            churn_score = 0
            
            # Factor 1: Días desde última compra
            days_since_last = customer_data.get('days_since_last', 0)
            if days_since_last > 90:
                factors['inactivity'] = 0.4
                churn_score += 0.4
            elif days_since_last > 60:
                factors['inactivity'] = 0.2
                churn_score += 0.2
            
            # Factor 2: Tendencia de compras decreciente
            trends = self._analyze_trends(customer_id)
            if trends.get('frequency_trend', {}).get('direction') == 'decreasing':
                factors['declining_frequency'] = 0.3
                churn_score += 0.3
            
            if trends.get('spending_trend', {}).get('direction') == 'decreasing':
                factors['declining_spending'] = 0.2
                churn_score += 0.2
            
            # Factor 3: Baja frecuencia histórica
            total_purchases = customer_data.get('total_purchases', 0)
            customer_lifespan = customer_data.get('customer_lifespan', 1)
            
            if customer_lifespan > 0:
                purchase_frequency = total_purchases / (customer_lifespan / 30)  # por mes
                if purchase_frequency < 0.5:  # menos de 0.5 compras por mes
                    factors['low_frequency'] = 0.15
                    churn_score += 0.15
            
            # Factor 4: Valor bajo del cliente
            avg_purchase = customer_data.get('avg_purchase', 0)
            if avg_purchase < 1000:  # threshold configurable
                factors['low_value'] = 0.1
                churn_score += 0.1
            
            # Normalizar score
            churn_score = min(churn_score, 1.0)
            
            # Determinar riesgo
            if churn_score >= 0.7:
                risk_level = 'high'
                recommendation = 'Contactar inmediatamente con oferta personalizada'
            elif churn_score >= 0.4:
                risk_level = 'medium'
                recommendation = 'Enviar campaña de re-engagement'
            else:
                risk_level = 'low'
                recommendation = 'Mantener comunicación regular'
            
            return {
                'churn_probability': round(churn_score, 2),
                'risk_level': risk_level,
                'factors': factors,
                'days_since_last_purchase': days_since_last,
                'recommendation': recommendation,
                'confidence': 'high' if total_purchases > 5 else 'medium'
            }
            
        except Exception as e:
            logger.error(f"Error prediciendo churn: {e}")
            return {'error': str(e)}

    def _classify_customer_segment(self, customer_id: int) -> Dict[str, Any]:
        """Clasificación automática del segmento del cliente"""
        try:
            customer_data = self._get_customer_data(customer_id)
            if not customer_data:
                return {'segment': 'unknown'}
            
            total_spent = customer_data.get('total_spent', 0)
            total_purchases = customer_data.get('total_purchases', 0)
            days_since_last = customer_data.get('days_since_last', 0)
            customer_lifespan = customer_data.get('customer_lifespan', 0)
            
            # Calcular métricas para segmentación
            if customer_lifespan > 0:
                purchase_frequency = total_purchases / (customer_lifespan / 30)
            else:
                purchase_frequency = 0
            
            # Aplicar reglas de segmentación
            segments = []
            
            # High Value
            if total_spent >= self.segment_definitions['high_value']['min_total'] and \
               total_purchases >= self.segment_definitions['high_value']['min_frequency']:
                segments.append(('high_value', 'Cliente de Alto Valor'))
            
            # Frequent
            if total_purchases >= self.segment_definitions['frequent']['min_frequency'] and \
               days_since_last <= self.segment_definitions['frequent']['max_days_since']:
                segments.append(('frequent', 'Cliente Frecuente'))
            
            # At Risk
            if days_since_last >= self.segment_definitions['at_risk']['days_since_last']:
                segments.append(('at_risk', 'Cliente en Riesgo'))
            
            # New
            if customer_lifespan <= self.segment_definitions['new']['registration_days'] and \
               total_purchases <= self.segment_definitions['new']['transaction_count']:
                segments.append(('new', 'Cliente Nuevo'))
            
            # Dormant
            if days_since_last >= self.segment_definitions['dormant']['days_since_last']:
                segments.append(('dormant', 'Cliente Inactivo'))
            
            # Seleccionar segmento principal
            if not segments:
                segments.append(('regular', 'Cliente Regular'))
            
            primary_segment = segments[0]
            
            return {
                'primary_segment': primary_segment[0],
                'segment_name': primary_segment[1],
                'all_segments': [seg[0] for seg in segments],
                'characteristics': {
                    'total_spent': total_spent,
                    'total_purchases': total_purchases,
                    'purchase_frequency': round(purchase_frequency, 2),
                    'days_since_last': days_since_last,
                    'avg_purchase': customer_data.get('avg_purchase', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error clasificando segmento: {e}")
            return {'segment': 'error', 'error': str(e)}

    def _predict_next_purchase(self, customer_id: int) -> Dict[str, Any]:
        """Predicción de próxima compra"""
        try:
            # Obtener patrón de frecuencia
            customer_data = self._get_customer_data(customer_id)
            patterns = self._analyze_purchase_patterns(customer_id)
            
            if not customer_data or not patterns:
                return {'prediction': 'insufficient_data'}
            
            # Buscar patrón de frecuencia
            frequency_pattern = None
            for pattern in patterns:
                if pattern['pattern_type'] == 'frequency':
                    frequency_pattern = pattern
                    break
            
            if not frequency_pattern:
                return {'prediction': 'no_pattern_detected'}
            
            # Calcular próxima fecha probable
            last_purchase_str = customer_data.get('last_purchase')
            if not last_purchase_str:
                return {'prediction': 'no_previous_purchases'}
            
            last_purchase = datetime.strptime(last_purchase_str, '%Y-%m-%d %H:%M:%S')
            avg_interval = frequency_pattern['avg_days_between_purchases']
            confidence = frequency_pattern['confidence']
            
            predicted_date = last_purchase + timedelta(days=avg_interval)
            days_until = (predicted_date - datetime.now()).days
            
            # Ajustar predicción basada en patrón estacional si existe
            seasonal_pattern = None
            for pattern in patterns:
                if pattern['pattern_type'] == 'seasonal':
                    seasonal_pattern = pattern
                    break
            
            seasonal_adjustment = 1.0
            if seasonal_pattern:
                current_month = datetime.now().month
                monthly_averages = seasonal_pattern['monthly_averages']
                if current_month in monthly_averages:
                    overall_avg = sum(monthly_averages.values()) / len(monthly_averages)
                    current_month_avg = monthly_averages[current_month]
                    seasonal_adjustment = current_month_avg / overall_avg if overall_avg > 0 else 1.0
            
            # Ajustar probabilidad
            base_probability = 0.8 if confidence == 'high' else 0.6 if confidence == 'medium' else 0.4
            final_probability = min(base_probability * seasonal_adjustment, 1.0)
            
            return {
                'predicted_date': predicted_date.strftime('%Y-%m-%d'),
                'days_until_prediction': days_until,
                'probability': round(final_probability, 2),
                'confidence': confidence,
                'based_on_pattern': frequency_pattern['frequency_type'],
                'seasonal_factor': round(seasonal_adjustment, 2) if seasonal_pattern else None,
                'recommendation': self._generate_next_purchase_recommendation(days_until, final_probability)
            }
            
        except Exception as e:
            logger.error(f"Error prediciendo próxima compra: {e}")
            return {'prediction': 'error', 'error': str(e)}

    def _generate_next_purchase_recommendation(self, days_until: int, probability: float) -> str:
        """Generar recomendación basada en predicción de compra"""
        if days_until < 0:
            return "Cliente debería haber comprado. Contactar para re-engagement."
        elif days_until <= 7:
            if probability > 0.7:
                return "Alta probabilidad de compra esta semana. Enviar oferta específica."
            else:
                return "Posible compra próximamente. Mantener visibilidad."
        elif days_until <= 30:
            return f"Compra esperada en {days_until} días. Preparar campaña dirigida."
        else:
            return "Compra a largo plazo. Mantener engagement regular."

    def _recommend_products(self, customer_id: int) -> List[Dict[str, Any]]:
        """Recomendación de productos basada en patrones"""
        try:
            # Obtener historial de productos del cliente
            query = """
            SELECT p.id, p.nombre, p.categoria, p.precio, 
                   SUM(dv.cantidad) as total_quantity,
                   COUNT(*) as purchase_frequency,
                   MAX(v.fecha_venta) as last_purchase
            FROM productos p
            JOIN detalle_venta dv ON p.id = dv.producto_id
            JOIN ventas v ON dv.venta_id = v.id
            WHERE v.cliente_id = ?
            GROUP BY p.id
            ORDER BY purchase_frequency DESC, last_purchase DESC
            """
            
            customer_products = self.db_manager.execute_query(query, (customer_id,))
            if not customer_products:
                return []
            
            # Obtener productos similares (misma categoría)
            categories = list(set(p['categoria'] for p in customer_products))
            
            similar_products_query = """
            SELECT p.id, p.nombre, p.categoria, p.precio,
                   COUNT(dv.venta_id) as popularity
            FROM productos p
            JOIN detalle_venta dv ON p.id = dv.producto_id
            WHERE p.categoria IN ({}) AND p.id NOT IN ({})
            GROUP BY p.id
            HAVING popularity >= 3
            ORDER BY popularity DESC
            LIMIT 10
            """.format(
                ','.join('?' * len(categories)),
                ','.join(str(p['id']) for p in customer_products)
            )
            
            params = categories
            similar_products = self.db_manager.execute_query(similar_products_query, params)
            
            # Calcular scores de recomendación
            recommendations = []
            
            # Productos de recompra (que ya compró antes)
            for product in customer_products[:3]:  # Top 3
                last_purchase = datetime.strptime(product['last_purchase'], '%Y-%m-%d %H:%M:%S')
                days_since = (datetime.now() - last_purchase).days
                
                # Score basado en frecuencia y recencia
                frequency_score = min(product['purchase_frequency'] / 5.0, 1.0)
                recency_score = max(0, 1.0 - days_since / 365.0)
                final_score = (frequency_score + recency_score) / 2
                
                recommendations.append({
                    'product_id': product['id'],
                    'product_name': product['nombre'],
                    'category': product['categoria'],
                    'price': product['precio'],
                    'recommendation_type': 'repurchase',
                    'score': round(final_score, 2),
                    'reason': f'Compró {product["purchase_frequency"]} veces anteriormente'
                })
            
            # Productos similares (nuevos)
            for product in similar_products[:2]:  # Top 2
                # Score basado en popularidad y categoría preferida
                popularity_score = min(product['popularity'] / 10.0, 1.0)
                category_preference = 0.7  # Asumimos preferencia por categorías ya compradas
                final_score = popularity_score * category_preference
                
                recommendations.append({
                    'product_id': product['id'],
                    'product_name': product['nombre'],
                    'category': product['categoria'],
                    'price': product['precio'],
                    'recommendation_type': 'cross_sell',
                    'score': round(final_score, 2),
                    'reason': f'Popular en {product["categoria"]} (categoría de interés)'
                })
            
            # Ordenar por score y retornar top 5
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            return recommendations[:5]
            
        except Exception as e:
            logger.error(f"Error recomendando productos: {e}")
            return []

    def _calculate_clv_prediction(self, customer_id: int) -> Dict[str, Any]:
        """Cálculo del valor de vida del cliente (CLV) predictivo"""
        try:
            customer_data = self._get_customer_data(customer_id)
            if not customer_data:
                return {'error': 'No hay datos suficientes'}
            
            total_spent = customer_data.get('total_spent', 0)
            total_purchases = customer_data.get('total_purchases', 0)
            customer_lifespan = customer_data.get('customer_lifespan', 0)
            
            if total_purchases == 0 or customer_lifespan == 0:
                return {'clv_prediction': 0, 'confidence': 'low'}
            
            # Métricas base
            avg_purchase_value = total_spent / total_purchases
            purchase_frequency = total_purchases / (customer_lifespan / 30)  # por mes
            
            # Predicción de retención (simplificada)
            days_since_last = customer_data.get('days_since_last', 0)
            retention_probability = max(0, 1.0 - days_since_last / 365.0)
            
            # Estimación de vida útil restante
            if purchase_frequency > 0:
                estimated_lifetime_months = min(24, 12 / max(0.1, 1.0 - retention_probability))
            else:
                estimated_lifetime_months = 6
            
            # Cálculo CLV
            predicted_clv = avg_purchase_value * purchase_frequency * estimated_lifetime_months * retention_probability
            
            # Análisis de tendencia para ajustar predicción
            trends = self._analyze_trends(customer_id)
            trend_multiplier = 1.0
            
            if trends.get('overall_trend') == 'positive':
                trend_multiplier = 1.2
            elif trends.get('overall_trend') == 'negative':
                trend_multiplier = 0.8
            
            final_clv = predicted_clv * trend_multiplier
            
            # Determinar confianza
            confidence = 'high' if total_purchases > 5 and customer_lifespan > 90 else 'medium' if total_purchases > 2 else 'low'
            
            return {
                'predicted_clv': round(final_clv, 2),
                'current_clv': total_spent,
                'avg_purchase_value': round(avg_purchase_value, 2),
                'purchase_frequency_monthly': round(purchase_frequency, 2),
                'retention_probability': round(retention_probability, 2),
                'estimated_lifetime_months': round(estimated_lifetime_months, 1),
                'trend_multiplier': trend_multiplier,
                'confidence': confidence,
                'segment_projection': self._classify_clv_segment(final_clv)
            }
            
        except Exception as e:
            logger.error(f"Error calculando CLV: {e}")
            return {'error': str(e)}

    def _classify_clv_segment(self, clv: float) -> str:
        """Clasificar cliente por CLV"""
        if clv >= 50000:
            return 'champion'
        elif clv >= 25000:
            return 'loyal'
        elif clv >= 10000:
            return 'potential'
        elif clv >= 5000:
            return 'new'
        else:
            return 'low_value'

    def _calculate_overall_confidence(self, customer_id: int) -> float:
        """Calcular score de confianza general del análisis"""
        try:
            customer_data = self._get_customer_data(customer_id)
            if not customer_data:
                return 0.0
            
            factors = []
            
            # Factor 1: Cantidad de transacciones
            transactions = customer_data.get('total_purchases', 0)
            if transactions >= 10:
                factors.append(1.0)
            elif transactions >= 5:
                factors.append(0.8)
            elif transactions >= 3:
                factors.append(0.6)
            else:
                factors.append(0.3)
            
            # Factor 2: Antigüedad como cliente
            lifespan = customer_data.get('customer_lifespan', 0)
            if lifespan >= 365:
                factors.append(1.0)
            elif lifespan >= 180:
                factors.append(0.8)
            elif lifespan >= 90:
                factors.append(0.6)
            else:
                factors.append(0.4)
            
            # Factor 3: Actividad reciente
            days_since_last = customer_data.get('days_since_last', 999)
            if days_since_last <= 30:
                factors.append(1.0)
            elif days_since_last <= 90:
                factors.append(0.7)
            elif days_since_last <= 180:
                factors.append(0.4)
            else:
                factors.append(0.2)
            
            return sum(factors) / len(factors)
            
        except Exception as e:
            logger.error(f"Error calculando confianza: {e}")
            return 0.0

    def get_segment_analysis(self) -> Dict[str, Any]:
        """Análisis completo de segmentos de clientes"""
        try:
            query = """
            SELECT c.id, c.nombre,
                   COUNT(v.id) as total_purchases,
                   COALESCE(SUM(v.total), 0) as total_spent,
                   COALESCE(AVG(v.total), 0) as avg_purchase,
                   MAX(v.fecha_venta) as last_purchase,
                   julianday('now') - julianday(MAX(v.fecha_venta)) as days_since_last,
                   julianday(MAX(v.fecha_venta)) - julianday(MIN(v.fecha_venta)) as customer_lifespan
            FROM clientes c
            LEFT JOIN ventas v ON c.id = v.cliente_id
            WHERE c.activo = 1
            GROUP BY c.id
            HAVING total_purchases > 0
            """
            
            customers = self.db_manager.execute_query(query)
            if not customers:
                return {'error': 'No hay datos de clientes'}
            
            # Clasificar todos los clientes
            segments = defaultdict(list)
            
            for customer in customers:
                segment_info = self._classify_customer_segment(customer['id'])
                segment_key = segment_info.get('primary_segment', 'unknown')
                segments[segment_key].append(customer)
            
            # Calcular estadísticas por segmento
            segment_stats = {}
            for segment, customer_list in segments.items():
                if not customer_list:
                    continue
                
                total_customers = len(customer_list)
                total_revenue = sum(c['total_spent'] for c in customer_list)
                avg_clv = total_revenue / total_customers
                avg_frequency = sum(c['total_purchases'] for c in customer_list) / total_customers
                avg_recency = sum(c['days_since_last'] or 0 for c in customer_list) / total_customers
                
                segment_stats[segment] = {
                    'name': self._get_segment_name(segment),
                    'customer_count': total_customers,
                    'percentage': round((total_customers / len(customers)) * 100, 1),
                    'total_revenue': total_revenue,
                    'avg_clv': round(avg_clv, 2),
                    'avg_frequency': round(avg_frequency, 1),
                    'avg_recency': round(avg_recency, 1),
                    'revenue_percentage': round((total_revenue / sum(c['total_spent'] for c in customers)) * 100, 1)
                }
            
            return {
                'total_customers_analyzed': len(customers),
                'segments': segment_stats,
                'analysis_date': datetime.now().isoformat(),
                'recommendations': self._generate_segment_recommendations(segment_stats)
            }
            
        except Exception as e:
            logger.error(f"Error en análisis de segmentos: {e}")
            return {'error': str(e)}

    def _get_segment_name(self, segment_key: str) -> str:
        """Obtener nombre descriptivo del segmento"""
        names = {
            'high_value': 'Clientes de Alto Valor',
            'frequent': 'Clientes Frecuentes',
            'at_risk': 'Clientes en Riesgo',
            'new': 'Clientes Nuevos',
            'dormant': 'Clientes Inactivos',
            'regular': 'Clientes Regulares',
            'unknown': 'Sin Clasificar'
        }
        return names.get(segment_key, segment_key.title())

    def _generate_segment_recommendations(self, segment_stats: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generar recomendaciones basadas en análisis de segmentos"""
        recommendations = []
        
        for segment, stats in segment_stats.items():
            if segment == 'high_value':
                if stats['customer_count'] > 0:
                    recommendations.append({
                        'segment': segment,
                        'priority': 'high',
                        'action': 'Programa VIP',
                        'description': f'{stats["customer_count"]} clientes de alto valor generan {stats["revenue_percentage"]}% de los ingresos. Implementar programa de fidelización exclusivo.'
                    })
            
            elif segment == 'at_risk':
                if stats['customer_count'] > 0:
                    recommendations.append({
                        'segment': segment,
                        'priority': 'urgent',
                        'action': 'Campaña de Retención',
                        'description': f'{stats["customer_count"]} clientes en riesgo ({stats["percentage"]}%). Contactar con ofertas personalizadas inmediatamente.'
                    })
            
            elif segment == 'dormant':
                if stats['customer_count'] > 0:
                    recommendations.append({
                        'segment': segment,
                        'priority': 'medium',
                        'action': 'Reactivación',
                        'description': f'{stats["customer_count"]} clientes inactivos. Implementar campaña de win-back con incentivos especiales.'
                    })
            
            elif segment == 'new':
                if stats['customer_count'] > 0:
                    recommendations.append({
                        'segment': segment,
                        'priority': 'high',
                        'action': 'Onboarding',
                        'description': f'{stats["customer_count"]} clientes nuevos. Desarrollar programa de bienvenida y educación sobre productos.'
                    })
        
        return recommendations

    def save_prediction(self, prediction: CustomerPrediction):
        """Guardar predicción en base de datos"""
        try:
            query = """
            INSERT INTO customer_predictions (
                customer_id, prediction_type, probability, confidence, 
                factors, recommendation, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                prediction.customer_id,
                prediction.prediction_type,
                prediction.probability,
                prediction.confidence,
                json.dumps(prediction.factors),
                prediction.recommendation,
                prediction.created_at.isoformat()
            )
            
            return self.db_manager.execute_query(query, params)
            
        except Exception as e:
            logger.error(f"Error guardando predicción: {e}")
            return False

    def get_predictions_history(self, customer_id: Optional[int] = None, days: int = 30) -> List[Dict[str, Any]]:
        """Obtener historial de predicciones"""
        try:
            base_query = """
            SELECT * FROM customer_predictions 
            WHERE created_at >= date('now', '-{} days')
            """.format(days)
            
            params = []
            if customer_id:
                base_query += " AND customer_id = ?"
                params.append(customer_id)
            
            base_query += " ORDER BY created_at DESC"
            
            results = self.db_manager.execute_query(base_query, params)
            
            # Convertir factores JSON a dict
            for result in results:
                if result.get('factors'):
                    result['factors'] = json.loads(result['factors'])
            
            return results
            
        except Exception as e:
            logger.error(f"Error obteniendo historial de predicciones: {e}")
            return []

    def create_prediction_tables(self):
        """Crear tablas necesarias para el análisis predictivo"""
        try:
            # Tabla de predicciones
            predictions_table = """
            CREATE TABLE IF NOT EXISTS customer_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                prediction_type TEXT NOT NULL,
                probability REAL NOT NULL,
                confidence TEXT NOT NULL,
                factors TEXT,
                recommendation TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES clientes (id)
            );
            """
            
            # Tabla de segmentos históricos
            segments_table = """
            CREATE TABLE IF NOT EXISTS customer_segments_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                segment_id TEXT NOT NULL,
                segment_name TEXT NOT NULL,
                characteristics TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES clientes (id)
            );
            """
            
            # Tabla de patrones detectados
            patterns_table = """
            CREATE TABLE IF NOT EXISTS customer_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                pattern_type TEXT NOT NULL,
                pattern_data TEXT NOT NULL,
                confidence REAL NOT NULL,
                detected_at TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES clientes (id)
            );
            """
            
            self.db_manager.execute_query(predictions_table)
            self.db_manager.execute_query(segments_table)
            self.db_manager.execute_query(patterns_table)
            
            return True
            
        except Exception as e:
            logger.error(f"Error creando tablas de análisis predictivo: {e}")
            return False