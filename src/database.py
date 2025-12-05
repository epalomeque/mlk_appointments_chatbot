# src/database.py
from sqlmodel import create_engine, SQLModel, Session
from src.config import DATABASE_URL

# Crear el motor de base de datos
engine = create_engine(DATABASE_URL, echo=True)


def init_db():
    """Inicializar la base de datos creando las tablas"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Obtener una sesión de base de datos"""
    with Session(engine) as session:
        yield session

