from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.orm import Session
from typing import List

# Importamos nuestras herramientas
from src.infrastructure.database import get_db
from src.application.unit_of_work import UnitOfWork
from src.application.services import ServicioDeReservas, ServicioDeConsultas
from src.application.dtos import (
    ComandoReservar,
    ClaseDisponibleDTO,
    RespuestaReserva,
    ErrorRespuestaDTO,
)

router = APIRouter(tags=["Gimnasio FitZone"])


# ==========================================
# CATÁLOGO DE RESPUESTAS DE ERROR (Contratos OpenAPI)
# ==========================================
RESPUESTAS_ERROR_RESERVA = {
    status.HTTP_400_BAD_REQUEST: {
        "model": ErrorRespuestaDTO,
        "description": "Fallo por regla de negocio (ej. cupo lleno, membresía vencida, horario solapado).",
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
                    "mensaje": "El usuario no cuenta con rol autorizado para realizar esta reserva.",
                    "solucion": "Verifica que el actor posea rol 'Socio' o 'Recepción'.",
                }
            }
        },
    },
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorRespuestaDTO,
        "description": "El recurso solicitado (clase o socio) no fue encontrado.",
        "content": {
            "application/json": {
                "example": {
                    "error": "Regla de Negocio",
                    "mensaje": "La clase solicitada no existe.",
                    "solucion": "Verifica el código de clase consultando el calendario.",
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
# ENDPOINTS (Las ventanillas de atención)
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
    Retorna el horario general de clases grupales y cuántos lugares quedan disponibles.
    Permite al socio o a recepción verificar disponibilidad antes de solicitar una reserva.
    """
    return servicio.consultar_calendario_disponible()


@router.post(
    "/reservas",
    response_model=RespuestaReserva,
    status_code=status.HTTP_201_CREATED,
    summary="Apartar un lugar en una clase grupal",
    response_description="Confirmación exitosa con identificador UUID de la reserva generada.",
    responses=RESPUESTAS_ERROR_RESERVA,
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
    - **Autorización (BR-01 a BR-04)**: El actor debe poseer un rol válido para solicitar la reserva.
    """
    reserva_id = servicio.reservar_clase(comando)

    # Retornamos el diccionario que coincide con RespuestaReserva
    return {"mensaje": "¡Tu lugar está confirmado!", "reserva_id": str(reserva_id)}
