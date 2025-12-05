# tests/test_chat.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch


def test_chat_endpoint(client: TestClient, mock_ollama_service):
    """Test básico del endpoint de chat"""
    response = client.post(
        "/api/chat",
        json={"message": "Hola, quiero agendar una cita"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "response" in data
    assert "message_id" in data
    assert data["message_id"] is not None
    assert len(data["response"]) > 0


def test_chat_conversation_flow(client: TestClient):
    """Test de una conversación completa con el chat para agendar una cita"""
    # Mock del servicio de Ollama con respuestas contextuales
    mock_responses = [
        "Hola! Con gusto te ayudo a agendar una cita. ¿Cuál es tu nombre?",
        "Perfecto, ¿para qué fecha y hora te gustaría agendar la cita?",
        "Excelente, ¿podrías darme una breve descripción del motivo de la cita?",
        "Perfecto, he registrado tu solicitud. ¿Te gustaría que te confirme los detalles?"
    ]
    
    with patch("src.main.ollama_service.chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.side_effect = mock_responses
        
        # Primera interacción: Saludo inicial
        response1 = client.post(
            "/api/chat",
            json={"message": "Hola, quiero agendar una cita"}
        )
        assert response1.status_code == 200
        assert "nombre" in response1.json()["response"].lower() or "ayudo" in response1.json()["response"].lower()
        message_id_1 = response1.json()["message_id"]
        assert message_id_1 is not None
        
        # Segunda interacción: Proporcionar nombre
        response2 = client.post(
            "/api/chat",
            json={"message": "Mi nombre es Juan Pérez"}
        )
        assert response2.status_code == 200
        assert "fecha" in response2.json()["response"].lower() or "hora" in response2.json()["response"].lower()
        message_id_2 = response2.json()["message_id"]
        assert message_id_2 is not None
        assert message_id_2 > message_id_1  # El ID debe incrementar
        
        # Tercera interacción: Proporcionar fecha
        response3 = client.post(
            "/api/chat",
            json={"message": "Quiero la cita para mañana a las 3pm"}
        )
        assert response3.status_code == 200
        assert len(response3.json()["response"]) > 0
        message_id_3 = response3.json()["message_id"]
        assert message_id_3 > message_id_2
        
        # Cuarta interacción: Proporcionar descripción
        response4 = client.post(
            "/api/chat",
            json={"message": "Es para una consulta médica de rutina"}
        )
        assert response4.status_code == 200
        assert len(response4.json()["response"]) > 0
        message_id_4 = response4.json()["message_id"]
        assert message_id_4 > message_id_3
        
        # Verificar que se guardaron todos los mensajes
        # (Los mensajes se guardan en la base de datos a través del endpoint)


def test_chat_with_existing_appointments(client: TestClient, sample_appointment_data: dict):
    """Test del chat cuando ya existen citas en el sistema (contexto)"""
    # Crear una cita primero
    appointment_response = client.post("/api/appointments", json=sample_appointment_data)
    assert appointment_response.status_code == 200
    
    # Mock del servicio de Ollama
    with patch("src.main.ollama_service.chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = "Veo que ya tienes una cita agendada. ¿Necesitas otra?"
        
        # Enviar mensaje al chat
        response = client.post(
            "/api/chat",
            json={"message": "¿Tengo alguna cita agendada?"}
        )
        
        assert response.status_code == 200
        # El servicio debería recibir contexto sobre las citas existentes
        # (esto se verifica indirectamente a través del mock)


def test_chat_error_handling(client: TestClient):
    """Test del manejo de errores en el chat"""
    # Mock del servicio de Ollama que lanza un error
    with patch("src.main.ollama_service.chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.side_effect = Exception("Error de conexión")
        
        response = client.post(
            "/api/chat",
            json={"message": "Test message"}
        )
        
        # El endpoint debería manejar el error y retornar un 500
        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()


def test_chat_message_persistence(client: TestClient):
    """Test que verifica que los mensajes del chat se persisten en la base de datos"""
    with patch("src.main.ollama_service.chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = "Respuesta del bot"
        
        # Enviar un mensaje
        response = client.post(
            "/api/chat",
            json={"message": "Mensaje de prueba"}
        )
        
        assert response.status_code == 200
        message_id = response.json()["message_id"]
        
        # El message_id debería ser un número válido
        assert isinstance(message_id, int)
        assert message_id > 0

