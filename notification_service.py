import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from datetime import datetime
import json
from collections.abc import Sequence

class MaintenanceNotificationService:
    def __init__(self, config_path='config.json'):
        self.load_config(config_path)
        self.setup_logging()
        self.last_notification = None
        self.notification_cooldown_hours = 24  # Evitar spam de emails
        
    def load_config(self, config_path):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
            
    def setup_logging(self):
        self.logger = logging.getLogger('MaintenanceNotification')
        
    def should_send_notification(self):
        """Verifica si debemos enviar una nueva notificación"""
        if not self.last_notification:
            return True
            
        hours_since_last = (datetime.now() - self.last_notification).total_seconds() / 3600
        return hours_since_last >= self.notification_cooldown_hours
        
    def send_maintenance_alert(self, days_to_maintenance, machine_status):
        """Envía alerta de mantenimiento por email"""
        try:
            if not self.should_send_notification():
                self.logger.info("Notificación en cooldown, saltando...")
                return
                
            email_config = self.config['email_notifications']
            
            msg = MIMEMultipart()
            msg['From'] = email_config['sender_email']
            msg['Subject'] = f"⚠️ Mantenimiento Requerido en {days_to_maintenance:.1f} días"
            msg.set_charset('utf-8')  # Establecer codificación UTF-8
            
            # Crear contenido HTML del email
            html = f"""
            <html>
                <head>
                    <meta charset="utf-8">  <!-- Especificar UTF-8 -->
                </head>
                <body style="font-family: Arial, sans-serif;">
                    <div style="padding: 20px; background-color: #f8f9fa; border-radius: 10px;">
                        <h2 style="color: {'red' if days_to_maintenance < 2 else 'orange'};">
                            ⚠️ Alerta de Mantenimiento
                        </h2>
                        
                        <p>Estado actual:</p>
                        
                        <ul>
                            <li>🌡️ Temperatura: {machine_status['temperature']:.1f}°C</li>
                            <li>📳 Vibración: {machine_status['vibration']:.2f} mm/s</li>
                            <li>⚙️ Desgaste: {machine_status['wear_level']*100:.1f}%</li>
                        </ul>
                        
                        <p style="background-color: #e9ecef; padding: 10px; border-radius: 5px;">
                            Por favor, programe el mantenimiento lo antes posible para evitar fallos del equipo.
                        </p>
                        
                        <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                            <small style="color: #6c757d;">
                                Este es un mensaje automático del Sistema de Mantenimiento Predictivo.
                                No responda a este email.
                            </small>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            # Imprimir contenido del email en los logs
            self.logger.info("============= CONTENIDO DEL EMAIL =============")
            self.logger.info(f"De: {email_config['sender_email']}")
            self.logger.info(f"Para: {', '.join(email_config['recipients'])}")
            self.logger.info(f"Asunto: {msg['Subject']}")
            self.logger.info("/nContenido HTML:")
            self.logger.info(html)
            self.logger.info("=============================================")
            
            part = MIMEText(html, 'html', 'utf-8')  # Especificar UTF-8
            msg.attach(part)
            
            # Conectar y enviar
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                server.starttls()
                self.logger.info("Intentando autenticar con el servidor SMTP...")
                server.login(
                    email_config['sender_email'],
                    email_config['sender_password']
                )
                self.logger.info("Autenticación exitosa, enviando email...")
                
                for recipient in email_config['recipients']:
                    msg['To'] = recipient
                    server.send_message(msg)
                    self.logger.info(f"Email enviado a {recipient}")
                    
            self.last_notification = datetime.now()
            self.logger.info(f"Alerta de mantenimiento enviada: {days_to_maintenance:.1f} días")
            
        except Exception as e:
            self.logger.error(f"Error enviando alerta de mantenimiento: {e}") 