from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

# Importamos nuestras herramientas
from src.infrastructure.database import get_db
from src.application.unit_of_work import UnitOfWork
from src.application.services import ServicioDeReservas, ServicioDeConsultas
from src.application.dtos import ComandoReservar, ClaseDisponibleDTO

router = APIRouter(tags=["Gimnasio FitZone"])


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
    summary="Consultar el horario de clases",
)
def consultar_calendario(
    servicio: ServicioDeConsultas = Depends(get_servicio_consultas),
):
    """
    Entrega la lista de clases programadas y cuántos lugares quedan disponibles.
    Ideal para que el socio decida a qué clase asistir.
    """
    return servicio.consultar_calendario_disponible()


@router.post("/reservas", status_code=201, summary="Apartar un lugar en una clase")
def apartar_lugar(
    comando: ComandoReservar,
    servicio: ServicioDeReservas = Depends(get_servicio_reservas),
):
    """
    Recibe el formulario del socio (o de recepción) y procesa la reservación.
    Si rompe alguna regla (ej. clase llena, membresía vencida), el sistema lo detendrá.
    """
    reserva_id = servicio.reservar_clase(comando)
    return {"mensaje": "¡Tu lugar está confirmado!", "reserva_id": reserva_id}
