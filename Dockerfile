FROM python:3.11.8-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    pkg-config \
    libcairo2 \
    libcairo2-dev \
    libfreetype6-dev \
    libpng-dev \
    python3-dev \
    meson \
    ninja-build \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip setuptools wheel

# Instalar primero pycairo sin aislamiento (clave)
RUN pip install --no-cache-dir --no-build-isolation pycairo==1.29.0

# Luego instalar el resto
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:$PORT"]
