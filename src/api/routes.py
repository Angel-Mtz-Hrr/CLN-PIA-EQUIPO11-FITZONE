from fastapi import APIRouter, Depends, status, Body, Path, HTTPException
from sqlalchemy.orm import Session
from typing import List

# Importamos nuestras herramientas
from src.infrastructure.database import get_db
from src.application.unit_of_work import UnitOfWork
from src.application.services import ServicioDeReservas, ServicioDeConsultas
from src.domain.value_objects import EstadoDeReserva, Rol
from src.application.dtos import (
    ComandoReservar,
    ComandoCancelar,
    ComandoRegistrarAsistencia,
    ClaseDisponibleDTO,
    DetalleClaseDTO,
    RespuestaReserva,
    RespuestaAccionDTO,
    ReservaDTO,
    MembresiaDTO,
    ErrorRespuestaDTO,
)

router = APIRouter(tags=["Gimnasio FitZone"])


# ==========================================
# CATÁLOGO DE RESPUESTAS DE ERROR (Contratos OpenAPI)
# ==========================================
RESPUESTAS_ERROR_NEGOCIO = {
    status.HTTP_400_BAD_REQUEST: {
        "model": ErrorRespuestaDTO,
        "description": "Fallo por regla de negocio (ej. cupo lleno, membresía vencida, sin reserva activa).",
        "content": {
            "application/json": {
                "examples": {
                    "cupo_lleno": {
                        "summary": "Clase sin cupo disponible",
                        "value": {
                            "error": "Regla de Negocio",
                            "mensaje": "La clase no cuenta con cupo disponible.",
                            "solucion": "Intenta anotarte en la lista de espera o elige otro horario.",
                        },
                    },
                    "membresia_vencida": {
                        "summary": "Membresía no vigente o suspendida",
                        "value": {
                            "error": "Regla de Negocio",
                            "mensaje": "La membresía del socio no está vigente o se encuentra suspendida.",
                            "solucion": "Acude a recepción para renovar tu suscripción.",
                        },
                    },
                }
            }
        },
    },
    status.HTTP_403_FORBIDDEN: {
        "model": ErrorRespuestaDTO,
        "description": "El actor no tiene los permisos requeridos para ejecutar la acción.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Permiso Denegado",
                    "mensaje": "El usuario no cuenta con rol autorizado para realizar esta acción.",
                    "solucion": "Verifica que el actor posea el rol adecuado (Socio o Recepción).",
                }
            }
        },
    },
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorRespuestaDTO,
        "description": "El recurso solicitado no fue encontrado en el sistema.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Regla de Negocio",
                    "mensaje": "El recurso solicitado no existe.",
                    "solucion": "Verifica los identificadores enviados.",
                }
            }
        },
    },
}


# ==========================================
# DEPENDENCIAS (Inyectores de servicios)
# ==========================================
def get_servicio_reservas(db: Session = Depends(get_db)):
    uow = UnitOfWork(db)
    return ServicioDeReservas(uow)


def get_servicio_consultas(db: Session = Depends(get_db)):
    return ServicioDeConsultas(db)


# ==========================================
# ENDPOINTS DE CONSULTA (Queries - CQRS)
# ==========================================
@router.get(
    "/calendario",
    response_model=List[ClaseDisponibleDTO],
    status_code=status.HTTP_200_OK,
    summary="Consultar el horario de clases y cupos disponibles",
    response_description="Lista completa de clases programadas con cupos disponibles en tiempo real.",
)
def consultar_calendario(
    servicio: ServicioDeConsultas = Depends(get_servicio_consultas),
):
    """
    Retorna el catálogo completo de clases grupales y cuántos lugares quedan disponibles.
    Permite al socio o a recepción verificar disponibilidad antes de solicitar una reserva.
    """
    return servicio.consultar_calendario_disponible()


@router.get(
    "/clases/{clase_id}",
    response_model=DetalleClaseDTO,
    status_code=status.HTTP_200_OK,
    summary="Consultar detalle y aforo de una clase grupal",
    response_description="Detalles de horario, cupo total, lugares ocupados y disponibles.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorRespuestaDTO,
            "description": "Clase no encontrada.",
        }
    },
)
def consultar_detalle_clase(
    clase_id: str = Path(
        ...,
        description="Identificador único de la clase (ej. FIT-P001)",
        examples=["FIT-P001"],
    ),
    servicio: ServicioDeConsultas = Depends(get_servicio_consultas),
):
    """
    Obtiene la ficha técnica de una sesión grupal específica, incluyendo aforo total y lugares ocupados en tiempo real.
    """
    detalle = servicio.consultar_detalle_clase(clase_id)
    if not detalle:
        raise ValueError(f"La clase '{clase_id}' no existe en el sistema.")
    return detalle


@router.get(
    "/socios/{socio_id}/reservas",
    response_model=List[ReservaDTO],
    status_code=status.HTTP_200_OK,
    summary="Consultar el historial y estado de reservas de un socio",
    response_description="Lista cronológica de reservaciones (activas, canceladas o asistidas).",
)
def consultar_reservas_de_socio(
    socio_id: str = Path(
        ...,
        description="Identificador único del socio (ej. FIT-C001)",
        examples=["FIT-C001"],
    ),
    servicio: ServicioDeConsultas = Depends(get_servicio_consultas),
):
    """
    Entrega todas las reservaciones registradas a nombre de un socio para dar seguimiento a su historial de asistencia.
    """
    return servicio.consultar_reservas_de_socio(socio_id)


@router.get(
    "/socios/{socio_id}/membresia",
    response_model=MembresiaDTO,
    status_code=status.HTTP_200_OK,
    summary="Consultar estado y vigencia de la membresía de un socio",
    response_description="Detalles del plan, inicio y vencimiento de la membresía.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorRespuestaDTO,
            "description": "Socio sin membresía.",
        }
    },
)
def consultar_membresia_socio(
    socio_id: str = Path(
        ...,
        description="Identificador del socio (ej. FIT-C001)",
        examples=["FIT-C001"],
    ),
    servicio: ServicioDeConsultas = Depends(get_servicio_consultas),
):
    """
    Permite validar si el socio tiene una membresía activa y al día antes de agendar o permitir acceso.
    """
    membresia = servicio.consultar_membresia_socio(socio_id)
    if not membresia:
        raise ValueError(f"El socio '{socio_id}' no tiene una membresía registrada.")
    return membresia


# ==========================================
# ENDPOINTS TRANSACCIONALES (Commands - CQRS)
# ==========================================
@router.post(
    "/reservas",
    response_model=RespuestaReserva,
    status_code=status.HTTP_201_CREATED,
    summary="Apartar un lugar en una clase grupal",
    response_description="Confirmación exitosa con identificador UUID de la reserva generada.",
    responses=RESPUESTAS_ERROR_NEGOCIO,
)
def apartar_lugar(
    comando: ComandoReservar = Body(
        ...,
        description="Formulario de reserva que incluye la clase, el socio y el actor que solicita la operación.",
        openapi_examples={
            "reserva_socio": {
                "summary": "Reserva directa realizada por el Socio",
                "description": "El socio FIT-C001 reserva por sí mismo un lugar en la clase FIT-P001.",
                "value": {
                    "clase_id": "FIT-P001",
                    "socio_id": "FIT-C001",
                    "actor_id": "FIT-C001",
                    "actor_rol": "Socio",
                },
            },
            "reserva_recepcion": {
                "summary": "Reserva gestionada por el personal de Recepción",
                "description": "El recepcionista FIT-R001 aparta un lugar para el socio FIT-C002.",
                "value": {
                    "clase_id": "FIT-P001",
                    "socio_id": "FIT-C002",
                    "actor_id": "FIT-R001",
                    "actor_rol": "Recepción",
                },
            },
        },
    ),
    servicio: ServicioDeReservas = Depends(get_servicio_reservas),
):
    """
    Recibe la solicitud de reserva y aplica las reglas de negocio estrictas:
    - **Existencia**: La clase y la membresía deben existir en el sistema.
    - **Capacidad (BR-05)**: La clase debe contar con cupo disponible mayor a cero.
    - **Vigencia (BR-06)**: La membresía del socio debe estar activa y dentro de su rango de fechas.
    - **Autorización (BR-01 a BR-04)**: El actor debe poseer un rol válido (Socio o Recepción).
    """
    reserva_id = servicio.reservar_clase(comando)
    return {"mensaje": "¡Tu lugar está confirmado!", "reserva_id": str(reserva_id)}


@router.post(
    "/reservas/cancelar",
    response_model=RespuestaAccionDTO,
    status_code=status.HTTP_200_OK,
    summary="Cancelar una reserva activa",
    response_description="Confirmación de liberación de lugar en la clase grupal.",
    responses=RESPUESTAS_ERROR_NEGOCIO,
)
def cancelar_reserva(
    comando: ComandoCancelar = Body(
        ...,
        description="Datos requeridos para cancelar una reservación activa.",
        openapi_examples={
            "cancelacion_socio": {
                "summary": "Cancelación solicitada por el propio socio",
                "value": {
                    "clase_id": "FIT-P001",
                    "socio_id": "FIT-C001",
                    "actor_id": "FIT-C001",
                    "actor_rol": "Socio",
                },
            },
            "cancelacion_recepcion": {
                "summary": "Cancelación efectuada por recepción",
                "value": {
                    "clase_id": "FIT-P001",
                    "socio_id": "FIT-C001",
                    "actor_id": "FIT-R001",
                    "actor_rol": "Recepción",
                },
            },
        },
    ),
    servicio: ServicioDeReservas = Depends(get_servicio_reservas),
):
    """
    Cancela una reserva activa:
    - Libera el cupo inmediatamente en la clase.
    - Dispara el evento de dominio `ReservaCancelada`.
    - Si existe lista de espera, notifica al siguiente socio formado.
    """
    servicio.cancelar_reserva(comando)
    return {
        "mensaje": "Reserva cancelada exitosamente y lugar liberado.",
        "clase_id": comando.clase_id,
        "socio_id": comando.socio_id,
        "nuevo_estado": EstadoDeReserva.CANCELADA,
    }


@router.post(
    "/reservas/asistencia",
    response_model=RespuestaAccionDTO,
    status_code=status.HTTP_200_OK,
    summary="Registrar asistencia en puerta de una clase",
    response_description="Confirmación de asistencia verificada en el acceso.",
    responses=RESPUESTAS_ERROR_NEGOCIO,
)
def registrar_asistencia(
    comando: ComandoRegistrarAsistencia = Body(
        ...,
        description="Verificación de asistencia del socio al inicio de la sesión.",
        openapi_examples={
            "asistencia_recepcion": {
                "summary": "Validación por recepcionista",
                "value": {
                    "clase_id": "FIT-P001",
                    "socio_id": "FIT-C001",
                    "actor_id": "FIT-R001",
                    "actor_rol": "Recepción",
                },
            }
        },
    ),
    servicio: ServicioDeReservas = Depends(get_servicio_reservas),
):
    """
    Marca la asistencia de un socio al llegar al gimnasio:
    - Exige rol de `Recepción` (BR-02).
    - Valida que el socio posea una reserva activa para esa clase.
    - Pasa la reserva a estado `ASISTIDA` y dispara el evento `AsistenciaRegistrada`.
    """
    servicio.registrar_asistencia(comando)
    return {
        "mensaje": "Asistencia registrada correctamente.",
        "clase_id": comando.clase_id,
        "socio_id": comando.socio_id,
        "nuevo_estado": EstadoDeReserva.ASISTIDA,
    }
