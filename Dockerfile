# Imagen base ligera y estable
FROM python:3.11-slim

# Evita archivos .pyc y mejora logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema necesarias para pycairo y gráficos
RUN apt-get update && apt-get install -y \
    gcc \
    libcairo2 \
    libcairo2-dev \
    pkg-config \
    python3-dev \
    build-essential \
    libfreetype6-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar primero requirements para cache eficiente
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el proyecto
COPY . .

# Exponer puerto (Railway usa variable PORT)
EXPOSE 8000

# Comando de producción
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:$PORT"]
