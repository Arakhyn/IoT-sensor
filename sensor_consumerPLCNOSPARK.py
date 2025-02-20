import json
import os
from kafka import KafkaConsumer
import psycopg2
from datetime import datetime
import sys
import time

# Configurar salida para UTF-8 en Windows
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

def create_postgres_connection(dbname, user, password, host, port):
    conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
    return conn

def create_postgres_table(conn):
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS plc_mech (
        timestamp TIMESTAMP,
        plc_id VARCHAR(50),
        temperature FLOAT,
        vibration FLOAT,
        pressure FLOAT,
        rotation_speed INTEGER,
        power_consumption FLOAT,
        noise_level FLOAT,
        oil_level FLOAT,
        humidity FLOAT,
        machine_age INTEGER,
        wear_level FLOAT,
        maintenance_needed BOOLEAN,
        machine_type VARCHAR(50),
        installation_date DATE,
        last_maintenance INTEGER
    );
    '''
    cursor = conn.cursor()
    cursor.execute(create_table_query)
    conn.commit()

def save_to_postgres(message):
    conn = None
    try:
        conn = create_postgres_connection(
            dbname=config['postgres_local']['dbname'],
            user=config['postgres_local']['user'],
            password=config['postgres_local']['password'],
            host=config['postgres_local']['host'],
            port=config['postgres_local']['port']
        )
        create_postgres_table(conn)

        cursor = conn.cursor()
        
        # Agregar timestamp de escritura
        write_timestamp = datetime.now()
        
        cursor.execute(
            '''
            INSERT INTO plc_mech (
                timestamp, plc_id, temperature, vibration, pressure, rotation_speed,
                power_consumption, noise_level, oil_level, humidity, machine_age,
                wear_level, maintenance_needed, machine_type, installation_date, last_maintenance
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''',
            (
                message['timestamp'], message['plc_id'], message['data']['temperature'],
                message['data']['vibration'], message['data']['pressure'],
                message['data']['rotation_speed'], message['data']['power_consumption'],
                message['data']['noise_level'], message['data']['oil_level'],
                message['data']['humidity'], message['data']['machine_age'],
                message['data']['wear_level'], message['data']['maintenance_needed'],
                message['metadata']['machine_type'], message['metadata']['installation_date'],
                message['metadata']['last_maintenance']
            )
        )
        conn.commit()
        
        # Verificar último registro cada 10 segundos
        current_time = time.time()
        if not hasattr(save_to_postgres, 'last_status_time'):
            save_to_postgres.last_status_time = current_time
            save_to_postgres.message_count = 0
        
        save_to_postgres.message_count += 1
        
        if current_time - save_to_postgres.last_status_time >= 10:
            cursor.execute("""
                SELECT COUNT(*) as count,
                       MAX(timestamp) as last_timestamp,
                       EXTRACT(EPOCH FROM (NOW() - MAX(timestamp))) as seconds_since_last
                FROM plc_mech
            """)
            stats = cursor.fetchone()
            print(f"[STATUS] Consumidor funcionando correctamente:")
            print(f"[INFO] - Mensajes procesados (10s): {save_to_postgres.message_count}")
            print(f"[INFO] - Total registros en BD: {stats[0]}")
            
            save_to_postgres.message_count = 0
            save_to_postgres.last_status_time = current_time
        
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        if conn:
            conn.close()

def main():
    global config
    config = load_config('config.json')

    print("[INFO] Iniciando consumidor...")
    
    try:
        consumer = KafkaConsumer(
            config['kinesis_stream'],
            bootstrap_servers=[config['kafka_broker']],
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='my-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )

        print("[INFO] Esperando mensajes...")
        
        for message in consumer:
            save_to_postgres(message.value)

    except Exception as e:
        print(f"[ERROR] Error en el consumidor: {e}")
    finally:
        if 'consumer' in locals():
            consumer.close()
            print("[INFO] Consumidor cerrado")

def load_config(file_path):
    with open(file_path, 'r') as file:
        config = json.load(file)
    return config

if __name__ == "__main__":
    main()