"""
Utilidades de Machine Learning - AlmacénPro v2.0
Funciones auxiliares para análisis predictivo y procesamiento de datos
"""

import math
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)

class DataPreprocessor:
    """Preprocesador de datos para análisis predictivo"""
    
    @staticmethod
    def normalize_values(values: List[float], method: str = 'min_max') -> List[float]:
        """Normalizar lista de valores"""
        if not values or len(values) == 0:
            return values
        
        if method == 'min_max':
            min_val = min(values)
            max_val = max(values)
            
            if max_val == min_val:
                return [0.5] * len(values)
            
            return [(val - min_val) / (max_val - min_val) for val in values]
        
        elif method == 'z_score':
            mean_val = sum(values) / len(values)
            std_dev = (sum((x - mean_val) ** 2 for x in values) / len(values)) ** 0.5
            
            if std_dev == 0:
                return [0.0] * len(values)
            
            return [(val - mean_val) / std_dev for val in values]
        
        return values
    
    @staticmethod
    def handle_outliers(values: List[float], method: str = 'iqr', factor: float = 1.5) -> List[float]:
        """Manejar valores atípicos"""
        if not values or len(values) < 4:
            return values
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        if method == 'iqr':
            q1_idx = n // 4
            q3_idx = 3 * n // 4
            
            q1 = sorted_values[q1_idx]
            q3 = sorted_values[q3_idx]
            iqr = q3 - q1
            
            lower_bound = q1 - factor * iqr
            upper_bound = q3 + factor * iqr
            
            # Reemplazar outliers con valores límite
            return [max(lower_bound, min(upper_bound, val)) for val in values]
        
        elif method == 'z_score':
            mean_val = sum(values) / len(values)
            std_dev = (sum((x - mean_val) ** 2 for x in values) / len(values)) ** 0.5
            
            if std_dev == 0:
                return values
            
            threshold = factor * std_dev
            return [val for val in values if abs(val - mean_val) <= threshold]
        
        return values
    
    @staticmethod
    def create_time_features(dates: List[datetime]) -> Dict[str, List[int]]:
        """Crear características temporales a partir de fechas"""
        features = {
            'year': [],
            'month': [],
            'day': [],
            'weekday': [],
            'quarter': [],
            'is_weekend': [],
            'days_since_epoch': []
        }
        
        epoch = datetime(1970, 1, 1)
        
        for date in dates:
            features['year'].append(date.year)
            features['month'].append(date.month)
            features['day'].append(date.day)
            features['weekday'].append(date.weekday())
            features['quarter'].append((date.month - 1) // 3 + 1)
            features['is_weekend'].append(1 if date.weekday() >= 5 else 0)
            features['days_since_epoch'].append((date - epoch).days)
        
        return features
    
    @staticmethod
    def create_lag_features(values: List[float], lags: List[int]) -> Dict[str, List[Optional[float]]]:
        """Crear características con rezago temporal"""
        lag_features = {}
        
        for lag in lags:
            lag_name = f'lag_{lag}'
            lag_values = [None] * lag + values[:-lag] if lag < len(values) else [None] * len(values)
            lag_features[lag_name] = lag_values
        
        return lag_features

class FeatureEngineer:
    """Ingeniero de características para modelos predictivos"""
    
    @staticmethod
    def calculate_rfm_scores(customer_data: Dict[str, Any]) -> Dict[str, float]:
        """Calcular puntuaciones RFM (Recency, Frequency, Monetary)"""
        try:
            # Recency (días desde última compra)
            days_since_last = customer_data.get('days_since_last', 999)
            recency_score = max(0, 1.0 - min(days_since_last / 365, 1.0))
            
            # Frequency (número de transacciones)
            total_purchases = customer_data.get('total_purchases', 0)
            # Normalizar frequency (asumiendo máximo razonable de 50 compras)
            frequency_score = min(total_purchases / 50.0, 1.0)
            
            # Monetary (valor total gastado)
            total_spent = customer_data.get('total_spent', 0)
            # Normalizar monetary (asumiendo máximo razonable de 100,000)
            monetary_score = min(total_spent / 100000.0, 1.0)
            
            return {
                'recency': recency_score,
                'frequency': frequency_score,
                'monetary': monetary_score,
                'rfm_combined': (recency_score + frequency_score + monetary_score) / 3
            }
            
        except Exception as e:
            logger.error(f"Error calculando RFM: {e}")
            return {'recency': 0, 'frequency': 0, 'monetary': 0, 'rfm_combined': 0}
    
    @staticmethod
    def calculate_cohort_features(customer_data: Dict[str, Any], cohort_period: str = 'month') -> Dict[str, Any]:
        """Calcular características de cohorte"""
        try:
            first_purchase = customer_data.get('first_purchase')
            if not first_purchase:
                return {'cohort': 'unknown', 'periods_active': 0}
            
            first_date = datetime.strptime(first_purchase, '%Y-%m-%d %H:%M:%S')
            current_date = datetime.now()
            
            if cohort_period == 'month':
                cohort = f"{first_date.year}-{first_date.month:02d}"
                periods_active = (current_date.year - first_date.year) * 12 + (current_date.month - first_date.month)
            elif cohort_period == 'quarter':
                quarter = (first_date.month - 1) // 3 + 1
                cohort = f"{first_date.year}-Q{quarter}"
                current_quarter = (current_date.month - 1) // 3 + 1
                periods_active = (current_date.year - first_date.year) * 4 + (current_quarter - quarter)
            else:  # year
                cohort = str(first_date.year)
                periods_active = current_date.year - first_date.year
            
            return {
                'cohort': cohort,
                'periods_active': max(0, periods_active),
                'cohort_age_days': (current_date - first_date).days
            }
            
        except Exception as e:
            logger.error(f"Error calculando cohorte: {e}")
            return {'cohort': 'unknown', 'periods_active': 0, 'cohort_age_days': 0}
    
    @staticmethod
    def calculate_behavioral_features(purchases: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calcular características comportamentales"""
        try:
            if not purchases:
                return {
                    'avg_days_between_purchases': 0,
                    'purchase_variance': 0,
                    'trend_slope': 0,
                    'seasonality_strength': 0,
                    'preferred_weekday': 0,
                    'consistency_score': 0
                }
            
            # Calcular intervalos entre compras
            dates = sorted([datetime.strptime(p['fecha_venta'], '%Y-%m-%d %H:%M:%S') for p in purchases])
            intervals = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))] if len(dates) > 1 else [0]
            
            avg_interval = sum(intervals) / len(intervals) if intervals else 0
            interval_variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals) if intervals else 0
            
            # Calcular tendencia de montos
            amounts = [float(p['total']) for p in purchases]
            trend_slope = FeatureEngineer._calculate_trend_slope(amounts)
            
            # Calcular estacionalidad
            seasonality = FeatureEngineer._calculate_seasonality(dates)
            
            # Día de la semana preferido
            weekdays = [d.weekday() for d in dates]
            preferred_weekday = Counter(weekdays).most_common(1)[0][0] if weekdays else 0
            
            # Score de consistencia (inverso de la varianza normalizada)
            consistency = 1.0 - min(interval_variance / (avg_interval ** 2), 1.0) if avg_interval > 0 else 0
            
            return {
                'avg_days_between_purchases': avg_interval,
                'purchase_variance': interval_variance,
                'trend_slope': trend_slope,
                'seasonality_strength': seasonality,
                'preferred_weekday': preferred_weekday,
                'consistency_score': max(0, consistency)
            }
            
        except Exception as e:
            logger.error(f"Error calculando características comportamentales: {e}")
            return {
                'avg_days_between_purchases': 0, 'purchase_variance': 0,
                'trend_slope': 0, 'seasonality_strength': 0,
                'preferred_weekday': 0, 'consistency_score': 0
            }
    
    @staticmethod
    def _calculate_trend_slope(values: List[float]) -> float:
        """Calcular pendiente de tendencia usando regresión lineal simple"""
        if len(values) < 2:
            return 0.0
        
        n = len(values)
        x = list(range(n))
        
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(xi * yi for xi, yi in zip(x, values))
        sum_x2 = sum(xi * xi for xi in x)
        
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope
    
    @staticmethod
    def _calculate_seasonality(dates: List[datetime]) -> float:
        """Calcular fuerza de la estacionalidad"""
        if len(dates) < 12:  # Necesario para detectar estacionalidad anual
            return 0.0
        
        # Agrupar por mes
        monthly_counts = defaultdict(int)
        for date in dates:
            monthly_counts[date.month] += 1
        
        # Calcular coeficiente de variación
        counts = list(monthly_counts.values())
        if not counts:
            return 0.0
        
        mean_count = sum(counts) / len(counts)
        variance = sum((c - mean_count) ** 2 for c in counts) / len(counts)
        
        if mean_count == 0:
            return 0.0
        
        coefficient_of_variation = (variance ** 0.5) / mean_count
        return min(coefficient_of_variation, 1.0)

class SimpleMLModels:
    """Modelos de machine learning simplificados"""
    
    @staticmethod
    def naive_bayes_churn(features: Dict[str, float], prior_churn_rate: float = 0.2) -> Tuple[float, Dict[str, float]]:
        """Predicción de churn usando Naive Bayes simplificado"""
        try:
            # Pesos empíricos basados en importancia de features
            feature_weights = {
                'recency': 0.4,  # Más importante
                'frequency': 0.25,
                'monetary': 0.15,
                'consistency_score': 0.2
            }
            
            # Calcular probabilidad de churn
            churn_score = 0.0
            feature_contributions = {}
            
            for feature, weight in feature_weights.items():
                if feature in features:
                    # Invertir recency y consistency (menores valores = mayor churn)
                    if feature in ['recency', 'consistency_score']:
                        contribution = (1.0 - features[feature]) * weight
                    else:
                        # Para frequency y monetary, menores valores = mayor churn
                        contribution = (1.0 - features[feature]) * weight
                    
                    churn_score += contribution
                    feature_contributions[feature] = contribution
            
            # Ajustar con prior
            final_probability = (churn_score + prior_churn_rate) / 2
            final_probability = max(0.0, min(1.0, final_probability))
            
            return final_probability, feature_contributions
            
        except Exception as e:
            logger.error(f"Error en predicción Naive Bayes: {e}")
            return 0.5, {}
    
    @staticmethod
    def linear_regression_clv(features: Dict[str, float], historical_clv: float = 0) -> float:
        """Predicción de CLV usando regresión lineal simplificada"""
        try:
            # Coeficientes empíricos
            coefficients = {
                'frequency': 2000,    # Cada compra adicional vale $2000
                'monetary': 0.5,      # 50% del gasto histórico se proyecta
                'recency': 5000,      # Clientes recientes valen más
                'consistency_score': 3000,  # Consistencia es valiosa
                'rfm_combined': 4000  # Score general
            }
            
            predicted_clv = historical_clv * 0.3  # Base del CLV histórico
            
            for feature, coefficient in coefficients.items():
                if feature in features:
                    predicted_clv += features[feature] * coefficient
            
            # Aplicar límites razonables
            predicted_clv = max(0, min(predicted_clv, 200000))
            
            return predicted_clv
            
        except Exception as e:
            logger.error(f"Error en predicción CLV: {e}")
            return historical_clv or 1000
    
    @staticmethod
    def k_means_segmentation(customers_features: List[Dict[str, float]], k: int = 5) -> List[int]:
        """Segmentación K-means simplificada"""
        try:
            if len(customers_features) < k:
                return list(range(len(customers_features)))
            
            # Características principales para clustering
            main_features = ['recency', 'frequency', 'monetary']
            
            # Extraer vectores de características
            vectors = []
            for customer in customers_features:
                vector = [customer.get(feat, 0) for feat in main_features]
                vectors.append(vector)
            
            # Inicializar centroides aleatoriamente
            import random
            centroids = []
            for _ in range(k):
                centroid = [random.uniform(0, 1) for _ in main_features]
                centroids.append(centroid)
            
            # Algoritmo K-means (versión simplificada)
            assignments = [0] * len(vectors)
            
            for iteration in range(10):  # Máximo 10 iteraciones
                # Asignar puntos a centroides más cercanos
                new_assignments = []
                for vector in vectors:
                    distances = [SimpleMLModels._euclidean_distance(vector, centroid) 
                               for centroid in centroids]
                    closest = distances.index(min(distances))
                    new_assignments.append(closest)
                
                # Verificar convergencia
                if new_assignments == assignments:
                    break
                
                assignments = new_assignments
                
                # Actualizar centroides
                for cluster_id in range(k):
                    cluster_points = [vectors[i] for i, assignment in enumerate(assignments) 
                                    if assignment == cluster_id]
                    
                    if cluster_points:
                        new_centroid = []
                        for feat_idx in range(len(main_features)):
                            avg_value = sum(point[feat_idx] for point in cluster_points) / len(cluster_points)
                            new_centroid.append(avg_value)
                        centroids[cluster_id] = new_centroid
            
            return assignments
            
        except Exception as e:
            logger.error(f"Error en K-means: {e}")
            # Fallback: asignación secuencial
            return [i % k for i in range(len(customers_features))]
    
    @staticmethod
    def _euclidean_distance(point1: List[float], point2: List[float]) -> float:
        """Calcular distancia euclidiana entre dos puntos"""
        return sum((a - b) ** 2 for a, b in zip(point1, point2)) ** 0.5

class PredictionValidator:
    """Validador de predicciones y modelos"""
    
    @staticmethod
    def validate_churn_prediction(prediction: float, customer_features: Dict[str, float]) -> Dict[str, Any]:
        """Validar predicción de churn"""
        validation = {
            'is_valid': True,
            'confidence': 'high',
            'warnings': []
        }
        
        try:
            # Verificar rango de predicción
            if not (0 <= prediction <= 1):
                validation['is_valid'] = False
                validation['warnings'].append("Predicción fuera del rango [0,1]")
            
            # Verificar coherencia con features
            recency = customer_features.get('recency', 0.5)
            frequency = customer_features.get('frequency', 0.5)
            
            # Si recency es muy baja (cliente inactivo) pero predicción es muy baja, es sospechoso
            if recency < 0.2 and prediction < 0.3:
                validation['confidence'] = 'low'
                validation['warnings'].append("Predicción posiblemente muy optimista para cliente inactivo")
            
            # Si frequency es alta pero predicción es alta, es sospechoso
            if frequency > 0.8 and prediction > 0.7:
                validation['confidence'] = 'medium'
                validation['warnings'].append("Cliente frecuente con alta predicción de churn")
            
            # Evaluar confianza basada en cantidad de features
            available_features = sum(1 for v in customer_features.values() if v is not None)
            if available_features < 3:
                validation['confidence'] = 'low'
                validation['warnings'].append("Pocas características disponibles para predicción confiable")
            
        except Exception as e:
            logger.error(f"Error validando predicción de churn: {e}")
            validation['is_valid'] = False
            validation['warnings'].append(f"Error en validación: {e}")
        
        return validation
    
    @staticmethod
    def validate_clv_prediction(predicted_clv: float, historical_clv: float, customer_features: Dict[str, float]) -> Dict[str, Any]:
        """Validar predicción de CLV"""
        validation = {
            'is_valid': True,
            'confidence': 'high',
            'warnings': []
        }
        
        try:
            # Verificar valores negativos
            if predicted_clv < 0:
                validation['is_valid'] = False
                validation['warnings'].append("CLV predicho no puede ser negativo")
            
            # Verificar valores extremos
            if predicted_clv > historical_clv * 10 and historical_clv > 0:
                validation['confidence'] = 'low'
                validation['warnings'].append("CLV predicho excesivamente alto comparado con histórico")
            
            if predicted_clv < historical_clv * 0.1 and historical_clv > 1000:
                validation['confidence'] = 'low'
                validation['warnings'].append("CLV predicho excesivamente bajo comparado con histórico")
            
            # Verificar coherencia con monetary
            monetary = customer_features.get('monetary', 0)
            if monetary > 0.8 and predicted_clv < historical_clv:
                validation['warnings'].append("Cliente de alto valor con CLV predicho menor al histórico")
            
        except Exception as e:
            logger.error(f"Error validando predicción de CLV: {e}")
            validation['is_valid'] = False
            validation['warnings'].append(f"Error en validación: {e}")
        
        return validation
    
    @staticmethod
    def calculate_prediction_confidence(features: Dict[str, float], prediction_type: str) -> float:
        """Calcular confianza de predicción"""
        try:
            base_confidence = 0.5
            
            # Factores que aumentan confianza
            confidence_factors = []
            
            # Cantidad de features disponibles
            available_features = sum(1 for v in features.values() if v is not None)
            feature_confidence = min(available_features / 6.0, 1.0)  # Máximo 6 features principales
            confidence_factors.append(feature_confidence)
            
            # Coherencia entre features
            if prediction_type == 'churn':
                recency = features.get('recency', 0.5)
                frequency = features.get('frequency', 0.5)
                # Features coherentes aumentan confianza
                coherence = 1.0 - abs(recency - frequency)
                confidence_factors.append(coherence)
            
            elif prediction_type == 'clv':
                monetary = features.get('monetary', 0.5)
                frequency = features.get('frequency', 0.5)
                # Correlación positiva entre monetary y frequency
                coherence = 1.0 - abs(monetary - frequency) / 2
                confidence_factors.append(coherence)
            
            # Calcular confianza final
            final_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else base_confidence
            return max(0.1, min(1.0, final_confidence))
            
        except Exception as e:
            logger.error(f"Error calculando confianza: {e}")
            return 0.5

class ModelEvaluator:
    """Evaluador de rendimiento de modelos"""
    
    @staticmethod
    def calculate_model_metrics(predictions: List[float], actuals: List[float], model_type: str) -> Dict[str, float]:
        """Calcular métricas de evaluación del modelo"""
        try:
            if len(predictions) != len(actuals) or len(predictions) == 0:
                return {'error': 'Datos de predicción y reales no coinciden'}
            
            metrics = {}
            
            if model_type == 'regression':
                # Métricas para regresión (CLV)
                metrics['mae'] = ModelEvaluator._mean_absolute_error(predictions, actuals)
                metrics['mse'] = ModelEvaluator._mean_squared_error(predictions, actuals)
                metrics['rmse'] = metrics['mse'] ** 0.5
                metrics['r2'] = ModelEvaluator._r_squared(predictions, actuals)
                
            elif model_type == 'classification':
                # Métricas para clasificación (Churn)
                # Convertir probabilidades a predicciones binarias
                binary_predictions = [1 if p >= 0.5 else 0 for p in predictions]
                binary_actuals = [1 if a >= 0.5 else 0 for a in actuals]
                
                metrics['accuracy'] = ModelEvaluator._accuracy(binary_predictions, binary_actuals)
                metrics['precision'] = ModelEvaluator._precision(binary_predictions, binary_actuals)
                metrics['recall'] = ModelEvaluator._recall(binary_predictions, binary_actuals)
                metrics['f1'] = ModelEvaluator._f1_score(metrics['precision'], metrics['recall'])
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculando métricas: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def _mean_absolute_error(predictions: List[float], actuals: List[float]) -> float:
        """Mean Absolute Error"""
        return sum(abs(p - a) for p, a in zip(predictions, actuals)) / len(predictions)
    
    @staticmethod
    def _mean_squared_error(predictions: List[float], actuals: List[float]) -> float:
        """Mean Squared Error"""
        return sum((p - a) ** 2 for p, a in zip(predictions, actuals)) / len(predictions)
    
    @staticmethod
    def _r_squared(predictions: List[float], actuals: List[float]) -> float:
        """R-squared (coeficiente de determinación)"""
        mean_actual = sum(actuals) / len(actuals)
        
        ss_res = sum((a - p) ** 2 for a, p in zip(actuals, predictions))
        ss_tot = sum((a - mean_actual) ** 2 for a in actuals)
        
        if ss_tot == 0:
            return 1.0 if ss_res == 0 else 0.0
        
        return 1 - (ss_res / ss_tot)
    
    @staticmethod
    def _accuracy(predictions: List[int], actuals: List[int]) -> float:
        """Accuracy para clasificación"""
        if len(predictions) == 0:
            return 0.0
        return sum(p == a for p, a in zip(predictions, actuals)) / len(predictions)
    
    @staticmethod
    def _precision(predictions: List[int], actuals: List[int]) -> float:
        """Precision para clasificación"""
        tp = sum(p == 1 and a == 1 for p, a in zip(predictions, actuals))
        fp = sum(p == 1 and a == 0 for p, a in zip(predictions, actuals))
        
        if tp + fp == 0:
            return 0.0
        return tp / (tp + fp)
    
    @staticmethod
    def _recall(predictions: List[int], actuals: List[int]) -> float:
        """Recall para clasificación"""
        tp = sum(p == 1 and a == 1 for p, a in zip(predictions, actuals))
        fn = sum(p == 0 and a == 1 for p, a in zip(predictions, actuals))
        
        if tp + fn == 0:
            return 0.0
        return tp / (tp + fn)
    
    @staticmethod
    def _f1_score(precision: float, recall: float) -> float:
        """F1-score"""
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)

# Funciones de utilidad adicionales
def calculate_confidence_interval(values: List[float], confidence_level: float = 0.95) -> Tuple[float, float]:
    """Calcular intervalo de confianza"""
    try:
        if not values or len(values) < 2:
            return 0.0, 0.0
        
        mean_val = sum(values) / len(values)
        std_err = (sum((x - mean_val) ** 2 for x in values) / (len(values) - 1)) ** 0.5
        
        # Usar distribución t simplificada (aproximación)
        t_value = 2.0 if confidence_level >= 0.95 else 1.65
        margin_error = t_value * std_err / (len(values) ** 0.5)
        
        return mean_val - margin_error, mean_val + margin_error
        
    except Exception as e:
        logger.error(f"Error calculando intervalo de confianza: {e}")
        return 0.0, 0.0

def detect_anomalies(values: List[float], threshold: float = 2.0) -> List[bool]:
    """Detectar anomalías usando Z-score"""
    try:
        if len(values) < 3:
            return [False] * len(values)
        
        mean_val = sum(values) / len(values)
        std_dev = (sum((x - mean_val) ** 2 for x in values) / len(values)) ** 0.5
        
        if std_dev == 0:
            return [False] * len(values)
        
        return [abs(val - mean_val) / std_dev > threshold for val in values]
        
    except Exception as e:
        logger.error(f"Error detectando anomalías: {e}")
        return [False] * len(values)

def smooth_time_series(values: List[float], window_size: int = 3) -> List[float]:
    """Suavizar serie temporal usando media móvil"""
    try:
        if len(values) < window_size:
            return values
        
        smoothed = []
        half_window = window_size // 2
        
        for i in range(len(values)):
            start_idx = max(0, i - half_window)
            end_idx = min(len(values), i + half_window + 1)
            
            window_values = values[start_idx:end_idx]
            smoothed_value = sum(window_values) / len(window_values)
            smoothed.append(smoothed_value)
        
        return smoothed
        
    except Exception as e:
        logger.error(f"Error suavizando serie temporal: {e}")
        return values