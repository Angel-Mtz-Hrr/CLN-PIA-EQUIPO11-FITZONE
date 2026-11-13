from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass

from .value_objects import (
    ClaseId,
    SocioId,
    ReservaId,
    PlanId,
    MembresiaId,
    Capacidad,
    Horario,
    EstadoDeReserva,
    Actor,
    Rol,
    VigenciaDeMembresia,
    TipoRegistroHistorial,
)
from .events import (
    DomainEvent,
    ReservaRealizada,
    ReservaCancelada,
    LugarOfrecidoASocio,
    AsistenciaRegistrada,
    NoShowRegistrado,
)

# ==========================================
# RESERVAS Y LISTA DE ESPERA (Entidades Locales)
# ==========================================


class Reserva:
    """Entidad que representa el lugar apartado por un socio."""

    def __init__(self, id: ReservaId, socio_id: SocioId):
        self.id = id
        self.socio_id = socio_id
        self.estado = EstadoDeReserva.ACTIVA
        self.fecha_creacion = datetime.now()

    def cancelar(self):
        self.estado = EstadoDeReserva.CANCELADA

    def marcar_asistencia(self):
        self.estado = EstadoDeReserva.ASISTIDA

    def marcar_no_show(self):
        self.estado = EstadoDeReserva.NO_SHOW


class EntradaDeListaDeEspera:
    """Entidad para los socios formados cuando la clase se llena."""

    def __init__(self, socio_id: SocioId, posicion: int):
        self.socio_id = socio_id
        self.posicion = posicion
        self.fecha_ingreso = datetime.now()


# ==========================================
# AGREGADO PRINCIPAL: CLASE GRUPAL
# ==========================================


class ClaseGrupal:
    """
    Agregado Principal (Aggregate Root).
    Protege la capacidad, las reservas y la lista de espera (BR-05).
    """

    def __init__(
        self, id: ClaseId, nombre: str, horario: Horario, capacidad: Capacidad
    ):
        self.id = id
        self.nombre = nombre
        self.horario = horario
        self.capacidad = capacidad

        self._reservas: List[Reserva] = []
        self._lista_espera: List[EntradaDeListaDeEspera] = []
        self._eventos_pendientes: List[DomainEvent] = []

    @property
    def eventos(self) -> List[DomainEvent]:
        return self._eventos_pendientes

    def limpiar_eventos(self):
        self._eventos_pendientes.clear()

    def lugares_disponibles(self) -> int:
        reservas_activas = sum(
            1 for r in self._reservas if r.estado == EstadoDeReserva.ACTIVA
        )
        return self.capacidad.valor - reservas_activas

    def reservar_lugar(self, socio_id: SocioId, actor: Actor, reserva_id: ReservaId):
        if self.lugares_disponibles() <= 0:
            raise ValueError(
                f"No podemos reservar. La clase '{self.nombre}' está llena."
            )

        if actor.rol not in [Rol.SOCIO, Rol.RECEPCION]:
            raise PermissionError("Solo el socio o recepción pueden realizar reservas.")

        # BR-03: reservar "a nombre de otro socio" es tarea de Recepción, no de otro socio.
        if actor.rol == Rol.SOCIO and actor.id != socio_id:
            raise PermissionError("Un socio solo puede reservar a su propio nombre.")

        if any(
            r.socio_id == socio_id and r.estado == EstadoDeReserva.ACTIVA
            for r in self._reservas
        ):
            raise ValueError("El socio ya tiene una reserva activa para esta clase.")

        nueva_reserva = Reserva(id=reserva_id, socio_id=socio_id)
        self._reservas.append(nueva_reserva)
        self._eventos_pendientes.append(
            ReservaRealizada(clase_id=self.id, socio_id=socio_id)
        )

    def cancelar_reserva(self, socio_id: SocioId, actor: Actor):
        # BR-03: solo el propio socio o Recepción (a nombre del socio) pueden cancelar.
        if actor.rol not in [Rol.SOCIO, Rol.RECEPCION]:
            raise PermissionError(
                "Solo el socio o recepción pueden cancelar reservaciones."
            )
        if actor.rol == Rol.SOCIO and actor.id != socio_id:
            raise PermissionError("Un socio solo puede cancelar sus propias reservas.")

        reserva = next(
            (
                r
                for r in self._reservas
                if r.socio_id == socio_id and r.estado == EstadoDeReserva.ACTIVA
            ),
            None,
        )

        if not reserva:
            raise ValueError("No se encontró una reserva activa para cancelar.")

        reserva.cancelar()
        self._eventos_pendientes.append(
            ReservaCancelada(clase_id=self.id, socio_id=socio_id)
        )

        self._ofrecer_lugar_al_siguiente_en_espera()

    def registrar_asistencia(self, socio_id: SocioId, actor: Actor):
        if actor.rol != Rol.RECEPCION:
            raise PermissionError("Solo recepción puede validar los accesos en puerta.")

        reserva = next(
            (
                r
                for r in self._reservas
                if r.socio_id == socio_id and r.estado == EstadoDeReserva.ACTIVA
            ),
            None,
        )
        if not reserva:
            raise ValueError(
                "El socio no tiene reserva activa o intentó entrar sin avisar."
            )

        reserva.marcar_asistencia()
        self._eventos_pendientes.append(
            AsistenciaRegistrada(clase_id=self.id, socio_id=socio_id)
        )

    def procesar_cierre_de_clase(self):
        ahora = datetime.now()
        if ahora < self.horario.fin:
            raise ValueError(
                "No podemos procesar ausencias antes de que la clase termine."
            )

        for reserva in self._reservas:
            if reserva.estado == EstadoDeReserva.ACTIVA:
                reserva.marcar_no_show()
                self._eventos_pendientes.append(
                    NoShowRegistrado(clase_id=self.id, socio_id=reserva.socio_id)
                )

    def _ofrecer_lugar_al_siguiente_en_espera(self):
        if self._lista_espera and self.lugares_disponibles() > 0:
            siguiente = self._lista_espera.pop(0)
            self._eventos_pendientes.append(
                LugarOfrecidoASocio(clase_id=self.id, socio_id=siguiente.socio_id)
            )


# ==========================================
# AGREGADOS DE MEMBRESÍA Y PLAN (Solo Lectura)
# ==========================================


class PlanDeMembresia:
    """Define qué tipos de clase están incluidas. Es de solo lectura (BR-07)."""

    def __init__(self, id: PlanId, nombre: str, clases_incluidas: List[str]):
        self.id = id
        self.nombre = nombre
        self.clases_incluidas = clases_incluidas


class Membresia:
    """Representa la suscripción actual de un socio (BR-06)."""

    def __init__(
        self,
        id: MembresiaId,
        socio_id: SocioId,
        plan_id: PlanId,
        vigencia: VigenciaDeMembresia,
        suspendida: bool = False,
    ):
        self.id = id
        self.socio_id = socio_id
        self.plan_id = plan_id
        self.vigencia = vigencia
        self.suspendida = suspendida

    def esta_vigente_en(self, instante: datetime) -> bool:
        """Verifica si la membresía es válida y no ha sido suspendida."""
        if self.suspendida:
            return False
        return self.vigencia.esta_vigente_en(instante)


# ==========================================
# AGREGADO DE HISTORIAL
# ==========================================


@dataclass(frozen=True)
class RegistroDeHistorial:
    """Value Object que representa una línea en el historial del socio."""

    tipo: TipoRegistroHistorial
    clase_id: ClaseId
    instante: datetime


class HistorialDeAsistencia:
    """Centraliza el comportamiento histórico del socio para métricas administrativas."""

    def __init__(self, socio_id: SocioId):
        self.socio_id = socio_id
        self._registros: List[RegistroDeHistorial] = []

    def registrar_accion(
        self, clase_id: ClaseId, tipo: TipoRegistroHistorial, instante: datetime = None
    ):
        fecha = instante or datetime.now()
        registro = RegistroDeHistorial(tipo=tipo, clase_id=clase_id, instante=fecha)
        self._registros.append(registro)

    def total_no_shows(self) -> int:
        return sum(
            1 for r in self._registros if r.tipo == TipoRegistroHistorial.NO_SHOW
        )
