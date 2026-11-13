from typing import List, Optional
import uuid
from datetime import datetime
from src.domain.value_objects import (
    Actor,
    ReservaId,
    ClaseId,
    SocioId,
    Capacidad,
    Horario,
    VigenciaDeMembresia,
    PlanId,
    EstadoDeReserva,
    Rol,
)
from src.domain.entities import ClaseGrupal, Membresia, Reserva, PlanDeMembresia
from src.domain.specifications import MembresiaVigenteSpec, ClaseIncluidaEnPlanSpec
from src.application.dtos import (
    ComandoReservar,
    ComandoCancelar,
    ComandoRegistrarAsistencia,
    ReservaDTO,
    ClaseDisponibleDTO,
    DetalleClaseDTO,
    MembresiaDTO,
)
from src.application.unit_of_work import UnitOfWork
from src.infrastructure.orm import (
    ClaseGrupalORM,
    ReservaORM,
    MembresiaORM,
    PlanDeMembresiaORM,
)


# ==========================================
# COMMAND SERVICES (La Ventanilla de Trámites)
# ==========================================
class ServicioDeReservas:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def _reconstruir_agregado_clase(self, clase_orm: ClaseGrupalORM) -> ClaseGrupal:
        """Reconstruye el Agregado ClaseGrupal con sus reservas existentes para proteger invariantes."""
        clase = ClaseGrupal(
            id=ClaseId(clase_orm.id),
            nombre=clase_orm.nombre,
            horario=Horario(clase_orm.inicio, clase_orm.fin),
            capacidad=Capacidad(clase_orm.capacidad_maxima),
        )
        for r in clase_orm.reservas:
            reserva_entidad = Reserva(id=ReservaId(r.id), socio_id=SocioId(r.socio_id))
            reserva_entidad.estado = r.estado
            reserva_entidad.fecha_creacion = r.fecha_creacion
            clase._reservas.append(reserva_entidad)
        return clase

    @staticmethod
    def _traducir_membresia(membresia_orm: MembresiaORM) -> Membresia:
        """Convierte la fila de la base de datos en la entidad Membresia del dominio."""
        return Membresia(
            id=membresia_orm.id,
            socio_id=SocioId(membresia_orm.socio_id),
            plan_id=PlanId(membresia_orm.plan_id),
            vigencia=VigenciaDeMembresia(
                membresia_orm.inicio_vigencia, membresia_orm.fin_vigencia
            ),
            suspendida=membresia_orm.suspendida,
        )

    def _obtener_plan(self, plan_id: str) -> PlanDeMembresia:
        """Busca el plan contratado y lo traduce al dominio (BR-07)."""
        plan_orm = self.uow.db.get(PlanDeMembresiaORM, plan_id)
        if not plan_orm:
            raise ValueError(f"El plan '{plan_id}' de la membresía no existe.")
        return PlanDeMembresia(
            id=PlanId(plan_orm.id),
            nombre=plan_orm.nombre,
            clases_incluidas=[t.strip() for t in plan_orm.clases_incluidas.split(",")],
        )

    def reservar_clase(self, comando: ComandoReservar) -> str:
        """CU-01: Proceso para apartar un lugar en una clase (BR-01, BR-05, BR-06)."""
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

            # 2. Traducir ORM a Entidades Puras
            clase = self._reconstruir_agregado_clase(clase_orm)
            membresia = self._traducir_membresia(membresia_orm)

            # 3. Validar Reglas de Negocio mediante Specifications (BR-06)
            spec_vigencia = MembresiaVigenteSpec(fecha_actual=datetime.now())
            if not spec_vigencia.is_satisfied_by(membresia):
                raise ValueError(
                    "La membresía del socio no está vigente o está suspendida."
                )

            # 3b. BR-07: la clase debe estar incluida en el plan contratado
            plan = self._obtener_plan(membresia_orm.plan_id)
            spec_plan = ClaseIncluidaEnPlanSpec(tipo_clase=clase_orm.nombre)
            if not spec_plan.is_satisfied_by(plan):
                raise ValueError(
                    f"La clase '{clase_orm.nombre}' no está incluida en tu plan "
                    f"'{plan.nombre}'. Puedes actualizar tu plan en recepción "
                    "para tener acceso a ella."
                )

            # 4. Ejecutar la acción en el Dominio (protege cupo BR-05 y duplicidad)
            actor = Actor(id=comando.actor_id, rol=comando.actor_rol)
            nuevo_id_reserva = ReservaId(str(uuid.uuid4()))

            clase.reservar_lugar(
                socio_id=SocioId(comando.socio_id),
                actor=actor,
                reserva_id=nuevo_id_reserva,
            )

            # 5. Guardar en Base de Datos
            nueva_reserva_orm = ReservaORM(
                id=nuevo_id_reserva,
                clase_id=clase.id,
                socio_id=comando.socio_id,
                estado=EstadoDeReserva.ACTIVA,
                fecha_creacion=datetime.now(),
            )
            self.uow.db.add(nueva_reserva_orm)
            self.uow.confirmar(agregado=clase)

            return nuevo_id_reserva

    def cancelar_reserva(self, comando: ComandoCancelar) -> None:
        """CU-03: Cancela la reserva activa, libera cupo y detona eventos para la lista de espera."""
        with self.uow:
            clase_orm = self.uow.clases.obtener_por_id(comando.clase_id)
            if not clase_orm:
                raise ValueError("La clase solicitada no existe.")

            clase = self._reconstruir_agregado_clase(clase_orm)
            actor = Actor(id=comando.actor_id, rol=comando.actor_rol)

            # Dominio procesa la cancelación y emite ReservaCancelada
            clase.cancelar_reserva(socio_id=SocioId(comando.socio_id), actor=actor)

            # Reflejar cambio de estado en la persistencia ORM
            reserva_orm = next(
                (
                    r
                    for r in clase_orm.reservas
                    if r.socio_id == comando.socio_id
                    and r.estado == EstadoDeReserva.ACTIVA
                ),
                None,
            )
            if reserva_orm:
                reserva_orm.estado = EstadoDeReserva.CANCELADA

            self.uow.confirmar(agregado=clase)

    def registrar_asistencia(self, comando: ComandoRegistrarAsistencia) -> None:
        """CU-04: Recepción confirma que el socio llegó y entró a la sesión (BR-02)."""
        with self.uow:
            clase_orm = self.uow.clases.obtener_por_id(comando.clase_id)
            if not clase_orm:
                raise ValueError("La clase solicitada no existe.")

            # BR-06: una membresía vencida o suspendida tampoco puede entrar al gimnasio
            membresia_orm = self.uow.membresias.obtener_membresia_de_socio(
                comando.socio_id
            )
            if not membresia_orm:
                raise ValueError("El socio no tiene ninguna membresía registrada.")
            membresia = self._traducir_membresia(membresia_orm)
            if not MembresiaVigenteSpec(fecha_actual=datetime.now()).is_satisfied_by(
                membresia
            ):
                raise ValueError(
                    "La membresía del socio no está vigente o está suspendida. "
                    "No se puede permitir el acceso."
                )

            clase = self._reconstruir_agregado_clase(clase_orm)
            actor = Actor(id=comando.actor_id, rol=comando.actor_rol)

            # El dominio valida que actor.rol sea RECEPCION y que haya reserva activa
            clase.registrar_asistencia(socio_id=SocioId(comando.socio_id), actor=actor)

            # Reflejar estado ASISTIDA en persistencia
            reserva_orm = next(
                (
                    r
                    for r in clase_orm.reservas
                    if r.socio_id == comando.socio_id
                    and r.estado == EstadoDeReserva.ACTIVA
                ),
                None,
            )
            if reserva_orm:
                reserva_orm.estado = EstadoDeReserva.ASISTIDA

            self.uow.confirmar(agregado=clase)


class ServicioDeCierreDeClase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def registrar_no_shows(self, clase_id: str, actor: Actor) -> int:
        """
        CU-05 (BR-08): Al terminar la clase, toda reserva ACTIVA (no cancelada y sin
        asistencia) se registra como NO_SHOW. No se aplica ninguna sanción (BR-09).
        Devuelve cuántos no-shows se registraron.
        """
        if actor.rol not in [Rol.ADMINISTRADOR, Rol.SISTEMA]:
            raise PermissionError(
                "Solo el administrador o el sistema pueden cerrar una clase."
            )
        with self.uow:
            clase_orm = self.uow.clases.obtener_por_id(clase_id)
            if not clase_orm:
                raise ValueError("La clase solicitada no existe.")

            clase = ClaseGrupal(
                id=ClaseId(clase_orm.id),
                nombre=clase_orm.nombre,
                horario=Horario(clase_orm.inicio, clase_orm.fin),
                capacidad=Capacidad(clase_orm.capacidad_maxima),
            )
            for r in clase_orm.reservas:
                res = Reserva(id=ReservaId(r.id), socio_id=SocioId(r.socio_id))
                res.estado = r.estado
                clase._reservas.append(res)

            clase.procesar_cierre_de_clase()

            no_shows = 0
            for r in clase_orm.reservas:
                if r.estado == EstadoDeReserva.ACTIVA:
                    r.estado = EstadoDeReserva.NO_SHOW
                    no_shows += 1

            self.uow.confirmar(agregado=clase)
            return no_shows


# ==========================================
# QUERY SERVICES (La Ventanilla de Información - CQRS)
# ==========================================
class ServicioDeConsultas:
    """
    Bypass del Dominio: Para consultas de lectura rápida sin cargar lógica transaccional.
    """

    def __init__(self, db_session):
        self.db = db_session

    def consultar_calendario_disponible(self) -> List[ClaseDisponibleDTO]:
        clases_orm = self.db.query(ClaseGrupalORM).all()
        resultado = []
        for c in clases_orm:
            lugares_ocupados = len(
                [r for r in c.reservas if r.estado == EstadoDeReserva.ACTIVA]
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

    def consultar_detalle_clase(self, clase_id: str) -> Optional[DetalleClaseDTO]:
        c = (
            self.db.query(ClaseGrupalORM)
            .filter(ClaseGrupalORM.id == clase_id)
            .first()
        )
        if not c:
            return None

        lugares_ocupados = len(
            [r for r in c.reservas if r.estado == EstadoDeReserva.ACTIVA]
        )
        return DetalleClaseDTO(
            id=c.id,
            nombre=c.nombre,
            horario_inicio=c.inicio,
            horario_fin=c.fin,
            capacidad_maxima=c.capacidad_maxima,
            lugares_ocupados=lugares_ocupados,
            lugares_disponibles=c.capacidad_maxima - lugares_ocupados,
        )

    def consultar_reservas_de_socio(self, socio_id: str) -> List[ReservaDTO]:
        reservas_orm = (
            self.db.query(ReservaORM)
            .filter(ReservaORM.socio_id == socio_id)
            .order_by(ReservaORM.fecha_creacion.desc())
            .all()
        )
        return [
            ReservaDTO(
                id=r.id,
                clase_id=r.clase_id,
                socio_id=r.socio_id,
                estado=r.estado,
                fecha_creacion=r.fecha_creacion,
            )
            for r in reservas_orm
        ]

    def consultar_membresia_socio(self, socio_id: str) -> Optional[MembresiaDTO]:
        m = (
            self.db.query(MembresiaORM)
            .filter(MembresiaORM.socio_id == socio_id)
            .first()
        )
        if not m:
            return None

        ahora = datetime.now()
        vigente = not m.suspendida and (m.inicio_vigencia <= ahora <= m.fin_vigencia)
        return MembresiaDTO(
            id=m.id,
            socio_id=m.socio_id,
            plan_id=m.plan_id,
            inicio_vigencia=m.inicio_vigencia,
            fin_vigencia=m.fin_vigencia,
            vigente=vigente,
            suspendida=m.suspendida,
        )
