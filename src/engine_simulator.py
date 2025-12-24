"""
PoseidonEye - Engine Simulator
Simulates real-time marine engine sensor data and publishes via MQTT.
"""

import time
import random
import json
from datetime import datetime
import paho.mqtt.client as mqtt


class MarineEngineSimulator:
    """Simulates a marine diesel engine with realistic sensor data."""
    
    def __init__(self, broker_host="localhost", broker_port=1883):
        self.client = mqtt.Client("PoseidonEye_Simulator")
        self.broker_host = broker_host
        self.broker_port = broker_port
        
        # Normal operating parameters
        self.base_exhaust_temp = 380  # °C
        self.base_lube_oil_pressure = 3.5  # bar
        self.base_bearing_temp = 70  # °C
        self.base_vibration = 4.5  # mm/s
        
        # Anomaly simulation flags
        self.inject_anomaly = False
        self.anomaly_type = None
        
    def connect(self):
        """Connect to MQTT broker."""
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            print(f"✓ MQTT Broker'a bağlanıldı: {self.broker_host}:{self.broker_port}")
            return True
        except Exception as e:
            print(f"✗ MQTT Bağlantı Hatası: {e}")
            return False
    
    def generate_sensor_data(self):
        """Generate realistic sensor readings with optional anomalies."""
        
        # Normal variation (±5%)
        exhaust_temp = self.base_exhaust_temp + random.uniform(-20, 20)
        lube_oil_pressure = self.base_lube_oil_pressure + random.uniform(-0.2, 0.2)
        bearing_temp = self.base_bearing_temp + random.uniform(-5, 5)
        vibration = self.base_vibration + random.uniform(-0.5, 0.5)
        
        # Inject anomalies if flagged
        if self.inject_anomaly:
            if self.anomaly_type == "overheating":
                exhaust_temp += random.uniform(50, 100)
                bearing_temp += random.uniform(15, 30)
            elif self.anomaly_type == "low_pressure":
                lube_oil_pressure -= random.uniform(1.0, 1.5)
            elif self.anomaly_type == "high_vibration":
                vibration += random.uniform(5, 10)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "exhaust_gas_temp_c": round(exhaust_temp, 2),
            "lube_oil_pressure_bar": round(lube_oil_pressure, 2),
            "main_bearing_temp_c": round(bearing_temp, 2),
            "vibration_rms_mm_s": round(vibration, 2),
            "engine_rpm": random.randint(720, 750),
            "fuel_consumption_l_h": round(random.uniform(180, 220), 2)
        }
    
    def publish_data(self, topic="poseidoneye/engine/sensors"):
        """Publish sensor data to MQTT topic."""
        data = self.generate_sensor_data()
        payload = json.dumps(data)
        self.client.publish(topic, payload)
        
        # Console output with color coding
        status = "⚠️ ANOMALY" if self.inject_anomaly else "✓ NORMAL"
        print(f"[{data['timestamp']}] {status} | "
              f"Exhaust: {data['exhaust_gas_temp_c']}°C | "
              f"Oil Pressure: {data['lube_oil_pressure_bar']} bar | "
              f"Vibration: {data['vibration_rms_mm_s']} mm/s")
        
        return data
    
    def run(self, interval=2, duration=None):
        """Run continuous simulation."""
        if not self.connect():
            return
        
        print("\n" + "="*80)
        print("🚢 POSEIDONEYE ENGINE SIMULATOR - BAŞLATILDI")
        print("="*80 + "\n")
        
        start_time = time.time()
        iteration = 0
        
        try:
            while True:
                # Randomly inject anomalies (10% chance every 30 seconds)
                if iteration % 15 == 0 and random.random() < 0.1:
                    self.inject_anomaly = True
                    self.anomaly_type = random.choice(["overheating", "low_pressure", "high_vibration"])
                    print(f"\n⚠️  ANOMALY INJECTED: {self.anomaly_type.upper()}\n")
                elif iteration % 15 == 0:
                    self.inject_anomaly = False
                
                self.publish_data()
                time.sleep(interval)
                iteration += 1
                
                # Check duration limit
                if duration and (time.time() - start_time) >= duration:
                    break
                    
        except KeyboardInterrupt:
            print("\n\n🛑 Simülatör durduruldu.")
        finally:
            self.client.disconnect()


if __name__ == "__main__":
    simulator = MarineEngineSimulator()
    simulator.run(interval=2)  # Publish every 2 seconds
