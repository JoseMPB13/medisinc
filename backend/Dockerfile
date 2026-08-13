# Imagen base de Python 3.11 en versión slim
FROM python:3.11-slim

# Establecer directorio de trabajo en la imagen
WORKDIR /app

# Prevenir escritura de archivos .pyc y forzar salida sin buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del backend
COPY ./app ./app

# Exponer el puerto 8000
EXPOSE 8000

# Comando por defecto para iniciar FastAPI con Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
