# src/models.py
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, create_engine, Session


class Appointment(SQLModel, table=True):
    """Modelo para las citas agendadas"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    email: Optional[str] = None
    phone: Optional[str] = None
    date: datetime = Field(index=True)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class ChatMessage(SQLModel, table=True):
    """Modelo para almacenar el historial de conversación"""
    id: Optional[int] = Field(default=None, primary_key=True)
    # Identificador del usuario/cliente para encadenar turnos
    user_id: Optional[str] = Field(default=None, index=True)
    user_message: str
    bot_response: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

