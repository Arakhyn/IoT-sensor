# 🏭 Sistema de Mantenimiento Predictivo Industrial

![Python](https://img.shields.io/badge/Python-3.9-blue.svg)
![Kafka](https://img.shields.io/badge/Kafka-Latest-brightgreen.svg)
![Docker](https://img.shields.io/badge/Docker-Enabled-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

Sistema de monitorización y mantenimiento predictivo en tiempo real para equipos industriales, utilizando Apache Kafka y análisis predictivo.

## 🚀 Características

- 📊 Dashboard interactivo en tiempo real
- 🤖 Análisis predictivo de mantenimiento
- 📧 Sistema de notificaciones por email
- 💾 Almacenamiento en PostgreSQL
- 🔄 Procesamiento de datos en tiempo real con Kafka
- 🐳 Completamente dockerizado

## 📋 Requisitos Previos

- Docker y Docker Compose
- Python 3.9+
- PostgreSQL
- Apache Kafka

## 🛠️ Instalación

### Usando Docker (Recomendado)

1. Clonar el repositorio:

git clone https://github.com/tu-usuario/predictive-maintenance.git
cd predictive-maintenance

2. Configurar el entorno:

cp config.json.example config.json

3. Iniciar los servicios:

docker-compose up -d

### Instalación Manual

1. Crear entorno virtual:

python -m venv venv
source venv/bin/activate # En Windows: venv/Scripts/activate

2. Instalar dependencias:

pip install -r requirements.txt

3. Configurar servicios:

cp config.json.example config.json


4. Iniciar la aplicación:


python main.py



## 📊 Uso

1. Acceder al dashboard:
   - http://localhost:8050

2. Monitorizar los datos en tiempo real:
   - Temperatura
   - Vibración
   - Nivel de desgaste
   - Predicciones de mantenimiento

3. Sistema de alertas:
   - Notificaciones por email cuando se requiere mantenimiento
   - Alertas de patrones anómalos
   - Predicciones de fallos

## 🏗️ Arquitectura

![Untitled diagram-2025-02-16-125242](https://github.com/user-attachments/assets/cd921e6e-651f-4584-824c-32c6e649570a)



## 📁 Estructura del Proyecto


predictive-maintenance/
├── docker-compose.yml # Configuración de Docker
├── Dockerfile # Definición de la imagen
├── requirements.txt # Dependencias Python
├── main.py # Punto de entrada
├── sensor_producerPLC.py # Productor de datos
├── sensor_consumerPLCNOSPARK.py # Consumidor
└── maintenance_dashboard.py # Dashboard



## ⚙️ Configuración

El archivo `config.json` permite configurar:
- Conexión a Kafka
- Credenciales de PostgreSQL
- Configuración de email
- Parámetros de monitorización

## 🤝 Contribuir

1. Fork del repositorio
2. Crear rama de feature (`git checkout -b feature/AmazingFeature`)
3. Commit de cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📝 Licencia

Distribuido bajo la Licencia MIT. Ver `LICENSE` para más información.

## 📧 Contacto

Email - tomas.palazon@outlook.com

Link del proyecto: [https://github.com/tu-usuario/predictive-maintenance](https://github.com/tu-usuario/predictive-maintenance)

## 🙏 Agradecimientos

- [Apache Kafka](https://kafka.apache.org/)
- [Plotly Dash](https://plotly.com/dash/)
- [PostgreSQL](https://www.postgresql.org/)
