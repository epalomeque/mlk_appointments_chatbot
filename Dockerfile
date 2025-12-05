# Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de configuración
COPY pyproject.toml ./

# Instalar dependencias del proyecto usando pip
RUN pip install --no-cache-dir \
    fastapi>=0.123.4 \
    uvicorn>=0.38.0 \
    sqlmodel==0.0.19 \
    python-dotenv==1.0.1 \
    httpx==0.27.0 \
    dateparser==1.2.0 \
    psycopg2-binary>=2.9.9 \
    "pydantic[email]>=2.0.0"

# Copiar el código de la aplicación
COPY src/ ./src/
COPY .env* ./

# Crear directorio para la base de datos SQLite (si se usa)
RUN mkdir -p app/db

# Exponer el puerto
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

