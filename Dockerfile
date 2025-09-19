# Dockerfile

# 1. Usamos una imagen oficial y ligera de Python como base
FROM python:3.11-slim

# 2. (Opcional pero recomendado) Instalamos las 'locales' en español para que Babel funcione bien con las fechas
RUN apt-get update && apt-get install -y locales \
    && sed -i -e 's/# es_ES.UTF-8 UTF-8/es_ES.UTF-8 UTF-8/' /etc/locale.gen \
    && locale-gen
ENV LANG es_ES.UTF-8
ENV LANGUAGE es_ES:es
ENV LC_ALL es_ES.UTF-8

# 3. Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# 4. Copiamos solo el archivo de requisitos primero para aprovechar la caché de Docker
# Si no cambian los requisitos, no se reinstalarán las dependencias en cada build
COPY requirements.txt .

# 5. Instalamos las dependencias del proyecto
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiamos todo el resto del código del proyecto al contenedor
COPY . .

# 7. El comando que se ejecutará cuando el contenedor arranque
CMD ["python3", "main.py"]