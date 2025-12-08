# src/tools.py
from datetime import datetime
from typing import List, Optional
import logging

from sqlmodel import Session, select

from src.database import engine
from src.models import Appointment


logger = logging.getLogger(__name__)


def get_appointment_lists(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: Optional[int] = 48,
) -> List[Appointment]:
    """Obtener la lista de citas.

    Si no se especifica un rango, devuelve las próximas citas desde "ahora".

    Args:
        start: Fecha/ahora inicial del rango (incluida). Si es None, se usa ahor.
        end: Fecha/hora final del rango (incluida). Si es None, no se limita por arriba.
        limit: Máximo de registros a devolver. Si es None, sin límite explícito.

    Returns:
        Lista de objetos Appointment ordenados por fecha ascendente.
    """
    logger.info(
        "Iniciando get_appointment_lists(start=%s, end=%s, limit=%s)", start, end, limit
    )
    start_dt = start or datetime.utcnow()

    stmt = select(Appointment).where(Appointment.date >= start_dt)
    if end is not None:
        stmt = stmt.where(Appointment.date <= end)
    stmt = stmt.order_by(Appointment.date.asc())
    if isinstance(limit, int) and limit > 0:
        stmt = stmt.limit(limit)

    with Session(engine) as session:
        return list(session.exec(stmt).all())


def check_occupied_slots(start: datetime, end: datetime) -> List[Appointment]:
    """Verificar los horarios ocupados dentro de un rango.

    Dado que el modelo `Appointment` solo almacena un `date` puntual (sin duración),
    se considera ocupado todo `Appointment.date` que caiga dentro del intervalo
    [start, end].

    Args:
        start: Inicio del rango (incluido).
        end: Fin del rango (incluido).

    Returns:
        Lista de citas cuyo `date` está entre `start` y `end` (ambos inclusive),
        ordenadas por fecha ascendente.
    """
    logger.info(
        "Iniciando check_occupied_slots(start=%s, end=%s)", start, end
    )
    if end < start:
        raise ValueError("El parámetro 'end' no puede ser anterior a 'start'.")

    stmt = (
        select(Appointment)
        .where(Appointment.date >= start)
        .where(Appointment.date <= end)
        .order_by(Appointment.date.asc())
    )

    with Session(engine) as session:
        return list(session.exec(stmt).all())


def save_appointment(
    name: str,
    date: datetime,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    description: Optional[str] = None,
) -> Appointment:
    """Guardar una cita confirmada en la base de datos.

    Args:
        name: Nombre de la persona que agenda la cita. Obligatorio.
        date: Fecha/hora de la cita (UTC) como objeto ``datetime``. Obligatorio.
        email: Correo electrónico opcional.
        phone: Teléfono opcional.
        description: Descripción/notas opcionales.

    Returns:
        La instancia de ``Appointment`` creada y persistida.
    """
    logger.info(
        "Iniciando save_appointment(name=%s, date=%s, email=%s, phone=%s)",
        name,
        date,
        email,
        phone,
    )
    if not name:
        raise ValueError("El parámetro 'name' es obligatorio.")
    if not isinstance(date, datetime):
        raise TypeError("El parámetro 'date' debe ser un datetime válido.")

    appointment = Appointment(
        name=name,
        email=email,
        phone=phone,
        date=date,
        description=description,
    )

    with Session(engine) as session:
        session.add(appointment)
        session.commit()
        session.refresh(appointment)
        return appointment


def update_appointment(
    appointment_id: int,
    name: Optional[str] = None,
    date: Optional[datetime] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    description: Optional[str] = None,
) -> Appointment:
    """Modificar una cita existente.

    Args:
        appointment_id: ID de la cita a modificar. Obligatorio.
        name: Nuevo nombre (opcional).
        date: Nueva fecha/hora (opcional).
        email: Nuevo email (opcional).
        phone: Nuevo teléfono (opcional).
        description: Nueva descripción (opcional).

    Returns:
        La instancia de ``Appointment`` actualizada.

    Raises:
        LookupError: Si no existe la cita con el ID indicado.
        TypeError: Si ``date`` se proporciona y no es un ``datetime`` válido.
    """
    logger.info(
        "Iniciando update_appointment(id=%s, name=%s, date=%s, email=%s, phone=%s)",
        appointment_id,
        name,
        date,
        email,
        phone,
    )
    if date is not None and not isinstance(date, datetime):
        raise TypeError("El parámetro 'date' debe ser un datetime válido si se proporciona.")

    with Session(engine) as session:
        appt = session.get(Appointment, appointment_id)
        if not appt:
            raise LookupError(f"No existe la cita con id={appointment_id}.")

        if name is not None:
            appt.name = name
        if email is not None:
            appt.email = email
        if phone is not None:
            appt.phone = phone
        if date is not None:
            appt.date = date
        if description is not None:
            appt.description = description

        appt.updated_at = datetime.utcnow()

        session.add(appt)
        session.commit()
        session.refresh(appt)
        return appt


def delete_appointment(appointment_id: int) -> bool:
    """Borrar una cita por su ID.

    Args:
        appointment_id: ID de la cita a eliminar.

    Returns:
        ``True`` si la cita fue eliminada.

    Raises:
        LookupError: Si no existe la cita con el ID indicado.
    """
    logger.info("Iniciando delete_appointment(id=%s)", appointment_id)
    with Session(engine) as session:
        appt = session.get(Appointment, appointment_id)
        if not appt:
            raise LookupError(f"No existe la cita con id={appointment_id}.")
        session.delete(appt)
        session.commit()
        return True
