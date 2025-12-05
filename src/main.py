# src/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from datetime import datetime
from typing import List
from uuid import uuid4

from src.database import init_db, get_session
from src.models import Appointment, ChatMessage
from src.schemas import (
    ChatRequest, ChatResponse, 
    AppointmentCreate, AppointmentUpdate, AppointmentResponse, AppointmentListResponse
)
from src.ollama_service import ollama_service

app = FastAPI(
    title="MLK Appointments Chatbot",
    description="Chatbot para agendar citas con integración Ollama",
    version="0.1.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Inicializar la base de datos al iniciar la aplicación"""
    init_db()


@app.on_event("shutdown")
async def shutdown_event():
    """Cerrar conexiones al apagar la aplicación"""
    await ollama_service.close()


@app.get("/")
async def root():
    return {
        "message": "MLK Appointments Chatbot API",
        "version": "0.1.0",
        "endpoints": {
            "chat": "/api/chat",
            "appointments": "/api/appointments",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Endpoint de salud para verificar el estado del servicio"""
    return {
        "status": "healthy",
        "ollama_url": ollama_service.base_url,
        "model": ollama_service.model
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session: Session = Depends(get_session)
):
    """
    Endpoint para interactuar con el chatbot de Ollama
    """
    try:
        # Obtener contexto de citas existentes para mejorar las respuestas
        appointments = session.exec(
            select(Appointment).order_by(Appointment.date.desc()).limit(5)
        ).all()
        
        # Construir contexto combinando citas recientes y el contexto opcional enviado por el cliente
        context_parts = []
        if appointments:
            context_parts.append(
                "Citas recientes: " + ", ".join([
                    f"{apt.name} el {apt.date.strftime('%Y-%m-%d %H:%M')}"
                    for apt in appointments
                ])
            )
        if getattr(request, "context", None):
            context_parts.append(f"Contexto del usuario: {request.context}")

        context = "\n".join(context_parts) if context_parts else None
        
        # Determinar o generar user_id para mantener el contexto entre turnos
        user_id = (request.user_id or "").strip() or str(uuid4())

        # Recuperar historial reciente de este usuario
        history_items: List[ChatMessage] = session.exec(
            select(ChatMessage)
            .where(ChatMessage.user_id == user_id)
            .order_by(ChatMessage.created_at.asc())
        ).all()
        history = [(item.user_message, item.bot_response) for item in history_items]

        # Obtener respuesta de Ollama, pasando también historial
        response_text = await ollama_service.chat(request.message, context, history)
        
        # Guardar el mensaje en el historial
        chat_message = ChatMessage(
            user_id=user_id,
            user_message=request.message,
            bot_response=response_text
        )
        session.add(chat_message)
        session.commit()
        session.refresh(chat_message)
        
        return ChatResponse(
            response=response_text,
            message_id=chat_message.id,
            user_id=user_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el chat: {str(e)}")


@app.post("/api/appointments", response_model=AppointmentResponse)
async def create_appointment(
    appointment: AppointmentCreate,
    session: Session = Depends(get_session)
):
    """
    Crear una nueva cita
    """
    try:
        db_appointment = Appointment(
            name=appointment.name,
            email=appointment.email,
            phone=appointment.phone,
            date=appointment.date,
            description=appointment.description
        )
        session.add(db_appointment)
        session.commit()
        session.refresh(db_appointment)
        return AppointmentResponse.model_validate(db_appointment)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear la cita: {str(e)}")


@app.get("/api/appointments", response_model=AppointmentListResponse)
async def list_appointments(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """
    Listar todas las citas
    """
    try:
        statement = select(Appointment).order_by(Appointment.date.asc())
        appointments = session.exec(statement.offset(skip).limit(limit)).all()
        total = len(session.exec(select(Appointment)).all())
        
        return AppointmentListResponse(
            appointments=[AppointmentResponse.model_validate(apt) for apt in appointments],
            total=total
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar citas: {str(e)}")


@app.get("/api/appointments/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: int,
    session: Session = Depends(get_session)
):
    """
    Obtener una cita por ID
    """
    appointment = session.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return AppointmentResponse.model_validate(appointment)


@app.put("/api/appointments/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    appointment_update: AppointmentUpdate,
    session: Session = Depends(get_session)
):
    """
    Actualizar una cita existente
    """
    appointment = session.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    try:
        # Actualizar solo los campos proporcionados
        update_data = appointment_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(appointment, field, value)
        
        appointment.updated_at = datetime.utcnow()
        session.add(appointment)
        session.commit()
        session.refresh(appointment)
        return AppointmentResponse.model_validate(appointment)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar la cita: {str(e)}")


@app.delete("/api/appointments/{appointment_id}")
async def delete_appointment(
    appointment_id: int,
    session: Session = Depends(get_session)
):
    """
    Eliminar una cita
    """
    appointment = session.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    session.delete(appointment)
    session.commit()
    return {"message": "Cita eliminada exitosamente"}
