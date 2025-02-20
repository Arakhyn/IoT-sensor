from pymodbus.client import ModbusTcpClient
import snap7
from kafka import KafkaProducer
import json
import time
from datetime import datetime
import logging
import random
import numpy as np
import sys
from collections.abc import Sequence

# Configurar salida para UTF-8 en Windows
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

class EnhancedPLCDataCollector:
    def __init__(self, plc_ip, plc_port=502, plc_type='simulation'):
        self.plc_type = plc_type
        self.plc_ip = plc_ip
        self.plc_port = plc_port
        
        # Estado interno de la máquina para simulación
        self.machine_age = 0  # Edad en horas
        self.maintenance_needed = False
        self.last_maintenance = 0
        self.wear_level = 0.0
        self.baseline_values = {
            'temperature': 23.0,
            'vibration': 0.5,
            'pressure': 1.5,
            'rotation_speed': 1750,
            'power_consumption': 75.0,
            'noise_level': 65.0,
            'oil_level': 95.0,
            'humidity': 45.0
        }
        
        # Configurar cliente y logging como en el original
        self._setup_connections()
        self._setup_logging()

    def _setup_connections(self):
        """Configura las conexiones necesarias"""
        if self.plc_type == 'modbus':
            self.client = ModbusTcpClient(self.plc_ip, port=self.plc_port)
        elif self.plc_type == 'siemens':
            self.client = snap7.client.Client()
            try:
                self.client.connect(self.plc_ip, 0, 1)
            except Exception as e:
                print(f"⚠️ No se pudo conectar al PLC Siemens: {e}")
                self.client = None

        try:
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=['localhost:9092'],
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
        except Exception as e:
            print(f"⚠️ No se pudo conectar a Kafka: {e}")
            self.kafka_producer = None

    def _setup_logging(self):
        """Configura el sistema de logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('plc_producer.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def simulate_sensor_value(self, baseline, noise_factor=0.1, trend=0):
        """
        Simula un valor de sensor con ruido y tendencia
        
        Args:
            baseline: valor base del sensor
            noise_factor: factor de ruido (0.1 = 10% de ruido)
            trend: tendencia adicional al valor
        """
        noise = np.random.normal(0, baseline * noise_factor)
        return max(0, baseline + noise + trend)

    def calculate_wear_effects(self):
        """Calcula los efectos del desgaste en los valores de los sensores"""
        # Incrementar desgaste con el tiempo
        self.wear_level = min(1.0, self.wear_level + random.uniform(0.001, 0.003))
        
        # Efectos del desgaste en diferentes parámetros
        effects = {
            'temperature': self.wear_level * 15,  # Hasta +15 grados
            'vibration': self.wear_level * 1.5,   # Hasta +1.5 unidades
            'pressure': self.wear_level * -0.5,    # Hasta -0.5 bar
            'rotation_speed': self.wear_level * -100,  # Hasta -100 RPM
            'power_consumption': self.wear_level * 25,  # Hasta +25%
            'noise_level': self.wear_level * 20,   # Hasta +20 dB
            'oil_level': self.wear_level * -30,    # Hasta -30%
            'humidity': self.wear_level * 15       # Hasta +15%
        }
        
        # Simular fallos aleatorios basados en el desgaste
        if random.random() < (self.wear_level * 0.1):  # Probabilidad de fallo aumenta con el desgaste
            failure_type = random.choice(['overheating', 'vibration', 'pressure_loss'])
            if failure_type == 'overheating':
                effects['temperature'] += 30
            elif failure_type == 'vibration':
                effects['vibration'] += 2.0
            elif failure_type == 'pressure_loss':
                effects['pressure'] -= 1.0

        return effects

    def simulate_plc_data(self):
        """Simula datos de PLC más realistas para ML"""
        # Incrementar edad de la máquina
        self.machine_age += 1
        
        # Calcular efectos del desgaste
        wear_effects = self.calculate_wear_effects()
        
        # Generar datos con variaciones realistas
        data = {}
        for param, baseline in self.baseline_values.items():
            data[param] = self.simulate_sensor_value(
                baseline,
                noise_factor=0.05,
                trend=wear_effects.get(param, 0)
            )
        
        # Agregar métricas adicionales
        data['machine_age'] = self.machine_age
        data['wear_level'] = self.wear_level
        data['maintenance_needed'] = self.wear_level > 0.7
        
        return data

    def collect_and_send(self):
        """Recolecta y envía datos simulados"""
        message_count = 0
        last_status_time = time.time()
        
        while True:
            try:
                data = self.simulate_plc_data()
                message_count += 1
                
                message = {
                    'timestamp': datetime.now().isoformat(),
                    'plc_id': f"PLC_{self.plc_ip}",
                    'data': data,
                    'metadata': {
                        'machine_type': 'industrial_pump',
                        'installation_date': '2024-01-01',
                        'last_maintenance': self.last_maintenance
                    }
                }
                
                if self.kafka_producer:
                    self.kafka_producer.send('plc_data', message)
                    
                    # Mostrar resumen cada 10 segundos
                    current_time = time.time()
                    if current_time - last_status_time >= 10:
                        self.logger.info(f"[STATUS] Productor funcionando correctamente - Mensajes enviados (10s): {message_count}")
                        message_count = 0
                        last_status_time = current_time
                
                time.sleep(1)

            except Exception as e:
                self.logger.error(f"[ERROR] Error en ciclo de recolección: {e}")
                time.sleep(5)

    def close(self):
        """Cierra conexiones"""
        self.logger.info("[INFO] Cerrando colector de datos")
        if hasattr(self, 'client') and self.client:
            self.client.close()
        if hasattr(self, 'kafka_producer') and self.kafka_producer:
            self.kafka_producer.close()

def main():
    PLC_IP = '192.168.1.10'
    PLC_TYPE = 'simulation'

    try:
        collector = EnhancedPLCDataCollector(plc_ip=PLC_IP, plc_type=PLC_TYPE)
        collector.collect_and_send()
    except KeyboardInterrupt:
        print("\nDeteniendo colector...")
        collector.close()
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'collector' in locals():
            collector.close()

if __name__ == "__main__":
    main()