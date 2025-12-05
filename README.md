# MLK Appointments Chatbot

Chatbot para agendar citas con integración a Ollama, construido con FastAPI, SQLModel y PostgreSQL/SQLite.

## 📋 Requisitos

### Para desarrollo local (SQLite)

- **Python 3.13** o superior
- **Ollama** corriendo y accesible (por defecto en `http://localhost:11434`)
- Un modelo de Ollama instalado (por defecto: `llama3`)

### Para producción con Docker

- **Docker** 20.10 o superior
- **Docker Compose** 2.0 o superior
- **Ollama** corriendo y accesible desde el contenedor

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd mlk-appointments-chatbot
```

### 2. Crear entorno virtual (recomendado)

```bash
python -m venv venv

# En Windows
venv\Scripts\activate

# En Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -e .
```

O instalar manualmente:

```bash
pip install fastapi>=0.123.4 uvicorn>=0.38.0 sqlmodel==0.0.19 python-dotenv==1.0.1 httpx==0.27.0 dateparser==1.2.0 "pydantic[email]>=2.0.0"
```

## ⚙️ Configuración

### Variables de entorno

Copia el archivo `env.example` a `.env` y configura las variables:

```bash
cp env.example .env
```

Edita el archivo `.env` con tus configuraciones:

```env
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# Database Configuration (para SQLite local)
DATABASE_URL=sqlite:///./app/db/database.db

# FastAPI Configuration
FASTAPI_PORT=8000
```

## 🏃 Arranque en Modo Local (SQLite)

### 1. Crear directorio para la base de datos

```bash
mkdir -p app/db
```

### 2. Iniciar el servidor

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

O usando Python directamente:

```bash
python -m uvicorn src.main:app --reload
```

El servidor estará disponible en: `http://localhost:8000`

### 3. Verificar que funciona

Abre tu navegador en `http://localhost:8000` o visita `http://localhost:8000/docs` para la documentación interactiva de la API.

## 🐳 Arranque con Docker

### 1. Configurar variables de entorno

Asegúrate de tener un archivo `.env` con las siguientes variables:

```env
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# Database Configuration (PostgreSQL en Docker)
DATABASE_URL=postgresql://mlkuser:mlkpassword@postgres:5432/mlkappointments

# PostgreSQL Configuration
POSTGRES_USER=mlkuser
POSTGRES_PASSWORD=mlkpassword
POSTGRES_DB=mlkappointments
POSTGRES_PORT=5432

# FastAPI Configuration
FASTAPI_PORT=8000
```

**Nota importante**: Si Ollama está corriendo en tu máquina host (no en Docker), desde el contenedor deberás usar `host.docker.internal` en lugar de `localhost`. Por ejemplo: `OLLAMA_BASE_URL=http://host.docker.internal:11434`

### 2. Construir e iniciar los servicios

```bash
docker-compose up -d --build
```

Esto construirá la imagen de la API y levantará los servicios de PostgreSQL y FastAPI.

### 3. Ver los logs

```bash
# Ver todos los logs
docker-compose logs -f

# Ver solo los logs de la API
docker-compose logs -f api

# Ver solo los logs de PostgreSQL
docker-compose logs -f postgres
```

### 4. Detener los servicios

```bash
docker-compose down
```

Para eliminar también los volúmenes (incluyendo la base de datos):

```bash
docker-compose down -v
```

## 📡 Consumo de Endpoints

### Documentación Interactiva

La API incluye documentación interactiva generada automáticamente:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Endpoints Disponibles

#### 1. Health Check

Verifica el estado del servicio y la configuración de Ollama.

```http
GET /health
```

**Respuesta:**
```json
{
  "status": "healthy",
  "ollama_url": "http://localhost:11434",
  "model": "llama3"
}
```

#### 2. Chat con el Bot

Envía un mensaje al chatbot para agendar una cita.

```http
POST /api/chat
Content-Type: application/json

{
  "message": "Quiero agendar una cita para mañana a las 3pm",
  "user_id": "optional-user-id"
}
```

**Respuesta:**
```json
{
  "response": "Perfecto, puedo ayudarte a agendar una cita...",
  "message_id": 1
}
```

**Ejemplo con cURL:**
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hola, necesito agendar una cita para el próximo lunes"
  }'
```

#### 3. Crear una Cita

Crea una nueva cita en el sistema.

```http
POST /api/appointments
Content-Type: application/json

{
  "name": "Juan Pérez",
  "email": "juan@example.com",
  "phone": "+1234567890",
  "date": "2024-12-20T15:00:00",
  "description": "Consulta médica"
}
```

**Respuesta:**
```json
{
  "id": 1,
  "name": "Juan Pérez",
  "email": "juan@example.com",
  "phone": "+1234567890",
  "date": "2024-12-20T15:00:00",
  "description": "Consulta médica",
  "created_at": "2024-12-19T10:30:00",
  "updated_at": null
}
```

**Ejemplo con cURL:**
```bash
curl -X POST "http://localhost:8000/api/appointments" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "María García",
    "email": "maria@example.com",
    "date": "2024-12-25T14:00:00",
    "description": "Revisión anual"
  }'
```

#### 4. Listar Citas

Obtiene todas las citas agendadas.

```http
GET /api/appointments?skip=0&limit=100
```

**Parámetros de consulta:**
- `skip` (opcional): Número de registros a saltar (default: 0)
- `limit` (opcional): Número máximo de registros a retornar (default: 100)

**Respuesta:**
```json
{
  "appointments": [
    {
      "id": 1,
      "name": "Juan Pérez",
      "email": "juan@example.com",
      "date": "2024-12-20T15:00:00",
      "description": "Consulta médica",
      "created_at": "2024-12-19T10:30:00",
      "updated_at": null
    }
  ],
  "total": 1
}
```

**Ejemplo con cURL:**
```bash
curl -X GET "http://localhost:8000/api/appointments?skip=0&limit=10"
```

#### 5. Obtener una Cita por ID

Obtiene los detalles de una cita específica.

```http
GET /api/appointments/{appointment_id}
```

**Ejemplo con cURL:**
```bash
curl -X GET "http://localhost:8000/api/appointments/1"
```

#### 6. Eliminar una Cita

Elimina una cita del sistema.

```http
DELETE /api/appointments/{appointment_id}
```

**Respuesta:**
```json
{
  "message": "Cita eliminada exitosamente"
}
```

**Ejemplo con cURL:**
```bash
curl -X DELETE "http://localhost:8000/api/appointments/1"
```

### Ejemplos de Uso Completo

#### Flujo completo: Chat y creación de cita

```bash
# 1. Iniciar conversación con el bot
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Quiero agendar una cita"}'

# 2. El bot responderá y podrás continuar la conversación
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Mi nombre es Ana y quiero una cita para mañana a las 2pm"}'

# 3. Crear la cita manualmente (o el bot puede guiarte)
curl -X POST "http://localhost:8000/api/appointments" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ana López",
    "email": "ana@example.com",
    "date": "2024-12-20T14:00:00",
    "description": "Cita solicitada vía chatbot"
  }'

# 4. Verificar las citas agendadas
curl -X GET "http://localhost:8000/api/appointments"
```

## 🔧 Solución de Problemas

### Error de conexión con Ollama

Si obtienes errores al conectar con Ollama:

1. Verifica que Ollama esté corriendo: `curl http://localhost:11434/api/tags`
2. Verifica que la IP sea accesible desde tu máquina/contenedor
3. Asegúrate de que el modelo esté instalado: `ollama list`
4. Si usas Docker, verifica la configuración de red

### Error de base de datos

**SQLite:**
- Verifica que el directorio `app/db` exista y tenga permisos de escritura

**PostgreSQL (Docker):**
- Verifica que el contenedor de PostgreSQL esté corriendo: `docker-compose ps`
- Revisa los logs: `docker-compose logs postgres`
- Verifica las credenciales en el archivo `.env`

### Puerto ya en uso

Si el puerto 8000 está ocupado:

1. Cambia el puerto en `.env`: `FASTAPI_PORT=8001`
2. O detén el proceso que está usando el puerto

## 📁 Estructura del Proyecto

```
mlk-appointments-chatbot/
├── src/
│   ├── __init__.py
│   ├── main.py              # Aplicación FastAPI principal
│   ├── config.py            # Configuración y variables de entorno
│   ├── models.py            # Modelos SQLModel
│   ├── schemas.py           # Esquemas Pydantic para validación
│   ├── database.py          # Configuración de base de datos
│   └── ollama_service.py    # Servicio de integración con Ollama
├── app/
│   └── db/                  # Base de datos SQLite (si se usa)
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── env.example
└── README.md
```

## 🧪 Testing

Puedes usar el archivo `test_main.http` (si está disponible) o herramientas como:

- **Postman**
- **Thunder Client** (extensión de VS Code)
- **cURL** (línea de comandos)
- **Swagger UI** en `/docs`

## 📝 Notas Adicionales

- El chatbot utiliza el historial de conversaciones y las citas existentes para proporcionar contexto mejorado
- Las fechas deben estar en formato ISO 8601: `YYYY-MM-DDTHH:MM:SS`
- El servicio de chat guarda automáticamente el historial de conversaciones
- La base de datos se inicializa automáticamente al iniciar la aplicación

## 📄 Licencia

[Especificar licencia si aplica]

