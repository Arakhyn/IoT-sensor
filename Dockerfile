FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && /
    apt-get install -y --no-install-recommends /
    gcc /
    postgresql-client /
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Puerto para el dashboard
EXPOSE 8050

# Comando para ejecutar la aplicación
CMD ["python", "main.py"]
