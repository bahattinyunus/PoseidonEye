"""
PoseidonEye - Real-time Dashboard
Streamlit-based monitoring interface for marine engine health.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import paho.mqtt.client as mqtt
import json
from datetime import datetime
import time
from collections import deque
from perception_core import PerceptionCore, generate_training_data


# Page configuration
st.set_page_config(
    page_title="PoseidonEye Command Center",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium look
st.markdown("""
<style>
    .main {
        background-color: #0a0e27;
    }
    .stMetric {
        background-color: #1a1f3a;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #00d4ff;
    }
    h1 {
        color: #00d4ff;
        text-shadow: 0 0 10px #00d4ff;
    }
    .alert-critical {
        background-color: #ff3366;
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .alert-warning {
        background-color: #ffaa00;
        color: black;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = {
        'timestamps': deque(maxlen=50),
        'exhaust_temp': deque(maxlen=50),
        'oil_pressure': deque(maxlen=50),
        'bearing_temp': deque(maxlen=50),
        'vibration': deque(maxlen=50)
    }

if 'perception_core' not in st.session_state:
    st.session_state.perception_core = PerceptionCore()
    training_data = generate_training_data(1000)
    st.session_state.perception_core.train(training_data)

if 'alerts' not in st.session_state:
    st.session_state.alerts = deque(maxlen=10)


def on_message(client, userdata, msg):
    """MQTT message callback."""
    try:
        data = json.loads(msg.payload.decode())
        
        # Update sensor data
        st.session_state.sensor_data['timestamps'].append(
            datetime.fromisoformat(data['timestamp'])
        )
        st.session_state.sensor_data['exhaust_temp'].append(data['exhaust_gas_temp_c'])
        st.session_state.sensor_data['oil_pressure'].append(data['lube_oil_pressure_bar'])
        st.session_state.sensor_data['bearing_temp'].append(data['main_bearing_temp_c'])
        st.session_state.sensor_data['vibration'].append(data['vibration_rms_mm_s'])
        
        # Run anomaly detection
        result = st.session_state.perception_core.predict_anomaly(data)
        if result['is_anomaly']:
            st.session_state.alerts.append({
                'timestamp': datetime.now(),
                'severity': result['severity'],
                'violations': result['threshold_violations']
            })
    except Exception as e:
        st.error(f"MQTT Error: {e}")


# Header
st.title("⚓ POSEIDONEYE COMMAND CENTER")
st.markdown("### AI-Powered Marine Engine Intelligence System")

# Sidebar
with st.sidebar:
    st.header("🔧 System Configuration")
    
    mqtt_broker = st.text_input("MQTT Broker", "localhost")
    mqtt_port = st.number_input("MQTT Port", value=1883)
    
    if st.button("🔌 Connect to Engine"):
        try:
            client = mqtt.Client("PoseidonEye_Dashboard")
            client.on_message = on_message
            client.connect(mqtt_broker, mqtt_port, 60)
            client.subscribe("poseidoneye/engine/sensors")
            client.loop_start()
            st.success("✓ Connected to engine telemetry")
        except Exception as e:
            st.error(f"Connection failed: {e}")
    
    st.markdown("---")
    st.header("📊 System Status")
    st.metric("Data Points", len(st.session_state.sensor_data['timestamps']))
    st.metric("Active Alerts", len(st.session_state.alerts))

# Main dashboard
col1, col2, col3, col4 = st.columns(4)

# Get latest values
if len(st.session_state.sensor_data['timestamps']) > 0:
    latest_exhaust = st.session_state.sensor_data['exhaust_temp'][-1]
    latest_oil = st.session_state.sensor_data['oil_pressure'][-1]
    latest_bearing = st.session_state.sensor_data['bearing_temp'][-1]
    latest_vibration = st.session_state.sensor_data['vibration'][-1]
else:
    latest_exhaust = latest_oil = latest_bearing = latest_vibration = 0

with col1:
    st.metric(
        "🔥 Exhaust Temp",
        f"{latest_exhaust:.1f} °C",
        delta=f"{'⚠️ HIGH' if latest_exhaust > 450 else '✓ OK'}"
    )

with col2:
    st.metric(
        "🛢️ Oil Pressure",
        f"{latest_oil:.2f} bar",
        delta=f"{'⚠️ LOW' if latest_oil < 2.5 else '✓ OK'}"
    )

with col3:
    st.metric(
        "🌡️ Bearing Temp",
        f"{latest_bearing:.1f} °C",
        delta=f"{'⚠️ HIGH' if latest_bearing > 85 else '✓ OK'}"
    )

with col4:
    st.metric(
        "📊 Vibration",
        f"{latest_vibration:.2f} mm/s",
        delta=f"{'⚠️ HIGH' if latest_vibration > 10 else '✓ OK'}"
    )

# Alerts section
if len(st.session_state.alerts) > 0:
    st.markdown("### 🚨 Active Alerts")
    for alert in reversed(list(st.session_state.alerts)):
        severity_class = "alert-critical" if alert['severity'] == "CRITICAL" else "alert-warning"
        st.markdown(
            f"<div class='{severity_class}'>"
            f"[{alert['timestamp'].strftime('%H:%M:%S')}] {alert['severity']}: "
            f"{', '.join(alert['violations'])}"
            f"</div>",
            unsafe_allow_html=True
        )

# Real-time charts
st.markdown("### 📈 Real-Time Telemetry")

if len(st.session_state.sensor_data['timestamps']) > 0:
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Exhaust Temperature', 'Oil Pressure', 'Bearing Temperature', 'Vibration'),
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    timestamps = list(st.session_state.sensor_data['timestamps'])
    
    # Exhaust temp
    fig.add_trace(
        go.Scatter(x=timestamps, y=list(st.session_state.sensor_data['exhaust_temp']),
                   mode='lines', name='Exhaust Temp', line=dict(color='#ff6b6b', width=2)),
        row=1, col=1
    )
    fig.add_hline(y=450, line_dash="dash", line_color="red", row=1, col=1)
    
    # Oil pressure
    fig.add_trace(
        go.Scatter(x=timestamps, y=list(st.session_state.sensor_data['oil_pressure']),
                   mode='lines', name='Oil Pressure', line=dict(color='#4ecdc4', width=2)),
        row=1, col=2
    )
    fig.add_hline(y=2.5, line_dash="dash", line_color="red", row=1, col=2)
    
    # Bearing temp
    fig.add_trace(
        go.Scatter(x=timestamps, y=list(st.session_state.sensor_data['bearing_temp']),
                   mode='lines', name='Bearing Temp', line=dict(color='#ffe66d', width=2)),
        row=2, col=1
    )
    fig.add_hline(y=85, line_dash="dash", line_color="red", row=2, col=1)
    
    # Vibration
    fig.add_trace(
        go.Scatter(x=timestamps, y=list(st.session_state.sensor_data['vibration']),
                   mode='lines', name='Vibration', line=dict(color='#a8dadc', width=2)),
        row=2, col=2
    )
    fig.add_hline(y=10, line_dash="dash", line_color="red", row=2, col=2)
    
    fig.update_layout(
        height=600,
        showlegend=False,
        plot_bgcolor='#1a1f3a',
        paper_bgcolor='#0a0e27',
        font=dict(color='#ffffff')
    )
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("⏳ Waiting for engine telemetry data...")

# RUL Prediction
st.markdown("### 🔧 Remaining Useful Life (RUL) Prediction")

if len(st.session_state.sensor_data['timestamps']) > 0:
    latest_data = {
        'exhaust_gas_temp_c': latest_exhaust,
        'lube_oil_pressure_bar': latest_oil,
        'main_bearing_temp_c': latest_bearing,
        'vibration_rms_mm_s': latest_vibration
    }
    
    rul = st.session_state.perception_core.estimate_rul(latest_data)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Component", rul['component'])
    with col2:
        st.metric("RUL (Hours)", f"{rul['rul_hours']:,}")
    with col3:
        st.metric("Degradation", f"{rul['degradation_percentage']:.1f}%")
    
    st.info(f"📋 Recommendation: {rul['recommended_action']}")

# Auto-refresh
st.markdown("---")
st.markdown("*Dashboard auto-refreshes every 2 seconds*")
time.sleep(2)
st.rerun()
