"""
PoseidonEye - AI Perception Core
Anomaly detection and RUL prediction for marine engines.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import json
from datetime import datetime, timedelta


class PerceptionCore:
    """AI-powered anomaly detection and predictive maintenance engine."""
    
    def __init__(self, contamination=0.1):
        """
        Initialize the perception core.
        
        Args:
            contamination: Expected proportion of anomalies in the dataset (default: 10%)
        """
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_columns = [
            'exhaust_gas_temp_c',
            'lube_oil_pressure_bar',
            'main_bearing_temp_c',
            'vibration_rms_mm_s'
        ]
        
        # Critical thresholds
        self.thresholds = {
            'exhaust_gas_temp_c': 450,
            'lube_oil_pressure_bar': 2.5,
            'main_bearing_temp_c': 85,
            'vibration_rms_mm_s': 10
        }
    
    def train(self, training_data):
        """
        Train the anomaly detection model on historical normal data.
        
        Args:
            training_data: DataFrame with sensor readings
        """
        X = training_data[self.feature_columns].values
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_trained = True
        print("✓ Perception Core eğitildi.")
    
    def predict_anomaly(self, sensor_data):
        """
        Predict if current sensor readings indicate an anomaly.
        
        Args:
            sensor_data: Dict or DataFrame row with sensor readings
            
        Returns:
            dict: Prediction results with anomaly score and classification
        """
        if not self.is_trained:
            raise ValueError("Model henüz eğitilmedi. Önce train() metodunu çağırın.")
        
        # Convert to DataFrame if dict
        if isinstance(sensor_data, dict):
            df = pd.DataFrame([sensor_data])
        else:
            df = sensor_data
        
        X = df[self.feature_columns].values
        X_scaled = self.scaler.transform(X)
        
        # Predict (-1 for anomaly, 1 for normal)
        prediction = self.model.predict(X_scaled)[0]
        anomaly_score = self.model.score_samples(X_scaled)[0]
        
        # Check threshold violations
        threshold_violations = []
        for param, threshold in self.thresholds.items():
            value = sensor_data.get(param, 0)
            if param == 'lube_oil_pressure_bar':
                if value < threshold:
                    threshold_violations.append(f"{param}: {value} < {threshold}")
            else:
                if value > threshold:
                    threshold_violations.append(f"{param}: {value} > {threshold}")
        
        return {
            'is_anomaly': prediction == -1,
            'anomaly_score': float(anomaly_score),
            'confidence': abs(anomaly_score),
            'threshold_violations': threshold_violations,
            'severity': self._calculate_severity(anomaly_score, threshold_violations),
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_severity(self, anomaly_score, violations):
        """Calculate severity level based on score and violations."""
        if len(violations) >= 2 or anomaly_score < -0.5:
            return "CRITICAL"
        elif len(violations) == 1 or anomaly_score < -0.3:
            return "WARNING"
        else:
            return "NORMAL"
    
    def estimate_rul(self, sensor_data, component='main_bearing'):
        """
        Estimate Remaining Useful Life (RUL) for a component.
        
        Args:
            sensor_data: Current sensor readings
            component: Component to estimate RUL for
            
        Returns:
            dict: RUL estimation in hours
        """
        # Simplified RUL calculation based on degradation rate
        # In production, this would use more sophisticated models (LSTM, etc.)
        
        if component == 'main_bearing':
            temp = sensor_data.get('main_bearing_temp_c', 70)
            vibration = sensor_data.get('vibration_rms_mm_s', 4.5)
            
            # Calculate degradation factor (0-1, higher = more degraded)
            temp_factor = max(0, (temp - 70) / 30)  # Normal: 70°C, Critical: 100°C
            vib_factor = max(0, (vibration - 4.5) / 10)  # Normal: 4.5, Critical: 14.5
            degradation = (temp_factor + vib_factor) / 2
            
            # Base RUL: 10,000 hours for new bearing
            base_rul = 10000
            rul_hours = base_rul * (1 - degradation)
            
            return {
                'component': component,
                'rul_hours': max(0, int(rul_hours)),
                'rul_days': max(0, int(rul_hours / 24)),
                'degradation_percentage': round(degradation * 100, 2),
                'recommended_action': self._get_maintenance_recommendation(rul_hours)
            }
    
    def _get_maintenance_recommendation(self, rul_hours):
        """Get maintenance recommendation based on RUL."""
        if rul_hours < 100:
            return "IMMEDIATE REPLACEMENT REQUIRED"
        elif rul_hours < 500:
            return "Schedule maintenance within 1 week"
        elif rul_hours < 2000:
            return "Monitor closely, plan maintenance"
        else:
            return "Normal operation"
    
    def save_model(self, filepath='models/perception_core.pkl'):
        """Save trained model to disk."""
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns
        }, filepath)
        print(f"✓ Model kaydedildi: {filepath}")
    
    def load_model(self, filepath='models/perception_core.pkl'):
        """Load trained model from disk."""
        data = joblib.load(filepath)
        self.model = data['model']
        self.scaler = data['scaler']
        self.feature_columns = data['feature_columns']
        self.is_trained = True
        print(f"✓ Model yüklendi: {filepath}")


def generate_training_data(n_samples=1000):
    """Generate synthetic training data for initial model training."""
    np.random.seed(42)
    
    data = {
        'exhaust_gas_temp_c': np.random.normal(380, 15, n_samples),
        'lube_oil_pressure_bar': np.random.normal(3.5, 0.15, n_samples),
        'main_bearing_temp_c': np.random.normal(70, 4, n_samples),
        'vibration_rms_mm_s': np.random.normal(4.5, 0.4, n_samples)
    }
    
    return pd.DataFrame(data)


if __name__ == "__main__":
    # Example usage
    print("🧠 PoseidonEye Perception Core - Test")
    print("="*50)
    
    # Generate and train on synthetic data
    training_data = generate_training_data(1000)
    core = PerceptionCore()
    core.train(training_data)
    
    # Test with normal data
    normal_data = {
        'exhaust_gas_temp_c': 385,
        'lube_oil_pressure_bar': 3.4,
        'main_bearing_temp_c': 72,
        'vibration_rms_mm_s': 4.7
    }
    
    result = core.predict_anomaly(normal_data)
    print(f"\n✓ Normal Data Test: {result}")
    
    # Test with anomalous data
    anomaly_data = {
        'exhaust_gas_temp_c': 480,
        'lube_oil_pressure_bar': 2.1,
        'main_bearing_temp_c': 95,
        'vibration_rms_mm_s': 12.5
    }
    
    result = core.predict_anomaly(anomaly_data)
    print(f"\n⚠️  Anomaly Data Test: {result}")
    
    # RUL estimation
    rul = core.estimate_rul(anomaly_data)
    print(f"\n🔧 RUL Estimation: {rul}")
