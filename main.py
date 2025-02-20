# -*- coding: utf-8 -*-
import subprocess
import time
import signal
import sys
import logging
from pathlib import Path
import threading
import psutil
import os
from collections.abc import Sequence

# Configurar logging con encoding UTF-8 para Windows
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('main.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProcessManager:
    def __init__(self):
        self.processes = {}
        self.running = True
        self.python_path = self.get_python_path()
        self.monitor_threads = []
        
    def get_python_path(self):
        if sys.platform.startswith('win'):
            return r"YOUR PATH \python.exe"  ##YOU HAVE TO CHANGE "YOUR PATH" TO YOUR PATH WHERE PYTHON.EXE IS                        
        return sys.executable
    
    def run_script(self, name, script_path):
        """Ejecuta un script como un proceso separado"""
        try:
            # Configurar el entorno para UTF-8 en Windows
            env = os.environ.copy()
            if sys.platform.startswith('win'):
                env['PYTHONIOENCODING'] = 'utf-8'
            
            process = subprocess.Popen(
                [self.python_path, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1,
                env=env
            )
            self.processes[name] = process
            
            # Iniciar hilos de monitoreo para stdout y stderr
            self.start_log_monitor(name, process)
            
            return True
        except Exception as e:
            logger.error(f"Error iniciando {name}: {e}")
            return False
    
    def start_log_monitor(self, name, process):
        """Inicia hilos para monitorear la salida del proceso"""
        def monitor_output(pipe, is_error):
            try:
                for line in pipe:
                    # Si la línea ya tiene un formato [TAG], usarlo directamente
                    if line.strip().startswith('['):
                        logger.info(f"{name}: {line.strip()}")
                    # Si la línea contiene un nivel de log, respetarlo
                    elif ' - INFO - ' in line:
                        logger.info(f"{name}: {line.strip()}")
                    elif ' - WARNING - ' in line:
                        logger.warning(f"{name}: {line.strip()}")
                    elif ' - ERROR - ' in line:
                        logger.error(f"{name}: {line.strip()}")
                    # Para el resto de mensajes, usar el pipe original
                    else:
                        if is_error:
                            logger.error(f"{name}: {line.strip()}")
                        else:
                            logger.info(f"{name}: {line.strip()}")
            except Exception as e:
                logger.error(f"Error en monitor de {name}: {e}")
        
        # Crear y empezar hilos de monitoreo
        if process.stdout:
            stdout_thread = threading.Thread(
                target=monitor_output,
                args=(process.stdout, False),
                daemon=True
            )
            stdout_thread.start()
            self.monitor_threads.append(stdout_thread)
        
        if process.stderr:
            stderr_thread = threading.Thread(
                target=monitor_output,
                args=(process.stderr, True),
                daemon=True
            )
            stderr_thread.start()
            self.monitor_threads.append(stderr_thread)
    
    def check_processes(self):
        """Verifica el estado de todos los procesos"""
        for name, process in self.processes.items():
            if process.poll() is not None:
                logger.error(f"{name} se ha detenido inesperadamente")
                return False
        return True
    
    def stop_all(self):
        """Detiene todos los procesos"""
        for name, process in self.processes.items():
            try:
                # Obtener el proceso y todos sus hijos
                parent = psutil.Process(process.pid)
                children = parent.children(recursive=True)
                
                # Terminar procesos hijos
                for child in children:
                    try:
                        child.terminate()
                    except:
                        pass
                
                # Terminar proceso principal
                process.terminate()
                try:
                    process.wait(timeout=5)
                except:
                    process.kill()
                logger.info(f"{name} detenido correctamente")
            except Exception as e:
                logger.error(f"Error deteniendo {name}: {e}")
                try:
                    process.kill()
                except:
                    pass
        
        # Esperar a que los hilos de monitoreo terminen
        for thread in self.monitor_threads:
            try:
                thread.join(timeout=1)
            except:
                pass

    def verify_dependencies(self):
        try:
            logger.info("Verificando dependencias...")
            
            # Desinstalar numpy primero
            subprocess.check_call([self.python_path, "-m", "pip", "uninstall", "-y", "numpy"])
            subprocess.check_call([self.python_path, "-m", "pip", "install", "numpy==1.24.3"])
            
            # Verificar numpy
            result = subprocess.check_output(
                [self.python_path, "-c", "import numpy; print(numpy.__version__)"],
                universal_newlines=True
            )
            logger.info(f"NumPy instalado correctamente: {result.strip()}")
            
            # Lista de dependencias con versiones específicas
            dependencies = [
                "kafka-python==2.0.2",  # Ajusté a 2.0.2 por estabilidad
                "pandas==1.5.3",
                "scikit-learn==1.2.2",
                "dash==2.9.3",
                "plotly==5.14.1",
                "sqlalchemy==2.0.15",
                "psycopg2-binary==2.9.6",
                "IPython==8.12.0",  # Versión específica compatible con Python 3.9
                "jedi==0.18.2",     # Compatible con parso
                "parso==0.8.3"      # Versión estable
            ]
            
            for dep in dependencies:
                logger.info(f"Instalando {dep}...")
                subprocess.check_call([self.python_path, "-m", "pip", "install", dep])
                
            return True
        except Exception as e:
            logger.error(f"Error instalando dependencias: {e}")
            return False

def main():
    manager = ProcessManager()
    
    try:
        # Iniciar productor
        if not manager.run_script('Producer', 'sensor_producerPLC.py'):
            return
        
        # Esperar un momento
        time.sleep(2)
        
        # Iniciar consumidor
        if not manager.run_script('Consumer', 'sensor_consumerPLCNOSPARK.py'):
            manager.stop_all()
            return
        
        # Esperar un momento
        time.sleep(2)
        
        # Iniciar dashboard
        if not manager.run_script('Dashboard', 'maintenance_dashboard.py'):
            manager.stop_all()
            return
        
        # Añadir el agente predictivo
        if not manager.run_script('ML_Agent', 'predictive_maintenance_agent.py'):
            manager.stop_all()
            return
        
        logger.info("""
        🚀 Sistema iniciado correctamente:
        - Producer: Generando datos
        - Consumer: Procesando datos
        - Dashboard: http://localhost:8050
        
        Presiona Ctrl+C para detener todos los procesos
        """)
        
        # Mantener el programa principal ejecutándose y monitoreando
        while manager.running:
            if not manager.check_processes():
                manager.stop_all()
                break
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("\n👋 Deteniendo el sistema...")
    except Exception as e:
        logger.error(f"Error en el programa principal: {e}")
    finally:
        manager.stop_all()

if __name__ == "__main__":
    # Manejar señal de interrupción
    def signal_handler(sig, frame):
        logger.info("\n👋 Deteniendo el sistema...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    main()
