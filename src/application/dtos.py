from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from src.domain.value_objects import Rol, EstadoDeReserva


# ==========================================
# DTO DE ERROR (Contrato unificado para Swagger UI)
# ==========================================
class ErrorRespuestaDTO(BaseModel):
    """Esquema devuelto cuando falla una regla de negocio o una comprobación de permisos."""

    error: str = Field(
        ...,
        description="Categoría o tipo de error producido en la capa de negocio.",
        examples=["Regla de Negocio"],
    )
    mensaje: str = Field(
        ...,
        description="Explicación detallada de la regla infringida.",
        examples=["La clase no cuenta con cupo disponible."],
    )
    solucion: str = Field(
        ...,
        description="Acción sugerida para mitigar o corregir el error.",
        examples=["Selecciona otro horario o inscríbete en lista de espera."],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "error": "Regla de Negocio",
                    "mensaje": "La membresía del socio no está vigente o se encuentra suspendida.",
                    "solucion": "Renueva tu plan en recepción antes de reservar.",
                }
            ]
        }
    )


# ==========================================
# COMMANDS (Formularios de entrada para modificar datos)
# ==========================================
class ComandoReservar(BaseModel):
    clase_id: str = Field(
        ...,
        description="Identificador único de la clase deportiva programada (ej. FIT-P001).",
        examples=["FIT-P001"],
    )
    socio_id: str = Field(
        ...,
        description="Identificador del socio titular que solicita el lugar (ej. FIT-C001).",
        examples=["FIT-C001"],
    )
    actor_id: str = Field(
        ...,
        description="ID del usuario autenticado que efectúa la solicitud (socio o personal).",
        examples=["FIT-C001"],
    )
    actor_rol: Rol = Field(
        ...,
        description="Rol con el que se ejecuta la transacción en el sistema (BR-01 a BR-04).",
        examples=[Rol.SOCIO],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "clase_id": "FIT-P001",
                    "socio_id": "FIT-C001",
                    "actor_id": "FIT-C001",
                    "actor_rol": "Socio",
                }
            ]
        }
    )


class ComandoCancelar(BaseModel):
    clase_id: str = Field(
        ...,
        description="Identificador único de la clase cuya reserva se cancelará.",
        examples=["FIT-P001"],
    )
    socio_id: str = Field(
        ...,
        description="Identificador del socio que renuncia a su reservación.",
        examples=["FIT-C001"],
    )
    actor_id: str = Field(
        ...,
        description="ID del usuario que solicita la cancelación (socio o personal).",
        examples=["FIT-C001"],
    )
    actor_rol: Rol = Field(
        ...,
        description="Rol con el que se solicita la cancelación.",
        examples=[Rol.SOCIO],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "clase_id": "FIT-P001",
                    "socio_id": "FIT-C001",
                    "actor_id": "FIT-C001",
                    "actor_rol": "Socio",
                }
            ]
        }
    )


class ComandoRegistrarAsistencia(BaseModel):
    clase_id: str = Field(
        ...,
        description="Identificador de la clase deportiva.",
        examples=["FIT-P001"],
    )
    socio_id: str = Field(
        ...,
        description="Identificador del socio que se presenta al gimnasio.",
        examples=["FIT-C001"],
    )
    actor_id: str = Field(
        ...,
        description="ID del empleado o instructor que verifica el acceso.",
        examples=["FIT-R001"],
    )
    actor_rol: Rol = Field(
        ...,
        description="Rol del operador (generalmente Recepción o Instructor).",
        examples=[Rol.RECEPCION],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "clase_id": "FIT-P001",
                    "socio_id": "FIT-C001",
                    "actor_id": "FIT-R001",
                    "actor_rol": "Recepción",
                }
            ]
        }
    )


# ==========================================
# QUERIES / RESPUESTAS (Formularios de salida para leer datos)
# ==========================================
class RespuestaReserva(BaseModel):
    """Comprobante que el sistema devuelve al usuario al reservar exitosamente."""

    mensaje: str = Field(
        ...,
        description="Mensaje confirmatorio para el usuario.",
        examples=["¡Tu lugar está confirmado!"],
    )
    reserva_id: str = Field(
        ...,
        description="Identificador único (UUID) de la reservación creada.",
        examples=["a81bc81b-dead-4e5d-abff-90865d1e13b1"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "mensaje": "¡Tu lugar está confirmado!",
                    "reserva_id": "a81bc81b-dead-4e5d-abff-90865d1e13b1",
                }
            ]
        }
    )


class ReservaDTO(BaseModel):
    id: str = Field(
        ...,
        description="Identificador único de la reservación.",
        examples=["a81bc81b-dead-4e5d-abff-90865d1e13b1"],
    )
    clase_id: str = Field(
        ...,
        description="Identificador de la clase asociada.",
        examples=["FIT-P001"],
    )
    socio_id: str = Field(
        ...,
        description="Identificador del socio titular.",
        examples=["FIT-C001"],
    )
    estado: EstadoDeReserva = Field(
        ...,
        description="Estado actual de la reserva en el ciclo de vida.",
        examples=[EstadoDeReserva.ACTIVA],
    )
    fecha_creacion: datetime = Field(
        ...,
        description="Timestamp ISO 8601 del momento de registro de la reserva.",
        examples=["2026-11-06T10:30:00"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "a81bc81b-dead-4e5d-abff-90865d1e13b1",
                    "clase_id": "FIT-P001",
                    "socio_id": "FIT-C001",
                    "estado": "ACTIVA",
                    "fecha_creacion": "2026-11-06T10:30:00",
                }
            ]
        }
    )


class ClaseDisponibleDTO(BaseModel):
    id: str = Field(
        ...,
        description="Identificador único de la clase programada.",
        examples=["FIT-P001"],
    )
    nombre: str = Field(
        ...,
        description="Nombre descriptivo de la disciplina o clase deportiva.",
        examples=["CrossFit Matutino"],
    )
    horario_inicio: datetime = Field(
        ...,
        description="Fecha y hora de inicio de la clase (ISO 8601).",
        examples=["2026-11-10T07:00:00"],
    )
    horario_fin: datetime = Field(
        ...,
        description="Fecha y hora de finalización de la clase (ISO 8601).",
        examples=["2026-11-10T08:00:00"],
    )
    lugares_disponibles: int = Field(
        ...,
        description="Número de cupos restantes disponibles para reserva inmediata.",
        examples=[8],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "FIT-P001",
                    "nombre": "CrossFit Matutino",
                    "horario_inicio": "2026-11-10T07:00:00",
                    "horario_fin": "2026-11-10T08:00:00",
                    "lugares_disponibles": 8,
                }
            ]
        }
    )
