from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from src.domain.value_objects import Rol, EstadoDeReserva


# ==========================================
# COMMANDS (Formularios de entrada para modificar datos)
# ==========================================
class ComandoReservar(BaseModel):
    clase_id: str
    socio_id: str
    actor_id: str
    actor_rol: Rol


class ComandoCancelar(BaseModel):
    clase_id: str
    socio_id: str
    actor_id: str
    actor_rol: Rol


class ComandoRegistrarAsistencia(BaseModel):
    clase_id: str
    socio_id: str
    actor_id: str
    actor_rol: Rol


# ==========================================
# QUERIES / RESPUESTAS (Formularios de salida para leer datos)
# ==========================================
class ReservaDTO(BaseModel):
    id: str
    clase_id: str
    socio_id: str
    estado: EstadoDeReserva
    fecha_creacion: datetime


class ClaseDisponibleDTO(BaseModel):
    id: str
    nombre: str
    horario_inicio: datetime
    horario_fin: datetime
    lugares_disponibles: int
