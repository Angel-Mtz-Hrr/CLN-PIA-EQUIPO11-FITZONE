from typing import List
import uuid
from datetime import datetime
from src.domain.value_objects import Actor, ReservaId, ClaseId, SocioId
from src.domain.specifications import MembresiaVigenteSpec
from src.application.dtos import (
    ComandoReservar,
    ComandoCancelar,
    ComandoRegistrarAsistencia,
    ReservaDTO,
    ClaseDisponibleDTO,
)
from src.application.unit_of_work import UnitOfWork
from src.infrastructure.orm import ClaseGrupalORM


# ==========================================
# COMMAND SERVICES (La Ventanilla de Trámites)
# ==========================================
class ServicioDeReservas:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def reservar_clase(self, comando: ComandoReservar) -> str:
        """CU-01: Proceso para apartar un lugar en una clase."""
        with self.uow:
            # 1. Traer los archiveros
            clase_orm = self.uow.clases.obtener_por_id(comando.clase_id)
            membresia_orm = self.uow.membresias.obtener_membresia_de_socio(
                comando.socio_id
            )

            if not clase_orm:
                raise ValueError("La clase solicitada no existe.")
            if not membresia_orm:
                raise ValueError("El socio no tiene ninguna membresía registrada.")

            # 2. Traducir ORM a Entidades Puras (simplificado para el ejemplo)
            # En un entorno completo, aquí usamos un "Mapper" para reconstruir el Agregado ClaseGrupal.
            from src.domain.entities import ClaseGrupal, Membresia
            from src.domain.value_objects import (
                Capacidad,
                Horario,
                VigenciaDeMembresia,
                PlanId,
            )

            clase = ClaseGrupal(
                id=ClaseId(clase_orm.id),
                nombre=clase_orm.nombre,
                horario=Horario(clase_orm.inicio, clase_orm.fin),
                capacidad=Capacidad(clase_orm.capacidad_maxima),
            )

            membresia = Membresia(
                id=membresia_orm.id,
                socio_id=SocioId(membresia_orm.socio_id),
                plan_id=PlanId(membresia_orm.plan_id),
                vigencia=VigenciaDeMembresia(
                    membresia_orm.inicio_vigencia, membresia_orm.fin_vigencia
                ),
                suspendida=membresia_orm.suspendida,
            )

            # 3. Validar Reglas de Negocio mediante Specifications (BR-06)
            spec_vigencia = MembresiaVigenteSpec(fecha_actual=datetime.now())
            if not spec_vigencia.is_satisfied_by(membresia):
                raise ValueError(
                    "La membresía del socio no está vigente o está suspendida."
                )

            # 4. Ejecutar la acción en el Dominio
            actor = Actor(id=comando.actor_id, rol=comando.actor_rol)
            nuevo_id_reserva = ReservaId(str(uuid.uuid4()))

            clase.reservar_lugar(
                socio_id=SocioId(comando.socio_id),
                actor=actor,
                reserva_id=nuevo_id_reserva,
            )

            # 5. Guardar en Base de Datos (Mapeo inverso)
            from src.infrastructure.orm import ReservaORM

            nueva_reserva_orm = ReservaORM(
                id=nuevo_id_reserva, clase_id=clase.id, socio_id=comando.socio_id
            )
            self.uow.db.add(nueva_reserva_orm)
            self.uow.confirmar(agregado=clase)

            return nuevo_id_reserva

    def cancelar_reserva(self, comando: ComandoCancelar):
        """CU-03: Cancela la reserva y detona eventos para la lista de espera."""
        pass  # La lógica es similar a reservar: buscar, llamar a clase.cancelar_reserva() y guardar.


class ServicioDeCierreDeClase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def registrar_no_shows(self, clase_id: str):
        """CU-05: El sistema barre la clase al terminar y castiga a los ausentes."""
        pass  # Busca la clase, llama a clase.procesar_cierre_de_clase() y guarda.


# ==========================================
# QUERY SERVICES (La Ventanilla de Información - CQRS)
# ==========================================
class ServicioDeConsultas:
    """
    Bypass del Dominio: Para solo leer, consultamos directo a la base de datos
    para que sea ultra rápido y no carguemos reglas innecesarias en memoria.
    """

    def __init__(self, db_session):
        self.db = db_session

    def consultar_calendario_disponible(self) -> List[ClaseDisponibleDTO]:
        clases_orm = self.db.query(ClaseGrupalORM).all()
        resultado = []
        for c in clases_orm:
            # Cálculo rápido de lugares
            lugares_ocupados = len(
                [r for r in c.reservas if r.estado.value == "ACTIVA"]
            )
            resultado.append(
                ClaseDisponibleDTO(
                    id=c.id,
                    nombre=c.nombre,
                    horario_inicio=c.inicio,
                    horario_fin=c.fin,
                    lugares_disponibles=c.capacidad_maxima - lugares_ocupados,
                )
            )
        return resultado
