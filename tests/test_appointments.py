# tests/test_appointments.py
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient


def test_create_appointment(client: TestClient, sample_appointment_data: dict):
    """Test para crear una nueva cita"""
    response = client.post("/api/appointments", json=sample_appointment_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["name"] == sample_appointment_data["name"]
    assert data["email"] == sample_appointment_data["email"]
    assert data["phone"] == sample_appointment_data["phone"]
    assert data["description"] == sample_appointment_data["description"]
    assert "id" in data
    assert "created_at" in data
    assert data["updated_at"] is None


def test_create_appointment_minimal(client: TestClient):
    """Test para crear una cita con datos mínimos"""
    appointment_data = {
        "name": "María García",
        "date": "2024-12-25T10:00:00"
    }
    
    response = client.post("/api/appointments", json=appointment_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["name"] == appointment_data["name"]
    assert data["email"] is None
    assert data["phone"] is None
    assert data["description"] is None


def test_get_appointment(client: TestClient, sample_appointment_data: dict):
    """Test para obtener una cita por ID"""
    # Primero crear una cita
    create_response = client.post("/api/appointments", json=sample_appointment_data)
    assert create_response.status_code == 200
    appointment_id = create_response.json()["id"]
    
    # Luego obtenerla
    response = client.get(f"/api/appointments/{appointment_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == appointment_id
    assert data["name"] == sample_appointment_data["name"]
    assert data["email"] == sample_appointment_data["email"]


def test_get_appointment_not_found(client: TestClient):
    """Test para obtener una cita que no existe"""
    response = client.get("/api/appointments/99999")
    
    assert response.status_code == 404
    assert "no encontrada" in response.json()["detail"].lower()


def test_list_appointments(client: TestClient, sample_appointment_data: dict):
    """Test para listar todas las citas"""
    # Crear múltiples citas
    for i in range(3):
        appointment_data = sample_appointment_data.copy()
        appointment_data["name"] = f"Persona {i+1}"
        appointment_data["date"] = (datetime.now() + timedelta(days=i+1)).isoformat()
        client.post("/api/appointments", json=appointment_data)
    
    # Listar todas las citas
    response = client.get("/api/appointments")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "appointments" in data
    assert "total" in data
    assert data["total"] == 3
    assert len(data["appointments"]) == 3


def test_list_appointments_with_pagination(client: TestClient, sample_appointment_data: dict):
    """Test para listar citas con paginación"""
    # Crear 5 citas
    for i in range(5):
        appointment_data = sample_appointment_data.copy()
        appointment_data["name"] = f"Persona {i+1}"
        appointment_data["date"] = (datetime.now() + timedelta(days=i+1)).isoformat()
        client.post("/api/appointments", json=appointment_data)
    
    # Listar con límite
    response = client.get("/api/appointments?skip=0&limit=2")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 5
    assert len(data["appointments"]) == 2


def test_update_appointment(client: TestClient, sample_appointment_data: dict):
    """Test para actualizar una cita existente"""
    # Crear una cita
    create_response = client.post("/api/appointments", json=sample_appointment_data)
    assert create_response.status_code == 200
    appointment_id = create_response.json()["id"]
    
    # Actualizar la cita
    update_data = {
        "name": "Juan Pérez Actualizado",
        "phone": "+9876543210",
        "description": "Consulta actualizada"
    }
    
    response = client.put(f"/api/appointments/{appointment_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == appointment_id
    assert data["name"] == update_data["name"]
    assert data["phone"] == update_data["phone"]
    assert data["description"] == update_data["description"]
    # El email no debería cambiar porque no se actualizó
    assert data["email"] == sample_appointment_data["email"]
    assert data["updated_at"] is not None


def test_update_appointment_partial(client: TestClient, sample_appointment_data: dict):
    """Test para actualizar solo algunos campos de una cita"""
    # Crear una cita
    create_response = client.post("/api/appointments", json=sample_appointment_data)
    appointment_id = create_response.json()["id"]
    
    # Actualizar solo el nombre
    update_data = {"name": "Nuevo Nombre"}
    
    response = client.put(f"/api/appointments/{appointment_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["name"] == "Nuevo Nombre"
    # Los demás campos deben mantenerse
    assert data["email"] == sample_appointment_data["email"]
    assert data["phone"] == sample_appointment_data["phone"]


def test_update_appointment_not_found(client: TestClient):
    """Test para actualizar una cita que no existe"""
    update_data = {"name": "Nuevo Nombre"}
    
    response = client.put("/api/appointments/99999", json=update_data)
    
    assert response.status_code == 404
    assert "no encontrada" in response.json()["detail"].lower()


def test_delete_appointment(client: TestClient, sample_appointment_data: dict):
    """Test para eliminar una cita"""
    # Crear una cita
    create_response = client.post("/api/appointments", json=sample_appointment_data)
    appointment_id = create_response.json()["id"]
    
    # Eliminar la cita
    response = client.delete(f"/api/appointments/{appointment_id}")
    
    assert response.status_code == 200
    assert "eliminada" in response.json()["message"].lower()
    
    # Verificar que la cita ya no existe
    get_response = client.get(f"/api/appointments/{appointment_id}")
    assert get_response.status_code == 404


def test_delete_appointment_not_found(client: TestClient):
    """Test para eliminar una cita que no existe"""
    response = client.delete("/api/appointments/99999")
    
    assert response.status_code == 404
    assert "no encontrada" in response.json()["detail"].lower()


def test_appointment_crud_flow(client: TestClient):
    """Test completo del flujo CRUD: crear, leer, actualizar, eliminar"""
    # 1. Crear
    appointment_data = {
        "name": "Test User",
        "email": "test@example.com",
        "date": "2024-12-20T15:00:00",
        "description": "Test appointment"
    }
    
    create_response = client.post("/api/appointments", json=appointment_data)
    assert create_response.status_code == 200
    appointment_id = create_response.json()["id"]
    
    # 2. Leer
    get_response = client.get(f"/api/appointments/{appointment_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == appointment_data["name"]
    
    # 3. Actualizar
    update_data = {"name": "Updated User", "description": "Updated description"}
    update_response = client.put(f"/api/appointments/{appointment_id}", json=update_data)
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated User"
    
    # 4. Eliminar
    delete_response = client.delete(f"/api/appointments/{appointment_id}")
    assert delete_response.status_code == 200
    
    # 5. Verificar que ya no existe
    get_response = client.get(f"/api/appointments/{appointment_id}")
    assert get_response.status_code == 404

