# src/schemas.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class ChatRequest(BaseModel):
    """Esquema para solicitud de chat"""
    message: str
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Esquema para respuesta de chat"""
    response: str
    message_id: Optional[int] = None


class AppointmentCreate(BaseModel):
    """Esquema para crear una cita"""
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    date: datetime
    description: Optional[str] = None


class AppointmentResponse(BaseModel):
    """Esquema para respuesta de cita"""
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    date: datetime
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AppointmentListResponse(BaseModel):
    """Esquema para lista de citas"""
    appointments: list[AppointmentResponse]
    total: int

