from pydantic import BaseModel, ConfigDict
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

    # Esto le dice a Swagger exactamente qué poner de ejemplo en la cajita
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "clase_id": "FIT-P001",
                "socio_id": "FIT-C001",
                "actor_id": "FIT-C001",
                "actor_rol": "Socio",
            }
        }
    )


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
class RespuestaReserva(BaseModel):
    """El comprobante que el sistema le devuelve al usuario al reservar."""

    mensaje: str
    reserva_id: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mensaje": "¡Tu lugar está confirmado!",
                "reserva_id": "b1b2b3-...",
            }
        }
    )


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
