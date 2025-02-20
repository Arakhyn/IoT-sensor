# -*- coding: utf-8 -*-

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
from sqlalchemy import create_engine, text
import json
from datetime import datetime, timedelta
import logging
from plotly.subplots import make_subplots
import numpy as np
from notification_service import MaintenanceNotificationService
from predictive_maintenance_agent import PredictiveMaintenanceAgent
from collections.abc import Sequence
import sys
sys.modules['IPython'] = None  # Finge que IPython no está disponible

class MaintenanceDashboard:
    def __init__(self, config_path='config.json'):
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[
                'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css'
            ]
        )
        self.load_config(config_path)
        self.setup_database_connection()
        self.setup_layout()
        self.setup_callbacks()
        
        # Configuración del logging
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Handler para archivo
        file_handler = logging.FileHandler('dashboard.log', encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Configurar logger
        logging.basicConfig(
            level=logging.INFO,
            handlers=[file_handler, console_handler]
        )
        
        self.logger = logging.getLogger('Dashboard')
        
        self.ml_agent = PredictiveMaintenanceAgent()
        
    def load_config(self, config_path):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
            
    def setup_database_connection(self):
        pg = self.config['postgres_local']
        db_url = f"postgresql://{pg['user']}:{pg['password']}@{pg['host']}:{pg['port']}/{pg['dbname']}"
        self.engine = create_engine(db_url)
        
    def get_sensor_data(self, minutes=5):
        """Obtiene los datos más recientes de los sensores"""
        try:
            # Verificar último dato recibido
            last_record_query = text("""
                SELECT timestamp, 
                       EXTRACT(EPOCH FROM (NOW() - MAX(timestamp))) as seconds_since_last
                FROM plc_mech
                GROUP BY timestamp
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            
            last_record = pd.read_sql(last_record_query, self.engine)
            
            if not last_record.empty:
                seconds_since_last = last_record['seconds_since_last'].iloc[0]
                if seconds_since_last > 30:  # Si han pasado más de 30 segundos
                    self.logger.warning(f"No se han recibido datos nuevos en {seconds_since_last:.0f} segundos")
            
            # Obtener datos normalmente
            query = text("""
                SELECT timestamp, temperature, vibration, pressure, 
                       rotation_speed, power_consumption, noise_level,
                       oil_level, humidity, machine_age, wear_level, 
                       maintenance_needed
                FROM plc_mech
                WHERE timestamp >= NOW() - make_interval(mins => :minutes)
                ORDER BY timestamp ASC
            """)
            
            df = pd.read_sql(query, self.engine, params={'minutes': minutes})
            
            if df.empty:
                self.logger.warning("No hay datos disponibles en el período seleccionado")
                return pd.DataFrame()
            
            return df
        except Exception as e:
            self.logger.error(f"Error obteniendo datos: {e}")
            return pd.DataFrame()
        
    def setup_layout(self):
        self.app.layout = html.Div([
            # Header con título y tiempo de actualización
            html.Div([
                html.H1('Sistema de Monitoreo y Mantenimiento Predictivo', 
                       className='text-center mb-4'),
                html.Div(id='last-update-time', className='text-muted text-center mb-4')
            ], className='container-fluid bg-light py-4'),
            
            # Contenedor principal
            html.Div([
                # KPIs principales
                html.Div([
                    # Primera fila: KPIs
                    html.Div([
                        # Estado General
                        html.Div([
                            html.Div([
                                html.H4('Estado General'),
                                html.Div(id='health-status', className='display-4')
                            ], className='card h-100 shadow-sm')
                        ], className='col-md-4 mb-4'),
                        
                        # Tiempo hasta Mantenimiento
                        html.Div([
                            html.Div([
                                html.H4('Tiempo hasta Mantenimiento'),
                                html.Div(id='time-to-maintenance', className='display-4')
                            ], className='card h-100 shadow-sm')
                        ], className='col-md-4 mb-4'),
                        
                        # Eficiencia General
                        html.Div([
                            html.Div([
                                html.H4('Eficiencia General'),
                                html.Div(id='efficiency-status', className='display-4')
                            ], className='card h-100 shadow-sm')
                        ], className='col-md-4 mb-4')
                    ], className='row'),
                    
                    # Segunda fila: Gráficos principales
                    html.Div([
                        # Tendencias
                        html.Div([
                            html.Div([
                                html.H3('Tendencias en Tiempo Real'),
                                dcc.Graph(id='sensor-trends'),
                                dcc.Dropdown(
                                    id='sensor-selector',
                                    options=[
                                        {'label': 'Temperatura (°C)', 'value': 'temperature'},
                                        {'label': 'Vibración', 'value': 'vibration'},
                                        {'label': 'Presión', 'value': 'pressure'},
                                        {'label': 'Velocidad (RPM)', 'value': 'rotation_speed'},
                                        {'label': 'Consumo Energético', 'value': 'power_consumption'},
                                        {'label': 'Nivel de Ruido (dB)', 'value': 'noise_level'},
                                        {'label': 'Nivel de Aceite (%)', 'value': 'oil_level'},
                                        {'label': 'Humedad (%)', 'value': 'humidity'},
                                        {'label': 'Edad de la Máquina (h)', 'value': 'machine_age'},
                                        {'label': 'Nivel de Desgaste (%)', 'value': 'wear_level'}
                                    ],
                                    value=['temperature', 'vibration'],
                                    multi=True,
                                    placeholder="Selecciona las variables a monitorear"
                                )
                            ], className='card shadow-sm p-3')
                        ], className='col-md-8 mb-4'),
                        
                        # Indicadores
                        html.Div([
                            html.Div([
                                html.H3('Indicadores de Estado'),
                                dcc.Graph(id='status-indicators')
                            ], className='card shadow-sm p-3')
                        ], className='col-md-4 mb-4')
                    ], className='row'),
                    
                    # Tercera fila: Análisis y predicciones
                    html.Div([
                        # Predicciones ML
                        html.Div([
                            html.Div([
                                html.H3('Predicciones del Modelo'),
                                dcc.Graph(id='ml-predictions')
                            ], className='card shadow-sm p-3')
                        ], className='col-md-6 mb-4'),
                        
                        # Correlaciones
                        html.Div([
                            html.Div([
                                html.H3('Correlaciones'),
                                dcc.Graph(id='correlation-heatmap')
                            ], className='card shadow-sm p-3')
                        ], className='col-md-6 mb-4')
                    ], className='row'),
                    
                    # Cuarta fila: Alertas
                    html.Div([
                        html.Div([
                            html.Div([
                                html.H3('Alertas y Recomendaciones'),
                                html.Div(id='alerts-panel')
                            ], className='card shadow-sm p-3')
                        ], className='col-12 mb-4')
                    ], className='row')
                ], className='container-fluid px-4')
            ], className='bg-white py-4'),
            
            dcc.Interval(
                id='interval-component',
                interval=5*1000,
                n_intervals=0
            )
        ])
    
    def setup_callbacks(self):
        @self.app.callback(
            [Output('sensor-trends', 'figure'),
             Output('status-indicators', 'figure'),
             Output('ml-predictions', 'figure'),
             Output('correlation-heatmap', 'figure'),
             Output('health-status', 'children'),
             Output('time-to-maintenance', 'children'),
             Output('efficiency-status', 'children'),
             Output('alerts-panel', 'children'),
             Output('last-update-time', 'children')],
            [Input('interval-component', 'n_intervals'),
             Input('sensor-selector', 'value')]
        )
        def update_dashboard(n, selected_sensors):
            try:
                # Obtener datos
                df = self.get_sensor_data(minutes=30)
                if df.empty:
                    raise ValueError("No hay datos disponibles")

                # Último registro y tiempo actual
                latest = df.iloc[-1]
                current_time = datetime.now()

                # Crear todas las figuras
                trends_fig = self.create_trends_figure(df, selected_sensors or ['temperature'])
                status_fig = self.create_status_indicators(latest)
                ml_fig = self.create_ml_predictions(df)
                corr_fig = self.create_correlation_heatmap(df)

                # Calcular KPIs
                health_status = self.calculate_health_status(latest)
                time_to_maintenance = self.estimate_maintenance_time(latest)
                efficiency = self.calculate_efficiency(df)

                # Generar alertas
                alerts = self.generate_alerts(latest)

                # Tiempo de actualización
                update_time = f"Última actualización: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"

                return (
                    trends_fig, status_fig, ml_fig, corr_fig,
                    health_status, time_to_maintenance, efficiency,
                    alerts, update_time
                )

            except Exception as e:
                self.logger.error(f"Error actualizando dashboard: {e}")
                # Retornar valores por defecto en caso de error
                empty_fig = go.Figure()
                empty_fig.update_layout(
                    title="Error cargando datos",
                    annotations=[{
                        'text': str(e),  # Mostrar el error específico
                        'xref': "paper",
                        'yref': "paper",
                        'showarrow': False,
                        'font': {'size': 20}
                    }]
                )
                error_div = html.Div(
                    f"Error: {str(e)}", 
                    style={'color': 'red', 'padding': '10px'}
                )
                return [empty_fig] * 4 + [error_div] * 4 + [f"Error: {str(e)}"]

    def create_trends_figure(self, df, selected_sensors):
        """Crea el gráfico de tendencias con unidades apropiadas"""
        fig = go.Figure()
        
        # Diccionario de unidades y factores de escala
        units = {
            'temperature': {'unit': '°C', 'scale': 1},
            'vibration': {'unit': 'mm/s', 'scale': 1},
            'pressure': {'unit': 'bar', 'scale': 1},
            'rotation_speed': {'unit': 'RPM', 'scale': 1},
            'power_consumption': {'unit': 'kW', 'scale': 1},
            'noise_level': {'unit': 'dB', 'scale': 1},
            'oil_level': {'unit': '%', 'scale': 1},
            'humidity': {'unit': '%', 'scale': 1},
            'machine_age': {'unit': 'h', 'scale': 1},
            'wear_level': {'unit': '%', 'scale': 100}  # Convertir a porcentaje
        }
        
        for sensor in selected_sensors:
            # Aplicar factor de escala y añadir unidades
            y_values = df[sensor] * units[sensor]['scale']
            name = f"{sensor.replace('_', ' ').title()} ({units[sensor]['unit']})"
            
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=y_values,
                name=name,
                mode='lines+markers',
                hovertemplate=f"%{{y:.2f}} {units[sensor]['unit']}<br>%{{x}}<extra></extra>"
            ))
        
        fig.update_layout(
            title='Tendencias en Tiempo Real',
            xaxis_title='Tiempo',
            yaxis_title='Valor',
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        return fig

    def create_status_indicators(self, latest):
        """Crea indicadores tipo gauge para variables críticas"""
        fig = make_subplots(
            rows=2, cols=2,
            specs=[[{'type': 'indicator'}, {'type': 'indicator'}],
                  [{'type': 'indicator'}, {'type': 'indicator'}]]
        )
        
        # Temperatura
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=latest['temperature'],
            title={'text': "Temperatura (°C)"},
            gauge={'axis': {'range': [0, 100]},
                  'steps': [
                      {'range': [0, 60], 'color': "lightgreen"},
                      {'range': [60, 80], 'color': "yellow"},
                      {'range': [80, 100], 'color': "red"}
                  ]},
        ), row=1, col=1)
        
        # Vibración
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=latest['vibration'],
            title={'text': "Vibración"},
            gauge={'axis': {'range': [0, 2]},
                  'steps': [
                      {'range': [0, 0.7], 'color': "lightgreen"},
                      {'range': [0.7, 1.2], 'color': "yellow"},
                      {'range': [1.2, 2], 'color': "red"}
                  ]},
        ), row=1, col=2)
        
        # Presión
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=latest['pressure'],
            title={'text': "Presión"},
            gauge={'axis': {'range': [0, 3]},
                  'steps': [
                      {'range': [0, 1], 'color': "red"},
                      {'range': [1, 2], 'color': "lightgreen"},
                      {'range': [2, 3], 'color': "yellow"}
                  ]},
        ), row=2, col=1)
        
        # Desgaste
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=latest['wear_level'] * 100,
            title={'text': "Desgaste (%)"},
            gauge={'axis': {'range': [0, 100]},
                  'steps': [
                      {'range': [0, 30], 'color': "lightgreen"},
                      {'range': [30, 70], 'color': "yellow"},
                      {'range': [70, 100], 'color': "red"}
                  ]},
        ), row=2, col=2)
        
        fig.update_layout(height=600)
        return fig

    def create_ml_predictions(self, df):
        """Crea gráfico de predicciones del modelo"""
        fig = go.Figure()
        
        # Predicción de desgaste
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['wear_level'] * 100,  # Convertir a porcentaje
            name='Nivel de Desgaste',
            mode='lines+markers',
            hovertemplate='%{y:.1f}%<br>%{x}<extra></extra>'
        ))
        
        # Umbral de mantenimiento
        fig.add_hline(
            y=70,  # 70% es el umbral
            line_dash="dash",
            line_color="red"
        )
        
        # Añadir área sombreada para zonas de riesgo
        fig.add_hrect(
            y0=0, y1=30,
            fillcolor="green", opacity=0.1,
            layer="below", line_width=0
        )
        fig.add_hrect(
            y0=30, y1=70,
            fillcolor="yellow", opacity=0.1,
            layer="below", line_width=0
        )
        fig.add_hrect(
            y0=70, y1=100,
            fillcolor="red", opacity=0.1,
            layer="below", line_width=0
        )
        
        fig.update_layout(
            title='Predicción de Desgaste',
            xaxis_title='Tiempo',
            yaxis_title='Nivel de Desgaste (%)',
            yaxis=dict(range=[0, 100]),
            hovermode='x unified',
            showlegend=True,
            height=400,
            margin=dict(t=50, l=50, r=50, b=50)
        )
        return fig

    def create_correlation_heatmap(self, df):
        """Crea mapa de calor de correlaciones"""
        # Seleccionar columnas numéricas y renombrarlas para mejor visualización
        column_names = {
            'temperature': 'Temperatura',
            'vibration': 'Vibración',
            'pressure': 'Presión',
            'rotation_speed': 'Velocidad',
            'power_consumption': 'Consumo',
            'noise_level': 'Ruido',
            'oil_level': 'Aceite',
            'humidity': 'Humedad',
            'wear_level': 'Desgaste'
        }
        
        numeric_cols = list(column_names.keys())
        df_corr = df[numeric_cols].corr()
        
        # Renombrar índices y columnas
        df_corr.index = [column_names[col] for col in df_corr.index]
        df_corr.columns = [column_names[col] for col in df_corr.columns]
        
        fig = go.Figure(data=go.Heatmap(
            z=df_corr,
            x=df_corr.columns,
            y=df_corr.index,
            colorscale='RdBu',
            zmid=0,
            text=np.around(df_corr, decimals=2),
            texttemplate='%{text}',
            textfont={"size": 10},
            hoverongaps=False,
            hovertemplate='%{x} vs %{y}<br>Correlación: %{z:.2f}<extra></extra>'
        ))
        
        fig.update_layout(
            title='Correlaciones entre Variables',
            height=500,
            xaxis={'side': 'bottom'},
            yaxis={'side': 'left', 'autorange': 'reversed'},
            margin=dict(t=50, l=50, r=50, b=50)
        )
        return fig

    def calculate_health_status(self, latest):
        """Calcula el estado de salud general"""
        health = (1 - latest['wear_level']) * 100
        color = 'green' if health > 70 else 'orange' if health > 30 else 'red'
        return html.Div([
            html.H2(f"{health:.1f}%"),
            html.Div("Salud del Sistema", style={'color': color})
        ])

    def calculate_efficiency(self, df):
        """Calcula la eficiencia general del sistema"""
        efficiency = (df['rotation_speed'].mean() / 1750) * 100  # 1750 RPM es el valor ideal
        color = 'green' if efficiency > 90 else 'orange' if efficiency > 70 else 'red'
        return html.Div([
            html.H2(f"{efficiency:.1f}%"),
            html.Div("Eficiencia", style={'color': color})
        ])

    def estimate_maintenance_time(self, latest):
        """Estima tiempo hasta próximo mantenimiento y envía alertas si es necesario"""
        if latest['wear_level'] >= 0.7:
            return html.Div([
                html.H2("0 días"),
                html.Div("¡Mantenimiento requerido!", style={'color': 'red'})
            ])
        
        wear_rate = latest['wear_level'] / latest['machine_age'] if latest['machine_age'] > 0 else 0
        if wear_rate > 0:
            hours_to_maintenance = (0.7 - latest['wear_level']) / wear_rate
            days = max(0, hours_to_maintenance / 24)
            
            # Enviar alerta si quedan menos de 3 días
            if days < 3:
                notification_service = MaintenanceNotificationService()
                notification_service.send_maintenance_alert(
                    days_to_maintenance=days,
                    machine_status={
                        'temperature': latest['temperature'],
                        'vibration': latest['vibration'],
                        'wear_level': latest['wear_level']
                    }
                )
            
            return html.Div([
                html.H2(f"{int(days)} días"),
                html.Div("hasta mantenimiento")
            ])
        return html.Div([
            html.H2("N/A"),
            html.Div("Datos insuficientes")
        ])

    def generate_alerts(self, latest):
        """Genera alertas basadas en los datos actuales"""
        alerts = []
        
        # Alertas de temperatura
        if latest['temperature'] > 80:
            alerts.append(
                html.Div("⚠️ Temperatura crítica", 
                        className='alert alert-danger p-2 m-1')
            )
        elif latest['temperature'] > 60:
            alerts.append(
                html.Div("⚠️ Temperatura alta", 
                        className='alert alert-warning p-2 m-1')
            )
        
        # Alertas de vibración
        if latest['vibration'] > 1.2:
            alerts.append(
                html.Div("⚠️ Vibración excesiva", 
                        className='alert alert-danger p-2 m-1')
            )
        
        # Alertas de desgaste
        if latest['wear_level'] > 0.7:
            alerts.append(
                html.Div("🔧 Mantenimiento requerido", 
                        className='alert alert-danger p-2 m-1')
            )
        elif latest['wear_level'] > 0.5:
            alerts.append(
                html.Div("⚠️ Programar mantenimiento", 
                        className='alert alert-warning p-2 m-1')
            )
        
        # Si no hay alertas, mostrar estado normal
        if not alerts:
            alerts.append(
                html.Div("✅ Sistema funcionando normalmente", 
                        className='alert alert-success p-2 m-1')
            )
        
        # Retornar contenedor de alertas
        return html.Div(
            alerts,
            className='alert-container p-3',
            style={
                'maxHeight': '300px',
                'overflowY': 'auto'
            }
        )

    def update_dashboard(self, data):
        predictions = self.ml_agent.get_predictions(data)
        # Usar predicciones para actualizar UI

    def run(self):
        self.app.run_server(debug=True)

if __name__ == "__main__":
    dashboard = MaintenanceDashboard()
    dashboard.run() 