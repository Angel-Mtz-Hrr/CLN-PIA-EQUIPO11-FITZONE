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
        description="ID del usuario que solicita la cancelación (socio o recepción).",
        examples=["FIT-C001"],
    )
    actor_rol: Rol = Field(
        ...,
        description="Rol del solicitante para validar autorización.",
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
        description="ID del empleado de recepción o instructor que valida en puerta.",
        examples=["FIT-R001"],
    )
    actor_rol: Rol = Field(
        ...,
        description="Rol del operador (debe ser Recepción según BR-02).",
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


class RespuestaAccionDTO(BaseModel):
    """Respuesta para transiciones de estado como cancelaciones o asistencias."""

    mensaje: str = Field(
        ...,
        description="Descripción del resultado de la acción ejecutada.",
        examples=["Reserva cancelada exitosamente."],
    )
    clase_id: str = Field(
        ...,
        description="ID de la clase afectada.",
        examples=["FIT-P001"],
    )
    socio_id: str = Field(
        ...,
        description="ID del socio involucrado.",
        examples=["FIT-C001"],
    )
    nuevo_estado: EstadoDeReserva = Field(
        ...,
        description="Estado resultante de la reserva en el ciclo de vida.",
        examples=[EstadoDeReserva.CANCELADA],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "mensaje": "Reserva cancelada exitosamente.",
                    "clase_id": "FIT-P001",
                    "socio_id": "FIT-C001",
                    "nuevo_estado": "CANCELADA",
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


class DetalleClaseDTO(BaseModel):
    """Información completa de aforo y horario de una clase grupal específica."""

    id: str = Field(
        ...,
        description="Identificador único de la clase.",
        examples=["FIT-P001"],
    )
    nombre: str = Field(
        ...,
        description="Nombre descriptivo de la disciplina.",
        examples=["Clase Mensual 01"],
    )
    horario_inicio: datetime = Field(
        ...,
        description="Inicio programado de la clase.",
        examples=["2026-11-06T10:00:00"],
    )
    horario_fin: datetime = Field(
        ...,
        description="Fin programado de la clase.",
        examples=["2026-11-06T11:00:00"],
    )
    capacidad_maxima: int = Field(
        ...,
        description="Capacidad o aforo total autorizado (BR-05).",
        examples=[15],
    )
    lugares_ocupados: int = Field(
        ...,
        description="Cantidad actual de reservaciones activas.",
        examples=[2],
    )
    lugares_disponibles: int = Field(
        ...,
        description="Lugares disponibles para reservar en este momento.",
        examples=[13],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "FIT-P001",
                    "nombre": "Clase Mensual 01",
                    "horario_inicio": "2026-11-06T10:00:00",
                    "horario_fin": "2026-11-06T11:00:00",
                    "capacidad_maxima": 15,
                    "lugares_ocupados": 2,
                    "lugares_disponibles": 13,
                }
            ]
        }
    )


class MembresiaDTO(BaseModel):
    """Estado y vigencia de la suscripción de un socio (BR-06 y BR-07)."""

    id: str = Field(
        ...,
        description="Código de membresía del socio.",
        examples=["MEM-FIT-C001"],
    )
    socio_id: str = Field(
        ...,
        description="Identificador del socio titular.",
        examples=["FIT-C001"],
    )
    plan_id: str = Field(
        ...,
        description="Identificador del plan contratado.",
        examples=["PLAN-001"],
    )
    inicio_vigencia: datetime = Field(
        ...,
        description="Fecha y hora de inicio de vigencia.",
        examples=["2026-10-01T00:00:00"],
    )
    fin_vigencia: datetime = Field(
        ...,
        description="Fecha y hora de vencimiento.",
        examples=["2027-10-01T00:00:00"],
    )
    vigente: bool = Field(
        ...,
        description="Indica si la membresía está vigente al día de hoy.",
        examples=[True],
    )
    suspendida: bool = Field(
        ...,
        description="Indica si la cuenta se encuentra suspendida.",
        examples=[False],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "MEM-FIT-C001",
                    "socio_id": "FIT-C001",
                    "plan_id": "PLAN-001",
                    "inicio_vigencia": "2026-10-01T00:00:00",
                    "fin_vigencia": "2027-10-01T00:00:00",
                    "vigente": True,
                    "suspendida": False,
                }
            ]
        }
    )


# ==========================================
# CIERRE DE CLASE / NO-SHOWS (BR-08, BR-09)
# ==========================================
class ComandoCerrarClase(BaseModel):
    """Solicitud para cerrar una clase ya terminada y registrar los no-shows."""

    actor_id: str = Field(
        ...,
        description="Identificador de quien ejecuta el cierre.",
        examples=["FIT-A001"],
    )
    actor_rol: Rol = Field(
        ...,
        description="Rol de quien ejecuta el cierre (Administrador o Sistema).",
        examples=["Administrador"],
    )


class RespuestaCierreDTO(BaseModel):
    """Resultado del cierre de una clase."""

    mensaje: str = Field(..., examples=["Clase cerrada. No-shows registrados: 2."])
    clase_id: str = Field(..., examples=["FIT-P001"])
    no_shows_registrados: int = Field(
        ...,
        description="Reservas activas sin asistencia que pasaron a NO_SHOW (sin sanción, BR-09).",
        examples=[2],
    )
