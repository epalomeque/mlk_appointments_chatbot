# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from datetime import datetime
from unittest.mock import AsyncMock, patch

from src.main import app, get_session
from src.models import Appointment, ChatMessage


# Base de datos en memoria para testing
@pytest.fixture(name="session")
def session_fixture():
    """Crear una sesión de base de datos en memoria para testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Crear un cliente de prueba para FastAPI"""
    def get_session_override():
        return session
    
    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="mock_ollama_service")
def mock_ollama_service_fixture():
    """Mock del servicio de Ollama para evitar llamadas reales durante los tests"""
    with patch("src.main.ollama_service.chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = "Respuesta simulada del chatbot"
        yield mock_chat


@pytest.fixture(name="sample_appointment_data")
def sample_appointment_data_fixture():
    """Datos de ejemplo para crear una cita"""
    return {
        "name": "Juan Pérez",
        "email": "juan@example.com",
        "phone": "+1234567890",
        "date": "2024-12-20T15:00:00",
        "description": "Consulta médica"
    }

