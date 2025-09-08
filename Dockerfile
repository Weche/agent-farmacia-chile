# Usa una imagen base ligera de Python
FROM python:3.11-slim

# Evita que Python genere archivos .pyc y usa buffering estándar
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Crea directorio de trabajo
WORKDIR /app

# Instala dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia solo los requirements primero (mejora el cache de Docker)
COPY requirements.txt requirements.txt
# Si usas el actualizado:
# COPY requirements_updated.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código al contenedor
COPY . .

# Exponer el puerto (ajusta según tu aplicación)
EXPOSE 8000

# Comando por defecto (ajústalo a tu entrypoint real)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]