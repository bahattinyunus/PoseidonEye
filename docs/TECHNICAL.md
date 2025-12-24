# PoseidonEye - Teknik Dokümantasyon

## İçindekiler

1. [Sistem Mimarisi](#sistem-mimarisi)
2. [Veri Akışı](#veri-akışı)
3. [AI Model Detayları](#ai-model-detayları)
4. [API Referansı](#api-referansı)
5. [Deployment](#deployment)

## Sistem Mimarisi

PoseidonEye, üç ana katmandan oluşur:

### 1. Veri Toplama Katmanı
- **Sensörler**: Fiziksel sensörlerden veri toplama
- **MQTT Broker**: Eclipse Mosquitto ile mesaj iletimi
- **Simulator**: Test ve geliştirme için veri simülasyonu

### 2. İşleme Katmanı
- **Perception Core**: Isolation Forest ile anomali tespiti
- **RUL Estimator**: Kalan ömür tahmini
- **Data Pipeline**: Veri normalizasyonu ve ön işleme

### 3. Sunum Katmanı
- **Streamlit Dashboard**: Web tabanlı görselleştirme
- **Alert System**: Gerçek zamanlı uyarı yönetimi

## Veri Akışı

```
Sensör → MQTT → Perception Core → Dashboard
                      ↓
                 RUL Estimator
                      ↓
                 Alert System
```

## AI Model Detayları

### Isolation Forest Parametreleri

```python
IsolationForest(
    contamination=0.1,      # Beklenen anomali oranı
    n_estimators=100,       # Karar ağacı sayısı
    max_samples='auto',     # Örnekleme boyutu
    random_state=42         # Tekrarlanabilirlik
)
```

### Özellik Mühendisliği

Model, 4 ana özellik kullanır:
1. `exhaust_gas_temp_c`: Egzoz gazı sıcaklığı
2. `lube_oil_pressure_bar`: Yağlama yağı basıncı
3. `main_bearing_temp_c`: Ana yatak sıcaklığı
4. `vibration_rms_mm_s`: Titreşim RMS değeri

Tüm özellikler StandardScaler ile normalize edilir.

## API Referansı

### PerceptionCore

#### `train(training_data)`
Modeli eğitir.

**Parametreler:**
- `training_data` (DataFrame): Normal çalışma verileri

**Örnek:**
```python
core = PerceptionCore()
core.train(training_data)
```

#### `predict_anomaly(sensor_data)`
Anomali tespiti yapar.

**Parametreler:**
- `sensor_data` (dict): Sensör okumaları

**Dönüş:**
```python
{
    'is_anomaly': bool,
    'anomaly_score': float,
    'severity': str,
    'threshold_violations': list
}
```

#### `estimate_rul(sensor_data, component)`
Kalan ömür tahmini yapar.

**Parametreler:**
- `sensor_data` (dict): Sensör okumaları
- `component` (str): Komponent adı

**Dönüş:**
```python
{
    'rul_hours': int,
    'rul_days': int,
    'degradation_percentage': float,
    'recommended_action': str
}
```

## Deployment

### Docker Deployment

```bash
# Tüm servisleri başlat
docker-compose up -d

# Logları görüntüle
docker-compose logs -f

# Servisleri durdur
docker-compose down
```

### Production Checklist

- [ ] MQTT broker güvenlik ayarları (TLS/SSL)
- [ ] Dashboard authentication
- [ ] Model versiyonlama
- [ ] Backup stratejisi
- [ ] Monitoring ve logging
- [ ] Alert notification kanalları (email, SMS)

### Performans Optimizasyonu

1. **MQTT QoS**: QoS 1 kullanın (at least once delivery)
2. **Model Caching**: Eğitilmiş modeli disk'e kaydedin
3. **Data Retention**: Sadece son 1000 veri noktasını tutun
4. **Dashboard Refresh**: 2 saniye optimal, daha sık güncelleme gereksiz

## Troubleshooting

### MQTT Bağlantı Hatası
```bash
# Mosquitto servisini kontrol et
sudo systemctl status mosquitto

# Port kontrolü
netstat -an | grep 1883
```

### Model Eğitim Hatası
- Eğitim verisinin en az 100 satır olduğundan emin olun
- Tüm feature column'ların mevcut olduğunu kontrol edin
- NaN değerleri temizleyin

### Dashboard Yüklenmiyor
```bash
# Streamlit versiyonunu kontrol et
streamlit --version

# Port çakışması kontrolü
lsof -i :8501
```
